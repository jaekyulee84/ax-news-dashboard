import re
import sqlite3
from datetime import datetime
import requests
from bs4 import BeautifulSoup

DB_NAME = "news.db"


def init_db():
  """SQLite 데이터베이스 초기화 및 category 컬럼 마이그레이션"""
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    # 1. 테이블 생성 (신규 환경 대비)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                published_at TEXT,
                collected_at TEXT NOT NULL,
                category TEXT DEFAULT 'General'
            )
        """)

    # 2. 기존 테이블에 category 컬럼이 없는 경우 안전하게 추가 (마이그레이션)
    cursor.execute("PRAGMA table_info(articles)")
    columns = [column[1] for column in cursor.fetchall()]
    if "category" not in columns:
      cursor.execute(
          "ALTER TABLE articles ADD COLUMN category TEXT DEFAULT 'General'"
      )

    conn.commit()


def classify_category(title: str) -> str:
  """기사 제목 키워드를 기반으로 카테고리 자동 분류"""
  t = title.lower()

  # 1. AI 관련 키워드
  if any(
      kw in t
      for kw in [
          "ai",
          "gpt",
          "llm",
          "claude",
          "openai",
          "model",
          "deep learning",
          "machine learning",
      ]
  ):
    return "AI"

  # 2. Tech / 개발 관련 키워드
  if any(
      kw in t
      for kw in [
          "code",
          "programming",
          "app",
          "software",
          "linux",
          "python",
          "google",
          "apple",
          "security",
          "os",
      ]
  ):
    return "Tech"

  # 3. 비즈니스 / 시장 관련 키워드
  if any(
      kw in t
      for kw in [
          "market",
          "money",
          "business",
          "fund",
          "economy",
          "startup",
          "stock",
      ]
  ):
    return "Business"

  # 4. 그 외 기본 카테고리
  return "General"


def fetch_news_data():
  """예시 타깃 페이지 수집 및 카테고리 분류 적용"""
  target_url = "https://news.ycombinator.com/"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  try:
    response = requests.get(target_url, headers=headers, timeout=10)
    response.raise_for_status()
  except requests.RequestException as e:
    print(f"[오류] 데이터 수집 실패: {e}")
    return []

  soup = BeautifulSoup(response.text, "html.parser")
  articles = []

  story_rows = soup.select("tr.athing")
  for row in story_rows:
    title_element = row.select_one("span.titleline > a")
    if not title_element:
      continue

    title = title_element.get_text(strip=True)
    link = title_element.get("href", "")

    if link.startswith("item?id="):
      link = f"https://news.ycombinator.com/{link}"

    # 카테고리 자동 분류 적용
    category = classify_category(title)

    articles.append({
        "title": title,
        "url": link,
        "published_at": datetime.now().strftime("%Y-%m-%d"),
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": category,
    })

  return articles


def save_to_db(articles):
  """수집된 데이터를 SQLite DB에 중복 없이 저장"""
  if not articles:
    print("[알림] 저장할 데이터가 없습니다.")
    return

  inserted_count = 0
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    for item in articles:
      try:
        cursor.execute(
            """
                    INSERT INTO articles (title, url, published_at, collected_at, category)
                    VALUES (?, ?, ?, ?, ?)
                """,
            (
                item["title"],
                item["url"],
                item["published_at"],
                item["collected_at"],
                item["category"],
            ),
        )
        inserted_count += 1
      except sqlite3.IntegrityError:
        continue
    conn.commit()

  print(
      f"[완료] 총 {len(articles)}건 중 신규 {inserted_count}건이 DB에"
      " 저장되었습니다."
  )


if __name__ == "__main__":
  print("=== 카테고리 분류 크롤링 파이프라인 시작 ===")
  init_db()
  data = fetch_news_data()
  save_to_db(data)