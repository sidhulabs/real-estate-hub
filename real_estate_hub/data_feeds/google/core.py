import os
from typing import Any, Dict, Tuple

import requests
from loguru import logger

from real_estate_hub.config import Config


class GoogleAPI(object):
    def __init__(self, location, google_api_key: str = os.environ.get("GOOGLE_API_KEY")):
        self.location = location
        self.google_api_key = google_api_key
        self.google_api_url = Config.GOOGLE_MAPS_API_URL

        assert self.google_api_key, "Please set the GOOGLE_API_KEY environment variable or pass in the API key."

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
