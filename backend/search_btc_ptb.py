import requests
import json

def search_btc_markets():
    print("Searching for btc markets...")
    params = {
        "active": "true",
        "limit": 500
    }
    r = requests.get("https://gamma-api.polymarket.com/markets", params=params)
    markets = r.json()
    
    for m in markets:
        q = m.get('question', '').lower()
        if 'btc' in q or 'bitcoin' in q:
            meta = m.get('eventMetadata', {})
            ptb = meta.get('priceToBeat')
            start = m.get('eventStartTime')
            slug = m.get('slug')
            print(f"Slug: {slug} | Start: {start} | PTB: {ptb}")
            if ptb and abs(float(ptb) - 67050.22) < 5.0:
                print(f"*** POTENTIAL MATCH FOUND! ***")
                print(json.dumps(m, indent=2))

if __name__ == "__main__":
    search_btc_markets()
