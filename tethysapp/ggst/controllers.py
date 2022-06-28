from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, reverse, redirect
from tethys_sdk.gizmos import TextInput, Button
from tethys_sdk.routing import controller

from .app import Ggst as app
from .utils import (
    get_catalog_url,
    get_layer_select,
    get_region_select,
    get_region_bounds,
    get_signal_process_select,
    get_symbology_select,
    get_storage_type_select,
    user_permission_test,
)

job_manager = app.get_job_manager()


@controller
def home(request):
    """
    Controller for the app home page.
    """
    region_select = get_region_select()
    num_regions = len(region_select.options)
    context = {"region_select": region_select, "num_regions": num_regions}

    return render(request, "ggst/home.html", context)


@controller(
    name='global-map',
    url='ggst/global-map',
)
def global_map(request):
    """
    Controller for the Global Map page.
    """
    layer_select = get_layer_select("tws")
    storage_type_select = get_storage_type_select()
    symbology_select = get_symbology_select()
    catalog_url = get_catalog_url()
    wms_url = catalog_url.replace("catalog.xml", "").replace("catalog", "wms")
    context = {
        "layer_select": layer_select,
        "storage_type_select": storage_type_select,
        "style_select": symbology_select,
        "wms_url": wms_url,
    }

    return render(request, "ggst/global_map.html", context)


@controller(
    name='region-map',
    url='ggst/region-map',
)
def region_map(request):
    """
    Controller for the Region Map home page.
    """
    info = request.GET

    region_name = info.get("region-select")
    region_select = get_region_select()
    layer_select = get_layer_select("tws")
    signal_process_select = get_signal_process_select()
    storage_type_select = get_storage_type_select()
    symbology_select = get_symbology_select()
    catalog_url = get_catalog_url()
    wms_url = catalog_url.replace("catalog.xml", "").replace("catalog", "wms")
    bbox = get_region_bounds(region_name)
    lat, lon = (int(bbox[1]) + int(bbox[3])) / 2, (int(bbox[0]) + int(bbox[2])) / 2

    context = {
        "region_name": region_name,
        "region_select": region_select,
        "map_lat": lat,
        "map_lon": lon,
        "layer_select": layer_select,
        "signal_process_select": signal_process_select,
        "storage_type_select": storage_type_select,
        "style_select": symbology_select,
        "wms_url": wms_url,
    }

    return render(request, "ggst/region_map.html", context)


@user_passes_test(user_permission_test)
@controller(
    name='add-region',
    url='ggst/add-region',
)
def add_region(request):

    region_name_input = TextInput(
        display_text="Region Display Name",
        name="region-name-input",
        placeholder="e.g.: Utah",
        icon_append="bi bi-house-door",
    )  # Input for the Region Display Name

    add_button = Button(
        display_text="Add Region",
        icon="bi bi-plus",
        style="success",
        name="submit-add-region",
        attributes={"id": "submit-add-region"},
    )  # Add region button

    context = {"region_name_input": region_name_input, "add_button": add_button}

    return render(request, "ggst/add_region.html", context)


@user_passes_test(user_permission_test)
@controller(
    name='delete-region',
    url='ggst/delete-region',
)
def delete_region(request):

    region_select = get_region_select()
    num_regions = len(region_select.options)

    delete_button = Button(
        display_text="Delete Region",
        icon="bi bi-dash",
        style="danger",
        name="submit-delete-region",
        attributes={"id": "submit-delete-region"},
    )  # Delete region button

    context = {
        "region_select": region_select,
        "num_regions": num_regions,
        "delete_button": delete_button,
    }

    return render(request, "ggst/delete_region.html", context)


@controller(
    name='update-global-files',
    url='ggst/update-global-files',
)
def update_global_files(request):
    """
    Controller for the Update Global Files page.
    """
    update_button = Button(
        display_text="Update Files",
        icon="bi bi-plus",
        style="success",
        name="submit-update-files",
        attributes={"id": "submit-update-files"},
        # href=reverse('ggst:run-dask', kwargs={'job_type': 'distributed'})
    )  # Update files button
    context = {"update_button": update_button}

    return render(request, "ggst/update_global_files.html", context)


@user_passes_test(user_permission_test)
def error_message(request):
    messages.add_message(request, messages.ERROR, "Invalid Scheduler!")
    return redirect(reverse("ggst:home"))
