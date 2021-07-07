/*****************************************************************************
 * FILE:    GGST Delete Region
 * DATE:    7 July 2021
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
        $region_input;



    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/

    var delete_region,
        init_jquery,
        reset_alert,
        reset_form;


    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/

    init_jquery = function(){
        $region_input = $("#region-select");
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
            $("#region-select").val('');
            $("#region-select").val(null).trigger('change.select2');
            addSuccessMessage('Region Delete Complete!');
        }
    };

    delete_region = function(){
        reset_alert(); //Reset the alerts
        const region_name = $region_input.val();

        if(region_name === ""){
            addErrorMessage("Region Name cannot be empty!");
            return false;
        }else{
            reset_alert();
        }
        const submit_button = $("#submit-delete-region");
        const submit_button_html = submit_button.html();
        submit_button.text('Submitting ...');
        addInfoMessage("Deleting Region. Please wait...","message");
        var xhr = ajax_update_database("delete", {
            region_name: region_name
        });
        xhr.done(function(return_data){ //Reset the form once the data is added successfully
            if("success" in return_data){
                submit_button.html(submit_button_html);
                reset_form(return_data);
            }else{
                console.log(return_data);
            }
        });
    };

    $("#submit-delete-region").click(delete_region);


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