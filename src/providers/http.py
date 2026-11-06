import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.domain.models import ProviderError

DEFAULT_TIMEOUT = 15  # seconds


def make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = "Mozilla/5.0 (housing-bot)"
    return s


def get(session: requests.Session, url: str, **kw) -> requests.Response:
    """GET with timeout; converts any requests failure into ProviderError."""
    try:
        r = session.get(url, timeout=kw.pop("timeout", DEFAULT_TIMEOUT), **kw)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        raise ProviderError(f"GET {url} failed: {e}") from e


def post(session: requests.Session, url: str, **kw) -> requests.Response:
    """POST with timeout; converts any requests failure into ProviderError."""
    try:
        r = session.post(url, timeout=kw.pop("timeout", DEFAULT_TIMEOUT), **kw)
        r.raise_for_status()
        return r
    except requests.RequestException as e:
        raise ProviderError(f"POST {url} failed: {e}") from e
