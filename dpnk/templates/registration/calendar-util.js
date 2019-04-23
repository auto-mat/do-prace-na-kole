{% load i18n %}
{% load l10n %}

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

function get_trip_url(event) {
    commute_mode = event.extendedProps.commute_mode;
    cmo = commute_modes[commute_mode];
    if(!cmo) return;
    return "/view_trip/" + format_date(event.start) + "/" + event.extendedProps.direction
}

function ajax_req_json(url, json, method, success) {
    $.ajax(url, {
        data : JSON.stringify(json),
        contentType : 'application/json',
        type : method,
        headers: {
            'X-CSRFToken': "{{ csrf_token }}"
        },
        error: function(jqXHR, status, error) {
            if (error) {
                show_message(error + " " + jqXHR.responseText);
            } else if (jqXHR.statusText == 'error') {
                show_message("{% trans 'Chyba připojení' %}");
            }
        },
        success: success
    });
}
