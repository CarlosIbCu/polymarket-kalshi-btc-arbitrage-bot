import requests
import re
import datetime

# Configuration
# "elections" subdomain covers ALL markets
KALSHI_API_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"
BINANCE_PRICE_URL = "https://api.binance.com/api/v3/ticker/price"
BTC_SYMBOL = "BTCUSDT"

def get_binance_price():
    try:
        resp = requests.get(BINANCE_PRICE_URL, params={"symbol": BTC_SYMBOL})
        data = resp.json()
        return float(data["price"])
    except:
        return 0.0

def fetch_kalshi_data_struct():
    """
    Dynamically fetches ACTIVE Kalshi Bitcoin Daily markets.
    Fixes the '400 Bad Request' by using status='open'.
    """
    try:
        # 1. Fetch Markets
        # CRITICAL FIX: status must be 'open', not 'active'
        params = {
            "limit": 100,
            "series_ticker": "KXBTCDAILY", 
            "status": "open"
        }
        
        response = requests.get(KALSHI_API_URL, params=params)
        
        # Fallback: If KXBTCDAILY fails (400/404) or is empty, try broader KXBTC
        if response.status_code != 200 or not response.json().get("markets"):
            print("   (Debug) KXBTCDAILY empty or invalid. Retrying with KXBTC...")
            params["series_ticker"] = "KXBTC"
            response = requests.get(KALSHI_API_URL, params=params)
            response.raise_for_status()

        data = response.json()
        all_markets = data.get("markets", [])
        
        if not all_markets:
            return None, "No active Kalshi markets found (Market might be closed/settled)."

        # 2. Filter for 'Daily Close' and Today's Expiration
        # Some KXBTC markets are "High at 9AM", we want "Daily Close" (usually 4PM ET)
        # We assume the user wants the standard daily market.
        
        # Filter: Title must usually contain "Bitcoin"
        # Sort by close_time (soonest first)
        all_markets.sort(key=lambda x: x.get("close_time", "9999"))
        
        # Identify the soonest close time (Today's Close)
        target_close_time = all_markets[0].get("close_time")
        
        # Keep only markets expiring then
        todays_markets = [m for m in all_markets if m.get("close_time") == target_close_time]
        
        if not todays_markets:
            return None, "Found markets but filtering failed."

        # 3. Parse Data
        clean_markets = []
        for m in todays_markets:
            # We want simple price range markets.
            # Filter out complex types if necessary.
            
            # Strike Parsing
            strike = m.get('floor_strike')
            if not strike:
                # Subtitle fallback: "Bitcoin above $95,000"
                sub = m.get('subtitle', '')
                match = re.search(r'\$?([\d,]+)', sub)
                if match:
                    strike = float(match.group(1).replace(',', ''))
            
            if strike:
                clean_markets.append({
                    'strike': float(strike),
                    'yes_ask': m.get('yes_ask', 0), # Cents
                    'no_ask': m.get('no_ask', 0),   # Cents
                    'ticker': m.get('ticker'),
                    'subtitle': m.get('subtitle')
                })

        # Sort by Strike
        clean_markets.sort(key=lambda x: x['strike'])
        
        # Get Current BTC
        current_btc = get_binance_price()
        
        return {
            "markets": clean_markets,
            "current_price": current_btc,
            "event_ticker": "KXBTCDAILY (Dynamic)"
        }, None

    except Exception as e:
        return None, f"Kalshi API Error: {str(e)}"

# --- Test Block ---
if __name__ == "__main__":
    print("Fetching Dynamic Kalshi Data...")
    data, err = fetch_kalshi_data_struct()
    
    if err:
        print(f"Error: {err}")
    else:
        print(f"Current BTC: ${data['current_price']:,.2f}")
        print(f"Found {len(data['markets'])} Markets expiring soonest.")
        
        # Show sample
        if len(data['markets']) > 0:
            m = data['markets'][len(data['markets'])//2]
            print(f"Sample: Strike ${m['strike']} | Yes {m['yes_ask']}c | No {m['no_ask']}c")