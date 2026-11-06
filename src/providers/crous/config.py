import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CrousConfig:
    """All CROUS tunables and URL builders in one place (no module-level globals)."""

    # Yearly campaign id in /tools/<id>/... (37 = old, 47 = 2026-2027). Changes every year!
    tool_id: str = field(default_factory=lambda: os.getenv("CROUS_TOOL_ID", "47"))
    host: str = "trouverunlogement.lescrous.fr"
    page_size: int = 24
    max_pages: int = 5  # safety cap on pagination
    point_padding_deg: float = 0.03  # ~3 km box for geocode results that are a single point


    @property
    def base_url(self) -> str:
        return f"https://{self.host}"

    @property
    def photon_url(self) -> str:
        return f"{self.base_url}/photon/api"

    @property
    def search_api_url(self) -> str:
        return f"{self.base_url}/api/fr/search/{self.tool_id}"

    @property
    def image_base(self) -> str:
        # API gives relative paths (medias[].src); served through this cache resolver.
        return f"{self.base_url}/media/cache/resolve/preview"

    def search_page_url(self, bounds: str) -> str:
        """Human-facing search page (Referer + handy link for messages)."""
        return f"{self.base_url}/tools/{self.tool_id}/search?bounds={bounds}"

    def detail_url(self, accommodation_id: int | str) -> str:
        return f"{self.base_url}/tools/{self.tool_id}/accommodations/{accommodation_id}"
