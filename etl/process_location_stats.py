import os
from collections import deque
from datetime import datetime
from typing import Any, Dict, List

import prefect
from elasticsearch import Elasticsearch
from elasticsearch.helpers import parallel_bulk
from prefect import Flow, Parameter, task
from prefect.run_configs import KubernetesRun
from prefect.storage import Docker
from sidhulabs.elastic.client import get_elastic_client

from real_estate_hub.data_generators.location_stats import LocationStatsGenerator

DOCKER_IMAGE = "bigsidhu/real-estate-hub"

storage = Docker(
    registry_url=DOCKER_IMAGE.split("/")[0], image_name=DOCKER_IMAGE.split("/")[1], dockerfile="./Dockerfile"
)

run_config = KubernetesRun(
    image=f"{DOCKER_IMAGE}:{storage.image_tag}",
    env={
        "GOOGLE_GEOCODING_API_KEY": os.environ.get("GOOGLE_GEOCODING_API_KEY"),
        "RAPID_API_KEY": os.environ.get("RAPID_API_KEY"),
        "ELASTIC_API_ID": os.environ.get("ELASTIC_API_ID"),
        "ELASTIC_API_KEY": os.environ.get("ELASTIC_API_KEY"),
    },
)


@task
def test_es_client(es_client: Elasticsearch):
    """Test ES Connection."""

    logger = prefect.context.get("logger")

    logger.info(es_client.info(pretty=True))


@task
def get_data(locations: List[str]) -> List[Dict[str, Any]]:
    """
    Gets location data for each location in the list.

    Adds metadata to the data such as the date the data was processed, the as of date for the stats and the location.
    """

    logger = prefect.context.get("logger")

    data = []
    # Not parallel since I'm cheap and  using a free API which has a request limit :)
    for location in locations:
        logger.info(f"Getting data for {location}")
        loc = LocationStatsGenerator(location)
        loc_data = loc.location_data
        loc_data["location"] = location
        loc_data["asof_date"] = datetime.strptime(loc.as_of_date, "%Y-%m-%d").date()
        loc_data["processed_date"] = datetime.now()
        data.append(loc_data)

    return data


@task
def upload_to_es(es_client: Elasticsearch, data: List[Dict[str, Any]]):
    """Upload data to Elasticsearch index `location_stats`"""
    deque(parallel_bulk(es_client, data, index="location_stats"), maxlen=0)


with Flow("location-stats-etl", storage=storage, run_config=run_config) as flow:

    locations = Parameter("locations", required=True)

    es_client = task(get_elastic_client)("https://elastic.sidhulabs.ca")
    conn_success = test_es_client(es_client)

    locations_data = get_data(locations)

    upload_to_es(es_client, locations_data)

# flow.run(parameters=dict(locations=["Riverdale, ON"]))

flow.register(project_name="Real Estate Hub")
