"""
Bayesian PGIS 서울 중구 안전지도 - 주소 기반 동 분할 + 프로페셔널 디자인
"""

import json
import os
from datetime import datetime
import math
import streamlit as st
import folium
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

# ========== 중구 행정동 데이터 (주소 기반) ==========
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

REPORTS_FILE = os.path.join(os.path.dirname(__file__), "reports.json")

# ========== CSS 스타일 (프로페셔널 디자인) ==========
CUSTOM_CSS = """
<style>
    /* 메인 배경 */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* 헤더 스타일 */
    .header-main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .header-main h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .header-main p {
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
        opacity: 0.9;
    }
    
    /* 메트릭 카드 */
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
    
    /* 섹션 제목 */
    .section-title {
        color: #667eea;
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }
    
    /* 카드 */
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* 버튼 */
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
    
    /* 데이터프레임 */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* 위험도 레벨 배지 */
    .risk-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .risk-low { background: #d1fae5; color: #065f46; }
    .risk-mid { background: #fef3c7; color: #92400e; }
    .risk-high { background: #fed7aa; color: #92400e; }
    .risk-critical { background: #fee2e2; color: #991b1b; }
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
    if value < 0.2:
        return "#10b981"
    elif value < 0.4:
        return "#fbbf24"
    elif value < 0.6:
        return "#f97316"
    else:
        return "#ef4444"

def get_risk_level(value):
    """위험도 레벨 텍스트"""
    if value < 0.2:
        return ("안전", "risk-low")
    elif value < 0.4:
        return ("주의", "risk-mid")
    elif value < 0.6:
        return ("위험", "risk-high")
    else:
        return ("매우 위험", "risk-critical")

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
if "next_id" not in st.session_state:
    st.session_state.next_id = max([r.get("id", 0) for r in st.session_state.reports], default=0) + 1
if "grid" not in st.session_state:
    st.session_state.grid = create_grid()
if "selected_dong" not in st.session_state:
    st.session_state.selected_dong = "전체"

# ========== 메인 헤더 ==========
st.markdown(f"""
<div class="header-main">
    <h1>🗺️ 서울 중구 안전지도</h1>
    <p>베이지안 정리 기반 | 주소별 동 분할 | {len(st.session_state.grid):,}개 격자 분석</p>
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

# ========== 레이아웃 ==========
col_left, col_right = st.columns([1, 2.5])

with col_left:
    st.markdown("### 📝 신고 관리")
    
    # 동 선택
    selected_dong = st.selectbox("📍 동 선택", ["전체"] + list(JUNGGU_DONGS.keys()))
    st.session_state.selected_dong = selected_dong
    
    # 탭
    tab1, tab2, tab3 = st.tabs(["신고", "업로드", "분석"])
    
    with tab1:
        with st.form("report_form", border=True):
            st.markdown("**새 신고 작성**")
            report_type = st.selectbox("위험 유형", ["조명 부족", "시야 차단", "도로 파손", "불법 주정차", "기타"])
            intensity = st.slider("위험도", 1, 5, 3, help="1: 안전 → 5: 매우 위험")
            lat = st.number_input("위도", value=37.5630, format="%.4f")
            lng = st.number_input("경도", value=126.9945, format="%.4f")
            desc = st.text_area("상세 설명", max_chars=100, placeholder="예: 횡단보도 직전 조명 전부 고장...")
            
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
                st.success(f"✅ 신고 저장 | {dong}")
                st.rerun()
    
    with tab2:
        st.markdown("**데이터 업로드**")
        uploaded = st.file_uploader("CSV/JSON 파일", type=["csv", "json"])
        if uploaded and st.button("📤 업로드", use_container_width=True):
            try:
                if uploaded.name.endswith(".csv"):
                    df = pd.read_csv(uploaded)
                    for _, row in df.iterrows():
                        lat, lng = float(row.get("lat", 37.5630)), float(row.get("lng", row.get("lon", 126.9945)))
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
                else:
                    data = json.load(uploaded)
                    for item in data:
                        if "id" not in item:
                            item["id"] = st.session_state.next_id
                            st.session_state.next_id += 1
                        if "dong" not in item:
                            item["dong"] = get_dong_by_coords(item.get("lat", 37.5630), item.get("lng", 126.9945))
                    st.session_state.reports.extend(data)
                
                save_reports(st.session_state.reports)
                st.success(f"✅ {len(data if isinstance(data, list) else df)} 건 업로드")
                st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")
    
    with tab3:
        st.markdown("**데이터 관리**")
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
            if st.button("🗑️ 전체 삭제", use_container_width=True, type="secondary"):
                if st.session_state.reports:
                    if st.checkbox("정말 삭제하시겠습니까?"):
                        st.session_state.reports = []
                        save_reports([])
                        st.success("삭제됨")
                        st.rerun()

with col_right:
    st.markdown("### 🎯 베이지안 위험도 지도")
    
    # 베이지안 계산
    bayesian_grid = bayesian_update(st.session_state.grid, st.session_state.reports)
    
    # 지도
    m = folium.Map(location=JUNGGU_CENTER, zoom_start=13, tiles="OpenStreetMap")
    
    # 격자 표시
    for cell in bayesian_grid:
        if selected_dong != "전체" and cell["dong"] != selected_dong:
            continue
        color = get_color(cell["posterior"])
        popup = f"<b>{cell['dong']}</b><br/>위험도: {cell['posterior']:.2%}<br/>신고: {cell['report_count']}건"
        
        folium.Rectangle(
            bounds=[
                [cell["lat"] - GRID_SIZE_M/222000, cell["lon"] - GRID_SIZE_M/222000],
                [cell["lat"] + GRID_SIZE_M/222000, cell["lon"] + GRID_SIZE_M/222000],
            ],
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
            weight=1,
            popup=popup,
        ).add_to(m)
    
    # 신고 마커
    type_colors = {
        "조명 부족": "orange",
        "시야 차단": "red",
        "도로 파손": "purple",
        "불법 주정차": "blue",
        "기타": "gray",
    }
    
    for report in st.session_state.reports:
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
            color="black",
            fill=False,
            weight=2,
            label=dong_name,
        ).add_to(b)
    
    st_folium(m, width=700, height=700)

# ========== 하단: 분석 ==========
st.divider()
st.markdown("### 📊 상세 분석")

# 동별 분석
if st.session_state.reports:
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # 동별 신고 현황
        dong_reports = pd.DataFrame(st.session_state.reports).groupby("dong").size().sort_values(ascending=False)
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
        intensity_dist = pd.DataFrame(st.session_state.reports)["intensity"].value_counts().sort_index()
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
st.markdown("### 📋 상세 신고 목록")
if st.session_state.reports:
    df_reports = pd.DataFrame(st.session_state.reports)
    if selected_dong != "전체":
        df_reports = df_reports[df_reports["dong"] == selected_dong]
    
    df_display = df_reports[["id", "dong", "type", "intensity", "time", "desc"]].copy()
    df_display.columns = ["ID", "동", "유형", "위험도", "시간", "설명"]
    
    st.dataframe(
        df_display.sort_values("ID", ascending=False),
        use_container_width=True,
        height=400,
    )
else:
    st.info("📌 아직 신고가 없습니다. 왼쪽 폼에서 신고를 등록해주세요.")

# ========== 푸터 ==========
st.divider()
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.caption("💡 **베이지안 정리**: P(위험|신고) = P(신고|위험)×P(위험) / P(신고)")
with col_f2:
    st.caption(f"📍 **범위**: 서울 중구 | **격자**: {GRID_SIZE_M}m | **동**: {len(JUNGGU_DONGS)}개")
with col_f3:
    st.caption("💾 자동 저장: reports.json | 최종 업데이트: 2026-06-16")
