import requests
import json

def exhaustive_event_scan():
    print("Exhaustively scanning top 2000 active events for PTB 67050.22...")
    offset = 0
    target_val = 67050.22
    found = False
    while offset < 2000:
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
                # Check ALL fields for the value
                s = json.dumps(e)
                if str(target_val) in s or "67050" in s:
                    meta = e.get('eventMetadata', {})
                    ptb = meta.get('priceToBeat')
                    if ptb:
                        print(f"*** POSSIBLE MATCH ***")
                        print(f"ID: {e.get('id')} | Slug: {e.get('slug')} | PTB: {ptb}")
                        if abs(float(ptb) - target_val) < 1.0:
                            print(f"*** CONFIRMED MATCH! ***")
                            # print(json.dumps(e, indent=2))
                            found = True
                
        except Exception as ex:
            print(f"Error at offset {offset}: {ex}")
        offset += 100
        if found: break

    if not found:
        print("No match found in top 2000 events.")

if __name__ == "__main__":
    exhaustive_event_scan()
