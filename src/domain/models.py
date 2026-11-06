"""Platform-agnostic domain models. No I/O, no Telegram, no SQL in here."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ProviderName(str, Enum):
    CROUS = "crous"
    ARPEJ = "arpej"


class Role(str, Enum):
    MEMBER = "Member"
    ADMIN = "Admin"


@dataclass(frozen=True)
class Offer:
    """Normalized listing returned by every provider."""

    provider: ProviderName
    external_id: str  # stable id inside the provider (URL slug, API id, ...)
    name: str
    url: str = ""
    address: str = ""
    postcode: str = ""
    city: str = ""
    price: str = ""  # keep as display string for now; parse to cents later
    size: str = ""
    image_url: str = ""
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def id(self) -> str:
        """Global offer id used as primary key in the `offers` table."""
        return f"{self.provider.value}:{self.external_id}"


@dataclass
class SearchCriteria:
    """Provider-specific criteria, stored as JSON in `searches.criteria`.

    CROUS: {"mode": "link", "url": "..."} or {"mode": "city", "city": "Paris"}
    ARPEJ: {"city_ids": [52524, ...]}
    """

    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class Search:
    """One saved search per (user, provider)."""

    user_id: int
    provider: ProviderName
    criteria: SearchCriteria
    active: bool = True
    id: int | None = None


@dataclass
class User:
    telegram_id: int
    username: str = ""
    role: Role = Role.MEMBER
    notify_enabled: bool = True


@dataclass
class ProviderStatus:
    provider: ProviderName
    last_run_at: datetime | None = None
    last_ok_at: datetime | None = None
    last_error: str | None = None


class ProviderError(Exception):
    """Raised by a provider on network/parse failure. The scanner isolates these."""
