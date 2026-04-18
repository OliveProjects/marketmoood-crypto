#!/usr/bin/env python3
"""
Runs every 5 minutes.
Fetches crypto intraday (5m/2d → trimmed to last 24h) and weekly (60m/5d).
Uses 5-minute candles instead of 60-minute — eliminates the 60-min staleness lag.
Fetches 2 days so the cutoff_ms filter produces a true rolling 24h window, not a
calendar-day window (crypto trades 24/7, so "1d" would start at UTC midnight).
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
    "Bitcoin":           "BTC-USD",
    "Ethereum":          "ETH-USD",
    "XRP":               "XRP-USD",
    "BNB":               "BNB-USD",
    "Solana":            "SOL-USD",
    "Dogecoin":          "DOGE-USD",
    "Cardano":           "ADA-USD",
    "Avalanche":         "AVAX-USD",
    "Tron":              "TRX-USD",
    "Chainlink":         "LINK-USD",
    "Sui":               "SUI-USD",
    "Shiba Inu":         "SHIB-USD",
    "Stellar":           "XLM-USD",
    "Hedera":            "HBAR-USD",
    "Polkadot":          "DOT-USD",
    "Litecoin":          "LTC-USD",
    "Bitcoin Cash":      "BCH-USD",
    "Uniswap":           "UNI-USD",
    "Near Protocol":     "NEAR-USD",
    "Pepe":              "PEPE-USD",
    "Aptos":             "APT-USD",
    "Internet Computer": "ICP-USD",
    "Monero":            "XMR-USD",
    "Ethereum Classic":  "ETC-USD",
    "Polygon":           "POL-USD",
    "Aave":              "AAVE-USD",
    "Arbitrum":          "ARB-USD",
    "Optimism":          "OP-USD",
    "Filecoin":          "FIL-USD",
    "VeChain":           "VET-USD",
}


def save(path: str, data: object):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    size_kb = os.path.getsize(path) // 1024
    print(f"  Saved {path} ({size_kb} KB)")


def fetch_yahoo_chart(symbol: str, interval: str, range_: str) -> list | None:
    try:
        r = requests.get(
            f"{YAHOO_BASE}{symbol}",
            params={"interval": interval, "range": range_},
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        result = r.json()["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
        return [
            {"x": int(ts) * 1000, "y": round(float(c), 8)}
            for ts, c in zip(timestamps, closes)
            if c is not None
        ]
    except Exception as e:
        print(f"    ERROR {symbol} {interval}/{range_}: {e}")
        return None


def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"=== fetch_fast.py (crypto)  {ts} ===")

    cutoff_ms = (int(time.time()) - 86_400) * 1000  # 24h ago

    intraday: dict = {}
    weekly: dict = {}

    for name, symbol in SYMBOLS.items():
        print(f"  {name}")
        pts_i = fetch_yahoo_chart(symbol, "5m", "2d")
        if pts_i:
            intraday[name] = [p for p in pts_i if p["x"] >= cutoff_ms]
        pts_w = fetch_yahoo_chart(symbol, "60m", "5d")
        if pts_w:
            weekly[name] = pts_w
        time.sleep(0.3)

    now_ms = int(time.time() * 1000)
    save("data/crypto-intraday.json", {"fetched_at": now_ms, "assets": intraday})
    save("data/crypto-weekly.json",   {"fetched_at": now_ms, "assets": weekly})

    print("=== Done ===")


if __name__ == "__main__":
    main()
