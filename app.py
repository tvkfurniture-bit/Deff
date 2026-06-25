import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np
import warnings
warnings.filterwarnings("ignore")

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuantX · F&O Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── THEME-AWARE CSS ────────────────────────────────────────────────────────────
# Uses CSS custom properties that work with BOTH Streamlit light and dark modes.
# Hard-coded backgrounds are replaced with rgba() glassmorphism layers on top of
# whatever the host theme provides.
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

  /* ── Base typography ───────────────────────────────────────────────────── */
  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
  }

  /* Hide menu & footer but KEEP the sidebar collapse toggle visible */
  #MainMenu, footer { visibility: hidden; }
  header { visibility: visible !important; background: transparent !important; }
  /* Hide everything in header EXCEPT the sidebar toggle button */
  header > div:first-child { background: transparent !important; box-shadow: none !important; }
  [data-testid="stHeader"] { background: transparent !important; }
  /* Make the header bar itself invisible but keep the toggle clickable */
  section[data-testid="stSidebarContent"] ~ div > header { background: transparent; }

  .block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 100%; }

  /* ── Floating sidebar open button (shown when sidebar is collapsed) ────── */
  .sidebar-fab {
    position: fixed;
    top: 0.75rem;
    left: 0.75rem;
    z-index: 99999;
    display: flex;
    align-items: center;
    gap: 0.45rem;
    background: rgba(0,204,136,0.12);
    border: 1px solid rgba(0,204,136,0.4);
    border-radius: 8px;
    padding: 0.38rem 0.75rem;
    font-size: 0.72rem;
    font-weight: 700;
    color: #00CC88;
    letter-spacing: 0.06em;
    cursor: pointer;
    backdrop-filter: blur(10px);
    transition: background 0.18s, border-color 0.18s;
    font-family: 'Inter', sans-serif;
    text-transform: uppercase;
  }
  .sidebar-fab:hover { background: rgba(0,204,136,0.22); border-color: rgba(0,204,136,0.7); }

  /* ── Inline quick-controls bar (index + tf chips) ──────────────────────── */
  .ctrl-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
    padding: 0.6rem 0.9rem;
    background: rgba(128,128,128,0.06);
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 10px;
    backdrop-filter: blur(8px);
  }
  .ctrl-label {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: rgba(128,128,128,0.55);
    margin-right: 0.2rem;
  }
  .ctrl-chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    font-weight: 600;
    padding: 0.22rem 0.65rem;
    border-radius: 5px;
    border: 1px solid rgba(128,128,128,0.2);
    background: rgba(128,128,128,0.08);
    color: inherit;
    cursor: default;
  }
  .ctrl-chip.active {
    border-color: rgba(0,204,136,0.5);
    background: rgba(0,204,136,0.1);
    color: #00CC88;
  }
  .ctrl-divider {
    width: 1px; height: 18px;
    background: rgba(128,128,128,0.2);
    margin: 0 0.2rem;
  }
  .ctrl-mkt {
    margin-left: auto;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.06em;
  }

  /* ── Sidebar border ────────────────────────────────────────────────────── */
  [data-testid="stSidebar"] {
    border-right: 1px solid rgba(128,128,128,0.15);
  }

  /* ── Wordmark ──────────────────────────────────────────────────────────── */
  .quantx-wordmark {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1;
    margin-bottom: 0.15rem;
  }
  .quantx-wordmark .accent { color: #00FFA3; }
  .quantx-tagline {
    font-size: 0.68rem;
    color: rgba(128,128,128,0.7);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 500;
    margin-bottom: 1.6rem;
  }

  /* ── Glassmorphism metric cards ────────────────────────────────────────── */
  .metric-card {
    background: rgba(128, 128, 128, 0.06);
    border: 1px solid rgba(128, 128, 128, 0.18);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: border-color 0.2s ease;
  }
  .metric-card:hover {
    border-color: rgba(128,128,128,0.35);
  }
  .metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    opacity: 0.85;
  }
  .metric-card.card-buy::before   { background: linear-gradient(90deg, #00FFA3, transparent); }
  .metric-card.card-sell::before  { background: linear-gradient(90deg, #FF4B4B, transparent); }
  .metric-card.card-blue::before  { background: linear-gradient(90deg, #5B8CFF, transparent); }
  .metric-card.card-amber::before { background: linear-gradient(90deg, #FFB347, transparent); }

  .metric-label {
    font-size: 0.67rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: rgba(128,128,128,0.7);
    margin-bottom: 0.4rem;
  }
  .metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.45rem;
    font-weight: 700;
    line-height: 1;
  }
  .metric-sub {
    font-size: 0.72rem;
    color: rgba(128,128,128,0.7);
    margin-top: 0.3rem;
    font-weight: 400;
  }

  /* Signal colours — high contrast on any background */
  .clr-buy    { color: #00CC88 !important; }
  .clr-sell   { color: #FF4B4B !important; }
  .clr-none   { color: #5B8CFF !important; }
  .clr-up     { color: #00CC88; }
  .clr-down   { color: #FF4B4B; }
  .clr-amber  { color: #FFB347; }

  /* ── Section headers ───────────────────────────────────────────────────── */
  .section-header {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(128,128,128,0.6);
    border-bottom: 1px solid rgba(128,128,128,0.15);
    padding-bottom: 0.4rem;
    margin-bottom: 0.8rem;
    margin-top: 1.2rem;
  }

  /* ── Pivot table ───────────────────────────────────────────────────────── */
  .pivot-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
  }
  .pivot-table td, .pivot-table th {
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid rgba(128,128,128,0.12);
    text-align: right;
  }
  .pivot-table th {
    color: rgba(128,128,128,0.6);
    font-size: 0.65rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    text-align: left;
    font-family: 'Inter', sans-serif;
  }
  .pivot-table td:first-child { text-align: left; color: rgba(128,128,128,0.75); }
  .r-level { color: #FF6B6B; font-weight: 600; }
  .s-level { color: #00CC88; font-weight: 600; }
  .p-level { color: #5B8CFF; font-weight: 600; }

  /* ── Trade log entries ─────────────────────────────────────────────────── */
  .trade-log-entry {
    background: rgba(128,128,128,0.06);
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    backdrop-filter: blur(8px);
  }
  .trade-log-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: rgba(128,128,128,0.65);
  }
  .trade-log-signal {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    padding: 0.22rem 0.65rem;
    border-radius: 5px;
  }
  .trade-log-signal.buy  { background: rgba(0,204,136,0.15); color: #00CC88; border: 1px solid rgba(0,204,136,0.3); }
  .trade-log-signal.sell { background: rgba(255,75,75,0.15);  color: #FF4B4B; border: 1px solid rgba(255,75,75,0.3); }
  .trade-log-price {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    margin-top: 0.15rem;
  }

  /* ── Kill switch banners ───────────────────────────────────────────────── */
  .ks-halted {
    background: rgba(255,75,75,0.08);
    border: 1px solid rgba(255,75,75,0.3);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-size: 0.75rem;
    color: #FF4B4B;
    text-align: center;
    font-weight: 700;
    letter-spacing: 0.06em;
    margin-top: 0.5rem;
  }
  .ks-active {
    background: rgba(0,204,136,0.08);
    border: 1px solid rgba(0,204,136,0.3);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-size: 0.75rem;
    color: #00CC88;
    text-align: center;
    font-weight: 700;
    letter-spacing: 0.06em;
    margin-top: 0.5rem;
  }

  /* ── Market status dot ─────────────────────────────────────────────────── */
  .status-dot {
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    animation: pulse-dot 2s infinite;
    margin-right: 6px;
    vertical-align: middle;
  }
  @keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.45; transform: scale(0.85); }
  }

  /* ── Signal badge ──────────────────────────────────────────────────────── */
  .signal-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.35rem;
    font-weight: 700;
  }

  /* ── Streamlit widget overrides ────────────────────────────────────────── */
  [data-testid="stSelectbox"] > div > div,
  [data-testid="stRadio"] label { }
  hr { border-color: rgba(128,128,128,0.15) !important; }
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ──────────────────────────────────────────────────────────────────
INDICES = {
    "NIFTY 50":   "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "FIN NIFTY":  "^CNXFIN",
    "SENSEX":     "^BSESN",
    "BSE BANKEX": "BSE-BANKEX.BO",
}
TIMEFRAMES = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m"}
TF_PERIODS  = {"1m": "1d", "5m": "3d", "15m": "5d", "1h": "30d"}

# ─── INDICATOR HELPERS (pure pandas / numpy — no pandas-ta) ─────────────────────
def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()

def _rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta    = series.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=length - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=length - 1, adjust=False).mean()
    rs       = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(com=length - 1, adjust=False).mean()

# ─── DATA FETCHING ───────────────────────────────────────────────────────────────
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
def fetch_prev_day_ohlc(ticker: str) -> dict:
    try:
        df = yf.download(ticker, period="5d", interval="1d",
                         auto_adjust=True, progress=False)
        if df is None or df.empty or len(df) < 2:
            return {}
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        row = df.iloc[-2]
        return {
            "high":  float(row["High"]),
            "low":   float(row["Low"]),
            "close": float(row["Close"]),
        }
    except Exception:
        return {}

# ─── PIVOT CALCULATIONS ──────────────────────────────────────────────────────────
def calculate_pivots(ohlc: dict) -> dict:
    if not ohlc:
        return {}
    H, L, C = ohlc["high"], ohlc["low"], ohlc["close"]
    rng = H - L
    P   = (H + L + C) / 3
    return {
        "R2": P + 0.618 * rng,
        "R1": P + 0.382 * rng,
        "P":  P,
        "S1": P - 0.382 * rng,
        "S2": P - 0.618 * rng,
    }

# ─── INDICATOR CALCULATIONS ──────────────────────────────────────────────────────
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 22:
        return df
    df = df.copy()
    df["EMA9"]  = _ema(df["Close"], 9)
    df["EMA21"] = _ema(df["Close"], 21)
    df["RSI"]   = _rsi(df["Close"], 14)
    df["ATR"]   = _atr(df["High"], df["Low"], df["Close"], 14)
    return df

# ─── SIGNAL GENERATION ───────────────────────────────────────────────────────────
def generate_signal(df: pd.DataFrame, kill_switch: bool) -> dict:
    default = {"signal": "NONE", "entry": None, "sl": None, "target": None,
               "rsi": None, "atr": None, "ema9": None, "ema21": None}
    if kill_switch or df.empty or len(df) < 22:
        return default
    row  = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else row
    try:
        close  = float(row["Close"])
        ema9   = float(row["EMA9"])
        ema21  = float(row["EMA21"])
        rsi    = float(row["RSI"])
        atr    = float(row["ATR"])
        prev_h = float(prev["High"])
        prev_l = float(prev["Low"])
    except Exception:
        return default

    if any(np.isnan(v) for v in [ema9, ema21, rsi, atr]):
        return default

    signal = "NONE"
    sl = target = None

    if close > ema9 and ema9 > ema21 and rsi > 60 and close > prev_h:
        signal = "BUY"
        sl     = close - 1.5 * atr
        target = close + 2 * (close - sl)
    elif close < ema9 and ema9 < ema21 and rsi < 40 and close < prev_l:
        signal = "SELL"
        sl     = close + 1.5 * atr
        target = close - 2 * (sl - close)

    return {"signal": signal, "entry": close, "sl": sl, "target": target,
            "rsi": rsi, "atr": atr, "ema9": ema9, "ema21": ema21}

# ─── CHART (theme-neutral plotly) ────────────────────────────────────────────────
def build_chart(df: pd.DataFrame, pivots: dict, sig: dict) -> go.Figure:
    """
    Uses template='none' with semi-transparent grid lines so the chart
    looks sharp on both Streamlit dark and light themes.
    """
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.75, 0.25], vertical_spacing=0.04,
    )

    # Candlesticks — Neon Green / Neon Red per spec
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        increasing=dict(line=dict(color="#00CC88", width=1),
                        fillcolor="rgba(0,204,136,0.55)"),
        decreasing=dict(line=dict(color="#FF4B4B", width=1),
                        fillcolor="rgba(255,75,75,0.55)"),
        name="Price", showlegend=False,
    ), row=1, col=1)

    # EMAs
    if "EMA9" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["EMA9"],
            line=dict(color="#FFD700", width=1.4),
            name="EMA 9", hoverinfo="skip",
        ), row=1, col=1)
    if "EMA21" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["EMA21"],
            line=dict(color="#BB88FF", width=1.4),
            name="EMA 21", hoverinfo="skip",
        ), row=1, col=1)

    # Pivot S/R lines
    pivot_styles = {
        "R2": ("#FF4B4B", "dash"),
        "R1": ("#FF8888", "dot"),
        "P":  ("#5B8CFF", "dash"),
        "S1": ("#66EEB0", "dot"),
        "S2": ("#00CC88", "dash"),
    }
    for lvl, val in pivots.items():
        color, dash = pivot_styles.get(lvl, ("#888", "dash"))
        fig.add_hline(
            y=val, line=dict(color=color, width=0.9, dash=dash),
            annotation_text=f" {lvl} {val:,.0f}",
            annotation_font=dict(color=color, size=10),
            annotation_position="right",
            row=1, col=1,
        )

    # RSI subplot
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["RSI"],
            line=dict(color="#00CC88", width=1.3),
            name="RSI", fill="tozeroy",
            fillcolor="rgba(0,204,136,0.07)",
        ), row=2, col=1)
        for level, color in [(60, "rgba(0,204,136,0.5)"),
                             (40, "rgba(255,75,75,0.5)"),
                             (50, "rgba(128,128,128,0.3)")]:
            fig.add_hline(y=level, line=dict(color=color, width=0.7, dash="dot"),
                          row=2, col=1)

    # Theme-neutral layout: transparent paper/plot bg, rgba grids
    GRID = "rgba(128,128,128,0.12)"
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",   # transparent — host theme shows through
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", size=11),
        margin=dict(l=10, r=90, t=30, b=10),
        legend=dict(
            bgcolor="rgba(128,128,128,0.1)",
            bordercolor="rgba(128,128,128,0.2)", borderwidth=1,
            font=dict(size=10), x=0.01, y=0.98,
        ),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(30,30,40,0.9)", bordercolor="rgba(128,128,128,0.3)",
            font=dict(size=11),
        ),
    )
    fig.update_xaxes(
        gridcolor=GRID, showgrid=True, zeroline=False,
        showspikes=True, spikecolor="rgba(128,128,128,0.4)",
        spikedash="dot", spikethickness=1,
    )
    fig.update_yaxes(gridcolor=GRID, showgrid=True, zeroline=False, tickformat=",.0f")
    fig.update_yaxes(title_text="RSI", row=2, col=1, tickformat=".0f", range=[0, 100])
    return fig

# ─── TRADE LOG ───────────────────────────────────────────────────────────────────
def update_trade_log(sig: dict, index_name: str):
    if "trade_log" not in st.session_state:
        st.session_state.trade_log = []
    if sig["signal"] != "NONE" and sig["entry"] is not None:
        log = st.session_state.trade_log
        if not log or log[0]["signal"] != sig["signal"] or log[0]["index"] != index_name:
            st.session_state.trade_log = [{
                "time":   datetime.now().strftime("%H:%M:%S"),
                "index":  index_name,
                "signal": sig["signal"],
                "entry":  sig["entry"],
                "sl":     sig["sl"],
                "target": sig["target"],
            }] + log[:9]

# ─── MARKET STATUS (IST) — computed once, used in sidebar + main canvas ──────────
def market_status() -> tuple[bool, str]:
    now = datetime.now()
    mkt_open  = now.replace(hour=9,  minute=15, second=0, microsecond=0)
    mkt_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    is_open   = mkt_open <= now <= mkt_close and now.weekday() < 5
    return is_open, now.strftime("%d %b %Y · %H:%M:%S")

is_open_mkt, ts_mkt = market_status()   # compute once here

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="quantx-wordmark">Quant<span class="accent">X</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="quantx-tagline">F&amp;O Intelligence Terminal</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Market Index</div>', unsafe_allow_html=True)
    selected_label = st.selectbox("", list(INDICES.keys()), label_visibility="collapsed")
    ticker = INDICES[selected_label]

    st.markdown('<div class="section-header">Timeframe</div>', unsafe_allow_html=True)
    tf_label = st.radio("", list(TIMEFRAMES.keys()), horizontal=True, label_visibility="collapsed")
    interval = TIMEFRAMES[tf_label]

    st.markdown('<div class="section-header">Kill Switch</div>', unsafe_allow_html=True)
    kill_switch = st.toggle("Halt All Signals", value=False)
    if kill_switch:
        st.markdown('<div class="ks-halted">⛔ TRADING HALTED</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ks-active">✅ SIGNALS ACTIVE</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Auto Refresh</div>', unsafe_allow_html=True)
    refresh_sec = st.slider("Interval (sec)", 15, 120, 30, 5, label_visibility="collapsed")
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=refresh_sec * 1000, key="autorefresh")

    st.markdown("---")
    dot_color   = "#00CC88" if is_open_mkt else "#FF4B4B"
    status_text = "LIVE · NSE" if is_open_mkt else "CLOSED · NSE"
    st.markdown(
        f'<div style="font-size:0.7rem;font-weight:700;letter-spacing:0.1em;color:{dot_color}">'
        f'<span class="status-dot" style="background:{dot_color};box-shadow:0 0 8px {dot_color}"></span>'
        f'{status_text}</div>'
        f'<p style="font-size:0.66rem;color:rgba(128,128,128,0.65);margin-top:0.3rem">{ts_mkt}</p>',
        unsafe_allow_html=True,
    )

# ─── FETCH & COMPUTE ─────────────────────────────────────────────────────────────
with st.spinner("Fetching live data…"):
    df_raw = fetch_data(ticker, interval)
    prev_d = fetch_prev_day_ohlc(ticker)

if df_raw.empty:
    st.error("⚠️ No data returned. Market may be closed or the ticker is unavailable.")
    st.stop()

df_ind = calculate_indicators(df_raw)
pivots = calculate_pivots(prev_d)
sig    = generate_signal(df_ind, kill_switch)
update_trade_log(sig, selected_label)

try:
    ltp         = float(df_ind["Close"].iloc[-1])
    open_price  = float(df_ind["Open"].iloc[0])
    day_chg     = ltp - open_price
    day_chg_pct = (day_chg / open_price * 100) if open_price else 0
    volatility  = float(df_ind["ATR"].iloc[-1]) if "ATR" in df_ind.columns else 0.0
except Exception:
    ltp = open_price = day_chg = day_chg_pct = volatility = 0.0

# ─── FLOATING SIDEBAR TOGGLE (FAB) ──────────────────────────────────────────────
# JavaScript clicks Streamlit's native sidebar toggle button so the panel opens
# even when the header is transparent / the native arrow is hard to see.
st.markdown("""
<button class="sidebar-fab" onclick="
  (function(){
    var btn = window.parent.document.querySelector('[data-testid=\\'stSidebarCollapsedControl\\'] button')
           || window.parent.document.querySelector('button[kind=\\'header\\']')
           || window.parent.document.querySelector('[data-testid=\\'collapsedControl\\'] button');
    if(btn){ btn.click(); }
    else {
      /* Fallback: find any button containing the chevron/arrow in the top-left */
      var all = window.parent.document.querySelectorAll('button');
      for(var i=0;i<all.length;i++){
        var r = all[i].getBoundingClientRect();
        if(r.left < 80 && r.top < 80){ all[i].click(); break; }
      }
    }
  })()
" title="Open control panel">⚙ &nbsp;Controls</button>
""", unsafe_allow_html=True)

# ─── QUICK-CONTROLS BAR (always visible on main canvas) ──────────────────────────
is_open_mkt, ts_mkt = market_status()
mkt_dot   = "#00CC88" if is_open_mkt else "#FF4B4B"
mkt_label = "LIVE" if is_open_mkt else "CLOSED"

index_chips = ""
for label in INDICES.keys():
    active = "active" if label == selected_label else ""
    index_chips += f'<span class="ctrl-chip {active}">{label}</span>'

tf_chips = ""
for tfl in TIMEFRAMES.keys():
    active = "active" if tfl == tf_label else ""
    tf_chips += f'<span class="ctrl-chip {active}">{tfl}</span>'

st.markdown(f"""
<div class="ctrl-bar">
  <span class="ctrl-label">Index</span>
  {index_chips}
  <div class="ctrl-divider"></div>
  <span class="ctrl-label">TF</span>
  {tf_chips}
  <div class="ctrl-label ctrl-mkt" style="color:{mkt_dot}">
    <span style="display:inline-block;width:7px;height:7px;border-radius:50%;
      background:{mkt_dot};box-shadow:0 0 6px {mkt_dot};margin-right:5px;
      vertical-align:middle;"></span>NSE {mkt_label} · {ts_mkt}
  </div>
</div>
<p style="font-size:0.7rem;color:rgba(128,128,128,0.5);margin:-0.5rem 0 0.8rem 0.2rem;">
  ⚙ Use the <strong>Controls</strong> button (top-left) or the sidebar to change index, timeframe &amp; refresh settings.
</p>
""", unsafe_allow_html=True)

# ─── METRIC CARDS ────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    chg_cls   = "clr-up" if day_chg >= 0 else "clr-down"
    chg_arrow = "▲" if day_chg >= 0 else "▼"
    st.markdown(f"""
    <div class="metric-card card-blue">
      <div class="metric-label">LTP · {selected_label}</div>
      <div class="metric-value">₹{ltp:,.2f}</div>
      <div class="metric-sub">
        <span class="{chg_cls}">{chg_arrow} {abs(day_chg):,.2f} ({abs(day_chg_pct):.2f}%)</span>
        &nbsp;today
      </div>
    </div>""", unsafe_allow_html=True)

with c2:
    s = sig["signal"]
    card_cls  = "card-buy" if s == "BUY" else ("card-sell" if s == "SELL" else "card-blue")
    sig_cls   = "clr-buy"  if s == "BUY" else ("clr-sell"  if s == "SELL" else "clr-none")
    icon      = "▲" if s == "BUY" else ("▼" if s == "SELL" else "⏸")
    rsi_txt   = f"RSI {sig['rsi']:.1f}" if sig["rsi"] else "—"
    st.markdown(f"""
    <div class="metric-card {card_cls}">
      <div class="metric-label">Signal · {tf_label}</div>
      <div class="metric-value {sig_cls}">{icon} {s}</div>
      <div class="metric-sub">{rsi_txt} · EMA confluence</div>
    </div>""", unsafe_allow_html=True)

with c3:
    sl_val   = f"₹{sig['sl']:,.2f}" if sig["sl"] else "—"
    sl_pct   = (abs(ltp - sig["sl"]) / ltp * 100) if sig["sl"] and ltp else 0
    sl_color = "clr-sell" if sig["sl"] else ""
    st.markdown(f"""
    <div class="metric-card card-sell">
      <div class="metric-label">Stop Loss · 1.5× ATR</div>
      <div class="metric-value {sl_color}">{sl_val}</div>
      <div class="metric-sub">Risk {sl_pct:.2f}% · ATR {volatility:,.1f}</div>
    </div>""", unsafe_allow_html=True)

with c4:
    tgt_val  = f"₹{sig['target']:,.2f}" if sig["target"] else "—"
    rr_dist  = abs(sig["target"] - ltp) if sig["target"] and ltp else 0
    tgt_color = "clr-buy" if sig["target"] else ""
    st.markdown(f"""
    <div class="metric-card card-buy">
      <div class="metric-label">Target · 1:2 R/R</div>
      <div class="metric-value {tgt_color}">{tgt_val}</div>
      <div class="metric-sub">Reward ₹{rr_dist:,.2f} potential</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── MAIN CHART ──────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="section-header">Price Action · Candlestick with Fibonacci S/R Overlays</div>',
    unsafe_allow_html=True,
)
fig = build_chart(df_ind, pivots, sig)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ─── BOTTOM ROW ──────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="section-header">Fibonacci Pivot Levels</div>', unsafe_allow_html=True)
    if pivots:
        level_meta = {
            "R2": ("Resistance 2", "r-level"),
            "R1": ("Resistance 1", "r-level"),
            "P":  ("Pivot Point",  "p-level"),
            "S1": ("Support 1",    "s-level"),
            "S2": ("Support 2",    "s-level"),
        }
        rows_html = ""
        for k in ["R2", "R1", "P", "S1", "S2"]:
            v        = pivots.get(k, 0)
            name, cls = level_meta[k]
            diff     = ((v - ltp) / ltp * 100) if ltp else 0
            diff_str = f"+{diff:.2f}%" if diff > 0 else f"{diff:.2f}%"
            diff_col = "clr-up" if diff > 0 else "clr-down"
            rows_html += f"""
            <tr>
              <td>{name}</td>
              <td class="{cls}">{k}</td>
              <td class="{cls}">₹{v:,.2f}</td>
              <td class="{diff_col}" style="text-align:right">{diff_str}</td>
            </tr>"""
        st.markdown(f"""
        <table class="pivot-table">
          <thead><tr>
            <th>Level</th><th>Label</th><th>Price</th><th style="text-align:right">vs LTP</th>
          </tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)
    else:
        st.markdown(
            '<p style="color:rgba(128,128,128,0.6);font-size:0.8rem">Pivot data unavailable.</p>',
            unsafe_allow_html=True,
        )

with col_right:
    st.markdown('<div class="section-header">Live Trade Log · Last 5 Signals</div>', unsafe_allow_html=True)
    log = st.session_state.get("trade_log", [])
    if not log:
        st.markdown(
            '<p style="color:rgba(128,128,128,0.6);font-size:0.8rem;padding:0.5rem 0">'
            'No signals yet — waiting for EMA + RSI confluence…</p>',
            unsafe_allow_html=True,
        )
    else:
        for entry in log[:5]:
            sc    = "buy" if entry["signal"] == "BUY" else "sell"
            sl_s  = f"SL ₹{entry['sl']:,.2f}"     if entry["sl"]     else ""
            tgt_s = f"· T ₹{entry['target']:,.2f}" if entry["target"] else ""
            st.markdown(f"""
            <div class="trade-log-entry">
              <div>
                <div class="trade-log-time">{entry['time']} · {entry['index']}</div>
                <div class="trade-log-price">₹{entry['entry']:,.2f}
                  <span style="color:rgba(128,128,128,0.6);font-size:0.7rem"> {sl_s} {tgt_s}</span>
                </div>
              </div>
              <span class="trade-log-signal {sc}">{entry['signal']}</span>
            </div>""", unsafe_allow_html=True)
