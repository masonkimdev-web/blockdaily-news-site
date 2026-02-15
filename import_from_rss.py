import os
import re
import json
from datetime import datetime
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

# ===== 환경 변수(.env) 로드 & OpenAI 클라이언트 =====
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ===== 설정 =====
# 예: https://your-wp-site.com/wp-json/wp/v2/posts
WP_API_BASE = os.getenv("WP_API_BASE")

CONTENT_BASE = "content/news"
IMAGE_BASE = "static/images/news"

DEFAULT_CATEGORY = "블록체인"      # 카테고리 고정
TIME_SUFFIX = "T09:00:00+09:00"    # 한국 시간 기준 고정

MAX_POSTS = 10                    # 최대 가져올 포스트 수
PER_PAGE = 1                      # WP API per_page (최대 100)
# =========================


def slugify(text: str) -> str:
    """제목 기반 slug 생성 (한글+영문+숫자만, 공백은 -)"""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9가-힣\- ]", "", text)
    text = text.replace(" ", "-")
    return text[:60]


def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def clean_html_to_markdown(html: str) -> str:
    """본문 HTML → 최소한의 마크다운/텍스트로 정리"""
    soup = BeautifulSoup(html, "html.parser")

    # br/hr 을 줄바꿈으로
    for br in soup.find_all(["br", "hr"]):
        br.replace_with("\n")

    text = soup.get_text("\n")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n\n".join(lines)


def extract_first_image_from_html(
    html: str, base_url: str | None = None
) -> str | None:
    """content.rendered 안에 <img>가 있을 경우 첫 번째 이미지 src 반환"""
    soup = BeautifulSoup(html, "html.parser")
    img = soup.find("img")
    if img and img.get("src"):
        src = img["src"]
        if base_url and (src.startswith("/") or not src.startswith("http")):
            return urljoin(base_url, src)
        return src
    return None


def extract_featured_image_from_post(
    post: dict, content_html: str, base_url: str | None = None
) -> str | None:
    """
    대표 이미지 URL 추출:
    1순위: REST API의 _embedded.wp:featuredmedia.source_url
    2순위: content.rendered 안의 첫 번째 <img>
    """
    try:
        embedded = post.get("_embedded", {})
        media_list = embedded.get("wp:featuredmedia")
        if isinstance(media_list, list) and media_list:
            media = media_list[0]
            url = media.get("source_url")
            if not url:
                url = (
                    media.get("media_details", {})
                    .get("sizes", {})
                    .get("full", {})
                    .get("source_url")
                )
            if url:
                return url
    except Exception:
        pass

    # fallback: content 안에서 <img> 찾기
    return extract_first_image_from_html(content_html, base_url)


def rewrite_with_openai(title: str, content: str) -> tuple[str, str, str, list[str]]:
    """
    참고 텍스트를 바탕으로 블로그형 칼럼(약 1000자) 생성
    - title: 제목(앞에 [바이낸스] 자동)
    - summary: 2~3문장 요약
    - body: 본문(약 900~1100자)
    - tags: 태그 리스트(최대 8개)
    """
    prompt = f"""
너는 '블록체인 공부 기록 블로그'의 글쓴이야.
아래 텍스트는 참고자료일 뿐이며, 원문을 재작성/의역/요약해서는 안 돼.
반드시 **내가 직접 생각해서 쓴 블로그 글**처럼 완전히 새로 작성해줘.

[참고 제목]
{title}

[참고 내용]
{content}

✅ 작성 목표(아주 중요)
- 결과물은 "블로그 글"이며, 기자/뉴스/리포트 문체 금지
- '발표했다/전망된다/밝혔다/관계자' 같은 뉴스 표현 금지
- 문장 구조를 원문과 완전히 다르게(원문 문장 그대로 사용 금지)
- 내가 공부하면서 떠올린 질문/생각/관점을 1인칭으로 자연스럽게 포함
- 과장, 확정적 단정, 선동적 표현 금지

✅ 분량
- 본문은 **공백 제외 약 1000자(900~1100자)** 범위
- 너무 짧거나 길면 실패로 간주

✅ SEO 블로그 구조(이 순서 그대로)
1) 도입(2~3문장): 독자가 검색해서 들어왔을 때 "왜 중요한지" 바로 납득되는 후킹
2) 핵심 정리(3~5문장): 참고 내용의 '맥락'만 내 말로 풀어서 설명(복붙 금지)
3) 내가 보는 포인트(불릿 3개): "내가 주목한 점"을 짧게 요약
4) 내 생각/해석(6~9문장): 공부하면서 든 생각, 헷갈린 지점, 연결되는 개념 등을 자연스럽게
5) 마무리(2~3문장): 독자에게 던지는 질문 1개 + 다음에 더 파볼 주제 1개

✅ 톤 가이드
- 블로그 칼럼 톤: 친절하지만 가볍지 않게
- "저는/제가/개인적으로/제 기준에서는" 같은 1인칭 표현을 최소 3번 포함
- 문장에 날짜/속보/단독 같은 뉴스 요소 넣지 말 것

✅ 출력(JSON) 형식 (반드시 이 키만 사용)
{{
  "title": "새 제목(클릭 유도형이되 과장 금지)",
  "summary": "2~3문장 요약(블로그 소개글처럼)",
  "content": "본문(약 1000자)",
  "tags": ["블록체인", "태그2", "태그3", "태그4", "태그5"]
}}

추가 규칙:
- title에는 [바이낸스]를 붙이지 마(코드에서 붙임).
- tags는 최대 8개, 중복 금지, 너무 일반적인 단어만 나열하지 말 것.
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        msg = resp.choices[0].message
        content_str = "".join(getattr(part, "text", str(part)) for part in msg.content) if isinstance(msg.content, list) else msg.content
        data = json.loads(content_str)

        new_title = (data.get("title") or title).strip()
        new_summary = (data.get("summary") or "").strip()
        new_body = (data.get("content") or content).strip()
        new_tags = data.get("tags") or []

        if not new_title.startswith("[바이낸스]"):
            new_title = f"[바이낸스] {new_title}"

        if not isinstance(new_tags, list):
            new_tags = []
        new_tags = [str(t).strip() for t in new_tags if str(t).strip()][:8]

        if not new_summary:
            new_summary = (new_body[:120] + "...") if len(new_body) > 120 else new_body

        return new_title, new_summary, new_body, new_tags

    except Exception as e:
        print("[WARN] OpenAI 재작성 실패:", e)
        fallback_title = f"[바이낸스] {title}" if not title.startswith("[바이낸스]") else title
        fallback_summary = (content[:120] + "...") if len(content) > 120 else content
        return fallback_title, fallback_summary, content, []




def fetch_wp_posts(
    max_posts: int = MAX_POSTS, per_page: int = PER_PAGE
) -> list[dict]:
    """
    WP REST API에서 posts JSON을 최대 max_posts까지 가져온다.
    _embed=1을 붙여서 대표 이미지 정보까지 가져온다.
    """
    collected: list[dict] = []
    page = 1

    if not WP_API_BASE:
        raise RuntimeError("WP_API_BASE 환경 변수가 설정되어 있지 않습니다.")

    while len(collected) < max_posts:
        params = {"per_page": per_page, "page": page, "_embed": "1"}
        print(f"[INFO] WP posts 요청: page={page}, per_page={per_page}")
        resp = requests.get(WP_API_BASE, params=params, timeout=10)

        if resp.status_code != 200:
            print(f"[WARN] WP API 요청 실패 status={resp.status_code}")
            break

        items = resp.json()
        if not items:
            print("[INFO] 더 이상 가져올 포스트가 없습니다.")
            break

        collected.extend(items)
        if len(items) < per_page:
            break

        page += 1

    return collected[:max_posts]


def main():
    print(f"[INFO] WP JSON에서 포스트 가져오는 중: {WP_API_BASE}")
    posts = fetch_wp_posts(MAX_POSTS, PER_PAGE)
    print(f"[INFO] 총 가져온 포스트 수: {len(posts)}")

    for post in posts:
        # 원 제목
        raw_title = post.get("title", {}).get("rendered", "") or "제목 없음"
        orig_title = (
            BeautifulSoup(raw_title, "html.parser").get_text().strip()
        )

        # 링크 (이미지 절대 경로 계산에만 사용)
        link = post.get("link", "").strip()

        # 날짜
        raw_date = post.get("date") or post.get("date_gmt") or ""
        try:
            dt = datetime.fromisoformat(raw_date.replace("Z", ""))
        except Exception:
            dt = datetime.now()

        date_str = dt.strftime("%Y-%m-%d")
        year = dt.strftime("%Y")
        month = dt.strftime("%m")

        # slug (원래 제목 기준으로 만드는 게 안전)
        slug_base = slugify(orig_title) or "untitled"
        slug = f"{date_str}-{slug_base}"

        # 경로
        content_dir = os.path.join(CONTENT_BASE, year, month)
        ensure_dir(content_dir)
        md_path = os.path.join(content_dir, f"{slug}.md")

        if os.path.exists(md_path):
            print(f"[SKIP] 이미 존재: {md_path}")
            continue

        # 본문 HTML
        raw_content_html = (
            post.get("content", {}).get("rendered", "")
            or post.get("excerpt", {}).get("rendered", "")
            or ""
        )

        body_text_raw = clean_html_to_markdown(raw_content_html)

        # 🔹 OpenAI로 제목+본문 재작성 (한국어 기사 + 요약 + 태그)
        new_title, new_summary, new_body, new_tags = rewrite_with_openai(
            orig_title, body_text_raw
        )
        title = new_title
        summary_text = new_summary
        body_text = new_body
        tags = new_tags
        print(f"[AI] 제목 재작성: '{orig_title}'  →  '{title}'")

        # 🔹 대표 이미지 추출 (REST API + fallback)
        img_url = extract_featured_image_from_post(
            post, raw_content_html, base_url=link
        )
        featured_image = ""

        if img_url:
            try:
                parsed = urlparse(img_url)
                ext = os.path.splitext(parsed.path)[1]
                if ext.lower() not in [".jpg", ".jpeg", ".png", ".webp"]:
                    ext = ".jpg"

                img_dir = os.path.join(IMAGE_BASE, year, month)
                ensure_dir(img_dir)
                img_filename = slug + ext
                img_path = os.path.join(img_dir, img_filename)

                print(f"[IMG] 다운로드: {img_url} -> {img_path}")

                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                }
                r = requests.get(img_url, headers=headers, timeout=10)
                print(f"[IMG] status={r.status_code}")

                if r.status_code == 200:
                    with open(img_path, "wb") as f:
                        f.write(r.content)
                    # XMag 리스트용: thumbnail: "images/news/YYYY/MM/파일명"
                    featured_image = f"news/{year}/{month}/{img_filename}"
                else:
                    print(
                        f"[WARN] 이미지 다운로드 실패 status={r.status_code}"
                    )
            except Exception as e:
                print(f"[WARN] 이미지 처리 중 오류: {e}")

        # ===== front matter 작성 =====
        safe_title = title.replace('"', '\\"')
        safe_summary = (summary_text or "").replace('"', '\\"')

        front_matter = "---\n"
        front_matter += f'title: "{safe_title}"\n'
        front_matter += f"date: {date_str}{TIME_SUFFIX}\n"
        front_matter += f"lastmod: {date_str}{TIME_SUFFIX}\n"
        front_matter += "draft: false\n"
        front_matter += f'categories: ["{DEFAULT_CATEGORY}"]\n'

        # 🔹 태그 채우기 (없으면 빈 리스트)
        front_matter += "tags:\n"
        for t in (tags or []):
            safe_tag = str(t).replace('"', '\\"')
            front_matter += f'  - "{safe_tag}"\n'

        front_matter += f'summary: "{safe_summary}"\n'

        if featured_image:
            # XMag list.html에서 .Params.thumbnail 을 보고 있으므로 thumbnail 사용
            front_matter += f'thumbnail: "{featured_image}"\n'

        front_matter += "---\n\n"

        full_content = front_matter + body_text + "\n"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        print(f"[OK] 생성: {md_path}")

    print("[DONE] WP JSON → Hugo 변환 완료")


if __name__ == "__main__":
    main()
