"""Unified API Handler for FinShock Quant.

Supports:
1. AWS Lambda invocation via API Gateway proxy (`lambda_handler`)
2. Local development server execution via standard library `http.server`
"""

import json
import os
import sys
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Tuple, Optional, Any, Dict

# Add root directory to sys.path so backend imports work everywhere
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.core.assets import (
    DEFAULT_ASSETS,
    ASSET_ORDER,
    CORRELATION_MATRIX,
    DEFAULT_CAPITAL,
    RISK_FREE_RATE,
)
from backend.core.scenarios import SCENARIOS
from backend.core.quant import (
    normalize_weights,
    calculate_portfolio_metrics,
    apply_market_shock,
    run_monte_carlo_simulation,
    calculate_risk_decomposition,
    generate_efficient_frontier,
)
from backend.services.storage import (
    get_aws_status,
    save_experiment,
    list_experiments,
)
from backend.services.aws_services import (
    get_all_aws_services_status,
    publish_risk_breach_alert,
    export_report_to_s3,
    get_risk_free_rate_from_ssm,
    log_cloudwatch_metric,
)
from backend.services.tearsheet import generate_executive_tearsheet

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Content-Type": "application/json",
}


def route_request(method: str, path: str, body: Optional[dict] = None) -> Tuple[int, dict]:
    """Route HTTP request to quantitative/service functions."""
    if method == "OPTIONS":
        return 200, {}

    if method == "GET":
        if path == "/api/health":
            return 200, {"status": "healthy", "service": "FinShock Quant Engine"}
            
        elif path == "/api/aws-status":
            return 200, get_aws_status()
            
        elif path == "/api/aws-services":
            return 200, get_all_aws_services_status()
            
        elif path == "/api/assets":
            rf_rate = get_risk_free_rate_from_ssm(RISK_FREE_RATE)
            return 200, {
                "assets": DEFAULT_ASSETS,
                "asset_order": ASSET_ORDER,
                "correlation_matrix": CORRELATION_MATRIX,
                "default_capital": DEFAULT_CAPITAL,
                "risk_free_rate": rf_rate,
            }
            
        elif path == "/api/scenarios":
            return 200, {"scenarios": SCENARIOS}
            
        elif path == "/api/experiments":
            experiments = list_experiments()
            return 200, {"experiments": experiments, "count": len(experiments)}

    elif method == "POST":
        payload = body or {}
        
        if path == "/api/analyze":
            capital = float(payload.get("capital", DEFAULT_CAPITAL))
            weights = payload.get("weights", {aid: DEFAULT_ASSETS[aid]["default_weight"] for aid in ASSET_ORDER})
            rf_rate = get_risk_free_rate_from_ssm(RISK_FREE_RATE)
            metrics = calculate_portfolio_metrics(
                weights=weights,
                assets=DEFAULT_ASSETS,
                asset_order=ASSET_ORDER,
                correlation_matrix=CORRELATION_MATRIX,
                capital=capital,
                risk_free_rate=rf_rate,
            )
            return 200, metrics
            
        elif path == "/api/shock":
            capital = float(payload.get("capital", DEFAULT_CAPITAL))
            weights = payload.get("weights", {aid: DEFAULT_ASSETS[aid]["default_weight"] for aid in ASSET_ORDER})
            scenario_id = payload.get("scenario_id")
            
            if scenario_id and scenario_id in SCENARIOS:
                shock_rates = SCENARIOS[scenario_id]["shocks"]
            else:
                shock_rates = payload.get("custom_shocks", {})
                
            shock_result = apply_market_shock(
                capital=capital,
                weights=weights,
                assets=DEFAULT_ASSETS,
                asset_order=ASSET_ORDER,
                shock_rates=shock_rates,
            )
            # Emit metric to CloudWatch
            log_cloudwatch_metric("PortfolioStressLossPct", abs(shock_result["pnl_percent"]))
            return 200, shock_result
            
        elif path == "/api/simulate":
            capital = float(payload.get("capital", DEFAULT_CAPITAL))
            weights = payload.get("weights", {aid: DEFAULT_ASSETS[aid]["default_weight"] for aid in ASSET_ORDER})
            num_sims = int(payload.get("num_simulations", 1000))
            horizon = int(payload.get("time_horizon_days", 252))
            
            sim_result = run_monte_carlo_simulation(
                capital=capital,
                weights=weights,
                assets=DEFAULT_ASSETS,
                asset_order=ASSET_ORDER,
                correlation_matrix=CORRELATION_MATRIX,
                num_simulations=num_sims,
                time_horizon_days=horizon,
            )
            return 200, sim_result
            
        elif path == "/api/experiments":
            saved = save_experiment(payload)
            return 201, saved

        elif path == "/api/send-alert":
            title = payload.get("title", "Portfolio Risk Breach")
            pnl_pct = float(payload.get("pnl_percent", 0.0))
            var_pct = float(payload.get("var_95_percent", 0.0))
            alert_res = publish_risk_breach_alert(title, pnl_pct, var_pct)
            return 200, alert_res

        elif path == "/api/export-report":
            report_name = payload.get("title", "Stress_Test_Report")
            export_res = export_report_to_s3(report_name, payload)
            return 200, export_res

        elif path == "/api/risk-decomposition":
            capital = float(payload.get("capital", DEFAULT_CAPITAL))
            weights = payload.get("weights", {aid: DEFAULT_ASSETS[aid]["default_weight"] for aid in ASSET_ORDER})
            decomp = calculate_risk_decomposition(
                weights=weights,
                assets=DEFAULT_ASSETS,
                asset_order=ASSET_ORDER,
                correlation_matrix=CORRELATION_MATRIX,
                capital=capital
            )
            return 200, decomp

        elif path == "/api/efficient-frontier":
            weights = payload.get("weights", {aid: DEFAULT_ASSETS[aid]["default_weight"] for aid in ASSET_ORDER})
            rf_rate = get_risk_free_rate_from_ssm(RISK_FREE_RATE)
            frontier = generate_efficient_frontier(
                assets=DEFAULT_ASSETS,
                asset_order=ASSET_ORDER,
                correlation_matrix=CORRELATION_MATRIX,
                current_weights=weights,
                risk_free_rate=rf_rate
            )
            return 200, frontier

        elif path == "/api/generate-tearsheet":
            title = payload.get("title", "Executive Risk Audit")
            capital = float(payload.get("capital", DEFAULT_CAPITAL))
            metrics = payload.get("metrics", {})
            risk_decomp = payload.get("risk_decomp", {})
            shock_result = payload.get("shock_result", {})
            notes = payload.get("notes", "")
            tearsheet_res = generate_executive_tearsheet(
                title=title,
                capital=capital,
                metrics=metrics,
                risk_decomp=risk_decomp,
                shock_result=shock_result,
                notes=notes
            )
            return 200, tearsheet_res

    return 404, {"error": f"Endpoint not found: {method} {path}"}


def lambda_handler(event: dict, context: Any) -> dict:
    """AWS Lambda entry point for API Gateway & Amazon EventBridge."""
    # 1. Check for Amazon EventBridge Scheduled Event (Nightly Stress Check)
    if event.get("source") == "aws.events" or event.get("detail-type") == "Scheduled Event":
        # Automated baseline test execution
        metrics = calculate_portfolio_metrics(
            weights={aid: DEFAULT_ASSETS[aid]["default_weight"] for aid in ASSET_ORDER},
            assets=DEFAULT_ASSETS,
            asset_order=ASSET_ORDER,
            correlation_matrix=CORRELATION_MATRIX,
            capital=DEFAULT_CAPITAL,
            risk_free_rate=RISK_FREE_RATE
        )
        log_cloudwatch_metric("AutomatedNightlyCheck", 1.0, "Count")
        return {"status": "EventBridge Scheduled Stress Check Completed", "metrics": metrics}

    # 2. Standard API Gateway HTTP / REST Request
    method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("path") or event.get("rawPath", "/api/health")
    
    body = None
    raw_body = event.get("body")
    if raw_body:
        try:
            body = json.loads(raw_body)
        except Exception:
            body = {}
            
    status_code, response_data = route_request(method, path, body)
    
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(response_data),
    }


class LocalAPIRequestHandler(SimpleHTTPRequestHandler):
    """Local HTTP Server handler for development."""

    def __init__(self, *args, **kwargs):
        # Serve frontend files if directory exists
        frontend_dist = os.path.join(BASE_DIR, "frontend", "dist")
        frontend_static = os.path.join(BASE_DIR, "frontend")
        directory = frontend_dist if os.path.exists(frontend_dist) else frontend_static
        super().__init__(*args, directory=directory, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            status, data = route_request("GET", parsed.path)
            self._send_json(status, data)
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        body = {}
        if content_len > 0:
            raw = self.rfile.read(content_len).decode("utf-8")
            try:
                body = json.loads(raw)
            except Exception:
                body = {}
        status, data = route_request("POST", parsed.path, body)
        self._send_json(status, data)

    def _send_json(self, status: int, data: dict):
        self.send_response(status)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), LocalAPIRequestHandler)
    print(f"FinShock Quant Engine running at http://localhost:{port}")
    print("Endpoints available: /api/assets, /api/scenarios, /api/analyze, /api/shock, /api/simulate, /api/aws-status")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping FinShock server.")
        server.server_close()
