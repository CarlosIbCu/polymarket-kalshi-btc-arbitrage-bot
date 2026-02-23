import requests
import json

def list_recent_btc_markets():
    params = {
        "active": "true",
        "limit": 100
    }
    r = requests.get("https://gamma-api.polymarket.com/markets", params=params)
    markets = r.json()
    
    print(f"{'Slug':<40} | {'Questions':<50} | {'PTB':<15}")
    print("-" * 110)
    for m in markets:
        q = m.get('question', '').lower()
        if 'btc' in q or 'bitcoin' in q:
            meta = m.get('eventMetadata', {})
            ptb = meta.get('priceToBeat', 'N/A')
            print(f"{m.get('slug'):<40} | {m.get('question')[:50]:<50} | {ptb:<15}")

if __name__ == "__main__":
    list_recent_btc_markets()
