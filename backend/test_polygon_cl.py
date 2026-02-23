from web3 import Web3
import time

RPCS = [
    "https://polygon-rpc.com",
    "https://rpc-mainnet.maticvigil.com",
    "https://1rpc.io/matic",
    "https://rpc.ankr.com/polygon",
    "https://polygon.llamarpc.com",
    "https://polygon-mainnet.infura.io/v3/1642bc9c70de4b5dbc9da0906dd203a7"
]

POLYGON_BTC_USD_FEED = "0xc907E119666Ab2312797E4F60cA2d78f5d05c30"

ABI = [
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"internalType": "uint80", "name": "roundId", "type": "uint80"},
            {"internalType": "int256", "name": "answer", "type": "int256"},
            {"internalType": "uint256", "name": "startedAt", "type": "uint256"},
            {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
            {"internalType": "uint80", "name": "answeredInRound", "type": "uint80"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def test_polygon_cl():
    for rpc in RPCS:
        print(f"Testing {rpc}...")
        try:
            w3 = Web3(Web3.HTTPProvider(rpc))
            if not w3.is_connected():
                print(f"  Failed to connect")
                continue
            
            contract = w3.eth.contract(address=w3.to_checksum_address(POLYGON_BTC_USD_FEED), abi=ABI)
            round_data = contract.functions.latestRoundData().call()
            decimals = contract.functions.decimals().call()
            price = float(round_data[1]) / (10 ** decimals)
            updated_at = round_data[3]
            print(f"  SUCCESS! Price: {price} | UpdatedAt: {updated_at} | Latency: {time.time() - updated_at}s")
            return # Stop after first success
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_polygon_cl()
