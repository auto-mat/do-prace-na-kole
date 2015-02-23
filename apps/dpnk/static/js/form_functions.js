
//UserProfile update form:
$(function(){
   $("#div_id_nickname").toggle($("#id_dont_show_name").prop("checked"));
   $("#id_dont_show_name").change(function(){
      $("#div_id_nickname").toggle();
   });
});

