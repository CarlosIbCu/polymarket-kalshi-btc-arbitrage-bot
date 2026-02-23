import requests
import json

POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"

def check_1h_resolution():
    params = {
        "active": "true",
        "closed": "false",
        "limit": 100,
        "query": "Bitcoin Up or Down"
    }
    r = requests.get(POLYMARKET_API_URL, params=params)
    events = r.json()
    
    for event in events:
        title = event.get('title', '')
        if "Bitcoin Up or Down" in title and "15 Minutes" not in title:
            print(f"\nEvent: {title}")
            for market in event.get('markets', []):
                print(f"  Question: {market.get('question')}")
                print(f"  Resolution Source: {market.get('resolutionSource')}")
                
if __name__ == "__main__":
    check_1h_resolution()
