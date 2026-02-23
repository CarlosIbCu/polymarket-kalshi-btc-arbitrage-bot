import datetime
import pytz

BASE_URL = "https://polymarket.com/event/"

def generate_slug(target_time, asset="btc"):
    """
    Generates the Polymarket hourly market event slug for a given datetime.
    Format: {asset}-up-or-down-{month}-{day}-{hour}{am/pm}-et
    Example: bitcoin-up-or-down-february-19-5pm-et
    Example: ethereum-up-or-down-february-21-4am-et
    """
    asset_map = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "sol": "solana",
        "xrp": "xrp"
    }
    asset_name = asset_map.get(asset.lower(), "bitcoin")
    
    et_tz = pytz.timezone('US/Eastern')
    if target_time.tzinfo is None:
        target_time = pytz.utc.localize(target_time).astimezone(et_tz)
    else:
        target_time = target_time.astimezone(et_tz)

    month = target_time.strftime("%B").lower()
    day = target_time.day
    hour_int = int(target_time.strftime("%I"))  # No leading zero
    am_pm = target_time.strftime("%p").lower()

    return f"{asset_name}-up-or-down-{month}-{day}-{hour_int}{am_pm}-et"

def generate_market_url(target_time, asset="btc"):
    slug = generate_slug(target_time, asset=asset)
    return f"{BASE_URL}{slug}"

def get_current_hour_start():
    """Returns the start of the current UTC hour."""
    now = datetime.datetime.now(pytz.utc)
    return now.replace(minute=0, second=0, microsecond=0)

if __name__ == "__main__":
    now = datetime.datetime.now(pytz.utc)
    et_tz = pytz.timezone('US/Eastern')
    hour_start = get_current_hour_start()
    print(f"Current Time (UTC): {now}")
    print(f"Current Time (ET):  {now.astimezone(et_tz)}")
    print(f"Slug: {generate_slug(hour_start)}")
    print(f"URL:  {generate_market_url(hour_start)}")
