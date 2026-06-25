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
    page_title="QuantX · F&O Intelligence Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

  html, body, [class*="css"] { font-family:'Inter',sans-serif; background:#0E1117; color:#E0E0E0; }
  .stApp { background:#0E1117; }
  #MainMenu, footer, header { visibility:hidden; }
  .block-container { padding:1.2rem 2rem 2rem; max-width:100%; }

  [data-testid="stSidebar"] { background:#0B0D13; border-right:1px solid #1A1E2A; }

  .qx-wordmark { font-family:'JetBrains Mono',monospace; font-size:1.55rem; font-weight:700;
    letter-spacing:-0.04em; color:#fff; line-height:1; margin-bottom:.1rem; }
  .qx-wordmark span { color:#00FFA3; }
  .qx-tagline { font-size:.64rem; color:#3D4560; letter-spacing:.14em; text-transform:uppercase;
    font-weight:600; margin-bottom:1.4rem; }

  /* REGIME BANNER */
  .regime-trending { background:rgba(0,255,163,.07); border:1px solid rgba(0,255,163,.25);
    border-radius:8px; padding:.55rem 1rem; font-size:.72rem; font-weight:700;
    letter-spacing:.08em; color:#00FFA3; text-align:center; margin-bottom:1rem; }
  .regime-choppy   { background:rgba(255,180,0,.07);  border:1px solid rgba(255,180,0,.25);
    border-radius:8px; padding:.55rem 1rem; font-size:.72rem; font-weight:700;
    letter-spacing:.08em; color:#FFB400; text-align:center; margin-bottom:1rem; }
  .regime-volatile { background:rgba(255,75,75,.07);  border:1px solid rgba(255,75,75,.25);
    border-radius:8px; padding:.55rem 1rem; font-size:.72rem; font-weight:700;
    letter-spacing:.08em; color:#FF4B4B; text-align:center; margin-bottom:1rem; }

  /* METRIC CARDS */
  .metric-card { background:#13161E; border:1px solid #1E2330; border-radius:10px;
    padding:.9rem 1.1rem; position:relative; overflow:hidden; height:100%; }
  .metric-card::before { content:''; position:absolute; top:0;left:0;right:0; height:2px;
    background:linear-gradient(90deg,#00FFA3 0%,transparent 100%); opacity:.55; }
  .metric-card.sell-card::before { background:linear-gradient(90deg,#FF4B4B 0%,transparent 100%); }
  .metric-card.neutral-card::before { background:linear-gradient(90deg,#5B6BFF 0%,transparent 100%); }
  .metric-card.amber-card::before  { background:linear-gradient(90deg,#FFB400 0%,transparent 100%); }
  .metric-label { font-size:.62rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
    color:#3D4560; margin-bottom:.35rem; }
  .metric-value { font-family:'JetBrains Mono',monospace; font-size:1.35rem; font-weight:700;
    color:#fff; line-height:1.1; }
  .metric-sub { font-size:.69rem; color:#555E78; margin-top:.28rem; }
  .signal-buy  { color:#00FFA3!important; }
  .signal-sell { color:#FF4B4B!important; }
  .signal-none { color:#5B6BFF!important; }

  .section-hdr { font-size:.62rem; font-weight:700; letter-spacing:.13em; text-transform:uppercase;
    color:#3D4560; border-bottom:1px solid #1A1E2A; padding-bottom:.35rem; margin:.9rem 0 .7rem; }

  /* SCORE GAUGE */
  .score-wrap { display:flex; align-items:center; gap:.6rem; margin-top:.3rem; }
  .score-bar-bg { flex:1; height:5px; background:#1A1E2A; border-radius:3px; overflow:hidden; }
  .score-bar-fill { height:100%; border-radius:3px; transition:width .4s ease; }
  .score-num { font-family:'JetBrains Mono',monospace; font-size:.9rem; font-weight:700;
    min-width:2.4rem; text-align:right; }

  /* MTF GRID */
  .mtf-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:.4rem; margin-top:.4rem; }
  .mtf-cell { background:#0E1117; border:1px solid #1A1E2A; border-radius:6px;
    padding:.45rem .5rem; text-align:center; }
  .mtf-tf   { font-size:.58rem; color:#3D4560; font-weight:700; letter-spacing:.1em;
    text-transform:uppercase; margin-bottom:.25rem; }
  .mtf-sig  { font-size:.72rem; font-weight:700; font-family:'JetBrains Mono',monospace; }
  .mtf-buy  { color:#00FFA3; }
  .mtf-sell { color:#FF4B4B; }
  .mtf-none { color:#3D4560; }

  /* PIVOT TABLE */
  .pivot-table { width:100%; border-collapse:collapse; font-family:'JetBrains Mono',monospace;
    font-size:.8rem; }
  .pivot-table td,.pivot-table th { padding:.5rem .75rem; border-bottom:1px solid #1A1E2A; text-align:right; }
  .pivot-table th { color:#3D4560; font-size:.6rem; letter-spacing:.08em;
    text-transform:uppercase; text-align:left; }
  .pivot-table td:first-child { text-align:left; color:#555E78; }
  .r-level{color:#FF4B4B;} .s-level{color:#00FFA3;} .p-level{color:#5B6BFF;}

  /* OPTIONS CALC */
  .options-card { background:#0B0D13; border:1px solid #1A1E2A; border-radius:8px;
    padding:.8rem 1rem; margin-top:.5rem; }
  .options-row { display:flex; justify-content:space-between; align-items:center;
    padding:.3rem 0; border-bottom:1px solid #1A1E2A; }
  .options-row:last-child { border-bottom:none; }
  .options-key { font-size:.65rem; color:#555E78; font-weight:600; letter-spacing:.06em; text-transform:uppercase; }
  .options-val { font-family:'JetBrains Mono',monospace; font-size:.85rem; color:#E0E0E0; font-weight:600; }
  .options-val.green { color:#00FFA3; }
  .options-val.red   { color:#FF4B4B; }

  /* TRADE LOG */
  .tlog-entry { background:#13161E; border:1px solid #1E2330; border-radius:8px;
    padding:.65rem .9rem; margin-bottom:.4rem;
    display:flex; justify-content:space-between; align-items:center; }
  .tlog-time  { font-family:'JetBrains Mono',monospace; font-size:.63rem; color:#3D4560; }
  .tlog-badge { font-size:.66rem; font-weight:700; letter-spacing:.07em;
    padding:.18rem .55rem; border-radius:4px; }
  .tlog-badge.buy  { background:rgba(0,255,163,.12); color:#00FFA3; }
  .tlog-badge.sell { background:rgba(255,75,75,.12);  color:#FF4B4B; }
  .tlog-price { font-family:'JetBrains Mono',monospace; font-size:.78rem; color:#E0E0E0; }

  /* KILL SWITCH */
  .ks-off { background:rgba(255,75,75,.08); border:1px solid #FF4B4B44; border-radius:8px;
    padding:.55rem 1rem; font-size:.72rem; color:#FF4B4B; text-align:center;
    font-weight:700; letter-spacing:.06em; margin-top:.4rem; }
  .ks-on  { background:rgba(0,255,163,.08); border:1px solid #00FFA344; border-radius:8px;
    padding:.55rem 1rem; font-size:.72rem; color:#00FFA3; text-align:center;
    font-weight:700; letter-spacing:.06em; margin-top:.4rem; }

  .status-dot { display:inline-block; width:6px; height:6px; border-radius:50%;
    animation:pulse 2s infinite; margin-right:5px; vertical-align:middle; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.35} }

  /* WIN RATE */
  .wr-bar-bg { width:100%; height:6px; background:#1A1E2A; border-radius:3px; overflow:hidden; margin-top:.4rem; }
  .wr-bar-fill { height:100%; border-radius:3px; }

  [data-testid="stSelectbox"]>div>div,[data-testid="stRadio"] label { color:#E0E0E0!important; }
  .stSelectbox [data-baseweb="select"]>div { background:#1A1E2A!important; border-color:#1A1E2A!important; }
  hr { border-color:#1A1E2A!important; }
  .stNumberInput input { background:#1A1E2A!important; border-color:#1A1E2A!important; color:#E0E0E0!important; }
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ──────────────────────────────────────────────────────────────────
INDICES = {
    "NIFTY 50":   {"ticker": "^NSEI",        "lot": 75,  "label": "NIFTY"},
    "BANK NIFTY": {"ticker": "^NSEBANK",     "lot": 30,  "label": "BANKNIFTY"},
    "FIN NIFTY":  {"ticker": "^CNXFIN",      "lot": 65,  "label": "FINNIFTY"},
    "SENSEX":     {"ticker": "^BSESN",       "lot": 20,  "label": "SENSEX"},
    "BSE BANKEX": {"ticker": "BSE-BANKEX.BO","lot": 20,  "label": "BANKEX"},
}
TIMEFRAMES = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m"}
TF_PERIODS = {"1m": "1d", "5m": "3d", "15m": "5d",  "1h": "30d"}
MTF_MAP    = {"1m": ["1m","5m","15m"], "5m": ["5m","15m","60m"],
              "15m":["15m","60m","1d"],"1h": ["60m","1d","1wk"]}

# ─── INDICATOR ENGINE ───────────────────────────────────────────────────────────
def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()

def _rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d = s.diff()
    ag = d.clip(lower=0).ewm(com=n-1, adjust=False).mean()
    al = (-d).clip(lower=0).ewm(com=n-1, adjust=False).mean()
    return 100 - (100 / (1 + ag / al.replace(0, np.nan)))

def _atr(h: pd.Series, l: pd.Series, c: pd.Series, n: int = 14) -> pd.Series:
    pc = c.shift(1)
    tr = pd.concat([h-l, (h-pc).abs(), (l-pc).abs()], axis=1).max(axis=1)
    return tr.ewm(com=n-1, adjust=False).mean()

def _adx(h: pd.Series, l: pd.Series, c: pd.Series, n: int = 14) -> pd.Series:
    """Wilder's ADX — pure pandas implementation."""
    up   = h.diff()
    down = -l.diff()
    pdm  = up.where((up > down) & (up > 0), 0.0)
    ndm  = down.where((down > up) & (down > 0), 0.0)
    atr  = _atr(h, l, c, n)
    pdi  = 100 * pdm.ewm(com=n-1, adjust=False).mean() / atr.replace(0, np.nan)
    ndi  = 100 * ndm.ewm(com=n-1, adjust=False).mean() / atr.replace(0, np.nan)
    dx   = (100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan))
    return dx.ewm(com=n-1, adjust=False).mean()

# ─── DATA FETCHING ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def fetch_data(ticker: str, interval: str) -> pd.DataFrame:
    period = TF_PERIODS.get(interval, "5d")
    if interval not in TF_PERIODS:
        period = "30d"
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
        return {"high": float(row["High"]), "low": float(row["Low"]),
                "close": float(row["Close"])}
    except Exception:
        return {}

# ─── PIVOT CALCULATIONS ──────────────────────────────────────────────────────────
def calculate_pivots(ohlc: dict) -> dict:
    if not ohlc:
        return {}
    H, L, C = ohlc["high"], ohlc["low"], ohlc["close"]
    rng = H - L
    P   = (H + L + C) / 3
    return {"R2": P+0.618*rng, "R1": P+0.382*rng, "P": P,
            "S1": P-0.382*rng, "S2": P-0.618*rng}

# ─── INDICATOR CALCULATIONS ──────────────────────────────────────────────────────
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 30:
        return df
    df = df.copy()
    df["EMA9"]   = _ema(df["Close"], 9)
    df["EMA21"]  = _ema(df["Close"], 21)
    df["EMA50"]  = _ema(df["Close"], 50)
    df["RSI"]    = _rsi(df["Close"], 14)
    df["ATR"]    = _atr(df["High"], df["Low"], df["Close"], 14)
    df["ADX"]    = _adx(df["High"], df["Low"], df["Close"], 14)
    df["ATR20"]  = _atr(df["High"], df["Low"], df["Close"], 20)  # baseline ATR
    if "Volume" in df.columns:
        df["VolAvg20"] = df["Volume"].rolling(20).mean()
    return df

# ─── SIGNAL SCORING ENGINE ───────────────────────────────────────────────────────
def score_signal(row: pd.Series, prev: pd.Series, direction: str) -> int:
    """Returns 0-100 signal quality score."""
    score = 0
    close  = float(row.get("Close", 0))
    ema9   = float(row.get("EMA9",  0))
    ema21  = float(row.get("EMA21", 0))
    ema50  = float(row.get("EMA50", 0))
    rsi    = float(row.get("RSI",   50))
    adx    = float(row.get("ADX",   0))
    atr    = float(row.get("ATR",   0))
    atr20  = float(row.get("ATR20", atr))
    vol    = float(row.get("Volume",  0))
    vavg   = float(row.get("VolAvg20", 0))

    if direction == "BUY":
        # EMA alignment (25 pts)
        if ema9 > ema21:      score += 15
        if ema21 > ema50:     score += 10
        # RSI zone (20 pts) — penalise overbought
        if rsi > 60:          score += 10
        if 60 <= rsi <= 75:   score += 10
        elif rsi > 75:        score -= 5
        # Candle breakout (10 pts)
        if close > float(prev.get("High", 0)): score += 10
    else:  # SELL
        if ema9 < ema21:      score += 15
        if ema21 < ema50:     score += 10
        if rsi < 40:          score += 10
        if 25 <= rsi < 40:    score += 10
        elif rsi < 25:        score -= 5
        if close < float(prev.get("Low", 0)):  score += 10

    # ADX trend strength (20 pts)
    if adx > 25:  score += 20
    elif adx > 20: score += 10

    # Volume surge (25 pts)
    if vavg > 0:
        ratio = vol / vavg
        if ratio >= 1.5:   score += 25
        elif ratio >= 1.2: score += 15
        elif ratio >= 1.0: score += 5

    return max(0, min(100, score))

# ─── MARKET REGIME ───────────────────────────────────────────────────────────────
def get_regime(df: pd.DataFrame) -> dict:
    """Returns regime: TRENDING / CHOPPY / VOLATILE"""
    if df.empty or len(df) < 20:
        return {"label": "UNKNOWN", "class": "regime-choppy", "suppress": True}
    row   = df.iloc[-1]
    adx   = float(row.get("ADX", 0))
    atr   = float(row.get("ATR", 0))
    atr20 = float(row.get("ATR20", atr))
    vol_ratio = atr / atr20 if atr20 > 0 else 1.0

    if vol_ratio > 2.0:
        return {"label": "⚡ HIGH VOLATILITY — Reduce Size", "class": "regime-volatile", "suppress": False}
    elif adx >= 25:
        return {"label": "📈 TRENDING — Signals Active", "class": "regime-trending", "suppress": False}
    else:
        return {"label": "〰️ CHOPPY — Signals Suppressed", "class": "regime-choppy", "suppress": True}

# ─── MAIN SIGNAL GENERATION ──────────────────────────────────────────────────────
def generate_signal(df: pd.DataFrame, kill_switch: bool, regime: dict) -> dict:
    default = {"signal": "NONE", "entry": None, "sl": None, "target": None,
               "rsi": None, "atr": None, "adx": None, "score": 0,
               "ema9": None, "ema21": None, "ema50": None, "suppressed": False}
    if kill_switch or df.empty or len(df) < 30:
        return default
    if regime.get("suppress", False):
        d = default.copy(); d["suppressed"] = True; return d

    row  = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else row
    try:
        close = float(row["Close"]); ema9 = float(row["EMA9"])
        ema21 = float(row["EMA21"]); rsi  = float(row["RSI"])
        atr   = float(row["ATR"]);   adx  = float(row.get("ADX", 0))
        ema50 = float(row.get("EMA50", ema21))
        prev_h = float(prev["High"]); prev_l = float(prev["Low"])
    except Exception:
        return default
    if any(np.isnan(v) for v in [ema9, ema21, rsi, atr]):
        return default

    signal = "NONE"; sl = target = None; score = 0

    if close > ema9 and ema9 > ema21 and rsi > 60 and close > prev_h:
        score = score_signal(row, prev, "BUY")
        if score >= 70:
            signal = "BUY"; sl = close - 1.5*atr; target = close + 2*(close-sl)

    elif close < ema9 and ema9 < ema21 and rsi < 40 and close < prev_l:
        score = score_signal(row, prev, "SELL")
        if score >= 70:
            signal = "SELL"; sl = close + 1.5*atr; target = close - 2*(sl-close)

    return {"signal": signal, "entry": close, "sl": sl, "target": target,
            "rsi": rsi, "atr": atr, "adx": adx, "score": score,
            "ema9": ema9, "ema21": ema21, "ema50": ema50, "suppressed": False}

# ─── MTF ANALYSIS ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def get_mtf_signals(ticker: str, base_tf: str) -> dict:
    tfs = MTF_MAP.get(base_tf, ["5m","15m","60m"])
    results = {}
    for tf in tfs:
        period = TF_PERIODS.get(tf, "30d")
        try:
            df = yf.download(ticker, period=period, interval=tf,
                             auto_adjust=True, progress=False)
            if df is None or df.empty or len(df) < 22:
                results[tf] = "—"; continue
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            df.dropna(inplace=True)
            df = calculate_indicators(df)
            if len(df) < 2: results[tf] = "—"; continue
            r = df.iloc[-1]; p = df.iloc[-2]
            e9 = float(r.get("EMA9",0)); e21 = float(r.get("EMA21",0))
            rsi = float(r.get("RSI",50)); c = float(r["Close"])
            if c>e9 and e9>e21 and rsi>55:  results[tf] = "BUY"
            elif c<e9 and e9<e21 and rsi<45: results[tf] = "SELL"
            else: results[tf] = "FLAT"
        except Exception:
            results[tf] = "—"
    return results

# ─── OPTIONS POSITION CALCULATOR ─────────────────────────────────────────────────
def calc_options_metrics(sig: dict, capital: float, risk_pct: float, lot_size: int) -> dict:
    if sig["signal"] == "NONE" or sig["sl"] is None:
        return {}
    entry = sig["entry"]; sl = sig["sl"]; target = sig["target"]
    sl_pts  = abs(entry - sl)
    tgt_pts = abs(target - entry)
    max_loss_rs    = capital * (risk_pct / 100)
    lots_suggested = max(1, int(max_loss_rs / (sl_pts * lot_size)))
    capital_at_risk = lots_suggested * sl_pts * lot_size
    potential_gain  = lots_suggested * tgt_pts * lot_size
    return {
        "sl_pts":        sl_pts,
        "tgt_pts":       tgt_pts,
        "lots":          lots_suggested,
        "cap_risk":      capital_at_risk,
        "pot_gain":      potential_gain,
        "rr":            round(tgt_pts / sl_pts, 2) if sl_pts else 0,
    }

# ─── TRADE LOG ───────────────────────────────────────────────────────────────────
def update_trade_log(sig: dict, index_name: str):
    if "trade_log" not in st.session_state:
        st.session_state.trade_log = []
    if sig["signal"] != "NONE" and sig["entry"] is not None:
        log = st.session_state.trade_log
        if not log or log[0]["signal"] != sig["signal"] or log[0]["index"] != index_name:
            st.session_state.trade_log = [{
                "time":   datetime.now().strftime("%H:%M:%S"),
                "index":  index_name, "signal": sig["signal"],
                "entry":  sig["entry"], "sl": sig["sl"],
                "target": sig["target"], "score": sig.get("score", 0),
            }] + log[:19]

def get_win_rate() -> tuple[float, int]:
    log = st.session_state.get("trade_log", [])
    if not log: return 0.0, 0
    buy_signals  = [e for e in log if e["signal"] == "BUY"]
    sell_signals = [e for e in log if e["signal"] == "SELL"]
    total = len(log)
    wins  = len(buy_signals) + len(sell_signals)  # placeholder — real PnL needs exit tracking
    return (wins / total * 100) if total else 0.0, total

# ─── CHART ───────────────────────────────────────────────────────────────────────
def build_chart(df: pd.DataFrame, pivots: dict, sig: dict) -> go.Figure:
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.03)

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing=dict(line=dict(color="#00FFA3",width=1), fillcolor="rgba(0,255,163,.5)"),
        decreasing=dict(line=dict(color="#FF4B4B",width=1), fillcolor="rgba(255,75,75,.5)"),
        name="Price", showlegend=False,
    ), row=1, col=1)

    for col, name, color in [("EMA9","EMA 9","#FFD700"),("EMA21","EMA 21","#AA80FF"),("EMA50","EMA 50","#5B6BFF")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[col],
                line=dict(color=color,width=1.1), name=name, hoverinfo="skip"), row=1, col=1)

    pivot_styles = {"R2":("#FF4B4B","dash"),"R1":("#FF8080","dot"),
                    "P":("#5B6BFF","dash"),"S1":("#80FFC8","dot"),"S2":("#00FFA3","dash")}
    for lvl, val in pivots.items():
        color, dash = pivot_styles.get(lvl, ("#888","dash"))
        fig.add_hline(y=val, line=dict(color=color,width=0.8,dash=dash),
                      annotation_text=f" {lvl} {val:,.0f}",
                      annotation_font=dict(color=color,size=10),
                      annotation_position="right", row=1, col=1)

    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"],
            line=dict(color="#00FFA3",width=1.1), name="RSI",
            fill="tozeroy", fillcolor="rgba(0,255,163,.05)"), row=2, col=1)
        for level, color in [(60,"#00FFA3"),(40,"#FF4B4B"),(50,"#2A3040")]:
            fig.add_hline(y=level, line=dict(color=color,width=0.6,dash="dot"), row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0,100], tickformat=".0f",
                         gridcolor="#1A1E2A", showgrid=True)

    if "ADX" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["ADX"],
            line=dict(color="#FFB400",width=1.1), name="ADX",
            fill="tozeroy", fillcolor="rgba(255,180,0,.05)"), row=3, col=1)
        fig.add_hline(y=25, line=dict(color="#FFB400",width=0.7,dash="dot"), row=3, col=1)
        fig.update_yaxes(title_text="ADX", row=3, col=1, range=[0,60], tickformat=".0f",
                         gridcolor="#1A1E2A", showgrid=True)

    fig.update_layout(
        paper_bgcolor="#0E1117", plot_bgcolor="#0E1117",
        font=dict(family="JetBrains Mono, monospace", color="#555E78", size=10),
        margin=dict(l=10,r=80,t=25,b=10),
        legend=dict(bgcolor="#13161E", bordercolor="#1E2330", borderwidth=1,
                    font=dict(size=9,color="#E0E0E0"), x=0.01, y=0.99),
        xaxis_rangeslider_visible=False, hovermode="x unified",
        hoverlabel=dict(bgcolor="#13161E",bordercolor="#1E2330",
                        font=dict(color="#E0E0E0",size=10)),
    )
    fig.update_xaxes(gridcolor="#1A1E2A", showgrid=True, zeroline=False,
                     showspikes=True, spikecolor="#2A3040", spikedash="dot", spikethickness=1)
    fig.update_yaxes(gridcolor="#1A1E2A", showgrid=True, zeroline=False, tickformat=",.0f",
                     row=1, col=1)
    return fig

# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="qx-wordmark">Quant<span>X</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="qx-tagline">F&amp;O Intelligence Terminal · v2</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-hdr">Market Index</div>', unsafe_allow_html=True)
    selected_label = st.selectbox("", list(INDICES.keys()), label_visibility="collapsed")
    idx_meta = INDICES[selected_label]
    ticker   = idx_meta["ticker"]
    lot_size = idx_meta["lot"]

    st.markdown('<div class="section-hdr">Timeframe</div>', unsafe_allow_html=True)
    tf_label = st.radio("", list(TIMEFRAMES.keys()), horizontal=True, label_visibility="collapsed")
    interval = TIMEFRAMES[tf_label]

    st.markdown('<div class="section-hdr">Position Sizing</div>', unsafe_allow_html=True)
    capital   = st.number_input("Capital (₹)", min_value=10000, max_value=10000000,
                                value=100000, step=10000, label_visibility="collapsed")
    risk_pct  = st.slider("Risk per Trade (%)", 0.5, 3.0, 1.0, 0.25)

    st.markdown('<div class="section-hdr">Kill Switch</div>', unsafe_allow_html=True)
    kill_switch = st.toggle("Halt All Signals", value=False)
    if kill_switch:
        st.markdown('<div class="ks-off">⛔ TRADING HALTED</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ks-on">✅ SIGNALS ACTIVE</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-hdr">Auto Refresh</div>', unsafe_allow_html=True)
    refresh_sec = st.slider("Interval (sec)", 15, 120, 30, 5, label_visibility="collapsed")
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=refresh_sec * 1000, key="autorefresh")

    st.markdown("---")
    now       = datetime.now()
    mkt_open  = now.replace(hour=9,  minute=15, second=0, microsecond=0)
    mkt_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    is_open   = mkt_open <= now <= mkt_close and now.weekday() < 5
    dot_clr   = "#00FFA3" if is_open else "#FF4B4B"
    status_tx = "LIVE" if is_open else "CLOSED"
    st.markdown(
        f'<div style="font-size:.68rem;font-weight:700;letter-spacing:.1em;color:{dot_clr}">'
        f'<span class="status-dot" style="background:{dot_clr};box-shadow:0 0 6px {dot_clr}"></span>'
        f'NSE {status_tx}</div>'
        f'<p style="font-size:.63rem;color:#3D4560;margin-top:.25rem">'
        f'{now.strftime("%d %b %Y · %H:%M:%S")}</p>',
        unsafe_allow_html=True)

    st.markdown('<div class="section-hdr">Lot Size Reference</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:.7rem;color:#555E78;font-family:\'JetBrains Mono\',monospace">'
                f'{idx_meta["label"]} · {lot_size} units/lot</p>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  FETCH & COMPUTE
# ═══════════════════════════════════════════════════════════════════════════════
with st.spinner("Syncing live market data…"):
    df_raw  = fetch_data(ticker, interval)
    prev_d  = fetch_prev_day_ohlc(ticker)
    mtf_sigs = get_mtf_signals(ticker, interval)

if df_raw.empty:
    st.error("⚠️ No data returned. Market may be closed or ticker unavailable.")
    st.stop()

df_ind = calculate_indicators(df_raw)
pivots = calculate_pivots(prev_d)
regime = get_regime(df_ind)
sig    = generate_signal(df_ind, kill_switch, regime)
update_trade_log(sig, selected_label)

try:
    ltp         = float(df_ind["Close"].iloc[-1])
    open_price  = float(df_ind["Open"].iloc[0])
    day_chg     = ltp - open_price
    day_chg_pct = (day_chg / open_price * 100) if open_price else 0
    volatility  = float(df_ind["ATR"].iloc[-1])  if "ATR" in df_ind.columns else 0.0
    adx_val     = float(df_ind["ADX"].iloc[-1])  if "ADX" in df_ind.columns else 0.0
except Exception:
    ltp = open_price = day_chg = day_chg_pct = volatility = adx_val = 0.0

opts = calc_options_metrics(sig, capital, risk_pct, lot_size)

# ═══════════════════════════════════════════════════════════════════════════════
#  REGIME BANNER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f'<div class="{regime["class"]}">{regime["label"]}</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  ROW 1 — METRIC CARDS
# ═══════════════════════════════════════════════════════════════════════════════
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    chg_c = "#00FFA3" if day_chg >= 0 else "#FF4B4B"
    arrow = "▲" if day_chg >= 0 else "▼"
    st.markdown(f"""<div class="metric-card neutral-card">
      <div class="metric-label">LTP · {selected_label}</div>
      <div class="metric-value">₹{ltp:,.2f}</div>
      <div class="metric-sub" style="color:{chg_c}">{arrow} {abs(day_chg):,.2f} ({abs(day_chg_pct):.2f}%)</div>
    </div>""", unsafe_allow_html=True)

with c2:
    s   = sig["signal"]
    sc  = "signal-buy" if s=="BUY" else ("signal-sell" if s=="SELL" else "signal-none")
    crd = "metric-card" if s=="BUY" else ("sell-card metric-card" if s=="SELL" else "neutral-card metric-card")
    ico = "🔼" if s=="BUY" else ("🔽" if s=="SELL" else ("⚠️" if sig.get("suppressed") else "⏸"))
    sub = f"Score {sig['score']}/100" if sig['score'] else ("Regime suppressed" if sig.get("suppressed") else "Awaiting confluence")
    st.markdown(f"""<div class="{crd}">
      <div class="metric-label">Signal · {tf_label}</div>
      <div class="metric-value {sc}">{ico} {s}</div>
      <div class="metric-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

with c3:
    sl_v  = f"₹{sig['sl']:,.2f}" if sig["sl"] else "—"
    sl_pc = abs(ltp-sig["sl"])/ltp*100 if sig["sl"] and ltp else 0
    sl_c  = "#FF4B4B" if sig["sl"] else "#3D4560"
    st.markdown(f"""<div class="metric-card sell-card">
      <div class="metric-label">Stop Loss · 1.5× ATR</div>
      <div class="metric-value" style="color:{sl_c}">{sl_v}</div>
      <div class="metric-sub">Risk {sl_pc:.2f}% · ATR {volatility:,.1f}</div>
    </div>""", unsafe_allow_html=True)

with c4:
    tgt_v  = f"₹{sig['target']:,.2f}" if sig["target"] else "—"
    rr_d   = abs(sig["target"]-ltp) if sig["target"] and ltp else 0
    tgt_c  = "#00FFA3" if sig["target"] else "#3D4560"
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Target · 1:2 R/R</div>
      <div class="metric-value" style="color:{tgt_c}">{tgt_v}</div>
      <div class="metric-sub">Reward ₹{rr_d:,.2f} · ADX {adx_val:.1f}</div>
    </div>""", unsafe_allow_html=True)

with c5:
    score    = sig.get("score", 0)
    sc_color = "#00FFA3" if score >= 70 else ("#FFB400" if score >= 50 else "#FF4B4B")
    sc_crd   = "metric-card" if score >= 70 else ("amber-card metric-card" if score >= 50 else "sell-card metric-card")
    st.markdown(f"""<div class="{sc_crd}">
      <div class="metric-label">Signal Score</div>
      <div class="score-wrap">
        <div class="score-bar-bg">
          <div class="score-bar-fill" style="width:{score}%;background:{sc_color}"></div>
        </div>
        <div class="score-num" style="color:{sc_color}">{score}</div>
      </div>
      <div class="metric-sub">Min 70 to fire · {'>= 70 ✅' if score>=70 else ('Suppressed ⚠️' if score>=50 else 'Below threshold ✗')}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  CHART
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-hdr">Price Action · Candlestick + EMA + S/R + RSI + ADX</div>',
            unsafe_allow_html=True)
fig = build_chart(df_ind, pivots, sig)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ═══════════════════════════════════════════════════════════════════════════════
#  BOTTOM ROW
# ═══════════════════════════════════════════════════════════════════════════════
col_a, col_b, col_c = st.columns([1, 1, 1], gap="large")

# ── PIVOT TABLE ──────────────────────────────────────────────────────────────
with col_a:
    st.markdown('<div class="section-hdr">Fibonacci Pivot Levels</div>', unsafe_allow_html=True)
    if pivots:
        meta = {"R2":("Resistance 2","r-level"),"R1":("Resistance 1","r-level"),
                "P":("Pivot","p-level"),"S1":("Support 1","s-level"),"S2":("Support 2","s-level")}
        rows = ""
        for k in ["R2","R1","P","S1","S2"]:
            v = pivots.get(k,0); nm, cls = meta[k]
            diff = ((v-ltp)/ltp*100) if ltp else 0
            ds   = f"+{diff:.2f}%" if diff>0 else f"{diff:.2f}%"
            rows += f"<tr><td>{nm}</td><td class='{cls}'><b>{k}</b></td><td class='{cls}'>₹{v:,.2f}</td><td style='color:#3D4560'>{ds}</td></tr>"
        st.markdown(f"""<table class="pivot-table">
          <thead><tr><th>Level</th><th>Label</th><th>Price</th><th>vs LTP</th></tr></thead>
          <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#3D4560;font-size:.78rem">Pivot data unavailable.</p>',
                    unsafe_allow_html=True)

    # MTF GRID
    st.markdown('<div class="section-hdr">Multi-Timeframe Alignment</div>', unsafe_allow_html=True)
    tfs = MTF_MAP.get(interval, ["5m","15m","60m"])
    cells = ""
    for tf in tfs:
        ms = mtf_sigs.get(tf, "—")
        cls = "mtf-buy" if ms=="BUY" else ("mtf-sell" if ms=="SELL" else "mtf-none")
        ico = "↑" if ms=="BUY" else ("↓" if ms=="SELL" else "–")
        cells += f'<div class="mtf-cell"><div class="mtf-tf">{tf}</div><div class="mtf-sig {cls}">{ico} {ms}</div></div>'
    st.markdown(f'<div class="mtf-grid">{cells}</div>', unsafe_allow_html=True)

# ── OPTIONS POSITION CALCULATOR ───────────────────────────────────────────────
with col_b:
    st.markdown('<div class="section-hdr">Options Position Calculator</div>', unsafe_allow_html=True)
    if opts:
        dir_word = "CE (Call)" if sig["signal"]=="BUY" else "PE (Put)"
        rows_html = f"""
        <div class="options-row"><span class="options-key">Direction</span>
          <span class="options-val {'green' if sig['signal']=='BUY' else 'red'}">{sig['signal']} · {dir_word}</span></div>
        <div class="options-row"><span class="options-key">SL Points</span>
          <span class="options-val">{opts['sl_pts']:,.2f} pts</span></div>
        <div class="options-row"><span class="options-key">Target Points</span>
          <span class="options-val green">{opts['tgt_pts']:,.2f} pts</span></div>
        <div class="options-row"><span class="options-key">R:R Ratio</span>
          <span class="options-val">1 : {opts['rr']}</span></div>
        <div class="options-row"><span class="options-key">Lots Suggested</span>
          <span class="options-val">{opts['lots']} lot{'s' if opts['lots']>1 else ''} ({opts['lots']*lot_size} units)</span></div>
        <div class="options-row"><span class="options-key">Capital at Risk</span>
          <span class="options-val red">₹{opts['cap_risk']:,.0f} ({risk_pct}%)</span></div>
        <div class="options-row"><span class="options-key">Potential Gain</span>
          <span class="options-val green">₹{opts['pot_gain']:,.0f}</span></div>
        """
        st.markdown(f'<div class="options-card">{rows_html}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<p style="font-size:.6rem;color:#3D4560;margin-top:.5rem;line-height:1.5">'
            f'⚠️ Based on ₹{capital:,.0f} capital · {risk_pct}% risk rule · {lot_size} units/lot.<br>'
            f'Paper-trade signals for 30 days before live deployment.</p>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="options-card"><p style="color:#3D4560;font-size:.78rem;text-align:center;padding:.5rem 0">'
            'No active signal.<br>Position sizing will appear here when a<br>Score ≥ 70 signal fires.</p></div>',
            unsafe_allow_html=True)

# ── TRADE LOG ────────────────────────────────────────────────────────────────
with col_c:
    st.markdown('<div class="section-hdr">Live Trade Log · Last 5 Signals</div>', unsafe_allow_html=True)
    log = st.session_state.get("trade_log", [])
    if not log:
        st.markdown('<p style="color:#3D4560;font-size:.78rem;padding:.4rem 0">'
                    'No signals yet. Waiting for Score ≥ 70 confluence…</p>', unsafe_allow_html=True)
    else:
        for entry in log[:5]:
            sc   = "buy" if entry["signal"]=="BUY" else "sell"
            sl_s = f"SL ₹{entry['sl']:,.2f}" if entry["sl"] else ""
            ts   = f"T ₹{entry['target']:,.2f}" if entry["target"] else ""
            scr  = f"· Score {entry.get('score',0)}" if entry.get('score') else ""
            st.markdown(f"""<div class="tlog-entry">
              <div>
                <div class="tlog-time">{entry['time']} · {entry['index']} {scr}</div>
                <div class="tlog-price">₹{entry['entry']:,.2f}
                  <span style="color:#3D4560;font-size:.65rem"> {sl_s} {ts}</span></div>
              </div>
              <span class="tlog-badge {sc}">{entry['signal']}</span>
            </div>""", unsafe_allow_html=True)

    # Win rate
    st.markdown('<div class="section-hdr" style="margin-top:1rem">Session Signal Stats</div>',
                unsafe_allow_html=True)
    total_log = len(log)
    buy_ct    = sum(1 for e in log if e["signal"]=="BUY")
    sell_ct   = sum(1 for e in log if e["signal"]=="SELL")
    avg_score = np.mean([e.get("score",0) for e in log]) if log else 0
    st.markdown(f"""<div class="options-card">
      <div class="options-row"><span class="options-key">Total Signals</span>
        <span class="options-val">{total_log}</span></div>
      <div class="options-row"><span class="options-key">Buy Signals</span>
        <span class="options-val green">{buy_ct}</span></div>
      <div class="options-row"><span class="options-key">Sell Signals</span>
        <span class="options-val red">{sell_ct}</span></div>
      <div class="options-row"><span class="options-key">Avg Score</span>
        <span class="options-val">{avg_score:.1f}/100</span></div>
    </div>""", unsafe_allow_html=True)

# ─── RISK DISCLAIMER FOOTER ──────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="font-size:.58rem;color:#2A3040;text-align:center;line-height:1.7">'
    '⚠️ RISK DISCLAIMER: QuantX is an analytical tool only. F&amp;O trading involves substantial risk of loss. '
    'Options can expire worthless. Never risk more than 1–2% of capital per trade. '
    'Past signal performance does not guarantee future results. '
    'Paper-trade for a minimum of 30 days before committing real capital. '
    'This tool does not constitute financial advice. Trade responsibly.</p>',
    unsafe_allow_html=True)
