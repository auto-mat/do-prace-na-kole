{% load i18n %}
{% load l10n %}
{% load static %}
{% include "registration/util.js" %}
{% include "leaflet/_leaflet_draw_i18n.js" %}
{% get_current_language as current_language_code %}
L.drawLocal.draw.toolbar.finish.text="{% trans 'Finish' %}"; // TODO move this code to django-leaflet or something
L.drawLocal.draw.toolbar.finish.title="{% trans 'Finish drawing' %}";

var editing = false;

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
        'name': "{{cm.name}}",
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
var editable_layers_{{cm.slug}} = null;
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

function toggle_map_size_{{cm.slug}}(){
    $("#map_{{cm.slug}}").toggleClass('leaflet-container-default');
    $("#map_{{cm.slug}}").toggleClass('leaflet-container-large');
    $("#enlarge_map_text_{{cm.slug}}").toggle();
    $("#shrink_map_text_{{cm.slug}}").toggle();
    setTimeout(function(){ map_{{cm.slug}}.invalidateSize()}, 400);
    $('html, body').animate({
        scrollTop: $("#resize-button-{{cm.slug}}").offset().top
    }, 'fast');
}



var route_options_{{cm.slug}} = {};

var gpx_file_{{cm.slug}} = null;

var basic_route_options_{{cm.slug}} = {
    "{% trans 'Zadat vzdálenost ručně' %}": function () {
        $("#km-{{cm.slug}}").val(0);
        hide_map_{{cm.slug}}();
        $("#map_shower_{{cm.slug}}").hide();
        $("#gpx_upload_{{cm.slug}}").hide();
    },
    "{% trans 'Nakreslit trasu do mapy' %}": function () {
        editable_layers_{{cm.slug}}.clearLayers();
        $("#gpx_upload_{{cm.slug}}").hide();
        show_map_{{cm.slug}}();
    },
    "{% trans 'Nahrát GPX soubor' %}": function () {
        editable_layers_{{cm.slug}}.clearLayers();
        $("#gpx_upload_{{cm.slug}}").show();
        show_map_{{cm.slug}}();
    },
};

function select_old_trip_{{cm.slug}}(trip){
    $("#km-{{cm.slug}}").val(trip.distanceMeters / 1000);
    show_map_{{cm.slug}}();
    $("#gpx_upload_{{cm.slug}}").hide();
    load_track(map_{{cm.slug}}, "/trip_geojson/" + trip.trip_date + "/" + trip.direction, {}, editable_layers_{{cm.slug}});
}

function on_route_select_{{cm.slug}}() {
    var sel = document.getElementById("route_select_{{cm.slug}}");
    route_options_{{cm.slug}}[sel.value]();
}

function update_distance_from_map_{{cm.slug}}() {
   // https://stackoverflow.com/questions/31221088/how-to-calculate-the-distance-of-a-polyline-in-leaflet-like-geojson-io#31223825
   var totalDistance = 0.00000;
   $.each(editable_layers_{{cm.slug}}.getLayers(), function(i, layer){
       var tempLatLng = null;
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

Dropzone.autoDiscover = false;
{% include "registration/dropzone-locale.js" %}

dz_{{cm.slug}} = $('#gpx_upload_{{cm.slug}}').dropzone({
    dictDefaultMessage: "{% trans "GPX soubory nahrajete přetažením, nebo kliknutím " %}",
    uploadMultiple: false,
    paramName: "gpx",
    maxFiles: 1,
    acceptedFiles: ".gpx",
    init: function() {
        this.on("addedfile", function(file) {
           var files_to_remove = this.files.filter(function (f) {return f != file});
           for (i in files_to_remove) {
              this.removeFile(files_to_remove[i]);
           }
        });
    },
    accept: function(file, done) { // https://stackoverflow.com/questions/33710825/getting-file-contents-when-using-dropzonejs
        var reader = new FileReader();
        var dz = this;
        reader.addEventListener("loadend", function(event) {
            gpx = new L.GPX(event.target.result, {
            }).on('loaded', function(e) {
            })
            map_{{cm.slug}}.fitBounds(gpx.getBounds());
            editable_layers_{{cm.slug}}.clearLayers();
            gpx.getLayers()[0].getLayers()[0].addTo(editable_layers_{{cm.slug}});
            update_distance_from_map_{{cm.slug}}();
            file.status = Dropzone.SUCCESS;
            dz.emit("success", file);
            dz.emit("complete", file);
            gpx_file_{{cm.slug}} = file;
        });
        reader.readAsText(file);
    },
}); 

{% endif %}
{% endfor %}

{% include "registration/calendar-util.js" %}
{% include "registration/calendar-render.js" %}


function add_trip(trip, file, cont) {
    trip.sourceApplication = "web";
    var formData = new FormData();
    for(key in trip) {
      formData.append(key, trip[key]);
    }
    if (file) {
       formData.append('file', file);
    }
    $.ajax({
        url: '/rest/gpx/',
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        cache: false,
        headers: {
            'X-CSRFToken': "{{ csrf_token }}"
        },
        success: function (returndata) {
            display_trip(returndata, true);
            cont();
        }
    });
}

function delete_trip(event) {
    ajax_req_json(
        '/rest/gpx/' + event.extendedProps.trip_id + '/',
        {},
        'DELETE',
        function (jqXHR, status) {
           event.remove();
           displayed_trips = displayed_trips.filter( function (trip) {return trip.id != event.extendedProps.trip_id});
           redraw_everything_trip_related();
           full_calendar.render();
    });
}

function display_trip(trip, rerender) {
    displayed_trips.push(trip);
    if ((possible_vacation_days.indexOf(trip.trip_date) >= 0) && !commute_modes[trip.commuteMode].does_count) {
        return
    }
    var trip_class = 'locked-trip ';
    if (active_days.indexOf(trip.trip_date) >= 0) {
      trip_class = 'active-trip-filled ';
    }
    trip_class += 'cal_event_'+trip.direction
    new_event = {
        start: trip.trip_date,
        end: add_days(new Date(trip.trip_date), 1),
        order: typical_directions.indexOf(trip.direction),
        allDay: true,
        commute_mode: trip.commuteMode,
        direction: trip.direction,
        trip_id: trip.id,
        className: trip_class,
    }
    if (commute_modes[trip.commuteMode].does_count && commute_modes[trip.commuteMode].eco) {
        new_event.title = display_meters(trip.distanceMeters) + "km";
    }
    event = full_calendar.addEvent(new_event);
    if(rerender){
        reload_route_options();
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

function get_selected_commute_mode() {
    return $("div#nav-commute-modes a.active")[0].hash.substr("#tab-for-".length);
}

function get_selected_distance(commute_mode) {
    return Number($('#km-'+commute_mode).val())
}

function eventClick(info) {
    $(".tooltip").tooltip("hide");
    if(info.event.extendedProps.placeholder){
        var trip = {
           "trip_date": format_date(info.event.start),
           "direction": info.event.extendedProps.direction,
           "commuteMode": get_selected_commute_mode(),
        }
        if (commute_modes[commute_mode].does_count && commute_modes[commute_mode].eco) {
            trip["distanceMeters"] = get_selected_distance(commute_mode) * 1000;
        }
        els = eval('editable_layers_' + commute_mode);
        if (els) {
            layers = els.getLayers();
            geojson = {
                type: "MultiLineString",
                coordinates: [],
            };
            for(i in layers) {
                layer = layers[i];
                lgeojson = layer.toGeoJSON();
                geojson.coordinates.push(lgeojson.geometry.coordinates);
            }
            if(geojson.coordinates.length) {
                trip['track'] = JSON.stringify(geojson);
            }
        }
        show_loading_icon_on_event(info);
        var file = null;
        try {
            file = eval('gpx_file_' + commute_mode);
        } catch( e ) {
        }
        add_trip(trip, file, redraw_everything_trip_related);
    }
    trip_url = get_trip_url(info.event);
    if(trip_url){
        $('#trip-modal').modal({show:true});
        $('#trip-modal-body').empty();
        $('#trip-modal-spinner').show();
        if(locked_days.indexOf(format_date(info.event.start)) >= 0) {
            $('#trip-lock').show();
            $('#trip-edit-delete').hide();
        } else {
            $('#trip-lock').hide();
            $('#trip-edit-delete').show();
            $('#trip-edit-button').attr("href", "/trip/" + format_date(info.event.start) + "/" + info.event.extendedProps.direction);
            $('#trip-delete-button').unbind('click');
            $('#trip-delete-button').click(function() {
                show_loading_icon_on_event(info);
                delete_trip(info.event);
                $('#trip-modal').modal('toggle');
            });
        }
        $('#trip-modal-body').load(trip_url + " #inner-content", function(){
            $('#trip-modal-spinner').hide();
            if($('#track_map').length) {
                var map = create_map('track_map');
                load_track(map, "/trip_geojson/" + format_date(info.event.start) + "/" + info.event.extendedProps.direction, {});
            }
        });
    }
    if(info.event.extendedProps.wp_event){
        window.open(info.event.extendedProps.wp_event.url);
    }
}

function create_map(element_id){
    var map = L.map(element_id).setView([50.0866699218750000, 14.4387817382809995], 8);
    L.tileLayer('https://tiles.prahounakole.cz/{z}/{x}/{y}.png',
                {
                    attribution: '&copy; přispěvatelé <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                }).addTo(map);
   return map;
}


document.addEventListener('DOMContentLoaded', function() {
    {% if interactive_entry_enabled %}
    {% for cm in commute_modes %}
    {% if cm.does_count and cm.eco %}
    map_{{cm.slug}} = create_map('map_{{cm.slug}}')

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

    {% endif %}
    var calendarEl = document.getElementById('calendar');
    if($(window).width() > $(window).height()) {
        defaultView = 'dayGridMonth';
    } else {
        defaultView = 'listMonth';
    }
    full_calendar = new FullCalendar.Calendar(calendarEl, {
        eventSources: [
           {events: {{events|safe}}},
           {events: get_placeholder_events, className: "active-trip-unfilled", id: 2},
           {events: get_vacation_events, className: "cal-vacation", id: 3},
           {events: get_wordpress_events, className: "wp-event", id: 4},
        ],
        eventOrder: 'order',
        selectable: true,
        lang: '{{ current_language_code }}',
        locale: '{{ current_language_code }}',
        height: 'auto',
        firstDay: 1,
        eventLimit: true,
        plugins: [ 'interaction', 'dayGrid', 'list' ],
        selectable: true,
        defaultView: defaultView,
        rerenderDelay: 50,
        buttonText: {
          today:    '{% trans "Dnes" %}',
          month:    '{% trans "Kalendář" %}',
          list:     '{% trans "Seznam" %}'
        },
        header: {
            left: 'title',
            center: '',
            right: 'today, prev,next',
        },
        footer: {
            left: 'dayGridMonth,listMonth',
        },
        select: function(info) {
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
        {% if interactive_entry_enabled %}
        for(i in displayed_trips) {
            if(displayed_trips[i].distanceMeters) {
                console.log("#nav-" + displayed_trips[i].commuteMode + "-tab");
                $("#nav-" + displayed_trips[i].commuteMode + "-tab").tab('show');
                break;
            }
        }
        {% for cm in commute_modes %}
        {% if cm.does_count and cm.eco %}
        $("#km-{{cm.slug}}").val(0);
        for(i in displayed_trips) {
            if(displayed_trips[i].distanceMeters && displayed_trips[i].commuteMode == '{{cm.slug}}') {
                $("#km-{{cm.slug}}").val(displayed_trips[i].distanceMeters / 1000);
                break;
            }
        }
        {% endif %}
        {% endfor %}
        redraw_shopping_cart();
        {% endif %}
        $(".main-loading-overlay").hide();
    });
});
