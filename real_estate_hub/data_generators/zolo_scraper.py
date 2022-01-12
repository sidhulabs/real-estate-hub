from __future__ import annotations

import requests
import string
import pandas as pd
from loguru import logger


class ZoloScraper(object):
    
    def __init__(self, address: str):
        self.url = 'https://www.zolo.ca/toronto-real-estate'
        self.address = address

        self.search_address = self.address.lower().translate(str.maketrans('', '', string.punctuation)).replace(" ", "-")

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0",
            "Accept-Language": "en-US,en;q=0.5",
        }

        cookies = {
            "PHPSESSID": "052f1b49bc9b279d68d6911295199cfa",
            "_gid": "GA1.2.1842034191.1641867455",
            "emladr": "ashtontml%40yahoo.com",
            "__cf_bm": "bfQeNl60JfAE42ha8_bArpmCeR3j.kI_crnfcB8A390-1641873736-0-AUpfkEJzN4mwjMMGf6v4r6d0UEyiU5AVjE7rQygGBqYFa3/ZfrlLBMO+IrKNBVMXqJA2+tgo/cNRlC0zIoVFXBw=",
            "__cfruid": "298781a739b44b8470037ab5af4bd60b4bb2423e-1641600804",
            "BSID": "cb5e1fe0-7017-11ec-8aa0-bc764e102e1e",
            "_ga": "GA1.2.1201354367.1637730058",
            "BID": "c0554356-52b8-11ec-8aa0-bc764e102e1e",
        }

        req = requests.get(f"{self.url}/{self.search_address}", headers=headers, cookies=cookies)

        self.html = req.text

    @logger.catch
    def get_sold_history(self) -> pd.DataFrame | None:
        """
        Get historical history of a property from Zolo.

        Returns:
            pd.DataFrame: Pandas Dataframe of sell history
        """

        # Throws a Value Error if no tables found
        try:
            df_tables = pd.read_html(self.html, match="Sold")
        except ValueError:
            logger.warning(f"No Sold History found for {self.search_address}")
            return None
        
        df = df_tables[0]

        if 0 in df.columns:
            df = df.drop(columns=[0])

        df = df[df["Price"].astype("string").str.startswith("$") | df["Price"].isna()]
        
        df.columns = ["MLS #", "Date", "Event", "Price"]
        df["MLS #"] = df["MLS #"].ffill()

        return df


        



        
