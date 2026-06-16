사용자 가이드 — PGIS Streamlit 앱

요약
- 지도에서 직접 신고 입력(클릭) 가능
- 신고는 브라우저 `localStorage`에 저장되어 세션 간 보존됨
- 사이드바에서 신고 내역을 CSV로 내보낼 수 있음
- 서버에 영구 저장하려면 CSV/JSON 파일을 업로드하면 `reports.json`으로 저장됨

실행
```powershell
cd c:\pgis\pgis
pip install -r requirements.txt
streamlit run app.py
```

주요 흐름
1. `📍 위험 지점 신고하기` 버튼을 클릭합니다.
2. 지도에서 신고할 지점을 클릭합니다.
3. 신고 폼에서 유형/강도/설명을 입력하고 `신고 제출`을 클릭합니다.
   - 제출 시 브라우저 `localStorage`에 자동 저장됩니다.
   - 제출 직후 지도와 통계가 갱신됩니다.
4. `⬇️ 신고 내역 내보내기` 버튼을 눌러 현재 로컬에 저장된 신고들을 CSV로 다운로드합니다.

서버에 저장하기
- 사이드바 상단의 업로더에 CSV 또는 JSON 파일을 업로드하면 서버쪽 파일 `reports.json`에 저장됩니다.
- 업로드 후 페이지를 새로고침하면 업로드한 데이터가 초기 데이터로 로드됩니다.
- `reports.json` 경로: 앱 루트 폴더의 `reports.json` (예: `c:\pgis\pgis\reports.json`).

로컬 데이터 초기화
- 브라우저 저장된 신고를 지우려면 브라우저 개발자 도구 -> Application -> Local Storage -> `pgis_reports` 삭제.
- 서버 저장을 초기화하려면 `reports.json` 파일을 삭제하거나 빈 배열 `[]`로 덮어쓰기하세요.

개발자 노트
- Mapbox 토큰: 환경변수 `MAPBOX_TOKEN` 또는 `NEXT_PUBLIC_MAPBOX_TOKEN` 사용 가능. 미설정 시 Carto 기본 타일을 사용합니다.
- 거리 계산: 내부에서 Turf의 거리 단위를 `kilometers`로 사용하며, 근접 판단 기준은 80m(0.08km)입니다.

문의 및 확장 제안
- 실시간 서버 동기화가 필요하면 간단한 `POST /reports` API를 추가해 iframe에서 호출하여 서버 저장을 자동화할 수 있습니다.
- 인증된 사용자 신고 기능(로그인)과 관리 페이지(신고 승인/편집)도 확장 가능합니다.
