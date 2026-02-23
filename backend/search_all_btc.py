import requests
import json

POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"

def search_all():
    params = {
        "active": "true",
        "closed": "false",
        "limit": 100
    }
    r = requests.get(POLYMARKET_API_URL, params=params)
    events = r.json()
    
    for event in events:
        title = event.get('title', '')
        if 'Bitcoin' in title:
            print(f"{title} | {event.get('slug')}")

if __name__ == "__main__":
    search_all()
