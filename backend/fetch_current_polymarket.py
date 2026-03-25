import requests
from get_current_markets import get_current_market_urls

POLY_EVENTS_URL = "https://gamma-api.polymarket.com/events"
CLOB_API_URL = "https://clob.polymarket.com/book"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"

def get_clob_price(token_id):
    """Fetches the cheapest ASK (Buy) price."""
    try:
        if not token_id: return 0.0
        response = requests.get(CLOB_API_URL, params={"token_id": token_id})
        data = response.json()
        asks = data.get('asks', [])
        if asks:
            return float(asks[0]['price'])
        return 0.0
    except:
        return 0.0

def search_market(query):
    try:
        resp = requests.get(POLY_EVENTS_URL, params={"limit": 10, "closed": "false", "q": query})
        data = resp.json()
        return data[0] if data else None
    except:
        return None

def fetch_polymarket_data_struct():
    try:
        conf = get_current_market_urls()
        
        # 1. Try fetching by Slug first, then Query
        event = None
        resp = requests.get(POLY_EVENTS_URL, params={"slug": conf["polymarket_slug"]})
        if resp.status_code == 200 and resp.json():
            event = resp.json()[0]
        else:
            # Fallback to search
            event = search_market(conf["polymarket_query"])
            
        if not event: return None, "Event not found (Check Date)"

        # 2. Get Market Details
        market = event.get("markets", [])[0]
        clob_ids = eval(market.get("clobTokenIds", "[]"))
        outcomes = eval(market.get("outcomes", "[]"))
        
        prices = {}
        ids = {}
        for outcome, token_id in zip(outcomes, clob_ids):
            label = "Up" if outcome == "Yes" else "Down"
            price = get_clob_price(token_id)
            prices[label] = price
            ids[label] = token_id

        # 3. Get Binance Reference Price (Strike)
        # Fetch latest price to be safe
        b_resp = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"})
        ref_price = float(b_resp.json()["price"])

        return {
            "price_to_beat": ref_price, # Using current price as proxy for strike if needed
            "prices": prices,
            "up_token_id": ids.get('Up'),
            "down_token_id": ids.get('Down'),
            "slug": event.get("slug")
        }, None

    except Exception as e:
        return None, str(e)