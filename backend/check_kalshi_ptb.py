import requests
import json

def check_kalshi_ptb():
    print("Checking Kalshi markers for 15:00 UTC...")
    # Fetch BTC markets from Kalshi
    r = requests.get("https://api.eod.kalshi.com/trade-api/v2/markets", params={"ticker": "BTC"})
    data = r.json()
    markets = data.get('markets', [])
    
    for m in markets:
        title = m.get('title', '')
        if '10:15 AM' in title or '10 AM' in title:
            # Kalshi strike is usually in the title or a field
            print(f"ID: {m.get('ticker')} | Title: {title}")
            # print(json.dumps(m, indent=2))

if __name__ == "__main__":
    check_kalshi_ptb()
