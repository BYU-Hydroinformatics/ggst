from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import PersistentStoreDatabaseSetting, PersistentStoreConnectionSetting, CustomSetting


class Ggst(TethysAppBase):
    """
    Tethys app class for Grace Groundwater Subsetting Tool.
    """

    name = 'Grace Groundwater Subsetting Tool'
    index = 'ggst:home'
    icon = 'ggst/images/logo.jpg'
    package = 'ggst'
    root_url = 'ggst'
    color = '#222222'
    description = 'Visualize and subset Grace data'
    tags = 'Remote Sensing'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='ggst',
                controller='ggst.controllers.home'
            ),
            UrlMap(
                name='global-map',
                url='ggst/global-map',
                controller='ggst.controllers.global_map'
            ),
            UrlMap(
                name='global-map-ts',
                url='ggst/global-map/get-plot-global',
                controller='ggst.controllers_ajax.get_global_plot'
            ),
            UrlMap(
                name='region-map',
                url='ggst/region-map',
                controller='ggst.controllers.region_map'
            ),
            UrlMap(
                name='region-map-plot',
                url='ggst/region-map/get-plot-region',
                controller='ggst.controllers_ajax.get_region_plot'
            ),
            UrlMap(
                name='region-map-center',
                url='ggst/region-map/map-center',
                controller='ggst.controllers_ajax.get_region_center'
            ),
            UrlMap(
                name='region-map-range',
                url='ggst/region-map/range',
                controller='ggst.controllers_ajax.get_legend_range'
            ),
            UrlMap(
                name='add-region',
                url='ggst/add-region',
                controller='ggst.controllers.add_region'
            ),
            UrlMap(
                name='add-region-submit',
                url='ggst/add-region/submit',
                controller='ggst.controllers_ajax.region_add'
            ),
            UrlMap(
                name='subset_region',
                url='ggst/api/subset_region',
                controller='ggst.api.subset_region_api'
            ),
            UrlMap(
                name='global_time_step',
                url='ggst/global-map/timestep',
                controller='ggst.controllers_ajax.get_time_step_options'
            ),
            UrlMap(
                name='region_time_step',
                url='ggst/region-map/timestep',
                controller='ggst.controllers_ajax.get_time_step_options'
            ),
            UrlMap(
                name='regional_time_series',
                url='ggst/region-map/get-region-summary',
                controller='ggst.controllers_ajax.get_region_chart'
            )
        )

        return url_maps

    def custom_settings(self):
        custom_settings = (
            CustomSetting(
                name='grace_thredds_directory',
                type=CustomSetting.TYPE_STRING,
                description='Full Path to the Thredds GRACE directory ',
                required=True,
            ),
            CustomSetting(
                name='grace_thredds_catalog',
                type=CustomSetting.TYPE_STRING,
                description='Path to the Ground Water Thredds Catalog XML URL',
                required=True,
            ),
        )
        return custom_settings
