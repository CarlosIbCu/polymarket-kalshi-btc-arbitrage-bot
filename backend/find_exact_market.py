import requests
import json

def find_exact_market():
    print("Searching for exact market by title and PTB...")
    params = {
        "active": "true",
        "query": "Bitcoin Up or Down - 15 Minutes"
    }
    r = requests.get("https://gamma-api.polymarket.com/events", params=params)
    events = r.json()
    
    for e in events:
        slug = e.get('slug')
        title = e.get('title')
        meta = e.get('eventMetadata', {})
        ptb = meta.get('priceToBeat')
        print(f"Slug: {slug} | Title: {title} | PTB: {ptb}")
        if ptb and abs(float(ptb) - 67050.22) < 5.0:
            print(f"*** POSSIBLE MATCH! ***")
            print(json.dumps(e, indent=2))

    print("\nSearching for 5-minute markets...")
    params = {
        "active": "true",
        "query": "Bitcoin Up or Down - 5 Minutes"
    }
    r = requests.get("https://gamma-api.polymarket.com/events", params=params)
    for e in r.json():
        slug = e.get('slug')
        ptb = e.get('eventMetadata', {}).get('priceToBeat')
        print(f"Slug: {slug} | PTB: {ptb}")

if __name__ == "__main__":
    find_exact_market()
