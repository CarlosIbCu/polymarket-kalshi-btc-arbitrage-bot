import requests
import json

def list_series_events(series_slug):
    print(f"Listing events for series: {series_slug}")
    params = {
        "active": "true",
        "series_slug": series_slug
    }
    r = requests.get("https://gamma-api.polymarket.com/events", params=params)
    events = r.json()
    
    for e in events:
        meta = e.get('eventMetadata', {})
        ptb = meta.get('priceToBeat')
        print(f"Slug: {e.get('slug')} | Title: {e.get('title')} | PTB: {ptb}")

def find_other_series():
    print("Searching for other BTC-related series...")
    params = {
        "active": "true",
        "query": "Bitcoin 15-minute"
    }
    r = requests.get("https://gamma-api.polymarket.com/events", params=params)
    for e in r.json():
        ss = e.get('seriesSlug')
        if ss:
            print(f"Found Series Slug: {ss} from Event: {e.get('slug')}")

if __name__ == "__main__":
    list_series_events("btc-up-or-down-15m")
    find_other_series()
