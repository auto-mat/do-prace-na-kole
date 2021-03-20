import { UserAttendance } from "./userAttendance";
import { Emissions } from "./emissions";

export interface Team {
    members: UserAttendance[],
    name: string,
    icon: string,
    id: number,
    subsidiary: string,
    frequency: number,
    distance: number,
    eco_trip_count: number,
    working_rides_base_count: number,
    emissions: Emissions,
    campaign: string,
    icon_url: string,
    gallery: string,
    gallery_slug: string,
}

export interface RestTeams {
    results: Team[];
    next: string | null;
    previous: string | null;
}
