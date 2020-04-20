export default interface Trip {
    commuteMode: string;
    trip_date: string;
    direction: string;
    track?: string;
    durationSeconds?: number;
    distanceMeters?: number;
    id?: number;
    sourceApplication?: string;
}
