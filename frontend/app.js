// FinShock Quant Lab — Institutional Quantitative Terminal Frontend Controller

const AWS_API_GATEWAY_URL = 'https://ig4f3mvsgb.execute-api.ap-south-1.amazonaws.com';
const API_BASE = (window.location.origin.startsWith('http') && window.location.port === '8000') 
  ? window.location.origin 
  : (window.FINSHOCK_API_BASE || AWS_API_GATEWAY_URL);

const STATE = {
  capital: 1000000,
  assets: {},
  assetOrder: [],
  weights: {},
  scenarios: {},
  activeScenarioId: 'covid_2020_flash_crash',
  customShocks: {},
  metrics: null,
  shockResult: null,
  simResult: null,
  riskDecomp: null,
  frontierData: null,
};

// Institutional Strategy Presets (11 Assets, Sum = 100%)
const PRESETS = {
  balanced: {
    NIFTY_50: 25, SP500: 15, NASDAQ_100: 10, EMERGING_MKTS: 5,
    GOLD: 10, CRUDE_OIL: 5, GSEC_10Y: 15, US_TREASURY_10Y: 5,
    REIT_IN: 5, BITCOIN: 2, LIQUID_CASH: 3
  },
  allweather: {
    NIFTY_50: 15, SP500: 10, NASDAQ_100: 5, EMERGING_MKTS: 0,
    GOLD: 20, CRUDE_OIL: 10, GSEC_10Y: 25, US_TREASURY_10Y: 10,
    REIT_IN: 0, BITCOIN: 0, LIQUID_CASH: 5
  },
  techgrowth: {
    NIFTY_50: 20, SP500: 25, NASDAQ_100: 30, EMERGING_MKTS: 5,
    GOLD: 5, CRUDE_OIL: 0, GSEC_10Y: 5, US_TREASURY_10Y: 0,
    REIT_IN: 5, BITCOIN: 5, LIQUID_CASH: 0
  },
  inflation: {
    NIFTY_50: 10, SP500: 5, NASDAQ_100: 0, EMERGING_MKTS: 5,
    GOLD: 30, CRUDE_OIL: 20, GSEC_10Y: 10, US_TREASURY_10Y: 0,
    REIT_IN: 15, BITCOIN: 0, LIQUID_CASH: 5
  },
  defensive: {
    NIFTY_50: 10, SP500: 5, NASDAQ_100: 0, EMERGING_MKTS: 0,
    GOLD: 15, CRUDE_OIL: 0, GSEC_10Y: 40, US_TREASURY_10Y: 20,
    REIT_IN: 0, BITCOIN: 0, LIQUID_CASH: 10
  },
};

// Benchmark Live Ticker Feed Data
const TICKER_DATA = [
  { sym: 'NIFTY 50', price: '24,850.25', chg: '+0.68%', dir: 'up' },
  { sym: 'S&P 500', price: '5,815.10', chg: '+0.42%', dir: 'up' },
  { sym: 'NASDAQ 100', price: '18,340.50', chg: '+0.85%', dir: 'up' },
  { sym: 'GOLD (10g)', price: '₹76,420', chg: '+1.15%', dir: 'up' },
  { sym: 'BRENT CRUDE', price: '$74.80/bbl', chg: '-1.40%', dir: 'down' },
  { sym: '10Y G-SEC', price: '6.78%', chg: '-0.02%', dir: 'down' },
  { sym: 'US 10Y YIELD', price: '4.08%', chg: '+0.03%', dir: 'up' },
  { sym: 'REIT IN', price: '₹385.40', chg: '+0.30%', dir: 'up' },
  { sym: 'BITCOIN', price: '$65,420', chg: '+2.45%', dir: 'up' },
  { sym: 'USD/INR', price: '₹84.05', chg: '+0.05%', dir: 'up' },
];

function formatINR(val) {
  if (isNaN(val) || val === null) return '₹--';
  return '₹' + Math.round(val).toLocaleString('en-IN');
}

function formatPercent(val) {
  if (isNaN(val) || val === null) return '--%';
  return val.toFixed(1) + '%';
}

// Initialize Application
async function init() {
  initMarketTicker();
  setupTabs();
  setupAwsModal();
  setupTearsheetModal();
  setupCapitalControls();
  setupPresetButtons();
  setupCustomShockControls();
  setupFrontierButtons();
  setupSimulateButton();
  setupSaveExperimentButton();
  setupSendAlertButton();
  setupExportS3Button();

  await checkAwsStatus();
  await loadAssetsAndScenarios();
  await refreshSavedExperiments();

  // Initial calculation and simulation passes
  await triggerAnalysis();
  await triggerShock();
  await triggerMonteCarlo();
  await triggerRiskDecomposition();
  await triggerEfficientFrontier();
}

// Market Pulse Live Ticker Tape
async function updateLiveMarketTicker() {
  try {
    const res = await fetch(`${API_BASE}/api/market-pulse`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.tickers && data.tickers.length > 0) {
      const container = document.getElementById('tickerItemsContainer');
      if (!container) return;
      container.innerHTML = data.tickers.map(t => `
        <div class="ticker-item">
          <span class="sym">${t.sym}</span>
          <span class="price">${t.price}</span>
          <span class="chg ${t.dir}">${t.chg}</span>
        </div>
      `).join('');
    }
  } catch (err) {
    console.warn('Failed to refresh live market ticker:', err);
  }
}

function initMarketTicker() {
  const container = document.getElementById('tickerItemsContainer');
  if (!container) return;
  // Immediate paint with cached/baseline symbols
  container.innerHTML = TICKER_DATA.map(t => `
    <div class="ticker-item">
      <span class="sym">${t.sym}</span>
      <span class="price">${t.price}</span>
      <span class="chg ${t.dir}">${t.chg}</span>
    </div>
  `).join('');
  
  // Fetch real-time live market quotes and poll every 60s
  updateLiveMarketTicker();
  setInterval(updateLiveMarketTicker, 60000);
}

// Check AWS Connection Status & Load 10-Service Architecture
async function checkAwsStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/aws-services`);
    if (!res.ok) return;
    const data = await res.json();
    const badge = document.getElementById('awsStatusBadge');
    const badgeText = document.getElementById('awsBadgeText');

    if (data.aws_connected) {
      badge.className = 'aws-badge aws-connected';
      badgeText.textContent = `AWS: ${data.region}`;
      document.getElementById('awsModalStatus').textContent = 'Connected (Cloud Mode)';
      document.getElementById('awsModalStatus').className = 'badge-status text-success';
    } else {
      badge.className = 'aws-badge aws-local';
      badgeText.textContent = 'AWS: Local Mode';
      document.getElementById('awsModalStatus').textContent = 'Local Fallback (Waiting for keys)';
      document.getElementById('awsModalStatus').className = 'badge-status text-dim';
    }
    document.getElementById('awsModalRegion').textContent = `${data.region} (Mumbai)`;

    // Populate 10-service table
    const tbody = document.getElementById('awsServicesTableBody');
    if (tbody && data.services) {
      tbody.innerHTML = '';
      data.services.forEach(srv => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td><strong>${srv.name}</strong></td>
          <td><span class="chip-btn">${srv.category}</span></td>
          <td style="font-family: var(--font-sans); color: var(--text-muted); font-size: 0.8rem;">${srv.role}</td>
          <td><span style="color: ${srv.active ? '#10b981' : '#f59e0b'}; font-weight:600;">${srv.status}</span></td>
        `;
        tbody.appendChild(row);
      });
    }
  } catch (err) {
    console.warn('Could not query AWS status', err);
  }
}

// Load Assets and Macro Scenarios
async function loadAssetsAndScenarios() {
  try {
    const [assetsRes, scenariosRes] = await Promise.all([
      fetch(`${API_BASE}/api/assets`),
      fetch(`${API_BASE}/api/scenarios`),
    ]);

    const assetsData = await assetsRes.json();
    const scenariosData = await scenariosRes.json();

    STATE.assets = assetsData.assets;
    STATE.assetOrder = assetsData.asset_order;
    STATE.scenarios = scenariosData.scenarios;
    STATE.correlationMatrix = assetsData.correlation_matrix;

    // Set initial weights
    STATE.weights = {};
    STATE.assetOrder.forEach(aid => {
      STATE.weights[aid] = Math.round((STATE.assets[aid].default_weight || 0) * 100);
      STATE.customShocks[aid] = 0;
    });

    renderAssetSliders();
    renderScenariosGrid();
    renderCustomShockSliders();
    renderCorrelationMatrix();
  } catch (err) {
    console.error('Failed to load initial metadata', err);
  }
}

// Render Asset Sliders
function renderAssetSliders() {
  const container = document.getElementById('assetSliders');
  container.innerHTML = '';

  STATE.assetOrder.forEach(aid => {
    const asset = STATE.assets[aid];
    const weight = STATE.weights[aid] || 0;

    const item = document.createElement('div');
    item.className = 'asset-slider-item';
    item.innerHTML = `
      <div class="asset-meta">
        <span class="asset-name">
          <span class="asset-color-dot" style="background-color: ${asset.color || '#3b82f6'}"></span>
          ${asset.name}
        </span>
        <span class="asset-percent-val" id="val_${aid}">${weight}%</span>
      </div>
      <input type="range" id="slider_${aid}" min="0" max="100" value="${weight}" data-aid="${aid}">
    `;

    const slider = item.querySelector('input');
    slider.addEventListener('input', (e) => {
      STATE.weights[aid] = parseInt(e.target.value, 10);
      document.getElementById(`val_${aid}`).textContent = `${STATE.weights[aid]}%`;
      updateAllocationVisuals();
      debounce(onAllocationChange, 250)();
    });

    container.appendChild(item);
  });

  updateAllocationVisuals();
}

function updateAllocationVisuals() {
  const sum = Object.values(STATE.weights).reduce((a, b) => a + b, 0);
  const badge = document.getElementById('allocationSumBadge');
  badge.textContent = `${sum}%`;
  badge.className = sum === 100 ? 'sum-badge valid' : 'sum-badge invalid';

  const bar = document.getElementById('allocationVisualBar');
  bar.innerHTML = '';
  STATE.assetOrder.forEach(aid => {
    const pct = STATE.weights[aid] || 0;
    if (pct > 0) {
      const seg = document.createElement('div');
      seg.className = 'allocation-bar-segment';
      seg.style.width = `${(pct / Math.max(1, sum)) * 100}%`;
      seg.style.backgroundColor = STATE.assets[aid]?.color || '#3b82f6';
      bar.appendChild(seg);
    }
  });
}

async function onAllocationChange() {
  await triggerAnalysis();
  await triggerShock();
  triggerRiskDecomposition();
  triggerEfficientFrontier();
}

// Render Macro Scenarios
function renderScenariosGrid() {
  const container = document.getElementById('scenariosGrid');
  container.innerHTML = '';

  Object.entries(STATE.scenarios).forEach(([scId, sc]) => {
    const card = document.createElement('div');
    card.className = `scenario-card ${scId === STATE.activeScenarioId ? 'active' : ''}`;
    card.dataset.scid = scId;
    const isCustom = sc.is_custom || scId.startsWith('custom_');
    card.innerHTML = `
      ${isCustom ? '<span class="sc-badge-custom">Custom Stress Test</span>' : ''}
      <div class="sc-title">${sc.name}</div>
      <div class="sc-desc">${sc.description}</div>
    `;

    card.addEventListener('click', () => {
      document.querySelectorAll('.scenario-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      STATE.activeScenarioId = scId;
      triggerShock();
    });

    container.appendChild(card);
  });
}

// Custom Macro Shock Sandbox
function setupCustomShockControls() {
  const toggleBtn = document.getElementById('customShockToggle');
  const panel = document.getElementById('customShockPanel');
  const toggleIcon = document.getElementById('customShockToggleBtn');

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const isOpen = panel.style.display !== 'none';
      panel.style.display = isOpen ? 'none' : 'block';
      toggleIcon.textContent = isOpen ? 'Custom Crisis Builder' : 'Collapse Sandbox';
    });
  }

  const resetBtn = document.getElementById('resetCustomShockBtn');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      STATE.assetOrder.forEach(aid => {
        STATE.customShocks[aid] = 0;
        const slider = document.getElementById(`shock_slider_${aid}`);
        const valEl = document.getElementById(`shock_val_${aid}`);
        if (slider) slider.value = 0;
        if (valEl) {
          valEl.textContent = '0%';
          valEl.className = 'custom-shock-val zero';
        }
      });
      triggerShock(true);
    });
  }

  const applyBtn = document.getElementById('applyCustomShockBtn');
  if (applyBtn) {
    applyBtn.addEventListener('click', () => {
      document.querySelectorAll('.scenario-card').forEach(c => c.classList.remove('active'));
      STATE.activeScenarioId = 'custom';
      triggerShock(true);
    });
  }

  const saveBtn = document.getElementById('saveCustomScenarioBtn');
  const nameInput = document.getElementById('customScenarioNameInput');
  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      const name = (nameInput && nameInput.value.trim()) || `Custom Stress Test #${Object.keys(STATE.scenarios).length + 1}`;
      const payload = {
        name: name,
        description: `User-defined macro shock scenario across multi-asset universe`,
        shocks: { ...STATE.customShocks },
      };
      try {
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';
        const res = await fetch(`${API_BASE}/api/scenarios`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          const data = await res.json();
          const newSc = data.scenario;
          STATE.scenarios[newSc.id] = newSc;
          STATE.activeScenarioId = newSc.id;
          renderScenariosGrid();
          triggerShock();
          if (nameInput) nameInput.value = '';
        }
      } catch (err) {
        console.error('Failed to save custom scenario:', err);
      } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = '💾 Save Scenario';
      }
    });
  }
}

function renderCustomShockSliders() {
  const container = document.getElementById('customShockGrid');
  if (!container) return;
  container.innerHTML = '';

  STATE.assetOrder.forEach(aid => {
    const asset = STATE.assets[aid];
    const val = STATE.customShocks[aid] || 0;

    const item = document.createElement('div');
    item.className = 'custom-shock-item';
    item.innerHTML = `
      <div class="custom-shock-item-header">
        <span style="font-weight: 600; color: var(--text-primary); font-size: 0.72rem;">${asset.name}</span>
        <span id="shock_val_${aid}" class="custom-shock-val ${val < 0 ? 'neg' : val > 0 ? 'pos' : 'zero'}">${val > 0 ? '+' : ''}${val}%</span>
      </div>
      <input type="range" id="shock_slider_${aid}" min="-50" max="50" step="5" value="${val}" style="width: 100%;">
    `;

    const slider = item.querySelector('input');
    slider.addEventListener('input', (e) => {
      const newVal = parseInt(e.target.value, 10);
      STATE.customShocks[aid] = newVal;
      const valEl = document.getElementById(`shock_val_${aid}`);
      valEl.textContent = `${newVal > 0 ? '+' : ''}${newVal}%`;
      valEl.className = `custom-shock-val ${newVal < 0 ? 'neg' : newVal > 0 ? 'pos' : 'zero'}`;
    });

    container.appendChild(item);
  });
}

// Trigger Quantitative Portfolio Analysis
async function triggerAnalysis() {
  try {
    const res = await fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        capital: STATE.capital,
        weights: STATE.weights,
      }),
    });
    const data = await res.json();
    STATE.metrics = data;

    document.getElementById('metricExpReturn').textContent = formatPercent(data.expected_return * 100);
    document.getElementById('metricVolatility').textContent = formatPercent(data.volatility * 100);
    document.getElementById('metricSharpe').textContent = data.sharpe_ratio.toFixed(2);
    const histVarPct = data.hist_var_95_percent !== undefined ? data.hist_var_95_percent : data.var_95_percent;
    const histVarAmt = data.hist_var_95_amount !== undefined ? data.hist_var_95_amount : data.var_95_amount;
    const histCVarPct = data.hist_cvar_95_percent !== undefined ? data.hist_cvar_95_percent : data.cvar_95_percent;
    const histCVarAmt = data.hist_cvar_95_amount !== undefined ? data.hist_cvar_95_amount : data.cvar_95_amount;

    document.getElementById('metricVaR').innerHTML = `${formatPercent(data.var_95_percent)} <span style="font-size: 0.72rem; color: #94a3b8; font-weight: 500;">(Hist: ${formatPercent(histVarPct)})</span>`;
    document.getElementById('metricVaRAmount').innerHTML = `Parametric: ${formatINR(data.var_95_amount)} · <span style="color: #cbd5e1;">Hist Fat-Tail: ${formatINR(histVarAmt)}</span>`;

    document.getElementById('metricCVaR').innerHTML = `${formatPercent(data.cvar_95_percent)} <span style="font-size: 0.72rem; color: #94a3b8; font-weight: 500;">(Hist: ${formatPercent(histCVarPct)})</span>`;
    document.getElementById('metricCVaRAmount').innerHTML = `Parametric: ${formatINR(data.cvar_95_amount)} · <span style="color: #cbd5e1;">Hist Fat-Tail: ${formatINR(histCVarAmt)}</span>`;
  } catch (err) {
    console.error('Error calculating metrics', err);
  }
}

// Trigger Scenario Shock API
async function triggerShock(isCustom = false) {
  try {
    const body = {
      capital: STATE.capital,
      weights: STATE.weights,
    };
    if (isCustom || STATE.activeScenarioId === 'custom') {
      STATE.activeScenarioId = 'custom';
      body.custom_shocks = STATE.customShocks;
    } else {
      body.scenario_id = STATE.activeScenarioId;
    }

    const res = await fetch(`${API_BASE}/api/shock`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    STATE.shockResult = data;

    document.getElementById('resBaselineVal').textContent = formatINR(data.baseline_capital);
    document.getElementById('resStressedVal').textContent = formatINR(data.stressed_capital);

    const pnlValEl = document.getElementById('resPnlVal');
    const pnlPctEl = document.getElementById('resPnlPct');
    const isGain = data.total_pnl >= 0;

    pnlValEl.textContent = `${isGain ? '+' : ''}${formatINR(data.total_pnl)}`;
    pnlValEl.className = `main-val pnl-val ${isGain ? 'gain' : 'loss'}`;

    pnlPctEl.textContent = `${isGain ? '+' : ''}${data.pnl_percent.toFixed(2)}%`;
    pnlPctEl.className = `pnl-pct-badge ${isGain ? 'gain' : 'loss'}`;

    // Render Table
    const tbody = document.getElementById('shockTableBody');
    tbody.innerHTML = '';
    data.asset_breakdown.forEach(item => {
      const row = document.createElement('tr');
      const itemGain = item.pnl >= 0;
      row.innerHTML = `
        <td style="font-weight: 600;">
          <span class="asset-color-dot" style="display:inline-block; background-color:${item.color}; margin-right:6px;"></span>
          ${item.name}
        </td>
        <td>${item.category}</td>
        <td>${(item.base_weight * 100).toFixed(0)}%</td>
        <td>${formatINR(item.baseline_value)}</td>
        <td style="color: ${item.shock_percent >= 0 ? '#10b981' : '#f43f5e'}; font-weight:700;">
          ${item.shock_percent >= 0 ? '+' : ''}${item.shock_percent}%
        </td>
        <td>${formatINR(item.stressed_value)}</td>
        <td style="color: ${itemGain ? '#10b981' : '#f43f5e'}; font-weight:700;">
          ${itemGain ? '+' : ''}${formatINR(item.pnl)}
        </td>
        <td>${(item.post_shock_weight * 100).toFixed(1)}%</td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    console.error('Error applying market shock', err);
  }
}

// Trigger Monte Carlo Simulation
async function triggerMonteCarlo() {
  const numSims = parseInt(document.getElementById('simCountSelect').value, 10);
  const horizon = parseInt(document.getElementById('simHorizonSelect').value, 10);
  const btn = document.getElementById('runSimBtn');
  btn.textContent = 'Simulating...';

  try {
    const res = await fetch(`${API_BASE}/api/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        capital: STATE.capital,
        weights: STATE.weights,
        num_simulations: numSims,
        time_horizon_days: horizon,
      }),
    });
    const data = await res.json();
    STATE.simResult = data;

    document.getElementById('simProbPreservation').textContent = `${(data.probability_of_preservation * 100).toFixed(1)}%`;
    document.getElementById('simMedianOutcome').textContent = formatINR(data.terminal_outcomes.median);
    document.getElementById('simP5Outcome').textContent = formatINR(data.terminal_outcomes.percentile_5);
    document.getElementById('simP95Outcome').textContent = formatINR(data.terminal_outcomes.percentile_95);

    renderMonteCarloCanvas(data);
  } catch (err) {
    console.error('Simulation failed', err);
  } finally {
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Run Correlated Simulation`;
  }
}

// Render Monte Carlo Canvas
function renderMonteCarloCanvas(data) {
  const canvas = document.getElementById('mcCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const w = rect.width > 50 ? rect.width : (canvas.parentElement?.clientWidth || 860);

  canvas.width = w * dpr;
  canvas.height = 420 * dpr;
  ctx.scale(dpr, dpr);

  const h = 420;
  ctx.clearRect(0, 0, w, h);

  const padLeft = 85;
  const padRight = 35;
  const padTop = 25;
  const padBottom = 40;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const fan = data.fan_chart;
  const p5 = fan.p5;
  const p25 = fan.p25;
  const p50 = fan.p50_median;
  const p75 = fan.p75;
  const p95 = fan.p95;
  const steps = p50.length;
  const months = data.time_points_months;

  let minVal = Math.min(...p5) * 0.95;
  let maxVal = Math.max(...p95) * 1.05;
  if (minVal >= maxVal) maxVal = minVal + 1000;

  const getX = (i) => padLeft + (i / (steps - 1)) * plotW;
  const getY = (val) => padTop + plotH - ((val - minVal) / (maxVal - minVal)) * plotH;

  // Grid lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.lineWidth = 1;
  const yTicks = 5;
  ctx.fillStyle = '#64748b';
  ctx.font = '500 11px "JetBrains Mono"';
  ctx.textAlign = 'right';

  for (let i = 0; i <= yTicks; i++) {
    const val = minVal + (i / yTicks) * (maxVal - minVal);
    const y = getY(val);
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(w - padRight, y);
    ctx.stroke();
    ctx.fillText(formatINR(val), padLeft - 12, y + 4);
  }

  // Baseline initial capital reference line
  const baseLineY = getY(STATE.capital);
  ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(padLeft, baseLineY);
  ctx.lineTo(w - padRight, baseLineY);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = '#38bdf8';
  ctx.textAlign = 'right';
  ctx.fillText('Initial Capital Ref', w - padRight - 6, baseLineY - 8);

  // X-axis ticks
  ctx.textAlign = 'center';
  ctx.fillStyle = '#94a3b8';
  for (let i = 0; i < steps; i += Math.max(1, Math.floor(steps / 6))) {
    const x = getX(i);
    ctx.fillText(`${months[i]}M`, x, h - padBottom + 22);
  }

  // Draw 5th-95th confidence shaded area
  ctx.fillStyle = 'rgba(56, 189, 248, 0.05)';
  ctx.beginPath();
  for (let i = 0; i < steps; i++) ctx.lineTo(getX(i), getY(p95[i]));
  for (let i = steps - 1; i >= 0; i--) ctx.lineTo(getX(i), getY(p5[i]));
  ctx.closePath();
  ctx.fill();

  // Draw 25th-75th confidence shaded area
  ctx.fillStyle = 'rgba(56, 189, 248, 0.10)';
  ctx.beginPath();
  for (let i = 0; i < steps; i++) ctx.lineTo(getX(i), getY(p75[i]));
  for (let i = steps - 1; i >= 0; i--) ctx.lineTo(getX(i), getY(p25[i]));
  ctx.closePath();
  ctx.fill();

  function drawChartLine(arr, strokeColor, lw = 1.5, dash = []) {
    ctx.save();
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = lw;
    if (dash.length > 0) ctx.setLineDash(dash);
    ctx.beginPath();
    for (let i = 0; i < steps; i++) {
      if (i === 0) ctx.moveTo(getX(i), getY(arr[i]));
      else ctx.lineTo(getX(i), getY(arr[i]));
    }
    ctx.stroke();
    ctx.restore();
  }

  drawChartLine(p95, '#3fb950', 1.5);
  drawChartLine(p75, '#38bdf8', 1.2, [4, 2]);
  drawChartLine(p50, '#e3b341', 2.2);
  drawChartLine(p25, '#fb923c', 1.2, [4, 2]);
  drawChartLine(p5, '#f85149', 1.5);
}

// Markowitz Efficient Frontier & Optimizer
async function triggerEfficientFrontier() {
  try {
    const res = await fetch(`${API_BASE}/api/efficient-frontier`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ weights: STATE.weights }),
    });
    if (!res.ok) return;
    const data = await res.json();
    STATE.frontierData = data;

    // Update Comparison Stats
    const curr = data.current_portfolio;
    const maxS = data.max_sharpe_portfolio;
    const minV = data.min_variance_portfolio;

    document.getElementById('frontierCurrentReturn').textContent = `${curr.return.toFixed(2)}% Return`;
    document.getElementById('frontierCurrentVol').textContent = `${curr.volatility.toFixed(2)}% Vol · Sharpe: ${curr.sharpe_ratio.toFixed(2)}`;

    document.getElementById('frontierMaxSharpeReturn').textContent = `${maxS.return.toFixed(2)}% Return`;
    document.getElementById('frontierMaxSharpeVol').textContent = `${maxS.volatility.toFixed(2)}% Vol · Sharpe: ${maxS.sharpe_ratio.toFixed(2)}`;

    document.getElementById('frontierMinVarReturn').textContent = `${minV.return.toFixed(2)}% Return`;
    document.getElementById('frontierMinVarVol').textContent = `${minV.volatility.toFixed(2)}% Vol · Sharpe: ${minV.sharpe_ratio.toFixed(2)}`;

    renderFrontierCanvas(data);
  } catch (err) {
    console.error('Error fetching efficient frontier', err);
  }
}

function setupFrontierButtons() {
  const maxSBtn = document.getElementById('applyMaxSharpeBtn');
  if (maxSBtn) {
    maxSBtn.addEventListener('click', () => {
      if (!STATE.frontierData?.max_sharpe_portfolio) return;
      applyOptimalWeights(STATE.frontierData.max_sharpe_portfolio.weights);
    });
  }

  const minVBtn = document.getElementById('applyMinVarBtn');
  if (minVBtn) {
    minVBtn.addEventListener('click', () => {
      if (!STATE.frontierData?.min_variance_portfolio) return;
      applyOptimalWeights(STATE.frontierData.min_variance_portfolio.weights);
    });
  }
}

function applyOptimalWeights(weightsMap) {
  STATE.assetOrder.forEach(aid => {
    STATE.weights[aid] = Math.round(weightsMap[aid] || 0);
  });
  renderAssetSliders();
  triggerAnalysis();
  triggerShock();
  triggerRiskDecomposition();
  triggerEfficientFrontier();
}

function renderFrontierCanvas(data) {
  const canvas = document.getElementById('frontierCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const w = rect.width > 50 ? rect.width : (canvas.parentElement?.clientWidth || 860);

  canvas.width = w * dpr;
  canvas.height = 420 * dpr;
  ctx.scale(dpr, dpr);

  const h = 420;
  ctx.clearRect(0, 0, w, h);

  const padLeft = 70;
  const padRight = 40;
  const padTop = 30;
  const padBottom = 45;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const points = data.frontier_curve || [];
  if (points.length === 0) return;

  const minVol = 0;
  const maxVol = Math.max(...points.map(p => p.volatility), data.current_portfolio.volatility, 30) * 1.15;
  const minRet = 4.0;
  const maxRet = Math.max(...points.map(p => p.return), data.max_sharpe_portfolio.return, 18) * 1.15;

  const getX = (vol) => padLeft + ((vol - minVol) / (maxVol - minVol)) * plotW;
  const getY = (ret) => padTop + plotH - ((ret - minRet) / (maxRet - minRet)) * plotH;

  // Grid
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.lineWidth = 1;
  ctx.fillStyle = '#64748b';
  ctx.font = '500 11px "JetBrains Mono"';
  ctx.textAlign = 'right';

  for (let i = 0; i <= 5; i++) {
    const retVal = minRet + (i / 5) * (maxRet - minRet);
    const y = getY(retVal);
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(w - padRight, y);
    ctx.stroke();
    ctx.fillText(`${retVal.toFixed(1)}%`, padLeft - 10, y + 4);
  }

  ctx.textAlign = 'center';
  for (let i = 0; i <= 6; i++) {
    const volVal = minVol + (i / 6) * (maxVol - minVol);
    const x = getX(volVal);
    ctx.beginPath();
    ctx.moveTo(x, padTop);
    ctx.lineTo(x, h - padBottom);
    ctx.stroke();
    ctx.fillText(`${volVal.toFixed(0)}% σ`, x, h - padBottom + 20);
  }

  // Capital Allocation Line (CAL) from Rf (6.5%) through Max Sharpe
  const rf = 6.5;
  const maxS = data.max_sharpe_portfolio;
  ctx.save();
  ctx.strokeStyle = 'rgba(245, 158, 11, 0.35)';
  ctx.lineWidth = 1.5;
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(getX(0), getY(rf));
  const calSlope = (maxS.return - rf) / maxS.volatility;
  const calEndVol = maxVol;
  const calEndRet = rf + calSlope * calEndVol;
  ctx.lineTo(getX(calEndVol), getY(calEndRet));
  ctx.stroke();
  ctx.restore();

  // Draw Smooth Frontier Hyperbola
  ctx.save();
  ctx.strokeStyle = '#818cf8';
  ctx.lineWidth = 3;
  ctx.beginPath();
  points.forEach((p, idx) => {
    const px = getX(p.volatility);
    const py = getY(p.return);
    if (idx === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();
  ctx.restore();

  // Draw Point Markers
  function drawPoint(vol, ret, color, size, label, textColor) {
    const x = getX(vol);
    const y = getY(ret);

    ctx.save();
    ctx.fillStyle = color;
    ctx.shadowColor = color;
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.arc(x, y, size, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    ctx.fillStyle = textColor || color;
    ctx.font = '700 11px "JetBrains Mono"';
    ctx.textAlign = 'left';
    ctx.fillText(` ${label}`, x + size + 3, y + 4);
  }

  const curr = data.current_portfolio;
  const minV = data.min_variance_portfolio;

  drawPoint(minV.volatility, minV.return, '#10b981', 6, `Min Var (${minV.volatility.toFixed(1)}%)`);
  drawPoint(maxS.volatility, maxS.return, '#f59e0b', 7, `Max Sharpe (SR: ${maxS.sharpe_ratio.toFixed(2)})`);
  drawPoint(curr.volatility, curr.return, '#38bdf8', 6, `Current (${curr.volatility.toFixed(1)}%)`);
}

// Euler Risk Decomposition (MCR)
async function triggerRiskDecomposition() {
  try {
    const res = await fetch(`${API_BASE}/api/risk-decomposition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        capital: STATE.capital,
        weights: STATE.weights,
      }),
    });
    if (!res.ok) return;
    const data = await res.json();
    STATE.riskDecomp = data;

    // Render Table Rows
    const tbody = document.getElementById('riskDecompTableBody');
    if (tbody) {
      tbody.innerHTML = '';
      data.assets_risk_decomposition.forEach(item => {
        const row = document.createElement('tr');
        const ratio = item.risk_budget_ratio;
        const ratioClass = ratio > 1.3 ? 'danger' : ratio < 0.8 ? 'safe' : 'neutral';

        row.innerHTML = `
          <td><strong>${item.name}</strong></td>
          <td>${item.category}</td>
          <td style="font-family: var(--font-mono);">${item.weight_pct.toFixed(1)}%</td>
          <td>${formatINR(item.allocated_capital)}</td>
          <td style="font-family: var(--font-mono); color: var(--accent-cyan); font-weight:600;">${((item.marginal_risk_contrib || 0) * 100).toFixed(2)}%</td>
          <td style="font-family: var(--font-mono); color: ${item.pct_risk_contrib > item.weight_pct ? '#f85149' : '#3fb950'}; font-weight:700;">
            ${item.pct_risk_contrib.toFixed(1)}%
          </td>
          <td><span class="risk-ratio-badge ${ratioClass}">${ratio.toFixed(2)}x</span></td>
        `;
        tbody.appendChild(row);
      });
    }

    // Render Visual Risk vs. Capital Bars
    const barsContainer = document.getElementById('riskBarsContainer');
    if (barsContainer) {
      barsContainer.innerHTML = '';
      data.assets_risk_decomposition.forEach(item => {
        if (item.weight_pct <= 0 && item.pct_risk_contrib <= 0) return;
        const row = document.createElement('div');
        row.className = 'risk-bar-row';
        const ratio = item.risk_budget_ratio;
        const isTrap = ratio > 1.3 && item.pct_risk_contrib > 15;

        row.innerHTML = `
          <div class="risk-bar-name">
            <span class="asset-color-dot" style="background:${STATE.assets[item.asset_id]?.color || '#3b82f6'};"></span>
            ${item.name}
          </div>
          <div class="risk-bar-track-wrap">
            <div class="dual-bar-track" title="Capital Weight: ${item.weight_pct.toFixed(1)}%">
              <div class="dual-bar-fill capital-fill" style="width: ${Math.min(100, item.weight_pct * 2)}%;"></div>
            </div>
            <div class="dual-bar-track" title="Risk Contribution: ${item.pct_risk_contrib.toFixed(1)}%">
              <div class="dual-bar-fill risk-fill" style="width: ${Math.min(100, item.pct_risk_contrib * 2)}%;"></div>
            </div>
            <div class="risk-bar-labels">
              <span>Capital: ${item.weight_pct.toFixed(1)}%</span>
              <span style="color: ${item.pct_risk_contrib > item.weight_pct ? '#f85149' : '#3fb950'}">Risk: ${item.pct_risk_contrib.toFixed(1)}%</span>
            </div>
          </div>
          <div style="text-align: right;">
            <span class="risk-ratio-badge ${isTrap ? 'danger' : ratio < 0.8 ? 'safe' : 'neutral'}">
              ${ratio.toFixed(2)}x ${isTrap ? 'OVERWEIGHT' : ''}
            </span>
          </div>
        `;
        barsContainer.appendChild(row);
      });
    }
  } catch (err) {
    console.error('Error calculating risk decomposition', err);
  }
}

// Render Correlation Matrix Heatmap
function renderCorrelationMatrix() {
  const table = document.getElementById('corrTable');
  if (!table) return;
  table.innerHTML = '';

  const header = document.createElement('thead');
  let headRow = '<tr><th>Asset Class</th>';
  STATE.assetOrder.forEach(aid => {
    headRow += `<th>${STATE.assets[aid]?.name.split(' ')[0]}</th>`;
  });
  headRow += '</tr>';
  header.innerHTML = headRow;
  table.appendChild(header);

  const tbody = document.createElement('tbody');
  STATE.assetOrder.forEach((aidI, i) => {
    const row = document.createElement('tr');
    let cells = `<td style="font-weight:600; white-space:nowrap;">${STATE.assets[aidI]?.name}</td>`;
    STATE.assetOrder.forEach((aidJ, j) => {
      const val = STATE.correlationMatrix[i][j];
      let heatClass = 'heat-zero';
      if (val === 1.0) heatClass = 'heat-pos-high';
      else if (val < -0.1) heatClass = 'heat-neg-high';
      else if (val < 0.05) heatClass = 'heat-neg-med';
      else if (val < 0.3) heatClass = 'heat-zero';
      else if (val < 0.6) heatClass = 'heat-pos-low';
      else heatClass = 'heat-pos-med';

      cells += `<td class="matrix-cell ${heatClass}">${val.toFixed(2)}</td>`;
    });
    row.innerHTML = cells;
    tbody.appendChild(row);
  });
  table.appendChild(tbody);
}

// Executive Tear-Sheet Modal & Generator
function setupTearsheetModal() {
  const genBtn = document.getElementById('generateTearsheetBtn');
  const modal = document.getElementById('tearsheetModal');
  const closeBtn = document.getElementById('closeTearsheetModal');
  const iframe = document.getElementById('tearsheetIframe');
  const downloadLink = document.getElementById('tearsheetDownloadBtn');
  const printBtn = document.getElementById('tearsheetPrintBtn');

  if (genBtn) {
    genBtn.addEventListener('click', async () => {
      genBtn.textContent = 'Compiling...';
      try {
        const payload = {
          title: `${STATE.scenarios[STATE.activeScenarioId]?.name || 'Portfolio'} Risk Tear-Sheet`,
          capital: STATE.capital,
          metrics: STATE.metrics || {},
          risk_decomp: STATE.riskDecomp || {},
          shock_result: STATE.shockResult || {},
          notes: `Evaluated across ${STATE.assetOrder.length} institutional asset classes with 95% 1-Year Value-at-Risk parameters.`,
        };

        const res = await fetch(`${API_BASE}/api/generate-tearsheet`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (iframe) iframe.srcdoc = data.html_content;
        if (downloadLink) downloadLink.href = data.url || '#';
        document.getElementById('tearsheetModalSubtitle').textContent = `Report ID: ${data.report_id} · Exported to ${data.exported_to}`;
        modal.classList.add('open');
      } catch (err) {
        alert('Failed to generate executive tear-sheet: ' + err.message);
      } finally {
        genBtn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg> Tear-Sheet (S3)`;
      }
    });
  }

  if (closeBtn) closeBtn.addEventListener('click', () => modal.classList.remove('open'));
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('open');
    });
  }
  if (printBtn) {
    printBtn.addEventListener('click', () => {
      if (iframe?.contentWindow) iframe.contentWindow.print();
    });
  }
}

// Experiments Persistence
async function setupSaveExperimentButton() {
  document.getElementById('saveExpBtn').addEventListener('click', async () => {
    const defaultTitle = `${STATE.scenarios[STATE.activeScenarioId]?.name || 'Scenario'} Stress Run`;
    const title = prompt('Enter a name for this experiment:', defaultTitle);
    if (!title) return;

    try {
      const payload = {
        title,
        capital: STATE.capital,
        weights: STATE.weights,
        scenario_id: STATE.activeScenarioId,
        metrics: STATE.metrics,
        pnl: STATE.shockResult?.total_pnl,
        pnl_percent: STATE.shockResult?.pnl_percent,
      };

      const res = await fetch(`${API_BASE}/api/experiments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        await refreshSavedExperiments();
        alert('Experiment saved to Amazon DynamoDB / Local Registry successfully.');
      }
    } catch (err) {
      alert('Failed to save experiment: ' + err.message);
    }
  });
}

// Send SNS Alert
function setupSendAlertButton() {
  document.getElementById('sendAlertBtn').addEventListener('click', async () => {
    const scName = STATE.scenarios[STATE.activeScenarioId]?.name || 'Custom Crisis';
    const pnlPct = STATE.shockResult ? STATE.shockResult.pnl_percent : -12.5;
    const varPct = STATE.metrics ? STATE.metrics.var_95_percent : 14.8;

    try {
      const res = await fetch(`${API_BASE}/api/send-alert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `${scName} Risk Event`,
          pnl_percent: pnlPct,
          var_95_percent: varPct,
        }),
      });
      const data = await res.json();
      alert(`[Amazon SNS Alert]\nStatus: ${data.status}\nSent to: ${data.sent_to}\n${data.topic_arn ? 'Topic: ' + data.topic_arn : ''}`);
    } catch (err) {
      alert('Failed to trigger SNS alert: ' + err.message);
    }
  });
}

// Export Quantitative Report to Amazon S3
function setupExportS3Button() {
  document.getElementById('exportS3Btn').addEventListener('click', async () => {
    const scName = STATE.scenarios[STATE.activeScenarioId]?.name || 'Portfolio';
    const btn = document.getElementById('exportS3Btn');
    btn.textContent = 'Exporting...';

    try {
      const payload = {
        title: `${scName}_Stress_Report`,
        capital: STATE.capital,
        weights: STATE.weights,
        scenario: STATE.scenarios[STATE.activeScenarioId],
        metrics: STATE.metrics,
        shock_result: STATE.shockResult,
      };

      const res = await fetch(`${API_BASE}/api/export-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      alert(`[Amazon S3 Export]\nDestination: ${data.exported_to}\nFile Key: ${data.file_key}\n${data.url ? 'URL: ' + data.url : ''}`);
    } catch (err) {
      alert('Failed to export to S3: ' + err.message);
    } finally {
      btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg> Export S3`;
    }
  });
}

async function refreshSavedExperiments() {
  try {
    const res = await fetch(`${API_BASE}/api/experiments`);
    if (!res.ok) return;
    const data = await res.json();
    const list = document.getElementById('experimentsList');
    const badge = document.getElementById('expCountBadge');
    badge.textContent = data.count || 0;

    if (!data.experiments || data.experiments.length === 0) {
      list.innerHTML = '<div class="empty-state">No saved experiments yet. Run a shock and click "Save Experiment".</div>';
      return;
    }

    list.innerHTML = '';
    data.experiments.forEach(exp => {
      const item = document.createElement('div');
      item.className = 'exp-item';
      item.innerHTML = `
        <div>
          <div class="exp-title">${exp.title}</div>
          <div class="exp-date">${new Date(exp.created_at).toLocaleDateString()} · ${formatINR(exp.capital)}</div>
        </div>
        <span class="chip-btn">Load</span>
      `;
      item.addEventListener('click', () => loadExperiment(exp));
      list.appendChild(item);
    });
  } catch (err) {
    console.warn('Could not refresh experiments', err);
  }
}

function loadExperiment(exp) {
  STATE.capital = exp.capital || 1000000;
  document.getElementById('capitalInput').value = STATE.capital;
  if (exp.weights) {
    STATE.weights = { ...exp.weights };
    renderAssetSliders();
  }
  if (exp.scenario_id && STATE.scenarios[exp.scenario_id]) {
    STATE.activeScenarioId = exp.scenario_id;
    document.querySelectorAll('.scenario-card').forEach(c => {
      c.classList.toggle('active', c.dataset.scid === exp.scenario_id);
    });
  }
  triggerAnalysis();
  triggerShock();
  triggerRiskDecomposition();
  triggerEfficientFrontier();
}

// UI Tabs Setup
function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      const targetId = btn.dataset.tab;
      document.getElementById(targetId).classList.add('active');

      if (targetId === 'tab-monte-carlo' && STATE.simResult) {
        renderMonteCarloCanvas(STATE.simResult);
      } else if (targetId === 'tab-frontier') {
        triggerEfficientFrontier();
      } else if (targetId === 'tab-risk-decomp') {
        triggerRiskDecomposition();
      }
    });
  });
}

function setupAwsModal() {
  const badge = document.getElementById('awsStatusBadge');
  const modal = document.getElementById('awsModal');
  const close = document.getElementById('closeAwsModal');
  badge.addEventListener('click', () => modal.classList.add('open'));
  close.addEventListener('click', () => modal.classList.remove('open'));
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('open');
  });
}

function setupCapitalControls() {
  const input = document.getElementById('capitalInput');
  input.addEventListener('change', (e) => {
    STATE.capital = parseFloat(e.target.value) || 1000000;
    triggerAnalysis();
    triggerShock();
    triggerRiskDecomposition();
  });

  document.querySelectorAll('.capital-quick-tags .chip-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.capital-quick-tags .chip-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      STATE.capital = parseFloat(btn.dataset.capital);
      input.value = STATE.capital;
      triggerAnalysis();
      triggerShock();
      triggerRiskDecomposition();
    });
  });
}

function setupPresetButtons() {
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const presetKey = btn.dataset.preset;
      const presetWeights = PRESETS[presetKey];
      if (presetWeights) {
        STATE.weights = { ...presetWeights };
        renderAssetSliders();
        triggerAnalysis();
        triggerShock();
        triggerRiskDecomposition();
        triggerEfficientFrontier();
      }
    });
  });
}

function setupSimulateButton() {
  document.getElementById('runSimBtn').addEventListener('click', triggerMonteCarlo);
}

function debounce(fn, ms) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), ms);
  };
}

// Start app on DOMContentLoaded
window.addEventListener('DOMContentLoaded', init);
