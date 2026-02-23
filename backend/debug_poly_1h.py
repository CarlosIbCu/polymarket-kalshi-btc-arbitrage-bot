import requests
import json
from get_current_markets_1h import get_current_market_urls

def debug_poly_1h():
    market_info = get_current_market_urls()
    slug = market_info["polymarket_slug"]
    print(f"Slug: {slug}")
    
    r = requests.get("https://gamma-api.polymarket.com/events", params={"slug": slug})
    data = r.json()
    
    if not data:
        print("No data found for slug.")
        return
        
    event = data[0]
    markets = event.get("markets", [])
    print("\nFirst Market Data (1h) SAVED TO poly_1h_debug_raw.json")
    with open("poly_1h_debug_raw.json", "w") as f:
        json.dump(markets[0] if markets else None, f, indent=2)

if __name__ == "__main__":
    debug_poly_1h()
