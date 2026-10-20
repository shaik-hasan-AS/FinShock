# FinShock: Institutional Quantitative Risk & Macro Stress-Testing Platform
### Comprehensive System Architecture, Feature Guide & Presentation Deck
*Author: FinShock Engineering Team | Target: Executive, Technical & Academic Presentations*

---

## Table of Contents
1. [1-Minute Elevator Pitch](#1-1-minute-elevator-pitch)
2. [What Exactly Does FinShock Do? (Product Capabilities)](#2-what-exactly-does-finshock-do-product-capabilities)
   - 2.1 The Core Problem in Finance
   - 2.2 End-to-End User Journey & Workflow
   - 2.3 The 11-Asset Multi-Asset Universe
   - 2.4 The 6 Quantitative Analytics Engines
3. [All 10 AWS Services: Exact Role & Code Implementation](#3-all-10-aws-services-exact-role--code-implementation)
   - Deep Dive into Every Service
   - Cloud Architecture Diagram (ASCII)
   - AWS Free-Tier Safety Limits & Cost Guardrails
4. [Slide-by-Slide Presentation Deck (12 Slides with Speaker Notes)](#4-slide-by-slide-presentation-deck-12-slides-with-speaker-notes)
5. [Anticipated Q&A & Defensible Technical Answers](#5-anticipated-qa--defensible-technical-answers)

---

## 1. 1-Minute Elevator Pitch

> *"Most investors and treasuries only find out their portfolio is broken after a market crash occurs. Traditional risk systems assume financial returns behave like a normal bell curve—a naive mathematical flaw that cost institutions billions in 2008 and 2020.*
>
> ***FinShock** is an institutional-grade, cloud-native quantitative risk engine. It lets portfolio managers model multi-asset investments across 11 global asset classes, simulate historic crises like COVID-19 or 1970s stagflation, build custom crisis vectors, compute non-normal historical fat-tail VaR, run 5,000-path correlated Monte Carlo simulations, and find the mathematical Markowitz optimal allocation.*
>
> *Best of all, FinShock is engineered entirely on **10 AWS serverless services**—delivering hedge-fund analytics with zero fixed server costs and 100% Free-Tier compliance."*

---

## 2. What Exactly Does FinShock Do? (Product Capabilities)

### 2.1 The Core Problem in Finance
In standard portfolio management tools:
* **The "Gaussian Fallacy":** Risk engines assume returns follow a normal Gaussian distribution ($Z$-score). In reality, financial returns have **skewness** (asymmetric crashes) and **excess kurtosis** (fat tails).
* **Correlation Spikes in Panics:** During systemic crashes, diversification often vanishes as asset correlations jump toward 1.0.
* **Prohibitive Cost:** Institutional platforms (Bloomberg PORT, MSCI Barra, BlackRock Aladdin) cost $30,000+ per seat per year. Retail tools only show backward-looking past returns without forward-looking scenario testing.

### 2.2 End-to-End User Journey & Workflow
When a user opens FinShock at `http://localhost:8000`:
1. **Live Market Pulse Ticker:** An animated ribbon streams real-time prices and 1-day percentage movements for 9 global benchmark assets (NIFTY 50, S&P 500, Nasdaq 100, Gold, Brent Crude, US 10Y Yield, Bitcoin, USD/INR).
2. **Portfolio Allocation Sliders:** The user enters their capital (e.g., ₹10,00,000 / $100,000) and tunes percentage weights across 11 assets or selects institutional presets (*Balanced 60/40*, *All-Weather Defensive*, *Tech Growth & Crypto*, *Capital Preservation*).
3. **Instant Risk KPI Evaluation:** The system computes annual expected return, portfolio volatility, Sharpe ratio, and a side-by-side comparison of **Parametric VaR** vs. **Empirical Historical VaR**.
4. **Macro Crisis Stress Testing:** The user clicks any pre-calibrated scenario (e.g., *Global Pandemic Flash Crash March 2020*) to see instantaneous portfolio drawdown, asset-by-asset P&L, and post-shock rebalanced weights.
5. **Custom Crisis Builder:** The user can open the sandbox drawer, slide bespoke percentage shocks for any asset (e.g., Oil $+60\%$, Equities $-30\%$), give it a name (*"2026 AI Valuation Crash"*), click **"Save as Scenario"**, and stress-test immediately.
6. **Correlated Monte Carlo Fan Chart:** The user triggers a 1-year forward stochastic simulation to see outcome probabilities ($P_5, P_{25}, P_{50}, P_{75}, P_{95}$) and capital preservation odds.
7. **Markowitz Efficient Frontier:** The user generates the Pareto optimal risk-return curve and applies the **Tangency Portfolio (Max Sharpe)** or **Minimum Variance Portfolio** in one click.
8. **Institutional Export & Alerts:** The user exports a printable HTML Executive Risk Tearsheet saved to Amazon S3 or dispatches an instant SNS Risk Breach Alert.

---

### 2.3 The 11-Asset Multi-Asset Universe
FinShock supports an institutional 11-asset investment universe:

| Asset Ticker | Asset Name | Category | Macro Role in Portfolio |
|---|---|---|---|
| `NIFTY_50` | NIFTY 50 | Domestic Equities | India large-cap core equity growth |
| `SP500` | S&P 500 | Global Equities | Developed market baseline equity exposure |
| `NASDAQ_100` | Nasdaq 100 | Global Equities | High-beta technology, AI capex, and duration |
| `EMERGING_MKTS` | Emerging Markets (EEM) | Global Equities | High-growth EM Asia/LATAM consumer markets |
| `GOLD` | Physical Gold | Commodities | Safe-haven crisis buffer and currency debasement hedge |
| `CRUDE_OIL` | Brent Crude | Commodities | Inflation driver and geopolitical energy proxy |
| `GSEC_10Y` | 10Y Sovereign G-Sec | Fixed Income | Domestic risk-free sovereign yield benchmark |
| `US_TREASURY_10Y`| 10Y US Treasury | Fixed Income | Global sovereign benchmark & flight-to-safety asset |
| `REIT_IN` | Indian Commercial REIT | Real Estate | High-dividend real property yield & inflation hedge |
| `BITCOIN` | Bitcoin (Digital Asset) | Alternative Assets | Asymmetric upside, digital store-of-value alternative |
| `LIQUID_CASH` | Overnight / Liquid Fund | Cash Equivalent | Capital preservation and dry powder for rebalancing |

---

### 2.4 The 6 Quantitative Analytics Engines

#### Engine 1: Dual Value at Risk (Parametric vs. Empirical Historical)
* **Gaussian Parametric VaR (1-Year 95% & 99%):**
  $$\text{VaR}_{95} = 1.645 \cdot \sigma_p - \mu_p, \quad \text{VaR}_{99} = 2.326 \cdot \sigma_p - \mu_p$$
  Expected Shortfall (CVaR):
  $$\text{CVaR}_{95} = \left(\frac{\phi(1.645)}{0.05}\right) \cdot \sigma_p - \mu_p$$
* **Empirical Historical VaR (Quant Upgrade):**
  Evaluates portfolio weights against a curated **2008–2024 annual crisis return matrix** (Lehman 2008, Eurozone 2011, Taper Tantrum 2013, China Deval 2015, COVID 2020, Fed Hikes 2022).
  - Computes exact historical portfolio returns: $R_{p, t} = \sum_i w_i R_{i, t}$
  - Calculates non-parametric 5th percentile empirical loss.
  - Computes **Skewness** ($S$) and **Excess Kurtosis** ($K$), proving mathematically why Gaussian models underestimate crisis losses by $2\times$ to $5\times$.

#### Engine 2: Macro Scenario Stress Testing & Custom Builder
* **5 Calibrated Crisis Scenarios:**
  1. *Global Pandemic Flash Crash (March 2020):* $-29\%$ NIFTY, $-32\%$ S&P, $-55\%$ Crude, $+8\%$ Gold & Treasuries.
  2. *1970s Style Stagflation Surge:* $+45\%$ Crude, $+28\%$ Gold, $-16\%$ NIFTY, $-22\%$ S&P, $-12\%$ US Treasuries.
  3. *Tech Multiples Reset:* $-32\%$ Nasdaq, $-42\%$ Bitcoin, $+9\%$ Gold, $+5\%$ US Treasuries.
  4. *Hormuz/Suez Geopolitical Blockade:* $+65\%$ Crude, $+24\%$ Gold, $-24\%$ EMs, $-21\%$ NIFTY.
  5. *Global Disinflation Easing (Upside):* $+22\%$ Nasdaq, $+16\%$ NIFTY, $+35\%$ Bitcoin, $-3\%$ Gold.
* **Custom Scenario Builder:** Allows arbitrary $\pm 50\%$ shocks per asset with custom name, description, and dynamic persistence via `POST /api/scenarios`.

#### Engine 3: Correlated Monte Carlo Simulation (Cholesky Decomposition)
* Solves cross-asset dependencies using Cholesky Factorization ($L \cdot L^T = \Sigma_{\text{corr}}$).
* Simulates 500–5,000 geometric Brownian motion paths over 252 trading days:
  $$S_{i, t+\Delta t} = S_{i, t} \exp\left( (\mu_i - \frac{1}{2}\sigma_i^2)\Delta t + \sigma_i \sqrt{\Delta t} \, (L \cdot Z)_i \right)$$
* Generates percentile fan charts ($P_5, P_{25}, P_{50}, P_{75}, P_{95}$), terminal outcome histograms, and Probability of Capital Preservation.

#### Engine 4: Markowitz Modern Portfolio Theory (MPT) Frontier
* Formulates and solves quadratic covariance optimization:
  $$\min_w \frac{1}{2} w^T \Sigma w \quad \text{subject to} \quad \sum_{i=1}^n w_i = 1, \quad w_i \ge 0$$
* Plots the continuous Pareto frontier.
* Identifies the **Tangency Portfolio** ($\max \frac{\mu_p - R_f}{\sigma_p}$) and **Minimum Variance Portfolio**. Single-click button applies optimal weights directly.

#### Engine 5: Risk Decomposition (MCR & Component VaR)
* Calculates Marginal Contribution to Risk:
  $$\text{MCR}_i = \frac{(\Sigma w)_i}{\sigma_p}$$
* Calculates Percentage Contribution to Total Risk:
  $$\% \text{ Risk}_i = \frac{w_i \cdot \text{MCR}_i}{\sigma_p} \times 100$$
* Exposes hidden asset concentration (e.g., Tech and Crypto accounting for 70% of risk despite only 25% capital weight).

#### Engine 6: Zero-Dependency Real-Time Market Data
* Connects directly to public market endpoints using standard Python `urllib.request`.
* Zero third-party packages needed (no bloated yfinance dependency).
* Features 60-second in-memory caching with graceful fallbacks, sub-second API latency, and real-time live ticker tape updates.

---

## 3. All 10 AWS Services: Exact Role & Code Implementation

FinShock utilizes **10 distinct AWS services**, organized cleanly across Compute, Networking, Storage, Database, Messaging, Orchestration, Observability, and Governance:

```
                                [ CLIENT / BROWSER ]
                   HTML5 + Glassmorphism CSS + Vanilla JS Charts
                                         │
                        HTTPS API v2 Calls (/api/*)
                                         ▼
                     [ 1. AMAZON API GATEWAY (HTTP API v2) ]
                                         │
                              Proxy Lambda Event
                                         ▼
                             [ 2. AWS LAMBDA ]
                      Unified Quantitative Risk Engine
                ┌────────────────────────┼────────────────────────┐
                │                        │                        │
        Dynamic Parameters       Persist Experiment         Store Reports
                ▼                        ▼                        ▼
       [ 3. AWS SSM STORE ]    [ 4. AMAZON DYNAMODB ]      [ 5. AMAZON S3 ]
     (/finshock/config/rf)    (finshock_experiments)     (finshock-reports)
                │                        │                        │
                ▼                        ▼                        ▼
      [ 6. CLOUDWATCH ]          [ 7. AMAZON SNS ]        [ 8. AMAZON SQS ]
    (Custom Metrics/Logs)      (Risk Breach Alerts)     (Async Batch Queue)
                                         ▲
                                         │ Nightly Stress Cron
                               [ 9. EVENTBRIDGE ]
                               (cron(0 2 * * ? *))
                                         │
                                         ▼
                         [ 10. CLOUDFORMATION / SAM ]
                           (IaC Stack: template.yaml)
```

---

### Deep Dive into Every AWS Service

#### 1. AWS Lambda (Serverless Compute)
* **What it does:** Executes the quantitative risk engine without running dedicated EC2 servers.
* **Code Implementation:** Handled in `backend/handler.py` via `lambda_handler(event, context)`. Routes requests to `quant.py`, `scenarios.py`, and `market_data.py`.
* **Why Lambda:** Financial stress testing is spike-driven. Users run simulations intensely for a few minutes and then pause. Lambda automatically scales to zero when idle, saving 100% of idle server costs.
* **Free-Tier Limits:** **1,000,000 free requests/month** + 3.2 million seconds of compute time.

#### 2. Amazon API Gateway (HTTP API v2)
* **What it does:** Provides the high-performance HTTP entry point for all frontend requests (`/api/analyze`, `/api/shock`, `/api/simulate`, `/api/market-pulse`).
* **Code Implementation:** Defined in `template.yaml` as an `AWS::Serverless::HttpApi` with integrated CORS rules allowing browser fetch requests.
* **Why API Gateway v2:** HTTP API v2 offers 70% lower latency and 70% lower cost than traditional REST APIs, with native payload proxying into Lambda.
* **Free-Tier Limits:** **1,000,000 free API calls/month** for 12 months.

#### 3. Amazon DynamoDB (NoSQL Database)
* **What it does:** Stores saved stress-test experiments, custom scenario allocations, portfolio weights, and simulation results.
* **Code Implementation:** Implemented in `backend/services/storage.py` via boto3 client `dynamodb` with table name `finshock_experiments` (Partition Key: `id`, string UUID).
* **Why DynamoDB:** Single-digit millisecond latency, zero database maintenance, no connection pool exhaustion, and built-in TTL support.
* **Free-Tier Limits:** **25 GB of storage + 25 Read/Write Capacity Units (RCU/WCU) always free** (non-expiring).

#### 4. Amazon S3 (Object Storage)
* **What it does:** Stores generated HTML Executive Risk Tearsheets, stress test audit logs, and benchmark historical return datasets.
* **Code Implementation:** Handled in `backend/services/aws_services.py` (`export_report_to_s3`) and `backend/services/tearsheet.py`. Uploads reports to bucket `finshock-reports`.
* **Why S3:** Highly durable (99.999999999% durability), allows direct sharing of pre-signed URLs or downloadable tearsheets without overloading application memory.
* **Free-Tier Limits:** **5 GB standard storage + 20,000 GET requests + 2,000 PUT requests/month**.

#### 5. Amazon SNS (Simple Notification Service)
* **What it does:** Dispatches real-time **Risk Breach Alerts** via SMS or Email whenever a simulated macro shock causes portfolio drawdown or VaR to breach safe thresholds (e.g., loss $> 15\%$).
* **Code Implementation:** Implemented in `backend/services/aws_services.py` (`publish_risk_breach_alert`) publishing to topic `finshock-risk-alerts`.
* **Why SNS:** Immediate fan-out notification without needing to maintain complex email SMTP servers or webhook workers.
* **Free-Tier Limits:** **1,000,000 free SNS mobile/email publishes/month**.

#### 6. Amazon SQS (Simple Queue Service)
* **What it does:** Acts as an asynchronous buffer queue (`finshock-simulation-queue`) for heavy batch Monte Carlo simulations (e.g., 5,000+ paths across 10 portfolios).
* **Code Implementation:** Implemented in `backend/services/aws_services.py` (`enqueue_simulation_task`).
* **Why SQS:** Decouples long-running numerical calculations from interactive user HTTP requests, preventing API Gateway 29-second timeouts during heavy batch runs.
* **Free-Tier Limits:** **1,000,000 free SQS requests/month**.

#### 7. Amazon EventBridge (Cloud Watch Events / Cron)
* **What it does:** Triggers automated nightly re-evaluations of all saved portfolios at market close (02:00 UTC) to identify new risk threshold breaches.
* **Code Implementation:** Configured in `template.yaml` as a CloudWatch Event schedule: `cron(0 2 * * ? *)`.
* **Why EventBridge:** Eliminates the need for standing cron servers, Celery beat workers, or always-on Linux VM daemons.
* **Free-Tier Limits:** **14,000,000 free event invocations/month**.

#### 8. AWS Systems Manager (SSM) Parameter Store
* **What it does:** Centrally stores dynamic global risk configuration parameters—such as the benchmark sovereign risk-free rate (`/finshock/config/risk_free_rate = 0.065`).
* **Code Implementation:** Implemented in `backend/services/aws_services.py` (`get_risk_free_rate_from_ssm`).
* **Why SSM:** Allows risk officers to update macroeconomic parameters dynamically without redeploying code or restarting servers.
* **Free-Tier Limits:** **Standard SSM parameters are 100% free with unlimited storage**.

#### 9. Amazon CloudWatch (Observability & Custom Metrics)
* **What it does:** Monitors application latency, logs errors, and publishes custom financial metrics (e.g., `PortfolioStressLossPct`) under namespace `FinShock/Quant`.
* **Code Implementation:** Implemented in `backend/services/aws_services.py` (`log_cloudwatch_metric`) and `backend/handler.py`.
* **Why CloudWatch:** Provides centralized observability, anomaly detection, and automated alarms if calculations breach drawdown limits.
* **Free-Tier Limits:** **5 GB log ingestion + 10 custom metrics + 3 alarm configurations free**.

#### 10. AWS CloudFormation / SAM (Infrastructure as Code)
* **What it does:** Automates the deployment, provisioning, and teardown of the entire 10-service architecture through a single template.
* **Code Implementation:** Defined in `template.yaml` using the AWS Serverless Application Model (SAM). Deployable via `sam build && sam deploy`.
* **Why SAM:** Guarantees reproducibility, version-controlled cloud infrastructure, and zero manual point-and-click configuration in the AWS Console.
* **Free-Tier Limits:** **CloudFormation stack creation and resource management are 100% free**.

---

### AWS Free-Tier Guardrails & Safety Summary

| Service | Free-Tier Monthly Allowance | FinShock Typical Usage | Monthly Cost |
|---|---|---|---|
| **AWS Lambda** | 1,000,000 requests | ~2,500 requests | **$0.00** |
| **Amazon API Gateway** | 1,000,000 calls | ~5,000 calls | **$0.00** |
| **Amazon DynamoDB** | 25 GB storage + 25 RCU/WCU | < 50 MB (1,000 items) | **$0.00** |
| **Amazon S3** | 5 GB storage + 2,000 PUTs | < 100 MB (HTML reports) | **$0.00** |
| **Amazon SNS** | 1,000,000 publishes | < 100 alerts | **$0.00** |
| **Amazon SQS** | 1,000,000 requests | < 500 tasks | **$0.00** |
| **Amazon EventBridge** | 14,000,000 events | 30 nightly runs | **$0.00** |
| **AWS SSM Parameter Store** | Unlimited standard params | 1 parameter | **$0.00** |
| **Amazon CloudWatch** | 5 GB logs + 10 metrics | < 50 MB logs + 1 metric | **$0.00** |
| **AWS CloudFormation / SAM** | Unlimited stack actions | 1 active stack | **$0.00** |
| **TOTAL** | — | — | **$0.00 / mo** |

*Note: FinShock is also built with a local fallback engine—if AWS credentials are not configured, it seamlessly stores experiments in local memory and serves static files via Python `http.server` without breaking.*

---

## 4. Slide-by-Slide Presentation Deck (12 Slides with Speaker Notes)

Use this exact section to create your slide presentation (PowerPoint, Keynote, or Google Slides):

---

### Slide 1: Title & Overview
* **Slide Title:** **FinShock**
* **Subtitle:** Institutional Multi-Asset Quantitative Risk Engine & Macro Stress-Testing Platform
* **Key Visual:** Screenshot of FinShock Dashboard with the Live Market Pulse ribbon, Portfolio KPI cards, and Macro Scenarios.
* **Bullets:**
  - Multi-Asset Risk Management across 11 Global & Domestic Asset Classes
  - Dual Value-at-Risk Framework: Gaussian Parametric vs. Historical Fat-Tail VaR
  - Correlated Monte Carlo (Cholesky) & Markowitz Efficient Frontier Optimizer
  - Powered by 10 Native AWS Cloud Services (100% Free-Tier Compliant)
* **Speaker Notes:**
  > *"Good morning everyone. Today I'm presenting FinShock—a cloud-native quantitative risk platform built to bring institutional hedge-fund risk analytics to modern investors. We will look at how financial risk is broken, how FinShock fixes it with rigorous mathematics, and how we engineered the entire system across 10 AWS cloud services at zero server cost."*

---

### Slide 2: The Problem: Why Traditional Risk Tools Fail
* **Slide Title:** The Flaw in Modern Risk Analytics: The Gaussian Fallacy
* **Bullets:**
  - **The Bell Curve Trap:** Standard VaR models assume financial returns are normally distributed. In real crises, fat tails cause massive catastrophic losses.
  - **The Diversification Illusion:** In a liquidity crisis (2008 Lehman, March 2020), correlations spike toward $+1.0$; asset classes that seemed uncorrelated crash together.
  - **High Barriers to Entry:** Institutional platforms like Bloomberg PORT or MSCI Barra cost $30,000+ per year. Retail platforms only display backward-looking past returns.
* **Speaker Notes:**
  > *"Most investors think their portfolio is diversified until a crash hits. The fundamental flaw in conventional risk management is the normal distribution assumption. Financial markets do not follow a tidy bell curve. In market panics, correlations spike and fat tails wipe out capital. FinShock was created to eliminate this blind spot."*

---

### Slide 3: The FinShock Solution
* **Slide Title:** FinShock: Institutional Intelligence for Every Investor
* **Bullets:**
  - **11-Asset Multi-Asset Modeling:** Combines Indian Equities & Sovereign Bonds with US Tech, Gold, Crude Oil, REITs, and Bitcoin.
  - **Forward-Looking Crisis Simulation:** Instant replay of historical panics (COVID-19, 1970s Stagflation) plus a bespoke Custom Crisis Builder.
  - **Dual VaR Architecture:** Side-by-side comparison of Gaussian Parametric VaR with real Historical Simulation VaR (2008–2024).
  - **Serverless Cloud Architecture:** Zero fixed infrastructure, scaling automatically on 10 AWS Free-Tier services.
* **Speaker Notes:**
  > *"FinShock bridges the gap between academic quantitative finance and real-world portfolio management. It gives investors an intuitive, high-speed dashboard to model multi-asset allocations, stress-test against systemic shocks, and run deep mathematical simulations in milliseconds."*

---

### Slide 4: Multi-Asset Universe (11 Institutional Asset Classes)
* **Slide Title:** Multi-Asset Coverage: Beyond Just Equities
* **Bullets:**
  - **Domestic & Global Equities:** NIFTY 50, S&P 500, Nasdaq 100, Emerging Markets (EEM)
  - **Sovereign Fixed Income:** 10Y Indian Sovereign G-Sec, 10Y US Treasury
  - **Macro Commodities:** Physical Gold (Safe-haven buffer), Brent Crude (Energy)
  - **Real Estate & Alternative:** Indian Commercial REITs, Bitcoin (Digital store of value)
  - **Cash Equivalents:** Overnight Liquid Funds (Dry powder)
* **Speaker Notes:**
  > *"Real portfolios aren't just stocks. FinShock models an institutional 11-asset universe spanning domestic equities, global tech, emerging markets, sovereign yields in India and the US, real estate, energy, safe-haven gold, and alternative digital assets like Bitcoin."*

---

### Slide 5: The Quantitative Core: Dual Value at Risk (VaR & CVaR)
* **Slide Title:** Dual VaR: Unmasking Fat-Tail Downside Risk
* **Bullets:**
  - **Gaussian Parametric VaR:** $Z_{0.95} \cdot \sigma_p - \mu_p$. Assumes ideal bell-curve behavior; useful as a regulatory baseline.
  - **Empirical Historical VaR (Quant Upgrade):** Evaluates allocation against real 2008–2024 crash vectors (2008 Lehman, 2011 Downgrade, 2020 COVID, 2022 Fed rate shock).
  - **Higher Statistical Moments:** Directly calculates and displays distribution **Skewness** (asymmetry) and **Excess Kurtosis** (tail fatness).
  - **Conditional VaR (Expected Shortfall):** Quantifies average losses beyond the 95th percentile tail.
* **Speaker Notes:**
  > *"Here is where our quant rigor shines. FinShock calculates traditional Gaussian VaR, but immediately places it side-by-side with Empirical Historical VaR. When a user holds heavy tech or equities, the historical model reveals that true tail losses are often double what normal distribution models report."*

---

### Slide 6: Crisis Simulation & The Custom Scenario Builder
* **Slide Title:** Stress Testing: From Historical Panics to Custom Shocks
* **Bullets:**
  - **5 Pre-Calibrated Macro Scenarios:**
    - March 2020 Pandemic Flash Crash
    - 1970s Style Stagflation Surge
    - Tech & AI Multiples Reset
    - Hormuz/Suez Geopolitical Energy Blockade
    - Global Disinflation Easing (Upside)
  - **Interactive Custom Crisis Builder:** Dial bespoke $\pm 50\%$ shocks per asset class.
  - **Dynamic Persistence:** Click **'Save as Scenario'** to register custom shock vectors into the active scenario registry with instant P&L and rebalancing breakdowns.
* **Speaker Notes:**
  > *"Instead of wondering what will happen if crude oil spikes 50% or tech crashes 30%, users can simply test it. FinShock includes 5 calibrated systemic shocks, and a Custom Crisis Builder where users can construct, name, and save their own bespoke stress vectors."*

---

### Slide 7: Correlated Monte Carlo & Markowitz Optimization
* **Slide Title:** Stochastic Forecasting & Modern Portfolio Theory (MPT)
* **Bullets:**
  - **Cholesky Factorization:** Decomposes the $11 \times 11$ cross-asset correlation matrix ($L \cdot L^T = \Sigma$) to simulate 500–5,000 correlated geometric Brownian motion paths.
  - **Probabilistic Fan Chart:** Visualizes outcome percentiles ($P_5, P_{25}, P_{50}, P_{75}, P_{95}$) and calculates Capital Preservation Probability.
  - **Markowitz Pareto Frontier:** Quadratic covariance optimization plots the efficient boundary.
  - **One-Click Rebalancing:** Automatically discovers the Maximum Sharpe Tangency Portfolio and Minimum Variance Portfolio.
* **Speaker Notes:**
  > *"To forecast the future, we use Monte Carlo simulations with Cholesky decomposition to preserve cross-asset dependencies. Furthermore, our Markowitz optimizer calculates the mathematically optimal Pareto frontier, allowing the user to adopt the Maximum Sharpe Tangency Portfolio with one click."*

---

### Slide 8: Real-Time Market Pulse Ticker Feed
* **Slide Title:** Real-Time Intelligence: Zero-Dependency Market Pulse
* **Bullets:**
  - **Real-Time Data Feed:** Streams live quotes and 1-day percentage changes for NIFTY, S&P 500, Nasdaq, Gold, Crude, US 10Y, Bitcoin, and USD/INR.
  - **Zero External Dependencies:** Built entirely with Python's standard library `urllib.request` (no heavy third-party packages).
  - **In-Memory Caching (60s TTL):** Eliminates API rate limits while ensuring sub-second response times.
  - **Visual Ticker Ribbon:** Animated live pulse indicator with real-time UI refresh.
* **Speaker Notes:**
  > *"A risk tool shouldn't rely on stale static numbers. We built a zero-dependency live market streamer using Python's standard library that fetches live market quotes every 60 seconds with in-memory caching and fallback protection."*

---

### Slide 9: Cloud Architecture: 10 Integrated AWS Services
* **Slide Title:** Cloud-Native Architecture: 10 Integrated AWS Services
* **Bullets:**
  - **Compute & API:** AWS Lambda + Amazon API Gateway (HTTP API v2)
  - **Database & Storage:** Amazon DynamoDB (experiments) + Amazon S3 (risk tearsheets)
  - **Messaging & Queuing:** Amazon SNS (breach alerts) + Amazon SQS (simulation queue)
  - **Orchestration & Config:** Amazon EventBridge (nightly cron) + AWS SSM Parameter Store
  - **Observability & IaC:** Amazon CloudWatch (metrics/logs) + AWS CloudFormation/SAM
* **Speaker Notes:**
  > *"Our cloud infrastructure is our biggest engineering achievement. FinShock is architected on 10 native AWS services. Every component—from serverless compute and NoSQL storage to asynchronous queues and scheduled crons—is fully decoupled and managed via Infrastructure as Code."*

---

### Slide 10: Institutional Reporting & Automated Risk Alerts
* **Slide Title:** Governance & Reporting: Tearsheets & SNS Breach Alerts
* **Bullets:**
  - **Executive HTML Tearsheet:** Generates professional, print-ready risk reports with portfolio KPIs, Marginal Risk Contribution tables, stress breakdowns, and disclaimers.
  - **Amazon S3 Storage:** Tearsheets are exported directly to S3 with secure URI access.
  - **Amazon SNS Risk Alerts:** Automatically publishes SMS/Email alerts to risk managers whenever a portfolio breaches a conservative drawdown limit ($> 15\%$).
* **Speaker Notes:**
  > *"For compliance and governance, FinShock generates executive risk tearsheets stored in Amazon S3, and dispatches real-time email or SMS alerts via Amazon SNS if a portfolio's stressed loss breaches predefined risk thresholds."*

---

### Slide 11: Free-Tier Compliance & Engineering Rigor
* **Slide Title:** Operational Excellence: High Performance at Zero Cost
* **Bullets:**
  - **Zero Idle Infrastructure:** No standing EC2 instances, no provisioned DB instances, no idle costs.
  - **Guaranteed Free-Tier Compliance:** Sized comfortably within AWS monthly free allowances (Lambda 1M calls, DynamoDB 25GB, S3 5GB).
  - **Test-Driven Reliability:** 18 comprehensive unit tests covering API routing, quant metrics, custom scenarios, and market data.
  - **Local Fallback Mode:** Operates seamlessly offline without AWS credentials for rapid local development.
* **Speaker Notes:**
  > *"We engineered FinShock to be production-ready yet 100% compliant with the AWS Free Tier. There are zero standing server charges. Every component is covered by unit tests, and if AWS is disconnected, the platform falls back smoothly to local in-memory operation."*

---

### Slide 12: Conclusion & Future Roadmap
* **Slide Title:** Conclusion & Next Steps
* **Bullets:**
  - **Summary:** An institutional multi-asset risk engine, democratized through serverless cloud engineering and modern quantitative finance.
  - **Future Roadmap:**
    - AI Macro Scenario Synthesis using **Amazon Bedrock** (LLM-driven crisis generation).
    - Multi-tenant client portfolio management with Amazon Cognito authentication.
    - Historical tick-level backtesting across 20-year rolling windows.
  - **Thank You! Questions & Discussion**
* **Speaker Notes:**
  > *"In summary, FinShock combines academic quantitative rigor with modern cloud architecture. It replaces expensive, closed systems with a transparent, serverless platform. Thank you for your time, and I'd be glad to take any questions."*

---

## 5. Anticipated Q&A & Defensible Technical Answers

Here are the most common questions evaluators, interviewers, or clients will ask—and how to answer them with authority:

#### Q1: "Why did you implement Historical VaR in addition to Parametric VaR?"
> **Answer:** *"Parametric VaR assumes returns follow a Gaussian normal distribution. In reality, equity and crypto returns exhibit negative skewness (sharp left-side crashes) and excess kurtosis (fat tails). In March 2020, actual market losses were 4 standard deviation events under normal assumptions—theoretically a 1-in-30,000 year event. By adding Empirical Historical Simulation across real crisis years (2008, 2020, 2022), FinShock captures real tail losses and displays skewness and kurtosis directly."*

#### Q2: "Why use 10 AWS services instead of just running a simple container on EC2?"
> **Answer:** *"Running an EC2 or ECS container incurs fixed 24/7 costs even when nobody is using the platform. By adopting a serverless microservices model with Lambda, API Gateway, DynamoDB, S3, SNS, SQS, EventBridge, SSM, and CloudWatch, we achieved three things: (1) Zero idle cost with 100% Free-Tier compliance, (2) Infinite auto-scaling during traffic spikes, and (3) Complete decoupling so a heavy Monte Carlo simulation never slows down interactive user requests."*

#### Q3: "How does Cholesky Decomposition work in your Monte Carlo simulation?"
> **Answer:** *"If you simulate multi-asset prices using independent random numbers, assets move completely independently, which is unrealistic. In reality, when equities fall, gold or sovereign bonds often rise. We perform a Cholesky factorization on our $11 \times 11$ empirical correlation matrix to obtain a lower triangular matrix $L$ such that $L \cdot L^T = \Sigma_{\text{corr}}$. By multiplying our uncorrelated Gaussian random vectors by $L$, we generate correlated Brownian motion shocks that preserve real cross-asset market behavior."*

#### Q4: "How does the Live Market Pulse avoid rate limits and third-party package dependencies?"
> **Answer:** *"Many projects pull in heavy third-party packages like `yfinance`, which frequently break on updates and bloat Lambda deployment packages. We wrote our fetcher using Python's standard library `urllib.request` querying public endpoints with a 60-second in-memory TTL cache. This provides sub-second API response times and prevents upstream rate limiting while remaining 100% lightweight."*

#### Q5: "What happens if someone runs FinShock locally without an AWS account?"
> **Answer:** *"FinShock includes an automatic graceful fallback mechanism. In `backend/services/storage.py` and `aws_services.py`, the system checks for active AWS credentials. If credentials are not present, it logs a clean fallback mode, stores experiments in runtime memory, simulates SNS alerts locally, and serves the entire application via standard Python `http.server` on port 8000."*
