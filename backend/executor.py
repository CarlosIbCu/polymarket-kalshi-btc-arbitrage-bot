import os
import math
import time
import requests
import base64
from eth_account import Account
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs
from py_clob_client.exceptions import PolyApiException
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
DRY_RUN = True   # <--- Set to True to SIMULATE, False to SPEND MONEY
TARGET_SPEND = 1.10 # Target $1.10 to clear $1 limit

class TradeExecutor:
    def __init__(self):
        self.is_ready = False
        
        # --- KALSHI SETUP ---
        try:
            self.kalshi_session = requests.Session()
            self.kalshi_api = "https://api.kalshi.com/trade-api/v2"
            self.kalshi_key_id = os.getenv("KALSHI_KEY_ID")
            key_path = os.getenv("KALSHI_PRIVATE_KEY")
            
            if not key_path:
                raise ValueError("Missing KALSHI_PRIVATE_KEY")
                
            if "BEGIN" in key_path: # It's a string key
                self.kalshi_private_key = load_pem_private_key(key_path.encode(), password=None)
            else: # It's a file path
                with open(key_path, "rb") as f:
                    self.kalshi_private_key = load_pem_private_key(f.read(), password=None)
            self.is_ready_kalshi = True
        except Exception as e:
            self.is_ready_kalshi = False
            print(f"❌ Kalshi Keys Missing/Invalid: {e}")

        # --- POLYMARKET SETUP ---
        try:
            pk = os.getenv("POLY_PRIVATE_KEY", "").strip()
            if not pk: raise ValueError("Missing POLY_PRIVATE_KEY")
            if pk.startswith("0x"): pk = pk[2:]
            self.poly_key = pk
            
            signer = Account.from_key(pk)
            self.poly_eoa = signer.address
            self.poly_proxy = os.getenv("POLY_PROXY_ADDRESS")
            
            # Default to Type 1 (Proxy) if address exists, else Type 0 (EOA)
            sig_type = 1 if self.poly_proxy else 0
            funder = self.poly_proxy if self.poly_proxy else self.poly_eoa
            
            print(f"   ℹ️  Polymarket Identity: {funder} (Type: {sig_type})")
            
            self.poly_client = ClobClient("https://clob.polymarket.com", key=pk, chain_id=137, signature_type=sig_type, funder=funder)
            self.poly_client.set_api_creds(self.poly_client.create_or_derive_api_creds())
            self.is_ready_poly = True
            print("✅ Polymarket Connected")
        except Exception as e:
            self.is_ready_poly = False
            print(f"❌ Poly Setup Failed: {e}")

        self.is_ready = self.is_ready_poly and self.is_ready_kalshi

    def get_kalshi_headers(self, method, path):
        ts = str(int(time.time() * 1000))
        msg = ts + method + path
        sig = self.kalshi_private_key.sign(msg.encode('utf-8'), padding.PSS(padding.MGF1(hashes.SHA256()), padding.PSS.DIGEST_LENGTH), hashes.SHA256())
        return {
            "KALSHI-ACCESS-KEY": self.kalshi_key_id,
            "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode('utf-8'),
            "KALSHI-ACCESS-TIMESTAMP": ts,
            "Content-Type": "application/json"
        }
        
    def login_kalshi(self):
        pass # Keys are loaded, lazy validation

    def execute_trade(self, opp):
        if not self.is_ready: 
            print("⚠️ Executor not ready.")
            return
        
        price = float(opp.get('poly_price', 0))
        
        # --- FIX: Handle 0 Price Gracefully ---
        if price <= 0.000001: 
            print(f"⚠️ SKIP: Polymarket Price is ${price} (Empty Order Book). Cannot Buy.")
            return

        # 1. Calc Quantity (> $1)
        # We catch ZeroDivisionError just in case, though the check above handles it
        try:
            qty = math.ceil(TARGET_SPEND / price)
        except ZeroDivisionError:
            print("❌ Price is 0. Cannot divide.")
            return
            
        total = qty * price
        
        print(f"\n⚡ EXECUTION: {opp.get('kalshi_ticker')}")
        print(f"   Strategy: Buy Poly {opp.get('kalshi_side', '??').upper()} + Kalshi {opp.get('kalshi_side', '??').upper()}")
        print(f"   Math: {qty} units @ ${price:.2f} = ${total:.2f}")

        # --- DRY RUN CHECK ---
        if DRY_RUN:
            print(f"   🧪 [DRY RUN ACTIVE] Skipping API calls.")
            print(f"      -> Would have bought Poly Token: {opp['poly_token_id']}")
            print(f"      -> Would have bought Kalshi: {opp['kalshi_price']}")
            return

        # 2. Polymarket Execution
        try:
            print("   1. Buying Polymarket...")
            order = OrderArgs(price=price, size=float(qty), side="BUY", token_id=opp['poly_token_id'])
            
            # Try Type 1 (Standard Proxy)
            try:
                self.poly_client.post_order(self.poly_client.create_order(order))
                print("      ✅ Poly Order Sent (Type 1)")
            except PolyApiException as e:
                # Fallback to Type 2 or Type 0 if signature fails
                if "signature" in str(e).lower() or "400" in str(e):
                    print("      ⚠️ Sig Type 1 failed, trying Type 2...")
                    c2 = ClobClient("https://clob.polymarket.com", key=self.poly_key, chain_id=137, signature_type=2, funder=self.poly_proxy)
                    c2.set_api_creds(self.poly_client.creds)
                    c2.post_order(c2.create_order(order))
                    print("      ✅ Poly Order Sent (Type 2)")
                else:
                    raise e
        except Exception as e:
            print(f"      ❌ Poly Failed: {e}")
            return # Stop if Poly fails to avoid unhedged exposure

        # 3. Kalshi Execution
        try:
            print("   2. Buying Kalshi...")
            side = opp['kalshi_side'].lower()
            payload = {
                "action": "buy", "count": qty, "type": "limit", "ticker": opp['kalshi_ticker'], "side": side,
                "yes_price": int(opp['kalshi_price']*100) if side=='yes' else None,
                "no_price": int(opp['kalshi_price']*100) if side=='no' else None
            }
            # Remove None values
            payload = {k:v for k,v in payload.items() if v is not None}
            
            path = "/portfolio/orders"
            headers = self.get_kalshi_headers("POST", "/trade-api/v2" + path)
            resp = self.kalshi_session.post(self.kalshi_api + path, json=payload, headers=headers)
            
            if resp.status_code in [200, 201]:
                print(f"      ✅ Kalshi Success: {resp.json().get('order', {}).get('order_id')}")
            else:
                print(f"      ❌ Kalshi Failed: {resp.text}")
        except Exception as e:
            print(f"      ❌ Kalshi Failed: {e}")