import requests
import json
import datetime
import pytz

def get_gamma_data(slug):
    r = requests.get("https://gamma-api.polymarket.com/events", params={"slug": slug})
    if r.status_code == 200:
        return r.json()
    return None

def get_prices():
    # Binance
    url_bn = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    bn = requests.get(url_bn).json().get("price")
    
    # Coinbase
    url_cb = "https://api.exchange.coinbase.com/products/BTC-USD/ticker"
    cb = requests.get(url_cb).json().get("price")
    
    return bn, cb

if __name__ == "__main__":
    slug = "btc-updown-15m-1771640100"
    data = get_gamma_data(slug)
    
    print(f"Slug: {slug}")
    if data:
        event = data[0]
        print("\nMetadata:")
        print(json.dumps(event.get("eventMetadata", {}), indent=2))
        
        markets = event.get("markets", [])
        if markets:
            print("\nFirst Market (lastTradePrice, bestBid, bestAsk):")
            m = markets[0]
            print(f"bestBid: {m.get('bestBid')}")
            print(f"bestAsk: {m.get('bestAsk')}")
            print(f"lastTradePrice: {m.get('lastTradePrice')}")

    bn, cb = get_prices()
    print(f"\nCurrent Prices (Live):")
    print(f"Binance: {bn}")
    print(f"Coinbase: {cb}")
    # Compare with Chainlink proxy if available
    from fetch_current_polymarket import get_chainlink_btc_usd_price
    cl, err = get_chainlink_btc_usd_price()
    print(f"Chainlink Proxy: {cl}")
