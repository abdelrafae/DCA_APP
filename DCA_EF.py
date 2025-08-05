

import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import differential_evolution
from io import BytesIO
import matplotlib.pyplot as plt


import os, textwrap, pathlib
cfg_dir = pathlib.Path(".streamlit")
cfg_dir.mkdir(exist_ok=True)
(cfg_dir / "config.toml").write_text(textwrap.dedent("""\
[theme]
base = "light"
primaryColor = "#2748d9"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F6F8FF"
textColor = "#1f2a44"
"""), encoding="utf-8")

# --- Put near the top of app.py ---
from PIL import Image
import base64, io, streamlit as st

def add_logo_below_deploy(path:str, width:int=120, top_px:int=64, right_px:int=16):
    """Renders a logo fixed just below the header, near the Deploy menu."""
    img = Image.open(path)
    # keep aspect ratio based on width
    w = width
    h = int(img.height * (w / img.width))
    buf = io.BytesIO(); img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    st.markdown(f"""
    <style>
      /* place the logo below the header, aligned to the right (under "Deploy") */
      .app-logo-fixed {{
        position: fixed;
        top: {top_px}px;              /* distance from top of page; increase to go lower */
        right: {right_px}px;          /* distance from right edge; increase to move left */
        width: {w}px;
        height: {h}px;
        z-index: 1000;                /* above page content */
        pointer-events: none;         /* clicks pass through */
      }}
      @media (max-width: 900px) {{
        .app-logo-fixed {{ width: {int(w*0.8)}px; right: 10px; top: {top_px+2}px; }}
      }}
    </style>
    <img class="app-logo-fixed" src="data:image/png;base64,{b64}" alt="logo">
    """, unsafe_allow_html=True)

# add_logo_below_deploy("D:\mohie\R.png", width=120, top_px=64, right_px=18)

 add_logo_below_deploy("assets/R.png", width=120, top_px=64, right_px=18)


# ============================ PAGE ============================
st.set_page_config(page_title="Hyperbolic Decline Dashboard", layout="wide", page_icon="📉")

# -------------------- Appearance Controls --------------------
with st.sidebar:
    st.markdown("### 🎨 Appearance")
    accent_choice = st.selectbox(
        "Accent color",
        ["Blue", "Teal", "Purple", "Emerald"],
        index=0,
        help="Changes highlights, headers, and button accents."
    )
    # density = st.select_slider("Density", ["Compact", "Comfortable"], value="Comfortable")

ACCENTS = {
    "Blue":    {"accent":"#2748d9", "accentSoft":"#eef3ff"},
    "Teal":    {"accent":"#0e8f8c", "accentSoft":"#e9fbfb"},
    "Purple":  {"accent":"#6d28d9", "accentSoft":"#f3e9ff"},
    "Emerald": {"accent":"#059669", "accentSoft":"#e9fbf4"},
}
ACCENT = ACCENTS[accent_choice]["accent"]
ACCENT_SOFT = ACCENTS[accent_choice]["accentSoft"]
PAD = "16px" 

# if density=="Comfortable" else "10px"
GAP = "18px" 

# if density=="Comfortable" else "12px"

# -------------------- THEME / CSS --------------------
st.markdown(f"""
<style>
:root {{
  --ink:#1f2a44;
  --muted:#6b7a99;
  --accent:{ACCENT};
  --accentSoft:{ACCENT_SOFT};
  --card:#ffffff;
  --line:#e8ecf6;
  --pad:{PAD};
  --gap:{GAP};
}}

html,body,[data-testid="stAppViewContainer"] * {{ color:var(--ink) !important; }}
[data-testid="stAppViewContainer"] {{
  background: radial-gradient(1200px 600px at 0% 0%, #e9f0ff 0%, #f6f8ff 25%, #ffffff 60%);
}}
[data-testid="stHeader"]{{ background:#ffffffcc; backdrop-filter:blur(6px); border-bottom:1px solid var(--line); }}

/* Sidebar */
section[data-testid="stSidebar"]{{
  background:linear-gradient(180deg,#eef3ff 0%,#ffffff 40%);
  border-right:1px solid var(--line);
}}
section[data-testid="stSidebar"] *{{ color:var(--ink) !important; }}

/* Cards with header accent bar */
.card{{
  background:var(--card);
  border-radius:18px;
  padding:calc(var(--pad) + 2px) var(--pad) var(--pad) var(--pad);
  border:1px solid var(--line);
  box-shadow:0 8px 24px rgba(36,71,187,.08);
  position:relative;
  margin-bottom:var(--gap);
}}
.card h3,.card h4{{ margin:0 0 10px 0; color:var(--ink)!important; font-weight:800; }}
.card::before {{
  content:"";
  position:absolute; left:0; top:0; height:6px; width:100%;
  background: linear-gradient(90deg, var(--accent), rgba(39,72,217,.0) 70%);
  border-top-left-radius:18px; border-top-right-radius:18px;
}}

/* KPI boxes */
.kpi-box{{
  background:#fff; border:1px solid var(--line); border-radius:14px;
  padding:12px 14px; box-shadow:0 4px 14px rgba(36,71,187,.08);
}}
.kpi-box:hover{{ box-shadow:0 8px 24px rgba(36,71,187,.14); }}
.kpi-label{{ font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; }}
.kpi-value{{ font-size:26px; font-weight:800; }}
.kpi-unit{{ font-size:11px; color:var(--muted); margin-left:6px }}

/* Inputs / uploader */
input,textarea,select{{ background:#fff !important; color:var(--ink)!important; }}
div[data-baseweb="select"]>div,div[data-baseweb="input"]>div{{ background:#fff !important; border:1px solid var(--line)!important; }}
[data-testid="stFileUploader"] section{{ background:#fff !important; border:1px dashed #cad3eb !important; }}

/* Buttons */
.stButton>button,.stDownloadButton>button,[data-testid="baseButton-secondary"]{{
  background:var(--accentSoft) !important; color:var(--accent) !important; border:1px solid #dbe3ff !important;
  border-radius:12px !important; padding:.7rem 1rem !important; font-weight:700 !important; min-height:40px;
}}
.stButton>button:hover,.stDownloadButton>button:hover,[data-testid="baseButton-secondary"]:hover{{
  filter:brightness(.98);
}}
.stForm .stButton>button{{ width:100%; }}

/* Tabs */
[role="tablist"] button{{ color: var(--muted) !important; font-weight: 600; }}
[role="tab"][aria-selected="true"]{{ color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; }}

/* DataFrame: white, legible text, subtle grid */
[data-testid="stDataFrame"] {{
  border:1px solid var(--line); border-radius:14px; overflow:hidden;
  box-shadow:0 4px 14px rgba(36,71,187,.06); background:#fff;
}}
[data-testid="stDataFrame"] thead tr {{ background:#f6f8ff !important; color:var(--ink)!important; font-weight:700; }}
[data-testid="stDataFrame"] tbody tr {{ background:#ffffff !important; }}
[data-testid="stDataFrame"] * {{ color:#1f2a44 !important; }}

/* Number inputs (remove dark steppers) */
[data-testid="stNumberInput"] > div > div {{
  background:#fff !important; border:1px solid var(--line) !important; border-radius:12px !important; overflow:hidden;
}}
[data-testid="stNumberInput"] input {{ background:#fff !important; color:var(--ink) !important; }}
[data-testid="stNumberInput"] button {{
  background:#fff !important; color:var(--accent) !important; border-left:1px solid var(--line) !important; box-shadow:none !important;
}}
[data-testid="stNumberInput"] button:hover {{ background:#f3f6ff !important; }}
[data-testid="stNumberInput"] button:active{{ background:#e7edff !important; }}
</style>
""", unsafe_allow_html=True)

# ADD this block *after* your existing <style>…</style> (keep the rest unchanged)
st.markdown("""
<style>
/* ===== File Uploader button: force light style across Streamlit versions ===== */
[data-testid="stFileUploader"] button,
[data-testid="stFileUploader"] [data-testid="baseButton-secondary"],
[data-testid="stFileUploader"] [data-testid="baseButton-primary"],
[data-testid="stFileUploader"] [data-baseweb="button"] {
  background: var(--accentSoft) !important;
  color: var(--accent) !important;
  border: 1px solid #dbe3ff !important;
  border-radius: 12px !important;
  box-shadow: none !important;
}
[data-testid="stFileUploader"] button:hover { filter: brightness(.98); }
/* remove dark overlays/focus rings that some themes inject */
[data-testid="stFileUploader"] button::before,
[data-testid="stFileUploader"] button::after { content: none !important; }
[data-testid="stFileUploader"] svg path { fill: var(--accent) !important; }

/* ===== Disabled buttons (e.g., Apply before changes): keep light ===== */
.stButton>button:disabled,
.stDownloadButton>button:disabled,
.stForm .stButton>button:disabled,
button[disabled],
[aria-disabled="true"] {
  background: #eef1f7 !important;
  color: #9aa8c7 !important;
  border: 1px solid #e1e6f4 !important;
  opacity: 1 !important;        /* prevent dark dimming */
  box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

# Add this AFTER your existing CSS block
st.markdown("""
<style>
/* 1) File-uploader icons (cloud + document): remove dark fills */
[data-testid="stFileUploader"] svg rect,
[data-testid="stFileUploader"] svg circle { fill: transparent !important; }
[data-testid="stFileUploader"] svg path { stroke: var(--accent) !important; fill: transparent !important; }
/* keep icon size natural */
[data-testid="stFileUploader"] svg { background: transparent !important; }

/* 2) File-uploader small "remove file" pill: make it light */
[data-testid="stFileUploader"] button[aria-label*="Remove"],
[data-testid="stFileUploader"] button[title*="Remove"],
[data-testid="stFileUploader"] [data-baseweb="button"][aria-label*="Remove"] {
  background: var(--accentSoft) !important;
  color: var(--accent) !important;
  border: 1px solid #dbe3ff !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}
[data-testid="stFileUploader"] button[aria-label*='Remove'] svg path { fill: var(--accent) !important; }

/* 3) Disabled Apply button: force light even when BaseWeb overrides it */
.stForm .stButton > button[disabled],
.stForm .stButton > button:disabled,
.stForm button[disabled],
.stForm [aria-disabled="true"],
.stForm [data-baseweb="button"][aria-disabled="true"] {
  background: #eef1f7 !important;
  color: #9aa8c7 !important;
  border: 1px solid #e1e6f4 !important;
  opacity: 1 !important;
  box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* ===== Select / Dropdown ===== */
/* Closed control */
div[data-baseweb="select"] > div {
  background:#ffffff !important;
  color:#111111 !important;
  border:1px solid var(--line) !important;
}
div[data-baseweb="select"] * { color:#111111 !important; }

/* Opened menu (lives in a portal) */
div[role="listbox"],
ul[role="listbox"],
[data-baseweb="menu"] {
  background:#ffffff !important;
  color:#111111 !important;
  border:1px solid var(--line) !important;
  box-shadow: 0 8px 24px rgba(15, 23, 42, .08) !important;
}

/* Options */
div[role="listbox"] [role="option"],
[data-baseweb="menu"] li {
  background:#ffffff !important;
  color:#111111 !important;
}
div[role="listbox"] [role="option"]:hover,
[data-baseweb="menu"] li:hover {
  background:#f3f6ff !important;       /* light hover */
  color:#111111 !important;
}
div[role="listbox"] [role="option"][aria-selected="true"] {
  background:#eef3ff !important;        /* selected */
  color:#111111 !important;
}

/* If the select has a search input in the menu, keep it white/black */
[data-baseweb="menu"] input,
div[role="listbox"] input {
  background:#ffffff !important;
  color:#111111 !important;
  border:1px solid var(--line) !important;
}

/* ===== DataFrame / Table ===== */
[data-testid="stDataFrame"] {
  background:#ffffff !important;
  border:1px solid var(--line) !important;
  border-radius:14px !important;
  box-shadow:0 4px 14px rgba(36,71,187,.06) !important;
}
[data-testid="stDataFrame"] * {
  color:#111111 !important;            /* black text */
}
[data-testid="stDataFrame"] thead tr {
  background:#ffffff !important;       /* white header */
  border-bottom:1px solid var(--line) !important;
}
[data-testid="stDataFrame"] tbody tr {
  background:#ffffff !important;       /* white rows */
}
[data-testid="stDataFrame"] th, 
[data-testid="stDataFrame"] td {
  border-color:#e9edf7 !important;     /* subtle grid lines */
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* --- Custom icons for st.file_uploader (no f-string required) --- */

/* Layout for the dropzone and file items */
[data-testid="stFileUploader"] section { position: relative; padding-left: 68px; }
[data-testid="stFileUploader"] ul li { position: relative; padding-left: 52px; }

/* Hide default SVGs */
[data-testid="stFileUploader"] section svg,
[data-testid="stFileUploader"] ul li svg { display: none !important; }

/* Dropzone icon (upload) */
[data-testid="stFileUploader"] section::before {
  content: "";
  position: absolute; left: 18px; top: 18px;
  width: 38px; height: 38px; border-radius: 12px;
  background: var(--accentSoft);
  color: var(--accent);                         /* used by SVG via currentColor */
  background-repeat: no-repeat; background-position: center; background-size: 22px 22px;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
  background-image: url("data:image/svg+xml;utf8,\
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>\
<path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/>\
<polyline points='17 8 12 3 7 8'/>\
<line x1='12' y1='3' x2='12' y2='15'/>\
</svg>");
}

/* Uploaded file icon (file) */
[data-testid="stFileUploader"] ul li::before {
  content: "";
  position: absolute; left: 12px; top: 8px;
  width: 32px; height: 32px; border-radius: 10px;
  background: var(--accentSoft);
  color: var(--accent);
  background-repeat: no-repeat; background-position: center; background-size: 20px 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
  background-image: url("data:image/svg+xml;utf8,\
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>\
<path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/>\
<polyline points='14 2 14 8 20 8'/>\
</svg>");
}

/* Remove button (X) */
[data-testid="stFileUploader"] button[aria-label*="Remove"] {
  position: relative;
  width: 28px; height: 28px;
  background: var(--accentSoft) !important;
  color: var(--accent) !important;
  border: 1px solid #dbe3ff !important;
  border-radius: 8px !important;
  box-shadow: none !important;
  overflow: hidden;
}
[data-testid="stFileUploader"] button[aria-label*="Remove"] svg { display: none !important; }
[data-testid="stFileUploader"] button[aria-label*="Remove"]::before {
  content: "";
  position: absolute; inset: 0;
  background-repeat: no-repeat; background-position: center; background-size: 16px 16px;
  color: var(--accent);
  background-image: url("data:image/svg+xml;utf8,\
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>\
<line x1='18' y1='6' x2='6' y2='18'/>\
<line x1='6' y1='6' x2='18' y2='18'/>\
</svg>");
}
</style>
""", unsafe_allow_html=True)

# Put this AFTER your existing CSS blocks
st.markdown("""
<style>
/* =========================
   FINAL OVERRIDE: Apply (Submit) in forms
   ========================= */

/* 0) Nuke any dark background on wrappers around the submit button */
.stForm .stButton,
.stForm .stButton > div,
.stForm .stButton > span,
.stForm .stButton > div > div {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
}

/* 1) Style the actual control (covers button, BaseWeb div-button, role=button) */
.stForm .stButton :is(button, [role="button"], [data-baseweb="button"]) {
  background: var(--accentSoft) !important;
  color: var(--accent) !important;
  border: 1px solid #dbe3ff !important;
  border-radius: 12px !important;
  min-height: 40px;
  box-shadow: none !important;
}

/* 2) Hover (enabled) */
.stForm .stButton :is(button, [role="button"], [data-baseweb="button"]):not([disabled]):not([aria-disabled="true"]):hover {
  filter: brightness(.98);
}

/* 3) Disabled – keep it light (no dark pill) */
.stForm .stButton :is(button, [role="button"], [data-baseweb="button"])[disabled],
.stForm .stButton :is(button, [role="button"], [data-baseweb="button"])[aria-disabled="true"] {
  background: #eef1f7 !important;
  color: #9aa8c7 !important;
  border: 1px solid #e1e6f4 !important;
  opacity: 1 !important;    /* avoid dim darkening */
  box-shadow: none !important;
}

/* 4) Kill BaseWeb pseudo overlays that paint the dark background */
.stForm .stButton :is(button, [role="button"], [data-baseweb="button"])::before,
.stForm .stButton :is(button, [role="button"], [data-baseweb="button"])::after {
  content: none !important;
  background: transparent !important;
}

/* 5) Some builds wrap the label in a span with its own background—clear it too */
.stForm .stButton :is(button, [role="button"], [data-baseweb="button"]) * {
  background: transparent !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* ===========================================
   FINAL OVERRIDE for open Select menus (portal)
   Works across Streamlit/BaseWeb builds 1.30–1.36
   =========================================== */

/* The portal container that hosts the open menu */
body > div[data-baseweb="layer"],
body > div[role="presentation"][data-baseweb="layer"],
body > div[aria-hidden="false"][data-baseweb="layer"] {
  color: #111111 !important;
}

/* The actual menu panel and listbox inside the portal */
body > div[data-baseweb="layer"]  [data-baseweb="menu"],
body > div[data-baseweb="layer"]  [role="listbox"],
body > div[role="presentation"][data-baseweb="layer"] [data-baseweb="menu"],
body > div[role="presentation"][data-baseweb="layer"] [role="listbox"],
body > div[aria-hidden="false"][data-baseweb="layer"] [data-baseweb="menu"],
body > div[aria-hidden="false"][data-baseweb="layer"] [role="listbox"] {
  background: #ffffff !important;
  color: #111111 !important;
  border: 1px solid var(--line) !important;
  box-shadow: 0 8px 24px rgba(15,23,42,.08) !important;
}

/* Make sure everything inside reads as black on white */
body > div[data-baseweb="layer"]  [data-baseweb="menu"] *,
body > div[data-baseweb="layer"]  [role="listbox"] *,
body > div[role="presentation"][data-baseweb="layer"] [data-baseweb="menu"] *,
body > div[role="presentation"][data-baseweb="layer"] [role="listbox"] * {
  color: #111111 !important;
  background: #ffffff !important;
}

/* Individual options + hover/selected states */
body > div[data-baseweb="layer"]  [data-baseweb="menu"] li,
body > div[data-baseweb="layer"]  [role="option"],
body > div[role="presentation"][data-baseweb="layer"] [data-baseweb="menu"] li,
body > div[role="presentation"][data-baseweb="layer"] [role="option"] {
  background: #ffffff !important;
  color: #111111 !important;
}
body > div[data-baseweb="layer"]  [data-baseweb="menu"] li:hover,
body > div[data-baseweb="layer"]  [role="option"]:hover,
body > div[role="presentation"][data-baseweb="layer"] [data-baseweb="menu"] li:hover,
body > div[role="presentation"][data-baseweb="layer"] [role="option"]:hover {
  background: #f3f6ff !important;
}
body > div[data-baseweb="layer"]  [role="option"][aria-selected="true"],
body > div[role="presentation"][data-baseweb="layer"] [role="option"][aria-selected="true"] {
  background: #eef3ff !important;
  color: #111111 !important;
}

/* Reinforce the closed control, in case theme tries to darken it */
div[data-baseweb="select"] > div,
div[data-baseweb="select"] * {
  background: #ffffff !important;
  color: #111111 !important;
}
</style>
""", unsafe_allow_html=True)

# ============================ SIDEBAR: Data ============================
with st.sidebar:
    st.markdown("### 📊 Hyperbolic Decline")
    # st.caption("Horizon-style dashboard for fitting from Qi to Qe.")
    uploaded_file = st.file_uploader("📂 Upload CSV (columns: wellname, date, oil, days)", type=["csv"])
    st.markdown("---")
    st.markdown("#### ⚙️ Column Mapping & Bounds")

# ============================ DATA LOAD ============================
if uploaded_file:
    @st.cache_data(show_spinner=False)
    def load_data(file):
        return pd.read_csv(file)

    df_raw = load_data(uploaded_file)
    df_raw.columns = df_raw.columns.str.strip().str.lower().str.replace(" ", "_")

    with st.sidebar:
        with st.container():
            well_col = st.selectbox("🛢️ Well Column", df_raw.columns, key="well_col")
            date_col = st.selectbox("📅 Date Column", df_raw.columns, key="date_col")
            oil_col  = st.selectbox("🛢️ Total Oil Column", df_raw.columns, key="oil_col")
            days_col = st.selectbox("📆 Days Column", df_raw.columns, key="days_col")
            oil_rate_col = st.text_input("🆕 New Oil-Rate Column Name", "oil_rate", key="oil_rate_name")
            b_min = st.number_input("🔽 Min b", value=0.00, step=0.01, key="b_min")
            b_max = st.number_input("🔼 Max b", value=1.00, step=0.01, key="b_max")
            submitted = st.button("✅ Apply", use_container_width=True, key="apply_btn")

    if submitted:
        df = df_raw[[well_col, date_col, oil_col, days_col]].copy()
        df.columns = ["well", "date", "oil", "days"]

        try:
            df["date"] = pd.to_datetime(df["date"])
        except Exception as e:
            st.error(f"❌ Date conversion error: {e}")
            st.stop()

        df["oil"] = pd.to_numeric(df["oil"], errors="coerce")
        df["days"] = pd.to_numeric(df["days"], errors="coerce")
        df[oil_rate_col] = df["oil"] / df["days"]

        df = df[(df[oil_rate_col] > 0) & df[oil_rate_col].notna()]
        df.dropna(subset=["well", "date", oil_rate_col], inplace=True)
        df.sort_values(by=["well", "date"], inplace=True)

        st.session_state.data_ready = df
        st.session_state.b_range = (b_min, b_max)
        st.session_state.oil_rate_col = oil_rate_col

# ============================ MAIN ============================
st.markdown("<div class='card'><h3>Main Dashboard</h3></div>", unsafe_allow_html=True)

if "data_ready" not in st.session_state:
    st.markdown("<div class='card'><h4>Welcome</h4><p>Upload a CSV from the left sidebar, map columns, and set b-bounds.</p></div>", unsafe_allow_html=True)
    st.stop()

df = st.session_state.data_ready
b_min, b_max = st.session_state.b_range
oil_rate_col = st.session_state.get("oil_rate_col", "oil_rate")
wells = sorted(df["well"].unique())

tab_overview, tab_single, tab_batch = st.tabs(["📈 Overview", "🛢️ Single Well Fit", "🧮 All Wells Summary"])

# ============================ OVERVIEW ============================
with tab_overview:
    c1, c2, c3 = st.columns([1,1,1])
    c1.markdown(f"<div class='kpi-box'><div class='kpi-label'>Total Wells</div><div class='kpi-value'>{len(wells)}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi-box'><div class='kpi-label'>Records Loaded</div><div class='kpi-value'>{len(df):,}</div></div>", unsafe_allow_html=True)
    span_days = int((df['date'].max() - df['date'].min()).days)
    c3.markdown(f"<div class='kpi-box'><div class='kpi-label'>Time Span (days)</div><div class='kpi-value'>{span_days}</div></div>", unsafe_allow_html=True)

# ============================ SINGLE WELL FIT ============================
with tab_single:
    # Layout tuned: left column for KPIs/table, right column for chart
    left, right = st.columns([1.15, 1.85], gap="large")

    with left:
        st.markdown("<div class='card'><h4>Well Selection</h4>", unsafe_allow_html=True)
        selected_well = st.selectbox("Select Well", wells, key="selected_well")
        st.markdown("</div>", unsafe_allow_html=True)

    # Prepare series
    wd = df[df["well"] == selected_well].copy()
    qi_idx = wd[oil_rate_col].idxmax()
    qi_date = wd.loc[qi_idx, "date"]
    Qi = wd.loc[qi_idx, oil_rate_col]

    before_qi = wd[wd["date"] < qi_date]
    after_qi = wd[wd["date"] >= qi_date].copy()
    after_qi["t_months"] = (after_qi["date"] - after_qi["date"].iloc[0]).dt.days / 30.4375
    t_data = after_qi["t_months"].values
    q_data = after_qi[oil_rate_col].values
    Qe = q_data[-1]

    def arps_rate(qi, di, b, t):
        """Hyperbolic for b>0, exponential when b≈0 (safe)."""
        if b <= 1e-10:
            return qi * np.exp(-di * t)
        return qi / (1 + b * di * t) ** (1.0 / b)

    def loss(params):
        di, b = params
        if di <= 0 or not (b_min <= b <= b_max): return 1e6
        q_pred = arps_rate(Qi, di, b, t_data)
        if np.any(np.isnan(q_pred)) or np.any(q_pred < 0): return 1e6
        weights = np.linspace(1, 3, len(q_data))
        mse_log = np.mean(weights * (np.log1p(q_pred) - np.log1p(q_data))**2)
        penalty_qe = (abs(q_pred[-1] - Qe) / max(Qe, 1)) ** 2 * 100
        penalty_b = (max(b - 1, 0))**2 * 5
        return mse_log + penalty_qe + penalty_b

    result = differential_evolution(loss, bounds=[(1e-4, 0.6), (b_min, b_max)], seed=42)
    di_opt, b_opt = result.x
    q_fit = arps_rate(Qi, di_opt, b_opt, t_data)
    qe_fit = q_fit[-1]
    mismatch = (qe_fit - Qe) / max(Qe, 1) * 100

    after_qi["fitted_rate"] = q_fit
    after_qi["cumulative_actual_full"] = after_qi[oil_rate_col].cumsum()
    after_qi["cumulative_fitted"] = after_qi["fitted_rate"].cumsum()
    cum_actual_full = after_qi["cumulative_actual_full"].iloc[-1]
    cum_fitted = after_qi["cumulative_fitted"].iloc[-1]
    cum_delta_pct = (cum_fitted - cum_actual_full) / max(cum_actual_full, 1) * 100

    # ---------- KPI GRID ----------
    with left:
        st.markdown("<div class='card'><h4>Fitting KPIs</h4>", unsafe_allow_html=True)
        k1, k2, k3 = st.columns([1,1,1])
        k4, k5, k6 = st.columns([1,1,1])

        k1.markdown(f"<div class='kpi-box'><div class='kpi-label'>Qi (detected)</div><div class='kpi-value'>{Qi:.2f}<span class='kpi-unit'> STB/d</span></div></div>", unsafe_allow_html=True)
        k2.markdown(f"<div class='kpi-box'><div class='kpi-label'>Qe (actual)</div><div class='kpi-value'>{Qe:.2f}<span class='kpi-unit'> STB/d</span></div></div>", unsafe_allow_html=True)
        # colorize delta (green when fit <= actual, red otherwise)
        delta_color = "#10b981" if mismatch <= 0 else "#ef4444"
        k3.markdown(f"<div class='kpi-box'><div class='kpi-label'>Qe (fit)</div>"
                    f"<div class='kpi-value'>{qe_fit:.2f}<span class='kpi-unit'> STB/d</span></div>"
                    f"<div style='color:{delta_color};font-weight:700;margin-top:4px'>{mismatch:+.2f}% vs actual</div></div>", unsafe_allow_html=True)

        k4.markdown(f"<div class='kpi-box'><div class='kpi-label'>Di</div><div class='kpi-value'>{di_opt:.5f}<span class='kpi-unit'> /month</span></div></div>", unsafe_allow_html=True)
        k5.markdown(f"<div class='kpi-box'><div class='kpi-label'>b-factor</div><div class='kpi-value'>{b_opt:.3f}</div></div>", unsafe_allow_html=True)
        cum_color = "#10b981" if cum_delta_pct <= 0 else "#ef4444"
        k6.markdown(f"<div class='kpi-box'><div class='kpi-label'>Cum (fit)</div>"
                    f"<div class='kpi-value'>{cum_fitted:,.0f}<span class='kpi-unit'> STB</span></div>"
                    f"<div style='color:{cum_color};font-weight:700;margin-top:4px'>{cum_delta_pct:+.2f}% vs actual</div></div>", unsafe_allow_html=True)

        # ---- Table ----
        st.markdown("<div class='card'><h4>Decline Table</h4>", unsafe_allow_html=True)
        tbl = after_qi[["date", oil_rate_col, "fitted_rate", "cumulative_fitted"]].rename(
            columns={oil_rate_col: "oil_rate"}
        ).copy()
        tbl["date"] = tbl["date"].dt.strftime("%Y-%m-%d")
        st.dataframe(tbl, use_container_width=True, height=360)
        buffer = BytesIO()
        after_qi.to_excel(buffer, index=False)
        st.download_button("📥 Download Result (Excel)", buffer.getvalue(),
                           file_name=f"{selected_well}_fit.xlsx", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- CHART (Matplotlib) ----------
    with right:
        st.markdown("<div class='card'><h4>Decline Curve</h4>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(10.5, 5.4), dpi=110)
        ax.scatter(before_qi["date"], before_qi[oil_rate_col], s=26, label="Pre-Qi")
        ax.scatter(after_qi["date"], after_qi[oil_rate_col], s=26, label="Post-Qi")
        ax.plot(after_qi["date"], q_fit, linewidth=2.2, label="Fitted Hyperbolic")
        ax.axvline(qi_date, linestyle="--", color="k", alpha=0.45)
        ax.text(qi_date, ax.get_ylim()[1]*0.96, "Qi", rotation=90, va="top", ha="right")

        ax.set_title(f"{selected_well} – Fit from Qi", pad=10, loc="left", color="#243B6A", fontweight="bold")
        ax.set_xlabel("Date"); ax.set_ylabel("Rate (STB/day)")
        ax.grid(True, linestyle="--", alpha=0.28)
        ax.set_facecolor("white"); fig.patch.set_facecolor("white")
        ax.legend(frameon=False, loc="upper right")
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)

# ============================ BATCH: ALL WELLS ============================
with tab_batch:
    st.markdown("<div class='card'><h4>Compute Fitting Results for All Wells</h4>", unsafe_allow_html=True)
    run = st.button("⚙️ Compute All-Wells Fitting Table", use_container_width=True)
    if run:
        results = []
        wells_all = sorted(df["well"].unique())
        progress = st.progress(0)
        status = st.empty()

        def arps_local(qi, di, b, t):
            if b <= 1e-10:
                return qi * np.exp(-di * t)
            return qi / (1 + b * di * t) ** (1.0 / b)

        for i, w in enumerate(wells_all, start=1):
            status.info(f"Processing **{w}** ({i}/{len(wells_all)}) …")
            wdf = df[df["well"] == w].copy()
            try:
                qi_idx_w = wdf[oil_rate_col].idxmax()
                qi_date_w = wdf.loc[qi_idx_w, "date"]
                Qi_w = wdf.loc[qi_idx_w, oil_rate_col]

                after = wdf[wdf["date"] >= qi_date_w].copy()
                after["t_months"] = (after["date"] - after["date"].iloc[0]).dt.days / 30.4375
                t_w = after["t_months"].values
                q_w = after[oil_rate_col].values

                if len(t_w) < 3:
                    results.append({
                        "well": w, "qi_date": qi_date_w.date(), "Qi_detected": Qi_w,
                        "Qe_actual_last": q_w[-1] if len(q_w)>0 else np.nan,
                        "Qe_fit": np.nan, "Mismatch_%": np.nan, "Di_per_month": np.nan,
                        "b_factor": np.nan,
                        "Cum_Actual_All": after[oil_rate_col].cumsum().iloc[-1] if len(q_w)>0 else np.nan,
                        "Cum_Fitted": np.nan, "status": "insufficient data"
                    })
                    progress.progress(i/len(wells_all))
                    continue

                Qe_w = q_w[-1]

                def loss_w(params):
                    di, b = params
                    if di <= 0 or not (b_min <= b <= b_max): return 1e6
                    q_pred = arps_local(Qi_w, di, b, t_w)
                    if np.any(np.isnan(q_pred)) or np.any(q_pred < 0): return 1e6
                    weights = np.linspace(1, 3, len(q_w))
                    mse_log = np.mean(weights * (np.log1p(q_pred) - np.log1p(q_w))**2)
                    penalty_qe = (abs(q_pred[-1] - Qe_w) / max(Qe_w, 1)) ** 2 * 100
                    penalty_b = (max(b - 1, 0))**2 * 5
                    return mse_log + penalty_qe + penalty_b

                res_w = differential_evolution(loss_w, bounds=[(1e-4, 0.6), (b_min, b_max)], seed=42)
                di_w, b_w = res_w.x
                q_fit_w = arps_local(Qi_w, di_w, b_w, t_w)
                qe_fit_w = q_fit_w[-1]
                mismatch_w = abs(qe_fit_w - Qe_w) / max(Qe_w, 1) * 100

                after["fitted_rate"] = q_fit_w
                after["cumulative_actual_full"] = after[oil_rate_col].cumsum()
                after["cumulative_fitted"] = after["fitted_rate"].cumsum()

                results.append({
                    "well": w, "qi_date": qi_date_w.date(), "Qi_detected": Qi_w,
                    "Qe_actual_last": Qe_w, "Qe_fit": qe_fit_w, "Mismatch_%": mismatch_w,
                    "Di_per_month": di_w, "b_factor": b_w,
                    "Cum_Actual_All": after["cumulative_actual_full"].iloc[-1],
                    "Cum_Fitted": after["cumulative_fitted"].iloc[-1], "status": "ok"
                })

            except Exception as e:
                results.append({
                    "well": w, "qi_date": None, "Qi_detected": np.nan,
                    "Qe_actual_last": np.nan, "Qe_fit": np.nan, "Mismatch_%": np.nan,
                    "Di_per_month": np.nan, "b_factor": np.nan,
                    "Cum_Actual_All": np.nan, "Cum_Fitted": np.nan,
                    "status": f"error: {e}"
                })

            progress.progress(i/len(wells_all))

        status.success("✅ Done.")
        summary_df = pd.DataFrame(results)
        st.markdown("<div class='card'><h4>All-Wells Fitting Summary</h4>", unsafe_allow_html=True)
        st.dataframe(summary_df, use_container_width=True, height=420)

        sum_buffer = BytesIO()
        with pd.ExcelWriter(sum_buffer, engine="xlsxwriter") as writer:
            summary_df.to_excel(writer, sheet_name="summary", index=False)
        st.download_button("📥 Download Summary (Excel)", sum_buffer.getvalue(),
                           file_name="all_wells_fitting_summary.xlsx", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)



