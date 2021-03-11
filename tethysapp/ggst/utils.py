import glob
import json
import logging
import math
import os
import shutil
import warnings
from io import BytesIO
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import geopandas as gpd
import numpy as np
import pandas as pd
import shapefile
import xarray
from shapely.geometry import mapping
from shapely.geometry import shape
from tethys_sdk.gizmos import SelectInput

from .app import Ggst as app

warnings.simplefilter("ignore")

logger = logging.getLogger('subset_grace')
logger.setLevel(logging.DEBUG)


def user_permission_test(user):
    return user.is_superuser or user.is_staff


def get_regions():
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), '')
    regions_list = [(f.name.replace('_', ' ').title(), f.name) for f in os.scandir(grace_dir) if f.is_dir()]
    return regions_list


def get_catalog_url():
    catalog_url = app.get_custom_setting("grace_thredds_catalog")
    return catalog_url


def get_symbology_select():
    select_signal_process = SelectInput(display_text='Select Style',
                                        name='select-symbology',
                                        multiple=False,
                                        options=[('GRACE', 'grace'),
                                                 ('Red-Blue', 'bluered'),
                                                 ('Grey Scale', 'greyscale'),
                                                 ('ALG2', 'alg2'),
                                                 ('SST 36', 'sst_36'),
                                                 ('Rainbow', 'rainbow')],
                                        initial=['GRACE']
                                        )
    return select_signal_process


def get_signal_process_select():
    select_signal_process = SelectInput(display_text='Select Signal Processing Method',
                                        name='select-signal-process',
                                        multiple=False,
                                        options=[('JPL Solution', "jpl"), ('CSR Solution', "csr"),
                                                 ('GFZ Solution', "gfz"), ('Ensemble Avg of JPL, CSR, & GFZ', "avg")],
                                        initial=['CSR Solution']
                                        )
    return select_signal_process


def get_storage_type_select():
    select_storage_type = SelectInput(display_text='Select Storage Component',
                                      name='select-storage-type',
                                      multiple=False,
                                      options=[('Total Water Storage (GRACE)', "tot"),
                                               ('Surface Water Storage (GLDAS)', "sw"),
                                               ('Soil Moisture Storage (GLDAS)', "soil"),
                                               ('Groundwater Storage (Calculated)', "gw")],
                                      initial=['Total Water Storage (GRACE)']
                                      )
    return select_storage_type


def get_grace_timestep_options():
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), '')
    nc_file = f'{grace_dir}GRC_avg_sw.nc'
    ds = xarray.open_dataset(nc_file)
    grace_layer_options = [(pd.to_datetime(time_step).strftime('%Y %B %d'),
                            f'{str(time_step)}|{int(time_step.astype(int) / 1000000)}')
                           for time_step in ds.time.values]
    return grace_layer_options


def get_layer_select():
    select_layer = SelectInput(display_text='Select a day',
                               name='select-layer',
                               multiple=False,
                               options=get_grace_timestep_options()
                               )
    return select_layer


def get_region_select():
    """
    Generate Region Select Gizmo

    Returns:
        Tethys Select Input Gizmo Object to select regions
    """
    region_list = get_regions()
    region_select = SelectInput(display_text='Select a Region',
                                name='region-select',
                                options=region_list,)

    return region_select


def clip_nc(nc_file: str,
            gdf: gpd.GeoDataFrame,
            region_name: str,
            grace_dir: str) -> str:
    # logger.info(f'Subset {nc_file} for {region_name}')
    print(nc_file)
    ds = xarray.open_dataset(nc_file)
    ds = ds.assign({"lon": (((ds.lon + 180) % 360) - 180)}).sortby('lon')
    ds['lwe_thickness'] = ds['lwe_thickness'].rio.write_crs("epsg:4326")

    if 'tot' in nc_file:
        ds = ds.drop_vars(['gw', 'lat_bnds', 'lon_bnds'])
    ds.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    clipped = ds.rio.clip(gdf.geometry.apply(mapping), gdf.crs, drop=True)
    output_path = os.path.join(grace_dir, region_name, f"{region_name}{nc_file.split('/')[-1][3:]}")
    ts_path = os.path.join(grace_dir, region_name, f"{region_name}{nc_file.split('/')[-1][3:-3]}_ts.nc")
    lwe_thickness = clipped.lwe_thickness.mean(['lat', 'lon'])
    clipped.to_netcdf(output_path,
                      encoding={"lwe_thickness":
                                    {'_FillValue': -99999.0,
                                     'missing_value': -99999.0}})
    lwe_thickness.to_netcdf(ts_path)
    return output_path


def subset_shape(gdf: gpd.GeoDataFrame,
                 region_name: str) -> str:
    logger.info('Starting the subsetting...')
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), '')
    print(grace_dir)
    nc_files_list = glob.glob(f'{grace_dir}*.nc')
    print(nc_files_list)
    output_dir = os.path.join(grace_dir, region_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    print('before')
    subset_paths = [clip_nc(nc_file, gdf, region_name, grace_dir) for nc_file in nc_files_list]
    print('after')
    logger.info('End of the subsetting...')
    return output_dir


def process_shapefile(region_store: str,
                      files_list: list) -> str:
    process_files = [(BytesIO(f_name.read()), f_name.name) for f_name in files_list]
    dbf, prj, shp, shx = sorted(process_files, key=lambda x: x[1])
    r = shapefile.Reader(shp=shp[0], shx=shx[0], dbf=dbf[0])
    attributes, geometry = [], []
    field_names = [field[0] for field in r.fields[1:]]
    for row in r.shapeRecords():
        geometry.append(shape(row.shape.__geo_interface__))
        attributes.append(dict(zip(field_names, row.record)))

    prj_string = prj[0].read().decode()
    gdf = gpd.GeoDataFrame(data=attributes, geometry=geometry, crs=prj_string)
    gdf.to_crs('EPSG:4326', inplace=True)
    print(region_store)
    output_dir = subset_shape(gdf, region_store)
    return output_dir


def gen_zip_api(gdf: gpd.GeoDataFrame,
                region_name: str) -> Any:
    output_dir = subset_shape(gdf, region_name)
    src_path = Path(output_dir).expanduser().resolve(strict=True)
    in_memory_zip = BytesIO()
    zf = ZipFile(in_memory_zip, mode="w")
    for file in src_path.rglob('*'):
        zf.write(file, file.relative_to(src_path.parent))
    zf.close()
    shutil.rmtree(output_dir)
    return in_memory_zip


def generate_global_timeseries(storage_type, signal_process, lat, lon):
    graph_json = {}
    ts_plot = []
    ts_plot_int = []
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), '')
    nc_file = f'{grace_dir}GRC_{signal_process}_{storage_type}.nc'
    stn_lat = float(lat)
    stn_lon = float(lon)
    if stn_lon < 0.0:
        stnd_lon = float(stn_lon + 360.0)
    else:
        stnd_lon = stn_lon
    ds = xarray.open_dataset(nc_file)
    time_array = ds.time.values
    lat_array = ds['lat'][:]
    lon_array = ds['lon'][:]
    lon_idx = (np.abs(lon_array - stnd_lon)).argmin().values
    lat_idx = (np.abs(lat_array - stn_lat)).argmin().values
    init_value = float(ds['lwe_thickness'][0, lat_idx, lon_idx].values)

    for time_index, time_stamp in enumerate(time_array):
        data = ds['lwe_thickness'][time_index, :, :]
        value = data[lat_idx, lon_idx].values
        utc_time = int(time_stamp.astype(int) / 1000000)
        difference_data_value = (value - init_value) * 0.01 * 6371000 * math.radians(0.25) * \
                                6371000 * math.radians(0.25) * abs(math.cos(math.radians(lat_idx))) * 0.000810714
        ts_plot.append([utc_time, round(float(value), 3)])
        ts_plot_int.append([utc_time, round(float(difference_data_value), 3)])

    graph_json["values"] = sorted(ts_plot)
    graph_json["integr_values"] = sorted(ts_plot_int)
    graph_json["point"] = [round(stn_lat, 2), round(stn_lon, 2)]
    graph_json = json.dumps(graph_json)

    return graph_json


def get_region_bounds(region_name):
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), '')
    nc_file = os.path.join(grace_dir, region_name, f'{region_name}_avg_sw.nc')
    ds = xarray.open_dataset(nc_file)
    lat = ds['lat'][:]
    lon = ds['lon'][:]
    minx = float(lon.min())
    miny = float(lat.min())
    maxx = float(lon.max())
    maxy = float(lat.max())
    bbox = [minx, miny, maxx, maxy]
    return bbox


def file_range(region_name, signal_process, storage_type):
    grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), '')
    nc_file = os.path.join(grace_dir, region_name, f'{region_name}_{signal_process}_{storage_type}.nc')
    ds = xarray.open_dataset(nc_file)
    lwe_thickness = ds['lwe_thickness'][:]
    min_val = round(float(lwe_thickness.min()), 2)
    max_val = round(float(lwe_thickness.max()), 2)
    return min_val, max_val
