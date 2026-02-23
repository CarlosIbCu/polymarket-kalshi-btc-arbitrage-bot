import json
import os
import datetime

def read_utf16_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-16') as f:
            return json.load(f)
    except Exception as e:
        try:
            with open(filepath, 'r', encoding='utf-16le') as f:
                return json.load(f)
        except Exception as e2:
            return None

if __name__ == "__main__":
    filepath = 'current_gamma_inspect.json'
    data = read_utf16_json(filepath)
    if data:
        event = data[0] if data else {}
        print(f"Event Slug: {event.get('slug')}")
        print(f"Description: {event.get('description')}")
        print(f"Resolution Rules: {event.get('resolutionRules')}")
        print(f"Custom Metadata: {json.dumps(event.get('customMetadata'), indent=2)}")
        
        print("\n--- MARKETS ---")
        for i, m in enumerate(event.get('markets', [])):
            print(f"\nMarket {i}:")
            print(f"  Ticker: {m.get('ticker')}")
            print(f"  Metadata: {json.dumps(m.get('metadata'), indent=2)}")
            print(f"  Outcomes: {m.get('outcomes')}")
            print(f"  Prices: {m.get('outcomePrices')}")
        
        if 'eventMetadata' in event:
             print("\n--- EVENT METADATA ---")
             print(json.dumps(event['eventMetadata'], indent=2))
    else:
        print("Failed to load data.")
