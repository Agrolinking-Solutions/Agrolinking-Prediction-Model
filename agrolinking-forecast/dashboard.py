"""
AGROLINKING COMMODITY INTELLIGENCE DASHBOARD
Run: streamlit run dashboard.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import json, os, glob, base64
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(
    page_title="Agrolinking | Commodity Intelligence",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Brand ──────────────────────────────────────────────────────────────────
DARK   = "#053307"
MID    = "#007f07"
YELLOW = "#FFCE35"
WHITE  = "#FFFFFF"

# ── Paths ──────────────────────────────────────────────────────────────────
BASE   = os.path.expanduser("~/Agrolinking-Prediction-Model/agrolinking-forecast")
MASTER = os.path.join(BASE, "data/processed/agricom_master.csv")
LOGS   = os.path.join(BASE, "outputs/forecast_logs")
LOGO   = os.path.join(BASE, "assets/Agrolinking_Logo.png")

# ── Session defaults ───────────────────────────────────────────────────────
if "dark"  not in st.session_state: st.session_state.dark  = False
if "page"  not in st.session_state: st.session_state.page  = "Dashboard"

dm   = st.session_state.dark
page = st.session_state.page

# ── Theme tokens ───────────────────────────────────────────────────────────
if dm:
    BG=("#0A130A"); BG2=("#111D11"); BG3=("#182018")
    CARD=("#141F14"); BORDER=("#1E2E1E"); BORDER2=("#2A3E2A")
    TEXT=("#E8F5E8"); TEXT2=("#9DC89D"); TEXT3=("#5E8A5E")
    ACC=("#22C55E"); YACC=("#FFCE35")
    UP=("#86EFAC"); UPBG=("#052E16")
    DN=("#FCA5A5"); DNBG=("#450A0A")
    FL=("#FDE68A"); FLBG=("#451A03")
    SHAD="0 2px 8px rgba(0,0,0,0.5), 0 8px 32px rgba(0,0,0,0.4)"
    SHADLG="0 12px 48px rgba(0,0,0,0.6)"
    CBG=("#141F14"); CGRID=("#1E2E1E"); CTXT=("#9DC89D"); CBRD=("#1E2E1E")
else:
    BG=("#FFFFFF"); BG2=("#F6F8F6"); BG3=("#EDF3ED")
    CARD=("#FFFFFF"); BORDER=("#E2EBE2"); BORDER2=("#C8D8C8")
    TEXT=("#0D1F0D"); TEXT2=("#3A5A3A"); TEXT3=("#6B8B6B")
    ACC=("#007f07"); YACC=("#FFCE35")
    UP=("#14532D"); UPBG=("#DCFCE7")
    DN=("#7F1D1D"); DNBG=("#FEE2E2")
    FL=("#78350F"); FLBG=("#FEF9C3")
    SHAD="0 1px 4px rgba(5,51,7,0.07), 0 4px 20px rgba(5,51,7,0.04)"
    SHADLG="0 8px 40px rgba(5,51,7,0.10)"
    CBG=("#FFFFFF"); CGRID=("#E8F0E8"); CTXT=("#3A5A3A"); CBRD=("#E2EBE2")

# ══════════════════════════════════════════════════════════════════════════
# MEGA CSS
# ══════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300;12..96,400;12..96,500;12..96,600;12..96,700;12..96,800&family=Golos+Text:wght@400;500;600;700&display=swap');

*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html,body,[class*="css"]{{
    font-family:'Golos Text',sans-serif;
    background:{BG}!important;
    color:{TEXT}!important;
    -webkit-font-smoothing:antialiased;
    transition:background .35s,color .35s;
}}
.main .block-container{{padding:0!important;max-width:100%!important;}}
[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],footer,#MainMenu,
section[data-testid="stSidebar"]{{display:none!important;visibility:hidden!important;}}
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="stVerticalBlock"]{{background:{BG}!important;}}

/* ── KEYFRAMES ── */
@keyframes fadeUp{{from{{opacity:0;transform:translateY(28px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes slideRight{{from{{opacity:0;transform:translateX(-22px)}}to{{opacity:1;transform:translateX(0)}}}}
@keyframes marquee{{from{{transform:translateX(100%)}}to{{transform:translateX(-100%)}}}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.35;transform:scale(1.45)}}}}
@keyframes float{{0%,100%{{transform:translateY(0) rotate(0deg)}}33%{{transform:translateY(-12px) rotate(1deg)}}66%{{transform:translateY(-6px) rotate(-1deg)}}}}
@keyframes glow{{0%,100%{{box-shadow:0 0 20px rgba(0,127,7,.15)}}50%{{box-shadow:0 0 40px rgba(0,127,7,.35),0 0 80px rgba(0,127,7,.1)}}}}
@keyframes shimmer{{0%{{background-position:-200% 0}}100%{{background-position:200% 0}}}}
@keyframes orbit{{from{{transform:rotate(0deg) translateX(120px) rotate(0deg)}}to{{transform:rotate(360deg) translateX(120px) rotate(-360deg)}}}}
@keyframes countUp{{from{{opacity:0;transform:scale(.8)}}to{{opacity:1;transform:scale(1)}}}}
@keyframes borderGlow{{0%,100%{{border-color:{BORDER}}}50%{{border-color:{ACC}}}}}

.anim-up{{animation:fadeUp .65s cubic-bezier(.16,1,.3,1) both;}}
.anim-in{{animation:fadeIn .5s ease both;}}
.anim-right{{animation:slideRight .55s cubic-bezier(.16,1,.3,1) both;}}
.d1{{animation-delay:.06s}}.d2{{animation-delay:.12s}}.d3{{animation-delay:.18s}}
.d4{{animation-delay:.24s}}.d5{{animation-delay:.30s}}.d6{{animation-delay:.36s}}

/* ── TOPBAR ── */
.topbar{{
    background:#053307;
    padding:9px 48px;
    display:flex;align-items:center;gap:18px;
    border-bottom:1px solid rgba(255,255,255,.06);
}}
.topbar-badge{{
    font-size:9.5px;font-weight:700;letter-spacing:1.4px;
    text-transform:uppercase;color:#053307;
    background:#FFCE35;padding:4px 11px;border-radius:4px;flex-shrink:0;
}}
.topbar-track{{flex:1;overflow:hidden;white-space:nowrap;}}
.topbar-inner{{
    display:inline-block;
    animation:marquee 58s linear infinite;
    font-size:12px;color:rgba(255,255,255,.72);
    font-family:'Golos Text',sans-serif;
}}
.topbar-inner strong{{color:#FFCE35;font-weight:600;}}
.tk-up{{color:#86efac;}}.tk-down{{color:#fca5a5;}}
.tk-sep{{color:rgba(255,255,255,.18);margin:0 14px;}}

/* ── NAVBAR ── */
.nav-shell{{background:{BG};padding:13px 40px;transition:background .35s;}}
.navbar{{
    background:{CARD};border:1px solid {BORDER};border-radius:16px;
    padding:0 22px;height:60px;max-width:1140px;margin:0 auto;
    display:flex;align-items:center;justify-content:space-between;
    box-shadow:{SHAD};transition:background .35s,border-color .35s,box-shadow .35s;
}}
.nb-left{{display:flex;align-items:center;gap:16px;}}
.nb-right{{display:flex;align-items:center;gap:10px;}}
.nb-divider{{width:1px;height:20px;background:{BORDER};transition:background .35s;}}
.nb-label{{font-size:10.5px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};}}
.nb-date{{font-size:12px;color:{TEXT3};font-weight:500;}}
.live-pill{{
    display:inline-flex;align-items:center;gap:5px;
    background:{UPBG};border:1px solid rgba(34,197,94,.25);
    color:{UP};padding:5px 12px;border-radius:6px;
    font-size:10px;font-weight:700;letter-spacing:.9px;text-transform:uppercase;
    transition:background .35s,color .35s;
}}
.live-dot{{width:6px;height:6px;background:currentColor;border-radius:50%;animation:pulse 1.5s ease-in-out infinite;}}

/* ── TABS ── */
.page-tabs{{
    background:{BG2};border-bottom:1px solid {BORDER};
    padding:0 40px;display:flex;gap:2px;overflow-x:auto;
    transition:background .35s,border-color .35s;
}}
.page-tabs::-webkit-scrollbar{{height:0;}}
.ptab{{
    padding:14px 18px;font-size:13px;font-weight:600;
    color:{TEXT3};border-bottom:2.5px solid transparent;
    cursor:pointer;transition:color .2s,border-color .2s;
    white-space:nowrap;letter-spacing:.2px;user-select:none;
}}
.ptab:hover{{color:{TEXT2};}}
.ptab.active{{color:{ACC};border-bottom-color:{ACC};}}

/* ── HERO ── */
.hero{{
    background:{BG};padding:80px 48px 72px;
    position:relative;overflow:hidden;
    transition:background .35s;
}}
.hero-3d{{
    position:absolute;right:5%;top:50%;transform:translateY(-50%);
    width:340px;height:340px;pointer-events:none;opacity:.18;
}}
.hero-inner{{max-width:1140px;margin:0 auto;position:relative;z-index:1;}}
.hero-eyebrow{{
    display:inline-flex;align-items:center;gap:8px;
    color:{ACC};font-size:10.5px;font-weight:700;
    letter-spacing:2px;text-transform:uppercase;margin-bottom:20px;
}}
.hero-eyebrow::before{{
    content:'';display:block;width:22px;height:2px;
    background:{ACC};border-radius:2px;
}}
.hero-h1{{
    font-family:'Bricolage Grotesque',sans-serif;
    font-size:60px;font-weight:800;color:{TEXT};
    line-height:1.02;letter-spacing:-2.5px;
    margin-bottom:22px;max-width:820px;
    transition:color .35s;
}}
.hero-h1 mark{{background:none;color:{ACC};}}
.hero-body{{
    font-size:15.5px;line-height:1.72;color:{TEXT2};
    max-width:520px;transition:color .35s;
}}
.kpis{{
    display:flex;border-top:1px solid {BORDER};
    padding-top:36px;margin-top:48px;flex-wrap:wrap;
    transition:border-color .35s;
}}
.kpi{{
    padding:0 52px 0 0;margin-right:52px;
    border-right:1px solid {BORDER};transition:border-color .35s;
}}
.kpi:last-child{{border-right:none;padding-right:0;margin-right:0;}}
.kpi-n{{
    font-family:'Bricolage Grotesque',sans-serif;
    font-size:44px;font-weight:700;color:{TEXT};
    line-height:1;letter-spacing:-2px;
    animation:countUp .7s cubic-bezier(.16,1,.3,1) both;
    transition:color .35s;
}}
.kpi-l{{
    font-size:10px;font-weight:700;color:{TEXT3};
    text-transform:uppercase;letter-spacing:1.6px;
    margin-top:7px;transition:color .35s;
}}

/* ── SECTION ── */
.content{{padding:52px 48px 0;background:{BG};transition:background .35s;}}
.section-hd{{
    margin-bottom:28px;padding-bottom:20px;
    border-bottom:1px solid {BORDER};transition:border-color .35s;
}}
.eyebrow{{
    display:block;font-size:10px;font-weight:700;
    letter-spacing:2px;text-transform:uppercase;
    color:{ACC};margin-bottom:7px;transition:color .35s;
}}
.section-h2{{
    font-family:'Bricolage Grotesque',sans-serif;
    font-size:27px;font-weight:700;color:{TEXT};
    letter-spacing:-.7px;line-height:1.15;
    transition:color .35s;
}}

/* ── STAT CARDS ── */
.stat-grid{{
    display:grid;
    grid-template-columns:repeat(auto-fill,minmax(210px,1fr));
    gap:14px;margin-bottom:48px;
}}
.stat-card{{
    background:{CARD};border:1px solid {BORDER};border-radius:16px;
    padding:24px;box-shadow:{SHAD};
    transition:transform .2s cubic-bezier(.16,1,.3,1),box-shadow .2s,
               background .35s,border-color .35s;
}}
.stat-card:hover{{transform:translateY(-4px) scale(1.015);box-shadow:{SHADLG};}}
.stat-label{{font-size:10px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:{TEXT3};margin-bottom:10px;transition:color .35s;}}
.stat-value{{font-family:'Bricolage Grotesque',sans-serif;font-size:34px;font-weight:700;color:{TEXT};letter-spacing:-1.5px;line-height:1;transition:color .35s;}}
.stat-sub{{font-size:12px;color:{TEXT3};margin-top:6px;transition:color .35s;}}

/* ── PRICE CARDS ── */
.pgrid{{
    display:grid;
    grid-template-columns:repeat(auto-fill,minmax(185px,1fr));
    gap:14px;margin-bottom:56px;
}}
.pcard{{
    background:{CARD};border:1px solid {BORDER};
    border-top:3.5px solid {BORDER};border-radius:16px;
    padding:22px 20px 18px;
    transition:transform .2s cubic-bezier(.16,1,.3,1),box-shadow .2s,
               background .35s,border-color .35s;
}}
.pcard:hover{{transform:translateY(-5px) scale(1.02);box-shadow:{SHADLG};}}
.pcard.up{{border-top-color:{ACC};}}
.pcard.down{{border-top-color:{DN};}}
.pcard.flat{{border-top-color:{YACC};}}
.pcard-name{{font-size:9.5px;font-weight:700;letter-spacing:1.4px;text-transform:uppercase;color:{TEXT3};margin-bottom:10px;margin-top:2px;display:flex;align-items:center;gap:7px;transition:color .35s;}}
.dot{{width:7px;height:7px;border-radius:50%;flex-shrink:0;display:inline-block;}}
.pcard-price{{font-family:'Bricolage Grotesque',sans-serif;font-size:21px;font-weight:700;color:{TEXT};letter-spacing:-.8px;line-height:1.1;transition:color .35s;}}
.pcard-unit{{font-size:10.5px;color:{TEXT3};margin:3px 0 12px;transition:color .35s;}}
.chip{{display:inline-flex;align-items:center;gap:4px;font-size:10.5px;font-weight:700;padding:3px 9px;border-radius:5px;transition:background .35s,color .35s;}}
.chip.up{{background:{UPBG};color:{UP};}}
.chip.down{{background:{DNBG};color:{DN};}}
.chip.flat{{background:{FLBG};color:{FL};}}
.pcard-prev{{font-size:10.5px;color:{TEXT3};margin-top:8px;transition:color .35s;}}

/* ── TABLE ── */
.tbl-wrap{{margin-bottom:56px;}}
.tbl{{width:100%;border-collapse:collapse;background:{CARD};border-radius:16px;overflow:hidden;border:1px solid {BORDER};box-shadow:{SHAD};transition:background .35s,border-color .35s;}}
.tbl thead tr{{background:#053307;}}
.tbl th{{padding:14px 20px;text-align:left;font-size:9.5px;font-weight:700;letter-spacing:1.7px;text-transform:uppercase;color:rgba(255,255,255,.5);white-space:nowrap;}}
.tbl td{{padding:13px 20px;border-bottom:1px solid {BORDER};font-size:13.5px;vertical-align:middle;background:{CARD};color:{TEXT};transition:background .2s,color .35s,border-color .35s;}}
.tbl tr:last-child td{{border-bottom:none;}}
.tbl tbody tr:hover td{{background:{BG2}!important;}}
.td-name{{font-weight:600;color:{TEXT};display:flex;align-items:center;gap:9px;transition:color .35s;}}
.td-num{{font-family:'Bricolage Grotesque',sans-serif;font-size:14.5px;font-weight:600;color:{TEXT};letter-spacing:-.3px;transition:color .35s;}}
.td-up{{color:{UP};font-weight:700;font-size:12.5px;display:inline-flex;align-items:center;gap:4px;}}
.td-down{{color:{DN};font-weight:700;font-size:12.5px;display:inline-flex;align-items:center;gap:4px;}}
.td-flat{{color:{FL};font-weight:700;font-size:12.5px;display:inline-flex;align-items:center;gap:4px;}}

/* ── LONG RANGE ── */
.lr-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:56px;}}
.lr-card{{background:{CARD};border:1px solid {BORDER};border-radius:16px;overflow:hidden;box-shadow:{SHAD};transition:transform .2s,box-shadow .2s,background .35s,border-color .35s;}}
.lr-card:hover{{transform:translateY(-4px);box-shadow:{SHADLG};}}
.lr-hd{{padding:16px 22px;display:flex;align-items:center;justify-content:space-between;}}
.lr-hd.h1{{background:#053307;}}.lr-hd.h3{{background:#0C4410;}}.lr-hd.h6{{background:#082D0A;}}
.lr-title{{font-family:'Bricolage Grotesque',sans-serif;font-size:13px;font-weight:700;color:#fff;letter-spacing:-.2px;}}
.lr-badge{{font-size:9px;font-weight:700;padding:3px 8px;border-radius:4px;letter-spacing:.8px;text-transform:uppercase;}}
.lr-badge.high{{background:rgba(255,206,53,.2);color:#FFCE35;}}
.lr-badge.mid{{background:rgba(255,255,255,.12);color:rgba(255,255,255,.72);}}
.lr-badge.low{{background:rgba(255,255,255,.07);color:rgba(255,255,255,.4);}}
.lr-row{{display:flex;align-items:center;padding:10px 22px;border-bottom:1px solid {BORDER};gap:8px;transition:background .15s,border-color .35s;}}
.lr-row:hover{{background:{BG2};}}
.lr-row:last-child{{border-bottom:none;}}
.lr-name{{font-size:12px;font-weight:600;color:{TEXT};flex:0 0 108px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:flex;align-items:center;gap:7px;transition:color .35s;}}
.lr-range{{font-family:'Bricolage Grotesque',sans-serif;font-size:11.5px;font-weight:600;color:{TEXT};flex:1;text-align:center;transition:color .35s;}}
.lr-dir{{flex:0 0 22px;text-align:right;font-size:11.5px;font-weight:700;}}

/* ── MOVEMENT ── */
.mv-card{{background:{CARD};border:1px solid {BORDER};border-radius:16px;overflow:hidden;margin-bottom:56px;box-shadow:{SHAD};transition:background .35s,border-color .35s;}}
.mv-row{{display:flex;align-items:center;gap:14px;padding:13px 22px;border-bottom:1px solid {BORDER};background:{CARD};transition:background .15s,border-color .35s;}}
.mv-row:hover{{background:{BG2};}}
.mv-row:last-child{{border-bottom:none;}}
.mv-icon{{width:36px;height:36px;border-radius:9px;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .35s;}}
.mv-icon.up{{background:{UPBG};color:{UP};}}
.mv-icon.down{{background:{DNBG};color:{DN};}}
.mv-icon.flat{{background:{FLBG};color:{FL};}}
.mv-info{{flex:1;min-width:0;}}
.mv-name{{font-weight:600;font-size:14px;color:{TEXT};transition:color .35s;}}
.mv-sub{{font-size:11.5px;color:{TEXT3};margin-top:1px;transition:color .35s;}}
.mv-pct{{font-family:'Bricolage Grotesque',sans-serif;font-size:17px;font-weight:700;flex-shrink:0;margin-left:auto;}}
.mv-pct.up{{color:{UP};}}.mv-pct.down{{color:{DN};}}.mv-pct.flat{{color:{FL};}}

/* ── CHART ── */
.chart-wrap{{background:{CARD};border:1px solid {BORDER};border-radius:16px;padding:24px 20px 8px;margin-bottom:56px;box-shadow:{SHAD};transition:background .35s,border-color .35s;}}

/* ── FEATURE CARDS (About) ── */
.feature-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px;margin-bottom:48px;}}
.feature-card{{
    background:{CARD};border:1px solid {BORDER};border-radius:16px;padding:28px;
    box-shadow:{SHAD};
    transition:transform .2s cubic-bezier(.16,1,.3,1),box-shadow .2s,background .35s,border-color .35s;
    position:relative;overflow:hidden;
}}
.feature-card::before{{
    content:'';position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,{ACC},{YACC});opacity:0;
    transition:opacity .25s;
}}
.feature-card:hover{{transform:translateY(-5px);box-shadow:{SHADLG};}}
.feature-card:hover::before{{opacity:1;}}
.feature-num{{
    font-family:'Bricolage Grotesque',sans-serif;
    font-size:48px;font-weight:800;color:{BORDER2};
    line-height:1;margin-bottom:12px;
    transition:color .35s;
}}
.feature-card:hover .feature-num{{color:{ACC};}}
.feature-h3{{font-family:'Bricolage Grotesque',sans-serif;font-size:17px;font-weight:700;color:{TEXT};margin-bottom:8px;transition:color .35s;}}
.feature-p{{font-size:13.5px;color:{TEXT2};line-height:1.65;transition:color .35s;}}

/* ── ABOUT HERO ── */
.about-hero{{
    background:#053307;padding:88px 48px 80px;
    position:relative;overflow:hidden;
}}
.about-hero-bg{{
    position:absolute;inset:0;
    background:radial-gradient(ellipse 60% 70% at 80% 50%, rgba(255,206,53,.08) 0%, transparent 70%),
               radial-gradient(ellipse 40% 50% at 20% 80%, rgba(0,127,7,.15) 0%, transparent 60%);
    pointer-events:none;
}}
.about-hero-inner{{max-width:1140px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:center;}}
.about-h1{{font-family:'Bricolage Grotesque',sans-serif;font-size:52px;font-weight:800;color:#fff;letter-spacing:-2px;line-height:1.05;}}
.about-h1 mark{{background:none;color:#FFCE35;}}
.about-sub{{font-size:16px;color:rgba(255,255,255,.62);line-height:1.72;margin-top:20px;}}
.about-stats{{display:grid;grid-template-columns:1fr 1fr;gap:16px;}}
.about-stat{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:14px;padding:22px;}}
.about-stat-n{{font-family:'Bricolage Grotesque',sans-serif;font-size:36px;font-weight:700;color:#FFCE35;letter-spacing:-1.5px;line-height:1;}}
.about-stat-l{{font-size:11px;font-weight:600;color:rgba(255,255,255,.45);text-transform:uppercase;letter-spacing:1.3px;margin-top:6px;}}

/* ── MODEL INSIGHT CARDS ── */
.insight-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:40px;}}
.insight-card{{
    background:{CARD};border:1px solid {BORDER};border-radius:16px;padding:24px;
    box-shadow:{SHAD};
    transition:transform .2s,box-shadow .2s,background .35s,border-color .35s;
    position:relative;overflow:hidden;
}}
.insight-card:hover{{transform:translateY(-4px);box-shadow:{SHADLG};}}
.insight-card::after{{
    content:'';position:absolute;bottom:0;left:0;right:0;height:3px;
}}
.insight-card.arima::after{{background:#4CAF50;}}
.insight-card.prophet::after{{background:{YACC};}}
.insight-card.xgboost::after{{background:{ACC};}}
.insight-model{{font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT3};margin-bottom:12px;}}
.insight-score{{font-family:'Bricolage Grotesque',sans-serif;font-size:40px;font-weight:700;color:{TEXT};letter-spacing:-2px;line-height:1;transition:color .35s;}}
.insight-label{{font-size:12px;color:{TEXT3};margin-top:6px;transition:color .35s;}}

/* ── FOOTER ── */
.footer{{
    background:linear-gradient(135deg,#053307 0%,#0a4a10 50%,#053307 100%);
    border-top:none;margin-top:56px;
    position:relative;overflow:hidden;
}}
.footer-glow{{
    position:absolute;inset:0;
    background:radial-gradient(ellipse 50% 80% at 30% 50%,rgba(0,127,7,.15) 0%,transparent 70%),
               radial-gradient(ellipse 30% 60% at 80% 30%,rgba(255,206,53,.06) 0%,transparent 60%);
    pointer-events:none;
}}
.footer-top{{
    border-bottom:1px solid rgba(255,255,255,.08);
    padding:48px 48px 40px;
    display:grid;grid-template-columns:1.6fr 1fr 1fr 1fr;
    gap:40px;max-width:100%;position:relative;z-index:1;
}}
.footer-logo-area{{}}
.footer-brand{{font-family:'Bricolage Grotesque',sans-serif;font-size:22px;font-weight:800;color:#fff;letter-spacing:-.5px;margin-bottom:10px;}}
.footer-brand-tag{{font-size:13px;color:rgba(255,255,255,.45);line-height:1.7;max-width:260px;}}
.footer-badge{{
    display:inline-flex;align-items:center;gap:6px;
    background:rgba(255,206,53,.15);border:1px solid rgba(255,206,53,.25);
    color:#FFCE35;padding:6px 14px;border-radius:6px;
    font-size:10.5px;font-weight:700;letter-spacing:1px;
    text-transform:uppercase;margin-top:18px;
}}
.footer-badge-dot{{width:6px;height:6px;background:#FFCE35;border-radius:50%;animation:pulse 2s ease-in-out infinite;}}
.footer-col-title{{font-size:10px;font-weight:700;letter-spacing:1.8px;text-transform:uppercase;color:rgba(255,255,255,.35);margin-bottom:16px;}}
.footer-link{{display:block;font-size:13px;color:rgba(255,255,255,.58);margin-bottom:10px;text-decoration:none;transition:color .2s;cursor:default;}}
.footer-link:hover,.footer-link-a:hover{{color:#FFCE35;}}
.footer-link-a{{display:block;font-size:13px;color:rgba(255,255,255,.58);margin-bottom:10px;text-decoration:none;transition:color .2s;}}
.footer-bottom{{
    padding:22px 48px;display:flex;align-items:center;justify-content:space-between;
    position:relative;z-index:1;flex-wrap:wrap;gap:12px;
}}
.footer-copy{{font-size:11.5px;color:rgba(255,255,255,.28);}}
.footer-copy a{{color:rgba(255,255,255,.45);text-decoration:none;}}
.footer-disclaimer{{font-size:10.5px;color:rgba(255,255,255,.2);max-width:500px;text-align:right;}}

/* ── STREAMLIT OVERRIDES ── */
div.stButton>button{{
    background:{ACC}!important;color:#fff!important;
    border:none!important;border-radius:9px!important;
    font-family:'Golos Text',sans-serif!important;
    font-size:13px!important;font-weight:600!important;
    padding:8px 18px!important;letter-spacing:.2px!important;
    transition:background .2s,transform .15s!important;
}}
div.stButton>button:hover{{background:#053307!important;transform:translateY(-2px)!important;}}
div[data-testid="stSelectbox"]>div>div{{
    border-radius:9px!important;border:1px solid {BORDER}!important;
    font-family:'Golos Text',sans-serif!important;
    background:{CARD}!important;color:{TEXT}!important;
    font-size:13.5px!important;
    transition:background .35s,border-color .35s,color .35s!important;
}}
div[data-testid="stSelectbox"] *{{color:{TEXT}!important;background:{CARD}!important;}}
[data-testid="stDataFrame"]{{border-radius:12px!important;overflow:hidden!important;border:1px solid {BORDER}!important;}}
[data-testid="stDataFrame"] *{{color:{TEXT}!important;background:{CARD}!important;font-family:'Golos Text',sans-serif!important;}}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════
COMMODITIES = ['Hibiscus','Soybeans','Ginger','Cocoa','Cashew Nuts','Sorghum','Sesame','Beans (red)','Beans (white)','Maize (white)','Maize (yellow)']
DOTS = {'Hibiscus':'#E91E63','Soybeans':'#795548','Ginger':'#FF9800','Cocoa':'#4E342E',
        'Cashew Nuts':'#F9A825','Sorghum':'#827717','Sesame':'#558B2F',
        'Beans (red)':'#C62828','Beans (white)':'#757575','Maize (white)':'#FDD835','Maize (yellow)':'#F9A825'}
MONTHS_S = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
MONTHS_L = ['January','February','March','April','May','June',
            'July','August','September','October','November','December']

def fmt(p):
    if not p: return "—"
    return f"₦{int(round(p)):,}"

def fmtM(p):
    if not p: return "—"
    if p >= 1_000_000: return f"₦{p/1_000_000:.2f}M"
    if p >= 1_000:     return f"₦{p/1_000:.0f}K"
    return f"₦{int(p):,}"

def pct(new, old):
    if not old or old == 0: return None
    return (new - old) / old * 100

def dirn(cur, fwd):
    if not cur or not fwd: return "flat"
    p = (fwd - cur) / cur * 100
    if p > 3: return "up"
    if p < -3: return "down"
    return "flat"

def svg_up(sz=12): return f'<svg width="{sz}" height="{sz}" viewBox="0 0 12 12"><path d="M6 2L11 9H1L6 2Z" fill="currentColor"/></svg>'
def svg_dn(sz=12): return f'<svg width="{sz}" height="{sz}" viewBox="0 0 12 12"><path d="M6 10L1 3H11L6 10Z" fill="currentColor"/></svg>'
def svg_fl(sz=12): return f'<svg width="{sz}" height="{sz}" viewBox="0 0 12 12"><rect y="5" width="12" height="2" rx="1" fill="currentColor"/></svg>'

def dir_td(d):
    if d=="up":   return f'<span class="td-up">{svg_up(11)} Up</span>'
    if d=="down": return f'<span class="td-down">{svg_dn(11)} Down</span>'
    return f'<span class="td-flat">{svg_fl(11)} Flat</span>'

def mv_ico(d):
    if d=="up":   return f'<div class="mv-icon up">{svg_up(14)}</div>'
    if d=="down": return f'<div class="mv-icon down">{svg_dn(14)}</div>'
    return f'<div class="mv-icon flat">{svg_fl(14)}</div>'

def lr_arr(d):
    if d=="up":   return f'<span class="lr-dir" style="color:{UP};">{svg_up(11)}</span>'
    if d=="down": return f'<span class="lr-dir" style="color:{DN};">{svg_dn(11)}</span>'
    return f'<span class="lr-dir" style="color:{FL};">{svg_fl(11)}</span>'

def dot(c,sz=7):
    return f'<span class="dot" style="width:{sz}px;height:{sz}px;background:{DOTS.get(c,"#888")};"></span>'

def chip_html(pc_):
    if pc_ and pc_ > 1:   return f'<span class="chip up">{svg_up(10)}&nbsp;+{pc_:.1f}%</span>'
    if pc_ and pc_ < -1:  return f'<span class="chip down">{svg_dn(10)}&nbsp;{pc_:.1f}%</span>'
    return f'<span class="chip flat">{svg_fl(10)}&nbsp;Stable</span>'

def chart_cfg(h=360, ml=64, mr=20, mt=24, mb=50):
    return dict(
        plot_bgcolor=CBG, paper_bgcolor=CBG,
        font=dict(family='Golos Text, sans-serif', color=CTXT, size=12),
        margin=dict(l=ml, r=mr, t=mt, b=mb),
        height=h,
        legend=dict(
            orientation='h', yanchor='bottom', y=1.04, xanchor='left', x=0,
            font=dict(size=12, family='Golos Text', color=CTXT),
            bgcolor='rgba(0,0,0,0)', borderwidth=0
        ),
        hovermode='x unified',
        hoverlabel=dict(bgcolor=CBG, bordercolor=CBRD,
                        font=dict(family='Golos Text', size=12, color=CTXT)),
        xaxis=dict(
            showgrid=True, gridcolor=CGRID, gridwidth=1,
            tickfont=dict(size=11, color=CTXT, family='Golos Text'),
            zeroline=False, showline=True, linecolor=CBRD,
            ticks='outside', ticklen=4, tickcolor=CBRD,
            title_font=dict(size=12, color=CTXT, family='Golos Text')
        ),
        yaxis=dict(
            showgrid=True, gridcolor=CGRID, gridwidth=1,
            tickfont=dict(size=11, color=CTXT, family='Golos Text'),
            zeroline=False, showline=True, linecolor=CBRD,
            ticks='outside', ticklen=4, tickcolor=CBRD,
            title_font=dict(size=12, color=CTXT, family='Golos Text')
        )
    )

# ── Data ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_master():
    if not os.path.exists(MASTER): return pd.DataFrame()
    df = pd.read_csv(MASTER)
    df['week_start_date'] = pd.to_datetime(df['week_start_date'], format='mixed')
    return df

def load_fc():
    files = sorted(glob.glob(os.path.join(LOGS, "final_forecasts_*.json")))
    if not files: return {}, None
    with open(files[-1]) as f:
        return json.load(f), os.path.basename(files[-1]).replace("final_forecasts_","").replace(".json","")

def load_yest(ds):
    if not ds: return {}
    y = (datetime.strptime(ds,"%Y-%m-%d")-timedelta(days=1)).strftime("%Y-%m-%d")
    p = os.path.join(LOGS, f"final_forecasts_{y}.json")
    if os.path.exists(p):
        with open(p) as f: return json.load(f)
    m = load_master()
    out = {}
    if not m.empty:
        for c in COMMODITIES:
            h = m[(m['commodity']==c)&(m['record_type']=='historical')].sort_values('week_start_date')
            if not h.empty: out[c] = {'daily': float(h['price'].iloc[-1])}
    return out

master    = load_master()
fc, fc_dt = load_fc()
yest      = load_yest(fc_dt)
NOW       = datetime.now()

logo_b64 = ""
if os.path.exists(LOGO):
    with open(LOGO,"rb") as f: logo_b64 = base64.b64encode(f.read()).decode()

n_c = len([c for c in COMMODITIES if c in fc])
n_m = sum(1 for c in COMMODITIES if c in fc and c in yest
          and abs(pct(fc[c].get('daily',0), yest.get(c,{}).get('daily')) or 0) > 1)

# ══════════════════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════════════════
parts = []
for c in COMMODITIES:
    if c not in fc: continue
    p   = fc[c].get('daily', 0)
    yp  = yest.get(c,{}).get('daily') if yest else None
    pc_ = pct(p, yp)
    chg = (f'&nbsp;<span class="tk-up">+{pc_:.1f}%</span>' if pc_ and pc_>1
           else f'&nbsp;<span class="tk-down">{pc_:.1f}%</span>' if pc_ and pc_<-1 else "")
    parts.append(f'<strong>{c[:3].upper()}</strong>&nbsp;{fmt(p)}{chg}')
ticker = '<span class="tk-sep">·</span>'.join(parts) * 3

st.markdown(f"""
<div class="topbar">
  <span class="topbar-badge">Market Data</span>
  <div class="topbar-track"><span class="topbar-inner">&emsp;{ticker}&emsp;</span></div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# NAVBAR
# ══════════════════════════════════════════════════════════════════════════
_logo_filter = "brightness(0) invert(1)" if dm else "none"
logo_img = (f'<img src="data:image/png;base64,{logo_b64}" height="27" style="filter:{_logo_filter}" alt="Agrolinking">'
            if logo_b64 else
            f'<span style="font-family:Bricolage Grotesque,sans-serif;font-size:18px;font-weight:800;color:{TEXT};">agrolinking</span>')

st.markdown(f"""
<div class="nav-shell">
 <div class="navbar">
  <div class="nb-left">
    {logo_img}
    <div class="nb-divider"></div>
    <span class="nb-label">Commodity Intelligence</span>
  </div>
  <div class="nb-right">
    <span class="nb-date">{NOW.strftime('%a, %d %b %Y &nbsp;·&nbsp; %I:%M %p')}</span>
    <div class="live-pill"><div class="live-dot"></div>Live</div>
  </div>
 </div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# PAGE TABS — clickable buttons disguised as tabs using st.columns
# ══════════════════════════════════════════════════════════════════════════
PAGES = ["Dashboard", "Daily Prices", "Long-Range", "Model Analysis", "About"]

# Render visual tabs (HTML only, decorative)
tabs_html = f'<div class="page-tabs">'
for p in PAGES:
    active = "active" if page == p else ""
    tabs_html += f'<span class="ptab {active}">{p}</span>'
tabs_html += '</div>'
st.markdown(tabs_html, unsafe_allow_html=True)

# Actual clickable nav using columns of buttons
nav_cols = st.columns([1,1,1,1,1,2,1])
pages_btns = PAGES
for i, (col, pg) in enumerate(zip(nav_cols[:5], pages_btns)):
    with col:
        if st.button(pg, key=f"nav_{pg}", use_container_width=True):
            st.session_state.page = pg
            st.rerun()

with nav_cols[5]:
    pass  # spacer

with nav_cols[6]:
    dm_label = "☀ Light" if dm else "☾ Dark"
    if st.button(dm_label, key="dm_btn"):
        st.session_state.dark = not dm
        st.rerun()

# Also keep a compact refresh
ref_col, _ = st.columns([1, 10])
with ref_col:
    if st.button("↻", key="ref_btn", help="Refresh data"):
        st.cache_data.clear()
        st.rerun()

page = st.session_state.page  # re-read after potential rerun

# ══════════════════════════════════════════════════════════════════════════
# ██  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════
if page == "Dashboard":

    # Hero with 3D SVG decoration
    st.markdown(f"""
    <div class="hero anim-up">
      <svg class="hero-3d" viewBox="0 0 300 300" fill="none">
        <defs>
          <radialGradient id="rg1" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="{ACC}" stop-opacity=".6"/>
            <stop offset="100%" stop-color="{ACC}" stop-opacity="0"/>
          </radialGradient>
        </defs>
        <circle cx="150" cy="150" r="130" stroke="{ACC}" stroke-width="1" stroke-dasharray="6 4" opacity=".5"
                style="animation:orbit 20s linear infinite;transform-origin:150px 150px;"/>
        <circle cx="150" cy="150" r="90" stroke="{YACC}" stroke-width="1" stroke-dasharray="4 6" opacity=".4"
                style="animation:orbit 14s linear infinite reverse;transform-origin:150px 150px;"/>
        <circle cx="150" cy="150" r="50" fill="url(#rg1)" style="animation:float 6s ease-in-out infinite;"/>
        <circle cx="150" cy="150" r="22" fill="{ACC}" opacity=".7"/>
        <circle cx="150" cy="32" r="8" fill="{YACC}" opacity=".9"
                style="animation:orbit 20s linear infinite;transform-origin:150px 150px;"/>
        <circle cx="230" cy="150" r="5" fill="{ACC}" opacity=".8"
                style="animation:orbit 14s linear infinite reverse;transform-origin:150px 150px;"/>
      </svg>
      <div class="hero-inner">
        <div class="hero-eyebrow">Agrolinking Research &amp; Data</div>
        <h1 class="hero-h1">The Price Intelligence<br>for <mark>African Agriculture</mark></h1>
        <p class="hero-body">AI-powered daily, weekly, and long-range commodity price forecasts
        for Nigeria's key agricultural export markets — driven by ARIMA, Prophet and XGBoost.</p>
        <div class="kpis">
          <div class="kpi anim-up d1"><div class="kpi-n">{n_c}</div><div class="kpi-l">Commodities</div></div>
          <div class="kpi anim-up d2"><div class="kpi-n">{n_m}</div><div class="kpi-l">Movers Today</div></div>
          <div class="kpi anim-up d3"><div class="kpi-n">3</div><div class="kpi-l">Models</div></div>
          <div class="kpi anim-up d4"><div class="kpi-n">{fc_dt or '—'}</div><div class="kpi-l">Last Updated</div></div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    if not fc:
        st.info("No forecast data. Run: `python3 run_pipeline.py`")
        st.stop()

    # Stat cards
    all_pcts = [pct(fc[c].get('daily',0), yest.get(c,{}).get('daily'))
                for c in COMMODITIES if c in fc and yest.get(c,{}).get('daily')]
    n_up   = sum(1 for p in all_pcts if p and p > 1)
    n_dn   = sum(1 for p in all_pcts if p and p < -1)
    top_g  = max((c for c in COMMODITIES if c in fc),
                 key=lambda c: pct(fc[c].get('daily',0), yest.get(c,{}).get('daily')) or -999, default="—")
    tg_pct = pct(fc.get(top_g,{}).get('daily',0), yest.get(top_g,{}).get('daily')) if top_g in fc else None

    st.markdown(f"""
    <div class="content anim-up d1">
      <div class="section-hd">
        <span class="eyebrow">Market Summary</span>
        <span class="section-h2">Today at a Glance</span>
      </div>
    </div>""", unsafe_allow_html=True)

    sc = '<div style="padding:0 48px;"><div class="stat-grid">'
    for i,(lbl,val,sub) in enumerate([
        ("Total Commodities", str(n_c), "tracked in pipeline"),
        ("Rising Today", str(n_up), "price increase"),
        ("Falling Today", str(n_dn), "price decrease"),
        ("Top Gainer", top_g, f"+{tg_pct:.1f}% today" if tg_pct else "—"),
    ]):
        sc += f'<div class="stat-card anim-up" style="animation-delay:{i*.07}s"><div class="stat-label">{lbl}</div><div class="stat-value">{val}</div><div class="stat-sub">{sub}</div></div>'
    sc += '</div></div>'
    st.markdown(sc, unsafe_allow_html=True)

    # Price trend chart
    st.markdown(f"""
    <div class="content anim-up d2">
      <div class="section-hd">
        <span class="eyebrow">Historical + Forecast</span>
        <span class="section-h2">Price Trend</span>
      </div>
    </div>""", unsafe_allow_html=True)

    if not master.empty:
        c1, c2 = st.columns([2,5])
        with c1:
            st.markdown(f"<div style='padding:0 0 16px 48px;'>", unsafe_allow_html=True)
            sel = st.selectbox("Commodity", [c for c in COMMODITIES if c in fc],
                               label_visibility="collapsed", key="d_sel")
            st.markdown("</div>", unsafe_allow_html=True)

        hist = master[(master['commodity']==sel)&(master['record_type']=='historical')].sort_values('week_start_date').tail(65)
        fore = master[(master['commodity']==sel)&(master['record_type']=='forecast')].sort_values('week_start_date').tail(30)
        lc   = DOTS.get(sel, MID)
        fc_c = fc.get(sel, {})

        fig = go.Figure()
        if fc_c.get('monthly') and isinstance(fc_c['monthly'], dict):
            m = fc_c['monthly']
            if m.get('lower') and m.get('upper'):
                try:
                    r,g,b = int(lc[1:3],16),int(lc[3:5],16),int(lc[5:7],16)
                    fig.add_hrect(y0=m['lower'],y1=m['upper'],
                        fillcolor=f"rgba({r},{g},{b},.07)",
                        line=dict(color=f"rgba({r},{g},{b},.2)",width=1),
                        annotation_text="1-month range",
                        annotation_font=dict(size=11,color=CTXT,family='Golos Text'),
                        annotation_position="top right")
                except: pass

        if not hist.empty:
            fig.add_trace(go.Scatter(x=hist['week_start_date'],y=hist['price'],
                name='Historical',mode='lines',
                line=dict(color=lc,width=2.2),
                hovertemplate='<b>%{x|%d %b %Y}</b><br>₦%{y:,.0f}/MT<extra></extra>'))
        if not fore.empty:
            fig.add_trace(go.Scatter(x=fore['week_start_date'],y=fore['price'],
                name='Forecast',mode='lines+markers',
                line=dict(color=YELLOW,width=2,dash='dot'),
                marker=dict(size=5,color=YELLOW),
                hovertemplate='<b>%{x|%d %b %Y}</b><br>₦%{y:,.0f}/MT (forecast)<extra></extra>'))

        cfg = chart_cfg(380)
        cfg['xaxis']['tickformat'] = '%b %Y'
        cfg['xaxis']['title'] = dict(text='Date',font=dict(size=12,color=CTXT,family='Golos Text'))
        cfg['yaxis']['tickprefix'] = '₦'
        cfg['yaxis']['tickformat'] = ',.0f'
        cfg['yaxis']['title'] = dict(text='Price (NGN/MT)',font=dict(size=12,color=CTXT,family='Golos Text'))
        fig.update_layout(**cfg)

        st.markdown("<div style='padding:0 48px;'><div class='chart-wrap'>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True,
                        config={'displayModeBar':True,'displaylogo':False,
                                'modeBarButtonsToRemove':['select2d','lasso2d','autoScale2d']})
        st.markdown("</div></div>", unsafe_allow_html=True)

    # Movement
    st.markdown(f"""
    <div class="content anim-up d3">
      <div class="section-hd">
        <span class="eyebrow">vs Previous Day</span>
        <span class="section-h2">Market Movement</span>
      </div>
    </div>""", unsafe_allow_html=True)

    mv = ""
    for c in COMMODITIES:
        if c not in fc: continue
        tp  = fc[c].get('daily',0)
        yp  = yest.get(c,{}).get('daily') if yest else None
        pc_ = pct(tp,yp)
        if pc_ is None: continue
        d   = "up" if pc_>1 else ("down" if pc_<-1 else "flat")
        ptxt = f"+{pc_:.1f}%" if d=="up" else (f"{pc_:.1f}%" if d=="down" else "Stable")
        mv += f"""<div class="mv-row anim-right">
          {mv_ico(d)}
          <div class="mv-info">
            <div class="mv-name">{c}</div>
            <div class="mv-sub">{fmt(yp)} &rarr; {fmt(tp)} &nbsp;&middot;&nbsp; NGN/MT</div>
          </div>
          <div class="mv-pct {d}">{ptxt}</div>
        </div>"""
    if not mv:
        mv = f'<div style="padding:24px;text-align:center;color:{TEXT3};">No previous data available.</div>'
    st.markdown(f'<div style="padding:0 48px;"><div class="mv-card">{mv}</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# ██  DAILY PRICES
# ══════════════════════════════════════════════════════════════════════════
elif page == "Daily Prices":
    st.markdown(f"""
    <div class="hero anim-up" style="padding:60px 48px 52px;">
      <div class="hero-inner">
        <div class="hero-eyebrow">Live Forecast</div>
        <h1 class="hero-h1" style="font-size:46px;">Today's Commodity Prices</h1>
        <p class="hero-body">Daily AI-generated price forecasts for all tracked commodities.</p>
      </div>
    </div>""", unsafe_allow_html=True)

    if not fc:
        st.info("No forecast data. Run the pipeline first.")
        st.stop()

    st.markdown(f"""
    <div class="content">
      <div class="section-hd">
        <span class="eyebrow">Daily Forecast</span>
        <span class="section-h2">All Commodities</span>
      </div>
    </div>""", unsafe_allow_html=True)

    cards = ""
    for i,c in enumerate(COMMODITIES):
        if c not in fc: continue
        price = fc[c].get('daily',0)
        yp    = yest.get(c,{}).get('daily') if yest else None
        pc_   = pct(price,yp)
        d     = "up" if (pc_ and pc_>1) else ("down" if (pc_ and pc_<-1) else "flat")
        prev  = f"Prev: {fmt(yp)}" if yp else "First forecast"
        cards += f"""<div class="pcard {d} anim-up" style="animation-delay:{i*.05}s">
          <div class="pcard-name">{dot(c)} {c}</div>
          <div class="pcard-price">{fmt(price)}</div>
          <div class="pcard-unit">NGN / Tonne</div>
          {chip_html(pc_)}
          <div class="pcard-prev">{prev}</div>
        </div>"""
    st.markdown(f'<div style="padding:0 48px;"><div class="pgrid">{cards}</div></div>', unsafe_allow_html=True)

    # Short-range table
    st.markdown(f"""
    <div class="content">
      <div class="section-hd">
        <span class="eyebrow">Weekly &amp; 2-Week</span>
        <span class="section-h2">Short-Range Outlook</span>
      </div>
    </div>""", unsafe_allow_html=True)

    nxt = NOW + timedelta(days=7-NOW.weekday() if NOW.weekday()!=0 else 7)
    twk = nxt + timedelta(weeks=1)
    rows = ""
    for c in COMMODITIES:
        if c not in fc: continue
        fc_c = fc[c]
        daily,weekly,biwk = fc_c.get('daily',0),fc_c.get('weekly',0),fc_c.get('biweekly',0)
        d = dirn(daily,weekly)
        rows += f"""<tr>
          <td><div class="td-name">{dot(c,8)} {c}</div></td>
          <td class="td-num">{fmt(daily)}</td>
          <td class="td-num">{fmt(weekly)}</td>
          <td class="td-num">{fmt(biwk)}</td>
          <td>{dir_td(d)}</td>
        </tr>"""
    st.markdown(f"""<div style="padding:0 48px;">
      <div class="tbl-wrap"><table class="tbl">
        <thead><tr>
          <th>Commodity</th><th>Daily (Today)</th>
          <th>w/c {nxt.day} {MONTHS_S[nxt.month-1]}</th>
          <th>w/c {twk.day} {MONTHS_S[twk.month-1]}</th>
          <th>Direction</th>
        </tr></thead><tbody>{rows}</tbody>
      </table></div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# ██  LONG RANGE
# ══════════════════════════════════════════════════════════════════════════
elif page == "Long-Range":
    st.markdown(f"""
    <div class="hero anim-up" style="padding:60px 48px 52px;">
      <div class="hero-inner">
        <div class="hero-eyebrow">Extended Outlook</div>
        <h1 class="hero-h1" style="font-size:46px;">Long-Range Price Forecasts</h1>
        <p class="hero-body">Monthly, quarterly and 6-month price ranges with confidence levels and trend signals.</p>
      </div>
    </div>""", unsafe_allow_html=True)

    if not fc:
        st.info("No forecast data. Run the pipeline first.")
        st.stop()

    m1 = NOW+timedelta(weeks=4)
    m3 = NOW+timedelta(weeks=13)
    m6 = NOW+timedelta(weeks=26)
    CFG = [
        ('monthly',f"1-Month — {MONTHS_L[m1.month-1]} {m1.year}",'h1','High Confidence','high'),
        ('q3month',f"3-Month — {MONTHS_L[m3.month-1]} {m3.year}",'h3','Medium Confidence','mid'),
        ('q6month',f"6-Month — {MONTHS_L[m6.month-1]} {m6.year}",'h6','Low Confidence','low'),
    ]

    st.markdown(f"""
    <div class="content">
      <div class="section-hd">
        <span class="eyebrow">1-Month · 3-Month · 6-Month</span>
        <span class="section-h2">Price Range Outlook</span>
      </div>
    </div>""", unsafe_allow_html=True)

    lr_cards = ""
    for horizon,title,hcls,conf,ccls in CFG:
        inner = ""
        for c in COMMODITIES:
            if c not in fc: continue
            h     = fc[c].get(horizon)
            daily = fc[c].get('daily',0)
            if h and isinstance(h,dict) and h.get('point'):
                rng = f"{fmtM(h['lower'])} &ndash; {fmtM(h['upper'])}"
                d   = dirn(daily,h['point'])
            else:
                rng,d = "&mdash;","flat"
            inner += f"""<div class="lr-row">
              <div class="lr-name">{dot(c,7)} {c}</div>
              <div class="lr-range">{rng}</div>
              {lr_arr(d)}
            </div>"""
        lr_cards += f"""<div class="lr-card anim-up">
          <div class="lr-hd {hcls}">
            <span class="lr-title">{title}</span>
            <span class="lr-badge {ccls}">{conf}</span>
          </div>{inner}
        </div>"""
    st.markdown(f'<div style="padding:0 48px;"><div class="lr-grid">{lr_cards}</div></div>', unsafe_allow_html=True)

    # Trajectory bar chart
    st.markdown(f"""
    <div class="content">
      <div class="section-hd">
        <span class="eyebrow">Visual</span>
        <span class="section-h2">Forecast Trajectory</span>
      </div>
    </div>""", unsafe_allow_html=True)

    ca,cb = st.columns([2,5])
    with ca:
        st.markdown("<div style='padding:0 0 16px 48px;'>", unsafe_allow_html=True)
        sel2 = st.selectbox("Select",[c for c in COMMODITIES if c in fc],
                            label_visibility="collapsed",key="lr_sel")
        st.markdown("</div>", unsafe_allow_html=True)

    fc_c = fc.get(sel2,{}); lc2 = DOTS.get(sel2,MID)
    h_labs = ['Today','Week','2-Week','1-Month','3-Month','6-Month']
    h_keys = ['daily','weekly','biweekly','monthly','q3month','q6month']
    h_vals,h_lo,h_hi = [],[],[]
    for hk in h_keys:
        v = fc_c.get(hk)
        if isinstance(v,dict):
            h_vals.append(v.get('point',0) or 0)
            h_lo.append(v.get('lower',0) or 0)
            h_hi.append(v.get('upper',0) or 0)
        else:
            h_vals.append(v or 0)
            h_lo.append(v or 0)
            h_hi.append(v or 0)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=h_labs,y=h_vals,
        marker_color=[lc2 if i<3 else YELLOW for i in range(6)],
        marker_line_width=0,
        hovertemplate='%{x}: ₦%{y:,.0f}<extra></extra>'))

    cfg2 = chart_cfg(300,64,20,20,44)
    cfg2['yaxis']['tickprefix']='₦';cfg2['yaxis']['tickformat']=',.0f'
    cfg2['yaxis']['title']=dict(text='Price (NGN/MT)',font=dict(size=12,color=CTXT,family='Golos Text'))
    cfg2['showlegend']=False
    fig2.update_layout(**cfg2)
    st.markdown("<div style='padding:0 48px;'><div class='chart-wrap'>", unsafe_allow_html=True)
    st.plotly_chart(fig2,use_container_width=True,config={'displayModeBar':False})
    st.markdown("</div></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# ██  MODEL ANALYSIS — FULL VERSION
# ══════════════════════════════════════════════════════════════════════════
elif page == "Model Analysis":
    st.markdown(f"""
    <div class="hero anim-up" style="padding:60px 48px 52px;">
      <div class="hero-inner">
        <div class="hero-eyebrow">Under the Hood</div>
        <h1 class="hero-h1" style="font-size:46px;">Forecast Model Analysis</h1>
        <p class="hero-body">Comparing ARIMA, Prophet and XGBoost outputs with cross-reference validation,
        model performance insights and commodity-level breakdowns.</p>
      </div>
    </div>""", unsafe_allow_html=True)

    if not fc:
        st.info("No forecast data. Run the pipeline first.")
        st.stop()

    # ── Model insight cards
    comms = [c for c in COMMODITIES if c in fc]
    arima_vals   = [fc[c].get('all_models',{}).get('arima',  0) or 0 for c in comms]
    prophet_vals = [fc[c].get('all_models',{}).get('prophet',0) or 0 for c in comms]
    xgb_vals     = [fc[c].get('all_models',{}).get('xgboost',0) or 0 for c in comms]

    wc = {'arima':0,'prophet':0,'xgboost':0,'ensemble':0}
    for c in COMMODITIES:
        if c in fc:
            m = fc[c].get('model','ensemble')
            wc[m if m in wc else 'ensemble'] += 1

    st.markdown(f"""
    <div class="content">
      <div class="section-hd">
        <span class="eyebrow">Model Performance</span>
        <span class="section-h2">At a Glance</span>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding:0 48px;">
      <div class="insight-grid">
        <div class="insight-card arima anim-up d1">
          <div class="insight-model">ARIMA</div>
          <div class="insight-score">{wc['arima']}</div>
          <div class="insight-label">commodities where ARIMA won</div>
          <div style="margin-top:16px;font-size:12.5px;color:{TEXT2};line-height:1.6;">
            Time-series model capturing autocorrelation, trend and moving average patterns.
            Best for stable, slowly-changing commodity prices.
          </div>
        </div>
        <div class="insight-card prophet anim-up d2">
          <div class="insight-model">Prophet</div>
          <div class="insight-score">{wc['prophet']}</div>
          <div class="insight-label">commodities where Prophet won</div>
          <div style="margin-top:16px;font-size:12.5px;color:{TEXT2};line-height:1.6;">
            Meta's forecasting library. Handles seasonal cycles, holidays and structural
            breaks — ideal for commodities with harvest-cycle seasonality.
          </div>
        </div>
        <div class="insight-card xgboost anim-up d3">
          <div class="insight-model">XGBoost</div>
          <div class="insight-score">{wc['xgboost']}</div>
          <div class="insight-label">commodities where XGBoost won</div>
          <div style="margin-top:16px;font-size:12.5px;color:{TEXT2};line-height:1.6;">
            Gradient-boosted trees with lag features. Best at capturing non-linear
            relationships and recent momentum shifts in price data.
          </div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Ensemble note
    if wc['ensemble'] > 0:
        st.markdown(f"""
        <div style="padding:0 48px 32px;">
          <div style="background:{BG2};border:1px solid {BORDER};border-radius:12px;padding:18px 22px;
                      display:flex;align-items:center;gap:16px;">
            <div style="width:36px;height:36px;border-radius:9px;background:{UPBG};
                        display:flex;align-items:center;justify-content:center;flex-shrink:0;">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 2L14 6V10L8 14L2 10V6L8 2Z" stroke="{ACC}" stroke-width="1.5" fill="none"/>
                <circle cx="8" cy="8" r="2" fill="{ACC}"/>
              </svg>
            </div>
            <div>
              <div style="font-weight:600;font-size:13.5px;color:{TEXT};">Ensemble Fallback — {wc['ensemble']} commodity(ies)</div>
              <div style="font-size:12px;color:{TEXT3};margin-top:2px;">
                When no external reference is available, the system uses a weighted average of Prophet (50%) + XGBoost (35%) + ARIMA (15%).
              </div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    # Comparison bar chart + pie
    st.markdown(f"""
    <div class="content">
      <div class="section-hd">
        <span class="eyebrow">ARIMA · Prophet · XGBoost</span>
        <span class="section-h2">Model Comparison by Commodity</span>
      </div>
    </div>""", unsafe_allow_html=True)

    col_a, col_b = st.columns([3,2])
    with col_a:
        st.markdown("<div style='padding:0 0 0 48px;'>", unsafe_allow_html=True)
        fig3 = go.Figure()
        for name,vals,color in [('ARIMA',arima_vals,'#4CAF50'),('Prophet',prophet_vals,YELLOW),('XGBoost',xgb_vals,DARK)]:
            fig3.add_trace(go.Bar(name=name,x=comms,y=vals,
                marker_color=color,marker_line_width=0,
                hovertemplate=f'<b>%{{x}}</b><br>{name}: ₦%{{y:,.0f}}<extra></extra>'))
        cfg3 = chart_cfg(320,70,10,24,80)
        cfg3['barmode']='group'
        cfg3['yaxis']['tickprefix']='₦';cfg3['yaxis']['tickformat']=',.0f'
        cfg3['yaxis']['title']=dict(text='Price (NGN/MT)',font=dict(size=12,color=CTXT,family='Golos Text'))
        cfg3['xaxis']['tickangle']=-30;cfg3['xaxis']['tickfont']['size']=10
        fig3.update_layout(**cfg3)
        st.markdown("<div class='chart-wrap'>", unsafe_allow_html=True)
        st.plotly_chart(fig3,use_container_width=True,config={'displayModeBar':False})
        st.markdown("</div></div>", unsafe_allow_html=True)

    with col_b:
        fig4 = go.Figure(go.Pie(
            labels=['ARIMA','Prophet','XGBoost','Ensemble'],
            values=[wc['arima'],wc['prophet'],wc['xgboost'],wc['ensemble']],
            hole=0.58,
            marker_colors=['#4CAF50',YELLOW,DARK,'#757575'],
            marker_line=dict(color=CBG,width=2),
            textinfo='label+percent',
            textfont=dict(family='Golos Text, sans-serif',size=11,color=CTXT),
            hovertemplate='%{label}: %{value}<extra></extra>'))
        cfg4 = dict(showlegend=False,plot_bgcolor=CBG,paper_bgcolor=CBG,
                    margin=dict(l=0,r=0,t=24,b=10),height=300,
                    hoverlabel=dict(bgcolor=CBG,bordercolor=CBRD,font=dict(family='Golos Text',size=12,color=CTXT)),
                    annotations=[dict(text='Winners',x=.5,y=.5,
                        font=dict(size=12,family='Bricolage Grotesque',color=CTXT),showarrow=False)])
        fig4.update_layout(**cfg4)
        st.markdown("<div style='padding:0 48px 0 0;'><div class='chart-wrap'>", unsafe_allow_html=True)
        st.plotly_chart(fig4,use_container_width=True,config={'displayModeBar':False})
        st.markdown("</div></div>", unsafe_allow_html=True)

    # Per-commodity accuracy breakdown
    st.markdown(f"""
    <div class="content">
      <div class="section-hd">
        <span class="eyebrow">Validation Results</span>
        <span class="section-h2">Commodity-Level Breakdown</span>
      </div>
    </div>""", unsafe_allow_html=True)

    tbl_rows = ""
    for c in COMMODITIES:
        if c not in fc: continue
        fc_c    = fc[c]
        model   = fc_c.get('model','ensemble').title()
        err     = f"{fc_c['error_pct']:.1f}%" if fc_c.get('error_pct') else "N/A"
        ref     = fmt(fc_c.get('reference')) if fc_c.get('reference') else "No reference"
        flag    = fc_c.get('flag','—')
        daily   = fmt(fc_c.get('daily',0))
        weekly  = fmt(fc_c.get('weekly',0))
        monthly = fmtM(fc_c.get('monthly',{}).get('point') if isinstance(fc_c.get('monthly'),dict) else fc_c.get('monthly')) if fc_c.get('monthly') else "—"
        tbl_rows += f"""<tr>
          <td><div class="td-name">{dot(c,8)} {c}</div></td>
          <td class="td-num">{daily}</td>
          <td class="td-num">{weekly}</td>
          <td class="td-num">{monthly}</td>
          <td style="font-weight:600;color:{ACC};">{model}</td>
          <td style="color:{TEXT3};">{err}</td>
          <td style="color:{TEXT3};">{ref}</td>
          <td style="font-size:12px;color:{TEXT3};">{flag}</td>
        </tr>"""

    st.markdown(f"""<div style="padding:0 48px 48px;">
      <div class="tbl-wrap"><table class="tbl">
        <thead><tr>
          <th>Commodity</th><th>Daily</th><th>Weekly</th><th>1-Month</th>
          <th>Model</th><th>X-Ref Error</th><th>Reference</th><th>Status</th>
        </tr></thead>
        <tbody>{tbl_rows}</tbody>
      </table></div>
    </div>""", unsafe_allow_html=True)

    # Accuracy line chart
    st.markdown(f"""
    <div class="content">
      <div class="section-hd">
        <span class="eyebrow">Historical Accuracy</span>
        <span class="section-h2">Model Agreement Over Time</span>
      </div>
    </div>""", unsafe_allow_html=True)

    if not master.empty:
        ca2,cb2 = st.columns([2,5])
        with ca2:
            st.markdown("<div style='padding:0 0 16px 48px;'>", unsafe_allow_html=True)
            sel3 = st.selectbox("Select commodity",[c for c in COMMODITIES if c in fc],
                                label_visibility="collapsed",key="ma_sel")
            st.markdown("</div>", unsafe_allow_html=True)

        hist2 = master[(master['commodity']==sel3)&(master['record_type']=='historical')].sort_values('week_start_date').tail(40)
        fore2 = master[(master['commodity']==sel3)&(master['record_type']=='forecast')].sort_values('week_start_date').tail(20)
        lc3   = DOTS.get(sel3,MID)

        fig5 = go.Figure()
        if not hist2.empty:
            fig5.add_trace(go.Scatter(x=hist2['week_start_date'],y=hist2['price'],
                name='Actual',mode='lines',line=dict(color=lc3,width=2),
                hovertemplate='<b>%{x|%d %b %Y}</b><br>₦%{y:,.0f}/MT<extra></extra>'))
        if not fore2.empty:
            fig5.add_trace(go.Scatter(x=fore2['week_start_date'],y=fore2['price'],
                name='Forecast',mode='lines+markers',
                line=dict(color=YELLOW,width=2,dash='dot'),
                marker=dict(size=5,color=YELLOW),
                hovertemplate='<b>%{x|%d %b %Y}</b><br>₦%{y:,.0f}/MT (fc)<extra></extra>'))

        cfg5 = chart_cfg(320)
        cfg5['xaxis']['tickformat']='%b %Y'
        cfg5['xaxis']['title']=dict(text='Date',font=dict(size=12,color=CTXT,family='Golos Text'))
        cfg5['yaxis']['tickprefix']='₦';cfg5['yaxis']['tickformat']=',.0f'
        cfg5['yaxis']['title']=dict(text='Price (NGN/MT)',font=dict(size=12,color=CTXT,family='Golos Text'))
        fig5.update_layout(**cfg5)
        st.markdown("<div style='padding:0 48px;'><div class='chart-wrap'>", unsafe_allow_html=True)
        st.plotly_chart(fig5,use_container_width=True,config={'displayModeBar':False})
        st.markdown("</div></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# ██  ABOUT — fixed layout
# ══════════════════════════════════════════════════════════════════════════
elif page == "About":
    st.markdown(f"""
    <div class="about-hero anim-in">
      <div class="about-hero-bg"></div>
      <div class="about-hero-inner">
        <div>
          <h1 class="about-h1">Built on <mark>Data.</mark><br>Driven by Insight.</h1>
          <p class="about-sub">Agrolinking's Commodity Intelligence System delivers AI-powered
          price forecasting for Nigerian agricultural markets — powering smarter decisions
          across the entire value chain, from farm gate to export market.</p>
        </div>
        <div class="about-stats">
          <div class="about-stat anim-up d1">
            <div class="about-stat-n">{n_c}</div>
            <div class="about-stat-l">Commodities Tracked</div>
          </div>
          <div class="about-stat anim-up d2">
            <div class="about-stat-n">3</div>
            <div class="about-stat-l">Forecast Models</div>
          </div>
          <div class="about-stat anim-up d3">
            <div class="about-stat-n">6</div>
            <div class="about-stat-l">Forecast Horizons</div>
          </div>
          <div class="about-stat anim-up d4">
            <div class="about-stat-n">Daily</div>
            <div class="about-stat-l">Pipeline Frequency</div>
          </div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="content">
      <div class="section-hd">
        <span class="eyebrow">How It Works</span>
        <span class="section-h2">The Intelligence Pipeline</span>
      </div>
    </div>""", unsafe_allow_html=True)

    features = [
        ("01","Data Ingestion","Weekly commodity prices from Agricom Africa's market posts, cleaned and standardised into NGN/MT format across 9 commodities including Hibiscus, Ginger, Cocoa, and Beans."),
        ("02","Three-Model Ensemble","ARIMA captures time-series patterns, Prophet models seasonality and structural breaks, XGBoost learns non-linear feature relationships. All three run in parallel every day."),
        ("03","Cross-Reference Validation","Forecasts are validated against live data from AFEX, Tridge, and Agricom with ensemble fallback when external references are unavailable or show outlier values."),
        ("04","Daily & Long-Range Output","Pipeline generates daily, weekly, 2-week, monthly, 3-month and 6-month forecasts — each with confidence intervals, trend signals and model attribution."),
        ("05","Living Dataset","Every forecast is appended to the master dataset, creating a self-improving recycling loop where models train on validated predictions over time."),
        ("06","Ready-to-Share Reports","Formatted price messages in Agricom post style are generated automatically — ready to copy-paste to WhatsApp or your team communication channels."),
    ]

    feat_html = '<div style="padding:0 48px;"><div class="feature-grid">'
    for i,(num,title,body) in enumerate(features):
        feat_html += f"""
        <div class="feature-card anim-up" style="animation-delay:{i*.07}s">
          <div class="feature-num">{num}</div>
          <div class="feature-h3">{title}</div>
          <p class="feature-p">{body}</p>
        </div>"""
    feat_html += '</div></div>'
    st.markdown(feat_html, unsafe_allow_html=True)

    # Commodities grid
    st.markdown(f"""
    <div class="content">
      <div class="section-hd">
        <span class="eyebrow">Coverage</span>
        <span class="section-h2">Tracked Commodities</span>
      </div>
    </div>""", unsafe_allow_html=True)

    cg = '<div style="padding:0 48px 48px;"><div class="pgrid">'
    for i,c in enumerate(COMMODITIES):
        d_ = DOTS.get(c,"#888")
        price = fc.get(c,{}).get('daily',0) if fc else 0
        pc_   = pct(price, yest.get(c,{}).get('daily')) if yest.get(c,{}).get('daily') else None
        dir_c = "up" if (pc_ and pc_>1) else ("down" if (pc_ and pc_<-1) else "flat")
        cg += f"""<div class="pcard {dir_c} anim-up" style="animation-delay:{i*.05}s">
          <div class="pcard-name"><span class="dot" style="width:9px;height:9px;background:{d_};"></span> {c}</div>
          <div class="pcard-price">{fmt(price)}</div>
          <div class="pcard-unit">NGN / Tonne &nbsp;·&nbsp; Latest forecast</div>
          {chip_html(pc_)}
        </div>"""
    cg += '</div></div>'
    st.markdown(cg, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# FOOTER — rich, polished, gradient
# ══════════════════════════════════════════════════════════════════════════
logo_f = (f'<img src="data:image/png;base64,{logo_b64}" height="24" '
          'style="filter:brightness(0) invert(1);margin-bottom:12px;" alt="Agrolinking">'
          if logo_b64 else
          '<span style="font-family:\'Bricolage Grotesque\',sans-serif;font-size:20px;font-weight:800;color:#fff;margin-bottom:12px;display:block;">agrolinking</span>')

st.markdown(f"""
<div class="footer">
  <div class="footer-glow"></div>
  <div class="footer-top">
    <div class="footer-logo-area">
      {logo_f}
      <div class="footer-brand">Agrolinking</div>
      <div class="footer-brand-tag">Redefining the future of agricultural connection in Africa — powered by data, driven by impact.</div>
      <div class="footer-badge">
        <span class="footer-badge-dot"></span>
        Live Data Active
      </div>
    </div>
    <div>
      <div class="footer-col-title">Platform</div>
      <span class="footer-link">Dashboard</span>
      <span class="footer-link">Daily Prices</span>
      <span class="footer-link">Long-Range Outlook</span>
      <span class="footer-link">Model Analysis</span>
      <span class="footer-link">About</span>
    </div>
    <div>
      <div class="footer-col-title">Data Sources</div>
      <span class="footer-link">Agricom Africa</span>
      <span class="footer-link">WFP Nigeria Food Prices</span>
      <span class="footer-link">AFEX Market Data</span>
      <span class="footer-link">Tridge Intelligence</span>
    </div>
    <div>
      <div class="footer-col-title">Company</div>
      <a href="https://agrolinking.com" class="footer-link-a">agrolinking.com</a>
      <a href="https://agrolinking.com/about-us" class="footer-link-a">About Us</a>
      <a href="https://agrolinking.com/contact-us" class="footer-link-a">Contact</a>
      <span class="footer-link">Last pipeline: {fc_dt or '—'}</span>
    </div>
  </div>
  <div class="footer-bottom">
    <div class="footer-copy">
      &copy; {NOW.year} Agrolinking Solutions &nbsp;&middot;&nbsp;
      ARIMA &middot; Prophet &middot; XGBoost &nbsp;&middot;&nbsp;
      <a href="https://agrolinking.com">agrolinking.com</a>
    </div>
    <div class="footer-disclaimer">
      Forecasts are AI-generated for informational purposes only.
      Always verify against current market conditions before commercial decisions.
    </div>
  </div>
</div>
""", unsafe_allow_html=True)