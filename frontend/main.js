// central client-side logic for DavaoBuild AI dashboard

// ========== CONFIGURATION ==========
// Base URL for API calls - automatically detect running environment.
// If you're serving the frontend from GitHub Pages (or another host),
// set PRODUCTION_API_URL to your deployed backend and comment out the
// local detection line below.
const PRODUCTION_API_URL = 'https://davaobuildai.onrender.com'; // <-- updated to match deployed backend
const API_BASE_URL = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost')
    ? 'http://127.0.0.1:5000'
    : PRODUCTION_API_URL;
// You can also hardcode the URL directly if you prefer:
// const API_BASE_URL = 'https://davao-build-api.onrender.com';


let priceChart = null;

// ========== UTILITY FUNCTIONS ==========
// Format numbers with thousand separators (1,234.56)
function formatCurrency(num) {
    if (num === null || num === undefined) return "₱0.00";
    return "₱" + parseFloat(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatNumber(num) {
    if (num === null || num === undefined) return "0.00";
    return parseFloat(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// helper for displaying toasts (used by various actions)
function dummyAction(msg) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.innerText = msg;
    t.style.display = 'block';
    setTimeout(() => (t.style.display = 'none'), 3000);
}

// ---------- prediction logic ----------
async function generatePrediction() {
    const material = document.getElementById('materialSelector').value;
    showLoading();
    hideError();
    try {
        // API_BASE_URL resolves to localhost during development
        // or to the production Render URL when deployed.
        const res = await fetch(`${API_BASE_URL}/predict/${material}`);
        if (!res.ok) throw new Error('network');
        const data = await res.json();

        document.getElementById('predictionCurrent').innerText = formatCurrency(data.current_price);
        document.getElementById('prediction7day').innerText = formatCurrency(data.pred_7d);
        document.getElementById('prediction30day').innerText = formatCurrency(data.pred_30d);
        const trendLabel = data.trend === 'up' ? '⬆ Increasing' : data.trend === 'down' ? '⬇ Decreasing' : '➡ Stable';
        document.getElementById('predictionTrend').innerText = trendLabel;
        document.getElementById('predictionConfidence').innerText = `${formatCurrency(data.confidence_min)} – ${formatCurrency(data.confidence_max)}`;

        // confidence meter
        const pct = data.confidence_pct || 0;
        const bar = document.getElementById('confidenceBar');
        bar.style.width = pct + '%';
        bar.innerText = pct + '%';

        updateChart(data.historical_dates, data.historical_prices, data.forecast_prices);
        // explanation or rationale
        if(data.explanation) {
            const expEl = document.getElementById('predictionExplanation');
            if(expEl) expEl.innerText = data.explanation;
        }
        document.getElementById('predictionResults').style.display = 'block';
    } catch (err) {
        console.error(err);
        showError();
    } finally {
        hideLoading();
    }
}

function showLoading() {
    const el = document.getElementById('loadingIndicator');
    if (el) el.style.display = 'block';
}
function hideLoading() {
    const el = document.getElementById('loadingIndicator');
    if (el) el.style.display = 'none';
}
function showError() {
    const el = document.getElementById('predictionError');
    if (el) el.style.display = 'block';
}
function hideError() {
    const el = document.getElementById('predictionError');
    if (el) el.style.display = 'none';
}

// ---------- chart helpers ----------
function initializeChart() {
    const ctx = document.getElementById('priceChart').getContext('2d');
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Historical',
                    data: [],
                    borderColor: getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim(),
                    fill: false,
                },
                {
                    label: 'AI Forecast',
                    data: [],
                    borderColor: getComputedStyle(document.documentElement).getPropertyValue('--accent-color').trim(),
                    borderDash: [5, 5],
                    fill: false,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { display: true },
                y: { beginAtZero: false },
            },
        },
    });
}

function updateChart(labels, hist, forecast) {
    if (!priceChart) initializeChart();
    priceChart.data.labels = labels;
    priceChart.data.datasets[0].data = hist;
    priceChart.data.datasets[1].data = forecast;
    priceChart.update();
}

// ---------- market insight ----------
async function fetchMarketInsight(material) {
    try {
        const res = await fetch(`${API_BASE_URL}/market-insight/${material}`);
        if (!res.ok) throw new Error('network');
        const data = await res.json();
        document.getElementById('marketRiskLevel').innerText = data.risk;
        document.getElementById('marketSentiment').innerText = data.sentiment;
        // Format the main insight with better readability
        let insightText = data.insight || "No data available";
        // Clean up the text and add bullets if multiple insights
        if (data.all_insights && Array.isArray(data.all_insights)) {
            insightText = "• " + data.all_insights.slice(0, 2).join("\n• ");
        }
        document.getElementById('marketInsightText').innerText = insightText;
    } catch (e) {
        console.error(e);
    }
}

// ---------- estimator ----------
async function runEstimator() {
    const payload = {
        project_type: document.getElementById('proj-type').value,
        material: document.getElementById('est-material').value,
        quantity: parseFloat(document.getElementById('est-qty').value) || 0,
        location: document.getElementById('est-location').value,
        timeline: parseFloat(document.getElementById('est-timeline').value) || 0,
    };
    try {
        const res = await fetch(`${API_BASE_URL}/estimate`, {
            method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const result = await res.json();
        document.getElementById('estimateCurrentCost').innerText = formatCurrency(result.current_cost);
        document.getElementById('estimatePredictedCost').innerText = formatCurrency(result.predicted_cost);
        document.getElementById('estimateRecommendation').innerText = result.recommendation;
        document.getElementById('estimateConfidence').innerText = `Confidence: ${result.confidence_pct}%`;
        document.getElementById('estResults').style.display = 'grid';
    } catch (e) {
        console.error('Estimate error:', e);
    }
}

// ---------- materials viewer ----------
async function fetchMaterials() {
    try {
        // Try to fetch today's data first, fallback to regular materials endpoint
        const endpoint = `${API_BASE_URL}/materials-today`;
        const res = await fetch(endpoint).catch(() => fetch(`${API_BASE_URL}/materials`));
        const list = await res.json();
        const tbody = document.getElementById('materialsBody');
        tbody.innerHTML = '';
        list.forEach((m) => {
            const tr = document.createElement('tr');
            const name = m.name || m.name;
            const price = formatCurrency(m.price);
            const updated = m.updated || new Date().toISOString().split('T')[0];
            tr.innerHTML = `<td style="padding:0.8rem;border-bottom:1px solid #eee;">${name}</td>
                <td style="padding:0.8rem;border-bottom:1px solid #eee;">${price}</td>
                <td style="padding:0.8rem;border-bottom:1px solid #eee;">${updated}</td>`;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error(e);
    }
}

// ---------- footer data ----------
async function fetchFooterData() {
    try {
        const res = await fetch(`${API_BASE_URL}/footer-data`);
        const data = await res.json();
        document.getElementById('footerDiesel').innerText = `${data.diesel_currency}${formatNumber(data.diesel_price)}`;
        document.getElementById('footerExchange').innerText = `${data.exchange_currency} ${formatNumber(data.exchange_rate)}`;
        document.getElementById('footerInflation').innerText = `${data.regional_inflation}%`;
        document.getElementById('footerStatus').innerText = data.system_status;
    } catch (e) {
        console.error('Footer data fetch error:', e);
        // Keep default values if fetch fails
    }
}

// ---------- bootstrap listeners ----------
document.addEventListener('DOMContentLoaded', () => {
    // prediction controls
    const predictBtn = document.getElementById('predictBtn');
    if (predictBtn) predictBtn.addEventListener('click', generatePrediction);
    const selector = document.getElementById('materialSelector');
    if (selector) {
        selector.addEventListener('change', () => fetchMarketInsight(selector.value));
        // load market insight for default material
        fetchMarketInsight(selector.value);
    }
    // estimator
    const estimateBtn = document.getElementById('estimateBtn');
    if (estimateBtn) estimateBtn.addEventListener('click', runEstimator);
    // other
    fetchMaterials();
    fetchFooterData();
    initializeChart();
    // trigger a default prediction so the panel is filled immediately
    generatePrediction();
});

// ---------- navigation & mobile menu helpers ----------
function navigateTo(pageId) {
    // Try to navigate to a full page first (pages have ids like `page-<name>`)
    const pageEl = document.getElementById('page-' + pageId);
    if (pageEl) {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        pageEl.classList.add('active');
        document.querySelectorAll('.nav__links .link a').forEach(a => a.classList.remove('active'));
        const activeLink = document.getElementById('link-' + pageId);
        if (activeLink) activeLink.classList.add('active');
        if (pageId === 'forecast' || pageId === 'forecastChart') {
            setTimeout(initChart, 100);
        }
        window.scrollTo(0, 0);
        return;
    }

    // If no full page, map legacy nav targets to section IDs and scroll there
    const mapping = {
        'prediction-panel': 'ai-prediction',
        'market-analysis': 'market-insight',
        'estimator': 'ai-estimator',
        'prices': 'material-table',
        'home': 'page-home'
    };
    const targetId = mapping[pageId] || pageId;
    const sectionEl = document.getElementById(targetId);
    if (sectionEl) {
        sectionEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // update active link styles
        document.querySelectorAll('.nav__links .link a').forEach(a => a.classList.remove('active'));
        // try to set the clicked link active by matching the onclick attribute
        const links = document.querySelectorAll('.nav__links .link a');
        links.forEach(a => {
            const onclick = a.getAttribute('onclick') || '';
            if (onclick.includes(pageId) || onclick.includes(targetId)) a.classList.add('active');
        });
    }
}

function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    const overlay = document.getElementById('overlay');
    if (menu.classList.contains('open')) {
        menu.classList.remove('open');
        overlay.style.display = 'none';
    } else {
        menu.classList.add('open');
        overlay.style.display = 'block';
    }
}

// helper for smooth scrolling to sections
function scrollToSection(id) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
}

document.addEventListener('DOMContentLoaded', () => {
    // navigate to dashboard on load
    navigateTo('home');
});