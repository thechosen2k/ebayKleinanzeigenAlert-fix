import json
import os

from ebAlert import create_logger
from ebAlert.core.config import settings

log = create_logger(__name__)


def _load() -> dict:
    if os.path.exists(settings.HEALTH_FILE_LOCATION):
        try:
            with open(settings.HEALTH_FILE_LOCATION, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            log.error(exc)
            return {}
    return {}


def _save(data: dict) -> None:
    with open(settings.HEALTH_FILE_LOCATION, "w") as f:
        json.dump(data, f)


def record_result(link_id: int, item_count: int, page_fetched: bool) -> bool:
    """
    Track consecutive successful-but-empty fetches for a link.
    Returns True exactly once when the link crosses HEALTH_CHECK_THRESHOLD
    consecutive empty results, so the caller can send a single alert.
    """
    if not page_fetched:
        # A fetch error (network/HTTP) is not a selector-breakage signal, ignore it here.
        return False

    data = _load()
    key = str(link_id)

    if item_count == 0:
        count = data.get(key, 0) + 1
        data[key] = count
        _save(data)
        return count == settings.HEALTH_CHECK_THRESHOLD

    if key in data:
        del data[key]
        _save(data)
    return False
