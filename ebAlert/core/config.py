import os
import logging

# Secrets live outside the repo/deploy tree so a code deploy never clobbers them.
_env_file = os.path.join(os.path.expanduser("~"), ".ebalert.env")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


class Settings:
    TOKEN = os.environ.get("TOKEN") or "Your_secret_key"
    CHAT_ID = os.environ.get("CHAT_ID") or "Your_chat_id"
    FILE_LOCATION = os.path.join(os.path.expanduser("~"), "ebayklein.db")
    TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&parse_mode=HTML&"""
    LOGGING = os.environ.get("LOGGING") or logging.ERROR
    URL_BASE = "https://www.kleinanzeigen.de"
    FILTER_WANTED_ADS = (os.environ.get("FILTER_WANTED_ADS") or "true").lower() != "false"
    HEALTH_FILE_LOCATION = os.path.join(os.path.expanduser("~"), "ebalert_health.json")
    # Individual niche searches can legitimately have zero current listings for days,
    # so the health check looks at the *fraction* of all links returning zero items in
    # one run, not any single link in isolation - that's what actually distinguishes a
    # broken selector (most/all links go to zero at once) from a quiet niche search.
    HEALTH_EMPTY_RATIO_THRESHOLD = float(os.environ.get("HEALTH_EMPTY_RATIO_THRESHOLD") or 0.5)
    HEALTH_MIN_LINKS = int(os.environ.get("HEALTH_MIN_LINKS") or 5)


settings = Settings()
