import requests
import json

def check_slug(slug):
    # Search events by slug
    url = f"https://gamma-api.polymarket.com/events?slug={slug}"
    r = requests.get(url)
    data = r.json()
    if not data:
        print(f"Slug {slug} not found in events")
        return
        
    event = data[0]
    print(f"Event Found: {event.get('title')}")
    for m in event.get('markets', []):
        print(f"  Market: {m.get('question')}")
        print(f"  ResSource: {m.get('resolutionSource')}")
        print(f"  Active: {m.get('active')}")
        print(f"  Ends: {m.get('end_date_iso')}")
        # print(json.dumps(m, indent=2))

if __name__ == "__main__":
    check_slug("btc-updown-15m-1771595400")
    # Also check the current expected 15m boundary
    # 14:15 UTC -> 1771596900
    check_slug("btc-updown-15m-1771596900")
    # Also check 14:20 UTC -> 1771597200
    check_slug("btc-updown-15m-1771597200")
