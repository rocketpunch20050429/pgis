import json
import os
import csv
from datetime import datetime
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

# Page config
st.set_page_config(
    page_title="마을 안전 사각지대 예측 지도",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ 데이터 경로 ============
REPORTS_FILE = os.path.join(os.path.dirname(__file__), "reports.json")

# ============ 데이터 로드/저장 ============
def load_reports():
    """reports.json에서 신고 데이터 로드"""
    if os.path.exists(REPORTS_FILE):
        try:
            with open(REPORTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_reports(reports):
    """신고 데이터를 reports.json에 저장"""
    try:
        with open(REPORTS_FILE, "w", encoding="utf-8") as f:
            json.dump(reports, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"저장 오류: {e}")
        return False

# ============ 세션 상태 초기화 ============
if "reports" not in st.session_state:
    st.session_state.reports = load_reports()
if "mode" not in st.session_state:
    st.session_state.mode = "diagnostic"
if "next_id" not in st.session_state:
    st.session_state.next_id = max([r.get("id", 0) for r in st.session_state.reports], default=0) + 1

# ============ 화면 헤더 ============
st.title("📍 마을 안전 사각지대 예측 지도")
st.markdown("주민 신고와 공공데이터를 바탕으로 한 위험지역 예측 시스템")

# ============ 좌측 사이드바 ============
with st.sidebar:
    st.header("🔧 제어 패널")
    
    # ---- 데이터 업로드 ----
    st.subheader("📤 데이터 업로드")
    uploaded = st.file_uploader("CSV 또는 JSON 업로드", type=["csv", "json"])
    if uploaded is not None:
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
                new_reports = []
                for _, row in df.iterrows():
                    new_reports.append({
                        "id": st.session_state.next_id,
                        "lng": float(row.get("lng", row.get("lon", 126.9780))),
                        "lat": float(row.get("lat", 37.5665)),
                        "type": row.get("type", row.get("category", "신고")),
                        "intensity": int(row.get("intensity", 3)),
                        "time": str(row.get("time", "00:00")),
                        "desc": str(row.get("desc", row.get("description", ""))),
                    })
                    st.session_state.next_id += 1
                st.session_state.reports.extend(new_reports)
            else:
                data = json.load(uploaded)
                if isinstance(data, list):
                    for item in data:
                        if "id" not in item:
                            item["id"] = st.session_state.next_id
                            st.session_state.next_id += 1
                    st.session_state.reports.extend(data)
            
            save_reports(st.session_state.reports)
            st.success("✅ 데이터 업로드 완료!")
            st.rerun()
        except Exception as e:
            st.error(f"업로드 오류: {e}")
    
    # ---- 통계 ----
    st.subheader("📊 통계")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("신고 건수", len(st.session_state.reports))
    with col2:
        avg_intensity = sum([r.get("intensity", 0) for r in st.session_state.reports]) / max(len(st.session_state.reports), 1)
        st.metric("평균 위험도", f"{avg_intensity:.1f}")
    with col3:
        st.metric("위험 지역", len([r for r in st.session_state.reports if r.get("intensity", 0) >= 4]))
    
    # ---- 지도 모드 선택 ----
    st.subheader("🗺️ 지도 모드")
    st.session_state.mode = st.radio(
        "표시 방식 선택",
        ["diagnostic", "uncertainty", "posterior"],
        format_func=lambda x: {
            "diagnostic": "위험 변화 지도",
            "uncertainty": "정보량 지도",
            "posterior": "최종 위험도 지도"
        }[x]
    )
    
    # ---- 신고 추가 폼 ----
    st.subheader("🚨 신고 추가")
    with st.form("report_form"):
        report_type = st.selectbox(
            "위험 유형",
            ["조명 부족", "시야 차단", "도로 파손", "불법 주정차", "기타"]
        )
        intensity = st.slider("위험도 (1~5)", 1, 5, 3)
        desc = st.text_area("상세 설명", max_chars=200)
        lng = st.number_input("경도 (Longitude)", value=126.9780, format="%.4f")
        lat = st.number_input("위도 (Latitude)", value=37.5665, format="%.4f")
        
        if st.form_submit_button("📍 신고 추가"):
            new_report = {
                "id": st.session_state.next_id,
                "lng": lng,
                "lat": lat,
                "type": report_type,
                "intensity": intensity,
                "time": datetime.now().strftime("%H:%M"),
                "desc": desc or "신고",
            }
            st.session_state.reports.append(new_report)
            st.session_state.next_id += 1
            save_reports(st.session_state.reports)
            st.success("✅ 신고 추가 완료!")
            st.rerun()
    
    # ---- 내보내기 ----
    st.subheader("⬇️ 내보내기")
    if st.button("CSV로 다운로드"):
        df = pd.DataFrame(st.session_state.reports)
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 신고_데이터.csv",
            data=csv,
            file_name=f"reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # ---- 데이터 관리 ----
    st.subheader("🗑️ 데이터 관리")
    if st.button("전체 데이터 삭제"):
        st.session_state.reports = []
        save_reports([])
        st.success("✅ 데이터 삭제 완료!")
        st.rerun()

# ============ 메인 영역: 지도 ============
st.subheader("🗺️ 서울 안전 사각지대 지도")

# 지도 생성 (folium)
m = folium.Map(
    location=[37.5665, 126.9780],
    zoom_start=11,
    tiles="OpenStreetMap"
)

# 신고 마커 추가
type_colors = {
    "조명 부족": "yellow",
    "시야 차단": "red",
    "도로 파손": "purple",
    "불법 주정차": "blue",
    "기타": "gray"
}

for report in st.session_state.reports:
    color = type_colors.get(report.get("type", "기타"), "gray")
    intensity = report.get("intensity", 0)
    
    # 마커 색상 (위험도에 따라 더 진해짐)
    if intensity >= 4:
        color = "darkred"
    elif intensity >= 3:
        color = "orange"
    else:
        color = "lightblue"
    
    popup_text = f"""
    <b>{report.get('type', '신고')}</b><br/>
    위험도: {intensity}/5<br/>
    시간: {report.get('time', '')}<br/>
    설명: {report.get('desc', '')}
    """
    
    folium.Marker(
        location=[report.get("lat"), report.get("lng")],
        popup=folium.Popup(popup_text, max_width=200),
        icon=folium.Icon(color=color, icon="info-sign"),
    ).add_to(m)

# 지도 렌더링
map_data = st_folium(m, width=1400, height=600)

# ============ 하단: 신고 목록 ============
st.subheader("📋 신고 내역")

if st.session_state.reports:
    df = pd.DataFrame(st.session_state.reports)
    # 컬럼 재정렬 및 표시명 변경
    df_display = df[["id", "lng", "lat", "type", "intensity", "time", "desc"]]
    df_display.columns = ["ID", "경도", "위도", "유형", "위험도", "시간", "설명"]
    st.dataframe(df_display, use_container_width=True)
else:
    st.info("등록된 신고가 없습니다.")

# ============ 푸터 ============
st.divider()
st.caption("💡 팁: 지도에서 마커를 클릭하면 상세 정보를 볼 수 있습니다.")
st.caption("🔄 데이터는 자동으로 서버에 저장됩니다.")
