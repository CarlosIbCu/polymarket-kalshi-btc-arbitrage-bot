import requests
import json

POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"

def search_btc_hourly():
    # Search for events related to BTC up or down
    params = {
        "active": "true",
        "closed": "false",
        "limit": 100,
        "query": "Bitcoin"
    }
    response = requests.get(POLYMARKET_API_URL, params=params)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
        
    data = response.json()
    for event in data:
        print(f"Event: {event.get('title')} | Slug: {event.get('slug')}")
        # for market in event.get('markets', []):
        #     print(f"  Market: {market.get('question')}")

if __name__ == "__main__":
    search_btc_hourly()
