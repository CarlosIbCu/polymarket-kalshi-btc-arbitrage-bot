import requests
import json

POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"

def search_active_15m():
    params = {
        "active": "true",
        "closed": "false",
        "limit": 100,
        "query": "Bitcoin"
    }
    r = requests.get(POLYMARKET_API_URL, params=params)
    events = r.json()
    
    for event in events:
        slug = event.get('slug', '')
        if "btc-updown-15m" in slug:
            print(f"\nEvent Slug: {slug}")
            for market in event.get('markets', []):
                print(f"  Resolution Source: {market.get('resolutionSource')}")
                
if __name__ == "__main__":
    search_active_15m()
