# AgniFlowZ — Python + frontend + blockchain starter

This project recreates the dashboard in the supplied screenshot with:
- **Frontend:** HTML, CSS, JavaScript and Chart.js
- **Backend:** Python + FastAPI
- **Blockchain:** Solidity contract + Python `web3.py` integration
- **Demo mode:** works without a blockchain so you can test the UI first

> Important: the included contract is an educational order registry. It records sell orders and marks orders purchased, but **does not transfer AGNI tokens or money**. Do not use it with real funds. Real deployment requires audited escrow/payment logic, token approvals, identity and regulatory review.

## 1. Run the website in demo mode (Windows)

Install Python 3.10+ then open PowerShell in this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload
```

Open http://127.0.0.1:8000

The screenshot used port 3000, but FastAPI defaults to 8000. To use port 3000:

```powershell
uvicorn main:app --reload --port 3000
```

## 2. Blockchain setup (local development)

Use a local Ethereum development chain such as Hardhat. Never put a mainnet private key into this project.

1. Install Node.js and create a local Hardhat project in a separate folder.
2. Install Hardhat and start a local node (`npx hardhat node`).
3. Deploy `contracts/EnergyMarket.sol` using Hardhat or Remix connected to the local node.
4. Copy the deployed contract address into `.env` as `MARKET_CONTRACT_ADDRESS`.
5. Set:
   - `APP_MODE=blockchain`
   - `RPC_URL=http://127.0.0.1:8545`
   - `CHAIN_ID=31337` (check your local chain)
   - `PRIVATE_KEY=` a **throwaway local development account key only**
6. Restart FastAPI.

The backend expects Solidity's generated ABI for these functions:
`createSellOrder(uint256,uint256)`, `buyEnergy(uint256)`, `orderCount()`, and `orders(uint256)`.
The ABI needed for those calls is included in `main.py`.

### Safer wallet design for production
For a real application, do not keep user private keys in the backend. Use a browser wallet such as MetaMask to sign transactions on the client, and let the backend serve read-only data and analytics. Add ERC-20 escrow, access control, validation, tests, monitoring, and a security audit before handling value.

## API endpoints

- `GET /api/metrics` — live-looking demo energy metrics
- `GET /api/orders` — sell orders
- `POST /api/orders/sell` — create sell order
- `POST /api/orders/{order_id}/buy` — buy/mark an order as purchased

Example sell request:

```json
{"energy_kwh": 1.5, "price_per_kwh": 12.5}
```

## Connect real smart meters
The current readings are simulated. For actual devices, ingest validated readings from your smart meter gateway using MQTT/HTTPS, authenticate devices, and store signed timestamped readings. Never trust client-supplied meter values as settlement evidence.
