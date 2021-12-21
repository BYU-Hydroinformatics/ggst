from django.http import JsonResponse, HttpResponse
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
import json
import geopandas as gpd
from shapely.geometry import shape
from .utils import gen_zip_api, generate_timeseries


@api_view(["GET"])
@authentication_classes(
    (
        TokenAuthentication,
        SessionAuthentication,
    )
)
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
