/*****************************************************************************
 * FILE:    GGST Region Map
 * DATE:    8 March 2021
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
        map_lat,
        map_lon,
        mychart,
        overlay_maps,
        public_interface,
        regional_chart,
        range_min,
        range_max,
        region_name,
        $selectStyle,
        $selectLayer,
        $selectRegion,
        $selectStorageType,
        shapeGroup,
        shapeLayer,
        tdWmsLayer,
        wms_legend,
        wms_url,
        wmsLayer;



    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/

    var add_wms,
        add_regional_graph,
        get_dropdown_vals,
        get_legend_range,
        get_region_center,
        get_region_shape,
        get_ts,
        get_timestep,
        init_all,
        init_jquery,
        init_map,
        original_map_chart,
        reset_alert,
        resize_map_chart,
        updateChart,
        update_wms;


    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/

    init_jquery = function(){
        $selectLayer = $("#select-layer");
        $selectStorageType = $("#select-storage-type");
        $selectRegion =$("#region-select");
        $selectStyle = $("#select-symbology");
        wms_url = $("#map-info").attr("wms-url");
        map_lat = $("#map-info").attr("map-lat");
        map_lon = $("#map-info").attr("map-lon");
        region_name = $("#map-info").attr("region-name");
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

    resize_map_chart = function(){
        $('#chart').addClass('partial-chart');
        $('#chart').removeClass('full-chart');
        $('#reg-chart').addClass('partial-chart');
        $('#reg-chart').removeClass('full-chart');
        $('#map').removeClass('full-map');
        $('#map').addClass('partial-map');
    };

    original_map_chart = function(){
        $('#chart').removeClass('partial-chart');
        $('#chart').addClass('full-chart');
        $('#reg-chart').removeClass('partial-chart');
        $('#reg-chart').addClass('full-chart');
        $('#map').addClass('full-map');
        $('#map').removeClass('partial-map');
    };

    init_map = function(){
        map = L.map('map', {
            zoom: 3,
            center: [map_lat, map_lon],
            // crs: L.CRS.EPSG3857
        });
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

        map.timeDimension = new L.TimeDimension();

        var player  = new L.TimeDimension.Player({
            loop: true,
            startOver:true
        }, map.timeDimension);

        var timeDimensionControlOptions = {
            player:        player,
            timeDimension: map.timeDimension,
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
        shapeGroup = L.layerGroup({"interactive": false}).addTo(map);

        var opacity_input = L.control({position: 'topleft'});
        opacity_input.onAdd = function(map){
            var div = L.DomUtil.create('div', 'opacity_input lcontrol');
            div.innerHTML = '<b>Opacity:</b><input type="number" class="form-control input-sm" name="opacity" id="opacity_val" ' +
                'min="0" max="1" step="0.1" value="1.0">';
            return div;
        };
        opacity_input.addTo(map);

        overlay_maps = {
            "GRACE Layer": graceGroup,
            "Contours": contourGroup,
            "Outline": shapeGroup
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
    }

    get_dropdown_vals = function(){
        let layer_val = $selectLayer.val();
        let storage_type = $selectStorageType.val();
        let region = $selectRegion.val();
        let symbology = $selectStyle.val();
        return {
            layer_val,
            storage_type,
            region,
            symbology
        };
    };

    get_region_center = function(region){
        const xhr = ajax_update_database('map-center', {'region': region});
        xhr.done(function(result){
            if('success' in result){
                map.setView(new L.LatLng(result['lat'], result['lon']), 6);
            }
        });
    };

    get_region_shape = function(region){
        const xhr = ajax_update_database('geojson', {'region': region});
        xhr.done(function(result){
            if('success' in result){
                shapeGroup.clearLayers();
                shapeLayer = L.geoJSON(result["geojson"], {
                    color: "#000000",
                    interactive: false,
                    fill: false
                });
                shapeGroup.addLayer(shapeLayer);
                // L.geoJSON(result["geojson"]).addTo(map);
            }
        });
    }

    update_wms = function(region_name, layer_val, storage_type, style, range_min, range_max, mode_type){
        let wmsUrl = wms_url + region_name + '/' + region_name + '_' + storage_type + '.nc';
        let opacity = $("#opacity_val").val();
        let layer_arr = layer_val.toString().split("|");
        let time_string = layer_arr[0];
        $('.lcontrol').removeClass('hidden');
        $('.leaflet-bar-timecontrol').removeClass('hidden');
        graceGroup.clearLayers();
        contourGroup.clearLayers();
        contourLayer = L.tileLayer.wms(wmsUrl, {
            layers: 'lwe_thickness',
            format: 'image/png',
            transparent: true,
            styles: 'contour/'+style,
            crs: L.CRS.EPSG4326,
            opacity: opacity,
            colorscalerange: [range_min, range_max],
            version:'1.3.0',
            zIndex: 10,
            // time: time_string
        });

        if(mode_type==='add') {
            contourTimeLayer = L.timeDimension.layer.wms(contourLayer, {
                updateTimeDimension: true,
                setDefaultTime: true,
                cache: 48,
                requestTimeFromCapabilities: true,
                updateTimeDimensionMode: 'replace'
            });
        }else if (mode_type==='update'){
            contourTimeLayer = L.timeDimension.layer.wms(contourLayer, {
                // updateTimeDimension: true,
                setDefaultTime: true,
                cache: 48,
                // requestTimeFromCapabilities: true,
            });
        }

        wmsLayer = L.tileLayer.wms(wmsUrl, {
            layers: 'lwe_thickness',
            format: 'image/png',
            transparent: true,
            styles: 'boxfill/'+style,
            crs: L.CRS.EPSG4326,
            opacity: opacity,
            colorscalerange: [range_min, range_max],
            version:'1.3.0',
            zIndex:5,
            // time: time_string
        });

        if(mode_type==='add') {
            tdWmsLayer = L.timeDimension.layer.wms(wmsLayer, {
                // updateTimeDimension: true,
                // setDefaultTime: false,
                cache: 48,
                requestTimeFromCapabilities: true,
                updateTimeDimensionMode: 'replace'
            });
        }else if(mode_type==='update'){
            tdWmsLayer = L.timeDimension.layer.wms(wmsLayer, {
                // updateTimeDimension: true,
                // setDefaultTime: false,
                cache: 48,
                // requestTimeFromCapabilities: true,
            });
        }
        // tdWmsLayer.addTo(map);
        // contourTimeLayer.addTo(map);
        graceGroup.addLayer(tdWmsLayer);
        contourGroup.addLayer(contourTimeLayer);
        contourTimeLayer.bringToFront();
        // tdWmsLayer.setOpacity(opacity);
        var src = wmsUrl + "?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetLegendGraphic&LAYER=lwe_thickness"+
            "&colorscalerange="+range_min+","+range_max+"&PALETTE="+style+"&transparent=FALSE";
        $("#legend-image").attr("src", src);
        map.timeDimension.setCurrentTime(layer_arr[1]);
        if(mode_type==='add'){
            add_regional_graph();
            resize_map_chart();
        }
    };


    get_legend_range = function(region_name, layer_val, storage_type, style){
        const xhr = ajax_update_database('range',
            {'region_name': region_name,
                'storage_type': storage_type});
        xhr.done(function(result){
            if('success' in result){
                range_min = result['range_min'];
                range_max = result['range_max'];
                $("#leg_min").val(range_min);
                $("#leg_max").val(range_max);
                update_wms(region_name, layer_val, storage_type, style, range_min, range_max, 'add');
            }
        });
    };

    add_wms = function(region_name, layer_val, storage_type, style){
        get_legend_range(region_name, layer_val, storage_type, style);
    };

    get_timestep = function(storage_type){
        var xhr = ajax_update_database("timestep", {
            storage_type: storage_type
        });
        xhr.done(function(result) {
            if ("success" in result) {
                $("#select-layer").html('');
                var layer_options = result['layer_options'];
                layer_options.forEach(function(attr,i){
                    var layer_option = new Option(attr[0], attr[1]);
                    $("#select-layer").append(layer_option);
                });
                let layer_val = $selectLayer.val();
                // $selectLayer.val(layer_val);
                // $("#select-layer").text(result['layer_options'].slice(-1)[0]);
                // $("#select-layer").val(result['layer_options'].slice(-1)[1]).trigger('change.select2');
                // $("#select-layer").select2('destroy');
                $('#select-layer').select2(result['layer_options'].slice(-1)[1], null);
                // $('#select-layer').val(result['layer_options'].slice(-1)[1]).select2();
                let symbology = $selectStyle.val();
                let region = $selectRegion.val();
                add_wms(region, layer_val, storage_type, symbology);
            }
        });
    };

    get_ts = function(coords){
        let {layer_val, storage_type, region} = get_dropdown_vals();
        let signal_name = $("#select-signal-process option:selected").text();
        let storage_name = $("#select-storage-type option:selected").text();
        // let symbology = $("#select-symbology option:selected").val();
        var xhr = ajax_update_database("get-plot-region", {
            region: region,
            storage_type: storage_type,
            lon: coords[0],
            lat: coords[1]
        });

        xhr.done(function(result) {
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
                        type: 'line',
                        visible: true,
                        tooltip: {
                            valueDecimals: 2,
                            valueSuffix: ' Liquid Water Eqv. Thickness (cm)',
                            xDateFormat: '%A, %b %e, %Y',
                            headerFormat: '<span style="font-size: 12px; font-weight:bold;">{point.key} (Click to visualize the map on this time)</span><br/>'
                        }
                    },
                        {
                            data:result.error_range,
                            name: signal_name+' '+storage_name + ' Error Range',
                            type: 'arearange',
                            // visible: true,
                            fillOpacity: 0.3,
                            lineWidth: 0,
                            // linkedTo: ':previous',
                            color: Highcharts.getOptions().colors[0]
                        },
                        {
                            data:result.integr_values,
                            name: signal_name + storage_name + ' Depletion Curve',
                            type: 'area',
                            visible: false,
                            tooltip: {
                                valueDecimals: 2,
                                valueSuffix: ' Change in Volume (Acre-ft)',
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
                console.log(result);
            }
        });

    };

    add_regional_graph = function(){
        let {layer_val, storage_type, region, symbology} = get_dropdown_vals();

        regional_chart=Highcharts.stockChart('reg-chart', {
            legend: {
                enabled: true
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

            xAxis: {
                plotLines: [{
                    color: 'red',
                    dashStyle: 'solid',
                    value: new Date(map.timeDimension.getCurrentTime()),
                    width: 2,
                    id: 'pbCurrentTime'
                }],
                title: {
                    text: 'Date'
                },
            },
            yAxis: {
                title: {
                    text: "Storage Volume",
                }

            },

            title: {
                text: $("#region-select option:selected").text() + ' Regional Average Water Storage Anomaly'
            },

            series: [],

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
        });//end of High Charts stuff
        tdWmsLayer._timeDimension.on('timeload', (function() {
            if (!regional_chart){
                return;
            }
            regional_chart.xAxis[0].removePlotBand("pbCurrentTime");
            regional_chart.xAxis[0].addPlotLine({
                color: 'red',
                dashStyle: 'solid',
                value: new Date(map.timeDimension.getCurrentTime()),
                width: 2,
                id: 'pbCurrentTime'
            });
        }).bind(this));

        var color;
        var depletion_color
        var charttype;
        var seriesname;
        var myseries, error_range, depletion_curve;
        charttype="Total";
        color="#053372";
        depletion_color="#222222";

        seriesname= $("#select-storage-type option:selected").text();
        var xhr = ajax_update_database("get-region-summary", {
            region: region,
            storage_type: storage_type
        });

        xhr.done(function(result) {
            if ("success" in result) {
                myseries =
                    {
                        name: seriesname,
                        data: result.values,
                        type: 'line',
                        color:color,
                        lineWidth: 3,
                        tooltip: {
                            valueDecimals: 2,
                            valueSuffix: ' Liquid Water Eqv. Thickness (cm)',
                            xDateFormat: '%A, %b %e, %Y',
                            headerFormat: '<span style="font-size: 12px; font-weight:bold;">{point.key} (Click to visualize the map on this time)</span><br/>'
                        }
                    };
                regional_chart.addSeries(myseries);
                error_range = {
                    data:result.error_range,
                    name: seriesname+ ' Error Range',
                    type: 'arearange',
                    // visible: true,
                    fillOpacity: 0.3,
                    lineWidth: 0,
                    // linkedTo: ':previous',
                    color: color
                }
                regional_chart.addSeries(error_range);
                depletion_curve=
                    {
                        name: seriesname + " Depletion Curve",
                        data: result.integr_values,
                        type: 'area',
                        color:depletion_color,
                        tooltip: {
                            valueDecimals: 2,
                            valueSuffix: ' Change in Volume (Acre-ft)',
                            xDateFormat: '%A, %b %e, %Y',
                            headerFormat: '<span style="font-size: 12px; font-weight:bold;">{point.key} (Click to visualize the map on this time)</span><br/>'
                        },
                        visible:false
                    };
                regional_chart.addSeries(depletion_curve);
            }
        });
    };

    init_all = function(){
        init_jquery();
        init_map();
    }
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

        $selectRegion.change(function(){
            let {layer_val, storage_type, region, symbology} = get_dropdown_vals();
            get_region_center(region);
            get_region_shape(region);
            add_wms(region, layer_val, storage_type, symbology);
            //             update_wms(region, layer_val, storage_type, symbology, range_min, range_max, 'update');

            // original_map_chart();
        })
        $selectRegion.val(region_name).trigger('change');
        // .change();
        $selectLayer.change(function(){
            let {layer_val, storage_type, region, symbology} = get_dropdown_vals();
            update_wms(region, layer_val, storage_type, symbology, range_min, range_max, 'update');
        });

        $selectStorageType.change(function(){
            let storage_type = $selectStorageType.val();
            get_timestep(storage_type);

            if(globalCoords){
                get_ts(globalCoords);
            }
        });

        $selectStyle.change(function(){
            let {layer_val, storage_type, region, symbology} = get_dropdown_vals();
            update_wms(region, layer_val, storage_type, symbology, range_min, range_max, 'update');
        });

        $("#opacity_val").change(function(){
            let opacity = $("#opacity_val").val();
            tdWmsLayer.setOpacity(opacity);
        });

        $("#leg_min").change(function(){
            let {layer_val, storage_type, region, symbology} = get_dropdown_vals();
            let range_min = $("#leg_min").val();
            let range_max = $("#leg_max").val();
            update_wms(region_name, layer_val, storage_type, symbology, range_min, range_max, 'update');
        });

        $("#leg_max").change(function(){
            let {layer_val, storage_type, region, symbology} = get_dropdown_vals();
            let range_min = $("#leg_min").val();
            let range_max = $("#leg_max").val();
            update_wms(region_name, layer_val, storage_type, symbology, range_min, range_max, 'update');
        });

    });

    return public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.