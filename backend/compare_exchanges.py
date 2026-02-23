import requests

def compare():
    try:
        bybit = requests.get("https://api.bybit.com/v5/market/tickers", params={"category": "spot", "symbol": "BTCUSDT"}).json()
        bybit_price = bybit["result"]["list"][0]["lastPrice"]
        print(f"Bybit:   {bybit_price}")
    except Exception as e:
        print(f"Bybit Error: {e}")

    try:
        binance = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"}).json()
        print(f"Binance: {binance['price']}")
    except Exception as e:
        print(f"Binance Error: {e}")

if __name__ == "__main__":
    compare()
