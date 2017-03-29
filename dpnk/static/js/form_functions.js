
$(function(){
    //UserProfile update form:
    $("#div_id_nickname").toggle($("#id_dont_show_name").prop("checked"));
    $("#id_dont_show_name").change(function(){
        $("#div_id_nickname").toggle();
    });

    //UserProfile update form:
    $("#id_dont_want_insert_track").change(function(){
        $("#div_id_track").toggle(! $("#id_dont_want_insert_track").prop("checked"));
        $("#div_id_distance").toggle($("#id_dont_want_insert_track").prop("checked"));
    });

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

   $('form.dirty-check').areYouSure({'message':"Ve formuláři jsou neuložené změny."});

   // Fix triggering chaining on hidden company field
   $( "#id_company_0" ).on( "djselectableselect", function( event, ui ) {
      $('#id_company_1').change();
   } );
});

window.addEventListener("map:init", function (e) {
   $("#id_dont_want_insert_track").change();
}, false);
