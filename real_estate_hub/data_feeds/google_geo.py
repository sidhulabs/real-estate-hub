import os
import time
from typing import Any, Dict, List, Tuple

import requests
from loguru import logger

from real_estate_hub.config import Config


class GoogleGeo(object):
    def __init__(
        self, location, lat: float = None, long: float = None, google_api_key: str = os.environ.get("GOOGLE_API_KEY")
    ):
        self.location = location
        self.google_api_key = google_api_key
        self.google_api_url = Config.GOOGLE_MAPS_API_URL

        self.google_geo_supported_nearby_place_types = {
            "airport",
            "amusement_park",
            "aquarium",
            "art_gallery",
            "bakery",
            "bank",
            "bar",
            "beatuy_salon",
            "book_store",
            "bowling_alley",
            "bus_station",
            "cafe",
            "campground",
            "car_repair",
            "casino",
            "cemetery",
            "church",
            "city_hall",
            "clothing_store",
            "convenience_store",
            "courthouse",
            "dentist",
            "department_store",
            "doctor",
            "drugstore",
            "electrician",
            "electronics_store",
            "fire_station",
            "funeral_home",
            "gas_station",
            "gym",
            "hair_care",
            "hardware_store",
            "health",
            "hindu_temple",
            "home_goods_store",
            "hospital",
            "laundry",
            "library",
            "liquor_store",
            "local_government_office",
            "locksmith",
            "mosque",
            "movie_theater",
            "museum",
            "night_club",
            "park",
            "pet_store",
            "pharmacy",
            "physiotherapist",
            "plumber",
            "police",
            "post_office",
            "primary_school",
            "restaurant",
            "school",
            "secondary_school",
            "shopping_mall",
            "spa",
            "stadium",
            "storage",
            "store",
            "subway_station",
            "supermarket",
            "synagogue",
            "tourist_attraction",
            "train_station",
            "transit_station",
            "university",
            "veterinary_care",
            "zoo",
        }

        assert self.google_api_key, "Please set the GOOGLE_API_KEY environment variable or pass in the API key."

        if lat and long:
            self.lat = lat
            self.long = long
        else:
            self.lat, self.long = self.get_lat_long()

    @logger.catch
    def make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Makes a request to the Google Maps API.

        The API key is automatically added to the request parameters if not present.

        Args:
            endpoint (str): Google Maps API endpoint to make the request to.
            params (Dict[str, Any]): Params for the API request.

        Returns:
            Dict[str, Any]: JSON response from the API.
        """

        if "key" not in params:
            params["key"] = self.google_api_key

        req = requests.get(url=f"{self.google_api_url}/{endpoint}/json", params=params)

        req.raise_for_status()

        return req.json()

    @logger.catch
    def get_lat_long(self) -> Tuple[float, float]:
        """
        Gets the latitude and longitude of the location.

        Returns:
            Tuple[float, float]: Latitude and longitude of the location.
        """

        params = {"address": self.location, "components": Config.GOOGLE_GEO_FILTERING_COMPONENTS}

        data = self.make_request("geocode", params)

        location_dict = data["results"][0]["geometry"]["location"]
        lattitude = location_dict["lat"]
        longitude = location_dict["lng"]

        return lattitude, longitude

    @logger.catch
    def get_commute_time(self, mode: str) -> str:
        """
        Gets the commute for a specific commute mode, i.e driving, transit.

        Args:
            mode (str): Commute mode.

        Returns:
            str: Commute time
        """

        params = {
            "origin": f"{self.lat},{self.long}",
            "destination": "Union Station Toronto ON",
            "departure_time": "now",
            "mode": mode,
            "avoid": "tolls|ferries|indoor",
        }

        data = self.make_request("directions", params)

        return data["routes"][0]["legs"][0]["duration"]["text"]

    @logger.catch
    def get_nearby_places(self) -> Dict[str, Any]:
        """
        Gets nearby places for a location within a radius.

        Returns:
            Dict[str, Any]: Filtered locations
        """

        params = {
            "location": f"{self.lat},{self.long}",
            "rankby": "distance",
        }
        endpoint = "place/nearbysearch"

        all_results = self._get_all_results(endpoint, params)

        if not all_results:
            return None

        filtered_nearby_places = []

        for result in all_results:
            for data in result["results"]:
                for place_type in data["types"]:
                    if place_type in self.google_geo_supported_nearby_place_types:
                        place = {
                            "Type": place_type.replace("_", " ").title(),
                            "Name": data["name"],
                            # 'icon': data["icon"],
                            # 'Address': data["vicinity"],
                            # 'Rating': str(data.get("rating", "NA")),
                        }
                        filtered_nearby_places.append(place)
                        break
        return filtered_nearby_places

    def _get_all_results(self, endpoint: str, params: Dict[str, Any], all_data=[]) -> List[Dict[str, Any]]:
        """
        Gets all results for a given endpoint.

        Args:
            endpoint (str): Google Maps API endpoint to make the request to.
            params (Dict[str, Any]): Params for the API request.

        Returns:
            List[Dict[str, Any]]: All results for the endpoint.
        """

        data = self.make_request(endpoint, params)

        all_data.append(data)

        if "next_page_token" not in data:
            return all_data

        params = {
            "pagetoken": data["next_page_token"],
        }

        # From Google's docs, need to wait a bit before making next page request
        time.sleep(1.5)

        return self._get_all_results(endpoint, params, all_data)
