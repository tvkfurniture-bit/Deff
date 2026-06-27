"""
QuantX v4 — Elite F&O Intelligence Terminal
============================================
Pure pandas/numpy indicators (no pandas-ta) — Python 3.11 compatible.
Deploy on Streamlit Cloud with .python-version pinned to 3.11.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, time
import pytz
import warnings
warnings.filterwarnings("ignore")

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════════════
# TIMEZONE & MARKET TIME DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════
IST = pytz.timezone('Asia/Kolkata')

def market_status() -> tuple[bool, str, str]:
    """Calculates true market status based on IST timezone."""
    now_ist = datetime.now(IST)
    current_time = now_ist.time()
    
    market_open = time(9, 15)
    market_close = time(15, 30)
    is_weekday = now_ist.weekday() < 5
    
    if not is_weekday:
        status = "WEEKEND"
        is_live = False
    elif current_time < market_open:
        status = "PRE-MARKET"
        is_live = False
    elif current_time > market_close:
        status = "POST-MARKET"
        is_live = False
    else:
        status = "LIVE"
        is_live = True
        
    time_str = now_ist.strftime("%d %b %Y  %H:%M:%S")
    return is_live, status, time_str

is_open, mkt_regime_label, ts_now = market_status()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="QuantX · F&O Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# STATE INITIALIZATION (Ensures auto-refresh does not clear selections)
# ══════════════════════════════════════════════════════════════════════════════
if "selected_label" not in st.session_state:
    st.session_state.selected_label = "NIFTY 50"
if "tf_label" not in st.session_state:
    st.session_state.tf_label = "5m"
if "capital" not in st.session_state:
    st.session_state.capital = 500000
if "risk_pct" not in st.session_state:
    st.session_state.risk_pct = 1.0
if "trade_log" not in st.session_state:
    st.session_state.trade_log = []

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — Adaptive Theme Layout CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* ── Reset & base ─────────────────────────────────────────────────────────── */
html, body, [class*="css"], .stApp {
  font-family: 'Inter', sans-serif;
}

/* Scanline texture — adaptive overlay */
.stApp::before {
  content: '';
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(120,120,120,0.01) 2px,
    rgba(120,120,120,0.01) 4px
  );
  pointer-events: none;
  z-index: 0;
}

/* ── Chrome suppression ───────────────────────────────────────────────────── */
#MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {
  display: none !important;
}
header[data-testid="stHeader"] {
  background: transparent !important;
  height: 0 !important;
}

.block-container {
  padding: 1rem 1rem 3rem 1rem !important;
  max-width: 100% !important;
}

/* ── Sidebar styling ──────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  border-right: 1px solid rgba(120, 120, 120, 0.15) !important;
  padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child {
  padding-top: 1.5rem;
}

/* ── Tab styling ──────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid rgba(120, 120, 120, 0.15) !important;
  gap: 0 !important;
  padding: 0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
  background: transparent !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.72rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
  padding: 0.7rem 1rem !important;
  transition: all 0.2s !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
  color: #00E676 !important;
  border-bottom: 2px solid #00E676 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
  background: rgba(120, 120, 120, 0.05) !important;
}
[data-testid="stTabPanel"] {
  padding-top: 1rem !important;
  background: transparent !important;
}

/* ── Plotly charts ────────────────────────────────────────────────────────── */
.js-plotly-plot, .plotly, .plot-container {
  border-radius: 12px !important;
  overflow: hidden !important;
}

/* ── Streamlit dataframe ──────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
  border: 1px solid rgba(120, 120, 120, 0.15) !important;
  border-radius: 10px !important;
  overflow: hidden !important;
}

/* ── Spinner ──────────────────────────────────────────────────────────────── */
[data-testid="stSpinner"] { color: #00E676 !important; }

/* ── Alerts ───────────────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
  background: rgba(255,75,75,0.08) !important;
  border: 1px solid rgba(255,75,75,0.25) !important;
  border-radius: 10px !important;
  color: #FF6B6B !important;
}

/* ════════════════════════════════════════════════════════════════════════════
   CUSTOM THEME ADAPTIVE COMPONENTS
   ════════════════════════════════════════════════════════════════════════════ */

.qx-wordmark {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.55rem;
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1;
  margin-bottom: 0.1rem;
}
.qx-wordmark .acc { color: #00E676; text-shadow: 0 0 20px rgba(0,230,118,0.3); }
.qx-tagline {
  font-size: 0.6rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-weight: 500;
  margin-bottom: 1.8rem;
  opacity: 0.6;
}

.qx-section {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.58rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin: 1.4rem 0 0.7rem 0;
  opacity: 0.5;
}
.qx-section::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(120, 120, 120, 0.2);
}

.qx-dot {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  margin-right: 5px;
  vertical-align: middle;
  animation: qx-pulse 2s ease-in-out infinite;
}
@keyframes qx-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}

.qx-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 1.2rem;
  background: rgba(120, 120, 120, 0.05);
  border: 1px solid rgba(120, 120, 120, 0.15);
  border-radius: 12px;
  margin-bottom: 1rem;
  backdrop-filter: blur(20px);
}
.qx-header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.qx-header-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.qx-header-sub {
  font-size: 0.65rem;
  letter-spacing: 0.05em;
  margin-top: 0.1rem;
  opacity: 0.7;
}

.qx-chip {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.2rem 0.6rem;
  border-radius: 20px;
  letter-spacing: 0.05em;
}
.qx-chip-green {
  background: rgba(0,230,118,0.1);
  border: 1px solid rgba(0,230,118,0.3);
  color: #00E676;
}
.qx-chip-red {
  background: rgba(255,75,75,0.1);
  border: 1px solid rgba(255,75,75,0.3);
  color: #FF4B4B;
}
.qx-chip-amber {
  background: rgba(255,179,71,0.1);
  border: 1px solid rgba(255,179,71,0.3);
  color: #FFB347;
}
.qx-chip-gray {
  background: rgba(120,120,120,0.1);
  border: 1px solid rgba(120,120,120,0.2);
}

/* ── Responsive Flex Grid ────────────────────────────────────────────────── */
.qx-metrics-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  width: 100%;
  margin-bottom: 1rem;
}

.qx-card {
  flex: 1 1 150px;
  position: relative;
  background: rgba(120, 120, 120, 0.05);
  border: 1px solid rgba(120, 120, 120, 0.15);
  border-radius: 12px;
  padding: 1rem;
  overflow: hidden;
  transition: border-color 0.25s, box-shadow 0.25s;
}
.qx-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  opacity: 0.9;
}
.qx-card-green { border-color: rgba(0,230,118,0.15); }
.qx-card-green::before { background: linear-gradient(90deg, #00E676 0%, transparent 70%); }
.qx-card-green:hover { border-color: rgba(0,230,118,0.35); box-shadow: 0 0 24px rgba(0,230,118,0.06); }

.qx-card-red { border-color: rgba(255,61,0,0.15); }
.qx-card-red::before { background: linear-gradient(90deg, #FF3D00 0%, transparent 70%); }
.qx-card-red:hover { border-color: rgba(255,61,0,0.35); box-shadow: 0 0 24px rgba(255,61,0,0.06); }

.qx-card-blue { border-color: rgba(91,140,255,0.15); }
.qx-card-blue::before { background: linear-gradient(90deg, #5B8CFF 0%, transparent 70%); }
.qx-card-blue:hover { border-color: rgba(91,140,255,0.35); box-shadow: 0 0 24px rgba(91,140,255,0.06); }

.qx-card-amber { border-color: rgba(255,179,71,0.15); }
.qx-card-amber::before { background: linear-gradient(90deg, #FFB347 0%, transparent 70%); }
.qx-card-amber:hover { border-color: rgba(255,179,71,0.35); box-shadow: 0 0 24px rgba(255,179,71,0.06); }

.qx-card-neutral { border-color: rgba(120, 120, 120, 0.15); }
.qx-card-neutral::before { background: linear-gradient(90deg, rgba(120, 120, 120, 0.4) 0%, transparent 70%); }

.qx-card-label {
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  opacity: 0.6;
  margin-bottom: 0.4rem;
}
.qx-card-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.02em;
}
.qx-card-sub {
  font-size: 0.62rem;
  margin-top: 0.35rem;
  font-weight: 400;
  opacity: 0.8;
}
.qx-card-icon {
  position: absolute;
  top: 0.8rem;
  right: 0.8rem;
  font-size: 0.9rem;
  opacity: 0.15;
}

.clr-green  { color: #00E676 !important; }
.clr-red    { color: #FF3D00 !important; }
.clr-blue   { color: #5B8CFF !important; }
.clr-amber  { color: #FFB347 !important; }

/* ── Signal banner ────────────────────────────────────────────────────────── */
.qx-signal-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-radius: 14px;
  margin-bottom: 1.2rem;
  border: 1px solid;
  position: relative;
  overflow: hidden;
}
.qx-signal-banner::before {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0.04;
}
.qx-signal-banner.buy {
  border-color: rgba(0,230,118,0.35);
  background: rgba(0,230,118,0.05);
}
.qx-signal-banner.buy::before { background: #00E676; }
.qx-signal-banner.sell {
  border-color: rgba(255,61,0,0.35);
  background: rgba(255,61,0,0.05);
}
.qx-signal-banner.sell::before { background: #FF3D00; }
.qx-signal-banner.none {
  border-color: rgba(120, 120, 120, 0.2);
  background: rgba(120, 120, 120, 0.05);
}

.qx-signal-main {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.qx-signal-type {
  font-family: 'JetBrains Mono', monospace;
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1;
}
.qx-signal-meta {
  font-size: 0.72rem;
  line-height: 1.6;
  opacity: 0.9;
}

.qx-score-wrap {
  text-align: center;
}
.qx-score-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.6rem;
  font-weight: 700;
  line-height: 1;
}
.qx-score-label {
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  opacity: 0.6;
  margin-top: 0.2rem;
}

/* ── Regime badge ─────────────────────────────────────────────────────────── */
.qx-regime {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.28rem 0.75rem;
  border-radius: 20px;
}
.qx-regime-trend {
  background: rgba(0,230,118,0.08);
  border: 1px solid rgba(0,230,118,0.25);
  color: #00E676;
}
.qx-regime-chop {
  background: rgba(255,179,71,0.08);
  border: 1px solid rgba(255,179,71,0.25);
  color: #FFB347;
}
.qx-regime-vol {
  background: rgba(255,61,0,0.08);
  border: 1px solid rgba(255,61,0,0.25);
  color: #FF3D00;
}

/* ── Tables ───────────────────────────────────────────────────────────────── */
.qx-mtf-table, .qx-pivot-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
}
.qx-mtf-table th, .qx-pivot-table th {
  padding: 0.5rem 0.75rem;
  text-align: left;
  font-family: 'Inter', sans-serif;
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  opacity: 0.6;
  border-bottom: 1px solid rgba(120, 120, 120, 0.2);
}
.qx-mtf-table td, .qx-pivot-table td {
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid rgba(120, 120, 120, 0.1);
  vertical-align: middle;
}
.qx-mtf-table tr:last-child td, .qx-pivot-table tr:last-child td { border-bottom: none; }
.qx-mtf-table tr:hover td, .qx-pivot-table tr:hover td { background: rgba(120, 120, 120, 0.05); }

.qx-mtf-pill {
  display: inline-block;
  padding: 0.18rem 0.6rem;
  border-radius: 4px;
  font-size: 0.68rem;
  font-weight: 700;
}
.mtf-bull { background: rgba(0,230,118,0.1); color: #00E676; }
.mtf-bear { background: rgba(255,61,0,0.1); color: #FF3D00; }
.mtf-neut { background: rgba(120,120,120,0.1); }

.pv-r { color: #FF6B6B; font-weight: 600; }
.pv-s { color: #00E676; font-weight: 600; }
.pv-p { color: #5B8CFF; font-weight: 600; }
.pv-pos { color: #00E676; }
.pv-neg { color: #FF3D00; }

/* ── Trade logs ───────────────────────────────────────────────────────────── */
.qx-log-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: rgba(120,120,120,0.05);
  border: 1px solid rgba(120,120,120,0.15);
  border-radius: 10px;
  margin-bottom: 0.4rem;
  transition: border-color 0.2s;
}
.qx-log-entry:hover { border-color: rgba(120,120,120,0.3); }
.qx-log-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  opacity: 0.5;
}
.qx-log-idx {
  font-size: 0.65rem;
  font-weight: 600;
  opacity: 0.7;
  margin-top: 0.15rem;
}
.qx-log-price {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82rem;
  font-weight: 600;
}
.qx-log-levels {
  font-size: 0.62rem;
  opacity: 0.5;
  font-family: 'JetBrains Mono', monospace;
}
.qx-log-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.25rem 0.7rem;
  border-radius: 6px;
  letter-spacing: 0.06em;
}
.qx-log-badge.buy  { background: rgba(0,230,118,0.1); color: #00E676; border: 1px solid rgba(0,230,118,0.25); }
.qx-log-badge.sell { background: rgba(255,61,0,0.1); color: #FF3D00; border: 1px solid rgba(255,61,0,0.25); }

.qx-opt-card {
  background: rgba(120,120,120,0.05);
  border: 1px solid rgba(120,120,120,0.15);
  border-radius: 12px;
  padding: 1rem 1.2rem;
  margin-bottom: 0.5rem;
}
.qx-opt-header {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  opacity: 0.6;
  margin-bottom: 0.6rem;
}
.qx-opt-strike {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1;
}
.qx-opt-meta {
  font-size: 0.7rem;
  opacity: 0.7;
  margin-top: 0.35rem;
}

/* ── Kill switches ────────────────────────────────────────────────────────── */
.qx-ks-halted {
  background: rgba(255,61,0,0.06);
  border: 1px solid rgba(255,61,0,0.25);
  border-radius: 8px;
  padding: 0.55rem 0.9rem;
  font-size: 0.68rem;
  color: #FF3D00;
  text-align: center;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.qx-ks-active {
  background: rgba(0,230,118,0.05);
  border: 1px solid rgba(0,230,118,0.2);
  border-radius: 8px;
  padding: 0.55rem 0.9rem;
  font-size: 0.68rem;
  color: #00E676;
  text-align: center;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.qx-bt-stat {
  background: rgba(120,120,120,0.05);
  border: 1px solid rgba(120,120,120,0.15);
  border-radius: 10px;
  padding: 0.85rem 1rem;
  text-align: center;
}
.qx-bt-stat-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1;
}
.qx-bt-stat-lbl {
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  opacity: 0.6;
  margin-top: 0.3rem;
}

.qx-divider {
  border: none;
  border-top: 1px solid rgba(120, 120, 120, 0.2);
  margin: 1rem 0;
}

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(120,120,120,0.2); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,230,118,0.3); }

/* ── True Mobile CSS Media Queries ────────────────────────────────────────── */
@media (max-width: 768px) {
  .block-container {
    padding: 0.5rem 0.5rem 2rem 0.5rem !important;
  }
  .qx-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.6rem 0.8rem;
  }
  .qx-signal-banner {
    flex-direction: column;
    gap: 1rem;
    align-items: center;
    text-align: center;
    padding: 1rem;
  }
  .qx-signal-main {
    flex-direction: column;
    gap: 0.4rem;
  }
  .qx-opt-strike {
    font-size: 1.15rem;
  }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HTML RENDER HELPER (Ensures raw Markdown is not processed inside HTML)
# ══════════════════════════════════════════════════════════════════════════════
def render_html(html_str: str):
    """Safely collapse and output HTML strings to prevent Markdown code block bugs."""
    clean_html = " ".join(html_str.split())
    st.markdown(clean_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & CONFIG
# ══════════════════════════════════════════════════════════════════════════════
INDICES = {
    "NIFTY 50":    "^NSEI",
    "BANK NIFTY":  "^NSEBANK",
    "FIN NIFTY":   "^CNXFIN",
    "SENSEX":      "^BSESN",
    "BSE BANKEX":  "BSE-BANKEX.BO",
}

# Accurate dynamically aligned 2025/2026 Lot Sizes
LOT_SIZES = {
    "NIFTY 50":   25,
    "BANK NIFTY": 15,
    "FIN NIFTY":  25,
    "SENSEX":     10,
    "BSE BANKEX": 15,
}

STRIKE_GAPS = {
    "NIFTY 50":   50,
    "BANK NIFTY": 100,
    "FIN NIFTY":  50,
    "SENSEX":     100,
    "BSE BANKEX": 100,
}

TIMEFRAMES = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m"}
TF_PERIODS  = {"1m": "1d", "5m": "3d", "15m": "5d", "1h": "30d"}

SCORE_WEIGHTS = {
    "ema_cross":   25,
    "rsi_zone":    20,
    "vwap_side":   20,
    "bb_position": 15,
    "volume_conf": 10,
    "adx_trend":   10,
}

SIGNAL_THRESHOLD = 70

# ══════════════════════════════════════════════════════════════════════════════
# MATHEMATICALLY RESILIENT INDICATORS (Trap NaN, Inf, and Zero values)
# ══════════════════════════════════════════════════════════════════════════════
def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()

def _rsi(s: pd.Series, n: int = 14) -> pd.Series:
    try:
        d = s.diff()
        g = d.clip(lower=0)
        l = (-d).clip(lower=0)
        ag = g.ewm(com=n - 1, adjust=False).mean()
        al = l.ewm(com=n - 1, adjust=False).mean()
        
        # Division by zero protection (replace zeros with NaN then fill with 50)
        denom = al.replace(0, np.nan)
        rs = ag / denom
        rsi_series = 100 - (100 / (1 + rs))
        return rsi_series.fillna(50)
    except Exception:
        return pd.Series(50, index=s.index)

def _atr(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    try:
        if len(close) < n:
            return (high - low).rolling(window=max(1, len(close)), min_periods=1).mean().fillna(1.0)
        pc = close.shift(1)
        tr = pd.concat([(high - low), (high - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
        return tr.ewm(com=n - 1, adjust=False).mean().fillna(1.0)
    except Exception:
        return pd.Series(1.0, index=close.index)

def _vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    try:
        typical = (high + low + close) / 3
        vol_clean = volume.fillna(0)
        
        cum_tv = (typical * vol_clean).cumsum()
        cum_vol = vol_clean.cumsum()
        
        # Safe division for zero volume periods
        denom = cum_vol.replace(0, np.nan)
        vwap_series = cum_tv / denom
        return vwap_series.ffill().bfill().fillna(typical)
    except Exception:
        return (high + low + close) / 3

def _bbands(s: pd.Series, n: int = 20, std: float = 2.0):
    try:
        mid   = s.rolling(n).mean()
        sigma = s.rolling(n).std().fillna(0)
        return mid + std * sigma, mid, mid - std * sigma
    except Exception:
        return s, s, s

def _adx(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    try:
        up   = high.diff()
        down = -low.diff()
        plus_dm  = np.where((up > down) & (up > 0), up, 0.0)
        minus_dm = np.where((down > up) & (down > 0), down, 0.0)
        tr_s = _atr(high, low, close, n).replace(0, np.nan)
        
        plus_di  = 100 * pd.Series(plus_dm,  index=high.index).ewm(com=n-1, adjust=False).mean() / tr_s
        minus_di = 100 * pd.Series(minus_dm, index=high.index).ewm(com=n-1, adjust=False).mean() / tr_s
        plus_di  = plus_di.fillna(0)
        minus_di = minus_di.fillna(0)
        
        denom = (plus_di + minus_di).replace(0, np.nan)
        dx = (100 * (plus_di - minus_di).abs() / denom).fillna(0)
        adx_series = dx.ewm(com=n-1, adjust=False).mean()
        return adx_series.fillna(0), plus_di, minus_di
    except Exception:
        zero_series = pd.Series(0.0, index=close.index)
        return zero_series, zero_series, zero_series

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING (Holiday-Proof Daily Fallbacks)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=30, show_spinner=False)
def fetch_data(ticker: str, interval: str) -> pd.DataFrame:
    period = TF_PERIODS.get(interval, "5d")
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False)
        if df is None or df.empty:
            return pd.DataFrame()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df.dropna(inplace=True)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60, show_spinner=False)
def fetch_prev_day(ticker: str) -> dict:
    """Scans historical data back up to 12 days to capture holiday and weekend gaps."""
    try:
        df = yf.download(ticker, period="12d", interval="1d",
                         auto_adjust=True, progress=False)
        if df is None or df.empty or len(df) < 2:
            return {}
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        
        # Localize indices to ensure day boundaries are checked in IST timezone
        df.index = df.index.tz_localize('UTC').tz_convert(IST) if df.index.tz is None else df.index.tz_convert(IST)
        
        # Take daily candle prior to today's date
        today_ist = datetime.now(IST).date()
        valid_rows = df[df.index.date < today_ist]
        
        if valid_rows.empty:
            r = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
        else:
            r = valid_rows.iloc[-1]
            
        return {"high": float(r["High"]), "low": float(r["Low"]), "close": float(r["Close"])}
    except Exception:
        return {}

@st.cache_data(ttl=60, show_spinner=False)
def fetch_mtf_bias(ticker: str) -> dict:
    result = {}
    for tf_label, interval in TIMEFRAMES.items():
        df = fetch_data.__wrapped__(ticker, interval)
        if df is None or df.empty or len(df) < 22:
            result[tf_label] = {"bias": "NEUTRAL", "rsi": None, "ema_diff": 0}
            continue
        try:
            df = df.copy()
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            e9  = float(_ema(df["Close"], 9).iloc[-1])
            e21 = float(_ema(df["Close"], 21).iloc[-1])
            rsi = float(_rsi(df["Close"], 14).iloc[-1])
            diff = (e9 - e21) / e21 * 100
            if e9 > e21 and rsi > 52:
                bias = "BULLISH"
            elif e9 < e21 and rsi < 48:
                bias = "BEARISH"
            else:
                bias = "NEUTRAL"
            result[tf_label] = {"bias": bias, "rsi": rsi, "ema_diff": round(diff, 3)}
        except Exception:
            result[tf_label] = {"bias": "NEUTRAL", "rsi": None, "ema_diff": 0}
    return result

# ══════════════════════════════════════════════════════════════════════════════
# INDICATORS ON MAIN DATAFRAME
# ══════════════════════════════════════════════════════════════════════════════
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 22:
        return df
    try:
        df = df.copy()
        df["EMA9"]  = _ema(df["Close"], 9)
        df["EMA21"] = _ema(df["Close"], 21)
        df["RSI"]   = _rsi(df["Close"], 14)
        df["ATR"]   = _atr(df["High"], df["Low"], df["Close"], 14)
        df["VWAP"]  = _vwap(df["High"], df["Low"], df["Close"], df["Volume"])
        df["BB_U"], df["BB_M"], df["BB_L"] = _bbands(df["Close"], 20, 2.0)
        adx_vals, plus_di, minus_di = _adx(df["High"], df["Low"], df["Close"], 14)
        df["ADX"]      = adx_vals
        df["PLUS_DI"]  = plus_di
        df["MINUS_DI"] = minus_di
        df["VOL_MA20"] = df["Volume"].rolling(20).mean().fillna(df["Volume"])
        return df
    except Exception:
        return df

# ══════════════════════════════════════════════════════════════════════════════
# MARKET REGIME DETECTION
# ══════════════════════════════════════════════════════════════════════════════
def detect_regime(df: pd.DataFrame) -> str:
    if df.empty or "ADX" not in df.columns:
        return "UNKNOWN"
    try:
        adx  = float(df["ADX"].iloc[-1])
        atr  = float(df["ATR"].iloc[-1])
        close = float(df["Close"].iloc[-1])
        atr_pct = (atr / close * 100) if close > 0 else 0
        if atr_pct > 1.5:
            return "VOLATILE"
        if adx >= 22:
            return "TRENDING"
        return "CHOPPY"
    except Exception:
        return "UNKNOWN"

# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL SCORING ENGINE
# ══════════════════════════════════════════════════════════════════════════════
def score_signal(df: pd.DataFrame, kill_switch: bool, regime: str) -> dict:
    default = {
        "signal": "NONE", "score": 0, "entry": None,
        "sl": None, "target": None, "rsi": None, "atr": None,
        "ema9": None, "ema21": None, "vwap": None,
        "component_scores": {},
    }
    if kill_switch or df.empty or len(df) < 25 or regime == "CHOPPY":
        d = default.copy()
        d["kill_reason"] = "KILL SWITCH" if kill_switch else ("CHOPPY MARKET" if regime == "CHOPPY" else "INSUFFICIENT DATA")
        return d

    try:
        row   = df.iloc[-1]
        close = float(row["Close"])
        e9    = float(row["EMA9"])
        e21   = float(row["EMA21"])
        rsi   = float(row["RSI"])
        atr   = float(row["ATR"])
        vwap  = float(row["VWAP"]) if not np.isnan(row["VWAP"]) else close
        bb_u  = float(row["BB_U"])
        bb_l  = float(row["BB_L"])
        adx   = float(row["ADX"])
        vol   = float(row["Volume"])
        vol_ma = float(row["VOL_MA20"]) if not np.isnan(row["VOL_MA20"]) else vol

        if any(np.isnan(v) for v in [e9, e21, rsi, atr, adx]):
            return default

        scores = {}

        # BUY scoring
        buy_score = 0
        if e9 > e21:
            ema_str = min((e9 - e21) / e21 * 1000, 1.0) if e21 > 0 else 0
            buy_score += SCORE_WEIGHTS["ema_cross"] * (0.6 + 0.4 * ema_str)
        scores["ema_cross_buy"] = buy_score

        rsi_buy = 0
        if 55 <= rsi <= 70:
            rsi_buy = SCORE_WEIGHTS["rsi_zone"]
        elif 50 < rsi < 55:
            rsi_buy = SCORE_WEIGHTS["rsi_zone"] * 0.6
        buy_score += rsi_buy
        scores["rsi_buy"] = rsi_buy

        vwap_buy = SCORE_WEIGHTS["vwap_side"] if close > vwap else 0
        buy_score += vwap_buy
        scores["vwap_buy"] = vwap_buy

        bb_range = bb_u - bb_l
        bb_pos   = (close - bb_l) / bb_range if bb_range > 0 else 0.5
        bb_buy   = SCORE_WEIGHTS["bb_position"] * min(bb_pos * 1.2, 1.0)
        buy_score += bb_buy
        scores["bb_buy"] = bb_buy

        vol_ratio = vol / vol_ma if vol_ma > 0 else 1.0
        vol_buy   = SCORE_WEIGHTS["volume_conf"] * min(vol_ratio / 1.5, 1.0)
        buy_score += vol_buy
        scores["vol_buy"] = vol_buy

        adx_buy = SCORE_WEIGHTS["adx_trend"] * min(adx / 35, 1.0)
        buy_score += adx_buy
        scores["adx_buy"] = adx_buy

        # SELL scoring
        sell_score = 0
        if e9 < e21:
            ema_str = min((e21 - e9) / e21 * 1000, 1.0) if e21 > 0 else 0
            sell_score += SCORE_WEIGHTS["ema_cross"] * (0.6 + 0.4 * ema_str)

        rsi_sell = 0
        if 30 <= rsi <= 45:
            rsi_sell = SCORE_WEIGHTS["rsi_zone"]
        elif 45 < rsi < 50:
            rsi_sell = SCORE_WEIGHTS["rsi_zone"] * 0.6
        sell_score += rsi_sell

        vwap_sell = SCORE_WEIGHTS["vwap_side"] if close < vwap else 0
        sell_score += vwap_sell

        bb_sell = SCORE_WEIGHTS["bb_position"] * min((1 - bb_pos) * 1.2, 1.0)
        sell_score += bb_sell
        sell_score += vol_buy
        sell_score += adx_buy

        buy_score  = round(min(buy_score, 100), 1)
        sell_score = round(min(sell_score, 100), 1)

        signal = "NONE"
        score  = max(buy_score, sell_score)

        if buy_score >= SIGNAL_THRESHOLD and buy_score > sell_score and rsi < 75:
            signal = "BUY"
            score  = buy_score
            sl     = close - 1.5 * atr
            target = close + 2 * (close - sl)
        elif sell_score >= SIGNAL_THRESHOLD and sell_score > buy_score and rsi > 25:
            signal = "SELL"
            score  = sell_score
            sl     = close + 1.5 * atr
            target = close - 2 * (sl - close)
        else:
            sl = target = None

        return {
            "signal": signal,
            "score": score,
            "buy_score": buy_score,
            "sell_score": sell_score,
            "entry": close,
            "sl": sl,
            "target": target,
            "rsi": rsi,
            "atr": atr,
            "ema9": e9,
            "ema21": e21,
            "vwap": vwap,
            "adx": adx,
            "component_scores": scores,
            "kill_reason": None,
        }

    except Exception as ex:
        d = default.copy()
        d["kill_reason"] = f"ERROR: {ex}"
        return d

# ══════════════════════════════════════════════════════════════════════════════
# WALK-FORWARD BACKTEST
# ══════════════════════════════════════════════════════════════════════════════
def run_backtest(df: pd.DataFrame, lookback: int = 50) -> dict:
    empty = {"trades": [], "win_rate": 0, "total": 0,
             "wins": 0, "losses": 0, "equity": []}
    if df.empty or len(df) < lookback + 25:
        return empty

    df_bt = df.iloc[-(lookback + 25):].copy()
    trades = []
    equity = [10000.0]

    for i in range(25, len(df_bt)):
        slice_ = df_bt.iloc[:i]
        if len(slice_) < 22:
            continue
        row   = slice_.iloc[-1]
        prev  = slice_.iloc[-2]
        try:
            close = float(row["Close"])
            e9    = float(row["EMA9"])
            e21   = float(row["EMA21"])
            rsi   = float(row["RSI"])
            atr   = float(row["ATR"])
            vwap  = float(row["VWAP"]) if "VWAP" in slice_.columns and not np.isnan(row["VWAP"]) else close
            prev_h = float(prev["High"])
            prev_l = float(prev["Low"])
        except Exception:
            continue

        if any(np.isnan(v) for v in [e9, e21, rsi, atr]):
            continue

        signal = None
        if e9 > e21 and rsi > 58 and close > vwap and close > prev_h:
            signal = "BUY"
            sl     = close - 1.5 * atr
            target = close + 2 * (close - sl)
        elif e9 < e21 and rsi < 42 and close < vwap and close < prev_l:
            signal = "SELL"
            sl     = close + 1.5 * atr
            target = close - 2 * (sl - close)

        if signal and len(trades) < lookback:
            future = df_bt.iloc[i: i + 4]
            result = "OPEN"
            pnl    = 0
            for _, fr in future.iterrows():
                fh, fl = float(fr["High"]), float(fr["Low"])
                if signal == "BUY":
                    if fl <= sl:
                        result = "LOSS"; pnl = sl - close; break
                    if fh >= target:
                        result = "WIN";  pnl = target - close; break
                else:
                    if fh >= sl:
                        result = "LOSS"; pnl = close - sl; break
                    if fl <= target:
                        result = "WIN";  pnl = close - target; break
            if result != "OPEN":
                risk  = abs(close - sl) if sl else atr
                pnl_r = pnl / risk if risk else 0
                trades.append({
                    "time":   str(row.name)[:16],
                    "signal": signal,
                    "entry":  round(close, 2),
                    "sl":     round(sl, 2),
                    "target": round(target, 2),
                    "result": result,
                    "pnl_r":  round(pnl_r, 2),
                })
                eq_chg = 1 + (0.02 if result == "WIN" else -0.01)
                equity.append(equity[-1] * eq_chg)
            else:
                equity.append(equity[-1])

    wins   = sum(1 for t in trades if t["result"] == "WIN")
    losses = sum(1 for t in trades if t["result"] == "LOSS")
    total  = wins + losses
    wr     = round(wins / total * 100, 1) if total > 0 else 0

    return {
        "trades":    trades,
        "win_rate":  wr,
        "total":     total,
        "wins":      wins,
        "losses":    losses,
        "equity":    equity,
    }

# ══════════════════════════════════════════════════════════════════════════════
# DATA ALIGNMENT CONTROLS
# ══════════════════════════════════════════════════════════════════════════════
# Native interactive controls tied directly to Streamlit Session State keys
with st.expander("⚙️ QUANT-X CONTROL PANEL", expanded=True):
    col_c1, col_c2, col_c3 = st.columns([1, 1, 1.2])
    with col_c1:
        selected_label = st.selectbox("Market Asset Index", list(INDICES.keys()), key="selected_label")
        ticker   = INDICES[selected_label]
        lot_size = LOT_SIZES[selected_label]
    with col_c2:
        tf_label = st.selectbox("Data Timeframe Interval", list(TIMEFRAMES.keys()), key="tf_label")
        interval = TIMEFRAMES[tf_label]
    with col_c3:
        capital = st.number_input("Account Margin Capital (₹)", step=50000, min_value=10000, key="capital")
        risk_pct = st.slider("Risk Exposure per Trade (%)", 0.5, 3.0, step=0.25, key="risk_pct")

# ══════════════════════════════════════════════════════════════════════════════
# FETCH & COMPUTE
# ══════════════════════════════════════════════════════════════════════════════
with st.spinner("Fetching live market data…"):
    df_raw = fetch_data(ticker, interval)
    prev_d = fetch_prev_day(ticker)

if df_raw.empty:
    st.error("⚠️  No data returned. Market may be closed or the ticker is unavailable.")
    st.stop()

df_ind  = calculate_indicators(df_raw)
regime  = detect_regime(df_ind)
pivots  = calculate_pivots(prev_d)
bt      = run_backtest(df_ind, lookback=40)
kill_sw, kill_reason = auto_kill_check(bt, manual_kill)
sig     = score_signal(df_ind, kill_sw, regime)
update_trade_log(sig, selected_label)

try:
    ltp         = float(df_ind["Close"].iloc[-1])
    open_price  = float(df_ind["Open"].iloc[0])
    day_chg     = ltp - open_price
    day_chg_pct = (day_chg / open_price * 100) if open_price else 0
    volatility  = float(df_ind["ATR"].iloc[-1]) if "ATR" in df_ind.columns else 0.0
    vwap_val    = float(df_ind["VWAP"].iloc[-1]) if "VWAP" in df_ind.columns else 0.0
    adx_val     = float(df_ind["ADX"].iloc[-1]) if "ADX" in df_ind.columns else 0.0
    rsi_val     = float(df_ind["RSI"].iloc[-1]) if "RSI" in df_ind.columns else 0.0
except Exception:
    ltp = open_price = day_chg = day_chg_pct = volatility = vwap_val = adx_val = rsi_val = 0.0

atm_data = get_atm_strike(ltp, selected_label)
pos      = position_size(capital, risk_pct, abs(ltp - (sig["sl"] or ltp)), lot_size)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER BAR
# ══════════════════════════════════════════════════════════════════════════════
regime_html = {
    "TRENDING": '<span class="qx-regime qx-regime-trend">◈ TRENDING</span>',
    "CHOPPY":   '<span class="qx-regime qx-regime-chop">◈ CHOPPY — SIGNALS PAUSED</span>',
    "VOLATILE": '<span class="qx-regime qx-regime-vol">◈ VOLATILE</span>',
}.get(regime, '<span class="qx-regime qx-regime-chop">◈ UNKNOWN</span>')

dot_c = "#00E676" if is_open else "#FF4B4B"
score = sig.get("score", 0)

ks_html = ""
if kill_sw:
    ks_html = f'<span class="qx-chip qx-chip-red">⛔ HALTED — {kill_reason[:35]}</span>'

header_html = f"""
<div class="qx-header">
  <div class="qx-header-left">
    <div>
      <div class="qx-header-title" style="font-size: 1rem;">Quant<span style="color:#00E676">X</span> · {selected_label} · {tf_label}</div>
      <div class="qx-header-sub">Signal threshold {SIGNAL_THRESHOLD}/100 · {lot_size} units/lot</div>
    </div>
    {regime_html}
    {ks_html}
  </div>
  <div style="display:flex;align-items:center;gap:0.6rem">
    <span class="qx-chip {'qx-chip-green' if is_open else 'qx-chip-red'}">
      <span style="display:inline-block;width:5px;height:5px;border-radius:50%;background:{dot_c};margin-right:4px;vertical-align:middle;animation:qx-pulse 2s infinite"></span>
      NSE {mkt_regime_label}
    </span>
  </div>
</div>
"""
render_html(header_html)

# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL BANNER
# ══════════════════════════════════════════════════════════════════════════════
s      = sig["signal"]
sc     = "buy" if s == "BUY" else ("sell" if s == "SELL" else "none")
s_col  = "clr-green" if s == "BUY" else ("clr-red" if s == "SELL" else "clr-blue")
s_icon = "▲" if s == "BUY" else ("▼" if s == "SELL" else "⏸")
rsi_txt  = f"{sig['rsi']:.1f}" if sig["rsi"] else "—"
atr_txt  = f"₹{sig['atr']:,.1f}" if sig["atr"] else "—"
sl_txt   = f"₹{sig['sl']:,.2f}" if sig["sl"] else "—"
tgt_txt  = f"₹{sig['target']:,.2f}" if sig["target"] else "—"
arc_svg  = score_arc_svg(score, s)

kill_note = ""
if sig.get("kill_reason"):
    kill_note = f'<span style="font-size:0.65rem;color:rgba(255,75,75,0.7);font-family:JetBrains Mono,monospace">{sig["kill_reason"]}</span>'

banner_html = f"""
<div class="qx-signal-banner {sc}">
  <div class="qx-signal-main">
    <div style="font-size:2.4rem;line-height:1">{s_icon}</div>
    <div>
      <div class="qx-signal-type {'clr-green' if s == 'BUY' else ('clr-red' if s == 'SELL' else 'clr-blue')}">{s}</div>
      <div class="qx-signal-meta">
        Entry <strong>{f"₹{sig['entry']:,.2f}" if sig['entry'] else '—'}</strong> &nbsp;·&nbsp;
        SL <strong style="color:#FF6B6B">{sl_txt}</strong> &nbsp;·&nbsp;
        Target <strong style="color:#00E676">{tgt_txt}</strong><br>
        RSI <strong>{rsi_txt}</strong> &nbsp;·&nbsp;
        ATR <strong>{atr_txt}</strong> &nbsp;·&nbsp;
        ADX <strong>{adx_val:.1f}</strong> &nbsp;·&nbsp;
        VWAP <strong>₹{vwap_val:,.1f}</strong>
        {"<br>" + kill_note if kill_note else ""}
      </div>
    </div>
  </div>
  <div class="qx-score-wrap">
    {arc_svg}
    <div class="qx-score-label">Signal Score</div>
  </div>
</div>
"""
render_html(banner_html)

# ══════════════════════════════════════════════════════════════════════════════
# MOBILE-FIRST METRIC ROW (Using Flex Wrap Grid)
# ══════════════════════════════════════════════════════════════════════════════
chg_cls   = "clr-green" if day_chg >= 0 else "clr-red"
chg_arrow = "▲" if day_chg >= 0 else "▼"
vol_above = vwap_val > 0 and ltp > vwap_val
sl_pct = (abs(ltp - (sig["sl"] or ltp)) / ltp * 100) if sig["sl"] and ltp else 0
rr_pts = abs((sig["target"] or ltp) - ltp) if sig["target"] else 0
vwap_cls  = "clr-green" if vol_above else "clr-red"
vwap_side = "ABOVE" if vol_above else "BELOW"
adx_txt = "STRONG" if adx_val > 25 else ("WEAK" if adx_val < 18 else "MOD")
adx_cls = "clr-green" if adx_val > 25 else ("clr-red" if adx_val < 18 else "clr-amber")
wr_cls = "clr-green" if bt["win_rate"] >= 55 else ("clr-amber" if bt["win_rate"] >= 40 else "clr-red")

metrics_html = f"""
<div class="qx-metrics-grid">
  <!-- LTP -->
  <div class="qx-card qx-card-blue">
    <div class="qx-card-icon">📈</div>
    <div class="qx-card-label">LTP · {selected_label}</div>
    <div class="qx-card-value">₹{ltp:,.2f}</div>
    <div class="qx-card-sub"><span class="{chg_cls}">{chg_arrow} {abs(day_chg_pct):.2f}%</span></div>
  </div>
  <!-- SL -->
  <div class="qx-card qx-card-red">
    <div class="qx-card-icon">🛡</div>
    <div class="qx-card-label">Stop Loss</div>
    <div class="qx-card-value clr-red">{sl_txt}</div>
    <div class="qx-card-sub">Risk {sl_pct:.2f}%</div>
  </div>
  <!-- TGT -->
  <div class="qx-card qx-card-green">
    <div class="qx-card-icon">🎯</div>
    <div class="qx-card-label">Target (1:2)</div>
    <div class="qx-card-value clr-green">{tgt_txt}</div>
    <div class="qx-card-sub">Reward ₹{rr_pts:,.0f}</div>
  </div>
  <!-- VWAP -->
  <div class="qx-card qx-card-amber">
    <div class="qx-card-icon">⚖</div>
    <div class="qx-card-label">VWAP</div>
    <div class="qx-card-value">₹{vwap_val:,.0f}</div>
    <div class="qx-card-sub"><span class="{vwap_cls}">{vwap_side}</span></div>
  </div>
  <!-- Trend Strength -->
  <div class="qx-card qx-card-neutral">
    <div class="qx-card-icon">📡</div>
    <div class="qx-card-label">ADX Indicator</div>
    <div class="qx-card-value">{adx_val:.1f}</div>
    <div class="qx-card-sub"><span class="{adx_cls}">{adx_txt}</span></div>
  </div>
  <!-- Win Rate -->
  <div class="qx-card {'qx-card-green' if bt['win_rate'] >= 55 else ('qx-card-amber' if bt['win_rate'] >= 40 else 'qx-card-red')}">
    <div class="qx-card-icon">🏆</div>
    <div class="qx-card-label">Backtest Win %</div>
    <div class="qx-card-value {wr_cls}">{bt['win_rate']}%</div>
    <div class="qx-card-sub">{bt['wins']}W / {bt['losses']}L</div>
  </div>
</div>
"""
render_html(metrics_html)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📊  Price Chart",
    "📈  Backtest Results",
    "🎯  Options & Position",
    "📋  Analytics",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — PRICE CHART
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    col_chart, col_right = st.columns([3, 1], gap="large")

    with col_chart:
        fig = build_chart(df_ind, pivots, sig, show_ema, show_vwap, show_bb)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_right:
        st.markdown('<div class="qx-section">Multi-Timeframe Bias</div>', unsafe_allow_html=True)
        with st.spinner("Loading MTF…"):
            try:
                mtf = fetch_mtf_bias(ticker)
            except Exception:
                mtf = {tf: {"bias": "NEUTRAL", "rsi": None} for tf in TIMEFRAMES}

        mtf_rows = ""
        bull_count = 0
        bear_count = 0
        for tf_k, td in mtf.items():
            bias = td["bias"]
            rsi_v = f"{td['rsi']:.0f}" if td["rsi"] else "—"
            pill_cls = "mtf-bull" if bias == "BULLISH" else ("mtf-bear" if bias == "BEARISH" else "mtf-neut")
            if bias == "BULLISH": bull_count += 1
            elif bias == "BEARISH": bear_count += 1
            align_icon = "▲" if bias == "BULLISH" else ("▼" if bias == "BEARISH" else "—")
            mtf_rows += f"""
            <tr>
              <td style="font-size:0.72rem;font-weight:600">{tf_k}</td>
              <td><span class="qx-mtf-pill {pill_cls}">{align_icon} {bias[:4]}</span></td>
              <td style="opacity:0.8;font-size:0.7rem">{rsi_v}</td>
            </tr>"""

        align_total = bull_count - bear_count
        align_note_color = "clr-green" if align_total >= 2 else ("clr-red" if align_total <= -2 else "clr-amber")
        align_note = f"{'Bullish' if align_total > 0 else 'Bearish' if align_total < 0 else 'Mixed'} ({bull_count}↑ {bear_count}↓)"

        mtf_table_html = f"""
        <table class="qx-mtf-table">
          <thead><tr><th>TF</th><th>Bias</th><th>RSI</th></tr></thead>
          <tbody>{mtf_rows}</tbody>
        </table>
        <p style="font-size:0.65rem;margin-top:0.6rem" class="{align_note_color}">Alignment: {align_note}</p>
        """
        render_html(mtf_table_html)

        st.markdown('<div class="qx-section">Fibonacci Pivots</div>', unsafe_allow_html=True)
        if pivots:
            lm = {"R2":("Res 2","pv-r"), "R1":("Res 1","pv-r"), "P":("Pivot","pv-p"),
                  "S1":("Sup 1","pv-s"), "S2":("Sup 2","pv-s")}
            rows_html = ""
            for k in ["R2","R1","P","S1","S2"]:
                v = pivots.get(k, 0)
                name, cls = lm[k]
                diff = ((v - ltp) / ltp * 100) if ltp else 0
                dc = "pv-pos" if diff > 0 else "pv-neg"
                rows_html += f"""<tr>
                  <td style="opacity:0.7;font-size:0.72rem">{name}</td>
                  <td class="{cls}" style="font-size:0.72rem;font-weight:700">{k}</td>
                  <td class="{cls}" style="font-weight:600">₹{v:,.0f}</td>
                  <td class="{dc}" style="text-align:right;font-size:0.7rem">{diff:+.2f}%</td>
                </tr>"""
            
            pivots_html = f"""
            <table class="qx-pivot-table">
              <thead><tr><th>Level</th><th></th><th>Price</th><th style="text-align:right">vs LTP</th></tr></thead>
              <tbody>{rows_html}</tbody>
            </table>"""
            render_html(pivots_html)
        else:
            st.markdown('<p style="opacity:0.5;font-size:0.78rem">Pivot data unavailable</p>', unsafe_allow_html=True)

        st.markdown('<div class="qx-section">Signal Log</div>', unsafe_allow_html=True)
        log = st.session_state.get("trade_log", [])
        if not log:
            st.markdown('<p style="opacity:0.5;font-size:0.75rem;padding:0.3rem 0">No signals yet — waiting for confluence…</p>', unsafe_allow_html=True)
        else:
            for e in log[:5]:
                bc = "buy" if e["signal"] == "BUY" else "sell"
                sl_s  = f"SL ₹{e['sl']:,.0f}" if e["sl"] else ""
                tgt_s = f"T ₹{e['target']:,.0f}" if e["target"] else ""
                sc_s  = f"Score {e.get('score',0):.0f}" if e.get("score") else ""
                log_entry_html = f"""
                <div class="qx-log-entry">
                  <div>
                    <div class="qx-log-time">{e['time']}</div>
                    <div class="qx-log-idx">{e['index']}</div>
                    <div class="qx-log-price">₹{e['entry']:,.2f}</div>
                    <div class="qx-log-levels">{sl_s} &nbsp; {tgt_s} &nbsp; {sc_s}</div>
                  </div>
                  <span class="qx-log-badge {bc}">{e['signal']}</span>
                </div>"""
                render_html(log_entry_html)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — BACKTEST RESULTS
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="qx-section">Walk-Forward Backtest · Last 40 Bars</div>', unsafe_allow_html=True)

    if kill_sw:
        ks_banner = f'<div class="qx-ks-halted">⛔ &nbsp; AUTO KILL-SWITCH ACTIVE — {kill_reason}</div>'
    else:
        ks_banner = '<div class="qx-ks-active">✅ &nbsp; SIGNALS ACTIVE — Win rate above threshold</div>'
    render_html(ks_banner)

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    wr     = bt["win_rate"]
    wr_col = "clr-green" if wr >= 55 else ("clr-amber" if wr >= 40 else "clr-red")
    avg_r  = round(sum(t["pnl_r"] for t in bt["trades"]) / len(bt["trades"]), 2) if bt["trades"] else 0
    eq_ret = round((bt["equity"][-1] / bt["equity"][0] - 1) * 100, 1) if len(bt["equity"]) > 1 else 0

    bs1, bs2, bs3, bs4, bs5 = st.columns(5)
    stat_cards = [
        (bs1, f"{wr}%",         "Win Rate",     wr_col),
        (bs2, str(bt["total"]), "Total Trades", ""),
        (bs3, str(bt["wins"]),  "Wins",         "clr-green"),
        (bs4, str(bt["losses"]),"Losses",       "clr-red"),
        (bs5, f"{eq_ret:+.1f}%","Equity Return","clr-green" if eq_ret > 0 else "clr-red"),
    ]
    for col, val, lbl, vc in stat_cards:
        with col:
            bt_card = f"""
            <div class="qx-bt-stat">
              <div class="qx-bt-stat-val {vc}">{val}</div>
              <div class="qx-bt-stat-lbl">{lbl}</div>
            </div>"""
            render_html(bt_card)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    col_eq, col_tbl = st.columns([1, 1], gap="large")

    with col_eq:
        st.markdown('<div class="qx-section">Equity Curve</div>', unsafe_allow_html=True)
        if len(bt["equity"]) > 2:
            eq_fig = build_equity_curve(bt["equity"])
            st.plotly_chart(eq_fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<p style="opacity:0.5;font-size:0.78rem">Insufficient trades to plot equity curve.</p>', unsafe_allow_html=True)

    with col_tbl:
        st.markdown('<div class="qx-section">Recent Trades</div>', unsafe_allow_html=True)
        if bt["trades"]:
            df_trades = pd.DataFrame(bt["trades"][-15:])
            df_trades = df_trades[["time", "signal", "entry", "sl", "target", "result", "pnl_r"]]
            df_trades.columns = ["Time", "Signal", "Entry", "SL", "Target", "Result", "P&L (R)"]
            
            # Pandas 3.0+ compatibility fix: changing .applymap() to .map()
            st.dataframe(
                df_trades.style
                    .map(lambda v: "color:#00E676" if v == "WIN" else ("color:#FF4B4B" if v == "LOSS" else ""), subset=["Result"])
                    .map(lambda v: "color:#00E676" if isinstance(v, float) and v > 0 else ("color:#FF4B4B" if isinstance(v, float) and v < 0 else ""), subset=["P&L (R)"])
                    .format({"Entry": "₹{:,.2f}", "SL": "₹{:,.2f}", "Target": "₹{:,.2f}", "P&L (R)": "{:+.2f}R"}),
                use_container_width=True,
                height=220,
                hide_index=True,
            )
        else:
            st.markdown('<p style="opacity:0.5;font-size:0.78rem">No completed trades in backtest window.</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — OPTIONS & POSITION SIZING
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    col_opt, col_pos = st.columns([1, 1], gap="large")

    with col_opt:
        st.markdown('<div class="qx-section">F&O Strike Suggester</div>', unsafe_allow_html=True)

        opt_cards_html = f"""
        <div class="qx-opt-card" style="border-left:3px solid rgba(0,230,118,0.4)">
          <div class="qx-opt-header">BUY SIGNAL → CALL OPTION (CE)</div>
          <div class="qx-opt-strike">{atm_data['ce']:,} CE</div>
          <div class="qx-opt-meta">
            ATM Strike &nbsp;·&nbsp; Gap {atm_data['gap']} pts &nbsp;·&nbsp; {selected_label}<br>
            ITM CE: <strong>{atm_data['itm_ce']:,}</strong> &nbsp;·&nbsp;
            OTM CE: <strong>{atm_data['otm_ce']:,}</strong>
          </div>
        </div>
        <div class="qx-opt-card" style="border-left:3px solid rgba(255,75,75,0.4)">
          <div class="qx-opt-header">SELL SIGNAL → PUT OPTION (PE)</div>
          <div class="qx-opt-strike">{atm_data['pe']:,} PE</div>
          <div class="qx-opt-meta">
            ATM Strike &nbsp;·&nbsp; Gap {atm_data['gap']} pts &nbsp;·&nbsp; {selected_label}<br>
            ITM PE: <strong>{atm_data['itm_pe']:,}</strong> &nbsp;·&nbsp;
            OTM PE: <strong>{atm_data['otm_pe']:,}</strong>
          </div>
        </div>
        """
        render_html(opt_cards_html)

        st.markdown('<div class="qx-section">Index Specifications</div>', unsafe_allow_html=True)
        spec_rows = ""
        for idx_n, idx_t in INDICES.items():
            active = "rgba(0,230,118,0.04)" if idx_n == selected_label else "transparent"
            spec_rows += f"""
            <tr style="background:{active}">
              <td style="font-weight:{'700' if idx_n == selected_label else '400'}">
                {idx_n}
              </td>
              <td>{LOT_SIZES[idx_n]}</td>
              <td>{STRIKE_GAPS[idx_n]}</td>
            </tr>"""
        
        spec_table_html = f"""
        <table class="qx-pivot-table">
          <thead><tr><th>Index</th><th>Lot Size</th><th>Strike Gap</th></tr></thead>
          <tbody>{spec_rows}</tbody>
        </table>"""
        render_html(spec_table_html)

    with col_pos:
        st.markdown('<div class="qx-section">Position Size Calculator</div>', unsafe_allow_html=True)

        sl_pts = abs(ltp - (sig["sl"] or ltp))
        pos    = position_size(capital, risk_pct, sl_pts, lot_size)

        pos_sizing_html = f"""
        <div class="qx-opt-card">
          <div class="qx-opt-header">Capital & Risk Parameters</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-top:0.5rem">
            <div>
              <div style="font-size:0.6rem;opacity:0.5;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.2rem">Capital</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:700">₹{capital:,.0f}</div>
            </div>
            <div>
              <div style="font-size:0.6rem;opacity:0.5;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.2rem">Risk / Trade</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:700;color:#FFB347">{risk_pct}%</div>
            </div>
            <div>
              <div style="font-size:0.6rem;opacity:0.5;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.2rem">SL Distance</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:700;color:#FF6B6B">₹{sl_pts:,.1f}</div>
            </div>
            <div>
              <div style="font-size:0.6rem;opacity:0.5;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.2rem">Lot Size</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:700">{lot_size}</div>
            </div>
          </div>
        </div>

        <div class="qx-opt-card" style="border-left:3px solid rgba(0,230,118,0.4);margin-top:0.5rem">
          <div class="qx-opt-header">Recommended Position</div>
          <div class="qx-opt-strike clr-green">{pos['lots']} lot{'s' if pos['lots'] != 1 else ''}</div>
          <div class="qx-opt-meta">
            Max risk: <strong>₹{pos['risk_amount']:,.0f}</strong>
            &nbsp;({risk_pct}% of capital)<br>
            Qty: <strong>{pos['lots'] * lot_size}</strong> units &nbsp;·&nbsp;
            Est. margin: <strong>₹{pos['margin_est']:,.0f}</strong>
          </div>
        </div>

        <div class="qx-opt-card" style="margin-top:0.5rem;background:rgba(255,179,71,0.03);border-color:rgba(255,179,71,0.15)">
          <div class="qx-opt-header" style="color:rgba(255,179,71,0.6)">Risk Rules — Never Break These</div>
          <div style="font-size:0.72rem;opacity:0.8;line-height:1.8">
            ◈ &nbsp;Risk ≤ 1–2% of capital per trade<br>
            ◈ &nbsp;Max 3 open positions simultaneously<br>
            ◈ &nbsp;Stop at 3× daily loss (₹{capital * risk_pct / 100 * 3:,.0f})<br>
            ◈ &nbsp;Never average a losing F&O position<br>
            ◈ &nbsp;Exit before 15:15 IST (avoid expiry theta)
          </div>
        </div>
        """
        render_html(pos_sizing_html)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    col_a, col_b = st.columns([1, 1], gap="large")

    with col_a:
        st.markdown('<div class="qx-section">Signal Score Breakdown</div>', unsafe_allow_html=True)
        cs = sig.get("component_scores", {})
        if cs:
            score_data = {
                "EMA Cross":    cs.get("ema_cross_buy", 0),
                "RSI Zone":     cs.get("rsi_buy", 0),
                "VWAP Side":    cs.get("vwap_buy", 0),
                "BB Position":  cs.get("bb_buy", 0),
                "Volume Conf.": cs.get("vol_buy", 0),
                "ADX Trend":    cs.get("adx_buy", 0),
            }
            max_scores = {k: v for k, v in SCORE_WEIGHTS.items()}
            bar_fig = go.Figure()
            bars_achieved = list(score_data.values())
            bars_max      = [SCORE_WEIGHTS.get(k.lower().replace(" ","_").replace(".",""), 15) for k in score_data.keys()]
            bar_colors    = ["rgba(0,230,118,0.7)" if a >= m * 0.7 else
                             ("rgba(255,179,71,0.7)" if a >= m * 0.4 else "rgba(255,75,75,0.6)")
                             for a, m in zip(bars_achieved, bars_max)]
            bar_fig.add_trace(go.Bar(
                x=list(score_data.keys()), y=bars_achieved,
                marker_color=bar_colors,
                text=[f"{v:.0f}" for v in bars_achieved],
                textposition="outside",
                textfont=dict(size=9, family="JetBrains Mono"),
            ))
            bar_fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=20, b=0), height=200,
                showlegend=False,
                xaxis=dict(tickfont=dict(size=9), gridcolor="rgba(120,120,120,0.1)"),
                yaxis=dict(gridcolor="rgba(120,120,120,0.1)", tickfont=dict(size=9), range=[0, 28]),
                bargap=0.35,
            )
            st.plotly_chart(bar_fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<p style="opacity:0.5;font-size:0.78rem">Run a signal to see score breakdown.</p>', unsafe_allow_html=True)

        st.markdown('<div class="qx-section">Current Indicator Snapshot</div>', unsafe_allow_html=True)
        ind_rows = [
            ("EMA 9",     f"₹{sig['ema9']:,.2f}" if sig['ema9'] else "—",       ""),
            ("EMA 21",    f"₹{sig['ema21']:,.2f}" if sig['ema21'] else "—",     ""),
            ("RSI 14",    f"{rsi_val:.2f}",  "clr-green" if rsi_val > 60 else ("clr-red" if rsi_val < 40 else "")),
            ("ATR 14",    f"₹{volatility:,.2f}", ""),
            ("VWAP",      f"₹{vwap_val:,.2f}", ""),
            ("ADX 14",    f"{adx_val:.2f}",  "clr-green" if adx_val > 25 else "clr-red"),
            ("BB Upper",  f"₹{float(df_ind['BB_U'].iloc[-1]):,.2f}" if 'BB_U' in df_ind.columns else "—", ""),
            ("BB Lower",  f"₹{float(df_ind['BB_L'].iloc[-1]):,.2f}" if 'BB_L' in df_ind.columns else "—", ""),
            ("Signal Score", f"{score:.0f} / 100", "clr-green" if score >= 70 else ("clr-amber" if score >= 50 else "clr-red")),
        ]
        rows_html = ""
        for lbl, val, vc in ind_rows:
            rows_html += f"""<tr>
              <td style="opacity:0.6;font-size:0.72rem">{lbl}</td>
              <td class="{vc}" style="font-weight:600;font-size:0.78rem">{val}</td>
            </tr>"""
        
        snapshot_table_html = f"""
        <table class="qx-pivot-table">
          <thead><tr><th>Indicator</th><th>Value</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>"""
        render_html(snapshot_table_html)

    with col_b:
        st.markdown('<div class="qx-section">Session Summary</div>', unsafe_allow_html=True)
        log = st.session_state.get("trade_log", [])
        sess_buy  = sum(1 for e in log if e["signal"] == "BUY")
        sess_sell = sum(1 for e in log if e["signal"] == "SELL")
        
        session_summary_html = f"""
        <div class="qx-opt-card">
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5rem">
            <div style="text-align:center">
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.5rem;font-weight:700">{len(log)}</div>
              <div style="font-size:0.6rem;opacity:0.5;text-transform:uppercase;letter-spacing:0.1em">Signals</div>
            </div>
            <div style="text-align:center">
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.5rem;font-weight:700;color:#00E676">{sess_buy}</div>
              <div style="font-size:0.6rem;opacity:0.5;text-transform:uppercase;letter-spacing:0.1em">BUY</div>
            </div>
            <div style="text-align:center">
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.5rem;font-weight:700;color:#FF4B4B">{sess_sell}</div>
              <div style="font-size:0.6rem;opacity:0.5;text-transform:uppercase;letter-spacing:0.1em">SELL</div>
            </div>
          </div>
        </div>
        """
        render_html(session_summary_html)

        st.markdown('<div class="qx-section">Full Signal Log</div>', unsafe_allow_html=True)
        if log:
            df_log = pd.DataFrame(log)
            df_log = df_log[["time", "index", "signal", "entry", "sl", "target", "score"]].copy()
            df_log.columns = ["Time", "Index", "Signal", "Entry ₹", "SL ₹", "Target ₹", "Score"]
            
            # Pandas 3.0+ compatibility fix: changing .applymap() to .map()
            st.dataframe(
                df_log.style
                    .map(lambda v: "color:#00E676" if v == "BUY" else ("color:#FF4B4B" if v == "SELL" else ""), subset=["Signal"])
                    .format({"Entry ₹": "₹{:,.2f}", "SL ₹": "₹{:,.2f}", "Target ₹": "₹{:,.2f}", "Score": "{:.0f}"}),
                use_container_width=True,
                height=260,
                hide_index=True,
            )
            csv = df_log.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ Download Signal Log (.csv)",
                data=csv,
                file_name=f"quantx_signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.markdown('<p style="opacity:0.5;font-size:0.78rem">No signals recorded this session.</p>', unsafe_allow_html=True)

        st.markdown('<div class="qx-section">System Status</div>', unsafe_allow_html=True)
        status_items = [
            ("Data Feed",       "LIVE" if not df_ind.empty else "ERROR",         "clr-green" if not df_ind.empty else "clr-red"),
            ("Signal Engine",   "HALTED" if kill_sw else "ACTIVE",              "clr-red" if kill_sw else "clr-green"),
            ("Market Regime",   regime,                                           "clr-green" if regime == "TRENDING" else ("clr-amber" if regime == "VOLATILE" else "clr-red")),
            ("Backtest WR",     f"{bt['win_rate']}%",                            "clr-green" if bt["win_rate"] >= 55 else ("clr-amber" if bt["win_rate"] >= 40 else "clr-red")),
            ("Kill Switch",     "MANUAL" if manual_kill else ("AUTO-TRIGGERED" if kill_sw else "OFF"), "clr-red" if kill_sw else "clr-green"),
            ("Auto Refresh",    f"Every {refresh_sec}s",                          "clr-blue"),
        ]
        rows_html = ""
        for lbl, val, vc in status_items:
            rows_html += f"""<tr>
              <td style="opacity:0.6;font-size:0.72rem">{lbl}</td>
              <td class="{vc}" style="font-weight:700;font-size:0.72rem;font-family:'JetBrains Mono',monospace">{val}</td>
            </tr>"""
        
        status_table_html = f"""
        <table class="qx-pivot-table">
          <thead><tr><th>Component</th><th>Status</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>"""
        render_html(status_table_html)

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<hr class="qx-divider" style="margin-top:2rem">
<div style="display:flex;justify-content:space-between;align-items:center;
            padding:0.5rem 0;font-size:0.6rem;opacity:0.5">
  <span>QuantX v4 &nbsp;·&nbsp; F&amp;O Intelligence Terminal &nbsp;·&nbsp;
        Pure pandas/numpy · Python 3.11</span>
  <span style="color:rgba(255,179,71,0.8);font-weight:600">
    ⚠ For educational &amp; research use only. Not SEBI-registered investment advice.
  </span>
</div>
""", unsafe_allow_html=True)
