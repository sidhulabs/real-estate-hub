import pytest

from real_estate_hub.data_feeds.google_geo import GoogleGeo


@pytest.fixture(scope="session")
def location():
    return GoogleGeo("1 bedford road")


def test_commute_driving_time(location):
    assert location.get_commute_time("driving") is not None


def test_commute_transit_time(location):
    assert location.get_commute_time("transit") is not None


def test_get_nearby(location):
    assert location.get_nearby_places() is not None
