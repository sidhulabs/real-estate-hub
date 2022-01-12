import pytest

from real_estate_hub.data_generators.zolo_scraper import ZoloScraper

@pytest.fixture(scope="session")
def zolo_scraper():
    return ZoloScraper("37 O'donnell Avenue")

def test_get_sold_history(zolo_scraper):
    assert zolo_scraper.get_sold_history().shape[0] == 3
