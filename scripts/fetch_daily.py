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
DAY_SECONDS = 86_400

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
    # Yahoo has moved newer coins to numbered symbols: the plain form answers 404
    "Sui":               "SUI20947-USD",
    "Shiba Inu":         "SHIB-USD",
    "Stellar":           "XLM-USD",
    "Hedera":            "HBAR-USD",
    "Polkadot":          "DOT-USD",
    "Litecoin":          "LTC-USD",
    "Bitcoin Cash":      "BCH-USD",
    "Uniswap":           "UNI7083-USD",
    "Near Protocol":     "NEAR-USD",
    "Pepe":              "PEPE24478-USD",
    "Aptos":             "APT21794-USD",
    "Internet Computer": "ICP-USD",
    "Monero":            "XMR-USD",
    "Ethereum Classic":  "ETC-USD",
    "Polygon":           "POL28321-USD",
    "Aave":              "AAVE-USD",
    "Arbitrum":          "ARB-USD",
    "Optimism":          "OP-USD",
    "Filecoin":          "FIL-USD",
    "VeChain":           "VET-USD",
    "Tether":            "USDT-USD",
    "USDC":              "USDC-USD",
    "Hyperliquid":       "HYPE32196-USD",
    "USDS":              "USDS33039-USD",
    "LEO Token":         "LEO-USD",
    "Zcash":             "ZEC-USD",
}


def save(path: str, data: object):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    size_kb = os.path.getsize(path) // 1024
    print(f"  Saved {path} ({size_kb} KB)")


def with_yesterdays_close(history: list, symbol: str) -> list:
    """Sets yesterday's bar from Yahoo's previous close.

    This job really runs a few hours after midnight UTC, when Yahoo's daily bars don't
    have the finished day yet. The app compares today with the last bar before today, so
    every coin showed a two-day move as today's. The previous close is also the exact
    value for coins worth under a cent, where Yahoo rounds the bars themselves.
    """
    r = requests.get(
        f"{YAHOO_BASE}{symbol}",
        params={"interval": "1d", "range": "1d"},
        headers=HEADERS, timeout=20,
    )
    r.raise_for_status()
    previous_close = r.json()["chart"]["result"][0]["meta"].get("chartPreviousClose")
    if not previous_close:
        return history
    today = int(time.time()) // DAY_SECONDS * DAY_SECONDS * 1000
    yesterday = today - DAY_SECONDS * 1000
    earlier = [p for p in history if p["x"] < yesterday]
    later = [p for p in history if p["x"] >= today]
    return earlier + [{"x": yesterday, "y": round(float(previous_close), 10)}] + later


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
            history = with_yesterdays_close(history, symbol)
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

    if len(assets) < 28:
        print(f"  Only {len(assets)} assets fetched (expected 30) — skipping save to preserve existing data.")
        return

    save("data/crypto-history.json", {
        "fetched_at": int(time.time() * 1000),
        "indices": assets,
    })
    print("=== Done ===")


if __name__ == "__main__":
    main()
