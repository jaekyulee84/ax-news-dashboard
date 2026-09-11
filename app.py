import sqlite3
import pandas as pd
import streamlit as st

DB_NAME = "news.db"

# 페이지 기본 설정
st.set_page_config(page_title="AI 뉴스 대시보드", page_icon="📰", layout="wide")


def load_data():
  """news.db에서 데이터 조회"""
  with sqlite3.connect(DB_NAME) as conn:
    query = """
            SELECT id, title, url, category, published_at, collected_at 
            FROM articles 
            ORDER BY id DESC
        """
    df = pd.read_sql_query(query, conn)
  return df


# 1. 데이터 로드
st.title("📰 IT / AI 실시간 뉴스 대시보드")
st.caption("news.db에 자동 수집된 데이터를 시각화하고 탐색합니다.")

df = load_data()

if df.empty:
  st.warning("데이터베이스에 저장된 기사가 없습니다. crawler.py를 먼저 실행해 주세요.")
  st.stop()

# 2. 상단 핵심 지표(Metrics)
col1, col2, col3 = st.columns(3)
with col1:
  st.metric(label="총 수집 기사", value=f"{len(df)}건")
with col2:
  ai_count = len(df[df["category"] == "AI"])
  st.metric(label="AI 관련 기사", value=f"{ai_count}건")
with col3:
  tech_count = len(df[df["category"] == "Tech"])
  st.metric(label="Tech 관련 기사", value=f"{tech_count}건")

st.divider()

# 3. 사이드바 필터링
st.sidebar.header("🔍 검색 및 필터")
categories = ["전체"] + sorted(df["category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("카테고리 선택", categories)

search_keyword = st.sidebar.text_input("제목 키워드 검색", "")

# 데이터 필터링 적용
filtered_df = df.copy()
if selected_category != "전체":
  filtered_df = filtered_df[filtered_df["category"] == selected_category]

if search_keyword:
  filtered_df = filtered_df[
      filtered_df["title"].str.contains(search_keyword, case=False, na=False)
  ]

# 4. 본문 시각화 및 데이터 표
tab1, tab2 = st.tabs(["📊 카테고리 분포", "📋 기사 목록 탐색"])

with tab1:
  st.subheader("카테고리별 기사 분포")
  category_counts = df["category"].value_counts()
  st.bar_chart(category_counts)

with tab2:
  st.subheader(f"조회 결과 (총 {len(filtered_df)}건)")

  # 표 형태로 출력 및 링크 컬럼 지정
  st.dataframe(
      filtered_df[["id", "category", "title", "published_at", "url"]],
      column_config={"url": st.column_config.LinkColumn("원문 링크")},
      use_container_width=True,
      hide_index=True,
  )

# 사이드바 새로고침 버튼
if st.sidebar.button("🔄 데이터 새로고침"):
  st.rerun()