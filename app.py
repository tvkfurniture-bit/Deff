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
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

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
# DESIGN SYSTEM — Theme-Adaptive Terminal Aesthetic
# Typography: JetBrains Mono (data) + Inter (UI)
# Supporting flawless execution in both Dark and Light System settings.
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
    rgba(120,120,120,0.015) 2px,
    rgba(120,120,120,0.015) 4px
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
[data-testid="stSidebarCollapsedControl"] {
  display: flex !important;
  visibility: visible !important;
  z-index: 99999 !important;
}

.block-container {
  padding: 1.2rem 2rem 3rem 2rem !important;
  max-width: 100% !important;
}

/* ── Sidebar styling ──────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  border-right: 1px solid rgba(120, 120, 120, 0.1) !important;
  padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child {
  padding-top: 1.5rem;
}

/* ── Sidebar widgets ──────────────────────────────────────────────────────── */
[data-testid="stSidebar"] .stSelectbox > label,
[data-testid="stSidebar"] .stRadio > label,
[data-testid="stSidebar"] .stToggle > label,
[data-testid="stSidebar"] .stSlider > label {
  font-size: 0.62rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  opacity: 0.7;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
  border-radius: 8px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.82rem !important;
}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.78rem !important;
  font-weight: 600 !important;
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
  padding: 0.7rem 1.4rem !important;
  transition: all 0.2s !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
  color: #00FFA3 !important;
  border-bottom: 2px solid #00FFA3 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {
  background: rgba(120, 120, 120, 0.05) !important;
}
[data-testid="stTabPanel"] {
  padding-top: 1.5rem !important;
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
[data-testid="stSpinner"] { color: #00FFA3 !important; }

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
.qx-wordmark .acc { color: #00FFA3; text-shadow: 0 0 20px rgba(0,255,163,0.3); }
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
  margin-bottom: 1.2rem;
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
  background: rgba(0,255,163,0.1);
  border: 1px solid rgba(0,255,163,0.3);
  color: #00FFA3;
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
.qx-chip-blue {
  background: rgba(91,140,255,0.1);
  border: 1px solid rgba(91,140,255,0.3);
  color: #5B8CFF;
}
.qx-chip-gray {
  background: rgba(120,120,120,0.1);
  border: 1px solid rgba(120,120,120,0.2);
}

/* ── Custom Theme Adaptive Cards ──────────────────────────────────────────── */
.qx-card {
  position: relative;
  background: rgba(120, 120, 120, 0.05);
  border: 1px solid rgba(120, 120, 120, 0.15);
  border-radius: 14px;
  padding: 1.1rem 1.25rem;
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
.qx-card-green { border-color: rgba(0,255,163,0.15); }
.qx-card-green::before { background: linear-gradient(90deg, #00FFA3 0%, transparent 70%); }
.qx-card-green:hover { border-color: rgba(0,255,163,0.35); box-shadow: 0 0 24px rgba(0,255,163,0.06); }

.qx-card-red { border-color: rgba(255,75,75,0.15); }
.qx-card-red::before { background: linear-gradient(90deg, #FF4B4B 0%, transparent 70%); }
.qx-card-red:hover { border-color: rgba(255,75,75,0.35); box-shadow: 0 0 24px rgba(255,75,75,0.06); }

.qx-card-blue { border-color: rgba(91,140,255,0.15); }
.qx-card-blue::before { background: linear-gradient(90deg, #5B8CFF 0%, transparent 70%); }
.qx-card-blue:hover { border-color: rgba(91,140,255,0.35); box-shadow: 0 0 24px rgba(91,140,255,0.06); }

.qx-card-amber { border-color: rgba(255,179,71,0.15); }
.qx-card-amber::before { background: linear-gradient(90deg, #FFB347 0%, transparent 70%); }
.qx-card-amber:hover { border-color: rgba(255,179,71,0.35); box-shadow: 0 0 24px rgba(255,179,71,0.06); }

.qx-card-neutral { border-color: rgba(120, 120, 120, 0.15); }
.qx-card-neutral::before { background: linear-gradient(90deg, rgba(120, 120, 120, 0.4) 0%, transparent 70%); }

.qx-card-label {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  opacity: 0.6;
  margin-bottom: 0.45rem;
}
.qx-card-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.02em;
}
.qx-card-sub {
  font-size: 0.67rem;
  margin-top: 0.35rem;
  font-weight: 400;
  opacity: 0.8;
}
.qx-card-icon {
  position: absolute;
  top: 0.9rem;
  right: 1rem;
  font-size: 1.1rem;
  opacity: 0.15;
}

.clr-green  { color: #00FFA3 !important; }
.clr-red    { color: #FF4B4B !important; }
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
  border-color: rgba(0,255,163,0.35);
  background: rgba(0,255,163,0.05);
}
.qx-signal-banner.buy::before { background: #00FFA3; }
.qx-signal-banner.sell {
  border-color: rgba(255,75,75,0.35);
  background: rgba(255,75,75,0.05);
}
.qx-signal-banner.sell::before { background: #FF4B4B; }
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
  background: rgba(0,255,163,0.08);
  border: 1px solid rgba(0,255,163,0.25);
  color: #00FFA3;
}
.qx-regime-chop {
  background: rgba(255,179,71,0.08);
  border: 1px solid rgba(255,179,71,0.25);
  color: #FFB347;
}
.qx-regime-vol {
  background: rgba(255,75,75,0.08);
  border: 1px solid rgba(255,75,75,0.25);
  color: #FF4B4B;
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
.mtf-bull { background: rgba(0,255,163,0.1); color: #00FFA3; }
.mtf-bear { background: rgba(255,75,75,0.1); color: #FF4B4B; }
.mtf-neut { background: rgba(120,120,120,0.1); }

.pv-r { color: #FF6B6B; font-weight: 600; }
.pv-s { color: #00FFA3; font-weight: 600; }
.pv-p { color: #5B8CFF; font-weight: 600; }
.pv-pos { color: #00FFA3; }
.pv-neg { color: #FF4B4B; }

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
.qx-log-badge.buy  { background: rgba(0,255,163,0.1); color: #00FFA3; border: 1px solid rgba(0,255,163,0.25); }
.qx-log-badge.sell { background: rgba(255,75,75,0.1); color: #FF4B4B; border: 1px solid rgba(255,75,75,0.25); }

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
  font-size: 1.6rem;
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
  background: rgba(255,75,75,0.06);
  border: 1px solid rgba(255,75,75,0.25);
  border-radius: 8px;
  padding: 0.55rem 0.9rem;
  font-size: 0.68rem;
  color: #FF4B4B;
  text-align: center;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.qx-ks-active {
  background: rgba(0,255,163,0.05);
  border: 1px solid rgba(0,255,163,0.2);
  border-radius: 8px;
  padding: 0.55rem 0.9rem;
  font-size: 0.68rem;
  color: #00FFA3;
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

.qx-fab {
  position: fixed;
  top: 0.65rem;
  left: 0.65rem;
  z-index: 99998;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(0,255,163,0.08);
  border: 1px solid rgba(0,255,163,0.3);
  border-radius: 8px;
  padding: 0.35rem 0.7rem;
  font-size: 0.65rem;
  font-weight: 700;
  color: #00FFA3;
  letter-spacing: 0.08em;
  cursor: pointer;
  backdrop-filter: blur(12px);
  font-family: 'Inter', sans-serif;
  text-transform: uppercase;
  transition: all 0.18s;
}
.qx-fab:hover { background: rgba(0,255,163,0.15); }

.qx-divider {
  border: none;
  border-top: 1px solid rgba(120, 120, 120, 0.2);
  margin: 1rem 0;
}

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(120,120,120,0.2); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,255,163,0.3); }
</style>
""", unsafe_allow_html=True)

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

LOT_SIZES = {
    "NIFTY 50":   50,
    "BANK NIFTY": 15,
    "FIN NIFTY":  40,
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
# PURE PANDAS / NUMPY INDICATORS
# ══════════════════════════════════════════════════════════════════════════════
def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()

def _rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d = s.diff()
    g = d.clip(lower=0)
    l = (-d).clip(lower=0)
    ag = g.ewm(com=n - 1, adjust=False).mean()
    al = l.ewm(com=n - 1, adjust=False).mean()
    rs = ag / al.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def _atr(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    pc = close.shift(1)
    tr = pd.concat([(high - low), (high - pc).abs(), (low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(com=n - 1, adjust=False).mean()

def _vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    typical = (high + low + close) / 3
    cum_tv  = (typical * volume).cumsum()
    cum_vol = volume.replace(0, np.nan).cumsum()
    return cum_tv / cum_vol

def _bbands(s: pd.Series, n: int = 20, std: float = 2.0):
    mid   = s.rolling(n).mean()
    sigma = s.rolling(n).std()
    return mid + std * sigma, mid, mid - std * sigma

def _adx(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    up   = high.diff()
    down = -low.diff()
    plus_dm  = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    tr_s = _atr(high, low, close, n)
    plus_di  = 100 * pd.Series(plus_dm,  index=high.index).ewm(com=n-1, adjust=False).mean() / tr_s.replace(0, np.nan)
    minus_di = 100 * pd.Series(minus_dm, index=high.index).ewm(com=n-1, adjust=False).mean() / tr_s.replace(0, np.nan)
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
    return dx.ewm(com=n-1, adjust=False).mean(), plus_di, minus_di

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING
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
    try:
        df = yf.download(ticker, period="5d", interval="1d",
                         auto_adjust=True, progress=False)
        if df is None or df.empty or len(df) < 2:
            return {}
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        r = df.iloc[-2]
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
    df["VOL_MA20"] = df["Volume"].rolling(20).mean()
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
        atr_pct = atr / close * 100
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
            ema_str = min((e9 - e21) / e21 * 1000, 1.0)
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
            ema_str = min((e21 - e9) / e21 * 1000, 1.0)
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
# AUTO KILL-SWITCH
# ══════════════════════════════════════════════════════════════════════════════
def auto_kill_check(bt: dict, manual_kill: bool) -> tuple[bool, str]:
    if manual_kill:
        return True, "Manual kill switch engaged"
    if bt["total"] >= 5 and bt["win_rate"] < 40:
        return True, f"Win rate {bt['win_rate']}% < 40% threshold — auto-halted"
    return False, ""

# ══════════════════════════════════════════════════════════════════════════════
# PIVOT LEVELS (Fibonacci method)
# ══════════════════════════════════════════════════════════════════════════════
def calculate_pivots(ohlc: dict) -> dict:
    if not ohlc:
        return {}
    H, L, C = ohlc["high"], ohlc["low"], ohlc["close"]
    R = H - L
    P = (H + L + C) / 3
    return {
        "R2": P + 0.618 * R,
        "R1": P + 0.382 * R,
        "P":  P,
        "S1": P - 0.382 * R,
        "S2": P - 0.618 * R,
    }

# ══════════════════════════════════════════════════════════════════════════════
# OPTIONS INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════
def get_atm_strike(ltp: float, index_name: str) -> dict:
    gap = STRIKE_GAPS.get(index_name, 50)
    atm   = round(ltp / gap) * gap
    return {
        "atm":  atm,
        "ce":   atm,
        "pe":   atm,
        "itm_ce": atm - gap,
        "itm_pe": atm + gap,
        "otm_ce": atm + gap,
        "otm_pe": atm - gap,
        "gap":  gap,
    }

def position_size(capital: float, risk_pct: float, sl_pts: float, lot_size: int) -> dict:
    # CRITICAL FIX: Ensure 'margin_est' is returned in all evaluation paths.
    if sl_pts <= 0 or lot_size <= 0:
        return {"lots": 0, "risk_amount": 0, "margin_est": 0}
    risk_amt = capital * risk_pct / 100
    risk_per_lot = sl_pts * lot_size
    lots = int(risk_amt / risk_per_lot) if risk_per_lot > 0 else 0
    return {
        "lots": max(lots, 0),
        "risk_amount": round(risk_amt, 0),
        "margin_est": round(lots * lot_size * 15, 0),
    }

# ══════════════════════════════════════════════════════════════════════════════
# CHART BUILDER
# ══════════════════════════════════════════════════════════════════════════════
def build_chart(df: pd.DataFrame, pivots: dict, sig: dict,
                show_ema: bool, show_vwap: bool, show_bb: bool) -> go.Figure:

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.60, 0.20, 0.20],
        vertical_spacing=0.025,
        subplot_titles=("", "RSI · 14", "Volume"),
    )

    for ann in fig.layout.annotations:
        ann.update(font=dict(size=9, color="rgba(120,120,120,0.65)",
                             family="Inter"), x=0.01, xanchor="left")

    # ── Candlesticks ────────────────────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        increasing=dict(line=dict(color="#00CC88", width=1),
                        fillcolor="rgba(0,204,136,0.6)"),
        decreasing=dict(line=dict(color="#FF4B4B", width=1),
                        fillcolor="rgba(255,75,75,0.6)"),
        name="Price", showlegend=False,
    ), row=1, col=1)

    # ── EMAs ────────────────────────────────────────────────────────────────
    if show_ema and "EMA9" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["EMA9"],
            line=dict(color="#FFD700", width=1.5),
            name="EMA 9", hoverinfo="skip",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["EMA21"],
            line=dict(color="#BB88FF", width=1.5),
            name="EMA 21", hoverinfo="skip",
        ), row=1, col=1)

    # ── VWAP ────────────────────────────────────────────────────────────────
    if show_vwap and "VWAP" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["VWAP"],
            line=dict(color="#5B8CFF", width=1.4, dash="dot"),
            name="VWAP", hoverinfo="skip",
        ), row=1, col=1)

    # ── Bollinger Bands ──────────────────────────────────────────────────────
    if show_bb and "BB_U" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_U"],
            line=dict(color="rgba(255,179,71,0.5)", width=0.9),
            name="BB Upper", hoverinfo="skip", showlegend=False,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_L"],
            line=dict(color="rgba(255,179,71,0.5)", width=0.9),
            name="BB Lower", hoverinfo="skip", showlegend=False,
            fill="tonexty", fillcolor="rgba(255,179,71,0.03)",
        ), row=1, col=1)

    # ── Pivot levels ─────────────────────────────────────────────────────────
    pv_style = {
        "R2": ("#FF4B4B", "dash"), "R1": ("#FF8888", "dot"),
        "P":  ("#5B8CFF", "dash"),
        "S1": ("#66EEB0", "dot"),  "S2": ("#00FFA3", "dash"),
    }
    for lvl, val in pivots.items():
        col, dsh = pv_style.get(lvl, ("#888", "dash"))
        fig.add_hline(
            y=val, line=dict(color=col, width=0.8, dash=dsh),
            annotation_text=f"  {lvl} {val:,.0f}",
            annotation_font=dict(color=col, size=9, family="JetBrains Mono"),
            annotation_position="right", row=1, col=1,
        )

    # ── Signal markers ───────────────────────────────────────────────────────
    if sig["signal"] != "NONE" and sig["entry"]:
        icon  = "▲" if sig["signal"] == "BUY" else "▼"
        color = "#00FFA3" if sig["signal"] == "BUY" else "#FF4B4B"
        fig.add_trace(go.Scatter(
            x=[df.index[-1]], y=[sig["entry"]],
            mode="markers+text",
            marker=dict(size=12, color=color, symbol="triangle-up" if sig["signal"] == "BUY" else "triangle-down"),
            text=[f" {icon} {sig['signal']}"],
            textposition="top center",
            textfont=dict(color=color, size=11, family="JetBrains Mono"),
            name=sig["signal"], showlegend=False,
            hoverinfo="skip",
        ), row=1, col=1)
        
        if sig["sl"]:
            fig.add_hline(y=sig["sl"], line=dict(color="rgba(255,75,75,0.6)", width=1, dash="dot"),
                          annotation_text="  SL", annotation_font=dict(color="#FF4B4B", size=9), row=1, col=1)
        if sig["target"]:
            fig.add_hline(y=sig["target"], line=dict(color="rgba(0,255,163,0.6)", width=1, dash="dot"),
                          annotation_text="  TGT", annotation_font=dict(color="#00FFA3", size=9), row=1, col=1)

    # ── RSI subplot ──────────────────────────────────────────────────────────
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["RSI"],
            line=dict(color="rgba(120,120,120,0.7)", width=1.3),
            fill="tozeroy", fillcolor="rgba(120,120,120,0.04)",
            name="RSI",
        ), row=2, col=1)
        for lv, cl in [(70, "rgba(255,75,75,0.4)"), (60, "rgba(0,255,163,0.35)"),
                       (40, "rgba(255,75,75,0.35)"), (30, "rgba(255,75,75,0.4)")]:
            fig.add_hline(y=lv, line=dict(color=cl, width=0.6, dash="dot"), row=2, col=1)
        fig.add_hrect(y0=60, y1=70, fillcolor="rgba(0,255,163,0.04)", line_width=0, row=2, col=1)
        fig.add_hrect(y0=30, y1=40, fillcolor="rgba(255,75,75,0.04)", line_width=0, row=2, col=1)

    # ── Volume subplot ───────────────────────────────────────────────────────
    if "Volume" in df.columns:
        vol_colors = ["rgba(0,204,136,0.55)" if float(c) >= float(o) else "rgba(255,75,75,0.55)"
                      for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            marker_color=vol_colors, name="Volume",
        ), row=3, col=1)
        if "VOL_MA20" in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df["VOL_MA20"],
                line=dict(color="rgba(255,179,71,0.7)", width=1.2),
                name="Vol MA20", hoverinfo="skip",
            ), row=3, col=1)

    # ── Layout ───────────────────────────────────────────────────────────────
    # Neutral Grid values allowing flawless rendering in Dark & Light Modes
    GRID  = "rgba(120,120,120,0.15)"
    PAPER = "rgba(0,0,0,0)"
    fig.update_layout(
        paper_bgcolor=PAPER,
        plot_bgcolor=PAPER,
        font=dict(family="JetBrains Mono, monospace", size=10),
        margin=dict(l=10, r=100, t=20, b=10),
        legend=dict(
            bgcolor="rgba(120,120,120,0.05)",
            bordercolor="rgba(120,120,120,0.2)", borderwidth=1,
            font=dict(size=9), x=0.01, y=0.99,
            orientation="h",
        ),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        hoverlabel=dict(
            font=dict(size=10, family="JetBrains Mono"),
        ),
        height=580,
    )
    for row_n in [1, 2, 3]:
        fig.update_xaxes(
            gridcolor=GRID, showgrid=True, zeroline=False,
            showspikes=True, spikecolor="rgba(120,120,120,0.5)",
            spikedash="dot", spikethickness=1,
            tickfont=dict(size=9),
            row=row_n, col=1,
        )
        fig.update_yaxes(
            gridcolor=GRID, showgrid=True, zeroline=False,
            tickfont=dict(size=9),
            row=row_n, col=1,
        )
    fig.update_yaxes(tickformat=",.0f", row=1, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], tickformat=".0f",
                     tickfont=dict(size=8), row=2, col=1)
    fig.update_yaxes(title_text="Vol", tickformat=".2s",
                     tickfont=dict(size=8), row=3, col=1)
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# EQUITY CURVE CHART
# ══════════════════════════════════════════════════════════════════════════════
def build_equity_curve(equity: list) -> go.Figure:
    fig = go.Figure()
    x   = list(range(len(equity)))
    fig.add_trace(go.Scatter(
        x=x, y=equity,
        line=dict(color="#00FFA3", width=2),
        fill="tozeroy", fillcolor="rgba(0,255,163,0.06)",
        mode="lines", name="Equity",
    ))
    fig.add_hline(y=equity[0], line=dict(color="rgba(120,120,120,0.3)", width=0.8, dash="dot"))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=20, b=10),
        height=200,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(gridcolor="rgba(120,120,120,0.15)", zeroline=False,
                   tickformat=",.0f", tickfont=dict(size=9)),
        hovermode="x",
        hoverlabel=dict(font=dict(size=10, family="JetBrains Mono")),
    )
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# TRADE LOG
# ══════════════════════════════════════════════════════════════════════════════
def update_trade_log(sig: dict, index_name: str):
    if "trade_log" not in st.session_state:
        st.session_state.trade_log = []
    if sig["signal"] != "NONE" and sig["entry"]:
        log = st.session_state.trade_log
        if not log or log[0]["signal"] != sig["signal"] or log[0]["index"] != index_name:
            st.session_state.trade_log = [{
                "time":   datetime.now().strftime("%H:%M:%S"),
                "index":  index_name,
                "signal": sig["signal"],
                "entry":  sig["entry"],
                "sl":     sig["sl"],
                "target": sig["target"],
                "score":  sig.get("score", 0),
            }] + log[:14]

# ══════════════════════════════════════════════════════════════════════════════
# MARKET STATUS (IST)
# ══════════════════════════════════════════════════════════════════════════════
def market_status() -> tuple[bool, str]:
    now = datetime.now()
    mo  = now.replace(hour=9,  minute=15, second=0, microsecond=0)
    mc  = now.replace(hour=15, minute=30, second=0, microsecond=0)
    is_open = mo <= now <= mc and now.weekday() < 5
    return is_open, now.strftime("%d %b %Y  %H:%M:%S")

# ══════════════════════════════════════════════════════════════════════════════
# SCORE ARC SVG
# ══════════════════════════════════════════════════════════════════════════════
def score_arc_svg(score: float, signal: str) -> str:
    color = "#00FFA3" if signal == "BUY" else ("#FF4B4B" if signal == "SELL" else "#5B8CFF")
    pct   = score / 100
    r     = 38
    cx, cy = 50, 50
    circumf = 2 * np.pi * r
    arc_len = pct * circumf * 0.75
    gap     = circumf - arc_len

    start_angle = 135 * np.pi / 180
    end_angle   = (135 + 270 * pct) * np.pi / 180
    x1 = cx + r * np.cos(start_angle)
    y1 = cy + r * np.sin(start_angle)
    x2 = cx + r * np.cos(end_angle)
    y2 = cy + r * np.sin(end_angle)
    large = 1 if 270 * pct > 180 else 0

    sig_color = {"BUY": "#00FFA3", "SELL": "#FF4B4B", "NONE": "#5B8CFF"}.get(signal, "#5B8CFF")
    sig_label = signal if signal != "NONE" else "WAIT"

    return f"""
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" width="110" height="110">
      <path d="M {cx + r * np.cos(135 * np.pi/180):.2f} {cy + r * np.sin(135 * np.pi/180):.2f}
               A {r} {r} 0 1 1 {cx + r * np.cos(45 * np.pi/180):.2f} {cy + r * np.sin(45 * np.pi/180):.2f}"
            fill="none" stroke="rgba(120,120,120,0.15)" stroke-width="6"
            stroke-linecap="round"/>
      {'<path d="M ' + f'{x1:.2f} {y1:.2f} A {r} {r} 0 {large} 1 {x2:.2f} {y2:.2f}"' +
       f' fill="none" stroke="{color}" stroke-width="6" stroke-linecap="round"/>' if pct > 0 else ''}
      <text x="50" y="47" text-anchor="middle" dominant-baseline="middle"
            font-family="JetBrains Mono" font-size="18" font-weight="700" fill="{color}">{int(score)}</text>
      <text x="50" y="62" text-anchor="middle" dominant-baseline="middle"
            font-family="Inter" font-size="6.5" font-weight="700" fill="{sig_color}"
            letter-spacing="1">{sig_label}</text>
    </svg>
    """

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════
if "trade_log" not in st.session_state:
    st.session_state.trade_log = []
if "capital" not in st.session_state:
    st.session_state.capital = 500000
if "risk_pct" not in st.session_state:
    st.session_state.risk_pct = 1.0

is_open, ts_now = market_status()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div class="qx-wordmark">Quant<span class="acc">X</span></div>'
        '<div class="qx-tagline">F&amp;O Intelligence Terminal · v4</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="qx-section">Market Index</div>', unsafe_allow_html=True)
    selected_label = st.selectbox("Index", list(INDICES.keys()), label_visibility="collapsed")
    ticker   = INDICES[selected_label]
    lot_size = LOT_SIZES[selected_label]

    st.markdown('<div class="qx-section">Timeframe</div>', unsafe_allow_html=True)
    tf_label = st.radio("TF", list(TIMEFRAMES.keys()), horizontal=True, label_visibility="collapsed")
    interval = TIMEFRAMES[tf_label]

    st.markdown('<div class="qx-section">Chart Overlays</div>', unsafe_allow_html=True)
    show_ema  = st.toggle("EMA 9 / 21",        value=True)
    show_vwap = st.toggle("VWAP",              value=True)
    show_bb   = st.toggle("Bollinger Bands",   value=False)

    st.markdown('<div class="qx-section">Risk Management</div>', unsafe_allow_html=True)
    capital  = st.number_input("Capital (₹)", value=st.session_state.capital,
                                step=50000, min_value=10000, label_visibility="visible")
    risk_pct = st.slider("Risk per Trade (%)", 0.5, 3.0, st.session_state.risk_pct, 0.25)
    st.session_state.capital  = capital
    st.session_state.risk_pct = risk_pct

    st.markdown('<div class="qx-section">Kill Switch</div>', unsafe_allow_html=True)
    manual_kill = st.toggle("Halt All Signals", value=False)

    st.markdown('<div class="qx-section">Auto Refresh</div>', unsafe_allow_html=True)
    refresh_sec = st.slider("Interval (sec)", 15, 120, 30, 5, label_visibility="collapsed")
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=refresh_sec * 1000, key="qx_refresh")

    st.markdown("---")
    dot_c  = "#00FFA3" if is_open else "#FF4B4B"
    mkt_s  = "LIVE · NSE/BSE" if is_open else "CLOSED · NSE/BSE"
    st.markdown(f"""
    <div style="font-size:0.67rem;font-weight:700;letter-spacing:0.1em;color:{dot_c}">
      <span class="qx-dot" style="background:{dot_c};box-shadow:0 0 6px {dot_c}"></span>
      {mkt_s}
    </div>
    <p style="font-size:0.63rem;opacity:0.6;margin-top:0.3rem;font-family:'JetBrains Mono',monospace">{ts_now}</p>
    <p style="font-size:0.6rem;opacity:0.5;margin-top:0.8rem">
      Signal fires at score ≥ {SIGNAL_THRESHOLD}/100<br>
      Auto-halts if win rate &lt; 40%
    </p>
    """, unsafe_allow_html=True)

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
# FLOATING CONTROL INTERFACES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<button class="qx-fab" onclick="(function(){
  var b=window.parent.document.querySelector('[data-testid=\\'stSidebarCollapsedControl\\'] button')
       ||window.parent.document.querySelector('[data-testid=\\'collapsedControl\\'] button');
  if(b){b.click();}else{
    var all=window.parent.document.querySelectorAll('button');
    for(var i=0;i<all.length;i++){var r=all[i].getBoundingClientRect();
      if(r.left<80&&r.top<80){all[i].click();break;}}
  }
})()">⚙&nbsp;Controls</button>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER BAR
# ══════════════════════════════════════════════════════════════════════════════
regime_html = {
    "TRENDING": '<span class="qx-regime qx-regime-trend">◈ TRENDING</span>',
    "CHOPPY":   '<span class="qx-regime qx-regime-chop">◈ CHOPPY — SIGNALS PAUSED</span>',
    "VOLATILE": '<span class="qx-regime qx-regime-vol">◈ VOLATILE</span>',
}.get(regime, '<span class="qx-regime qx-regime-chop">◈ UNKNOWN</span>')

dot_c = "#00FFA3" if is_open else "#FF4B4B"
mkt_label = "LIVE" if is_open else "CLOSED"
score = sig.get("score", 0)

ks_html = ""
if kill_sw:
    ks_html = f'<span class="qx-chip qx-chip-red">⛔ HALTED — {kill_reason[:35]}</span>'

st.markdown(f"""
<div class="qx-header">
  <div class="qx-header-left">
    <div>
      <div class="qx-header-title">QuantX &nbsp;<span style="opacity:0.3">|</span>&nbsp; {selected_label} &nbsp;<span style="opacity:0.3">·</span>&nbsp; {tf_label}</div>
      <div class="qx-header-sub">F&amp;O Intelligence Terminal &nbsp;·&nbsp; Signal threshold {SIGNAL_THRESHOLD}/100 &nbsp;·&nbsp; {lot_size} lot</div>
    </div>
    {regime_html}
    {ks_html}
  </div>
  <div style="display:flex;align-items:center;gap:0.6rem">
    <span class="qx-chip {'qx-chip-green' if is_open else 'qx-chip-red'}">
      <span style="display:inline-block;width:5px;height:5px;border-radius:50%;background:{'#00FFA3' if is_open else '#FF4B4B'};margin-right:4px;vertical-align:middle;animation:qx-pulse 2s infinite"></span>
      NSE {mkt_label}
    </span>
    <span class="qx-chip qx-chip-gray" style="font-family:'JetBrains Mono',monospace">{ts_now}</span>
  </div>
</div>
""", unsafe_allow_html=True)

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

st.markdown(f"""
<div class="qx-signal-banner {sc}">
  <div class="qx-signal-main">
    <div style="font-size:2.4rem;line-height:1">{s_icon}</div>
    <div>
      <div class="qx-signal-type {'clr-green' if s == 'BUY' else ('clr-red' if s == 'SELL' else 'clr-blue')}">{s}</div>
      <div class="qx-signal-meta">
        Entry <strong>{f"₹{sig['entry']:,.2f}" if sig['entry'] else '—'}</strong> &nbsp;·&nbsp;
        SL <strong style="color:#FF6B6B">{sl_txt}</strong> &nbsp;·&nbsp;
        Target <strong style="color:#00FFA3">{tgt_txt}</strong><br>
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
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# METRIC CARDS ROW
# ══════════════════════════════════════════════════════════════════════════════
chg_cls   = "clr-green" if day_chg >= 0 else "clr-red"
chg_arrow = "▲" if day_chg >= 0 else "▼"
vol_above = vwap_val > 0 and ltp > vwap_val

c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.markdown(f"""
    <div class="qx-card qx-card-blue">
      <div class="qx-card-icon">📈</div>
      <div class="qx-card-label">LTP · {selected_label}</div>
      <div class="qx-card-value">₹{ltp:,.2f}</div>
      <div class="qx-card-sub"><span class="{chg_cls}">{chg_arrow} {abs(day_chg_pct):.2f}%</span> &nbsp;today</div>
    </div>""", unsafe_allow_html=True)

with c2:
    sl_pct = (abs(ltp - (sig["sl"] or ltp)) / ltp * 100) if sig["sl"] and ltp else 0
    st.markdown(f"""
    <div class="qx-card qx-card-red">
      <div class="qx-card-icon">🛡</div>
      <div class="qx-card-label">Stop Loss · 1.5× ATR</div>
      <div class="qx-card-value clr-red">{sl_txt}</div>
      <div class="qx-card-sub">Risk {sl_pct:.2f}% &nbsp;·&nbsp; ATR ₹{volatility:,.1f}</div>
    </div>""", unsafe_allow_html=True)

with c3:
    rr_pts = abs((sig["target"] or ltp) - ltp) if sig["target"] else 0
    st.markdown(f"""
    <div class="qx-card qx-card-green">
      <div class="qx-card-icon">🎯</div>
      <div class="qx-card-label">Target · 1:2 R/R</div>
      <div class="qx-card-value clr-green">{tgt_txt}</div>
      <div class="qx-card-sub">Reward ₹{rr_pts:,.1f} &nbsp;·&nbsp; 1:2 ratio</div>
    </div>""", unsafe_allow_html=True)

with c4:
    vwap_cls  = "clr-green" if vol_above else "clr-red"
    vwap_side = "ABOVE" if vol_above else "BELOW"
    st.markdown(f"""
    <div class="qx-card qx-card-amber">
      <div class="qx-card-icon">⚖</div>
      <div class="qx-card-label">VWAP · Institutional</div>
      <div class="qx-card-value">₹{vwap_val:,.1f}</div>
      <div class="qx-card-sub">Price <span class="{vwap_cls}">{vwap_side}</span> VWAP</div>
    </div>""", unsafe_allow_html=True)

with c5:
    adx_txt = "STRONG" if adx_val > 25 else ("WEAK" if adx_val < 18 else "MOD")
    adx_cls = "clr-green" if adx_val > 25 else ("clr-red" if adx_val < 18 else "clr-amber")
    st.markdown(f"""
    <div class="qx-card qx-card-neutral">
      <div class="qx-card-icon">📡</div>
      <div class="qx-card-label">ADX · Trend Strength</div>
      <div class="qx-card-value">{adx_val:.1f}</div>
      <div class="qx-card-sub"><span class="{adx_cls}">{adx_txt} TREND</span> &nbsp;·&nbsp; RSI {rsi_val:.1f}</div>
    </div>""", unsafe_allow_html=True)

with c6:
    wr_cls = "clr-green" if bt["win_rate"] >= 55 else ("clr-amber" if bt["win_rate"] >= 40 else "clr-red")
    st.markdown(f"""
    <div class="qx-card {'qx-card-green' if bt['win_rate'] >= 55 else ('qx-card-amber' if bt['win_rate'] >= 40 else 'qx-card-red')}">
      <div class="qx-card-icon">🏆</div>
      <div class="qx-card-label">Backtest Win Rate</div>
      <div class="qx-card-value {wr_cls}">{bt['win_rate']}%</div>
      <div class="qx-card-sub">{bt['wins']}W / {bt['losses']}L &nbsp;·&nbsp; {bt['total']} trades</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

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

        st.markdown(f"""
        <table class="qx-mtf-table">
          <thead><tr><th>TF</th><th>Bias</th><th>RSI</th></tr></thead>
          <tbody>{mtf_rows}</tbody>
        </table>
        <p style="font-size:0.65rem;margin-top:0.6rem" class="{align_note_color}">Alignment: {align_note}</p>
        """, unsafe_allow_html=True)

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
            st.markdown(f"""
            <table class="qx-pivot-table">
              <thead><tr><th>Level</th><th></th><th>Price</th><th style="text-align:right">vs LTP</th></tr></thead>
              <tbody>{rows_html}</tbody>
            </table>""", unsafe_allow_html=True)
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
                st.markdown(f"""
                <div class="qx-log-entry">
                  <div>
                    <div class="qx-log-time">{e['time']}</div>
                    <div class="qx-log-idx">{e['index']}</div>
                    <div class="qx-log-price">₹{e['entry']:,.2f}</div>
                    <div class="qx-log-levels">{sl_s} &nbsp; {tgt_s} &nbsp; {sc_s}</div>
                  </div>
                  <span class="qx-log-badge {bc}">{e['signal']}</span>
                </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — BACKTEST RESULTS
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="qx-section">Walk-Forward Backtest · Last 40 Bars</div>', unsafe_allow_html=True)

    if kill_sw:
        st.markdown(f'<div class="qx-ks-halted">⛔ &nbsp; AUTO KILL-SWITCH ACTIVE — {kill_reason}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="qx-ks-active">✅ &nbsp; SIGNALS ACTIVE — Win rate above threshold</div>', unsafe_allow_html=True)

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
            st.markdown(f"""
            <div class="qx-bt-stat">
              <div class="qx-bt-stat-val {vc}">{val}</div>
              <div class="qx-bt-stat-lbl">{lbl}</div>
            </div>""", unsafe_allow_html=True)

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
            st.dataframe(
                df_trades.style
                    .applymap(lambda v: "color:#00FFA3" if v == "WIN" else ("color:#FF4B4B" if v == "LOSS" else ""), subset=["Result"])
                    .applymap(lambda v: "color:#00FFA3" if isinstance(v, float) and v > 0 else ("color:#FF4B4B" if isinstance(v, float) and v < 0 else ""), subset=["P&L (R)"])
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

        ce_color = "qx-card-green" if s == "BUY" else "qx-card-neutral"
        pe_color = "qx-card-red"   if s == "SELL" else "qx-card-neutral"

        st.markdown(f"""
        <div class="qx-opt-card" style="border-left:3px solid rgba(0,255,163,0.4)">
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
        """, unsafe_allow_html=True)

        st.markdown('<div class="qx-section">Index Specifications</div>', unsafe_allow_html=True)
        spec_rows = ""
        for idx_n, idx_t in INDICES.items():
            active = "rgba(0,255,163,0.04)" if idx_n == selected_label else "transparent"
            spec_rows += f"""
            <tr style="background:{active}">
              <td style="font-weight:{'700' if idx_n == selected_label else '400'}">
                {idx_n}
              </td>
              <td>{LOT_SIZES[idx_n]}</td>
              <td>{STRIKE_GAPS[idx_n]}</td>
            </tr>"""
        st.markdown(f"""
        <table class="qx-pivot-table">
          <thead><tr><th>Index</th><th>Lot Size</th><th>Strike Gap</th></tr></thead>
          <tbody>{spec_rows}</tbody>
        </table>""", unsafe_allow_html=True)

    with col_pos:
        st.markdown('<div class="qx-section">Position Size Calculator</div>', unsafe_allow_html=True)

        sl_pts = abs(ltp - (sig["sl"] or ltp))
        pos    = position_size(capital, risk_pct, sl_pts, lot_size)

        st.markdown(f"""
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

        <div class="qx-opt-card" style="border-left:3px solid rgba(0,255,163,0.4);margin-top:0.5rem">
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
        """, unsafe_allow_html=True)

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
            bar_colors    = ["rgba(0,255,163,0.7)" if a >= m * 0.7 else
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
        st.markdown(f"""
        <table class="qx-pivot-table">
          <thead><tr><th>Indicator</th><th>Value</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="qx-section">Session Summary</div>', unsafe_allow_html=True)
        log = st.session_state.get("trade_log", [])
        sess_buy  = sum(1 for e in log if e["signal"] == "BUY")
        sess_sell = sum(1 for e in log if e["signal"] == "SELL")
        st.markdown(f"""
        <div class="qx-opt-card">
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5rem">
            <div style="text-align:center">
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.5rem;font-weight:700">{len(log)}</div>
              <div style="font-size:0.6rem;opacity:0.5;text-transform:uppercase;letter-spacing:0.1em">Signals</div>
            </div>
            <div style="text-align:center">
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.5rem;font-weight:700;color:#00FFA3">{sess_buy}</div>
              <div style="font-size:0.6rem;opacity:0.5;text-transform:uppercase;letter-spacing:0.1em">BUY</div>
            </div>
            <div style="text-align:center">
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.5rem;font-weight:700;color:#FF4B4B">{sess_sell}</div>
              <div style="font-size:0.6rem;opacity:0.5;text-transform:uppercase;letter-spacing:0.1em">SELL</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="qx-section">Full Signal Log</div>', unsafe_allow_html=True)
        if log:
            df_log = pd.DataFrame(log)
            df_log = df_log[["time", "index", "signal", "entry", "sl", "target", "score"]].copy()
            df_log.columns = ["Time", "Index", "Signal", "Entry ₹", "SL ₹", "Target ₹", "Score"]
            st.dataframe(
                df_log.style
                    .applymap(lambda v: "color:#00FFA3" if v == "BUY" else ("color:#FF4B4B" if v == "SELL" else ""), subset=["Signal"])
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
        st.markdown(f"""
        <table class="qx-pivot-table">
          <thead><tr><th>Component</th><th>Status</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)

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
