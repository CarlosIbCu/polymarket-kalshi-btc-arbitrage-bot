import requests
import json
from find_new_kalshi_market import generate_kalshi_event_ticker
import datetime
import pytz

KALSHI_API_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"
SERIES_TICKER = "KXBTC15M"

def debug_full_kalshi():
    now = datetime.datetime.now(pytz.utc)
    event_ticker = generate_kalshi_event_ticker(now)
    print(f"DEBUG: Current UTC: {now}")
    print(f"DEBUG: Event Ticker: {event_ticker}")

    params = {
        "event_ticker": event_ticker,
        "series_ticker": SERIES_TICKER,
        "limit": 1
    }
    
    response = requests.get(KALSHI_API_URL, params=params)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    markets = data.get('markets', [])
    if not markets:
        print("No markets found.")
        return

    print("\nFULL MARKET DATA SAVED TO kalshi_debug_raw.json")
    with open("kalshi_debug_raw.json", "w") as f:
        json.dump(markets[0], f, indent=2)

if __name__ == "__main__":
    debug_full_kalshi()
