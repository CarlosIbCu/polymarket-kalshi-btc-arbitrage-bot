import requests
import json

def scan_all_events():
    print("Exhaustively scanning top 1000 events for PTB...")
    offset = 0
    found = False
    while offset < 1000:
        params = {
            "active": "true",
            "closed": "false",
            "limit": 100,
            "offset": offset
        }
        try:
            r = requests.get("https://gamma-api.polymarket.com/events", params=params)
            events = r.json()
            if not events:
                break
            for e in events:
                meta = e.get('eventMetadata', {})
                ptb = meta.get('priceToBeat')
                if ptb:
                    ptb_val = float(ptb)
                    if abs(ptb_val - 67050.22) < 2.0:
                        print(f"*** MATCH IN EVENT {e.get('id')} ***")
                        print(f"Slug: {e.get('slug')}")
                        print(f"Title: {e.get('title')}")
                        print(f"PTB: {ptb}")
                        found = True
                        # print(json.dumps(e, indent=2))
        except Exception as ex:
            print(f"Error at offset {offset}: {ex}")
        
        offset += 100
    
    if not found:
        print("No match found in top 1000 events.")

if __name__ == "__main__":
    scan_all_events()
