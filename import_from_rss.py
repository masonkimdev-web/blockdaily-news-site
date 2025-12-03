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

MAX_POSTS = 100                    # 최대 가져올 포스트 수
PER_PAGE = 50                      # WP API per_page (최대 100)
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
    영어 워드프레스 글을:
    - 한국어 뉴스 기사 스타일로 재작성
    - 클릭 잘 나오는 새 제목
    - 한 줄 요약(summary)
    - 한국어 태그 리스트
    를 생성해서 (새 제목, 요약, 새 본문, 태그목록)을 반환
    """
    prompt = f"""
너는 블록체인·가상자산 뉴스를 다루는 한국어 온라인 미디어의 편집 기자다.
아래 영어 원문을 바탕으로, 한국 독자를 위한 기사로 재구성해줘.

[원래 제목]
{title}

[원래 본문]
{content}

요구사항:
- 결과물은 **반드시 한국어**로 작성할 것
- 제목(title):
  - 클릭률(CTR)이 높게 보이도록 새롭게 재창작
  - 원래 제목을 그대로 번역하거나 복사하지 말 것
- 요약(summary):
  - 1~2문장, 120자 내외
  - 기사의 핵심 포인트(가격 변동, 주요 발언, 규제 이슈 등)를 간단히 정리
- 태그(tags):
  - 한국어 단어/구로만 구성
  - 예: ["비트코인", "이더리움", "현물 ETF", "SEC", "온체인 데이터"]
  - 3~7개 정도, 너무 길지 않게
- 본문(content):
  - 블로그용 뉴스 기사 톤 (너무 캐주얼 X, 너무 논문체 X)
  - 원문이 담고 있는 사실 관계, 수치(가격, 날짜, 수량 등)는 정확히 유지
  - 불필요한 반복/군더더기 문장은 정리
  - 단락을 적절히 나눠서 가독성 좋게 작성

반환 형식(JSON) 예시:
{{
  "title": "새로 재작성된 한국어 제목",
  "summary": "기사를 1~2문장으로 요약한 한국어 문장.",
  "tags": ["비트코인", "ETF", "SEC"],
  "content": "재작성된 한국어 본문 전체"
}}

JSON만 출력해줘.
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        msg = resp.choices[0].message

        # SDK 버전에 따라 content 타입이 다를 수 있어 방어적으로 처리
        if isinstance(msg.content, list):
            content_str = "".join(
                getattr(part, "text", str(part)) for part in msg.content
            )
        else:
            content_str = msg.content

        data = json.loads(content_str)

        new_title = data.get("title", title).strip()
        new_summary = data.get("summary", "").strip()
        new_content = data.get("content", content).strip()

        raw_tags = data.get("tags", [])
        if isinstance(raw_tags, list):
            new_tags = [str(t).strip() for t in raw_tags if str(t).strip()]
        else:
            # "비트코인, ETF, SEC" 이런 식으로 올 수도 있으니 분리
            new_tags = [t.strip() for t in str(raw_tags).split(",") if t.strip()]

        # 모델이 원제목 그대로 돌려줄 경우 최소한의 변형
        if new_title == title:
            new_title = f"{title}… 핵심 이슈 정리"

        return new_title, new_summary, new_content, new_tags

    except Exception as e:
        print("[WARN] OpenAI 재작성 실패:", e)
        # 실패 시: 원본 기준으로 fallback
        fallback_summary = (
            (content[:150].replace("\n", " ") + "…") if content else ""
        )
        return title, fallback_summary, content, []


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
