"""Quantitative analysis engine for FinShock Quant.

Includes:
- Portfolio return and volatility calculations using covariance matrix
- Parametric and empirical Value at Risk (VaR) and Conditional VaR (CVaR)
- Scenario stress testing and instantaneous market shocks
- Correlated Monte Carlo simulation using Cholesky decomposition
"""

import math
import random
from typing import Dict, List, Tuple, Any

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def normalize_weights(weights: Dict[str, float], asset_ids: List[str]) -> Dict[str, float]:
    """Ensure weights are non-negative and sum to 1.0."""
    total = sum(max(0.0, float(weights.get(aid, 0.0))) for aid in asset_ids)
    if total <= 0.0:
        equal_weight = 1.0 / len(asset_ids)
        return {aid: equal_weight for aid in asset_ids}
    return {aid: max(0.0, float(weights.get(aid, 0.0))) / total for aid in asset_ids}


def calculate_covariance_matrix(
    asset_ids: List[str],
    assets: Dict[str, Dict[str, Any]],
    correlation_matrix: List[List[float]]
) -> List[List[float]]:
    """Compute covariance matrix: Cov(i, j) = Corr(i, j) * Vol(i) * Vol(j)."""
    n = len(asset_ids)
    cov = [[0.0] * n for _ in range(n)]
    vols = [assets[aid]["volatility"] for aid in asset_ids]
    for i in range(n):
        for j in range(n):
            cov[i][j] = correlation_matrix[i][j] * vols[i] * vols[j]
    return cov


def calculate_portfolio_metrics(
    weights: Dict[str, float],
    assets: Dict[str, Dict[str, Any]],
    asset_order: List[str],
    correlation_matrix: List[List[float]],
    capital: float,
    risk_free_rate: float = 0.065
) -> Dict[str, Any]:
    """Calculate portfolio expected return, volatility, Sharpe ratio, and parametric VaR/CVaR."""
    norm_w = normalize_weights(weights, asset_order)
    w_vec = [norm_w[aid] for aid in asset_order]
    
    # Portfolio expected annual return
    exp_return = sum(w * assets[aid]["expected_return"] for w, aid in zip(w_vec, asset_order))
    
    # Portfolio variance: w^T * Cov * w
    cov = calculate_covariance_matrix(asset_order, assets, correlation_matrix)
    variance = 0.0
    for i in range(len(asset_order)):
        for j in range(len(asset_order)):
            variance += w_vec[i] * w_vec[j] * cov[i][j]
            
    volatility = math.sqrt(max(0.0, variance))
    sharpe_ratio = (exp_return - risk_free_rate) / volatility if volatility > 1e-6 else 0.0
    
    # Parametric Value at Risk (1-year horizon)
    # Z_0.95 = 1.64485, Z_0.99 = 2.32635
    z_95 = 1.6448536269514722
    z_99 = 2.3263478740408408
    
    # VaR is reported as expected maximum monetary loss (positive number)
    var_95_pct = max(0.0, z_95 * volatility - exp_return)
    var_99_pct = max(0.0, z_99 * volatility - exp_return)
    
    # Standard normal density phi(z)
    phi_95 = math.exp(-0.5 * z_95 * z_95) / math.sqrt(2 * math.pi)
    phi_99 = math.exp(-0.5 * z_99 * z_99) / math.sqrt(2 * math.pi)
    
    # Parametric CVaR / Expected Shortfall
    cvar_95_pct = max(var_95_pct, (phi_95 / 0.05) * volatility - exp_return)
    cvar_99_pct = max(var_99_pct, (phi_99 / 0.01) * volatility - exp_return)
    
    return {
        "capital": capital,
        "weights": norm_w,
        "expected_return": round(exp_return, 4),
        "volatility": round(volatility, 4),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "var_95_percent": round(var_95_pct * 100, 2),
        "var_95_amount": round(capital * var_95_pct, 2),
        "var_99_percent": round(var_99_pct * 100, 2),
        "var_99_amount": round(capital * var_99_pct, 2),
        "cvar_95_percent": round(cvar_95_pct * 100, 2),
        "cvar_95_amount": round(capital * cvar_95_pct, 2),
        "cvar_99_percent": round(cvar_99_pct * 100, 2),
        "cvar_99_amount": round(capital * cvar_99_pct, 2),
    }


def apply_market_shock(
    capital: float,
    weights: Dict[str, float],
    assets: Dict[str, Dict[str, Any]],
    asset_order: List[str],
    shock_rates: Dict[str, float]
) -> Dict[str, Any]:
    """Calculate instantaneous impact of a market shock on portfolio value and asset breakdown."""
    norm_w = normalize_weights(weights, asset_order)
    
    breakdown = []
    total_stressed_value = 0.0
    
    for aid in asset_order:
        base_alloc = capital * norm_w[aid]
        shock = float(shock_rates.get(aid, 0.0))
        stressed_val = base_alloc * (1.0 + shock)
        pnl = stressed_val - base_alloc
        total_stressed_value += stressed_val
        
        breakdown.append({
            "asset_id": aid,
            "name": assets[aid]["name"],
            "category": assets[aid]["category"],
            "base_weight": round(norm_w[aid], 4),
            "baseline_value": round(base_alloc, 2),
            "shock_percent": round(shock * 100, 2),
            "stressed_value": round(stressed_val, 2),
            "pnl": round(pnl, 2),
            "color": assets[aid].get("color", "#64748b"),
        })
        
    total_pnl = total_stressed_value - capital
    pnl_percent = (total_pnl / capital) * 100.0 if capital > 0 else 0.0
    
    # Calculate post-shock weights
    for item in breakdown:
        item["post_shock_weight"] = round(item["stressed_value"] / total_stressed_value, 4) if total_stressed_value > 0 else 0.0

    return {
        "baseline_capital": round(capital, 2),
        "stressed_capital": round(total_stressed_value, 2),
        "total_pnl": round(total_pnl, 2),
        "pnl_percent": round(pnl_percent, 2),
        "asset_breakdown": breakdown,
    }


def _cholesky_decomposition(matrix: List[List[float]]) -> List[List[float]]:
    """Compute Lower Triangular Cholesky factor L such that L * L^T = Matrix."""
    n = len(matrix)
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            sum_val = sum(L[i][k] * L[j][k] for k in range(j))
            if i == j:
                diff = matrix[i][i] - sum_val
                L[i][j] = math.sqrt(max(0.0001, diff))
            else:
                L[i][j] = (matrix[i][j] - sum_val) / L[j][j] if L[j][j] > 1e-12 else 0.0
    return L


def run_monte_carlo_simulation(
    capital: float,
    weights: Dict[str, float],
    assets: Dict[str, Dict[str, Any]],
    asset_order: List[str],
    correlation_matrix: List[List[float]],
    num_simulations: int = 1000,
    time_horizon_days: int = 252,
    num_steps: int = 20,
    seed: int = 42
) -> Dict[str, Any]:
    """Run correlated geometric Brownian motion Monte Carlo simulation.
    
    Produces percentile fan curves (5th, 25th, 50th, 75th, 95th) and empirical risk stats.
    Bounded to maximum 3000 simulations to enforce AWS Lambda cost and memory guardrails.
    """
    sim_count = max(100, min(3000, num_simulations))
    norm_w = normalize_weights(weights, asset_order)
    w_vec = [norm_w[aid] for aid in asset_order]
    n_assets = len(asset_order)
    
    # Expected returns and volatilities
    mu_annual = [assets[aid]["expected_return"] for aid in asset_order]
    sigma_annual = [assets[aid]["volatility"] for aid in asset_order]
    
    dt = (time_horizon_days / 252.0) / num_steps
    time_points = [round((step / num_steps) * (time_horizon_days / 252.0) * 12, 1) for step in range(num_steps + 1)] # in months
    
    if HAS_NUMPY:
        np.random.seed(seed)
        corr_np = np.array(correlation_matrix, dtype=float)
        # Cholesky decomposition for correlation
        try:
            L = np.linalg.cholesky(corr_np)
        except np.linalg.LinAlgError:
            corr_np += np.eye(n_assets) * 1e-5
            L = np.linalg.cholesky(corr_np)
            
        mu_vec = np.array(mu_annual)
        sigma_vec = np.array(sigma_annual)
        drift = (mu_vec - 0.5 * sigma_vec**2) * dt
        vol_sqrt_dt = sigma_vec * math.sqrt(dt)
        
        # Array to hold all simulated portfolio paths: (sim_count, num_steps + 1)
        portfolio_paths = np.zeros((sim_count, num_steps + 1))
        portfolio_paths[:, 0] = capital
        
        # Initial asset prices normalized so portfolio value is capital
        initial_alloc = capital * np.array(w_vec)
        asset_paths = np.tile(initial_alloc, (sim_count, 1))  # (sim_count, n_assets)
        
        for step in range(1, num_steps + 1):
            uncorr_z = np.random.normal(0.0, 1.0, (sim_count, n_assets))
            corr_z = uncorr_z @ L.T
            growth_factors = np.exp(drift + vol_sqrt_dt * corr_z)
            asset_paths = asset_paths * growth_factors
            portfolio_paths[:, step] = np.sum(asset_paths, axis=1)
            
        # Calculate percentiles across simulations for each time step
        p5 = np.percentile(portfolio_paths, 5, axis=0).tolist()
        p25 = np.percentile(portfolio_paths, 25, axis=0).tolist()
        p50 = np.percentile(portfolio_paths, 50, axis=0).tolist()
        p75 = np.percentile(portfolio_paths, 75, axis=0).tolist()
        p95 = np.percentile(portfolio_paths, 95, axis=0).tolist()
        terminal_values = portfolio_paths[:, -1]
        
        # Empirical VaR and CVaR from terminal returns
        terminal_pnls = (terminal_values - capital) / capital
        empirical_var_95 = float(-np.percentile(terminal_pnls, 5))
        tail_95 = terminal_pnls[terminal_pnls <= np.percentile(terminal_pnls, 5)]
        empirical_cvar_95 = float(-np.mean(tail_95)) if len(tail_95) > 0 else empirical_var_95
        
        min_outcome = float(np.min(terminal_values))
        max_outcome = float(np.max(terminal_values))
        mean_outcome = float(np.mean(terminal_values))
        
        # Distribution histogram buckets (20 bins)
        counts, bin_edges = np.histogram(terminal_values, bins=15)
        histogram = [
            {"bin_start": round(float(bin_edges[i]), 0), "bin_end": round(float(bin_edges[i+1]), 0), "count": int(counts[i])}
            for i in range(len(counts))
        ]
        
    else:
        # Pure Python fallback using standard library
        random.seed(seed)
        L = _cholesky_decomposition(correlation_matrix)
        portfolio_paths = [[capital] * (num_steps + 1) for _ in range(sim_count)]
        terminal_values = []
        
        for sim in range(sim_count):
            allocs = [capital * w for w in w_vec]
            for step in range(1, num_steps + 1):
                uncorr_z = [random.gauss(0.0, 1.0) for _ in range(n_assets)]
                corr_z = [sum(L[i][j] * uncorr_z[j] for j in range(i + 1)) for i in range(n_assets)]
                for i in range(n_assets):
                    drift_i = (mu_annual[i] - 0.5 * sigma_annual[i]**2) * dt
                    growth = math.exp(drift_i + sigma_annual[i] * math.sqrt(dt) * corr_z[i])
                    allocs[i] *= growth
                portfolio_paths[sim][step] = sum(allocs)
            terminal_values.append(portfolio_paths[sim][-1])
            
        # Calculate percentiles step by step
        p5, p25, p50, p75, p95 = [], [], [], [], []
        for step in range(num_steps + 1):
            step_vals = sorted(portfolio_paths[s][step] for s in range(sim_count))
            p5.append(step_vals[int(sim_count * 0.05)])
            p25.append(step_vals[int(sim_count * 0.25)])
            p50.append(step_vals[int(sim_count * 0.50)])
            p75.append(step_vals[int(sim_count * 0.75)])
            p95.append(step_vals[int(sim_count * 0.95)])
            
        sorted_terminal = sorted(terminal_values)
        min_outcome = sorted_terminal[0]
        max_outcome = sorted_terminal[-1]
        mean_outcome = sum(sorted_terminal) / sim_count
        
        pnl_5th = (sorted_terminal[int(sim_count * 0.05)] - capital) / capital
        empirical_var_95 = -pnl_5th
        tail = [(v - capital) / capital for v in sorted_terminal[:int(sim_count * 0.05) + 1]]
        empirical_cvar_95 = -sum(tail) / len(tail) if tail else empirical_var_95
        histogram = []
        
    return {
        "num_simulations": sim_count,
        "time_horizon_days": time_horizon_days,
        "time_points_months": time_points,
        "fan_chart": {
            "p5": [round(x, 2) for x in p5],
            "p25": [round(x, 2) for x in p25],
            "p50_median": [round(x, 2) for x in p50],
            "p75": [round(x, 2) for x in p75],
            "p95": [round(x, 2) for x in p95],
        },
        "summary": {
            "min_terminal_value": round(min_outcome, 2),
            "median_terminal_value": round(p50[-1], 2),
            "mean_terminal_value": round(mean_outcome, 2),
            "max_terminal_value": round(max_outcome, 2),
            "empirical_var_95_percent": round(max(0.0, empirical_var_95 * 100), 2),
            "empirical_cvar_95_percent": round(max(0.0, empirical_cvar_95 * 100), 2),
            "prob_capital_preservation": round(sum(1 for v in terminal_values if v >= capital) / sim_count * 100, 1),
        },
        "histogram": histogram,
    }


def calculate_risk_decomposition(
    weights: Dict[str, float],
    assets: Dict[str, Dict[str, Any]],
    asset_order: List[str],
    correlation_matrix: List[List[float]],
    capital: float
) -> Dict[str, Any]:
    """Calculate Marginal Contribution to Risk (MCR) and Percentage Component VaR.
    
    Formula:
    Sigma = Covariance Matrix
    w = weight vector
    sigma_p = portfolio volatility = sqrt(w^T * Sigma * w)
    MCR_i = (Sigma * w)_i / sigma_p
    PCR_i = w_i * MCR_i / sigma_p = w_i * (Sigma * w)_i / sigma_p^2
    Sum(PCR_i) = 1.0 (100% of total risk explained)
    """
    norm_w = normalize_weights(weights, asset_order)
    w_vec = [norm_w[aid] for aid in asset_order]
    cov = calculate_covariance_matrix(asset_order, assets, correlation_matrix)
    n = len(asset_order)

    # Compute Sigma * w vector
    sigma_w = [sum(cov[i][j] * w_vec[j] for j in range(n)) for i in range(n)]
    var_p = sum(w_vec[i] * sigma_w[i] for i in range(n))
    vol_p = math.sqrt(max(1e-8, var_p))

    decomposition = []
    for i, aid in enumerate(asset_order):
        w_i = w_vec[i]
        mcr_i = sigma_w[i] / vol_p
        pcr_i = (w_i * sigma_w[i]) / var_p if var_p > 0 else 0.0
        risk_budget_ratio = (pcr_i / w_i) if w_i > 1e-4 else 0.0

        decomposition.append({
            "asset_id": aid,
            "name": assets[aid]["name"],
            "category": assets[aid]["category"],
            "weight_pct": round(w_i * 100, 2),
            "allocated_capital": round(capital * w_i, 2),
            "marginal_risk_contrib": round(mcr_i, 4),
            "pct_risk_contrib": round(pcr_i * 100, 2),
            "risk_budget_ratio": round(risk_budget_ratio, 2),
            "color": assets[aid].get("color", "#64748b")
        })

    return {
        "portfolio_volatility": round(vol_p * 100, 2),
        "total_capital": capital,
        "assets_risk_decomposition": decomposition
    }


def generate_efficient_frontier(
    assets: Dict[str, Dict[str, Any]],
    asset_order: List[str],
    correlation_matrix: List[List[float]],
    current_weights: Dict[str, float],
    risk_free_rate: float = 0.065,
    num_samples: int = 1500
) -> Dict[str, Any]:
    """Compute Markowitz Mean-Variance Efficient Frontier and identify:
    1. Minimum Variance Portfolio
    2. Maximum Sharpe Ratio (Tangency) Portfolio
    3. User's Current Portfolio relative position
    4. Upper Pareto-optimal frontier curve points
    """
    n = len(asset_order)
    mu = [assets[aid]["expected_return"] for aid in asset_order]
    cov = calculate_covariance_matrix(asset_order, assets, correlation_matrix)
    
    # Calculate user's current portfolio stats
    curr_norm = normalize_weights(current_weights, asset_order)
    curr_w = [curr_norm[aid] for aid in asset_order]
    curr_ret = sum(curr_w[i] * mu[i] for i in range(n))
    curr_sig_w = [sum(cov[i][j] * curr_w[j] for j in range(n)) for i in range(n)]
    curr_vol = math.sqrt(max(1e-8, sum(curr_w[i] * curr_sig_w[i] for i in range(n))))
    curr_sharpe = (curr_ret - risk_free_rate) / curr_vol if curr_vol > 0 else 0.0

    min_vol = float('inf')
    min_vol_weights = None
    min_vol_ret = 0.0

    max_sharpe = -float('inf')
    max_sharpe_weights = None
    max_sharpe_vol = 0.0
    max_sharpe_ret = 0.0

    # Seed candidates with single-asset corners, equal weight, and Dirichlet samples
    candidate_weights = []
    # Single asset vertices
    for i in range(n):
        v = [0.0] * n
        v[i] = 1.0
        candidate_weights.append(v)
    # Equal weight
    candidate_weights.append([1.0 / n] * n)

    random.seed(42)
    # Dirichlet/Uniform simplex sampling
    for _ in range(num_samples):
        # Generate random exponential variables
        raw = [random.expovariate(1.0) for _ in range(n)]
        s = sum(raw)
        candidate_weights.append([r / s for r in raw])

    eval_points = []
    for w in candidate_weights:
        r = sum(w[i] * mu[i] for i in range(n))
        sig_w = [sum(cov[i][j] * w[j] for j in range(n)) for i in range(n)]
        vol = math.sqrt(max(1e-8, sum(w[i] * sig_w[i] for i in range(n))))
        sh = (r - risk_free_rate) / vol if vol > 0 else 0.0

        eval_points.append((vol, r, sh, w))

        if vol < min_vol:
            min_vol = vol
            min_vol_weights = w
            min_vol_ret = r

        if sh > max_sharpe:
            max_sharpe = sh
            max_sharpe_weights = w
            max_sharpe_vol = vol
            max_sharpe_ret = r

    # Build Pareto-optimal efficient frontier curve (highest return for each vol bin)
    vol_bins = 24
    min_v_range = min_vol
    max_v_range = max(p[0] for p in eval_points)
    bin_size = (max_v_range - min_v_range) / vol_bins
    
    frontier_dict = {}
    for p in eval_points:
        vol, r, sh, _ = p
        b_idx = int((vol - min_v_range) / bin_size) if bin_size > 0 else 0
        if b_idx not in frontier_dict or r > frontier_dict[b_idx]["return"]:
            frontier_dict[b_idx] = {"volatility": round(vol * 100, 2), "return": round(r * 100, 2), "sharpe": round(sh, 2)}

    frontier_curve = sorted(frontier_dict.values(), key=lambda x: x["volatility"])

    # Ensure curve is monotonically increasing
    monotonic_frontier = []
    highest_ret = -float('inf')
    for pt in frontier_curve:
        if pt["return"] >= highest_ret:
            highest_ret = pt["return"]
            monotonic_frontier.append(pt)

    return {
        "current_portfolio": {
            "volatility": round(curr_vol * 100, 2),
            "return": round(curr_ret * 100, 2),
            "sharpe_ratio": round(curr_sharpe, 2),
            "weights": {aid: round(curr_norm[aid] * 100, 1) for aid in asset_order}
        },
        "min_variance_portfolio": {
            "volatility": round(min_vol * 100, 2),
            "return": round(min_vol_ret * 100, 2),
            "sharpe_ratio": round((min_vol_ret - risk_free_rate) / min_vol, 2),
            "weights": {asset_order[i]: round(min_vol_weights[i] * 100, 1) for i in range(n)}
        },
        "max_sharpe_portfolio": {
            "volatility": round(max_sharpe_vol * 100, 2),
            "return": round(max_sharpe_ret * 100, 2),
            "sharpe_ratio": round(max_sharpe, 2),
            "weights": {asset_order[i]: round(max_sharpe_weights[i] * 100, 1) for i in range(n)}
        },
        "frontier_curve": monotonic_frontier
    }
