import _thread
import ssl
from datetime import datetime

import elastic_transport
import elasticsearch
import pandas as pd
import plotly.express as px
import streamlit as st
from loguru import logger
from sidhulabs.elastic.client import get_elastic_client

from real_estate_hub.config import Config
from real_estate_hub.data_feeds.google_geo import GoogleGeo
from real_estate_hub.data_feeds.location_stats import LocationStatsGenerator
from real_estate_hub.data_feeds.web.zolo_scraper import ZoloScraper

st.set_page_config(layout="wide", page_title="Real Estate Hub")
st.title("Sidhu Lab's Real Estate Hub")


@st.cache(show_spinner=True)
def get_location_data(lat: float, long: float) -> LocationStatsGenerator:
    return LocationStatsGenerator(lat, long)


@st.cache(
    show_spinner=True,
    hash_funcs={
        elastic_transport.HttpHeaders: id,
        _thread._local: id,
        _thread.LockType: id,
        ssl.SSLContext: id,
        elasticsearch._sync.client.xpack.XPackClient: id,
    },
    allow_output_mutation=True,
)
def get_es_client() -> elasticsearch.Elasticsearch:
    return get_elastic_client("https://elastic.sidhulabs.ca:443")


@st.cache(show_spinner=True)
def get_zolo_scraper(address: str) -> ZoloScraper:
    logger.info(f"Getting data for {address} from Zolo")
    return ZoloScraper(address)


@st.cache(show_spinner=True)
def get_google_directions(location: str, lat: float = None, long: float = None) -> GoogleGeo:
    return GoogleGeo(location, lat=lat, long=long)


es_client = get_es_client()

existing_es_doc = False
non_existing_es_doc = False
update_doc = False

if location := st.text_input("Address, City, or Postal Code"):

    results = es_client.search(
        index="location_stats_test",
        size=1,
        sort=[{"location_stats.asof_date": {"order": "desc"}}],
        query={
            "bool": {
                "must": [{"match_phrase": {"location": f"{location}"}}],
                "filter": [{"range": {"processed_date": {"gte": "now-31d"}}}],
            }
        },
    )

    # If we have a hit for a location in Elasticsearch, get the latitude and longitude for it
    # Else get the latitude and longitude for the location from the Google API
    if results["hits"]["hits"]:
        logger.info(f"Found results for location {location} in Elasticsearch!")

        existing_es_doc = True
        lat, long = (
            results["hits"]["hits"][0]["_source"]["latitude"],
            results["hits"]["hits"][0]["_source"]["longitude"],
        )
        google_directions = get_google_directions(location, lat, long)
    else:
        logger.info(f"No results found for location {location} in Elasticsearch!")

        non_existing_es_doc = True

        try:
            google_directions = get_google_directions(location)
            lat, long = google_directions.lat, google_directions.long
        except Exception as e:
            logger.error(f"Error getting location data from Google for {location}: {e}")
            st.error("Address not found!")
            st.stop()

    logger.info(f"Lat,Long: {lat}, {long}")
    st.subheader(f"Location Stats for {location.title()}")
    st.map(pd.DataFrame({"lat": [lat], "lon": [long]}))

    # If location stats aren't in Elasticsearch, get it from the API
    try:
        loc_stats = LocationStatsGenerator(
            lat, long, location_data=results["hits"]["hits"][0]["_source"]["location_stats"]
        )

        logger.info(f"Using location stats from Elasticsearch for {location}")
    except (IndexError, KeyError) as e:
        logger.info(f"No location stats found in Elasticsearch for {location}")

        update_doc = True
        loc_stats = get_location_data(lat, long)

    with st.expander(f"Neighbourhood Info as of {loc_stats.as_of_date}", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            # General Stats
            st.table(loc_stats.get_general_stats().rename(columns={"key": "Stat", "value": "Value"}))

            # Household income
            income = loc_stats.get_income()
            fig = px.bar(
                income,
                x="key",
                y="value",
                title="Household Income",
                labels=dict(key="Household Income", value="Number of Homes"),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Marital Status
            st.table(loc_stats.get_marital_status().rename(columns={"key": "Marital Status", "value": "Count"}))

            # Education Breakdown
            educations = loc_stats.get_education()
            fig = px.pie(educations, values="value", names="key", title="Education Level")
            st.plotly_chart(fig, use_container_width=True)

            # Language info
            st.table(loc_stats.get_language().rename(columns={"key": "Language", "value": "Count"}).head(10))

        with col2:
            # Home Built by Year
            st.table(
                loc_stats.get_age_of_home_distribution().rename(
                    columns={"key": "Year Built", "value": "Number of Homes"}
                )
            )

            # Population by Age Group
            pop = loc_stats.get_age_distribution()
            fig = px.bar(
                pop,
                x="key",
                y="value",
                title="Population by Age Group",
                labels=dict(key="Age Group", value="Number of People"),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Children at Home
            st.table(
                loc_stats.get_children_at_home().rename(
                    columns={"key": "Age of Children", "value": "Number of Children"}
                )
            )

            # Rent to own stats
            rent_to_own = loc_stats.get_rent_or_owned()
            fig = px.pie(
                rent_to_own,
                values="value",
                names="key",
                title="Proportion of rentals vs. owned Properties",
                labels=dict(key="Type of Property"),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Job Info
            st.table(loc_stats.get_occupations().rename(columns={"key": "Job", "value": "Number of People"}))

    # If nearby places aren't in Elasticsearch, get it from the API
    try:
        nearby_places = results["hits"]["hits"][0]["_source"]["nearby_places"]

        logger.info(f"Using nearby places from Elasticsearch for {location}")
    except (IndexError, KeyError) as e:
        logger.info(f"No nearby places found in Elasticsearch for {location}")

        update_doc = True
        nearby_places = google_directions.get_nearby_places()

    if nearby_places:
        with st.expander("Nearby Places"):
            st.table(pd.DataFrame(nearby_places).drop_duplicates(subset="Name").reset_index(drop=True))

    # If commute times aren't in Elasticsearch, get it from the API
    try:
        commute_times = results["hits"]["hits"][0]["_source"]["commute_times"]

        logger.info(f"Using commute times from Elasticsearch for {location}")
    except (IndexError, KeyError) as e:
        logger.info(f"No commute times found in Elasticsearch for {location}")

        update_doc = True
        commute_times = {
            "driving_commute_time": google_directions.get_commute_time("driving"),
            "transit_commute_time": google_directions.get_commute_time("transit"),
        }

    with st.expander("Commute Times"):
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Driving to Union", commute_times["driving_commute_time"])
        with col2:
            st.metric("Transit to Union", commute_times["transit_commute_time"])

    # Zolo stuff
    zolo_info = get_zolo_scraper(location)
    if sold_history := zolo_info.get_sold_history():
        with st.expander("Sold History"):
            st.table(sold_history)

    doc = {
        "location": location,
        "latitude": lat,
        "longitude": long,
        "location_stats": loc_stats.location_data,
        "nearby_places": nearby_places,
        "commute_times": commute_times,
        "processed_date": datetime.now(),
    }

    # Create new Elasticsearch document if the search is new
    if non_existing_es_doc:
        logger.info(f"Inserting new doc for for {location} into Elasticsearch")
        es_client.index(index="location_stats_test", document=doc)

    # Update existing Elasticsearch document if some data is missing
    if existing_es_doc and update_doc:
        logger.info(f"Updating existing doc for {location} in Elasticsearch")

        es_client.index(index="location_stats_test", document=doc, id=results["hits"]["hits"][0]["_id"])
