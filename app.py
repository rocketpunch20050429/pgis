"""
Bayesian PGIS 서울 중구 안전지도 - 지도 클릭 직접 입력
"""

import json
import os
from datetime import datetime, timedelta
import html
import math
import streamlit as st
import streamlit.components.v1 as components
from branca.element import MacroElement, Template
import folium
from folium.plugins import HeatMap
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

.stApp { background: #f0f4f8 !important; }
.main .block-container {
    padding: 1.5rem 2rem 4rem !important;
    max-width: 1720px !important;
}

/* ── Header ──────────────────────────────────────────────────────────── */
.pgis-header {
    position: relative;
    overflow: hidden;
    background: #0f172a;
    border-radius: 16px;
    padding: 26px 32px 22px;
    margin-bottom: 18px;
    box-shadow: 0 24px 48px rgba(15,23,42,.22), inset 0 1px 0 rgba(255,255,255,.05);
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
    letter-spacing: .5px;
    text-transform: uppercase;
    margin-bottom: 9px;
}
.pgis-header h1 {
    margin: 0 !important;
    font-size: 1.875rem !important;
    font-weight: 900 !important;
    color: #f8fafc !important;
    line-height: 1.15 !important;
    letter-spacing: -.5px !important;
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
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin-bottom: 18px;
}
.pgis-kpi {
    position: relative;
    overflow: hidden;
    background: #fff;
    border-radius: 12px;
    padding: 16px 18px 14px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(15,23,42,.05);
    transition: box-shadow .2s, transform .2s;
    cursor: default;
}
.pgis-kpi:hover {
    box-shadow: 0 8px 24px rgba(15,23,42,.09);
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
    letter-spacing: -.2px;
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
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 3px rgba(15,23,42,.05) !important;
    padding: 1.1rem !important;
}

/* ── Report board ────────────────────────────────────────────────────── */
.report-board {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(15,23,42,.05);
}
.report-board__header {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: flex-end;
    padding: 14px 18px;
    border-bottom: 1px solid #e2e8f0;
    background: #f8fafc;
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

/* ── Streamlit overrides ─────────────────────────────────────────────── */
hr { border: none !important; border-top: 1px solid #e2e8f0 !important; margin: 1rem 0 !important; }
h3 { font-size: 0.9375rem !important; font-weight: 800 !important; color: #0f172a !important; letter-spacing: -.2px !important; }
[data-testid="stCaption"] { color: #94a3b8 !important; font-size: 11.5px !important; }

/* ── Scrollbar ───────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
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

def filter_reports_by_date(reports, target_date, today=None):
    today = today or datetime.now().date()
    return [
        report for report in reports
        if (parsed := parse_report_datetime(report, today)) is not None
        and parsed.date() == target_date
    ]

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

def get_report_distance_weight(distance_m):
    if distance_m > REPORT_INFLUENCE_RADIUS_M:
        return 0
    return math.exp(-0.5 * (distance_m / REPORT_DECAY_DISTANCE_M) ** 2)

def get_density_factor(weighted_count):
    return 1 - math.exp(-weighted_count / REPORT_DENSITY_SATURATION)

def calculate_bayesian_stats_for_point(lat, lng, reports, prior=0.1):
    nearby_count = 0
    weighted_count = 0
    weighted_risk = 0
    
    for report in reports:
        distance = haversine_distance(lat, lng, report["lat"], report["lng"])
        distance_weight = get_report_distance_weight(distance)
        if distance_weight <= 0:
            continue

        nearby_count += 1
        weighted_count += distance_weight
        weighted_risk += distance_weight * (report["intensity"] / 5)

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

def bayesian_update(grid, reports):
    """베이지안 정리 계산"""
    reports = normalize_reports(reports)
    updated = []
    
    for cell in grid:
        stats = calculate_bayesian_stats_for_point(cell["lat"], cell["lon"], reports, cell["prior"])
        
        updated.append({
            **cell,
            **stats,
        })
    
    return updated

def get_color(value):
    """위험도 색상"""
    if value < 0.16:
        return "#6cc3b0"
    elif value < 0.30:
        return "#d6bd3f"
    elif value < 0.46:
        return "#e9873f"
    else:
        return "#d85745"

def get_probability_grade(probability):
    if probability >= 0.46:
        return {
            "label": "고위험",
            "color": "#d85745",
            "soft": "#fff1f0",
            "text": "이 지역은 위험도가 높습니다. 가능하면 주의해서 이동하세요.",
        }
    if probability >= 0.30:
        return {
            "label": "주의",
            "color": "#e9873f",
            "soft": "#fff7ed",
            "text": "주변에 위험 신고가 있습니다. 이동 시 주변 상황을 확인하세요.",
        }
    if probability >= 0.16:
        return {
            "label": "관찰",
            "color": "#d6bd3f",
            "soft": "#fefce8",
            "text": "현재 위험도는 중간 수준입니다. 상황 변화를 지켜보세요.",
        }
    return {
        "label": "낮음",
        "color": "#6cc3b0",
        "soft": "#ecfdf5",
        "text": "현재 이 지역의 위험도는 낮습니다. 안전한 상태입니다.",
    }

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

def get_zone_radius_m(value, report_count, weighted_count=0):
    coverage_radius = GRID_SIZE_M * 0.72
    risk_expansion = GRID_SIZE_M * 0.18 * get_heat_weight(value)
    density_expansion = min(weighted_count * GRID_SIZE_M * 0.08, GRID_SIZE_M * 0.16)
    report_expansion = min(report_count, 3) * GRID_SIZE_M * 0.025
    return coverage_radius + risk_expansion + density_expansion + report_expansion

def get_zone_opacity(value, density_factor=0):
    return min(0.52, 0.12 + get_heat_weight(value) * 0.24 + density_factor * 0.14)

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
    df = df_reports.sort_values("id", ascending=False).copy()
    total_count = len(df)
    high_count = int((df["intensity"] >= 4).sum()) if total_count else 0
    avg_intensity = float(df["intensity"].mean()) if total_count else 0
    filter_label = selected_dong if selected_dong != "전체" else "전체 동"

    rows = []
    for _, report in df.iterrows():
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
                <span class="report-pill">총 {total_count}건</span>
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
        except:
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

# ========== 세션 상태 ==========
if "reports" not in st.session_state:
    st.session_state.reports = load_reports()
normalized_reports = normalize_reports(st.session_state.reports)
if normalized_reports != st.session_state.reports:
    st.session_state.reports = normalized_reports
    save_reports(st.session_state.reports)
else:
    st.session_state.reports = normalized_reports
next_report_id = max([r.get("id", 0) for r in st.session_state.reports], default=0) + 1
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
        <div class="pgis-header__chip">📊&nbsp;<b>{len(st.session_state.reports)}</b>건 누적 신고</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ========== 메트릭 ==========
today = datetime.now().date()
yesterday = today - timedelta(days=1)
today_reports = filter_reports_by_date(st.session_state.reports, today, today)
yesterday_reports = filter_reports_by_date(st.session_state.reports, yesterday, today)
overall_stats = summarize_reports(st.session_state.reports)
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

# ========== 메인 레이아웃 ==========
selected_dong = st.session_state.get("selected_dong", "전체")

_tc, _ = st.columns([0.12, 1])
with _tc:
    if st.button("◀ 접기" if st.session_state.sidebar_open else "☰ 신고 폼"):
        st.session_state.sidebar_open = not st.session_state.sidebar_open
        st.rerun()

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
        selected_dong = st.selectbox("📍 동 선택", ["전체"] + list(JUNGGU_DONGS.keys()))
        st.session_state.selected_dong = selected_dong

        st.markdown("---")

        # 신고 폼
        with st.form("report_form", border=True):
            st.markdown("**새 신고 작성**")

            report_type = st.selectbox("위험 유형", ["조명 부족", "시야 차단", "도로 파손", "불법 주정차", "기타"])
            intensity = st.slider("위험도", 1, 5, 3, help="1: 안전 → 5: 매우 위험")

            default_lat = st.session_state.clicked_lat if st.session_state.clicked_lat is not None else JUNGGU_CENTER[0]
            default_lng = st.session_state.clicked_lng if st.session_state.clicked_lng is not None else JUNGGU_CENTER[1]
            input_version = st.session_state.location_input_version
            lat = st.number_input("위도", value=float(default_lat), format="%.6f", key=f"lat_input_{input_version}")
            lng = st.number_input("경도", value=float(default_lng), format="%.6f", key=f"lng_input_{input_version}")
            selected_report_dong = get_dong_by_coords(lat, lng)

            desc = st.text_area("상세 설명", max_chars=100, placeholder="예: 횡단보도 직전 조명 전부 고장...")

            if st.session_state.clicked_lat is not None and st.session_state.clicked_lng is not None:
                st.success(f"✅ 지도에서 선택된 위치 · {selected_report_dong}")
                st.caption(f"위도 {lat:.6f} / 경도 {lng:.6f}")
            else:
                st.info("💡 오른쪽 지도에서 좌클릭 한 번으로 신고 위치를 선택하세요.")

            if st.form_submit_button("📌 신고 등록", use_container_width=True):
                dong = get_dong_by_coords(lat, lng)
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
                saved_report = persist_report(new_report)
                if saved_report:
                    st.session_state.reports.append(saved_report)
                    st.session_state.next_id = max(st.session_state.next_id, saved_report["id"] + 1)
                    save_reports(st.session_state.reports)
                    st.session_state.clicked_lat = None
                    st.session_state.clicked_lng = None
                    st.session_state.location_input_version += 1
                    st.session_state.map_click_msg = False
                    st.success(f"✅ 신고 저장 | {dong}")
                    st.rerun()

        st.markdown("---")

        st.markdown("""
        <div class="pgis-section-head" style="margin-bottom:8px;">
            <div class="pgis-section-title">
                <div class="pgis-section-title__icon" style="background:#f5f3ff;">📊</div>
                데이터 관리
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("⬇️ CSV 다운로드", use_container_width=True):
                if st.session_state.reports:
                    df = pd.DataFrame(normalize_reports(st.session_state.reports))
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
            if st.button("📤 CSV 업로드", use_container_width=True):
                st.session_state.show_upload = True

        if st.session_state.get("show_upload", False):
            uploaded = st.file_uploader("CSV 파일 선택", type=["csv"])
            if uploaded and st.button("업로드 실행"):
                try:
                    df = pd.read_csv(uploaded)
                    uploaded_at = datetime.now()
                    saved_count = 0
                    skipped_count = 0
                    last_uploaded_report = None
                    for _, row in df.iterrows():
                        new_report = build_report_from_csv_row(row, st.session_state.next_id, uploaded_at)
                        if not new_report:
                            skipped_count += 1
                            continue
                        saved_report = persist_report(new_report)
                        if saved_report:
                            st.session_state.reports.append(saved_report)
                            st.session_state.next_id = max(st.session_state.next_id, saved_report["id"] + 1)
                            saved_count += 1
                            last_uploaded_report = saved_report
                    save_reports(st.session_state.reports)
                    if last_uploaded_report:
                        st.session_state.clicked_lat = last_uploaded_report["lat"]
                        st.session_state.clicked_lng = last_uploaded_report["lng"]
                        st.session_state.location_input_version += 1
                        st.session_state.map_click_msg = True
                        st.session_state.map_focus = "register"
                    if skipped_count:
                        st.warning(f"✅ {saved_count}건 업로드 · 위도/경도 누락 {skipped_count}건 제외")
                    else:
                        st.success(f"✅ {saved_count}건 업로드")
                    st.session_state.show_upload = False
                    st.rerun()
                except Exception as e:
                    st.error(f"오류: {e}")

        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()

# ========== 우측: 지도 ==========
with col_right:
    st.markdown("""
    <div class="pgis-section-head">
        <div class="pgis-section-title">
            <div class="pgis-section-title__icon" style="background:#fef9c3;">🎯</div>
            베이지안 위험도 지도
        </div>
        <div class="pgis-hint-row">
            <span class="pgis-hint">🖱 <b>좌클릭</b>&nbsp;신고 등록</span>
            <span class="pgis-hint">🖱 <b>우클릭</b>&nbsp;확률 조회</span>
            <span class="pgis-hint">✦ <b>마커 호버</b>&nbsp;신고 상세</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 베이지안 계산
    reports_for_map = normalize_reports(st.session_state.reports)
    bayesian_grid = bayesian_update(st.session_state.grid, reports_for_map)
    query_lat = st.session_state.query_lat
    query_lng = st.session_state.query_lng
    has_query_location = query_lat is not None and query_lng is not None
    query_stats = (
        calculate_bayesian_stats_for_point(query_lat, query_lng, reports_for_map)
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
    </style>
    """))
    
    # 위험도 레이어
    visible_cells = [
        cell for cell in bayesian_grid
        if selected_dong == "전체" or cell["dong"] == selected_dong
    ]
    heat_points = [
        [
            cell["lat"],
            cell["lon"],
            get_heat_weight(cell["posterior"]) * (0.65 + cell["density_factor"] * 0.35),
        ]
        for cell in visible_cells
        if get_heat_weight(cell["posterior"]) > 0
    ]
    
    if heat_points:
        HeatMap(
            heat_points,
            radius=34,
            blur=28,
            min_opacity=0.12,
            gradient={
                0.15: "#6cc3b0",
                0.45: "#d6bd3f",
                0.70: "#e9873f",
                1.00: "#d85745",
            },
        ).add_to(m)
        m.get_root().header.add_child(folium.Element("""
        <style>
            .leaflet-heatmap-layer {
                pointer-events: none !important;
            }
        </style>
        """))
    
    for cell in visible_cells:
        heat_weight = get_heat_weight(cell["posterior"])
        if heat_weight <= 0 and cell["report_count"] == 0:
            continue
        
        color = get_color(cell["posterior"])
        folium.Circle(
            location=[cell["lat"], cell["lon"]],
            radius=get_zone_radius_m(cell["posterior"], cell["report_count"], cell["weighted_count"]),
            color=color,
            weight=0.8 if heat_weight > 0.25 else 0,
            opacity=0.55,
            fill=True,
            fillColor=color,
            fillOpacity=get_zone_opacity(cell["posterior"], cell["density_factor"]),
            interactive=False,
        ).add_to(m)
    
    # 신고 마커
    type_colors = {
        "조명 부족": "orange",
        "시야 차단": "red",
        "도로 파손": "purple",
        "불법 주정차": "blue",
        "기타": "gray",
    }
    
    for report in reports_for_map:
        if selected_dong != "전체" and report.get("dong") != selected_dong:
            continue
        
        tip_html = build_report_popup_html(report)
        folium.Marker(
            location=[report["lat"], report["lng"]],
            tooltip=folium.Tooltip(tip_html, sticky=True),
            icon=folium.Icon(color=type_colors.get(report["type"], "gray"), icon_color="white", icon="info-sign"),
        ).add_to(m)
    
    if st.session_state.map_focus == "query" and has_query_location and query_stats:
        query_dong = get_dong_by_coords(query_lat, query_lng)
        probability = query_stats["posterior"]
        probability_color = get_color(probability)
        query_popup = build_query_popup_html(query_lat, query_lng, query_dong, query_stats, reports_for_map)
        folium.CircleMarker(
            location=[query_lat, query_lng],
            radius=12,
            color=probability_color,
            weight=3,
            opacity=0.95,
            fill=True,
            fillColor=probability_color,
            fillOpacity=0.24,
            tooltip=f"예상 사고확률 {probability:.1%}",
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
        selected_popup = f"""
        <div style="font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; min-width: 170px;">
            <div style="font-weight: 700; color: #0f172a; margin-bottom: 4px;">선택한 신고 위치</div>
            <div style="color: #475569; font-size: 12px;">{selected_location_dong}</div>
            <div style="color: #475569; font-size: 12px;">위도 {selected_map_lat:.6f}</div>
            <div style="color: #475569; font-size: 12px;">경도 {selected_map_lng:.6f}</div>
        </div>
        """
        folium.CircleMarker(
            location=[selected_map_lat, selected_map_lng],
            radius=16,
            color="#2563eb",
            weight=3,
            opacity=0.95,
            fill=True,
            fillColor="#60a5fa",
            fillOpacity=0.22,
            bubbling_mouse_events=True,
            popup=folium.Popup(selected_popup, max_width=240),
            tooltip="선택한 신고 위치",
        ).add_to(m)
        folium.Marker(
            location=[selected_map_lat, selected_map_lng],
            icon=folium.DivIcon(
                html="""
                <div style="
                    width: 18px;
                    height: 18px;
                    margin-left: -9px;
                    margin-top: -9px;
                    border-radius: 999px;
                    background: #2563eb;
                    border: 3px solid #ffffff;
                    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.35);
                "></div>
                """
            ),
        ).add_to(m)
    
    legend_html = """
    <div style="
        position: fixed;
        left: 24px;
        bottom: 28px;
        z-index: 9999;
        width: 152px;
        padding: 10px 12px;
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid rgba(148, 163, 184, 0.35);
        border-radius: 8px;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.14);
        color: #0f172a;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    ">
        <div style="font-size: 12px; font-weight: 700; margin-bottom: 7px;">위험도</div>
        <div style="
            height: 8px;
            border-radius: 8px;
            background: linear-gradient(90deg, #6cc3b0 0%, #d6bd3f 42%, #e9873f 70%, #d85745 100%);
        "></div>
        <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 10px; color: #64748b;">
            <span>낮음</span>
            <span>높음</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # 지도 렌더링 및 클릭 처리
    map_data = st_folium(
        m,
        width=1040,
        height=760,
        returned_objects=[
            "last_clicked",
            "last_object_clicked",
            "last_object_clicked_tooltip",
            "last_object_clicked_popup",
        ],
    )
    
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

if st.session_state.reports:
    reports_df = pd.DataFrame(normalize_reports(st.session_state.reports))
    if reports_df.empty or "dong" not in reports_df.columns:
        st.info("분석 가능한 신고 데이터가 없습니다.")
    else:
        _chart_layout = dict(
            height=300,
            showlegend=False,
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font=dict(family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", size=12, color="#475569"),
            margin=dict(l=8, r=8, t=44, b=8),
            xaxis=dict(showgrid=False, linecolor="#e2e8f0", tickcolor="#e2e8f0"),
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9", linecolor="#e2e8f0", zeroline=False),
        )

        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            dong_stats = (
                reports_df.groupby("dong")
                .agg(count=("intensity", "count"), avg_intensity=("intensity", "mean"))
                .sort_values("count", ascending=False)
                .reset_index()
            )

            def _bar_color(avg):
                if avg >= 4.0: return "#ef4444"
                if avg >= 3.0: return "#f59e0b"
                return "#22c55e"

            fig1 = go.Figure(go.Bar(
                x=dong_stats["dong"],
                y=dong_stats["count"],
                marker_color=[_bar_color(a) for a in dong_stats["avg_intensity"]],
                marker_line_width=0,
                text=[f"평균 {a:.1f}" for a in dong_stats["avg_intensity"]],
                textposition="outside",
                textfont=dict(size=10, color="#64748b"),
                hovertemplate="<b>%{x}</b><br>신고 %{y}건<br>평균 위험도 %{customdata:.1f}<extra></extra>",
                customdata=dong_stats["avg_intensity"],
            ))
            fig1.update_layout(
                **_chart_layout,
                title=dict(
                    text="<b>행정동별 신고 현황</b>  <span style='font-size:10px;color:#94a3b8;font-weight:400'>막대 색상 = 평균 위험도</span>",
                    font_size=13, x=0,
                ),
                yaxis_title="신고 건수",
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col_chart2:
            all_levels = pd.Series(0, index=range(1, 6))
            intensity_counts = reports_df["intensity"].value_counts()
            intensity_dist = all_levels.add(intensity_counts, fill_value=0).astype(int)
            total_i = intensity_dist.sum() or 1
            level_colors = ["#22c55e", "#84cc16", "#f59e0b", "#f97316", "#ef4444"]
            level_labels = ["1단계\n(낮음)", "2단계", "3단계\n(보통)", "4단계", "5단계\n(높음)"]

            fig2 = go.Figure(go.Bar(
                x=level_labels,
                y=intensity_dist.values,
                marker_color=level_colors,
                marker_line_width=0,
                text=[f"{v}건 ({v/total_i:.0%})" if v > 0 else "" for v in intensity_dist.values],
                textposition="outside",
                textfont=dict(size=10),
                hovertemplate="<b>위험도 %{x}</b><br>신고 %{y}건<extra></extra>",
            ))
            fig2.update_layout(
                **_chart_layout,
                title=dict(text="<b>위험도 단계별 분포</b>", font_size=13, x=0),
                yaxis_title="신고 건수",
            )
            st.plotly_chart(fig2, use_container_width=True)

        col_chart3, col_chart4 = st.columns(2)

        with col_chart3:
            type_counts = reports_df["type"].value_counts().reset_index()
            type_counts.columns = ["type", "count"]
            type_color_map = {
                "조명 부족": "#f97316",
                "시야 차단": "#ef4444",
                "도로 파손": "#8b5cf6",
                "불법 주정차": "#3b82f6",
                "기타": "#94a3b8",
            }
            total_t = type_counts["count"].sum() or 1
            fig3 = go.Figure(go.Bar(
                x=type_counts["count"],
                y=type_counts["type"],
                orientation="h",
                marker_color=[type_color_map.get(t, "#94a3b8") for t in type_counts["type"]],
                marker_line_width=0,
                text=[f"{c}건 ({c/total_t:.0%})" for c in type_counts["count"]],
                textposition="outside",
                textfont=dict(size=10),
                hovertemplate="<b>%{y}</b><br>신고 %{x}건<extra></extra>",
            ))
            fig3.update_layout(
                **_chart_layout,
                title=dict(text="<b>신고 유형별 분포</b>", font_size=13, x=0),
            )
            fig3.update_xaxes(showgrid=True, gridcolor="#f1f5f9", linecolor="#e2e8f0", title_text="신고 건수")
            fig3.update_yaxes(showgrid=False, linecolor="#e2e8f0", autorange="reversed")
            st.plotly_chart(fig3, use_container_width=True)

        with col_chart4:
            high_risk = int((reports_df["intensity"] >= 4).sum())
            mid_risk = int((reports_df["intensity"] == 3).sum())
            low_risk = int((reports_df["intensity"] <= 2).sum())
            dong_risk = (
                reports_df.groupby("dong")
                .agg(count=("intensity", "count"), avg=("intensity", "mean"))
                .sort_values(["avg", "count"], ascending=False)
                .reset_index()
            )
            rows_html = ""
            for _, row in dong_risk.iterrows():
                risk_color = "#ef4444" if row["avg"] >= 4 else "#f59e0b" if row["avg"] >= 3 else "#22c55e"
                rows_html += (
                    f'<div style="display:flex;align-items:center;justify-content:space-between;'
                    f'padding:8px 14px;border-bottom:1px solid #f1f5f9;">'
                    f'<span style="font-size:13px;font-weight:600;color:#0f172a;">{html.escape(str(row["dong"]))}</span>'
                    f'<div style="display:flex;align-items:center;gap:8px;">'
                    f'<span style="font-size:11px;color:#64748b;">{int(row["count"])}건</span>'
                    f'<span style="background:{risk_color};color:#fff;font-size:10px;font-weight:700;'
                    f'padding:2px 8px;border-radius:999px;">평균 {row["avg"]:.1f}</span>'
                    f'</div></div>'
                )
            st.markdown(
                f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">'
                f'<div style="padding:12px 14px 10px;border-bottom:1px solid #e2e8f0;background:#f8fafc;">'
                f'<div style="font-size:13px;font-weight:800;color:#0f172a;margin-bottom:8px;">주의 필요 지역</div>'
                f'<div style="display:flex;gap:20px;">'
                f'<div style="text-align:center;">'
                f'<div style="font-size:22px;font-weight:900;color:#ef4444;">{high_risk}</div>'
                f'<div style="font-size:10px;color:#94a3b8;font-weight:700;">고위험</div>'
                f'</div>'
                f'<div style="text-align:center;">'
                f'<div style="font-size:22px;font-weight:900;color:#f59e0b;">{mid_risk}</div>'
                f'<div style="font-size:10px;color:#94a3b8;font-weight:700;">주의</div>'
                f'</div>'
                f'<div style="text-align:center;">'
                f'<div style="font-size:22px;font-weight:900;color:#22c55e;">{low_risk}</div>'
                f'<div style="font-size:10px;color:#94a3b8;font-weight:700;">낮음</div>'
                f'</div>'
                f'</div>'
                f'</div>'
                f'<div style="overflow-y:auto;max-height:220px;">{rows_html}</div>'
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
if st.session_state.reports:
    df_reports = pd.DataFrame(normalize_reports(st.session_state.reports))
    if df_reports.empty or "dong" not in df_reports.columns:
        st.info("표시할 수 있는 신고 데이터가 없습니다.")
    else:
        if selected_dong != "전체":
            df_reports = df_reports[df_reports["dong"] == selected_dong]

        if df_reports.empty:
            st.info("선택한 동에 표시할 신고 데이터가 없습니다.")
        else:
            components.html(
                render_report_status_table(df_reports, selected_dong),
                height=590,
                scrolling=False,
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
    st.caption(f"💾 자동 저장: {storage_backend} | 최종 업데이트: 2026-06-18")
