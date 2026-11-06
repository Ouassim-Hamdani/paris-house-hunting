from src.domain.models import ProviderName
from src.providers.arpej import ArpejProvider
from src.providers.base import Provider
from src.providers.crous import CrousProvider


def build_registry() -> dict[ProviderName, Provider]:
    """All providers keyed by name. Use `active()` for scans/menus."""
    providers: list[Provider] = [CrousProvider(), ArpejProvider()]
    return {p.name: p for p in providers}


def active(registry: dict[ProviderName, Provider]) -> dict[ProviderName, Provider]:
    return {n: p for n, p in registry.items() if p.enabled}
