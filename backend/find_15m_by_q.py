import requests
import json

def find_15m_markets():
    print("Searching for 15-minute markets...")
    params = {
        "active": "true",
        "limit": 500
    }
    r = requests.get("https://gamma-api.polymarket.com/markets", params=params)
    markets = r.json()
    
    for m in markets:
        q = m.get('question', '')
        if '15 minute' in q.lower():
            meta = m.get('eventMetadata', {})
            ptb = meta.get('priceToBeat')
            start = m.get('eventStartTime')
            slug = m.get('slug')
            print(f"Slug: {slug} | Start: {start} | PTB: {ptb} | Q: {q}")

if __name__ == "__main__":
    find_15m_markets()
