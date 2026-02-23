import requests

def get_pyth_price():
    # BTC/USD price feed ID
    price_id = "e62df6c8b4a85fe1a67db44dc12de5db330f7acb466183979af01e0569912ef1"
    url = f"https://hermes.pyth.network/v2/updates/price/latest?ids[]={price_id}"
    
    try:
        r = requests.get(url)
        data = r.json()
        price_data = data['parsed'][0]['price']
        price = int(price_data['price']) * (10 ** price_data['expo'])
        print(f"Pyth BTC/USD: ${price}")
    except Exception as e:
        print(f"Error fetching Pyth price: {e}")

if __name__ == "__main__":
    get_pyth_price()
