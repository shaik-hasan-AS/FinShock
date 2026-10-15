"""Tests for the FinShock API routing and AWS Lambda handler."""

import json
from backend.handler import route_request, lambda_handler


def test_api_health():
    status, data = route_request("GET", "/api/health")
    assert status == 200
    assert data["status"] == "healthy"


def test_api_assets_and_scenarios():
    status_a, assets_data = route_request("GET", "/api/assets")
    assert status_a == 200
    assert "NIFTY_50" in assets_data["assets"]
    assert len(assets_data["correlation_matrix"]) == 11
    assert len(assets_data["assets"]) == 11

    status_s, scenarios_data = route_request("GET", "/api/scenarios")
    assert status_s == 200
    assert "covid_2020_flash_crash" in scenarios_data["scenarios"]


def test_api_analyze():
    payload = {
        "capital": 1000000,
        "weights": {"NIFTY_50": 0.4, "SP500": 0.2, "GOLD": 0.15, "GSEC_10Y": 0.15, "LIQUID_CASH": 0.1}
    }
    status, data = route_request("POST", "/api/analyze", payload)
    assert status == 200
    assert data["capital"] == 1000000
    assert "var_95_amount" in data
    assert "cvar_95_amount" in data


def test_api_shock_and_simulate():
    shock_payload = {
        "capital": 1000000,
        "scenario_id": "stagflation_surge"
    }
    status_sh, shock_data = route_request("POST", "/api/shock", shock_payload)
    assert status_sh == 200
    assert "stressed_capital" in shock_data

    sim_payload = {
        "capital": 1000000,
        "num_simulations": 100,
        "time_horizon_days": 60
    }
    status_sim, sim_data = route_request("POST", "/api/simulate", sim_payload)
    assert status_sim == 200
    assert "fan_chart" in sim_data
    assert len(sim_data["fan_chart"]["p50_median"]) > 0


def test_lambda_handler_api_gateway():
    event = {
        "httpMethod": "GET",
        "path": "/api/aws-status",
        "body": None,
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "mode" in body
    assert body["mode"] in ("local_fallback", "aws_cloud")


def test_api_aws_services():
    status, data = route_request("GET", "/api/aws-services")
    assert status == 200
    assert data["total_services_count"] == 10
    assert data["free_tier_compliant"] is True
    service_names = [s["name"] for s in data["services"]]
    assert "AWS Lambda" in service_names
    assert "Amazon SNS" in service_names
    assert "Amazon SQS" in service_names
    assert "Amazon EventBridge" in service_names
    assert "AWS Systems Manager (SSM)" in service_names


def test_api_alert_and_export():
    status_al, alert_data = route_request("POST", "/api/send-alert", {
        "title": "Severe Crash Test",
        "pnl_percent": -18.5,
        "var_95_percent": 16.2
    })
    assert status_al == 200
    assert "sent_to" in alert_data

    status_ex, exp_data = route_request("POST", "/api/export-report", {
        "title": "Q3_Stress_Report",
        "capital": 1000000,
        "pnl_percent": -12.0
    })
    assert status_ex == 200
    assert "exported_to" in exp_data


def test_lambda_eventbridge_scheduled_check():
    scheduled_event = {
        "source": "aws.events",
        "detail-type": "Scheduled Event"
    }
    resp = lambda_handler(scheduled_event, None)
    assert "EventBridge Scheduled Stress Check Completed" in resp["status"]
    assert "metrics" in resp


def test_api_risk_decomposition_and_frontier():
    payload = {
        "capital": 1000000,
        "weights": {"NIFTY_50": 0.4, "SP500": 0.2, "GOLD": 0.2, "GSEC_10Y": 0.2}
    }
    status_rd, rd_data = route_request("POST", "/api/risk-decomposition", payload)
    assert status_rd == 200
    assert "assets_risk_decomposition" in rd_data
    assert len(rd_data["assets_risk_decomposition"]) == 11
    assert "portfolio_volatility" in rd_data

    status_ef, ef_data = route_request("POST", "/api/efficient-frontier", payload)
    assert status_ef == 200
    assert "frontier_curve" in ef_data
    assert "max_sharpe_portfolio" in ef_data
    assert "min_variance_portfolio" in ef_data
    assert ef_data["max_sharpe_portfolio"]["sharpe_ratio"] >= ef_data["min_variance_portfolio"]["sharpe_ratio"]


def test_api_generate_tearsheet():
    payload = {
        "title": "Institutional Stress Test Audit",
        "capital": 1000000,
        "metrics": {"expected_return": 0.12, "volatility": 0.14, "sharpe_ratio": 1.1, "var_95_percent": 15.0, "cvar_95_percent": 21.0},
        "notes": "Verified portfolio meets target risk thresholds."
    }
    status_ts, ts_data = route_request("POST", "/api/generate-tearsheet", payload)
    assert status_ts == 200
    assert "report_id" in ts_data
    assert "html_content" in ts_data
    assert len(ts_data["html_content"]) > 100

