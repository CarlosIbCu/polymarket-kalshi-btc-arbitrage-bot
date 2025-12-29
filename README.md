# 🤖 Polymarket-Kalshi BTC Arbitrage Bot

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-14+-black.svg)
![Status](https://img.shields.io/badge/status-active-green.svg)

**Real-time arbitrage detection for the Bitcoin 1-Hour Price market between Polymarket and Kalshi.**

## 🚀 Overview

The **Polymarket-Kalshi BTC Arbitrage Bot** is a powerful tool designed to monitor and identify risk-free arbitrage opportunities in the **Bitcoin 1-Hour Price** market between two of the world's leading prediction markets: **Polymarket** and **Kalshi**.

By leveraging real-time data from Polymarket's CLOB (Central Limit Order Book) and Kalshi's API, this bot calculates the combined cost of opposing positions (e.g., "Yes" on Kalshi + "Down" on Polymarket) for the same hourly expiration. If the total cost is less than $1.00, a risk-free profit opportunity exists.

This project includes:
-   **Python Backend**: Fast and efficient data fetching and arbitrage logic using FastAPI.
-   **Next.js Dashboard**: A beautiful, real-time UI built with shadcn/ui to visualize market data and opportunities.

> 📚 **Learn the Theory**: Read our detailed [Arbitrage Thesis](thesis.md) to understand the mathematics behind risk-free profits in binary option markets.

## ✨ Features

-   **Real-Time Monitoring**: Fetches live prices every second.
-   **Smart Matching**: Automatically matches Polymarket events with their corresponding Kalshi markets.
-   **Arbitrage Detection**: Instantly identifies "risk-free" trades where the total cost < $1.00.
-   **AI-Powered Analysis** (via BlockRun): Get intelligent risk assessment, liquidity analysis, and trade recommendations using GPT-5, Claude, Gemini, and more. Pay with USDC micropayments - no API keys needed.
-   **Visual Dashboard**:
    -   **Live Updates**: See prices change in real-time.
    -   **Best Opportunity Highlight**: Prominently displays the most profitable trade.
    -   **Visual Cost Bars**: Quickly assess the cost breakdown of each strategy.
-   **Comprehensive Analysis**: Checks multiple strategies (Poly Down + Kalshi Yes, Poly Up + Kalshi No).

## 🛠️ Tech Stack

-   **Backend**: Python, FastAPI, Uvicorn, Requests
-   **Frontend**: TypeScript, Next.js, Tailwind CSS, shadcn/ui, Lucide React

## 🤖 AI-Powered Analysis (Optional)

This bot supports **AI-powered arbitrage analysis** via [BlockRun](https://blockrun.ai). Get intelligent insights on:
- Risk assessment for detected opportunities
- Liquidity analysis and execution feasibility
- Market sentiment and timing recommendations

### How It Works

BlockRun enables AI agents to access 31+ LLMs (GPT-5, GPT-4o, Claude, Gemini) via **x402 USDC micropayments** on Base. No API keys required - your wallet pays directly for LLM calls.

### Enable AI Analysis

1. Set environment variables:
```bash
export BLOCKRUN_ENABLED=true
export BLOCKRUN_API_URL="https://api.blockrun.ai/v1"
```

2. Ensure your wallet has USDC on Base network

3. Use the AI endpoints:
```bash
# Get AI analysis of current opportunities
curl "http://localhost:8000/ai/analyze"

# Get BTC market sentiment
curl "http://localhost:8000/ai/sentiment"

# Include AI analysis in main arbitrage endpoint
curl "http://localhost:8000/arbitrage?include_ai=true"

# Use a specific model (default: gpt-4o-mini)
curl "http://localhost:8000/ai/analyze?model=claude-3-5-sonnet"
```

### Available AI Models

| Provider | Models |
|----------|--------|
| OpenAI | gpt-5, gpt-4o, gpt-4o-mini |
| Anthropic | claude-3-5-sonnet |
| Google | gemini-2.0-flash |

Learn more at [blockrun.ai](https://blockrun.ai)

---

## 📦 Installation

### Prerequisites
-   Python 3.9+
-   Node.js 18+
-   npm or yarn

### 1. Clone the Repository
```bash
git clone https://github.com/CarlosIbCu/polymarket-kalshi-btc-arbitrage-bot.git
cd polymarket-kalshi-btc-arbitrage-bot
```

### 2. Setup Backend
Navigate to the `backend` directory and install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### 3. Setup Frontend
Navigate to the `frontend` directory and install dependencies:
```bash
cd ../frontend
npm install
```

## 🚀 Usage

To run the full application, you need to start both the backend and frontend servers.

### 1. Start Backend API
In the `backend` directory:
```bash
python3 api.py
```
The API will start at `http://localhost:8000`.

### 2. Start Frontend Dashboard
In the `frontend` directory:
```bash
npm run dev
```
The dashboard will be available at `http://localhost:3000`.

## 📊 How It Works

1.  **Data Ingestion**: The bot fetches the latest "Bitcoin Up or Down" hourly market from Polymarket and searches for the corresponding markets on Kalshi.
2.  **Normalization**: Prices are normalized to a standard probability format (0.00 - 1.00).
3.  **Comparison**: The bot compares the "Price to Beat" (Strike Price) on Polymarket with Kalshi's strike prices.
    -   If `Poly Strike > Kalshi Strike`: Checks `Poly Down + Kalshi Yes`.
    -   If `Poly Strike < Kalshi Strike`: Checks `Poly Up + Kalshi No`.
4.  **Calculation**: It sums the cost of the two legs. If `Total Cost < $1.00`, it's an arbitrage opportunity!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the project
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
