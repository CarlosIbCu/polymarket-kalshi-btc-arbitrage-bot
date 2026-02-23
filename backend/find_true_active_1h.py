import requests
import re
import json

POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"

def find_active_1h_market():
    params = {
        "active": "true",
        "closed": "false",
        "limit": 100,
        "query": "Bitcoin Up or Down 15 Minutes"
    }
    r = requests.get(POLYMARKET_API_URL, params=params)
    events = r.json()
    
    print(f"Found {len(events)} active events.")
    for event in events:
        title = event.get('title', '')
        slug = event.get('slug', '')
        print(f"\nEvent: {title}")
        print(f"  Slug: {slug}")
        
        for market in event.get('markets', []):
            question = market.get('question', '')
            print(f"  Market: {question}")
            
if __name__ == "__main__":
    find_active_1h_market()
