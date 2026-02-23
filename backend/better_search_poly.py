import requests
import json

def search():
    # Try searching for "Bitcoin" with lower limit and check all fields
    params = {
        "active": "true",
        "closed": "false",
        "limit": 100,
        "query": "Bitcoin"
    }
    r = requests.get("https://gamma-api.polymarket.com/markets", params=params)
    markets = r.json()
    
    print(f"Found {len(markets)} markets for 'Bitcoin' query")
    for m in markets:
        q = m.get('question', '')
        if '15' in q or 'minute' in q.lower():
            print(f"MATCH: {q} | {m.get('slug')}")
            print(f"  Description: {m.get('description')}")
            print(f"  Metadata: {m.get('resolutionSource')}")
            print("-" * 20)
            
    # Also try "BTC"
    params["query"] = "BTC"
    r = requests.get("https://gamma-api.polymarket.com/markets", params=params)
    markets = r.json()
    print(f"\nFound {len(markets)} markets for 'BTC' query")
    for m in markets:
        q = m.get('question', '')
        if '15' in q or 'minute' in q.lower():
            print(f"MATCH: {q} | {m.get('slug')}")
            print("-" * 20)

if __name__ == "__main__":
    search()
