import requests
import json

def search_all_markets(target_val):
    print(f"Searching for {target_val} in all active BTC markets...")
    # Get all active markets with 'Bitcoin' or 'BTC'
    params = {
        "active": "true",
        "closed": "false",
        "limit": 500
    }
    r = requests.get("https://gamma-api.polymarket.com/markets", params=params)
    markets = r.json()
    
    for m in markets:
        q = m.get('question', '').lower()
        if 'btc' in q or 'bitcoin' in q:
            # Check priceToBeat in metadata
            meta = m.get('eventMetadata', {}) # sometimes in market, sometimes in event
            ptb = meta.get('priceToBeat')
            if ptb:
                print(f"Slug: {m.get('slug')} | PTB: {ptb}")
            
            # Check if target_val is in the string representation
            if str(target_val) in str(m):
                print(f"*** FOUND VALUE IN MARKET {m.get('id')} ***")
                print(json.dumps(m, indent=2))

if __name__ == "__main__":
    search_all_markets(67050.22)
