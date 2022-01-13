# Real-estate-hub
Get information about a neighbourhood, home or area.

Environment variables requires:
- GOOGLE_GEOCODING_API_KEY
- RAPID_API_KEY

## How to Run

### Local Dev

`poetry run streamlit app/main.py`

### Docker

`docker run --rm -it -p 8501:8501 $(docker build .)`
