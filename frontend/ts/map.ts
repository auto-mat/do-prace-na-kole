import LocalizedStrings from 'localized-strings';
import "leaflet.awesome-markers";
import {RestCityInCampaign}  from "./dpnk/cityInCampaign"
import {RestTrips}  from "./dpnk/trip"

import {
    load_track,
    create_map,
} from "./leaflet";

let strings = new LocalizedStrings(
    {
        en:{
            competitors: "Competitors",
        },
        cs:{
            competitors: "Účastnicí",
        }
    },
    {
        customLanguageInterface: function(){return document.documentElement.lang},
    },
)

$(function (){
    var map = create_map('map');

    $.getJSON('/rest/gpx/?format=json', function( data: RestTrips ){
        for (var i in data.results) {
            var trip = data.results[i];
            load_track(map, "/trip_geojson/" + trip.trip_date + "/" + trip.direction, {}, null, function(){});
        }
    });
    $.getJSON('/rest/city_in_campaign/?format=json', function( data: RestCityInCampaign ){
        for (var i in data.results) {
            var city = data.results[i];
            L.marker(
                [city.city__location.latitude, city.city__location.longitude],
                {
                    icon: L.AwesomeMarkers.icon({
                        icon: 'university',
                        prefix: 'fa',
                        className: 'awesome-marker awesome-marker-square',
                        iconAnchor:   [17, 22],
                    }),
                },
            ).on('click', function(city) {
                var city = city;
                console.log(strings);
                return function (){
                    $('#map-info').html(`<h3>${city.city__name}</h3><p><b>${strings.competitors}:</b> ${city.competitor_count}</p>`);
                }
            }(city)).addTo(map);
        }
    });
});
