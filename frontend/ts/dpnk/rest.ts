import Trip from "./trip";
import CityInCampaign from "./cityInCampaign";

export interface RestTrips {
    results: Trip[];
}

export interface RestCityInCampaign {
    results: CityInCampaign[];
}
