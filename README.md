# Real Estate Hub
[![Tests](https://github.com/sidhulabs/real-estate-hub/actions/workflows/tests.yml/badge.svg)](https://github.com/sidhulabs/real-estate-hub/actions/workflows/tests.yml)

Get information about a neighbourhood, home or area. Useful when looking at new homes to buy.

Displays the following stats:
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

## How to Run

Environment variables required:
- GOOGLE_GEOCODING_API_KEY for [Google Geocoding](https://developers.google.com/maps/documentation/geocoding/start)
- RAPID_API_KEY from [Rapid API](https://rapidapi.com/)

### Local Dev

`poetry run streamlit app/main.py`

### Docker

`docker run -e GOOGLE_GEOCODING_API_KEY=$GOOGLE_GEOCODING_API_KEY -e RAPID_API_KEY=$RAPID_API_KEY  --rm -it -p 8501:8501 $(docker build .)`
