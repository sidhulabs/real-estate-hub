import _thread

import pandas as pd
import plotly.express as px
import streamlit as st
from loguru import logger
from sidhulabs.elastic.client import get_elastic_client

from real_estate_hub.data_generators.location_stats import LocationStatsGenerator
from real_estate_hub.data_generators.zolo_scraper import ZoloScraper

st.set_page_config(layout="wide", page_title="Real Estate Hub")
st.title("Sidhu Lab's Real Estate Hub")


@st.cache(show_spinner=True, hash_funcs={_thread.LockType: id})
def get_data_generator(name: str) -> LocationStatsGenerator:
    logger.info(f"Getting data for {name}")
    es_client = get_elastic_client("https://elastic.sidhulabs.ca")
    return LocationStatsGenerator(name, es_client=es_client)


@st.cache(show_spinner=True)
def get_zolo_scraper(address: str) -> ZoloScraper:
    logger.info(f"Getting data for {address}")
    return ZoloScraper(address)


name = st.text_input("Address, City, or Postal Code", autocomplete="on")

if name:
    loc_stats = get_data_generator(name)
    zolo_info = get_zolo_scraper(name)

    st.subheader(f"Location Stats for {name} as of {loc_stats.as_of_date}")

    st.map(pd.DataFrame({"lat": [loc_stats.lat], "lon": [loc_stats.long]}))

    with st.expander("Neighbourhood Info", expanded=True):
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

    sold_history = zolo_info.get_sold_history()

    if sold_history is not None:
        with st.expander("Sold History"):
            st.table(sold_history)
