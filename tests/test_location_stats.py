import pytest

from real_estate_hub.data_feeds.location_stats import LocationStatsGenerator


@pytest.fixture(scope="session")
def loc_data_generator() -> LocationStatsGenerator:
    return LocationStatsGenerator(43.678985, -79.34491009999999)


def test_get_general_stats(loc_data_generator):
    assert loc_data_generator.get_general_stats().shape[0] == 9


def test_get_age_distribution(loc_data_generator):
    assert loc_data_generator.get_age_distribution().shape[0] == 11


def test_get_population_forecast(loc_data_generator):
    assert loc_data_generator.get_population_forecast().shape[0] == 5


def test_get_education(loc_data_generator):
    assert loc_data_generator.get_education().shape[0] == 6


def test_get_marital_status(loc_data_generator):
    assert loc_data_generator.get_marital_status().shape[0] == 6


def test_get_language(loc_data_generator):
    assert loc_data_generator.get_language().shape[0] == 16


def test_get_income(loc_data_generator):
    assert loc_data_generator.get_income().shape[0] == 7


def test_get_children_at_home(loc_data_generator):
    assert loc_data_generator.get_children_at_home().shape[0] == 6


def test_get_rent_or_owned(loc_data_generator):
    assert loc_data_generator.get_rent_or_owned().shape[0] == 2


def test_get_age_of_home_distribution(loc_data_generator):
    assert loc_data_generator.get_age_of_home_distribution().shape[0] == 7


def test_get_occupations(loc_data_generator):
    assert loc_data_generator.get_occupations().shape[0] == 9
