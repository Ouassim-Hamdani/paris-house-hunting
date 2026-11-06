import re
from dataclasses import dataclass
from urllib.parse import quote

import requests

from src.domain.models import Offer, ProviderError, ProviderName
from src.providers import http
from src.providers.crous.bounds import Bounds
from src.providers.crous.config import CrousConfig


@dataclass(frozen=True)
class GeoResult:
    label: str
    bounds: Bounds


def _range(lo: float, hi: float, unit: str) -> str:
    return f"{lo:g} {unit}" if lo == hi else f"{lo:g} - {hi:g} {unit}"


class CrousClient:
    """Everything that talks to the CROUS site: place lookup and housing search."""

    def __init__(self, session: requests.Session | None = None, config: CrousConfig | None = None):
        self.session = session or http.make_session()
        self.config = config or CrousConfig()

    # --- place lookup -----------------------------------------------------
    def geocode(self, query: str, limit: int = 5) -> list[GeoResult]:
        """City/campus name -> candidate places in France (first = best guess)."""
        params = [("q", query), ("limit", "18"), ("lang", "fr")]
        data = http.get(
            self.session,
            self.config.photon_url,
            params=params,
            headers={"Referer": self.config.base_url + "/"},
        ).json()

        results: list[GeoResult] = []
        for f in data.get("features", []):
            p = f.get("properties", {})
            if p.get("country") != "France":  # with lang=fr; responses carry no ISO code
                continue
            if p.get("extent"):
                bounds = Bounds(*p["extent"])
            else:  # single point (village, school...): pad into a small box
                lon, lat = f["geometry"]["coordinates"]
                bounds = Bounds.around_point(lon, lat, self.config.point_padding_deg)
            label = ", ".join(x for x in (p.get("name"), p.get("state")) if x)
            results.append(GeoResult(label, bounds))
            if len(results) >= limit:
                break
        return results

    # --- housing search ---------------------------------------------------
    def search(self, bounds: Bounds) -> list[Offer]:
        return [self._to_offer(it) for it in self._fetch_items(bounds) if it.get("available", True)]

    def _fetch_items(self, bounds: Bounds) -> list[dict]:
        headers = {
            "Accept": "application/ld+json, application/json",
            "Origin": self.config.base_url,
            "Referer": self.config.search_page_url(str(bounds)),
        }
        items: list[dict] = []
        for page in range(1, self.config.max_pages + 1):
            resp = http.post(
                self.session,
                self.config.search_api_url,
                json=self._payload(bounds, page),
                headers=headers,
            )
            try:
                results = resp.json()["results"]
                batch, total = results["items"], results["total"]["value"]
            except (ValueError, KeyError, TypeError) as e:
                raise ProviderError(f"Unexpected CROUS response: {e!r}") from e
            items.extend(batch)
            if not batch or len(items) >= total:
                break
            
        return items

    def _payload(self, bounds: Bounds, page: int) -> dict:
        # The API accepts just `location` (idTool is already in the URL). Page fields are kept
        # only so pagination is explicit rather than relying on server defaults.
        return {
            "page": page,
            "pageSize": self.config.page_size,
            "location": bounds.corners(),
        }

    def _to_offer(self, it: dict) -> Offer:
        """Map one API item to our normalized Offer."""
        res = it.get("residence") or {}
        address = res.get("address", "")
        m = re.search(r"(\d{5})\s+(.+)$", address)

        rents = [om.get("rent") or {} for om in it.get("occupationModes", [])]  # in cents
        lows = [r["min"] for r in rents if r.get("min") is not None]
        highs = [r["max"] for r in rents if r.get("max") is not None]
        price = _range(min(lows) / 100, max(highs or lows) / 100, "€") if lows else ""

        area = it.get("area") or {}
        size = _range(area["min"], area.get("max", area["min"]), "m²") if area.get("min") is not None else ""

        media = (it.get("medias") or res.get("medias") or [{}])[0].get("src", "")  # room, then residence
        return Offer(
            provider=ProviderName.CROUS,
            external_id=str(it["id"]),
            name=f"{res.get('label', '').title()} - {it.get('label', '')}".strip(" -"),
            url=self.config.detail_url(it["id"]),
            address=address,
            postcode=m.group(1) if m else "",
            city=m.group(2).title() if m else "",
            price=price,
            size=size,
            image_url=f"{self.config.image_base}/{quote(media)}" if media else "",
        )

    