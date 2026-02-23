import datetime
import pytz
import requests
import json

# Base URL for Polymarket events
BASE_URL = "https://polymarket.com/event/"

def get_current_15min_window(now_utc=None):
    """
    Given a UTC datetime, return the start of the current 15-minute window.
    e.g., 17:07 UTC -> 17:00 UTC, 17:22 UTC -> 17:15 UTC
    """
    if now_utc is None:
        now_utc = datetime.datetime.now(pytz.utc)
    # Floor to 15-minute boundary
    floored_minute = (now_utc.minute // 15) * 15
    return now_utc.replace(minute=floored_minute, second=0, microsecond=0)

def generate_slug(target_time_utc, asset="btc"):
    """
    Generates the Polymarket 15-minute market slug for a given UTC datetime.
    Format: {asset}-updown-15m-{unix_timestamp}
    The timestamp is the Unix epoch of the 15-minute candle start in UTC.

    Example: btc-updown-15m-1771476300
    Example: eth-updown-15m-1771667100
    """
    # Ensure UTC
    if target_time_utc.tzinfo is None:
        target_time_utc = pytz.utc.localize(target_time_utc)
    else:
        target_time_utc = target_time_utc.astimezone(pytz.utc)

    # Floor to 15-min boundary
    floored_minute = (target_time_utc.minute // 15) * 15
    candle_start = target_time_utc.replace(minute=floored_minute, second=0, microsecond=0)

    timestamp = int(candle_start.timestamp())
    return f"{asset.lower()}-updown-15m-{timestamp}"

def generate_market_url(target_time_utc, asset="btc"):
    """
    Generates the full Polymarket URL for a given UTC datetime.
    """
    slug = generate_slug(target_time_utc, asset=asset)
    return f"{BASE_URL}{slug}"

def get_current_market_slug(asset="btc"):
    """
    Returns the slug for the currently active 15-minute market for the given asset.
    First tries to fetch from Polymarket API, falls back to timestamp generation.
    """
    try:
        params = {
            "active": "true",
            "closed": "false",
            "limit": 20
        }
        r = requests.get("https://gamma-api.polymarket.com/events", params=params)
        data = r.json()
        search_term = f"{asset.lower()}-updown-15m"
        for event in data:
            slug = event.get('slug', '')
            if search_term in slug:
                # print(f"Found active slug from API: {slug}")
                return slug
    except Exception as e:
        # print(f"Error fetching active slug: {e}")
        pass

    now = datetime.datetime.now(pytz.utc)
    window_start = get_current_15min_window(now)
    return generate_slug(window_start, asset=asset)

if __name__ == "__main__":
    print("--- Polymarket 15m BTC URL Generator ---")

    now = datetime.datetime.now(pytz.utc)
    et_tz = pytz.timezone('US/Eastern')

    print(f"Current Time (UTC): {now}")
    print(f"Current Time (ET):  {now.astimezone(et_tz)}")
    print()

    window_start = get_current_15min_window(now)
    slug = generate_slug(window_start)
    url = generate_market_url(window_start)

    print(f"Current 15m Window Start (UTC): {window_start}")
    print(f"Current 15m Window Start (ET):  {window_start.astimezone(et_tz)}")
    print(f"Generated Slug: {slug}")
    print(f"Generated URL:  {url}")
