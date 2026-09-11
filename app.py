import sqlite3
import pandas as pd
import streamlit as st

DB_NAME = "news.db"

st.set_page_config(
    page_title="AX 딥트윈 투자 분석 대시보드", page_icon="🧠", layout="wide"
)


def load_data():
  """articles 테이블과 deeptwin_insights 테이블을 JOIN하여 조회"""
  with sqlite3.connect(DB_NAME) as conn:
    query = """
            SELECT 
                a.id, 
                a.title, 
                a.url, 
                a.category, 
                a.published_at,
                d.signal_type,
                d.impact_horizon,
                d.risk_score,
                d.key_thesis,
                d.analyzed_at
            FROM articles a
            LEFT JOIN deeptwin_insights d ON a.id = d.article_id
            ORDER BY a.id DESC
        """
    df = pd.read_sql_query(query, conn)
  return df


# 1. 헤더
st.title("🧠 AX 딥트윈 투자 분석 대시보드")
st.caption(
    "베테랑 투자자의 암묵지(Deeptwin)를 이식하여 실시간 뉴스의 실질적"
    " 시장 파급력과 리스크를 선별합니다."
)

df = load_data()

if df.empty:
  st.warning("수집된 데이터가 없습니다. 크롤러를 먼저 실행해 주세요.")
  st.stop()

# 2. 핵심 KPI 메트릭 카드
catalyst_count = len(df[df["signal_type"].str.contains("Catalyst", na=False)])
risk_count = len(df[df["signal_type"].str.contains("Risk", na=False)])
noise_count = len(df[df["signal_type"].str.contains("Noise", na=False)])

m1, m2, m3, m4 = st.columns(4)
with m1:
  st.metric(label="총 분석 기사", value=f"{len(df)}건")
with m2:
  st.metric(
      label="🚀 투자 촉매 (Catalyst)",
      value=f"{catalyst_count}건",
      delta="핵심 모멘텀",
  )
with m3:
  st.metric(
      label="🚨 위험 경고 (Risk)",
      value=f"{risk_count}건",
      delta="-주의 필요",
      delta_color="inverse",
  )
with m4:
  st.metric(label="⚪ 단순 소음 (Noise)", value=f"{noise_count}건", delta="필터링")

st.divider()

# 3. 사이드바 필터
st.sidebar.header("🔍 탐색 필터")
categories = ["전체"] + sorted(df["category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("기본 카테고리", categories)

signals = ["전체", "Catalyst (촉매)", "Risk (경고)", "Neutral (관망)", "Noise (소음)"]
selected_signal = st.sidebar.selectbox("딥트윈 시그널 필터", signals)

search_keyword = st.sidebar.text_input("제목 키워드 검색", "")

# 필터링 적용
filtered_df = df.copy()
if selected_category != "전체":
  filtered_df = filtered_df[filtered_df["category"] == selected_category]

if selected_signal != "전체":
  filtered_df = filtered_df[
      filtered_df["signal_type"].str.contains(
          selected_signal.split()[0], na=False
      )
  ]

if search_keyword:
  filtered_df = filtered_df[
      filtered_df["title"].str.contains(search_keyword, case=False, na=False)
  ]

# 4. 탭 구성 (3개 탭으로 확장)
tab1, tab2, tab3 = st.tabs(
    ["🧠 딥트윈 투자 인사이트", "📊 카테고리 통계", "📋 전체 기사 원장"]
)

# [신규 탭] 딥트윈 전용 투자 리포트 뷰
with tab1:
  st.subheader(f"베테랑 투자자 분석 뷰 (조회 {len(filtered_df)}건)")

  # 딥트윈 분석 데이터가 있는 기사들을 카드 형태로 출력
  insights_df = filtered_df[filtered_df["signal_type"].notna()]

  if insights_df.empty:
    st.info(
      "선택된 필터에 해당하는 딥트윈 분석 결과가 없습니다. `deeptwin_analyst.py`를"
      " 실행하여 분석을 진행해 주세요."
    )
  else:
    for _, row in insights_df.iterrows():
      # 시그널 타입별 배지 스타일
      signal = row["signal_type"]
      if "Catalyst" in signal:
        badge = "🟢 **[Catalyst / 성장 촉매]**"
      elif "Risk" in signal:
        badge = "🔴 **[Risk / 위험 경고]**"
      elif "Noise" in signal:
        badge = "⚪ **[Noise / 소음 배제]**"
      else:
        badge = "🟡 **[Neutral / 중립 관망]**"

      with st.expander(f"{badge} {row['title']}", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
          st.write(f"**위험도 스코어:** {row['risk_score']} / 5")
          st.write(f"**파급 기간:** {row['impact_horizon']}")
          st.markdown(f"[🔗 원문 기사 열기]({row['url']})")
        with c2:
          st.markdown(f"**💡 베테랑 투자자의 핵심 명제 (Key Thesis):**")
          st.info(row["key_thesis"])
          st.caption(
              f"카테고리: {row['category']} | 분석시점: {row['analyzed_at']}"
          )

with tab2:
  st.subheader("데이터 분류 통계")
  col_a, col_b = st.columns(2)
  with col_a:
    st.write("기본 카테고리 분포")
    st.bar_chart(df["category"].value_counts())
  with col_b:
    st.write("딥트윈 시그널 분포")
    st.bar_chart(df["signal_type"].value_counts())

with tab3:
  st.subheader("원시 데이터 테이블")
  st.dataframe(
      filtered_df[[
          "id",
          "category",
          "signal_type",
          "title",
          "published_at",
          "url",
      ]],
      column_config={"url": st.column_config.LinkColumn("원문 링크")},
      use_container_width=True,
      hide_index=True,
  )

if st.sidebar.button("🔄 데이터 새로고침"):
  st.rerun()