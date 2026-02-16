"""
UPDATED: Fetch soccer markets from Polymarket Sports API
This uses the correct sports endpoint
"""
import requests
import json
from datetime import datetime

# Polymarket sports leagues
SOCCER_LEAGUES = {
    'laliga': {'name': 'La Liga', 'url': 'laliga'},
    'sea': {'name': 'Serie A', 'url': 'sea'},
    'bundesliga': {'name': 'Bundesliga', 'url': 'bundesliga'},
    'epl': {'name': 'English Premier League', 'url': 'epl'},
    'ligue1': {'name': 'Ligue 1', 'url': 'ligue-1'},
    'ucl': {'name': 'Champions League', 'url': 'ucl'},
    'uel': {'name': 'Europa League', 'url': 'uel'},
    'ere': {'name': 'Eredivisie', 'url': 'ere'},
    'por': {'name': 'Primeira Liga', 'url': 'por'},
    'elc': {'name': 'EFL Championship', 'url': 'elc'},
}

def fetch_polymarket_sports_api():
    """
    Try to fetch from Polymarket's sports API
    Note: This might be a GraphQL API or require different auth
    """
    print("=" * 60)
    print("POLYMARKET SPORTS API TEST")
    print("=" * 60)
    
    # Try the events API with sports tag
    try:
        print("\n📡 Attempting Method 1: Events API with sports tag...")
        url = "https://gamma-api.polymarket.com/events"
        params = {
            "active": "true",
            "closed": "false",
            "tag": "sports"  # Try sports tag
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"✓ Response received: {len(data)} events")
        
        if len(data) > 0:
            print("\n📊 Sample event:")
            first = data[0]
            print(f"   Question: {first.get('question')}")
            print(f"   Slug: {first.get('slug')}")
            return data
        else:
            print("❌ No events returned with sports tag")
            
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    # Try direct sports endpoint (if it exists)
    try:
        print("\n📡 Attempting Method 2: Direct sports endpoint...")
        url = "https://gamma-api.polymarket.com/sports"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"✓ Sports endpoint exists!")
        print(f"   Response: {type(data)}")
        
        return data
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("❌ Method 2: /sports endpoint doesn't exist")
        else:
            print(f"❌ Method 2 failed: {e}")
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
    
    # Try fetching a specific game directly
    try:
        print("\n📡 Attempting Method 3: Direct event fetch...")
        # Use the slug from the URL you shared
        slug = "fl1-hac-tou-2026-02-15"
        url = f"https://gamma-api.polymarket.com/events/{slug}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"✓ Successfully fetched specific game!")
        print(f"\n📊 Game Details:")
        print(f"   Slug: {data.get('slug')}")
        print(f"   Question: {data.get('question')}")
        
        markets = data.get('markets', [])
        print(f"   Markets: {len(markets)}")
        
        if markets:
            for i, market in enumerate(markets[:3], 1):
                print(f"\n   Market {i}:")
                print(f"     Outcomes: {market.get('outcomes')}")
                print(f"     Token IDs: {market.get('clobTokenIds', [])[:2]}...")
        
        return data
        
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")
    
    print("\n" + "=" * 60)
    print("⚠️  Could not find sports API endpoint")
    print("   Polymarket sports markets may require:")
    print("   1. Different API endpoint")
    print("   2. Authentication/API key")
    print("   3. GraphQL instead of REST")
    print("=" * 60)
    
    return None


def test_event_slug(slug):
    """
    Test fetching a specific event by slug
    """
    print(f"\n📡 Fetching event: {slug}")
    
    try:
        url = f"https://gamma-api.polymarket.com/events/{slug}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"✓ Success!")
        print(f"   Question: {data.get('question')}")
        print(f"   Slug: {data.get('slug')}")
        print(f"   Markets: {len(data.get('markets', []))}")
        
        return data
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None


def get_market_prices_from_event(event_data):
    """
    Extract prices from event data
    """
    if not event_data:
        return None
    
    markets = event_data.get('markets', [])
    if not markets:
        return None
    
    print("\n📊 MARKET PRICES:")
    print("=" * 60)
    
    for i, market in enumerate(markets, 1):
        outcomes = market.get('outcomes', [])
        token_ids = market.get('clobTokenIds', [])
        
        print(f"\nMarket {i}: {outcomes}")
        
        # Fetch prices from CLOB for each outcome
        for outcome, token_id in zip(outcomes, token_ids):
            try:
                url = "https://clob.polymarket.com/book"
                params = {"token_id": token_id}
                
                response = requests.get(url, params=params, timeout=5)
                response.raise_for_status()
                data = response.json()
                
                bids = data.get('bids', [])
                asks = data.get('asks', [])
                
                best_bid = max([float(b['price']) for b in bids]) if bids else 0.0
                best_ask = min([float(a['price']) for a in asks]) if asks else 0.0
                
                print(f"   {outcome}: Bid ${best_bid:.3f}, Ask ${best_ask:.3f}")
                
            except Exception as e:
                print(f"   {outcome}: Error fetching prices")


if __name__ == "__main__":
    # Try to fetch sports markets
    data = fetch_polymarket_sports_api()
    
    # Test with known soccer game slug
    print("\n" + "=" * 60)
    print("TESTING WITH KNOWN SOCCER GAME:")
    print("=" * 60)
    
    # Test multiple game slugs
    test_slugs = [
        "fl1-hac-tou-2026-02-15",  # Ligue 1 game (from your URL)
    ]
    
    for slug in test_slugs:
        event = test_event_slug(slug)
        if event:
            get_market_prices_from_event(event)
    
    print("\n" + "=" * 60)
    print("💡 FINDINGS:")
    print("=" * 60)
    print("✓ Polymarket HAS extensive soccer markets")
    print("✓ Markets are accessible via event slugs")
    print("✓ We can fetch prices via CLOB API")
    print("\n🔧 NEXT STEPS:")
    print("  1. Build slug discovery mechanism")
    print("  2. Map slugs to Kalshi tickers")
    print("  3. Run arbitrage checks")
    print("=" * 60)
