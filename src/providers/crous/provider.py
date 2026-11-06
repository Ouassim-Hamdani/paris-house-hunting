from urllib.parse import parse_qs, urlparse

import requests

from src.domain.models import Offer, ProviderName, SearchCriteria
from src.providers import http
from src.providers.base import Provider
from src.providers.crous.bounds import Bounds
from src.providers.crous.client import CrousClient, GeoResult
from src.providers.crous.config import CrousConfig


class CrousProvider(Provider):
    """Criteria handling on top of CrousClient (which owns all API calls)."""

    name = ProviderName.CROUS

    def __init__(self, session: requests.Session | None = None, config: CrousConfig | None = None):
        self.config = config or CrousConfig()
        self.client = CrousClient(session or http.make_session(), self.config)

    # --- setup helpers (used by the Telegram conversation) ---------------
    def geocode(self, query: str, limit: int = 5) -> list[GeoResult]:
        return self.client.geocode(query, limit)

    @staticmethod
    def criteria_from_geo(result: GeoResult) -> SearchCriteria:
        return SearchCriteria({"bounds": str(result.bounds), "label": result.label})

    def criteria_from_link(self, url: str) -> SearchCriteria:
        """Extract bounds from a pasted CROUS link (the pasted URL itself is never fetched)."""
        u = urlparse(url.strip())
        if u.scheme != "https" or u.hostname != self.config.host:
            raise ValueError(f"Only https://{self.config.host} links are allowed")
        qs = parse_qs(u.query)
        criteria = SearchCriteria(
            {"bounds": qs.get("bounds", [""])[0], "label": qs.get("locationName", ["custom link"])[0]}
        )
        self.validate_criteria(criteria)
        return criteria

    # --- Provider interface ----------------------------------------------
    def validate_criteria(self, criteria: SearchCriteria) -> None:
        Bounds.parse(criteria.data.get("bounds", ""))

    def search(self, criteria: SearchCriteria) -> list[Offer]:
        self.validate_criteria(criteria)
        return self.client.search(Bounds.parse(criteria.data["bounds"]))
