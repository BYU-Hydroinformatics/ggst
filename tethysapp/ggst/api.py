from django.http import JsonResponse, HttpResponse
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
import json
import geopandas as gpd
from shapely.geometry import shape
from .utils import (
    gen_zip_api,
    generate_timeseries,
    process_shapefile,
    storage_options,
    region_api_ts,
)
from tethys_sdk.routing import controller


@api_view(["POST"])
@authentication_classes(
    (
        TokenAuthentication,
        SessionAuthentication,
    )
)
@controller(name="subset-region-zipfile", url="ggst/api/subsetRegionZipfile/")
def subset_region_zip(request):
    if request.method == "POST":
        region_name = None
        info = request.POST
        r_files = request.FILES
        if len(r_files.keys()) == 0:
            return JsonResponse(
                {"error": "No zipfile to process. Please check and try again."}
            )
        if info.get("name"):
            region_name = info.get("name")
        if len(r_files.keys()) > 1:
            return JsonResponse(
                {"error": "Please send only one zipfile and try again."}
            )
        try:
            file_key = list(r_files.keys())[0]
            zip_file = r_files.getlist(file_key)
            shapefile = process_shapefile(region_name, zip_file, "api")
            in_memory_zip = gen_zip_api(shapefile, region_name)
            response = HttpResponse(in_memory_zip.getvalue())
            response["Content-Type"] = "application/x-zip-compressed"
            response["Content-Disposition"] = f"attachment; filename={region_name}.zip"
            return response
        except Exception as e:
            return JsonResponse({"error": f"Error processing request: {e}"})


@api_view(["POST"])
@authentication_classes(
    (
        TokenAuthentication,
        SessionAuthentication,
    )
)
@controller(name="region-zip-timeseries", url="ggst/api/zipRegionTimeseries/")
def region_zip_timeseries(request):
    if request.method == "POST":
        region_name = None
        storage_type = None
        info = request.POST
        r_files = request.FILES
        if len(r_files.keys()) == 0:
            return JsonResponse(
                {"error": "No zipfile to process. Please check and try again."}
            )
        if len(r_files.keys()) > 1:
            return JsonResponse(
                {"error": "Please send only one zipfile and try again."}
            )

        if info.get("name"):
            region_name = info.get("name")
        if info.get("storage_type"):
            storage_type = info.get("storage_type")
        try:
            file_key = list(r_files.keys())[0]
            zip_file = r_files.getlist(file_key)
            json_obj = region_api_ts(region_name, storage_type, zip_file)
            return JsonResponse(json_obj)
        except Exception as e:
            return JsonResponse({"error": f"Error processing request: {e}"})


@api_view(["GET"])
@authentication_classes(
    (
        TokenAuthentication,
        SessionAuthentication,
    )
)
@controller(name="get-region-timeseries", url="ggst/api/getRegionTimeseries/")
def subset_region_api(request):
    json_obj = {}

    if request.method == "GET":
        region_name = None
        geometry = None
        info = request.GET
        if info.get("name"):
            region_name = info.get("name")
        if info.get("geometry"):
            geometry = info.get("geometry")

        try:
            subset_region = json.loads(geometry)
            shapefile = gpd.GeoDataFrame(
                {"geometry": [shape(subset_region)]}, crs="EPSG:4326"
            )
            in_memory_zip = gen_zip_api(shapefile, region_name)
            response = HttpResponse(in_memory_zip.getvalue())
            response["Content-Type"] = "application/x-zip-compressed"
            response["Content-Disposition"] = f"attachment; filename={region_name}.zip"
            return response
        except Exception as e:
            json_obj["error"] = "Error processing request: " + str(e)

            return JsonResponse(json_obj)


@api_view(["GET"])
@controller(name="get-storage-options", url="ggst/api/getStorageOptions/")
def api_get_storage_options(request):
    return_obj = {}

    if request.method == "GET":
        options = storage_options()
        return_obj["storage_options"] = options
        return JsonResponse(return_obj)


@api_view(["GET"])
@controller(name="get-point-values", url="ggst/api/getPointValues/")
def api_get_point_values(request):
    return_obj = {}

    if request.method == "GET":

        lat = None
        lon = None
        storage_type = None

        if request.GET.get("latitude"):
            lat = request.GET["latitude"]
        if request.GET.get("longitude"):
            lon = request.GET["longitude"]
        if request.GET.get("storage_type"):
            storage_type = request.GET["storage_type"]

        try:

            graph = generate_timeseries(storage_type, lat, lon, "global")
            graph = json.loads(graph)
            return_obj["values"] = graph["values"]
            return_obj["error_range"] = graph["error_range"]
            return_obj["integr_values"] = graph["integr_values"]
            return_obj["location"] = graph["point"]
            return_obj["success"] = "success"

            return JsonResponse(return_obj)
        except Exception as e:
            return JsonResponse({"error": f"Error processing request: {e}"})
