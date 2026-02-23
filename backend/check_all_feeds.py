import requests
import datetime

def fetch_pyth():
    # BTC/USD price feed ID
    price_id = "e62df6c8b4a85fe1a67db44dc12de5db330f7acb466183979af01e0569912ef1"
    url = f"https://hermes.pyth.network/v2/updates/price/latest?ids[]={price_id}"
    try:
        r = requests.get(url)
        data = r.json()
        p_info = data['parsed'][0]['price']
        price = float(p_info['price']) * (10 ** p_info['expo'])
        print(f"Pyth BTC/USD:  ${price:,.2f}")
    except Exception as e:
        print(f"Pyth Error: {e}")

def fetch_binance():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"})
        print(f"Binance USDT: ${float(r.json()['price']):,.2f}")
        r2 = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDC"})
        print(f"Binance USDC: ${float(r2.json()['price']):,.2f}")
    except Exception as e:
        print(f"Binance Error: {e}")

def fetch_coinbase():
    try:
        r = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/ticker")
        print(f"Coinbase USD: ${float(r.json()['price']):,.2f}")
    except Exception as e:
        print(f"Coinbase Error: {e}")

if __name__ == "__main__":
    print(f"Current UTC: {datetime.datetime.now(datetime.timezone.utc)}")
    fetch_pyth()
    fetch_binance()
    fetch_coinbase()
