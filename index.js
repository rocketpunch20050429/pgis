
import { Html, Head, Main, NextScript } from "next/document"
export default function Document() {
  return (
    <Html lang="ko">
      <Head>
        <link href="https://api.mapbox.com/mapbox-gl-js/v3.4.0/mapbox-gl.css" rel="stylesheet"/>
        <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" rel="stylesheet"/>
      </Head>
      <body><Main /><NextScript /></body>
    </Html>
  )
}
