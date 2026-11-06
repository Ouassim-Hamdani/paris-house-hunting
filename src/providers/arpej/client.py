import time
import unicodedata

import requests

from src.domain.models import Offer, ProviderError, ProviderName
from src.providers import http
from src.providers.arpej.config import ArpejConfig


def city_key(name: str) -> str:
    """Normalize messy city names ('  Metz ', 'JOINVILLE-LE-PONT', 'Cesson') to an identical key."""
    if not name:
        return ""
    # Strip accents
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    # Normalize multiple whitespaces, hyphens, and lowercase
    s = s.strip().lower()
    return " ".join(s.split())


def _city_label(name: str) -> str:
    """Pretty display label: strips extra spaces and formats ALLCAPS like 'JOINVILLE-LE-PONT' -> 'Joinville-Le-Pont'."""
    clean = " ".join((name or "").strip().split())
    if not clean:
        return ""
    # If the word is entirely uppercase (e.g. JOINVILLE-LE-PONT or METZ), format to Title Case
    if clean.isupper():
        # Title case while preserving hyphens properly
        return "-".join(part.capitalize() for part in clean.split("-"))
    return clean


class ArpejClient:
    """Everything that talks to the ARPEJ site. No dependency on any other provider."""

    def __init__(self, session: requests.Session | None = None, config: ArpejConfig | None = None):
        self.session = session or http.make_session()
        self.config = config or ArpejConfig()
        self._catalog: tuple[float, list[dict]] | None = None

    # --- API ----------------------------------------------------------------
    def fetch_residences(self, include_full: bool = False) -> list[dict]:
        """One request returns every residence nationwide (we filter by city ourselves)."""
        params = {
            "lang": "fr",
            "display": "map",
            "show_if_full": "true" if include_full else "false",
        }
        data = http.get(self.session, self.config.residences_url, params=params).json()
        try:
            return data["residences"]
        except (KeyError, TypeError) as e:
            raise ProviderError(f"Unexpected ARPEJ response: {e!r}") from e

    # --- city list (for the Telegram multi-select) ------------------------------
    def cities(self) -> list[dict]:
        """[{'id': normalized key, 'label': display name}] built from ALL residences (full too)."""
        now = time.monotonic()
        if self._catalog and now - self._catalog[0] < self.config.catalog_ttl_seconds:
            return self._catalog[1]
        found: dict[str, str] = {}
        for r in self.fetch_residences(include_full=True):
            raw_city = (r.get("extra_data") or {}).get("city", "")
            if key := city_key(raw_city):
                found.setdefault(key, _city_label(raw_city))
        catalog = [{"id": k, "label": v} for k, v in sorted(found.items(), key=lambda kv: kv[1])]
        self._catalog = (now, catalog)
        return catalog

    # --- search -----------------------------------------------------------------
    def search(self, cities: set[str] | list[str] | tuple[str, ...]) -> list[Offer]:
        """Available residences whose normalized city is in `cities`."""
        if isinstance(cities, str):
            cities = [cities]
        target_keys = {city_key(c) for c in cities if c}
        offers = []
        for r in self.fetch_residences(include_full=False):
            extra = r.get("extra_data") or {}
            raw_city = extra.get("city", "")
            if extra.get("available_rooms", 0) > 0 and city_key(raw_city) in target_keys:
                offers.append(self._to_offer(r))
        return offers

    def _to_offer(self, r: dict) -> Offer:
        """Map one API residence to our normalized Offer."""
        extra = r.get("extra_data") or {}
        images = extra.get("images") or []
        price = extra.get("price_from")
        return Offer(
            provider=ProviderName.ARPEJ,
            external_id=str(r["ID"]),
            name=r.get("title", ""),
            url=r.get("link", ""),
            address=" ".join((extra.get("address") or "").split()),
            postcode=(extra.get("zip_code") or "").strip(),
            city=_city_label(extra.get("city", "")),
            price=f"{float(price):g} €" if price else "",
            image_url=images[0].get("url", "") if images else "",
        )


if __name__ == "__main__":
    client = ArpejClient()
    print(client.search(("Villejuif")))
