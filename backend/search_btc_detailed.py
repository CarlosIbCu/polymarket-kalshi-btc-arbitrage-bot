import requests
import json

POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"

def search_detailed():
    params = {
        "active": "true",
        "closed": "false",
        "limit": 100,
        "query": "Bitcoin"
    }
    r = requests.get(POLYMARKET_API_URL, params=params)
    events = r.json()
    
    for event in events:
        title = event.get('title', '')
        if "15 Minute" in title or "15-min" in title or "15m" in title or "15-minute" in title.lower():
            print(f"\nEvent: {title}")
            print(f"Slug: {event.get('slug')}")
            for market in event.get('markets', []):
                print(f"  Market: {market.get('question')}")
                print(f"  Resolution Source: {market.get('resolutionSource')}")
                print(f"  Token IDs: {market.get('clobTokenIds')}")

if __name__ == "__main__":
    search_detailed()
