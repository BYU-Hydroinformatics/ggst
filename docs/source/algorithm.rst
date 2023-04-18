Computational Algorithm
====
The GRACE Groundwater Subsetting Tool Web Application relies on the Earth Observation data collected by NASA through satellites- the latter map the gravitational field of the Earth. Changes in gravity are driven by changes in water storage; offering a rare opportunity to monitor groundwater level through satellites coupled with estimated model surface water.

Collecting data using the satellites began in March 2012. They are launched into an orbit, trailing each other; approximately 137 miles apart. When these satellites are over locations with higher mass concentrations, there is a larger gravitational pull on the lead satellite, pulling it lower than the second satellite, which will also receive a larger pull when it is directly over the same area. These movements- ups and downs- change the distance between the two spacecraft. 

To accurately measure the distance between the two satellites, each is equipped with a k-band microwave whose accuracy is within 10 microns. This has an advantage of quantifying the gravitational anomalies at the locations where the satellites were pulled- this results in a gravitational anomaly map. 

These anomalies are primarily caused by change in water storage. This raw data is then recorded and processed to monitor changes in water resources with a near complete spatial coverage. Hydrologists can also use this data to predict trends in underground water; albeit limitations due to resolution of data and uncertainty.

Derivation of Groundwater Dataset
====
The groundwater component of the GRACE raw data can be separated using a mass balance approach, using the NASA’s Global Land Data Assimilation System (GLDAS) models to compute the surface water component of the data.  To compute the surface water storage, researchers sum the components of the GLDAS models that represent surface water storage and subtract this total from the GRACE  dataset to estimate a groundwater storage anomaly dataset. The latter has a nominal resolution of 3 degree latitude by 3 degrees longitude, which is rescaled down to 0.5 degree using scaling factors by redistributing mass changes from the 3 degrees to 0.5 degree.

This application uses four sets of data;

* The GRACE TWSa dataset
* The GLDAS canopy storage dataset (CAN)
* The GLDAS snow water equivalent (SWE) and
* The GLDAS soil moisture (SM)
To compute the groundwater storage anomaly (GWa), we use three components of the GLDAS models: SWE, CAN, and SM. We convert each GLDAS component to an anomaly format by subtracting the mean centered on values from 2004 to 2009 and then average across the three GLDAS models to produce a component anomaly dataset: SWEa, CANa, and SMa. We use the standard deviation from the three GLDAS models to help estimate uncertainty. 

We download GLDAS files, format them as netCDFs and store them locally. Normally the data is grids with a 1 degree latitude by 1 degree longitude resolution; which we then convert to a 0.5 degree resolution. This conversion is performed by an area-weighted average of the four GRACE grid cells coincident with each GLDAS grid cell.

The converted files are used to compute the groundwater anomaly using a mass balance approach. It is the difference between the TWSa and the sum of the surface water components anomalies.

GWa = TWSa – (SWEa + CANa + SMa)                                                              (1)

The result is then the Ground Water storage anomaly, a tested and approved method to predict long term changes in groundwater storage. 

Grid subsetting
====
For the regional subsetting, the user provides a shapefile which defines the boundary of the region of interest. We then select the cells which have cell centers within the defined boundary and calculate the average storage anomaly for each of the components: TWSa, SWEa, CANa, and SMa resulting in a time series from 2002 to the present for each component on a monthly time step. The figure below shows the Chad Basin in Niger subsetted and displayed with the region shapefile. For water storage, the average of each component is multiplied by the area of the region, resulting in volume anomalies.



Uncertainty Estimates
=====
It is critical to understand that the results of these predictions have uncertainties and limitations. 

To compute the uncertainty of the groundwater storage component, we combine the uncertainty estimates from both the GRACE and GLDAS by computing the square root of the sum of the squares of the uncertainty of the individual components as measured by their standard deviations.

                             (2)

The limitations that arise from this data is that it is not suitable to use for placement of wells; rather for an estimate in general trends in groundwater storage.

Storage Depletion Curve
=====
The GGST offers an option of viewing time series data in the format of a storage depletion curve, which is the time-integral of the storage anomaly.

The storage depletion curve presents cumulative changes in water component storage relative to levels when the GRACE missions began distributing data in April 2002. The storage depletion curve is used in groundwater management since it offers a simple visualization on how much storage aquifers have gained or lost since a given point in time.

To compute the depletion, We sum the GWSa over time to determine changes in groundwater storage volume over time for the region. These data show if a region is depleting storage in the region, or if groundwater is recharging in the region thereby providing valuable information relative to groundwater sustainability.

Here is an illustration on the Northern Africa and the Arabian Peninsula from 2002 - 2021. It show that the groundwater in that region has been depleting since the early 2009 and onward.
 

Limitations
=====
GRACE comes with limitations that users need to know and understand. The data are at a relatively small resolution, 1 degree latitude by 1 degree longitude, representing a 100 x 100 km approximately. At such a low resolution, basing decisions on a single cell comes with high and unknown uncertainties as GRACE data is at a coarser resolution -3 degrees latitude by 3 degrees longitude- which is then processed to higher resolutions TWSa data.

Even with these limitations, these data provide valuable insights into aquifers such as regions that are depleting, recharging, hence allowing managers to sustainably use their groundwater resources. The best use of the GGST is to draw general trends in aquifers rather than selecting a placement of a well.

It is also recommended that, whenever possible, these data be validated with local data where possible. GGST displays the uncertainties in the data calculations as error bands on time series, providing context on regions and different time periods.

Software Availability
=====
The GGST web application was created using Tethys Platform, developed in our hydroinformatics laboratory. It can be accessed on a Tethys portal hosted at Brigham Young University by browsing to this link and selecting the Grace Groundwater Subsetting Tool application.
