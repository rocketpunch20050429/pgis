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
import plotly.express as px

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
    .main { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    
    .header-main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .header-main h1 { margin: 0; font-size: 2.5rem; font-weight: 700; }
    .header-main p { margin: 0.5rem 0 0 0; font-size: 1rem; opacity: 0.9; }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 4px solid #667eea;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }
    
    .click-alert {
        background: linear-gradient(135deg, #fbbf24 0%, #f97316 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-weight: 600;
        text-align: center;
        font-size: 1.1rem;
    }
    
    .section-title {
        color: #667eea;
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }
    
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s;
        width: 100%;
    }
    
    .stButton > button:hover {
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4);
        transform: translateY(-2px);
    }
    
    .success-msg {
        background: #d1fae5;
        border-left: 4px solid #10b981;
        color: #065f46;
        padding: 1rem;
        border-radius: 6px;
        margin-top: 1rem;
    }

    .report-board {
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid rgba(148, 163, 184, 0.28);
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 18px 42px rgba(15, 23, 42, 0.12);
    }

    .report-board__header {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: flex-end;
        padding: 1rem 1.15rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.24);
        background: linear-gradient(180deg, rgba(248, 250, 252, 0.95), rgba(255, 255, 255, 0.95));
    }

    .report-board__title {
        color: #0f172a;
        font-size: 1rem;
        font-weight: 750;
        line-height: 1.2;
        margin: 0;
    }

    .report-board__sub {
        color: #64748b;
        font-size: 0.78rem;
        margin-top: 0.25rem;
    }

    .report-board__meta {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        justify-content: flex-end;
    }

    .report-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        border: 1px solid rgba(148, 163, 184, 0.34);
        border-radius: 999px;
        color: #334155;
        background: #ffffff;
        font-size: 0.74rem;
        font-weight: 650;
        padding: 0.34rem 0.58rem;
        white-space: nowrap;
    }

    .report-table-wrap {
        max-height: 460px;
        overflow: auto;
    }

    .report-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        table-layout: fixed;
        color: #0f172a;
    }

    .report-table thead th {
        position: sticky;
        top: 0;
        z-index: 2;
        background: #f8fafc;
        color: #475569;
        border-bottom: 1px solid rgba(148, 163, 184, 0.32);
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0;
        text-align: left;
        padding: 0.72rem 0.85rem;
    }

    .report-table tbody td {
        border-bottom: 1px solid rgba(226, 232, 240, 0.86);
        padding: 0.78rem 0.85rem;
        vertical-align: middle;
        font-size: 0.84rem;
        background: rgba(255, 255, 255, 0.92);
    }

    .report-table tbody tr:nth-child(even) td {
        background: rgba(248, 250, 252, 0.78);
    }

    .report-table tbody tr:hover td {
        background: #eef6ff;
    }

    .report-table .col-id { width: 70px; }
    .report-table .col-status { width: 112px; }
    .report-table .col-dong { width: 120px; }
    .report-table .col-type { width: 140px; }
    .report-table .col-risk { width: 170px; }
    .report-table .col-time { width: 110px; }
    .report-table .col-desc { width: auto; }

    .status-badge,
    .risk-badge {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 750;
        padding: 0.28rem 0.52rem;
        white-space: nowrap;
    }

    .status-badge {
        color: #0f766e;
        background: #ccfbf1;
        border: 1px solid rgba(20, 184, 166, 0.24);
    }

    .risk-badge.low {
        color: #047857;
        background: #d1fae5;
    }

    .risk-badge.mid {
        color: #92400e;
        background: #fef3c7;
    }

    .risk-badge.high {
        color: #b91c1c;
        background: #fee2e2;
    }

    .risk-cell {
        display: grid;
        gap: 0.38rem;
    }

    .risk-meter {
        height: 7px;
        border-radius: 999px;
        background: #e2e8f0;
        overflow: hidden;
    }

    .risk-meter span {
        display: block;
        height: 100%;
        border-radius: inherit;
        background: linear-gradient(90deg, #14b8a6, #eab308, #ef4444);
    }

    .desc-text {
        color: #475569;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
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
            "text": "주변 신고 강도와 밀도가 함께 높습니다. 현장 점검 우선순위를 높이는 편이 타당합니다.",
        }
    if probability >= 0.30:
        return {
            "label": "주의",
            "color": "#e9873f",
            "soft": "#fff7ed",
            "text": "즉각적인 위험 신호가 일부 관측됩니다. 유사 신고가 반복되는지 추적이 필요합니다.",
        }
    if probability >= 0.16:
        return {
            "label": "관찰",
            "color": "#d6bd3f",
            "soft": "#fefce8",
            "text": "현재는 중간 수준입니다. 주변 신고가 누적되면 위험 추정치가 빠르게 변할 수 있습니다.",
        }
    return {
        "label": "낮음",
        "color": "#6cc3b0",
        "soft": "#ecfdf5",
        "text": "현재 반경 내 신고 영향은 제한적입니다. 다만 현장 조건 변화는 계속 확인해야 합니다.",
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
        confidence_label = "높음"
    elif confidence_score >= 35:
        confidence_label = "보통"
    elif stats["report_count"] > 0:
        confidence_label = "낮음"
    else:
        confidence_label = "자료 부족"

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
    confidence_percent = max(6, min(100, context["confidence_score"]))
    local_score = stats["local_risk"] * 5 if stats["weighted_count"] > 0 else 0
    nearest_text = format_distance(context["nearest_distance"])
    dominant_type = html.escape(context["dominant_type"])

    if context["nearby_reports"]:
        report_rows = []
        for item in context["nearby_reports"][:3]:
            report = item["report"]
            report_type = html.escape(str(report.get("type", "신고")))
            report_time = html.escape(str(report.get("time", "-")))
            report_rows.append(f"""
            <div style="display:flex; gap:9px; align-items:flex-start; padding:8px 0; border-top:1px solid #e5e7eb;">
                <div style="width:7px; height:7px; border-radius:99px; background:{grade['color']}; margin-top:6px; flex:0 0 auto;"></div>
                <div style="flex:1; min-width:0;">
                    <div style="display:flex; justify-content:space-between; gap:8px; font-size:12px; color:#0f172a; font-weight:750;">
                        <span>{report_type}</span>
                        <span style="color:#64748b; font-weight:650;">{format_distance(item['distance'])}</span>
                    </div>
                    <div style="font-size:11px; color:#64748b; margin-top:2px;">위험도 {report['intensity']}/5 · {report_time}</div>
                </div>
            </div>
            """)
        nearby_html = "".join(report_rows)
    else:
        nearby_html = """
        <div style="padding:10px 0 2px; color:#64748b; font-size:12px; border-top:1px solid #e5e7eb;">
            반경 850m 안에 반영된 신고가 없어 기본 위험률을 중심으로 추정했습니다.
        </div>
        """

    return f"""
    <div class="query-risk-popup" style="width:372px; overflow:hidden; font-family:system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#0f172a; border-radius:14px; background:#ffffff;">
        <div style="padding:16px 17px 15px; color:#ffffff; background:linear-gradient(135deg, #172033 0%, #31526b 58%, {grade['color']} 100%);">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:12px;">
                <div style="font-size:12px; opacity:0.86; font-weight:650;">베이지안 예상 사고확률</div>
                <div style="padding:5px 9px; border-radius:999px; background:rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.24); font-size:11px; font-weight:800;">{grade['label']}</div>
            </div>
            <div style="display:flex; align-items:flex-end; justify-content:space-between; gap:12px; margin-top:10px;">
                <div>
                    <div style="font-size:34px; line-height:1; font-weight:850;">{probability:.2%}</div>
                    <div style="font-size:12px; opacity:0.86; margin-top:7px;">{html.escape(dong)} · 위도 {lat:.5f}, 경도 {lng:.5f}</div>
                </div>
                <div style="font-size:11px; text-align:right; opacity:0.88;">분석 반경<br/><b>{REPORT_INFLUENCE_RADIUS_M}m</b></div>
            </div>
            <div style="height:7px; border-radius:999px; background:rgba(255,255,255,0.23); overflow:hidden; margin-top:14px;">
                <div style="width:{probability_percent:.1f}%; height:100%; border-radius:999px; background:#ffffff;"></div>
            </div>
        </div>

        <div style="padding:14px 16px 15px;">
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                <div style="padding:10px; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc;">
                    <div style="font-size:11px; color:#64748b; font-weight:700;">영향 신고</div>
                    <div style="font-size:18px; font-weight:850; margin-top:3px;">{stats['report_count']}건</div>
                </div>
                <div style="padding:10px; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc;">
                    <div style="font-size:11px; color:#64748b; font-weight:700;">가장 가까운 신고</div>
                    <div style="font-size:18px; font-weight:850; margin-top:3px;">{nearest_text}</div>
                </div>
                <div style="padding:10px; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc;">
                    <div style="font-size:11px; color:#64748b; font-weight:700;">주변 평균 위험도</div>
                    <div style="font-size:18px; font-weight:850; margin-top:3px;">{context['avg_intensity']:.1f}/5</div>
                </div>
                <div style="padding:10px; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc;">
                    <div style="font-size:11px; color:#64748b; font-weight:700;">주요 유형</div>
                    <div style="font-size:15px; font-weight:850; margin-top:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{dominant_type}</div>
                </div>
            </div>

            <div style="margin-top:11px; padding:11px 12px; border-radius:10px; background:{grade['soft']}; border:1px solid rgba(15,23,42,0.07); color:#334155; font-size:12px; line-height:1.45;">
                {grade['text']}
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:12px;">
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:11px; color:#64748b; font-weight:700;">
                        <span>신뢰도</span><span>{context['confidence_label']}</span>
                    </div>
                    <div style="height:6px; border-radius:999px; background:#e5e7eb; overflow:hidden; margin-top:6px;">
                        <div style="width:{confidence_percent:.1f}%; height:100%; background:#2563eb; border-radius:999px;"></div>
                    </div>
                </div>
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:11px; color:#64748b; font-weight:700;">
                        <span>밀도 영향</span><span>{density_percent:.0f}%</span>
                    </div>
                    <div style="height:6px; border-radius:999px; background:#e5e7eb; overflow:hidden; margin-top:6px;">
                        <div style="width:{max(4, density_percent):.1f}%; height:100%; background:{grade['color']}; border-radius:999px;"></div>
                    </div>
                </div>
            </div>

            <div style="margin-top:13px; display:grid; grid-template-columns:repeat(3, 1fr); gap:7px; text-align:center;">
                <div style="border-radius:9px; background:#f8fafc; padding:8px 4px;">
                    <div style="font-size:10px; color:#64748b; font-weight:700;">사전확률</div>
                    <div style="font-size:13px; font-weight:850; margin-top:2px;">10.0%</div>
                </div>
                <div style="border-radius:9px; background:#f8fafc; padding:8px 4px;">
                    <div style="font-size:10px; color:#64748b; font-weight:700;">국소 위험</div>
                    <div style="font-size:13px; font-weight:850; margin-top:2px;">{local_score:.1f}/5</div>
                </div>
                <div style="border-radius:9px; background:#f8fafc; padding:8px 4px;">
                    <div style="font-size:10px; color:#64748b; font-weight:700;">가능도</div>
                    <div style="font-size:13px; font-weight:850; margin-top:2px;">{stats['likelihood']:.1%}</div>
                </div>
            </div>

            <div style="margin-top:13px;">
                <div style="font-size:12px; font-weight:850; margin-bottom:2px;">주변 신고 근거</div>
                {nearby_html}
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

def get_risk_display(intensity):
    if intensity >= 4:
        return "높음", "high"
    if intensity >= 3:
        return "주의", "mid"
    return "낮음", "low"

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

def load_reports():
    if os.path.exists(REPORTS_FILE):
        try:
            with open(REPORTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_reports(reports):
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

# ========== 메인 헤더 ==========
st.markdown(f"""
<div class="header-main">
    <h1>🗺️ 서울 중구 안전지도</h1>
    <p>베이지안 정리 기반 | 좌클릭 신고·우클릭 조회 | 전일 대비 지표 | {len(st.session_state.grid):,}개 격자 분석</p>
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

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric(
        "📊 총 신고",
        overall_stats["count"],
        format_metric_delta(today_stats["count"], yesterday_stats["count"], "건"),
        delta_color="inverse",
        help="전체 누적 신고 수입니다. 변화량은 오늘 신고 건수에서 어제 신고 건수를 뺀 값입니다.",
    )
with col2:
    st.metric(
        "📈 평균 위험도",
        f"{overall_stats['avg_intensity']:.1f}",
        format_metric_delta(today_stats["avg_intensity"], yesterday_stats["avg_intensity"], "점", 1),
        delta_color="inverse",
        help="전체 신고의 평균 위험도입니다. 변화량은 오늘 평균 위험도와 어제 평균 위험도의 차이입니다.",
    )
with col3:
    st.metric(
        "🔴 고위험",
        overall_stats["high_risk_count"],
        format_metric_delta(today_stats["high_risk_count"], yesterday_stats["high_risk_count"], "건"),
        delta_color="inverse",
        help="위험도 4점 이상 신고의 누적 수입니다. 변화량은 오늘 고위험 신고 수와 어제 고위험 신고 수의 차이입니다.",
    )
with col4:
    st.metric("📍 격자 셀", len(st.session_state.grid), "±0개 전일 대비", delta_color="off")
with col5:
    st.metric("🏘️ 동 구분", len(JUNGGU_DONGS), "±0개 전일 대비", delta_color="off")

st.divider()

# ========== 클릭 알림 ==========
if st.session_state.map_click_msg:
    st.markdown(f"""
    <div class="click-alert">
        ✅ 위치 선택 완료! 위도: {st.session_state.clicked_lat:.4f} / 경도: {st.session_state.clicked_lng:.4f}
    </div>
    """, unsafe_allow_html=True)

# ========== 메인 레이아웃 ==========
col_left, col_right = st.columns([0.9, 3.4], gap="medium")

# ========== 좌측: 신고 폼 ==========
with col_left:
    st.markdown("### 📝 신고 작성")
    
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
        
        # 좌표가 선택되었으면 하이라이트
        if st.session_state.clicked_lat is not None and st.session_state.clicked_lng is not None:
            st.success(f"✅ 지도에서 선택된 위치 · {selected_report_dong}")
            st.caption(f"위도 {lat:.6f} / 경도 {lng:.6f}")
        else:
            st.info("💡 오른쪽 지도에서 좌클릭 한 번으로 신고 위치를 선택하세요.")
        
        if st.form_submit_button("📌 신고 등록", use_container_width=True):
            dong = get_dong_by_coords(lat, lng)
            created_at = datetime.now()
            st.session_state.reports.append({
                "id": st.session_state.next_id,
                "lng": lng,
                "lat": lat,
                "type": report_type,
                "intensity": intensity,
                "time": created_at.strftime("%m-%d %H:%M"),
                "created_at": created_at.isoformat(timespec="minutes"),
                "desc": desc,
                "dong": dong,
            })
            st.session_state.next_id += 1
            save_reports(st.session_state.reports)
            
            # 클릭 상태 초기화
            st.session_state.clicked_lat = None
            st.session_state.clicked_lng = None
            st.session_state.location_input_version += 1
            st.session_state.map_click_msg = False
            
            st.success(f"✅ 신고 저장 | {dong}")
            st.rerun()
    
    st.markdown("---")
    
    # 데이터 관리
    st.markdown("### 📊 데이터 관리")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("⬇️ CSV 내보내기", use_container_width=True):
            if st.session_state.reports:
                df = pd.DataFrame(st.session_state.reports)
                csv = df.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    "다운로드",
                    csv,
                    f"reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
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
                for _, row in df.iterrows():
                    lat = float(row.get("lat", 37.5630))
                    lng = float(row.get("lng", row.get("lon", 126.9945)))
                    row_created_at = row.get("created_at", None)
                    if pd.isna(row_created_at):
                        row_created_at = row.get("timestamp", uploaded_at.isoformat(timespec="minutes"))
                    if pd.isna(row_created_at):
                        row_created_at = uploaded_at.isoformat(timespec="minutes")
                    st.session_state.reports.append({
                        "id": st.session_state.next_id,
                        "lng": lng,
                        "lat": lat,
                        "type": str(row.get("type", "신고")),
                        "intensity": int(row.get("intensity", 3)),
                        "time": str(row.get("time", uploaded_at.strftime("%m-%d %H:%M"))),
                        "created_at": str(row_created_at),
                        "desc": str(row.get("desc", "")),
                        "dong": get_dong_by_coords(lat, lng),
                    })
                    st.session_state.next_id += 1
                
                save_reports(st.session_state.reports)
                st.success(f"✅ {len(df)} 건 업로드")
                st.session_state.show_upload = False
                st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")
    
    if st.button("🔄 새로고침", use_container_width=True):
        st.rerun()

# ========== 우측: 지도 ==========
with col_right:
    st.markdown("### 🎯 베이지안 위험도 지도")
    st.markdown("💡 **좌클릭: 신고 위치 등록 · 우클릭: 예상 사고확률 조회**", help="좌클릭한 좌표는 왼쪽 신고 폼에 입력되고, 우클릭한 좌표는 베이지안 예상 사고확률을 조회합니다.")
    
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
    if query_stats:
        query_dong = get_dong_by_coords(query_lat, query_lng)
        st.info(
            f"우클릭 조회 · {query_dong} · 예상 사고확률 {query_stats['posterior']:.2%} "
            f"· 영향 신고 {query_stats['report_count']}건"
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
        control_scale=True,
        prefer_canvas=True,
    )
    RightClickQueryHandler().add_to(m)
    m.get_root().header.add_child(folium.Element("""
    <style>
        .leaflet-popup:has(.query-risk-popup) .leaflet-popup-content-wrapper {
            padding: 0 !important;
            border-radius: 16px !important;
            overflow: hidden;
            box-shadow: 0 22px 52px rgba(15, 23, 42, 0.22) !important;
        }
        .leaflet-popup:has(.query-risk-popup) .leaflet-popup-content {
            margin: 0 !important;
            width: 372px !important;
        }
        .leaflet-popup:has(.query-risk-popup) .leaflet-popup-tip {
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.16) !important;
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
        
        popup = f"<b>{report['type']}</b><br/>위험도: {report['intensity']}/5<br/>시간: {report['time']}<br/>{report.get('desc', '')}"
        folium.Marker(
            location=[report["lat"], report["lng"]],
            popup=folium.Popup(popup, max_width=250),
            icon=folium.Icon(color=type_colors.get(report["type"], "gray"), icon_color="white", icon="info-sign"),
            tooltip=report["type"],
        ).add_to(m)
    
    # 동 경계
    for dong_name, dong_data in JUNGGU_DONGS.items():
        if selected_dong != "전체" and dong_name != selected_dong:
            continue
        b = dong_data["bounds"]
        folium.Rectangle(
            bounds=[[b["south"], b["west"]], [b["north"], b["east"]]],
            color="#475569",
            fill=False,
            weight=1.2,
            opacity=0.55,
            dash_array="4, 6",
            interactive=False,
            label=dong_name,
        ).add_to(m)
    
    if has_query_location and query_stats:
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
            popup=folium.Popup(query_popup, max_width=420, show=True),
            tooltip=f"예상 사고확률 {probability:.1%}",
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
st.markdown("### 📊 상세 분석")

if st.session_state.reports:
    reports_df = pd.DataFrame(normalize_reports(st.session_state.reports))
    if reports_df.empty or "dong" not in reports_df.columns:
        st.info("분석 가능한 신고 데이터가 없습니다.")
    else:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # 동별 신고 현황
            dong_reports = reports_df.groupby("dong").size().sort_values(ascending=False)
            fig1 = px.bar(
                x=dong_reports.index,
                y=dong_reports.values,
                labels={"x": "동", "y": "신고 건수"},
                color=dong_reports.values,
                color_continuous_scale="RdYlGn_r",
            )
            fig1.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col_chart2:
            # 위험도 분포
            intensity_dist = reports_df["intensity"].value_counts().sort_index()
            fig2 = px.bar(
                x=intensity_dist.index,
                y=intensity_dist.values,
                labels={"x": "위험도", "y": "신고 건수"},
                color=intensity_dist.index,
                color_continuous_scale="Reds",
            )
            fig2.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

# 신고 테이블
st.markdown("### 📋 업로드 현황")
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
    st.caption("💾 자동 저장: reports.json | 최종 업데이트: 2026-06-16")
