import requests

def compare():
    usdt = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"}).json()
    usdc = requests.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDC"}).json()
    print(f"BTC-USDT: {usdt['price']}")
    print(f"BTC-USDC: {usdc['price']}")

if __name__ == "__main__":
    compare()
