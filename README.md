# pgis

Streamlit app for Railway.

## 🚀 주요 기능

- **대화형 지도**: Leaflet 기반 서울 안전 위험 지도
- **개별 신고**: 지도 클릭으로 위험 지점 신고
- **대량 데이터 업로드**: CSV/Excel 파일로 한 번에 여러 위험 요소 업로드
- **베이지안 분석**: 공공데이터 + 주민신고 기반 위험도 계산
- **실시간 지도 업데이트**: 신고 즉시 지도에 반영

## 📤 데이터 업로드 기능

위험 요소(싱크홀, 가로등 파손 등) 데이터를 CSV 또는 Excel 파일로 대량 업로드할 수 있습니다.

**필수 정보:**
- 위도, 경도 (서울 범위)
- 위험 유형 (조명 부족, 시야 차단, 도로 파손, 불법 주정차)
- 위험도 (1~5)

자세한 사항은 [데이터 업로드 가이드](UPLOAD_GUIDE.md)를 참고하세요.

## 🛠️ 설치 및 실행

Railway start command:

```bash
python -m streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.headless=true --browser.gatherUsageStats=false
```

## 📋 요구사항

- Python 3.8+
- Streamlit >= 1.35
- Pandas >= 2.0
- openpyxl >= 3.0

설치:
```bash
pip install -r requirements.txt
```

## 🚀 배포 (Railway)

Deploy notes:

- Keep `app.py`, `requirements.txt`, `railway.json`, `Procfile`, and `.python-version` in the project root.
- In Railway, generate a public domain from Settings > Networking > Public Networking.
- Optional: set `MAPBOX_TOKEN` or `NEXT_PUBLIC_MAPBOX_TOKEN` in Railway variables. Without it, the app falls back to Carto map tiles.
