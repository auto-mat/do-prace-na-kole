import '../less/table.less';

//@ts-ignore
if(window.formset_errors) {
    $(function () {
        $('#rides-form').trigger('checkform.areYouSure');
    });
}

