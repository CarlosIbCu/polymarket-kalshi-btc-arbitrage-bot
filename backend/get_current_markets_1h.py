import datetime
import pytz
from find_new_market_1h import generate_market_url as generate_polymarket_url, generate_slug as generate_polymarket_slug, get_current_hour_start
from find_new_kalshi_market_1h import generate_kalshi_url, generate_kalshi_event_ticker

def get_current_market_urls(asset="btc"):
    """
    Returns the current active 1H market URLs for Polymarket and Kalshi.
    'Current' = the hourly window that is currently open (top of current hour).
    """
    hour_start = get_current_hour_start()

    polymarket_url = generate_polymarket_url(hour_start, asset=asset)
    polymarket_slug = generate_polymarket_slug(hour_start, asset=asset)
    kalshi_event_ticker = generate_kalshi_event_ticker(hour_start, asset=asset)
    kalshi_url = generate_kalshi_url(hour_start, asset=asset)

    return {
        "polymarket": polymarket_url,
        "polymarket_slug": polymarket_slug,
        "kalshi": kalshi_url,
        "kalshi_event_ticker": kalshi_event_ticker,
        "target_time_utc": hour_start,
        "target_time_et": hour_start.astimezone(pytz.timezone('US/Eastern'))
    }

if __name__ == "__main__":
    urls = get_current_market_urls()
    print(f"Window Start (UTC): {urls['target_time_utc']}")
    print(f"Window Start (ET):  {urls['target_time_et']}")
    print(f"Polymarket Slug:    {urls['polymarket_slug']}")
    print(f"Kalshi Ticker:      {urls['kalshi_event_ticker']}")
