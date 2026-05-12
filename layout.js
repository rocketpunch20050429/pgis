import "./globals.css"
export const metadata = {
  title: "마을 안전 사각지대 예측 지도",
  description: "베이지안 추론 기반 생활 안전 사각지대 동적 예측 및 PGIS 매핑 시스템",
}
export default function RootLayout({ children }) {
  return (
    <html lang="ko"><head>
      <link href="https://api.mapbox.com/mapbox-gl-js/v3.4.0/mapbox-gl.css" rel="stylesheet"/>
      <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" rel="stylesheet"/>
    </head><body>{children}</body></html>
  )
}
