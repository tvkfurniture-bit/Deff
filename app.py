# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║        QuantX · F&O Intelligence Terminal  v3.0                            ║
# ║        Full-stack: Signal Scoring · Regime · MTF · Options Calc            ║
# ║        Backtesting · Auto Kill-Switch · Telegram Alerts · VWAP · BB        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import warnings, json, urllib.request, urllib.parse
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

# ─── THEME CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

  html,body,[class*="css"]{font-family:'Inter',sans-serif;background:#0E1117;color:#E0E0E0;}
  .stApp{background:#0E1117;}
  #MainMenu,footer,header{visibility:hidden;}
  .block-container{padding:1.1rem 1.8rem 2rem;max-width:100%;}
  [data-testid="stSidebar"]{background:#0B0D13;border-right:1px solid #1A1E2A;}

  /* ── Wordmark ── */
  .qx-wordmark{font-family:'JetBrains Mono',monospace;font-size:1.5rem;font-weight:700;
    letter-spacing:-.04em;color:#fff;line-height:1;margin-bottom:.1rem;}
  .qx-wordmark span{color:#00FFA3;}
  .qx-tagline{font-size:.62rem;color:#3D4560;letter-spacing:.14em;text-transform:uppercase;
    font-weight:600;margin-bottom:1.3rem;}

  /* ── Regime banners ── */
  .regime-trending{background:rgba(0,255,163,.07);border:1px solid rgba(0,255,163,.25);
    border-radius:8px;padding:.5rem 1rem;font-size:.72rem;font-weight:700;
    letter-spacing:.08em;color:#00FFA3;text-align:center;margin-bottom:.9rem;}
  .regime-choppy{background:rgba(255,180,0,.07);border:1px solid rgba(255,180,0,.25);
    border-radius:8px;padding:.5rem 1rem;font-size:.72rem;font-weight:700;
    letter-spacing:.08em;color:#FFB400;text-align:center;margin-bottom:.9rem;}
  .regime-volatile{background:rgba(255,75,75,.07);border:1px solid rgba(255,75,75,.25);
    border-radius:8px;padding:.5rem 1rem;font-size:.72rem;font-weight:700;
    letter-spacing:.08em;color:#FF4B4B;text-align:center;margin-bottom:.9rem;}

  /* ── Metric cards ── */
  .metric-card{background:#13161E;border:1px solid #1E2330;border-radius:10px;
    padding:.85rem 1rem;position:relative;overflow:hidden;height:100%;}
  .metric-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,#00FFA3 0%,transparent 100%);opacity:.6;}
  .metric-card.sell-card::before{background:linear-gradient(90deg,#FF4B4B 0%,transparent 100%);}
  .metric-card.neutral-card::before{background:linear-gradient(90deg,#5B6BFF 0%,transparent 100%);}
  .metric-card.amber-card::before{background:linear-gradient(90deg,#FFB400 0%,transparent 100%);}
  .metric-label{font-size:.6rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
    color:#3D4560;margin-bottom:.3rem;}
  .metric-value{font-family:'JetBrains Mono',monospace;font-size:1.3rem;font-weight:700;
    color:#fff;line-height:1.1;}
  .metric-sub{font-size:.67rem;color:#555E78;margin-top:.25rem;}
  .signal-buy{color:#00FFA3!important;} .signal-sell{color:#FF4B4B!important;}
  .signal-none{color:#5B6BFF!important;}

  /* ── Score bar ── */
  .score-wrap{display:flex;align-items:center;gap:.55rem;margin-top:.3rem;}
  .score-bar-bg{flex:1;height:5px;background:#1A1E2A;border-radius:3px;overflow:hidden;}
  .score-bar-fill{height:100%;border-radius:3px;}
  .score-num{font-family:'JetBrains Mono',monospace;font-size:.88rem;font-weight:700;min-width:2.2rem;text-align:right;}

  /* ── Section headers ── */
  .section-hdr{font-size:.6rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
    color:#3D4560;border-bottom:1px solid #1A1E2A;padding-bottom:.3rem;margin:.85rem 0 .65rem;}

  /* ── MTF Grid ── */
  .mtf-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:.4rem;margin-top:.35rem;}
  .mtf-cell{background:#0E1117;border:1px solid #1A1E2A;border-radius:6px;padding:.4rem .5rem;text-align:center;}
  .mtf-tf{font-size:.56rem;color:#3D4560;font-weight:700;letter-spacing:.1em;text-transform:uppercase;margin-bottom:.2rem;}
  .mtf-sig{font-size:.7rem;font-weight:700;font-family:'JetBrains Mono',monospace;}
  .mtf-buy{color:#00FFA3;} .mtf-sell{color:#FF4B4B;} .mtf-none{color:#3D4560;}

  /* ── Pivot table ── */
  .pivot-table{width:100%;border-collapse:collapse;font-family:'JetBrains Mono',monospace;font-size:.78rem;}
  .pivot-table td,.pivot-table th{padding:.45rem .7rem;border-bottom:1px solid #1A1E2A;text-align:right;}
  .pivot-table th{color:#3D4560;font-size:.58rem;letter-spacing:.08em;text-transform:uppercase;text-align:left;}
  .pivot-table td:first-child{text-align:left;color:#555E78;}
  .r-level{color:#FF4B4B;font-weight:600;} .s-level{color:#00FFA3;font-weight:600;} .p-level{color:#5B6BFF;font-weight:600;}

  /* ── Options / stat card ── */
  .opt-card{background:#0B0D13;border:1px solid #1A1E2A;border-radius:8px;padding:.75rem .95rem;margin-top:.4rem;}
  .opt-row{display:flex;justify-content:space-between;align-items:center;padding:.28rem 0;border-bottom:1px solid #1A1E2A;}
  .opt-row:last-child{border-bottom:none;}
  .opt-key{font-size:.63rem;color:#555E78;font-weight:600;letter-spacing:.06em;text-transform:uppercase;}
  .opt-val{font-family:'JetBrains Mono',monospace;font-size:.82rem;color:#E0E0E0;font-weight:600;}
  .opt-val.green{color:#00FFA3;} .opt-val.red{color:#FF4B4B;} .opt-val.amber{color:#FFB400;}

  /* ── Trade log ── */
  .tlog-entry{background:#13161E;border:1px solid #1E2330;border-radius:8px;
    padding:.6rem .85rem;margin-bottom:.38rem;display:flex;justify-content:space-between;align-items:center;}
  .tlog-time{font-family:'JetBrains Mono',monospace;font-size:.6rem;color:#3D4560;}
  .tlog-badge{font-size:.63rem;font-weight:700;letter-spacing:.07em;padding:.16rem .5rem;border-radius:4px;}
  .tlog-badge.buy{background:rgba(0,255,163,.12);color:#00FFA3;}
  .tlog-badge.sell{background:rgba(255,75,75,.12);color:#FF4B4B;}
  .tlog-badge.win{background:rgba(0,255,163,.2);color:#00FFA3;border:1px solid #00FFA344;}
  .tlog-badge.loss{background:rgba(255,75,75,.2);color:#FF4B4B;border:1px solid #FF4B4B44;}
  .tlog-price{font-family:'JetBrains Mono',monospace;font-size:.75rem;color:#E0E0E0;}

  /* ── Backtest summary ── */
  .bt-card{background:#13161E;border:1px solid #1E2330;border-radius:10px;padding:.85rem 1rem;margin-top:.5rem;}
  .bt-row{display:flex;justify-content:space-between;padding:.22rem 0;border-bottom:1px solid #1A1E2A;}
  .bt-row:last-child{border-bottom:none;}
  .bt-key{font-size:.6rem;color:#555E78;font-weight:600;text-transform:uppercase;letter-spacing:.06em;}
  .bt-val{font-family:'JetBrains Mono',monospace;font-size:.78rem;font-weight:700;}

  /* ── Kill switch ── */
  .ks-off{background:rgba(255,75,75,.08);border:1px solid #FF4B4B44;border-radius:8px;
    padding:.5rem 1rem;font-size:.7rem;color:#FF4B4B;text-align:center;font-weight:700;
    letter-spacing:.06em;margin-top:.35rem;}
  .ks-on{background:rgba(0,255,163,.08);border:1px solid #00FFA344;border-radius:8px;
    padding:.5rem 1rem;font-size:.7rem;color:#00FFA3;text-align:center;font-weight:700;
    letter-spacing:.06em;margin-top:.35rem;}

  /* ── Alert banner ── */
  .alert-buy{background:rgba(0,255,163,.1);border:1px solid #00FFA3;border-radius:8px;
    padding:.6rem 1rem;font-size:.78rem;font-weight:700;color:#00FFA3;margin-bottom:.8rem;}
  .alert-sell{background:rgba(255,75,75,.1);border:1px solid #FF4B4B;border-radius:8px;
    padding:.6rem 1rem;font-size:.78rem;font-weight:700;color:#FF4B4B;margin-bottom:.8rem;}

  /* ── Auto-KS warning ── */
  .auto-ks-warn{background:rgba(255,75,75,.12);border:1px solid #FF4B4B66;border-radius:8px;
    padding:.55rem 1rem;font-size:.7rem;color:#FF4B4B;text-align:center;font-weight:700;
    margin-top:.4rem;letter-spacing:.04em;}

  .status-dot{display:inline-block;width:6px;height:6px;border-radius:50%;
    animation:pulse 2s infinite;margin-right:5px;vertical-align:middle;}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}

  [data-testid="stSelectbox"]>div>div,[data-testid="stRadio"] label{color:#E0E0E0!important;}
  .stSelectbox [data-baseweb="select"]>div{background:#1A1E2A!important;border-color:#1A1E2A!important;}
  hr{border-color:#1A1E2A!important;}
  .stNumberInput input,.stTextInput input{background:#1A1E2A!important;border-color:#1A1E2A!important;color:#E0E0E0!important;}
  div[data-testid="stSlider"]>div{color:#E0E0E0;}
  .stTabs [data-baseweb="tab-list"]{background:#0B0D13;border-bottom:1px solid #1A1E2A;}
  .stTabs [data-baseweb="tab"]{color:#555E78;font-size:.72rem;font-weight:600;letter-spacing:.06em;}
  .stTabs [aria-selected="true"]{color:#00FFA3!important;border-bottom:2px solid #00FFA3!important;}
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ───────────────────────────────────────────────────────────────────
INDICES = {
    "NIFTY 50":   {"ticker":"^NSEI",        "lot":75,  "label":"NIFTY",      "strike_gap":50},
    "BANK NIFTY": {"ticker":"^NSEBANK",     "lot":30,  "label":"BANKNIFTY",  "strike_gap":100},
    "FIN NIFTY":  {"ticker":"^CNXFIN",      "lot":65,  "label":"FINNIFTY",   "strike_gap":50},
    "SENSEX":     {"ticker":"^BSESN",       "lot":20,  "label":"SENSEX",     "strike_gap":100},
    "BSE BANKEX": {"ticker":"BSE-BANKEX.BO","lot":20,  "label":"BANKEX",     "strike_gap":100},
}
TIMEFRAMES = {"1m":"1m","5m":"5m","15m":"15m","1h":"60m"}
TF_PERIODS = {"1m":"1d","5m":"3d","15m":"5d","1h":"30d"}
MTF_MAP    = {
    "1m":  ["1m","5m","15m"],
    "5m":  ["5m","15m","60m"],
    "15m": ["15m","60m","1d"],
    "1h":  ["60m","1d","1wk"],
}

# ─── PURE-PANDAS INDICATOR ENGINE ────────────────────────────────────────────────
def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()

def _rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d  = s.diff()
    ag = d.clip(lower=0).ewm(com=n-1, adjust=False).mean()
    al = (-d).clip(lower=0).ewm(com=n-1, adjust=False).mean()
    return 100 - (100 / (1 + ag / al.replace(0, np.nan)))

def _atr(h: pd.Series, l: pd.Series, c: pd.Series, n: int = 14) -> pd.Series:
    pc = c.shift(1)
    tr = pd.concat([h-l,(h-pc).abs(),(l-pc).abs()], axis=1).max(axis=1)
    return tr.ewm(com=n-1, adjust=False).mean()

def _adx(h: pd.Series, l: pd.Series, c: pd.Series, n: int = 14) -> pd.Series:
    up, dn  = h.diff(), -l.diff()
    pdm = up.where((up>dn)&(up>0), 0.0)
    ndm = dn.where((dn>up)&(dn>0), 0.0)
    atr = _atr(h, l, c, n)
    pdi = 100*pdm.ewm(com=n-1,adjust=False).mean()/atr.replace(0,np.nan)
    ndi = 100*ndm.ewm(com=n-1,adjust=False).mean()/atr.replace(0,np.nan)
    dx  = 100*(pdi-ndi).abs()/(pdi+ndi).replace(0,np.nan)
    return dx.ewm(com=n-1, adjust=False).mean()

def _vwap(h: pd.Series, l: pd.Series, c: pd.Series, v: pd.Series) -> pd.Series:
    tp  = (h + l + c) / 3
    return (tp * v).cumsum() / v.cumsum().replace(0, np.nan)

def _bollinger(c: pd.Series, n: int = 20, k: float = 2.0):
    mid = c.rolling(n).mean()
    std = c.rolling(n).std()
    return mid, mid + k*std, mid - k*std

# ─── DATA FETCHING ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def fetch_data(ticker: str, interval: str) -> pd.DataFrame:
    period = TF_PERIODS.get(interval, "5d")
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False)
        if df is None or df.empty: return pd.DataFrame()
        df.columns = [c[0] if isinstance(c,tuple) else c for c in df.columns]
        df.dropna(inplace=True)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60, show_spinner=False)
def fetch_prev_day_ohlc(ticker: str) -> dict:
    try:
        df = yf.download(ticker, period="5d", interval="1d",
                         auto_adjust=True, progress=False)
        if df is None or df.empty or len(df)<2: return {}
        df.columns = [c[0] if isinstance(c,tuple) else c for c in df.columns]
        row = df.iloc[-2]
        return {"high":float(row["High"]),"low":float(row["Low"]),"close":float(row["Close"])}
    except Exception:
        return {}

# ─── INDICATORS ──────────────────────────────────────────────────────────────────
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 30: return df
    df = df.copy()
    df["EMA9"]  = _ema(df["Close"], 9)
    df["EMA21"] = _ema(df["Close"], 21)
    df["EMA50"] = _ema(df["Close"], 50)
    df["RSI"]   = _rsi(df["Close"], 14)
    df["ATR"]   = _atr(df["High"], df["Low"], df["Close"], 14)
    df["ATR20"] = _atr(df["High"], df["Low"], df["Close"], 20)
    df["ADX"]   = _adx(df["High"], df["Low"], df["Close"], 14)
    if "Volume" in df.columns and df["Volume"].sum() > 0:
        df["VWAP"]     = _vwap(df["High"], df["Low"], df["Close"], df["Volume"])
        df["VolAvg20"] = df["Volume"].rolling(20).mean()
    bb_mid, bb_up, bb_lo = _bollinger(df["Close"], 20, 2.0)
    df["BB_MID"] = bb_mid; df["BB_UP"] = bb_up; df["BB_LO"] = bb_lo
    return df

# ─── PIVOT CALCULATION ───────────────────────────────────────────────────────────
def calculate_pivots(ohlc: dict) -> dict:
    if not ohlc: return {}
    H,L,C = ohlc["high"], ohlc["low"], ohlc["close"]
    rng = H - L
    P   = (H + L + C) / 3
    return {"R2":P+0.618*rng,"R1":P+0.382*rng,"P":P,"S1":P-0.382*rng,"S2":P-0.618*rng}

# ─── SIGNAL SCORING ENGINE ───────────────────────────────────────────────────────
def score_signal(row: pd.Series, prev: pd.Series, direction: str) -> int:
    score = 0
    close = float(row.get("Close",0));  ema9  = float(row.get("EMA9",0))
    ema21 = float(row.get("EMA21",0));  ema50 = float(row.get("EMA50",0))
    rsi   = float(row.get("RSI",50));   adx   = float(row.get("ADX",0))
    vol   = float(row.get("Volume",0)); vavg  = float(row.get("VolAvg20",0))
    vwap  = float(row.get("VWAP",0)) if not np.isnan(row.get("VWAP",np.nan) or np.nan) else 0
    bb_up = float(row.get("BB_UP",0));  bb_lo = float(row.get("BB_LO",0))

    if direction == "BUY":
        if ema9 > ema21:             score += 15
        if ema21 > ema50:            score += 10
        if rsi > 60:                 score += 10
        if 60 <= rsi <= 75:          score += 10
        elif rsi > 75:               score -= 5
        if close > float(prev.get("High",0)): score += 10
        if vwap and close > vwap:    score += 5   # above VWAP: trend confirmation
        if bb_up and close < bb_up:  score += 3   # not at band extreme
    else:
        if ema9 < ema21:             score += 15
        if ema21 < ema50:            score += 10
        if rsi < 40:                 score += 10
        if 25 <= rsi < 40:           score += 10
        elif rsi < 25:               score -= 5
        if close < float(prev.get("Low",0)):  score += 10
        if vwap and close < vwap:    score += 5
        if bb_lo and close > bb_lo:  score += 3

    if adx > 25:   score += 20
    elif adx > 20: score += 10

    if vavg > 0:
        ratio = vol / vavg
        if ratio >= 1.5:   score += 25
        elif ratio >= 1.2: score += 15
        elif ratio >= 1.0: score += 5

    return max(0, min(100, score))

# ─── MARKET REGIME ───────────────────────────────────────────────────────────────
def get_regime(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 20:
        return {"label":"UNKNOWN","class":"regime-choppy","suppress":True,"adx":0}
    row    = df.iloc[-1]
    adx    = float(row.get("ADX",0))
    atr    = float(row.get("ATR",0))
    atr20  = float(row.get("ATR20",atr))
    vr     = atr/atr20 if atr20>0 else 1.0
    if vr > 2.0:
        return {"label":"⚡ HIGH VOLATILITY — Reduce Size by 50%","class":"regime-volatile","suppress":False,"adx":adx}
    elif adx >= 25:
        return {"label":f"📈 TRENDING — Signals Active  (ADX {adx:.1f})","class":"regime-trending","suppress":False,"adx":adx}
    else:
        return {"label":f"〰️ CHOPPY — Signals Suppressed  (ADX {adx:.1f} < 25)","class":"regime-choppy","suppress":True,"adx":adx}

# ─── MAIN SIGNAL GENERATION ──────────────────────────────────────────────────────
def generate_signal(df: pd.DataFrame, kill_switch: bool, regime: dict) -> dict:
    default = {"signal":"NONE","entry":None,"sl":None,"target":None,
               "rsi":None,"atr":None,"adx":None,"score":0,
               "ema9":None,"ema21":None,"ema50":None,"suppressed":False}
    if kill_switch or df.empty or len(df) < 30: return default
    if regime.get("suppress",False):
        d = default.copy(); d["suppressed"] = True; return d

    row  = df.iloc[-1]
    prev = df.iloc[-2] if len(df)>1 else row
    try:
        close = float(row["Close"]); ema9  = float(row["EMA9"])
        ema21 = float(row["EMA21"]); rsi   = float(row["RSI"])
        atr   = float(row["ATR"]);   adx   = float(row.get("ADX",0))
        ema50 = float(row.get("EMA50",ema21))
        prev_h= float(prev["High"]); prev_l= float(prev["Low"])
    except Exception:
        return default
    if any(np.isnan(v) for v in [ema9,ema21,rsi,atr]): return default

    signal = "NONE"; sl = target = None; score = 0

    if close>ema9 and ema9>ema21 and rsi>60 and close>prev_h:
        score = score_signal(row, prev, "BUY")
        if score >= 70:
            signal="BUY"; sl=close-1.5*atr; target=close+2*(close-sl)

    elif close<ema9 and ema9<ema21 and rsi<40 and close<prev_l:
        score = score_signal(row, prev, "SELL")
        if score >= 70:
            signal="SELL"; sl=close+1.5*atr; target=close-2*(sl-close)

    return {"signal":signal,"entry":close,"sl":sl,"target":target,
            "rsi":rsi,"atr":atr,"adx":adx,"score":score,
            "ema9":ema9,"ema21":ema21,"ema50":ema50,"suppressed":False}

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
            if df is None or df.empty or len(df)<22:
                results[tf]="—"; continue
            df.columns = [c[0] if isinstance(c,tuple) else c for c in df.columns]
            df.dropna(inplace=True)
            df = calculate_indicators(df)
            if len(df)<2: results[tf]="—"; continue
            r = df.iloc[-1]
            e9=float(r.get("EMA9",0)); e21=float(r.get("EMA21",0))
            rs=float(r.get("RSI",50)); cl=float(r["Close"])
            if cl>e9 and e9>e21 and rs>55:   results[tf]="BUY"
            elif cl<e9 and e9<e21 and rs<45:  results[tf]="SELL"
            else:                              results[tf]="FLAT"
        except Exception:
            results[tf]="—"
    return results

# ─── OPTIONS POSITION CALCULATOR ─────────────────────────────────────────────────
def calc_options_metrics(sig: dict, capital: float, risk_pct: float,
                         lot_size: int, strike_gap: int) -> dict:
    if sig["signal"]=="NONE" or sig["sl"] is None: return {}
    entry=sig["entry"]; sl=sig["sl"]; target=sig["target"]
    sl_pts  = abs(entry-sl);  tgt_pts = abs(target-entry)
    max_loss  = capital*(risk_pct/100)
    lots      = max(1,int(max_loss/(sl_pts*lot_size)))
    cap_risk  = lots*sl_pts*lot_size
    pot_gain  = lots*tgt_pts*lot_size
    # Suggested ATM strike
    atm = round(entry/strike_gap)*strike_gap
    if sig["signal"]=="BUY":
        ce_strike = atm; pe_strike = None
    else:
        ce_strike = None; pe_strike = atm
    return {"sl_pts":sl_pts,"tgt_pts":tgt_pts,"lots":lots,
            "cap_risk":cap_risk,"pot_gain":pot_gain,
            "rr":round(tgt_pts/sl_pts,2) if sl_pts else 0,
            "atm":atm,"ce_strike":ce_strike,"pe_strike":pe_strike}

# ─── BACKTESTING ON HISTORICAL BARS ──────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def run_backtest(ticker: str, interval: str) -> dict:
    """
    Walk-forward simulation on the last N candles.
    Returns win/loss stats and a list of trades for display.
    """
    period = TF_PERIODS.get(interval,"5d")
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False)
        if df is None or df.empty or len(df)<60:
            return {"trades":[],"wins":0,"losses":0,"total":0,"pnl":0,"wr":0}
        df.columns = [c[0] if isinstance(c,tuple) else c for c in df.columns]
        df.dropna(inplace=True)
        df = calculate_indicators(df)
    except Exception:
        return {"trades":[],"wins":0,"losses":0,"total":0,"pnl":0,"wr":0}

    trades = []; wins=0; losses=0; total_pnl=0.0
    in_trade = False; trade_dir=None; entry_p=sl_p=target_p=None

    for i in range(50, len(df)-1):
        row  = df.iloc[i]
        prev = df.iloc[i-1]
        nxt  = df.iloc[i+1]  # next candle for exit simulation

        if in_trade:
            # Exit logic: check next candle's high/low
            exit_p = None; outcome = None
            if trade_dir=="BUY":
                if float(nxt.get("Low",9e9)) <= sl_p:
                    exit_p=sl_p; outcome="LOSS"
                elif float(nxt.get("High",0)) >= target_p:
                    exit_p=target_p; outcome="WIN"
                elif i == len(df)-2:
                    exit_p=float(nxt["Close"]); outcome="WIN" if exit_p>entry_p else "LOSS"
            else:
                if float(nxt.get("High",0)) >= sl_p:
                    exit_p=sl_p; outcome="LOSS"
                elif float(nxt.get("Low",9e9)) <= target_p:
                    exit_p=target_p; outcome="WIN"
                elif i == len(df)-2:
                    exit_p=float(nxt["Close"]); outcome="WIN" if exit_p<entry_p else "LOSS"
            if outcome:
                pnl = (exit_p-entry_p) if trade_dir=="BUY" else (entry_p-exit_p)
                total_pnl += pnl
                if outcome=="WIN": wins+=1
                else: losses+=1
                trades.append({"dir":trade_dir,"entry":entry_p,"exit":exit_p,
                                "pnl":pnl,"outcome":outcome,
                                "time":df.index[i].strftime("%d-%b %H:%M")})
                in_trade=False

        if not in_trade:
            try:
                close=float(row["Close"]); ema9=float(row["EMA9"])
                ema21=float(row["EMA21"]); rsi=float(row["RSI"])
                atr=float(row["ATR"]);     adx=float(row.get("ADX",0))
                prev_h=float(prev["High"]); prev_l=float(prev["Low"])
            except Exception:
                continue
            if any(np.isnan(v) for v in [ema9,ema21,rsi,atr]): continue
            if adx < 20: continue   # regime filter

            if close>ema9 and ema9>ema21 and rsi>60 and close>prev_h:
                sc = score_signal(row, prev, "BUY")
                if sc>=70:
                    in_trade=True; trade_dir="BUY"; entry_p=close
                    sl_p=close-1.5*atr; target_p=close+2*(close-sl_p)

            elif close<ema9 and ema9<ema21 and rsi<40 and close<prev_l:
                sc = score_signal(row, prev, "SELL")
                if sc>=70:
                    in_trade=True; trade_dir="SELL"; entry_p=close
                    sl_p=close+1.5*atr; target_p=close-2*(sl_p-close)

    total = wins+losses
    wr    = round(wins/total*100,1) if total else 0
    return {"trades":trades[-20:],"wins":wins,"losses":losses,
            "total":total,"pnl":round(total_pnl,2),"wr":wr}

# ─── TRADE LOG & AUTO KILL-SWITCH ────────────────────────────────────────────────
def update_trade_log(sig: dict, index_name: str):
    if "trade_log" not in st.session_state:
        st.session_state.trade_log = []
    if sig["signal"]!="NONE" and sig["entry"] is not None:
        log = st.session_state.trade_log
        if not log or log[0]["signal"]!=sig["signal"] or log[0]["index"]!=index_name:
            st.session_state.trade_log = [{
                "time":  datetime.now().strftime("%H:%M:%S"),
                "index": index_name, "signal": sig["signal"],
                "entry": sig["entry"], "sl": sig["sl"],
                "target":sig["target"], "score": sig.get("score",0),
                "outcome": "OPEN",
            }] + log[:29]

def check_auto_kill_switch(bt: dict, threshold: float = 40.0) -> bool:
    """Auto-engage kill switch if backtest win-rate < threshold."""
    return bt["total"] >= 5 and bt["wr"] < threshold

# ─── TELEGRAM ALERT ──────────────────────────────────────────────────────────────
def send_telegram_alert(token: str, chat_id: str, message: str) -> bool:
    if not token or not chat_id: return False
    try:
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({"chat_id":chat_id,"text":message,"parse_mode":"HTML"}).encode()
        req  = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception:
        return False

def build_alert_message(sig: dict, index_name: str, tf: str, opts: dict) -> str:
    s    = sig["signal"]
    icon = "🟢" if s=="BUY" else "🔴"
    msg  = (f"{icon} <b>QuantX Signal — {s}</b>\n"
            f"Index : {index_name}  [{tf}]\n"
            f"Entry : ₹{sig['entry']:,.2f}\n"
            f"SL    : ₹{sig['sl']:,.2f}\n"
            f"Target: ₹{sig['target']:,.2f}\n"
            f"Score : {sig['score']}/100\n")
    if opts:
        msg += (f"Lots  : {opts['lots']}  ({opts['lots']*opts.get('lot_size',1)} units)\n"
                f"Risk  : ₹{opts['cap_risk']:,.0f}\n")
        strike = opts.get("ce_strike") or opts.get("pe_strike")
        kind   = "CE" if s=="BUY" else "PE"
        if strike: msg += f"Strike: {strike} {kind}\n"
    msg += f"\n⚠️ For informational use only. Trade responsibly."
    return msg

# ─── CHART BUILDER ───────────────────────────────────────────────────────────────
def build_chart(df: pd.DataFrame, pivots: dict, sig: dict,
                show_bb: bool, show_vwap: bool, show_signals: bool,
                backtest_trades: list) -> go.Figure:
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.62, 0.19, 0.19], vertical_spacing=0.025)

    # ── Candlesticks ──
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing=dict(line=dict(color="#00FFA3",width=1),fillcolor="rgba(0,255,163,.5)"),
        decreasing=dict(line=dict(color="#FF4B4B",width=1),fillcolor="rgba(255,75,75,.5)"),
        name="Price", showlegend=False,
    ), row=1, col=1)

    # ── EMAs ──
    for col,name,color,w in [("EMA9","EMA 9","#FFD700",1.1),
                               ("EMA21","EMA 21","#AA80FF",1.1),
                               ("EMA50","EMA 50","#4466DD",1.0)]:
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df.index,y=df[col],
                line=dict(color=color,width=w),name=name,hoverinfo="skip"), row=1,col=1)

    # ── VWAP ──
    if show_vwap and "VWAP" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["VWAP"],
            line=dict(color="#00CFFF",width=1.1,dash="dash"),
            name="VWAP",hoverinfo="skip"), row=1,col=1)

    # ── Bollinger Bands ──
    if show_bb and "BB_UP" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["BB_UP"],
            line=dict(color="rgba(255,200,0,.35)",width=.8),
            name="BB Upper",hoverinfo="skip",showlegend=True), row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["BB_LO"],
            line=dict(color="rgba(255,200,0,.35)",width=.8),
            fill="tonexty",fillcolor="rgba(255,200,0,.04)",
            name="BB Lower",hoverinfo="skip"), row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["BB_MID"],
            line=dict(color="rgba(255,200,0,.25)",width=.7,dash="dot"),
            name="BB Mid",hoverinfo="skip"), row=1,col=1)

    # ── Pivot lines ──
    pivot_styles={"R2":("#FF4B4B","dash"),"R1":("#FF8080","dot"),
                  "P":("#5B6BFF","dash"),"S1":("#80FFC8","dot"),"S2":("#00FFA3","dash")}
    for lvl,val in pivots.items():
        color,dash=pivot_styles.get(lvl,("#888","dash"))
        fig.add_hline(y=val,line=dict(color=color,width=.8,dash=dash),
                      annotation_text=f" {lvl} {val:,.0f}",
                      annotation_font=dict(color=color,size=10),
                      annotation_position="right",row=1,col=1)

    # ── Backtest signal markers on chart ──
    if show_signals and backtest_trades:
        bt_df = pd.DataFrame(backtest_trades)
        for _, t in bt_df.iterrows():
            color  = "#00FFA3" if t["dir"]=="BUY" else "#FF4B4B"
            symbol = "triangle-up" if t["dir"]=="BUY" else "triangle-down"
            fig.add_trace(go.Scatter(
                x=[t["time"]], y=[t["entry"]],
                mode="markers",
                marker=dict(symbol=symbol,color=color,size=9,
                            line=dict(color="#0E1117",width=1)),
                name=f"{t['dir']} {t['outcome']}",
                showlegend=False, hoverinfo="text",
                hovertext=f"{t['dir']} @ {t['entry']:.0f} → {t['exit']:.0f} ({t['outcome']})"
            ), row=1,col=1)

    # ── Current signal arrow ──
    if sig["signal"] in ("BUY","SELL") and sig["entry"]:
        color  = "#00FFA3" if sig["signal"]=="BUY" else "#FF4B4B"
        symbol = "triangle-up" if sig["signal"]=="BUY" else "triangle-down"
        fig.add_trace(go.Scatter(
            x=[df.index[-1]], y=[sig["entry"]],
            mode="markers+text",
            marker=dict(symbol=symbol,color=color,size=14,
                        line=dict(color="#fff",width=1.5)),
            text=[f" {sig['signal']}"], textposition="top right",
            textfont=dict(color=color,size=11,family="JetBrains Mono"),
            name="Signal",showlegend=False,
        ), row=1,col=1)

    # ── RSI ──
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["RSI"],
            line=dict(color="#00FFA3",width=1.1),name="RSI",
            fill="tozeroy",fillcolor="rgba(0,255,163,.04)"), row=2,col=1)
        for level,color in [(60,"rgba(0,255,163,.5)"),(40,"rgba(255,75,75,.5)"),(50,"rgba(128,128,128,.25)")]:
            fig.add_hline(y=level,line=dict(color=color,width=.6,dash="dot"),row=2,col=1)
        fig.update_yaxes(title_text="RSI",row=2,col=1,range=[0,100],
                         tickformat=".0f",gridcolor="#1A1E2A",showgrid=True)

    # ── ADX ──
    if "ADX" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["ADX"],
            line=dict(color="#FFB400",width=1.1),name="ADX",
            fill="tozeroy",fillcolor="rgba(255,180,0,.04)"), row=3,col=1)
        fig.add_hline(y=25,line=dict(color="#FFB400",width=.7,dash="dot"),row=3,col=1)
        fig.update_yaxes(title_text="ADX",row=3,col=1,range=[0,60],
                         tickformat=".0f",gridcolor="#1A1E2A",showgrid=True)

    fig.update_layout(
        paper_bgcolor="#0E1117", plot_bgcolor="#0E1117",
        font=dict(family="JetBrains Mono, monospace",color="#555E78",size=10),
        margin=dict(l=10,r=85,t=25,b=10),
        legend=dict(bgcolor="#13161E",bordercolor="#1E2330",borderwidth=1,
                    font=dict(size=9,color="#E0E0E0"),x=0.01,y=0.99),
        xaxis_rangeslider_visible=False, hovermode="x unified",
        hoverlabel=dict(bgcolor="#13161E",bordercolor="#1E2330",font=dict(color="#E0E0E0",size=10)),
    )
    fig.update_xaxes(gridcolor="#1A1E2A",showgrid=True,zeroline=False,
                     showspikes=True,spikecolor="#2A3040",spikedash="dot",spikethickness=1)
    fig.update_yaxes(gridcolor="#1A1E2A",showgrid=True,zeroline=False,tickformat=",.0f",row=1,col=1)
    return fig

# ─── PnL EQUITY CURVE ────────────────────────────────────────────────────────────
def build_equity_curve(trades: list) -> go.Figure:
    if not trades:
        return None
    cumulative = [0]
    for t in trades:
        cumulative.append(cumulative[-1]+t["pnl"])
    colors = ["#00FFA3" if v >= cumulative[i] else "#FF4B4B"
              for i,v in enumerate(cumulative[1:], start=1)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=cumulative, mode="lines+markers",
        line=dict(color="#5B6BFF",width=1.5),
        marker=dict(color=["#00FFA3" if t["outcome"]=="WIN" else "#FF4B4B" for t in trades]+["#5B6BFF"],
                    size=6),
        fill="tozeroy",
        fillcolor="rgba(91,107,255,.07)",
        name="Equity Curve",
    ))
    fig.update_layout(
        paper_bgcolor="#0E1117",plot_bgcolor="#0E1117",
        margin=dict(l=10,r=10,t=20,b=20),
        font=dict(family="JetBrains Mono",color="#555E78",size=10),
        showlegend=False, hovermode="x",
        hoverlabel=dict(bgcolor="#13161E",font=dict(color="#E0E0E0",size=10)),
    )
    fig.update_xaxes(gridcolor="#1A1E2A",showgrid=True,zeroline=False)
    fig.update_yaxes(gridcolor="#1A1E2A",showgrid=True,zeroline=True,
                     zerolinecolor="#2A3040",tickformat=",.1f")
    return fig

# ════════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="qx-wordmark">Quant<span>X</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="qx-tagline">F&amp;O Intelligence Terminal · v3</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-hdr">Market Index</div>', unsafe_allow_html=True)
    selected_label = st.selectbox("", list(INDICES.keys()), label_visibility="collapsed")
    idx_meta  = INDICES[selected_label]
    ticker    = idx_meta["ticker"]
    lot_size  = idx_meta["lot"]
    strike_gap= idx_meta["strike_gap"]

    st.markdown('<div class="section-hdr">Timeframe</div>', unsafe_allow_html=True)
    tf_label = st.radio("", list(TIMEFRAMES.keys()), horizontal=True, label_visibility="collapsed")
    interval = TIMEFRAMES[tf_label]

    st.markdown('<div class="section-hdr">Position Sizing</div>', unsafe_allow_html=True)
    capital  = st.number_input("Capital (₹)", min_value=10000, max_value=10000000,
                                value=100000, step=10000, label_visibility="collapsed")
    risk_pct = st.slider("Risk per Trade (%)", 0.5, 3.0, 1.0, 0.25)
    st.markdown(f'<p style="font-size:.62rem;color:#3D4560;margin-top:.2rem">'
                f'Max loss per trade: ₹{capital*(risk_pct/100):,.0f}</p>', unsafe_allow_html=True)

    st.markdown('<div class="section-hdr">Chart Overlays</div>', unsafe_allow_html=True)
    show_bb      = st.toggle("Bollinger Bands", value=True)
    show_vwap    = st.toggle("VWAP", value=True)
    show_signals = st.toggle("Backtest Signal Markers", value=True)

    st.markdown('<div class="section-hdr">Kill Switch</div>', unsafe_allow_html=True)
    kill_switch  = st.toggle("Halt All Signals", value=False)

    st.markdown('<div class="section-hdr">Telegram Alerts</div>', unsafe_allow_html=True)
    tg_token   = st.text_input("Bot Token", value="", type="password",
                                placeholder="123456:ABC-...", label_visibility="collapsed")
    tg_chat_id = st.text_input("Chat ID", value="",
                                placeholder="-100123456789", label_visibility="collapsed")
    st.markdown('<p style="font-size:.6rem;color:#3D4560;line-height:1.5">'
                '1. Create a bot via @BotFather<br>'
                '2. Add it to a group or DM it<br>'
                '3. Paste token + chat ID above</p>', unsafe_allow_html=True)

    st.markdown('<div class="section-hdr">Auto Refresh</div>', unsafe_allow_html=True)
    refresh_sec = st.slider("Interval (sec)", 15, 120, 30, 5, label_visibility="collapsed")
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=refresh_sec*1000, key="autorefresh")

    st.markdown("---")
    now       = datetime.now()
    mkt_open  = now.replace(hour=9,  minute=15, second=0, microsecond=0)
    mkt_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    is_open   = mkt_open <= now <= mkt_close and now.weekday() < 5
    dot_clr   = "#00FFA3" if is_open else "#FF4B4B"
    status_tx = "LIVE" if is_open else "CLOSED"
    st.markdown(
        f'<div style="font-size:.66rem;font-weight:700;letter-spacing:.1em;color:{dot_clr}">'
        f'<span class="status-dot" style="background:{dot_clr};box-shadow:0 0 6px {dot_clr}"></span>'
        f'NSE {status_tx}</div>'
        f'<p style="font-size:.61rem;color:#3D4560;margin-top:.2rem">'
        f'{now.strftime("%d %b %Y · %H:%M:%S IST")}</p>',
        unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:.62rem;color:#555E78;font-family:\'JetBrains Mono\',monospace;margin-top:.3rem">'
                f'{idx_meta["label"]} · Lot {lot_size} · Gap {strike_gap}</p>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
#  FETCH & COMPUTE
# ════════════════════════════════════════════════════════════════════════════════
with st.spinner("Syncing market data…"):
    df_raw   = fetch_data(ticker, interval)
    prev_d   = fetch_prev_day_ohlc(ticker)
    mtf_sigs = get_mtf_signals(ticker, interval)
    bt       = run_backtest(ticker, interval)

if df_raw.empty:
    st.error("⚠️ No data returned — market may be closed or ticker unavailable.")
    st.stop()

df_ind = calculate_indicators(df_raw)
pivots = calculate_pivots(prev_d)
regime = get_regime(df_ind)

# Auto kill-switch check
auto_ks = check_auto_kill_switch(bt)
if auto_ks and not kill_switch:
    kill_switch = True   # enforce programmatically

sig = generate_signal(df_ind, kill_switch, regime)
update_trade_log(sig, selected_label)
opts = calc_options_metrics(sig, capital, risk_pct, lot_size, strike_gap)

try:
    ltp        = float(df_ind["Close"].iloc[-1])
    open_price = float(df_ind["Open"].iloc[0])
    day_chg    = ltp - open_price
    day_chg_pct= (day_chg/open_price*100) if open_price else 0
    volatility = float(df_ind["ATR"].iloc[-1])  if "ATR" in df_ind.columns else 0.0
    adx_val    = float(df_ind["ADX"].iloc[-1])  if "ADX" in df_ind.columns else 0.0
    vwap_val   = float(df_ind["VWAP"].iloc[-1]) if "VWAP" in df_ind.columns else 0.0
except Exception:
    ltp=open_price=day_chg=day_chg_pct=volatility=adx_val=vwap_val=0.0

# ── Telegram alert (fires only once per new signal) ──
if sig["signal"]!="NONE" and (tg_token and tg_chat_id):
    last_sent = st.session_state.get("last_tg_signal","")
    sig_key   = f"{sig['signal']}_{sig['entry']:.1f}"
    if sig_key != last_sent:
        opts_with_lot = {**opts, "lot_size": lot_size}
        msg = build_alert_message(sig, selected_label, tf_label, opts_with_lot)
        sent = send_telegram_alert(tg_token, tg_chat_id, msg)
        if sent:
            st.session_state.last_tg_signal = sig_key

# ════════════════════════════════════════════════════════════════════════════════
#  MAIN UI
# ════════════════════════════════════════════════════════════════════════════════

# ── Auto kill-switch warning ──
if auto_ks:
    st.markdown(
        f'<div class="auto-ks-warn">🤖 AUTO KILL-SWITCH ENGAGED — Backtest win-rate '
        f'{bt["wr"]}% is below 40% safety floor. Signals halted automatically.</div>',
        unsafe_allow_html=True)
elif kill_switch:
    st.markdown('<div class="ks-off">⛔ KILL SWITCH ACTIVE — Trading Halted</div>',
                unsafe_allow_html=True)

# ── Signal alert banner ──
if sig["signal"]=="BUY":
    st.markdown(
        f'<div class="alert-buy">🟢 BUY SIGNAL — Score {sig["score"]}/100 · '
        f'Entry ₹{sig["entry"]:,.2f} · SL ₹{sig["sl"]:,.2f} · Target ₹{sig["target"]:,.2f}</div>',
        unsafe_allow_html=True)
elif sig["signal"]=="SELL":
    st.markdown(
        f'<div class="alert-sell">🔴 SELL SIGNAL — Score {sig["score"]}/100 · '
        f'Entry ₹{sig["entry"]:,.2f} · SL ₹{sig["sl"]:,.2f} · Target ₹{sig["target"]:,.2f}</div>',
        unsafe_allow_html=True)

# ── Regime banner ──
st.markdown(f'<div class="{regime["class"]}">{regime["label"]}</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
#  METRIC CARDS (Row 1)
# ════════════════════════════════════════════════════════════════════════════════
c1,c2,c3,c4,c5,c6 = st.columns(6)

with c1:
    chg_c="#00FFA3" if day_chg>=0 else "#FF4B4B"
    arrow="▲" if day_chg>=0 else "▼"
    st.markdown(f"""<div class="metric-card neutral-card">
      <div class="metric-label">LTP · {selected_label}</div>
      <div class="metric-value">₹{ltp:,.2f}</div>
      <div class="metric-sub" style="color:{chg_c}">{arrow} {abs(day_chg):,.2f} ({abs(day_chg_pct):.2f}%)</div>
    </div>""", unsafe_allow_html=True)

with c2:
    s   = sig["signal"]
    sc  = "signal-buy" if s=="BUY" else ("signal-sell" if s=="SELL" else "signal-none")
    crd = ("metric-card" if s=="BUY" else
           ("sell-card metric-card" if s=="SELL" else "neutral-card metric-card"))
    ico = "🔼" if s=="BUY" else ("🔽" if s=="SELL" else ("⚠️" if sig.get("suppressed") else "⏸"))
    sub = (f"Score {sig['score']}/100" if sig['score']
           else ("Regime suppressed" if sig.get("suppressed") else "Awaiting confluence"))
    st.markdown(f"""<div class="{crd}">
      <div class="metric-label">Signal · {tf_label}</div>
      <div class="metric-value {sc}">{ico} {s}</div>
      <div class="metric-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

with c3:
    sl_v = f"₹{sig['sl']:,.2f}" if sig["sl"] else "—"
    sl_pc= abs(ltp-sig["sl"])/ltp*100 if sig["sl"] and ltp else 0
    sl_c = "#FF4B4B" if sig["sl"] else "#3D4560"
    st.markdown(f"""<div class="metric-card sell-card">
      <div class="metric-label">Stop Loss · 1.5× ATR</div>
      <div class="metric-value" style="color:{sl_c}">{sl_v}</div>
      <div class="metric-sub">Risk {sl_pc:.2f}% · ATR {volatility:,.1f}</div>
    </div>""", unsafe_allow_html=True)

with c4:
    tgt_v= f"₹{sig['target']:,.2f}" if sig["target"] else "—"
    rr_d = abs(sig["target"]-ltp) if sig["target"] and ltp else 0
    tgt_c= "#00FFA3" if sig["target"] else "#3D4560"
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Target · 1:2 R/R</div>
      <div class="metric-value" style="color:{tgt_c}">{tgt_v}</div>
      <div class="metric-sub">Reward ₹{rr_d:,.2f}</div>
    </div>""", unsafe_allow_html=True)

with c5:
    score   = sig.get("score",0)
    sc_col  = "#00FFA3" if score>=70 else ("#FFB400" if score>=50 else "#FF4B4B")
    sc_crd  = ("metric-card" if score>=70
               else ("amber-card metric-card" if score>=50
                     else "sell-card metric-card"))
    st.markdown(f"""<div class="{sc_crd}">
      <div class="metric-label">Signal Score</div>
      <div class="score-wrap">
        <div class="score-bar-bg"><div class="score-bar-fill" style="width:{score}%;background:{sc_col}"></div></div>
        <div class="score-num" style="color:{sc_col}">{score}</div>
      </div>
      <div class="metric-sub">{'✅ ≥ 70 — fires' if score>=70 else ('⚠️ 50–69' if score>=50 else '✗ below threshold')}</div>
    </div>""", unsafe_allow_html=True)

with c6:
    vwap_c = "#00FFA3" if ltp>vwap_val else "#FF4B4B" if vwap_val else "#3D4560"
    vwap_str = f"₹{vwap_val:,.2f}" if vwap_val else "N/A"
    above  = "Above" if ltp>vwap_val else "Below"
    st.markdown(f"""<div class="metric-card neutral-card">
      <div class="metric-label">VWAP</div>
      <div class="metric-value" style="color:{vwap_c}">{vwap_str}</div>
      <div class="metric-sub">LTP {above} VWAP · ADX {adx_val:.1f}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
#  TABS: Chart  |  Backtest  |  Analytics
# ════════════════════════════════════════════════════════════════════════════════
tab_chart, tab_bt, tab_analytics = st.tabs(["📈  Price Chart", "🧪  Backtest Results", "📊  Analytics"])

with tab_chart:
    st.markdown('<div class="section-hdr">Candlestick · EMA · S/R · RSI · ADX'
                + (' · VWAP' if show_vwap else '')
                + (' · Bollinger Bands' if show_bb else '')
                + '</div>', unsafe_allow_html=True)
    fig = build_chart(df_ind, pivots, sig, show_bb, show_vwap, show_signals,
                      bt["trades"] if show_signals else [])
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

with tab_bt:
    st.markdown('<div class="section-hdr">Walk-Forward Backtest · Last 50 candles · Score ≥ 70 · ADX ≥ 20</div>',
                unsafe_allow_html=True)

    if bt["total"] == 0:
        st.markdown('<p style="color:#3D4560;font-size:.78rem">Not enough data for backtest on this timeframe.</p>',
                    unsafe_allow_html=True)
    else:
        # ── Summary row ──
        b1,b2,b3,b4,b5 = st.columns(5)
        wr_col = "#00FFA3" if bt["wr"]>=55 else ("#FFB400" if bt["wr"]>=40 else "#FF4B4B")
        pnl_col= "#00FFA3" if bt["pnl"]>=0 else "#FF4B4B"
        for col, label, val, color in [
            (b1,"Total Trades",bt["total"],"#E0E0E0"),
            (b2,"Wins",bt["wins"],"#00FFA3"),
            (b3,"Losses",bt["losses"],"#FF4B4B"),
            (b4,f"Win Rate",f"{bt['wr']}%",wr_col),
            (b5,"Net PnL (pts)",f"{bt['pnl']:+.1f}",pnl_col),
        ]:
            col.markdown(f"""<div class="metric-card neutral-card">
              <div class="metric-label">{label}</div>
              <div class="metric-value" style="color:{color}">{val}</div>
            </div>""", unsafe_allow_html=True)

        if auto_ks:
            st.markdown(
                '<p style="color:#FF4B4B;font-size:.72rem;margin-top:.6rem">'
                '⚠️ Win rate below 40% — Auto Kill-Switch has been engaged. '
                'Review your timeframe or wait for market conditions to improve.</p>',
                unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Equity curve ──
        eq_fig = build_equity_curve(bt["trades"])
        if eq_fig:
            st.markdown('<div class="section-hdr">Equity Curve (cumulative points)</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(eq_fig, use_container_width=True, config={"displayModeBar":False})

        # ── Trade table ──
        st.markdown('<div class="section-hdr">Recent Backtest Trades</div>', unsafe_allow_html=True)
        for t in reversed(bt["trades"][-10:]):
            oc  = "tlog-badge win" if t["outcome"]=="WIN" else "tlog-badge loss"
            dc  = "signal-buy" if t["dir"]=="BUY" else "signal-sell"
            pnl_c="#00FFA3" if t["pnl"]>=0 else "#FF4B4B"
            st.markdown(f"""<div class="tlog-entry">
              <div>
                <div class="tlog-time">{t['time']}</div>
                <div class="tlog-price">
                  <span class="{dc}">{t['dir']}</span>
                  &nbsp;Entry ₹{t['entry']:,.0f} → Exit ₹{t['exit']:,.0f}
                  &nbsp;<span style="color:{pnl_c};font-size:.72rem">{t['pnl']:+.1f} pts</span>
                </div>
              </div>
              <span class="{oc}">{t['outcome']}</span>
            </div>""", unsafe_allow_html=True)

with tab_analytics:
    # ── Bottom row: Pivots | Options Calc | Trade Log ──
    col_a, col_b, col_c = st.columns([1,1,1], gap="large")

    with col_a:
        st.markdown('<div class="section-hdr">Fibonacci Pivot Levels</div>', unsafe_allow_html=True)
        if pivots:
            meta={"R2":("Resistance 2","r-level"),"R1":("Resistance 1","r-level"),
                  "P":("Pivot","p-level"),"S1":("Support 1","s-level"),"S2":("Support 2","s-level")}
            rows=""
            for k in ["R2","R1","P","S1","S2"]:
                v=pivots.get(k,0); nm,cls=meta[k]
                diff=((v-ltp)/ltp*100) if ltp else 0
                ds=f"+{diff:.2f}%" if diff>0 else f"{diff:.2f}%"
                rows+=f"<tr><td>{nm}</td><td class='{cls}'><b>{k}</b></td><td class='{cls}'>₹{v:,.2f}</td><td style='color:#3D4560'>{ds}</td></tr>"
            st.markdown(f"""<table class="pivot-table">
              <thead><tr><th>Level</th><th>Label</th><th>Price</th><th>vs LTP</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#3D4560;font-size:.78rem">Pivot data unavailable.</p>',
                        unsafe_allow_html=True)

        st.markdown('<div class="section-hdr">Multi-Timeframe Alignment</div>', unsafe_allow_html=True)
        tfs   = MTF_MAP.get(interval,["5m","15m","60m"])
        cells = ""
        for tf in tfs:
            ms  = mtf_sigs.get(tf,"—")
            cls = "mtf-buy" if ms=="BUY" else ("mtf-sell" if ms=="SELL" else "mtf-none")
            ico = "↑" if ms=="BUY" else ("↓" if ms=="SELL" else "–")
            cells += f'<div class="mtf-cell"><div class="mtf-tf">{tf}</div><div class="mtf-sig {cls}">{ico} {ms}</div></div>'
        st.markdown(f'<div class="mtf-grid">{cells}</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="section-hdr">Options Position Calculator</div>', unsafe_allow_html=True)
        if opts:
            dir_word = "CE (Call)" if sig["signal"]=="BUY" else "PE (Put)"
            strike   = opts.get("ce_strike") or opts.get("pe_strike")
            kind     = "CE" if sig["signal"]=="BUY" else "PE"
            rows_html= f"""
            <div class="opt-row"><span class="opt-key">Direction</span>
              <span class="opt-val {'green' if sig['signal']=='BUY' else 'red'}">{sig['signal']} · {dir_word}</span></div>
            <div class="opt-row"><span class="opt-key">ATM Strike</span>
              <span class="opt-val">{strike} {kind}</span></div>
            <div class="opt-row"><span class="opt-key">SL Points</span>
              <span class="opt-val">{opts['sl_pts']:,.2f} pts</span></div>
            <div class="opt-row"><span class="opt-key">Target Points</span>
              <span class="opt-val green">{opts['tgt_pts']:,.2f} pts</span></div>
            <div class="opt-row"><span class="opt-key">R:R Ratio</span>
              <span class="opt-val">1 : {opts['rr']}</span></div>
            <div class="opt-row"><span class="opt-key">Lots Suggested</span>
              <span class="opt-val">{opts['lots']} lot{'s' if opts['lots']>1 else ''} ({opts['lots']*lot_size} units)</span></div>
            <div class="opt-row"><span class="opt-key">Capital at Risk</span>
              <span class="opt-val red">₹{opts['cap_risk']:,.0f} ({risk_pct}%)</span></div>
            <div class="opt-row"><span class="opt-key">Potential Gain</span>
              <span class="opt-val green">₹{opts['pot_gain']:,.0f}</span></div>
            """
            st.markdown(f'<div class="opt-card">{rows_html}</div>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size:.59rem;color:#3D4560;margin-top:.4rem;line-height:1.55">'
                        f'⚠️ Based on ₹{capital:,.0f} capital · {risk_pct}% risk · {lot_size} units/lot.<br>'
                        f'Paper-trade for 30+ sessions before live deployment.</p>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="opt-card"><p style="color:#3D4560;font-size:.76rem;text-align:center;padding:.5rem 0">'
                        'No active signal.<br>Calculator populates when Score ≥ 70 fires.</p></div>',
                        unsafe_allow_html=True)

    with col_c:
        st.markdown('<div class="section-hdr">Live Trade Log · Last 10 Signals</div>', unsafe_allow_html=True)
        log = st.session_state.get("trade_log",[])
        if not log:
            st.markdown('<p style="color:#3D4560;font-size:.76rem;padding:.4rem 0">'
                        'No signals yet. Waiting for Score ≥ 70 confluence…</p>',
                        unsafe_allow_html=True)
        else:
            for entry in log[:10]:
                sc  = "buy" if entry["signal"]=="BUY" else "sell"
                sl_s= f"SL ₹{entry['sl']:,.2f}" if entry["sl"] else ""
                ts  = f"T ₹{entry['target']:,.2f}" if entry["target"] else ""
                scr = f"· Score {entry.get('score',0)}" if entry.get('score') else ""
                st.markdown(f"""<div class="tlog-entry">
                  <div>
                    <div class="tlog-time">{entry['time']} · {entry['index']} {scr}</div>
                    <div class="tlog-price">₹{entry['entry']:,.2f}
                      <span style="color:#3D4560;font-size:.62rem"> {sl_s} {ts}</span>
                    </div>
                  </div>
                  <span class="tlog-badge {sc}">{entry['signal']}</span>
                </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-hdr" style="margin-top:.9rem">Session Stats</div>',
                    unsafe_allow_html=True)
        total_log = len(log)
        buy_ct    = sum(1 for e in log if e["signal"]=="BUY")
        sell_ct   = sum(1 for e in log if e["signal"]=="SELL")
        avg_sc    = np.mean([e.get("score",0) for e in log]) if log else 0
        sc_col2   = "#00FFA3" if avg_sc>=70 else ("#FFB400" if avg_sc>=50 else "#FF4B4B")
        st.markdown(f"""<div class="opt-card">
          <div class="opt-row"><span class="opt-key">Total Signals</span>
            <span class="opt-val">{total_log}</span></div>
          <div class="opt-row"><span class="opt-key">Buy</span>
            <span class="opt-val green">{buy_ct}</span></div>
          <div class="opt-row"><span class="opt-key">Sell</span>
            <span class="opt-val red">{sell_ct}</span></div>
          <div class="opt-row"><span class="opt-key">Avg Score</span>
            <span class="opt-val" style="color:{sc_col2}">{avg_sc:.1f}/100</span></div>
          <div class="opt-row"><span class="opt-key">BT Win Rate</span>
            <span class="opt-val" style="color:{'#00FFA3' if bt['wr']>=55 else ('#FFB400' if bt['wr']>=40 else '#FF4B4B')}">{bt['wr']}%</span></div>
        </div>""", unsafe_allow_html=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="font-size:.57rem;color:#2A3040;text-align:center;line-height:1.75">'
    '⚠️ RISK DISCLAIMER: QuantX is an analytical tool only — not financial advice. '
    'F&amp;O trading involves substantial risk of loss. Options can expire worthless. '
    'Never risk more than 1–2% of capital per trade. Signals are based on historical data patterns '
    'and do not guarantee future results. Paper-trade for a minimum of 30 sessions before committing '
    'real capital. Past backtest performance is not indicative of live trading results. Trade responsibly.</p>',
    unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
#  QUANTX v3 — FEATURE COMPLETION BLOCK
#  All modules from the proposal not yet in the base file:
#    1. Backtest win-rate progress bar in sidebar
#    2. Confluence strength indicator (MTF agreement score)
#    3. Intraday session heat-map (volatility by hour)
#    4. Daily P&L simulator (running the position sizing forward)
#    5. Market open countdown timer
# ════════════════════════════════════════════════════════════════════════════════

# ─── 1. SIDEBAR WIN-RATE BAR (appended to sidebar at runtime via session state) ─
#  Already rendered inside the Analytics tab above.
#  Expose it also in the sidebar for quick glance without tab switching.
with st.sidebar:
    st.markdown('<div class="section-hdr">Backtest Health</div>', unsafe_allow_html=True)
    wr   = bt["wr"]
    wr_c = "#00FFA3" if wr>=55 else ("#FFB400" if wr>=40 else "#FF4B4B")
    st.markdown(f"""
    <div style="font-family:'JetBrains Mono',monospace;font-size:.7rem;margin-bottom:.3rem">
      <span style="color:#555E78">Win Rate</span>
      <span style="color:{wr_c};float:right;font-weight:700">{wr}% ({bt['wins']}W / {bt['losses']}L)</span>
    </div>
    <div class="wr-bar-bg">
      <div class="wr-bar-fill" style="width:{min(wr,100)}%;background:{wr_c}"></div>
    </div>
    <p style="font-size:.59rem;color:#3D4560;margin-top:.3rem">
      {'🟢 Strategy healthy' if wr>=55 else ('🟡 Borderline — reduce size' if wr>=40 else '🔴 Auto Kill-Switch engaged')}
    </p>
    """, unsafe_allow_html=True)

# ─── 2. MTF CONFLUENCE SCORE ─────────────────────────────────────────────────────
def mtf_confluence_score(mtf: dict, direction: str) -> tuple[int, str]:
    """
    Returns (score 0-100, label) based on how many timeframes agree
    with the primary signal direction.
    """
    values = list(mtf.values())
    agrees = sum(1 for v in values if v == direction)
    total  = len([v for v in values if v in ("BUY","SELL","FLAT")])
    if total == 0:
        return 0, "No data"
    pct = int(agrees / len(values) * 100)
    if agrees == len(values):  label = "Full alignment ✅"
    elif agrees >= 2:           label = "Partial alignment ⚠️"
    elif agrees == 1:           label = "Weak — 1 TF agrees"
    else:                       label = "No alignment ✗"
    return pct, label

if sig["signal"] in ("BUY","SELL"):
    cf_score, cf_label = mtf_confluence_score(mtf_sigs, sig["signal"])
else:
    cf_score, cf_label = 0, "—"

# Render confluence bar below the signal score card (injected after cards)
if sig["signal"] in ("BUY","SELL"):
    cf_col = "#00FFA3" if cf_score>=67 else ("#FFB400" if cf_score>=33 else "#FF4B4B")
    st.markdown(f"""
    <div style="background:#13161E;border:1px solid #1E2330;border-radius:8px;
      padding:.65rem 1rem;margin-bottom:.5rem;display:flex;align-items:center;gap:1rem">
      <div style="flex:0 0 auto">
        <div style="font-size:.6rem;font-weight:700;letter-spacing:.1em;
          text-transform:uppercase;color:#3D4560;margin-bottom:.2rem">MTF Confluence</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:.82rem;
          font-weight:700;color:{cf_col}">{cf_score}% · {cf_label}</div>
      </div>
      <div style="flex:1;height:5px;background:#1A1E2A;border-radius:3px;overflow:hidden">
        <div style="width:{cf_score}%;height:100%;background:{cf_col};border-radius:3px"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─── 3. MARKET OPEN COUNTDOWN ────────────────────────────────────────────────────
def market_countdown() -> str:
    now = datetime.now()
    if now.weekday() >= 5:
        # Weekend — find next Monday
        days_ahead = 7 - now.weekday()
        next_open  = (now + timedelta(days=days_ahead)).replace(
            hour=9, minute=15, second=0, microsecond=0)
        diff = next_open - now
        h, rem = divmod(int(diff.total_seconds()), 3600)
        m, s   = divmod(rem, 60)
        return f"Market opens Monday in {h}h {m}m"
    mkt_open  = now.replace(hour=9,  minute=15, second=0, microsecond=0)
    mkt_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    if now < mkt_open:
        diff = mkt_open - now
        h, rem = divmod(int(diff.total_seconds()), 3600)
        m, s   = divmod(rem, 60)
        return f"⏰ Market opens in {h}h {m}m {s}s"
    elif now > mkt_close:
        next_open = (now + timedelta(days=1)).replace(
            hour=9, minute=15, second=0, microsecond=0)
        # Skip weekends
        while next_open.weekday() >= 5:
            next_open += timedelta(days=1)
        diff = next_open - now
        h, rem = divmod(int(diff.total_seconds()), 3600)
        m, _   = divmod(rem, 60)
        return f"⏰ Next session opens in {h}h {m}m"
    else:
        diff = mkt_close - now
        h, rem = divmod(int(diff.total_seconds()), 3600)
        m, s   = divmod(rem, 60)
        return f"🟢 Market closes in {h}h {m}m {s}s"

countdown_str = market_countdown()
with st.sidebar:
    st.markdown(
        f'<p style="font-size:.65rem;color:#555E78;font-family:\'JetBrains Mono\',monospace;'
        f'margin-top:.4rem;text-align:center">{countdown_str}</p>',
        unsafe_allow_html=True)

# ─── 4. INTRADAY VOLATILITY HEAT-MAP (Analytics tab) ────────────────────────────
def build_hourly_volatility(df: pd.DataFrame) -> go.Figure:
    """Bar chart of avg candle range by hour — shows which hours are most volatile."""
    if df.empty or "High" not in df.columns:
        return None
    tmp = df.copy()
    try:
        tmp.index = pd.to_datetime(tmp.index)
        tmp["hour"]  = tmp.index.hour
        tmp["range"] = (tmp["High"] - tmp["Low"]) / tmp["Close"] * 100
        hourly = tmp.groupby("hour")["range"].mean().reset_index()
        hourly = hourly[(hourly["hour"]>=9) & (hourly["hour"]<=15)]
        if hourly.empty:
            return None
        max_range = hourly["range"].max()
        colors = [
            "#FF4B4B" if v >= max_range*0.75 else
            ("#FFB400" if v >= max_range*0.5 else "#5B6BFF")
            for v in hourly["range"]
        ]
        fig = go.Figure(go.Bar(
            x=[f"{h:02d}:00" for h in hourly["hour"]],
            y=hourly["range"].round(3),
            marker_color=colors,
            text=[f"{v:.3f}%" for v in hourly["range"]],
            textposition="outside",
            textfont=dict(size=9, color="#E0E0E0"),
        ))
        fig.update_layout(
            paper_bgcolor="#0E1117", plot_bgcolor="#0E1117",
            font=dict(family="JetBrains Mono", color="#555E78", size=10),
            margin=dict(l=10,r=10,t=20,b=30),
            showlegend=False,
            bargap=0.25,
        )
        fig.update_xaxes(gridcolor="#1A1E2A", showgrid=False, zeroline=False)
        fig.update_yaxes(gridcolor="#1A1E2A", showgrid=True, zeroline=False,
                         ticksuffix="%", tickformat=".3f")
        return fig
    except Exception:
        return None

# ─── 5. DAILY P&L SIMULATOR ──────────────────────────────────────────────────────
def simulate_daily_pnl(bt: dict, capital: float, risk_pct: float,
                        lot_size: int) -> dict:
    """
    Takes backtest trades and simulates actual ₹ PnL using position sizing.
    Returns per-trade and cumulative ₹ PnL.
    """
    if not bt["trades"]:
        return {"pnl_series": [], "final_pnl": 0, "max_dd": 0, "best": 0, "worst": 0}

    pnl_series = []; cumulative = 0.0; peak = 0.0; max_dd = 0.0
    trade_pnls = []

    for t in bt["trades"]:
        sl_pts = abs(t["entry"] - (t["entry"] - t["pnl"] if t["dir"]=="BUY"
                                   else t["entry"] + t["pnl"]))
        sl_pts = max(sl_pts, 1)  # guard div/0
        lots   = max(1, int((capital*(risk_pct/100)) / (sl_pts*lot_size)))
        pnl_rs = t["pnl"] * lots * lot_size
        cumulative += pnl_rs
        peak        = max(peak, cumulative)
        drawdown    = peak - cumulative
        max_dd      = max(max_dd, drawdown)
        pnl_series.append(cumulative)
        trade_pnls.append(pnl_rs)

    return {
        "pnl_series": pnl_series,
        "final_pnl":  round(cumulative, 2),
        "max_dd":     round(max_dd, 2),
        "best":       round(max(trade_pnls), 2) if trade_pnls else 0,
        "worst":      round(min(trade_pnls), 2) if trade_pnls else 0,
    }

pnl_sim = simulate_daily_pnl(bt, capital, risk_pct, lot_size)

# ─── RENDER EXTENDED ANALYTICS ───────────────────────────────────────────────────
with tab_analytics:
    st.markdown("<br>", unsafe_allow_html=True)

    # ── P&L Simulator ──
    st.markdown('<div class="section-hdr">₹ P&L Simulator · Based on Your Position Sizing</div>',
                unsafe_allow_html=True)

    if pnl_sim["pnl_series"]:
        ps1, ps2, ps3, ps4 = st.columns(4)
        final_c = "#00FFA3" if pnl_sim["final_pnl"]>=0 else "#FF4B4B"
        best_c  = "#00FFA3"
        worst_c = "#FF4B4B"
        for col, label, val, color in [
            (ps1, "Simulated Net P&L",   f"₹{pnl_sim['final_pnl']:,.0f}", final_c),
            (ps2, "Max Drawdown",         f"₹{pnl_sim['max_dd']:,.0f}",    "#FF4B4B"),
            (ps3, "Best Single Trade",    f"₹{pnl_sim['best']:,.0f}",      "#00FFA3"),
            (ps4, "Worst Single Trade",   f"₹{pnl_sim['worst']:,.0f}",     "#FF4B4B"),
        ]:
            col.markdown(f"""<div class="metric-card neutral-card">
              <div class="metric-label">{label}</div>
              <div class="metric-value" style="color:{color}">{val}</div>
              <div class="metric-sub">Capital ₹{capital:,.0f} · Risk {risk_pct}%/trade</div>
            </div>""", unsafe_allow_html=True)

        # ₹ equity curve
        fig_pnl = go.Figure()
        fig_pnl.add_trace(go.Scatter(
            y=pnl_sim["pnl_series"], mode="lines+markers",
            line=dict(color="#5B6BFF", width=1.5),
            marker=dict(
                color=["#00FFA3" if v>=0 else "#FF4B4B" for v in pnl_sim["pnl_series"]],
                size=6),
            fill="tozeroy",
            fillcolor="rgba(91,107,255,.07)",
            name="₹ P&L",
        ))
        fig_pnl.update_layout(
            paper_bgcolor="#0E1117", plot_bgcolor="#0E1117",
            margin=dict(l=10,r=10,t=10,b=20),
            font=dict(family="JetBrains Mono", color="#555E78", size=10),
            showlegend=False, hovermode="x",
            hoverlabel=dict(bgcolor="#13161E",font=dict(color="#E0E0E0",size=10)),
        )
        fig_pnl.update_xaxes(gridcolor="#1A1E2A",showgrid=True,zeroline=False)
        fig_pnl.update_yaxes(gridcolor="#1A1E2A",showgrid=True,zeroline=True,
                              zerolinecolor="#2A3040",tickprefix="₹",tickformat=",.0f")
        st.plotly_chart(fig_pnl, use_container_width=True, config={"displayModeBar":False})
    else:
        st.markdown('<p style="color:#3D4560;font-size:.78rem">'
                    'No backtest trades to simulate. Try a longer timeframe (15m or 1h).</p>',
                    unsafe_allow_html=True)

    # ── Intraday Volatility Heat-map ──
    st.markdown('<div class="section-hdr">Intraday Volatility · Avg Candle Range % by Hour</div>',
                unsafe_allow_html=True)
    hv_fig = build_hourly_volatility(df_ind)
    if hv_fig:
        st.plotly_chart(hv_fig, use_container_width=True, config={"displayModeBar":False})
        st.markdown(
            '<p style="font-size:.61rem;color:#3D4560;margin-top:.2rem">'
            '🔴 High volatility hours (avoid for entries) · '
            '🟡 Moderate · '
            '🔵 Low volatility (safer entries, tighter spreads)</p>',
            unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#3D4560;font-size:.78rem">'
                    'Hourly data not available on this timeframe.</p>',
                    unsafe_allow_html=True)

    # ── Score breakdown table ──
    st.markdown('<div class="section-hdr">Signal Score Component Breakdown</div>',
                unsafe_allow_html=True)

    if sig["signal"] in ("BUY","SELL") and len(df_ind) >= 2:
        row_  = df_ind.iloc[-1]
        prev_ = df_ind.iloc[-2]
        d     = sig["signal"]
        ema9_ = float(row_.get("EMA9",0));  ema21_ = float(row_.get("EMA21",0))
        ema50_= float(row_.get("EMA50",0)); rsi_   = float(row_.get("RSI",50))
        adx_  = float(row_.get("ADX",0));   close_ = float(row_.get("Close",0))
        vol_  = float(row_.get("Volume",0));vavg_  = float(row_.get("VolAvg20",0))
        vwap_ = float(row_.get("VWAP",0)) if not np.isnan(row_.get("VWAP",np.nan) or np.nan) else 0

        components = []
        if d=="BUY":
            components = [
                ("EMA9 > EMA21",        ema9_>ema21_,                     15),
                ("EMA21 > EMA50",       ema21_>ema50_,                    10),
                ("RSI > 60",            rsi_>60,                          10),
                ("RSI in 60–75 zone",   60<=rsi_<=75,                     10),
                ("Close > Prev High",   close_>float(prev_.get("High",0)),10),
                ("Price above VWAP",    vwap_>0 and close_>vwap_,          5),
                ("ADX > 25",            adx_>25,                          20),
                ("ADX > 20 (partial)",  20<adx_<=25,                      10),
                ("Volume ≥ 1.5× avg",  vavg_>0 and vol_/vavg_>=1.5 if vavg_>0 else False, 25),
                ("Volume ≥ 1.2× avg",  vavg_>0 and 1.2<=vol_/vavg_<1.5 if vavg_>0 else False, 15),
            ]
        else:
            components = [
                ("EMA9 < EMA21",        ema9_<ema21_,                     15),
                ("EMA21 < EMA50",       ema21_<ema50_,                    10),
                ("RSI < 40",            rsi_<40,                          10),
                ("RSI in 25–40 zone",   25<=rsi_<40,                      10),
                ("Close < Prev Low",    close_<float(prev_.get("Low",9e9)),10),
                ("Price below VWAP",    vwap_>0 and close_<vwap_,          5),
                ("ADX > 25",            adx_>25,                          20),
                ("ADX > 20 (partial)",  20<adx_<=25,                      10),
                ("Volume ≥ 1.5× avg",  vavg_>0 and vol_/vavg_>=1.5 if vavg_>0 else False, 25),
                ("Volume ≥ 1.2× avg",  vavg_>0 and 1.2<=vol_/vavg_<1.5 if vavg_>0 else False, 15),
            ]

        rows_sc = ""
        for name, passed, pts in components:
            icon = "✅" if passed else "✗"
            clr  = "#00FFA3" if passed else "#3D4560"
            rows_sc += (f"<tr><td style='color:{clr}'>{icon} {name}</td>"
                        f"<td style='text-align:right;color:{clr};font-family:JetBrains Mono'>"
                        f"{'+'if passed else ''}{pts if passed else 0} pts</td></tr>")
        st.markdown(f"""<table class="pivot-table">
          <thead><tr><th>Component</th><th style="text-align:right">Points</th></tr></thead>
          <tbody>{rows_sc}</tbody>
        </table>""", unsafe_allow_html=True)
        st.markdown(
            f'<p style="font-size:.66rem;color:#555E78;margin-top:.5rem;font-family:\'JetBrains Mono\',monospace">'
            f'Total score: <span style="color:{"#00FFA3" if sig["score"]>=70 else "#FFB400"}">'
            f'{sig["score"]}/100</span> · '
            f'{"🟢 Fires trade" if sig["score"]>=70 else "⚠️ Does not fire (need ≥70)"}</p>',
            unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#3D4560;font-size:.78rem">'
                    'Score breakdown appears when a BUY or SELL condition is partially met.</p>',
                    unsafe_allow_html=True)
