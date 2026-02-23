import datetime
import pytz

BASE_URL = "https://kalshi.com/markets/kxbtcd/bitcoin-price-abovebelow/"
SERIES_TICKER = "KXBTCD"
ET_TZ = pytz.timezone('US/Eastern')

def generate_kalshi_event_ticker(target_time, asset="btc"):
    """
    Generates the Kalshi hourly event ticker for a given UTC datetime.
    Format: KX{ASSET}D-{YY}{MMM}{DD}{HH}  (ET-based, uppercase month, 2-digit hour)
    Example: KXBTCD-26FEB1914  (Feb 19 2026, 14:00 ET)
    Example: KXETHD-26FEB2105
    """
    series_ticker = f"KX{asset.upper()}D"
    
    if target_time.tzinfo is None:
        target_time = pytz.utc.localize(target_time)
    else:
        target_time = target_time.astimezone(pytz.utc)

    # Floor to current hour, then add 1h to get the close
    hour_start = target_time.replace(minute=0, second=0, microsecond=0)
    hour_close = hour_start + datetime.timedelta(hours=1)
    hour_close_et = hour_close.astimezone(ET_TZ)

    year = hour_close_et.strftime("%y")
    month = hour_close_et.strftime("%b").upper()
    day = hour_close_et.strftime("%d")
    hour = hour_close_et.strftime("%H")

    return f"{series_ticker}-{year}{month}{day}{hour}"

def generate_kalshi_url(target_time, asset="btc"):
    """
    Generates the Kalshi URL for the 1h market for a given UTC time and asset.
    """
    base_url = f"https://kalshi.com/markets/kx{asset.lower()}d/{asset.lower()}-price-abovebelow/"
    ticker = generate_kalshi_event_ticker(target_time, asset=asset)
    return f"{base_url}{ticker.lower()}"

if __name__ == "__main__":
    now = datetime.datetime.now(pytz.utc)
    print(f"Event Ticker: {generate_kalshi_event_ticker(now)}")
    print(f"URL:          {generate_kalshi_url(now)}")
