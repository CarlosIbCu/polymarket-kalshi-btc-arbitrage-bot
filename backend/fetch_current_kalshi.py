import requests
import time
import datetime
import pytz
from get_current_markets import get_current_market_urls

# Configuration
KALSHI_API_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"
SERIES_TICKER = "KXBTC15M"

# Retry settings
MAX_RETRIES = 3
TIMEOUT = 5  # seconds

def fetch_with_retry(url, params=None, max_retries=MAX_RETRIES, timeout=TIMEOUT):
    """Make a request with retries and timeout."""
    last_error = None
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.Timeout:
            last_error = f"Timeout (attempt {attempt + 1}/{max_retries})"
        except requests.exceptions.RequestException as e:
            last_error = str(e)

        if attempt < max_retries - 1:
            time.sleep(0.5 * (attempt + 1))

    return None, last_error

def get_kalshi_15m_market(event_ticker, asset="btc"):
    """
    Fetches the Kalshi 15m binary Up/Down market for the given event ticker.
    Returns a single market dict (yes_bid/yes_ask/no_bid/no_ask/floor_strike) or None.
    """
    series_ticker = f"KX{asset.upper()}15M"
    # Use series_ticker + event_ticker to get the right market
    params = {
        "event_ticker": event_ticker,
        "series_ticker": series_ticker,
        "limit": 10
    }
    data, err = fetch_with_retry(KALSHI_API_URL, params=params)
    if err:
        return None, f"Kalshi API error: {err}"

    markets = data.get('markets', [])
    if not markets:
        return None, f"No markets found for event ticker: {event_ticker}"

    # The 15m market is a single binary Yes/No (Up/Down)
    # yes = price goes UP, no = price goes DOWN
    m = markets[0]

    # The floor_strike is the price to beat (opening price of the 15-min window)
    floor_strike = m.get('floor_strike', 0.0)

    # Kalshi prices are in cents (0-100), convert to decimal (0.00-1.00)
    yes_ask_cents = m.get('yes_ask', 0)
    yes_bid_cents = m.get('yes_bid', 0)
    no_ask_cents = m.get('no_ask', 0)
    no_bid_cents = m.get('no_bid', 0)

    return {
        'ticker': m.get('ticker', ''),
        'event_ticker': m.get('event_ticker', ''),
        'title': m.get('title', ''),
        'floor_strike': floor_strike,               # Price to beat (opening price)
        'yes_ask': yes_ask_cents / 100.0,           # Cost to buy Up
        'yes_bid': yes_bid_cents / 100.0,
        'no_ask': no_ask_cents / 100.0,             # Cost to buy Down
        'no_bid': no_bid_cents / 100.0,
        'yes_ask_cents': yes_ask_cents,
        'no_ask_cents': no_ask_cents,
        'open_time': m.get('open_time', ''),
        'close_time': m.get('close_time', ''),
        'status': m.get('status', ''),
        'last_price': m.get('last_price', 0) / 100.0,
    }, None

def fetch_kalshi_data_struct(asset="btc"):
    """
    Fetches current Kalshi 15m market and returns a structured dictionary.
    """
    try:
        # Get current market info
        market_info = get_current_market_urls(asset=asset)
        kalshi_event_ticker = market_info["kalshi_event_ticker"]

        # Fetch the market
        market, err = get_kalshi_15m_market(kalshi_event_ticker, asset=asset)
        if err:
            return None, f"Kalshi Error: {err}"

        return {
            "event_ticker": kalshi_event_ticker,
            "market": market,
            # For compatibility with api.py — expose prices at top level
            "yes_ask": market['yes_ask'],       # Cost to bet Up
            "no_ask": market['no_ask'],         # Cost to bet Down
            "floor_strike": market['floor_strike'],
            "asset": asset.upper()
        }, None

    except Exception as e:
        return None, str(e)

def main():
    data, err = fetch_kalshi_data_struct()

    if err:
        print(f"Error: {err}")
        return

    m = data['market']
    print(f"Kalshi 15m Market: {data['event_ticker']}")
    print(f"Title:  {m['title']}")
    print(f"Status: {m['status']}")
    print(f"Price to Beat: ${m['floor_strike']:,.2f}")
    print(f"UP:   Yes Ask = {m['yes_ask_cents']}c (${m['yes_ask']:.3f})")
    print(f"DOWN: No Ask  = {m['no_ask_cents']}c (${m['no_ask']:.3f})")
    print(f"Close Time: {m['close_time']}")

if __name__ == "__main__":
    main()
