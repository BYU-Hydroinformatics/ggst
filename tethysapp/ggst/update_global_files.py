import glob
import itertools
import logging
import math
import os
import os.path
import re
import shutil
import sys
import time
import warnings
from datetime import datetime
from urllib.parse import urlparse

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
import xarray as xr
import dask
from packaging import version
from rasterio.enums import Resampling
from shapely.geometry import mapping
from siphon.http_util import session_manager
from siphon.catalog import TDSCatalog

# pandarallel.initialize()

warnings.simplefilter("ignore")

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger("update_global_files")

GRACE_CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json?echo_collection_id=C2536962485-POCLOUD&page_num=1&page_size=20"
# CLSM variables of interest
CLSM_VARIABLES = [
    "time",
    "lon",
    "lat",
    "SWE_inst",
    "CanopInt_inst",
    "TWS_inst",
    "SoilMoist_P_inst",
]

# NOAH  variables of interest
NOAH_VARIABLES = [
    "time",
    "lon",
    "lat",
    "SWE_inst",
    "CanopInt_inst",
    "SoilMoi0_10cm_inst",
    "SoilMoi10_40cm_inst",
    "SoilMoi40_100cm_inst",
    "SoilMoi100_200cm_inst",
]

# VIC variables of interest
VIC_VARIABLES = [
    "time",
    "lon",
    "lat",
    "SWE_inst",
    "CanopInt_inst",
    "SoilMoi0_30cm_inst",
    "SoilMoi_depth2_inst",
    "SoilMoi_depth3_inst",
]

# Declare TWS variables that need to be summed

CLSM_TWS_VARIABLES = ["SWE_inst", "CanopInt_inst", "SoilMoist_P_inst"]

NOAH_TWS_VARIABLES = [
    "SWE_inst",
    "CanopInt_inst",
    "SoilMoi0_10cm_inst",
    "SoilMoi10_40cm_inst",
    "SoilMoi40_100cm_inst",
    "SoilMoi100_200cm_inst",
]

VIC_TWS_VARIABLES = [
    "SWE_inst",
    "CanopInt_inst",
    "SoilMoi0_30cm_inst",
    "SoilMoi_depth2_inst",
    "SoilMoi_depth3_inst",
]

# Declare Surface Water Variables
CLSM_SW_VARIABLES = ["SWE_inst", "CanopInt_inst"]

NOAH_SW_VARIABLES = ["SWE_inst", "CanopInt_inst"]

VIC_SW_VARIABLES = ["SWE_inst", "CanopInt_inst"]

# Declare Soil Moisture variables
CLSM_SM_VARIABLES = ["SoilMoist_P_inst"]

NOAH_SM_VARIABLES = [
    "SoilMoi0_10cm_inst",
    "SoilMoi10_40cm_inst",
    "SoilMoi40_100cm_inst",
    "SoilMoi100_200cm_inst",
]

VIC_SM_VARIABLES = ["SoilMoi0_30cm_inst", "SoilMoi_depth2_inst", "SoilMoi_depth3_inst"]

# Declare Canopy Variables
CLSM_CANOPY_VARIABLES = ["CanopInt_inst"]

NOAH_CANOPY_VARIABLES = ["CanopInt_inst"]

VIC_CANOPY_VARIABLES = ["CanopInt_inst"]

# Declare Snow Water Equivalent Variables
CLSM_SWE_VARIABLES = ["SWE_inst"]

NOAH_SWE_VARIABLES = ["SWE_inst"]

VIC_SWE_VARIABLES = ["SWE_inst"]

UNIT_FACTORS = {
    "mm": 1000,
    "kg/m2": 1000,
    "kg/m^2": 1000,
    "cm": 100,
    "dm": 10,
    "m": 1,
    "km": 0.001,
    "kg m-2": 1000,
}


def update_url(url):
    parts = urlparse(url)
    updated = parts._replace(path="data" + parts.path)
    return updated.geturl()


def update_grace_url(url):
    parts = urlparse(url)
    updated = parts._replace(path="opendap/hyrax" + parts.path)
    return updated.geturl()


def get_catalog_urls(catalog_name, catalog):
    print(catalog_name, catalog)
    cur_ref = catalog.catalog_refs[catalog_name]
    cur_cat = cur_ref.follow()
    urls = [
        update_url(ds.access_urls["dap"])
        for ref in cur_cat.catalog_refs
        for name, ds in cur_cat.catalog_refs[ref].follow().datasets.items()
        if name[-4:] == ".nc4"
    ]
    return urls


def download_url(row):
    url = row["url"]
    output_dir = row["output_dir"]
    f_name = url.split("/")[-1]
    output_path = os.path.join(output_dir, f_name)
    if not os.path.exists(output_path):
        download_catalog_url(url, output_path)
        return True
    else:
        return False


def download_catalog(ouput_location, model, urls):
    df = pd.DataFrame({"url": urls})
    output_path = os.path.join(ouput_location, model)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    # df['earthdata_username'] = ed_user
    # df['earthdata_pass'] = ed_pass
    df["output_dir"] = output_path
    df["downloaded"] = df.apply(download_url, axis=1)
    return output_path


def get_grace_urls(catalog):
    urls = [
        update_grace_url(ds.access_urls["file"])
        for name, ds in catalog.datasets.items()
        if name[-3:] == ".nc"
    ]
    return urls


def get_version_number(string):
    return float(string.split(".")[-1])


def download_gldas_catalog(gldas_url, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    session_manager.set_session_options(auth=AUTH)
    catalog = TDSCatalog(gldas_url)

    valid_refs = [
        cat
        for cat in catalog.catalog_refs.keys()
        if "10_M" in cat or "NOAH025_M" in cat
        if "EP" not in cat
    ]
    latest_versions = []
    iterator = itertools.groupby(valid_refs, lambda string: string.split("_")[1])

    for element, group in iterator:
        # appending the group by converting it into a list
        cur_list = list(group)
        print(cur_list)
        max_version = max(cur_list, key=get_version_number)
        latest_versions.append(str(max_version))
    url_dict = {ver: get_catalog_urls(ver, catalog) for ver in latest_versions}
    output_paths = [
        download_catalog(output_dir, key, values) for key, values in url_dict.items()
    ]

    return output_paths


def download_catalog_url(final_url, output_path):
    with requests.Session() as session:
        r1 = session.request("get", final_url)
        r = session.get(r1.url, auth=AUTH)
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
                return True


def get_grace_listing_response(listing_url=GRACE_CMR_URL):
    listing_request = requests.get(listing_url)
    listing_response = listing_request.json()
    return listing_response


def get_latest_grace_link(listing_url=GRACE_CMR_URL):
    listing_response = get_grace_listing_response(listing_url)
    download_links = []

    for entry in listing_response["feed"]["entry"]:
        for link in entry["links"]:
            if link["rel"] == "http://esipfed.org/ns/fedsearch/1.1/data#":
                if "GRCTellus" in link["href"]:
                    download_links.append(link["href"])

    most_recent_link = None
    most_recent_date = datetime.min

    for link in download_links:
        # Extracting the date part from the file name
        file_name = link.split("/")[-1]
        parts = file_name.split(".")
        date_part = parts[2]  # '200204_202310'
        end_date_str = date_part.split("_")[1]  # Extracting the second part

        # Convert the date string to datetime object
        date_obj = datetime.strptime(end_date_str, "%Y%m")

        # Compare with the most recent date found so far
        if date_obj > most_recent_date:
            most_recent_date = date_obj
            most_recent_link = link
    return most_recent_link


def get_scale_factors_link(listing_url=GRACE_CMR_URL):
    listing_response = get_grace_listing_response(listing_url)
    download_links = []

    for entry in listing_response["feed"]["entry"]:
        for link in entry["links"]:
            if link["rel"] == "http://esipfed.org/ns/fedsearch/1.1/data#":
                if "SCALE" in link["href"]:
                    download_links.append(link["href"])
    output_link = download_links[0]
    return output_link


def download_grace_file(grace_url, output_dir):
    print("Downloading GRACE")
    latest_grace_link = get_latest_grace_link(grace_url)
    file_list = glob.glob(os.path.join(output_dir, "*200204*"))
    file_name = latest_grace_link.split("/")[-1]
    end_date = re.search(r"200204_\d{6}", file_name).group(0).split("_")[1]
    end_date_obj = datetime.strptime(end_date, "%Y%m")
    output_path = os.path.join(output_dir, file_name)
    if len(file_list) == 0:
        print("downloading at empty")
        download_catalog_url(latest_grace_link, output_path)
    else:
        for _file in file_list:
            old_file = _file.split("/")[-1]
            prev_end_date = re.search(r"200204_\d{6}", old_file).group(0).split("_")[1]
            prev_end_date_obj = datetime.strptime(prev_end_date, "%Y%m")
            if end_date_obj > prev_end_date_obj:
                print("deleting the previous file")
                if os.path.exists(_file):
                    os.remove(_file)
        download_catalog_url(latest_grace_link, output_path)
    return True


def download_grace_sf(output_dir, grace_url):
    sf_output_file = "scale_factors.nc"
    sf_output_path = os.path.join(output_dir, sf_output_file)
    if not os.path.exists(sf_output_path):
        link = get_scale_factors_link(grace_url)
        download_catalog_url(link, sf_output_path)
    return True


def download_grace_catalog(grace_url, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    download_grace_file(grace_url, output_dir)
    download_grace_sf(output_dir, grace_url)
    return True


def gldas_concat_helper(grace_dir, model_dir, model_type, gldas_variables):
    gldas_dir = os.path.join(grace_dir, "gldas")
    nc_files_glob = os.path.join(gldas_dir, model_dir, "*.nc4")
    list_of_files = glob.glob(os.path.join(gldas_dir, model_dir, "*"))
    sorted_files = sorted(
        [
            (
                np.datetime64(
                    datetime.strptime(re.search(r"\d{6}", _file).group(0), "%Y%m")
                ),
                _file,
            )
            for _file in list_of_files
        ]
    )
    timesteps, final_files = map(list, zip(*sorted_files))
    gldas_output_file = os.path.join(grace_dir, f"{model_type}.nc")
    if not os.path.exists(gldas_output_file):
        gldas_ds = xr.open_mfdataset(nc_files_glob, parallel=False).drop_vars(
            "time_bnds"
        )[gldas_variables]
        gldas_ds.to_netcdf(gldas_output_file)
    else:
        gldas_ds = xr.open_dataset(gldas_output_file)
        concat_list = list(
            np.array(final_files)[timesteps > gldas_ds.time.max().values]
        )
        if len(concat_list) > 0:
            gldas_vic_concat = xr.open_mfdataset(concat_list, parallel=True).drop_vars(
                "time_bnds"
            )[gldas_variables]
            final_ds = xr.concat([gldas_ds, gldas_vic_concat], "time")
            # os.remove(gldas_output_file)
            final_ds.to_netcdf(gldas_output_file, mode="w")

    return True


def concatenate_gldas_files(grace_dir):
    gldas_dir = os.path.join(grace_dir, "gldas")
    for model_dir in os.listdir(gldas_dir):
        if "VIC" in model_dir:
            print(model_dir)
            gldas_concat_helper(grace_dir, model_dir, "vic", VIC_VARIABLES)
        if "CLSM" in model_dir:
            print(model_dir)
            gldas_concat_helper(grace_dir, model_dir, "clsm", CLSM_VARIABLES)
        if "NOAH10" in model_dir:
            print(model_dir)
            gldas_concat_helper(grace_dir, model_dir, "noah", NOAH_VARIABLES)
        if "NOAH025" in model_dir:
            print(model_dir)
            gldas_concat_helper(grace_dir, model_dir, "noah025", NOAH_VARIABLES)
    return True


# Calculate Surface Area of Grid Cell
def calculate_surface_area(ds):
    # Find the lon size
    lon_interval_size = ds.variables["lon"][1] - ds.variables["lon"][0]
    # Find the lat size
    lat_interval_size = ds.variables["lat"][1] - ds.variables["lat"][0]
    surface_area_array = np.array(
        [
            6371000
            * math.radians(lat_interval_size)
            * 6371000
            * math.radians(lon_interval_size)
            * math.cos(math.radians(lat))
            for lat in ds.lat.values
        ]
    )
    return surface_area_array


# For a given gldas dataset and surface area data array calculate anomalies for each variable
def calculate_gldas_anomalies(ds, surface_area_da):
    for var in ds.variables:
        if var not in ["lat", "lon", "time", "spatial_ref"]:
            # Calculate variable mean from 2004 to 2009
            var_mean = ds.sel(time=slice("2004-01-01", "2009-12-31")).mean("time")[var]
            var_factor = UNIT_FACTORS[ds[var].units]
            ds[var] = (ds[var] - var_mean) / var_factor * surface_area_da
            ds[var] = ds[var] * 100 / surface_area_da
    return ds


def aggregate_noah025_anomalies(
    gldas_noah_anomalies, noah_variables, variable_name="lwe_thickness"
):
    noah_ds = (
        gldas_noah_anomalies[noah_variables]
        .to_array()
        .sum("variable")
        .to_dataset(name=variable_name)
    )
    # create a new dataset with all the model tws mean values
    # returns a single value at each time step
    model_ds = xr.Dataset(
        {
            "noah": noah_ds[variable_name],
        }
    )
    # create a final netcdf array with the mean and std values
    final_ds = xr.Dataset(
        {
            "lwe_thickness": model_ds.to_array().mean("variable"),
            "uncertainty": model_ds.to_array().std("variable"),
        }
    )
    return final_ds


def generate_noah025_global_files(grace_dir):
    """
    Generate global NOAH 025 files.
    """
    gldas_noah_ds = xr.open_dataset(
        os.path.join(grace_dir, "noah025.nc"), chunks="auto"
    )
    areas = calculate_surface_area(gldas_noah_ds)

    surface_area_da = (
        xr.DataArray(areas, dims=["lat"], coords={"lat": gldas_noah_ds.lat})
        .expand_dims(lon=len(gldas_noah_ds.coords["lon"]))
        .assign_coords(lon=gldas_noah_ds.lon)
        .transpose("lat", "lon")
    )

    gldas_noah_anomalies = calculate_gldas_anomalies(gldas_noah_ds, surface_area_da)

    for variable_type, variables in [
        ("SW", NOAH_SW_VARIABLES),
        ("SM", NOAH_SM_VARIABLES),
        ("SWE", NOAH_SWE_VARIABLES),
        ("CANOPY", NOAH_CANOPY_VARIABLES),
        ("TWS", NOAH_TWS_VARIABLES),
    ]:
        print(f"GLOBAL 025{variable_type}")
        final_ds = aggregate_noah025_anomalies(gldas_noah_anomalies, variables)
        final_ds.load().to_netcdf(
            os.path.join(grace_dir, f"GRC_025{variable_type.lower()}.nc")
        )

    print("Done generating global NOAH 025 files")
    return None


def generate_gldas_global_files(grace_dir):
    def aggregate_gldas_anomalies(
        clsm_variables, noah_variables, vic_variables, variable_name="lwe_thickness"
    ):
        clsm_ds = (
            gldas_clsm_anomalies[clsm_variables]
            .to_array()
            .sum("variable")
            .to_dataset(name=variable_name)
        )
        noah_ds = (
            gldas_noah_anomalies[noah_variables]
            .to_array()
            .sum("variable")
            .to_dataset(name=variable_name)
        )
        vic_ds = (
            gldas_vic_anomalies[vic_variables]
            .to_array()
            .sum("variable")
            .to_dataset(name=variable_name)
        )
        # create a new dataset with all the model tws mean values
        # returns a single value at each time step
        model_ds = xr.Dataset(
            {
                "clsm": clsm_ds[variable_name],
                "noah": noah_ds[variable_name],
                "vic": vic_ds[variable_name],
            }
        )

        # create a final netcdf array with the mean and std values
        final_ds = xr.Dataset(
            {
                "lwe_thickness": model_ds.to_array().mean("variable"),
                "uncertainty": model_ds.to_array().std("variable"),
            }
        )
        return final_ds

    # Load Concatenated GLDAS Model Files
    print("Start GLDAS global file generation")
    gldas_vic_ds = xr.open_dataset(os.path.join(grace_dir, "vic.nc"))
    gldas_clsm_ds = xr.open_dataset(os.path.join(grace_dir, "clsm.nc"))
    gldas_noah_ds = xr.open_dataset(os.path.join(grace_dir, "noah.nc"))

    # GLDAS Grid Cell Area
    areas = calculate_surface_area(gldas_clsm_ds)

    surface_area_da = (
        xr.DataArray(areas, dims=["lat"], coords={"lat": gldas_clsm_ds.lat})
        .expand_dims(lon=len(gldas_clsm_ds.coords["lon"]))
        .assign_coords(lon=gldas_clsm_ds.lon)
        .transpose("lat", "lon")
        #                    .drop('spatial_ref')
    )

    # Calculate Anomalies for each model
    gldas_clsm_anomalies = calculate_gldas_anomalies(gldas_clsm_ds, surface_area_da)
    gldas_noah_anomalies = calculate_gldas_anomalies(gldas_noah_ds, surface_area_da)
    gldas_vic_anomalies = calculate_gldas_anomalies(gldas_vic_ds, surface_area_da)

    print("GLOBAL SW")
    final_sw_ds = aggregate_gldas_anomalies(
        CLSM_SM_VARIABLES, NOAH_SW_VARIABLES, VIC_SW_VARIABLES
    )
    final_sw_ds.to_netcdf(os.path.join(grace_dir, "GRC_sw.nc"))
    print("GLOBAL SM")
    final_sm_ds = aggregate_gldas_anomalies(
        CLSM_SM_VARIABLES, NOAH_SM_VARIABLES, VIC_SM_VARIABLES
    )
    final_sm_ds.to_netcdf(os.path.join(grace_dir, "GRC_sm.nc"))
    print("GLOBAL SWE")
    final_swe_ds = aggregate_gldas_anomalies(
        CLSM_SWE_VARIABLES, NOAH_SWE_VARIABLES, VIC_SWE_VARIABLES
    )
    final_swe_ds.to_netcdf(os.path.join(grace_dir, "GRC_swe.nc"))
    print("GLOBAL CANOPY")
    final_canopy_ds = aggregate_gldas_anomalies(
        CLSM_CANOPY_VARIABLES, NOAH_CANOPY_VARIABLES, VIC_CANOPY_VARIABLES
    )
    final_canopy_ds.to_netcdf(os.path.join(grace_dir, "GRC_canopy.nc"))
    print("GLOBAL TWS")
    final_tws_ds = aggregate_gldas_anomalies(
        CLSM_TWS_VARIABLES, NOAH_TWS_VARIABLES, VIC_TWS_VARIABLES
    )
    final_tws_ds.to_netcdf(os.path.join(grace_dir, "GRC_tws.nc"))
    print("Done generating global gldas files")
    return True


def generate_global_grace_nc(grace_dir):
    print("Generate global grace nc")
    mascon_dir = os.path.join(grace_dir, "mascon")
    grace_file = glob.glob(os.path.join(mascon_dir, "GRC*.nc"))[0]
    scale_factors_file = os.path.join(mascon_dir, "scale_factors.nc")
    sf_ds = xr.open_dataset(scale_factors_file)
    sf_ds = sf_ds.assign({"lon": (((sf_ds.lon + 180) % 360) - 180)}).sortby("lon")
    sf_ds["scale_factor"] = sf_ds["scale_factor"].rio.write_crs("epsg:4326")
    sf_ds.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    grace_ds = xr.open_dataset(grace_file)[["lwe_thickness", "uncertainty"]]
    # Calculate GRACE TWS Anomalies
    # Clipping the grace ds to utah shapefile
    ds = grace_ds.copy()
    ds = ds.assign({"lon": (((ds.lon + 180) % 360) - 180)}).sortby("lon")
    ds["lwe_thickness"] = ds["lwe_thickness"].rio.write_crs("epsg:4326")
    ds["uncertainty"] = ds["uncertainty"].rio.write_crs("epsg:4326")
    ds.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    # Calculate grid cell long term mean
    grid_cell_mean = (
        ds.sel(time=slice("2004-01-01", "2009-12-31")).mean("time").lwe_thickness
    )
    # grace_clipped.sel(time=slice('2004-01-01', '2009-12-31')).mean('time').lwe_thickness
    # Calculate anamolies based on grid cell mean, scale factor and surface area
    gw_wsa_da = (ds.lwe_thickness - grid_cell_mean) * sf_ds.scale_factor
    del ds.uncertainty.attrs["grid_mapping"]
    final_grace_ds = xr.Dataset(
        {"lwe_thickness": gw_wsa_da, "uncertainty": ds.uncertainty}
    )
    final_grace_ds.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    final_grace_ds = final_grace_ds.drop_vars(["WGS84", "spatial_ref"])
    final_grace_ds.to_netcdf(os.path.join(grace_dir, "GRC_grace.nc"))
    return True


def generate_global_gw_nc(grace_dir):
    print("Global grace gw")
    global_grace_file = os.path.join(grace_dir, "GRC_grace.nc")
    grace_ds = xr.open_dataset(global_grace_file)
    grace_ds.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    grace_ds.rio.write_crs("epsg:4326", inplace=True)
    grace_ds["lwe_thickness"] = grace_ds["lwe_thickness"].rio.write_crs("epsg:4326")
    grace_ds["uncertainty"] = grace_ds["uncertainty"].rio.write_crs("epsg:4326")
    new_width = int(grace_ds.rio.width * 0.5)
    new_height = int(grace_ds.rio.height * 0.5)
    ds_sampled = grace_ds.rio.reproject(
        grace_ds.rio.crs,
        shape=(new_height, new_width),
        resampling=Resampling.average,
    )
    ds_sampled = ds_sampled.reindex(y=ds_sampled.y[::-1]).rename(
        {"y": "lat", "x": "lon"}
    )
    resampled_ds = ds_sampled.sel(lat=slice(-59.5, 89.5))
    monthly_mean = (
        resampled_ds.resample(time="1M").mean().dropna("time", "all").drop(["WGS84"])
    )
    time_df = monthly_mean["time"].to_dataframe().reset_index(drop=True)
    time_df["converted"] = time_df["time"].apply(
        lambda x: x.to_pydatetime().replace(day=1, hour=0)
    )
    monthly_mean["time"] = time_df["converted"].values

    tws_ds = xr.open_dataset(os.path.join(grace_dir, "GRC_tws.nc"))
    gw_da = monthly_mean.lwe_thickness - tws_ds.lwe_thickness

    swe_ds = xr.open_dataset(os.path.join(grace_dir, "GRC_swe.nc"))
    canopy_ds = xr.open_dataset(os.path.join(grace_dir, "GRC_canopy.nc"))
    sm_ds = xr.open_dataset(os.path.join(grace_dir, "GRC_sm.nc"))
    gw_uncertainty_da = np.sqrt(
        np.abs(
            monthly_mean.uncertainty**2
            - swe_ds.uncertainty**2
            - canopy_ds.uncertainty**2
            - sm_ds.uncertainty**2
        )
    )
    gw_ds = xr.Dataset({"lwe_thickness": gw_da, "uncertainty": gw_uncertainty_da})
    gw_ds.to_netcdf(os.path.join(grace_dir, "GRC_gw.nc"))
    return True


def generate_global_025gw_nc(grace_dir):
    print("Global grace gw")
    global_grace_file = os.path.join(grace_dir, "GRC_grace.nc")
    grace_ds = xr.open_dataset(global_grace_file)
    grace_ds.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    grace_ds.rio.write_crs("epsg:4326", inplace=True)
    grace_ds["lwe_thickness"] = grace_ds["lwe_thickness"].rio.write_crs("epsg:4326")
    grace_ds["uncertainty"] = grace_ds["uncertainty"].rio.write_crs("epsg:4326")

    new_width = int(grace_ds.rio.width / 0.5)
    new_height = int(grace_ds.rio.height / 0.5)
    ds_sampled = grace_ds.rio.reproject(
        grace_ds.rio.crs,
        shape=(new_height, new_width),
        resampling=Resampling.average,
    )
    ds_sampled = ds_sampled.reindex(y=ds_sampled.y[::-1]).rename(
        {"y": "lat", "x": "lon"}
    )

    resampled_ds = ds_sampled.sel(lat=slice(-59.5, 89.5))
    monthly_mean = (
        resampled_ds.resample(time="1M").mean().dropna("time", "all").drop(["WGS84"])
    )
    time_df = monthly_mean["time"].to_dataframe().reset_index(drop=True)
    time_df["converted"] = time_df["time"].apply(
        lambda x: x.to_pydatetime().replace(day=1, hour=0)
    )
    monthly_mean["time"] = time_df["converted"].values

    tws_ds = xr.open_dataset(os.path.join(grace_dir, "GRC_025tws.nc"))
    gw_da = monthly_mean.lwe_thickness - tws_ds.lwe_thickness

    swe_ds = xr.open_dataset(os.path.join(grace_dir, "GRC_025swe.nc"))
    canopy_ds = xr.open_dataset(os.path.join(grace_dir, "GRC_025canopy.nc"))
    sm_ds = xr.open_dataset(os.path.join(grace_dir, "GRC_025sm.nc"))
    gw_uncertainty_da = np.sqrt(
        np.abs(
            monthly_mean.uncertainty**2
            - swe_ds.uncertainty**2
            - canopy_ds.uncertainty**2
            - sm_ds.uncertainty**2
        )
    )
    gw_ds = xr.Dataset({"lwe_thickness": gw_da, "uncertainty": gw_uncertainty_da})
    gw_ds.to_netcdf(os.path.join(grace_dir, "GRC_025gw.nc"))
    return True


def generate_grace_global_files(grace_dir):
    generate_global_grace_nc(grace_dir)
    generate_global_gw_nc(grace_dir)
    #generate_global_025gw_nc(grace_dir)
    return True


def clip_global_nc(
    nc_file: str, gdf: gpd.GeoDataFrame, region_name: str, grace_dir: str
) -> str:
    # print(region_name)
    ds = xr.open_dataset(nc_file)
    if "spatial_ref" in ds.variables:
        ds = ds.drop_sel("spatial_ref")
    ds["lwe_thickness"] = ds["lwe_thickness"].rio.write_crs("epsg:4326")
    ds["uncertainty"] = ds["uncertainty"].rio.write_crs("epsg:4326")
    if "grid_mapping" in ds.uncertainty.attrs:
        del ds.uncertainty.attrs["grid_mapping"]
    ds.rio.set_spatial_dims(x_dim="lon", y_dim="lat", inplace=True)
    clipped = ds.rio.clip(
        gdf.geometry.apply(mapping), gdf.crs, all_touched=True, drop=True
    )
    if "spatial_ref" in ds.variables:
        clipped = clipped.drop("spatial_ref")
    if "WGS84" in ds.variables:
        clipped = clipped.drop("WGS84")

    output_path = os.path.join(
        grace_dir, region_name, f"{region_name}{nc_file.split('/')[-1][3:]}"
    )
    clipped.to_netcdf(
        output_path,
        encoding={"lwe_thickness": {"_FillValue": -99999.0, "missing_value": -99999.0}},
    )
    return output_path


def process_global_files(grace_dir, thredds_dir):
    start_time = time.time()
    gldas_dir = os.path.join(grace_dir, "gldas")
    mascon_dir = os.path.join(grace_dir, "mascon")
    download_gldas_catalog(
        "https://hydro1.gesdisc.eosdis.nasa.gov/opendap/GLDAS/catalog.xml", gldas_dir
    )
    download_grace_catalog(
        GRACE_CMR_URL,
        mascon_dir,
    )
    #
    concatenate_gldas_files(grace_dir)
    generate_gldas_global_files(grace_dir)
    #generate_noah025_global_files(grace_dir)
    generate_grace_global_files(grace_dir)
    grc_files = glob.glob(os.path.join(grace_dir, "GRC_*.nc"))
    [shutil.copy(_file, thredds_dir) for _file in grc_files]
    [
        clip_global_nc(
            _file,
            gpd.read_file(os.path.join(_dir.path, "shape.geojson")),
            _dir.name,
            thredds_dir,
        )
        for _file in glob.glob(os.path.join(thredds_dir, "*.nc"))
        for _dir in os.scandir(thredds_dir)
        if _dir.is_dir()
    ]
    print("Done processing...")
    end_time = time.time()
    total_time = (end_time - start_time) / 60
    print(total_time)
    return


if __name__ == "__main__":
    grace_output_dir = sys.argv[1]
    grace_thredds_dir = sys.argv[2]
    earthdata_username = sys.argv[3]
    earthdata_pass = sys.argv[4]
    SESSION = requests.session()
    AUTH = (earthdata_username, earthdata_pass)

    print(grace_output_dir, grace_thredds_dir, earthdata_username, earthdata_pass)
    process_global_files(grace_output_dir, grace_thredds_dir)
