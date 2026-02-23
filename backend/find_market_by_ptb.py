import requests
import json

def find_market_by_ptb(target_ptb):
    print(f"Searching for market with PTB near {target_ptb}...")
    params = {
        "active": "true",
        "closed": "false",
        "limit": 100
    }
    r = requests.get("https://gamma-api.polymarket.com/events", params=params)
    events = r.json()
    
    found = False
    for event in events:
        slug = event.get('slug', '')
        if 'btc' in slug.lower() or 'bitcoin' in event.get('title', '').lower():
            metadata = event.get('eventMetadata', {})
            ptb = metadata.get('priceToBeat')
            if ptb:
                print(f"Slug: {slug} | PTB: {ptb}")
                if abs(float(ptb) - target_ptb) < 1.0:
                    print(f"*** MATCH FOUND! ***")
                    print(json.dumps(event, indent=2))
                    found = True
    
    if not found:
        print("No match found in top 100 events. Searching for more...")
        # Search by keyword
        params = {"active": "true", "query": "Bitcoin"}
        r = requests.get("https://gamma-api.polymarket.com/events", params=params)
        for event in r.json():
            metadata = event.get('eventMetadata', {})
            ptb = metadata.get('priceToBeat')
            if ptb:
                print(f"Slug: {event.get('slug')} | PTB: {ptb}")
                if abs(float(ptb) - target_ptb) < 1.0:
                    print(f"*** MATCH FOUND! ***")
                    print(json.dumps(event, indent=2))

if __name__ == "__main__":
    find_market_by_ptb(67050.22)
