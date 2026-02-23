import requests
import json

def fetch_all_markets():
    all_markets = []
    limit = 100
    offset = 0
    while True:
        params = {
            "active": "true",
            "closed": "false",
            "limit": limit,
            "offset": offset
        }
        r = requests.get("https://gamma-api.polymarket.com/markets", params=params)
        data = r.json()
        if not data:
            break
        all_markets.extend(data)
        offset += limit
        if len(data) < limit:
            break
        if offset > 1000: # Safety break
            break
            
    with open("poly_markets_dump.json", "w") as f:
        json.dump(all_markets, f, indent=2)
    
    print(f"Dumped {len(all_markets)} markets to poly_markets_dump.json")
    
    # Filter for Bitcoin
    for m in all_markets:
        q = m.get('question', '').lower()
        if 'bitcoin' in q and ('15 minute' in q or '15-min' in q or '15m' in q):
            print(f"MATCH: {m.get('question')} | {m.get('slug')}")
            print(f"  Condition: {m.get('resolutionSource')}")

if __name__ == "__main__":
    fetch_all_markets()
