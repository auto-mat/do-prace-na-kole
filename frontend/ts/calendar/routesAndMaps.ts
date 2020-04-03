import {load_strings} from "./Localization";
let strings = load_strings();

import * as R from "./render";

import {load_strings_gpx} from "../dropzone/Localization";
load_strings_gpx();

import {commute_modes, csrf_token} from "./globals";
import {load_track} from "../leaflet";
import * as Dropzone from 'dropzone';
import "dropzone/dist/basic.css";
import "dropzone/dist/dropzone.css";
import Trip from "../dpnk/trip";

export class Maps{
    public static editable_layers: { [index: string]: L.FeatureGroup} = {};
    public static maps: {[index:string]: L.Map} = {};
    public static route_options: { [index: string]: {[index: string]: any}} = {};
    public static route_option_ids: { [index: string]: {[index:string]: string}} = {};
    public static gpx_files: { [index: string]: any} = {};
    public static dzs: {[index: string]: any } = {};
}

export function load_dropozones() {
    for (var cm_slug in commute_modes) {
        let cm = commute_modes[cm_slug];
        if (cm.distance_important) {
            Maps.dzs[cm_slug]= $(`#gpx_upload_${cm_slug}`).dropzone({
                uploadMultiple: false,
                paramName: "gpx",
                maxFiles: 1,
                acceptedFiles: ".gpx",
                init: function() {
                    this.on("addedfile", function(file: string) {
                        var files_to_remove = this.files.filter(function (f: string) {return f != file});
                        for (var i in files_to_remove) {
                            this.removeFile(files_to_remove[i]);
                        }
                    });
                },
                accept: (function (){
                    let cm_slug_inner = cm_slug;
                    return function(file: any, done: any) { // https://stackoverflow.com/questions/33710825/getting-file-contents-when-using-dropzonejs
                        var reader = new FileReader();
                        var dz = this;
                        reader.addEventListener("loadend", function(event) {
                            let gpx = new L.GPX(<string>event.target.result, {})
                                .on('loaded', function(e: any) {
                                    //let gpx = e.target;
                                    //Maps.maps[cm_slug_inner].fitBounds(gpx.getBounds());
                                });
                            Maps.editable_layers[cm_slug_inner].clearLayers();
                            //@ts-ignore
                            gpx.getLayers()[0].getLayers()[0].addTo(Maps.editable_layers[cm_slug_inner]);
                            Maps.maps[cm_slug_inner].fitBounds(Maps.editable_layers[cm_slug_inner].getBounds());
                            //gpx.addTo(Maps.editable_layers[cm_slug_inner]);
                            update_distance_from_map(cm_slug_inner);
                            file.status = Dropzone.SUCCESS;
                            dz.emit("success", file);
                            dz.emit("complete", file);
                            Maps.gpx_files[cm_slug_inner] = file;
                        });
                        reader.readAsText(file);
                    }
                })(),
            });
        }
    }
}

export function show_map(cm_slug: string){
    $(`#track_holder_${cm_slug}`).show();
    $(`#map_shower_${cm_slug}`).hide();
    Maps.maps[cm_slug].invalidateSize();
}

export function hide_map(cm_slug: string){
    $(`#track_holder_${cm_slug}`).hide();
    $(`#map_shower_${cm_slug}`).show();
}

export function toggle_map_size(cm_slug: string){
    $(`#map_${cm_slug}`).toggleClass('leaflet-container-default');
    $(`#map_${cm_slug}`).toggleClass('leaflet-container-large');
    $(`#enlarge_map_text_${cm_slug}`).toggle();
    $(`#shrink_map_text_${cm_slug}`).toggle();
    setTimeout(function(){ Maps.maps[cm_slug].invalidateSize()}, 400);
    $('html, body').animate({
        scrollTop: $(`#resize-button-${cm_slug}`).offset().top
    }, 'fast');
}

export function basic_route_options(cm_slug: string): {[index: string]: any} {
    let options: {[index: string]: any} = {};
    options[strings.manual_entry] = function () {
        $(`#km-${cm_slug}`).val(0);
        Maps.editable_layers[cm_slug].clearLayers();
        hide_map(cm_slug);
        $(`#map_shower_${cm_slug}`).hide();
        $(`#gpx_upload_${cm_slug}`).hide();
    };
    options[strings.draw_track] = function () {
        Maps.editable_layers[cm_slug].clearLayers();
        $(`#gpx_upload_${cm_slug}`).hide();
        show_map(cm_slug);
    };
    options[strings.upload_gpx] = function () {
        Maps.editable_layers[cm_slug].clearLayers();
        $(`#gpx_upload_${cm_slug}`).show();
        show_map(cm_slug);
    };
    return options;
}

export function basic_route_option_ids(cm_slug: string): {[index: string]: string} {
    let ids: {[index: string]: string} = {};
    ids[strings.manual_entry] = `option_enter_distance_${cm_slug}`;
    ids[strings.draw_track] = `option_draw_${cm_slug}`;
    ids[strings.upload_gpx] = `option_gpx_${cm_slug}`;
    return ids;
}

export function select_old_trip(cm_slug: string, trip: Trip){
    let cm = commute_modes[cm_slug];
    if (cm.distance_important) {
        $(`#km-${cm_slug}`).val(trip.distanceMeters / 1000);
        $(`#gpx_upload_${cm_slug}`).hide();
        show_map(cm_slug);
        load_track(
            Maps.maps[cm_slug],
            `/trip_geojson/` + trip.trip_date + `/` + trip.direction,
            {},
            Maps.editable_layers[cm_slug],
            function(){hide_map(cm_slug);}
        );
    }
    if (cm.duration_important) {
        $(`#duration-min-${cm_slug}`).val(trip.durationSeconds / 60);
    }
    R.redraw_shopping_cart();
}

export function on_route_select(cm_slug: string) {
    return function () {
        var sel = <HTMLSelectElement>document.getElementById(`route_select_${cm_slug}`);
        if(sel.value){
            Maps.route_options[cm_slug][sel.value]();
        }
        R.redraw_shopping_cart();
    }
}

export function update_distance_from_map(cm_slug: string) {
   // https://stackoverflow.com/questions/31221088/how-to-calculate-the-distance-of-a-polyline-in-leaflet-like-geojson-io#31223825
    return function () {
        var totalDistance = 0.00000;
        $.each(Maps.editable_layers[cm_slug].getLayers(), function(i, layer: L.Polyline){
            var tempLatLng: any = null;
            $.each(layer.getLatLngs(), function(i, latlng){
                if(tempLatLng == null){
                    tempLatLng = latlng;
                    return;
                }
                totalDistance += tempLatLng.distanceTo(latlng);
                tempLatLng = latlng;
            });
        });
        $(`#km-${cm_slug}`).val((totalDistance / 1000).toFixed(2));
        R.redraw_shopping_cart();
    }
}
