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
        graceGroup,
        map,
        public_interface,
        tdWmsLayer,
        wmsLayer,
        wms_legend;



    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/

    var add_wms,
        init_all,
        init_jquery,
        init_map,
        original_map_chart,
        reset_alert,
        resize_map_chart;


    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/

    init_jquery = function(){

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

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            // maxZoom: 10,
            attribution:
                '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
        wms_legend = L.control({
            position: 'bottomright'
        });

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

        var symbology_input = L.control({position: 'topright'});
        symbology_input.onAdd = function(map){
            var div = L.DomUtil.create('div', 'symbology_input lcontrol hidden');
            div.innerHTML = '<select  id="select_symbology">'+
                '<option value="" selected disabled>Select Symboloy</option>' +
                '<option value="grace">GRACE</option>' +
                '<option value="bluered">Red-Blue</option>' +
                '<option value="greyscale">Grey Scale</option>' +
                '<option value="alg2">alg2</option>' +
                '<option value="sst_36">sst_36</option>' +
                '<option value="rainbow">Rainbow</option>' +
                '</select>';
            return div
        };
        symbology_input.addTo(map);

        var opacity_input = L.control({position: 'topright'});
        opacity_input.onAdd = function(map){
            var div = L.DomUtil.create('div', 'opacity_input lcontrol hidden');
            div.innerHTML = '<b>Opacity:</b><input type="number" class="form-control input-sm" name="opacity" id="opacity_val" ' +
                'min="0" max="1" step="0.1" value="1.0">';
            return div;
        };
        opacity_input.addTo(map);
    };

    add_wms = function(wmsUrl, range_min, range_max, style){
        // map.removeLayer(tdWmsLayer);
        // map.removeLayer(contourTimeLayer);
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
            opacity: '1.0',
            colorscalerange: [range_min, range_max],
            version:'1.3.0',
            zIndex: 10
        });

        contourTimeLayer = L.timeDimension.layer.wms(contourLayer,{
            updateTimeDimension:true,
            setDefaultTime:true,
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
            zIndex:5
        });

        tdWmsLayer = L.timeDimension.layer.wms(wmsLayer,{
            updateTimeDimension:true,
            setDefaultTime:true,
            cache:48
        });
        // tdWmsLayer.addTo(map);
        // contourTimeLayer.addTo(map);
        graceGroup.addLayer(tdWmsLayer);
        contourGroup.addLayer(contourTimeLayer);
        contourTimeLayer.bringToFront();

        var src = wmsUrl + "?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetLegendGraphic&LAYER=lwe_thickness"+
            "&colorscalerange="+range_min+","+range_max+"&PALETTE=boxfill/"+style+"&transparent=TRUE";
        $("#legend-image").attr("src", src);
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
    });

    return public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.