.. raw:: html
   :file: translate.html

**Adding and Deleting Regions**
==============================
This section describes how to upload new regions to the GGST app. When a new region is uploaded, it is automatically processed and the storage components including subsetting netCDF files and storage time series are computed for the region and stored with the region for visualization in the app. The new region is added to the list of regions for the app, and it can be selected and viewed. This section also describes how to delete regions and the associated files. 

**Uploading a Region**
-----------------------
The GRACE Groundwater Subsetting Tool web application is hosted on three different Tethys portals:

* **Servir West Africa Portal**: Official Tethys portal hosted by the SERVIR Science Coordination Office (SCO) for the West Africa Hub (https://tethyswa.servirglobal.net/apps/)
* **BYU Main Portal**: A Tethys portal hosted by Brigham Young University for all completed apps (https://tethys.byu.edu).
* **BYU Staging Portal**: A Tethys portal hosted by Brigham Young University for testing new applications or features (https://tethys-staging.byu.edu/apps/).

To upload regions on the application, visit the portal of your choice and log in. Without logging in you can see the App Navigation pages: Home and Global Map. These allow you to view previously uploaded regions and create time series graphics for any singular point on the globe. Once you log in with administrative privileges, you will see the additional Configuration pages: Add a Region, Delete a Region, and Update Global Files. Update Global Files is used to download the latest GRACE and GLDAS files from the NASA server.

To add a new region, first prepare a shapefile for the region consisting of four files: *.shp, *.dbf, *.prj, and *.shx. The projection for the shapefile should be EPSG:4326 - WGS 84. The four files should not be zipped together.

Please refer to the following images as a visual guide:

.. image:: images-upload/uploadregion1.png
   :scale: 60%
 

.. image:: images-upload/uploadregion2.png
   :scale: 60%
   
   
.. image:: images-upload/uploadregion3.png
   :scale: 60%
  
   
.. image:: images-upload/uploadregion4.png
   :scale: 60%
   
   
.. image:: images-upload/uploadregion5.png
   :scale: 60%
  
   
**Deleting a Region**
---------------------
Deleting a region is very simple. Proceed to the Delete a Region page. Select the region from the drop-down menu and hit the delete button. A message will display when the deletion has been completed.

.. image:: images-upload/deleteregion.png
   :scale: 80%
   

