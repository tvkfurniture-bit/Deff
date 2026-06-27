"""
QuantX v5 — Elite F&O Intelligence Terminal
============================================
Production-hardened build. Key improvements over v4:
  • Full IST timezone enforcement (pytz-free via datetime.timezone + timedelta)
  • Pre-Market / Post-Market / Live badge logic
  • Zero-volume VWAP guard (NaN-safe cumulative)
  • Flat-RSI guard (zero gain/loss → returns 50)
  • ATR fallback to HL-range SMA when history is thin
  • fetch_prev_day looks back up to 10 trading days (holiday/Monday-safe)
  • All UI formatting paths guard against None / NaN / 0
  • Session state keys preserved across auto-refresh
  • Plotly margins tuned for 360 px viewport
  • position_size / get_atm_strike always return safe defaults
  • Pure pandas/numpy — no pandas-ta / TA-Lib / numba dependency
Deploy: Python 3.11 (pin via .python-version), Streamlit Community Cloud
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, timezone
import math
import warnings
warnings.filterwarnings("ignore")

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG  (must be first Streamlit call)
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="QuantX · F&O Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
  font-family: 'Inter', sans-serif;
}

.stApp::before {
  content: '';
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: repeating-linear-gradient(
    0deg, transparent, transparent 2px,
    rgba(120,120,120,0.013) 2px, rgba(120,120,120,0.013) 4px
  );
  pointer-events: none;
  z-index: 0;
}

/* ── Chrome suppression ───────────────────────────────────────────────────── */
#MainMenu, footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

header[data-testid="stHeader"] {
  background: transparent !important;
  height: 0 !important;
}

.block-container {
  padding: 1rem 1rem 3rem 1rem !important;
  max-width: 100% !important;
}

[data-testid="stSidebar"] {
  border-right: 1px solid rgba(120,120,120,0.1) !important;
  padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid rgba(120,120,120,0.15) !important;
  gap: 0 !important; padding: 0 !important;
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
  background: rgba(120,120,120,0.05) !important;
}
[data-testid="stTabPanel"] {
  padding-top: 1rem !important;
  background: transparent !important;
}

.js-plotly-plot, .plotly, .plot-container {
  border-radius: 12px !important;
  overflow: hidden !important;
}
[data-testid="stDataFrame"] {
  border: 1px solid rgba(120,120,120,0.15) !important;
  border-radius: 10px !important;
  overflow: hidden !important;
}
[data-testid="stSpinner"] { color: #00E676 !important; }
[data-testid="stAlert"] {
  background: rgba(255,75,75,0.08) !important;
  border: 1px solid rgba(255,75,75,0.25) !important;
  border-radius: 10px !important;
  color: #FF6B6B !important;
}

/* ═══════ COMPONENTS ════════════════════════════════════════════════════════ */

.qx-wordmark {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.55rem; font-weight: 700;
  letter-spacing: -0.04em; line-height: 1;
  margin-bottom: 0.1rem;
}
.qx-wordmark .acc { color: #00E676; text-shadow: 0 0 20px rgba(0,230,118,0.3); }
.qx-tagline {
  font-size: 0.6rem; letter-spacing: 0.18em;
  text-transform: uppercase; font-weight: 500;
  margin-bottom: 1.8rem; opacity: 0.6;
}
.qx-section {
  display: flex; align-items: center; gap: 0.5rem;
  font-size: 0.58rem; font-weight: 800;
  letter-spacing: 0.18em; text-transform: uppercase;
  margin: 1.4rem 0 0.7rem 0; opacity: 0.5;
}
.qx-section::after {
  content: ''; flex: 1; height: 1px;
  background: rgba(120,120,120,0.2);
}
.qx-dot {
  display: inline-block; width: 6px; height: 6px;
  border-radius: 50%; margin-right: 5px; vertical-align: middle;
  animation: qx-pulse 2s ease-in-out infinite;
}
@keyframes qx-pulse {
  0%,100% { opacity:1; transform:scale(1); }
  50%      { opacity:0.4; transform:scale(0.8); }
}

.qx-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.6rem 1.2rem;
  background: rgba(120,120,120,0.05);
  border: 1px solid rgba(120,120,120,0.15);
  border-radius: 12px; margin-bottom: 1.2rem;
  backdrop-filter: blur(20px);
}
.qx-header-left { display:flex; align-items:center; gap:1rem; }
.qx-header-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82rem; font-weight: 700; letter-spacing: -0.01em;
}
.qx-header-sub { font-size:0.65rem; letter-spacing:0.05em; margin-top:0.1rem; opacity:0.7; }

.qx-chip {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem; font-weight: 700;
  padding: 0.2rem 0.6rem; border-radius: 20px; letter-spacing: 0.05em;
}
.qx-chip-green  { background:rgba(0,230,118,0.1);   border:1px solid rgba(0,230,118,0.3);   color:#00E676; }
.qx-chip-red    { background:rgba(255,61,0,0.1);    border:1px solid rgba(255,61,0,0.3);    color:#FF3D00; }
.qx-chip-amber  { background:rgba(255,179,71,0.1);  border:1px solid rgba(255,179,71,0.3);  color:#FFB347; }
.qx-chip-blue   { background:rgba(91,140,255,0.1);  border:1px solid rgba(91,140,255,0.3);  color:#5B8CFF; }
.qx-chip-gray   { background:rgba(120,120,120,0.1); border:1px solid rgba(120,120,120,0.2); }

/* ── Metrics grid ─────────────────────────────────────────────────────────── */
.qx-metrics-grid { display:flex; flex-wrap:wrap; gap:0.75rem; width:100%; margin-bottom:1rem; }
.qx-card {
  flex: 1 1 150px; position:relative;
  background: rgba(120,120,120,0.05);
  border: 1px solid rgba(120,120,120,0.15);
  border-radius: 12px; padding: 1rem; overflow: hidden;
  transition: border-color 0.25s, box-shadow 0.25s;
}
.qx-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; opacity:0.9; }
.qx-card-green  { border-color:rgba(0,230,118,0.15); }
.qx-card-green::before  { background:linear-gradient(90deg,#00E676 0%,transparent 70%); }
.qx-card-green:hover    { border-color:rgba(0,230,118,0.35); box-shadow:0 0 24px rgba(0,230,118,0.06); }
.qx-card-red    { border-color:rgba(255,61,0,0.15); }
.qx-card-red::before    { background:linear-gradient(90deg,#FF3D00 0%,transparent 70%); }
.qx-card-red:hover      { border-color:rgba(255,61,0,0.35); box-shadow:0 0 24px rgba(255,61,0,0.06); }
.qx-card-blue   { border-color:rgba(91,140,255,0.15); }
.qx-card-blue::before   { background:linear-gradient(90deg,#5B8CFF 0%,transparent 70%); }
.qx-card-blue:hover     { border-color:rgba(91,140,255,0.35); box-shadow:0 0 24px rgba(91,140,255,0.06); }
.qx-card-amber  { border-color:rgba(255,179,71,0.15); }
.qx-card-amber::before  { background:linear-gradient(90deg,#FFB347 0%,transparent 70%); }
.qx-card-amber:hover    { border-color:rgba(255,179,71,0.35); box-shadow:0 0 24px rgba(255,179,71,0.06); }
.qx-card-neutral { border-color:rgba(120,120,120,0.15); }
.qx-card-neutral::before { background:linear-gradient(90deg,rgba(120,120,120,0.4) 0%,transparent 70%); }

.qx-card-label {
  font-size:0.58rem; font-weight:700; letter-spacing:0.12em;
  text-transform:uppercase; opacity:0.6; margin-bottom:0.4rem;
}
.qx-card-value {
  font-family:'JetBrains Mono',monospace;
  font-size:1.15rem; font-weight:700;
  line-height:1.1; letter-spacing:-0.02em;
}
.qx-card-sub   { font-size:0.62rem; margin-top:0.35rem; font-weight:400; opacity:0.8; }
.qx-card-icon  { position:absolute; top:0.8rem; right:0.8rem; font-size:0.9rem; opacity:0.15; }

.clr-green { color:#00E676 !important; }
.clr-red   { color:#FF3D00 !important; }
.clr-blue  { color:#5B8CFF !important; }
.clr-amber { color:#FFB347 !important; }

/* ── Signal banner ────────────────────────────────────────────────────────── */
.qx-signal-banner {
  display:flex; align-items:center; justify-content:space-between;
  padding:1rem 1.5rem; border-radius:14px;
  margin-bottom:1.2rem; border:1px solid; position:relative; overflow:hidden;
}
.qx-signal-banner::before { content:''; position:absolute; inset:0; opacity:0.04; }
.qx-signal-banner.buy  { border-color:rgba(0,230,118,0.35); background:rgba(0,230,118,0.05); }
.qx-signal-banner.buy::before { background:#00E676; }
.qx-signal-banner.sell { border-color:rgba(255,61,0,0.35);  background:rgba(255,61,0,0.05);  }
.qx-signal-banner.sell::before { background:#FF3D00; }
.qx-signal-banner.none { border-color:rgba(120,120,120,0.2); background:rgba(120,120,120,0.05); }
.qx-signal-main   { display:flex; align-items:center; gap:1rem; }
.qx-signal-type   { font-family:'JetBrains Mono',monospace; font-size:2rem; font-weight:700; letter-spacing:-0.02em; line-height:1; }
.qx-signal-meta   { font-size:0.72rem; line-height:1.6; opacity:0.9; }
.qx-score-wrap    { text-align:center; }
.qx-score-label   { font-size:0.58rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; opacity:0.6; margin-top:0.2rem; }

/* ── Regime ───────────────────────────────────────────────────────────────── */
.qx-regime { display:inline-flex; align-items:center; gap:0.4rem; font-size:0.65rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; padding:0.28rem 0.75rem; border-radius:20px; }
.qx-regime-trend { background:rgba(0,230,118,0.08);  border:1px solid rgba(0,230,118,0.25);  color:#00E676; }
.qx-regime-chop  { background:rgba(255,179,71,0.08); border:1px solid rgba(255,179,71,0.25); color:#FFB347; }
.qx-regime-vol   { background:rgba(255,61,0,0.08);   border:1px solid rgba(255,61,0,0.25);   color:#FF3D00; }

/* ── Tables ───────────────────────────────────────────────────────────────── */
.qx-mtf-table, .qx-pivot-table {
  width:100%; border-collapse:collapse;
  font-family:'JetBrains Mono',monospace; font-size:0.78rem;
}
.qx-mtf-table th, .qx-pivot-table th {
  padding:0.5rem 0.75rem; text-align:left;
  font-family:'Inter',sans-serif; font-size:0.58rem;
  font-weight:700; letter-spacing:0.12em; text-transform:uppercase;
  opacity:0.6; border-bottom:1px solid rgba(120,120,120,0.2);
}
.qx-mtf-table td, .qx-pivot-table td {
  padding:0.6rem 0.75rem;
  border-bottom:1px solid rgba(120,120,120,0.1);
  vertical-align:middle;
}
.qx-mtf-table tr:last-child td, .qx-pivot-table tr:last-child td { border-bottom:none; }
.qx-mtf-table tr:hover td, .qx-pivot-table tr:hover td { background:rgba(120,120,120,0.05); }
.qx-mtf-pill { display:inline-block; padding:0.18rem 0.6rem; border-radius:4px; font-size:0.68rem; font-weight:700; }
.mtf-bull { background:rgba(0,230,118,0.1);   color:#00E676; }
.mtf-bear { background:rgba(255,61,0,0.1);    color:#FF3D00; }
.mtf-neut { background:rgba(120,120,120,0.1); }
.pv-r { color:#FF6B6B; font-weight:600; }
.pv-s { color:#00E676; font-weight:600; }
.pv-p { color:#5B8CFF; font-weight:600; }
.pv-pos { color:#00E676; }
.pv-neg { color:#FF3D00; }

/* ── Log entries ──────────────────────────────────────────────────────────── */
.qx-log-entry {
  display:flex; align-items:center; justify-content:space-between;
  padding:0.75rem 1rem;
  background:rgba(120,120,120,0.05);
  border:1px solid rgba(120,120,120,0.15);
  border-radius:10px; margin-bottom:0.4rem;
  transition:border-color 0.2s;
}
.qx-log-entry:hover { border-color:rgba(120,120,120,0.3); }
.qx-log-time   { font-family:'JetBrains Mono',monospace; font-size:0.65rem; opacity:0.5; }
.qx-log-idx    { font-size:0.65rem; font-weight:600; opacity:0.7; margin-top:0.15rem; }
.qx-log-price  { font-family:'JetBrains Mono',monospace; font-size:0.82rem; font-weight:600; }
.qx-log-levels { font-size:0.62rem; opacity:0.5; font-family:'JetBrains Mono',monospace; }
.qx-log-badge  { font-family:'JetBrains Mono',monospace; font-size:0.7rem; font-weight:700; padding:0.25rem 0.7rem; border-radius:6px; letter-spacing:0.06em; }
.qx-log-badge.buy  { background:rgba(0,230,118,0.1);  color:#00E676; border:1px solid rgba(0,230,118,0.25); }
.qx-log-badge.sell { background:rgba(255,61,0,0.1);   color:#FF3D00; border:1px solid rgba(255,61,0,0.25); }

/* ── Options cards ────────────────────────────────────────────────────────── */
.qx-opt-card { background:rgba(120,120,120,0.05); border:1px solid rgba(120,120,120,0.15); border-radius:12px; padding:1rem 1.2rem; margin-bottom:0.5rem; }
.qx-opt-header { font-size:0.6rem; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; opacity:0.6; margin-bottom:0.6rem; }
.qx-opt-strike { font-family:'JetBrains Mono',monospace; font-size:1.4rem; font-weight:700; letter-spacing:-0.02em; line-height:1; }
.qx-opt-meta   { font-size:0.7rem; opacity:0.7; margin-top:0.35rem; }

/* ── Kill switch badges ───────────────────────────────────────────────────── */
.qx-ks-halted {
  background:rgba(255,61,0,0.06); border:1px solid rgba(255,61,0,0.25);
  border-radius:8px; padding:0.55rem 0.9rem;
  font-size:0.68rem; color:#FF3D00; text-align:center;
  font-weight:700; letter-spacing:0.08em; text-transform:uppercase;
}
.qx-ks-active {
  background:rgba(0,230,118,0.05); border:1px solid rgba(0,230,118,0.2);
  border-radius:8px; padding:0.55rem 0.9rem;
  font-size:0.68rem; color:#00E676; text-align:center;
  font-weight:700; letter-spacing:0.08em; text-transform:uppercase;
}
.qx-bt-stat { background:rgba(120,120,120,0.05); border:1px solid rgba(120,120,120,0.15); border-radius:10px; padding:0.85rem 1rem; text-align:center; }
.qx-bt-stat-val { font-family:'JetBrains Mono',monospace; font-size:1.25rem; font-weight:700; line-height:1; }
.qx-bt-stat-lbl { font-size:0.58rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; opacity:0.6; margin-top:0.3rem; }

.qx-divider { border:none; border-top:1px solid rgba(120,120,120,0.2); margin:1rem 0; }

::-webkit-scrollbar       { width:4px; height:4px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:rgba(120,120,120,0.2); border-radius:2px; }
::-webkit-scrollbar-thumb:hover { background:rgba(0,230,118,0.3); }

/* ── Mobile ───────────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .block-container { padding:0.5rem 0.5rem 2rem 0.5rem !important; }
  .qx-header { flex-direction:column; align-items:flex-start; gap:0.6rem; padding:0.6rem 0.8rem; }
  .qx-signal-banner { flex-direction:column; gap:1rem; align-items:center; text-align:center; padding:1rem; }
  .qx-signal-main   { flex-direction:column; gap:0.4rem; }
  .qx-opt-strike    { font-size:1.15rem; }
  .qx-card          { flex: 1 1 130px; }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SAFE HTML RENDER
# ══════════════════════════════════════════════════════════════════════════════
def render_html(html_str: str):
    st.markdown(" ".join(html_str.split()), unsafe_allow_html=True)

def _safe_fmt(val, fmt="₹{:,.2f}", fallback="—"):
    """Format a numeric value safely; return fallback on None/NaN/inf."""
    try:
        if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
            return fallback
        return fmt.format(val)
    except Exception:
        return fallback

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
INDICES = {
    "NIFTY 50":   "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "FIN NIFTY":  "^CNXFIN",
    "SENSEX":     "^BSESN",
    "BSE BANKEX": "BSE-BANKEX.BO",
}

# NSE F&O lot sizes (June 2024 revision)
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
TF_PERIODS = {"1m": "1d",  "5m": "3d", "15m": "5d", "1h": "30d"}

SCORE_WEIGHTS = {
    "ema_cross":   25,
    "rsi_zone":    20,
    "vwap_side":   20,
    "bb_position": 15,
    "volume_conf": 10,
    "adx_trend":   10,
}

SIGNAL_THRESHOLD = 70

# IST offset — no pytz needed
IST = timezone(timedelta(hours=5, minutes=30))

# ══════════════════════════════════════════════════════════════════════════════
# PURE PANDAS / NUMPY INDICATORS  (hardened)
# ══════════════════════════════════════════════════════════════════════════════

def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _rsi(s: pd.Series, n: int = 14) -> pd.Series:
    """Wilder RSI.  Zero-movement guard: returns 50 when gain=loss=0."""
    d    = s.diff()
    gain = d.clip(lower=0)
    loss = (-d).clip(lower=0)
    avg_gain = gain.ewm(com=n - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=n - 1, adjust=False).mean()

    # Where both are zero (flat price) avoid 0/0 → NaN; give 50
    both_zero = (avg_gain == 0) & (avg_loss == 0)
    rs        = avg_gain / avg_loss.replace(0, np.nan)
    rsi_raw   = 100 - (100 / (1 + rs))
    rsi_raw[both_zero] = 50.0
    return rsi_raw.fillna(50.0)


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    """Wilder ATR with HL-range SMA fallback when history is thin."""
    pc  = close.shift(1)
    tr  = pd.concat(
        [(high - low), (high - pc).abs(), (low - pc).abs()], axis=1
    ).max(axis=1)

    # Wilder smooth; if < n bars exist, fall back to SMA of HL range
    atr_wilder = tr.ewm(com=n - 1, adjust=False).mean()
    atr_sma    = (high - low).rolling(min(n, len(high))).mean()
    return atr_wilder.fillna(atr_sma).fillna(high - low)


def _vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Session VWAP.  Zero-volume bars are skipped (contribute 0 to both numerator and denominator)."""
    typical = (high + low + close) / 3
    vol_safe = volume.clip(lower=0)          # ensure no negatives
    cum_tv   = (typical * vol_safe).cumsum()
    cum_vol  = vol_safe.cumsum()
    # Where cumulative volume is 0 (all-zero volume history) return close
    return (cum_tv / cum_vol.replace(0, np.nan)).fillna(close)


def _bbands(s: pd.Series, n: int = 20, std_mult: float = 2.0):
    mid   = s.rolling(n, min_periods=max(1, n // 2)).mean()
    sigma = s.rolling(n, min_periods=max(1, n // 2)).std().fillna(0)
    return mid + std_mult * sigma, mid, mid - std_mult * sigma


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14):
    up   = high.diff()
    down = -low.diff()
    plus_dm  = pd.Series(np.where((up > down) & (up > 0),   up.values,   0.0), index=high.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down.values, 0.0), index=high.index)
    tr_s     = _atr(high, low, close, n)
    safe_tr  = tr_s.replace(0, np.nan)
    plus_di  = 100 * plus_dm.ewm(com=n-1, adjust=False).mean() / safe_tr
    minus_di = 100 * minus_dm.ewm(com=n-1, adjust=False).mean() / safe_tr
    sum_di   = (plus_di + minus_di).replace(0, np.nan)
    dx       = (100 * (plus_di - minus_di).abs() / sum_di).fillna(0)
    adx_line = dx.ewm(com=n-1, adjust=False).mean()
    return adx_line.fillna(0), plus_di.fillna(0), minus_di.fillna(0)

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING  (hardened)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=30, show_spinner=False)
def fetch_data(ticker: str, interval: str) -> pd.DataFrame:
    period = TF_PERIODS.get(interval, "5d")
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False)
        if df is None or df.empty:
            return pd.DataFrame()
        # Flatten MultiIndex columns (yfinance ≥0.2)
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        # Drop rows where Close is NaN
        df = df[df["Close"].notna()].copy()
        # Fill remaining NaN volumes with 0
        if "Volume" in df.columns:
            df["Volume"] = df["Volume"].fillna(0)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_prev_day(ticker: str) -> dict:
    """
    Look back up to 10 calendar days to find the most recent completed
    trading day OHLC.  Handles Mondays and post-holiday gaps correctly.
    """
    try:
        df = yf.download(ticker, period="15d", interval="1d",
                         auto_adjust=True, progress=False)
        if df is None or df.empty:
            return {}
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df[df["Close"].notna()]
        if len(df) < 2:
            return {}
        # Use the second-to-last available row (last completed day)
        r = df.iloc[-2]
        return {
            "high":  float(r["High"]),
            "low":   float(r["Low"]),
            "close": float(r["Close"]),
        }
    except Exception:
        return {}


@st.cache_data(ttl=60, show_spinner=False)
def fetch_mtf_bias(ticker: str) -> dict:
    result = {}
    for tf_label, interval in TIMEFRAMES.items():
        # Bypass cache wrapper to call raw yf.download
        try:
            period = TF_PERIODS.get(interval, "5d")
            df = yf.download(ticker, period=period, interval=interval,
                             auto_adjust=True, progress=False)
            if df is None or df.empty or len(df) < 22:
                result[tf_label] = {"bias": "NEUTRAL", "rsi": None, "ema_diff": 0}
                continue
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            df = df[df["Close"].notna()].copy()
            e9  = float(_ema(df["Close"], 9).iloc[-1])
            e21 = float(_ema(df["Close"], 21).iloc[-1])
            rsi = float(_rsi(df["Close"], 14).iloc[-1])
            diff = (e9 - e21) / (e21 or 1) * 100
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
# INDICATOR COMPUTATION
# ══════════════════════════════════════════════════════════════════════════════

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 5:
        return df
    df = df.copy()
    df["EMA9"]  = _ema(df["Close"], 9)
    df["EMA21"] = _ema(df["Close"], 21)
    df["RSI"]   = _rsi(df["Close"], 14)
    df["ATR"]   = _atr(df["High"], df["Low"], df["Close"], 14)
    df["VWAP"]  = _vwap(df["High"], df["Low"], df["Close"], df["Volume"])
    df["BB_U"], df["BB_M"], df["BB_L"] = _bbands(df["Close"], 20, 2.0)
    adx_v, plus_di, minus_di = _adx(df["High"], df["Low"], df["Close"], 14)
    df["ADX"]      = adx_v
    df["PLUS_DI"]  = plus_di
    df["MINUS_DI"] = minus_di
    df["VOL_MA20"] = df["Volume"].rolling(20, min_periods=1).mean()
    return df

# ══════════════════════════════════════════════════════════════════════════════
# MARKET REGIME
# ══════════════════════════════════════════════════════════════════════════════

def detect_regime(df: pd.DataFrame) -> str:
    if df.empty or "ADX" not in df.columns:
        return "UNKNOWN"
    try:
        adx      = float(df["ADX"].iloc[-1])
        atr      = float(df["ATR"].iloc[-1])
        close    = float(df["Close"].iloc[-1])
        atr_pct  = (atr / close * 100) if close else 0
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

def _safe_float(val, fallback=0.0) -> float:
    try:
        f = float(val)
        return fallback if (math.isnan(f) or math.isinf(f)) else f
    except Exception:
        return fallback


def score_signal(df: pd.DataFrame, kill_switch: bool, regime: str) -> dict:
    default = {
        "signal": "NONE", "score": 0, "buy_score": 0, "sell_score": 0,
        "entry": None, "sl": None, "target": None,
        "rsi": None, "atr": None, "ema9": None, "ema21": None,
        "vwap": None, "adx": None, "component_scores": {},
        "kill_reason": None,
    }

    if kill_switch:
        return {**default, "kill_reason": "KILL SWITCH ENGAGED"}
    if df.empty or len(df) < 10:
        return {**default, "kill_reason": "INSUFFICIENT DATA"}
    if regime == "CHOPPY":
        return {**default, "kill_reason": "CHOPPY MARKET — SIGNALS PAUSED"}

    try:
        row    = df.iloc[-1]
        close  = _safe_float(row["Close"])
        e9     = _safe_float(row["EMA9"])
        e21    = _safe_float(row["EMA21"])
        rsi    = _safe_float(row["RSI"],  50.0)
        atr    = _safe_float(row["ATR"])
        vwap   = _safe_float(row.get("VWAP", close), close)
        bb_u   = _safe_float(row.get("BB_U", close + atr))
        bb_l   = _safe_float(row.get("BB_L", close - atr))
        adx    = _safe_float(row.get("ADX",  0))
        vol    = _safe_float(row["Volume"])
        vol_ma = _safe_float(row.get("VOL_MA20", vol), vol or 1)

        if close == 0 or e9 == 0 or e21 == 0:
            return {**default, "kill_reason": "INVALID PRICE DATA"}

        scores = {}

        # ── BUY scoring ──────────────────────────────────────────────────────
        buy_score = 0.0

        ema_str = min(abs(e9 - e21) / (e21 or 1) * 1000, 1.0)
        if e9 > e21:
            buy_score += SCORE_WEIGHTS["ema_cross"] * (0.6 + 0.4 * ema_str)
        scores["ema_cross_buy"] = buy_score

        rsi_buy = 0.0
        if 55 <= rsi <= 70:
            rsi_buy = SCORE_WEIGHTS["rsi_zone"]
        elif 50 < rsi < 55:
            rsi_buy = SCORE_WEIGHTS["rsi_zone"] * 0.6
        buy_score += rsi_buy
        scores["rsi_buy"] = rsi_buy

        vwap_buy = SCORE_WEIGHTS["vwap_side"] if close > vwap else 0.0
        buy_score += vwap_buy
        scores["vwap_buy"] = vwap_buy

        bb_range = max(bb_u - bb_l, 1e-6)
        bb_pos   = (close - bb_l) / bb_range
        bb_buy   = SCORE_WEIGHTS["bb_position"] * min(bb_pos * 1.2, 1.0)
        buy_score += bb_buy
        scores["bb_buy"] = bb_buy

        vol_ratio = vol / (vol_ma or 1)
        vol_conf  = SCORE_WEIGHTS["volume_conf"] * min(vol_ratio / 1.5, 1.0)
        buy_score += vol_conf
        scores["vol_buy"] = vol_conf

        adx_score = SCORE_WEIGHTS["adx_trend"] * min(adx / 35, 1.0)
        buy_score += adx_score
        scores["adx_buy"] = adx_score

        # ── SELL scoring ─────────────────────────────────────────────────────
        sell_score = 0.0
        if e9 < e21:
            sell_score += SCORE_WEIGHTS["ema_cross"] * (0.6 + 0.4 * ema_str)

        rsi_sell = 0.0
        if 30 <= rsi <= 45:
            rsi_sell = SCORE_WEIGHTS["rsi_zone"]
        elif 45 < rsi < 50:
            rsi_sell = SCORE_WEIGHTS["rsi_zone"] * 0.6
        sell_score += rsi_sell

        vwap_sell = SCORE_WEIGHTS["vwap_side"] if close < vwap else 0.0
        sell_score += vwap_sell

        bb_sell = SCORE_WEIGHTS["bb_position"] * min((1 - bb_pos) * 1.2, 1.0)
        sell_score += bb_sell
        sell_score += vol_conf
        sell_score += adx_score

        buy_score  = round(min(buy_score, 100), 1)
        sell_score = round(min(sell_score, 100), 1)

        signal = "NONE"
        score  = max(buy_score, sell_score)
        sl_val = target_val = None

        if buy_score >= SIGNAL_THRESHOLD and buy_score > sell_score and rsi < 75:
            signal    = "BUY"
            score     = buy_score
            sl_val    = close - 1.5 * atr
            target_val = close + 2 * (close - sl_val)
        elif sell_score >= SIGNAL_THRESHOLD and sell_score > buy_score and rsi > 25:
            signal    = "SELL"
            score     = sell_score
            sl_val    = close + 1.5 * atr
            target_val = close - 2 * (sl_val - close)

        return {
            "signal":           signal,
            "score":            score,
            "buy_score":        buy_score,
            "sell_score":       sell_score,
            "entry":            close,
            "sl":               sl_val,
            "target":           target_val,
            "rsi":              rsi,
            "atr":              atr,
            "ema9":             e9,
            "ema21":            e21,
            "vwap":             vwap,
            "adx":              adx,
            "component_scores": scores,
            "kill_reason":      None,
        }

    except Exception as ex:
        return {**default, "kill_reason": f"ENGINE ERROR: {ex}"}

# ══════════════════════════════════════════════════════════════════════════════
# WALK-FORWARD BACKTEST
# ══════════════════════════════════════════════════════════════════════════════

def run_backtest(df: pd.DataFrame, lookback: int = 50) -> dict:
    empty = {"trades": [], "win_rate": 0, "total": 0,
             "wins": 0, "losses": 0, "equity": [10000.0]}
    if df.empty or len(df) < lookback + 10:
        return empty

    df_bt  = df.iloc[-(lookback + 25):].copy()
    trades = []
    equity = [10000.0]

    for i in range(min(25, len(df_bt) - 1), len(df_bt)):
        slice_ = df_bt.iloc[:i]
        if len(slice_) < 10:
            continue
        row  = slice_.iloc[-1]
        prev = slice_.iloc[-2]
        try:
            close   = _safe_float(row["Close"])
            e9      = _safe_float(row.get("EMA9"))
            e21     = _safe_float(row.get("EMA21"))
            rsi     = _safe_float(row.get("RSI"), 50.0)
            atr     = _safe_float(row.get("ATR"))
            vwap    = _safe_float(row.get("VWAP", close), close)
            prev_h  = _safe_float(prev["High"])
            prev_l  = _safe_float(prev["Low"])

            if close == 0 or atr == 0:
                continue
        except Exception:
            continue

        signal = None
        if e9 > e21 and rsi > 58 and close > vwap and close > prev_h:
            signal = "BUY"
            sl_b   = close - 1.5 * atr
            tgt_b  = close + 2 * (close - sl_b)
        elif e9 < e21 and rsi < 42 and close < vwap and close < prev_l:
            signal = "SELL"
            sl_b   = close + 1.5 * atr
            tgt_b  = close - 2 * (sl_b - close)
        else:
            sl_b = tgt_b = None

        if signal and sl_b and tgt_b and len(trades) < lookback:
            future = df_bt.iloc[i: i + 4]
            result = "OPEN"
            pnl    = 0.0
            for _, fr in future.iterrows():
                fh = _safe_float(fr["High"])
                fl = _safe_float(fr["Low"])
                if signal == "BUY":
                    if fl <= sl_b:
                        result = "LOSS"; pnl = sl_b - close; break
                    if fh >= tgt_b:
                        result = "WIN";  pnl = tgt_b - close; break
                else:
                    if fh >= sl_b:
                        result = "LOSS"; pnl = close - sl_b; break
                    if fl <= tgt_b:
                        result = "WIN";  pnl = close - tgt_b; break

            if result != "OPEN":
                risk  = abs(close - sl_b)
                pnl_r = pnl / (risk or 1)
                trades.append({
                    "time":   str(row.name)[:16],
                    "signal": signal,
                    "entry":  round(close, 2),
                    "sl":     round(sl_b, 2),
                    "target": round(tgt_b, 2),
                    "result": result,
                    "pnl_r":  round(pnl_r, 2),
                })
                eq_chg = 1.02 if result == "WIN" else 0.99
                equity.append(equity[-1] * eq_chg)
            else:
                equity.append(equity[-1])

    wins   = sum(1 for t in trades if t["result"] == "WIN")
    losses = sum(1 for t in trades if t["result"] == "LOSS")
    total  = wins + losses
    wr     = round(wins / total * 100, 1) if total > 0 else 0

    return {"trades": trades, "win_rate": wr, "total": total,
            "wins": wins, "losses": losses, "equity": equity}

# ══════════════════════════════════════════════════════════════════════════════
# AUTO KILL-SWITCH
# ══════════════════════════════════════════════════════════════════════════════

def auto_kill_check(bt: dict, manual_kill: bool) -> tuple:
    if manual_kill:
        return True, "Manual kill switch engaged"
    if bt["total"] >= 5 and bt["win_rate"] < 40:
        return True, f"Win rate {bt['win_rate']}% < 40% — auto-halted"
    return False, ""

# ══════════════════════════════════════════════════════════════════════════════
# PIVOT LEVELS  (Fibonacci)
# ══════════════════════════════════════════════════════════════════════════════

def calculate_pivots(ohlc: dict) -> dict:
    if not ohlc:
        return {}
    H = _safe_float(ohlc.get("high"))
    L = _safe_float(ohlc.get("low"))
    C = _safe_float(ohlc.get("close"))
    if H == 0 and L == 0:
        return {}
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
# OPTIONS & POSITION SIZING  (safe defaults)
# ══════════════════════════════════════════════════════════════════════════════

def get_atm_strike(ltp: float, index_name: str) -> dict:
    gap = STRIKE_GAPS.get(index_name, 50)
    if ltp <= 0:
        return {"atm": 0, "ce": 0, "pe": 0, "itm_ce": 0, "itm_pe": 0,
                "otm_ce": 0, "otm_pe": 0, "gap": gap}
    atm = round(ltp / gap) * gap
    return {
        "atm":    atm,
        "ce":     atm,
        "pe":     atm,
        "itm_ce": atm - gap,
        "itm_pe": atm + gap,
        "otm_ce": atm + gap,
        "otm_pe": atm - gap,
        "gap":    gap,
    }


def position_size(capital: float, risk_pct: float, sl_pts: float, lot_size: int) -> dict:
    safe = {"lots": 0, "risk_amount": 0, "margin_est": 0}
    try:
        if sl_pts <= 0 or lot_size <= 0 or capital <= 0:
            return safe
        risk_amt     = capital * risk_pct / 100
        risk_per_lot = sl_pts * lot_size
        lots         = int(risk_amt / risk_per_lot)
        return {
            "lots":       max(lots, 0),
            "risk_amount": round(risk_amt, 0),
            "margin_est":  round(lots * lot_size * 15, 0),
        }
    except Exception:
        return safe

# ══════════════════════════════════════════════════════════════════════════════
# MARKET STATUS  (IST-aware, Pre/Post/Live)
# ══════════════════════════════════════════════════════════════════════════════

def market_status() -> tuple:
    """
    Returns (status_label, is_live, ist_timestamp_str)
    status_label: "LIVE" | "PRE-MARKET" | "POST-MARKET" | "WEEKEND"
    """
    now_ist = datetime.now(IST)
    ts_str  = now_ist.strftime("%d %b %Y  %H:%M:%S IST")
    wd = now_ist.weekday()   # 0=Mon … 6=Sun

    if wd >= 5:   # Saturday=5, Sunday=6
        return "WEEKEND", False, ts_str

    open_t  = now_ist.replace(hour=9,  minute=15, second=0, microsecond=0)
    close_t = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)

    if now_ist < open_t:
        return "PRE-MARKET", False, ts_str
    if now_ist > close_t:
        return "POST-MARKET", False, ts_str
    return "LIVE", True, ts_str

# ══════════════════════════════════════════════════════════════════════════════
# SCORE ARC SVG
# ══════════════════════════════════════════════════════════════════════════════

def score_arc_svg(score: float, signal: str) -> str:
    score = max(0, min(score, 100))
    color = {"BUY": "#00E676", "SELL": "#FF4B4B"}.get(signal, "#5B8CFF")
    pct   = score / 100
    r     = 38
    cx, cy = 50, 50
    start_a = 135 * math.pi / 180
    end_a   = (135 + 270 * pct) * math.pi / 180
    x1 = cx + r * math.cos(start_a); y1 = cy + r * math.sin(start_a)
    x2 = cx + r * math.cos(end_a);   y2 = cy + r * math.sin(end_a)
    large  = 1 if 270 * pct > 180 else 0
    sig_label = signal if signal != "NONE" else "WAIT"
    sig_color = color

    arc_path = (
        f'<path d="M {x1:.2f} {y1:.2f} A {r} {r} 0 {large} 1 {x2:.2f} {y2:.2f}"'
        f' fill="none" stroke="{color}" stroke-width="6" stroke-linecap="round"/>'
        if pct > 0 else ""
    )
    sa135 = (cx + r * math.cos(135 * math.pi/180), cy + r * math.sin(135 * math.pi/180))
    sa45  = (cx + r * math.cos(45  * math.pi/180), cy + r * math.sin(45  * math.pi/180))

    return " ".join(f"""
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" width="100" height="100">
      <path d="M {sa135[0]:.2f} {sa135[1]:.2f} A {r} {r} 0 1 1 {sa45[0]:.2f} {sa45[1]:.2f}"
            fill="none" stroke="rgba(120,120,120,0.15)" stroke-width="6" stroke-linecap="round"/>
      {arc_path}
      <text x="50" y="47" text-anchor="middle" dominant-baseline="middle"
            font-family="JetBrains Mono" font-size="18" font-weight="700" fill="{color}">{int(score)}</text>
      <text x="50" y="62" text-anchor="middle" dominant-baseline="middle"
            font-family="Inter" font-size="6.5" font-weight="700"
            fill="{sig_color}" letter-spacing="1">{sig_label}</text>
    </svg>
    """.split())

# ══════════════════════════════════════════════════════════════════════════════
# CHART BUILDERS
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
        ann.update(font=dict(size=9, color="rgba(120,120,120,0.65)", family="Inter"),
                   x=0.01, xanchor="left")

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        increasing=dict(line=dict(color="#00E676", width=1), fillcolor="rgba(0,230,118,0.5)"),
        decreasing=dict(line=dict(color="#FF4B4B", width=1), fillcolor="rgba(255,75,75,0.5)"),
        name="Price", showlegend=False,
    ), row=1, col=1)

    if show_ema and "EMA9" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA9"],
            line=dict(color="#FFD700", width=1.2), name="EMA 9", hoverinfo="skip"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA21"],
            line=dict(color="#BB88FF", width=1.2), name="EMA 21", hoverinfo="skip"), row=1, col=1)

    if show_vwap and "VWAP" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"],
            line=dict(color="#5B8CFF", width=1.2, dash="dot"),
            name="VWAP", hoverinfo="skip"), row=1, col=1)

    if show_bb and "BB_U" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_U"],
            line=dict(color="rgba(255,179,71,0.4)", width=0.8),
            name="BB Upper", hoverinfo="skip", showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_L"],
            line=dict(color="rgba(255,179,71,0.4)", width=0.8),
            name="BB Lower", hoverinfo="skip", showlegend=False,
            fill="tonexty", fillcolor="rgba(255,179,71,0.02)"), row=1, col=1)

    pv_style = {
        "R2": ("#FF4B4B", "dash"), "R1": ("#FF8888", "dot"),
        "P":  ("#5B8CFF", "dash"),
        "S1": ("#66EEB0", "dot"),  "S2": ("#00E676", "dash"),
    }
    for lvl, val in pivots.items():
        col_c, dsh = pv_style.get(lvl, ("#888", "dash"))
        try:
            fig.add_hline(y=val, line=dict(color=col_c, width=0.8, dash=dsh),
                annotation_text=f"  {lvl} {val:,.0f}",
                annotation_font=dict(color=col_c, size=9, family="JetBrains Mono"),
                annotation_position="right", row=1, col=1)
        except Exception:
            pass

    if sig["signal"] != "NONE" and sig["entry"]:
        color = "#00E676" if sig["signal"] == "BUY" else "#FF4B4B"
        sym   = "triangle-up" if sig["signal"] == "BUY" else "triangle-down"
        icon  = "▲" if sig["signal"] == "BUY" else "▼"
        fig.add_trace(go.Scatter(
            x=[df.index[-1]], y=[sig["entry"]],
            mode="markers+text",
            marker=dict(size=12, color=color, symbol=sym),
            text=[f" {icon} {sig['signal']}"],
            textposition="top center",
            textfont=dict(color=color, size=11, family="JetBrains Mono"),
            name=sig["signal"], showlegend=False, hoverinfo="skip",
        ), row=1, col=1)
        if sig["sl"]:
            fig.add_hline(y=sig["sl"], line=dict(color="rgba(255,75,75,0.6)", width=1, dash="dot"),
                          annotation_text="  SL", annotation_font=dict(color="#FF4B4B", size=9),
                          row=1, col=1)
        if sig["target"]:
            fig.add_hline(y=sig["target"], line=dict(color="rgba(0,230,118,0.6)", width=1, dash="dot"),
                          annotation_text="  TGT", annotation_font=dict(color="#00E676", size=9),
                          row=1, col=1)

    # RSI subplot
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"],
            line=dict(color="rgba(120,120,120,0.7)", width=1.3),
            fill="tozeroy", fillcolor="rgba(120,120,120,0.04)", name="RSI"), row=2, col=1)
        for lv, cl in [(70, "rgba(255,75,75,0.4)"), (60, "rgba(0,230,118,0.35)"),
                       (40, "rgba(255,75,75,0.35)"), (30, "rgba(255,75,75,0.4)")]:
            fig.add_hline(y=lv, line=dict(color=cl, width=0.6, dash="dot"), row=2, col=1)
        fig.add_hrect(y0=60, y1=70, fillcolor="rgba(0,230,118,0.04)", line_width=0, row=2, col=1)
        fig.add_hrect(y0=30, y1=40, fillcolor="rgba(255,75,75,0.04)",  line_width=0, row=2, col=1)

    # Volume subplot
    if "Volume" in df.columns:
        vol_colors = [
            "rgba(0,230,118,0.5)" if float(c) >= float(o) else "rgba(255,75,75,0.5)"
            for c, o in zip(df["Close"], df["Open"])
        ]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"],
            marker_color=vol_colors, name="Volume"), row=3, col=1)
        if "VOL_MA20" in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df["VOL_MA20"],
                line=dict(color="rgba(255,179,71,0.7)", width=1.2),
                name="Vol MA20", hoverinfo="skip"), row=3, col=1)

    GRID  = "rgba(120,120,120,0.15)"
    PAPER = "rgba(0,0,0,0)"
    fig.update_layout(
        paper_bgcolor=PAPER, plot_bgcolor=PAPER,
        font=dict(family="JetBrains Mono, monospace", size=10),
        # Wider right margin for pivot annotations; compact on mobile
        margin=dict(l=5, r=80, t=20, b=10),
        legend=dict(bgcolor="rgba(120,120,120,0.05)", bordercolor="rgba(120,120,120,0.2)",
                    borderwidth=1, font=dict(size=9), x=0.01, y=0.99, orientation="h"),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        hoverlabel=dict(font=dict(size=10, family="JetBrains Mono")),
        height=520,
    )
    for row_n in [1, 2, 3]:
        fig.update_xaxes(gridcolor=GRID, showgrid=True, zeroline=False,
            showspikes=True, spikecolor="rgba(120,120,120,0.5)",
            spikedash="dot", spikethickness=1, tickfont=dict(size=9),
            row=row_n, col=1)
        fig.update_yaxes(gridcolor=GRID, showgrid=True, zeroline=False,
            tickfont=dict(size=9), row=row_n, col=1)

    fig.update_yaxes(tickformat=",.0f", row=1, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], tickformat=".0f",
                     tickfont=dict(size=8), row=2, col=1)
    fig.update_yaxes(title_text="Vol", tickformat=".2s",
                     tickfont=dict(size=8), row=3, col=1)
    return fig


def build_equity_curve(equity: list) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(equity))), y=equity,
        line=dict(color="#00E676", width=2),
        fill="tozeroy", fillcolor="rgba(0,230,118,0.06)",
        mode="lines", name="Equity",
    ))
    if equity:
        fig.add_hline(y=equity[0], line=dict(color="rgba(120,120,120,0.3)", width=0.8, dash="dot"))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=5, r=5, t=20, b=10), height=180,
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
        if not log or log[0].get("signal") != sig["signal"] or log[0].get("index") != index_name:
            st.session_state.trade_log = [{
                "time":   datetime.now(IST).strftime("%H:%M:%S"),
                "index":  index_name,
                "signal": sig["signal"],
                "entry":  sig["entry"],
                "sl":     sig["sl"],
                "target": sig["target"],
                "score":  sig.get("score", 0),
            }] + log[:14]

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT  (preserved across auto-refresh)
# ══════════════════════════════════════════════════════════════════════════════

for _k, _v in [("trade_log", []), ("capital", 500000), ("risk_pct", 1.0),
               ("sel_index", "NIFTY 50"), ("sel_tf", "5m")]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        '<div class="qx-wordmark">Quant<span class="acc">X</span></div>'
        '<div class="qx-tagline">v5 · F&O Intelligence Terminal</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="qx-section">Overlay Indicators</div>', unsafe_allow_html=True)
    show_ema  = st.toggle("EMA 9 / 21",      value=True)
    show_vwap = st.toggle("VWAP",            value=True)
    show_bb   = st.toggle("Bollinger Bands", value=False)

    st.markdown('<div class="qx-section">System Controls</div>', unsafe_allow_html=True)
    manual_kill = st.toggle("Manual Kill Switch", value=False)

    st.markdown('<div class="qx-section">Auto Refresh</div>', unsafe_allow_html=True)
    refresh_sec = st.slider("Interval (sec)", 15, 120, 30, 5,
                            label_visibility="collapsed")
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=refresh_sec * 1000, key="qx_refresh")

# ══════════════════════════════════════════════════════════════════════════════
# CONTROL PANEL EXPANDER  (selections persist via session_state)
# ══════════════════════════════════════════════════════════════════════════════

with st.expander("⚙️  QUANTX CONTROL PANEL", expanded=True):
    col_c1, col_c2, col_c3 = st.columns([1, 1, 1.2])
    with col_c1:
        sel_idx_keys = list(INDICES.keys())
        default_idx  = sel_idx_keys.index(st.session_state.sel_index) \
                       if st.session_state.sel_index in sel_idx_keys else 0
        selected_label = st.selectbox("Market Asset Index", sel_idx_keys,
                                      index=default_idx, key="ctrl_index")
        st.session_state.sel_index = selected_label
        ticker   = INDICES[selected_label]
        lot_size = LOT_SIZES[selected_label]

    with col_c2:
        tf_keys    = list(TIMEFRAMES.keys())
        default_tf = tf_keys.index(st.session_state.sel_tf) \
                     if st.session_state.sel_tf in tf_keys else 1
        tf_label   = st.selectbox("Data Timeframe", tf_keys, index=default_tf, key="ctrl_tf")
        st.session_state.sel_tf = tf_label
        interval   = TIMEFRAMES[tf_label]

    with col_c3:
        capital  = st.number_input("Account Capital (₹)", value=st.session_state.capital,
                                   step=50000, min_value=10000, key="ctrl_cap")
        risk_pct = st.slider("Risk per Trade (%)", 0.5, 3.0, st.session_state.risk_pct,
                             0.25, key="ctrl_risk")
        st.session_state.capital  = capital
        st.session_state.risk_pct = risk_pct

# ══════════════════════════════════════════════════════════════════════════════
# FETCH & COMPUTE
# ══════════════════════════════════════════════════════════════════════════════

mkt_status, is_live, ts_now = market_status()

with st.spinner("Fetching live market data…"):
    df_raw = fetch_data(ticker, interval)
    prev_d = fetch_prev_day(ticker)

if df_raw.empty:
    st.warning(
        f"⚠️  No data returned for **{selected_label}** ({tf_label}). "
        f"Market is currently **{mkt_status}** — data may resume when NSE opens."
    )
    st.stop()

df_ind = calculate_indicators(df_raw)
regime = detect_regime(df_ind)
pivots = calculate_pivots(prev_d)
bt     = run_backtest(df_ind, lookback=40)
kill_sw, kill_reason = auto_kill_check(bt, manual_kill)
sig    = score_signal(df_ind, kill_sw, regime)
update_trade_log(sig, selected_label)

# Safe scalar extraction
try:
    ltp         = _safe_float(df_ind["Close"].iloc[-1])
    open_price  = _safe_float(df_ind["Open"].iloc[0])
    day_chg     = ltp - open_price
    day_chg_pct = (day_chg / open_price * 100) if open_price else 0
    volatility  = _safe_float(df_ind["ATR"].iloc[-1])
    vwap_val    = _safe_float(df_ind["VWAP"].iloc[-1], ltp)
    adx_val     = _safe_float(df_ind["ADX"].iloc[-1])
    rsi_val     = _safe_float(df_ind["RSI"].iloc[-1], 50.0)
except Exception:
    ltp = open_price = day_chg = day_chg_pct = volatility = vwap_val = adx_val = rsi_val = 0.0

atm_data = get_atm_strike(ltp, selected_label)
sl_pts   = abs(ltp - (sig["sl"] or ltp))
pos      = position_size(capital, risk_pct, sl_pts, lot_size)
score    = sig.get("score", 0)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER BAR
# ══════════════════════════════════════════════════════════════════════════════

regime_html = {
    "TRENDING": '<span class="qx-regime qx-regime-trend">◈ TRENDING</span>',
    "CHOPPY":   '<span class="qx-regime qx-regime-chop">◈ CHOPPY — SIGNALS PAUSED</span>',
    "VOLATILE": '<span class="qx-regime qx-regime-vol">◈ VOLATILE</span>',
}.get(regime, '<span class="qx-regime qx-regime-chop">◈ UNKNOWN</span>')

mkt_chip_cls = {
    "LIVE":        "qx-chip-green",
    "PRE-MARKET":  "qx-chip-amber",
    "POST-MARKET": "qx-chip-amber",
    "WEEKEND":     "qx-chip-gray",
}.get(mkt_status, "qx-chip-gray")

ks_html = (f'<span class="qx-chip qx-chip-red">⛔ HALTED — {kill_reason[:40]}</span>'
           if kill_sw else "")

render_html(f"""
<div class="qx-header">
  <div class="qx-header-left">
    <div>
      <div class="qx-header-title" style="font-size:1rem">
        Quant<span style="color:#00E676">X</span> · {selected_label} · {tf_label}
      </div>
      <div class="qx-header-sub">Signal threshold {SIGNAL_THRESHOLD}/100 · {lot_size} units/lot</div>
    </div>
    {regime_html}
    {ks_html}
  </div>
  <div style="display:flex;align-items:center;gap:0.6rem">
    <span class="qx-chip {mkt_chip_cls}">
      <span style="display:inline-block;width:5px;height:5px;border-radius:50%;
            background:{'#00E676' if is_live else '#FFB347'};
            margin-right:4px;vertical-align:middle;
            {'animation:qx-pulse 2s infinite' if is_live else ''}"></span>
      NSE {mkt_status}
    </span>
    <span class="qx-chip qx-chip-gray" style="font-size:0.58rem">{ts_now}</span>
  </div>
</div>
""")

# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL BANNER
# ══════════════════════════════════════════════════════════════════════════════

s       = sig["signal"]
sc_cls  = "buy" if s == "BUY" else ("sell" if s == "SELL" else "none")
s_icon  = "▲" if s == "BUY" else ("▼" if s == "SELL" else "⏸")
s_color = "clr-green" if s == "BUY" else ("clr-red" if s == "SELL" else "clr-blue")
arc_svg = score_arc_svg(score, s)

rsi_txt  = f"{sig['rsi']:.1f}"   if sig["rsi"]    is not None else "—"
atr_txt  = f"₹{sig['atr']:,.1f}" if sig["atr"]    else "—"
sl_txt   = f"₹{sig['sl']:,.2f}"  if sig["sl"]     else "—"
tgt_txt  = f"₹{sig['target']:,.2f}" if sig["target"] else "—"
entry_txt = f"₹{sig['entry']:,.2f}" if sig["entry"]  else "—"
kill_note = (f'<br><span style="font-size:0.65rem;color:rgba(255,75,75,0.7);'
             f'font-family:JetBrains Mono,monospace">{sig["kill_reason"]}</span>'
             if sig.get("kill_reason") else "")

render_html(f"""
<div class="qx-signal-banner {sc_cls}">
  <div class="qx-signal-main">
    <div style="font-size:2.4rem;line-height:1">{s_icon}</div>
    <div>
      <div class="qx-signal-type {s_color}">{s}</div>
      <div class="qx-signal-meta">
        Entry <strong>{entry_txt}</strong> &nbsp;·&nbsp;
        SL <strong style="color:#FF6B6B">{sl_txt}</strong> &nbsp;·&nbsp;
        Target <strong style="color:#00E676">{tgt_txt}</strong><br>
        RSI <strong>{rsi_txt}</strong> &nbsp;·&nbsp;
        ATR <strong>{atr_txt}</strong> &nbsp;·&nbsp;
        ADX <strong>{adx_val:.1f}</strong> &nbsp;·&nbsp;
        VWAP <strong>₹{vwap_val:,.1f}</strong>
        {kill_note}
      </div>
    </div>
  </div>
  <div class="qx-score-wrap">
    {arc_svg}
    <div class="qx-score-label">Signal Score</div>
  </div>
</div>
""")

# ══════════════════════════════════════════════════════════════════════════════
# METRIC CARDS
# ══════════════════════════════════════════════════════════════════════════════

chg_cls   = "clr-green" if day_chg >= 0 else "clr-red"
chg_arrow = "▲" if day_chg >= 0 else "▼"
vol_above = (ltp > vwap_val) if vwap_val else False
vwap_cls  = "clr-green" if vol_above else "clr-red"
vwap_side = "ABOVE" if vol_above else "BELOW"
adx_str   = "STRONG" if adx_val > 25 else ("WEAK" if adx_val < 18 else "MOD")
adx_cls   = "clr-green" if adx_val > 25 else ("clr-red" if adx_val < 18 else "clr-amber")
wr_cls    = "clr-green" if bt["win_rate"] >= 55 else ("clr-amber" if bt["win_rate"] >= 40 else "clr-red")
rr_pts    = abs((sig["target"] or ltp) - ltp) if sig["target"] else 0

render_html(f"""
<div class="qx-metrics-grid">
  <div class="qx-card qx-card-blue">
    <div class="qx-card-icon">📈</div>
    <div class="qx-card-label">LTP · {selected_label}</div>
    <div class="qx-card-value">₹{ltp:,.2f}</div>
    <div class="qx-card-sub"><span class="{chg_cls}">{chg_arrow} {abs(day_chg_pct):.2f}%</span></div>
  </div>
  <div class="qx-card qx-card-red">
    <div class="qx-card-icon">🛡</div>
    <div class="qx-card-label">Stop Loss</div>
    <div class="qx-card-value clr-red">{sl_txt}</div>
    <div class="qx-card-sub">ATR×1.5 · {_safe_fmt(sl_pts, '₹{:,.1f}', '—')}</div>
  </div>
  <div class="qx-card qx-card-green">
    <div class="qx-card-icon">🎯</div>
    <div class="qx-card-label">Target (1:2)</div>
    <div class="qx-card-value clr-green">{tgt_txt}</div>
    <div class="qx-card-sub">Reward ₹{rr_pts:,.0f}</div>
  </div>
  <div class="qx-card qx-card-amber">
    <div class="qx-card-icon">⚖</div>
    <div class="qx-card-label">VWAP</div>
    <div class="qx-card-value">₹{vwap_val:,.0f}</div>
    <div class="qx-card-sub"><span class="{vwap_cls}">{vwap_side}</span></div>
  </div>
  <div class="qx-card qx-card-neutral">
    <div class="qx-card-icon">📡</div>
    <div class="qx-card-label">ADX</div>
    <div class="qx-card-value">{adx_val:.1f}</div>
    <div class="qx-card-sub"><span class="{adx_cls}">{adx_str}</span></div>
  </div>
  <div class="qx-card {'qx-card-green' if bt['win_rate'] >= 55 else ('qx-card-amber' if bt['win_rate'] >= 40 else 'qx-card-red')}">
    <div class="qx-card-icon">🏆</div>
    <div class="qx-card-label">Backtest Win %</div>
    <div class="qx-card-value {wr_cls}">{bt['win_rate']}%</div>
    <div class="qx-card-sub">{bt['wins']}W / {bt['losses']}L</div>
  </div>
</div>
""")

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs([
    "📊  Price Chart",
    "📈  Backtest",
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

        bull_count = bear_count = 0
        mtf_rows = ""
        for tf_k, td in mtf.items():
            bias   = td.get("bias", "NEUTRAL")
            rsi_v  = f"{td['rsi']:.0f}" if td.get("rsi") is not None else "—"
            pill   = "mtf-bull" if bias == "BULLISH" else ("mtf-bear" if bias == "BEARISH" else "mtf-neut")
            icon   = "▲" if bias == "BULLISH" else ("▼" if bias == "BEARISH" else "—")
            if bias == "BULLISH": bull_count += 1
            elif bias == "BEARISH": bear_count += 1
            mtf_rows += f"""<tr>
              <td style="font-size:0.72rem;font-weight:600">{tf_k}</td>
              <td><span class="qx-mtf-pill {pill}">{icon} {bias[:4]}</span></td>
              <td style="opacity:0.8;font-size:0.7rem">{rsi_v}</td>
            </tr>"""

        align_total = bull_count - bear_count
        align_col   = "clr-green" if align_total >= 2 else ("clr-red" if align_total <= -2 else "clr-amber")
        align_note  = f"{'Bullish' if align_total > 0 else 'Bearish' if align_total < 0 else 'Mixed'} ({bull_count}↑ {bear_count}↓)"

        render_html(f"""
        <table class="qx-mtf-table">
          <thead><tr><th>TF</th><th>Bias</th><th>RSI</th></tr></thead>
          <tbody>{mtf_rows}</tbody>
        </table>
        <p style="font-size:0.65rem;margin-top:0.6rem" class="{align_col}">Alignment: {align_note}</p>
        """)

        st.markdown('<div class="qx-section">Fibonacci Pivots</div>', unsafe_allow_html=True)
        if pivots:
            lm = {"R2":("Res 2","pv-r"), "R1":("Res 1","pv-r"),
                  "P":("Pivot","pv-p"),
                  "S1":("Sup 1","pv-s"), "S2":("Sup 2","pv-s")}
            rows_html = ""
            for k in ["R2","R1","P","S1","S2"]:
                v = pivots.get(k, 0)
                name, cls = lm[k]
                diff = ((v - ltp) / ltp * 100) if ltp else 0
                dc   = "pv-pos" if diff > 0 else "pv-neg"
                rows_html += f"""<tr>
                  <td style="opacity:0.7;font-size:0.72rem">{name}</td>
                  <td class="{cls}" style="font-size:0.72rem;font-weight:700">{k}</td>
                  <td class="{cls}" style="font-weight:600">₹{v:,.0f}</td>
                  <td class="{dc}" style="text-align:right;font-size:0.7rem">{diff:+.2f}%</td>
                </tr>"""
            render_html(f"""
            <table class="qx-pivot-table">
              <thead><tr><th>Level</th><th></th><th>Price</th><th style="text-align:right">vs LTP</th></tr></thead>
              <tbody>{rows_html}</tbody>
            </table>""")
        else:
            st.markdown('<p style="opacity:0.5;font-size:0.78rem">Pivot data unavailable</p>',
                        unsafe_allow_html=True)

        st.markdown('<div class="qx-section">Signal Log</div>', unsafe_allow_html=True)
        log = st.session_state.get("trade_log", [])
        if not log:
            st.markdown('<p style="opacity:0.5;font-size:0.75rem;padding:0.3rem 0">'
                        'No signals yet — waiting for confluence…</p>', unsafe_allow_html=True)
        else:
            for e in log[:5]:
                bc    = "buy" if e["signal"] == "BUY" else "sell"
                sl_s  = f"SL ₹{e['sl']:,.0f}" if e.get("sl") else ""
                tgt_s = f"T ₹{e['target']:,.0f}" if e.get("target") else ""
                sc_s  = f"Score {e.get('score',0):.0f}" if e.get("score") else ""
                render_html(f"""
                <div class="qx-log-entry">
                  <div>
                    <div class="qx-log-time">{e['time']}</div>
                    <div class="qx-log-idx">{e['index']}</div>
                    <div class="qx-log-price">₹{e['entry']:,.2f}</div>
                    <div class="qx-log-levels">{sl_s} &nbsp; {tgt_s} &nbsp; {sc_s}</div>
                  </div>
                  <span class="qx-log-badge {bc}">{e['signal']}</span>
                </div>""")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — BACKTEST
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="qx-section">Walk-Forward Backtest · Last 40 Bars</div>',
                unsafe_allow_html=True)

    ks_banner = (
        f'<div class="qx-ks-halted">⛔ &nbsp; AUTO KILL-SWITCH ACTIVE — {kill_reason}</div>'
        if kill_sw else
        '<div class="qx-ks-active">✅ &nbsp; SIGNALS ACTIVE — Win rate above threshold</div>'
    )
    render_html(ks_banner)
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    wr      = bt["win_rate"]
    wr_col  = "clr-green" if wr >= 55 else ("clr-amber" if wr >= 40 else "clr-red")
    avg_r   = round(sum(t["pnl_r"] for t in bt["trades"]) / len(bt["trades"]), 2) \
              if bt["trades"] else 0
    eq_ret  = round((bt["equity"][-1] / bt["equity"][0] - 1) * 100, 1) \
              if len(bt["equity"]) > 1 else 0

    bs1, bs2, bs3, bs4, bs5 = st.columns(5)
    for col_w, val, lbl, vc in [
        (bs1, f"{wr}%",          "Win Rate",     wr_col),
        (bs2, str(bt["total"]),  "Total Trades", ""),
        (bs3, str(bt["wins"]),   "Wins",         "clr-green"),
        (bs4, str(bt["losses"]), "Losses",       "clr-red"),
        (bs5, f"{eq_ret:+.1f}%", "Equity Ret",  "clr-green" if eq_ret > 0 else "clr-red"),
    ]:
        with col_w:
            render_html(f"""
            <div class="qx-bt-stat">
              <div class="qx-bt-stat-val {vc}">{val}</div>
              <div class="qx-bt-stat-lbl">{lbl}</div>
            </div>""")

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
    col_eq, col_tbl = st.columns([1, 1], gap="large")

    with col_eq:
        st.markdown('<div class="qx-section">Equity Curve</div>', unsafe_allow_html=True)
        if len(bt["equity"]) > 2:
            st.plotly_chart(build_equity_curve(bt["equity"]),
                            use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<p style="opacity:0.5;font-size:0.78rem">Insufficient trades for equity curve.</p>',
                        unsafe_allow_html=True)

    with col_tbl:
        st.markdown('<div class="qx-section">Recent Trades</div>', unsafe_allow_html=True)
        if bt["trades"]:
            df_trades = pd.DataFrame(bt["trades"][-15:])
            df_trades = df_trades[["time","signal","entry","sl","target","result","pnl_r"]].copy()
            df_trades.columns = ["Time","Signal","Entry","SL","Target","Result","P&L (R)"]
            st.dataframe(
                df_trades.style
                    .map(lambda v: "color:#00E676" if v=="WIN" else ("color:#FF4B4B" if v=="LOSS" else ""),
                         subset=["Result"])
                    .map(lambda v: "color:#00E676" if isinstance(v,float) and v>0
                                   else ("color:#FF4B4B" if isinstance(v,float) and v<0 else ""),
                         subset=["P&L (R)"])
                    .format({"Entry":"₹{:,.2f}","SL":"₹{:,.2f}","Target":"₹{:,.2f}","P&L (R)":"{:+.2f}R"}),
                use_container_width=True, height=220, hide_index=True,
            )
        else:
            st.markdown('<p style="opacity:0.5;font-size:0.78rem">No completed trades in window.</p>',
                        unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — OPTIONS & POSITION
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    col_opt, col_pos = st.columns([1, 1], gap="large")

    with col_opt:
        st.markdown('<div class="qx-section">F&O Strike Suggester</div>', unsafe_allow_html=True)
        render_html(f"""
        <div class="qx-opt-card" style="border-left:3px solid rgba(0,230,118,0.4)">
          <div class="qx-opt-header">BUY SIGNAL → CALL OPTION (CE)</div>
          <div class="qx-opt-strike">{atm_data['ce']:,} CE</div>
          <div class="qx-opt-meta">
            ATM Strike · Gap {atm_data['gap']} pts · {selected_label}<br>
            ITM CE: <strong>{atm_data['itm_ce']:,}</strong> &nbsp;·&nbsp;
            OTM CE: <strong>{atm_data['otm_ce']:,}</strong>
          </div>
        </div>
        <div class="qx-opt-card" style="border-left:3px solid rgba(255,61,0,0.4)">
          <div class="qx-opt-header">SELL SIGNAL → PUT OPTION (PE)</div>
          <div class="qx-opt-strike">{atm_data['pe']:,} PE</div>
          <div class="qx-opt-meta">
            ATM Strike · Gap {atm_data['gap']} pts · {selected_label}<br>
            ITM PE: <strong>{atm_data['itm_pe']:,}</strong> &nbsp;·&nbsp;
            OTM PE: <strong>{atm_data['otm_pe']:,}</strong>
          </div>
        </div>
        """)

        st.markdown('<div class="qx-section">Index Specifications</div>', unsafe_allow_html=True)
        spec_rows = ""
        for idx_n in INDICES:
            active = "rgba(0,230,118,0.04)" if idx_n == selected_label else "transparent"
            bold   = "700" if idx_n == selected_label else "400"
            spec_rows += f"""<tr style="background:{active}">
              <td style="font-weight:{bold}">{idx_n}</td>
              <td>{LOT_SIZES[idx_n]}</td>
              <td>{STRIKE_GAPS[idx_n]}</td>
            </tr>"""
        render_html(f"""
        <table class="qx-pivot-table">
          <thead><tr><th>Index</th><th>Lot Size</th><th>Strike Gap</th></tr></thead>
          <tbody>{spec_rows}</tbody>
        </table>""")

    with col_pos:
        st.markdown('<div class="qx-section">Position Size Calculator</div>', unsafe_allow_html=True)
        render_html(f"""
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
            Max risk: <strong>₹{pos['risk_amount']:,.0f}</strong> ({risk_pct}% of capital)<br>
            Qty: <strong>{pos['lots'] * lot_size}</strong> units &nbsp;·&nbsp;
            Est. margin: <strong>₹{pos['margin_est']:,.0f}</strong>
          </div>
        </div>

        <div class="qx-opt-card" style="margin-top:0.5rem;background:rgba(255,179,71,0.03);border-color:rgba(255,179,71,0.15)">
          <div class="qx-opt-header" style="color:rgba(255,179,71,0.6)">Risk Rules — Never Break These</div>
          <div style="font-size:0.72rem;opacity:0.8;line-height:1.8">
            ◈ &nbsp;Risk ≤ 1–2% of capital per trade<br>
            ◈ &nbsp;Max 3 open positions simultaneously<br>
            ◈ &nbsp;Daily stop ₹{capital * risk_pct / 100 * 3:,.0f} (3× risk)<br>
            ◈ &nbsp;Never average a losing F&amp;O position<br>
            ◈ &nbsp;Exit before 15:15 IST — avoid expiry theta decay
          </div>
        </div>
        """)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    col_a, col_b = st.columns([1, 1], gap="large")

    with col_a:
        st.markdown('<div class="qx-section">Signal Score Breakdown</div>', unsafe_allow_html=True)
        cs = sig.get("component_scores", {})
        if cs:
            labels  = ["EMA Cross", "RSI Zone", "VWAP Side", "BB Position", "Volume Conf.", "ADX Trend"]
            vals    = [cs.get("ema_cross_buy",0), cs.get("rsi_buy",0), cs.get("vwap_buy",0),
                       cs.get("bb_buy",0), cs.get("vol_buy",0), cs.get("adx_buy",0)]
            maxes   = [25, 20, 20, 15, 10, 10]
            colors  = ["rgba(0,230,118,0.7)" if a >= m*0.7
                       else ("rgba(255,179,71,0.7)" if a >= m*0.4 else "rgba(255,75,75,0.6)")
                       for a, m in zip(vals, maxes)]
            bar_fig = go.Figure(go.Bar(
                x=labels, y=vals, marker_color=colors,
                text=[f"{v:.0f}" for v in vals],
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
            st.markdown('<p style="opacity:0.5;font-size:0.78rem">Run a signal to see score breakdown.</p>',
                        unsafe_allow_html=True)

        st.markdown('<div class="qx-section">Indicator Snapshot</div>', unsafe_allow_html=True)
        bb_u_txt = _safe_fmt(float(df_ind["BB_U"].iloc[-1]) if "BB_U" in df_ind.columns else None)
        bb_l_txt = _safe_fmt(float(df_ind["BB_L"].iloc[-1]) if "BB_L" in df_ind.columns else None)
        rows_html = ""
        for lbl, val, vc in [
            ("EMA 9",        _safe_fmt(sig["ema9"]),  ""),
            ("EMA 21",       _safe_fmt(sig["ema21"]), ""),
            ("RSI 14",       f"{rsi_val:.2f}",
             "clr-green" if rsi_val>60 else ("clr-red" if rsi_val<40 else "")),
            ("ATR 14",       _safe_fmt(volatility),   ""),
            ("VWAP",         _safe_fmt(vwap_val),     ""),
            ("ADX 14",       f"{adx_val:.2f}",
             "clr-green" if adx_val>25 else "clr-red"),
            ("BB Upper",     bb_u_txt,                ""),
            ("BB Lower",     bb_l_txt,                ""),
            ("Signal Score", f"{score:.0f} / 100",
             "clr-green" if score>=70 else ("clr-amber" if score>=50 else "clr-red")),
        ]:
            rows_html += f"""<tr>
              <td style="opacity:0.6;font-size:0.72rem">{lbl}</td>
              <td class="{vc}" style="font-weight:600;font-size:0.78rem">{val}</td>
            </tr>"""
        render_html(f"""
        <table class="qx-pivot-table">
          <thead><tr><th>Indicator</th><th>Value</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""")

    with col_b:
        st.markdown('<div class="qx-section">Session Summary</div>', unsafe_allow_html=True)
        log       = st.session_state.get("trade_log", [])
        sess_buy  = sum(1 for e in log if e["signal"] == "BUY")
        sess_sell = sum(1 for e in log if e["signal"] == "SELL")
        render_html(f"""
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
        """)

        st.markdown('<div class="qx-section">Full Signal Log</div>', unsafe_allow_html=True)
        if log:
            df_log = pd.DataFrame(log)[["time","index","signal","entry","sl","target","score"]].copy()
            df_log.columns = ["Time","Index","Signal","Entry ₹","SL ₹","Target ₹","Score"]
            st.dataframe(
                df_log.style
                    .map(lambda v: "color:#00E676" if v=="BUY" else ("color:#FF4B4B" if v=="SELL" else ""),
                         subset=["Signal"])
                    .format({"Entry ₹":"₹{:,.2f}","SL ₹":"₹{:,.2f}","Target ₹":"₹{:,.2f}","Score":"{:.0f}"}),
                use_container_width=True, height=260, hide_index=True,
            )
            csv = df_log.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ Download Signal Log (.csv)", data=csv,
                file_name=f"quantx_signals_{datetime.now(IST).strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv", use_container_width=True,
            )
        else:
            st.markdown('<p style="opacity:0.5;font-size:0.78rem">No signals recorded this session.</p>',
                        unsafe_allow_html=True)

        st.markdown('<div class="qx-section">System Status</div>', unsafe_allow_html=True)
        rows_html = ""
        for lbl, val, vc in [
            ("Data Feed",     "LIVE" if not df_ind.empty else "ERROR",
             "clr-green" if not df_ind.empty else "clr-red"),
            ("Market Status", mkt_status,
             "clr-green" if is_live else "clr-amber"),
            ("Signal Engine", "HALTED" if kill_sw else "ACTIVE",
             "clr-red" if kill_sw else "clr-green"),
            ("Market Regime", regime,
             "clr-green" if regime=="TRENDING" else ("clr-amber" if regime=="VOLATILE" else "clr-red")),
            ("Backtest WR",   f"{bt['win_rate']}%",
             "clr-green" if bt["win_rate"]>=55 else ("clr-amber" if bt["win_rate"]>=40 else "clr-red")),
            ("Kill Switch",   "MANUAL" if manual_kill else ("AUTO-TRIGGERED" if kill_sw else "OFF"),
             "clr-red" if kill_sw else "clr-green"),
            ("Auto Refresh",  f"Every {refresh_sec}s", "clr-blue"),
        ]:
            rows_html += f"""<tr>
              <td style="opacity:0.6;font-size:0.72rem">{lbl}</td>
              <td class="{vc}" style="font-weight:700;font-size:0.72rem;font-family:'JetBrains Mono',monospace">{val}</td>
            </tr>"""
        render_html(f"""
        <table class="qx-pivot-table">
          <thead><tr><th>Component</th><th>Status</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""")

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<hr class="qx-divider" style="margin-top:2rem">
<div style="display:flex;justify-content:space-between;align-items:center;
            padding:0.5rem 0;font-size:0.6rem;opacity:0.5;flex-wrap:wrap;gap:0.5rem">
  <span>QuantX v5 &nbsp;·&nbsp; F&amp;O Intelligence Terminal &nbsp;·&nbsp;
        Pure pandas/numpy · Python 3.11 · IST-aware</span>
  <span style="color:rgba(255,179,71,0.8);font-weight:600">
    ⚠ Educational &amp; research use only. Not SEBI-registered investment advice.
  </span>
</div>
""", unsafe_allow_html=True)
