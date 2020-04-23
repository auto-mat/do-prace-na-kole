import '@fullcalendar/core/main.css';
import '@fullcalendar/daygrid/main.css';
import '@fullcalendar/list/main.css';

import {load_strings} from "./calendar/Localization";
import { Calendar } from '@fullcalendar/core';
import dayGridPlugin from '@fullcalendar/daygrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction';
//@ts-ignore
import * as csLocale from '@fullcalendar/core/locales/cs';
//@ts-ignore
import * as enLocale from '@fullcalendar/core/locales/en-gb';
import { DateInput } from "@fullcalendar/core/datelib/env";
import * as render from "./calendar/render";
import * as actions from "./calendar/actions";
import * as calendar from "./calendar/calendar";
import * as util from "./calendar/util";
import * as UIS from "./calendar/ui_state";
import {
    Maps,
    update_distance_from_map,
    toggle_map_size,
    hide_map,
    show_map,
    on_route_select,
    load_dropozones,
    select_old_trip,
} from './calendar/routesAndMaps';
import {RestTrips} from "./dpnk/rest";
import {
    interactive_entry_enabled,
    initial_events,
    commute_modes,
    Globals,
    load_globals,
} from "./calendar/globals";

let strings = load_strings();

export function load_initial_trips() {
    let mode_selected = false;
    let loaded_modes = [];
    for(var i in Globals.displayed_trips) {
        var trip = Globals.displayed_trips[i];
        let cm_slug = trip.commuteMode;
        let cm = commute_modes[cm_slug];
        if (cm.distance_important || cm.duration_important) {
            if (!mode_selected){
                $("#nav-" + trip.commuteMode + "-tab").tab('show');
                $("#nav-" + trip.commuteMode + "-tab").trigger('click');
                mode_selected = true;
            }
            if (loaded_modes.indexOf(cm_slug) == -1) {
                if(cm.distance_important){
                    $(`#option-${cm_slug}` + trip.trip_date + trip.direction).prop('selected', true);
                    on_route_select(cm_slug)();
                } else if (cm.duration_important) {
                    select_old_trip(cm_slug, trip);
                }
                hide_map(cm_slug);
                loaded_modes.push(cm_slug);
            }
        }
    }
    render.redraw_shopping_cart();
}

function hookup_callbacks() {
    for (var cm_slug_ in commute_modes) {
        (function (){
            var cm_slug = cm_slug_;
            $(`#map_shower_${cm_slug}`).click(function(){show_map(cm_slug)});
            $(`#map_hider_${cm_slug}`).click(function(){hide_map(cm_slug)});
            $(`#resize-map-button-${cm_slug}`).click(function(){toggle_map_size(cm_slug)});
        })();
    }
    $(`#nav-commute-modes`).click(function(){
        for(var cm_slug in commute_modes) {
            let cm = commute_modes[cm_slug];
            if (cm.distance_important) {
                hide_map(cm_slug);
            }
        }
        render.redraw_shopping_cart();
    });

    $(`.enter_km`).on("change paste", function(){
        render.redraw_shopping_cart();
    });
}

function load_trips_from_rest( data: RestTrips ){
    for (i in data.results) {
        calendar.display_trip(data.results[i], false);
    }
    if (data.next) {
        $.getJSON(data.next, load_trips_from_rest);
    } else {
        render.redraw_everything_trip_related();
        load_initial_trips();
        Globals.full_calendar.render();
        if (interactive_entry_enabled) {
            for(var i in Globals.displayed_trips) {
                if(Globals.displayed_trips[i].distanceMeters) {
                    break;
                }
            }
        }
        $(".main-loading-overlay").hide();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    load_globals();
    if (interactive_entry_enabled) {
        hookup_callbacks();
    }
    load_dropozones();
    var calendarEl = document.getElementById('calendar');
    let defaultView: string;
    if($(window).width() > $(window).height()) {
        defaultView = 'dayGridMonth';
    } else {
        defaultView = 'listMonth';
    }
    Globals.full_calendar = new Calendar(calendarEl, {
        eventSources: [
           {events: initial_events},
           {events: render.get_placeholder_events, id: 2},
           {events: render.get_vacation_events, className: "cal-vacation", id: 3},
           {events: render.get_wordpress_events, className: "wp-event", id: 4},
        ],
        eventOrder: 'order',
        locales: [csLocale, enLocale],
        locale: document.documentElement.lang,
        height: 'auto',
        firstDay: 1,
        eventLimit: true,
        plugins: [ interactionPlugin, dayGridPlugin, listPlugin ],
        selectable: true,
        views: {
            dayGrid: {
                eventLimit: 3
            }
        },
        defaultView: defaultView,
        rerenderDelay: 50,
        buttonText: {
          today: strings.today,
          month: strings.month_calendar,
          list: strings.week_calendar,
        },
        header: {
            left: 'title',
            center: '',
            right: 'today, prev,next',
        },
        footer: {
            left: 'dayGridMonth,listMonth',
        },
        dateClick: function(info: {date: DateInput}) {
            actions.add_vacation(info.date, util.add_days(info.date, 1));
        },
        eventRender: render.eventRender,
        eventClick: actions.eventClick,
        dayRender: render.dayRender,
    });
    $.getJSON('/rest/gpx/?format=json', load_trips_from_rest);
});
