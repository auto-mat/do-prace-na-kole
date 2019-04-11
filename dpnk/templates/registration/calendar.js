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
        console.log("TODO");
        show_map_{{cm.slug}}();
    },
};

function on_route_select_{{cm.slug}}() {
    var sel = document.getElementById("route_select_{{cm.slug}}");
    route_options_{{cm.slug}}[sel.value]();
}
{% endif %}
{% endfor %}

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

function get_vacation_events(fetchInfo, successCallback, failureCallback){
    vacation_events = [];
    var current_vacation_start = null;
    var possible_vacation_day = null;
    function close_out_vacation_if_needed() {
        if(current_vacation_start) {
           new_event =  {
               title: "{% trans 'Dovolena' %}",
               start: current_vacation_start,
               end: possible_vacation_day,
               allDay: true,
               vacation: true,
           } 
           vacation_events.push(new_event);
           current_vacation_start = null;
       }
    }
    for(i in possible_vacation_days){
       possible_vacation_day = possible_vacation_days[i];
       var directions = [];
       for (i in displayed_trips) {
           var trip = displayed_trips[i];
           if(trip.trip_date == possible_vacation_day){
               directions.push(trip.direction);
           }
       }
       num_trips = 0;
       for(i in typical_directions) {
           if(directions.includes(typical_directions[i])){
              num_trips++;
           }
       }
       if(num_trips == 2){
          if(!current_vacation_start){
              current_vacation_start = possible_vacation_day;
          }
       } else close_out_vacation_if_needed();
    }
    close_out_vacation_if_needed();
    successCallback(vacation_events);
}

function get_placeholder_events(fetchInfo, successCallback, failureCallback){
    placeholder_events = [];
    for(i in day_types["active-day"]){
       var active_day = day_types["active-day"][i];
       var directions = [];
       for (i in displayed_trips) {
           var trip = displayed_trips[i];
           if(trip.trip_date == active_day){
               directions.push(trip.direction);
           }
       }
       for(i in typical_directions) {
           if(!directions.includes(typical_directions[i])){
               new_event =  {
                   title: "+",
                   start: active_day,
                   end: add_days(new Date(active_day), 1),
                   order: i,
                   allDay: true,
                   placeholder: true,
                   direction: typical_directions[i],
               } 
               placeholder_events.push(new_event);
           }
       }
    }
    successCallback(placeholder_events);
}

function redraw_everything_trip_related() {
    full_calendar.getEventSourceById(2).refetch();
    full_calendar.getEventSourceById(3).refetch();
    reload_route_options();
}

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

function reload_route_options() {
    displayed_trips.sort(function(a, b) {
        da = Date.parse(a.trip_date);
        db = Date.parse(b.trip_date);
        return db - da;
    });
    {% for cm in commute_modes %}
    {% if cm.does_count and cm.eco %}
    route_options_{{cm.slug}} = jQuery.extend({}, basic_route_options_{{cm.slug}});
    var sel = $("#route_select_{{cm.slug}}");
    sel.children().remove(); 
    sel = sel[0];
    for(var i in displayed_trips) {
        var trip = displayed_trips[i];
        if (trip.commuteMode == '{{cm.slug}}') {
            var desc = "{% trans 'Stejně jako' %} " + trip.trip_date + "  " + direction_names[trip.direction] + " (" + trip.distanceMeters / 1000 + " Km)";
            (function () {
                var local_trip = trip; // Thanks! http://reallifejs.com/the-meat/getting-closure/never-forget/
                route_options_{{cm.slug}}[desc] = function () {
                    $("#km-{{cm.slug}}").val(local_trip.distanceMeters / 1000);
                    show_map_{{cm.slug}}();
                };
            })();
       }
    }
    for(var key in route_options_{{cm.slug}}){
        var option = document.createElement("option");
        option.value = key;
        option.text = key;
        sel.appendChild(option);
    }
    {% endif %}
    {% endfor %}
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
        },
        edit: {
            featureGroup: editable_layers_{{cm.slug}},
            remove: false
        }
    };
    var drawControl = new L.Control.Draw(draw_options);
    map_{{cm.slug}}.addControl(drawControl);
    map_{{cm.slug}}.on(L.Draw.Event.CREATED, function (e) {
        var type = e.layerType,
            layer = e.layer;
        if (type === 'marker') {
            layer.bindPopup('A popup!');
        }
        editable_layers_{{cm.slug}}.addLayer(layer);
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
        eventRender: function(info) {
            // Remove time column from Agenda view
            if(info.el.children[0].classList.contains("fc-list-item-time")){
                info.el.children[1].remove();
                info.el.children[0].remove();
                info.el.children[0].colSpan=3
            }
            var direction_icon = null;
            exp = info.event.extendedProps
            if (exp.loading) {
               show_loading_icon_on_event(info);
            }
            if (exp.vacation) { // https://stackoverflow.com/questions/26530076/fullcalendar-js-deleting-event-on-button-click#26530819
                var trash_icon =  document.createElement("i");
                var trash_button = document.createElement("button");
                trash_button.className = 'btn btn-default btn-xs trash-button';
                trash_button.append(trash_icon);
                trash_button.onclick = function(){remove_vacation(info)};
                trash_icon.className = 'fa fa-trash sm';
                info.el.firstChild.append(trash_button);
            } else {
                if (exp.direction == 'trip_to'){
                    direction_icon = document.createElement("i");
                    direction_icon.className='fa fa-industry xs';
                } else if (exp.direction == 'trip_from') {
                    direction_icon = document.createElement("i");
                    direction_icon.className='fa fa-home xs';
                }
                if (direction_icon) {
                    info.el.firstChild.append(direction_icon);
                }
                if (exp.commute_mode) {
                    var mode_icon = document.createElement("div");
                    mode_icon.className='mode-icon-container';
                    mode_icon.innerHTML = decodeURIComponent(commute_modes[exp.commute_mode].icon_html);
                    info.el.firstChild.prepend(mode_icon);
                }
            }

        },
        eventClick: function(info) {
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
            if(info.event.extendedProps.modal_url){
                $('#trip-modal').modal({show:true});
                $('#trip-modal-body').empty();
                $('#trip-modal-spinner').show();
                $('#trip-modal-body').load(info.event.extendedProps.modal_url + " #inner-content", function(){
                    $('#trip-modal-spinner').hide();
                });
            }
        },
        dayRender: function (cell) {
            var set = false;
            if(active_days.indexOf(format_date(cell.date)) >= 0 || locked_days.indexOf(format_date(cell.date)) >= 0) {
                var num_eco_trips = 0;
                for (i in displayed_trips){
                    if(displayed_trips[i].trip_date == format_date(cell.date)){
                        var trip = displayed_trips[i];
                        if(commute_modes[trip.commuteMode].eco){
                            num_eco_trips++;
                        }
                    }
                }
                if (num_eco_trips == 1) {
                    cell.el.classList.add('one-ride-day');
                } else if (num_eco_trips > 1) {
                    cell.el.classList.add('two-ride-day');
                }
            }
            for (key in day_types) {
                if (day_types[key].indexOf(format_date(cell.date)) >= 0) {
                    cell.el.classList.add(key);
                    set = true;
                }
            }
            if (!set){
                cell.el.classList.add("out-of-competition-day");
            }
        },
    });
    $.getJSON('/rest/gpx/?format=json', function( data ){
        for (i in data.results) {
            display_trip(data.results[i]);
        }
        redraw_everything_trip_related();
        full_calendar.render();
    });
});
