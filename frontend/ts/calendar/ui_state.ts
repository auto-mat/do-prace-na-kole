export function get_selected_commute_mode(): string {
    try {
        return (<HTMLAnchorElement>$("div#nav-commute-modes a.active")[0]).hash.substr("#tab-for-".length);
    } catch (e) {
        //console.log(e);
        return "bicycle";
    }
}

export function get_selected_distance(): number {
    let commute_mode = get_selected_commute_mode();
    return Number($('#km-'+commute_mode).val());
}

export function get_selected_duration(): number {
    let commute_mode = get_selected_commute_mode();
    return Number($('#duration-min-'+commute_mode).val());
}

export function get_selected_distance_string(): string {
    return get_selected_distance().toLocaleString(document.documentElement.lang);
}
