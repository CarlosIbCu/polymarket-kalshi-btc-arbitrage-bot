import datetime
import pytz

# Base URL for Kalshi 15m BTC markets
BASE_URL = "https://kalshi.com/markets/kxbtc15m/bitcoin-price-up-down/"
SERIES_TICKER = "KXBTC15M"

ET_TZ = pytz.timezone('US/Eastern')

def get_current_15min_window(now_utc=None):
    """
    Given a UTC datetime, return the start of the current 15-minute window (UTC).
    e.g., 17:07 UTC -> 17:00 UTC, 17:22 UTC -> 17:15 UTC
    """
    if now_utc is None:
        now_utc = datetime.datetime.now(pytz.utc)
    floored_minute = (now_utc.minute // 15) * 15
    return now_utc.replace(minute=floored_minute, second=0, microsecond=0)

def generate_kalshi_event_ticker(target_time_utc, asset="btc"):
    """
    Generates the Kalshi event ticker for a given UTC datetime.

    Format: KX{ASSET}15M-{YY}{MMM}{DD}{HHMM}
    where YY=2-digit year, MMM=uppercase 3-letter month, DD=day, HHMM=time
    ALL in Eastern Time (ET) at the candle CLOSE time.

    Example: KXBTC15M-26FEB190000
    Example: KXETH15M-26FEB210500
    """
    series_ticker = f"KX{asset.upper()}15M"
    
    if target_time_utc.tzinfo is None:
        target_time_utc = pytz.utc.localize(target_time_utc)
    else:
        target_time_utc = target_time_utc.astimezone(pytz.utc)

    # Floor to nearest 15-min and get candle close (start + 15 min)
    floored_minute = (target_time_utc.minute // 15) * 15
    candle_start_utc = target_time_utc.replace(minute=floored_minute, second=0, microsecond=0)
    candle_close_utc = candle_start_utc + datetime.timedelta(minutes=15)

    # Convert close to ET
    candle_close_et = candle_close_utc.astimezone(ET_TZ)

    year = candle_close_et.strftime("%y")           # 2-digit year, e.g. "26"
    month = candle_close_et.strftime("%b").upper()  # e.g. "FEB"
    day = candle_close_et.strftime("%d")            # e.g. "19"
    hour = candle_close_et.strftime("%H")           # e.g. "00"
    minute = candle_close_et.strftime("%M")         # e.g. "00"

    return f"{series_ticker}-{year}{month}{day}{hour}{minute}"

def generate_kalshi_url(target_time_utc, asset="btc"):
    """
    Generates the Kalshi URL for the 15m market for a given UTC time and asset.
    """
    base_url = f"https://kalshi.com/markets/kx{asset.lower()}15m/{asset.lower()}-price-up-down/"
    event_ticker = generate_kalshi_event_ticker(target_time_utc, asset=asset)
    return f"{base_url}{event_ticker.lower()}"

if __name__ == "__main__":
    print("--- Kalshi 15m BTC Market Generator ---")

    now = datetime.datetime.now(pytz.utc)
    et_tz = pytz.timezone('US/Eastern')

    print(f"Current Time (UTC): {now}")
    print(f"Current Time (ET):  {now.astimezone(et_tz)}")
    print()

    event_ticker = generate_kalshi_event_ticker(now)
    url = generate_kalshi_url(now)

    print(f"Event Ticker: {event_ticker}")
    print(f"URL:          {url}")

    # Verify against the known example:
    # kxbtc15m-26feb190000
    # open_time: 2026-02-19T04:45:00Z, close_time: 2026-02-19T05:00:00Z
    # close = 05:00 UTC = 00:00 ET on Feb 19, 2026
    # -> 26FEB190000
    test_utc = pytz.utc.localize(datetime.datetime(2026, 2, 19, 4, 51, 0))
    result = generate_kalshi_event_ticker(test_utc)
    print(f"\nVerification test (2026-02-19 04:51 UTC):")
    print(f"  Result:   {result}")
    print(f"  Expected: KXBTC15M-26FEB190000")
    print(f"  Match: {result == 'KXBTC15M-26FEB190000'}")
