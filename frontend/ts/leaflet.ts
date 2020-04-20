import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";
import "../less/leaflet.less"
import 'leaflet';
import 'leaflet-draw';
import 'leaflet-gpx';
import {load_strings} from "./leaflet/Localization";

const strings = load_strings();

// Hack to fix Leaflet Draw behaviour, which added point when moving map.
$(document).ready(function() {
    //@ts-ignore
    var originalOnTouch = L.Draw.Polyline.prototype._onTouch;
    //@ts-ignore
    L.Draw.Polyline.prototype._onTouch = function( e: any ) {
        if( e.originalEvent.pointerType != 'mouse' ) {
            if(this._calculateFinishDistance(e.latlng) > 10){ // dissables https://github.com/Leaflet/Leaflet.draw/blob/6e4e2c3806dcaeab2e569a82d5c6d2081b2e51db/src/draw/handler/Draw.Polyline.js#L305
                return originalOnTouch.call(this, e);
            }
        }
    }
    // https://github.com/Leaflet/Leaflet.draw/issues/789
    //@ts-ignore
    L.Draw.Polyline.prototype._updateFinishHandler = function( e: any ) {
        var markerCount = this._markers.length;
        // The last marker should have a click handler to close the polyline
        if (markerCount > 2) {
            setTimeout(function(){
                if ( this._markers === undefined ) {
                    return;
                }
                this._markers[this._markers.length - 1].on('click', this._finishShape, this);
            }.bind(this), 300);
        }
        // Remove the old marker click handler (as only the last point should close the polyline)
        if (markerCount > 2) {
            this._markers[markerCount - 2].off('click', this._finishShape, this);
        }
    }
});

// https://gis.stackexchange.com/questions/68489/loading-external-geojson-file-into-leaflet-map#98411
export function load_track (map: L.Map, trip_url: string, options: any, editable_layers: L.LayerGroup, on_no_track: any) {
    var track_geojson = L.geoJSON();
    if(editable_layers) {
        editable_layers.clearLayers();
    }
    $.ajax({
        dataType: "json",
        url: trip_url,
        success: function(data) {
            track_geojson.addData(data);
            if(editable_layers) {
                var layers = track_geojson.getLayers();
                editable_layers.clearLayers();
                for (var i in layers) {
                    let layer = layers[i]
                    //@ts-ignore
                    let latlngs = layer._latlngs
                    for(var n in latlngs) {
                        let coord_array = latlngs[n]
                        let polyline = new L.Polyline(coord_array);
                        editable_layers.addLayer(polyline);
                    }
                }
            } else {
                track_geojson.addTo(map);
            }
            map.fitBounds(track_geojson.getBounds())
        },
        error: function() {
            if(typeof on_no_track != 'undefined') {
                on_no_track();
            }
        }
    });
}

export function load_route_list(
    sel_tag: string,
    num_basic_options: number,
    route_options: string[],
    route_option_ids: {[index: string]: string},
){
    var jsel = $(sel_tag);
    $(jsel.children()).remove();
    var sel = jsel[0];
    var i = 0;
    var first_group: HTMLOptGroupElement = document.createElement("optgroup");
    first_group.label = "---";
    var second_group: HTMLOptGroupElement = document.createElement("optgroup");
    second_group.label = strings.same_as;
    for(var key in route_options){
        var desc = route_options[key];
        var option = document.createElement("option");
        option.value = desc;
        option.text = desc;
        option.id = route_option_ids[desc];
        if (i++ < num_basic_options){
            first_group.appendChild(option);
        } else {
            second_group.appendChild(option);
        }
    }
    sel.appendChild(first_group);
    sel.appendChild(second_group);
}


export function create_map(element_id: string){
    let options = {
        maxZoom: 18,
        minZoom: 7,
    };
    var map = L.map(element_id, options).setView(
        [50.0866699218750000, 14.4387817382809995],
        8,
    );
    var baseMaps: {[index: string]: L.TileLayer} = {
        'cyklomapa': L.tileLayer(
            'https://tiles.prahounakole.cz/{z}/{x}/{y}.png',
            {attribution: '&copy; přispěvatelé <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}),
        'Všeobecná mapa': L.tileLayer(
            'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            {attribution: '&copy; přispěvatelé <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'})
    };
    baseMaps["cyklomapa"].addTo(map);
    L.control.layers(baseMaps).addTo(map);
    return map;
}
