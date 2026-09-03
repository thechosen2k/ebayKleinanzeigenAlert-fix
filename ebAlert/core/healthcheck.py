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


def record_run(total_fetched: int, total_empty: int) -> bool:
    """
    Call once per full run with the aggregate results across all links.

    A single niche search can legitimately return zero items for days, so
    that's not a useful per-link signal. A site redesign, on the other hand,
    breaks the same selectors on every search page at once - so the useful
    signal is the *fraction* of links that came back empty in one run.

    Returns True exactly once when that fraction crosses
    HEALTH_EMPTY_RATIO_THRESHOLD, so the caller can send a single alert
    instead of one every run while the problem persists.
    """
    if total_fetched < settings.HEALTH_MIN_LINKS:
        return False

    ratio = total_empty / total_fetched
    data = _load()
    already_alerted = data.get("alerted", False)

    if ratio >= settings.HEALTH_EMPTY_RATIO_THRESHOLD:
        if already_alerted:
            return False
        data["alerted"] = True
        _save(data)
        return True

    if already_alerted:
        data["alerted"] = False
        _save(data)
    return False
