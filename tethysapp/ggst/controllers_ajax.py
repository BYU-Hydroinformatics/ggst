import json

from django.contrib.auth.decorators import (user_passes_test)
from django.http import JsonResponse

from .utils import (file_range,
                    generate_timeseries,
                    get_region_bounds,
                    user_permission_test,
                    process_shapefile)


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


def get_global_plot(request):

    if request.is_ajax() and request.method == 'POST':
        # try:
        return_obj = {}
        info = request.POST
        lon = info.get('lon')
        lat = info.get('lat')
        storage_type = info.get('storage_type')
        signal_process = info.get('signal_process')
        print(storage_type, signal_process, lat, lon)
        graph = generate_timeseries(storage_type,
                                    signal_process,
                                    lat,
                                    lon,
                                    'global')
        graph = json.loads(graph)
        return_obj["values"] = graph["values"]
        return_obj["integr_values"] = graph["integr_values"]
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
        signal_process = info.get('signal_process')
        graph = generate_timeseries(storage_type,
                                    signal_process,
                                    lat,
                                    lon,
                                    region)
        graph = json.loads(graph)
        return_obj["values"] = graph["values"]
        return_obj["integr_values"] = graph["integr_values"]
        return_obj["location"] = graph["point"]
        return_obj['success'] = "success"

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
        try:
            return_obj = {}
            info = request.POST
            storage_type = info.get('storage_type')
            signal_process = info.get('signal_process')
            region_name = info.get('region_name')
            range_min, range_max = file_range(region_name, signal_process, storage_type)
            return_obj['success'] = 'success'
            return_obj['range_min'] = range_min
            return_obj['range_max'] = range_max
            return JsonResponse(return_obj)
        except Exception as e:
            return JsonResponse({'error': str(e)})
