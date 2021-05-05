import {load_strings} from "./Localization";
let strings = load_strings();
import {EventInput} from '@fullcalendar/core/structs/event';
import {format_date} from "./util";
import 'ts-polyfill/lib/es2015-core';
import {
    day_types,
    commute_modes,
    locked_days,
    active_days,
    interactive_entry_enabled,
    wp_api_url,
    direction_names,
    typical_directions,
    possible_vacation_days,
    Globals,
} from "./globals";
import {load_route_list} from "../leaflet";
import {remove_vacation} from "./actions";
import * as UIS from "./ui_state";
import Trip from "../dpnk/trip";
import {add_days} from "./util";
import {
    basic_route_options,
    basic_route_option_ids,
    select_old_trip,
    hide_map,
    on_route_select,
    Maps,
} from "./routesAndMaps"

import {load_initial_trips} from "../calendar";

export function start_editing(){
    // Dissabled now
    Globals.editing = true;
    $('#edit-button-activator').hide();
    $('.editation').show();
    redraw_everything_trip_related();
    Globals.full_calendar.render();
}

for(var cm_slug in commute_modes) {
    let cm = commute_modes[cm_slug];
    if (cm.distance_important) {
        $(`#km-${cm_slug}`).bind('keyup change mouseup', redraw_shopping_cart);
    }
}

export function redraw_shopping_cart(){
    Globals.full_calendar.getEventSourceById(2).refetch();
    let commute_mode = UIS.get_selected_commute_mode();
    $('#trip-shopping-cart').html(decode_description_string(commute_modes[commute_mode].choice_description, ""));
    $('#trip-shopping-cart-points').html(decode_description_string(commute_modes[commute_mode].points, ""));
}

export function get_placeholder_events(fetchInfo: any, successCallback: any, failureCallback: any){
    if (!Globals.editing) {
        return successCallback([]);
    }
    let placeholder_events = [];
    for(var i in day_types["active-day"]){
       var active_day = day_types["active-day"][i];
       var filled_directions = [];
        // We only create placeholders if there hasn't been a trip in that direction on that day yet.
       for (var x in Globals.displayed_trips) {
           var trip = Globals.displayed_trips[x];
           if(trip.trip_date == active_day){
               filled_directions.push(trip.direction);
           }
       }
       for(var x in typical_directions) {
           if(filled_directions.indexOf(typical_directions[x]) == -1){
               let working_ride = day_types["non-working-day"].indexOf(active_day) == -1;
               let new_event =  {
                   title: '',
                   start: active_day,
                   end: add_days(new Date(active_day), 1),
                   order: x,
                   allDay: true,
                   placeholder: true,
                   direction: typical_directions[x],
                   working_ride: working_ride,
                   classNames: [
                       'cal_event_'+typical_directions[x],
                       "active-trip-unfilled",
                       "active-trip-unfilled-" + (working_ride ? "working" : "vacation"),
                   ],
               }
               placeholder_events.push(new_event);
           }
       }
    }
    successCallback(placeholder_events);
}

export function get_vacation_events(fetchInfo: any, successCallback: any, failureCallback: any){
    let vacation_events: EventInput[] = [];
    var current_vacation_start: null | string = null;
    var possible_vacation_day: null | string = null;
    function close_out_vacation_if_needed() {
        if(current_vacation_start) {
            var vacation_end: string = possible_vacation_day;
            let new_event =  {
                title: strings.vacation,
                start: current_vacation_start,
                end: vacation_end,
                allDay: true,
                vacation: true,
                eventOrder: 'order',
                order: 1,
                commute_mode: 'no_work',
            };
            vacation_events.push(new_event);
            current_vacation_start = null;
        }
    }
    var i;
    for(i=0; i <= possible_vacation_days.length; i++){
        if(possible_vacation_days[i]){
            possible_vacation_day = possible_vacation_days[i];
        }else{
            // Add one day at end so that vacations can end on last day of competition.
            // This is because fullcalendar allDay events end on midnight the next day.
            possible_vacation_day = format_date(add_days(new Date(possible_vacation_day), 1))
        }
        var directions = [];
        for (n in Globals.displayed_trips) {
            var trip = Globals.displayed_trips[n];
            if(trip.trip_date == possible_vacation_day && trip.commuteMode == 'no_work'){
                directions.push(trip.direction);
            }
        }
        let num_trips = 0;
        for(var n in typical_directions) {
            if(directions.indexOf(typical_directions[n]) != -1){
                num_trips++;
            }
        }
        if(num_trips >= 2){
            if(!current_vacation_start){
                current_vacation_start = possible_vacation_day;
            }
        } else close_out_vacation_if_needed();
    }
    close_out_vacation_if_needed();
    successCallback(vacation_events);
}


export function get_wordpress_events(fetchInfo: any, successCallback: any, failureCallback: any){
    $.ajax({
       dataType: "json",
       url: wp_api_url,
       success: function ( data: any ) {
           var used_dates: string[] = [];
            var events_by_day: {[index: string]: Event[]} = {};
           for (var i in data) {
               let event = data[i];
               if(typeof event.start_date !== 'undefined' && event.start_date.startsWith(new Date().getFullYear())){
                   if(!(event.start_date in events_by_day)) {
                       events_by_day[event.start_date] = [];
                   }
                   events_by_day[event.start_date].push(event);
               }
           }
           let events = [];
           for (var day in events_by_day) {
               for (var i in events_by_day[day]) {
                   let new_event = {
                       start: day,
                       end: add_days(new Date(day), 1),
                       eventOrder: 'order',
                       order: 3,
                       allDay: true,
                       wp_event: events_by_day[day][i],
                       title: strings.event,
                   }
                   events.push(new_event);
               }
           }
           successCallback(events);
       },
       timeout: 1000
    }).fail(function(data: any){
       successCallback([]);
    });
}


export function redraw_everything_trip_related() {
    Globals.full_calendar.getEventSourceById(2).refetch();
    Globals.full_calendar.getEventSourceById(3).refetch();
    if (interactive_entry_enabled) {
        reload_route_options();
    }
}

export function display_meters(meters: number): string {
    let km = (meters / 1000);
    return km.toFixed(0);
}

function format_trip_date(trip_date_string: string): string{
    var trip_date = new Date(trip_date_string);
    var date_options = { weekday: 'short', month: 'long', day: 'numeric' };
    return trip_date.toLocaleDateString(document.documentElement.lang, date_options);
}

export function reload_route_options() {
    Globals.displayed_trips.sort(function(a: Trip, b: Trip) {
        let da = Date.parse(a.trip_date);
        let db = Date.parse(b.trip_date);
        if (a.trip_date == b.trip_date) {
            if (a.direction == 'trip_to') {
                return 1;
            } else {
                return -1;
            }
        }
        return db - da;
    });
    Maps.route_options = {};
    Maps.route_option_ids = {};
    for (var cm_slug in commute_modes) {
        let cm = commute_modes[cm_slug];
        if (cm.distance_important) {
            $(`#route_select_${cm_slug}`).change(on_route_select(cm_slug));
            Maps.route_options[cm_slug] = jQuery.extend({}, basic_route_options(cm_slug));
            Maps.route_option_ids[cm_slug] = jQuery.extend({}, basic_route_option_ids(cm_slug));
            for(var i in Globals.displayed_trips) {
                var trip = Globals.displayed_trips[i];
                if (trip.commuteMode == cm_slug) {
                    var desc: string = format_trip_date(trip.trip_date) + "  ";
                    desc += direction_names[trip.direction];
                    desc += " (" + display_meters(trip.distanceMeters) + " km)";
                    (function () {
                        var local_trip = trip; // Thanks! http://reallifejs.com/the-meat/getting-closure/never-forget/
                        var local_cm_slug = cm_slug; // Thanks! http://reallifejs.com/the-meat/getting-closure/never-forget/
                        Maps.route_options[local_cm_slug][desc] = function () {
                            select_old_trip(local_cm_slug, local_trip);
                        };
                        Maps.route_option_ids[cm_slug][desc] = `option-${cm_slug}${trip.trip_date}${trip.direction}`;
                    })();
                }
            }
            var num_basic_options = Object.keys(basic_route_options(cm_slug)).length;
            load_route_list(
                `#route_select_${cm_slug}`,
                num_basic_options,
                Object.keys(Maps.route_options[cm_slug]),
                Maps.route_option_ids[cm_slug]
            );
        }
    }
}

function show_tooltip(el: HTMLElement, title: string) {
    el.setAttribute("title", title)
    el.setAttribute("data-toggle", "tooltip")
    el.setAttribute("data-placement", "bottom")
    $(document.body).tooltip({ selector: "[title]" });
}

function decode_description_string(description_string: string, direction: string) {
    return description_string.replace("\{\{distance\}\}", UIS.get_selected_distance_string()).replace("\{\{direction\}\}", direction == 'trip_to' ? strings.trip_to.toLowerCase() : strings.trip_from.toLowerCase())
}

export function show_loading_icon_on_event(info: any) {
    let el = info.el;
    while (el.firstChild.firstChild) {
        el.firstChild.removeChild(el.firstChild.firstChild);
    }
    var loading_icon = document.createElement("i");
    loading_icon.className = 'fa fa-spinner fa-spin';
    el.firstChild.appendChild(loading_icon);
}

export function eventRender(info: any) {
    // Remove time column from Agenda view
    if(info.el.children[0].classList.contains("fc-list-item-time")){
        $(info.el.children[1]).remove();
        $(info.el.children[0]).remove();
        info.el.children[0].colSpan=3
    }

    // Add buttons and icons to events
    function add_icon(icon_class: string, side: string) {
        var icon = document.createElement("i");
        icon.className=icon_class;
        if (side == 'right') {
            $(info.el.firstChild).append(icon);
        } else {
            $(info.el.firstChild).prepend(icon);
        }
    }
    let exp = info.event.extendedProps;
    if (exp.loading) {
       show_loading_icon_on_event(info);
    }
    if (exp.placeholder) {
        add_icon('fa fa-plus xs', 'right')
        show_tooltip(info.el, decode_description_string(commute_modes[UIS.get_selected_commute_mode()].add_command, exp.direction))
    } else if (exp.direction == 'trip_to'){
        show_tooltip(info.el, ` ${strings.trip_to} ${info.event.title}`)
    } else if (exp.direction == 'trip_from') {
        show_tooltip(info.el, ` ${strings.trip_from} ${info.event.title}`)
    } else if (exp.wp_event) {
        add_icon('fa fa-glass-cheers xs', 'right');
        show_tooltip(info.el, $("<textarea/>").html(exp.wp_event.title).text())
    }
    if (exp.commute_mode) {
        var mode_icon = document.createElement("div");
        mode_icon.className='mode-icon-container';
        mode_icon.innerHTML = decodeURIComponent(commute_modes[exp.commute_mode].icon_html);
        $(info.el.firstChild).prepend(mode_icon);
    }
    if (exp.vacation) { // https://stackoverflow.com/questions/26530076/fullcalendar-js-deleting-event-on-button-click#26530819
        show_tooltip(info.el, strings.vacation)
        var trash_icon =  document.createElement("i");
        var trash_button = document.createElement("button");
        trash_button.className = 'btn btn-default trash-button';
        $(trash_button).append(trash_icon);
        trash_button.onclick = function(){remove_vacation(info)};
        trash_icon.className = 'fa fa-trash sm';
        $(info.el.firstChild).prepend(trash_button);
    }
}

export function dayRender(cell: any) {
    var set = false;
    if(active_days.indexOf(format_date(cell.date)) >= 0 || locked_days.indexOf(format_date(cell.date)) >= 0) {
        var num_eco_trips = 0;
        for (var i in Globals.displayed_trips){
            if(Globals.displayed_trips[i].trip_date == format_date(cell.date)){
                var trip = Globals.displayed_trips[i];
                if(commute_modes[trip.commuteMode].eco){
                    if (trip.commuteMode == 'by_foot' && trip.distanceMeters < 1500){
                        continue;
                    }
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
    for (var key in day_types) {
        if (day_types[key].indexOf(format_date(cell.date)) >= 0) {
            cell.el.classList.add(key);
            set = true;
        }
    }
    if (!set){
        cell.el.classList.add("out-of-competition-day");
    }
}

export function update_points() {
    $.getJSON('/rest/userattendance/?format=json', function( data: any ){
        for (var i in data.results) {
            if(data.results[i].points > 0) {
                $("#points-counter").text(data.results[i].points_display);
            }
        }
    });
}
