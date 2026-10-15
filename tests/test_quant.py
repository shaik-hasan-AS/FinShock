"""Test suite for FinShock quantitative calculations."""

import pytest
from backend.core.assets import DEFAULT_ASSETS, ASSET_ORDER, CORRELATION_MATRIX
from backend.core.scenarios import SCENARIOS
from backend.core.quant import (
    normalize_weights,
    calculate_portfolio_metrics,
    apply_market_shock,
    run_monte_carlo_simulation,
    calculate_risk_decomposition,
    generate_efficient_frontier,
)


def test_normalize_weights():
    # Regular weights
    w = {"NIFTY_50": 40, "SP500": 20, "GOLD": 15, "GSEC_10Y": 15, "LIQUID_CASH": 10}
    norm = normalize_weights(w, ASSET_ORDER)
    assert abs(sum(norm.values()) - 1.0) < 1e-6
    assert abs(norm["NIFTY_50"] - 0.40) < 1e-6

    # Zero total weights defaults to equal weight
    zero_w = {k: 0.0 for k in ASSET_ORDER}
    norm_zero = normalize_weights(zero_w, ASSET_ORDER)
    assert abs(sum(norm_zero.values()) - 1.0) < 1e-6
    assert abs(norm_zero["NIFTY_50"] - (1.0 / len(ASSET_ORDER))) < 1e-6


def test_calculate_portfolio_metrics():
    capital = 1_000_000.0  # ₹10 Lakhs
    weights = {aid: DEFAULT_ASSETS[aid]["default_weight"] for aid in ASSET_ORDER}
    metrics = calculate_portfolio_metrics(
        weights=weights,
        assets=DEFAULT_ASSETS,
        asset_order=ASSET_ORDER,
        correlation_matrix=CORRELATION_MATRIX,
        capital=capital,
        risk_free_rate=0.065,
    )

    # Sanity checks for ₹10 Lakh baseline
    assert metrics["capital"] == capital
    assert 0.05 < metrics["expected_return"] < 0.20
    assert 0.03 < metrics["volatility"] < 0.25
    assert metrics["var_95_amount"] > 0
    assert metrics["cvar_95_amount"] >= metrics["var_95_amount"]
    assert metrics["var_99_amount"] >= metrics["var_95_amount"]


def test_apply_market_shock_covid():
    capital = 1_000_000.0
    weights = {aid: DEFAULT_ASSETS[aid]["default_weight"] for aid in ASSET_ORDER}
    covid_shocks = SCENARIOS["covid_2020_flash_crash"]["shocks"]

    result = apply_market_shock(
        capital=capital,
        weights=weights,
        assets=DEFAULT_ASSETS,
        asset_order=ASSET_ORDER,
        shock_rates=covid_shocks,
    )

    # In COVID crash, high equity portfolio suffers substantial loss
    assert result["baseline_capital"] == capital
    assert result["stressed_capital"] < capital
    assert result["total_pnl"] < 0
    assert -30.0 < result["pnl_percent"] < -10.0
    assert len(result["asset_breakdown"]) == len(ASSET_ORDER)

    # Gold and GSec acted as hedges
    gold_item = next(x for x in result["asset_breakdown"] if x["asset_id"] == "GOLD")
    assert gold_item["pnl"] > 0


def test_monte_carlo_simulation():
    capital = 1_000_000.0
    weights = {aid: DEFAULT_ASSETS[aid]["default_weight"] for aid in ASSET_ORDER}

    mc = run_monte_carlo_simulation(
        capital=capital,
        weights=weights,
        assets=DEFAULT_ASSETS,
        asset_order=ASSET_ORDER,
        correlation_matrix=CORRELATION_MATRIX,
        num_simulations=500,
        time_horizon_days=252,
        num_steps=12,
        seed=101,
    )

    assert mc["num_simulations"] == 500
    assert len(mc["time_points_months"]) == 13
    assert len(mc["fan_chart"]["p5"]) == 13
    assert len(mc["fan_chart"]["p95"]) == 13

    # Check percentile order: p5 <= p25 <= p50 <= p75 <= p95 at the end
    p5_end = mc["fan_chart"]["p5"][-1]
    p50_end = mc["fan_chart"]["p50_median"][-1]
    p95_end = mc["fan_chart"]["p95"][-1]
    assert p5_end <= p50_end <= p95_end
    assert mc["summary"]["max_terminal_value"] >= mc["summary"]["min_terminal_value"]


def test_risk_decomposition():
    weights = {aid: DEFAULT_ASSETS[aid]["default_weight"] for aid in ASSET_ORDER}
    decomp = calculate_risk_decomposition(
        weights=weights,
        assets=DEFAULT_ASSETS,
        asset_order=ASSET_ORDER,
        correlation_matrix=CORRELATION_MATRIX,
        capital=1000000.0
    )
    assert len(decomp["assets_risk_decomposition"]) == len(ASSET_ORDER)
    total_pct_contrib = sum(item["pct_risk_contrib"] for item in decomp["assets_risk_decomposition"])
    # Sum of percentage contributions to risk must equal ~100%
    assert abs(total_pct_contrib - 100.0) < 0.5


def test_efficient_frontier():
    weights = {aid: DEFAULT_ASSETS[aid]["default_weight"] for aid in ASSET_ORDER}
    frontier = generate_efficient_frontier(
        assets=DEFAULT_ASSETS,
        asset_order=ASSET_ORDER,
        correlation_matrix=CORRELATION_MATRIX,
        current_weights=weights,
        risk_free_rate=0.065,
        num_samples=200
    )
    assert "current_portfolio" in frontier
    assert "min_variance_portfolio" in frontier
    assert "max_sharpe_portfolio" in frontier
    assert len(frontier["frontier_curve"]) > 5
    # Max Sharpe portfolio should have Sharpe >= Current Portfolio Sharpe
    assert frontier["max_sharpe_portfolio"]["sharpe_ratio"] >= frontier["current_portfolio"]["sharpe_ratio"] - 0.05
    # Min Variance portfolio should have Volatility <= Current Portfolio Volatility
    assert frontier["min_variance_portfolio"]["volatility"] <= frontier["current_portfolio"]["volatility"] + 0.5
