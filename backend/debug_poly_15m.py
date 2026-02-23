import requests
import json
from find_new_market import get_current_market_slug

def debug_poly_15m():
    slug = get_current_market_slug()
    print(f"Slug: {slug}")
    
    r = requests.get("https://gamma-api.polymarket.com/events", params={"slug": slug})
    data = r.json()
    
    if not data:
        print("No data found for slug.")
        return
        
    event = data[0]
    metadata = event.get("eventMetadata", {})
    markets = event.get("markets", [])
    print("\nEvent Metadata and First Market SAVED TO poly_debug_raw.json")
    with open("poly_debug_raw.json", "w") as f:
        json.dump({
            "metadata": metadata,
            "market": markets[0] if markets else None
        }, f, indent=2)

if __name__ == "__main__":
    debug_poly_15m()
