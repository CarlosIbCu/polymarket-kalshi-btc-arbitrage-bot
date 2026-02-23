import requests
import json

POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"

def search_all_detailed():
    params = {
        "active": "true",
        "closed": "false",
        "limit": 100
    }
    r = requests.get(POLYMARKET_API_URL, params=params)
    events = r.json()
    
    found = 0
    for event in events:
        title = event.get('title', '')
        slug = event.get('slug', '')
        if any(x in title.lower() or x in slug.lower() for x in ['15m', '15-min', '15 min']):
            print(f"FOUND: {title} | {slug}")
            for m in event.get('markets', []):
                print(f"  Market: {m.get('question')}")
                print(f"  ResSource: {m.get('resolutionSource')}")
            found += 1
    print(f"Total 15m markets found: {found}")

if __name__ == "__main__":
    search_all_detailed()
