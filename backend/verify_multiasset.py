import requests
import json
import traceback

def verify():
    assets = ["btc", "eth", "sol", "xrp"]
    timeframes = ["15m", "1h"]
    
    overall_pass = True
    
    for asset in assets:
        for tf in timeframes:
            url = f"http://localhost:8000/arbitrage/{asset}/{tf}"
            print(f"Testing {url}...")
            try:
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    errors = data.get("errors", [])
                    slug = data.get("polymarket", {}).get("slug", "N/A")
                    ptb = data.get("polymarket", {}).get("price_to_beat", "N/A")
                    cur = data.get("polymarket", {}).get("current_price", "N/A")
                    opps = len(data.get("opportunities", []))
                    
                    if errors:
                        print(f"  [WARN] Data fetched but had internal errors: {errors}")
                    
                    print(f"  [PASS] Asset: {data.get('asset')} | Slug: {slug} | PTB: {ptb} | Current: {cur} | Opps: {opps}")
                else:
                    print(f"  [FAIL] HTTP {r.status_code}: {r.text}")
                    overall_pass = False
            except Exception as e:
                print(f"  [ERROR] {str(e)}")
                overall_pass = False
            print("-" * 60)
            
    if overall_pass:
        print("\n✅ ALL ENDPOINTS RESPONDED SUCCESSFULLY")
    else:
        print("\n❌ SOME ENDPOINTS FAILED")

if __name__ == "__main__":
    verify()
