from abc import ABC, abstractmethod

from src.domain.models import Offer, ProviderName, SearchCriteria


class Provider(ABC):
    """Contract every housing provider implements.

    Rules:
    - `search` is the only thing the scanner calls.
    - Raise `ProviderError` on network/parse failure (never return [] to hide errors).
    - Return an empty list only when the provider genuinely has no availability.
    - Offers must have a stable `external_id` (used for dedup).
    """

    name: ProviderName
    enabled: bool = True

    @abstractmethod
    def validate_criteria(self, criteria: SearchCriteria) -> None:
        """Raise ValueError if criteria are invalid/unsafe (called when a user saves a search)."""

    @abstractmethod
    def search(self, criteria: SearchCriteria) -> list[Offer]:
        """Fetch current available offers matching criteria."""

    def catalog(self) -> list[dict]:
        """Optional: selectable options for interactive setup (e.g. ARPEJ cities)."""
        return []
