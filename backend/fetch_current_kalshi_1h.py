import requests
import time
import datetime
import pytz
import re
from get_current_markets_1h import get_current_market_urls

KALSHI_API_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"
SERIES_TICKER = "KXBTCD"

MAX_RETRIES = 3
TIMEOUT = 5

def fetch_with_retry(url, params=None, max_retries=MAX_RETRIES, timeout=TIMEOUT):
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

def parse_strike(subtitle):
    """Parse strike price from Kalshi subtitle like '$96,250 or above'."""
    match = re.search(r'\$([\d,]+)', subtitle)
    if match:
        return float(match.group(1).replace(',', ''))
    return 0.0

def get_kalshi_markets(event_ticker, asset="btc"):
    series_ticker = f"KX{asset.upper()}D"
    params = {"limit": 100, "event_ticker": event_ticker, "series_ticker": series_ticker}
    data, err = fetch_with_retry(KALSHI_API_URL, params=params)
    if err:
        return None, f"Kalshi API error: {err}"
    return data.get('markets', []), None

def fetch_kalshi_data_struct(asset="btc"):
    """
    Fetches current hourly Kalshi markets (multi-strike ladder).
    Returns a list of markets with strike prices and Yes/No costs.
    """
    try:
        market_info = get_current_market_urls(asset=asset)
        kalshi_event_ticker = market_info["kalshi_event_ticker"]

        markets, err = get_kalshi_markets(kalshi_event_ticker, asset=asset)
        if err:
            return None, f"Kalshi Error: {err}"
        if not markets:
            return None, f"No 1H markets found for {kalshi_event_ticker}"

        market_data = []
        for m in markets:
            # For KXBTCD/KXETHD, the subtitle has the strike: "$96,250 or above"
            subtitle = m.get('subtitle', '') or m.get('yes_sub_title', '')
            strike = parse_strike(subtitle)
            if strike == 0.0:
                # Try floor_strike field
                strike = m.get('floor_strike', 0.0)
            if strike > 0:
                yes_ask = m.get('yes_ask', 0)
                no_ask = m.get('no_ask', 0)
                market_data.append({
                    'strike': strike,
                    'yes_ask': yes_ask,        # cents (0-100)
                    'yes_bid': m.get('yes_bid', 0),
                    'no_ask': no_ask,
                    'no_bid': m.get('no_bid', 0),
                    'yes_ask_dec': yes_ask / 100.0,   # decimal (0.00-1.00)
                    'no_ask_dec': no_ask / 100.0,
                    'subtitle': subtitle,
                    'ticker': m.get('ticker', ''),
                })

        market_data.sort(key=lambda x: x['strike'])

        return {
            "event_ticker": kalshi_event_ticker,
            "markets": market_data,
            # Also expose as a "ladder" for api.py compatibility
            "market_type": "multi_strike",
            "asset": asset.upper()
        }, None

    except Exception as e:
        return None, str(e)

if __name__ == "__main__":
    data, err = fetch_kalshi_data_struct()
    if err:
        print(f"Error: {err}")
    else:
        print(f"Event: {data['event_ticker']}")
        print(f"Total markets: {len(data['markets'])}")
        for m in data['markets'][:5]:
            print(f"  ${m['strike']:,.0f}: Yes={m['yes_ask']}c / No={m['no_ask']}c")
