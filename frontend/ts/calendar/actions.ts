import {load_strings} from "./Localization";
let strings = load_strings();
import {DateInput} from "@fullcalendar/core/datelib/env";
import EventApi from "@fullcalendar/core/api/EventApi";
import Trip from "../dpnk/trip";
import * as UIS from "./ui_state";

import {
    format_date,
    get_trip_url,
    add_days,
    ajax_req_json,
} from "./util";

import {
    calendar_url,
    locked_days,
    commute_modes,
    possible_vacation_days,
    csrf_token,
    Globals,
} from "./globals";

import {
    load_track,
    create_map,
} from "../leaflet";

import {
    show_message,
} from "./renderMessage";

import {
    show_loading_icon_on_event,
    redraw_everything_trip_related,
    update_points,
} from "./render";

import {
    display_trip,
} from "./calendar";

import {
    Maps,
    save_current_edits,
} from "./routesAndMaps";

function add_trip(trip: Trip, file: any, cont: any) {
    trip.sourceApplication = "web";
    var formData = new FormData();
    for(var key in trip) {
        var data: string | number = (trip as any)[key];
        if (key == 'distanceMeters') {
            data = Math.round(<number>data);
        }
        if(data) {
            let data_serialized: string = data.toString();
            formData.append(key, data_serialized);
        }
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
            'X-CSRFToken': csrf_token
        },
        success: function (returndata) {
            $(".tooltip").tooltip("hide");
            Maps.saved_distances[trip.commuteMode] = trip.distanceMeters;
            display_trip(returndata, true);
            update_points();
            cont();
        },
        error: function(jqXHR, status, error) {
            console.log("Error posting trip to rest api.")
            console.log(jqXHR);
            console.log(status);
            console.log(error);
            show_message(strings.connection_error + ":\n" + jqXHR.responseText);
        }
    });
}

function delete_trip(event: EventApi) {
    ajax_req_json(
        '/rest/gpx/' + event.extendedProps.trip_id + '/',
        {},
        'DELETE',
        function (jqXHR: any, status: any) {
           event.remove();
           Globals.displayed_trips = Globals.displayed_trips.filter( function (trip: Trip) {
               return trip.id != event.extendedProps.trip_id
           });
           redraw_everything_trip_related();
           Globals.full_calendar.render();
           update_points();
    });
}

export function add_vacation(startDate: DateInput, endDate: DateInput) {
    let startDateString = format_date(startDate);
    let endDateString = format_date(add_days(endDate, -1));
    if(possible_vacation_days.indexOf(startDateString) >= 0 && possible_vacation_days.indexOf(endDateString) >= 0){
        var new_event_input = {
            title: "",
            start: startDate,
            end: endDate,
            allDay: true,
            loading: true,
        }
        let new_event = Globals.full_calendar.addEvent(new_event_input);
        $.ajax({url: calendar_url,
               type: 'POST',
               dataType: 'json',
               headers: {
                  'X-CSRFToken': csrf_token,
               },
               data: {
                  on_vacation: true,
                  start_date: startDateString,
                  end_date: endDateString,
               },
               success: function(returnedData: any[]){
                   (function (){
                       var new_event_local = new_event;
                       new_event_local.remove();
                       for (var i in returnedData) {
                           display_trip(returnedData[i], false);
                       }
                       redraw_everything_trip_related();
                   })()
               },
               error: function(jqXHR, textStatus, errorThrown) {
                  new_event.remove();
                  show_message(strings.connection_error);
              }});
    }
}

export function remove_vacation(info: any) {
    var event = info.event;
    let startDateString = format_date(event.start)
    let endDateString = format_date(add_days(event.end, -1));
    show_loading_icon_on_event(info);
    $.post(calendar_url, {
        on_vacation: false,
        start_date: startDateString,
        end_date: endDateString,
        csrfmiddlewaretoken: csrf_token,
    },
           function(returnedData: any){
               var first_to_delete = possible_vacation_days.indexOf(startDateString);
               var last_to_delete = possible_vacation_days.indexOf(endDateString);
               if (last_to_delete == -1){
                   last_to_delete = possible_vacation_days.length - 1;
               }
               let days_to_delete = possible_vacation_days.slice(
                   first_to_delete,
                   last_to_delete + 1)
               Globals.displayed_trips = Globals.displayed_trips.filter( function (trip: Trip) {
                      return days_to_delete.indexOf(trip.trip_date) < 0;
               });
               Globals.full_calendar.getEventSourceById(3).refetch();
               $(".tooltip").tooltip("hide");
           }
          ).fail(function(jqXHR, textStatus, errorThrown) {
              Globals.full_calendar.addEvent(event);
              show_message(strings.connection_error);
          });
}

export function eventClick(info: any) {
    var commute_mode = UIS.get_selected_commute_mode();
    save_current_edits(commute_mode);
    $(".tooltip").tooltip("hide");
    if(info.event.extendedProps.vacation){
        return;
    }
    if(info.event.extendedProps.placeholder){
        var distance = UIS.get_selected_distance();
        if (distance <= 0) {
            alert(strings.enter_distance_fist)
            $("#km-"+commute_mode).focus()
            return;
        }
        if (distance > 999) {
            alert(strings.max_distance_error)
            $("#km-"+commute_mode).focus()
            return;
        }
        var trip: Trip = {
           trip_date: format_date(info.event.start),
           direction: info.event.extendedProps.direction,
           commuteMode: commute_mode,
           distanceMeters: 0,
           durationSeconds: 0,
           id: null,

        }
        if (commute_modes[commute_mode].distance_important) {
            trip["distanceMeters"] = UIS.get_selected_distance() * 1000;
            if(commute_modes[trip.commuteMode].minimum_distance && trip.distanceMeters < (commute_modes[trip.commuteMode].minimum_distance * 1000)) {
                show_message(strings.min_distance_error + (commute_modes[trip.commuteMode].minimum_distance) + "km.");
                return;
            }
        }
        if (commute_modes[commute_mode].duration_important) {
            trip["durationSeconds"] = UIS.get_selected_duration() * 60;
            if(commute_modes[trip.commuteMode].minimum_duration && trip.durationSeconds < (commute_modes[trip.commuteMode].minimum_duration)) {
                show_message(strings.min_duration_error + (commute_modes[trip.commuteMode].minimum_duration / 60) + "min.");
                return;
            }
        }
        let els = Maps.editable_layer(commute_mode);
        if (els) {
            let layers = els.getLayers();
            let geojson = {
                type: "MultiLineString",
                coordinates: <any[]>[],
            };
            for(var i in layers) {
                let layer = layers[i];
                let lgeojson = (layer as L.Polyline).toGeoJSON();
                geojson.coordinates.push(lgeojson.geometry.coordinates);
            }
            if(geojson.coordinates.length) {
                trip['track'] = JSON.stringify(geojson);
            }
        }
        show_loading_icon_on_event(info);
        var file = null;
        try {
            file = Maps.gpx_files[commute_mode];
        } catch( e ) {
        }
        add_trip(trip, file, redraw_everything_trip_related);
    }
    let trip_url = get_trip_url(info.event);
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
                load_track(map, "/trip_geojson/" + format_date(info.event.start) + "/" + info.event.extendedProps.direction, {}, null, null);
            }
        });
    }
    if(info.event.extendedProps.wp_event){
        window.open(info.event.extendedProps.wp_event.url);
    }
}
