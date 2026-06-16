import json
import os

import streamlit as st
import urllib.parse
try:
  import streamlit.components.v1 as components
  _HAS_COMPONENTS = True
except Exception:
  components = None
  _HAS_COMPONENTS = False


st.set_page_config(
    page_title="마을 안전 사각지대 예측 지도",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="collapsed",
)
#
st.markdown(
    """
    <style>
      #MainMenu, header, footer { visibility: hidden; }
      .stApp { background: #07111f; }
      .block-container {
        padding: 0 !important;
        max-width: 100% !important;
      }
      iframe {
        display: block;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_optional_secret(name):
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""


MAPBOX_TOKEN = (
    os.environ.get("NEXT_PUBLIC_MAPBOX_TOKEN")
    or os.environ.get("MAPBOX_TOKEN")
    or get_optional_secret("NEXT_PUBLIC_MAPBOX_TOKEN")
    or get_optional_secret("MAPBOX_TOKEN")
    or ""
)

# 서버 측 저장 파일 경로 (앱 루트)
SAVED_REPORTS_PATH = os.path.join(os.path.dirname(__file__), "reports.json")

# 파일 업로드를 통해 서버에 보고서 저장 가능
uploaded = st.file_uploader("신고 데이터 업로드 (JSON 또는 CSV)", type=["json", "csv"])
if uploaded is not None:
  try:
    content = uploaded.read()
    text = content.decode("utf-8")
    if uploaded.name.lower().endswith(".csv"):
      import csv
      rows = list(csv.DictReader(text.splitlines()))
      data = []
      for r in rows:
        # normalize keys
        data.append({
          "id": int(r.get("id") or 0),
          "lng": float(r.get("lng") or r.get("lon") or 0),
          "lat": float(r.get("lat") or 0),
          "type": r.get("type") or r.get("category") or "신고",
          "intensity": int(r.get("intensity") or 3),
          "time": r.get("time") or "00:00",
          "desc": r.get("desc") or r.get("description") or "",
        })
    else:
      data = json.loads(text)
    with open(SAVED_REPORTS_PATH, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False)
    st.success("신고 데이터가 서버에 저장되었습니다. 페이지를 새로고침하면 반영됩니다.")
  except Exception as e:
    st.error(f"업로드 처리 중 오류: {e}")

# 초기 로드용 서버 저장본이 있으면 읽어서 JS로 전달
initial_reports = None
if os.path.exists(SAVED_REPORTS_PATH):
  try:
    with open(SAVED_REPORTS_PATH, "r", encoding="utf-8") as f:
      initial_reports = json.load(f)
  except Exception:
    initial_reports = None

APP_HTML = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" />
  <style>
    :root {
      --navy: #f0f4f8;
      --panel: #ffffff;
      --text: #1e293b;
      --muted: #64748b;
      --line: #e2e8f0;
      --accent: #2563eb;
      --warning: #f59e0b;
      --danger: #ef4444;
      --safe: #10b981;
    }

    * { box-sizing: border-box; }

    html, body {
      margin: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: #ffffff;
      font-family: "Pretendard", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
    }

    button, select, input, textarea {
      font-family: inherit;
    }

    .app {
      display: flex;
      width: 100%;
      height: 900px;
      min-height: 720px;
      position: relative;
      background: #f8fafc;
      overflow: hidden;
    }

    .side-panel {
      width: 360px;
      min-width: 360px;
      height: 100%;
      display: flex;
      flex-direction: column;
      background: #ffffff;
      border-right: 1px solid #e2e8f0;
      transition: width 0.28s ease, min-width 0.28s ease;
      position: relative;
      z-index: 10;
      overflow: hidden;
    }

    .side-panel.closed {
      width: 0;
      min-width: 0;
      border-right: 0;
    }

    .panel-body {
      width: 360px;
      min-width: 360px;
      height: 100%;
      display: flex;
      flex-direction: column;
    }

    .panel-scroll {
      overflow-y: auto;
      padding-bottom: 16px;
    }

    .panel-header {
      padding: 20px 24px;
      border-bottom: 1px solid var(--line);
      flex: 0 0 auto;
    }

    .eyebrow {
      margin-bottom: 4px;
      color: var(--accent);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 2px;
    }

    h1 {
      margin: 0;
      font-size: 18px;
      font-weight: 850;
      line-height: 1.4;
      letter-spacing: 0;
    }

    .subtitle {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.4;
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      padding: 16px 24px;
    }

    .stat-card {
      min-height: 66px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 11px 8px;
      text-align: center;
    }

    .stat-value {
      font-size: 20px;
      font-weight: 850;
      line-height: 1.1;
      letter-spacing: 0;
      white-space: nowrap;
    }

    .stat-value span {
      margin-left: 1px;
      color: var(--muted);
      font-size: 10px;
      font-weight: 700;
    }

    .stat-label {
      margin-top: 4px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.2;
    }

    .section {
      padding: 0 24px 16px;
    }

    .section-title {
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
    }

    .mode-button {
      width: 100%;
      display: block;
      margin-bottom: 6px;
      padding: 10px 14px;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      background: transparent;
      color: var(--text);
      cursor: pointer;
      text-align: left;
      transition: background 0.18s ease, border-color 0.18s ease;
    }

    .mode-button.active {
      border-color: #2563eb;
      background: rgba(37, 99, 235, 0.1);
    }

    .mode-label {
      font-size: 13px;
      font-weight: 700;
      line-height: 1.25;
    }

    .mode-desc {
      margin-top: 2px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.25;
    }

    .primary-button {
      width: 100%;
      min-height: 42px;
      padding: 12px;
      border: 0;
      border-radius: 8px;
      background: var(--accent);
      color: white;
      cursor: pointer;
      font-size: 13px;
      font-weight: 800;
      line-height: 1.2;
      transition: background 0.18s ease;
    }

    .primary-button.cancel {
      background: var(--danger);
    }

    .hint {
      margin: 8px 0 0;
      color: var(--warning);
      text-align: center;
      font-size: 11px;
      line-height: 1.35;
    }

    .inner-card {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 16px;
    }

    .card-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
      font-size: 12px;
      font-weight: 800;
      line-height: 1.3;
    }

    .icon-button {
      width: 24px;
      height: 24px;
      padding: 0;
      border: 0;
      border-radius: 6px;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      font-size: 14px;
      line-height: 1;
    }

    .form-location {
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.35;
    }

    .field {
      width: 100%;
      min-height: 34px;
      margin-bottom: 8px;
      padding: 8px;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      background: #ffffff;
      color: var(--text);
      font-size: 12px;
      outline: none;
    }

    textarea.field {
      min-height: 58px;
      resize: vertical;
    }

    .field-label {
      margin-bottom: 5px;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.2;
    }

    .intensity-row {
      display: flex;
      gap: 4px;
      margin-bottom: 10px;
    }

    .intensity-button {
      flex: 1;
      height: 30px;
      border: 0;
      border-radius: 6px;
      background: #cbd5e1;
      color: white;
      cursor: pointer;
      font-size: 12px;
      font-weight: 800;
    }

    .analysis-row {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 7px 0;
      border-bottom: 1px solid #e2e8f0;
    }

    .analysis-label {
      color: var(--muted);
      font-size: 11px;
      line-height: 1.35;
    }

    .analysis-value {
      font-size: 13px;
      font-weight: 850;
      white-space: nowrap;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 42px;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 750;
      line-height: 1.2;
    }

    .legend-wrap {
      margin-top: auto;
      padding: 0 24px 20px;
      flex: 0 0 auto;
    }

    .legend-title {
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.3;
    }

    .gradient-legend {
      display: flex;
      align-items: center;
      gap: 5px;
    }

    .gradient-legend span {
      font-size: 9px;
      line-height: 1;
      white-space: nowrap;
    }

    .gradient-bar {
      flex: 1;
      height: 6px;
      border-radius: 999px;
    }

    .confidence-legend {
      display: flex;
      gap: 9px;
      flex-wrap: wrap;
    }

    .confidence-item {
      display: flex;
      align-items: center;
      gap: 5px;
      font-size: 10px;
      line-height: 1.2;
    }

    .swatch {
      width: 10px;
      height: 10px;
      border-radius: 3px;
    }

    .footnote {
      margin-top: 8px;
      color: #475569;
      font-size: 9px;
      line-height: 1.4;
    }

    .toggle {
      position: absolute;
      left: 360px;
      top: 50%;
      z-index: 20;
      width: 24px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      transform: translateY(-50%);
      border: 1px solid #e2e8f0;
      border-left: 0;
      border-radius: 0 8px 8px 0;
      background: #ffffff;
      color: var(--text);
      cursor: pointer;
      font-size: 16px;
      transition: left 0.28s ease;
    }

    .toggle.closed { left: 0; }

    #map {
      flex: 1;
      height: 100%;
      min-width: 0;
      background: #e0f2fe;
    }

    .leaflet-tile-pane {
      filter: saturate(1.14) contrast(1.02);
    }

    .top-badge {
      position: absolute;
      top: 16px;
      left: 50%;
      z-index: 12;
      display: flex;
      align-items: center;
      gap: 8px;
      transform: translateX(-50%);
      max-width: calc(100% - 420px);
      padding: 8px 20px;
      border: 1px solid #e2e8f0;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(8px);
      font-size: 12px;
      font-weight: 750;
      line-height: 1.2;
      white-space: nowrap;
      pointer-events: none;
      color: var(--text);
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      flex: 0 0 auto;
    }

    .formula {
      position: absolute;
      right: 16px;
      bottom: 16px;
      z-index: 12;
      width: 280px;
      max-width: calc(100% - 32px);
      padding: 12px 16px;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(8px);
      font-size: 11px;
      line-height: 1.6;
      pointer-events: none;
      color: var(--text);
    }

    .formula-note {
      margin-top: 4px;
      color: var(--muted);
      font-size: 10px;
      line-height: 1.45;
    }

    .leaflet-control-zoom a {
      background: #ffffff !important;
      color: var(--text) !important;
      border-color: #e2e8f0 !important;
    }

    .leaflet-popup-content-wrapper,
    .leaflet-popup-tip {
      background: transparent;
      box-shadow: none;
    }

    .leaflet-popup-content {
      margin: 0;
    }

    .marker-icon {
      width: 28px;
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      line-height: 1;
      filter: drop-shadow(0 0 4px rgba(0, 0, 0, 0.55));
    }

    .marker-icon.new {
      animation: pulse 1s infinite;
    }

    @keyframes pulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.28); }
    }

    @media (max-width: 820px) {
      .app { height: 860px; min-height: 700px; }
      .side-panel {
        position: absolute;
        left: 0;
        top: 0;
        width: min(360px, 88vw);
        min-width: min(360px, 88vw);
      }
      .panel-body {
        width: min(360px, 88vw);
        min-width: min(360px, 88vw);
      }
      .side-panel.closed {
        width: 0;
        min-width: 0;
      }
      .toggle { left: min(360px, 88vw); }
      .toggle.closed { left: 0; }
      .top-badge {
        top: 12px;
        max-width: calc(100% - 42px);
        padding: 8px 14px;
      }
      .formula {
        left: 12px;
        right: 12px;
        bottom: 12px;
        width: auto;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="side-panel" id="sidePanel">
      <div class="panel-body">
        <div class="panel-header">
          <div class="eyebrow">BAYESIAN PGIS</div>
          <h1>마을 안전 사각지대<br />예측 지도</h1>
          <p class="subtitle">주민 신고와 공공데이터를 바탕으로 한 위험지역 예측 시스템</p>
        </div>

        <div class="panel-scroll">
          <div class="stats">
            <div class="stat-card">
              <div class="stat-value" style="color: var(--accent);"><span id="totalReports">0</span><span>건</span></div>
              <div class="stat-label">신고 건수</div>
            </div>
            <div class="stat-card">
              <div class="stat-value" style="color: var(--warning);"><span id="avgPost">0.0</span><span>%</span></div>
              <div class="stat-label">평균 위험도</div>
            </div>
            <div class="stat-card">
              <div class="stat-value" style="color: var(--danger);"><span id="blindspots">0</span><span>격자</span></div>
              <div class="stat-label">위험 지역 수</div>
            </div>
          </div>

          <div class="section">
            <div class="section-title">지도 모드</div>
            <button class="mode-button active" data-mode="diagnostic">
              <div class="mode-label">위험 변화 지도</div>
              <div class="mode-desc">신고로 인한 위험도 변화</div>
            </button>
            <button class="mode-button" data-mode="uncertainty">
              <div class="mode-label">정보량 지도</div>
              <div class="mode-desc">신고가 많은 지역 표시</div>
            </button>
            <button class="mode-button" data-mode="posterior">
              <div class="mode-label">최종 위험도 지도</div>
              <div class="mode-desc">최종 위험도 한눈에 보기</div>
            </button>
          </div>

          <div class="section">
            <button class="primary-button" id="reportModeButton">📍 위험 지점 신고하기</button>
            <button class="primary-button" id="exportReports" style="margin-top:8px;background:#64748b;">⬇️ 신고 내역 내보내기</button>
            <p class="hint" id="reportHint" style="display: none;">지도에서 위험 지점을 클릭하세요</p>
          </div>

          <div class="section" id="reportFormSection" style="display: none;">
            <div class="inner-card">
              <div class="card-head">
                <span>🚨 위험 신고 작성</span>
                <button class="icon-button" id="closeReportForm" title="닫기">✕</button>
              </div>
              <div class="form-location" id="reportLocation"></div>
              <select class="field" id="reportType"></select>
              <div class="field-label">위험 정도 (1:약함 ~ 5:심각함)</div>
              <div class="intensity-row" id="intensityButtons"></div>
              <textarea class="field" id="reportDesc" placeholder="상세 설명 (선택)"></textarea>
              <button class="primary-button" id="submitReport">신고 제출 → 지도 업데이트</button>
            </div>
          </div>

          <div class="section" id="selectedHexSection" style="display: none;">
            <div class="inner-card">
              <div class="card-head">
                <span>📊 이 지역의 위험 분석</span>
                <button class="icon-button" id="closeHexInfo" title="닫기">✕</button>
              </div>
              <div id="selectedHexBody"></div>
            </div>
          </div>
        </div>

        <div class="legend-wrap">
          <div class="legend-title" id="legendTitle">범례 — 진단 지도</div>
          <div id="legendBody"></div>
          <div class="footnote">150m 단위 격자 분석 · 실시간 업데이트<br />서울특별시 전체 분석권역</div>
        </div>
      </div>
    </aside>

    <button class="toggle" id="togglePanel" title="패널 열기/닫기">‹</button>
    <div id="map"></div>

    <div class="top-badge">
      <span class="status-dot" id="statusDot"></span>
      <span id="statusText">위험 변화 지도 활성</span>
    </div>

    <div class="formula">
      <span style="font-weight: 800; color: var(--accent);">위험도 계산</span>
      <span style="color: var(--muted);"> = </span>
      <span>기본 위험도 × 신고량 반영</span>
      <div class="formula-note">공공데이터(기초) + 주민신고(가중치) = 최종 위험도</div>
    </div>
  </div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/@turf/turf@7/turf.min.js"></script>
  <script>
    const CENTER = [126.9780, 37.5665];
    const ZOOM = 11;
    const SEOUL_BBOX = [126.7640, 37.4130, 127.1840, 37.7150];
    const GRID_CELL_SIZE_KM = 0.15;

    const TYPE_META = {
      "조명 부족": { color: "#f59e0b", icon: "💡" },
      "시야 차단": { color: "#ef4444", icon: "🚧" },
      "도로 파손": { color: "#8b5cf6", icon: "🕳️" },
      "불법 주정차": { color: "#3b82f6", icon: "🚗" },
    };

    const MAP_MODES = {
      diagnostic: { label: "위험 변화 지도", desc: "기본 위험도 대비 변화" },
      uncertainty: { label: "정보량 지도", desc: "주민 신고 정보의 양" },
      posterior: { label: "최종 위험도 지도", desc: "종합 위험도" },
    };

    let reports = __INITIAL_REPORTS__ || [
      { id: 1, lng: 126.9751, lat: 37.5720, type: "조명 부족", intensity: 4, time: "22:30", desc: "골목 안쪽 가로등 고장" },
      { id: 2, lng: 126.9800, lat: 37.5695, type: "시야 차단", intensity: 5, time: "19:00", desc: "담벼락으로 시야 완전 차단" },
      { id: 3, lng: 126.9770, lat: 37.5680, type: "도로 파손", intensity: 3, time: "08:15", desc: "인도 블록 파손" },
      { id: 4, lng: 126.9815, lat: 37.5715, type: "불법 주정차", intensity: 4, time: "17:45", desc: "어린이보호구역 불법주정차" },
      { id: 5, lng: 126.9760, lat: 37.5740, type: "조명 부족", intensity: 5, time: "23:00", desc: "공원 입구 조명 전무" },
      { id: 6, lng: 126.9795, lat: 37.5660, type: "시야 차단", intensity: 3, time: "07:30", desc: "적치물로 보행 시야 방해" },
      { id: 7, lng: 126.9830, lat: 37.5700, type: "도로 파손", intensity: 2, time: "12:00", desc: "맨홀 뚜껑 파손" },
      { id: 8, lng: 126.9740, lat: 37.5705, type: "조명 부족", intensity: 4, time: "21:00", desc: "주택가 진입로 어두움" },
      { id: 9, lng: 126.9810, lat: 37.5735, type: "불법 주정차", intensity: 5, time: "08:00", desc: "통학로 차량 점거" },
      { id: 10, lng: 126.9775, lat: 37.5665, type: "시야 차단", intensity: 4, time: "18:30", desc: "공사 가림막 방치" },
      { id: 11, lng: 126.9755, lat: 37.5690, type: "조명 부족", intensity: 3, time: "20:00", desc: "골목 조명 흐림" },
      { id: 12, lng: 126.9820, lat: 37.5680, type: "도로 파손", intensity: 4, time: "09:30", desc: "보도블럭 융기" },
    ];
    // Load saved reports from localStorage if present (overrides server initial)
    try {
      const saved = JSON.parse(localStorage.getItem("pgis_reports") || "null");
      if (Array.isArray(saved) && saved.length > 0) {
        reports = saved;
      }
    } catch (e) {
      console.warn("Failed to load saved reports", e);
    }

    let mapMode = "diagnostic";
    let sideOpen = true;
    let reportMode = false;
    let reportForm = null;
    let selectedHex = null;
    let hexData = null;
    let hexLayer = null;
    let markerLayer = null;
    let lastSubmittedReportId = null;

    const els = {
      sidePanel: document.getElementById("sidePanel"),
      togglePanel: document.getElementById("togglePanel"),
      totalReports: document.getElementById("totalReports"),
      avgPost: document.getElementById("avgPost"),
      blindspots: document.getElementById("blindspots"),
      reportModeButton: document.getElementById("reportModeButton"),
      exportReports: document.getElementById("exportReports"),
      reportHint: document.getElementById("reportHint"),
      reportFormSection: document.getElementById("reportFormSection"),
      reportLocation: document.getElementById("reportLocation"),
      reportType: document.getElementById("reportType"),
      reportDesc: document.getElementById("reportDesc"),
      intensityButtons: document.getElementById("intensityButtons"),
      submitReport: document.getElementById("submitReport"),
      closeReportForm: document.getElementById("closeReportForm"),
      selectedHexSection: document.getElementById("selectedHexSection"),
      selectedHexBody: document.getElementById("selectedHexBody"),
      closeHexInfo: document.getElementById("closeHexInfo"),
      legendTitle: document.getElementById("legendTitle"),
      legendBody: document.getElementById("legendBody"),
      statusDot: document.getElementById("statusDot"),
      statusText: document.getElementById("statusText"),
    };

    const map = L.map("map", {
      center: [CENTER[1], CENTER[0]],
      zoom: ZOOM,
      zoomControl: false,
      preferCanvas: true,
    });

    L.control.zoom({ position: "bottomright" }).addTo(map);

    const MAPBOX_TOKEN = __MAPBOX_TOKEN__;
    const tileOptions = MAPBOX_TOKEN
      ? {
          url: `https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{z}/{x}/{y}?access_token=${MAPBOX_TOKEN}`,
          options: {
            attribution: "&copy; Mapbox &copy; OpenStreetMap",
            tileSize: 512,
            zoomOffset: -1,
            maxZoom: 20,
          },
        }
      : {
          // Use OpenStreetMap tiles as a reliable public fallback (no API token required)
          url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
          options: {
            attribution: "&copy; OpenStreetMap contributors",
            subdomains: "abc",
            maxZoom: 19,
          },
        };

    L.tileLayer(tileOptions.url, tileOptions.options).addTo(map);

    markerLayer = L.layerGroup().addTo(map);

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[char]));
    }

    function round2(value) {
      return Math.round(value * 100) / 100;
    }

    function seededPrior(feature) {
      const center = turf.centroid(feature).geometry.coordinates;
      const seed = Math.sin(center[0] * 127.1 + center[1] * 311.7) * 43758.5453123;
      const fraction = seed - Math.floor(seed);
      return 0.15 + fraction * 0.15;
    }

    function getHexGrid() {
      return turf.squareGrid(SEOUL_BBOX, GRID_CELL_SIZE_KM, { units: "kilometers" });
    }

    function computeBayesian(sourceReports, sourceHexGrid) {
      const features = sourceHexGrid.features.map((hex, index) => {
        const center = turf.centroid(hex);
        const nearby = sourceReports.filter((report) => {
          const distance = turf.distance(center, turf.point([report.lng, report.lat]), { units: "kilometers" });
          return distance < 0.08; // 80 meters
        });
        const prior = seededPrior(hex);
        const likelihood = nearby.length > 0
          ? Math.min(1, nearby.reduce((sum, report) => sum + report.intensity / 5, 0) / 3)
          : 0;
        const evidence = prior * likelihood + (1 - prior) * 0.1;
        const posterior = evidence > 0 ? (prior * likelihood) / evidence : prior * 0.5;
        const variation = posterior - prior;

        return {
          ...hex,
          id: index,
          properties: {
            ...hex.properties,
            hexId: index,
            prior: round2(prior),
            likelihood: round2(likelihood),
            posterior: round2(posterior),
            variation: round2(variation),
            reportCount: nearby.length,
            confidence: nearby.length >= 2 ? "high" : nearby.length === 1 ? "medium" : "low",
          },
        };
      });
      return { type: "FeatureCollection", features };
    }

    function interpolateColor(value, stops) {
      if (value <= stops[0][0]) return stops[0][1];
      if (value >= stops[stops.length - 1][0]) return stops[stops.length - 1][1];
      for (let i = 1; i < stops.length; i += 1) {
        if (value <= stops[i][0]) {
          const [v0, c0] = stops[i - 1];
          const [v1, c1] = stops[i];
          const t = (value - v0) / (v1 - v0);
          return mixHex(c0, c1, t);
        }
      }
      return stops[stops.length - 1][1];
    }

    function mixHex(a, b, t) {
      const ca = hexToRgb(a);
      const cb = hexToRgb(b);
      const mixed = ca.map((part, index) => Math.round(part + (cb[index] - part) * t));
      return "#" + mixed.map((part) => part.toString(16).padStart(2, "0")).join("");
    }

    function hexToRgb(hex) {
      const clean = hex.replace("#", "");
      return [
        parseInt(clean.slice(0, 2), 16),
        parseInt(clean.slice(2, 4), 16),
        parseInt(clean.slice(4, 6), 16),
      ];
    }

    function getHexStyle(feature) {
      const p = feature.properties;
      let fillColor = "#fbbf24";
      let fillOpacity = 0.44;

      if (mapMode === "diagnostic") {
        fillColor = interpolateColor(p.variation, [
          [-0.1, "#10b981"],
          [0, "#fbbf24"],
          [0.15, "#f97316"],
          [0.4, "#ef4444"],
          [0.7, "#7f1d1d"],
        ]);
      } else if (mapMode === "uncertainty") {
        fillColor = p.confidence === "high" ? "#3b82f6" : p.confidence === "medium" ? "#60a5fa" : "#1e3a5f";
        fillOpacity = p.confidence === "high" ? 0.58 : p.confidence === "medium" ? 0.38 : 0.14;
      } else {
        fillColor = interpolateColor(p.posterior, [
          [0, "#064e3b"],
          [0.2, "#10b981"],
          [0.4, "#fbbf24"],
          [0.6, "#f97316"],
          [0.8, "#ef4444"],
        ]);
      }

      return {
        color: "#334155",
        weight: 0.5,
        opacity: 0.65,
        fillColor,
        fillOpacity,
      };
    }

    function rebuildHexLayer() {
      if (hexLayer) map.removeLayer(hexLayer);
      hexLayer = L.geoJSON(hexData, {
        style: getHexStyle,
        onEachFeature: (feature, layer) => {
          layer.on("click", () => {
            if (reportMode) return;
            selectedHex = feature.properties;
            renderSelectedHex();
          });
        },
      }).addTo(map);
    }

    function markerPopup(report) {
      const dots = "🔴".repeat(report.intensity) + "⚪".repeat(5 - report.intensity);
      return `
        <div style="background:#ffffff;color:#1e293b;padding:12px;border-radius:8px;min-width:180px;border:1px solid #e2e8f0;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
          <div style="font-weight:800;font-size:14px;margin-bottom:6px;">${escapeHtml(report.type)}</div>
          <div style="font-size:12px;color:#64748b;margin-bottom:4px;">📍 ${escapeHtml(report.desc)}</div>
          <div style="font-size:12px;color:#64748b;">🕐 ${escapeHtml(report.time)} · 위험도 ${dots}</div>
        </div>
      `;
    }

    function renderMarkers() {
      markerLayer.clearLayers();
      reports.forEach((report) => {
        const meta = TYPE_META[report.type] || { icon: "⚠️" };
        const isNew = report.id === lastSubmittedReportId;
      const [bg, fg] = confidenceColor(selectedHex.confidence);
      els.selectedHexSection.style.display = "block";
      els.selectedHexBody.innerHTML = `
        ${metricRow("기본 위험도", `${(selectedHex.prior * 100).toFixed(0)}%`, "var(--muted)")}
        ${metricRow("신고 기반 위험도", `${(selectedHex.likelihood * 100).toFixed(0)}%`, "var(--accent)")}
        ${metricRow(
          "최종 위험도",
          `${(selectedHex.posterior * 100).toFixed(0)}%`,
          selectedHex.posterior > 0.5 ? "var(--danger)" : "var(--warning)"
        )}
        ${metricRow(
          "위험도 변화",
          `${selectedHex.variation > 0 ? "↑ +" : "↓ "}${Math.abs(selectedHex.variation * 100).toFixed(0)}%`,
          selectedHex.variation > 0.15 ? "var(--danger)" : "var(--safe)"
        )}
        <div class="analysis-row" style="border-bottom:0;margin-top:4px;">
          <span class="analysis-label">신고 건수</span>
          <span class="analysis-value">${selectedHex.reportCount}건</span>
        </div>
        <div class="analysis-row" style="border-bottom:0;padding-top:2px;">
          <span class="analysis-label">신뢰도</span>
          <span class="pill" style="background:${bg};color:${fg};">${confidenceLabel(selectedHex.confidence)}</span>
        </div>
      `;
      updateStats();
      if (selectedHex) {
        const refreshed = hexData.features.find((feature) => feature.properties.hexId === selectedHex.hexId);
        selectedHex = refreshed ? refreshed.properties : null;
        renderSelectedHex();
      }
    }

    function confidenceLabel(value) {
      if (value === "high") return "높음 (많은 신고)";
      if (value === "medium") return "중간 (적당한 신고)";
      return "낮음 (신고 부족)";
    }

    function confidenceColor(value) {
      if (value === "high") return ["rgba(59,130,246,0.2)", "var(--accent)"];
      if (value === "medium") return ["rgba(245,158,11,0.2)", "var(--warning)"];
      return ["rgba(100,116,139,0.2)", "var(--muted)"];
    }

    function metricRow(label, value, color) {
      return `
        <div class="analysis-row">
          <span class="analysis-label">${label}</span>
          <span class="analysis-value" style="color:${color};">${value}</span>
        </div>
      `;
    }

    function renderSelectedHex() {
      if (!selectedHex) {
        els.selectedHexSection.style.display = "none";
        return;
      }

      const [bg, fg] = confidenceColor(selectedHex.confidence);
      els.selectedHexSection.style.display = "block";
      els.selectedHexBody.innerHTML = `
        ${metricRow("기본 위험도", `${(selectedHex.prior * 100).toFixed(0)}%", "var(--muted)")}
        ${metricRow("신고 기반 위험도", `${(selectedHex.likelihood * 100).toFixed(0)}%", "var(--accent)")}
        ${metricRow(
          "최종 위험도",
          `${(selectedHex.posterior * 100).toFixed(0)}%",
          selectedHex.posterior > 0.5 ? "var(--danger)" : "var(--warning)"
        )}
        ${metricRow(
          "위험도 변화",
          `${selectedHex.variation > 0 ? "↑ +" : "↓ "}${Math.abs(selectedHex.variation * 100).toFixed(0)}%",
          selectedHex.variation > 0.15 ? "var(--danger)" : "var(--safe)"
        )}
        <div class="analysis-row" style="border-bottom:0;margin-top:4px;">
          <span class="analysis-label">신고 건수</span>
          <span class="analysis-value">${selectedHex.reportCount}건</span>
        </div>
        <div class="analysis-row" style="border-bottom:0;padding-top:2px;">
          <span class="analysis-label">신뢰도</span>
          <span class="pill" style="background:${bg};color:${fg};">${confidenceLabel(selectedHex.confidence)}</span>
        </div>
      `;
    }

    function renderLegend() {
      els.legendTitle.textContent = `범례 — ${MAP_MODES[mapMode].label}`;
      if (mapMode === "diagnostic") {
        els.legendBody.innerHTML = `
          <div class="gradient-legend">
            <span style="color:var(--safe);">안전함</span>
            <div class="gradient-bar" style="background:linear-gradient(to right,#10b981,#fbbf24,#f97316,#ef4444,#7f1d1d);"></div>
            <span style="color:var(--danger);">매우 위험</span>
          </div>
        `;
      } else if (mapMode === "uncertainty") {
        els.legendBody.innerHTML = `
          <div class="confidence-legend">
            <div class="confidence-item"><span class="swatch" style="background:#3b82f6;"></span>정보 많음</div>
            <div class="confidence-item"><span class="swatch" style="background:#60a5fa;"></span>정보 적당</div>
            <div class="confidence-item"><span class="swatch" style="background:#1e3a5f;"></span>정보 부족</div>
          </div>
        `;
      } else {
        els.legendBody.innerHTML = `
          <div class="gradient-legend">
            <span style="color:var(--safe);">안전 (0%)</span>
            <div class="gradient-bar" style="background:linear-gradient(to right,#064e3b,#10b981,#fbbf24,#f97316,#ef4444);"></div>
            <span style="color:var(--danger);">위험 (80%+)</span>
          </div>
        `;
      }
    }

    function renderStatus() {
      els.statusDot.style.background = reportMode ? "var(--danger)" : "var(--safe)";
      els.statusDot.style.boxShadow = reportMode ? "0 0 8px var(--danger)" : "0 0 8px var(--safe)";
      els.statusText.textContent = reportMode ? "신고 모드 — 지도를 클릭하세요" : `${MAP_MODES[mapMode].label} 활성`;
    }

    function renderModeButtons() {
      document.querySelectorAll(".mode-button").forEach((button) => {
        button.classList.toggle("active", button.dataset.mode === mapMode);
      });
    }

    function renderReportControls() {
      els.reportModeButton.classList.toggle("cancel", reportMode);
      els.reportModeButton.textContent = reportMode ? "✕ 신고 취소" : "📍 위험 지점 신고하기";
      els.reportHint.style.display = reportMode && !reportForm ? "block" : "none";
      els.reportFormSection.style.display = reportForm ? "block" : "none";

      if (reportForm) {
        els.reportLocation.textContent = `📍 ${reportForm.lat}, ${reportForm.lng}`;
        els.reportType.value = reportForm.type;
        els.reportDesc.value = reportForm.desc;
        renderIntensityButtons();
      }
      renderStatus();
    }

    function renderIntensityButtons() {
      els.intensityButtons.innerHTML = "";
      [1, 2, 3, 4, 5].forEach((value) => {
        const button = document.createElement("button");
        button.className = "intensity-button";
        button.type = "button";
        button.textContent = value;
        const active = reportForm && value <= reportForm.intensity;
        if (active) {
          button.style.background = value >= 4 ? "var(--danger)" : value >= 3 ? "var(--warning)" : "var(--safe)";
        }
        button.addEventListener("click", () => {
          reportForm.intensity = value;
          renderIntensityButtons();
        });
        els.intensityButtons.appendChild(button);
      });
    }

    function startReportMode() {
      reportMode = !reportMode;
      reportForm = null;
      renderReportControls();
    }

    function openReportForm(latlng) {
      reportForm = {
        lng: latlng.lng.toFixed(6),
        lat: latlng.lat.toFixed(6),
        type: "조명 부족",
        intensity: 3,
        desc: "",
      };
      selectedHex = null;
      renderSelectedHex();
      renderReportControls();
    }

    function submitReport() {
      if (!reportForm) return;
      const desc = els.reportDesc.value.trim();
      const now = new Date();
      const time = now.toTimeString().slice(0, 5);
      const newReport = {
        id: reports.length + 1,
        lng: parseFloat(reportForm.lng),
        lat: parseFloat(reportForm.lat),
        type: reportForm.type,
        intensity: reportForm.intensity,
        time,
        desc: desc || "주민 신고",
      };
      reports = reports.concat(newReport);
      lastSubmittedReportId = newReport.id;
      reportMode = false;
      reportForm = null;
      // persist
      try { localStorage.setItem("pgis_reports", JSON.stringify(reports)); } catch (e) { console.warn("save failed", e); }
      recompute();
      renderReportControls();
    }

    function exportReportsCSV() {
      if (!reports || reports.length === 0) return;
      const header = ["id","lng","lat","type","intensity","time","desc"];
      const rows = reports.map(r => header.map(h => JSON.stringify(r[h] ?? "")).join(","));
      const csv = [header.join(",")].concat(rows).join("\n");
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `pgis_reports_${new Date().toISOString().slice(0,10)}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }

    Object.keys(TYPE_META).forEach((type) => {
      const option = document.createElement("option");
      option.value = type;
      option.textContent = `${TYPE_META[type].icon} ${type}`;
      els.reportType.appendChild(option);
    });

    document.querySelectorAll(".mode-button").forEach((button) => {
      button.addEventListener("click", () => {
        mapMode = button.dataset.mode;
        renderModeButtons();
        renderLegend();
        renderStatus();
        if (hexLayer) hexLayer.setStyle(getHexStyle);
      });
    });

    els.reportModeButton.addEventListener("click", startReportMode);
    els.exportReports.addEventListener("click", exportReportsCSV);
    els.submitReport.addEventListener("click", submitReport);
    els.closeReportForm.addEventListener("click", () => {
      reportForm = null;
      renderReportControls();
    });
    els.closeHexInfo.addEventListener("click", () => {
      selectedHex = null;
      renderSelectedHex();
    });
    els.reportType.addEventListener("change", () => {
      if (reportForm) reportForm.type = els.reportType.value;
    });
    els.reportDesc.addEventListener("input", () => {
      if (reportForm) reportForm.desc = els.reportDesc.value;
    });
    els.togglePanel.addEventListener("click", () => {
      sideOpen = !sideOpen;
      els.sidePanel.classList.toggle("closed", !sideOpen);
      els.togglePanel.classList.toggle("closed", !sideOpen);
      els.togglePanel.textContent = sideOpen ? "‹" : "›";
      setTimeout(() => map.invalidateSize(), 320);
    });

    map.on("click", (event) => {
      if (reportMode) openReportForm(event.latlng);
    });

    recompute();
    renderModeButtons();
    renderLegend();
    renderReportControls();
    renderSelectedHex();
    setTimeout(() => map.invalidateSize(), 200);
  </script>
  <script>
    function showOverlay(msg) {
      let el = document.getElementById('pgisErrorOverlay');
      if (!el) {
        el = document.createElement('div');
        el.id = 'pgisErrorOverlay';
        Object.assign(el.style, {
          position: 'fixed',
          left: '8px',
          top: '8px',
          right: '8px',
          maxHeight: '40vh',
          overflow: 'auto',
          background: 'rgba(0,0,0,0.8)',
          color: '#fff',
          zIndex: 99999,
          padding: '12px',
          fontSize: '13px',
          borderRadius: '8px',
        });
        document.body.appendChild(el);
      }
      el.textContent = String(msg);
    }
    window.addEventListener('error', function (e) {
      showOverlay('Error: ' + (e && e.message) + ' (at ' + (e && e.filename) + ':' + (e && e.lineno) + ')');
    });
    window.addEventListener('unhandledrejection', function (e) {
      showOverlay('Unhandled promise rejection: ' + (e && e.reason && (e.reason.message || e.reason)));
    });
  </script>
</body>
</html>
"""

html_payload = APP_HTML.replace("__MAPBOX_TOKEN__", json.dumps(MAPBOX_TOKEN)).replace(
  "__INITIAL_REPORTS__", json.dumps(initial_reports) if initial_reports is not None else "null"
)

# Try to use components.html when available and working; otherwise serve the HTML
# via a local HTTP server and embed with st.iframe to avoid srcdoc/data URL issues.
served_ok = False
if _HAS_COMPONENTS:
  try:
    components.html(html_payload, height=900, scrolling=False)
    served_ok = True
  except Exception:
    served_ok = False

if not served_ok:
  # Direct render using st.markdown with unsafe_allow_html
  try:
    st.markdown(html_payload, unsafe_allow_html=True)
  except Exception as e:
    st.error(f"앱 렌더링 오류: {e}")
