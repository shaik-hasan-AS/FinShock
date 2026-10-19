# FinShock: Quantitative Risk Analytics & Macro Stress-Testing Platform
### Comprehensive Project Overview & AWS Cloud Architecture Guide
*Ready-to-present documentation and slide-by-slide presentation deck.*

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [The Problem Statement](#2-the-problem-statement)
3. [The FinShock Solution & Core Value](#3-the-finshock-solution--core-value)
4. [Quantitative Engine & Analytical Capabilities](#4-quantitative-engine--analytical-capabilities)
   - 11-Asset Multi-Asset Universe
   - Gaussian Parametric VaR vs. Empirical Historical VaR (Fat Tails)
   - Macro Scenario Stress Testing & Custom Crisis Builder
   - Correlated Monte Carlo Simulation (Cholesky Decomposition)
   - Markowitz Modern Portfolio Theory (MPT) Efficient Frontier
   - Marginal Contribution to Risk (MCR) & Component VaR
   - Real-Time Live Market Data (Market Pulse)
5. [AWS Cloud Architecture (10 Integrated Services)](#5-aws-cloud-architecture-10-integrated-services)
   - Deep Dive into Each Service & Architectural Role
   - AWS Free-Tier Compliance & Zero-Cost Guardrails Table
6. [System Data Flow & Architecture Diagram](#6-system-data-flow--architecture-diagram)
7. [Slide-by-Slide Presentation Deck Outline](#7-slide-by-slide-presentation-deck-outline)

---

## 1. Executive Summary

**FinShock** is an institutional-grade, cloud-native quantitative risk management and macro stress-testing platform. It enables portfolio managers, risk officers, treasury desks, and retail investors to model multi-asset portfolios, simulate systemic macroeconomic shocks, quantify fat-tailed downside risk, and optimize asset allocation across 11 global and domestic asset classes.

Built entirely on **10 AWS Serverless & Cloud-Native Services**, FinShock provides institutional hedge-fund capabilities with zero fixed infrastructure costs, guaranteed 100% AWS Free-Tier compliance, and seamless local fallback.

---

## 2. The Problem Statement

Traditional wealth management and risk platforms suffer from three systemic flaws:
1. **The "Gaussian Fallacy" (Normal Distribution Assumption):** Conventional Value-at-Risk (VaR) assumes financial returns follow a standard bell curve. In real crises (2008 Lehman collapse, March 2020 COVID shock, 2022 Fed rate shock), correlation structures break down and extreme fat tails emerge, severely underestimating true downside exposure.
2. **Static & Opaque Stress Testing:** Most retail platforms only show backward-looking past returns. They cannot answer forward-looking questions like *"What happens to my capital if Brent Crude surges 45% and central banks hike rates by 200 bps?"*
3. **Expensive, Heavyweight Infrastructure:** Institutional risk systems (Bloomberg PORT, MSCI Barra, Aladdin) cost tens of thousands of dollars annually. Existing open-source alternatives require heavy server clusters, complex Kubernetes setups, and steep operational overhead.

---

## 3. The FinShock Solution & Core Value

FinShock democratizes institutional quantitative risk intelligence:
* **True Multi-Asset Modeling:** Combines Indian Sovereign & Equities with US Tech, Global Equities, Physical Gold, Energy, Real Estate (REITs), and Digital Assets (Bitcoin).
* **Dual VaR Framework:** Evaluates both **Parametric Gaussian VaR** and **Empirical Historical VaR** across 2008–2024 crisis vectors to expose hidden tail risks.
* **Dynamic Scenario Sandbox:** Pre-calibrated macro shock vectors plus a bespoke **Custom Scenario Builder** where users adjust asset shocks and save reusable scenarios.
* **10-Service Cloud Architecture:** Complete integration with AWS Lambda, API Gateway v2, DynamoDB, S3, SNS, SQS, EventBridge, CloudWatch, SSM, and CloudFormation.
* **100% Free-Tier Compliant:** Engineered with zero idle compute costs, local SQLite/in-memory fallback, and automated budget safeguards.

---

## 4. Quantitative Engine & Analytical Capabilities

### A. 11-Asset Multi-Asset Universe
FinShock spans domestic, global, fixed-income, commodity, real estate, and alternative assets:
1. **NIFTY 50** (`NIFTY_50`): Domestic Indian Large-Cap Equities
2. **S&P 500** (`SP500`): US Large-Cap Equities
3. **Nasdaq 100** (`NASDAQ_100`): US High-Beta Tech & AI
4. **Emerging Markets** (`EMERGING_MKTS`): EM Asia/LATAM Equities
5. **Physical Gold** (`GOLD`): Inflation & Crisis Safe-Haven Commodity
6. **Brent Crude** (`CRUDE_OIL`): Macro Energy & Supply-Shock Commodity
7. **10Y Sovereign G-Sec** (`GSEC_10Y`): Indian Benchmark Sovereign Debt
8. **10Y US Treasury** (`US_TREASURY_10Y`): Global Risk-Free Benchmark
9. **Indian Commercial REIT** (`REIT_IN`): Real Estate Yield & Inflation Hedge
10. **Bitcoin** (`BITCOIN`): Digital Asset / Asymmetric Alternative
11. **Liquid Cash / Overnight** (`LIQUID_CASH`): Capital Preservation Benchmark

### B. Parametric VaR vs. Empirical Historical VaR (Fat Tails)
* **Gaussian Parametric VaR & CVaR:**
  $$\text{VaR}_{\alpha} = Z_{\alpha} \cdot \sigma_p - \mu_p$$
  $$\text{CVaR}_{\alpha} = \left(\frac{\phi(Z_{\alpha})}{1 - \alpha}\right) \cdot \sigma_p - \mu_p$$
  *Where $Z_{0.95} = 1.645$, $Z_{0.99} = 2.326$.*
* **Empirical Historical Simulation VaR (Quant Upgrade):**
  Uses a curated 2008–2024 annual crisis return matrix covering the 2008 Lehman GFC, 2011 US Debt Downgrade, 2013 Taper Tantrum, 2015 China Devaluation, 2020 COVID crash, and 2022 Fed rate tightening.
  - Computes exact historical portfolio returns: $R_{p, t} = \sum_i w_i R_{i, t}$
  - Calculates empirical 5th percentile loss without assuming normal distribution.
  - Outputs statistical **Skewness** and **Excess Kurtosis**, proving why real-world losses exceed theoretical bell-curve estimates.

### C. Macro Stress Testing & Custom Crisis Builder
* **5 Pre-calibrated Macro Crises:**
  1. **Global Pandemic Flash Crash (March 2020):** Liquidity freeze across equities & crude; flight to sovereign bonds and gold.
  2. **1970s Style Stagflation Surge:** Energy price explosion; central banks aggressively hike, punishing equities and long bonds.
  3. **Tech & AI Multiples Reset:** Multiples compression in speculative high-duration tech; rotation into domestic yields & gold.
  4. **Hormuz/Suez Geopolitical Blockade:** Maritime chokepoints shut; crude spikes +65%, importing EMs suffer currency depreciation.
  5. **Global Disinflation & Rate Easing (Upside):** Synchronized central bank cuts, capex cycle expansion, broad rally.
* **Custom Crisis Builder:**
  - Interactive slider controls allowing $\pm 50\%$ custom shocks per asset.
  - Save scenario feature (`POST /api/scenarios`) that registers custom scenarios directly into the active scenario grid.

### D. Correlated Monte Carlo Simulation
* Generates 500 to 5,000 geometric Brownian motion paths over a 252-day horizon.
* Decomposes the empirical 11×11 cross-asset correlation matrix using **Cholesky Factorization** ($L \cdot L^T = \Sigma$), ensuring correlated shocks reflect cross-asset dependencies (e.g., flight to safety, equity-bond decoupling).
* Produces probabilistic fan charts ($P_5, P_{25}, P_{50}, P_{75}, P_{95}$) and calculates the **Probability of Capital Preservation**.

### E. Markowitz Modern Portfolio Theory (MPT) Frontier
* Quadratic optimization across the covariance matrix:
  $$\min_w \frac{1}{2} w^T \Sigma w \quad \text{s.t.} \quad \sum w_i = 1, \quad w_i \ge 0$$
* Plots the continuous Pareto risk-return boundary.
* Solves and identifies:
  1. **Tangency Portfolio:** Maximizes the Sharpe Ratio over benchmark risk-free rate.
  2. **Minimum Variance Portfolio (MVP):** Minimizes total portfolio volatility.
* Single-click **"Apply Allocation"** updates the user's live portfolio.

### F. Marginal Contribution to Risk (MCR) & Component VaR
* Dissects total portfolio risk into asset-level drivers:
  $$\text{MCR}_i = \frac{(\Sigma w)_i}{\sigma_p}$$
  $$\% \text{ Contribution to Risk} = \frac{w_i \cdot \text{MCR}_i}{\sigma_p}$$
* Unveils concentration risks (e.g., when an asset with only 15% weight contributes 40% of portfolio volatility).

### G. Live Market Pulse Ticker
* Streamlines real-time / 1-day market prices and % changes for benchmark indices (NIFTY, S&P 500, Nasdaq, Gold, Crude, US 10Y, Bitcoin, USD/INR).
* Uses Python standard library `urllib.request` with 60-second in-memory caching and zero third-party dependencies.
* Animated UI with live pulse indicator and automatic 60-second polling.

---

## 5. AWS Cloud Architecture (10 Integrated Services)

FinShock's backend is architected around 10 AWS cloud services, designed specifically to operate completely inside the **AWS Free Tier**:

| # | AWS Service | Category | Specific Role in FinShock | Free-Tier Guardrail / Limit |
|---|---|---|---|---|
| **1** | **AWS Lambda** | Compute | Runs serverless quantitative calculations (`calculate_portfolio_metrics`, Monte Carlo, Markowitz optimization, shock tests). | **1 Million free requests/mo**, 3.2M sec compute time. Zero cost when idle. |
| **2** | **Amazon API Gateway (HTTP API v2)** | Networking | High-speed, low-latency HTTP v2 routing for `/api/*` endpoints with built-in CORS. | **1 Million free API calls/mo** for 12 months. |
| **3** | **Amazon DynamoDB** | Database | Persists saved stress-testing experiments, user portfolio allocations, and simulation results. | **25 GB storage + 25 RCU/WCU always free**. No provisioned server costs. |
| **4** | **Amazon S3** | Storage | Stores exported HTML Executive Risk Tearsheets, stress test audit logs, and benchmark historical datasets. | **5 GB standard storage + 20,000 GETs / 2,000 PUTs free/mo**. |
| **5** | **Amazon SNS** | Messaging | Publishes instant Risk Breach Alerts (via Email/SMS) when portfolio drawdown exceeds critical limits (e.g., >15%). | **1 Million free mobile/email alert publishes/mo**. |
| **6** | **Amazon SQS** | Queueing | Asynchronous buffer queue (`finshock-simulation-queue`) for heavy batch Monte Carlo runs (5,000+ paths). | **1 Million free queue requests/mo**. Prevents Lambda timeout under peak load. |
| **7** | **Amazon EventBridge** | Orchestration | Scheduled cron (`cron(0 2 * * ? *)`) that automatically triggers nightly portfolio risk re-evaluations. | **14 Million free events/mo**. |
| **8** | **AWS SSM Parameter Store** | Configuration | Centralized secure store for dynamic macro parameters (e.g., `/finshock/config/risk_free_rate = 0.065`). | **Standard parameters are 100% free with unlimited storage**. |
| **9** | **Amazon CloudWatch** | Observability | Logs quantitative errors, latency, and publishes custom portfolio risk metrics under namespace `FinShock/Quant`. | **5 GB log ingestion + 10 custom metrics + 3 alarms free**. |
| **10** | **AWS CloudFormation / SAM** | IaC | Fully automated Infrastructure as Code template (`template.yaml`) for one-command deployment (`sam deploy`). | **CloudFormation resource management is 100% free**. |

---

## 6. System Data Flow & Architecture Diagram

```
                             [ WEB BROWSER / CLIENT UI ]
                 (HTML5, CSS Glassmorphism, Vanilla JS, Chart.js)
                                      │
                   HTTP API v2 Requests (/api/*)
                                      ▼
                        [ AMAZON API GATEWAY v2 ]
                                      │
                             Proxy Event Payload
                                      ▼
                             [ AWS LAMBDA ]
                     (Unified Quantitative Engine)
               ┌──────────────────────┼──────────────────────┐
               │                      │                      │
       Fetch Benchmark Rate     Save Experiment       Store HTML Reports
               ▼                      ▼                      ▼
        [ AWS SSM STORE ]     [ AMAZON DYNAMODB ]      [ AMAZON S3 ]
      (/finshock/config/rf)  (finshock_experiments)  (finshock-reports)
               │                      │                      │
               ▼                      ▼                      ▼
        [ CLOUDWATCH ]          [ AMAZON SNS ]         [ AMAZON SQS ]
     (Custom Metrics/Logs)   (Risk Breach Alerts)   (Async Batch Queue)
                                      ▲
                                      │ Nightly Cron Trigger
                             [ AMAZON EVENTBRIDGE ]
```

---

## 7. Slide-by-Slide Presentation Deck Outline

Use this exact structure to build your slide deck (PowerPoint, Google Slides, or Keynote):

### Slide 1: Title & Hook
* **Title:** FinShock: Institutional-Grade Quantitative Risk Engine & Macro Stress-Testing Platform
* **Subtitle:** Serverless Multi-Asset Analytics Powered by 10 AWS Cloud Services
* **Presenter:** [Your Name / Team Name]
* **Key Visual:** FinShock dashboard screenshot with the Market Pulse ribbon and risk KPI cards.

### Slide 2: The Problem: Why Traditional Portfolio Risk Fails
* **The Gaussian Fallacy:** Traditional risk engines assume asset returns are normally distributed (bell curve). In real crises, fat tails cause massive unexpected losses.
* **Correlation Breakdown:** In panic events, historical correlations spike to near 1.0 across equities, destroying diversification.
* **Prohibitive Cost:** Enterprise platforms like Bloomberg PORT and Aladdin cost upwards of $30,000/year, locking out independent wealth managers and retail treasuries.

### Slide 3: The FinShock Solution
* **Institutional Rigor for Everyone:** Complete multi-asset risk analysis available via an interactive web interface or serverless API.
* **Real Crisis Simulation:** Ability to replay historical crises (2008 Lehman, March 2020 COVID, 2022 Fed rate hike) or dial custom macro shocks.
* **100% Serverless & Zero-Cost:** Engineered to run within AWS Free Tier without sacrificing speed or security.

### Slide 4: Multi-Asset Universe (11 Institutional Asset Classes)
* **Domestic & Global Equities:** NIFTY 50, S&P 500, Nasdaq 100, Emerging Markets
* **Fixed Income:** 10Y Indian Sovereign G-Sec, 10Y US Treasury
* **Commodities:** Physical Gold (Safe-haven), Brent Crude (Energy)
* **Real Estate & Alternative:** Indian Commercial REITs, Bitcoin (Crypto)
* **Cash Equivalent:** Liquid Overnight Fund

### Slide 5: The Quant Core: VaR, CVaR & Fat-Tail Analysis
* **Parametric VaR vs. Historical VaR:**
  - Parametric Gaussian VaR ($Z = 1.645$) gives theoretical baseline loss.
  - Empirical Historical VaR uses actual 2008–2024 crash vectors to reveal true fat-tail downside.
* **Higher Statistical Moments:** Displays distribution **Skewness** and **Excess Kurtosis** directly in the UI.
* **Conditional VaR (Expected Shortfall):** Quantifies average losses in the worst 5% tail, not just the threshold cutoff.

### Slide 6: Crisis Simulation & Custom Macro Shock Builder
* **5 Turnkey Historical Scenarios:**
  - COVID 2020 Flash Crash, 1970s Stagflation, Tech Multiples Reset, Hormuz Blockade, Soft Landing.
* **Live Custom Crisis Sandbox:**
  - Sliders for bespoke $\pm 50\%$ shock parameters across all 11 assets.
  - **"Save as Scenario"** feature registers custom scenarios into the runtime database with one click.
  - Generates instant stressed capital, asset-level P&L, and post-shock rebalanced weights.

### Slide 7: Correlated Monte Carlo & Markowitz Efficient Frontier
* **Cholesky Decomposition Engine:**
  - Simulates 500–5,000 correlated price trajectories using geometric Brownian motion.
  - Generates probabilistic fan charts ($P_5$ to $P_{95}$) and capital preservation probability.
* **Markowitz Efficient Frontier:**
  - Quadratic covariance optimization plots the Pareto risk-return boundary.
  - Automatically identifies Tangency Portfolio (Max Sharpe) and Minimum Variance Portfolio.
  - One-click allocation update directly to portfolio sliders.

### Slide 8: Real-Time Market Pulse Ticker
* **Live Financial Data Feed:**
  - Real-time / 1-day delayed quotes streaming for NIFTY, S&P, Nasdaq, Gold, Crude, Treasuries, BTC, and USD/INR.
  - Standard library implementation with zero external package bloat.
  - 60-second in-memory caching to eliminate rate limits and maintain sub-second response times.

### Slide 9: Cloud Architecture: 10 AWS Services
* Present the architectural table:
  - **Compute & Routing:** AWS Lambda + API Gateway v2
  - **Data & Storage:** DynamoDB (experiments) + S3 (reports & tearsheets)
  - **Messaging & Queuing:** SNS (instant breach alerts) + SQS (batch simulation queue)
  - **Orchestration & Config:** EventBridge (nightly cron) + SSM Parameter Store (benchmark yields)
  - **Observability & IaC:** CloudWatch (alarms/metrics) + CloudFormation/SAM (`template.yaml`)

### Slide 10: Institutional Reporting: Executive Tearsheet
* **One-Click Compliance Tearsheet:**
  - Generates executive-ready HTML reports stored directly in Amazon S3.
  - Includes portfolio KPI cards (Parametric vs. Historical VaR), Marginal Risk Contribution (MCR) tables, post-shock stress breakdown, and regulatory risk disclaimers.

### Slide 11: Free-Tier Compliance & Engineering Highlights
* **Zero Idle Cost:** No EC2 instances, no provisioned clusters, no standing databases.
* **Dual Execution Mode:** Runs seamlessly in the cloud via AWS SAM or locally via standard Python `http.server`.
* **Clean Code & Test Coverage:** 18 passing unit tests across quant calculations, API routing, custom scenario saving, and live market data.

### Slide 12: Summary & Future Roadmap
* **What We Built:** An institutional-quality multi-asset risk analytics engine deployed on modern serverless AWS infrastructure.
* **Future Expansions:**
  - AI-driven macroeconomic scenario generator using AWS Bedrock.
  - Multi-user portfolio sharing and historical backtesting against 10-year rolling daily tick data.
* **Q&A:** Open floor for questions.
