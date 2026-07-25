"""
streamlit_app.py  –  J&J MedTech  |  Code Automation
Run:  streamlit run streamlit_app.py
"""

import base64
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from ads_automation.parser import parse_protocol
from ads_automation.notebook_generator import create_notebook


# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Code Automation | J&J MedTech", layout="wide", page_icon=None)
# ─────────────────────────────────────────────────────────────────────────────

_LOGO_PATH    = Path(r"C:\Users\deepak.r\Downloads\jnjlogo.png")
_LOGO_WEB_URL = (
    "https://play-lh.googleusercontent.com/"
    "goJEGZ2I1rekFkK_Os2Hq6tgG_Iz07Wy6CyW2ti-Tn-j9_SiFVfAoQ6qKZKRJT-O_znd4tgvOgWK_8uHxWcBOQ"
)
_MUSIGMA_LOGO_URL = (
    "https://yt3.googleusercontent.com/ytc/"
    "AIdro_k-7HkbByPWjKpVPO3LCF8XYlKuQuwROO0vf3zo1cqgoaE=s900-c-k-c0x00ffffff-no-rj"
)

def _logo_src() -> str:
    """Local file as base64 data-URI (portable); falls back to web URL on VDI / any machine."""
    if _LOGO_PATH.exists():
        b64 = base64.b64encode(_LOGO_PATH.read_bytes()).decode()
        return f"data:image/png;base64,{b64}"
    return _LOGO_WEB_URL


JNJ_RED     = "#eb1700"
JNJ_MAROON  = "#9e0000"
JNJ_GRAY_01 = "#f5f4f2"
JNJ_GRAY_02 = "#eae8e5"
JNJ_GRAY_03 = "#d5cfc9"
JNJ_GRAY_05 = "#a39992"
JNJ_GRAY_06 = "#81766f"
JNJ_GRAY_08 = "#1a1410"
JNJ_BLUE_01 = "#69d0ff"
JNJ_BLUE_03 = "#0f68b2"
JNJ_BLUE_05 = "#004685"
JNJ_GREEN_03 = "#328714"
JNJ_ORANGE  = "#ff6017"


st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Roboto+Mono:wght@400;500;600&display=swap');

/* ── global box model ── */
*, *::before, *::after {{ box-sizing: border-box; }}

/* ── reset & base ── */
html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background-color: {JNJ_GRAY_01};
    color: {JNJ_GRAY_08};
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}}
.stApp {{ background-color: {JNJ_GRAY_01}; }}

/* ── hide Streamlit chrome ── */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 0 !important; max-width: 100% !important; }}

/* ── app container: clamp padding so content never hugs edges ── */
[data-testid="stAppViewContainer"] {{
    padding: 0 clamp(0.75rem, 2.5vw, 2rem);
}}

/* ════════════════════════════════════════════════════
   FLUID INNER WRAPPER SYSTEM
   Every section centres itself and breathes at all zoom levels
════════════════════════════════════════════════════ */
.jnj-inner {{
    width: 100%;
    max-width: min(1180px, 100%);
    margin-left: auto;
    margin-right: auto;
    padding-left:  clamp(1rem, 3.5vw, 2.75rem);
    padding-right: clamp(1rem, 3.5vw, 2.75rem);
}}

/* ════════════════════════════════════════════════════
   TOP NAVIGATION BAR
════════════════════════════════════════════════════ */
.jnj-nav {{
    background: #ffffff;
    border-bottom: 3px solid {JNJ_RED};
    position: sticky;
    top: 0;
    z-index: 999;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
}}
.jnj-nav-inner {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: clamp(0.6rem, 1.5vw, 1rem);
    padding-bottom: clamp(0.6rem, 1.5vw, 1rem);
}}
.jnj-logo-wrap {{
    display: flex;
    align-items: center;
    gap: clamp(10px, 2vw, 18px);
    flex-shrink: 0;
}}
.jnj-logo-divider {{
    width: 1px;
    height: clamp(20px, 3vw, 30px);
    background: {JNJ_GRAY_03};
    flex-shrink: 0;
}}
.jnj-logo-text {{
    font-size: clamp(0.78rem, 1.2vw, 0.92rem);
    font-weight: 700;
    color: {JNJ_GRAY_08};
    letter-spacing: 0.01em;
    line-height: 1.2;
}}
.jnj-logo-sub {{
    font-size: clamp(0.55rem, 0.8vw, 0.65rem);
    font-weight: 500;
    color: {JNJ_GRAY_05};
    letter-spacing: 0.06em;
    text-transform: uppercase;
    display: block;
    margin-top: 2px;
}}
.jnj-nav-right {{
    display: flex;
    align-items: center;
    gap: clamp(0.75rem, 2vw, 2rem);
    flex-shrink: 0;
}}
.jnj-nav-tag {{
    font-size: clamp(0.58rem, 0.9vw, 0.72rem);
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {JNJ_GRAY_05};
}}
.jnj-nav-version {{
    font-size: clamp(0.55rem, 0.8vw, 0.65rem);
    font-family: 'Roboto Mono', monospace;
    color: {JNJ_GRAY_06};
    background: {JNJ_GRAY_02};
    padding: 3px 10px;
    border-radius: 100px;
    white-space: nowrap;
}}
/* "Powered by Mu Sigma" block in nav */
.jnj-nav-built-by {{
    display: flex;
    align-items: center;
    gap: 7px;
    background: #ffffff;
    border: 1.5px solid {JNJ_GRAY_03};
    border-radius: 7px;
    padding: 5px 12px 5px 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}}
.jnj-nav-built-label {{
    font-size: clamp(0.62rem, 0.9vw, 0.72rem);
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: {JNJ_GRAY_08};
    white-space: nowrap;
}}

/* "Powered by" strip in sidebar */
.sidebar-built-by {{
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 9px;
    background: {JNJ_GRAY_01};
    border: 1px solid {JNJ_GRAY_02};
    border-radius: 5px;
    padding: 4px 8px;
    width: fit-content;
}}
.sidebar-built-label {{
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: {JNJ_GRAY_08};
}}

/* Hide nav right elements on very small viewports / high zoom */
@media screen and (max-width: 580px) {{
    .jnj-nav-tag {{ display: none; }}
    .jnj-nav-built-by {{ display: none; }}
    .jnj-logo-text {{ display: none; }}
    .jnj-logo-sub {{ display: none; }}
    .jnj-logo-divider {{ display: none; }}
}}

/* ════════════════════════════════════════════════════
   HERO BAND
════════════════════════════════════════════════════ */
.jnj-hero {{
    background: linear-gradient(135deg, {JNJ_GRAY_08} 0%, #231c18 60%, #1a0f0a 100%);
    padding: clamp(2.5rem, 6vw, 5rem) 0 clamp(2rem, 5vw, 4rem) 0;
    position: relative;
    overflow: hidden;
}}
/* left accent line */
.jnj-hero::before {{
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: clamp(4px, 0.5vw, 7px);
    height: 100%;
    background: linear-gradient(180deg, {JNJ_RED} 0%, {JNJ_MAROON} 100%);
}}
/* subtle dot grid texture */
.jnj-hero::after {{
    content: '';
    position: absolute;
    inset: 0;
    background-image: radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none;
}}
.jnj-hero-inner {{ position: relative; z-index: 1; }}
.jnj-hero-eyebrow {{
    font-size: clamp(0.55rem, 1vw, 0.68rem);
    font-weight: 700;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: {JNJ_RED};
    margin-bottom: clamp(0.6rem, 1.5vw, 1.1rem);
}}
.jnj-hero-title {{
    font-size: clamp(2.2rem, 5.5vw, 4.25rem);
    font-weight: 900;
    color: #ffffff;
    line-height: 1.03;
    letter-spacing: -0.04em;
    margin-bottom: 0;
}}
.jnj-hero-title span {{ color: {JNJ_RED}; }}
.jnj-hero-stats {{
    display: flex;
    gap: clamp(1.5rem, 4vw, 3rem);
    margin-top: clamp(1.75rem, 4vw, 2.75rem);
    padding-top: clamp(1.25rem, 3vw, 2rem);
    border-top: 1px solid rgba(255,255,255,0.09);
    flex-wrap: wrap;
}}
.jnj-hero-stat {{}}
.jnj-hero-stat-num {{
    font-size: clamp(1.6rem, 3.5vw, 2.4rem);
    font-weight: 900;
    color: #ffffff;
    line-height: 1;
    margin-bottom: 0.2rem;
    letter-spacing: -0.02em;
}}
.jnj-hero-stat-num span {{ color: {JNJ_RED}; }}
.jnj-hero-stat-label {{
    font-size: clamp(0.58rem, 0.9vw, 0.7rem);
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: {JNJ_GRAY_05};
}}

/* ════════════════════════════════════════════════════
   CONTENT WRAPPER
════════════════════════════════════════════════════ */
.jnj-content {{
    padding-top: clamp(1.75rem, 4vw, 3rem);
    padding-bottom: clamp(1.75rem, 4vw, 3rem);
}}

/* ════════════════════════════════════════════════════
   SECTION HEADERS (step circles)
════════════════════════════════════════════════════ */
.jnj-section-header {{
    display: flex;
    align-items: center;
    gap: clamp(0.65rem, 1.5vw, 1rem);
    margin-bottom: clamp(1rem, 2vw, 1.5rem);
    margin-top: clamp(1.75rem, 4vw, 2.75rem);
}}
.jnj-step-num {{
    width: clamp(28px, 4vw, 38px);
    height: clamp(28px, 4vw, 38px);
    min-width: clamp(28px, 4vw, 38px);
    background: {JNJ_RED};
    color: #fff;
    font-size: clamp(0.65rem, 1vw, 0.82rem);
    font-weight: 800;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 3px 10px rgba(235,23,0,0.3);
}}
.jnj-section-title {{
    font-size: clamp(1rem, 2vw, 1.25rem);
    font-weight: 700;
    color: {JNJ_GRAY_08};
    letter-spacing: -0.015em;
    line-height: 1.2;
}}
.jnj-section-title span {{
    display: block;
    font-size: clamp(0.7rem, 1.2vw, 0.8rem);
    font-weight: 400;
    color: {JNJ_GRAY_05};
    letter-spacing: 0.01em;
    margin-top: 2px;
}}

/* ════════════════════════════════════════════════════
   CARDS
════════════════════════════════════════════════════ */
.jnj-card {{
    background: #ffffff;
    border: 1px solid {JNJ_GRAY_02};
    border-radius: 10px;
    padding: clamp(1.25rem, 3vw, 2rem);
    margin-bottom: 1.25rem;
    box-shadow: 0 1px 6px rgba(0,0,0,0.045), 0 4px 16px rgba(0,0,0,0.03);
    transition: box-shadow 0.2s;
}}
.jnj-card:hover {{
    box-shadow: 0 2px 12px rgba(0,0,0,0.07), 0 6px 24px rgba(0,0,0,0.04);
}}
.jnj-card-red-top {{ border-top: 3px solid {JNJ_RED}; }}

/* ════════════════════════════════════════════════════
   META STRIP
════════════════════════════════════════════════════ */
.jnj-meta-strip {{
    background: #ffffff;
    border: 1px solid {JNJ_GRAY_02};
    border-left: 4px solid {JNJ_RED};
    border-radius: 0 10px 10px 0;
    padding: clamp(0.75rem, 2vw, 1.1rem) clamp(1rem, 2.5vw, 1.6rem);
    display: flex;
    gap: clamp(1rem, 4vw, 3rem);
    align-items: center;
    margin-bottom: clamp(1rem, 2.5vw, 1.6rem);
    flex-wrap: wrap;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}}
.jnj-meta-item {{ display: flex; flex-direction: column; gap: 3px; min-width: 0; }}
.jnj-meta-label {{
    font-size: clamp(0.55rem, 0.85vw, 0.62rem);
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: {JNJ_GRAY_05};
    white-space: nowrap;
}}
.jnj-meta-value {{
    font-size: clamp(0.8rem, 1.5vw, 0.95rem);
    font-weight: 600;
    color: {JNJ_GRAY_08};
    overflow: hidden;
    text-overflow: ellipsis;
}}
.jnj-meta-divider {{
    width: 1px;
    height: 34px;
    background: {JNJ_GRAY_02};
    flex-shrink: 0;
}}
@media screen and (max-width: 600px) {{
    .jnj-meta-strip {{ flex-direction: column; align-items: flex-start; gap: 0.75rem; }}
    .jnj-meta-divider {{ display: none; }}
}}

/* ════════════════════════════════════════════════════
   HINT PILLS
════════════════════════════════════════════════════ */
.jnj-hints {{
    display: flex;
    gap: 0.4rem;
    flex-wrap: wrap;
    margin-bottom: clamp(0.75rem, 2vw, 1.1rem);
}}
.jnj-hint {{
    font-size: clamp(0.62rem, 1vw, 0.72rem);
    font-weight: 500;
    color: {JNJ_GRAY_06};
    background: {JNJ_GRAY_01};
    border: 1px solid {JNJ_GRAY_02};
    border-radius: 4px;
    padding: 0.25rem clamp(0.5rem, 1.2vw, 0.8rem);
    white-space: nowrap;
}}

/* ════════════════════════════════════════════════════
   DATA EDITOR
════════════════════════════════════════════════════ */
[data-testid="stDataEditor"] {{
    border: 1px solid {JNJ_GRAY_02} !important;
    border-radius: 10px !important;
    overflow: hidden;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}}

/* ════════════════════════════════════════════════════
   UPLOAD ZONE
════════════════════════════════════════════════════ */
[data-testid="stFileUploader"] {{
    background: #ffffff !important;
    border: 2px dashed {JNJ_GRAY_03} !important;
    border-radius: 10px !important;
    padding: clamp(1rem, 3vw, 1.75rem) !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {JNJ_RED} !important;
    box-shadow: 0 0 0 4px rgba(235,23,0,0.07) !important;
}}

/* ════════════════════════════════════════════════════
   BUTTONS
════════════════════════════════════════════════════ */
.stButton > button[kind="primary"] {{
    background: {JNJ_RED} !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: clamp(0.78rem, 1.2vw, 0.9rem) !important;
    padding: 0.625rem clamp(1.25rem, 2.5vw, 1.875rem) !important;
    letter-spacing: 0.025em !important;
    transition: background 0.15s, box-shadow 0.15s, transform 0.1s !important;
    box-shadow: 0 2px 10px rgba(235,23,0,0.28), 0 1px 3px rgba(235,23,0,0.18) !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: {JNJ_MAROON} !important;
    box-shadow: 0 4px 16px rgba(235,23,0,0.36), 0 1px 4px rgba(235,23,0,0.22) !important;
    transform: translateY(-1px) !important;
}}
.stButton > button[kind="primary"]:active {{
    transform: translateY(0) !important;
}}
.stButton > button[kind="secondary"] {{
    background: #ffffff !important;
    color: {JNJ_GRAY_08} !important;
    border: 1px solid {JNJ_GRAY_03} !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: clamp(0.78rem, 1.2vw, 0.875rem) !important;
    transition: border-color 0.15s, background 0.15s !important;
}}
.stButton > button[kind="secondary"]:hover {{
    border-color: {JNJ_GRAY_06} !important;
    background: {JNJ_GRAY_01} !important;
}}

/* ════════════════════════════════════════════════════
   TEXT INPUT
════════════════════════════════════════════════════ */
.stTextInput > div > div > input {{
    background: #ffffff !important;
    border: 1px solid {JNJ_GRAY_03} !important;
    border-radius: 6px !important;
    color: {JNJ_GRAY_08} !important;
    font-family: 'Roboto Mono', monospace !important;
    font-size: clamp(0.76rem, 1.1vw, 0.84rem) !important;
    padding: 0.58rem 0.95rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: {JNJ_RED} !important;
    box-shadow: 0 0 0 3px rgba(235,23,0,0.1) !important;
    outline: none !important;
}}

/* ════════════════════════════════════════════════════
   STEP PREVIEW ROWS
════════════════════════════════════════════════════ */
.jnj-step-row {{
    display: flex;
    align-items: flex-start;
    gap: clamp(0.6rem, 1.5vw, 0.9rem);
    padding: clamp(0.7rem, 1.5vw, 1rem) clamp(0.75rem, 1.5vw, 1.1rem);
    border-bottom: 1px solid {JNJ_GRAY_01};
    transition: background 0.12s;
}}
.jnj-step-row:hover {{ background: {JNJ_GRAY_01}; }}
.jnj-step-row:last-child {{ border-bottom: none; }}
.jnj-step-index {{
    font-family: 'Roboto Mono', monospace;
    font-size: clamp(0.6rem, 0.9vw, 0.68rem);
    font-weight: 600;
    color: {JNJ_GRAY_05};
    min-width: 22px;
    padding-top: 2px;
    text-align: right;
    flex-shrink: 0;
}}
.jnj-badge {{
    font-size: clamp(0.55rem, 0.85vw, 0.62rem);
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border-radius: 4px;
    padding: 2px 8px;
    white-space: nowrap;
    flex-shrink: 0;
    margin-top: 1px;
}}
.jnj-badge-inc {{
    background: rgba(15,104,178,0.09);
    color: {JNJ_BLUE_03};
    border: 1px solid rgba(15,104,178,0.22);
}}
.jnj-badge-exc {{
    background: rgba(235,23,0,0.07);
    color: {JNJ_RED};
    border: 1px solid rgba(235,23,0,0.2);
}}
.jnj-step-text {{
    font-size: clamp(0.8rem, 1.3vw, 0.9rem);
    color: {JNJ_GRAY_08};
    line-height: 1.58;
}}

/* ════════════════════════════════════════════════════
   SUCCESS / ERROR BANNERS
════════════════════════════════════════════════════ */
.jnj-success {{
    background: rgba(50,135,20,0.06);
    border: 1px solid rgba(50,135,20,0.22);
    border-left: 4px solid {JNJ_GREEN_03};
    border-radius: 0 8px 8px 0;
    padding: clamp(0.75rem, 2vw, 1.1rem) clamp(1rem, 2vw, 1.4rem);
    color: #1e5c0a;
    font-size: clamp(0.78rem, 1.2vw, 0.875rem);
    font-weight: 500;
    margin-bottom: 1.5rem;
    line-height: 1.5;
}}
.jnj-success code {{
    font-family: 'Roboto Mono', monospace;
    font-size: 0.82em;
    background: rgba(50,135,20,0.09);
    padding: 1px 6px;
    border-radius: 3px;
}}
.jnj-error {{
    background: rgba(235,23,0,0.05);
    border-left: 4px solid {JNJ_RED};
    border-radius: 0 8px 8px 0;
    padding: clamp(0.75rem, 2vw, 1.1rem) clamp(1rem, 2vw, 1.4rem);
    color: {JNJ_MAROON};
    font-size: clamp(0.78rem, 1.2vw, 0.875rem);
    margin-bottom: 1rem;
}}

/* ════════════════════════════════════════════════════
   LIVE STAT ROW (below data editor)
════════════════════════════════════════════════════ */
.jnj-stat-row {{
    display: flex;
    gap: 1px;
    background: {JNJ_GRAY_02};
    border: 1px solid {JNJ_GRAY_02};
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}}
.jnj-stat-cell {{
    flex: 1;
    background: #ffffff;
    padding: clamp(1rem, 2vw, 1.4rem) clamp(1.1rem, 2.5vw, 1.75rem);
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}}
.jnj-stat-cell-label {{
    font-size: clamp(0.58rem, 0.9vw, 0.65rem);
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {JNJ_GRAY_05};
    white-space: nowrap;
}}
.jnj-stat-cell-value {{
    font-size: clamp(1.4rem, 3vw, 1.9rem);
    font-weight: 900;
    color: {JNJ_GRAY_08};
    line-height: 1;
    letter-spacing: -0.02em;
}}
.jnj-stat-cell-value.red   {{ color: {JNJ_RED}; }}
.jnj-stat-cell-value.blue  {{ color: {JNJ_BLUE_03}; }}
.jnj-stat-cell-value.green {{ color: {JNJ_GREEN_03}; }}
@media screen and (max-width: 480px) {{
    .jnj-stat-row {{ flex-direction: column; }}
}}

/* ════════════════════════════════════════════════════
   SIDEBAR
════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {{
    background: #ffffff !important;
    border-right: 1px solid {JNJ_GRAY_02} !important;
}}
[data-testid="stSidebar"] .block-container {{
    padding: clamp(1.25rem, 3vw, 1.75rem) clamp(1rem, 2.5vw, 1.4rem) !important;
    max-width: 100% !important;
}}
.sidebar-brand {{
    padding-bottom: 1.25rem;
    border-bottom: 2px solid {JNJ_RED};
    margin-bottom: 1.5rem;
}}
.sidebar-brand-name {{
    font-size: clamp(0.65rem, 1vw, 0.72rem);
    font-weight: 800;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {JNJ_RED};
}}
.sidebar-brand-sub {{
    font-size: clamp(0.58rem, 0.9vw, 0.65rem);
    color: {JNJ_GRAY_05};
    margin-top: 3px;
    font-weight: 400;
}}
.sidebar-section-label {{
    font-size: clamp(0.55rem, 0.85vw, 0.62rem);
    font-weight: 800;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {JNJ_GRAY_05};
    margin-bottom: 0.5rem;
    margin-top: 1.5rem;
}}
.sidebar-stat {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0.8rem;
    border-radius: 6px;
    margin-bottom: 4px;
    font-size: clamp(0.76rem, 1.1vw, 0.84rem);
    font-weight: 500;
}}
.sidebar-stat.total {{ background: {JNJ_GRAY_01}; color: {JNJ_GRAY_08}; }}
.sidebar-stat.inc   {{ background: rgba(15,104,178,0.07); color: {JNJ_BLUE_03}; }}
.sidebar-stat.exc   {{ background: rgba(235,23,0,0.06); color: {JNJ_RED}; }}
.sidebar-stat-num   {{ font-weight: 800; font-size: 1.05em; }}
.sidebar-divider    {{ height: 1px; background: {JNJ_GRAY_02}; margin: 1.25rem 0; }}
.sidebar-output {{
    background: {JNJ_GRAY_01};
    border-radius: 6px;
    padding: 0.75rem 0.9rem;
    font-family: 'Roboto Mono', monospace;
    font-size: clamp(0.6rem, 0.9vw, 0.68rem);
    color: {JNJ_GREEN_03};
    word-break: break-all;
    line-height: 1.5;
}}

/* ════════════════════════════════════════════════════
   FOOTER
════════════════════════════════════════════════════ */
.jnj-footer {{
    margin-top: clamp(2.5rem, 6vw, 4.5rem);
    padding: clamp(1.1rem, 2.5vw, 1.6rem) 0;
    border-top: 1px solid {JNJ_GRAY_02};
}}
.jnj-footer-inner {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
}}
.jnj-footer-left {{
    font-size: clamp(0.65rem, 1vw, 0.73rem);
    color: {JNJ_GRAY_05};
    line-height: 1.5;
}}
.jnj-footer-left strong {{ color: {JNJ_RED}; }}
.jnj-footer-right {{
    font-family: 'Roboto Mono', monospace;
    font-size: clamp(0.58rem, 0.9vw, 0.65rem);
    color: {JNJ_GRAY_05};
}}

/* ════════════════════════════════════════════════════
   TABS  —  underline style
════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0.25rem;
    background: transparent;
    border-bottom: 2px solid {JNJ_GRAY_02};
    padding: 0;
    margin-bottom: clamp(1.25rem, 3vw, 1.875rem);
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent;
    border-radius: 0;
    color: {JNJ_GRAY_05};
    font-family: 'Inter', sans-serif;
    font-size: clamp(0.78rem, 1.2vw, 0.875rem);
    font-weight: 500;
    padding: 0.65rem clamp(0.9rem, 2vw, 1.5rem) 0.75rem;
    border: none;
    border-bottom: 3px solid transparent;
    margin-bottom: -2px;
    letter-spacing: 0.01em;
    transition: color 0.15s;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: {JNJ_GRAY_08} !important;
    background: transparent !important;
}}
.stTabs [aria-selected="true"] {{
    background: transparent !important;
    color: {JNJ_RED} !important;
    font-weight: 700 !important;
    border-bottom: 3px solid {JNJ_RED} !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none; }}
.stTabs [data-baseweb="tab-border"]    {{ display: none; }}

/* ── scrollbar ── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {JNJ_GRAY_01}; }}
::-webkit-scrollbar-thumb {{ background: {JNJ_GRAY_03}; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: {JNJ_GRAY_05}; }}

/* ── selection colour ── */
::selection {{ background: rgba(235,23,0,0.12); color: {JNJ_GRAY_08}; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# session state
# ─────────────────────────────────────────────────────────────────────────────
for key, default in [
    ("steps_df",      None),
    ("title",         ""),
    ("data_sources",  []),
    ("notebook_path", None),
    ("input_mode",    None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ─────────────────────────────────────────────────────────────────────────────
# TOP NAV BAR
# ─────────────────────────────────────────────────────────────────────────────
_logo_html = f'<img src="{_logo_src()}" style="height:clamp(36px,5vw,54px);width:auto;display:block;">'

st.markdown(f"""
<div class="jnj-nav">
  <div class="jnj-inner jnj-nav-inner">
    <div class="jnj-logo-wrap">
        {_logo_html}
        <div class="jnj-logo-divider"></div>
        <div>
            <div class="jnj-logo-text">MedTech</div>
            <span class="jnj-logo-sub">Agentic AI Platform</span>
        </div>
    </div>
    <div class="jnj-nav-right">
        <span class="jnj-nav-tag">Code Automation</span>
        <div class="jnj-nav-built-by">
            <span class="jnj-nav-built-label">Powered by</span>
            <img src="{_MUSIGMA_LOGO_URL}"
                 style="height:clamp(22px,3.5vw,30px);width:auto;display:block;border-radius:4px;"
                 alt="Mu Sigma">
        </div>
        <span class="jnj-nav-version">v1.0.0</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
        <img src="{_logo_src()}" style="height:38px;width:auto;margin-bottom:10px;display:block;" alt="J&J">
        <div class="sidebar-brand-name">Code Automation</div>
        <div class="sidebar-brand-sub">Protocol Intelligence Platform</div>
        <div class="sidebar-built-by">
            <span class="sidebar-built-label">Powered by</span>
            <img src="{_MUSIGMA_LOGO_URL}" style="height:20px;width:auto;border-radius:3px;" alt="Mu Sigma">
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("New Protocol", type="secondary", use_container_width=True):
        for k in ["steps_df", "title", "data_sources", "notebook_path", "input_mode"]:
            st.session_state[k] = None if k not in ("data_sources",) else []
        st.session_state.title = ""
        st.rerun()

    if st.session_state.steps_df is not None:
        df = st.session_state.steps_df
        inc   = int((df["step_type"] == "inclusion").sum())
        exc   = int((df["step_type"] == "exclusion").sum())
        total = len(df)

        st.markdown('<div class="sidebar-section-label">Step Summary</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="sidebar-stat total">
            <span>Total Steps</span><span class="sidebar-stat-num">{total}</span>
        </div>
        <div class="sidebar-stat inc">
            <span>Inclusion</span><span class="sidebar-stat-num">{inc}</span>
        </div>
        <div class="sidebar-stat exc">
            <span>Exclusion</span><span class="sidebar-stat-num">{exc}</span>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.notebook_path:
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section-label">Last Output</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sidebar-output">{st.session_state.notebook_path}</div>',
                    unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HERO BAND
# ─────────────────────────────────────────────────────────────────────────────
df_now = st.session_state.steps_df
inc_count   = int((df_now["step_type"] == "inclusion").sum()) if df_now is not None else 0
exc_count   = int((df_now["step_type"] == "exclusion").sum()) if df_now is not None else 0
total_count = len(df_now) if df_now is not None else 0

st.markdown(f"""
<div class="jnj-hero">
    <div class="jnj-inner jnj-hero-inner">
        <div class="jnj-hero-eyebrow">J&amp;J MedTech &nbsp;·&nbsp; Agentic AI Platform</div>
        <div class="jnj-hero-title">Code <span>Automation</span></div>
        <div class="jnj-hero-stats">
            <div class="jnj-hero-stat">
                <div class="jnj-hero-stat-num">{total_count}<span>.</span></div>
                <div class="jnj-hero-stat-label">Total Steps</div>
            </div>
            <div class="jnj-hero-stat">
                <div class="jnj-hero-stat-num">{inc_count}<span>.</span></div>
                <div class="jnj-hero-stat-label">Inclusion</div>
            </div>
            <div class="jnj-hero-stat">
                <div class="jnj-hero-stat-num">{exc_count}<span>.</span></div>
                <div class="jnj-hero-stat-label">Exclusion</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# CONTENT
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="jnj-inner jnj-content">', unsafe_allow_html=True)


# ── STEP 1: INPUT MODE ────────────────────────────────────────────────────────
st.markdown("""
<div class="jnj-section-header" style="margin-top:0;">
    <div class="jnj-step-num">1</div>
    <div class="jnj-section-title">Protocol Input
        <span>Upload a .docx file or enter your study details manually</span>
    </div>
</div>
""", unsafe_allow_html=True)

tab_upload, tab_manual = st.tabs(["  Upload Protocol  ", "  Enter Manually  "])

# ── TAB A: UPLOAD ─────────────────────────────────────────────────────────────
with tab_upload:
    uploaded = st.file_uploader("", type=["docx"], label_visibility="collapsed")

    if uploaded and st.session_state.steps_df is None:
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        with st.spinner("Parsing protocol..."):
            try:
                result = parse_protocol(tmp_path)
                st.session_state.title        = result["title"]
                st.session_state.data_sources = result["data_sources"]
                st.session_state.input_mode   = "upload"
                rows = [
                    {"step_type": stype, "description": desc}
                    for _, stype, desc in result["attrition"]
                ]
                st.session_state.steps_df = pd.DataFrame(rows, columns=["step_type", "description"])
                st.rerun()
            except Exception as e:
                st.markdown(f'<div class="jnj-error">Parser error: {e}</div>', unsafe_allow_html=True)

# ── TAB B: MANUAL ENTRY ───────────────────────────────────────────────────────
with tab_manual:
    if st.session_state.input_mode != "manual":

        st.markdown("""
        <div class="jnj-hints" style="margin-bottom:1.25rem;">
            <span class="jnj-hint">Type your study title below</span>
            <span class="jnj-hint">Add each attrition step in the table</span>
            <span class="jnj-hint">Choose Inclusion or Exclusion per row</span>
        </div>
        """, unsafe_allow_html=True)

        manual_title = st.text_input(
            "Study Title",
            placeholder="e.g. Comparative effectiveness of MMAE adjunct...",
            key="manual_title_input",
        )
        manual_source = st.text_input(
            "Data Source (optional)",
            placeholder="e.g. Premier Healthcare Database",
            key="manual_source_input",
        )

        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

        if st.button("Start Entering Steps", type="primary", key="manual_start"):
            if not manual_title.strip():
                st.warning("Please enter a study title before continuing.")
            else:
                st.session_state.title        = manual_title.strip()
                st.session_state.data_sources = [manual_source.strip()] if manual_source.strip() else []
                st.session_state.input_mode   = "manual"
                st.session_state.steps_df     = pd.DataFrame(
                    [{"step_type": "inclusion", "description": ""}],
                    columns=["step_type", "description"],
                )
                st.rerun()
    else:
        st.markdown(f"""
        <div style="font-size:0.78rem;color:{JNJ_GRAY_06};margin-bottom:0.75rem;">
            Manual entry mode active &nbsp;·&nbsp;
            <span style="color:{JNJ_GRAY_08};font-weight:600;">{st.session_state.title}</span>
        </div>
        """, unsafe_allow_html=True)


# ── STEP 2: EDIT ──────────────────────────────────────────────────────────────
if st.session_state.steps_df is not None:

    st.markdown("""
    <div class="jnj-section-header">
        <div class="jnj-step-num">2</div>
        <div class="jnj-section-title">Edit Attrition Steps
            <span>Add, remove, or modify any step — changes flow directly into the notebook</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    sources_display = ", ".join(st.session_state.data_sources) if st.session_state.data_sources else "Not detected"
    st.markdown(f"""
    <div class="jnj-meta-strip">
        <div class="jnj-meta-item">
            <span class="jnj-meta-label">Study Title</span>
            <span class="jnj-meta-value">{st.session_state.title}</span>
        </div>
        <div class="jnj-meta-divider"></div>
        <div class="jnj-meta-item">
            <span class="jnj-meta-label">Data Source</span>
            <span class="jnj-meta-value">{sources_display}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="jnj-hints">
        <span class="jnj-hint">Click any cell to edit text</span>
        <span class="jnj-hint">Dropdown → switch Inclusion / Exclusion</span>
        <span class="jnj-hint">Select row checkbox → Delete key to remove</span>
        <span class="jnj-hint">+ row button to add a step</span>
    </div>
    """, unsafe_allow_html=True)

    edited_df = st.data_editor(
        st.session_state.steps_df,
        column_config={
            "step_type": st.column_config.SelectboxColumn(
                label="Type",
                options=["inclusion", "exclusion"],
                required=True,
                width="small",
            ),
            "description": st.column_config.TextColumn(
                label="Step Description",
                width="large",
                required=True,
            ),
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=False,
        key="step_editor",
    )

    # ── live stat row ─────────────────────────────────────────────────────────
    inc_live   = int((edited_df["step_type"] == "inclusion").sum())
    exc_live   = int((edited_df["step_type"] == "exclusion").sum())
    total_live = len(edited_df.dropna(subset=["description"]))

    st.markdown(f"""
    <div class="jnj-stat-row" style="margin-top:1rem;">
        <div class="jnj-stat-cell">
            <span class="jnj-stat-cell-label">Total Steps</span>
            <span class="jnj-stat-cell-value">{total_live}</span>
        </div>
        <div class="jnj-stat-cell">
            <span class="jnj-stat-cell-label">Inclusion</span>
            <span class="jnj-stat-cell-value blue">{inc_live}</span>
        </div>
        <div class="jnj-stat-cell">
            <span class="jnj-stat-cell-label">Exclusion</span>
            <span class="jnj-stat-cell-value red">{exc_live}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── STEP 3: GENERATE ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="jnj-section-header">
        <div class="jnj-step-num">3</div>
        <div class="jnj-section-title">Generate Notebook
            <span>Exports your curated steps as a structured .ipynb file</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_path, col_btn = st.columns([3, 1])
    with col_path:
        output_dir_input = st.text_input("Output directory", value="notebooks")
    with col_btn:
        st.markdown("<div style='margin-top:1.9rem;'></div>", unsafe_allow_html=True)
        generate = st.button("Generate Notebook", type="primary", use_container_width=True)

    if generate:
        clean_df = (
            edited_df
            .dropna(subset=["description"])
            .pipe(lambda d: d[d["description"].str.strip() != ""])
            .reset_index(drop=True)
        )

        if clean_df.empty:
            st.warning("No valid steps to export. Add at least one step.")
        else:
            display_steps = [
                f"({row['step_type'].capitalize()}) {row['description'].strip()}"
                for _, row in clean_df.iterrows()
            ]

            safe_title = (
                "".join(ch if ch.isalnum() else "_" for ch in st.session_state.title).strip("_")
            ) or "study"

            output_dir = Path(output_dir_input)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{safe_title[:80]}_attrition.ipynb"

            try:
                create_notebook(output_path, st.session_state.title, display_steps)
                st.session_state.steps_df     = clean_df
                st.session_state.notebook_path = str(output_path)

                st.markdown(f"""
                <div class="jnj-success">
                    Notebook written to <code>{output_path}</code>
                    &nbsp;·&nbsp; {len(display_steps)} steps exported
                </div>
                """, unsafe_allow_html=True)

                rows_html = ""
                for i, (_, row) in enumerate(clean_df.iterrows(), 1):
                    t    = row["step_type"]
                    css  = "inc" if t == "inclusion" else "exc"
                    lbl  = "INC" if t == "inclusion" else "EXC"
                    desc = str(row["description"]).strip()
                    rows_html += f"""
                    <div class="jnj-step-row">
                        <span class="jnj-step-index">{i:02d}</span>
                        <span class="jnj-badge jnj-badge-{css}">{lbl}</span>
                        <span class="jnj-step-text">{desc}</span>
                    </div>"""

                st.markdown(f"""
                <div class="jnj-card" style="padding:0;overflow:hidden;margin-top:0.5rem;">
                    <div style="padding:clamp(0.75rem,2vw,1rem) clamp(1rem,2.5vw,1.4rem);
                                border-bottom:1px solid {JNJ_GRAY_02};
                                font-size:0.68rem;font-weight:800;letter-spacing:0.14em;
                                text-transform:uppercase;color:{JNJ_GRAY_05};">
                        Step Preview &nbsp;·&nbsp; {len(display_steps)} steps
                    </div>
                    {rows_html}
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.markdown(f'<div class="jnj-error">Generation failed: {e}</div>',
                            unsafe_allow_html=True)


st.markdown('</div>', unsafe_allow_html=True)   # close jnj-content / jnj-inner


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="jnj-footer">
  <div class="jnj-inner jnj-footer-inner">
    <div class="jnj-footer-left">
        &copy; 2026 <strong>Johnson &amp; Johnson MedTech</strong> &nbsp;·&nbsp;
        Agentic AI Platform &nbsp;·&nbsp; Internal Use Only
    </div>
    <div class="jnj-footer-right">
        <span style="margin-right:0.5rem;font-weight:700;font-size:0.68rem;letter-spacing:0.05em;text-transform:uppercase;color:{JNJ_GRAY_08};">Powered by</span>
        <img src="{_MUSIGMA_LOGO_URL}"
             style="height:18px;width:auto;border-radius:3px;vertical-align:middle;margin-right:0.75rem;"
             alt="Mu Sigma">
        <span>Code Automation v1.0.0</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
