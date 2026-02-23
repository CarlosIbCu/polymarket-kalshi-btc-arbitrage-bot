import datetime
import pytz
from find_new_market import generate_market_url as generate_polymarket_url, get_current_15min_window, generate_slug as generate_polymarket_slug, get_current_market_slug
from find_new_kalshi_market import generate_kalshi_url, generate_kalshi_event_ticker

def get_current_market_urls(asset="btc"):
    """
    Returns a dictionary with the current active 15-minute market info for Polymarket and Kalshi.
    'Current' is defined as the 15-minute window that is currently open/active.
    """
    now = datetime.datetime.now(pytz.utc)

    # Polymarket: slug is based on the active market from API
    polymarket_slug = get_current_market_slug(asset=asset) 
    
    # Extract timestamp from slug: btc-updown-15m-1771597800
    try:
        ts_part = polymarket_slug.split('-')[-1]
        window_start = datetime.datetime.fromtimestamp(int(ts_part), pytz.utc)
    except:
        # Fallback to current 15-min window if parsing fails
        window_start = get_current_15min_window(now)

    polymarket_url = f"https://polymarket.com/event/{polymarket_slug}"

    # Kalshi: event ticker is based on the window close time (in ET)
    kalshi_event_ticker = generate_kalshi_event_ticker(window_start, asset=asset)
    kalshi_url = generate_kalshi_url(window_start, asset=asset)

    return {
        "polymarket": polymarket_url,
        "polymarket_slug": polymarket_slug,
        "kalshi": kalshi_url,
        "kalshi_event_ticker": kalshi_event_ticker,
        "target_time_utc": window_start,
        "target_time_et": window_start.astimezone(pytz.timezone('US/Eastern'))
    }

if __name__ == "__main__":
    urls = get_current_market_urls()
    et_tz = pytz.timezone('US/Eastern')

    print(f"Current Time (UTC): {datetime.datetime.now(pytz.utc)}")
    print(f"Window Start (ET):  {urls['target_time_et']}")
    print("-" * 50)
    print(f"Polymarket Slug: {urls['polymarket_slug']}")
    print(f"Polymarket URL:  {urls['polymarket']}")
    print(f"Kalshi Ticker:   {urls['kalshi_event_ticker']}")
    print(f"Kalshi URL:      {urls['kalshi']}")
