import glob
import json
import logging
import math
import os
import os.path
import shutil
import subprocess
import warnings
from io import BytesIO
from pathlib import Path
from typing import Any, Union
from zipfile import ZipFile

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
import shapefile
import utm
import xarray
from pyproj import CRS
from shapely.geometry import mapping, shape
from tethys_sdk.gizmos import SelectInput

from .app import Ggst as app

warnings.simplefilter("ignore")

logger = logging.getLogger("subset_grace")
logger.setLevel(logging.DEBUG)


def user_permission_test(user):
    return user.is_superuser or user.is_staff


def get_regions():
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), "")
    regions_list = [
        (f.name.replace("_", " ").title(), f.name)
        for f in os.scandir(grace_dir)
        if f.is_dir()
    ]
    return regions_list


def get_catalog_url():
    catalog_url = app.get_custom_setting("grace_thredds_catalog")
    return catalog_url


def get_styles():
    catalog_url = app.get_custom_setting("grace_thredds_catalog")
    wms_url = catalog_url.replace("catalog.xml", "").replace("catalog", "wms")
    metadata_url = os.path.join(wms_url, "GRC_grace.nc?request=GetMetadata&item=layerDetails&layerName=lwe_thickness")
    layer_metadata = requests.get(metadata_url).json()
    palettes = layer_metadata["palettes"]
    return palettes

def get_symbology_select():
    styles = get_styles()
    select_signal_process = SelectInput(
        display_text="Select Style",
        name="select-symbology",
        multiple=False,
        options=[(style, style) for style in styles],
        initial=["grace"],
    )
    return select_signal_process


def get_signal_process_select():
    select_signal_process = SelectInput(
        display_text="Select Signal Processing Method",
        name="select-signal-process",
        multiple=False,
        options=[
            ("JPL Solution", "jpl"),
            ("CSR Solution", "csr"),
            ("GFZ Solution", "gfz"),
            ("Ensemble Avg of JPL, CSR, & GFZ", "avg"),
        ],
        initial=["CSR Solution"],
    )
    return select_signal_process


def storage_options():
    options = [
        ("Total Water Storage (GRACE)", "grace"),
        ("Surface Water Storage (GLDAS)", "sw"),
        ("Soil Moisture Storage (GLDAS)", "sm"),
        ("Groundwater Storage (Calculated)", "gw"),
        # ("Surface Water Storage (GLDAS NOAH .25)", "025sw"),
        # ("Soil Moisture Storage (GLDAS NOAH .25)", "025sm"),
        # ("Groundwater Storage (Calculated NOAH .25)", "025gw"),
    ]
    return options


def get_storage_type_select():
    select_storage_type = SelectInput(
        display_text="Select Storage Component",
        name="select-storage-type",
        multiple=False,
        options=storage_options(),
        initial=["Total Water Storage (GRACE)"],
    )
    return select_storage_type


def get_grace_timestep_options(storage_type):
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), "")
    nc_file = f"{grace_dir}GRC_{storage_type}.nc"
    ds = xarray.open_dataset(nc_file)
    grace_layer_options = [
        (
            pd.to_datetime(time_step).strftime("%Y %B %d"),
            f"{str(time_step)}|{int(time_step.astype(int) / 1000000)}",
        )
        for time_step in ds.time.values
    ]
    return grace_layer_options


def get_layer_select(storage_type):
    select_layer = SelectInput(
        display_text="Select a day",
        name="select-layer",
        multiple=False,
        options=get_grace_timestep_options(storage_type),
    )
    return select_layer


def get_region_select():
    """
    Generate Region Select Gizmo

    Returns:
        Tethys Select Input Gizmo Object to select regions
    """
    region_list = get_regions()
    region_select = SelectInput(
        display_text="Select a Region",
        name="region-select",
        options=region_list,
    )
    return region_select


def clip_nc(
    nc_file: str,
    gdf: gpd.GeoDataFrame,
    region_name: str,
    grace_dir: str,
    export: bool = True,
) -> Union[str, xarray.Dataset]:
    # logger.info(f'Subset {nc_file} for {region_name}')
    # print(f'Subset {nc_file} for {region_name}')
    ds = xarray.open_dataset(nc_file)
    # ds = ds.assign({"lon": (((ds.lon + 180) % 360) - 180)}).sortby('lon')
    if "spatial_ref" in ds.variables:
        ds = ds.drop_sel("spatial_ref")

    ds["lwe_thickness"] = ds["lwe_thickness"].rio.write_crs("epsg:4326")
    ds["uncertainty"] = ds["uncertainty"].rio.write_crs("epsg:4326")

    if "grid_mapping" in ds.uncertainty.attrs:
        del ds.uncertainty.attrs["grid_mapping"]
    # if 'tot' in nc_file:
    #     ds = ds.drop_vars(['gw', 'lat_bnds', 'lon_bnds'])
    ds.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    clipped = ds.rio.clip(gdf.geometry.apply(mapping), gdf.crs, drop=True, all_touched=True)
    if "spatial_ref" in ds.variables:
        clipped = clipped.drop("spatial_ref")
    if "WGS84" in ds.variables:
        clipped = clipped.drop("WGS84")

    if export:
        output_path = os.path.join(
            grace_dir, region_name, f"{region_name}{nc_file.split('/')[-1][3:]}"
        )
        clipped.to_netcdf(
            output_path,
            encoding={
                "lwe_thickness": {"_FillValue": -99999.0, "missing_value": -99999.0}
            },
        )
        # lwe_thickness.to_netcdf(ts_path)
        # uncertainty.to_netcdf(error_path)
        return output_path
    else:
        return clipped


def calculate_area(gdf: gpd.GeoDataFrame):
    areas = []
    for row in gdf.itertuples():
        centroid = row.geometry.centroid
        utm_tuple = utm.from_latlon(centroid.y, centroid.x)
        if centroid.y > 0:
            south = False
        else:
            south = True
        crs = CRS.from_dict({"proj": "utm", "zone": utm_tuple[2], south: south})
        crs_code = f"EPSG:{crs.to_authority()[1]}"
        row_as_df = pd.DataFrame.from_records([row], columns=row._fields)
        row_as_gdf = gpd.GeoDataFrame(
            row_as_df, geometry=row_as_df.geometry, crs="EPSG:4326"
        )
        row_as_utm = row_as_gdf.to_crs(crs_code)
        areas.append(row_as_utm.area.sum())
    area = sum(areas)
    return area


def subset_shape(gdf: gpd.GeoDataFrame, region_name: str) -> str:
    logger.info("Starting the subsetting...")
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), "")
    nc_files_list = glob.glob(f"{grace_dir}*.nc")
    output_dir = os.path.join(grace_dir, region_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    [clip_nc(nc_file, gdf, region_name, grace_dir) for nc_file in nc_files_list]
    region_area = calculate_area(gdf)
    gdf.to_file(os.path.join(output_dir, "shape.geojson"), driver="GeoJSON")
    with open(os.path.join(output_dir, "area.json"), "w") as f:
        json.dump({"area": region_area}, f)
    logger.info("End of the subsetting...")
    return output_dir


def process_interface_files(files_list):
    process_files = [(BytesIO(f_name.read()), f_name.name) for f_name in files_list]
    dbf, prj, shp, shx = sorted(process_files, key=lambda x: x[1])
    return dbf[0], prj[0], shp[0], shx[0]


def process_api_files(files_list):
    input_zip = ZipFile(files_list[0])
    shp_list = [".shp", ".shx", ".prj", ".dbf"]
    files_dict = {
        name: input_zip.read(name)
        for name in input_zip.namelist()
        if name[-4:] in shp_list
    }
    zip_keys = sorted(files_dict.keys())
    dbf = BytesIO(files_dict[zip_keys[0]])
    prj = BytesIO(files_dict[zip_keys[1]])
    shp = BytesIO(files_dict[zip_keys[2]])
    shx = BytesIO(files_dict[zip_keys[3]])
    return dbf, prj, shp, shx


def process_shapefile(
    region_store: str, files_list: list, upload_type: str
) -> Union[str, gpd.GeoDataFrame]:
    dbf, prj, shp, shx = None, None, None, None
    if upload_type == "interface":
        dbf, prj, shp, shx = process_interface_files(files_list)
    if upload_type == "api":
        dbf, prj, shp, shx = process_api_files(files_list)
    r = shapefile.Reader(shp=shp, shx=shx, dbf=dbf)
    attributes, geometry = [], []
    field_names = [field[0] for field in r.fields[1:]]
    for row in r.shapeRecords():
        geometry.append(shape(row.shape.__geo_interface__))
        attributes.append(dict(zip(field_names, row.record)))

    prj_string = prj.read().decode()
    gdf = gpd.GeoDataFrame(data=attributes, geometry=geometry, crs=prj_string)
    gdf.to_crs("EPSG:4326", inplace=True)
    gdf.loc[:, gdf.columns.drop('geometry')] = gdf.loc[:, gdf.columns.drop('geometry')].astype(str)
    if upload_type == "interface":
        output_dir = subset_shape(gdf, region_store)
        return output_dir
    if upload_type == "api":
        return gdf


def gen_zip_api(gdf: gpd.GeoDataFrame, region_name: str) -> Any:
    output_dir = subset_shape(gdf, region_name)
    src_path = Path(output_dir).expanduser().resolve(strict=True)
    in_memory_zip = BytesIO()
    zf = ZipFile(in_memory_zip, mode="w")
    for file in src_path.rglob("*"):
        zf.write(file, file.relative_to(src_path.parent))
    zf.close()
    shutil.rmtree(output_dir)
    return in_memory_zip


def region_api_ts(region_name, storage_type, zipfile):
    graph_json = {}
    shape_file = process_shapefile(region_name, zipfile, "api")
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), "")
    nc_file = os.path.join(grace_dir, f"GRC_{storage_type}.nc")
    region_area = calculate_area(shape_file)
    ds = clip_nc(nc_file, shape_file, region_name, grace_dir, False)
    lwe_da = ds.lwe_thickness.mean(["lat", "lon"])
    error_da = ds.uncertainty.mean(["lat", "lon"])
    ts_plot = []
    error_range = []
    ts_plot_int = []
    init_value = lwe_da.values[0]
    for x, y in zip(lwe_da, error_da):
        value = x.values
        error_bar = y.values
        utc_time = np.datetime_as_string(x.time.values, unit="D")
        difference_data_value = (value - init_value) * 0.00000075 * region_area
        ts_plot.append([utc_time, round(float(value), 3)])
        error_range.append(
            [
                utc_time,
                round(float(value - error_bar), 3),
                round(float(value + error_bar), 3),
            ]
        )
        ts_plot_int.append([utc_time, round(float(difference_data_value), 3)])

    graph_json["values"] = ts_plot
    graph_json["depletion"] = ts_plot_int
    graph_json["error_range"] = error_range
    graph_json["area"] = region_area
    graph_json["success"] = "success"
    # graph_json = json.dumps(graph_json)
    return graph_json


def generate_timeseries(storage_type, lat, lon, region):
    graph_json = {}
    ts_plot = []
    ts_plot_int = []
    error_range = []
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), "")

    stn_lat = float(lat)
    stn_lon = float(lon)

    if region == "global":
        nc_file = f"{grace_dir}GRC_{storage_type}.nc"
        # if stn_lon < 0.0:
        #     stnd_lon = float(stn_lon + 360.0)
        # else:
        stnd_lon = stn_lon
    else:
        nc_file = os.path.join(grace_dir, region, f"{region}_{storage_type}.nc")
        stnd_lon = stn_lon

    ds = xarray.open_dataset(nc_file)
    time_array = ds.time.values
    lat_array = ds["lat"][:]
    lon_array = ds["lon"][:]
    # Find the lon size
    lon_interval_size = ds.variables["lon"][1] - ds.variables["lon"][0]
    # Find the lat size
    lat_interval_size = ds.variables["lat"][1] - ds.variables["lat"][0]
    lon_idx = (np.abs(lon_array - stnd_lon)).argmin().values
    lat_idx = (np.abs(lat_array - stn_lat)).argmin().values

    init_value = float(ds["lwe_thickness"][0, lat_idx, lon_idx].values)

    for time_index, time_stamp in enumerate(time_array):
        data = ds["lwe_thickness"][time_index, :, :]
        uncertainty = ds["uncertainty"][time_index, :, :]
        value = data[lat_idx, lon_idx].values
        error_bar = uncertainty[lat_idx, lon_idx].values
        utc_time = int(time_stamp.astype(int) / 1000000)
        difference_data_value = (
            (value - init_value)
            * 0.01
            * 6371000
            * math.radians(lon_interval_size)
            * 6371000
            * math.radians(lat_interval_size)
            * abs(math.cos(math.radians(lat_idx)))
            * 0.000810714
        )
        ts_plot.append([utc_time, round(float(value), 3)])
        ts_plot_int.append([utc_time, round(float(difference_data_value), 3)])
        error_range.append(
            [
                utc_time,
                round(float(value - error_bar), 3),
                round(float(value + error_bar), 3),
            ]
        )

    graph_json["values"] = sorted(ts_plot)
    graph_json["integr_values"] = sorted(ts_plot_int)
    graph_json["error_range"] = error_range
    graph_json["point"] = [round(stn_lat, 2), round(stn_lon, 2)]
    graph_json = json.dumps(graph_json)
    return graph_json


def get_regional_ts(region, storage_type):
    graph_json = {}
    ts_plot = []
    ts_plot_int = []
    error_range = []
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), "")
    nc_file = os.path.join(grace_dir, region, f"{region}_{storage_type}.nc")
    ds = xarray.open_dataset(nc_file)
    region_area = json.load(open(os.path.join(grace_dir, region, "area.json"), "r"))[
        "area"
    ]
    lwe_da = ds.lwe_thickness.mean(["lat", "lon"])
    error_da = ds.uncertainty.mean(["lat", "lon"])

    init_value = lwe_da.values[0]
    for x, y in zip(lwe_da, error_da):
        value = x.values
        error_bar = y.values
        utc_time = int(x.time.values.astype(int) / 1000000)
        difference_data_value = (value - init_value) * 0.00000075 * region_area
        ts_plot.append([utc_time, round(float(value), 3)])
        error_range.append(
            [
                utc_time,
                round(float(value - error_bar), 3),
                round(float(value + error_bar), 3),
            ]
        )
        ts_plot_int.append([utc_time, round(float(difference_data_value), 3)])

    graph_json["values"] = ts_plot
    graph_json["integr_values"] = ts_plot_int
    graph_json["error_range"] = error_range
    graph_json["area"] = region_area
    graph_json = json.dumps(graph_json)

    return graph_json


def get_region_bounds(region_name):
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), "")
    nc_file = os.path.join(grace_dir, region_name, f"{region_name}_sw.nc")
    ds = xarray.open_dataset(nc_file)
    lat = ds["lat"][:]
    lon = ds["lon"][:]
    minx = float(lon.min())
    miny = float(lat.min())
    maxx = float(lon.max())
    maxy = float(lat.max())
    bbox = [minx, miny, maxx, maxy]
    return bbox


def file_range(region_name, storage_type):
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), "")
    nc_file = os.path.join(grace_dir, region_name, f"{region_name}_{storage_type}.nc")
    ds = xarray.open_dataset(nc_file)
    lwe_thickness = ds["lwe_thickness"][:]
    min_val = round(float(lwe_thickness.min()), 2)
    max_val = round(float(lwe_thickness.max()), 2)
    return min_val, max_val


def delete_region_dir(region_name):
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), "")
    output_dir = os.path.join(grace_dir, region_name)
    shutil.rmtree(output_dir)
    return True


def get_geojson(region_name):
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), "")
    geojson_file = os.path.join(grace_dir, region_name, f"{shape.geojson}")
    geojson_obj = gpd.read_file(geojson_file).to_json()
    return geojson_obj


class GraceArray(object):
    def __init__(self, storage_type, signal_process, region, grace_dir):
        self.storage_type = storage_type
        self.signal_process = signal_process
        self.region = region
        self.grace_dir = grace_dir

    def _get_nc_file(self):
        region = self.region
        grace_dir = self.grace_dir
        signal_process = self.signal_process
        storage_type = self.storage_type
        if region == "global":
            nc_file = f"{grace_dir}GRC_{signal_process}_{storage_type}.nc"
        else:
            nc_file = os.path.join(
                grace_dir, region, f"{region}_{signal_process}_{storage_type}.nc"
            )

        self.nc_file = nc_file

    def _get_data_array(self):
        ds = xarray.open_dataset(self.nc_file)
        self.dataset = ds


class PointArray(GraceArray):
    def __init__(self, lat, lon, storage_type, signal_process, region, grace_dir):
        self.lat = lat
        self.lon = lon
        super().__init__(storage_type, signal_process, region, grace_dir)
        self._get_nc_file()
        self._get_data_array()
        self.time_array = self.dataset.time.values
        self.lat_array = self.dataset["lat"][:]
        self.lon_array = self.dataset["lon"][:]
        self.lat_idx = self._get_lat_idx()
        self.lon_idx = self._get_lon_idx()

    def _get_lat_idx(self):
        lat_array = self.lat_array
        lat = self.lat
        return (np.abs(lat_array - lat)).argmin().values

    def _get_lon_idx(self):
        lon = self.lon
        region = self.region
        lon_array = self.lon_array
        if region == "global":
            if lon < 0.0:
                stnd_lon = float(lon + 360.0)
            else:
                stnd_lon = lon
        else:
            stnd_lon = lon
        return (np.abs(lon_array - stnd_lon)).argmin().values


class TimeSeries(PointArray):
    def _get_global_vars(self):
        lat_idx = self.lat_idx
        lon_idx = self.lon_idx
        dataset = self.dataset
        lat = self.lat
        lon = self.lon
        return lat, lon, lat_idx, lon_idx, dataset

    def calc_mean_ts(self):
        lat, lon, lat_idx, lon_idx, dataset = self._get_global_vars()
        init_value = float(dataset["lwe_thickness"].mean(("lat", "lon"))[0].values)
        graph_json = self.get_ts(
            lat,
            lon,
            lat_idx,
            None,
            init_value,
            dataset.lwe_thickness.mean(("lat", "lon")),
        )
        return graph_json

    def calc_raw_ts(self):
        lat, lon, lat_idx, lon_idx, dataset = self._get_global_vars()
        init_value = float(dataset["lwe_thickness"][0, lat_idx, lon_idx].values)
        graph_json = self.get_ts(
            lat, lon, lat_idx, lon_idx, init_value, dataset.lwe_thickness
        )
        return graph_json

    @staticmethod
    def get_ts(lat, lon, lat_idx, lon_idx, init_value, ts_array):
        graph_json = {}
        time_series = []
        time_series_int = []
        for time_index, time_stamp in enumerate(ts_array):
            if lon_idx is None:
                value = float(time_stamp.values)
            else:
                value = ts_array[time_index, :, :][lat_idx, lon_idx].values
            difference_data_value = (
                (value - init_value)
                * 0.01
                * 6371000
                * math.radians(0.25)
                * 6371000
                * math.radians(0.25)
                * abs(math.cos(math.radians(lat_idx)))
                * 0.000810714
            )
            utc_time = int(time_stamp["time"].astype(int) / 1000000)
            time_series.append([utc_time, round(float(value), 3)])
            time_series_int.append([utc_time, round(float(difference_data_value), 3)])
        graph_json["values"] = sorted(time_series)
        graph_json["integr_values"] = sorted(time_series_int)
        graph_json["point"] = [round(lat, 2), round(lon, 2)]
        graph_json = json.dumps(graph_json)
        return graph_json


def trigger_global_process():
    file_path = os.path.join(Path(__file__).parent.absolute(), "update_global_files.py")
    grace_output_dir = os.path.join(
        app.get_custom_setting("global_output_directory"), ""
    )
    grace_thredds_dir = os.path.join(
        app.get_custom_setting("grace_thredds_directory"), ""
    )
    earthdata_username = app.get_custom_setting("earthdata_username")
    earthdata_pass = app.get_custom_setting("earthdata_pass")
    python_executable = app.get_custom_setting("conda_python_path")
    subprocess.Popen(
        [
            python_executable,
            file_path,
            grace_output_dir,
            grace_thredds_dir,
            earthdata_username,
            earthdata_pass,
        ]
    )
    return
