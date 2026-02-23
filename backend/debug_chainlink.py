from fetch_current_polymarket_1h import _get_web3, CHAINLINK_BTC_USD_PROXY, CHAINLINK_ABI
import datetime
import time

def debug_chainlink():
    w3 = _get_web3()
    contract = w3.eth.contract(address=CHAINLINK_BTC_USD_PROXY, abi=CHAINLINK_ABI)
    
    print(f"Testing Chainlink updates (Proxy: {CHAINLINK_BTC_USD_PROXY})")
    
    for i in range(5):
        block = w3.eth.block_number
        round_data = contract.functions.latestRoundData().call()
        # round_data = (roundId, answer, startedAt, updatedAt, answeredInRound)
        price = float(round_data[1]) / 1e8
        updated_at = datetime.datetime.fromtimestamp(round_data[3])
        
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Block: {block} | Price: ${price:,.2f} | Updated At: {updated_at}")
        time.sleep(2)

if __name__ == "__main__":
    debug_chainlink()
