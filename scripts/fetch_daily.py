#!/usr/bin/env python3
"""
Runs once daily. Fetches full 5-year price history for all crypto assets.
"""

import json
import os
import time
from datetime import datetime, timezone

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"

SYMBOLS = {
    "Bitcoin":  "BTC-USD",
    "Ethereum": "ETH-USD",
    "Solana":   "SOL-USD",
    "XRP":      "XRP-USD",
    "BNB":      "BNB-USD",
    "Dogecoin": "DOGE-USD",
    "Cardano":  "ADA-USD",
}


def save(path: str, data: object):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    size_kb = os.path.getsize(path) // 1024
    print(f"  Saved {path} ({size_kb} KB)")


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"=== fetch_daily.py (crypto)  {ts} ===")

    assets = []
    for name, symbol in SYMBOLS.items():
        print(f"  {name}")
        try:
            r = requests.get(
                f"{YAHOO_BASE}{symbol}",
                params={"interval": "1d", "range": "5y"},
                headers=HEADERS, timeout=20,
            )
            r.raise_for_status()
            result = r.json()["chart"]["result"][0]
            timestamps = result["timestamp"]
            closes = result["indicators"]["quote"][0]["close"]
            history = [
                {"x": int(ts) * 1000, "y": round(float(c), 8)}
                for ts, c in zip(timestamps, closes)
                if c is not None
            ]
            if len(history) < 2:
                continue
            meta = result.get("meta", {})
            price = meta.get("regularMarketPrice") or history[-1]["y"]
            prev = history[-2]["y"]
            assets.append({
                "name": name, "price": price,
                "changePct": (price - prev) / prev * 100.0,
                "changeAbs": price - prev,
                "history": history,
            })
        except Exception as e:
            print(f"    ERROR {name}: {e}")
        time.sleep(0.4)

    save("data/crypto-history.json", {
        "fetched_at": int(time.time() * 1000),
        "indices": assets,
    })
    print("=== Done ===")


if __name__ == "__main__":
    main()
