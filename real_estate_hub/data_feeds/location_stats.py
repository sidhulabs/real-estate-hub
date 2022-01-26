import os
from datetime import datetime
from typing import Any, Dict

import pandas as pd
import requests
from elasticsearch import Elasticsearch
from loguru import logger

from real_estate_hub.config import Config


class LocationStatsGenerator(object):
    def __init__(
        self,
        location: str,
        latitude: float,
        longitude: float,
        rapid_api_key: str = os.environ.get("RAPID_API_KEY"),
        es_client: Elasticsearch = None,
    ) -> None:

        self.location = location
        self.lat = latitude
        self.long = longitude
        self.rapid_api_key = rapid_api_key
        self.rapid_api_realtor_host = Config.RAPID_API_REALTOR_HOST
        self.rapid_api_realtor_url = f"https://{self.rapid_api_realtor_host}/properties/get-statistics"
        self.es_client = es_client

        assert self.rapid_api_key, "Please set the RAPID_API_KEY environment variable or pass in the API key."

        results = {"hits": {"hits": []}}
        if self.es_client:
            try:
                results = es_client.search(
                    index=Config.ELASTICSEARCH_INDEX,
                    body={
                        "size": 1,
                        "sort": [{"asof_date": {"order": "desc"}}],
                        "query": {
                            "bool": {
                                "must": [{"match": {"location": f"{self.location}*"}}],
                                "filter": [{"range": {"processed_date": {"gte": "now-30d"}}}],
                            }
                        },
                    },
                )
            except Exception as e:
                logger.error(f"Could not retrieve data for {location} from Elasticsearch: {e}")

        if results["hits"]["hits"]:
            logger.info(f"Retrieving data from Elasticsearch for {location}")
            self.location_data = results["hits"]["hits"][0]["_source"]
        else:
            logger.info("Location {location} not found in Elasticsearch. Retrieving data from API.")
            self.location_data = self._get_location_data()
            self.as_of_date = datetime.strptime(
                self.location_data["ErrorCode"]["ProductName"].split("[")[-1].replace("]", ""),
                "%A, %B %d, %Y %I:%M:%S %p",
            ).strftime("%Y-%m-%d")

            self.enhance_location_data()

            if self.es_client:
                logger.info("Uploading data to Elasticsearch")
                try:
                    self.es_client.index(index="location_stats", doc_type="_doc", body=self.location_data)
                except Exception as e:
                    logger.error("Could not upload data to Elasticsearch: {e}")

        self.as_of_date = self.location_data["asof_date"]

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

    def enhance_location_data(self):
        """
        Enhances location data json returned from Rapid API with:
           - longitude & latitude
           - location name
           - date the statistics were captured
           - today's date
        """

        self.location_data["asof_date"] = datetime.strptime(self.as_of_date, "%Y-%m-%d").date()
        self.location_data["processed_date"] = datetime.now()
        self.location_data["location"] = self.location
        self.location_data["latitude"] = self.lat
        self.location_data["longitude"] = self.long

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
