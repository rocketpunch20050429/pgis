"""
Bayesian PGIS 서울 중구 안전지도 - 지도 클릭 직접 입력
"""

import json
import os
from datetime import datetime, timedelta
import html
import inspect
import math
import streamlit as st
import streamlit.components.v1 as components
from branca.element import MacroElement, Template
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ========== 설정 ==========
JUNGGU_CENTER = [37.5630, 126.9945]
JUNGGU_BOUNDS = {
    "north": 37.5815,
    "south": 37.5445,
    "east": 127.0050,
    "west": 126.9840,
}
GRID_SIZE_M = 300
REPORT_INFLUENCE_RADIUS_M = 850
REPORT_DECAY_DISTANCE_M = 320
REPORT_DENSITY_SATURATION = 2.2
BACKGROUND_LIKELIHOOD = 0.07
FALSE_ALARM_RATE = 0.10
MAX_PRIOR_BOOST = 0.22
RIGHT_CLICK_QUERY_TOKEN = "__RIGHT_CLICK_QUERY__"
REPORTS_FILE = os.path.join(os.path.dirname(__file__), "reports.json")
REPORTS_TABLE = "reports"
REPORT_TABLE_LIMIT = 250
MAP_MARKER_LIMIT = 500
CSV_UPLOAD_ROW_LIMIT = 5000
HOTSPOT_LIMIT = 8
MAP_HOTSPOT_LIMIT = 5
ST_FOLIUM_SUPPORTS_CONTAINER_WIDTH = "use_container_width" in inspect.signature(st_folium).parameters

# ========== 중구 행정동 데이터 ==========
JUNGGU_DONGS = {
    "명동": {
        "bounds": {"north": 37.5680, "south": 37.5600, "east": 127.0010, "west": 126.9850},
        "center": [37.5640, 126.9930],
        "desc": "명동 쇼핑거리, 명동성당"
    },
    "을지로동": {
        "bounds": {"north": 37.5750, "south": 37.5650, "east": 127.0100, "west": 126.9950},
        "center": [37.5700, 127.0025],
        "desc": "을지로 전자상가"
    },
    "다산동": {
        "bounds": {"north": 37.5650, "south": 37.5530, "east": 127.0000, "west": 126.9850},
        "center": [37.5590, 126.9925],
        "desc": "다산동 지역"
    },
    "서소문동": {
        "bounds": {"north": 37.5650, "south": 37.5530, "east": 126.9850, "west": 126.9600},
        "center": [37.5590, 126.9725],
        "desc": "서소문로 일대"
    },
    "필동": {
        "bounds": {"north": 37.5800, "south": 37.5650, "east": 127.0020, "west": 126.9850},
        "center": [37.5725, 126.9935],
        "desc": "필동 주거지역"
    },
    "쌍림동": {
        "bounds": {"north": 37.5780, "south": 37.5650, "east": 126.9900, "west": 126.9700},
        "center": [37.5715, 126.9800],
        "desc": "쌍림동 지역"
    },
    "황학동": {
        "bounds": {"north": 37.5800, "south": 37.5650, "east": 127.0100, "west": 126.9950},
        "center": [37.5725, 127.0025],
        "desc": "황학동 주거지역"
    },
    "광희동": {
        "bounds": {"north": 37.5630, "south": 37.5500, "east": 127.0100, "west": 126.9950},
        "center": [37.5565, 127.0025],
        "desc": "광희동 지역"
    },
    "저동": {
        "bounds": {"north": 37.5815, "south": 37.5700, "east": 127.0050, "west": 126.9900},
        "center": [37.5757, 126.9975],
        "desc": "저동 주거지역"
    },
    "묵정동": {
        "bounds": {"north": 37.5580, "south": 37.5450, "east": 126.9950, "west": 126.9750},
        "center": [37.5515, 126.9850],
        "desc": "묵정동 지역"
    },
}

# ========== CSS 스타일 ==========
CUSTOM_CSS = """
<style>
/* ── Global ──────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

:root {
    --pgis-bg: #f3f6fa;
    --pgis-surface: #ffffff;
    --pgis-border: #dbe4ef;
    --pgis-text: #0f172a;
    --pgis-muted: #64748b;
    --pgis-soft: #f8fafc;
    --pgis-primary: #2563eb;
    --pgis-primary-dark: #1d4ed8;
    --pgis-shadow-sm: 0 1px 3px rgba(15,23,42,.06);
    --pgis-shadow-md: 0 10px 30px rgba(15,23,42,.10);
}

.stApp {
    background:
        linear-gradient(180deg, #eef4fb 0%, var(--pgis-bg) 260px, var(--pgis-bg) 100%) !important;
    color: var(--pgis-text) !important;
}
.main .block-container {
    width: 100%;
    padding: 1.25rem 1.5rem 3rem !important;
    max-width: 1540px !important;
}
[data-testid="stHorizontalBlock"],
[data-testid="column"],
[data-testid="stVerticalBlock"],
[data-testid="stElementContainer"] {
    min-width: 0 !important;
}
iframe {
    display: block;
    width: 100% !important;
    max-width: 100% !important;
}
.element-container:has(.pgis-command-strip),
.element-container:has(.pgis-header),
.element-container:has(.pgis-kpi-row),
.element-container:has(.analysis-summary-row) {
    margin-bottom: 0 !important;
}

/* ── Header ──────────────────────────────────────────────────────────── */
.pgis-header {
    position: relative;
    overflow: hidden;
    background: #0f172a;
    border-radius: 14px;
    padding: 22px 26px 20px;
    margin-bottom: 14px;
    box-shadow: 0 18px 42px rgba(15,23,42,.18), inset 0 1px 0 rgba(255,255,255,.05);
}
.pgis-header::after {
    content: '';
    position: absolute;
    inset: 0;
    background:
        radial-gradient(ellipse 65% 55% at 90% 50%, rgba(59,130,246,.15) 0%, transparent 65%),
        radial-gradient(ellipse 45% 80% at 0% 100%, rgba(99,102,241,.1) 0%, transparent 60%);
    pointer-events: none;
}
.pgis-header__eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(59,130,246,.14);
    border: 1px solid rgba(59,130,246,.3);
    border-radius: 999px;
    padding: 3px 10px 3px 8px;
    font-size: 10.5px;
    font-weight: 700;
    color: #93c5fd;
    letter-spacing: .06em;
    text-transform: uppercase;
    margin-bottom: 9px;
}
.pgis-header h1 {
    margin: 0 !important;
    font-size: 1.875rem !important;
    font-weight: 900 !important;
    color: #f8fafc !important;
    line-height: 1.15 !important;
    letter-spacing: 0 !important;
}
.pgis-header p {
    margin: 6px 0 0 !important;
    font-size: 13px !important;
    color: #94a3b8 !important;
    line-height: 1.6 !important;
}
.pgis-header__chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 14px;
}
.pgis-header__chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(255,255,255,.07);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 8px;
    min-height: 28px;
    padding: 4px 10px;
    font-size: 11.5px;
    font-weight: 600;
    color: #cbd5e1;
}
.pgis-header__chip b { color: #e2e8f0; }
.pgis-live-dot {
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #22c55e;
    box-shadow: 0 0 0 3px rgba(34,197,94,.22);
    animation: pgis-pulse 2.2s ease-in-out infinite;
}
@keyframes pgis-pulse {
    0%, 100% { box-shadow: 0 0 0 3px rgba(34,197,94,.2); }
    50%       { box-shadow: 0 0 0 7px rgba(34,197,94,.06); }
}

/* ── KPI Cards ───────────────────────────────────────────────────────── */
.pgis-kpi-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(158px, 1fr));
    gap: 10px;
    margin-bottom: 14px;
}
.pgis-kpi {
    position: relative;
    overflow: hidden;
    background: #fff;
    border-radius: 10px;
    padding: 15px 16px 13px;
    border: 1px solid var(--pgis-border);
    box-shadow: var(--pgis-shadow-sm);
    transition: box-shadow .2s, transform .2s;
    cursor: default;
}
.pgis-kpi:hover {
    box-shadow: var(--pgis-shadow-md);
    transform: translateY(-2px);
}
.pgis-kpi__topbar {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 12px 12px 0 0;
}
.pgis-kpi__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}
.pgis-kpi__label {
    font-size: 10.5px;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: .5px;
}
.pgis-kpi__icon { font-size: 17px; line-height: 1; }
.pgis-kpi__value {
    font-size: 28px;
    font-weight: 900;
    color: #0f172a;
    line-height: 1;
    letter-spacing: -.8px;
    margin-bottom: 8px;
}
.pgis-kpi__delta {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    border-radius: 999px;
    font-size: 10.5px;
    font-weight: 700;
    padding: 2px 8px;
}
.pgis-kpi__delta--up   { background: #fee2e2; color: #b91c1c; }
.pgis-kpi__delta--down { background: #dcfce7; color: #15803d; }
.pgis-kpi__delta--zero { background: #f1f5f9; color: #64748b; }

/* ── Click alert ─────────────────────────────────────────────────────── */
.click-alert {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-left: 4px solid #f59e0b;
    border-radius: 10px;
    color: #92400e;
    padding: 11px 16px;
    font-weight: 600;
    font-size: 13px;
    margin-bottom: 16px;
}

/* ── Workflow strip ──────────────────────────────────────────────────── */
.pgis-command-strip {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 12px;
    align-items: center;
    margin: 0 0 12px;
    padding: 12px 14px;
    background: rgba(255,255,255,.88);
    border: 1px solid var(--pgis-border);
    border-radius: 12px;
    box-shadow: var(--pgis-shadow-sm);
}
.pgis-command-strip__main { min-width: 0; }
.pgis-command-strip__title {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--pgis-text);
    font-size: 13.5px;
    font-weight: 850;
}
.pgis-command-strip__sub {
    margin-top: 4px;
    color: var(--pgis-muted);
    font-size: 12px;
    font-weight: 650;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.pgis-command-strip__meta {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 6px;
}
.pgis-state-chip {
    display: inline-flex;
    align-items: center;
    min-height: 28px;
    padding: 4px 10px;
    border: 1px solid var(--pgis-border);
    border-radius: 999px;
    background: #fff;
    color: #475569;
    font-size: 11.5px;
    font-weight: 750;
    white-space: nowrap;
}
.pgis-state-chip--active {
    border-color: rgba(37,99,235,.28);
    background: #eff6ff;
    color: #1d4ed8;
}

/* ── Section heading ─────────────────────────────────────────────────── */
.pgis-section-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 12px;
    flex-wrap: wrap;
}
.pgis-section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: 0;
}
.pgis-section-title__icon {
    width: 28px; height: 28px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; flex-shrink: 0;
}
.pgis-hint-row {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}
.pgis-hint {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 999px;
    min-height: 30px;
    padding: 4px 11px;
    font-size: 11px;
    font-weight: 600;
    color: #64748b;
}
.pgis-hint b { color: #0f172a; }

/* ── Buttons ─────────────────────────────────────────────────────────── */
.stButton > button {
    background: #0f172a !important;
    color: #f8fafc !important;
    border: 1px solid rgba(255,255,255,.06) !important;
    border-radius: 9px !important;
    font-weight: 700 !important;
    font-size: 12.5px !important;
    min-height: 42px !important;
    padding: 0.6rem 1.2rem !important;
    transition: background .18s, box-shadow .18s, transform .15s !important;
    letter-spacing: .1px !important;
}
.stButton > button:hover {
    background: #1e293b !important;
    box-shadow: 0 6px 18px rgba(15,23,42,.2) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }
.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible,
[data-testid="stFormSubmitButton"] > button:focus-visible {
    outline: 3px solid rgba(37,99,235,.24) !important;
    outline-offset: 2px !important;
}

[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 14px rgba(37,99,235,.35) !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    box-shadow: 0 8px 20px rgba(37,99,235,.45) !important;
    transform: translateY(-1px) !important;
}

.stDownloadButton > button {
    background: #2563eb !important;
    color: #fff !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 700 !important;
}

/* ── Form ────────────────────────────────────────────────────────────── */
[data-testid="stForm"] {
    background: #fff !important;
    border: 1px solid var(--pgis-border) !important;
    border-radius: 12px !important;
    box-shadow: var(--pgis-shadow-sm) !important;
    padding: 1rem !important;
}
[data-testid="stForm"] label,
[data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSlider"] label,
[data-testid="stFileUploader"] label {
    color: #334155 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
}
[data-baseweb="select"] > div,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stFileUploader"] section {
    border-color: var(--pgis-border) !important;
    border-radius: 9px !important;
}
[data-baseweb="select"] > div:focus-within,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--pgis-primary) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,.12) !important;
}
[data-testid="stExpander"] {
    border: 1px solid var(--pgis-border) !important;
    border-radius: 12px !important;
    background: #fff !important;
    box-shadow: var(--pgis-shadow-sm) !important;
}
[data-testid="stExpander"] details summary {
    color: var(--pgis-text) !important;
    font-weight: 850 !important;
}

/* ── Report board ────────────────────────────────────────────────────── */
.report-board {
    background: #fff;
    border: 1px solid var(--pgis-border);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--pgis-shadow-sm);
}
.report-board__header {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: flex-end;
    padding: 14px 18px;
    border-bottom: 1px solid var(--pgis-border);
    background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
}
.report-board__title {
    color: #0f172a;
    font-size: 13.5px;
    font-weight: 800;
    letter-spacing: -.2px;
    margin: 0;
}
.report-board__sub {
    color: #94a3b8;
    font-size: 11.5px;
    margin-top: 3px;
}
.report-board__meta {
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
    justify-content: flex-end;
}
.report-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border: 1px solid #e2e8f0;
    border-radius: 999px;
    color: #475569;
    background: #fff;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 9px;
    white-space: nowrap;
}
.report-table-wrap { max-height: 460px; overflow: auto; }
.report-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    table-layout: fixed;
    color: #0f172a;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.report-table thead th {
    position: sticky; top: 0; z-index: 2;
    background: #f8fafc;
    color: #64748b;
    border-bottom: 1px solid #e2e8f0;
    font-size: 11px; font-weight: 700;
    letter-spacing: .4px; text-transform: uppercase;
    text-align: left;
    padding: 10px 12px;
}
.report-table tbody td {
    border-bottom: 1px solid #f1f5f9;
    padding: 10px 12px;
    vertical-align: middle;
    font-size: 13px;
    background: #fff;
}
.report-table tbody tr:hover td { background: #f8fafc; }
.report-table .col-id     { width: 64px; }
.report-table .col-status { width: 108px; }
.report-table .col-dong   { width: 108px; }
.report-table .col-type   { width: 128px; }
.report-table .col-risk   { width: 158px; }
.report-table .col-time   { width: 100px; }
.report-table .col-desc   { width: auto; }

.status-badge, .risk-badge {
    display: inline-flex; align-items: center;
    border-radius: 999px;
    font-size: 11px; font-weight: 700;
    padding: 3px 8px; white-space: nowrap;
}
.status-badge { color: #0f766e; background: #ccfbf1; border: 1px solid rgba(20,184,166,.2); }
.risk-badge.low  { color: #15803d; background: #dcfce7; }
.risk-badge.mid  { color: #92400e; background: #fef3c7; }
.risk-badge.high { color: #b91c1c; background: #fee2e2; }
.risk-cell { display: grid; gap: 4px; }
.risk-meter { height: 5px; border-radius: 999px; background: #f1f5f9; overflow: hidden; }
.risk-meter span {
    display: block; height: 100%; border-radius: inherit;
    background: linear-gradient(90deg, #22c55e 0%, #f59e0b 50%, #ef4444 100%);
}
.desc-text { color: #64748b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ── Success / info ──────────────────────────────────────────────────── */
.success-msg {
    background: #dcfce7;
    border: 1px solid rgba(34,197,94,.3);
    border-left: 4px solid #22c55e;
    color: #14532d;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
}
.data-quality-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
    margin: 0 0 12px;
}
.data-quality-card {
    min-width: 0;
    border: 1px solid var(--pgis-border);
    border-radius: 10px;
    background: #fff;
    padding: 10px 11px;
}
.data-quality-label {
    color: #94a3b8;
    font-size: 10.5px;
    font-weight: 800;
    letter-spacing: .3px;
    text-transform: uppercase;
}
.data-quality-value {
    margin-top: 5px;
    color: #0f172a;
    font-size: 18px;
    font-weight: 900;
    line-height: 1;
}
.data-quality-sub {
    margin-top: 5px;
    color: #64748b;
    font-size: 11px;
    font-weight: 650;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.data-quality-card.is-good .data-quality-value { color: #16a34a; }
.data-quality-card.is-warn .data-quality-value { color: #f97316; }
.data-quality-card.is-bad .data-quality-value { color: #ef4444; }

/* ── Analysis charts ─────────────────────────────────────────────────── */
.analysis-brief-row {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin: 0 0 14px;
}
.analysis-brief-card {
    min-width: 0;
    border: 1px solid var(--pgis-border);
    border-radius: 12px;
    background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
    padding: 13px 14px;
    box-shadow: var(--pgis-shadow-sm);
}
.analysis-brief-label {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #64748b;
    font-size: 11px;
    font-weight: 850;
    letter-spacing: .3px;
    text-transform: uppercase;
}
.analysis-brief-value {
    margin-top: 7px;
    color: #0f172a;
    font-size: 18px;
    font-weight: 900;
    line-height: 1.18;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.analysis-brief-sub {
    margin-top: 6px;
    color: #64748b;
    font-size: 11.5px;
    font-weight: 650;
    line-height: 1.45;
}
.analysis-summary-row {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin: 0 0 14px;
}
.analysis-summary-card {
    background: #fff;
    border: 1px solid var(--pgis-border);
    border-radius: 12px;
    padding: 13px 14px;
    box-shadow: var(--pgis-shadow-sm);
    transition: box-shadow .18s, transform .18s;
}
.analysis-summary-card:hover {
    box-shadow: var(--pgis-shadow-md);
    transform: translateY(-1px);
}
.analysis-summary-label {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #64748b;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .3px;
    text-transform: uppercase;
}
.analysis-summary-value {
    margin-top: 8px;
    color: #0f172a;
    font-size: 24px;
    font-weight: 900;
    line-height: 1.05;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.analysis-summary-sub {
    margin-top: 6px;
    color: #94a3b8;
    font-size: 11.5px;
    font-weight: 650;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.analysis-tip {
    margin: 0 0 12px;
    padding: 10px 12px;
    color: #475569;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    font-size: 12px;
    font-weight: 650;
    line-height: 1.5;
}
.pgis-risk-list {
    overflow: hidden;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(15,23,42,.05);
}
.pgis-risk-list__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 13px 15px;
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
}
.pgis-risk-list__title {
    color: #0f172a;
    font-size: 13px;
    font-weight: 850;
}
.pgis-risk-list__sub {
    color: #94a3b8;
    font-size: 11.5px;
    font-weight: 650;
}
.pgis-risk-row {
    display: grid;
    grid-template-columns: 34px minmax(0, 1fr) auto;
    gap: 12px;
    align-items: center;
    padding: 12px 15px;
    border-bottom: 1px solid #f1f5f9;
}
.pgis-risk-row:last-child { border-bottom: 0; }
.pgis-risk-rank {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    background: #f1f5f9;
    color: #475569;
    font-size: 12px;
    font-weight: 850;
}
.pgis-risk-name {
    color: #0f172a;
    font-size: 13px;
    font-weight: 800;
}
.pgis-risk-meta {
    margin-top: 4px;
    color: #64748b;
    font-size: 11.5px;
    font-weight: 650;
}
.pgis-risk-meter {
    margin-top: 8px;
    height: 6px;
    overflow: hidden;
    border-radius: 999px;
    background: #f1f5f9;
}
.pgis-risk-meter span {
    display: block;
    height: 100%;
    border-radius: inherit;
}
.pgis-risk-score {
    min-width: 76px;
    text-align: right;
}
.pgis-risk-score b {
    display: block;
    color: #0f172a;
    font-size: 18px;
    line-height: 1;
}
.pgis-risk-score span {
    display: inline-flex;
    margin-top: 5px;
    padding: 2px 8px;
    border-radius: 999px;
    color: #fff;
    font-size: 10px;
    font-weight: 800;
}
.hotspot-list {
    overflow: hidden;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(15,23,42,.05);
}
.hotspot-row {
    display: grid;
    grid-template-columns: 34px minmax(0, 1fr) minmax(98px, auto);
    gap: 12px;
    align-items: center;
    padding: 13px 15px;
    border-bottom: 1px solid #f1f5f9;
}
.hotspot-row:last-child { border-bottom: 0; }
.hotspot-rank {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    background: #eef2ff;
    color: #3730a3;
    font-size: 12px;
    font-weight: 900;
}
.hotspot-name {
    color: #0f172a;
    font-size: 13px;
    font-weight: 850;
}
.hotspot-meta {
    margin-top: 4px;
    color: #64748b;
    font-size: 11.5px;
    font-weight: 650;
}
.hotspot-meter {
    margin-top: 8px;
    height: 6px;
    overflow: hidden;
    border-radius: 999px;
    background: #f1f5f9;
}
.hotspot-meter span {
    display: block;
    height: 100%;
    border-radius: inherit;
}
.hotspot-score {
    min-width: 98px;
    text-align: right;
}
.hotspot-score b {
    display: block;
    color: #0f172a;
    font-size: 18px;
    line-height: 1;
}
.hotspot-score span {
    display: inline-flex;
    margin-top: 5px;
    padding: 2px 8px;
    border-radius: 999px;
    color: #fff;
    font-size: 10px;
    font-weight: 850;
}
[data-baseweb="tab-list"] {
    gap: 6px;
    overflow-x: auto;
    padding-bottom: 2px;
}
[data-baseweb="tab"] {
    height: auto;
    padding: 8px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
    white-space: nowrap;
}
[data-testid="stPlotlyChart"] {
    overflow: hidden;
    border: 1px solid var(--pgis-border);
    border-radius: 12px;
    background: #fff;
}

/* ── Streamlit overrides ─────────────────────────────────────────────── */
hr { border: none !important; border-top: 1px solid #e2e8f0 !important; margin: 1rem 0 !important; }
h3 { font-size: 0.9375rem !important; font-weight: 800 !important; color: #0f172a !important; letter-spacing: -.2px !important; }
[data-testid="stCaption"] { color: #94a3b8 !important; font-size: 11.5px !important; }
[data-testid="stMarkdownContainer"] p {
    line-height: 1.55;
}

/* ── Scrollbar ───────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

@media (max-width: 900px) {
    .main .block-container {
        padding: 0.875rem 0.875rem 2.5rem !important;
    }
    .pgis-header {
        border-radius: 12px;
        padding: 18px 16px 16px;
        margin-bottom: 12px;
    }
    .pgis-header h1 {
        font-size: 1.45rem !important;
        letter-spacing: -.2px !important;
    }
    .pgis-header p {
        font-size: 12px !important;
        line-height: 1.5 !important;
    }
    .pgis-header__chip {
        flex: 1 1 calc(50% - 6px);
        justify-content: center;
        min-width: 0;
        text-align: center;
    }
    .pgis-kpi-row {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
        margin-bottom: 12px;
    }
    .pgis-kpi {
        padding: 13px 12px 12px;
    }
    .pgis-kpi__value {
        font-size: 22px;
        letter-spacing: -.3px;
    }
    .pgis-command-strip {
        grid-template-columns: 1fr;
    }
    .pgis-command-strip__meta {
        justify-content: flex-start;
    }
    .analysis-summary-row {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .analysis-summary-value {
        font-size: 21px;
    }
    .data-quality-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .analysis-brief-row {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .pgis-section-head,
    .report-board__header {
        align-items: flex-start;
        flex-direction: column;
    }
    .pgis-hint-row,
    .report-board__meta {
        justify-content: flex-start;
        width: 100%;
    }
    .pgis-hint {
        flex: 1 1 100%;
        justify-content: center;
    }
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: .75rem !important;
    }
    [data-testid="column"] {
        flex: 1 1 100% !important;
        width: 100% !important;
    }
    .stButton > button,
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] > button {
        width: 100% !important;
    }
}

@media (max-width: 640px) {
    .click-alert {
        align-items: flex-start;
        padding: 10px 12px;
        font-size: 12px;
    }
    .pgis-command-strip {
        padding: 11px 12px;
        border-radius: 10px;
    }
    .pgis-command-strip__sub {
        white-space: normal;
    }
    .pgis-state-chip {
        flex: 1 1 calc(50% - 6px);
        justify-content: center;
        text-align: center;
    }
    [data-baseweb="tab-list"] {
        gap: 4px;
        margin: 0 -2px;
        padding: 0 2px 5px;
        scrollbar-width: none;
    }
    [data-baseweb="tab-list"]::-webkit-scrollbar {
        display: none;
    }
    [data-baseweb="tab"] {
        flex: 0 0 auto;
        padding: 7px 10px;
        font-size: 11.5px;
    }
    .analysis-summary-card {
        padding: 12px;
    }
    .analysis-summary-value,
    .analysis-summary-sub {
        white-space: normal;
        word-break: keep-all;
    }
    .analysis-brief-value {
        white-space: normal;
        word-break: keep-all;
    }
    [data-testid="stPlotlyChart"] {
        border-radius: 10px;
    }
    [data-testid="stForm"] {
        padding: .875rem !important;
    }
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {
        font-size: 16px !important;
    }
    .report-board {
        border-radius: 10px;
    }
    .report-board__header {
        padding: 12px;
    }
    .report-table-wrap {
        max-height: none;
        overflow: visible;
    }
    .report-table,
    .report-table tbody,
    .report-table tr,
    .report-table td {
        display: block;
        width: 100% !important;
    }
    .report-table thead {
        display: none;
    }
    .report-table tbody tr {
        display: grid;
        gap: 8px;
        margin: 10px;
        padding: 12px;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        background: #fff;
    }
    .report-table tbody td {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        padding: 0;
        border-bottom: 0;
        background: transparent;
        font-size: 12px;
    }
    .report-table tbody td::before {
        color: #94a3b8;
        content: "";
        flex: 0 0 64px;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: .3px;
        text-transform: uppercase;
    }
    .report-table .col-id::before { content: "ID"; }
    .report-table .col-status::before { content: "상태"; }
    .report-table .col-dong::before { content: "행정동"; }
    .report-table .col-type::before { content: "유형"; }
    .report-table .col-risk::before { content: "위험도"; }
    .report-table .col-time::before { content: "시간"; }
    .report-table .col-desc {
        display: block;
    }
    .report-table .col-desc::before {
        display: block;
        margin-bottom: 4px;
        content: "설명";
    }
    .desc-text {
        overflow: visible;
        white-space: normal;
    }
    .pgis-risk-list__head,
    .pgis-risk-row,
    .hotspot-row {
        padding-left: 12px;
        padding-right: 12px;
    }
    .pgis-risk-row,
    .hotspot-row {
        grid-template-columns: 30px minmax(0, 1fr);
    }
    .pgis-risk-score,
    .hotspot-score {
        grid-column: 2;
        min-width: 0;
        text-align: left;
    }
}

@media (max-width: 420px) {
    .main .block-container {
        padding: .625rem .625rem 2rem !important;
    }
    .pgis-header__chip {
        flex-basis: 100%;
        justify-content: flex-start;
        text-align: left;
    }
    .pgis-state-chip {
        flex-basis: 100%;
        justify-content: flex-start;
    }
    .pgis-kpi-row {
        grid-template-columns: 1fr;
    }
    .analysis-summary-row {
        grid-template-columns: 1fr;
    }
    .data-quality-grid {
        grid-template-columns: 1fr;
    }
    .analysis-brief-row {
        grid-template-columns: 1fr;
    }
}
</style>
"""

# ========== 페이지 설정 ==========
st.set_page_config(
    page_title="중구 안전지도 | 베이지안 분석",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ========== 함수 ==========
def haversine_distance(lat1, lon1, lat2, lon2):
    """위도/경도 간 거리 계산 (미터)"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def get_dong_by_coords(lat, lon):
    """좌표로부터 동 찾기"""
    for dong_name, dong_data in JUNGGU_DONGS.items():
        b = dong_data["bounds"]
        if b["south"] <= lat <= b["north"] and b["west"] <= lon <= b["east"]:
            return dong_name
    return "알 수 없음"

def coerce_float(value, default):
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default

def coerce_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def is_within_junggu_bounds(lat, lng):
    return (
        JUNGGU_BOUNDS["south"] <= lat <= JUNGGU_BOUNDS["north"]
        and JUNGGU_BOUNDS["west"] <= lng <= JUNGGU_BOUNDS["east"]
    )

def get_csv_value(row, candidates, default=None):
    values = {str(key).strip().lower(): value for key, value in row.items()}
    for candidate in candidates:
        value = values.get(candidate.lower())
        if value is None or pd.isna(value):
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return default

def build_report_from_csv_row(row, report_id, uploaded_at):
    lat_value = get_csv_value(row, ["lat", "latitude", "위도", "y"])
    lng_value = get_csv_value(row, ["lng", "lon", "longitude", "경도", "x"])
    lat = coerce_float(lat_value, None)
    lng = coerce_float(lng_value, None)
    if lat is None or lng is None:
        return None

    report_type = str(get_csv_value(row, ["type", "위험 유형", "위험유형", "신고유형", "종류"], "신고"))
    intensity = max(1, min(5, coerce_int(get_csv_value(row, ["intensity", "위험도", "risk"], 3), 3)))
    report_time = str(get_csv_value(row, ["time", "report_time", "시간"], uploaded_at.strftime("%m-%d %H:%M")))
    created_at = get_csv_value(
        row,
        ["created_at", "timestamp", "datetime", "date", "신고일시", "날짜"],
        uploaded_at.isoformat(timespec="minutes"),
    )
    desc = str(get_csv_value(row, ["desc", "description", "상세 설명", "상세설명", "설명", "내용"], ""))
    dong = str(get_csv_value(row, ["dong", "동", "행정동"], get_dong_by_coords(lat, lng)))

    return {
        "id": report_id,
        "lng": lng,
        "lat": lat,
        "type": report_type,
        "intensity": intensity,
        "time": report_time,
        "created_at": str(created_at),
        "desc": desc,
        "dong": dong or get_dong_by_coords(lat, lng),
    }

def report_dedupe_key(report):
    lat = coerce_float(report.get("lat"), None)
    lng = coerce_float(report.get("lng", report.get("lon")), None)
    if lat is None or lng is None:
        return None

    return (
        round(lat, 6),
        round(lng, 6),
        str(report.get("type", "")).strip().casefold(),
        coerce_int(report.get("intensity"), 0),
        str(report.get("desc", "")).strip().casefold(),
    )

def summarize_report_quality(reports):
    total_count = len(reports or [])
    seen_keys = set()
    duplicate_count = 0
    missing_coord_count = 0
    outside_count = 0
    unknown_dong_count = 0
    issue_rows = set()

    for index, report in enumerate(reports or []):
        lat = coerce_float(report.get("lat"), None)
        lng = coerce_float(report.get("lng", report.get("lon")), None)
        if lat is None or lng is None:
            missing_coord_count += 1
            issue_rows.add(index)
            continue

        if not is_within_junggu_bounds(lat, lng):
            outside_count += 1
            issue_rows.add(index)

        if str(report.get("dong", "")).strip() in ("", "알 수 없음"):
            unknown_dong_count += 1
            issue_rows.add(index)

        dedupe_key = report_dedupe_key(report)
        if dedupe_key in seen_keys:
            duplicate_count += 1
            issue_rows.add(index)
        elif dedupe_key is not None:
            seen_keys.add(dedupe_key)

    issue_count = len(issue_rows)
    clean_count = max(0, total_count - issue_count)
    quality_score = round((clean_count / total_count) * 100) if total_count else 100

    return {
        "total_count": total_count,
        "quality_score": quality_score,
        "duplicate_count": duplicate_count,
        "missing_coord_count": missing_coord_count,
        "outside_count": outside_count,
        "unknown_dong_count": unknown_dong_count,
        "issue_count": issue_count,
    }

def render_data_quality_summary(stats):
    issue_count = stats["issue_count"]
    quality_score = stats["quality_score"]
    quality_class = "is-good" if quality_score >= 95 else "is-warn" if quality_score >= 80 else "is-bad"
    issue_class = "is-good" if issue_count == 0 else "is-warn"
    duplicate_class = "is-good" if stats["duplicate_count"] == 0 else "is-warn"
    outside_class = "is-good" if stats["outside_count"] == 0 else "is-bad"
    cards = [
        ("전체 신고", f'{stats["total_count"]:,}건', "현재 저장 기준", ""),
        ("데이터 품질", f"{quality_score}%", "중복·누락·범위 기준", quality_class),
        ("중복 의심", f'{stats["duplicate_count"]:,}건', "좌표·유형·강도·설명", duplicate_class),
        ("검토 필요", f"{issue_count:,}건", f'범위 밖 {stats["outside_count"]:,} · 좌표 누락 {stats["missing_coord_count"]:,}', issue_class if stats["outside_count"] == 0 else outside_class),
    ]

    return (
        '<div class="data-quality-grid">'
        + "".join(
            f'<div class="data-quality-card {card_class}">'
            f'<div class="data-quality-label">{html.escape(label)}</div>'
            f'<div class="data-quality-value">{html.escape(value)}</div>'
            f'<div class="data-quality-sub">{html.escape(sub)}</div>'
            f'</div>'
            for label, value, sub, card_class in cards
        )
        + '</div>'
    )

def normalize_report(report):
    if not isinstance(report, dict):
        return None

    normalized = dict(report)
    lat = coerce_float(normalized.get("lat"), JUNGGU_CENTER[0])
    lng = coerce_float(normalized.get("lng", normalized.get("lon")), JUNGGU_CENTER[1])
    intensity = max(1, min(5, coerce_int(normalized.get("intensity"), 3)))

    normalized["lat"] = lat
    normalized["lng"] = lng
    normalized["intensity"] = intensity
    normalized.setdefault("type", "report")
    normalized.setdefault("time", datetime.now().strftime("%m-%d %H:%M"))
    normalized.setdefault("desc", "")

    if not normalized.get("dong"):
        normalized["dong"] = get_dong_by_coords(lat, lng)

    return normalized

def normalize_reports(reports):
    normalized_reports = []
    next_id = 1

    for report in reports or []:
        normalized = normalize_report(report)
        if normalized is None:
            continue

        report_id = coerce_int(normalized.get("id"), 0)
        if report_id <= 0:
            report_id = next_id
        normalized["id"] = report_id
        next_id = max(next_id, report_id + 1)

        normalized_reports.append(normalized)

    return normalized_reports

def parse_report_datetime(report, today=None):
    if not isinstance(report, dict):
        return None

    today = today or datetime.now().date()
    for key in ("created_at", "timestamp", "datetime", "date", "time"):
        value = report.get(key)
        if value is None:
            continue

        if isinstance(value, datetime):
            return value

        text = str(value).strip()
        if not text:
            continue

        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            pass

        for fmt in ("%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue

        for fmt in ("%m-%d %H:%M", "%m/%d %H:%M", "%m-%d", "%m/%d"):
            try:
                parsed = datetime.strptime(text, fmt).replace(year=today.year)
                if parsed.date() > today:
                    parsed = parsed.replace(year=today.year - 1)
                return parsed
            except ValueError:
                continue

        try:
            parsed_time = datetime.strptime(text, "%H:%M").time()
            return datetime.combine(today, parsed_time)
        except ValueError:
            continue

    return None

def split_reports_by_dates(reports, target_dates, today=None):
    today = today or datetime.now().date()
    buckets = {target_date: [] for target_date in target_dates}
    for report in reports:
        parsed = parse_report_datetime(report, today)
        if parsed is None:
            continue
        report_date = parsed.date()
        if report_date in buckets:
            buckets[report_date].append(report)
    return buckets

def summarize_reports(reports):
    count = len(reports)
    avg_intensity = np.mean([r["intensity"] for r in reports]) if reports else 0
    high_risk_count = len([r for r in reports if r["intensity"] >= 4])
    return {
        "count": count,
        "avg_intensity": float(avg_intensity),
        "high_risk_count": high_risk_count,
    }

def format_metric_delta(current, previous, unit, decimals=0):
    diff = current - previous
    if decimals:
        if abs(diff) < 0.05:
            return f"±0.0{unit} 전일 대비"
        return f"{diff:+.{decimals}f}{unit} 전일 대비"

    diff = int(diff)
    if diff == 0:
        return f"±0{unit} 전일 대비"
    return f"{diff:+d}{unit} 전일 대비"

@st.cache_data(show_spinner=False)
def create_grid():
    """주소 기반 격자 생성"""
    grid = []
    grid_id = 0
    
    for dong_name, dong_data in JUNGGU_DONGS.items():
        bounds = dong_data["bounds"]
        lat_step = GRID_SIZE_M / 111000
        lon_step = GRID_SIZE_M / (111000 * math.cos(math.radians((bounds["north"] + bounds["south"]) / 2)))
        
        lat = bounds["south"]
        while lat < bounds["north"]:
            lon = bounds["west"]
            while lon < bounds["east"]:
                grid.append({
                    "id": grid_id,
                    "lat": lat + lat_step/2,
                    "lon": lon + lon_step/2,
                    "prior": 0.1,
                    "dong": dong_name,
                })
                grid_id += 1
                lon += lon_step
            lat += lat_step
    
    return grid

@st.cache_data(show_spinner=False)
def prepare_report_arrays(reports):
    normalized = normalize_reports(reports)
    if not normalized:
        return {
            "lat": np.array([], dtype=float),
            "lng": np.array([], dtype=float),
            "intensity": np.array([], dtype=float),
        }

    return {
        "lat": np.array([report["lat"] for report in normalized], dtype=float),
        "lng": np.array([report["lng"] for report in normalized], dtype=float),
        "intensity": np.array([report["intensity"] for report in normalized], dtype=float),
    }

def get_report_distance_weight(distance_m):
    if distance_m > REPORT_INFLUENCE_RADIUS_M:
        return 0
    return math.exp(-0.5 * (distance_m / REPORT_DECAY_DISTANCE_M) ** 2)

def get_density_factor(weighted_count):
    return 1 - math.exp(-weighted_count / REPORT_DENSITY_SATURATION)

def _empty_bayesian_stats(prior):
    likelihood = BACKGROUND_LIKELIHOOD
    evidence = prior * likelihood + (1 - prior) * FALSE_ALARM_RATE
    posterior = (prior * likelihood) / evidence if evidence > 0 else prior
    return {
        "likelihood": likelihood,
        "posterior": posterior,
        "report_count": 0,
        "weighted_count": 0,
        "local_risk": 0,
        "density_factor": 0,
    }

def calculate_bayesian_stats_from_arrays(lat, lng, report_arrays, prior=0.1):
    report_lats = report_arrays["lat"]
    if len(report_lats) == 0:
        return _empty_bayesian_stats(prior)

    lat_window = REPORT_INFLUENCE_RADIUS_M / 111000
    lon_scale = max(abs(math.cos(math.radians(lat))), 0.01)
    lon_window = REPORT_INFLUENCE_RADIUS_M / (111000 * lon_scale)
    report_lngs = report_arrays["lng"]
    candidate_mask = (
        (np.abs(report_lats - lat) <= lat_window)
        & (np.abs(report_lngs - lng) <= lon_window)
    )
    if not np.any(candidate_mask):
        return _empty_bayesian_stats(prior)

    candidate_lats = report_lats[candidate_mask]
    candidate_lngs = report_lngs[candidate_mask]
    candidate_intensity = report_arrays["intensity"][candidate_mask]

    phi1 = math.radians(lat)
    phi2 = np.radians(candidate_lats)
    dphi = np.radians(candidate_lats - lat)
    dlambda = np.radians(candidate_lngs - lng)
    a = np.sin(dphi / 2) ** 2 + math.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    distances = 6371000 * (2 * np.arcsin(np.sqrt(np.clip(a, 0, 1))))
    within_mask = distances <= REPORT_INFLUENCE_RADIUS_M
    if not np.any(within_mask):
        return _empty_bayesian_stats(prior)

    distances = distances[within_mask]
    intensities = candidate_intensity[within_mask]
    weights = np.exp(-0.5 * (distances / REPORT_DECAY_DISTANCE_M) ** 2)
    nearby_count = int(len(weights))
    weighted_count = float(weights.sum())
    weighted_risk = float((weights * (intensities / 5)).sum())

    if weighted_count > 0:
        local_risk = weighted_risk / weighted_count
        density_factor = get_density_factor(weighted_count)
        likelihood = BACKGROUND_LIKELIHOOD + (local_risk - BACKGROUND_LIKELIHOOD) * density_factor
        adaptive_prior = min(0.5, prior + density_factor * MAX_PRIOR_BOOST)
    else:
        local_risk = 0
        density_factor = 0
        likelihood = BACKGROUND_LIKELIHOOD
        adaptive_prior = prior
    
    evidence = adaptive_prior * likelihood + (1 - adaptive_prior) * FALSE_ALARM_RATE
    posterior = (adaptive_prior * likelihood) / evidence if evidence > 0 else adaptive_prior
    
    return {
        "likelihood": likelihood,
        "posterior": posterior,
        "report_count": nearby_count,
        "weighted_count": weighted_count,
        "local_risk": local_risk,
        "density_factor": density_factor,
    }

def calculate_bayesian_stats_for_point(lat, lng, reports, prior=0.1):
    report_arrays = prepare_report_arrays(reports)
    return calculate_bayesian_stats_from_arrays(lat, lng, report_arrays, prior)

@st.cache_data(show_spinner=False)
def calculate_hotspot_candidates(grid, reports, selected_dong, limit=HOTSPOT_LIMIT):
    normalized_reports = normalize_reports(reports)
    if not normalized_reports:
        return []

    report_arrays = prepare_report_arrays(normalized_reports)
    candidates = []
    for cell in grid:
        if selected_dong != "전체" and cell.get("dong") != selected_dong:
            continue

        stats = calculate_bayesian_stats_from_arrays(
            cell["lat"],
            cell["lon"],
            report_arrays,
            cell.get("prior", 0.1),
        )
        if stats["report_count"] <= 0 and stats["posterior"] < 0.16:
            continue

        candidates.append({
            "id": cell["id"],
            "dong": cell["dong"],
            "lat": float(cell["lat"]),
            "lng": float(cell["lon"]),
            "posterior": float(stats["posterior"]),
            "local_risk": float(stats["local_risk"]),
            "density_factor": float(stats["density_factor"]),
            "report_count": int(stats["report_count"]),
            "weighted_count": float(stats["weighted_count"]),
        })

    candidates.sort(
        key=lambda item: (
            item["posterior"],
            item["report_count"],
            item["local_risk"],
            item["weighted_count"],
        ),
        reverse=True,
    )
    return candidates[:limit]

def get_color(value):
    """위험도 색상"""
    if value < 0.16:
        return "#10b981"
    elif value < 0.30:
        return "#f59e0b"
    elif value < 0.46:
        return "#f97316"
    else:
        return "#ef4444"

def get_probability_grade(probability):
    if probability >= 0.46:
        return {
            "label": "고위험",
            "color": "#ef4444",
            "soft": "#fff1f0",
            "text": "이 지역은 위험도가 높습니다. 가능하면 주의해서 이동하세요.",
        }
    if probability >= 0.30:
        return {
            "label": "주의",
            "color": "#f97316",
            "soft": "#fff7ed",
            "text": "주변에 위험 신고가 있습니다. 이동 시 주변 상황을 확인하세요.",
        }
    if probability >= 0.16:
        return {
            "label": "관찰",
            "color": "#f59e0b",
            "soft": "#fefce8",
            "text": "현재 위험도는 중간 수준입니다. 상황 변화를 지켜보세요.",
        }
    return {
        "label": "안전",
        "color": "#10b981",
        "soft": "#ecfdf5",
        "text": "현재 이 지역의 위험도는 낮습니다. 안전한 상태입니다.",
    }

def render_hotspot_candidates(hotspots):
    if not hotspots:
        return ""

    rows = []
    for rank, hotspot in enumerate(hotspots, start=1):
        probability = max(0, min(1, hotspot["posterior"]))
        probability_percent = probability * 100
        grade = get_probability_grade(probability)
        density_percent = max(0, min(100, hotspot["density_factor"] * 100))
        meter_width = max(5, min(100, probability_percent))
        rows.append(
            f'<div class="hotspot-row">'
            f'<div class="hotspot-rank">{rank}</div>'
            f'<div>'
            f'<div class="hotspot-name">{html.escape(str(hotspot["dong"]))} 후보 지점</div>'
            f'<div class="hotspot-meta">주변 신고 {hotspot["report_count"]:,}건 · 밀도 {density_percent:.0f}% · '
            f'{hotspot["lat"]:.5f}, {hotspot["lng"]:.5f}</div>'
            f'<div class="hotspot-meter"><span style="width:{meter_width:.0f}%;background:{grade["color"]};"></span></div>'
            f'</div>'
            f'<div class="hotspot-score"><b>{probability_percent:.0f}%</b><span style="background:{grade["color"]};">{grade["label"]}</span></div>'
            f'</div>'
        )

    return '<div class="hotspot-list">' + "".join(rows) + '</div>'

def format_distance(distance_m):
    if distance_m is None:
        return "-"
    if distance_m < 1000:
        return f"{distance_m:.0f}m"
    return f"{distance_m / 1000:.1f}km"

def get_query_context(lat, lng, reports, stats):
    nearby_reports = []
    type_counts = {}

    for report in reports:
        distance = haversine_distance(lat, lng, report["lat"], report["lng"])
        weight = get_report_distance_weight(distance)
        if weight <= 0:
            continue

        report_type = str(report.get("type", "신고"))
        type_counts[report_type] = type_counts.get(report_type, 0) + 1
        nearby_reports.append({
            "report": report,
            "distance": distance,
            "weight": weight,
        })

    nearby_reports.sort(key=lambda item: item["distance"])
    nearest_distance = nearby_reports[0]["distance"] if nearby_reports else None
    dominant_type = max(type_counts, key=type_counts.get) if type_counts else "관측 없음"
    avg_intensity = (
        sum(item["report"]["intensity"] for item in nearby_reports) / len(nearby_reports)
        if nearby_reports else 0
    )
    confidence_score = min(100, round((stats["weighted_count"] / 2.2) * 100))
    if confidence_score >= 70:
        confidence_label = "충분"
    elif confidence_score >= 35:
        confidence_label = "보통"
    elif stats["report_count"] > 0:
        confidence_label = "적음"
    else:
        confidence_label = "없음"

    return {
        "nearby_reports": nearby_reports,
        "nearest_distance": nearest_distance,
        "dominant_type": dominant_type,
        "avg_intensity": avg_intensity,
        "confidence_score": confidence_score,
        "confidence_label": confidence_label,
    }

def build_query_popup_html(lat, lng, dong, stats, reports):
    probability = stats["posterior"]
    grade = get_probability_grade(probability)
    context = get_query_context(lat, lng, reports, stats)
    probability_percent = max(0, min(100, probability * 100))
    density_percent = max(0, min(100, stats["density_factor"] * 100))
    nearest_text = format_distance(context["nearest_distance"])
    dominant_type = html.escape(context["dominant_type"])
    avg_intensity = context["avg_intensity"]
    note = grade["text"]
    nearest_label = "없음" if context["nearest_distance"] is None else nearest_text

    return f"""
    <div class="query-risk-card">
        <div class="query-risk-head" style="background:linear-gradient(135deg, #1f2a44 0%, #3f6070 62%, {grade['color']} 100%);">
            <div>
                <div class="query-risk-kicker">예상 사고 가능성</div>
                <div class="query-risk-value">{probability:.2%}</div>
            </div>
            <div class="query-risk-badge">{grade['label']}</div>
        </div>
        <div class="query-risk-body">
            <div class="query-risk-place">{html.escape(dong)} · {lat:.5f}, {lng:.5f}</div>
            <div class="query-risk-bar">
                <div style="width:{probability_percent:.1f}%; background:{grade['color']};"></div>
            </div>
            <div class="query-risk-grid">
                <div>
                    <span>반경 내 신고 수</span>
                    <b>{stats['report_count']}건</b>
                </div>
                <div>
                    <span>가장 가까운 신고</span>
                    <b>{nearest_label}</b>
                </div>
                <div>
                    <span>신고 평균 위험도</span>
                    <b>{avg_intensity:.1f} / 5</b>
                </div>
                <div>
                    <span>신고 밀집도</span>
                    <b>{density_percent:.0f}%</b>
                </div>
            </div>
            <div class="query-risk-note">
                주요 신고 유형: <b>{dominant_type}</b><br>{note}
            </div>
        </div>
    </div>
    """

def get_heat_weight(value):
    return max(0.0, min(1.0, (value - 0.08) / 0.42))

def get_map_interaction(map_data):
    if not map_data:
        return None

    clicked = map_data.get("last_clicked")
    if isinstance(clicked, dict) and clicked.get("lat") is not None and clicked.get("lng") is not None:
        return "register", float(clicked["lat"]), float(clicked["lng"])

    object_tooltip = map_data.get("last_object_clicked_tooltip")
    object_clicked = map_data.get("last_object_clicked")
    if (
        object_tooltip == RIGHT_CLICK_QUERY_TOKEN
        and isinstance(object_clicked, dict)
        and object_clicked.get("lat") is not None
        and object_clicked.get("lng") is not None
    ):
        return "query", float(object_clicked["lat"]), float(object_clicked["lng"])

    return None

def render_kpi_row(overall_stats, today_stats, yesterday_stats, grid_count, dong_count):
    def _delta(curr, prev):
        diff = int(curr - prev)
        if diff > 0: return f"▲ {diff} 전일 대비", "up"
        if diff < 0: return f"▼ {abs(diff)} 전일 대비", "down"
        return "전일과 동일", "zero"

    def _delta_f(curr, prev):
        diff = curr - prev
        if abs(diff) < 0.05: return "전일과 동일", "zero"
        if diff > 0: return f"▲ {abs(diff):.1f} 전일 대비", "up"
        return f"▼ {abs(diff):.1f} 전일 대비", "down"

    count_d, count_c   = _delta(today_stats["count"],           yesterday_stats["count"])
    avg_d,   avg_c     = _delta_f(today_stats["avg_intensity"],  yesterday_stats["avg_intensity"])
    high_d,  high_c    = _delta(today_stats["high_risk_count"],  yesterday_stats["high_risk_count"])

    kpis = [
        {"icon": "📊", "label": "총 신고",    "value": overall_stats["count"],
         "delta": count_d, "dcls": count_c,  "color": "#3b82f6"},
        {"icon": "📈", "label": "평균 위험도", "value": f"{overall_stats['avg_intensity']:.1f}",
         "delta": avg_d,   "dcls": avg_c,    "color": "#f59e0b"},
        {"icon": "🔴", "label": "고위험 신고", "value": overall_stats["high_risk_count"],
         "delta": high_d,  "dcls": high_c,   "color": "#ef4444"},
        {"icon": "⊞",  "label": "분석 격자",  "value": f"{grid_count:,}",
         "delta": "실시간 갱신",              "dcls": "zero", "color": "#8b5cf6"},
        {"icon": "🏘",  "label": "행정동 수",  "value": dong_count,
         "delta": "서울 중구",               "dcls": "zero", "color": "#22c55e"},
    ]
    cards = "".join(
        f'<div class="pgis-kpi">'
        f'<div class="pgis-kpi__topbar" style="background:{k["color"]};"></div>'
        f'<div class="pgis-kpi__head">'
        f'<span class="pgis-kpi__label">{k["label"]}</span>'
        f'<span class="pgis-kpi__icon">{k["icon"]}</span>'
        f'</div>'
        f'<div class="pgis-kpi__value">{k["value"]}</div>'
        f'<span class="pgis-kpi__delta pgis-kpi__delta--{k["dcls"]}">{k["delta"]}</span>'
        f'</div>'
        for k in kpis
    )
    return f'<div class="pgis-kpi-row">{cards}</div>'


def get_risk_display(intensity):
    if intensity >= 4:
        return "높음", "high"
    if intensity >= 3:
        return "주의", "mid"
    return "낮음", "low"

_REPORT_TYPE_THEMES = {
    "조명 부족":   {"gradient": "linear-gradient(135deg,#f97316 0%,#ea580c 100%)", "icon": "💡", "soft": "#fff7ed", "accent": "#f97316"},
    "시야 차단":   {"gradient": "linear-gradient(135deg,#ef4444 0%,#dc2626 100%)", "icon": "🚧", "soft": "#fff1f0", "accent": "#ef4444"},
    "도로 파손":   {"gradient": "linear-gradient(135deg,#8b5cf6 0%,#7c3aed 100%)", "icon": "🕳️",  "soft": "#f5f3ff", "accent": "#8b5cf6"},
    "불법 주정차": {"gradient": "linear-gradient(135deg,#3b82f6 0%,#2563eb 100%)", "icon": "🚗", "soft": "#eff6ff", "accent": "#3b82f6"},
    "기타":        {"gradient": "linear-gradient(135deg,#64748b 0%,#475569 100%)", "icon": "⚠️", "soft": "#f8fafc", "accent": "#64748b"},
}

def build_report_popup_html(report):
    report_type  = report.get("type", "기타")
    intensity    = max(1, min(5, coerce_int(report.get("intensity"), 3)))
    time_val     = html.escape(str(report.get("time", "-")))
    dong         = html.escape(str(report.get("dong", "-")))
    desc         = html.escape(str(report.get("desc", "")).strip())
    report_id    = coerce_int(report.get("id"), 0)
    theme        = _REPORT_TYPE_THEMES.get(report_type, _REPORT_TYPE_THEMES["기타"])
    escaped_type = html.escape(report_type)

    intensity_pct   = intensity * 20
    risk_label = (
        "높음" if intensity >= 4 else
        "주의" if intensity >= 3 else
        "낮음"
    )
    dots = "".join(
        f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
        f'background:{"#ef4444" if i <= intensity and intensity >= 4 else "#f59e0b" if i <= intensity and intensity >= 3 else "#22c55e" if i <= intensity else "#e2e8f0"}'
        f';margin-right:2px;"></span>'
        for i in range(1, 6)
    )
    desc_block = (
        f'<div style="background:{theme["soft"]};border-left:3px solid {theme["accent"]};'
        f'border-radius:0 6px 6px 0;padding:7px 9px;margin-top:8px;">'
        f'<div style="font-size:10px;color:#374151;line-height:1.5;">{desc}</div></div>'
    ) if desc else ""

    return (
        f'<div class="pgis-report-card" style="width:258px;font-family:system-ui,-apple-system,BlinkMacSystemFont,'
        f"'Segoe UI',sans-serif;border-radius:13px;overflow:hidden;box-shadow:0 16px 40px rgba(15,23,42,.22);\">"

        # ── Header ──────────────────────────────────────────────────────────
        f'<div style="background:{theme["gradient"]};padding:12px 13px 10px;color:#fff;">'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
        f'<div style="width:30px;height:30px;border-radius:8px;background:rgba(255,255,255,.22);'
        f'display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;">{theme["icon"]}</div>'
        f'<div style="min-width:0;flex:1;">'
        f'<div style="font-size:13px;font-weight:800;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{escaped_type}</div>'
        f'<div style="font-size:10px;opacity:.82;margin-top:2px;">{dong} · #{report_id}</div>'
        f'</div>'
        f'<div style="flex-shrink:0;padding:3px 8px;border-radius:999px;background:rgba(255,255,255,.2);'
        f'border:1px solid rgba(255,255,255,.32);font-size:10px;font-weight:800;">{risk_label}</div>'
        f'</div>'
        # progress bar
        f'<div style="background:rgba(255,255,255,.22);border-radius:999px;height:4px;overflow:hidden;">'
        f'<div style="width:{intensity_pct}%;height:100%;background:#fff;border-radius:999px;"></div>'
        f'</div>'
        f'</div>'

        # ── Body ─────────────────────────────────────────────────────────────
        f'<div style="padding:10px 12px 12px;background:#fff;">'
        # dots row
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">'
        f'<div>'
        f'<div style="font-size:9px;color:#94a3b8;font-weight:700;letter-spacing:.3px;text-transform:uppercase;">위험도</div>'
        f'<div style="margin-top:4px;">{dots}</div>'
        f'</div>'
        f'<div style="font-size:24px;font-weight:900;color:#0f172a;line-height:1;">{intensity}'
        f'<span style="font-size:11px;font-weight:600;color:#94a3b8;">/5</span></div>'
        f'</div>'
        # info grid
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;">'
        f'<div style="background:#f8fafc;border-radius:7px;padding:6px 8px;border:1px solid #e5e7eb;">'
        f'<div style="font-size:9px;color:#94a3b8;font-weight:700;">⏱ 신고 시간</div>'
        f'<div style="font-size:11px;font-weight:700;color:#0f172a;margin-top:2px;">{time_val}</div>'
        f'</div>'
        f'<div style="background:#f8fafc;border-radius:7px;padding:6px 8px;border:1px solid #e5e7eb;">'
        f'<div style="font-size:9px;color:#94a3b8;font-weight:700;">📍 행정동</div>'
        f'<div style="font-size:11px;font-weight:700;color:#0f172a;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{dong}</div>'
        f'</div>'
        f'</div>'
        f'{desc_block}'
        f'</div>'
        f'</div>'
    )

class RightClickQueryHandler(MacroElement):
    _template = Template(f"""
    {{% macro script(this, kwargs) %}}
        const map = {{{{ this._parent.get_name() }}}};

        map.on("contextmenu", function(e) {{
            if (e.originalEvent) {{
                e.originalEvent.preventDefault();
                e.originalEvent.stopPropagation();
            }}

            const coords = {{ lat: e.latlng.lat, lng: e.latlng.lng }};
            const globalData = window.__GLOBAL_DATA__;
            if (!globalData || !window.Streamlit) {{
                return;
            }}

            globalData.last_object_clicked = coords;
            globalData.last_object_clicked_tooltip = "{RIGHT_CLICK_QUERY_TOKEN}";
            globalData.last_object_clicked_popup = null;

            const data = {{
                last_clicked: null,
                last_object_clicked: coords,
                last_object_clicked_tooltip: "{RIGHT_CLICK_QUERY_TOKEN}",
                last_object_clicked_popup: null
            }};
            globalData.previous_data = data;
            window.Streamlit.setComponentValue(data);
        }});
    {{% endmacro %}}
    """)

class BottomRightZoomControl(MacroElement):
    _template = Template("""
    {% macro script(this, kwargs) %}
        L.control.zoom({ position: "bottomright" }).addTo({{ this._parent.get_name() }});
    {% endmacro %}
    """)

def render_report_status_table(df_reports, selected_dong):
    df_all = df_reports.sort_values("id", ascending=False).copy()
    total_count = len(df_all)
    high_count = int((df_all["intensity"] >= 4).sum()) if total_count else 0
    avg_intensity = float(df_all["intensity"].mean()) if total_count else 0
    filter_label = selected_dong if selected_dong != "전체" else "전체 동"
    df = df_all.head(REPORT_TABLE_LIMIT)
    visible_count = len(df)

    rows = []
    for report in df.to_dict("records"):
        report_id = coerce_int(report.get("id"), 0)
        intensity = max(1, min(5, coerce_int(report.get("intensity"), 3)))
        risk_label, risk_class = get_risk_display(intensity)
        meter_width = intensity * 20
        dong = html.escape(str(report.get("dong", "-")))
        report_type = html.escape(str(report.get("type", "-")))
        time_value = html.escape(str(report.get("time", "-")))
        desc = html.escape(str(report.get("desc", "")).strip() or "설명 없음")

        rows.append(f"""
            <tr>
                <td class="col-id">#{report_id}</td>
                <td class="col-status"><span class="status-badge">기록 완료</span></td>
                <td class="col-dong">{dong}</td>
                <td class="col-type">{report_type}</td>
                <td class="col-risk">
                    <div class="risk-cell">
                        <span class="risk-badge {risk_class}">{risk_label} · {intensity}/5</span>
                        <div class="risk-meter"><span style="width: {meter_width}%"></span></div>
                    </div>
                </td>
                <td class="col-time">{time_value}</td>
                <td class="col-desc"><div class="desc-text" title="{desc}">{desc}</div></td>
            </tr>
        """)

    body = "\n".join(rows)
    return f"""
    {CUSTOM_CSS}
    <style>
        body {{
            margin: 0;
            padding: 2px 4px 18px;
            background: transparent;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }}
    </style>
    <div class="report-board">
        <div class="report-board__header">
            <div>
                <div class="report-board__title">업로드 현황</div>
                <div class="report-board__sub">최근 등록된 신고 데이터를 위치와 위험도 중심으로 정리했습니다.</div>
            </div>
            <div class="report-board__meta">
                <span class="report-pill">필터 {html.escape(str(filter_label))}</span>
                <span class="report-pill">최근 {visible_count}건 표시</span>
                <span class="report-pill">전체 {total_count}건</span>
                <span class="report-pill">고위험 {high_count}건</span>
                <span class="report-pill">평균 {avg_intensity:.1f}/5</span>
            </div>
        </div>
        <div class="report-table-wrap">
            <table class="report-table">
                <thead>
                    <tr>
                        <th class="col-id">ID</th>
                        <th class="col-status">상태</th>
                        <th class="col-dong">동</th>
                        <th class="col-type">유형</th>
                        <th class="col-risk">위험도</th>
                        <th class="col-time">시간</th>
                        <th class="col-desc">설명</th>
                    </tr>
                </thead>
                <tbody>{body}</tbody>
            </table>
        </div>
    </div>
    """

def normalize_database_url(database_url):
    if not database_url:
        return None

    database_url = database_url.strip()
    if database_url.startswith("postgres://"):
        database_url = "postgresql://" + database_url[len("postgres://"):]
    return database_url

def get_database_url():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return normalize_database_url(database_url)

    try:
        database_url = st.secrets.get("DATABASE_URL")
    except Exception:
        database_url = None

    return normalize_database_url(database_url)

def is_database_enabled():
    return bool(get_database_url())

def get_db_connection():
    try:
        import psycopg2
    except ImportError as exc:
        raise RuntimeError("PostgreSQL 저장을 사용하려면 psycopg2-binary가 필요합니다.") from exc

    return psycopg2.connect(get_database_url())

def row_to_report(row):
    created_at = row.get("created_at")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat(timespec="minutes")
    elif created_at is None:
        created_at = ""

    return normalize_report({
        "id": row.get("id"),
        "lng": row.get("lng"),
        "lat": row.get("lat"),
        "type": row.get("type", "신고"),
        "intensity": row.get("intensity", 3),
        "time": row.get("report_time", ""),
        "created_at": created_at,
        "desc": row.get("description", ""),
        "dong": row.get("dong", ""),
    })

def ensure_reports_table():
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {REPORTS_TABLE} (
                        id BIGSERIAL PRIMARY KEY,
                        lng DOUBLE PRECISION NOT NULL,
                        lat DOUBLE PRECISION NOT NULL,
                        type TEXT NOT NULL DEFAULT '신고',
                        intensity INTEGER NOT NULL CHECK (intensity BETWEEN 1 AND 5),
                        report_time TEXT NOT NULL DEFAULT '',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        description TEXT NOT NULL DEFAULT '',
                        dong TEXT NOT NULL DEFAULT ''
                    )
                """)
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{REPORTS_TABLE}_created_at ON {REPORTS_TABLE} (created_at)")
                cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{REPORTS_TABLE}_dong ON {REPORTS_TABLE} (dong)")
    finally:
        conn.close()

def load_reports_from_db():
    from psycopg2.extras import RealDictCursor

    ensure_reports_table()
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"""
                    SELECT id, lng, lat, type, intensity, report_time, created_at, description, dong
                    FROM {REPORTS_TABLE}
                    ORDER BY id ASC
                """)
                return [row_to_report(row) for row in cur.fetchall()]
    finally:
        conn.close()

def insert_report_to_db(report):
    from psycopg2.extras import RealDictCursor

    ensure_reports_table()
    normalized = normalize_report(report)
    created_at = parse_report_datetime(normalized) or datetime.now()

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    f"""
                    INSERT INTO {REPORTS_TABLE}
                        (lng, lat, type, intensity, report_time, created_at, description, dong)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, lng, lat, type, intensity, report_time, created_at, description, dong
                    """,
                    (
                        normalized["lng"],
                        normalized["lat"],
                        normalized["type"],
                        normalized["intensity"],
                        str(normalized.get("time", "")),
                        created_at,
                        str(normalized.get("desc", "")),
                        normalized["dong"],
                    ),
                )
                return row_to_report(cur.fetchone())
    finally:
        conn.close()

def persist_report(report):
    if is_database_enabled():
        try:
            return insert_report_to_db(report)
        except Exception as e:
            st.error(f"DB 저장 오류: {e}")
            return None

    return normalize_report(report)

def load_reports():
    if is_database_enabled():
        try:
            st.session_state.storage_backend = "PostgreSQL"
            return load_reports_from_db()
        except Exception as e:
            st.warning(f"PostgreSQL 연결 실패로 reports.json을 임시 사용합니다: {e}")
            st.session_state.storage_backend = "reports.json fallback"

    if os.path.exists(REPORTS_FILE):
        try:
            with open(REPORTS_FILE, "r", encoding="utf-8") as f:
                st.session_state.storage_backend = "reports.json"
                return json.load(f)
        except Exception as e:
            st.warning(f"reports.json을 읽지 못해 빈 데이터로 시작합니다: {e}")
            return []
    st.session_state.storage_backend = "reports.json"
    return []

def save_reports(reports):
    if is_database_enabled():
        return True

    try:
        with open(REPORTS_FILE, "w", encoding="utf-8") as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"저장 오류: {e}")
        return False

def show_session_feedback(key):
    feedback = st.session_state.get(key)
    if not feedback:
        return

    feedback_type, feedback_message = feedback
    if feedback_type == "success":
        st.success(feedback_message)
    elif feedback_type == "warning":
        st.warning(feedback_message)
    elif feedback_type == "error":
        st.error(feedback_message)
    else:
        st.info(feedback_message)
    st.session_state[key] = None

# ========== 세션 상태 ==========
if "reports" not in st.session_state:
    st.session_state.reports = load_reports()
normalized_reports = normalize_reports(st.session_state.reports)
if normalized_reports != st.session_state.reports:
    st.session_state.reports = normalized_reports
    save_reports(st.session_state.reports)
else:
    st.session_state.reports = normalized_reports
next_report_id = max((coerce_int(r.get("id"), 0) for r in st.session_state.reports), default=0) + 1
if "next_id" not in st.session_state or st.session_state.next_id < next_report_id:
    st.session_state.next_id = next_report_id
if "grid" not in st.session_state:
    st.session_state.grid = create_grid()
if "selected_dong" not in st.session_state:
    st.session_state.selected_dong = "전체"
if "clicked_lat" not in st.session_state:
    st.session_state.clicked_lat = None
if "clicked_lng" not in st.session_state:
    st.session_state.clicked_lng = None
if "query_lat" not in st.session_state:
    st.session_state.query_lat = None
if "query_lng" not in st.session_state:
    st.session_state.query_lng = None
if "location_input_version" not in st.session_state:
    st.session_state.location_input_version = 0
if "map_click_msg" not in st.session_state:
    st.session_state.map_click_msg = False
if "map_focus" not in st.session_state:
    st.session_state.map_focus = "register"
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True
if "show_upload" not in st.session_state:
    st.session_state.show_upload = False
if "report_feedback" not in st.session_state:
    st.session_state.report_feedback = None
if "upload_feedback" not in st.session_state:
    st.session_state.upload_feedback = None

reports_all = st.session_state.reports
reports_df_all = pd.DataFrame(reports_all) if reports_all else pd.DataFrame()

# ========== 메인 헤더 ==========
st.markdown(f"""
<div class="pgis-header">
    <div class="pgis-header__eyebrow">
        <span class="pgis-live-dot"></span>&nbsp;실시간 분석
    </div>
    <h1>서울 중구 안전지도</h1>
    <p>베이지안 정리 기반 위험도 분석 · 좌클릭 신고 등록 · 우클릭 확률 조회 · 마커 호버 신고 상세</p>
    <div class="pgis-header__chips">
        <div class="pgis-header__chip">⊞&nbsp;<b>{len(st.session_state.grid):,}</b>개 격자</div>
        <div class="pgis-header__chip">🏘&nbsp;<b>{len(JUNGGU_DONGS)}</b>개 행정동</div>
        <div class="pgis-header__chip">📐&nbsp;<b>{GRID_SIZE_M}m</b> 격자 간격</div>
        <div class="pgis-header__chip">🎯&nbsp;<b>{REPORT_INFLUENCE_RADIUS_M}m</b> 영향 반경</div>
        <div class="pgis-header__chip">📊&nbsp;<b>{len(reports_all)}</b>건 누적 신고</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ========== 메트릭 ==========
today = datetime.now().date()
yesterday = today - timedelta(days=1)
report_date_buckets = split_reports_by_dates(reports_all, [today, yesterday], today)
today_reports = report_date_buckets[today]
yesterday_reports = report_date_buckets[yesterday]
overall_stats = summarize_reports(reports_all)
today_stats = summarize_reports(today_reports)
yesterday_stats = summarize_reports(yesterday_reports)

st.markdown(
    render_kpi_row(overall_stats, today_stats, yesterday_stats, len(st.session_state.grid), len(JUNGGU_DONGS)),
    unsafe_allow_html=True,
)

st.divider()

# ========== 클릭 알림 ==========
if st.session_state.map_click_msg:
    st.markdown(f"""
    <div class="click-alert">
        <span>📍</span>
        <span>위치 선택 완료 &nbsp;—&nbsp; 위도 <b>{st.session_state.clicked_lat:.5f}</b> / 경도 <b>{st.session_state.clicked_lng:.5f}</b></span>
    </div>
    """, unsafe_allow_html=True)

show_session_feedback("report_feedback")

# ========== 메인 레이아웃 ==========
selected_dong = st.session_state.get("selected_dong", "전체")
dong_options = ["전체"] + list(JUNGGU_DONGS.keys())
if selected_dong not in dong_options:
    st.session_state.selected_dong = "전체"
    selected_dong = "전체"

if st.session_state.map_focus == "query" and st.session_state.query_lat is not None and st.session_state.query_lng is not None:
    workflow_title = "확률 조회 모드"
    workflow_sub = f"조회 위치 기준 · 위도 {st.session_state.query_lat:.5f} / 경도 {st.session_state.query_lng:.5f}"
elif st.session_state.clicked_lat is not None and st.session_state.clicked_lng is not None:
    workflow_title = "신고 위치 선택됨"
    workflow_sub = f"좌측 신고 폼에서 유형과 설명을 완성하세요 · {get_dong_by_coords(st.session_state.clicked_lat, st.session_state.clicked_lng)}"
else:
    workflow_title = "지도 탐색 대기"
    workflow_sub = "지도 좌클릭은 신고 위치 선택, 우클릭은 사고 가능성 조회입니다."

form_chip = "신고 폼 열림" if st.session_state.sidebar_open else "신고 폼 접힘"
st.markdown(f"""
<div class="pgis-command-strip">
    <div class="pgis-command-strip__main">
        <div class="pgis-command-strip__title">작업 상태 · {html.escape(workflow_title)}</div>
        <div class="pgis-command-strip__sub">{html.escape(workflow_sub)}</div>
    </div>
    <div class="pgis-command-strip__meta">
        <span class="pgis-state-chip pgis-state-chip--active">필터 {html.escape(str(selected_dong))}</span>
        <span class="pgis-state-chip">{form_chip}</span>
        <span class="pgis-state-chip">신고 {len(reports_all):,}건</span>
    </div>
</div>
""", unsafe_allow_html=True)

action_col1, action_col2, action_col3 = st.columns([1, 1, 4], gap="small")
with action_col1:
    if st.button("신고 폼 접기" if st.session_state.sidebar_open else "신고 폼 열기", key="toggle_report_form", use_container_width=True):
        st.session_state.sidebar_open = not st.session_state.sidebar_open
        st.rerun()
with action_col2:
    has_active_map_state = (
        st.session_state.clicked_lat is not None
        or st.session_state.clicked_lng is not None
        or st.session_state.query_lat is not None
        or st.session_state.query_lng is not None
    )
    if st.button("선택 초기화", key="clear_map_selection", use_container_width=True, disabled=not has_active_map_state):
        st.session_state.clicked_lat = None
        st.session_state.clicked_lng = None
        st.session_state.query_lat = None
        st.session_state.query_lng = None
        st.session_state.map_click_msg = False
        st.session_state.map_focus = "register"
        st.session_state.location_input_version += 1
        st.rerun()
with action_col3:
    has_clicked_location = st.session_state.clicked_lat is not None and st.session_state.clicked_lng is not None
    has_query_location_for_action = st.session_state.query_lat is not None and st.session_state.query_lng is not None
    if st.session_state.map_focus == "query" and has_query_location_for_action:
        if st.button("조회 위치를 신고 폼으로 가져오기", key="copy_query_to_report", use_container_width=True):
            st.session_state.clicked_lat = st.session_state.query_lat
            st.session_state.clicked_lng = st.session_state.query_lng
            st.session_state.sidebar_open = True
            st.session_state.map_click_msg = True
            st.session_state.map_focus = "register"
            st.session_state.location_input_version += 1
            st.rerun()
    elif has_clicked_location:
        if st.button("선택 위치 위험도 조회", key="query_selected_location", use_container_width=True):
            st.session_state.query_lat = st.session_state.clicked_lat
            st.session_state.query_lng = st.session_state.clicked_lng
            st.session_state.map_click_msg = False
            st.session_state.map_focus = "query"
            st.rerun()
    else:
        st.button("위치 선택 후 빠른 작업 가능", key="quick_action_placeholder", use_container_width=True, disabled=True)

if st.session_state.sidebar_open:
    col_left, col_right = st.columns([0.9, 3.4], gap="medium")
else:
    col_right = st.container()

# ========== 좌측: 신고 폼 ==========
if st.session_state.sidebar_open:
    with col_left:
        st.markdown("""
        <div class="pgis-section-head" style="margin-bottom:10px;">
            <div class="pgis-section-title">
                <div class="pgis-section-title__icon" style="background:#eff6ff;">📝</div>
                신고 작성
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 동 선택
        selected_dong = st.selectbox(
            "📍 동 선택",
            dong_options,
            key="selected_dong",
        )

        st.markdown("---")

        # 신고 폼
        with st.form("report_form", border=True):
            st.markdown("**새 신고 작성**")

            report_type = st.selectbox("위험 유형", ["조명 부족", "시야 차단", "도로 파손", "불법 주정차", "기타"])
            intensity = st.slider("위험도", 1, 5, 3, help="1: 안전 → 5: 매우 위험")

            default_lat = st.session_state.clicked_lat if st.session_state.clicked_lat is not None else JUNGGU_CENTER[0]
            default_lng = st.session_state.clicked_lng if st.session_state.clicked_lng is not None else JUNGGU_CENTER[1]
            input_version = st.session_state.location_input_version
            coord_col1, coord_col2 = st.columns(2)
            with coord_col1:
                lat = st.number_input("위도", value=float(default_lat), format="%.6f", key=f"lat_input_{input_version}")
            with coord_col2:
                lng = st.number_input("경도", value=float(default_lng), format="%.6f", key=f"lng_input_{input_version}")
            selected_report_dong = get_dong_by_coords(lat, lng)

            desc = st.text_area("상세 설명", max_chars=100, placeholder="예: 횡단보도 직전 조명 전부 고장...")

            if selected_report_dong == "알 수 없음":
                st.warning("선택한 좌표가 등록된 중구 행정동 범위 밖입니다.")
            elif st.session_state.clicked_lat is not None and st.session_state.clicked_lng is not None:
                st.success(f"✅ 지도에서 선택된 위치 · {selected_report_dong}")
                st.caption(f"위도 {lat:.6f} / 경도 {lng:.6f}")
            else:
                st.info("💡 오른쪽 지도에서 좌클릭 한 번으로 신고 위치를 선택하세요.")

            if st.form_submit_button("📌 신고 등록", use_container_width=True):
                dong = get_dong_by_coords(lat, lng)
                if dong == "알 수 없음":
                    st.error("서울 중구 행정동 범위 안의 위치를 선택하거나 위도/경도를 조정해주세요.")
                else:
                    created_at = datetime.now()
                    new_report = {
                        "id": st.session_state.next_id,
                        "lng": lng,
                        "lat": lat,
                        "type": report_type,
                        "intensity": intensity,
                        "time": created_at.strftime("%m-%d %H:%M"),
                        "created_at": created_at.isoformat(timespec="minutes"),
                        "desc": desc,
                        "dong": dong,
                    }
                    dedupe_key = report_dedupe_key(new_report)
                    existing_keys = {
                        key for key in (report_dedupe_key(report) for report in st.session_state.reports)
                        if key is not None
                    }
                    if dedupe_key in existing_keys:
                        st.warning("이미 같은 위치·유형·강도·설명의 신고가 등록되어 있습니다.")
                    else:
                        saved_report = persist_report(new_report)
                        if saved_report:
                            st.session_state.reports.append(saved_report)
                            st.session_state.next_id = max(st.session_state.next_id, saved_report["id"] + 1)
                            save_reports(st.session_state.reports)
                            st.session_state.clicked_lat = None
                            st.session_state.clicked_lng = None
                            st.session_state.location_input_version += 1
                            st.session_state.map_click_msg = False
                            st.session_state.report_feedback = ("success", f"✅ 신고 저장 완료 | {dong}")
                            st.rerun()

        show_session_feedback("upload_feedback")

        with st.expander("데이터 관리", expanded=False):
            data_quality = summarize_report_quality(reports_all)
            st.markdown(render_data_quality_summary(data_quality), unsafe_allow_html=True)
            if data_quality["issue_count"]:
                st.caption("검토 필요 항목은 중복 의심, 좌표 누락, 중구 범위 밖, 행정동 미확정 데이터를 포함합니다.")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("CSV 다운로드", use_container_width=True):
                    if reports_all:
                        df = reports_df_all.copy()
                        export_columns = ["id", "lat", "lng", "dong", "type", "intensity", "time", "created_at", "desc"]
                        df = df[[col for col in export_columns if col in df.columns]]
                        csv = df.to_csv(index=False, encoding="utf-8-sig")
                        st.download_button(
                            "지도 데이터 CSV 다운로드",
                            csv,
                            f"pgis_map_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "text/csv",
                            use_container_width=True
                        )
                    else:
                        st.info("신고 데이터가 없습니다")

            with col_b:
                if st.button("CSV 업로드", use_container_width=True):
                    st.session_state.show_upload = True

            if st.session_state.get("show_upload", False):
                uploaded = st.file_uploader("CSV 파일 선택", type=["csv"])
                if uploaded:
                    st.caption(
                        f"최대 {CSV_UPLOAD_ROW_LIMIT:,}행까지 업로드됩니다. "
                        "중복 기준은 좌표·유형·강도·설명 조합입니다."
                    )
                if uploaded and st.button("업로드 실행", use_container_width=True):
                    try:
                        df = pd.read_csv(uploaded)
                        if len(df) > CSV_UPLOAD_ROW_LIMIT:
                            st.error(f"한 번에 {CSV_UPLOAD_ROW_LIMIT:,}행까지만 업로드할 수 있습니다.")
                        else:
                            uploaded_at = datetime.now()
                            saved_count = 0
                            skipped_count = 0
                            outside_count = 0
                            duplicate_count = 0
                            last_uploaded_report = None
                            existing_keys = {
                                key for key in (report_dedupe_key(report) for report in st.session_state.reports)
                                if key is not None
                            }

                            for row in df.to_dict("records"):
                                new_report = build_report_from_csv_row(row, st.session_state.next_id, uploaded_at)
                                if not new_report:
                                    skipped_count += 1
                                    continue
                                if not is_within_junggu_bounds(new_report["lat"], new_report["lng"]):
                                    outside_count += 1
                                    continue

                                dedupe_key = report_dedupe_key(new_report)
                                if dedupe_key in existing_keys:
                                    duplicate_count += 1
                                    continue

                                saved_report = persist_report(new_report)
                                if saved_report:
                                    st.session_state.reports.append(saved_report)
                                    st.session_state.next_id = max(st.session_state.next_id, saved_report["id"] + 1)
                                    existing_keys.add(dedupe_key)
                                    saved_count += 1
                                    last_uploaded_report = saved_report

                            save_reports(st.session_state.reports)
                            if last_uploaded_report:
                                st.session_state.clicked_lat = last_uploaded_report["lat"]
                                st.session_state.clicked_lng = last_uploaded_report["lng"]
                                st.session_state.location_input_version += 1
                                st.session_state.map_click_msg = True
                                st.session_state.map_focus = "register"

                            upload_summary = [f"{saved_count:,}건 업로드"]
                            if skipped_count:
                                upload_summary.append(f"위도/경도 누락 {skipped_count:,}건 제외")
                            if outside_count:
                                upload_summary.append(f"중구 범위 밖 {outside_count:,}건 제외")
                            if duplicate_count:
                                upload_summary.append(f"중복 {duplicate_count:,}건 제외")

                            if saved_count:
                                st.session_state.upload_feedback = ("success", "✅ " + " · ".join(upload_summary))
                            else:
                                no_save_details = " · ".join(upload_summary[1:]) or f"{len(df):,}행 처리"
                                st.session_state.upload_feedback = (
                                    "warning",
                                    "신규로 추가된 신고가 없습니다 · " + no_save_details,
                                )

                            st.session_state.show_upload = False
                            st.rerun()
                    except Exception as e:
                        st.error(f"오류: {e}")

            if st.button("새로고침", use_container_width=True):
                st.rerun()

# ========== 우측: 지도 ==========
with col_right:
    reports_for_map = reports_all
    map_marker_candidates = [
        report for report in reports_for_map
        if selected_dong == "전체" or report.get("dong") == selected_dong
    ]
    map_marker_candidates.sort(key=lambda report: coerce_int(report.get("id"), 0), reverse=True)
    map_marker_total = len(map_marker_candidates)
    map_reports = map_marker_candidates[:MAP_MARKER_LIMIT]
    hidden_marker_count = max(0, map_marker_total - len(map_reports))
    marker_label = f"{len(map_reports):,}/{map_marker_total:,}건"

    st.markdown(f"""
    <div class="pgis-section-head">
        <div class="pgis-section-title">
            <div class="pgis-section-title__icon" style="background:#fef9c3;">🎯</div>
            베이지안 위험도 지도
        </div>
        <div class="pgis-hint-row">
            <span class="pgis-hint">🖱 <b>좌클릭</b>&nbsp;신고 등록</span>
            <span class="pgis-hint">🖱 <b>우클릭</b>&nbsp;확률 조회</span>
            <span class="pgis-hint">↔ <b>빠른 작업</b>&nbsp;선택·조회 전환</span>
            <span class="pgis-hint">✦ <b>마커 호버</b>&nbsp;신고 상세</span>
            <span class="pgis-hint">● <b>지도 표시</b>&nbsp;{marker_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if hidden_marker_count:
        st.caption(f"지도 성능을 위해 최신 {MAP_MARKER_LIMIT:,}건만 마커로 표시합니다. 상세 분석과 위험도 계산은 전체 {map_marker_total:,}건 기준입니다.")
    
    # 베이지안 계산
    report_arrays = prepare_report_arrays(reports_for_map)
    map_hotspots = calculate_hotspot_candidates(
        st.session_state.grid,
        reports_for_map,
        selected_dong,
        MAP_HOTSPOT_LIMIT,
    )
    query_lat = st.session_state.query_lat
    query_lng = st.session_state.query_lng
    has_query_location = query_lat is not None and query_lng is not None
    query_stats = (
        calculate_bayesian_stats_from_arrays(query_lat, query_lng, report_arrays)
        if has_query_location else None
    )
    selected_map_lat = st.session_state.clicked_lat
    selected_map_lng = st.session_state.clicked_lng
    has_selected_location = selected_map_lat is not None and selected_map_lng is not None
    if st.session_state.map_focus == "query" and has_query_location:
        map_center = [query_lat, query_lng]
    elif has_selected_location:
        map_center = [selected_map_lat, selected_map_lng]
    elif has_query_location:
        map_center = [query_lat, query_lng]
    else:
        map_center = JUNGGU_CENTER
    
    # 지도 생성
    m = folium.Map(
        location=map_center,
        zoom_start=15 if has_selected_location or has_query_location else 13,
        tiles="CartoDB positron",
        zoom_control=False,
        control_scale=True,
        prefer_canvas=True,
    )
    RightClickQueryHandler().add_to(m)
    BottomRightZoomControl().add_to(m)
    m.get_root().header.add_child(folium.Element("""
    <style>
        html, body, .folium-map, .leaflet-container {
            max-width: 100% !important;
            width: 100% !important;
        }
        /* ── Hover tooltip: strip Leaflet's default wrapper ── */
        .leaflet-tooltip:has(.pgis-report-card) {
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            padding: 0 !important;
            border-radius: 0 !important;
        }
        .leaflet-tooltip:has(.pgis-report-card)::before {
            display: none !important;
        }
        /* ── Query popup anchor ── */
        .query-risk-div-icon {
            background: transparent !important;
            border: 0 !important;
        }
        .query-risk-anchor {
            position: absolute;
            left: 0;
            top: 0;
            transform: translate(-50%, calc(-100% - 18px));
            pointer-events: none;
            z-index: 1000;
        }
        .query-risk-anchor::after {
            content: "";
            position: absolute;
            left: 50%;
            bottom: -6px;
            width: 12px;
            height: 12px;
            transform: translateX(-50%) rotate(45deg);
            background: #ffffff;
            border-right: 1px solid rgba(148, 163, 184, 0.28);
            border-bottom: 1px solid rgba(148, 163, 184, 0.28);
        }
        .query-risk-card {
            width: 252px;
            overflow: hidden;
            border-radius: 12px;
            background: #ffffff;
            color: #0f172a;
            border: 1px solid rgba(148, 163, 184, 0.30);
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.20);
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        .query-risk-head {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 10px;
            padding: 10px 11px 9px;
            color: #ffffff;
        }
        .query-risk-kicker {
            font-size: 11px;
            font-weight: 700;
            opacity: 0.88;
        }
        .query-risk-value {
            margin-top: 4px;
            font-size: 25px;
            line-height: 1;
            font-weight: 850;
        }
        .query-risk-badge {
            padding: 4px 7px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.24);
            font-size: 10px;
            font-weight: 800;
            white-space: nowrap;
        }
        .query-risk-body {
            padding: 9px 10px 10px;
        }
        .query-risk-place {
            font-size: 10px;
            color: #64748b;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .query-risk-bar {
            height: 5px;
            margin-top: 7px;
            border-radius: 999px;
            background: #e5e7eb;
            overflow: hidden;
        }
        .query-risk-bar > div {
            height: 100%;
            border-radius: 999px;
        }
        .query-risk-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            margin-top: 9px;
        }
        .query-risk-grid div {
            padding: 6px 7px;
            border-radius: 8px;
            background: #f8fafc;
            border: 1px solid #e5e7eb;
        }
        .query-risk-grid span {
            display: block;
            font-size: 10px;
            color: #64748b;
            font-weight: 700;
        }
        .query-risk-grid b {
            display: block;
            margin-top: 2px;
            font-size: 13px;
            color: #0f172a;
        }
        .query-risk-note {
            margin-top: 8px;
            font-size: 11px;
            line-height: 1.35;
            color: #334155;
        }

        /* ── 핀 애니메이션 ── */
        @keyframes pgis-ring {
            0%   { transform: scale(0.4); opacity: 0.7; }
            100% { transform: scale(2.8); opacity: 0;   }
        }
        @keyframes pgis-pop {
            0%   { transform: scale(0.7); }
            60%  { transform: scale(1.15); }
            100% { transform: scale(1);   }
        }

        /* ── 우클릭 쿼리 핀 ── */
        .pgis-qpin { position: relative; width: 0; height: 0; }
        .pgis-qpin__dot {
            position: absolute;
            width: 18px; height: 18px;
            border-radius: 50%;
            border: 2.5px solid #fff;
            box-shadow: 0 2px 14px rgba(0,0,0,.38), 0 0 0 1px rgba(0,0,0,.06);
            top: -9px; left: -9px;
            z-index: 20;
            animation: pgis-pop .35s cubic-bezier(.34,1.56,.64,1) both;
        }
        .pgis-qpin__ring {
            position: absolute;
            width: 18px; height: 18px;
            border-radius: 50%;
            top: -9px; left: -9px;
            z-index: 19;
            opacity: 0;
            animation: pgis-ring 2.4s ease-out infinite;
        }

        /* ── 신고 위치 핀 ── */
        .pgis-selpin { position: relative; width: 0; height: 0; }
        .pgis-selpin__dot {
            position: absolute;
            width: 18px; height: 18px;
            border-radius: 50%;
            background: #2563eb;
            border: 3px solid #fff;
            box-shadow: 0 3px 16px rgba(37,99,235,.55);
            top: -9px; left: -9px;
            z-index: 20;
            animation: pgis-pop .35s cubic-bezier(.34,1.56,.64,1) both;
        }
        .pgis-selpin__ring {
            position: absolute;
            width: 18px; height: 18px;
            border-radius: 50%;
            background: #3b82f6;
            top: -9px; left: -9px;
            z-index: 19;
            opacity: 0;
            animation: pgis-ring 2.2s ease-out infinite;
        }

        /* ── 신고 마커 핀 ── */
        .pgis-rpin {
            position: relative;
            filter: drop-shadow(0 4px 7px rgba(0,0,0,.28));
        }
        .pgis-rpin__body {
            width: 30px; height: 30px;
            border-radius: 50% 50% 50% 0;
            transform: rotate(-45deg);
            border: 2.5px solid #fff;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .pgis-rpin__emoji {
            transform: rotate(45deg);
            font-size: 13px;
            line-height: 1;
            margin-top: 1px;
        }
        @media (max-width: 640px) {
            .query-risk-anchor {
                transform: translate(-50%, calc(-100% - 12px)) scale(.9);
                transform-origin: bottom center;
            }
            .query-risk-card,
            .pgis-report-card {
                width: min(232px, calc(100vw - 28px)) !important;
            }
            .pgis-map-legend {
                right: 10px !important;
                bottom: 12px !important;
                min-width: 142px !important;
                padding: 10px 11px 11px !important;
            }
        }
    </style>
    """))
    
    # 베이지안 분포 — 선택(클릭/우클릭) 시에만 주변 격자 표시
    _active_lat = (
        query_lat if (st.session_state.map_focus == "query" and has_query_location)
        else (selected_map_lat if has_selected_location else None)
    )
    _active_lon = (
        query_lng if (st.session_state.map_focus == "query" and has_query_location)
        else (selected_map_lng if has_selected_location else None)
    )

    if _active_lat is not None:
        # 선택 지점의 위험도 색상
        if st.session_state.map_focus == "query" and has_query_location and query_stats:
            _prob_c = query_stats["posterior"]
        else:
            _prob_c = calculate_bayesian_stats_from_arrays(
                _active_lat, _active_lon, report_arrays
            )["posterior"]
        _col_c = get_color(_prob_c)
        _hw_c  = get_heat_weight(_prob_c)

        # 동심원 그라디언트 — 중심에서 바깥으로 자연스럽게 페이드
        # (큰 원부터 렌더→작은 원이 위에 쌓여 중심이 가장 진하게)
        _rings = [
            (REPORT_INFLUENCE_RADIUS_M * 1.60, 0.012 + _hw_c * 0.008),
            (REPORT_INFLUENCE_RADIUS_M * 1.15, 0.025 + _hw_c * 0.015),
            (REPORT_INFLUENCE_RADIUS_M * 0.78, 0.045 + _hw_c * 0.025),
            (REPORT_INFLUENCE_RADIUS_M * 0.48, 0.070 + _hw_c * 0.040),
            (REPORT_INFLUENCE_RADIUS_M * 0.22, 0.100 + _hw_c * 0.060),
        ]
        for _r, _op in _rings:
            folium.Circle(
                location=[_active_lat, _active_lon],
                radius=_r,
                color="none",
                weight=0,
                fill=True,
                fillColor=_col_c,
                fillOpacity=round(_op, 3),
                interactive=False,
            ).add_to(m)

    # 베이지안 위험 후보 지점 — 전체 격자 계산 상위 후보만 얇게 표시
    for rank, hotspot in enumerate(map_hotspots, start=1):
        grade = get_probability_grade(hotspot["posterior"])
        probability = hotspot["posterior"] * 100
        hotspot_tip = f"""
        <div style="font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:2px 0;">
            <div style="font-weight:850;color:#0f172a;font-size:12px;margin-bottom:4px;">#{rank} 위험 후보 · {html.escape(str(hotspot["dong"]))}</div>
            <div style="font-size:11px;color:#475569;">예상 위험도 <b>{probability:.0f}%</b> · 주변 신고 {hotspot["report_count"]:,}건</div>
            <div style="font-size:10.5px;color:#94a3b8;margin-top:3px;">좌표 {hotspot["lat"]:.5f}, {hotspot["lng"]:.5f}</div>
        </div>
        """
        folium.CircleMarker(
            location=[hotspot["lat"], hotspot["lng"]],
            radius=max(7, 13 - rank),
            color=grade["color"],
            weight=2,
            fill=True,
            fillColor=grade["color"],
            fillOpacity=0.16,
            tooltip=folium.Tooltip(hotspot_tip, sticky=True),
        ).add_to(m)

    # 신고 마커 — 커스텀 핀
    _type_cfg = {
        "조명 부족":   {"emoji": "💡", "bg": "#f97316"},
        "시야 차단":   {"emoji": "🚧", "bg": "#ef4444"},
        "도로 파손":   {"emoji": "🕳️",  "bg": "#8b5cf6"},
        "불법 주정차": {"emoji": "🚗", "bg": "#3b82f6"},
        "기타":        {"emoji": "⚠️", "bg": "#64748b"},
    }

    for report in map_reports:
        tip_html = build_report_popup_html(report)
        cfg = _type_cfg.get(report.get("type", "기타"), _type_cfg["기타"])
        folium.Marker(
            location=[report["lat"], report["lng"]],
            tooltip=folium.Tooltip(tip_html, sticky=True),
            icon=folium.DivIcon(
                icon_size=(30, 36),
                icon_anchor=(7, 30),
                html=f"""
                <div class="pgis-rpin">
                    <div class="pgis-rpin__body" style="background:{cfg['bg']};">
                        <span class="pgis-rpin__emoji">{cfg['emoji']}</span>
                    </div>
                </div>
                """,
            ),
        ).add_to(m)
    
    if st.session_state.map_focus == "query" and has_query_location and query_stats:
        query_dong = get_dong_by_coords(query_lat, query_lng)
        probability = query_stats["posterior"]
        probability_color = get_color(probability)
        query_popup = build_query_popup_html(query_lat, query_lng, query_dong, query_stats, reports_for_map)
        folium.Marker(
            location=[query_lat, query_lng],
            icon=folium.DivIcon(
                icon_size=(0, 0),
                icon_anchor=(0, 0),
                html=f"""
                <div class="pgis-qpin">
                    <div class="pgis-qpin__dot" style="background:{probability_color};"></div>
                    <div class="pgis-qpin__ring" style="background:{probability_color};"></div>
                </div>
                """,
            ),
        ).add_to(m)
        folium.Marker(
            location=[query_lat, query_lng],
            icon=folium.DivIcon(
                icon_size=(0, 0),
                icon_anchor=(0, 0),
                class_name="query-risk-div-icon",
                html=f"""<div class="query-risk-anchor">{query_popup}</div>""",
            ),
        ).add_to(m)

    if has_selected_location:
        selected_location_dong = get_dong_by_coords(selected_map_lat, selected_map_lng)
        _sel_stats = calculate_bayesian_stats_from_arrays(selected_map_lat, selected_map_lng, report_arrays)
        sel_grade = get_probability_grade(_sel_stats["posterior"])
        selected_popup = f"""
        <div style="font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:2px 0;">
            <div style="font-weight:800;color:#0f172a;font-size:13px;margin-bottom:6px;">신고 등록 위치</div>
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;">
                <span style="background:{sel_grade['color']};color:#fff;font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px;">{sel_grade['label']}</span>
                <span style="color:#64748b;font-size:11px;">{selected_location_dong}</span>
            </div>
            <div style="font-size:11px;color:#94a3b8;">위도 {selected_map_lat:.6f} / 경도 {selected_map_lng:.6f}</div>
        </div>
        """
        folium.Marker(
            location=[selected_map_lat, selected_map_lng],
            popup=folium.Popup(selected_popup, max_width=240),
            tooltip="신고 위치 — 클릭하면 위험도 확인",
            icon=folium.DivIcon(
                icon_size=(0, 0),
                icon_anchor=(0, 0),
                html="""
                <div class="pgis-selpin">
                    <div class="pgis-selpin__dot"></div>
                    <div class="pgis-selpin__ring"></div>
                </div>
                """,
            ),
        ).add_to(m)

    legend_html = """
    <div class="pgis-map-legend" style="
        position: fixed;
        right: 18px;
        bottom: 36px;
        z-index: 9999;
        min-width: 168px;
        padding: 13px 16px 14px;
        background: rgba(10,15,28,0.88);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,.10);
        border-radius: 14px;
        box-shadow: 0 10px 36px rgba(0,0,0,.38);
        font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    ">
        <div style="font-size:10px;font-weight:700;letter-spacing:.7px;color:#475569;text-transform:uppercase;margin-bottom:8px;">위험도</div>
        <div style="height:6px;border-radius:999px;background:linear-gradient(90deg,#10b981 0%,#f59e0b 42%,#f97316 70%,#ef4444 100%);margin-bottom:5px;"></div>
        <div style="display:flex;justify-content:space-between;font-size:9.5px;color:#64748b;margin-bottom:14px;">
            <span>안전</span><span>관찰</span><span>주의</span><span>위험</span>
        </div>
        <div style="border-top:1px solid rgba(255,255,255,.08);padding-top:12px;">
            <div style="font-size:10px;font-weight:700;letter-spacing:.7px;color:#475569;text-transform:uppercase;margin-bottom:8px;">신고 유형</div>
            <div style="display:flex;flex-direction:column;gap:5px;">
                <div style="display:flex;align-items:center;gap:7px;">
                    <span style="width:9px;height:9px;border-radius:50%;background:#f97316;flex-shrink:0;"></span>
                    <span style="font-size:11px;color:#cbd5e1;">💡 조명 부족</span>
                </div>
                <div style="display:flex;align-items:center;gap:7px;">
                    <span style="width:9px;height:9px;border-radius:50%;background:#ef4444;flex-shrink:0;"></span>
                    <span style="font-size:11px;color:#cbd5e1;">🚧 시야 차단</span>
                </div>
                <div style="display:flex;align-items:center;gap:7px;">
                    <span style="width:9px;height:9px;border-radius:50%;background:#8b5cf6;flex-shrink:0;"></span>
                    <span style="font-size:11px;color:#cbd5e1;">🕳️ 도로 파손</span>
                </div>
                <div style="display:flex;align-items:center;gap:7px;">
                    <span style="width:9px;height:9px;border-radius:50%;background:#3b82f6;flex-shrink:0;"></span>
                    <span style="font-size:11px;color:#cbd5e1;">🚗 불법 주정차</span>
                </div>
            </div>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # 지도 렌더링 및 클릭 처리
    map_height = 660 if st.session_state.sidebar_open else 720
    st_folium_kwargs = {
        "height": map_height,
        "returned_objects": [
            "last_clicked",
            "last_object_clicked",
            "last_object_clicked_tooltip",
            "last_object_clicked_popup",
        ],
    }
    if ST_FOLIUM_SUPPORTS_CONTAINER_WIDTH:
        st_folium_kwargs["use_container_width"] = True
    else:
        st_folium_kwargs["width"] = 1040

    map_data = st_folium(m, **st_folium_kwargs)
    
    # 클릭 이벤트 처리
    map_interaction = get_map_interaction(map_data)
    if map_interaction:
        interaction_type, clicked_lat, clicked_lng = map_interaction
        if interaction_type == "register":
            is_new_location = (
                st.session_state.clicked_lat is None
                or st.session_state.clicked_lng is None
                or abs(st.session_state.clicked_lat - clicked_lat) > 0.000001
                or abs(st.session_state.clicked_lng - clicked_lng) > 0.000001
            )
            if is_new_location:
                st.session_state.clicked_lat = clicked_lat
                st.session_state.clicked_lng = clicked_lng
                st.session_state.location_input_version += 1
                st.session_state.map_click_msg = True
                st.session_state.map_focus = "register"
                st.rerun()
        elif interaction_type == "query":
            is_new_query = (
                st.session_state.query_lat is None
                or st.session_state.query_lng is None
                or abs(st.session_state.query_lat - clicked_lat) > 0.000001
                or abs(st.session_state.query_lng - clicked_lng) > 0.000001
            )
            if is_new_query:
                st.session_state.query_lat = clicked_lat
                st.session_state.query_lng = clicked_lng
                st.session_state.map_focus = "query"
                st.rerun()

# ========== 하단: 분석 ==========
st.divider()
st.markdown("""
<div class="pgis-section-head">
    <div class="pgis-section-title">
        <div class="pgis-section-title__icon" style="background:#ecfdf5;">📊</div>
        상세 분석
    </div>
</div>
""", unsafe_allow_html=True)

if reports_all:
    reports_df = reports_df_all.copy()
    if reports_df.empty or "dong" not in reports_df.columns:
        st.info("분석 가능한 신고 데이터가 없습니다.")
    else:
        analysis_df = reports_df.copy()
        if selected_dong != "전체":
            analysis_df = analysis_df[analysis_df["dong"] == selected_dong].copy()

        if analysis_df.empty:
            st.info("선택한 동에 분석 가능한 신고 데이터가 없습니다.")
        else:
            analysis_df["intensity"] = (
                pd.to_numeric(analysis_df["intensity"], errors="coerce")
                .fillna(3)
                .clip(1, 5)
                .astype(int)
            )
            analysis_df["type"] = (
                analysis_df.get("type", pd.Series(["기타"] * len(analysis_df), index=analysis_df.index))
                .fillna("기타")
                .replace("", "기타")
            )
            parsed_datetimes = []
            for report in analysis_df.to_dict("records"):
                parsed = parse_report_datetime(report, today)
                if parsed is not None and parsed.tzinfo is not None:
                    parsed = parsed.astimezone().replace(tzinfo=None)
                parsed_datetimes.append(parsed)
            analysis_df["parsed_at"] = pd.to_datetime(parsed_datetimes, errors="coerce")
            dated_analysis_df = analysis_df.dropna(subset=["parsed_at"]).copy()
            hotspot_candidates = calculate_hotspot_candidates(
                st.session_state.grid,
                analysis_df.to_dict("records"),
                selected_dong,
                HOTSPOT_LIMIT,
            )
            top_hotspot = hotspot_candidates[0] if hotspot_candidates else None

            analysis_scope = selected_dong if selected_dong != "전체" else "전체 동"
            analysis_count = len(analysis_df)
            avg_intensity = float(analysis_df["intensity"].mean()) if analysis_count else 0
            high_risk = int((analysis_df["intensity"] >= 4).sum())
            mid_risk = int((analysis_df["intensity"] == 3).sum())
            low_risk = int((analysis_df["intensity"] <= 2).sum())

            type_counts = analysis_df["type"].value_counts().reset_index()
            type_counts.columns = ["type", "count"]
            top_type = str(type_counts.iloc[0]["type"]) if not type_counts.empty else "-"
            top_type_count = int(type_counts.iloc[0]["count"]) if not type_counts.empty else 0

            dong_stats = (
                analysis_df.groupby("dong")
                .agg(
                    count=("intensity", "count"),
                    avg_intensity=("intensity", "mean"),
                    high_count=("intensity", lambda s: int((s >= 4).sum())),
                )
                .sort_values(["count", "avg_intensity"], ascending=False)
                .reset_index()
            )
            top_dong = str(dong_stats.iloc[0]["dong"]) if not dong_stats.empty else "-"
            top_dong_count = int(dong_stats.iloc[0]["count"]) if not dong_stats.empty else 0
            dong_risk = (
                analysis_df.groupby("dong")
                .agg(
                    count=("intensity", "count"),
                    avg=("intensity", "mean"),
                    high_count=("intensity", lambda s: int((s >= 4).sum())),
                )
                .sort_values(["avg", "count"], ascending=False)
                .reset_index()
            )
            top_watch_row = dong_risk.iloc[0] if not dong_risk.empty else None

            if not dated_analysis_df.empty:
                dated_analysis_df["report_date"] = dated_analysis_df["parsed_at"].dt.date
                dated_analysis_df["report_hour"] = dated_analysis_df["parsed_at"].dt.hour
                latest_date = dated_analysis_df["report_date"].max()
                recent_start = latest_date - timedelta(days=6)
                previous_start = latest_date - timedelta(days=13)
                recent_df = dated_analysis_df[dated_analysis_df["report_date"] >= recent_start]
                previous_df = dated_analysis_df[
                    (dated_analysis_df["report_date"] >= previous_start)
                    & (dated_analysis_df["report_date"] < recent_start)
                ]
                recent_count = len(recent_df)
                previous_count = len(previous_df)
                trend_delta = recent_count - previous_count
                if trend_delta > 0:
                    trend_label = f"최근 7일 +{trend_delta:,}건"
                    trend_color = "#ef4444"
                elif trend_delta < 0:
                    trend_label = f"최근 7일 {trend_delta:,}건"
                    trend_color = "#16a34a"
                else:
                    trend_label = "최근 7일 변동 없음"
                    trend_color = "#64748b"
                peak_hour = int(dated_analysis_df["report_hour"].mode().iloc[0])
                peak_hour_label = f"{peak_hour:02d}:00대"
                latest_high_count = int((recent_df["intensity"] >= 4).sum())
            else:
                recent_count = 0
                previous_count = 0
                trend_label = "날짜 데이터 부족"
                trend_color = "#64748b"
                peak_hour_label = "집계 불가"
                latest_high_count = 0

            def _analysis_color(avg):
                if avg >= 4.0:
                    return "#ef4444"
                if avg >= 3.0:
                    return "#f97316"
                if avg >= 2.0:
                    return "#f59e0b"
                return "#22c55e"

            def _avg_risk_display(avg):
                if avg >= 4.0:
                    return "고위험", "#ef4444"
                if avg >= 3.0:
                    return "주의", "#f97316"
                if avg >= 2.0:
                    return "관찰", "#f59e0b"
                return "낮음", "#22c55e"

            def _chart_layout(title, height=430, left_margin=8, bottom_margin=30):
                return dict(
                    height=height,
                    showlegend=False,
                    plot_bgcolor="#ffffff",
                    paper_bgcolor="#ffffff",
                    font=dict(
                        family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                        size=12,
                        color="#475569",
                    ),
                    margin=dict(l=left_margin, r=34, t=48, b=bottom_margin),
                    title=dict(text=title, font_size=14, x=0, y=0.98),
                    hoverlabel=dict(bgcolor="#0f172a", bordercolor="#0f172a", font_color="#f8fafc"),
                    hovermode="closest",
                    bargap=0.34,
                )

            _plotly_config = {
                "displayModeBar": "hover",
                "displaylogo": False,
                "responsive": True,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            }

            if top_hotspot:
                hotspot_grade = get_probability_grade(top_hotspot["posterior"])
                watch_value = f'{top_hotspot["dong"]} {top_hotspot["posterior"]:.0%}'
                watch_sub = f'격자 #{top_hotspot["id"]} · 주변 신고 {top_hotspot["report_count"]:,}건 · 밀도 {top_hotspot["density_factor"]:.0%}'
                watch_color = hotspot_grade["color"]
            else:
                watch_value = str(top_watch_row["dong"]) if top_watch_row is not None else top_dong
                watch_sub = (
                    f'평균 {float(top_watch_row["avg"]):.1f}/5 · 고위험 {int(top_watch_row["high_count"]):,}건'
                    if top_watch_row is not None else "분석 데이터 부족"
                )
                watch_color = _analysis_color(float(top_watch_row["avg"])) if top_watch_row is not None else "#64748b"
            briefing_cards = [
                {
                    "label": "우선 확인",
                    "value": watch_value,
                    "sub": watch_sub,
                    "color": watch_color,
                },
                {
                    "label": "최근 흐름",
                    "value": trend_label,
                    "sub": f"최근 7일 {recent_count:,}건 · 이전 7일 {previous_count:,}건",
                    "color": trend_color,
                },
                {
                    "label": "집중 시간",
                    "value": peak_hour_label,
                    "sub": f"최근 고위험 {latest_high_count:,}건",
                    "color": "#8b5cf6",
                },
                {
                    "label": "대응 유형",
                    "value": top_type,
                    "sub": f"{top_type_count:,}건 · 지도 마커 색상과 동일",
                    "color": _REPORT_TYPE_THEMES.get(top_type, _REPORT_TYPE_THEMES["기타"])["accent"],
                },
            ]
            briefing_html = "".join(
                f'<div class="analysis-brief-card" style="border-top:3px solid {card["color"]};">'
                f'<div class="analysis-brief-label"><span style="color:{card["color"]};">●</span>{html.escape(card["label"])}</div>'
                f'<div class="analysis-brief-value" title="{html.escape(str(card["value"]))}">{html.escape(str(card["value"]))}</div>'
                f'<div class="analysis-brief-sub">{html.escape(card["sub"])}</div>'
                f'</div>'
                for card in briefing_cards
            )
            st.markdown(f'<div class="analysis-brief-row">{briefing_html}</div>', unsafe_allow_html=True)

            summary_cards = [
                {
                    "label": "분석 범위",
                    "value": analysis_scope,
                    "sub": f"{analysis_count:,}건 기준",
                    "color": "#3b82f6",
                },
                {
                    "label": "평균 위험도",
                    "value": f"{avg_intensity:.1f}/5",
                    "sub": f"높음 {high_risk:,}건 · 주의 {mid_risk:,}건 · 낮음 {low_risk:,}건",
                    "color": _analysis_color(avg_intensity),
                },
                {
                    "label": "최다 신고 지역",
                    "value": top_dong,
                    "sub": f"{top_dong_count:,}건 신고",
                    "color": "#8b5cf6",
                },
                {
                    "label": "주요 신고 유형",
                    "value": top_type,
                    "sub": f"{top_type_count:,}건",
                    "color": _REPORT_TYPE_THEMES.get(top_type, _REPORT_TYPE_THEMES["기타"])["accent"],
                },
            ]
            summary_html = "".join(
                f'<div class="analysis-summary-card" style="border-top:3px solid {card["color"]};">'
                f'<div class="analysis-summary-label"><span style="color:{card["color"]};">●</span>{html.escape(card["label"])}</div>'
                f'<div class="analysis-summary-value" title="{html.escape(str(card["value"]))}">{html.escape(str(card["value"]))}</div>'
                f'<div class="analysis-summary-sub">{html.escape(card["sub"])}</div>'
                f'</div>'
                for card in summary_cards
            )
            st.markdown(f'<div class="analysis-summary-row">{summary_html}</div>', unsafe_allow_html=True)

            tab_trend, tab_hotspot, tab_dong, tab_intensity, tab_type, tab_watch = st.tabs(
                ["추세", "위험 후보", "행정동 순위", "위험도 분포", "신고 유형", "주의 지역"]
            )

            with tab_trend:
                st.markdown(
                    '<div class="analysis-tip">최근 흐름을 먼저 보고, 신고가 늘어난 기간과 집중 시간대를 함께 확인합니다.</div>',
                    unsafe_allow_html=True,
                )
                if dated_analysis_df.empty:
                    st.info("추세를 계산할 수 있는 날짜 데이터가 부족합니다.")
                else:
                    daily_trend = (
                        dated_analysis_df.groupby("report_date")
                        .agg(
                            count=("intensity", "count"),
                            avg_intensity=("intensity", "mean"),
                            high_count=("intensity", lambda s: int((s >= 4).sum())),
                        )
                    )
                    daily_trend.index = pd.to_datetime(daily_trend.index)
                    trend_end = pd.to_datetime(latest_date)
                    trend_start = max(daily_trend.index.min(), trend_end - pd.Timedelta(days=29))
                    trend_index = pd.date_range(trend_start, trend_end, freq="D")
                    daily_trend = daily_trend.reindex(trend_index)
                    daily_trend["count"] = daily_trend["count"].fillna(0).astype(int)
                    daily_trend["high_count"] = daily_trend["high_count"].fillna(0).astype(int)
                    daily_trend["avg_intensity"] = daily_trend["avg_intensity"].fillna(0)
                    daily_trend["label"] = daily_trend.index.strftime("%m-%d")

                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Bar(
                        x=daily_trend["label"],
                        y=daily_trend["count"],
                        name="신고 건수",
                        marker_color="#93c5fd",
                        marker_line_width=0,
                        customdata=daily_trend["high_count"],
                        hovertemplate="<b>%{x}</b><br>신고 %{y:,}건<br>고위험 %{customdata:,}건<extra></extra>",
                    ))
                    fig_trend.add_trace(go.Scatter(
                        x=daily_trend["label"],
                        y=daily_trend["avg_intensity"],
                        name="평균 위험도",
                        mode="lines+markers",
                        yaxis="y2",
                        line=dict(color="#ef4444", width=3, shape="spline"),
                        marker=dict(size=6, color="#ef4444"),
                        hovertemplate="<b>%{x}</b><br>평균 위험도 %{y:.1f}/5<extra></extra>",
                    ))
                    trend_layout = _chart_layout(
                        f"<b>{html.escape(analysis_scope)} 최근 신고 추세</b>",
                        height=430,
                        bottom_margin=46,
                    )
                    trend_layout.update(
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                            font_size=11,
                        ),
                        yaxis=dict(
                            title_text="신고 건수",
                            showgrid=True,
                            gridcolor="#f1f5f9",
                            zeroline=False,
                            linecolor="#e2e8f0",
                        ),
                        yaxis2=dict(
                            title_text="평균 위험도",
                            overlaying="y",
                            side="right",
                            range=[0, 5.2],
                            showgrid=False,
                            zeroline=False,
                            linecolor="#e2e8f0",
                        ),
                    )
                    fig_trend.update_layout(**trend_layout)
                    fig_trend.update_xaxes(title_text="날짜", tickangle=-35, linecolor="#e2e8f0")
                    st.plotly_chart(fig_trend, use_container_width=True, config=_plotly_config)

                    hour_counts = (
                        dated_analysis_df["report_hour"]
                        .value_counts()
                        .reindex(range(24), fill_value=0)
                        .sort_index()
                    )
                    hour_labels = [f"{hour:02d}시" for hour in hour_counts.index]
                    hour_colors = [
                        "#ef4444" if hour == peak_hour else "#cbd5e1"
                        for hour in hour_counts.index
                    ]
                    fig_hour = go.Figure(go.Bar(
                        x=hour_labels,
                        y=hour_counts.values,
                        marker_color=hour_colors,
                        marker_line_width=0,
                        text=[f"{int(v):,}" if v > 0 else "" for v in hour_counts.values],
                        textposition="outside",
                        cliponaxis=False,
                        hovertemplate="<b>%{x}</b><br>신고 %{y:,}건<extra></extra>",
                    ))
                    fig_hour.update_layout(
                        **_chart_layout(
                            f"<b>{html.escape(analysis_scope)} 시간대별 신고 집중도</b>",
                            height=360,
                            bottom_margin=42,
                        )
                    )
                    fig_hour.update_xaxes(title_text="시간대", tickangle=-35, linecolor="#e2e8f0")
                    fig_hour.update_yaxes(
                        title_text="신고 건수",
                        showgrid=True,
                        gridcolor="#f1f5f9",
                        zeroline=False,
                        linecolor="#e2e8f0",
                    )
                    st.plotly_chart(fig_hour, use_container_width=True, config=_plotly_config)

            with tab_hotspot:
                st.markdown(
                    '<div class="analysis-tip">베이지안 격자 계산으로 위험 후보 지점을 추립니다. 지도 위 원형 레이어와 같은 후보입니다.</div>',
                    unsafe_allow_html=True,
                )
                if not hotspot_candidates:
                    st.info("위험 후보를 계산할 수 있는 신고 데이터가 아직 부족합니다.")
                else:
                    st.markdown(render_hotspot_candidates(hotspot_candidates), unsafe_allow_html=True)
                    hotspot_labels = [
                        f"#{rank} {hotspot['dong']} · {hotspot['posterior']:.0%} · 주변 {hotspot['report_count']:,}건"
                        for rank, hotspot in enumerate(hotspot_candidates, start=1)
                    ]
                    selected_hotspot_label = st.selectbox(
                        "후보 액션",
                        hotspot_labels,
                        key="selected_hotspot_action",
                    )
                    selected_hotspot = hotspot_candidates[hotspot_labels.index(selected_hotspot_label)]
                    hotspot_action_col1, hotspot_action_col2 = st.columns(2)
                    with hotspot_action_col1:
                        if st.button("선택 후보 위험도 조회", use_container_width=True):
                            st.session_state.query_lat = selected_hotspot["lat"]
                            st.session_state.query_lng = selected_hotspot["lng"]
                            st.session_state.map_focus = "query"
                            st.session_state.map_click_msg = False
                            st.rerun()
                    with hotspot_action_col2:
                        if st.button("선택 후보를 신고 폼으로 가져오기", use_container_width=True):
                            st.session_state.clicked_lat = selected_hotspot["lat"]
                            st.session_state.clicked_lng = selected_hotspot["lng"]
                            st.session_state.sidebar_open = True
                            st.session_state.map_focus = "register"
                            st.session_state.map_click_msg = True
                            st.session_state.location_input_version += 1
                            st.rerun()
                    hotspot_export = pd.DataFrame([
                        {
                            "rank": rank,
                            "grid_id": hotspot["id"],
                            "dong": hotspot["dong"],
                            "lat": hotspot["lat"],
                            "lng": hotspot["lng"],
                            "probability": round(hotspot["posterior"], 4),
                            "nearby_reports": hotspot["report_count"],
                            "density_factor": round(hotspot["density_factor"], 4),
                            "local_risk": round(hotspot["local_risk"], 4),
                        }
                        for rank, hotspot in enumerate(hotspot_candidates, start=1)
                    ])
                    st.download_button(
                        "위험 후보 CSV 다운로드",
                        hotspot_export.to_csv(index=False, encoding="utf-8-sig"),
                        f"pgis_hotspots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv",
                        use_container_width=True,
                    )

            with tab_dong:
                st.markdown(
                    '<div class="analysis-tip">신고가 많은 행정동을 먼저 보여줍니다. 막대 색은 해당 동의 평균 위험도입니다.</div>',
                    unsafe_allow_html=True,
                )
                dong_chart_df = (
                    dong_stats.head(12)
                    .sort_values(["count", "avg_intensity"], ascending=True)
                    .reset_index(drop=True)
                )
                fig1 = go.Figure(go.Bar(
                    x=dong_chart_df["count"],
                    y=dong_chart_df["dong"],
                    orientation="h",
                    marker_color=[_analysis_color(a) for a in dong_chart_df["avg_intensity"]],
                    marker_line_width=0,
                    text=[f"{int(c):,}건" for c in dong_chart_df["count"]],
                    textposition="outside",
                    textfont=dict(size=11, color="#475569"),
                    cliponaxis=False,
                    customdata=list(zip(dong_chart_df["avg_intensity"], dong_chart_df["high_count"])),
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "신고 %{x:,}건<br>"
                        "평균 위험도 %{customdata[0]:.1f}/5<br>"
                        "고위험 %{customdata[1]:,}건<extra></extra>"
                    ),
                ))
                fig1.update_layout(
                    **_chart_layout(
                        f"<b>{html.escape(analysis_scope)} 행정동별 신고 순위</b>",
                        height=max(360, 120 + len(dong_chart_df) * 34),
                        left_margin=92,
                    )
                )
                fig1.update_xaxes(
                    title_text="신고 건수",
                    showgrid=True,
                    gridcolor="#f1f5f9",
                    zeroline=False,
                    linecolor="#e2e8f0",
                )
                fig1.update_yaxes(title_text="", showgrid=False, linecolor="#e2e8f0")
                st.plotly_chart(fig1, use_container_width=True, config=_plotly_config)

            with tab_intensity:
                st.markdown(
                    '<div class="analysis-tip">신고의 심각도가 어느 단계에 몰려 있는지 확인합니다. 비율이 높은 단계부터 현장 대응 우선순위를 잡기 좋습니다.</div>',
                    unsafe_allow_html=True,
                )
                all_levels = pd.Series(0, index=range(1, 6))
                intensity_counts = analysis_df["intensity"].value_counts()
                intensity_dist = all_levels.add(intensity_counts, fill_value=0).astype(int)
                total_i = intensity_dist.sum() or 1
                level_colors = ["#22c55e", "#84cc16", "#f59e0b", "#f97316", "#ef4444"]
                level_labels = ["1 낮음", "2", "3 보통", "4", "5 높음"]
                level_share = [v / total_i for v in intensity_dist.values]

                fig2 = go.Figure(go.Bar(
                    x=level_labels,
                    y=intensity_dist.values,
                    marker_color=level_colors,
                    marker_line_width=0,
                    text=[f"{v:,}건<br>{share:.0%}" if v > 0 else "" for v, share in zip(intensity_dist.values, level_share)],
                    textposition="outside",
                    textfont=dict(size=11, color="#475569"),
                    cliponaxis=False,
                    customdata=level_share,
                    hovertemplate="<b>위험도 %{x}</b><br>신고 %{y:,}건<br>비율 %{customdata:.1%}<extra></extra>",
                ))
                fig2.update_layout(
                    **_chart_layout(f"<b>{html.escape(analysis_scope)} 위험도 단계별 분포</b>", height=410)
                )
                fig2.update_xaxes(title_text="위험도 단계", showgrid=False, linecolor="#e2e8f0")
                fig2.update_yaxes(
                    title_text="신고 건수",
                    showgrid=True,
                    gridcolor="#f1f5f9",
                    zeroline=False,
                    linecolor="#e2e8f0",
                )
                st.plotly_chart(fig2, use_container_width=True, config=_plotly_config)

            with tab_type:
                st.markdown(
                    '<div class="analysis-tip">유형별 신고 비중입니다. 같은 색상 체계를 지도 마커와 맞춰 두었습니다.</div>',
                    unsafe_allow_html=True,
                )
                type_color_map = {
                    "조명 부족": "#f97316",
                    "시야 차단": "#ef4444",
                    "도로 파손": "#8b5cf6",
                    "불법 주정차": "#3b82f6",
                    "기타": "#94a3b8",
                }
                total_t = type_counts["count"].sum() or 1
                type_chart_df = type_counts.sort_values("count", ascending=True).reset_index(drop=True)
                type_share = [c / total_t for c in type_chart_df["count"]]
                fig3 = go.Figure(go.Bar(
                    x=type_chart_df["count"],
                    y=type_chart_df["type"],
                    orientation="h",
                    marker_color=[type_color_map.get(t, "#94a3b8") for t in type_chart_df["type"]],
                    marker_line_width=0,
                    text=[f"{int(c):,}건 · {share:.0%}" for c, share in zip(type_chart_df["count"], type_share)],
                    textposition="outside",
                    textfont=dict(size=11, color="#475569"),
                    cliponaxis=False,
                    customdata=type_share,
                    hovertemplate="<b>%{y}</b><br>신고 %{x:,}건<br>비율 %{customdata:.1%}<extra></extra>",
                ))
                fig3.update_layout(
                    **_chart_layout(
                        f"<b>{html.escape(analysis_scope)} 신고 유형별 분포</b>",
                        height=max(340, 150 + len(type_chart_df) * 44),
                        left_margin=96,
                    )
                )
                fig3.update_xaxes(showgrid=True, gridcolor="#f1f5f9", linecolor="#e2e8f0", title_text="신고 건수")
                fig3.update_yaxes(showgrid=False, linecolor="#e2e8f0", autorange="reversed")
                st.plotly_chart(fig3, use_container_width=True, config=_plotly_config)

            with tab_watch:
                st.markdown(
                    '<div class="analysis-tip">평균 위험도와 신고 건수를 함께 보고 우선 확인할 지역을 고릅니다.</div>',
                    unsafe_allow_html=True,
                )
                rows_html = ""
                for rank, row in enumerate(dong_risk.head(10).to_dict("records"), start=1):
                    risk_label, risk_color = _avg_risk_display(float(row["avg"]))
                    meter_width = max(6, min(100, float(row["avg"]) / 5 * 100))
                    rows_html += (
                        f'<div class="pgis-risk-row">'
                        f'<div class="pgis-risk-rank">{rank}</div>'
                        f'<div>'
                        f'<div class="pgis-risk-name">{html.escape(str(row["dong"]))}</div>'
                        f'<div class="pgis-risk-meta">신고 {int(row["count"]):,}건 · 고위험 {int(row["high_count"]):,}건</div>'
                        f'<div class="pgis-risk-meter"><span style="width:{meter_width:.0f}%;background:{risk_color};"></span></div>'
                        f'</div>'
                        f'<div class="pgis-risk-score"><b>{float(row["avg"]):.1f}</b><span style="background:{risk_color};">{risk_label}</span></div>'
                        f'</div>'
                    )
                st.markdown(
                    f'<div class="pgis-risk-list">'
                    f'<div class="pgis-risk-list__head">'
                    f'<div>'
                    f'<div class="pgis-risk-list__title">주의 필요 지역</div>'
                    f'<div class="pgis-risk-list__sub">{html.escape(analysis_scope)} · 평균 위험도순</div>'
                    f'</div>'
                    f'<div class="report-pill">{analysis_count:,}건 분석</div>'
                    f'</div>'
                    f'{rows_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

st.markdown("""
<div class="pgis-section-head">
    <div class="pgis-section-title">
        <div class="pgis-section-title__icon" style="background:#f0f9ff;">📋</div>
        업로드 현황
    </div>
</div>
""", unsafe_allow_html=True)
if reports_all:
    df_reports = reports_df_all.copy()
    if df_reports.empty or "dong" not in df_reports.columns:
        st.info("표시할 수 있는 신고 데이터가 없습니다.")
    else:
        if selected_dong != "전체":
            df_reports = df_reports[df_reports["dong"] == selected_dong]

        if df_reports.empty:
            st.info("선택한 동에 표시할 신고 데이터가 없습니다.")
        else:
            report_table_rows = min(len(df_reports), REPORT_TABLE_LIMIT)
            report_table_height = min(640, max(260, 116 + report_table_rows * 44))
            components.html(
                render_report_status_table(df_reports, selected_dong),
                height=report_table_height,
                scrolling=True,
            )
else:
    st.info("📌 아직 신고가 없습니다. 지도에서 좌클릭 한 번으로 신고 위치를 등록해주세요.")

# ========== 푸터 ==========
st.divider()
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.caption("💡 **베이지안 정리**: P(위험|신고) = P(신고|위험)×P(위험) / P(신고)")
with col_f2:
    st.caption(f"📍 **범위**: 서울 중구 | **격자**: {GRID_SIZE_M}m | **영향 반경**: {REPORT_INFLUENCE_RADIUS_M}m | **동**: {len(JUNGGU_DONGS)}개")
with col_f3:
    storage_backend = st.session_state.get(
        "storage_backend",
        "PostgreSQL" if is_database_enabled() else "reports.json",
    )
    st.caption(f"💾 자동 저장: {storage_backend} | 화면 갱신: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
