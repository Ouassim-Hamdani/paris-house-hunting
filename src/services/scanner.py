import logging
import sqlite3
from dataclasses import dataclass

from src.domain.models import Offer, ProviderError, ProviderName, SearchCriteria
from src.providers.base import Provider
from src.storage.deliveries import DeliveryRepository
from src.storage.offers import OfferRepository
from src.storage.provider_status import ProviderStatusRepository
from src.storage.searches import SearchRepository

log = logging.getLogger(__name__)


@dataclass
class PendingNotification:
    user_id: int
    offer: Offer


class Scanner:
    """Scanner service orchestrating providers, searches, storage, and 24h deduplication."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        providers: dict[ProviderName, Provider],
        cooldown_hours: int = 24,
    ):
        self.conn = conn
        self.providers = providers
        self.cooldown_hours = cooldown_hours
        self.searches = SearchRepository(conn)
        self.offers = OfferRepository(conn)
        self.deliveries = DeliveryRepository(conn)
        self.status = ProviderStatusRepository(conn)

    def scan(self) -> list[PendingNotification]:
        """Runs one scan cycle across all active searches with error isolation."""
        active_entries = self.searches.list_active()
        if not active_entries:
            return []

        # 1. Group searches by (provider, criteria_str) so identical criteria only hit the provider API once
        grouped_queries: dict[tuple[ProviderName, str], list[int]] = {}
        search_lookup = {}
        for search, user_notify_enabled in active_entries:
            key = (search.provider, json_canonical(search.criteria))
            grouped_queries.setdefault(key, []).append(search.id or 0)
            search_lookup[search.id] = (search, user_notify_enabled)

        # 2. Query providers with error isolation
        query_results: dict[tuple[ProviderName, str], list[Offer]] = {}
        provider_seen_ids: dict[ProviderName, set[str]] = {p: set() for p in self.providers}

        for (provider_name, _), search_ids in grouped_queries.items():
            provider = self.providers.get(provider_name)
            if not provider or not provider.enabled:
                continue

            first_search, _ = search_lookup[search_ids[0]]
            try:
                found_offers = provider.search(first_search.criteria)
                query_results[(provider_name, json_canonical(first_search.criteria))] = found_offers
                self.status.record_run(provider_name, ok=True)
                for o in found_offers:
                    provider_seen_ids[provider_name].add(o.id)
            except ProviderError as e:
                log.error("Provider %s error: %s", provider_name.value, e)
                self.status.record_run(provider_name, ok=False, error=str(e))
            except Exception as e:
                log.exception("Unexpected error scanning %s: %s", provider_name.value, e)
                self.status.record_run(provider_name, ok=False, error=str(e))

        # 3. Store offers into database
        all_found_offers: dict[str, Offer] = {}
        for offers in query_results.values():
            for o in offers:
                all_found_offers[o.id] = o

        self.offers.upsert_many(list(all_found_offers.values()))

        # 4. Update availability state for providers that ran successfully
        for prov_name, seen_ids in provider_seen_ids.items():
            if (prov_name, ...) in [k for k in query_results.keys() if k[0] == prov_name]:
                self.offers.mark_unavailable_except(prov_name, seen_ids)

        # 5. Determine notifications for each user
        pending: list[PendingNotification] = []
        for (provider_name, crit_key), search_ids in grouped_queries.items():
            offers = query_results.get((provider_name, crit_key), [])
            for sid in search_ids:
                search, user_notify_enabled = search_lookup[sid]
                # Skip sending if user has notifications disabled
                if not user_notify_enabled:
                    continue

                for o in offers:
                    if self.deliveries.is_due_for_notification(search.user_id, o.id, self.cooldown_hours):
                        pending.append(PendingNotification(user_id=search.user_id, offer=o))

        return pending

    def record_delivery(self, user_id: int, offer_id: str) -> None:
        """Call this after the Telegram message has been successfully delivered."""
        self.deliveries.record_delivery(user_id, offer_id)


def json_canonical(criteria: SearchCriteria) -> str:
    import json
    return json.dumps(criteria.data, sort_keys=True, ensure_ascii=False)
