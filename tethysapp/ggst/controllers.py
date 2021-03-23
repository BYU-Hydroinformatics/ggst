from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from tethys_sdk.gizmos import (TextInput,
                               Button)

from .utils import (get_catalog_url,
                    get_layer_select,
                    get_region_select,
                    get_region_bounds,
                    get_signal_process_select,
                    get_symbology_select,
                    get_storage_type_select,
                    get_timeseries_select,
                    user_permission_test)


def home(request):
    """
    Controller for the app home page.
    """
    region_select = get_region_select()
    context = {
        'region_select': region_select
    }

    return render(request, 'ggst/home.html', context)


def global_map(request):
    """
    Controller for the Global Map page.
    """
    layer_select = get_layer_select()
    signal_process_select = get_signal_process_select()
    storage_type_select = get_storage_type_select()
    symbology_select = get_symbology_select()
    catalog_url = get_catalog_url()
    wms_url = catalog_url.replace('catalog.xml', '').replace('catalog', 'wms')
    context = {
        'layer_select': layer_select,
        'signal_process_select': signal_process_select,
        'storage_type_select': storage_type_select,
        'style_select': symbology_select,
        'wms_url': wms_url
    }

    return render(request, 'ggst/global_map.html', context)


def region_map(request):
    """
    Controller for the Region Map home page.
    """
    info = request.GET

    region_name = info.get('region-select')
    region_select = get_region_select()
    layer_select = get_layer_select()
    ts_select = get_timeseries_select()
    signal_process_select = get_signal_process_select()
    storage_type_select = get_storage_type_select()
    symbology_select = get_symbology_select()
    catalog_url = get_catalog_url()
    wms_url = catalog_url.replace('catalog.xml', '').replace('catalog', 'wms')
    bbox = get_region_bounds(region_name)
    lat, lon = (int(bbox[1]) + int(bbox[3])) / 2, (int(bbox[0]) + int(bbox[2])) / 2

    context = {'region_name': region_name,
               'region_select': region_select,
               'ts_select': ts_select,
               'map_lat': lat,
               'map_lon': lon,
               'layer_select': layer_select,
               'signal_process_select': signal_process_select,
               'storage_type_select': storage_type_select,
               'style_select': symbology_select,
               'wms_url': wms_url
               }

    return render(request, 'ggst/region_map.html', context)


@user_passes_test(user_permission_test)
def add_region(request):

    region_name_input = TextInput(display_text='Region Display Name',
                                  name='region-name-input',
                                  placeholder='e.g.: Utah',
                                  icon_append='glyphicon glyphicon-home',
                                  )  # Input for the Region Display Name

    add_button = Button(display_text='Add Region',
                        icon='glyphicon glyphicon-plus',
                        style='success',
                        name='submit-add-region',
                        attributes={'id': 'submit-add-region'}, )  # Add region button

    context = {"region_name_input": region_name_input,  "add_button": add_button}

    return render(request, 'ggst/add_region.html', context)
