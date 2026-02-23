import requests
import json
import re
from get_current_markets_1h import get_current_market_urls

POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"

def debug_polymarket():
    market_info = get_current_market_urls()
    slug = market_info["polymarket_slug"]
    
    response = requests.get(POLYMARKET_API_URL, params={"slug": slug})
    if response.status_code != 200:
        with open("poly_debug_out.txt", "w") as f:
            f.write(f"Error: {response.status_code}")
        return
        
    data = response.json()
    with open("poly_debug_out.txt", "w") as f:
        if not data:
            f.write("No data found")
        else:
            f.write(json.dumps(data[0], indent=2))

if __name__ == "__main__":
    debug_polymarket()
