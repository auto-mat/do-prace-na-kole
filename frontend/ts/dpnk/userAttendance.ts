import { Emissions } from "./emissions";

export interface UserAttendance {
    id: number,
    rest_url: string,
    name: string,
    frequency: number,
    distnace: number,
    avatar_url: string,
    eco_trip_count: number,
    working_rides_base_count: number,
    emissions: Emissions,
    is_me: boolean,
}
