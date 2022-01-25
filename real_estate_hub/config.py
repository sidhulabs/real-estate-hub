from strenum import StrEnum


class Config(StrEnum):
    """
    Configuration for the application.
    """

    ELASTICSEARCH_INDEX = "location_stats"

    RAPID_API_REALTOR_HOST = "realty-in-ca1.p.rapidapi.com"

    GOOGLE_GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
    GOOGLE_GEO_FILTERING_COMPONENTS = "country:CA|locality:ON"
