"""Live market data fetcher with in-memory caching and graceful fallback.

Fetches real-time / 1-day delayed quotes from public Yahoo Finance endpoints
using only Python standard library urllib.request.
"""

import json
import time
import urllib.request
from typing import Dict, Any, List

# Symbol mapping: FinShock asset ID -> Yahoo Finance ticker
YFINANCE_SYMBOLS: Dict[str, Dict[str, str]] = {
    "NIFTY_50": {"ticker": "^NSEI", "name": "NIFTY 50", "prefix": "₹"},
    "SP500": {"ticker": "^GSPC", "name": "S&P 500", "prefix": "$"},
    "NASDAQ_100": {"ticker": "^NDX", "name": "NASDAQ 100", "prefix": "$"},
    "EMERGING_MKTS": {"ticker": "EEM", "name": "EMERGING MKTS", "prefix": "$"},
    "GOLD": {"ticker": "GC=F", "name": "GOLD (10g)", "prefix": "$"},
    "CRUDE_OIL": {"ticker": "BZ=F", "name": "BRENT CRUDE", "prefix": "$", "suffix": "/bbl"},
    "US_TREASURY_10Y": {"ticker": "^TNX", "name": "US 10Y YIELD", "suffix": "%"},
    "BITCOIN": {"ticker": "BTC-USD", "name": "BITCOIN", "prefix": "$"},
    "USD/INR": {"ticker": "INR=X", "name": "USD/INR", "prefix": "₹"},
}

# Fallback baseline quotes if offline or rate limited
FALLBACK_TICKERS: List[Dict[str, Any]] = [
    {"sym": "NIFTY 50", "price": "₹24,850.25", "chg": "+0.68%", "dir": "up", "raw_price": 24850.25, "raw_chg": 0.68},
    {"sym": "S&P 500", "price": "$5,815.10", "chg": "+0.42%", "dir": "up", "raw_price": 5815.10, "raw_chg": 0.42},
    {"sym": "NASDAQ 100", "price": "$18,340.50", "chg": "+0.85%", "dir": "up", "raw_price": 18340.50, "raw_chg": 0.85},
    {"sym": "EMERGING MKTS", "price": "$44.30", "chg": "-0.35%", "dir": "down", "raw_price": 44.30, "raw_chg": -0.35},
    {"sym": "GOLD (10g)", "price": "₹76,420", "chg": "+1.15%", "dir": "up", "raw_price": 76420.0, "raw_chg": 1.15},
    {"sym": "BRENT CRUDE", "price": "$74.80/bbl", "chg": "-1.40%", "dir": "down", "raw_price": 74.80, "raw_chg": -1.40},
    {"sym": "US 10Y YIELD", "price": "4.08%", "chg": "+0.03%", "dir": "up", "raw_price": 4.08, "raw_chg": 0.03},
    {"sym": "BITCOIN", "price": "$65,420", "chg": "+2.45%", "dir": "up", "raw_price": 65420.0, "raw_chg": 2.45},
    {"sym": "USD/INR", "price": "₹84.05", "chg": "+0.05%", "dir": "up", "raw_price": 84.05, "raw_chg": 0.05},
]

# In-memory cache: 60-second TTL
_CACHE_DATA: List[Dict[str, Any]] = []
_CACHE_TIMESTAMP: float = 0.0
CACHE_TTL_SECONDS: float = 60.0


def _fetch_single_quote(ticker: str, timeout: float = 2.5) -> Dict[str, float]:
    """Fetch last price and change % for a single ticker from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode())
        meta = payload["chart"]["result"][0]["meta"]
        price = float(meta["regularMarketPrice"])
        prev = float(meta.get("chartPreviousClose", meta.get("previousClose", price)))
        chg = ((price - prev) / prev * 100.0) if prev > 0 else 0.0
        return {"price": price, "chg": chg}


def get_live_market_data(force_refresh: bool = False) -> Dict[str, Any]:
    """Get live market ticker data with caching and fallback protection."""
    global _CACHE_DATA, _CACHE_TIMESTAMP
    now = time.time()

    if not force_refresh and _CACHE_DATA and (now - _CACHE_TIMESTAMP) < CACHE_TTL_SECONDS:
        return {
            "source": "cache",
            "cached_at": _CACHE_TIMESTAMP,
            "ttl_remaining": int(CACHE_TTL_SECONDS - (now - _CACHE_TIMESTAMP)),
            "tickers": _CACHE_DATA,
        }

    tickers = []
    fetched_count = 0

    for aid, conf in YFINANCE_SYMBOLS.items():
        sym_name = conf["name"]
        prefix = conf.get("prefix", "")
        suffix = conf.get("suffix", "")
        try:
            quote = _fetch_single_quote(conf["ticker"])
            raw_p = quote["price"]
            raw_c = quote["chg"]
            price_str = f"{prefix}{raw_p:,.2f}{suffix}" if raw_p >= 1 else f"{prefix}{raw_p:.4f}{suffix}"
            chg_str = f"{raw_c:+.2f}%"
            direction = "up" if raw_c >= 0 else "down"

            tickers.append({
                "sym": sym_name,
                "price": price_str,
                "chg": chg_str,
                "dir": direction,
                "raw_price": round(raw_p, 2),
                "raw_chg": round(raw_c, 2),
            })
            fetched_count += 1
        except Exception:
            # Fall back to matching default entry if single symbol fails
            fallback = next((t for t in FALLBACK_TICKERS if t["sym"] == sym_name), None)
            if fallback:
                tickers.append(fallback)

    if fetched_count > 0:
        _CACHE_DATA = tickers
        _CACHE_TIMESTAMP = now
        source = "live"
    else:
        # Complete network failure fallback
        tickers = FALLBACK_TICKERS
        source = "fallback"

    return {
        "source": source,
        "cached_at": _CACHE_TIMESTAMP or now,
        "ttl_remaining": int(CACHE_TTL_SECONDS),
        "tickers": tickers,
    }
