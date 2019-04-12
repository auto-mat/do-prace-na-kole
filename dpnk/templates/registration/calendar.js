{% load i18n %}
{% load l10n %}
{% load static %}
{% include "registration/util.js" %}

var day_types = {
    "possible-vacation-day": {{possible_vacation_days|safe}},
    "active-day": {{active_days|safe}},
    "locked-day": {{locked_days|safe}},
    "non-working-day": {{non_working_days|safe}},
};
var possible_vacation_days = day_types["possible-vacation-day"];
var active_days = day_types["active-day"];
var locked_days = day_types["locked-day"];
possible_vacation_days.sort();

var commute_modes = {
    {% for cm in commute_modes %}
    '{{cm.slug}}': {
        'eco': {{cm.eco|yesno:"true,false" }},
        'does_count': {{cm.does_count|yesno:"true,false" }},
        'icon_html': "{{cm.icon_html|urlencode}}",
    },
    {% endfor %}
}

var full_calendar;

placeholder_events = []
vacation_events = []
displayed_trips = []

typical_directions = ["trip_to", "trip_from"];
direction_names = {
 "trip_to": "{% trans 'Do práce' %}",
 "trip_from": "{% trans 'Domu' %}",
 "recreational": "{% trans 'Výlet' %}",
}

{% for cm in commute_modes %}
{% if cm.does_count and cm.eco %}
var editable_layers_{{cm.slug}} = new L.FeatureGroup();
var map_{{cm.slug}} = null;

function show_map_{{cm.slug}}(){
    $("#track_holder_{{cm.slug}}").show();
    $("#map_shower_{{cm.slug}}").hide();
    map_{{cm.slug}}._onResize();
}

function hide_map_{{cm.slug}}(){
    $("#track_holder_{{cm.slug}}").hide();
    $("#map_shower_{{cm.slug}}").show();
}

var route_options_{{cm.slug}} = {};

var basic_route_options_{{cm.slug}} = {
    "{% trans 'Zadat Km ručně' %}": function () {
        $("#km-{{cm.slug}}").val(0);
        hide_map_{{cm.slug}}();
        $("#map_shower_{{cm.slug}}").hide();
    },
    "{% trans 'Nahrat GPX soubor' %}": function () {
        console.log("TODO");
        show_map_{{cm.slug}}();
    },
    "{% trans 'Nakreslit trasu do mapy' %}": function () {
        editable_layers_{{cm.slug}}.clearLayers();
        show_map_{{cm.slug}}();
    },
};

function select_old_trip_{{cm.slug}}(trip){
    $("#km-{{cm.slug}}").val(trip.distanceMeters / 1000);
    show_map_{{cm.slug}}();
    load_track(map_{{cm.slug}}, "/trip_geojson/" + trip.trip_date + "/" + trip.direction, {}, editable_layers_{{cm.slug}});
}

function on_route_select_{{cm.slug}}() {
    var sel = document.getElementById("route_select_{{cm.slug}}");
    route_options_{{cm.slug}}[sel.value]();
}

function update_distance_from_map_{{cm.slug}}() {
   var tempLatLng = null; // https://stackoverflow.com/questions/31221088/how-to-calculate-the-distance-of-a-polyline-in-leaflet-like-geojson-io#31223825
   var totalDistance = 0.00000;
   $.each(editable_layers_{{cm.slug}}.getLayers(), function(i, layer){
       $.each(layer._latlngs, function(i, latlng){
           if(tempLatLng == null){
               tempLatLng = latlng;
               return;
           }
           totalDistance += tempLatLng.distanceTo(latlng);
           tempLatLng = latlng;
       });
   });
   $("#km-{{cm.slug}}").val((totalDistance / 1000).toFixed(2));
}

{% endif %}
{% endfor %}

{% include "registration/calendar-util.js" %}
{% include "registration/calendar-render.js" %}

function add_trip(trip, cont) {
    trip.sourceApplication = "web";
    $.ajax('/rest/gpx/', {
        data : JSON.stringify(trip),
        contentType : 'application/json',
        type : 'POST',
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
        success: function(jqXHR, status) {
            display_trip(trip, true);
            cont();
        }
    });
}

function display_trip(trip, rerender) {
    displayed_trips.push(trip);
    if ((possible_vacation_days.indexOf(trip.trip_date) >= 0) && !commute_modes[trip.commuteMode].does_count) {
        return
    }
    new_event = {
        start: trip.trip_date,
        end: add_days(new Date(trip.trip_date), 1),
        order: typical_directions.indexOf(trip.direction),
        allDay: true,
        commute_mode: trip.commuteMode,
        direction: trip.direction,
    }
    if (commute_modes[trip.commuteMode].does_count && commute_modes[trip.commuteMode].eco) {
        new_event.title = String(trip.distanceMeters/1000) + "Km";
    } else {
        new_event.title = "→";
    }
    event = full_calendar.addEvent(new_event);
    if(rerender){
        reload_route_options()
        full_calendar.render();
    }
}

function add_vacation(startDate, endDate) {
    startDateString = format_date(startDate);
    endDateString = format_date(add_days(endDate, -1));
    if(possible_vacation_days.indexOf(startDateString) >= 0 && possible_vacation_days.indexOf(endDateString) >= 0){
        events = full_calendar.getEvents(); // TODO only look at vacation event source
        for (eid in events) {
            if (events[eid].extendedProps.vacation) {
                if (events_overlap(new_event, events[eid])) {
                    e2 = events[eid]
                    return;
                }
            }
        }
        new_event = {
            title: "",
            start: startDate,
            end: endDate,
            allDay: true,
            loading: true,
        }
        new_event = full_calendar.addEvent(new_event);
        $.ajax({url: "{% url 'calendar' %}", 
               type: 'POST',
               dataType: 'json',
               headers: {
                  'X-CSRFToken': "{{ csrf_token }}",
               },
               data: {
                  on_vacation: true,
                  start_date: startDateString,
                  end_date: endDateString,
               },
               success: function(returnedData){
                  new_event.remove();
                  for (i in returnedData) {
                     display_trip(returnedData[i]);
                  }
                  redraw_everything_trip_related();
               },
               fail: function(jqXHR, textStatus, errorThrown) {
                  new_event.remove();
                  show_message("{% trans 'Propojení selhalo' %}");
              }});
    }
}

function remove_vacation(info) {
    var event = info.event;
    startDateString = format_date(event.start)
    endDateString = format_date(event.end)
    show_loading_icon_on_event(info);
    $.post("{% url 'calendar' %}", {
        on_vacation: false,
        start_date: startDateString,
        end_date: endDateString,
        csrfmiddlewaretoken: "{{ csrf_token }}",
    },
           function(returnedData){
               days_to_delete = possible_vacation_days.slice(possible_vacation_days.indexOf(startDateString), possible_vacation_days.indexOf(endDateString))
               console.log(days_to_delete)
               displayed_trips = displayed_trips.filter( function (trip) {
                      return days_to_delete.indexOf(trip.trip_date) < 0;
               });
               full_calendar.getEventSourceById(3).refetch();
           }
          ).fail(function(jqXHR, textStatus, errorThrown) {
              full_calendar.addEvent(event);
              show_message("{% trans 'Propojení selhalo' %}");
          });
}

function eventClick(info) {
    console.log(info);
    if(info.event.extendedProps.placeholder){
        commute_mode = $("div#nav-commute-modes a.active")[0].hash.substr("#tab-for-".length);
        var trip = {
           "trip_date": format_date(info.event.start),
           "direction": info.event.extendedProps.direction,
           "commuteMode": commute_mode,
        }
        if (commute_modes[commute_mode].does_count && commute_modes[commute_mode].eco) {
            trip["distanceMeters"] = Number($('#km-'+commute_mode).val()) * 1000
        }
        show_loading_icon_on_event(info);
        add_trip(trip, redraw_everything_trip_related);
    }
    modal_url = get_modal_url(info.event);
    if(modal_url){
        $('#trip-modal').modal({show:true});
        $('#trip-modal-body').empty();
        $('#trip-modal-spinner').show();
        $('#trip-modal-body').load(modal_url + " #inner-content", function(){
            $('#trip-modal-spinner').hide();
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    {% for cm in commute_modes %}
    {% if cm.does_count and cm.eco %}

    map_{{cm.slug}} = L.map('map_{{cm.slug}}').setView([50.0866699218750000, 14.4387817382809995], 8);
    L.tileLayer('https://tiles.prahounakole.cz/{z}/{x}/{y}.png',
                {
                    attribution: '&copy; přispěvatelé <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                }).addTo(map_{{cm.slug}});

    map_{{cm.slug}}.addLayer(editable_layers_{{cm.slug}});

    var draw_options = {
        draw: {
            polygon: false,
            marker: false,
            rectangle: false,
            circle: false,
            circlemarker: false,
            polyline: {
                metric: true,
                feet: false,
                showLength: true,
            }
        },
        edit: {
            featureGroup: editable_layers_{{cm.slug}},
            remove: true
        },
        delete: {}
    };
    var drawControl = new L.Control.Draw(draw_options);
    map_{{cm.slug}}.addControl(drawControl);
    map_{{cm.slug}}.on(L.Draw.Event.DRAWSTOP, update_distance_from_map_{{cm.slug}});
    map_{{cm.slug}}.on(L.Draw.Event.EDITSTOP, update_distance_from_map_{{cm.slug}});
    map_{{cm.slug}}.on(L.Draw.Event.DELETESTOP, update_distance_from_map_{{cm.slug}});
    map_{{cm.slug}}.on(L.Draw.Event.CREATED, function (e) {
        editable_layers_{{cm.slug}}.addLayer(e.layer);
    });
    {% endif %}
    {% endfor %}

    var calendarEl = document.getElementById('calendar');
    if($(window).width() > $(window).height()) {
        defaultView = 'dayGridMonth';
    } else {
        defaultView = 'listMonth';
    }
    full_calendar = new FullCalendar.Calendar(calendarEl, {
        eventSources: [
           {events: {{events|safe}}},
           {events: get_placeholder_events, id: 2},
           {events: get_vacation_events, id: 3},
        ],
        eventOrder: 'order',
        selectable: true,
        lang: '{{ LANGUAGE_CODE }}',
        locale: '{{ LANGUAGE_CODE }}',
        height: 'auto',
        firstDay: 1,
        plugins: [ 'interaction', 'dayGrid', 'list' ],
        selectable: true,
        defaultView: defaultView,
        rerenderDelay: 50,
        header: {
            right: 'dayGridMonth,listMonth, now, prev,next',
        },
        select: function(info) {
            console.log(info)
            add_vacation(info.start, info.end);
        },
        eventRender: eventRender,
        eventClick: eventClick,
        dayRender: dayRender,
    });
    $.getJSON('/rest/gpx/?format=json', function( data ){
        for (i in data.results) {
            display_trip(data.results[i]);
        }
        redraw_everything_trip_related();
        full_calendar.render();
        $(".main-loading-overlay").hide();
    });
});
