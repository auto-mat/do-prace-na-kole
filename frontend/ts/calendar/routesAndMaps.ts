import {load_strings} from "./Localization";
let strings = load_strings();

import * as R from "./render";

import {load_strings_gpx} from "../dropzone/Localization";
load_strings_gpx();

import {commute_modes, csrf_token} from "./globals";
import {
    load_track,
    create_map,
} from "../leaflet";
import * as UIS from './ui_state';
import * as Dropzone from 'dropzone';
import "dropzone/dist/basic.css";
import "dropzone/dist/dropzone.css";
import Trip from "../dpnk/trip";

export class Maps{
    static editable_layers: { [index: string]: L.FeatureGroup} = {};
    static maps: {[index:string]: L.Map} = {};
    public static draw_controls: {[index:string]: any} = {};
    public static route_options: { [index: string]: {[index: string]: any}} = {};
    public static route_option_ids: { [index: string]: {[index:string]: string}} = {};
    public static gpx_files: { [index: string]: any} = {};
    public static dzs: {[index: string]: any } = {};
    public static saved_distances: {[index: string]: number} = {};

    static distance_changed(cm_slug: string) {
        let cm = commute_modes[cm_slug];
        if (cm.distance_important) {
            return UIS.get_selected_distance() * 1000 != Maps.saved_distances[cm_slug];
        } else {
            return false;
        }
    }

    static editable_layer(cm_slug: string) {
        if (typeof Maps.editable_layers[cm_slug] == 'undefined') {
            Maps.get_map(cm_slug);
        }
        return Maps.editable_layers[cm_slug];
    }
    static get_map(cm_slug: string) {
        if (typeof Maps.maps[cm_slug] != 'undefined') {
            return Maps.maps[cm_slug];
        }
        let cm = commute_modes[cm_slug];
        if (cm.distance_important) {
            let map = create_map(`map_${cm_slug}`);
            Maps.editable_layers[cm_slug] = new L.FeatureGroup();
            map.addLayer(Maps.editable_layers[cm_slug]);

            var draw_options = {
                draw: {
                    polygon: (false as false),
                    marker: (false as false),
                    rectangle: (false as false),
                    circle: (false as false),
                    circlemarker: (false as false),
                    polyline: {
                        metric: true,
                        feet: false,
                        showLength: true,
                    }
                },
                edit: {
                    featureGroup: Maps.editable_layers[cm_slug],
                    remove: (true as any),
                },
                //'delete': {}
            };
            var drawControl = new L.Control.Draw(draw_options);
            Maps.draw_controls[cm_slug] = drawControl;
            Maps.draw_controls[cm_slug].addTo(map);
            //@ts-ignore
            map.on(L.Draw.Event.DRAWSTOP, update_distance_from_map_factory(cm_slug));
            //@ts-ignore
            map.on(L.Draw.Event.EDITSTOP, update_distance_from_map_factory(cm_slug));
            //@ts-ignore
            map.on(L.Draw.Event.EDITVERTEX, function(){
                update_distance_from_map_factory(cm_slug)();
            });
            //@ts-ignore
            map.on(L.Draw.Event.DRAWVERTEX, function(e){
                //@ts-ignore
                update_distance_from_map_factory(cm_slug, [e.layers._layers])();
            });
            //@ts-ignore
            map.on(L.Draw.Event.DELETESTOP, update_distance_from_map_factory(cm_slug));
            {
                let cm_slug_closure = cm_slug;
                map.on(L.Draw.Event.CREATED, function (e: {layer: L.Layer}) {
                    Maps.editable_layer(cm_slug_closure).addLayer(e.layer);
                });
            }
            Maps.maps[cm_slug] = map;
            return map;
        }
    }
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
                            Maps.editable_layer(cm_slug_inner).clearLayers();
                            //@ts-ignore
                            gpx.getLayers()[0].getLayers()[0].addTo(Maps.editable_layer(cm_slug_inner));
                            Maps.get_map(cm_slug_inner).fitBounds(Maps.editable_layer(cm_slug_inner).getBounds());
                            //gpx.addTo(Maps.editable_layers[cm_slug_inner]);
                            file.status = Dropzone.SUCCESS;
                            dz.emit("success", file);
                            dz.emit("complete", file);
                            Maps.gpx_files[cm_slug_inner] = file;
                            update_distance_from_map_factory(cm_slug_inner)();
                        });
                        reader.readAsText(file);
                    }
                })(),
            });
        }
    }
}

export function show_map(cm_slug: string){
    for (var cm_slug_to_hide in commute_modes) {
        if (cm_slug_to_hide != cm_slug) {
            hide_map(cm_slug_to_hide);
        }
    }
    $(`#track_holder_${cm_slug}`).show();
    Maps.get_map(cm_slug).invalidateSize();
}

export function hide_map(cm_slug: string){
    $(`#track_holder_${cm_slug}`).hide();
}

export function basic_route_options(cm_slug: string): {[index: string]: any} {
    let options: {[index: string]: any} = {};
    options[strings.manual_entry] = function () {
        $(`#km-${cm_slug}`).val(0);
        $(`#km-${cm_slug}`).prop('disabled', false);
        Maps.editable_layer(cm_slug).clearLayers();
        hide_map(cm_slug);
        $(`#map_shower_${cm_slug}`).hide();
        $(`#gpx_upload_${cm_slug}`).hide();
    };
    options[strings.draw_track] = function () {
        $(`#km-${cm_slug}`).prop('disabled', true);
        Maps.editable_layer(cm_slug).clearLayers();
        $(`#gpx_upload_${cm_slug}`).hide();
        show_map(cm_slug);
    };
    options[strings.upload_gpx] = function () {
        $(`#km-${cm_slug}`).prop('disabled', true);
        Maps.editable_layer(cm_slug).clearLayers();
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
    $(`#km-${cm_slug}`).prop('disabled', true);
    let cm = commute_modes[cm_slug];
    if (cm.distance_important) {
        $(`#km-${cm_slug}`).val(trip.distanceMeters / 1000);
        Maps.saved_distances[cm_slug] = trip.distanceMeters;
        $(`#gpx_upload_${cm_slug}`).hide();
        show_map(cm_slug);
        load_track(
            Maps.get_map(cm_slug),
            `/trip_geojson/` + trip.trip_date + `/` + trip.direction,
            {},
            Maps.editable_layer(cm_slug),
            function(){
                hide_map(cm_slug);
                $(`#km-${cm_slug}`).prop('disabled', false);
            }
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
        if(typeof sel != 'undefined' && sel && sel.value){
            Maps.route_options[cm_slug][sel.value]();
        }
        R.redraw_shopping_cart();
    }
}

export function update_distance_from_map_factory(cm_slug: string, additional_layers?: any) {
   // https://stackoverflow.com/questions/31221088/how-to-calculate-the-distance-of-a-polyline-in-leaflet-like-geojson-io#31223825
    return function () {
        var totalDistance = 0.00000;
        let add_layer_to_distance = function(i: number, layer: L.Polyline){
            var tempLatLng: any = null;
            var latLngs: L.LatLng[] = null;
            if(layer.getLatLngs){
                latLngs = <L.LatLng[]>layer.getLatLngs();
            } else {
                let draw_layer: any = <any>layer;
                latLngs= [];
                $.each(draw_layer, function(n: number, marker){
                    latLngs.push(new L.LatLng(marker._latlng.lat, marker._latlng.lng));
                } );
            }
            $.each(latLngs, function(i: number, latlng){
                if(tempLatLng == null){
                    tempLatLng = latlng;
                    return;
                }
                totalDistance += tempLatLng.distanceTo(latlng);
                tempLatLng = latlng;
            });
        };
        $.each(Maps.editable_layer(cm_slug).getLayers(), add_layer_to_distance);
        if (additional_layers) {
            $.each(additional_layers, add_layer_to_distance);
        }
        $(`#km-${cm_slug}`).val((totalDistance / 1000).toFixed(2));
        R.redraw_shopping_cart();
    }
}

export function save_current_edits(cm_slug: string){
    let cm = commute_modes[cm_slug];
    if (!cm.distance_important) {
        return;
    }
    let dcs = Maps.draw_controls[cm_slug];
    if (dcs._toolbars.edit._activeMode) {
        dcs._toolbars.edit._activeMode.handler.save();
    }
    if (dcs._toolbars.draw._activeMode) {
        dcs._toolbars.draw._activeMode.handler.completeShape();
    }
    let old_distance = UIS.get_selected_distance();
    update_distance_from_map_factory(cm_slug)();
    if (UIS.get_selected_distance() == 0) {
        $(`#km-${cm_slug}`).val(old_distance);
    }
}
