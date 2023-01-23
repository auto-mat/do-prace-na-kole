{% load i18n %}
{% load l10n %}
window.day_types = {
    "possible-vacation-day": {{possible_vacation_days|safe}},
    "active-day": {{active_days|safe}},
    "locked-day": {{locked_days|safe}},
    "non-working-day": {{non_working_days|safe}},
};
var commute_modes = {
    {% for cm in commute_modes %}
    '{{cm.slug}}': {
        'eco': {{cm.eco|yesno:"true,false" }},
        'name': "{{cm.name}}",
        'add_command': "{{cm.add_command}}",
        'choice_description': "{{cm.choice_description|escapejs}}",
        'does_count': {{cm.does_count|yesno:"true,false" }},
        'icon_html': "{{cm.icon_html|urlencode}}",
        'points': "{{cm.points_display}}",
        'minimum_distance': {{cm.minimum_distance|unlocalize}},
        'minimum_duration': {{cm.minimum_duration|unlocalize}},
        'distance_important': {{cm.distance_important|yesno:"true,false" }},
        'duration_important': {{cm.duration_important|yesno:"true,false" }}
    },
    {% endfor %}
}

var interactive_entry_enabled = {{interactive_entry_enabled|yesno:"true,false"}};

document.addEventListener('scroll', function (event) {
    $(".tooltip").tooltip("hide");
}, true /*Capture event*/);

window.csrf_token = "{{ csrf_token }}";
window.calendar_url = "{% url 'calendar' %}";
window.initial_events = {{events|safe}};
window.wp_api_url = '{{campaign.campaign_type.wp_api_url}}/feed/?orderby=start_date&feed=content_to_backend&_post_type=locations&_page_subtype=event&_number=100&_post_parent={{user_attendance.team.subsidiary.city.get_wp_slug}}'
