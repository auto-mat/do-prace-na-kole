import Trip from "./trip";
import CityInCampaign from "./cityInCampaign";

export interface RestTrips {
    results: Trip[];
    next: string | null;
    previous: string | null;
}

export interface RestCityInCampaign {
    results: CityInCampaign[];
}
