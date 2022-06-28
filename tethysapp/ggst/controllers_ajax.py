import json

from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse, HttpResponseRedirect
from tethys_sdk.routing import controller

from .utils import (
    delete_region_dir,
    file_range,
    get_grace_timestep_options,
    generate_timeseries,
    get_region_bounds,
    user_permission_test,
    process_shapefile,
    trigger_global_process,
    get_regional_ts,
    get_geojson,
)


@user_passes_test(user_permission_test)
@controller(
    name='add-region-submit',
    url='ggst/add-region/submit',
)
def region_add(request):

    if request.is_ajax() and request.method == "POST":
        try:
            info = request.POST

            region_name = info.get("region_name")
            region_store = region_name.replace(" ", "_").lower()
            files_list = request.FILES.getlist("shapefile")
            output_dir = process_shapefile(region_store, files_list, "interface")
            response = {"success": "success", "output_dir": output_dir}
            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({"error": f"Error processing request: {e}"})


@user_passes_test(user_permission_test)
@controller(
    name='submit-delete-region',
    url='ggst/delete-region/delete',
)
def region_delete(request):

    if request.is_ajax() and request.method == "POST":
        try:
            info = request.POST

            region_name = info.get("region_name")
            dir_deleted = delete_region_dir(region_name)
            if dir_deleted:
                response = {"success": "success"}
                return JsonResponse(response)
            else:
                return JsonResponse({"error": "Failed to delete directory."})
        except Exception as e:
            return JsonResponse({"error": f"Error processing request: {e}"})


@user_passes_test(user_permission_test)
@controller(
    name='update-global-files-trigger',
    url='ggst/update-global-files/update',
)
def global_files_update(request):
    if request.is_ajax() and request.method == "POST":
        trigger_global_process()
        return HttpResponseRedirect("../")


@controller(
    name='map_time_step',
    url='ggst/{map_type}/timestep',
)
def get_time_step_options(request, map_type):
    if request.is_ajax() and request.method == "POST":
        try:
            return_obj = {}
            info = request.POST
            storage_type = info.get("storage_type")
            layer_options = get_grace_timestep_options(storage_type)
            return_obj["layer_options"] = layer_options
            return_obj["success"] = "success"
            return JsonResponse(return_obj)
        except Exception as e:
            return JsonResponse({"error": str(e)})


@controller(
    name='global-map-ts',
    url='ggst/global-map/get-plot-global',
)
def get_global_plot(request):

    if request.is_ajax() and request.method == "POST":
        try:
            return_obj = {}
            info = request.POST
            lon = info.get("lon")
            lat = info.get("lat")
            storage_type = info.get("storage_type")
            graph = generate_timeseries(storage_type, lat, lon, "global")
            graph = json.loads(graph)
            return_obj["values"] = graph["values"]
            return_obj["integr_values"] = graph["integr_values"]
            return_obj["error_range"] = graph["error_range"]
            return_obj["location"] = graph["point"]
            return_obj["success"] = "success"

            return JsonResponse(return_obj)
        except Exception as e:
            return JsonResponse({"error": str(e)})


@controller(
    name='region-map-plot',
    url='ggst/region-map/get-plot-region',
)
def get_region_plot(request):

    if request.is_ajax() and request.method == "POST":
        # try:
        return_obj = {}
        info = request.POST
        lon = info.get("lon")
        lat = info.get("lat")
        region = info.get("region")
        storage_type = info.get("storage_type")
        try:

            graph = generate_timeseries(storage_type, lat, lon, region)
            graph = json.loads(graph)
            return_obj["values"] = graph["values"]
            return_obj["error_range"] = graph["error_range"]
            return_obj["integr_values"] = graph["integr_values"]
            return_obj["location"] = graph["point"]
            return_obj["success"] = "success"

            return JsonResponse(return_obj)
        except Exception as e:
            return JsonResponse({"error": f"Error processing request: {e}"})


@controller(
    name='regional_time_series',
    url='ggst/region-map/get-region-summary',
)
def get_region_chart(request):
    if request.is_ajax() and request.method == "POST":
        try:
            return_obj = {}
            info = request.POST
            region = info.get("region")
            storage_type = info.get("storage_type")
            graph = get_regional_ts(region, storage_type)
            # return_obj["values"] = graph["values"]
            graph = json.loads(graph)
            return_obj["area"] = graph["area"]
            return_obj["values"] = graph["values"]
            return_obj["integr_values"] = graph["integr_values"]
            return_obj["error_range"] = graph["error_range"]
            return_obj["success"] = "success"
            return JsonResponse(return_obj)
        except Exception as e:
            return JsonResponse({"error": f"Error processing request: {e}"})


@controller(
    name='region-map-center',
    url='ggst/region-map/map-center',
)
def get_region_center(request):
    if request.is_ajax() and request.method == "POST":
        try:
            return_obj = {}
            info = request.POST
            region_name = info.get("region")
            bbox = get_region_bounds(region_name)
            lat, lon = (int(bbox[1]) + int(bbox[3])) / 2, (
                int(bbox[0]) + int(bbox[2])
            ) / 2
            return_obj["lat"] = lat
            return_obj["lon"] = lon
            return_obj["success"] = "success"
            return JsonResponse(return_obj)
        except Exception as e:
            return JsonResponse({"error": str(e)})


@controller(
    name='region-map-range',
    url='ggst/region-map/range',
)
def get_legend_range(request):
    if request.is_ajax() and request.method == "POST":
        try:
            return_obj = {}
            info = request.POST
            storage_type = info.get("storage_type")
            region_name = info.get("region_name")
            range_min, range_max = file_range(region_name, storage_type)
            return_obj["success"] = "success"
            return_obj["range_min"] = range_min
            return_obj["range_max"] = range_max
            return JsonResponse(return_obj)
        except Exception as e:
            return JsonResponse({"error": str(e)})


@controller(
    name='region_geojson',
    url='ggst/region-map/geojson',
)
def get_region_geojson(request):
    if request.is_ajax() and request.method == "POST":
        try:
            return_obj = {}
            info = request.POST
            region_name = info.get("region")
            geojson_obj = get_geojson(region_name)
            return_obj["geojson"] = json.loads(geojson_obj)
            return_obj["success"] = "success"
            return JsonResponse(return_obj)
        except Exception as e:
            return JsonResponse({"error": str(e)})
