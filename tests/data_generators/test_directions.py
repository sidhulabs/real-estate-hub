import pytest

from real_estate_hub.data_feeds.google.directions import GoogleDirections


@pytest.fixture(scope="session")
def commute():
    return GoogleDirections("Rosedale, ON")


def test_commute_driving_time(commute):
    assert commute.driving_commute_time is not None


def test_commute_transit_time(commute):
    assert commute.transit_commute_time is not None
