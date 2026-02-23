import requests
import json

POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"
slug = "btc-updown-15m-1771595400"

def check_market():
    params = {"slug": slug}
    r = requests.get(POLYMARKET_API_URL, params=params)
    if r.status_code != 200:
        print(f"Error: {r.status_code}")
        return
        
    data = r.json()
    if not data:
        print("Market not found")
        return
        
    event = data[0]
    print(f"Event: {event.get('title')}")
    for market in event.get('markets', []):
        print(f"Market Question: {market.get('question')}")
        print(f"Resolution Source: {market.get('resolutionSource')}")
        print(f"Description: {market.get('description')}")
        
if __name__ == "__main__":
    check_market()
