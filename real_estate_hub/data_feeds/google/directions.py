import os

from real_estate_hub.data_feeds.google.core import GoogleAPI


class GoogleDirections(GoogleAPI):
    def __init__(self, location: str, google_api_key: str = os.environ.get("GOOGLE_API_KEY")):

        super().__init__(location, google_api_key)

        self.driving_commute_time = self._get_commute_time("driving")
        self.transit_commute_time = self._get_commute_time("transit")

    def _get_commute_time(self, mode: str) -> str:
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
