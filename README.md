# 🗺️ 마을 안전 사각지대 예측 지도

**베이지안 추론 기반 생활 안전 사각지대 동적 예측 및 PGIS 매핑 시스템**

## 시작하기

### 1. Mapbox 토큰 설정
[Mapbox](https://mapbox.com)에서 무료 계정 생성 후 Access Token을 발급받으세요.

`.env.local` 파일에 토큰을 입력:
```
NEXT_PUBLIC_MAPBOX_TOKEN=pk.eyJ1...실제토큰
```

### 2. 설치 및 실행
```bash
npm install
npm run dev
```

### 3. Vercel 배포
```bash
npx vercel
```
Vercel 대시보드 > Settings > Environment Variables에서 `NEXT_PUBLIC_MAPBOX_TOKEN`을 설정하세요.

## 주요 기능
- 🗺️ **진단 지도**: Prior 대비 Posterior 편차로 안전 사각지대 도출
- 📊 **신뢰도 지도**: 데이터 밀도 기반 통계적 신뢰도 시각화
- 📍 **위험 신고**: 주민 참여형 PGIS 데이터 수집
- 🔄 **실시간 베이즈 업데이트**: 신고 즉시 확률 재계산

## 기술 스택
Next.js 14 · Mapbox GL JS · Turf.js · Vercel
