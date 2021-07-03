import os
import json

from django.contrib.auth.decorators import (user_passes_test)
from django.http import JsonResponse

from .utils import (file_range,
                    get_grace_timestep_options,
                    generate_timeseries,
                    get_region_bounds,
                    user_permission_test,
                    process_shapefile,
                    TimeSeries)

from .app import Ggst as app


@user_passes_test(user_permission_test)
def region_add(request):

    if request.is_ajax() and request.method == 'POST':
        # try:
        info = request.POST

        region_name = info.get('region_name')
        region_store = region_name.replace(' ', '_').lower()
        files_list = request.FILES.getlist('shapefile')
        output_dir = process_shapefile(region_store, files_list)
        response = {"success": "success",
                    "output_dir": output_dir}
        return JsonResponse(response)
        # except Exception as e:
        #     return JsonResponse({'error': f'Error processing request: {e}'})


def get_time_step_options(request):
    if request.is_ajax() and request.method == 'POST':
        try:
            return_obj = {}
            info = request.POST
            storage_type = info.get('storage_type')
            layer_options = get_grace_timestep_options(storage_type)
            return_obj['layer_options'] = layer_options
            return_obj['success'] = 'success'
            return JsonResponse(return_obj)
        except Exception as e:
            return JsonResponse({'error': str(e)})


def get_global_plot(request):

    if request.is_ajax() and request.method == 'POST':
        # try:
        return_obj = {}
        info = request.POST
        lon = info.get('lon')
        lat = info.get('lat')
        storage_type = info.get('storage_type')
        print(storage_type, lat, lon)
        grace_dir = os.path.join(app.get_custom_setting("grace_thredds_directory"), '')
        # ds = TimeSeries(storage_type, signal_process, float(lat), float(lon), 'global', grace_dir)
        graph = generate_timeseries(storage_type,
                                    lat,
                                    lon,
                                    'global')
        graph = json.loads(graph)
        return_obj["values"] = graph["values"]
        return_obj["integr_values"] = graph["integr_values"]
        return_obj["error_range"] = graph["error_range"]
        return_obj["location"] = graph["point"]
        return_obj['success'] = "success"

        return JsonResponse(return_obj)
        # except Exception as e:
        #     return JsonResponse({'error': str(e)})


def get_region_plot(request):

    if request.is_ajax() and request.method == 'POST':
        # try:
        return_obj = {}
        info = request.POST
        lon = info.get('lon')
        lat = info.get('lat')
        region = info.get('region')
        storage_type = info.get('storage_type')
        try:

            graph = generate_timeseries(storage_type,
                                        lat,
                                        lon,
                                        region)
            graph = json.loads(graph)
            return_obj["values"] = graph["values"]
            return_obj["integr_values"] = graph["integr_values"]
            return_obj["location"] = graph["point"]
            return_obj['success'] = "success"

            return JsonResponse(return_obj)
        except Exception as e:
            return JsonResponse({'error': f'Error processing request: {e}'})


def get_region_chart(request):
    if request.is_ajax() and request.method == 'POST':
        # try:
        return_obj = {}
        info = request.POST
        region = info.get('region')
        storage_type = info.get('storage_type')
        return JsonResponse(return_obj)


def get_region_center(request):
    if request.is_ajax() and request.method == 'POST':
        try:
            return_obj = {}
            info = request.POST
            region_name = info.get('region')
            bbox = get_region_bounds(region_name)
            lat, lon = (int(bbox[1]) + int(bbox[3])) / 2, (int(bbox[0]) + int(bbox[2])) / 2
            return_obj['lat'] = lat
            return_obj['lon'] = lon
            return_obj['success'] = 'success'
            return JsonResponse(return_obj)
        except Exception as e:
            return JsonResponse({'error': str(e)})


def get_legend_range(request):
    if request.is_ajax() and request.method == 'POST':
        # try:
        return_obj = {}
        info = request.POST
        storage_type = info.get('storage_type')
        region_name = info.get('region_name')
        print(region_name, storage_type)
        range_min, range_max = file_range(region_name, storage_type)
        return_obj['success'] = 'success'
        return_obj['range_min'] = range_min
        return_obj['range_max'] = range_max
        return JsonResponse(return_obj)
        # except Exception as e:
        #     return JsonResponse({'error': str(e)})
