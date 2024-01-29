from setuptools import setup, find_namespace_packages
from tethys_apps.app_installation import find_resource_files

# -- Apps Definition -- #
app_package = "ggst"
release_package = "tethysapp-" + app_package

# -- Python Dependencies -- #
dependencies = []

# -- Get Resource File -- #
resource_files = find_resource_files(
    "tethysapp/" + app_package + "/templates", "tethysapp/" + app_package
)
resource_files += find_resource_files(
    "tethysapp/" + app_package + "/public", "tethysapp/" + app_package
)
resource_files += find_resource_files(
    "tethysapp/" + app_package + "/workspaces", "tethysapp/" + app_package
)


setup(
    name=release_package,
    version="0.0.1",
    description="Visualize and subset GRACE data",
    long_description="",
    keywords="",
    author="Sarva Pulla, Norm Jones",
    author_email="sarva.pulla@archgeo.co",
    url="",
    license="MIT",
    packages=find_namespace_packages(),
    package_data={"": resource_files},
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies,
)
