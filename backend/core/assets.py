"""Expanded multi-asset universe, sector/class metadata, and empirical correlation structure."""

from typing import Dict, List, Any

# Institutional 11-asset multi-asset universe spanning Domestic & Global Equities, Tech, Fixed Income, Commodities, Crypto, and Real Estate
DEFAULT_ASSETS: Dict[str, Dict[str, Any]] = {
    "NIFTY_50": {
        "id": "NIFTY_50",
        "name": "NIFTY 50",
        "category": "Domestic Equities",
        "sector": "India Large-Cap",
        "expected_return": 0.125,
        "volatility": 0.155,
        "default_weight": 0.30,
        "color": "#38bdf8",
    },
    "SP500": {
        "id": "SP500",
        "name": "S&P 500",
        "category": "Global Equities",
        "sector": "US Large-Cap",
        "expected_return": 0.105,
        "volatility": 0.165,
        "default_weight": 0.15,
        "color": "#6366f1",
    },
    "NASDAQ_100": {
        "id": "NASDAQ_100",
        "name": "Nasdaq 100",
        "category": "Global Equities",
        "sector": "US Tech / AI",
        "expected_return": 0.145,
        "volatility": 0.220,
        "default_weight": 0.10,
        "color": "#a855f7",
    },
    "EMERGING_MKTS": {
        "id": "EMERGING_MKTS",
        "name": "Emerging Markets",
        "category": "Global Equities",
        "sector": "EM Asia/LATAM",
        "expected_return": 0.098,
        "volatility": 0.190,
        "default_weight": 0.05,
        "color": "#ec4899",
    },
    "GOLD": {
        "id": "GOLD",
        "name": "Physical Gold",
        "category": "Commodities",
        "sector": "Precious Metals",
        "expected_return": 0.085,
        "volatility": 0.140,
        "default_weight": 0.10,
        "color": "#f59e0b",
    },
    "CRUDE_OIL": {
        "id": "CRUDE_OIL",
        "name": "Brent Crude",
        "category": "Commodities",
        "sector": "Energy",
        "expected_return": 0.075,
        "volatility": 0.310,
        "default_weight": 0.00,
        "color": "#ea580c",
    },
    "GSEC_10Y": {
        "id": "GSEC_10Y",
        "name": "10Y Sovereign G-Sec",
        "category": "Fixed Income",
        "sector": "India Sovereign",
        "expected_return": 0.072,
        "volatility": 0.065,
        "default_weight": 0.15,
        "color": "#10b981",
    },
    "US_TREASURY_10Y": {
        "id": "US_TREASURY_10Y",
        "name": "10Y US Treasury",
        "category": "Fixed Income",
        "sector": "US Sovereign",
        "expected_return": 0.045,
        "volatility": 0.085,
        "default_weight": 0.05,
        "color": "#059669",
    },
    "REIT_IN": {
        "id": "REIT_IN",
        "name": "Indian Commercial REIT",
        "category": "Real Estate",
        "sector": "Commercial Property",
        "expected_return": 0.095,
        "volatility": 0.135,
        "default_weight": 0.05,
        "color": "#06b6d4",
    },
    "BITCOIN": {
        "id": "BITCOIN",
        "name": "Bitcoin (Digital Asset)",
        "category": "Alternative Assets",
        "sector": "Cryptocurrency",
        "expected_return": 0.220,
        "volatility": 0.580,
        "default_weight": 0.00,
        "color": "#eab308",
    },
    "LIQUID_CASH": {
        "id": "LIQUID_CASH",
        "name": "Liquid Fund / Overnight",
        "category": "Cash Equivalent",
        "sector": "Money Market",
        "expected_return": 0.065,
        "volatility": 0.015,
        "default_weight": 0.05,
        "color": "#64748b",
    },
}

ASSET_ORDER: List[str] = [
    "NIFTY_50",
    "SP500",
    "NASDAQ_100",
    "EMERGING_MKTS",
    "GOLD",
    "CRUDE_OIL",
    "GSEC_10Y",
    "US_TREASURY_10Y",
    "REIT_IN",
    "BITCOIN",
    "LIQUID_CASH",
]

# Empirical 11x11 Cross-Asset Correlation Matrix
CORRELATION_MATRIX: List[List[float]] = [
    # NIFTY   SP500  NASDAQ     EM    GOLD     OIL   GSEC  UST10Y   REIT    BTC   CASH
    [ 1.00,   0.52,   0.48,   0.65, -0.12,   0.22,  0.08,  -0.04,  0.42,  0.24,  0.00 ], # NIFTY_50
    [ 0.52,   1.00,   0.88,   0.72, -0.08,   0.28, -0.05,  -0.35,  0.55,  0.38,  0.00 ], # SP500
    [ 0.48,   0.88,   1.00,   0.68, -0.14,   0.20, -0.08,  -0.42,  0.48,  0.45,  0.00 ], # NASDAQ_100
    [ 0.65,   0.72,   0.68,   1.00,  0.02,   0.38,  0.02,  -0.18,  0.50,  0.32,  0.00 ], # EMERGING_MKTS
    [-0.12,  -0.08,  -0.14,   0.02,  1.00,   0.15,  0.20,   0.28,  0.05,  0.10,  0.00 ], # GOLD
    [ 0.22,   0.28,   0.20,   0.38,  0.15,   1.00, -0.18,  -0.12,  0.15,  0.12,  0.00 ], # CRUDE_OIL
    [ 0.08,  -0.05,  -0.08,   0.02,  0.20,  -0.18,  1.00,   0.45,  0.25, -0.05,  0.02 ], # GSEC_10Y
    [-0.04,  -0.35,  -0.42,  -0.18,  0.28,  -0.12,  0.45,   1.00,  0.12, -0.18,  0.00 ], # US_TREASURY_10Y
    [ 0.42,   0.55,   0.48,   0.50,  0.05,   0.15,  0.25,   0.12,  1.00,  0.18,  0.00 ], # REIT_IN
    [ 0.24,   0.38,   0.45,   0.32,  0.10,   0.12, -0.05,  -0.18,  0.18,  1.00,  0.00 ], # BITCOIN
    [ 0.00,   0.00,   0.00,   0.00,  0.00,   0.00,  0.02,   0.00,  0.00,  0.00,  1.00 ], # LIQUID_CASH
]

DEFAULT_CAPITAL: float = 1_000_000.0  # ₹10 Lakhs standard portfolio baseline
RISK_FREE_RATE: float = 0.065          # 6.5% Benchmark Rate
