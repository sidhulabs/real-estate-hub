import os
from datetime import datetime
from typing import Any, Dict

import pandas as pd
import requests
from loguru import logger


class LocationStatsGenerator(object):
    def __init__(
        self,
        location: str,
        google_api_key: str = os.environ.get("GOOGLE_GEOCODING_API_KEY"),
        rapid_api_key: str = os.environ.get("RAPID_API_KEY"),
    ) -> None:

        self.location = location
        self.google_api_key = google_api_key
        self.rapid_api_key = rapid_api_key
        self.google_geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.rapid_api_realtor_host = "realty-in-ca1.p.rapidapi.com"
        self.rapid_api_realtor_url = f"https://{self.rapid_api_realtor_host}/properties/get-statistics"

        assert (
            self.google_api_key
        ), "Please set the GOOGLE_GEOCODING_API_KEY environment variable or pass in the API key."
        assert self.rapid_api_key, "Please set the RAPID_API_KEY environment variable or pass in the API key."

        self.lat, self.long = self._get_long_lat()
        self.location_data = self._get_location_data()
        self.as_of_date = datetime.strptime(
            self.location_data["ErrorCode"]["ProductName"].split("[")[-1].replace("]", ""), "%A, %B %d, %Y %I:%M:%S %p"
        ).strftime("%Y-%m-%d")

    def get_general_stats(self) -> pd.DataFrame:
        return pd.DataFrame(self._get_nested_data(0))

    def get_age_distribution(self) -> pd.DataFrame:
        return pd.DataFrame(self._get_nested_data(2)).astype(dtype={"value": "int"})

    def get_population_forecast(self) -> pd.DataFrame:
        return pd.DataFrame(self._get_nested_data(3))

    def get_education(self) -> pd.DataFrame:
        return pd.DataFrame(self._get_nested_data(4))

    def get_marital_status(self) -> pd.DataFrame:
        return pd.DataFrame(self._get_nested_data(5))

    def get_language(self) -> pd.DataFrame:
        return (
            pd.DataFrame(self._get_nested_data(6))
            .astype(dtype={"value": "int"})
            .sort_values(by=["value"], ascending=False)
        )

    def get_income(self) -> pd.DataFrame:
        return pd.DataFrame(self._get_nested_data(7)).astype(dtype={"value": "int"})

    def get_children_at_home(self) -> pd.DataFrame:
        return pd.DataFrame(self._get_nested_data(8))

    def get_rent_or_owned(self) -> pd.DataFrame:
        return pd.DataFrame(self._get_nested_data(9))

    def get_age_of_home_distribution(self) -> pd.DataFrame:
        return pd.DataFrame(self._get_nested_data(10))

    def get_occupations(self) -> pd.DataFrame:
        return (
            pd.DataFrame(self._get_nested_data(11))
            .astype(dtype={"value": "int"})
            .sort_values(by=["value"], ascending=False)
        )

    @logger.catch
    def upload_to_elasticsearch(self, es_client):
        pass

    @logger.catch
    def _get_location_data(self) -> Dict[str, Any]:
        """
        Get location statistics data from Realtor API.

        Args:
            location (str): Location to get statistics for. Could be a city, address, or postal code.

        Raises:
            ValueError: If location cannot be found.

        Returns:
            Dict[str, Any]: Location statistics data.
        """

        if not self.long and not self.lat:
            raise ValueError(f"Could not find {self.location} on Google Maps.")

        logger.info(f"Latitude: {self.lat}, Longitude: {self.long}")

        data = self._get_location_stats()

        if not data:
            raise ValueError(f"Could not find data from Realtor API for {self.location}.")

        return data

    @logger.catch
    def _get_long_lat(self):
        """
        Get latitude and longitude for a city.

        Args:
            location (str): City, postal code or address.
        """

        params = {"address": self.location, "key": self.google_api_key}

        # sending get request and saving the response as response object
        r = requests.get(url=self.google_geocode_url, params=params)

        # get data from response
        data = r.json()

        # location
        location_dict = data["results"][0]["geometry"]["location"]
        lattitude = location_dict["lat"]
        longitude = location_dict["lng"]

        return lattitude, longitude

    @logger.catch
    def _get_location_stats(self):
        """
        Get location statistics from canadian realtor api.

        Args:
            lat (float): Longitude.
            long (float): Latitude.
        """

        querystring = {"CultureId": "1", "Latitude": str(self.lat), "Longitude": str(self.long)}  # return in english

        # header
        headers = {"x-rapidapi-host": self.rapid_api_realtor_host, "x-rapidapi-key": self.rapid_api_key}

        # response
        response = requests.request("GET", self.rapid_api_realtor_url, headers=headers, params=querystring)
        return response.json()  # json format

    def _get_nested_data(self, index: int) -> Dict[str, Any]:
        """
        Get nested data from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary to get nested data from.
            index (int): Index to get nested data from.

        Returns:
            Dict[str, Any]: Nested data.
        """

        try:
            return pd.DataFrame(self.location_data["Data"][index]["value"])
        except IndexError:
            logger.error(f"Could not get nested data at index {index} from `Data` field: {self.location_data}")
            return None
