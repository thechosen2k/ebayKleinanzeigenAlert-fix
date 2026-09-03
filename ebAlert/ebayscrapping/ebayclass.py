import re
from typing import Generator, Optional

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from ebAlert import create_logger
from ebAlert.core.config import settings

log = create_logger(__name__)

WANTED_AD_PATTERN = re.compile(r"^\s*suche\b", re.IGNORECASE)


def parse_price(price: str) -> Optional[float]:
    """Extract a numeric EUR amount from a price string like '349 €' or '2.000 € VB'."""
    if not price:
        return None
    match = re.search(r"([\d.,]+)\s*€", price)
    if not match:
        return None
    normalized = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


class EbayItem:
    """Class ebay item"""
    def __init__(self, contents: Tag):
        self.contents = contents
        self._city = None
        self._distance = None
        self._extract_city_distance()

    @property
    def link(self) -> str:
        href = self.contents.get('data-href') or (self.contents.a.get('href') if self.contents.a else None)
        if href:
            return settings.URL_BASE + href
        else:
            return "No url found."

    @property
    def title(self) -> str:
        heading = self.contents.find("h3")
        if heading:
            return heading.get_text(strip=True)
        return "No Title"

    @property
    def price(self) -> str:
        for p in self.contents.find_all("p"):
            text = p.get_text(strip=True)
            if "€" in text:
                return text
        return "No Price"

    @property
    def description(self) -> str:
        paragraphs = self.contents.find_all("p")
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and "€" not in text:
                return text.replace("\n", " ")
        return "No Description"

    @property
    def id(self) -> int:
        return int(self.contents.get('data-adid')) or 0

    @property
    def is_wanted_ad(self) -> bool:
        """True for 'Gesuch' posts (someone looking to buy) rather than actual offers."""
        return bool(WANTED_AD_PATTERN.match(self.title))

    @property
    def city(self):
        return self._city or "No city"

    @property
    def distance(self):
        return self._distance

    def __repr__(self):
        return '{}; {}; {}'.format(self.title, self.city, self.distance)

    def _extract_city_distance(self):
        location_icon = self.contents.find(attrs={"data-title": "locationOutline"})
        if not location_icon:
            return
        location_wrapper = location_icon.parent
        if not location_wrapper:
            return
        details_text = location_wrapper.get_text(" ", strip=True)
        match = re.search(r"(.*?)(?:\s*[·,]?\s*(\d+(?:[.,]\d+)?\s*km))?$", details_text)
        if match:
            self._city = match.group(1).strip() or None
            self._distance = match.group(2)


class EbayItemFactory:
    def __init__(self, link, session: requests.Session = None):
        self.link = link
        self.session = session or requests.Session()
        web_page = self.get_webpage()
        self.page_fetched = web_page is not None
        if web_page:
            raw_items = [EbayItem(article) for article in self.extract_item_from_page(web_page)]
            self.raw_item_count = len(raw_items)
            if not raw_items:
                print(f"<< no items extracted for url: {self.link} - page structure may have changed")
            if settings.FILTER_WANTED_ADS:
                self.item_list = [item for item in raw_items if not item.is_wanted_ad]
            else:
                self.item_list = raw_items
        else:
            self.raw_item_count = 0
            self.item_list = []

    def get_webpage(self) -> str:
        custom_header = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }
        try:
            response = self.session.get(self.link, headers=custom_header, timeout=15)
        except requests.RequestException as exc:
            print(f"<< webpage fetching error for url: {self.link} ({exc})")
            return None
        if response.status_code == 200:
            response.encoding = response.apparent_encoding
            return response.text
        else:
            print(f"<< webpage fetching error for url: {self.link} (status {response.status_code})")

    @staticmethod
    def extract_item_from_page(text: str) -> Generator:
        cleaned_response = text.replace("&#8203", "")
        soup = BeautifulSoup(cleaned_response, "html.parser")
        result = soup.find(attrs={"id": "srchrslt-adtable"})
        if result:
            for item in result.find_all("article", attrs={"data-adid": True}):
                yield item
