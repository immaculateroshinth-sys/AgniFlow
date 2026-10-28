import os, random, time
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()
BASE = Path(__file__).resolve().parent
app = FastAPI(title="AgniFlowZ API", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

MODE = os.getenv("APP_MODE", "demo").lower()
RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
MARKET_ADDRESS = os.getenv("MARKET_CONTRACT_ADDRESS", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")

# Minimal ABI for EnergyMarket.sol
MARKET_ABI = [
    {"type":"function","name":"createSellOrder","stateMutability":"nonpayable",
     "inputs":[{"name":"energyKWh","type":"uint256"},{"name":"pricePerKWh","type":"uint256"}],"outputs":[{"name":"orderId","type":"uint256"}]},
    {"type":"function","name":"buyEnergy","stateMutability":"nonpayable",
     "inputs":[{"name":"orderId","type":"uint256"}],"outputs":[]},
    {"type":"function","name":"orderCount","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"uint256"}]},
    {"type":"function","name":"orders","stateMutability":"view","inputs":[{"name":"","type":"uint256"}],
     "outputs":[{"name":"seller","type":"address"},{"name":"energyKWh","type":"uint256"},{"name":"pricePerKWh","type":"uint256"},{"name":"active","type":"bool"}]}
]

def get_chain():
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 3}))
        if not w3.is_connected():
            return None, None, None
        if not MARKET_ADDRESS:
            return w3, None, None
        contract = w3.eth.contract(address=Web3.to_checksum_address(MARKET_ADDRESS), abi=MARKET_ABI)
        return w3, contract, None
    except Exception as e:
        return None, None, str(e)

@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")

@app.get("/api/metrics")
def metrics():
    # Demo telemetry. Replace with MQTT/IoT meter readings for real installations.
    generation = round(5.2 + random.uniform(-0.35, 0.35), 2)
    consumption = round(3.1 + random.uniform(-0.3, 0.3), 2)
    return {"generation": generation, "consumption": consumption,
            "balance": 1000, "surplus": round(max(0, generation-consumption), 2),
            "sell_price": 12.5, "buy_price": 11.8, "mode": MODE}

class OrderRequest(BaseModel):
    energy_kwh: float = Field(default=1.0, gt=0, le=100000)
    price_per_kwh: float = Field(default=12.5, gt=0, le=1000000)

@app.get("/api/orders")
def get_orders():
    w3, contract, err = get_chain()
    if MODE == "blockchain" and contract:
        try:
            count = contract.functions.orderCount().call()
            result = []
            for i in range(count):
                seller, energy, price, active = contract.functions.orders(i).call()
                if active:
                    result.append({"id": i, "seller": seller, "energy_kwh": energy/1000,
                                   "price_per_kwh": price/1000, "active": active, "source": "blockchain"})
            return {"orders": result, "source": "blockchain"}
        except Exception as e:
            raise HTTPException(503, f"Could not read blockchain: {e}")
    return {"orders": [
        {"id": 1, "seller": "0xDemoSeller", "energy_kwh": 2.0, "price_per_kwh": 12.5, "active": True, "source": "demo"}
    ], "source": "demo"}

@app.post("/api/orders/sell")
def sell_order(req: OrderRequest):
    if MODE == "blockchain":
        w3, contract, err = get_chain()
        if not w3 or not contract or not PRIVATE_KEY:
            raise HTTPException(503, "Blockchain is not configured. Set RPC_URL, MARKET_CONTRACT_ADDRESS and PRIVATE_KEY in .env.")
        try:
            account = w3.eth.account.from_key(PRIVATE_KEY)
            # Solidity stores values as thousandths to support 3 decimal places.
            tx = contract.functions.createSellOrder(
                int(req.energy_kwh * 1000), int(req.price_per_kwh * 1000)
            ).build_transaction({
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
                "chainId": int(os.getenv("CHAIN_ID", str(w3.eth.chain_id))),
                "gas": 250000,
                "gasPrice": w3.eth.gas_price
            })
            signed = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            return {"ok": True, "source": "blockchain", "tx_hash": tx_hash.hex(),
                    "status": int(receipt.status), "message": "Sell order submitted on-chain"}
        except Exception as e:
            raise HTTPException(400, f"Blockchain transaction failed: {e}")
    return {"ok": True, "source": "demo", "tx_hash": None,
            "message": f"Demo sell order created for {req.energy_kwh:g} kWh at {req.price_per_kwh:g} AGNI/kWh"}

@app.post("/api/orders/{order_id}/buy")
def buy_order(order_id: int):
    if MODE == "blockchain":
        w3, contract, err = get_chain()
        if not w3 or not contract or not PRIVATE_KEY:
            raise HTTPException(503, "Blockchain is not configured. Set RPC_URL, MARKET_CONTRACT_ADDRESS and PRIVATE_KEY in .env.")
        try:
            account = w3.eth.account.from_key(PRIVATE_KEY)
            tx = contract.functions.buyEnergy(order_id).build_transaction({
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
                "chainId": int(os.getenv("CHAIN_ID", str(w3.eth.chain_id))),
                "gas": 250000,
                "gasPrice": w3.eth.gas_price
            })
            signed = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            return {"ok": True, "source": "blockchain", "tx_hash": tx_hash.hex(),
                    "status": int(receipt.status), "message": "Buy transaction submitted on-chain"}
        except Exception as e:
            raise HTTPException(400, f"Blockchain transaction failed: {e}")
    return {"ok": True, "source": "demo", "tx_hash": None,
            "message": f"Demo purchase request for order {order_id} recorded"}
