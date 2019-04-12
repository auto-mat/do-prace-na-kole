
function show_message(msg) {
    $("#message-modal-body").text(msg);
    $('#message-modal').modal({show:true});
}

function events_overlap(event1, event2) {
    if(event1.end && event2.end) {
        return ((event1.start >= event2.start && event1.start < event2.end) ||
                (event1.end > event2.start && event1.end <= event2.end));
    } else {
        return false;
    }
}

function show_loading_icon_on_event(info) {
    el = info.el
    while (el.firstChild) {
        el.removeChild(el.firstChild);
    }
    var loading_icon = document.createElement("i");
    loading_icon.className = 'fa fa-spinner fa-spin';
    el.appendChild(loading_icon);
}

function get_modal_url(event) {
    commute_mode = event.extendedProps.commute_mode;
    cmo = commute_modes[commute_mode];
    if(cmo.eco && cmo.does_count) {
        return "/trip/" + format_date(event.start) + "/" + event.extendedProps.direction
    }
}
