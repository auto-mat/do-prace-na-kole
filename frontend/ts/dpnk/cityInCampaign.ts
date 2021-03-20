export interface Location {
    longitude: number;
    latitude: number;
}

export default interface CityInCampaign {
    city__location: Location;
    city__name: string;
    competitor_count: number;
}

export interface RestCityInCampaign {
    results: CityInCampaign[];
}
