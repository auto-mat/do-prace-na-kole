export default interface CommuteMode {
    eco: boolean,
    name: string,
    add_command: string,
    choice_description: string,
    does_count: boolean,
    icon_html: string,
    points: string,
    minimum_distance: number,
    minimum_duration: number,
    distance_important: boolean,
    duration_important: boolean,
}
