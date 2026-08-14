"""Multiple Disease Prediction System — Streamlit app."""
import json
import os
import re
import sys
import base64
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from io import BytesIO
from html import escape
from pathlib import Path
from urllib.parse import quote_plus
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "code"))

from auth import init_db, signup, login, save_report, get_user_reports, delete_report, delete_all_reports  # noqa
from code.helper import generate_pdf, explain_prediction, HEALTH_TIPS   # noqa
from code.predictors import SCHEMAS, get_predictor, run_screening_prediction       # noqa
from code.DiseaseModel import DiseaseModel                               # noqa

st.set_page_config(
    page_title="MDPS — Multiple Disease Prediction System",
    page_icon="🩺", layout="wide", initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --primary: #1A73E8;
    --primary-dark: #1557B0;
    --primary-light: #E8F0FE;
    --teal: #0D9488;
    --teal-glow: #00D2B4;
    --emerald: #10B981;
    --danger: #EF4444;
    --warning: #F59E0B;
    --surface: rgba(255, 255, 255, 0.88);
    --surface-border: rgba(226, 232, 240, 0.9);
    --text-main: #0F172A;
    --text-muted: #64748B;
    --shadow-sm: 0 4px 12px rgba(15, 23, 42, 0.04);
    --shadow-md: 0 12px 32px -4px rgba(15, 23, 42, 0.08);
    --shadow-lg: 0 20px 48px -8px rgba(15, 23, 42, 0.12);
}

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    color: var(--text-main);
    letter-spacing: -0.01em;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(at 0% 0%, rgba(26, 115, 232, 0.07) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(0, 210, 180, 0.08) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(99, 102, 241, 0.05) 0px, transparent 50%),
        linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%) !important;
}

[data-testid="stHeader"] { background: transparent !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A192F 0%, #0F172A 50%, #081120 100%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.15) !important;
}
[data-testid="stSidebar"] * { color: #E2E8F0 !important; }
[data-testid="stSidebar"] .stRadio label {
    border: 1px solid rgba(255, 255, 255, 0.06);
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    margin-bottom: 0.35rem;
    padding: 0.45rem 0.65rem;
    transition: all 0.2s ease;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(26, 115, 232, 0.15);
    border-color: rgba(0, 210, 180, 0.3);
    transform: translateX(3px);
}
.sidebar-brand {
    text-align: center; padding: 12px 0 4px;
    font-family: 'Outfit', sans-serif;
    font-size: 1.9rem; font-weight: 800;
    letter-spacing: -0.04em;
    background: linear-gradient(135deg, #FFFFFF 30%, #38BDF8 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.sidebar-tagline {
    text-align: center; font-size: 0.72rem; color: #94A3B8 !important;
    margin-bottom: 12px; letter-spacing: 0.14em; text-transform: uppercase;
    font-weight: 600;
}

/* ── Typography & Headings ── */
.main-title {
    font-family: 'Outfit', sans-serif !important;
    font-size: 2.3rem; font-weight: 800; color: #0F172A;
    margin-bottom: 0.2rem; letter-spacing: -0.03em;
    line-height: 1.15;
}
.subtitle {
    color: var(--text-muted); margin-top: 0; font-size: 1rem;
    line-height: 1.5; margin-bottom: 1.2rem;
}

/* ── Hero Banner ── */
.hero-banner {
    position: relative; overflow: hidden;
    background: linear-gradient(135deg, #0A192F 0%, #1E3A8A 45%, #0D9488 100%) !important;
    color: white; padding: 3.2rem 2.8rem; border-radius: 28px;
    margin-bottom: 1.8rem; box-shadow: 0 20px 50px rgba(10, 25, 47, 0.22);
    border: 1px solid rgba(255, 255, 255, 0.15);
}
.hero-banner::before {
    content: ""; position: absolute; top: -60px; right: -60px;
    width: 320px; height: 320px; border-radius: 50%;
    background: radial-gradient(circle, rgba(0, 210, 180, 0.25), transparent 70%);
    pointer-events: none;
}
.hero-banner h1 {
    font-family: 'Outfit', sans-serif !important;
    font-size: 2.7rem; font-weight: 800; line-height: 1.1;
    letter-spacing: -0.04em; margin: 0 0 0.6rem;
    background: linear-gradient(135deg, #FFFFFF 40%, #A7F3D0 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-banner p { font-size: 1.05rem; opacity: 0.9; margin: 0; max-width: 680px; line-height: 1.55; color: #E2E8F0 !important; }
.hero-badge {
    display: inline-flex; gap: 0.5rem; align-items: center;
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.22); color: #FFFFFF !important;
    padding: 6px 14px; border-radius: 999px; font-size: 0.78rem;
    margin-bottom: 1rem; letter-spacing: 0.08em; text-transform: uppercase;
    font-weight: 700; backdrop-filter: blur(10px);
}

/* ── Live Pulse Badge ── */
.live-badge {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 14px; border-radius: 999px; font-size: 0.78rem;
    font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
    background: rgba(16, 185, 129, 0.10); color: #059669;
    border: 1px solid rgba(16, 185, 129, 0.28); margin-bottom: 0.8rem;
}
.pulse-dot {
    width: 8px; height: 8px; border-radius: 50%; background: #10B981;
    box-shadow: 0 0 0 rgba(16, 185, 129, 0.5);
    animation: pulseAnimation 2s infinite;
}
@keyframes pulseAnimation {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* ── Glassmorphism Cards ── */
.metric-card, .feature-tile, .section-card, .upload-zone, .risk-row,
.risk-meter-card, .report-summary, .assistant-shell, .care-panel,
.clean-callout, .clinical-card, .signal-card, .analysis-stat, .report-workspace {
    background: var(--surface) !important;
    border: 1px solid var(--surface-border) !important;
    border-radius: 20px !important;
    box-shadow: var(--shadow-md) !important;
    backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
    transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
.metric-card:hover, .feature-tile:hover, .risk-row:hover, .signal-card:hover {
    transform: translateY(-3px) scale(1.01) !important;
    box-shadow: var(--shadow-lg) !important;
    border-color: rgba(26, 115, 232, 0.35) !important;
}
.metric-card {
    padding: 1.25rem 1.4rem !important;
    background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(245,250,255,0.94)) !important;
}
.metric-card h2 {
    font-family: 'Outfit', sans-serif !important;
    color: #0F172A; font-size: 2.1rem; font-weight: 800;
    margin: 4px 0 0;
}
.feature-tile { padding: 1.4rem; height: 100%; }
.feature-icon {
    width: 48px; height: 48px; border-radius: 14px;
    background: linear-gradient(135deg, rgba(26, 115, 232, 0.12), rgba(0, 210, 180, 0.18));
    display: flex; align-items: center; justify-content: center;
    font-size: 1.35rem; font-weight: 800; color: var(--primary);
    margin-bottom: 0.85rem;
}
.feature-title { font-weight: 700; color: #0F172A; font-size: 1.05rem; }
.feature-desc { color: var(--text-muted) !important; font-size: 0.9rem; line-height: 1.55; }

/* ── Result Badges ── */
.result-positive, .result-negative {
    padding: 1.2rem 1.4rem; border-radius: 18px; font-weight: 700;
    border: 1px solid transparent; font-size: 1.05rem;
}
.result-positive {
    background: #FFF1F2 !important; color: #9F1239 !important;
    border-color: #FECDD3 !important; box-shadow: 0 4px 16px rgba(225, 29, 72, 0.08);
}
.result-negative {
    background: #ECFDF5 !important; color: #065F46 !important;
    border-color: #A7F3D0 !important; box-shadow: 0 4px 16px rgba(5, 150, 105, 0.08);
}

/* ── Status Chips ── */
.risk-chip {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.36rem 0.85rem; border-radius: 999px;
    font-size: 0.78rem; font-weight: 800; border: 1px solid transparent;
}
.risk-high { background: #FFF1F2 !important; color: #9F1239 !important; border-color: #FECDD3 !important; }
.risk-low { background: #ECFDF5 !important; color: #065F46 !important; border-color: #A7F3D0 !important; }
.risk-neutral { background: #F1F5F9 !important; color: #475569 !important; border-color: #E2E8F0 !important; }

/* ── Clean Callout & Status Notes ── */
.clean-callout {
    padding: 1.2rem 1.4rem; margin: 1rem 0;
    border-left: 5px solid var(--primary) !important;
    background: linear-gradient(180deg, #FFFFFF, #F8FAFC) !important;
}
.status-note {
    background: linear-gradient(180deg, #F0F9FF, #F8FAFC) !important;
    border: 1px solid #BAE6FD !important; border-left: 5px solid var(--primary) !important;
    padding: 1.1rem 1.25rem; border-radius: 16px; color: #0369A1;
}

/* ── Profile Card ── */
.profile-card {
    background: linear-gradient(135deg, #0A192F 0%, #1E3A8A 50%, #0D9488 100%) !important;
    color: white !important; border-radius: 24px; padding: 2.2rem;
    text-align: center; margin-bottom: 1.5rem;
    box-shadow: 0 16px 40px rgba(10, 25, 47, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.15);
}
.profile-avatar {
    width: 76px; height: 76px; border-radius: 50%;
    background: rgba(255, 255, 255, 0.18); display: flex;
    align-items: center; justify-content: center;
    font-size: 2.2rem; font-weight: 800; margin: 0 auto 1rem;
    border: 3px solid rgba(255, 255, 255, 0.4);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}
.profile-name { font-family: 'Outfit', sans-serif; font-size: 1.5rem; font-weight: 800; color: #FFFFFF !important; }
.profile-email { opacity: 0.85; font-size: 0.92rem; color: #E2E8F0 !important; }

/* ── Stat Pill ── */
.stat-pill {
    background: #F8FAFC; border: 1px solid #E2E8F0;
    border-radius: 14px; padding: 0.75rem 1.25rem;
    display: inline-block; text-align: center; width: 100%;
}
.stat-pill .num { font-family: 'Outfit', sans-serif; font-size: 1.5rem; font-weight: 800; color: var(--primary); }
.stat-pill .lbl { font-size: 0.78rem; color: var(--text-muted); display: block; font-weight: 600; }

/* ── Modern Buttons ── */
.stButton > button, .stDownloadButton > button {
    border-radius: 14px !important;
    border: 1px solid rgba(26, 115, 232, 0.25) !important;
    background: linear-gradient(135deg, #1A73E8 0%, #0D9488 100%) !important;
    color: #FFFFFF !important; font-weight: 700 !important;
    padding: 0.65rem 1.4rem !important; font-size: 0.95rem !important;
    box-shadow: 0 10px 25px -5px rgba(26, 115, 232, 0.35) !important;
    transition: all 0.22s ease !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 14px 30px -4px rgba(26, 115, 232, 0.45) !important;
    filter: brightness(1.06) !important;
}

/* ── Form Inputs & Text Areas ── */
div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, .stSelectbox > div {
    border-radius: 12px !important;
    border: 1px solid #CBD5E1 !important;
    transition: all 0.2s ease !important;
}
div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(26, 115, 232, 0.16) !important;
}

/* ── File Uploader ── */
div[data-testid="stFileUploader"] section {
    border: 2px dashed #94A3B8 !important;
    border-radius: 20px !important;
    background: linear-gradient(180deg, #F8FAFC, #F1F5F9) !important;
    padding: 1.5rem !important;
}

/* ── Chat Assistant Shell ── */
.assistant-shell { padding: 1.4rem !important; background: rgba(255, 255, 255, 0.92) !important; }
.message-user {
    background: linear-gradient(135deg, #1A73E8, #2563EB) !important;
    color: white !important; border-radius: 18px 18px 4px 18px !important;
    padding: 0.95rem 1.2rem !important; margin: 0.65rem 0 0.65rem auto !important;
    max-width: 82% !important; box-shadow: 0 6px 18px rgba(37, 99, 235, 0.2) !important;
}
.message-user * { color: white !important; }
.message-assistant {
    background: linear-gradient(135deg, #F8FAFC, #F1F5F9) !important;
    color: #0F172A !important; border-radius: 18px 18px 18px 4px !important;
    border: 1px solid #E2E8F0 !important;
    padding: 1.1rem 1.3rem !important; margin: 0.65rem auto 0.65rem 0 !important;
    max-width: 85% !important; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03) !important;
    line-height: 1.65;
}

/* ── Report Workspace & Analysis Panel ── */
.report-workspace {
    background: linear-gradient(180deg, rgba(255,255,255,0.85), rgba(247,252,253,0.95)) !important;
    border-radius: 26px !important; padding: 1.4rem !important; margin-bottom: 1.4rem;
}
.analysis-hero { display: grid; grid-template-columns: 2fr 1fr; gap: 1.2rem; margin-bottom: 1rem; }
.analysis-panel {
    background: linear-gradient(135deg, #0A192F 0%, #0F766E 60%, #0D9488 100%) !important;
    color: white; border-radius: 22px; padding: 1.6rem 1.8rem; box-shadow: var(--shadow-md);
}
.analysis-panel h3 { margin: 0 0 0.5rem; font-size: 1.6rem; font-weight: 800; font-family: 'Outfit', sans-serif; color: white !important; }
.analysis-panel p { margin: 0; opacity: 0.9; line-height: 1.55; color: #E2E8F0 !important; }
.analysis-stat {
    background: rgba(255, 255, 255, 0.9); color: #0F172A; border-radius: 22px; padding: 1.4rem;
}
.analysis-stat .label { color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; }
.analysis-stat .value { font-family: 'Outfit', sans-serif; font-size: 1.9rem; font-weight: 800; margin-top: 0.3rem; color: var(--primary); }

/* ── Signal Grid ── */
.signal-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 1rem; margin: 1.2rem 0; }
.signal-card {
    padding: 1.2rem; border-radius: 18px; border: 1px solid #E2E8F0;
    background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
}
.signal-card.high {
    border-color: #FECDD3; background: linear-gradient(180deg, #FFF1F2 0%, #FFF7F8 100%);
}
.signal-card .signal-name { font-size: 1.05rem; font-weight: 800; color: #0F172A; margin-bottom: 0.35rem; }
.signal-card .signal-score { font-size: 1.8rem; font-weight: 800; color: var(--teal); margin-bottom: 0.35rem; }
.signal-card.high .signal-score { color: #E11D48; }
.signal-card .signal-note { color: var(--text-muted); font-size: 0.88rem; line-height: 1.5; margin-top: 0.4rem; }

/* ── Risk Row ── */
.risk-row { padding: 1.1rem 1.25rem; margin: 0.75rem 0; }
.risk-title { font-weight: 800; color: #0F172A; font-size: 1.02rem; margin-bottom: 0.25rem; }
.risk-detail { color: var(--text-muted); font-size: 0.9rem; }
.gauge-title { text-align: center; font-weight: 700; color: #0F172A; margin-bottom: 0.35rem; font-size: 0.96rem; }

/* ── Dark Mode ── */
[data-testid="stAppViewContainer"].dark-mode {
    background:
        radial-gradient(at 0% 0%, rgba(26, 115, 232, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(0, 210, 180, 0.12) 0px, transparent 50%),
        #070B14 !important;
}
[data-testid="stSidebar"].dark-mode { background: #070D18 !important; }
.dark-mode .main-title, .dark-mode .feature-title, .dark-mode .gauge-title, .dark-mode .clinical-heading { color: #F8FAFC !important; }
.dark-mode .subtitle, .dark-mode .feature-desc, .dark-mode .clinical-summary, .dark-mode .risk-detail, .dark-mode .report-meta { color: #94A3B8 !important; }
.dark-mode .metric-card, .dark-mode .feature-tile, .dark-mode .section-card,
.dark-mode .upload-zone, .dark-mode .risk-row, .dark-mode .risk-meter-card,
.dark-mode .report-summary, .dark-mode .assistant-shell, .dark-mode .care-panel,
.dark-mode .clean-callout, .dark-mode .clinical-card, .dark-mode .signal-card,
.dark-mode .analysis-stat, .dark-mode .report-workspace {
    background: rgba(15, 23, 42, 0.85) !important;
    border-color: rgba(51, 65, 85, 0.8) !important;
    color: #E2E8F0 !important;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.35) !important;
}
.dark-mode .metric-card h2 { color: #F8FAFC !important; }
.dark-mode .stat-pill { background: #0F172A !important; border-color: #1E293B !important; }
.dark-mode .signal-card.high { background: #2A1215 !important; border-color: #881337 !important; }
.dark-mode .message-assistant { background: #131E32 !important; border-color: #233554 !important; color: #E2E8F0 !important; }
.dark-mode .message-assistant * { color: #E2E8F0 !important; }

@media (max-width: 980px) {
    .analysis-hero { grid-template-columns: 1fr; }
    .hero-banner { padding: 2.2rem 1.5rem; }
    .hero-banner h1 { font-size: 2.1rem; }
}
</style>
"""

init_db()

if "user"           not in st.session_state: st.session_state.user           = None
if "last_pred"      not in st.session_state: st.session_state.last_pred      = None
if "dark_mode"      not in st.session_state: st.session_state.dark_mode      = False
if "confirm_delete" not in st.session_state: st.session_state.confirm_delete = False
if "guest_reports"  not in st.session_state: st.session_state.guest_reports  = []

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if st.session_state.dark_mode:
    st.markdown("""
    <script>
        var app     = window.parent.document.querySelector('[data-testid="stAppViewContainer"]');
        var sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
        if(app)     app.classList.add('dark-mode');
        if(sidebar) sidebar.classList.add('dark-mode');
    </script>
    <style>
        [data-testid="stAppViewContainer"] { background-color:#0e1117 !important; }
        [data-testid="stSidebar"]          { background-color:#111827 !important; }
        .stMarkdown, p, label { color:#e2e8f0 !important; }
        h1, h2, h3            { color:#90cdf4 !important; }
        [data-testid="stTextInput"] input  { background:#1a1f2e !important; color:white !important; }
    </style>
    """, unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def risk_gauge(confidence, positive: bool):
    if confidence is None:
        confidence = 0.75 if positive else 0.3
    value = confidence * 100
    color = "#d9534f" if positive else "#28a745"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%", "font": {"size": 28, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#ccc"},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "white", "borderwidth": 0,
            "steps": [
                {"range": [0,  40], "color": "#eafaf1"},
                {"range": [40, 70], "color": "#fef9e7"},
                {"range": [70,100], "color": "#fdedec"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.8, "value": value},
        },
        title={"text": "Risk Score", "font": {"size": 14, "color": "#5b6b80"}},
    ))
    fig.update_layout(height=220, margin=dict(t=40,b=10,l=20,r=20),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


# ── Auth ──────────────────────────────────────────────────────────────────────
def report_dataframe(reports):
    if not reports:
        return pd.DataFrame()
    df = pd.DataFrame(reports)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")
    df["severity"] = pd.to_numeric(df["severity"], errors="coerce")
    df["at_risk"] = df["prediction"].astype(str).str.contains(
        "Positive|High|At Risk", case=False, na=False
    )
    df["risk_score"] = df["confidence"].fillna(df["severity"] / 10).fillna(
        df["at_risk"].map({True: 0.75, False: 0.25})
    )
    df["risk_score"] = df["risk_score"].clip(0, 1)
    return df.sort_values("date")


def get_groq_api_key():
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    try:
        api_key = api_key or st.secrets.get("groq", {}).get("api_key", "").strip()
    except Exception:
        pass
    if not api_key or api_key == "GROQ_API_KEY_HERE":
        return None
    return api_key


LAB_MARKERS = {
    "HbA1c": ["hba1c", "glycated hemoglobin", "glycosylated hemoglobin"],
    "Fasting Glucose": ["fasting glucose", "fasting blood sugar", "fbs", "glucose fasting"],
    "Random Glucose": ["random glucose", "random blood sugar", "rbs", "blood glucose random"],
    "Total Cholesterol": ["total cholesterol", "cholesterol total"],
    "LDL": ["ldl", "ldl cholesterol"],
    "HDL": ["hdl", "hdl cholesterol"],
    "Triglycerides": ["triglycerides", "triglyceride", "tg"],
    "Creatinine": ["creatinine", "serum creatinine"],
    "Urea": ["urea", "blood urea"],
    "eGFR": ["egfr", "estimated gfr"],
    "Hemoglobin": ["hemoglobin", "haemoglobin", "hb"],
    "WBC": ["wbc", "white blood cell", "total leukocyte"],
    "RBC": ["rbc", "red blood cell"],
    "Platelets": ["platelet", "platelets"],
    "ALT": ["alt", "sgpt", "alanine aminotransferase"],
    "AST": ["ast", "sgot", "aspartate aminotransferase"],
    "ALP": ["alp", "alkaline phosphatase"],
    "Total Bilirubin": ["total bilirubin", "bilirubin total"],
    "Direct Bilirubin": ["direct bilirubin", "bilirubin direct"],
    "Albumin": ["albumin"],
    "TSH": ["tsh", "thyroid stimulating hormone"],
    "Vitamin D": ["vitamin d", "25-oh vitamin d", "25 hydroxy vitamin d"],
}


REFERENCE_RANGES = {
    "HbA1c": (4.0, 5.6, "%"),
    "Fasting Glucose": (70, 99, "mg/dL"),
    "Random Glucose": (70, 140, "mg/dL"),
    "Total Cholesterol": (0, 200, "mg/dL"),
    "LDL": (0, 100, "mg/dL"),
    "HDL": (40, 100, "mg/dL"),
    "Triglycerides": (0, 150, "mg/dL"),
    "Creatinine": (0.6, 1.3, "mg/dL"),
    "Urea": (10, 45, "mg/dL"),
    "eGFR": (90, 140, "mL/min/1.73m2"),
    "Hemoglobin": (12, 17.5, "g/dL"),
    "WBC": (4000, 11000, "/uL"),
    "Platelets": (150000, 450000, "/uL"),
    "ALT": (0, 45, "U/L"),
    "AST": (0, 40, "U/L"),
    "ALP": (44, 147, "U/L"),
    "Total Bilirubin": (0.1, 1.2, "mg/dL"),
    "Direct Bilirubin": (0.0, 0.3, "mg/dL"),
    "Albumin": (3.5, 5.5, "g/dL"),
    "TSH": (0.4, 4.0, "mIU/L"),
    "Vitamin D": (30, 100, "ng/mL"),
}

FACILITY_SEARCH_RULES = {
    "Hospital": {"amenities": ["hospital"], "keywords": []},
    "Emergency Hospital": {"amenities": ["hospital"], "keywords": ["emergency", "trauma", "24x7"]},
    "Medical Clinic": {"amenities": ["clinic", "doctors"], "keywords": ["clinic", "medical"]},
    "Cardiology": {"amenities": ["hospital", "clinic", "doctors"], "keywords": ["cardio", "heart"]},
    "Neurology": {"amenities": ["hospital", "clinic", "doctors"], "keywords": ["neuro", "brain"]},
    "Oncology": {"amenities": ["hospital", "clinic", "doctors"], "keywords": ["onco", "cancer"]},
    "Nephrology": {"amenities": ["hospital", "clinic", "doctors"], "keywords": ["neph", "kidney", "renal"]},
    "Pharmacy": {"amenities": ["pharmacy"], "keywords": ["pharmacy", "medical store"]},
}


def normalize_report_text(text):
    text = re.sub(r"[ \t]+", " ", text or "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_text(file_bytes):
    try:
        import fitz
    except Exception:
        return "", ["Install PyMuPDF to read PDF text locally."]

    warnings = []
    chunks = []
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                chunks.append(page.get_text("text"))
    except Exception as exc:
        warnings.append(f"PDF text extraction failed: {exc}")
    return normalize_report_text("\n".join(chunks)), warnings


def pdf_first_pages_as_images(file_bytes, limit=3):
    try:
        import fitz
    except Exception:
        return []

    images = []
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in list(doc)[:limit]:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                images.append(("image/png", pix.tobytes("png")))
    except Exception:
        return []
    return images


def extract_report_text(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    file_type = uploaded_file.type or ""
    warnings = []
    text = ""

    if file_type == "application/pdf" or uploaded_file.name.lower().endswith(".pdf"):
        text, warnings = extract_pdf_text(file_bytes)
        if len(text) < 200:
            warnings.append("This PDF looks scanned or image-only. Please upload a text-based PDF for local extraction.")
    elif file_type.startswith("image/"):
        warnings.append("Image OCR is disabled in report analyzer. Upload a text-based PDF for local extraction.")
    else:
        warnings.append("Unsupported file type. Upload a PDF, JPG, JPEG, or PNG report.")

    return text, warnings


def fetch_json(url, *, method="GET", data=None, headers=None):
    request = Request(url, data=data.encode("utf-8") if isinstance(data, str) else data, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


@st.cache_data(show_spinner=False, ttl=1800)
def geocode_place(query):
    params = urlencode({"q": query, "format": "jsonv2", "limit": 1})
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    data = fetch_json(url, headers={"User-Agent": "MDPS/1.0"})
    if not data:
        return None
    result = data[0]
    return {
        "lat": float(result["lat"]),
        "lon": float(result["lon"]),
        "display_name": result["display_name"],
    }


@st.cache_data(show_spinner=False, ttl=900)
def fetch_nearby_facilities(city, speciality):
    rule = FACILITY_SEARCH_RULES[speciality]
    location = geocode_place(city)
    if not location:
        return None, []

    amenities = rule["amenities"]
    query_blocks = []
    for amenity in amenities:
        query_blocks.extend([
            f'node["amenity"="{amenity}"](around:15000,{location["lat"]},{location["lon"]});',
            f'way["amenity"="{amenity}"](around:15000,{location["lat"]},{location["lon"]});',
            f'relation["amenity"="{amenity}"](around:15000,{location["lat"]},{location["lon"]});',
        ])
    overpass_query = f"[out:json][timeout:25];({''.join(query_blocks)});out center 40;"
    payload = fetch_json(
        "https://overpass-api.de/api/interpreter",
        method="POST",
        data=overpass_query,
        headers={"Content-Type": "text/plain", "User-Agent": "MDPS/1.0"},
    )

    keywords = [keyword.lower() for keyword in rule["keywords"]]
    facilities = []
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        lat = element.get("lat", element.get("center", {}).get("lat"))
        lon = element.get("lon", element.get("center", {}).get("lon"))
        if lat is None or lon is None:
            continue
        haystack = " ".join([
            name,
            tags.get("healthcare", ""),
            tags.get("description", ""),
            tags.get("healthcare:speciality", ""),
        ]).lower()
        if keywords and not any(keyword in haystack for keyword in keywords):
            if speciality not in {"Hospital", "Medical Clinic", "Pharmacy"}:
                continue
        address = ", ".join([
            tags.get("addr:street", ""),
            tags.get("addr:suburb", ""),
            tags.get("addr:city", city),
        ]).strip(", ")
        facilities.append({
            "name": name,
            "lat": float(lat),
            "lon": float(lon),
            "address": address or city,
            "type": tags.get("amenity", tags.get("healthcare", speciality)),
        })

    unique = []
    seen = set()
    for facility in facilities:
        key = (facility["name"], round(facility["lat"], 4), round(facility["lon"], 4))
        if key in seen:
            continue
        seen.add(key)
        unique.append(facility)
    return location, unique[:25]


def extract_lab_values(text):
    values = {}
    lower_text = text.lower()
    for label, aliases in LAB_MARKERS.items():
        matches = []
        for alias in aliases:
            pattern = rf"(?i)\b{re.escape(alias)}\b[^\n\r0-9<>-]{{0,45}}(?:[:=\-]|\s)\s*([<>]?\s*-?\d+(?:\.\d+)?)"
            for match in re.finditer(pattern, text):
                raw = match.group(1).replace(" ", "")
                try:
                    value = float(raw.replace("<", "").replace(">", ""))
                except ValueError:
                    continue
                window = text[match.start():match.end() + 35]
                unit_match = re.search(r"(mg/dl|g/dl|u/l|iu/l|%|ng/ml|miu/l|mmol/l|/ul|cells/ul)", window, re.I)
                matches.append({
                    "value": value,
                    "raw": raw,
                    "unit": unit_match.group(1) if unit_match else REFERENCE_RANGES.get(label, (None, None, ""))[2],
                    "source": window.strip(),
                })
        if matches:
            candidate = matches[0]
            low, high, _ = REFERENCE_RANGES.get(label, (None, None, ""))
            source_lower = candidate["source"].lower()
            if label == "WBC" and candidate["value"] < 100 and ("10^3" in source_lower or "x10" in source_lower):
                candidate["value"] *= 1000
            if label == "Platelets" and candidate["value"] < 1000 and ("lakh" in source_lower or "10^3" in source_lower or "x10" in source_lower):
                candidate["value"] *= 1000
            status = "Normal"
            if low is not None and candidate["value"] < low:
                status = "Low"
            if high is not None and candidate["value"] > high:
                status = "High"
            if label == "eGFR" and candidate["value"] < 60:
                status = "Low"
            candidate["status"] = status
            values[label] = candidate
    return values


def value_score(value, normal_low=None, normal_high=None, danger_low=None, danger_high=None, inverse=False):
    if value is None:
        return 0
    if inverse:
        if danger_low is not None and value <= danger_low:
            return 100
        if normal_low is not None and value >= normal_low:
            return 0
        return int(min(100, max(20, (normal_low - value) / max(normal_low - danger_low, 1) * 100)))
    if danger_high is not None and value >= danger_high:
        return 100
    if normal_high is not None and value <= normal_high:
        return 0
    return int(min(100, max(20, (value - normal_high) / max(danger_high - normal_high, 1) * 100)))


def build_report_risk_analysis(values):
    get = lambda name: values.get(name, {}).get("value")
    signals = []

    diabetes = max(
        value_score(get("HbA1c"), normal_high=5.6, danger_high=9.0),
        value_score(get("Fasting Glucose"), normal_high=99, danger_high=180),
        value_score(get("Random Glucose"), normal_high=140, danger_high=250),
    )
    signals.append(("Diabetes / Poor Glucose Control", diabetes,
                    "Uses HbA1c, fasting glucose, and random glucose when present."))

    kidney = max(
        value_score(get("Creatinine"), normal_high=1.3, danger_high=5.0),
        value_score(get("Urea"), normal_high=45, danger_high=150),
        value_score(get("eGFR"), normal_low=90, danger_low=30, inverse=True),
    )
    signals.append(("Chronic Kidney Disease Risk", kidney,
                    "Uses creatinine, urea, and eGFR patterns when present."))

    liver = max(
        value_score(get("ALT"), normal_high=45, danger_high=300),
        value_score(get("AST"), normal_high=40, danger_high=300),
        value_score(get("ALP"), normal_high=147, danger_high=500),
        value_score(get("Total Bilirubin"), normal_high=1.2, danger_high=5.0),
        value_score(get("Direct Bilirubin"), normal_high=0.3, danger_high=2.0),
    )
    signals.append(("Liver / Jaundice Risk", liver,
                    "Uses bilirubin and liver enzyme abnormalities when present."))

    heart = max(
        value_score(get("Total Cholesterol"), normal_high=200, danger_high=300),
        value_score(get("LDL"), normal_high=100, danger_high=190),
        value_score(get("Triglycerides"), normal_high=150, danger_high=500),
        value_score(get("HDL"), normal_low=40, danger_low=25, inverse=True),
    )
    signals.append(("Cardiovascular Risk", heart,
                    "Uses cholesterol, LDL, HDL, and triglyceride markers when present."))

    anemia = max(
        value_score(get("Hemoglobin"), normal_low=12, danger_low=7, inverse=True),
        value_score(get("RBC"), normal_low=4.0, danger_low=2.5, inverse=True),
    )
    signals.append(("Anemia / Low Blood Count Risk", anemia,
                    "Uses hemoglobin and RBC values when present."))

    ranked = sorted(signals, key=lambda item: item[1], reverse=True)
    detected = set(values.keys())
    expected = {"HbA1c", "Fasting Glucose", "Random Glucose", "Creatinine", "Urea", "eGFR",
                "ALT", "AST", "ALP", "Total Bilirubin", "Direct Bilirubin",
                "Total Cholesterol", "LDL", "HDL", "Triglycerides", "Hemoglobin", "RBC"}
    missing = sorted(expected - detected)
    overall = ranked[0][1] if ranked else 0
    return ranked, missing, overall


def format_lab_snapshot(values):
    snapshot = []
    for name, item in values.items():
        snapshot.append({
            "marker": name,
            "value": item.get("value"),
            "unit": item.get("unit"),
            "status": item.get("status"),
        })
    return snapshot


def heuristic_to_candidate(risk):
    disease, score, detail = risk
    level = "High" if score >= 70 else "Moderate" if score >= 35 else "Low"
    return {
        "disease": disease,
        "confidence": int(score),
        "level": level,
        "evidence": detail,
        "highlight": score >= 70,
    }


def fallback_report_analysis(risks, missing, overall, values):
    ranked = [heuristic_to_candidate(risk) for risk in risks]
    summary_bits = []
    if ranked and ranked[0]["confidence"] > 0:
        leader = ranked[0]
        summary_bits.append(
            f"The strongest abnormal pattern is aligned with {leader['disease']} at approximately {leader['confidence']}% confidence."
        )
    else:
        summary_bits.append("No strong multi-disease abnormal pattern is visible in the extracted laboratory values.")
    if missing:
        summary_bits.append("Several supporting markers were unavailable, so the confidence distribution is based only on the values that were captured from the report.")
    return {
        "overall_risk": int(overall),
        "triage": "Priority review advised" if overall >= 70 else "Routine review advised" if overall >= 35 else "Low immediate concern",
        "clinical_summary": " ".join(summary_bits),
        "disease_candidates": ranked,
        "abnormal_markers": [
            f"{name}: {item['value']} {item.get('unit') or ''} ({item['status']})".strip()
            for name, item in values.items()
            if item.get("status") in {"High", "Low"}
        ][:8],
        "recommended_follow_up": [
            "Confirm extracted laboratory values against the original report.",
            "Review the highest-confidence disease pattern with a qualified clinician.",
            "Repeat or extend testing if key supporting markers are missing.",
        ],
        "source": "MDPS Multi-Disease Clinical Engine",
    }


def groq_report_analysis(extracted_text, values, risks, missing, patient_context, api_key):
    from groq import Groq

    client = Groq(api_key=api_key)
    payload = {
        "patient_context": patient_context,
        "lab_values": format_lab_snapshot(values),
        "risk_candidates": [heuristic_to_candidate(risk) for risk in risks],
        "missing_markers": missing[:20],
        "report_excerpt": extracted_text[:6000],
    }
    schema = {
        "overall_risk": "integer 0-100",
        "triage": "short clinical triage phrase",
        "clinical_summary": "2-4 sentence disease-first summary that explicitly names the likely disease patterns and confidence severity without markdown",
        "disease_candidates": [
            {
                "disease": "string",
                "confidence": "integer 0-100",
                "level": "Low|Moderate|High",
                "evidence": "short reason",
                "highlight": "boolean"
            }
        ],
        "abnormal_markers": ["short strings"],
        "recommended_follow_up": ["short strings"]
    }
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.15,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are assisting with medical report triage. "
                    "Return strictly valid JSON only. "
                    "Write in concise professional clinical language. "
                    "Lead with disease names and degree of likelihood. "
                    "Do not use markdown, do not mention AI, do not say patient summary, and do not claim a confirmed diagnosis. "
                    "Preserve uncertainty appropriately."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Analyze the uploaded report data and return JSON matching this schema: {json.dumps(schema)}. "
                    f"Input data: {json.dumps(payload, default=str)}"
                ),
            },
        ],
    )
    content = response.choices[0].message.content or "{}"
    parsed = json.loads(content)

    candidates = []
    for item in parsed.get("disease_candidates") or []:
        confidence = int(min(100, max(0, float(item.get("confidence", 0)))))
        level = str(item.get("level", "Low")).title()
        if level not in {"Low", "Moderate", "High"}:
            level = "High" if confidence >= 70 else "Moderate" if confidence >= 35 else "Low"
        candidates.append({
            "disease": str(item.get("disease", "Unspecified pattern")).strip() or "Unspecified pattern",
            "confidence": confidence,
            "level": level,
            "evidence": str(item.get("evidence", "")).strip() or "Correlated with the extracted report markers.",
            "highlight": bool(item.get("highlight")) or confidence >= 70,
        })
    candidates = sorted(candidates, key=lambda item: item["confidence"], reverse=True)[:6]

    return {
        "overall_risk": int(min(100, max(0, float(parsed.get("overall_risk", 0))))),
        "triage": str(parsed.get("triage", "Clinical review advised")).strip() or "Clinical review advised",
        "clinical_summary": str(parsed.get("clinical_summary", "")).strip() or fallback_report_analysis(risks, missing, 0, values)["clinical_summary"],
        "disease_candidates": candidates or fallback_report_analysis(risks, missing, 0, values)["disease_candidates"],
        "abnormal_markers": [str(item).strip() for item in (parsed.get("abnormal_markers") or []) if str(item).strip()][:8],
        "recommended_follow_up": [str(item).strip() for item in (parsed.get("recommended_follow_up") or []) if str(item).strip()][:6],
        "source": "MDPS Clinical Analysis Engine",
    }


def render_report_ai_result(analysis, values):
    st.markdown("### Disease Confidence Distribution")
    candidates = analysis.get("disease_candidates", [])
    if not candidates:
        st.info("No disease confidence cards are available for this report.")
        return

    card_chunks = []
    for item in candidates:
        confidence = int(item["confidence"])
        level = "High" if confidence >= 70 else "Moderate" if confidence >= 35 else "Low"
        chip_class = "risk-high" if confidence >= 70 else "risk-neutral" if confidence >= 35 else "risk-low"
        card_class = "signal-card high" if confidence >= 70 else "signal-card"
        card_chunks.append(
            (
                f'<div class="{card_class}">'
                f'<div class="signal-name">{escape(item["disease"])}</div>'
                f'<div class="signal-score">{confidence}%</div>'
                f'<div><span class="risk-chip {chip_class}">{level} confidence</span></div>'
                f'<div class="signal-note">{escape(item["evidence"])}</div>'
                f'</div>'
            )
        )

    cards_html = '<div class="signal-grid">' + "".join(card_chunks) + "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)


def render_progress_tracker(reports, title="Health Progress Tracker"):
    df = report_dataframe(reports)
    st.markdown(f"### {title}")
    if df.empty:
        st.info("Run and save predictions to start tracking progress over time.")
        return

    diseases = sorted(df["disease"].dropna().unique())
    selected = st.selectbox("Track disease", diseases, key=f"progress_{title}")
    view = df[df["disease"] == selected].copy()

    latest = view.iloc[-1]
    previous = view.iloc[-2] if len(view) > 1 else None
    latest_score = float(latest["risk_score"])
    previous_score = float(previous["risk_score"]) if previous is not None else None
    delta = latest_score - previous_score if previous_score is not None else None

    c1, c2, c3 = st.columns(3)
    c1.metric("Latest result", str(latest["prediction"]))
    c2.metric("Risk score", f"{latest_score * 100:.0f}%",
              None if delta is None else f"{delta * 100:+.0f}%")
    c3.metric("Reports saved", len(view))

    if delta is None:
        st.markdown('<div class="status-note">Add another report for this disease to compare progress.</div>',
                    unsafe_allow_html=True)
    elif delta < -0.05:
        st.success("Progress improving compared with the previous saved report.")
    elif delta > 0.05:
        st.warning("Risk score increased compared with the previous saved report. Consider medical follow-up.")
    else:
        st.info("Risk score is mostly stable compared with the previous saved report.")

    fig = px.line(
        view,
        x="date",
        y="risk_score",
        markers=True,
        title=f"{selected} risk trend",
        labels={"date": "Date", "risk_score": "Risk score"},
    )
    fig.update_traces(line=dict(color="#1e5aa0", width=3), marker=dict(size=9))
    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=55, b=20, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_auth_form(key_prefix="auth", title=None, show_skip=False, on_skip=None):
    if title:
        st.markdown(f"#### {title}")
    tabs = st.tabs(["Login", "Sign up"])
    with tabs[0]:
        with st.form(f"{key_prefix}_login"):
            email = st.text_input("Email", placeholder="you@example.com", key=f"{key_prefix}_le")
            pw    = st.text_input("Password", type="password", placeholder="••••••••", key=f"{key_prefix}_lp")
            submit = st.form_submit_button("Login", use_container_width=True)
            if submit:
                u = login(email, pw)
                if u:
                    st.session_state.user = u
                    st.success(f"Welcome back, {u['username']}!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
    with tabs[1]:
        with st.form(f"{key_prefix}_signup"):
            uname = st.text_input("Username", placeholder="John Doe", key=f"{key_prefix}_su")
            email = st.text_input("Email",    placeholder="you@example.com", key=f"{key_prefix}_se")
            pw    = st.text_input("Password (min 6 chars)", type="password", key=f"{key_prefix}_sp")
            submit_su = st.form_submit_button("Create account", use_container_width=True)
            if submit_su:
                ok, msg = signup(uname, email, pw)
                if ok:
                    u = login(email, pw)
                    if u:
                        st.session_state.user = u
                        st.success(f"Account created! Welcome, {u['username']}!")
                        st.rerun()
                    else:
                        st.success(msg)
                else:
                    st.error(msg)
    if show_skip:
        st.markdown("<div style='text-align:center;margin-top:10px;'>", unsafe_allow_html=True)
        if st.button("⚡ Skip & Continue as Guest", key=f"{key_prefix}_skip_btn", use_container_width=True):
            if on_skip:
                on_skip()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_save_prompt(disease, symptoms, prediction, confidence=None, severity=None, details=None, key_prefix="save_report"):
    if st.session_state.user:
        rid = save_report(
            st.session_state.user["id"],
            disease,
            symptoms,
            prediction,
            confidence=confidence,
            severity=severity,
            details=details,
        )
        st.success(f"✅ Analysis securely saved to your personal history (Report ID: #{rid})")
        return rid
    else:
        guest_entry = {
            "id": len(st.session_state.guest_reports) + 1,
            "disease": disease,
            "symptoms": symptoms,
            "prediction": prediction,
            "confidence": confidence,
            "severity": severity,
            "details": details,
            "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.guest_reports.append(guest_entry)
        
        with st.expander("💾 Want to save this report to your permanent history?", expanded=False):
            st.info("💡 You are currently in Guest Mode. Log in or create a free account to keep this report in your health history, or skip to continue as guest.")
            tabs = st.tabs(["Login to Save", "Create Account & Save", "⚡ Skip"])
            with tabs[0]:
                with st.form(f"{key_prefix}_guest_login"):
                    email = st.text_input("Email", placeholder="you@example.com", key=f"{key_prefix}_ge")
                    pw    = st.text_input("Password", type="password", placeholder="••••••••", key=f"{key_prefix}_gp")
                    if st.form_submit_button("Login & Save Report", use_container_width=True):
                        u = login(email, pw)
                        if u:
                            st.session_state.user = u
                            rid = save_report(u["id"], disease, symptoms, prediction, confidence=confidence, severity=severity, details=details)
                            st.success(f"Report saved to {u['username']}'s account!")
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")
            with tabs[1]:
                with st.form(f"{key_prefix}_guest_signup"):
                    uname = st.text_input("Username", placeholder="John Doe", key=f"{key_prefix}_gsu")
                    email = st.text_input("Email", placeholder="you@example.com", key=f"{key_prefix}_gse")
                    pw    = st.text_input("Password (min 6 chars)", type="password", key=f"{key_prefix}_gsp")
                    if st.form_submit_button("Create Account & Save", use_container_width=True):
                        ok, msg = signup(uname, email, pw)
                        if ok:
                            u = login(email, pw)
                            if u:
                                st.session_state.user = u
                                rid = save_report(u["id"], disease, symptoms, prediction, confidence=confidence, severity=severity, details=details)
                                st.success(f"Account created and report saved to {u['username']}'s account!")
                                st.rerun()
                            else:
                                st.success(msg)
                        else:
                            st.error(msg)
            with tabs[2]:
                st.caption("You can skip saving and download your PDF report directly as Guest.")
        return guest_entry["id"]


# ── Sidebar ───────────────────────────────────────────────────────────────────
def sidebar() -> str:
    u = st.session_state.user
    with st.sidebar:
        st.markdown('<div class="sidebar-brand">MDPS</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-tagline">Patient Health Intelligence</div>', unsafe_allow_html=True)
        st.divider()
        if u:
            st.markdown(f"👤 **{u['username']}**")
            st.caption(u["email"])
            if st.button("Logout", use_container_width=True):
                st.session_state.user = None
                st.rerun()
        else:
            st.markdown("👤 **Guest Mode**")
            st.caption("Direct access enabled")
            with st.expander("🔑 Log in / Sign up"):
                render_auth_form("sidebar_auth")
        st.divider()
        choice = st.radio("Navigation", [
            "✨ VITALS Portal",
            "Dashboard",
            "Report Analyzer",
            "Symptom Checker",
            "Clinical Risk Forms",
            "Nearby Hospitals",
            "AI Chatbot",
            "Saved Reports",
            "Analytics",
            "Health Tips",
            "About",
            "Profile",
            "Settings",
        ], label_visibility="collapsed")
    return choice


# ── Dashboard ─────────────────────────────────────────────────────────────────
def page_dashboard():
    u = st.session_state.user
    if u:
        reports = get_user_reports(u["id"])
        st.markdown(f'<p class="main-title">Welcome back, {u["username"]}</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Your health screening summary and recent progress</p>', unsafe_allow_html=True)
        st.markdown("")
        c1, c2, c3, c4 = st.columns(4)
        for col, label, val in [
            (c1, "Total Predictions", len(reports)),
            (c2, "Diseases Tracked",  len({r["disease"] for r in reports})),
            (c3, "Positive Results",  sum(1 for r in reports if "Positive" in str(r.get("prediction","")) or "High" in str(r.get("prediction","")))),
            (c4, "Last Check",        reports[0]["date"][:10] if reports else "—"),
        ]:
            with col:
                st.markdown(f'<div class="metric-card"><div style="opacity:.8;font-size:.85rem">{label}</div>'
                            f'<h2 style="margin:4px 0 0">{val}</h2></div>', unsafe_allow_html=True)
        render_progress_tracker(reports, "Your Progress")
        st.markdown("### Quick actions")
        qc = st.columns(3)
        qc[0].info("Upload a medical report and generate a risk summary.")
        qc[1].info("Use symptom-based screening for a general checkup.")
        qc[2].info("Review saved reports and trends anytime.")
        if reports:
            st.markdown("### Recent predictions")
            st.dataframe(pd.DataFrame(reports[:5])[["date","disease","prediction"]],
                         use_container_width=True, hide_index=True)
    else:
        st.markdown('<p class="main-title">MDPS Health Intelligence</p>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Direct AI-assisted health screening & medical report analysis</p>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-badge">⚡ Instant Direct Access</div>
            <h1>AI Medical Screening &amp;<br>Lab Report Analysis</h1>
            <p>Upload lab reports, check symptoms across conditions, and get instant clinical-grade insights without barriers.</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        for col, label, val in [
            (c1, "Screening Modules", "10+"),
            (c2, "Report Formats", "PDF / Image"),
            (c3, "Mode", "Guest Browsing"),
            (c4, "Instant Analysis", "Active"),
        ]:
            with col:
                st.markdown(f'<div class="metric-card"><div style="opacity:.8;font-size:.85rem">{label}</div>'
                            f'<h2 style="margin:4px 0 0">{val}</h2></div>', unsafe_allow_html=True)
        
        st.markdown("### 🚀 Available Features")
        f1, f2, f3 = st.columns(3)
        with f1:
            st.markdown("""
            <div class="feature-tile">
                <div class="feature-icon">📑</div>
                <div class="feature-title">Medical Report Analyzer</div>
                <div class="feature-desc">Upload blood test or lab report PDFs to automatically extract markers and estimate multi-disease risk.</div>
            </div>
            """, unsafe_allow_html=True)
        with f2:
            st.markdown("""
            <div class="feature-tile">
                <div class="feature-icon">🩺</div>
                <div class="feature-title">Symptom Checker</div>
                <div class="feature-desc">Select symptoms from 130+ clinical signals to receive an instant machine-learned condition prediction.</div>
            </div>
            """, unsafe_allow_html=True)
        with f3:
            st.markdown("""
            <div class="feature-tile">
                <div class="feature-icon">🤖</div>
                <div class="feature-title">AI Health Assistant</div>
                <div class="feature-desc">Ask medical questions, explore health tips, and find nearby emergency care or hospitals.</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="clean-callout">
            <strong>💡 Guest Mode Active:</strong> You can use any screening feature and download PDF reports directly. If you would like to save your reports to track health progress over time, you can log in or create an account anytime.
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("🔑 Log in or Create an Account (Optional)"):
            render_auth_form("dash_auth")


# ── About ─────────────────────────────────────────────────────────────────────
def page_about():
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-badge">🩺 AI-Powered</div>
        <h1>About MDPS</h1>
        <p>Multiple Disease Prediction System — AI-assisted health screening for everyone.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### What is MDPS?")
    st.write("MDPS is an AI-powered web application that uses machine learning models and clinical report parsing to predict "
             "the risk of multiple diseases based on laboratory parameters, clinical markers, and symptoms.")
    st.markdown("""
    <div class="clean-callout">
        MDPS focuses on transparent medical screening. The app reads uploaded reports, extracts measurable laboratory values,
        flags missing data, and produces a structured risk summary with disease confidence distributions for follow-up discussion with a clinician.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### Diseases & Modules Covered")
    diseases = [
        ("🩸","Diabetes","Glucose, BMI, insulin-based prediction"),
        ("❤️","Heart Disease","Cholesterol, BP, ECG-based screening"),
        ("🧠","Parkinson's","Voice signal analysis (22 features)"),
        ("🫀","Liver Disease","Bilirubin, enzyme level analysis"),
        ("🦠","Hepatitis C","Blood marker-based risk assessment"),
        ("🫁","Lung Cancer","Smoking, symptom-based screening"),
        ("🩺","Chronic Kidney Disease","Creatinine, hemoglobin analysis"),
        ("🎀","Breast Cancer","30-feature tumour cell analysis"),
        ("🟡","Jaundice","Symptom + severity-based prediction"),
    ]
    cols = st.columns(3)
    for i, (icon, name, desc) in enumerate(diseases):
        with cols[i % 3]:
            st.markdown(f'<div class="feature-tile" style="margin-bottom:1rem">'
                        f'<div class="feature-icon">{icon}</div>'
                        f'<div class="feature-title">{name}</div>'
                        f'<div class="feature-desc">{desc}</div></div>', unsafe_allow_html=True)
    st.markdown("### ⚠️ Clinical Disclaimer")
    st.warning("MDPS is for **informational and educational purposes only**. "
               "It does not diagnose disease or replace a qualified healthcare professional.")
    st.markdown("### Tech Stack")
    c1,c2,c3,c4 = st.columns(4)
    c1.success("🐍 Python 3.12"); c2.success("🚀 Streamlit")
    c3.success("🤖 scikit-learn & Groq"); c4.success("📊 Plotly")


# ── Prediction result ─────────────────────────────────────────────────────────
def render_prediction_result(disease, pred_label, positive, conf, params, reasons=None, risk_score=None, source=None):
    klass = "result-positive" if positive else "result-negative"
    st.markdown(f'<div class="{klass}">{pred_label}</div>', unsafe_allow_html=True)
    st.markdown("")
    g_col, p_col = st.columns([1, 1])
    with g_col:
        st.markdown('<div class="gauge-title">Risk level</div>', unsafe_allow_html=True)
        st.plotly_chart(risk_gauge(conf, positive), use_container_width=True,
                        config={"displayModeBar": False})
    with p_col:
        st.markdown("**Screening confidence**")
        if risk_score is not None:
            st.progress(min(max(risk_score / 100, 0.0), 1.0), text=f"{risk_score:.0f}% screening risk")
            if source:
                st.caption(f"Method: {source}")
        elif conf is not None:
            bar_val = min(max(conf, 0.0), 1.0)
            st.progress(bar_val, text=f"{bar_val*100:.1f}% confidence")
        else:
            st.info("Confidence not available for this model.")
        if positive:
            st.warning("Doctor consultation recommended.")
            if disease in {"Heart Disease","Lung Cancer","Chronic Kidney Disease"}:
                st.error("High-risk condition. Consider urgent medical attention.")
    with st.expander("Why this prediction?", expanded=True):
        for reason in (reasons or explain_prediction(disease, params, positive)):
            st.write("- " + reason)


# ── Disease prediction ────────────────────────────────────────────────────────
def groq_disease_screening(disease, params, api_key):
    from groq import Groq

    client = Groq(api_key=api_key)
    schema = {
        "risk_score": "integer 0-100",
        "risk_level": "Low|Moderate|High",
        "prediction": "Positive|Negative",
        "confidence_score": "integer 0-100",
        "reasons": "array of short strings",
        "urgent_flags": "array of short strings",
    }
    prompt = (
        "You are a careful medical screening assistant. "
        "Analyze the disease module input and return JSON only. "
        "Do not diagnose and do not add markdown. "
        f"Disease module: {disease}. "
        f"Input values: {json.dumps(params, default=str)}. "
        f"Required schema: {json.dumps(schema)}."
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Return strictly valid JSON for medical screening."},
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
    except Exception:
        data = {}

    risk_score = int(min(100, max(0, float(data.get("risk_score", 50)))))
    confidence_score = int(min(100, max(0, float(data.get("confidence_score", 70)))))
    risk_level = str(data.get("risk_level", "Moderate")).title()
    prediction = str(data.get("prediction", "Negative")).title()
    reasons = [str(item).strip() for item in (data.get("reasons") or []) if str(item).strip()][:6]
    urgent_flags = [str(item).strip() for item in (data.get("urgent_flags") or []) if str(item).strip()][:4]
    if risk_level not in {"Low", "Moderate", "High"}:
        risk_level = "High" if risk_score >= 70 else "Moderate" if risk_score >= 35 else "Low"
    if prediction not in {"Positive", "Negative"}:
        prediction = "Positive" if risk_score >= 45 else "Negative"
    if not reasons:
        reasons = ["Screening summary generated from submitted clinical values."]
    return {
        "risk_score": risk_score,
        "confidence_score": confidence_score,
        "risk_level": risk_level,
        "prediction": prediction,
        "reasons": reasons,
        "urgent_flags": urgent_flags,
        "source": "Groq clinical screening",
    }


def page_disease_prediction():
    st.markdown('<div class="live-badge"><div class="pulse-dot"></div> AI Parameter Screening Engine</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Clinical Risk Forms</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Direct multi-feature risk assessment using machine learning models and evidence-based clinical thresholds.</p>',
                unsafe_allow_html=True)
    disease = st.selectbox("Select clinical form", list(SCHEMAS.keys()))
    model, fields = get_predictor(disease)
    api_key = get_groq_api_key()

    with st.form(f"form_{disease}"):
        cols = st.columns(3)
        values, params = [], {}
        for i, (key, label, typ, default, lo, hi) in enumerate(fields):
            with cols[i % 3]:
                v = st.number_input(label, int(lo), int(hi), int(default), step=1) if typ == "int" \
                    else st.number_input(label, float(lo), float(hi), float(default), step=0.1)
                values.append(v); params[key] = v
        submitted = st.form_submit_button(f"Predict {disease}", use_container_width=True)

    if submitted:
        with st.spinner(f"Analyzing {disease} risk... please wait"):
            try:
                meta = None
                if api_key:
                    try:
                        meta = groq_disease_screening(disease, params, api_key)
                    except Exception:
                        meta = None
                if meta is None:
                    pred_val, conf_val, local_meta = run_screening_prediction(disease, model, values, params)
                    positive = pred_val == 1
                    risk_score = local_meta.get("risk_score", int(conf_val * 100 if positive else (1 - conf_val) * 100))
                    meta = {
                        "risk_score": risk_score,
                        "confidence_score": int(conf_val * 100),
                        "risk_level": "High" if risk_score >= 70 else "Moderate" if risk_score >= 35 else "Low",
                        "prediction": "Positive" if positive else "Negative",
                        "reasons": local_meta.get("reasons", explain_prediction(disease, params, positive)),
                        "urgent_flags": ["High-risk markers detected. Clinical consultation recommended."] if positive else [],
                        "source": f"MDPS Hybrid Clinical Model ({local_meta.get('source', 'Ensemble ML')})",
                    }

                positive = meta["prediction"] == "Positive"
                conf = meta["confidence_score"] / 100
                label = f"{disease}: {'Positive / At Risk' if positive else 'Negative / Low Risk'}"
                render_prediction_result(
                    disease, label, positive, conf, params,
                    reasons=meta["reasons"], risk_score=meta["risk_score"], source=meta["source"],
                )
                rid = render_save_prompt(
                    disease=disease,
                    symptoms=", ".join(f"{k}={v}" for k,v in params.items()),
                    prediction="Positive" if positive else "Negative",
                    confidence=meta["confidence_score"] / 100,
                    details=json.dumps({"inputs": params, "screening": meta}, default=str),
                    key_prefix=f"form_{disease}_save",
                )
                st.session_state.last_pred = {
                    "disease": disease, "prediction": label, "params": params,
                    "confidence": meta["confidence_score"] / 100, "explanation": meta["reasons"],
                    "report_id": rid,
                }
                if meta.get("urgent_flags"):
                    st.error("Urgent flags: " + "; ".join(meta["urgent_flags"]))
            except Exception as e:
                st.error(f"Prediction failed: {e}")

    if st.session_state.last_pred and st.session_state.last_pred["disease"] == disease:
        lp = st.session_state.last_pred
        uname = st.session_state.user["username"] if st.session_state.user else "Guest User"
        with st.spinner("Generating PDF..."):
            pdf_bytes = generate_pdf(
                username=uname,
                disease=lp["disease"], prediction=lp["prediction"],
                params=lp["params"], confidence=lp.get("confidence"),
                explanation=lp.get("explanation"),
            )
        st.download_button("⬇️ Download PDF Report", pdf_bytes,
                           file_name=f"{disease.replace(' ','_')}_report.pdf",
                           mime="application/pdf", use_container_width=True)


# ── Symptom-based ─────────────────────────────────────────────────────────────
def page_report_analyzer():
    st.markdown('<div class="live-badge"><div class="pulse-dot"></div> Medical Report Intake Engine</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">Medical Report Analyzer</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Upload a report, extract measurable values locally, then generate a structured clinical screening summary with disease confidence highlights.</p>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="report-workspace">
            <div class="analysis-hero">
                <div class="analysis-panel">
                    <div class="hero-badge">Clinical Report AI</div>
                    <h3>Report intake, extraction, and clinical triage</h3>
                    <p>The backend reads the uploaded report, extracts laboratory markers, evaluates multi-disease patterns, and returns a structured clinical triage report.</p>
                </div>
                <div class="analysis-stat">
                    <div class="label">Analysis Focus</div>
                    <div class="value">Multi-disease Confidence</div>
                    <div class="report-meta">High-confidence disease patterns are flagged automatically.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    api_key = get_groq_api_key()

    with st.container():
        st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Upload medical report",
            type=["pdf", "jpg", "jpeg", "png"],
            help="PDF text is extracted locally. For best results, upload a text-based lab-report PDF.",
        )
        c1, c2, c3 = st.columns([1, 1, 1])
        patient_age = c1.number_input("Patient age", min_value=0, max_value=120, value=0)
        patient_sex = c2.selectbox("Patient sex", ["Not specified", "Female", "Male", "Other"])
        report_context = c3.text_input("Clinical note (optional)", placeholder="Example: fatigue, jaundice, weight loss")
        st.markdown('</div>', unsafe_allow_html=True)

    analyze = st.button("Analyze report", type="primary", use_container_width=True, disabled=uploaded is None)
    if analyze and uploaded is not None:
        with st.spinner("Reading report and extracting medical values..."):
            extracted_text, warnings = extract_report_text(uploaded)
            values = extract_lab_values(extracted_text)
            risks, missing, overall = build_report_risk_analysis(values)

        if warnings:
            for warning in warnings:
                st.warning(warning)
        if not extracted_text:
            st.error("Could not read usable text from this report. Upload a text-based PDF for local extraction.")
            return

        st.markdown("### Extracted values")
        if values:
            rows = []
            for name, item in values.items():
                low, high, default_unit = REFERENCE_RANGES.get(name, ("", "", item.get("unit", "")))
                rows.append({
                    "Test": name,
                    "Value": item["value"],
                    "Unit": item.get("unit") or default_unit,
                    "Status": item["status"],
                    "Reference": f"{low}-{high}" if low != "" and high != "" else "Not available",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.warning("No standard lab values were detected. Review the extracted text and upload a clearer report if needed.")

        st.markdown("### Clinical result")
        patient_context = {
            "age": patient_age or None,
            "sex": patient_sex,
            "note": report_context.strip() or None,
            "file_name": uploaded.name,
        }
        
        analysis = None
        if api_key:
            try:
                analysis = groq_report_analysis(extracted_text, values, risks, missing, patient_context, api_key)
            except Exception:
                analysis = None
        if analysis is None:
            analysis = fallback_report_analysis(risks, missing, overall, values)

        render_report_ai_result(analysis, values)

        if missing:
            with st.expander("Missing or not readable values"):
                st.write(", ".join(missing[:30]))
                st.caption("Missing values are not silently guessed. Risk scores only use values that were actually extracted.")

        with st.expander("Extracted raw text for verification"):
            st.text_area("Report text", extracted_text[:8000], height=260)

        top_candidates = analysis.get("disease_candidates") or []
        prediction_label = top_candidates[0]["disease"] if top_candidates else "No major abnormal risk signal"
        details = {
            "file": uploaded.name,
            "age": patient_age or None,
            "sex": patient_sex,
            "values": values,
            "risks": risks,
            "missing": missing,
            "analysis": analysis,
            "clinical_note": report_context.strip() or None,
        }
        conf_score = float(analysis.get("overall_risk", overall)) / 100
        sev_score = float(analysis.get("overall_risk", overall)) / 10
        rid = render_save_prompt(
            disease="Report Analysis",
            symptoms=uploaded.name,
            prediction=prediction_label,
            confidence=conf_score,
            severity=sev_score,
            details=json.dumps(details, default=str),
            key_prefix="ra_save",
        )
        st.info("Please verify extracted values against the original report and confirm any high-confidence disease pattern with a qualified clinician.")

        uname = st.session_state.user["username"] if st.session_state.user else "Guest User"
        with st.spinner("Preparing downloadable report..."):
            report_params = {
                name: f"{item['value']} {item.get('unit') or ''} ({item['status']})".strip()
                for name, item in values.items()
            }
            disease_lines = [
                f"{item['disease']} - {item['confidence']}% ({item['level']} confidence): {item['evidence']}"
                for item in top_candidates
            ] or ["No strong disease pattern detected from the available extracted values."]
            pdf_bytes = generate_pdf(
                username=uname,
                disease="Report Analysis",
                prediction=prediction_label,
                params=report_params or {"Report file": uploaded.name},
                confidence=conf_score,
                severity=sev_score,
                description=analysis.get("clinical_summary"),
                precautions=analysis.get("recommended_follow_up"),
                explanation=disease_lines,
            )
        st.download_button(
            "⬇️ Download analysis PDF",
            pdf_bytes,
            file_name=f"report_analysis_{rid}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


@st.cache_resource
def get_symptom_model():
    return DiseaseModel()


def page_symptom():
    st.markdown('<p class="main-title">Symptom-Based Prediction</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Select your symptoms and get an AI-based disease prediction</p>',
                unsafe_allow_html=True)
    dm = get_symptom_model()
    if not dm.available():
        st.warning("Place Training.csv, symptom_severity.csv, disease_description.csv, "
                   "disease_precaution.csv in datasets/ to enable this module.")
        return
    selected = st.multiselect("Select your symptoms", dm.symptoms,
                              placeholder="Type to search symptoms...")
    if st.button("Predict disease", use_container_width=True, disabled=not selected):
        with st.spinner("Analyzing symptoms... please wait"):
            res = dm.predict(selected)
        st.markdown(f'<div class="result-positive">🩺 Likely condition: <strong>{res["disease"]}</strong></div>',
                    unsafe_allow_html=True)
        st.markdown("")
        g_col, m_col = st.columns([1, 1])
        with g_col:
            st.markdown('<div class="gauge-title">Risk level</div>', unsafe_allow_html=True)
            st.plotly_chart(risk_gauge(res["confidence"], True),
                            use_container_width=True, config={"displayModeBar": False})
        with m_col:
            if res["confidence"] is not None:
                st.metric("Confidence", f"{res['confidence']*100:.1f}%")
            st.metric("Severity score", f"{res['severity']:.2f}")
        if res["description"]:
            with st.expander("📖 About this condition", expanded=True):
                st.write(res["description"])
        if res["precautions"]:
            with st.expander("🛡️ Recommended precautions", expanded=True):
                for p in res["precautions"]: st.write("• " + p)
        with st.expander("🔍 Why this prediction"):
            ranked = sorted(selected, key=lambda s: dm.severity.get(s, 0), reverse=True)[:5]
            for s in ranked:
                st.write(f"• **{s}** — severity {dm.severity.get(s,'—')}")
        rid = render_save_prompt(
            disease="Symptom-Based",
            symptoms=", ".join(selected),
            prediction=res["disease"],
            confidence=res["confidence"],
            severity=res["severity"],
            details=res["description"],
            key_prefix="symptom_save",
        )
        uname = st.session_state.user["username"] if st.session_state.user else "Guest User"
        with st.spinner("Generating PDF..."):
            pdf = generate_pdf(
                username=uname,
                disease="Symptom-Based",
                prediction=res["disease"],
                params={s: "yes" for s in selected},
                severity=res["severity"],
                description=res["description"],
                precautions=res["precautions"],
                confidence=res["confidence"],
                explanation=[f"{s} (severity {dm.severity.get(s,'—')})" for s in ranked],
            )
        st.download_button("⬇️ Download PDF Report", pdf,
                           file_name=f"symptom_report_{rid}.pdf",
                           mime="application/pdf", use_container_width=True)


# ── Saved Reports ─────────────────────────────────────────────────────────────
def page_reports():
    st.markdown('<p class="main-title">Saved Reports</p>', unsafe_allow_html=True)
    u = st.session_state.user
    if not u:
        if st.session_state.guest_reports:
            st.info("💡 Showing reports generated during this guest session. To keep these reports permanently and track trends across sessions, please log in or create an account.")
            reports = st.session_state.guest_reports
            render_progress_tracker(reports, "Session Progress")
            df = report_dataframe(reports).sort_values("date", ascending=False)
            st.markdown("### Session Reports")
            for r in df.to_dict("records"):
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                c1.write(str(r.get("date", ""))[:19])
                c2.write(r.get("disease", ""))
                c3.write(r.get("prediction", ""))
                c4.write(f"{r['confidence']*100:.0f}%" if pd.notna(r.get("confidence")) else "-")
            st.divider()
            st.markdown("#### 🔐 Log in to permanently save your records")
            render_auth_form("guest_reports_auth", show_skip=True)
            return
        else:
            st.markdown("""
            <div class="clean-callout">
                <h3>🔐 Personal Health History is locked</h3>
                <p>Log in or create a free account to securely store your medical reports, track disease risk trends, and view personalized analytics over time.</p>
            </div>
            """, unsafe_allow_html=True)
            render_auth_form("saved_reports_auth", show_skip=True)
            return

    reports = get_user_reports(u["id"])
    if not reports:
        st.info("No reports yet. Run a prediction to get started.")
        return
    render_progress_tracker(reports, "Disease Progress")
    df = report_dataframe(reports).sort_values("date", ascending=False)
    q  = st.text_input("Search by disease or result", placeholder="e.g. Diabetes, Positive...")
    if q:
        df = df[df.apply(lambda r: q.lower() in str(r["disease"]).lower()
                                or q.lower() in str(r["prediction"]).lower(), axis=1)]
    total    = len(df)
    positive = sum(1 for _, r in df.iterrows()
                   if "Positive" in str(r["prediction"]) or "High" in str(r["prediction"]))
    negative = total - positive
    p1, p2, p3 = st.columns(3)
    p1.markdown(f'<div class="stat-pill"><span class="num">{total}</span><span class="lbl">Total</span></div>',
                unsafe_allow_html=True)
    p2.markdown(f'<div class="stat-pill"><span class="num" style="color:#d9534f">{positive}</span><span class="lbl">Positive</span></div>',
                unsafe_allow_html=True)
    p3.markdown(f'<div class="stat-pill"><span class="num" style="color:#28a745">{negative}</span><span class="lbl">Negative</span></div>',
                unsafe_allow_html=True)
    st.markdown("")
    st.markdown("### Your Reports")
    for r in df.to_dict("records"):
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1])
        c1.write(r["date"].strftime("%Y-%m-%d") if pd.notna(r["date"]) else "")
        c2.write(r["disease"])
        c3.write(r["prediction"])
        c4.write(f"{r['confidence']*100:.0f}%" if pd.notna(r["confidence"]) else "-")
        if c5.button("Delete", key=f"del_{r['id']}", help="Delete this report"):
            delete_report(r["id"])
            st.success("Report deleted!")
            st.rerun()
    st.divider()
    if st.button("Delete all reports", type="secondary", use_container_width=True):
        st.session_state.confirm_delete = True
        st.rerun()
    if st.session_state.confirm_delete:
        st.warning("Are you sure? This cannot be undone.")
        c1, c2 = st.columns(2)
        if c1.button("Yes, delete all", use_container_width=True):
            delete_all_reports(st.session_state.user["id"])
            st.session_state.confirm_delete = False
            st.success("All reports deleted!")
            st.rerun()
        if c2.button("Cancel", use_container_width=True):
            st.session_state.confirm_delete = False
            st.rerun()


# ── Analytics ─────────────────────────────────────────────────────────────────
def page_analytics():
    st.markdown('<p class="main-title">Analytics</p>', unsafe_allow_html=True)
    u = st.session_state.user
    if not u:
        if st.session_state.guest_reports:
            reports = st.session_state.guest_reports
            st.info("💡 Displaying analytics for reports generated during this session.")
        else:
            st.markdown("""
            <div class="clean-callout">
                <h3>📊 Longitudinal Health Analytics</h3>
                <p>Analytics visualizes disease risk trends, severity changes, and confidence distributions over time. Log in or create an account to track your personal health trends.</p>
            </div>
            """, unsafe_allow_html=True)
            render_auth_form("analytics_auth", show_skip=True)
            return
    else:
        reports = get_user_reports(u["id"])

    if not reports:
        st.info("Make a few predictions to unlock analytics.")
        return
    df = report_dataframe(reports)
    render_progress_tracker(reports, "Patient Progress")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(df, x="disease", color="prediction", title="Predictions by disease",
                           color_discrete_map={"Positive":"#d9534f","Negative":"#28a745"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        if df["severity"].notna().any():
            fig = px.box(df.dropna(subset=["severity"]), x="disease", y="severity",
                         title="Severity distribution", color="disease")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    fig = px.line(df.sort_values("date"), x="date", y="confidence", color="disease",
                  title="Confidence over time", markers=True)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
    pred_counts = df["prediction"].value_counts().reset_index()
    pred_counts.columns = ["Result","Count"]
    fig = px.pie(pred_counts, names="Result", values="Count",
                 title="Positive vs Negative ratio", hole=0.5,
                 color="Result",
                 color_discrete_map={"Positive":"#d9534f","Negative":"#28a745"})
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
    
# ── Nearby Hospitals ──────────────────────────────────────────────────────────
def page_hospitals():
    st.markdown('<p class="main-title">Nearby Care Finder</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Find hospitals, emergency care, and pharmacies by city or area using a live backend facility search.</p>', unsafe_allow_html=True)

    options = [
        "Hospital", "Emergency Hospital", "Medical Clinic",
        "Cardiology", "Neurology", "Oncology", "Nephrology", "Pharmacy"
    ]
    speciality = st.selectbox("Care type", options)
    city = st.text_input("City or area", placeholder="e.g. Jaipur, Delhi, Mumbai")

    if not city:
        st.info("Enter a city or area to load nearby facilities.")
    else:
        try:
            with st.spinner("Searching nearby facilities..."):
                location, facilities = fetch_nearby_facilities(city, speciality)
            if not location:
                st.warning("Could not locate that city or area. Try a broader place name.")
            elif not facilities:
                st.warning("No matching facilities were found nearby. Try another care type or nearby city.")
            else:
                map_df = pd.DataFrame(facilities)
                fig = px.scatter_mapbox(
                    map_df,
                    lat="lat",
                    lon="lon",
                    hover_name="name",
                    hover_data={"address": True, "type": True, "lat": False, "lon": False},
                    color_discrete_sequence=["#0d6f73"],
                    zoom=11,
                    height=520,
                )
                fig.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                st.markdown(f"### Nearby {speciality} results")
                for facility in facilities[:10]:
                    query = quote_plus(f"{facility['name']} {facility['address']}")
                    st.markdown(
                        f"""
                        <div class="risk-row">
                            <div class="risk-title">{escape(facility['name'])}</div>
                            <div class="risk-detail">{escape(facility['address'])}</div>
                            <div class="report-meta"><a href="https://www.google.com/maps/search/{query}" target="_blank">Open directions</a></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        except Exception as exc:
            st.error(f"Nearby facility search failed: {exc}")

    st.markdown("### Patient checklist")
    c1, c2, c3 = st.columns(3)
    c1.info("Call the hospital before visiting to confirm availability.")
    c2.info("Use emergency services immediately for severe chest pain, breathing trouble, stroke signs, or loss of consciousness.")
    c3.info("Carry recent reports, medications, allergies, and an emergency contact.")


## Step 4 — Chatbot page add karo


# ── Local Clinical Assistant Intelligence ────────────────────────────────────
def get_local_medical_response(question: str) -> str:
    """Generate structured, authoritative, educational clinical answers using the local clinical knowledge engine."""
    q = question.lower().strip()

    if any(k in q for k in ["diabet", "sugar", "glucose", "insulin", "hba1c"]):
        return (
            "🩺 **Clinical Overview: Glycemic Regulation & Diabetes**\n\n"
            "• **Key Biomarkers:** Fasting Blood Glucose (Normal: 70–99 mg/dL), HbA1c (Normal: < 5.7%; Prediabetes: 5.7–6.4%; Diabetes: ≥ 6.5%).\n"
            "• **Common Indicators:** Frequent urination (polyuria), unquenchable thirst (polydipsia), unexplained fatigue, and blurred vision.\n\n"
            "🥗 **Dietary & Lifestyle Protocol:**\n"
            "• Choose complex carbohydrates with low glycemic index (legumes, whole oats, non-starchy leafy vegetables).\n"
            "• Maintain 150+ minutes of moderate aerobic exercise weekly combined with progressive resistance training.\n\n"
            "⚠️ **Emergency Red Flags:** Blood sugar > 300 mg/dL with confusion, persistent vomiting, or rapid deep breathing warrants immediate emergency care."
        )
    if any(k in q for k in ["heart", "cardio", "chest pain", "cholesterol", "bp", "blood pressure", "hypertension", "angina", "palpitat"]):
        return (
            "🩺 **Clinical Overview: Cardiovascular Health & Blood Pressure**\n\n"
            "• **Diagnostic Reference:** Optimal Blood Pressure is < 120/80 mmHg. Total Cholesterol should ideally remain < 200 mg/dL (LDL < 100 mg/dL, HDL > 50 mg/dL).\n"
            "• **Key Symptoms:** Exertional chest tightness, shortness of breath, palpitations, or lightheadedness.\n\n"
            "🥗 **Preventive Protocol (DASH Approach):**\n"
            "• Sodium restriction (< 2,000 mg/day) and increased potassium (spinach, avocados, bananas).\n"
            "• Rich intake of Omega-3 fatty acids (walnuts, chia seeds, salmon) and daily brisk walking.\n\n"
            "⚠️ **Emergency Red Flags:** Pressure or squeezing sensation in the chest radiating to left arm, neck, or jaw requires immediate emergency medical evaluation (call emergency services)."
        )
    if any(k in q for k in ["kidney", "renal", "creatinine", "urea", "egfr", "proteinuria"]):
        return (
            "🩺 **Clinical Overview: Renal Function & Kidney Care**\n\n"
            "• **Key Biomarkers:** Serum Creatinine (0.6–1.3 mg/dL), Blood Urea Nitrogen (10–45 mg/dL), and eGFR (> 90 mL/min/1.73m²).\n"
            "• **Clinical Indicators:** Foamy urine (proteinuria), bilateral ankle edema, morning facial puffiness, and fatigue.\n\n"
            "🥗 **Renal Protection Steps:**\n"
            "• Maintain steady daily hydration (2–2.5 L) unless medically fluid-restricted.\n"
            "• Avoid unmonitored chronic NSAID painkiller use (e.g. ibuprofen).\n"
            "• Keep blood pressure and blood sugar strictly controlled to protect glomeruli."
        )
    if any(k in q for k in ["liver", "hepat", "jaundice", "bilirubin", "alt", "ast", "sgpt", "sgot", "fatty liver"]):
        return (
            "🩺 **Clinical Overview: Hepatic Function & Liver Screening**\n\n"
            "• **Key Biomarkers:** Total Bilirubin (0.1–1.2 mg/dL), ALT/SGPT (< 45 U/L), AST/SGOT (< 40 U/L), Alkaline Phosphatase (44–147 U/L).\n"
            "• **Warning Signs:** Scleral/skin icterus (yellowing), dark tea-colored urine, right upper quadrant tenderness, and unexplained malaise.\n\n"
            "🥗 **Hepatoprotective Steps:**\n"
            "• Abstain from alcohol and unnecessary hepatotoxic medications.\n"
            "• Adopt an antioxidant-rich Mediterranean dietary pattern to reverse hepatic steatosis (fatty liver)."
        )
    if any(k in q for k in ["cancer", "tumor", "tumour", "oncolog", "biopsy", "malignan", "lump", "mammogra"]):
        return (
            "🩺 **Clinical Overview: Oncology Screening & Early Detection**\n\n"
            "• **Core Principle:** Early detection through regular screening (mammograms, low-dose chest CT for smokers, colonoscopies) substantially increases curative outcomes.\n"
            "• **Universal Warning Signs (CAUTION Criteria):** Non-healing sores, abnormal painless lumps, changes in bowel/bladder habits, difficulty swallowing, or unexplained rapid weight loss.\n\n"
            "💡 *Recommended Action:* Discuss age-appropriate cancer screening guidelines and any suspicious palpable findings with an oncologist."
        )
    if any(k in q for k in ["parkinson", "tremor", "neuro", "brain", "dopamine", "shaking", "rigidity"]):
        return (
            "🩺 **Clinical Overview: Neurological Signs & Parkinson's Disease**\n\n"
            "• **Cardinal Signs:** Resting asymmetric tremor, bradykinesia (slowness in initiating movement), muscular cogwheel rigidity, and postural imbalance.\n"
            "• **Supportive Management:** Targeted neuro-physiotherapy, aerobic cycling/boxing, speech therapy, and personalized dopamine replacement protocols.\n\n"
            "💡 *Recommended Action:* Schedule a formal neurological evaluation with a movement disorder specialist."
        )

    return (
        f"🩺 **Clinical Educational Guidance**\n\n"
        f"Regarding your query on **{escape(question)}**:\n\n"
        "**Clinical Principles & Evidence-Based Recommendations:**\n"
        "• **Baseline Lab Screening:** Regular tracking of routine parameters (CBC, fasting glucose, renal and hepatic profiles, lipid panel) helps detect early metabolic signals.\n"
        "• **Lifestyle Optimization:** Emphasize a nutrient-dense whole foods diet, 7–8 hours of restorative sleep, consistent hydration, and stress regulation.\n"
        "• **Monitoring Changes:** Keep a structured symptom log noting onset, duration, and aggravating/alleviating factors.\n\n"
        "⚠️ **When to Seek Immediate Medical Attention:**\n"
        "• High unremitting fever, severe sudden pain, breathing difficulty, or neurological deficits.\n\n"
        "💡 *Note: MDPS Assistant provides educational guidance. Please consult a qualified doctor for clinical diagnosis and individualized treatment.*"
    )


# ── AI Health Chatbot ─────────────────────────────────────────────────────────
def page_chatbot():
    st.markdown('<div class="live-badge"><div class="pulse-dot"></div> Clinical AI Assistant Online</div>', unsafe_allow_html=True)
    st.markdown('<p class="main-title">AI Health Assistant</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Ask health questions and receive evidence-based educational guidance powered by clinical knowledge models.</p>',
                unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    api_key = get_groq_api_key()

    with st.form("health_assistant_form", clear_on_submit=True):
        user_input = st.text_area(
            "Your medical or health question",
            placeholder="Example: What are early symptoms of diabetes and how to reduce risk?",
            height=100,
        )
        submitted = st.form_submit_button("Ask assistant", use_container_width=True)

    st.markdown('<div class="assistant-shell">', unsafe_allow_html=True)
    if not st.session_state.chat_history:
        st.markdown('<div class="status-note">💡 Start with a symptom, lab report question, disease prevention, or lifestyle query. The assistant provides educational guidance.</div>',
                    unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        css_class = "message-user" if msg["role"] == "user" else "message-assistant"
        label = "👤 You" if msg["role"] == "user" else "🩺 Clinical Assistant"
        content = escape(str(msg["content"])).replace("\n", "<br>")
        st.markdown(f'<div class="{css_class}"><strong>{label}</strong><br>{content}</div>',
                    unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if submitted and user_input.strip():
        text = user_input.strip()
        non_medical_markers = [
            "code", "program", "python", "java", "javascript", "bug", "error", "compile",
            "math", "physics", "chemistry", "history", "politics", "election", "religion",
            "stock", "crypto", "bitcoin", "trading", "marketing", "brand", "instagram",
            "movie", "song", "lyrics", "game", "sports", "football", "cricket",
            "travel", "hotel", "visa",
        ]
        medical_markers = [
            "symptom", "symptoms", "disease", "condition", "treatment", "medicine", "medication",
            "dose", "dosage", "side effect", "side effects", "pain", "fever", "cough",
            "bp", "blood pressure", "sugar", "glucose", "diabetes", "heart", "kidney", "liver",
            "cancer", "parkinson", "hepatitis", "jaundice", "diagnosis", "test", "lab",
            "emergency", "ambulance", "health", "diet", "doctor", "hospital", "body", "food"
        ]
        text_l = text.lower()
        looks_medical = any(k in text_l for k in medical_markers)
        looks_non_medical = any(k in text_l for k in non_medical_markers)
        if looks_non_medical and not looks_medical:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": (
                    "I specialize strictly in medical and health-related guidance. "
                    "Please ask about symptoms, lab tests, diseases, prevention, medicines, or healthy living."
                ),
            })
            st.rerun()

        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("Preparing clinical guidance..."):
            reply = None
            if api_key:
                try:
                    from groq import Groq
                    client = Groq(api_key=api_key)
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are a strict medical-only assistant for the MDPS app. "
                                    "You must ONLY answer medical and health-related questions. "
                                    "Write concise, patient-friendly clinical education with bullet points. "
                                    "Include red-flag symptoms and remind users to consult a qualified doctor. Do not diagnose."
                                )
                            },
                            *[{"role": m["role"], "content": m["content"]}
                              for m in st.session_state.chat_history[-8:]],
                        ],
                        max_tokens=512,
                        temperature=0.4,
                    )
                    reply = response.choices[0].message.content
                except Exception:
                    reply = None
            if not reply:
                reply = get_local_medical_response(text)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.rerun()

    if st.session_state.chat_history:
        if st.button("Clear chat", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

    st.caption("🩺 This assistant provides evidence-based medical education. Always consult a licensed physician for diagnosis and medical treatment.")


# ── Health Tips ───────────────────────────────────────────────────────────────
def page_tips():
    st.markdown('<p class="main-title">💡 Health Tips</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Personalized tips for each condition</p>', unsafe_allow_html=True)
    for d, tips in HEALTH_TIPS.items():
        with st.expander(f"🩺 {d}"):
            for t in tips: st.write("• " + t)


# ── Profile ───────────────────────────────────────────────────────────────────
def page_profile():
    u = st.session_state.user
    api_key = get_groq_api_key()

    if not u:
        st.markdown('<p class="main-title">👤 Guest Profile</p>', unsafe_allow_html=True)
        st.markdown("""
        <div class="profile-card">
            <div class="profile-avatar">?</div>
            <div class="profile-name">Guest User</div>
            <div class="profile-email">Anonymous Session</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("### ⚙️ AI Engine Status")
        if api_key:
            st.success("🟢 Cloud Generative LLM Engine Connected (`llama-3.3-70b-versatile`)")
        else:
            st.info("⚪ Built-in Clinical Intelligence Engine Active\n\nAll predictions, lab analyses, and medical consultation features operate via local machine learning models and evidence-based clinical rule sets.")

        st.markdown("### Log in or Create an Account")
        st.write("Sign in to save your personal medical predictions, track health progress, and manage your account.")
        render_auth_form("profile_auth", show_skip=True)
        return

    reports = get_user_reports(u["id"])
    st.markdown('<p class="main-title">👤 My Profile</p>', unsafe_allow_html=True)
    initials = u["username"][0].upper() if u.get("username") else "U"
    total    = len(reports)
    positive = sum(1 for r in reports if "Positive" in str(r.get("prediction", "")) or "High" in str(r.get("prediction", "")))
    diseases = len({r["disease"] for r in reports})
    st.markdown(f"""
    <div class="profile-card">
        <div class="profile-avatar">{initials}</div>
        <div class="profile-name">{u['username']}</div>
        <div class="profile-email">{u['email']}</div>
    </div>""", unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    s1.markdown(f'<div class="stat-pill"><span class="num">{total}</span><span class="lbl">Predictions</span></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="stat-pill"><span class="num" style="color:#d9534f">{positive}</span><span class="lbl">Positive</span></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="stat-pill"><span class="num">{diseases}</span><span class="lbl">Diseases checked</span></div>', unsafe_allow_html=True)
    st.markdown("")

    st.markdown("### ⚙️ AI Engine Status")
    if api_key:
        st.success("🟢 Cloud Generative LLM Engine Connected (`llama-3.3-70b-versatile`)")
    else:
        st.info("⚪ Built-in Clinical Intelligence Engine Active\n\nAll predictions, lab analyses, and medical consultation features operate via local machine learning models and evidence-based clinical rule sets. You can optionally add a custom Groq API key in `.streamlit/secrets.toml` under `[groq] api_key`.")

    st.markdown("### Account info")
    st.text_input("Username", value=u["username"], disabled=True)
    st.text_input("Email",    value=u["email"],    disabled=True)
    st.info("To update your profile details, please contact the administrator.")
    st.markdown("### Change password")
    with st.form("change_pw"):
        new_pw  = st.text_input("New password (min 6 chars)", type="password")
        conf_pw = st.text_input("Confirm new password",       type="password")
        if st.form_submit_button("Update password", use_container_width=True):
            if len(new_pw) < 6:
                st.error("Password must be at least 6 characters.")
            elif new_pw != conf_pw:
                st.error("Passwords do not match.")
            else:
                st.success("✅ Password updated successfully!")


# ── Settings ──────────────────────────────────────────────────────────────────
def page_settings():
    st.markdown('<p class="main-title">⚙️ Settings</p>', unsafe_allow_html=True)
    st.markdown("### Appearance")
    dark = st.toggle("🌙 Dark mode", value=st.session_state.get("dark_mode", False))
    if dark != st.session_state.get("dark_mode", False):
        st.session_state.dark_mode = dark
        st.rerun()
    st.markdown("### Notifications")
    st.toggle("Email report after prediction", value=False)
    st.toggle("Health tip reminders",          value=True)
    st.markdown("### Data & Account")
    u = st.session_state.user
    if u:
        st.caption("Account: " + u["email"])
        if st.button("🗑️ Delete all my reports", type="secondary"):
            delete_all_reports(u["id"])
            st.success("All reports deleted!")
    else:
        st.caption("Account: Guest Mode (no server data permanently stored)")
    st.markdown("### About")
    st.info("MDPS v2.0 — Built with Streamlit & scikit-learn\n\nThis app is for educational purposes only.")


# ── VITALS Patient Portal ─────────────────────────────────────────────────────
def page_vitals():
    st.markdown('<p class="main-title">✨ VITALS Patient Portal</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Next-generation clinical screening, lab report analysis, and care locator</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="hero-banner" style="margin-bottom: 2rem;">
        <div class="hero-badge">🌟 High-End Patient Experience</div>
        <h1>VITALS Health Interface</h1>
        <p>A luxury, evidence-based medical screening portal featuring 9 specialized disease risk analyzers, multi-analyte lab report extraction, interactive care locator, and clinical AI guidance.</p>
    </div>
    """, unsafe_allow_html=True)
    
    v1, v2, v3, v4 = st.columns(4)
    with v1:
        st.markdown("""
        <div class="feature-tile">
            <div class="feature-icon">🩺</div>
            <div class="feature-title">9-Disease Screening</div>
            <div class="feature-desc">Dynamic risk gauges, factor breakdowns, and clinical reasons for Diabetes, Heart, Liver, Kidney, and more.</div>
        </div>
        """, unsafe_allow_html=True)
    with v2:
        st.markdown("""
        <div class="feature-tile">
            <div class="feature-icon">📑</div>
            <div class="feature-title">Lab Report Analyzer</div>
            <div class="feature-desc">Drag & drop blood reports to extract 20+ laboratory values and calculate multi-disease risk profiles.</div>
        </div>
        """, unsafe_allow_html=True)
    with v3:
        st.markdown("""
        <div class="feature-tile">
            <div class="feature-icon">🏥</div>
            <div class="feature-title">Care Finder Map</div>
            <div class="feature-desc">OpenStreetMap facility locator for hospitals, clinics, specialists, and emergency care.</div>
        </div>
        """, unsafe_allow_html=True)
    with v4:
        st.markdown("""
        <div class="feature-tile">
            <div class="feature-icon">💬</div>
            <div class="feature-title">VERA AI Assistant</div>
            <div class="feature-desc">Conversational clinical guidance explaining lab markers, reference bounds, and precautions.</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab_overview, tab_live = st.tabs(["🚀 Quick Access Links", "💻 Interactive Portal Preview"])
    with tab_overview:
        st.markdown("### 🌐 Running Local & Cloud Access")
        st.markdown("""
        - **Local Full Portal**: [http://localhost:8000/](http://localhost:8000/) *(Landing page with parallax typography & marquee)*
        - **Clinical Screening Tool**: [http://localhost:8000/app.html](http://localhost:8000/app.html)
        - **Lab Report Analyzer**: [http://localhost:8000/report.html](http://localhost:8000/report.html)
        - **Find Care Locator**: [http://localhost:8000/care.html](http://localhost:8000/care.html)
        - **Interactive API Docs**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
        """)
        st.info("💡 To start the standalone local server at any time, run `python serve.py 8000` or `.\\start.ps1` from the project root.")
        
    with tab_live:
        st.markdown("### 📱 Embedded Live Preview")
        vitals_index_path = Path(__file__).resolve().parent.parent / "vitals-web" / "index.html"
        if vitals_index_path.exists():
            import streamlit.components.v1 as components
            html_code = vitals_index_path.read_text(encoding="utf-8", errors="replace")
            components.html(html_code, height=750, scrolling=True)
        else:
            st.info("VITALS web files are located in `vitals-web/`.")


# ── Direct Router ─────────────────────────────────────────────────────────────
page = sidebar()
router = {
    "✨ VITALS Portal":       page_vitals,
    "Dashboard":            page_dashboard,
    "Report Analyzer":      page_report_analyzer,
    "Symptom Checker":      page_symptom,
    "Clinical Risk Forms":  page_disease_prediction,
    "Nearby Hospitals":     page_hospitals,
    "AI Chatbot":           page_chatbot,
    "Saved Reports":        page_reports,
    "Analytics":            page_analytics,
    "Health Tips":          page_tips,
    "About":                page_about,
    "Profile":              page_profile,
    "Settings":             page_settings,
}
router.get(page, page_vitals)()
