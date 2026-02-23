import json

def search():
    with open("poly_markets_dump.json", "r") as f:
        data = json.load(f)
    
    print(f"Total markets: {len(data)}")
    for m in data:
        q = m.get('question', '').lower()
        if 'bitcoin' in q:
            print(f"QUESTION: {m.get('question')}")
            print(f"  SLUG: {m.get('slug')}")
            print(f"  SOURCE: {m.get('resolutionSource')}")
            print(f"  DESCRIPTION: {m.get('description')}")
            print("-" * 20)

if __name__ == "__main__":
    search()
