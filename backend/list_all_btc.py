import requests
import json

def list_all_active_btc():
    print("Listing all active BTC markets (broad search)...")
    all_markets = []
    offset = 0
    while offset < 1000:
        params = {
            "active": "true",
            "closed": "false",
            "limit": 100,
            "offset": offset
        }
        r = requests.get("https://gamma-api.polymarket.com/markets", params=params)
        markets = r.json()
        if not markets:
            break
        all_markets.extend(markets)
        offset += 100
    
    print(f"Total active markets fetched: {len(all_markets)}")
    print(f"{'ID':<10} | {'Slug':<40} | {'Start':<25} | {'PTB':<15}")
    print("-" * 100)
    for m in all_markets:
        q = m.get('question', '').lower()
        if 'btc' in q or 'bitcoin' in q:
            meta = m.get('eventMetadata', {})
            ptb = meta.get('priceToBeat', 'N/A')
            start = m.get('eventStartTime', 'N/A')
            print(f"{m.get('id'):<10} | {m.get('slug'):<40} | {start:<25} | {ptb:<15}")

if __name__ == "__main__":
    list_all_active_btc()
