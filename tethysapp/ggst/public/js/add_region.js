/*****************************************************************************
 * FILE:    GGST Add Region
 * DATE:    2 February 2021
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
    var public_interface,
        $region_input,
        $shp_input,
        $thredds_select;



    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/

    var add_region,
        init_jquery,
        reset_alert,
        reset_form;


    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/

    init_jquery = function(){
        $shp_input = $("#shp-upload-input");
        $thredds_select = $("#thredds-select option:selected");
        $region_input = $("#region-name-input");
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

    reset_form = function(result){
        if("success" in result){
            $("#region-name-input").val('');
            $("#shp-upload-input").val('');
            addSuccessMessage('Region Upload Complete!');
        }
    };

    add_region = function(){
        reset_alert(); //Reset the alerts
        const region_name = $region_input.val();
        const thredds = $thredds_select.val();
        const shapefiles = $shp_input[0].files;

        if (/[^a-zA-Z0-9 ]/g.test(region_name) === true){
            addErrorMessage("Region Name cannot have special characters. Please use numbers and letters!");
            return false;
        }else{
            reset_alert();
        }
        if(region_name === ""){
            addErrorMessage("Region Name cannot be empty!");
            return false;
        }else{
            reset_alert();
        }
        if($shp_input.val() === ""){
            addErrorMessage("Region Shape File cannot be empty!");
            return false;
        }else{
            reset_alert();
        }

        //Preparing data to be submitted via AJAX POST request
        const data = new FormData();
        data.append("region_name",region_name);
        data.append("thredds",thredds);
        for(let i=0; i < shapefiles.length; i++){
            data.append("shapefile",shapefiles[i]);
        }

        addInfoMessage("Adding Region. Please wait...","message");
        const submit_button = $("#submit-add-region");
        const submit_button_html = submit_button.html();
        submit_button.text('Submitting ...');
        const submit_region = ajax_update_database_with_file("submit", data);
        submit_region.done(function(return_data){ //Reset the form once the data is added successfully
            if("success" in return_data){
                submit_button.html(submit_button_html);
                reset_form(return_data);
            }else{
                submit_button.html(submit_button_html);
                console.log(return_data);
            }
        });
    };

    $("#submit-add-region").click(add_region);


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
        init_jquery();

    });

    return public_interface;

}()); // End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.