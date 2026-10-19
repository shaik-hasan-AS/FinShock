"""Macroeconomic stress scenarios and market shocks across expanded multi-asset universe."""

from typing import Dict, Any

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "covid_2020_flash_crash": {
        "id": "covid_2020_flash_crash",
        "name": "Global Pandemic Flash Crash (March 2020)",
        "description": "Systemic liquidity freeze across global equities & commodities; flight to safe-haven sovereign bonds.",
        "shocks": {
            "NIFTY_50": -0.29,
            "SP500": -0.32,
            "NASDAQ_100": -0.27,
            "EMERGING_MKTS": -0.34,
            "GOLD": 0.08,
            "CRUDE_OIL": -0.55,
            "GSEC_10Y": 0.04,
            "US_TREASURY_10Y": 0.08,
            "REIT_IN": -0.22,
            "BITCOIN": -0.38,
            "LIQUID_CASH": 0.00,
        },
    },
    "stagflation_surge": {
        "id": "stagflation_surge",
        "name": "1970s Style Stagflation Surge",
        "description": "Oil & commodity shock with runaway inflation; central banks aggressively hike, punishing equities and fixed income.",
        "shocks": {
            "NIFTY_50": -0.16,
            "SP500": -0.22,
            "NASDAQ_100": -0.30,
            "EMERGING_MKTS": -0.18,
            "GOLD": 0.28,
            "CRUDE_OIL": 0.45,
            "GSEC_10Y": -0.09,
            "US_TREASURY_10Y": -0.12,
            "REIT_IN": -0.14,
            "BITCOIN": -0.25,
            "LIQUID_CASH": 0.00,
        },
    },
    "tech_valuation_reset": {
        "id": "tech_valuation_reset",
        "name": "Tech & AI Multiples Compression",
        "description": "Multiples de-rate in speculative high-duration assets; rotation into defensive domestic yields & gold.",
        "shocks": {
            "NIFTY_50": -0.08,
            "SP500": -0.15,
            "NASDAQ_100": -0.32,
            "EMERGING_MKTS": -0.10,
            "GOLD": 0.09,
            "CRUDE_OIL": -0.05,
            "GSEC_10Y": 0.03,
            "US_TREASURY_10Y": 0.05,
            "REIT_IN": 0.02,
            "BITCOIN": -0.42,
            "LIQUID_CASH": 0.00,
        },
    },
    "geopolitical_oil_shock": {
        "id": "geopolitical_oil_shock",
        "name": "Hormuz/Suez Geopolitical Blockade",
        "description": "Critical maritime chokepoint shut; energy spikes, importing emerging markets take severe currency and inflation hits.",
        "shocks": {
            "NIFTY_50": -0.21,
            "SP500": -0.14,
            "NASDAQ_100": -0.12,
            "EMERGING_MKTS": -0.24,
            "GOLD": 0.24,
            "CRUDE_OIL": 0.65,
            "GSEC_10Y": -0.06,
            "US_TREASURY_10Y": 0.02,
            "REIT_IN": -0.10,
            "BITCOIN": 0.05,
            "LIQUID_CASH": 0.00,
        },
    },
    "soft_landing_expansion": {
        "id": "soft_landing_expansion",
        "name": "Global Disinflation & Rate Easing (Upside)",
        "description": "Benign disinflation, synchronized central bank cuts, robust corporate capex cycle.",
        "shocks": {
            "NIFTY_50": 0.16,
            "SP500": 0.14,
            "NASDAQ_100": 0.22,
            "EMERGING_MKTS": 0.18,
            "GOLD": -0.03,
            "CRUDE_OIL": 0.08,
            "GSEC_10Y": 0.06,
            "US_TREASURY_10Y": 0.07,
            "REIT_IN": 0.12,
            "BITCOIN": 0.35,
            "LIQUID_CASH": 0.00,
        },
    },
}


def get_all_scenarios() -> Dict[str, Dict[str, Any]]:
    """Return all active scenarios, including standard macro and custom user scenarios."""
    return SCENARIOS


def add_custom_scenario(data: Dict[str, Any]) -> Dict[str, Any]:
    """Register a bespoke user-defined macro shock scenario."""
    name = (data.get("name") or "Custom Macro Shock").strip()
    raw_id = data.get("id") or ("custom_" + name.lower().replace(" ", "_").replace("-", "_")[:24])
    # Sanitize id
    sc_id = "".join(c for c in raw_id if c.isalnum() or c == "_") or "custom_scenario"
    description = (data.get("description") or f"Custom stress test scenario: {name}").strip()
    
    # Clean shocks
    raw_shocks = data.get("shocks", {})
    clean_shocks: Dict[str, float] = {}
    for aid, val in raw_shocks.items():
        try:
            clean_shocks[aid] = float(val)
        except (ValueError, TypeError):
            clean_shocks[aid] = 0.0

    scenario = {
        "id": sc_id,
        "name": name,
        "description": description,
        "shocks": clean_shocks,
        "is_custom": True,
    }
    SCENARIOS[sc_id] = scenario
    return scenario

