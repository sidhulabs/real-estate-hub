# Real Estate Hub
[![Tests](https://github.com/sidhulabs/real-estate-hub/actions/workflows/tests.yml/badge.svg)](https://github.com/sidhulabs/real-estate-hub/actions/workflows/tests.yml) [![Build and Publish Docker Image](https://github.com/sidhulabs/real-estate-hub/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/sidhulabs/real-estate-hub/actions/workflows/docker-publish.yml)

Get information about a neighbourhood, home or area in Canada. Useful when looking at new homes to buy. It uses various API's to aggregate info into one place.

The web app displays the following stats:
- General stats
- Age of homes in the area
- Household Income
- Population by Age Group
- Marital Status
- Age of Children
- Education Level
- Rental vs Owned Properties
- Languages
- Jobs of residents

If searching a household:
- Sold history

Commute to Union Station:
- By car
- By transit

The ETL process periodically fetches data for any given location and stores the data into Elasticsearch allowing you to build neighbourhood profiles over time. Applications include finding gentrifying neighbourhoods, tracking neighbourhood quality, etc.

## How to Run

Environment variables required:
- GOOGLE_API_KEY for [Google Geocoding](https://developers.google.com/maps/documentation/geocoding/start)
- RAPID_API_KEY from [Rapid API](https://rapidapi.com/)

If you want to save data to Elasticsearch:
- ELASTIC_API_ID
- ELASTIC_API_KEY

### Local Dev

`poetry run streamlit app/main.py`

### Docker

`docker run -e GOOGLE_API_KEY=$GOOGLE_API_KEY -e RAPID_API_KEY=$RAPID_API_KEY -e ELASTIC_API_ID=$ELASTIC_API_ID -e ELASTIC_API_KEY --rm -it -p 8501:8501 $(docker build .)`

### For Develepors

To install: `poetry install`

To run tests: `poetry run pytest`
