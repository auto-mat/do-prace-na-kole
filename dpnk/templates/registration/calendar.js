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
var commute_modes = {
    {% for cm in commute_modes %}
    '{{cm.slug}}': {
        'eco': {{cm.eco|yesno:"true,false" }},
        'does_count': {{cm.does_count|yesno:"true,false" }},
    },
    {% endfor %}
}
var possible_vacation_days = day_types["possible-vacation-day"];
var full_calendar;

placeholder_events = []
vacation_events = []
displayed_trips = []

typical_directions = ["trip_to", "trip_from"];

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

var route_options_{{cm.slug}} = {
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
    {% for trip in trips %}
    {% if trip.commute_mode == cm %}
    "{% trans 'Stejně jako' %} {{trip.date}} {{trip.get_direction_display }} ({{trip.distance}} Km)": function () {
        $("#km-{{cm.slug}}").val({{trip.distance|stringformat:"f"}});
        show_map_{{cm.slug}}();
    },
    {% endif %}
    {% endfor %}
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

function redraw_placeholders() {
    for(i in placeholder_events) {
        placeholder_events[i].remove();
    }
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
               placeholder_events.push(full_calendar.addEvent(new_event));
           }
       }
    }
}

function display_trip(trip) {
    displayed_trips.push(trip);
    new_event = {
        title: String(trip.distanceMeters/1000) + "Km",
        start: trip.trip_date,
        end: add_days(new Date(trip.trip_date), 1),
        order: typical_directions.indexOf(trip.direction),
        allDay: true,
        commute_mode: trip.commuteMode,
        direction: trip.direction,
    }
    full_calendar.addEvent(new_event);
}

function add_vacation(startDate, endDate) {
    startDateString = format_date(startDate);
    endDateString = format_date(add_days(endDate, -1));
    if(possible_vacation_days.indexOf(startDateString) >= 0 && possible_vacation_days.indexOf(endDateString) >= 0){
        new_event = {
            title: "{% trans 'Dovolená' %}",
            start: startDate,
            end: endDate,
            allDay: true,
            vacation: true,
        }
        events = full_calendar.getEvents();
        for (eid in events) {
            if (events[eid].extendedProps.vacation) {
                if (events_overlap(new_event, events[eid])) {
                    e2 = events[eid]
                    return;
                }
            }
        }
        new_event = full_calendar.addEvent(new_event);
        $.post("{% url 'calendar' %}", {
            on_vacation: true,
            start_date: startDateString,
            end_date: endDateString,
            csrfmiddlewaretoken: "{{ csrf_token }}",
        },
               function(returnedData){
               }
              ).fail(function(jqXHR, textStatus, errorThrown) {
                  new_event.remove();
                  show_message("{% trans 'Propojení selhalo' %}");
              });
    }
}

function remove_vacation(info) {
    var event = info.event;
    startDateString = format_date(event.start)
    endDateString = format_date(event.end)
    event.remove() //todo remove
    $.post("{% url 'calendar' %}", {
        on_vacation: false,
        start_date: startDateString,
        end_date: endDateString,
        csrfmiddlewaretoken: "{{ csrf_token }}",
    },
           function(returnedData){
               event.remove()
           }
          ).fail(function(jqXHR, textStatus, errorThrown) {
              full_calendar.addEvent(event);
              show_message("{% trans 'Propojení selhalo' %}");
          });
}

document.addEventListener('DOMContentLoaded', function() {
    {% for cm in commute_modes %}
    {% if cm.does_count and cm.eco %}
    var sel = document.getElementById("route_select_{{cm.slug}}");
    for(var key in route_options_{{cm.slug}}){
        var option = document.createElement("option");
        option.value = key;
        option.text = key;
        sel.appendChild(option);
    }

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
        events: {{events|safe}},
        eventOrder: 'order',
        selectable: true,
        lang: '{{ LANGUAGE_CODE }}',
        locale: '{{ LANGUAGE_CODE }}',
        height: 'auto',
        firstDay: 1,
        plugins: [ 'interaction', 'dayGrid', 'list' ],
        selectable: true,
        defaultView: defaultView,
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
            var mode_icon = null;
            if (exp.commute_mode == 'bicycle'){
                mode_icon = document.createElement("i");
                mode_icon.className='fa fa-bicycle xs';
            } else if (exp.commute_mode == 'by_foot') {
                mode_icon = document.createElement("i");
                mode_icon.className='fa fa-running xs';
            }
            if (mode_icon) {
                info.el.firstChild.prepend(mode_icon);
            }
            if (info.event.extendedProps.vacation) { // https://stackoverflow.com/questions/26530076/fullcalendar-js-deleting-event-on-button-click#26530819
                var trash_icon =  document.createElement("i");
                var trash_button = document.createElement("button");
                trash_button.className = 'btn btn-default btn-xs trash-button';
                trash_button.append(trash_icon);
                trash_button.onclick = function(){remove_vacation(info)};
                trash_icon.className = 'fa fa-trash sm';
                info.el.firstChild.append(trash_button);
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
                   "distanceMeters": Number($('#km-'+commute_mode).val()) * 1000,
                }
                display_trip(trip);
                redraw_placeholders();
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
            var num_eco_trips = 0;
            var events_this_day = [];
            var events = full_calendar.getEvents();
            for (i in events){
                if(format_date(events[i].start) == format_date(cell.date)){
                    var event = events[i];
                    events_this_day.push(event);
                    if(event.extendedProps['commute_mode'] && commute_modes[event.extendedProps['commute_mode']].eco){
                        num_eco_trips++;
                    }
                }
            }
            if (num_eco_trips == 1) {
                cell.el.classList.add('one-ride-day');
            } else if (num_eco_trips > 1) {
                cell.el.classList.add('two-ride-day');
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
        redraw_placeholders();
        full_calendar.render();
    });
});
