$(function(){
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

   $('#personal-data-form').submit(function (){
      if($('#id_id_userprofile-mailing_opt_in_0_2').prop('checked') == true){
         return window.confirm("Skutečně nechcete dostávat žádné soutěžní emaily? Můžete tak například přijít o některé akce v průběhu soutěže.");
      } else {
         return true;
      }
   });

   $('form.dirty-check').areYouSure({'message':"Ve formuláři jsou neuložené změny."});
});
