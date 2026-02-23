import time
from fetch_current_polymarket import get_chainlink_btc_usd_price, _get_web3, CHAINLINK_BTC_USD_PROXY, CHAINLINK_ABI

def test_cl():
    w3 = _get_web3()
    contract = w3.eth.contract(address=CHAINLINK_BTC_USD_PROXY, abi=CHAINLINK_ABI)
    
    for _ in range(5):
        price, err = get_chainlink_btc_usd_price()
        round_data = contract.functions.latestRoundData().call()
        updated_at = round_data[3]
        print(f"Price: {price} | UpdatedAt: {updated_at} | Latency: {time.time() - updated_at}s")
        time.sleep(1)

if __name__ == "__main__":
    test_cl()
