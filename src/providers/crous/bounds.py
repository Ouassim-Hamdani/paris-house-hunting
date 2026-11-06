import re
from dataclasses import dataclass

_BOUNDS_RE = re.compile(r"^-?\d+(\.\d+)?(_-?\d+(\.\d+)?){3}$")


@dataclass(frozen=True)
class Bounds:
    """Bounding box. String form `minLon_maxLat_maxLon_minLat` is what CROUS URLs and
    Photon's `extent` use, and what we store in `searches.criteria`."""

    min_lon: float
    max_lat: float
    max_lon: float
    min_lat: float

    def __post_init__(self) -> None:
        if not (-180 <= self.min_lon < self.max_lon <= 180 and -90 <= self.min_lat < self.max_lat <= 90):
            raise ValueError("bounds out of range")

    @classmethod
    def parse(cls, text: str) -> "Bounds":
        if not _BOUNDS_RE.match(text or ""):
            raise ValueError("bounds must look like minLon_maxLat_maxLon_minLat")
        return cls(*(float(x) for x in text.split("_")))

    @classmethod
    def around_point(cls, lon: float, lat: float, padding: float) -> "Bounds":
        return cls(lon - padding, lat + padding, lon + padding, lat - padding)

    def __str__(self) -> str:
        return "_".join(
            f"{v:.7f}".rstrip("0").rstrip(".")
            for v in (self.min_lon, self.max_lat, self.max_lon, self.min_lat)
        )

    def corners(self) -> list[dict]:
        """[top-left, bottom-right] as the search API expects."""
        return [
            {"lon": self.min_lon, "lat": self.max_lat},
            {"lon": self.max_lon, "lat": self.min_lat},
        ]
