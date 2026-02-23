from fetch_current_polymarket import fetch_polymarket_data_struct
import datetime

def verify_struct():
    data, err = fetch_polymarket_data_struct()
    if err:
        print(f"Error: {err}")
        return

    print(f"Time: {datetime.datetime.now()}")
    print(f"Slug: {data['slug']}")
    print(f"Price to Beat: {data['price_to_beat']}")
    print(f"Current Price: {data['current_price']}")
    print(f"Prices: {data['prices']}")

if __name__ == "__main__":
    verify_struct()
