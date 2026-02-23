import requests
import json

def find_market_by_start_time(start_time_iso):
    print(f"Searching for markets starting at {start_time_iso}...")
    params = {
        "active": "true",
        "limit": 500
    }
    r = requests.get("https://gamma-api.polymarket.com/markets", params=params)
    markets = r.json()
    
    for m in markets:
        if m.get('eventStartTime') == start_time_iso or m.get('startTime') == start_time_iso:
            q = m.get('question', '')
            if 'btc' in q.lower() or 'bitcoin' in q.lower():
                print(f"--- Market {m.get('id')} ---")
                print(f"Question: {m.get('question')}")
                print(f"Slug: {m.get('slug')}")
                meta = m.get('eventMetadata', {})
                print(f"PTB: {meta.get('priceToBeat')}")
                # print(json.dumps(m, indent=2))

if __name__ == "__main__":
    find_market_by_start_time("2026-02-20T15:00:00Z")
