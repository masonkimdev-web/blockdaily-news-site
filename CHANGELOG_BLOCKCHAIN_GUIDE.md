# Blockchain Guide Conversion Changelog

## 분석한 전환 문제

- 광고 키워드와 기존 Hero H1/설명의 메시지 연결이 약했다.
- CTA가 클릭 후 외부 페이지·새 창 이동과 가이드 병행 행동을 충분히 설명하지 않았다.
- 공식 근거가 로컬에 없는 할인율·평생 혜택 표현이 신뢰 및 정책 위험을 만들었다.
- 첫 CTA 주변 제휴 고지, 구체적인 위험 고지, 시작 전 준비물/흐름 안내가 부족했다.
- 긴 본문 중간 복귀 CTA와 질문 해소용 FAQ가 없었다.
- CTA 위치별 전환 이벤트와 UTM 문맥 보존이 없었다.
- 전용 canonical, OG/Twitter, BreadcrumbList, FAQPage가 없었다.
- 기존 모바일 sticky CTA는 닫기와 마지막 CTA 교차 숨김, 위치별 추적이 없었다.

자세한 근거와 심각도는 `CONVERSION_AUDIT.md`에 기록했다.

## 수정한 파일

- `.gitignore`: 로컬 빌드 결과인 `output/` 제외
- `content/blockchain-guide/_index.md`: Hero, 제휴/위험 안내, 시작 전 요약, Hero/시작 CTA, SEO front matter
- `layouts/blockchain-guide/list.html`: SEO/JSON-LD, 중간·최종·모바일 CTA, FAQ, 분석, 접근성/반응형/성능 스타일
- `data/blockchain_guide_faq.json`: 화면과 FAQPage JSON-LD의 공용 질문/답변
- `tests/fixtures/blockchain-guide-baseline.json`: 기존 가이드 기준선
- `scripts/verify-blockchain-guide.ps1`: 불변 조건 및 렌더 결과 자동 검증
- `CONVERSION_AUDIT.md`: 전환 감사
- `AB_TEST_PLAN.md`: 가이드 외부 요소 A/B 테스트 계획
- `CHANGELOG_BLOCKCHAIN_GUIDE.md`: 본 변경 기록

## Hero 변경

- H1을 `바이낸스 가입방법: 계정 생성부터 본인인증까지`로 바꿔 검색 의도와 안내 범위를 일치시켰다.
- 계정 생성, 본인인증(KYC), OTP 보안 설정까지 안내한다는 짧은 설명을 추가했다.
- 새 창에서 바이낸스 외부 가입 페이지를 열고 가이드와 함께 진행하는 행동을 명확히 했다.
- 검증 근거가 없는 `20% 평생 할인`, 자동 적용, 완료 시간 단정 표현을 Hero에서 제거했다.

## CTA 변경

- 모든 전환 CTA가 기존 URL `https://accounts.binance.com/register?ref=BLOCKDNEWS`를 그대로 사용한다.
- 위치값은 `hero`, `before_guide`, `middle`, `final`, `sticky` 다섯 개로 제한했다.
- 중간 CTA는 계정 생성 관련 섹션이 끝난 뒤 DOM의 독립된 보조 블록으로 삽입한다. 기존 제목, 문단, 이미지 노드는 이동하지 않는다.
- 외부 링크에 `target="_blank"`, `noopener`, `noreferrer`, `nofollow`, `sponsored`를 적용했다.

## 제휴 및 위험 고지

- 첫 CTA 바로 아래에 추천인 링크를 통한 운영자 제휴 수익 가능성을 표시했다.
- 최종 CTA에도 짧은 제휴 고지를 반복해 링크 성격을 투명하게 유지했다.
- Hero 아래에 가격 변동성, 원금 손실 가능성, 가입과 투자 구분, 입금/거래 전 수수료·위험 확인을 안내했다.
- 수익 보장, 조급성 유발, 공식 사이트로 오인할 표현을 추가하지 않았다.

## FAQ 변경

- 가입 비용, KYC 목적, 추천 링크, 원화 입금, OTP, 새 탭 병행, 가입 후 거래 시점 등 7개 FAQ를 추가했다.
- 정책 변동 가능성이 있는 답변은 가입 시점의 바이낸스 화면을 확인하도록 작성했다.
- 화면 FAQ와 FAQPage JSON-LD가 `data/blockchain_guide_faq.json`을 함께 사용하므로 내용이 일치한다.

## 모바일 변경

- 모바일 전용 하단 CTA에 safe area 여백, 48px 이상 터치 영역, 접근 가능한 이름과 닫기 버튼을 적용했다.
- 최종 CTA가 화면에 들어오면 sticky CTA를 숨긴다.
- 모바일 본문 글자 크기, 줄 높이, 제목 크기, 이미지 반응형 동작을 개선했다.
- 저장소에서 쿠키 배너 구현을 찾지 못해 실환경의 별도 삽입형 배너와 충돌 여부는 배포 후 확인해야 한다.

## Analytics 이벤트

- `blockchain_guide_view`
- `binance_cta_impression`
- `binance_cta_click`
- `outbound_referral_click`
- `faq_open`

공통으로 `page_path`, 다섯 UTM 값을 포함하며 CTA 이벤트에는 `cta_location`, `cta_text`, 최소 목적지 식별값 `accounts.binance.com/register`가 추가된다. 유입 UTM은 `sessionStorage`에 보존한다. 이메일, 전화번호, 계정 입력값은 읽거나 전송하지 않는다. `gtag`가 있으면 재사용하고, 없으면 `dataLayer`에 적재한다. 분석 오류는 예외 처리하며 링크 기본 이동을 막지 않는다.

저장소에는 GA4/GTM 태그가 없으므로 배포 환경에서 실제 GA4 태그 또는 GTM 컨테이너와 이벤트 수집 설정을 연결해야 보고서에 쌓인다. 외부 도메인의 가입 완료, KYC 완료, 첫 입금은 구현하지 않았으며 Affiliate dashboard 또는 별도 postback 연동이 필요하다.

## SEO 변경

- 검색 의도 중심 title, description 및 단일 H1
- 정확한 canonical `https://blockdailynews.online/blockchain-guide/`
- Open Graph 및 Twitter card
- 화면과 일치하는 FAQPage JSON-LD
- 홈 → 바이낸스 가입방법 BreadcrumbList JSON-LD
- `index,follow` 유지 및 기존 Hugo sitemap/robots 생성 구조 확인
- 기존의 “다음 단계” 내부 링크 유지

## 성능과 접근성 변경

- Hero 로고에 width/height, async decoding, fetch priority 적용
- 기존 14개 단계 이미지는 렌더 시에만 `loading="lazy"`, `decoding="async"` 속성을 보완하고 소스 경로/순서/배치는 유지
- 단계 이미지에 비율 예약과 `object-fit: contain`을 적용해 핵심 화면을 자르지 않고 레이아웃 이동을 줄임
- 키보드 focus 표시, 검색 input 이름, FAQ native details/summary, sticky CTA 접근 가능한 이름 적용
- `prefers-reduced-motion` 대응

## 실행한 테스트와 결과

| 검사 | 명령 | 결과 |
|---|---|---|
| production build | `hugo --destination output --minify` | 통과: 503 pages, 140 static files. 결과는 Git 제외된 `output/`에 저장 |
| 가이드 불변/CTA/SEO/FAQ/분석 검사 | `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify-blockchain-guide.ps1 -PublicRoot output` | 통과 |
| 브라우저 JS 문법 | 렌더된 일반 script를 `node --check -`로 검사 | 통과 |
| lint/typecheck | 해당 명령/설정 없음 | 실행하지 않음 |
| 별도 unit/integration framework | 해당 설정 없음 | 실행하지 않음. PowerShell 검증 스크립트로 대체 |

첫 빌드에서는 체크아웃되지 않은 `themes/hugo-xmag` 서브모듈 때문에 `meta.html` partial 누락 오류가 발생했다. 저장소가 지정한 커밋 `25609bf12d6186e7c8cce4e06ec3eef0b5d023f3`으로 서브모듈을 초기화한 뒤 같은 전체 빌드를 다시 실행해 통과했다.

## 가이드 본문 및 이미지 불변 검증

- 불변 범위: `## 1. 바이낸스 거래소란?`부터 `<!-- 로고 -->` 직전
- SHA-256: `8145953a578e841efaf6da5fcd0f65f78a35f0b517382b23181512e7c2bee85c` 일치
- 번호 섹션: 10개, 제목과 순서 일치
- 세부 단계: 14개, 제목과 순서 일치
- 기존 단계별 본문: 전체 구간 해시로 byte-level(개행 정규화) 일치 확인
- 기존 단계 이미지: 14개, 경로·순서·alt 일치
- 이미지와 설명 연결: Markdown 문서 순서 및 전체 구간 해시 일치로 보존 확인
- KYC, OTP, 이메일 인증, 비밀번호 안내와 기존 주의사항: 변경 없음

## 사람이 확인해야 할 바이낸스 정책

- 추천인 코드 `BLOCKDNEWS`가 현재 유효한지와 표시되는 적용 조건
- 추천 링크에 실제로 제공되는 혜택, 대상 상품, 기간 및 지역 제한
- 한국 거주자의 신규 가입 및 서비스 이용 가능 범위
- 현재 KYC 필수 범위와 허용 신분증
- 원화 및 지원 결제/입금 수단
- 현물/선물/입출금 수수료와 OTP 요구 조건
- 제휴 고지 문구가 Binance affiliate 약관 및 광고 매체 정책을 충족하는지

## 배포 후 확인할 지표

- 전체 및 `cta_location`별 referral CTA CTR
- 광고 캠페인/키워드 UTM별 CTA CTR
- Hero CTA 대비 before/middle/final/sticky 기여도
- CTA impression → click 전환율
- FAQ open rate와 FAQ 노출 세션의 final CTA CTR
- bounce rate, engagement time, 25/50/75/100% scroll depth
- 모바일/데스크톱별 CTR과 sticky 닫기율
- LCP, CLS, INP 및 JS 오류
- Affiliate dashboard의 가입 전환과 사이트 outbound click 간 차이
