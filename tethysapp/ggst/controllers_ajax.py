from .utils import (user_permission_test,
                    process_shapefile)
from django.http import JsonResponse
from django.contrib.auth.decorators import (login_required,
                                            user_passes_test)


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
