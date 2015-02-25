
$(function(){
    //UserProfile update form:
    $("#div_id_nickname").toggle($("#id_dont_show_name").prop("checked"));
    $("#id_dont_show_name").change(function(){
        $("#div_id_nickname").toggle();
    });

    //UserProfile update form:
    $("#id_dont_want_insert_track").change(function(){
        $("#div_id_track").toggle(! $("#id_dont_want_insert_track").prop("checked"));
    });
    $("#id_dont_want_insert_track").change();

    //WorkingSchedule update form:
    $(".working-ride").change(function(){
        rides_count = $(".working-ride:checked").size();

        minimum_rides = Math.round(Math.max(minimum_percentage*rides_count/100, minimum_percentage*minimum_rides_base/100));

        $("#rides-count").text(rides_count);
        $("#minimum-rides").text(minimum_rides);
        $("#not-enough-rides-warning").toggle(rides_count < minimum_rides);
    });
    $(".working-ride").change();
});
