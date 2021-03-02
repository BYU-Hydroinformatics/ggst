from django.http import JsonResponse, HttpResponse
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
import json
import geopandas as gpd
from shapely.geometry import shape
from .utils import gen_zip_api


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication,))
def subset_region_api(request):
    json_obj = {}

    if request.method == 'GET':
        region_name = None
        geometry = None
        info = request.GET
        if info.get('name'):
            region_name = info.get('name')
        if info.get('geometry'):
            geometry = info.get('geometry')

        try:
            subset_region = json.loads(geometry)
            shapefile = gpd.GeoDataFrame({'geometry': [shape(subset_region)]}, crs='EPSG:4326')
            in_memory_zip = gen_zip_api(shapefile, region_name)
            response = HttpResponse(in_memory_zip.getvalue())
            response['Content-Type'] = 'application/x-zip-compressed'
            response['Content-Disposition'] = f'attachment; filename={region_name}.zip'
            return response
        except Exception as e:
            json_obj['error'] = "Error processing request: "+str(e)

            return JsonResponse(json_obj)
