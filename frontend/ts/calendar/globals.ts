import {load_strings} from "./Localization";
let strings = load_strings();
import CommuteMode from "../dpnk/commuteMode";
import Trip from "../dpnk/trip";
import { Calendar } from '@fullcalendar/core';
import {EventInput} from '@fullcalendar/core/structs/event';

export var csrf_token: string;
export var commute_modes: {[index: string]: CommuteMode};
export var day_types: {[index: string]: [string]};
export var possible_vacation_days: [string];
export var active_days: [string];
export var locked_days: [string];
export var wp_api_url: string;
export var calendar_url: string;
export var initial_events: EventInput[];
export var interactive_entry_enabled: boolean;
export const typical_directions = ["trip_to", "trip_from"];
export const direction_names: {[index: string]: string} = {
    "trip_to": strings.trip_to,
    "trip_from": strings.trip_from,
    "recreational": strings.recreational,
}

export function load_globals() {
    //@ts-ignore
    csrf_token = window.csrf_token;
    //@ts-ignore
    commute_modes = window.commute_modes;
    //@ts-ignore
    let possible_vacation_days_ = window.day_types["possible-vacation-day"];
    possible_vacation_days_.sort();
    possible_vacation_days = possible_vacation_days_;
    //@ts-ignore
    day_types = window.day_types;
    //@ts-ignore
    active_days = window.day_types["active-day"];
    //@ts-ignore
    locked_days = window.day_types["locked-day"];
    //@ts-ignore
    wp_api_url = window.wp_api_url;
    //@ts-ignore
    calendar_url = window.calendar_url;
    //@ts-ignore
    initial_events = window.initial_events;
    //@ts-ignore
    interactive_entry_enabled = window.interactive_entry_enabled;
}

export class Globals {
    public static possible_vacation_days: [string] = possible_vacation_days;
    public static full_calendar: Calendar;
    public static placeholder_events: EventInput[] = []
    public static vacation_events: EventInput[] = []
    public static displayed_trips: Trip[] = []
    public static editing: boolean = true;
}
