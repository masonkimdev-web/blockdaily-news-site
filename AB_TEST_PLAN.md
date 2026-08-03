# Blockchain Guide A/B Test Plan

## 공통 원칙

- 실험 대상은 Hero, CTA, 고지, FAQ 같은 가이드 주변 전환 구조로 제한한다.
- 기존 10개 가이드 섹션, 14개 단계, 설명과 14개 단계 이미지는 실험하지 않는다.
- Primary metric: referral CTA click-through rate(고유 세션 기준 `binance_cta_click` / `blockchain_guide_view`)
- Guardrail: bounce rate, engagement time, scroll depth, 페이지 성능(Core Web Vitals 포함), 광고 정책 위반 가능성
- 한 번에 하나의 핵심 가설을 검증하고 광고 캠페인/기기 비중을 Variant 간 균등하게 배분한다.

## 1. Hero 제목

- 가설: “바이낸스 가입방법”을 제목 첫머리에 두면 검색·광고 의도 일치가 높아져 CTA CTR이 증가한다.
- Control: `바이낸스 가입방법: 계정 생성부터 본인인증까지`
- Variant: `바이낸스 회원가입 가이드: KYC와 OTP 설정까지`
- Primary metric: Hero 및 전체 referral CTA CTR
- Guardrail metric: bounce rate, engagement time, 광고 정책 위반 검토
- 성공 판단 기준: 최소 표본/실험 기간 충족 후 Variant CTR이 Control 대비 통계적으로 유의하게 증가하고 guardrail이 5% 이상 악화되지 않음

## 2. Hero 설명

- 가설: 새 창에서 가입 화면과 가이드를 함께 보라는 행동 지침이 불확실성을 낮춘다.
- Control: 현재의 과정 범위와 새 창 병행 안내
- Variant: 첫 문장에 “가입 화면을 새 창으로 먼저 여세요”를 배치
- Primary metric: Hero CTA CTR
- Guardrail metric: bounce rate, engagement time, scroll depth
- 성공 판단 기준: Hero CTA CTR 유의 상승, 가이드 25% 스크롤 도달률 비열세

## 3. Hero CTA 문구

- 가설: “따라 하기” 문구가 단순 이동 문구보다 클릭 후 행동을 구체화한다.
- Control: `바이낸스 가입 화면 열고 따라 하기`
- Variant: `바이낸스 가입 페이지에서 시작하기`
- Primary metric: `cta_location=hero` CTA CTR
- Guardrail metric: 즉시 이탈, engagement time, 광고 정책 위반 가능성
- 성공 판단 기준: Hero CTR 유의 상승 및 outbound 클릭 후 페이지 참여 지표 비열세

## 4. Hero CTA 위치

- 가설: 과정 설명 바로 다음에 CTA를 배치하면 링크 성격을 이해한 사용자의 클릭이 늘어난다.
- Control: 현재 Hero 카드 하단 CTA
- Variant: Hero 설명 직후, 과정 배지 앞 CTA
- Primary metric: Hero CTA CTR
- Guardrail metric: 가이드 시작 도달률, CLS, 모바일 LCP
- 성공 판단 기준: CTR 상승, CLS/LCP가 운영 성능 예산을 벗어나지 않음

## 5. 모바일 sticky CTA

- 가설: 닫을 수 있는 모바일 하단 CTA가 긴 본문에서 추천 링크 복귀를 늘린다.
- Control: sticky CTA 없음
- Variant: 현재의 모바일 전용 sticky CTA(최종 CTA 도달 시 숨김)
- Primary metric: 모바일 전체 referral CTA CTR 및 `cta_location=sticky` 기여도
- Guardrail metric: bounce rate, engagement time, scroll depth, 모바일 INP/CLS
- 성공 판단 기준: 모바일 전체 CTR 유의 상승, engagement/성능 guardrail 5% 이상 악화 없음

## 6. 제휴 고지 위치

- 가설: CTA 바로 아래의 짧은 고지는 투명성을 높이면서 클릭 방해를 최소화한다.
- Control: Hero CTA 바로 아래 고지
- Variant: Hero 설명과 CTA 사이 고지
- Primary metric: 전체 referral CTA CTR
- Guardrail metric: bounce rate, 광고 정책 위반 가능성, FAQ의 추천인 질문 열림률
- 성공 판단 기준: CTR 비열세 범위 내에서 정책/신뢰 검토 통과

## 7. FAQ 순서

- 가설: 가입 비용·추천 링크 질문을 먼저 보여주면 CTA 직전 불안을 더 빠르게 해소한다.
- Control: 가입 비용 → 본인인증 → 추천 링크 → 원화 입금 → OTP → 가이드 병행 → 거래 시점
- Variant: 추천 링크 → 가입 비용 → 본인인증 → OTP → 원화 입금 → 가이드 병행 → 거래 시점
- Primary metric: FAQ 노출 세션의 final CTA CTR
- Guardrail metric: FAQ open rate, engagement time, 최종 CTA 도달률
- 성공 판단 기준: final CTA CTR 유의 상승, FAQ 도달률 및 engagement time 비열세

## 운영 조건

- 통계 검정 방식, MDE, 최소 표본 수는 현재 트래픽과 baseline CTR을 수집한 뒤 확정한다.
- 신규 실험 도구 설치 없이 기존 광고/분석 플랫폼의 실험 기능을 우선 사용한다.
- 유효한 결론 전에는 여러 Variant를 동시에 영구 적용하지 않는다.
