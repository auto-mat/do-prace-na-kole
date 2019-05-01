{% load i18n %}
{% load l10n %}
{% get_current_language as current_language_code %}

function start_editing(){
    // Dissabled now
    editing = true;
    $('#edit-button-activator').hide();
    $('.editation').show();
    redraw_everything_trip_related();
    full_calendar.render();
    load_initial_trips(true);
}

$('.nav-tabs').on('shown.bs.tab', function(){
    redraw_shopping_cart();
    {% for cm in commute_modes %}
    {% if cm.does_count and cm.eco %}
    hide_map_{{cm.slug}}();
    {%endif%}
    {%endfor%}
    load_initial_trips();
});

{% for cm in commute_modes %}
{% if cm.does_count and cm.eco %}
$('#km-{{cm.slug}}').bind('keyup change mouseup', redraw_shopping_cart)
{%endif%}
{%endfor%}

function redraw_shopping_cart(){
    full_calendar.getEventSourceById(2).refetch();
    commute_mode = get_selected_commute_mode();
    $('#trip-shopping-cart').text(decode_tooltip(commute_mode, ""));
}

function get_placeholder_events(fetchInfo, successCallback, failureCallback){
    if (!editing) {
        return successCallback([]);
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
           if(directions.indexOf(typical_directions[i]) == -1){
               new_event =  {
                   title: "+",
                   start: active_day,
                   end: add_days(new Date(active_day), 1),
                   order: i,
                   allDay: true,
                   placeholder: true,
                   direction: typical_directions[i],
                   classNames: [
                       'cal_event_'+typical_directions[i],
                       "active-trip-unfilled",
                   ],
               }
               placeholder_events.push(new_event);
           }
       }
    }
    successCallback(placeholder_events);
}

function get_vacation_events(fetchInfo, successCallback, failureCallback){
    vacation_events = [];
    var current_vacation_start = null;
    var possible_vacation_day = null;
    function close_out_vacation_if_needed() {
        if(current_vacation_start) {
            var vacation_end = possible_vacation_day;
            new_event =  {
                title: "{% trans 'Dovolená' %}",
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
        for (n in displayed_trips) {
            var trip = displayed_trips[n];
            if(trip.trip_date == possible_vacation_day && trip.commuteMode == 'no_work'){
                directions.push(trip.direction);
            }
        }
        num_trips = 0;
        for(n in typical_directions) {
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


function get_wordpress_events(fetchInfo, successCallback, failureCallback){
    $.ajax({
       dataType: "json",
       url: '{{campaign.wp_api_url}}/feed/?orderby=start_date&feed=content_to_backend&_post_type=locations&_page_subtype=event&_number=100&_post_parent={{user_attendance.team.subsidiary.city.slug}}',
       success: function ( data ) {
           used_dates = [];
           events_by_day = {};
           for (i in data) {
               event = data[i];
               if(typeof event.start_date !== 'undefined' && event.start_date.startsWith("{{campaign.year}}")){
                   if(!(event.start_date in events_by_day)) {
                       events_by_day[event.start_date] = [];
                   }
                   events_by_day[event.start_date].push(event);
               }
           }
           events = [];
           for (day in events_by_day) {
               for (i in events_by_day[day]) {
                   new_event = {
                       start: day,
                       end: add_days(new Date(day), 1),
                       eventOrder: 'order',
                       order: 3,
                       allDay: true,
                       wp_event: events_by_day[day][i],
                       title: "{% trans 'Akce' %} ",
                   }
                   events.push(new_event);
               }
           }
           successCallback(events);
       },
       timeout: 1000
    }).fail(function(data){
       successCallback([]);
    });
}


function redraw_everything_trip_related() {
    full_calendar.getEventSourceById(2).refetch();
    full_calendar.getEventSourceById(3).refetch();
    {% if interactive_entry_enabled %}
    reload_route_options();
    {% endif %}
}

function display_meters(meters){
    return (meters / 1000).toFixed(0).toLocaleString("{{ current_language_code }}")
}

function reload_route_options() {
    displayed_trips.sort(function(a, b) {
        da = Date.parse(a.trip_date);
        db = Date.parse(b.trip_date);
        if (a.trip_date == b.trip_date) {
            if (a.direction == 'trip_to') {
                return 1;
            } else {
                return -1;
            }
        }
        return db - da;
    });
    {% for cm in commute_modes %}
    {% if cm.does_count and cm.eco %}
    route_options_{{cm.slug}} = jQuery.extend({}, basic_route_options_{{cm.slug}});
    route_option_ids_{{cm.slug}} = jQuery.extend({}, basic_route_option_ids_{{cm.slug}});
    for(var i in displayed_trips) {
        var trip = displayed_trips[i];
        if (trip.commuteMode == '{{cm.slug}}') {
            var desc = trip.trip_date + "  " + direction_names[trip.direction] + " (" + display_meters(trip.distanceMeters) + " km)";
            (function () {
                var local_trip = trip; // Thanks! http://reallifejs.com/the-meat/getting-closure/never-forget/
                route_options_{{cm.slug}}[desc] = function () {
                    select_old_trip_{{cm.slug}}(local_trip);
                };
                route_option_ids_{{cm.slug}}[desc] = "option-{{cm.slug}}" + trip.trip_date + trip.direction;
            })();
       }
    }
    var num_basic_options = Object.keys(basic_route_options_{{cm.slug}}).length;
    load_route_list(
        "#route_select_{{cm.slug}}",
        num_basic_options,
        route_options_{{cm.slug}},
        route_option_ids_{{cm.slug}}
    );
    {% endif %}
    {% endfor %}
}

function show_tooltip(el, title) {
    el.setAttribute("title", title)
    el.setAttribute("data-toggle", "tooltip")
    el.setAttribute("data-placement", "left")
    $(document.body).tooltip({ selector: "[title]" });
}

function decode_tooltip(commute_mode, direction) {
    return commute_modes[commute_mode].add_command.replace("\{\{distance\}\}", get_selected_distance_string()).replace("\{\{direction\}\}", direction == 'trip_to' ? "{% trans 'do práce' %}" : "{% trans 'domu' %}")
}

function eventRender(info) {
    // Remove time column from Agenda view
    if(info.el.children[0].classList.contains("fc-list-item-time")){
        $(info.el.children[1]).remove();
        $(info.el.children[0]).remove();
        info.el.children[0].colSpan=3
    }

    // Add buttons and icons to events
    var right_icon = null;
    exp = info.event.extendedProps
    if (exp.loading) {
       show_loading_icon_on_event(info);
    }
    if (exp.placeholder) {
        show_tooltip(info.el, decode_tooltip(get_selected_commute_mode(), exp.direction))
    } else if (exp.direction == 'trip_to'){
        show_tooltip(info.el, " {% trans 'Do práce' %} " + info.event.title)
    } else if (exp.direction == 'trip_from') {
        show_tooltip(info.el, " {% trans 'Domů' %} " + info.event.title)
    } else if (exp.wp_event) {
        right_icon = document.createElement("i");
        right_icon.className='fa fa-glass-cheers xs';
        show_tooltip(info.el, $("<textarea/>").html(exp.wp_event.title).text())
    }
    if (right_icon) {
        $(info.el.firstChild).append(right_icon);
    }
    if (exp.commute_mode) {
        var mode_icon = document.createElement("div");
        mode_icon.className='mode-icon-container';
        mode_icon.innerHTML = decodeURIComponent(commute_modes[exp.commute_mode].icon_html);
        $(info.el.firstChild).prepend(mode_icon);
    }
    if (exp.vacation) { // https://stackoverflow.com/questions/26530076/fullcalendar-js-deleting-event-on-button-click#26530819
        show_tooltip(info.el, "{% trans 'Dovolená' %}")
        var trash_icon =  document.createElement("i");
        var trash_button = document.createElement("button");
        trash_button.className = 'btn btn-default trash-button';
        $(trash_button).append(trash_icon);
        trash_button.onclick = function(){remove_vacation(info)};
        trash_icon.className = 'fa fa-trash sm';
        $(info.el.firstChild).prepend(trash_button);
    }
}

function dayRender(cell) {
    var set = false;
    if(active_days.indexOf(format_date(cell.date)) >= 0 || locked_days.indexOf(format_date(cell.date)) >= 0) {
        var num_eco_trips = 0;
        for (i in displayed_trips){
            if(displayed_trips[i].trip_date == format_date(cell.date)){
                var trip = displayed_trips[i];
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
    for (key in day_types) {
        if (day_types[key].indexOf(format_date(cell.date)) >= 0) {
            cell.el.classList.add(key);
            set = true;
        }
    }
    if (!set){
        cell.el.classList.add("out-of-competition-day");
    }
}
