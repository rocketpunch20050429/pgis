"""
Bayesian PGIS (Participatory GIS) for Seoul Junggu Safety Map
베이지안 분석 기반 서울 중구 안전지도
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

# ========== 설정 ==========
JUNGGU_CENTER = [37.5630, 126.9945]  # 서울 중구 중심
JUNGGU_BOUNDS = {
    "north": 37.5815,
    "south": 37.5445,
    "east": 127.0050,
    "west": 126.9840,
}
GRID_SIZE_M = 300  # 300m 격자
REPORTS_FILE = os.path.join(os.path.dirname(__file__), "reports.json")

# ========== 페이지 설정 ==========
st.set_page_config(
    page_title="중구 안전지도 - 베이지안 분석",
    page_icon="🗺️",
    layout="wide",
)

# ========== 베이지안 계산 함수 ==========
def haversine_distance(lat1, lon1, lat2, lon2):
    """위도/경도 간 거리 계산 (미터)"""
    R = 6371000  # 지구 반지름 (m)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def create_grid():
    """중구 범위의 격자 생성"""
    grid = []
    lat_step = GRID_SIZE_M / 111000  # 위도는 111km = 1도
    lon_step = GRID_SIZE_M / (111000 * math.cos(math.radians(JUNGGU_CENTER[0])))
    
    lat = JUNGGU_BOUNDS["south"]
    grid_id = 0
    while lat < JUNGGU_BOUNDS["north"]:
        lon = JUNGGU_BOUNDS["west"]
        while lon < JUNGGU_BOUNDS["east"]:
            grid.append({
                "id": grid_id,
                "lat": lat + lat_step/2,
                "lon": lon + lon_step/2,
                "prior": 0.1,  # 초기 위험도
            })
            grid_id += 1
            lon += lon_step
        lat += lat_step
    
    return grid

def bayesian_update(grid, reports):
    """베이지안 정리로 위험도 업데이트"""
    updated = []
    
    for cell in grid:
        prior = cell["prior"]
        
        # 근처 신고 찾기 (500m 이내)
        nearby = [r for r in reports 
                  if haversine_distance(cell["lat"], cell["lon"], r["lat"], r["lng"]) < 500]
        
        if nearby:
            # Likelihood: 신고 강도 기반
            likelihood = min(1.0, sum([r["intensity"] for r in nearby]) / (5 * len(nearby)))
        else:
            likelihood = 0.05
        
        # 베이지안 계산
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
    """위험도에 따른 색상"""
    if value < 0.2:
        return "#10b981"  # 초록 (안전)
    elif value < 0.4:
        return "#fbbf24"  # 노랑 (주의)
    elif value < 0.6:
        return "#f97316"  # 주황 (위험)
    else:
        return "#ef4444"  # 빨강 (매우 위험)

# ========== 데이터 관리 ==========
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
if "show_form" not in st.session_state:
    st.session_state.show_form = False

# ========== 메인 페이지 ==========
st.title("🗺️ 서울 중구 안전지도")
st.markdown("**베이지안 분석 기반** | 주민 신고 + 공공데이터 = 위험도 예측")

# 통계
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📊 총 신고건수", len(st.session_state.reports))
with col2:
    avg_risk = np.mean([r["intensity"] for r in st.session_state.reports]) if st.session_state.reports else 0
    st.metric("📈 평균 위험도", f"{avg_risk:.1f}")
with col3:
    high_risk = len([r for r in st.session_state.reports if r["intensity"] >= 4])
    st.metric("🔴 위험 신고", high_risk)
with col4:
    st.metric("📍 격자 셀", len(st.session_state.grid))

# ========== 레이아웃: 좌측(폼) + 우측(지도) ==========
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("📝 신고 작성")
    
    # 파일 업로드
    with st.expander("📤 데이터 업로드", expanded=False):
        uploaded = st.file_uploader("CSV/JSON 업로드", type=["csv", "json"])
        if uploaded:
            try:
                if uploaded.name.endswith(".csv"):
                    df = pd.read_csv(uploaded)
                    for _, row in df.iterrows():
                        st.session_state.reports.append({
                            "id": st.session_state.next_id,
                            "lng": float(row.get("lng", row.get("lon", 126.9945))),
                            "lat": float(row.get("lat", 37.5630)),
                            "type": str(row.get("type", "신고")),
                            "intensity": int(row.get("intensity", 3)),
                            "time": str(row.get("time", datetime.now().strftime("%H:%M"))),
                            "desc": str(row.get("desc", "")),
                        })
                        st.session_state.next_id += 1
                else:
                    data = json.load(uploaded)
                    if isinstance(data, list):
                        for item in data:
                            if "id" not in item:
                                item["id"] = st.session_state.next_id
                                st.session_state.next_id += 1
                        st.session_state.reports.extend(data)
                
                save_reports(st.session_state.reports)
                st.success("✅ 업로드 완료")
                st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")
    
    # 신고 폼
    with st.form("report_form"):
        report_type = st.selectbox("위험 유형", ["조명 부족", "시야 차단", "도로 파손", "불법 주정차", "기타"])
        intensity = st.slider("위험도", 1, 5, 3)
        lat = st.number_input("위도", value=37.5630, format="%.4f")
        lng = st.number_input("경도", value=126.9945, format="%.4f")
        desc = st.text_area("설명", max_chars=100)
        
        if st.form_submit_button("📌 신고 추가"):
            st.session_state.reports.append({
                "id": st.session_state.next_id,
                "lng": lng,
                "lat": lat,
                "type": report_type,
                "intensity": intensity,
                "time": datetime.now().strftime("%H:%M"),
                "desc": desc,
            })
            st.session_state.next_id += 1
            save_reports(st.session_state.reports)
            st.success("✅ 신고 저장됨")
            st.rerun()
    
    # 내보내기
    if st.session_state.reports:
        if st.button("⬇️ CSV 다운로드"):
            df = pd.DataFrame(st.session_state.reports)
            st.download_button(
                label="다운로드",
                data=df.to_csv(index=False, encoding="utf-8-sig"),
                file_name=f"reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
    
    # 삭제
    if st.button("🗑️ 전체 데이터 삭제", type="secondary"):
        st.session_state.reports = []
        save_reports([])
        st.success("✅ 삭제됨")
        st.rerun()

with col_right:
    st.subheader("🎯 베이지안 위험도 지도")
    
    # 베이지안 계산
    bayesian_grid = bayesian_update(st.session_state.grid, st.session_state.reports)
    
    # 지도 생성
    m = folium.Map(
        location=JUNGGU_CENTER,
        zoom_start=13,
        tiles="OpenStreetMap",
    )
    
    # 격자 시각화
    for cell in bayesian_grid:
        color = get_color(cell["posterior"])
        popup = f"위험도: {cell['posterior']:.2f}<br>신고: {cell['report_count']}"
        
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
    type_icon = {
        "조명 부족": "💡",
        "시야 차단": "🚧",
        "도로 파손": "🕳️",
        "불법 주정차": "🚗",
        "기타": "⚠️",
    }
    
    for report in st.session_state.reports:
        icon_emoji = type_icon.get(report["type"], "⚠️")
        popup = f"""
        <b>{report['type']}</b><br/>
        위험도: {report['intensity']}/5<br/>
        시간: {report['time']}<br/>
        {report.get('desc', '')}
        """
        folium.Marker(
            location=[report["lat"], report["lng"]],
            popup=folium.Popup(popup, max_width=200),
            icon=folium.Icon(color="red", icon_color="white"),
            tooltip=report["type"],
        ).add_to(m)
    
    # 중구 경계 표시
    folium.Rectangle(
        bounds=[
            [JUNGGU_BOUNDS["south"], JUNGGU_BOUNDS["west"]],
            [JUNGGU_BOUNDS["north"], JUNGGU_BOUNDS["east"]],
        ],
        color="black",
        fill=False,
        weight=2,
        label="서울 중구",
    ).add_to(m)
    
    st_folium(m, width=700, height=600)

# ========== 하단: 신고 목록 ==========
st.divider()
st.subheader("📋 신고 내역")

if st.session_state.reports:
    df = pd.DataFrame(st.session_state.reports)
    df_display = df[["id", "type", "intensity", "lat", "lng", "time", "desc"]].copy()
    df_display.columns = ["ID", "유형", "위험도", "위도", "경도", "시간", "설명"]
    st.dataframe(df_display, use_container_width=True, height=300)
else:
    st.info("등록된 신고가 없습니다.")

# ========== 푸터 ==========
st.divider()
st.caption("💡 **베이지안 정리**: 기본 위험도(Prior) + 신고 강도(Likelihood) → 최종 위험도(Posterior)")
st.caption("📍 범위: 서울 중구 | 격자: 300m × 300m | 자동 저장: reports.json")
