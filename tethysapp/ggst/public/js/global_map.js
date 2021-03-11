/*****************************************************************************
 * FILE:    GGST Global Map
 * DATE:    1 March 2021
 * AUTHOR: Sarva Pulla
 * COPYRIGHT: (c) Brigham Young University 2021
 * LICENSE: BSD 2-Clause
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var LIBRARY_OBJECT = (function() {
    // Wrap the library in a package function
    "use strict"; // And enable strict mode for this library

    /************************************************************************
     *                      MODULE LEVEL / GLOBAL VARIABLES
     *************************************************************************/
    var contourGroup,
        contourLayer,
        contourTimeLayer,
        drawnItems,
        graceGroup,
        globalCoords,
        interaction_type,
        layer_control,
        map,
        mychart,
        overlay_maps,
        public_interface,
        $selectSignalProcess,
        $selectStorageType,
        $selectLayer,
        $selectStyle,
        tdWmsLayer,
        wms_url,
        wmsLayer,
        wms_legend;



    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/

    var add_wms,
        get_dropdown_vals,
        get_ts,
        init_all,
        init_jquery,
        init_map,
        original_map_chart,
        reset_alert,
        resize_map_chart,
        updateChart;


    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/

    init_jquery = function(){
        $selectSignalProcess = $("#select-signal-process");
        $selectLayer = $("#select-layer");
        $selectStorageType = $("#select-storage-type");
        wms_url = $("#map-info").attr("wms-url");
    };

    resize_map_chart = function(){
        $('#chart').addClass('partial-chart');
        $('#chart').removeClass('full-chart');
        $('#map').removeClass('full-map');
        $('#map').addClass('partial-map');
    };

    original_map_chart = function(){
        $('#chart').removeClass('partial-chart');
        $('#chart').addClass('full-chart');
        $('#map').addClass('full-map');
        $('#map').removeClass('partial-map');
    };
    //Reset the alerts if everything is going well
    reset_alert = function(){
        $("#message").addClass('hidden');
        $("#message").empty()
            .addClass('hidden')
            .removeClass('alert-success')
            .removeClass('alert-info')
            .removeClass('alert-warning')
            .removeClass('alert-danger');
    };

    init_map = function() {
        map = L.map('map', {
            zoom: 3,
            center: [0, 0],
            // crs: L.CRS.EPSG3857
        });

        // L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        //     // maxZoom: 10,
        //     attribution:
        //         '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        // }).addTo(map);
        wms_legend = L.control({
            position: 'bottomright'
        });
        var Esri_WorldStreetMap = L.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
            {
                attribution:
                    'Tiles &copy; Esri 2012 <a href="https://leaflet-extras.github.io/leaflet-providers/preview/">See Here</a>'
            }
        )

        var Esri_WorldImagery = L.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            {
                attribution:
                    'Tiles &copy; Esri 2012 <a href="https://leaflet-extras.github.io/leaflet-providers/preview/">See Here</a>'
            }
        )
        var baseLayers = {
            "ESRI_World_Imagery": Esri_WorldImagery,
            "ESRI World Street Map": Esri_WorldStreetMap
        }

        wms_legend.onAdd = function(map) {
            // var src = "?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetLegendGraphic&LAYER=significant_wave_height&colorscalerange=0,3&PALETTE=scb_bugnylorrd&numcolorbands=100&transparent=TRUE";
            var legend_div = L.DomUtil.create('div', 'info legend lcontrol hidden');
            legend_div.innerHTML +=
                '<img src="" id="legend-image" alt="Legend">';
            return legend_div;
        };
        wms_legend.addTo(map);

        var timeDimension = new L.TimeDimension();
        map.timeDimension = timeDimension;

        var player  = new L.TimeDimension.Player({
            loop: true,
            startOver:true
        }, timeDimension);

        var timeDimensionControlOptions = {
            player:        player,
            timeDimension: timeDimension,
            position:      'bottomleft',
            autoPlay:      false,
            minSpeed:      1,
            speedStep:     0.5,
            maxSpeed:      20,
            timeSliderDragUpdate: true,
            loopButton:true,
            limitSliders:true
        };

        var timeDimensionControl = new L.Control.TimeDimension(timeDimensionControlOptions);
        map.addControl(timeDimensionControl);

        graceGroup = L.layerGroup().addTo(map);
        contourGroup = L.layerGroup().addTo(map);

        var min_input = L.control({position: 'topleft'});
        min_input.onAdd = function(map){
            var div = L.DomUtil.create('div', 'min_input lcontrol hidden');
            div.innerHTML = '<b>Min:</b><input type="number" class="form-control input-sm" name="leg_min" id="leg_min" min="-5000" max="5000" step="10" value="-500" disabled>';
            return div;
        };
        min_input.addTo(map);

        var max_input = L.control({position: 'topleft'});
        max_input.onAdd = function(map){
            var div = L.DomUtil.create('div', 'max_input lcontrol hidden');
            div.innerHTML = '<b>Max:</b><input type="number" class="form-control input-sm" name="leg_max" id="leg_max" ' +
                'min="-5000" max="5000" step="10" value="0" disabled>';
            return div;
        };
        max_input.addTo(map);

        var opacity_input = L.control({position: 'topright'});
        opacity_input.onAdd = function(map){
            var div = L.DomUtil.create('div', 'opacity_input lcontrol');
            div.innerHTML = '<b>Opacity:</b><input type="number" class="form-control input-sm" name="opacity" id="opacity_val" ' +
                'min="0" max="1" step="0.1" value="1.0">';
            return div;
        };
        opacity_input.addTo(map);

        overlay_maps = {
            "GRACE Layer": graceGroup,
            "Contours": contourGroup
        };

        layer_control = L.control.layers(baseLayers, overlay_maps).addTo(map);
        baseLayers.ESRI_World_Imagery.addTo(map);

        drawnItems = new L.FeatureGroup()
        map.addLayer(drawnItems)

        var drawControlFull = new L.Control.Draw({
            edit: {
                featureGroup: drawnItems,
                edit: false
            },
            draw: {
                polyline: false,
                circlemarker: false,
                rectangle: false,
                circle: false,
                polygon: false
            }
        })

        map.addControl(drawControlFull)

        map.on("draw:drawstart ", function(e) {
            drawnItems.clearLayers()
        })

        map.on("draw:created", function(e) {
            var layer = e.layer
            layer.addTo(drawnItems)

            var feature = drawnItems.toGeoJSON();
            var int_type = feature.features[0].geometry.type
            interaction_type = int_type

            var coords = feature["features"][0]["geometry"]["coordinates"]
            globalCoords = coords
            get_ts(globalCoords);
        })

        map.on("draw:edited", function(e) {
            var feature = drawnItems.toGeoJSON()
            var int_type = feature.features[0].geometry.type
            interaction_type = int_type

            var coords = feature["features"][0]["geometry"]["coordinates"]
            globalCoords = coords
            get_ts(globalCoords);
        })

        map.on("fullscreenchange", function() {
            if (map.isFullscreen()) {
                map.setView(0.0, 15.0)
            } else {
                map.setView(0.0, 15.0)
            }
        })


    };

    add_wms = function(signal_process, layer_val, storage_type, style){
        // map.removeLayer(tdWmsLayer);
        // map.removeLayer(contourTimeLayer);
        $('.lcontrol').removeClass('hidden');
        $('.leaflet-bar-timecontrol').removeClass('hidden');
        graceGroup.clearLayers();
        contourGroup.clearLayers();
        let wmsUrl = wms_url + 'GRC_' + signal_process + '_' + storage_type + '.nc';
        let range_min = -50;
        let range_max = 50;
        let layer_arr = layer_val.toString().split("|");
        let time_string = layer_arr[0]
        contourLayer = L.tileLayer.wms(wmsUrl, {
            layers: 'lwe_thickness',
            format: 'image/png',
            transparent: true,
            styles: 'contour/'+style,
            crs: L.CRS.EPSG4326,
            opacity: '1.0',
            colorscalerange: [range_min, range_max],
            version:'1.3.0',
            zIndex: 10,
            time: time_string
        });

        contourTimeLayer = L.timeDimension.layer.wms(contourLayer,{
            updateTimeDimension:true,
            // setDefaultTime:true,
            cache:48
        });

        wmsLayer = L.tileLayer.wms(wmsUrl, {
            layers: 'lwe_thickness',
            format: 'image/png',
            transparent: true,
            styles: 'boxfill/'+style,
            opacity: '1.0',
            colorscalerange: [range_min, range_max],
            version:'1.3.0',
            zIndex:5,
            time: time_string
        });

        tdWmsLayer = L.timeDimension.layer.wms(wmsLayer,{
            updateTimeDimension:true,
            // setDefaultTime:true,
            cache:48
        });
        // tdWmsLayer.addTo(map);
        // contourTimeLayer.addTo(map);
        graceGroup.addLayer(tdWmsLayer);
        contourGroup.addLayer(contourTimeLayer);
        contourTimeLayer.bringToFront();

        var src = wmsUrl + "?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetLegendGraphic&LAYER=lwe_thickness"+
            "&colorscalerange="+range_min+","+range_max+"&PALETTE=boxfill/"+style+"&transparent=TRUE";
        // var src = wmsUrl + "?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetLegendGraphic&LAYER=lwe_thickness&PALETTE=boxfill/"+style+"&transparent=TRUE";
        $("#legend-image").attr("src", src);
        map.timeDimension.setCurrentTime(layer_arr[1]);
    };

    get_ts = function(coords){
        let {signal_process, layer_val, storage_type} = get_dropdown_vals();
        let signal_name = $("#select-signal-process option:selected").text();
        let storage_name = $("#select-storage-type option:selected").text();
        // let symbology = $("#select-symbology option:selected").val();
        var xhr = ajax_update_database("get-plot-global", {
            storage_type: storage_type,
            signal_process: signal_process,
            lon: coords[0],
            lat: coords[1]
        });
        xhr.done(function(result) {
            console.log(result);
            if ("success" in result) {
                resize_map_chart();
                $('.error').html('');
                mychart=Highcharts.stockChart('chart', {
                    legend: {
                        enabled:true
                    },
                    chart: {
                        zoomType: 'x'
                    },
                    rangeSelector: {
                        selected: tdWmsLayer._defaultRangeSelector,
                        buttons: [{
                            type: 'all',
                            text: 'All'
                        }]
                    },
                    title: {
                        text: " Water Storage Anomaly values at " + result.location,
                        style: {
                            fontSize: '14px'
                        }
                    },
                    xAxis: {
//                        type: 'datetime',
//                        labels: {
//                            format: '{value: %d %b %Y}',
//                             rotation: 45,
//                             align: 'left'
//                        },
                        plotLines: [{
                            color: 'red',
                            dashStyle: 'solid',
                            value: new Date(map.timeDimension.getCurrentTime()),
                            width: 2,
                            id: 'pbCurrentTime'
                        }],
                        title: {
                            text: 'Date'
                        }
                    },
                    yAxis: {
                        title: {
                            text: "Storage Volume",
                        }

                    },
                    exporting: {
                        enabled: true
                    },
                    series: [{
                        data:result.values,
                        name: signal_name+' '+storage_name,
                        type: 'area',
                        visible: true,
                        tooltip: {
                            valueDecimals: 2,
                            valueSuffix: ' Liquid Water Eqv. Thickness (cm)',
                            xDateFormat: '%A, %b %e, %Y',
                            headerFormat: '<span style="font-size: 12px; font-weight:bold;">{point.key} (Click to visualize the map on this time)</span><br/>'
                        }
                    },
                        {
                            data:result.integr_values,
                            name: signal_name + storage_name + ' Depletion Curve',
                            type: 'area',
                            visible: false,
                            tooltip: {
                                valueDecimals: 2,
                                valueSuffix: ' Change in Volume since April 16, 2002 (Acre-ft)',
                                xDateFormat: '%A, %b %e, %Y',
                                headerFormat: '<span style="font-size: 12px; font-weight:bold;">{point.key} (Click to visualize the map on this time)</span><br/>'
                            }
                        },
                    ],
                    lang: {
                        noData:'There is no data to display.  Please select a point where data exists.'
                    },
                    noData: {
                        style: {
                            fontWeight: 'bold',
                            fontSize: '15px',
                            color: '#303030'
                        }
                    },

                    plotOptions: {
                        series: {
                            cursor: 'pointer',
                            point: {
                                events: {
                                    click: (function(event) {
                                        var day = new Date(event.point.x);
                                        map.timeDimension.setCurrentTime(day.getTime());
                                    }).bind(this)
                                }
                            }
                        }
                    }
                });
                updateChart = function () {

                    if (!mychart){
                        return;
                    }
                    var tot_series = mychart.series[0];
                    var sw_series = mychart.series[1];
                    var soil_series = mychart.series[2];
                    var gw_series = mychart.series[3];

                    var storage_type = $("#select_storage_type option:selected").val();


                    if (storage_type === "tot"){
                        tot_series.show() }
                    else if (storage_type === "sw"){
                        sw_series.show() }
                    else if (storage_type === "soil"){
                        soil_series.show() }
                    else if (storage_type === "gw"){
                        gw_series.show() }
                };
                //    updateChart();

                map.timeDimension.on('timeload', (function() {
                    if (!mychart){
                        return;
                    }
                    mychart.xAxis[0].removePlotBand("pbCurrentTime");
                    mychart.xAxis[0].addPlotLine({
                        color: 'red',
                        dashStyle: 'solid',
                        value: new Date(map.timeDimension.getCurrentTime()),
                        width: 2,
                        id: 'pbCurrentTime'
                    });
                }));
//                updateChart();
//                 $loading.addClass('hidden');
                $("#chart").removeClass('hidden');
            }else{
                // console.log(result);
                console.log('error');
            }
        });

    };

    get_dropdown_vals = function(){
        let signal_process = $selectSignalProcess.val();
        let layer_val = $selectLayer.val();
        let storage_type = $selectStorageType.val();
        return {signal_process,
            layer_val,
            storage_type};
    };


    init_all = function(){
        init_jquery();
        init_map();
    };


    /************************************************************************
     *                        DEFINE PUBLIC INTERFACE
     *************************************************************************/
    /*
     * Library object that contains public facing functions of the package.
     * This is the object that is returned by the library wrapper function.
     * See below.
     * NOTE: The functions in the public interface have access to the private
     * functions of the library because of JavaScript function scope.
     */
    public_interface = {

    };

    /************************************************************************
     *                  INITIALIZATION / CONSTRUCTOR
     *************************************************************************/

    // Initialization: jQuery function that gets called when
    // the DOM tree finishes loading
    $(function() {
        init_all();

        $selectLayer.change(function(){
            let {signal_process, layer_val, storage_type} = get_dropdown_vals();
            let symbology = $("#select-symbology option:selected").val();
            add_wms(signal_process, layer_val, storage_type, symbology);

        });

        $selectSignalProcess.change(function(){
            let {signal_process, layer_val, storage_type} = get_dropdown_vals();
            let symbology = $("#select-symbology option:selected").val();
            add_wms(signal_process, layer_val, storage_type, symbology);
            if(globalCoords){
                get_ts(globalCoords);
            }
        });

        $selectStorageType.change(function(){
            let {signal_process, layer_val, storage_type} = get_dropdown_vals();
            let symbology = $("#select-symbology option:selected").val();
            add_wms(signal_process, layer_val, storage_type, symbology);
            if(globalCoords){
                get_ts(globalCoords);
            }
        });

        $("#select-symbology").change(function(){
            let {signal_process, layer_val, storage_type} = get_dropdown_vals();
            let symbology = $("#select-symbology option:selected").val();
            add_wms(signal_process, layer_val, storage_type, symbology);
        }).change();

        $("#opacity_val").change(function(){
            var opacity = $("#opacity_val").val();
            tdWmsLayer.setOpacity(opacity);
        });
    });

    return public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.