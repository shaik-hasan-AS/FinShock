# FinShock Quant — Quantitative Risk & Scenario Research Lab

A modular quantitative-finance research application for portfolio risk analysis, macroeconomic stress testing, and correlated Monte Carlo simulations. Built with a 100% Free-Tier **10-Service AWS Architecture**.

## ☁️ 10 AWS Services Topology (100% Free Tier, $0.00 Idle Cost)

1. **AWS Lambda**: Serverless Python quantitative calculation engine (VaR, CVaR, Cholesky Monte Carlo).
2. **Amazon API Gateway (HTTP API v2)**: Low-latency, cost-effective routing for `/api/*` endpoints.
3. **Amazon DynamoDB**: On-demand storage for saved portfolio configurations and stress-test runs (`finshock_experiments`).
4. **Amazon S3**: Object storage for quantitative JSON/CSV stress reports and historical datasets.
5. **Amazon SNS**: Risk Breach Alerts published when portfolio VaR or scenario drawdown exceeds conservative limits (>15%).
6. **Amazon SQS**: Asynchronous simulation queue decoupling heavy 2,000-path Monte Carlo runs.
7. **Amazon EventBridge**: Automated nightly cron (`cron(0 2 * * ? *)`) re-evaluating portfolios against market shocks.
8. **AWS Systems Manager (SSM) Parameter Store**: Dynamic configuration store for benchmark rates (`/finshock/config/risk_free_rate`).
9. **Amazon CloudWatch**: Execution logs, anomaly alarms, and custom quantitative metric tracking (`PortfolioStressLossPct`).
10. **AWS CloudFormation / SAM**: Complete Infrastructure as Code (IaC) packaging and reproducible deployment in [template.yaml](template.yaml).
*(+ **AWS X-Ray**: Distributed visual request tracing enabled across API Gateway and Lambda).*

```
FinShock/
├── backend/
│   ├── core/
│   │   ├── assets.py         # Curated asset universe & empirical correlation matrix
│   │   ├── scenarios.py      # Macroeconomic shock scenarios (COVID, Stagflation, Tech crash, etc.)
│   │   └── quant.py          # Covariance math, VaR/CVaR, and Cholesky Monte Carlo simulation
│   ├── services/
│   │   └── storage.py        # Storage adapter: Local JSON fallback ↔ AWS DynamoDB & S3
│   └── handler.py            # Unified runner: local HTTP dev server & AWS Lambda handler
├── frontend/
│   ├── index.html            # Research lab dashboard
│   ├── styles.css            # Dark-mode quantitative terminal design
│   └── app.js                # State management, API integration & HTML5 canvas chart
├── tests/
│   ├── test_quant.py         # Mathematical verification of risk metrics & simulations
│   └── test_api.py           # Endpoint & AWS Lambda handler unit tests
└── template.yaml             # AWS SAM / CloudFormation serverless deployment specification
```

## 🚀 Quickstart (Local Development)

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Run test suite
PYTHONPATH=. pytest -v

# 3. Start local development server
python3 backend/handler.py
```
Open **http://localhost:8000** in your browser.

## ☁️ Connecting AWS (When Ready)

The backend auto-detects AWS credentials. To connect DynamoDB and S3:

1. Add your AWS credentials to `.env` or export them:
   ```bash
   export AWS_ACCESS_KEY_ID="your_access_key"
   export AWS_SECRET_ACCESS_KEY="your_secret_key"
   export AWS_DEFAULT_REGION="ap-south-1" # (Mumbai) or your chosen region
   ```
2. The storage adapter will automatically transition from local JSON files to AWS DynamoDB (`finshock_experiments`) and S3 (`finshock-reports`) with **zero code modifications**.

3. To deploy directly to AWS Lambda + API Gateway:
   ```bash
   sam build
   sam deploy --guided
   ```
