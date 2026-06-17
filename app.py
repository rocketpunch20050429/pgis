"""
Bayesian PGIS 서울 중구 안전지도 - 지도 클릭 직접 입력
"""

import json
import os
from datetime import datetime
import html
import math
import streamlit as st
import streamlit.components.v1 as components
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

def bayesian_update(grid, reports):
    """베이지안 정리 계산"""
    reports = normalize_reports(reports)
    updated = []
    
    for cell in grid:
        prior = cell["prior"]
        nearby = [r for r in reports 
                  if haversine_distance(cell["lat"], cell["lon"], r["lat"], r["lng"]) < 500]
        
        if nearby:
            likelihood = min(1.0, sum([r["intensity"] for r in nearby]) / (5 * len(nearby)))
        else:
            likelihood = 0.05
        
        evidence = prior * likelihood + (1 - prior) * 0.1
        posterior = (prior * likelihood) / evidence if evidence > 0 else prior
        
        updated.append({
            **cell,
            "likelihood": likelihood,
            "posterior": posterior,
            "report_count": len(nearby),
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

def get_heat_weight(value):
    return max(0.0, min(1.0, (value - 0.08) / 0.42))

def get_zone_radius(value, report_count):
    return 8 + get_heat_weight(value) * 18 + min(report_count, 5)

def get_zone_opacity(value):
    return 0.14 + get_heat_weight(value) * 0.28

def get_map_click_coords(map_data):
    if not map_data:
        return None

    for key in ("last_clicked", "last_object_clicked"):
        clicked = map_data.get(key)
        if isinstance(clicked, dict) and clicked.get("lat") is not None and clicked.get("lng") is not None:
            return float(clicked["lat"]), float(clicked["lng"])

    return None

def get_risk_display(intensity):
    if intensity >= 4:
        return "높음", "high"
    if intensity >= 3:
        return "주의", "mid"
    return "낮음", "low"

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
if "location_input_version" not in st.session_state:
    st.session_state.location_input_version = 0
if "map_click_msg" not in st.session_state:
    st.session_state.map_click_msg = False

# ========== 메인 헤더 ==========
st.markdown(f"""
<div class="header-main">
    <h1>🗺️ 서울 중구 안전지도</h1>
    <p>베이지안 정리 기반 | 지도 클릭으로 신고하기 | {len(st.session_state.grid):,}개 격자 분석</p>
</div>
""", unsafe_allow_html=True)

# ========== 메트릭 ==========
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("📊 총 신고", len(st.session_state.reports), "건")
with col2:
    avg_intensity = np.mean([r["intensity"] for r in st.session_state.reports]) if st.session_state.reports else 0
    st.metric("📈 평균 위험도", f"{avg_intensity:.1f}", "/5")
with col3:
    high_risk_count = len([r for r in st.session_state.reports if r["intensity"] >= 4])
    st.metric("🔴 고위험", high_risk_count, "건")
with col4:
    st.metric("📍 격자 셀", len(st.session_state.grid), "개")
with col5:
    st.metric("🏘️ 동 구분", len(JUNGGU_DONGS), "개")

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
            st.info("💡 오른쪽 지도에서 클릭하여 위치 선택!")
        
        if st.form_submit_button("📌 신고 등록", use_container_width=True):
            dong = get_dong_by_coords(lat, lng)
            st.session_state.reports.append({
                "id": st.session_state.next_id,
                "lng": lng,
                "lat": lat,
                "type": report_type,
                "intensity": intensity,
                "time": datetime.now().strftime("%m-%d %H:%M"),
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
                for _, row in df.iterrows():
                    lat = float(row.get("lat", 37.5630))
                    lng = float(row.get("lng", row.get("lon", 126.9945)))
                    st.session_state.reports.append({
                        "id": st.session_state.next_id,
                        "lng": lng,
                        "lat": lat,
                        "type": str(row.get("type", "신고")),
                        "intensity": int(row.get("intensity", 3)),
                        "time": str(row.get("time", datetime.now().strftime("%m-%d %H:%M"))),
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
    st.markdown("💡 **지도를 클릭하여 신고 위치를 선택하세요!**", help="클릭한 좌표가 왼쪽 폼에 자동으로 입력됩니다")
    
    # 베이지안 계산
    reports_for_map = normalize_reports(st.session_state.reports)
    bayesian_grid = bayesian_update(st.session_state.grid, reports_for_map)
    
    selected_map_lat = st.session_state.clicked_lat
    selected_map_lng = st.session_state.clicked_lng
    has_selected_location = selected_map_lat is not None and selected_map_lng is not None
    map_center = [selected_map_lat, selected_map_lng] if has_selected_location else JUNGGU_CENTER
    
    # 지도 생성
    m = folium.Map(
        location=map_center,
        zoom_start=15 if has_selected_location else 13,
        tiles="CartoDB positron",
        control_scale=True,
        prefer_canvas=True,
    )
    
    # 위험도 레이어
    visible_cells = [
        cell for cell in bayesian_grid
        if selected_dong == "전체" or cell["dong"] == selected_dong
    ]
    heat_points = [
        [cell["lat"], cell["lon"], get_heat_weight(cell["posterior"])]
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
        folium.CircleMarker(
            location=[cell["lat"], cell["lon"]],
            radius=get_zone_radius(cell["posterior"], cell["report_count"]),
            color=color,
            weight=0.8 if heat_weight > 0.25 else 0,
            opacity=0.55,
            fill=True,
            fillColor=color,
            fillOpacity=get_zone_opacity(cell["posterior"]),
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
        returned_objects=["last_clicked", "last_object_clicked"],
    )
    
    # 클릭 이벤트 처리
    clicked_coords = get_map_click_coords(map_data)
    if clicked_coords:
        clicked_lat, clicked_lng = clicked_coords
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
    st.info("📌 아직 신고가 없습니다. 지도를 클릭하여 신고를 등록해주세요.")

# ========== 푸터 ==========
st.divider()
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.caption("💡 **베이지안 정리**: P(위험|신고) = P(신고|위험)×P(위험) / P(신고)")
with col_f2:
    st.caption(f"📍 **범위**: 서울 중구 | **격자**: {GRID_SIZE_M}m | **동**: {len(JUNGGU_DONGS)}개")
with col_f3:
    st.caption("💾 자동 저장: reports.json | 최종 업데이트: 2026-06-16")
