import {load_strings} from "./Localization";
let strings = load_strings();

import {show_message} from "./renderMessage";

import {Calendar} from '@fullcalendar/core';
import {EventInput} from '@fullcalendar/core/structs/event';
import {DateInput} from "@fullcalendar/core/datelib/env";

import {commute_modes, csrf_token, Globals} from "./globals";

import DPNKEventProps from "./dpnkEventProps";

function pad(n: string, width: number, z: string) {
    z = z || '0';
    n = n + '';
    return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
}


function date_input_to_date(date_input: DateInput): Date{
    let cal = Globals.full_calendar;
    if (cal) {
        return cal.dateEnv.toDate(cal.dateEnv.createMarker(date_input));
    } else {
        //@ts-ignore
        return new Date(date_input);
    }
}

export function format_date(date_input: DateInput){
    let date = date_input_to_date(date_input);
    return date.getFullYear() + '-' + pad((date.getMonth() + 1).toString(), 2, '0') + '-' + pad(date.getDate().toString(), 2, '0');
}

export function add_days(date_input: DateInput, days: number): Date {
    let new_date = date_input_to_date(date_input);
    new_date.setDate(new_date.getDate() + days);
    return new_date;
}

function events_overlap(event1: EventInput, event2: EventInput): boolean {
    if(event1.end && event2.end) {
        return ((event1.start >= event2.start && event1.start < event2.end) ||
                (event1.end > event2.start && event1.end <= event2.end));
    } else {
        return false;
    }
}

export function get_trip_url(event: EventInput): string {
    let commute_mode = (<DPNKEventProps>event.extendedProps).commute_mode;
    let cmo = commute_modes[commute_mode];
    if(!cmo) return;
    return "/view_trip/" + format_date(event.start) + "/" + (<DPNKEventProps>event.extendedProps).direction
}

export function ajax_req_json(url: string, json: object, method: string, success: any) {
    $.ajax(url, {
        data : JSON.stringify(json),
        contentType : 'application/json',
        'type': method,
        headers: {
            'X-CSRFToken': csrf_token,
        },
        error: function(jqXHR, status, error) {
            if (error) {
                show_message(error + " " + jqXHR.responseText);
            } else if (jqXHR.statusText == 'error') {
                show_message(strings.connection_error);
            }
        },
        success: success
    });
}
