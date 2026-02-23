import requests

def compare_current():
    # Binance
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"})
        print(f"Binance:  ${r.json()['price']}")
    except: pass

    # Coinbase
    try:
        r = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/ticker")
        print(f"Coinbase: ${r.json()['price']}")
    except: pass

    # Bybit
    try:
        r = requests.get("https://api.bybit.com/v5/market/tickers", params={"category": "spot", "symbol": "BTCUSDT"})
        print(f"Bybit:   ${r.json()['result']['list'][0]['lastPrice']}")
    except: pass

    # OKX
    try:
        r = requests.get("https://www.okx.com/api/v5/market/ticker", params={"instId": "BTC-USDT"})
        print(f"OKX:     ${r.json()['data'][0]['last']}")
    except: pass

    # Kraken
    try:
        r = requests.get("https://api.kraken.com/0/public/Ticker", params={"pair": "XBTUSD"})
        print(f"Kraken:  ${r.json()['result']['XXBTZUSD']['c'][0]}")
    except: pass

if __name__ == "__main__":
    compare_current()
