from tethys_sdk.base import TethysAppBase
from tethys_sdk.app_settings import (CustomSetting)


class Ggst(TethysAppBase):
    """
    Tethys app class for Grace Groundwater Subsetting Tool.
    """

    name = "Grace Groundwater Subsetting Tool"
    index = "home"
    icon = "ggst/images/logo.jpg"
    package = "ggst"
    root_url = "ggst"
    color = "#222222"
    description = "Visualize and subset Grace data"
    tags = "Remote Sensing"
    enable_feedback = False
    feedback_emails = []

    controller_modules = ['controllers_ajax', "api"]

    def custom_settings(self):
        custom_settings = (
            CustomSetting(
                name="grace_thredds_directory",
                type=CustomSetting.TYPE_STRING,
                description="Full Path to the Thredds GRACE directory ",
                required=True,
            ),
            CustomSetting(
                name="grace_thredds_catalog",
                type=CustomSetting.TYPE_STRING,
                description="Path to the Ground Water Thredds Catalog XML URL",
                required=True,
            ),
            CustomSetting(
                name="global_output_directory",
                type=CustomSetting.TYPE_STRING,
                description="Path to the GRACE data directory",
                required=True,
            ),
            CustomSetting(
                name="earthdata_username",
                type=CustomSetting.TYPE_STRING,
                description="NASA Earth Data username",
                required=True,
            ),
            CustomSetting(
                name="earthdata_pass",
                type=CustomSetting.TYPE_STRING,
                description="NASA Earth Data pass",
                required=True,
            ),
            CustomSetting(
                name="conda_python_path",
                type=CustomSetting.TYPE_STRING,
                description="Path to the tethys conda env path. Output of which python command. ",
            ),
        )
        return custom_settings
