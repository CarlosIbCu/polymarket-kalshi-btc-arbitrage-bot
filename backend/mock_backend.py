from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/arbitrage")
def get_arbitrage_data():
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "polymarket": None,
        "kalshi": None,
        "checks": [],
        "opportunities": [],
        "errors": ["Failed to fetch polymarket data", "Failed to fetch kalshi data"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
