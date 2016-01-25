
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


   $('.submit-once-form').submit(function () {
       // Bail out if the form contains validation errors
       if ($.validator && !$(this).valid()) return;

       var form = $(this);
       $(this).find('input[type="submit"], button[type="submit"]').each(function (index) {
           // Create a disabled clone of the submit button
           $(this).clone(false).removeAttr('id').prop('disabled', true).insertBefore($(this));

           // Hide the actual submit button and move it to the beginning of the form
           $(this).hide();
           form.prepend($(this));
       });
   });

   $('.upravit_profil form').submit(function (){
      if($('#id_mailing_opt_in_2').prop('checked') == true){
         return window.confirm("Skutečně nechcete dostávat žádné soutěžní emaily? Můžete tak například přijít o některé akce v průběhu soutěže.");
      } else {
         return true;
      }
   });
});
