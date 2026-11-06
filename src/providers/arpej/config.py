from dataclasses import dataclass


@dataclass(frozen=True)
class ArpejConfig:
    """All ARPEJ tunables in one place."""

    host: str = "www.arpej.fr"
    catalog_ttl_seconds: int =1 * 24 * 3600  # city list barely changes

    @property
    def base_url(self) -> str:
        return f"https://{self.host}"

    @property
    def residences_url(self) -> str:
        return f"{self.base_url}/wp-json/sn/residences"
