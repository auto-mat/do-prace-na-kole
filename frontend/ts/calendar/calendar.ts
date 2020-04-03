import {
    display_meters,
    reload_route_options,
} from "./render";

import {
    typical_directions,
    commute_modes,
    active_days,
    possible_vacation_days,
    Globals,
} from "./globals";

import {
    add_days,
} from "./util"

import Trip from "../dpnk/trip";

export function display_trip(trip: Trip, rerender: boolean) {
    Globals.displayed_trips.push(trip);
    if ((possible_vacation_days.indexOf(trip.trip_date) >= 0) && !commute_modes[trip.commuteMode].does_count) {
        return
    }
    var trip_class = 'locked-trip';
    if (active_days.indexOf(trip.trip_date) >= 0) {
      trip_class = 'active-trip-filled';
    }
    trip_class += ' cal_event_'+trip.direction
    var commute_mode = commute_modes[trip.commuteMode];
    if(commute_mode.eco){
        trip_class += ' cal_event_eco'
    } else {
        trip_class += ' cal_event_not_eco'
    }
    if(commute_mode.does_count){
        trip_class += ' cal_event_counts'
    } else {
        trip_class += ' cal_event_does_not_count'
    }
    let new_event = {
        start: trip.trip_date,
        end: add_days(new Date(trip.trip_date), 1),
        order: typical_directions.indexOf(trip.direction),
        allDay: true,
        commute_mode: trip.commuteMode,
        direction: trip.direction,
        trip_id: trip.id,
        className: trip_class,
        title: "",
    }
    if (commute_mode.distance_important) {
        new_event.title = new_event.title.concat(display_meters(trip.distanceMeters as number) + " km ");
    }
    if (commute_mode.duration_important) {
        new_event.title = new_event.title.concat(`${trip.durationSeconds as number / 60} min`);
    }
    Globals.full_calendar.addEvent(new_event);
    if(rerender){
        reload_route_options();
        Globals.full_calendar.render();
    }
}
