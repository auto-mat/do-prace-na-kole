{% load i18n %}
{% load l10n %}
{% get_current_language as current_language_code %}

function start_editing(){
    editing = true;
    $('#edit-button-activator').hide();
    $('.editation').show();
    redraw_everything_trip_related();
    full_calendar.render();
    load_initial_trips();
}

$('.nav-tabs').on('shown.bs.tab', redraw_shopping_cart);

{% for cm in commute_modes %}
{% if cm.does_count and cm.eco %}
$('#km-{{cm.slug}}').bind('keyup change mouseup', redraw_shopping_cart)
{%endif%}
{%endfor%}

function redraw_shopping_cart(){
    full_calendar.getEventSourceById(2).refetch();
    commute_mode = get_selected_commute_mode();
    start = "Máte vybráno ";
    mid = " "
    end = (commute_modes[commute_mode].does_count && commute_modes[commute_mode].eco) ? get_selected_distance() + " km" : "";
    $('#trip-shopping-cart').text(start + commute_modes[commute_mode].name + mid + end);
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

function get_vacation_events(fetchInfo, successCallback, failureCallback){
    vacation_events = [];
    var current_vacation_start = null;
    var possible_vacation_day = null;
    function close_out_vacation_if_needed() {
        if(current_vacation_start) {
           new_event =  {
               title: "{% trans 'Dovolená' %}",
               start: current_vacation_start,
               end: possible_vacation_day,
               allDay: true,
               vacation: true,
               eventOrder: 'order',
               order: 1,
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


function get_wordpress_events(fetchInfo, successCallback, failureCallback){
    $.getJSON('{{campaign.wp_api_url}}/feed/?orderby=start_date&feed=content_to_backend&_post_type=locations&_page_subtype=event&_number=100&_post_parent={{user_attendance.team.subsidiary.city.slug}}', function ( data ) {
        used_dates = [];
        events_by_day = {};
        for (i in data) {
            event = data[i];
            if(event.start_date.startsWith("{{campaign.year}}")){
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
        return db - da;
    });
    {% for cm in commute_modes %}
    {% if cm.does_count and cm.eco %}
    route_options_{{cm.slug}} = jQuery.extend({}, basic_route_options_{{cm.slug}});
    route_option_ids_{{cm.slug}} = jQuery.extend({}, basic_route_option_ids_{{cm.slug}});
    var sel = $("#route_select_{{cm.slug}}");
    sel.children().remove();
    sel = sel[0];
    for(var i in displayed_trips) {
        var trip = displayed_trips[i];
        if (trip.commuteMode == '{{cm.slug}}') {
            var desc = "{% trans 'Stejně jako' %} " + trip.trip_date + "  " + direction_names[trip.direction] + " (" + display_meters(trip.distanceMeters) + " km)";
            (function () {
                var local_trip = trip; // Thanks! http://reallifejs.com/the-meat/getting-closure/never-forget/
                route_options_{{cm.slug}}[desc] = function () {
                    select_old_trip_{{cm.slug}}(local_trip);
                };
                route_option_ids_{{cm.slug}}[desc] = "option-{{cm.slug}}" + trip.trip_date + trip.direction;
            })();
       }
    }
    for(var key in route_options_{{cm.slug}}){
        var option = document.createElement("option");
        option.value = key;
        option.text = key;
        option.id = route_option_ids_{{cm.slug}}[key];
        sel.appendChild(option);
    }
    {% endif %}
    {% endfor %}
}

function show_tooltip(el, title) {
    el.setAttribute("title", title)
    el.setAttribute("data-toggle", "tooltip")
    el.setAttribute("data-placement", "left")
    $(document.body).tooltip({ selector: "[title]" });
}


function eventRender(info) {
    // Remove time column from Agenda view
    if(info.el.children[0].classList.contains("fc-list-item-time")){
        info.el.children[1].remove();
        info.el.children[0].remove();
        info.el.children[0].colSpan=3
    }

    // Add buttons and icons to events
    var right_icon = null;
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
        if (exp.placeholder) {
            show_tooltip(info.el, commute_modes[get_selected_commute_mode()].add_command.replace("\{\{distance\}\}", get_selected_distance()).replace("\{\{direction\}\}", exp.direction == 'trip_to' ? "{% trans 'do práce' %}" : "{% trans 'domu' %}"))
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
            info.el.firstChild.append(right_icon);
        }
        if (exp.commute_mode) {
            var mode_icon = document.createElement("div");
            mode_icon.className='mode-icon-container';
            mode_icon.innerHTML = decodeURIComponent(commute_modes[exp.commute_mode].icon_html);
            info.el.firstChild.prepend(mode_icon);
        }
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
