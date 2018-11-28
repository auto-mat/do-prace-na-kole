// From https://github.com/yourlabs/django-autocomplete-light/blob/master/test_project/linked_data/static/linked_data.js
$(document).ready(function() {
    $(':input[name$=company_0]').on('change', function() {
        $(':input[name=subsidiary]').val(null).trigger('change');
    });
});
