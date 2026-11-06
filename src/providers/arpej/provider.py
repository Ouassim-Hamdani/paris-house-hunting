from __future__ import annotations

import requests

from src.domain.models import Offer, ProviderName, SearchCriteria
from src.providers.arpej.client import ArpejClient
from src.providers.arpej.config import ArpejConfig
from src.providers.base import Provider


class ArpejProvider(Provider):
    """Criteria handling on top of ArpejClient. Criteria: {"cities": ["rennes", "brest"]}
    (normalized keys taken from `catalog()`)."""

    name = ProviderName.ARPEJ

    def __init__(self, session: requests.Session | None = None, config: ArpejConfig | None = None):
        self.client = ArpejClient(session, config)

    def catalog(self) -> list[dict]:
        return self.client.cities()

    def validate_criteria(self, criteria: SearchCriteria) -> None:
        cities = criteria.data.get("cities")
        if not cities or not all(isinstance(c, str) and c for c in cities):
            raise ValueError("cities must be a non-empty list of city keys from the ARPEJ catalog")

    def search(self, criteria: SearchCriteria) -> list[Offer]:
        self.validate_criteria(criteria)
        return self.client.search(set(criteria.data["cities"]))
