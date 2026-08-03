# Blockchain Guide Conversion Audit

## 범위와 기준선

- 운영 참고 URL: `https://blockdailynews.online/blockchain-guide/`
- 확인 방식: 운영 URL 직접 열기는 도구의 안전 제한으로 실패했으며, 검색 엔진에 색인된 운영 페이지와 로컬 Hugo 소스/렌더 결과를 함께 검토했다.
- 실제 수정 대상: `content/blockchain-guide/_index.md`, `layouts/blockchain-guide/list.html` 주변 전환 구조
- 기존 추천 URL: `https://accounts.binance.com/register?ref=BLOCKDNEWS`
- 가이드 본문 기준선: 10개 번호 섹션, 14개 세부 단계, 14개 단계 이미지
- 불변 본문 범위: `## 1. 바이낸스 거래소란?`부터 `<!-- 로고 -->` 직전까지
- 불변 본문 SHA-256(개행 정규화): `8145953a578e841efaf6da5fcd0f65f78a35f0b517382b23181512e7c2bee85c`

단계 제목, 설명, 이미지 경로, 이미지 순서, alt와 단계-이미지 연결은 `tests/fixtures/blockchain-guide-baseline.json`에 기록했다. 기존 가이드 본문 자체는 개선 대상으로 제안하지 않는다.

## 로컬 구조 분석

- `/blockchain-guide/` 라우트: `content/blockchain-guide/_index.md`
- 페이지 레이아웃: `layouts/blockchain-guide/list.html`
- 하위 가이드 레이아웃: `layouts/blockchain-guide/single.html`
- Hero 및 기존 CTA: `_index.md` 안의 HTML 블록과 `layouts/partials/binance_cta.html`
- 추천 URL 선언: `_index.md`, guide 레이아웃 및 관련 가이드 문서에 직접 선언
- 단계/이미지 데이터: 별도 배열이 아니라 `_index.md` Markdown 제목·문단·인라인 `<img>`가 문서 순서대로 연결
- FAQ/FAQPage: 작업 전 대상 라우트에는 없음
- SEO: 작업 전 전용 레이아웃에는 title, description, robots만 있고 canonical/OG/Twitter/구조화 데이터가 없음
- 분석: 저장소에서 GA4/GTM/analytics helper를 찾지 못함
- 모바일 sticky CTA: 공용 partial 기반 링크가 있었으나 닫기, 위치값, 노출/클릭 추적, 마지막 CTA 도달 시 숨김이 없음
- 쿠키 배너: 대상 레이아웃과 공용 partial에서 구현을 찾지 못함

## 문제별 감사

| 문제 | 근거 | 전환 영향 | 심각도 | 수정 가능한 영역 | 관련 파일 |
|---|---|---|---|---|---|
| 검색 의도와 Hero 메시지 불일치 | H1이 “비트코인 하는법 1단계” 중심이고 가입 과정의 범위가 즉시 드러나지 않음 | 광고 문구와 랜딩 메시지의 연속성이 낮아 초기 이탈 가능 | 높음 | Hero/H1 | `content/blockchain-guide/_index.md` |
| CTA 행동과 외부 이동이 불명확 | 할인 주장 중심 문구이며 새 창/외부 페이지/가이드 병행 행동 안내가 약함 | 클릭 전 불확실성과 이탈 증가 | 높음 | Hero 및 보조 CTA | `_index.md`, `layouts/blockchain-guide/list.html` |
| 검증되지 않은 혜택 표현 | “20% 평생 할인”, “자동 적용”을 단정하지만 로컬에 공식 근거 없음 | 신뢰와 광고 정책 위험 | 높음 | CTA 주변 문구 | `_index.md`, guide layout |
| 제휴 관계 고지 부족 | 첫 CTA 근처에 운영자 수익 가능성 고지가 없음 | 사용자의 정보 비대칭 및 신뢰 저하 | 높음 | Hero/최종 CTA | `_index.md`, guide layout |
| 위험 안내가 일반적임 | 투자 권유가 아니라는 문구만 있고 변동성·원금손실·가입과 투자 구분이 없음 | 금융 콘텐츠 신뢰와 정책 적합성 저하 | 중간 | Hero 아래/최종 영역 | `_index.md`, guide layout |
| 시작 전 인지 부담 | 준비물과 전체 흐름, 첫 행동이 한 블록에 정리돼 있지 않음 | 시작 지연과 스크롤 이탈 | 중간 | 가이드 직전 요약 | `_index.md` |
| 긴 본문 중 복귀 경로 부족 | 계정 생성 후 직접 추천 링크 CTA가 없음 | 가입 탭을 닫은 사용자의 재진입 손실 | 중간 | 섹션 사이 독립 CTA | guide layout |
| FAQ 및 구조화 데이터 없음 | 가입 비용, KYC, OTP, 원화 입금 등 사전 불안을 해소하는 별도 영역이 없음 | CTA 직전 망설임 해소 기회 손실 | 중간 | 가이드 뒤 FAQ | FAQ data, guide layout |
| CTA 분석 위치값 없음 | CTA별 `hero/before_guide/middle/final/sticky` 구분과 이벤트가 없음 | 개선 효과 및 광고 유입별 성과를 판단할 수 없음 | 높음 | analytics helper | guide layout |
| GA/GTM 태그 부재 | 저장소 검색에서 GA4/GTM 설치를 확인하지 못함 | 이벤트 코드가 있어도 수집 대상 설정 전에는 보고서에 나타나지 않음 | 높음 | 배포 설정/GTM | 저장소 외 운영 설정 필요 |
| 모바일 sticky 방해 가능성 | 닫기 버튼과 최종 CTA 교차 숨김이 없음 | 콘텐츠 가림과 사용자 불편 | 중간 | 모바일 sticky | guide layout |
| SEO 공유 메타/구조화 데이터 부족 | canonical, OG, Twitter, BreadcrumbList, FAQPage 없음 | 검색/공유 결과 품질 저하 | 중간 | `<head>` | guide layout |
| 이미지 레이아웃 이동 가능성 | 단계 이미지에 고유 크기 예약과 lazy/decoding 힌트가 없음 | CLS 및 모바일 읽기 흐름 저하 | 중간 | 렌더 속성/CSS | guide layout |
| 전체 빌드 재현성 문제 | 테마 서브모듈 디렉터리가 비어 `meta.html` partial을 찾지 못함 | CI/로컬 전체 빌드 실패 | 높음 | 저장소 환경 | `.gitmodules`, `themes/hugo-xmag` |

## 측정 한계

페이지는 추천 링크 클릭까지만 관찰할 수 있다. 바이낸스 가입 완료, KYC 완료, 첫 입금은 외부 도메인의 전환이므로 Affiliate dashboard, Binance가 제공하는 postback 또는 허용된 서버 간 연동 없이는 이 프로젝트만으로 측정할 수 없다.
