import sqlite3
import pandas as pd
import streamlit as st

DB_NAME = "enterprise.db"

st.set_page_config(
    page_title="Defense AX-Radar | 국방 R&D 및 신뢰성 인텔리전스",
    page_icon="🛡️",
    layout="wide",
)


def load_defense_rnd_data():
  """국방 R&D 사업 및 신뢰성 시험 요구도 데이터 조회"""
  with sqlite3.connect(DB_NAME) as conn:
    query = """
            SELECT id, announcement_title, agency, target_trl, env_standards, 
                   reliability_scope, feasibility_status, expert_opinion, created_at 
            FROM defense_rnd_radar 
            ORDER BY id DESC
        """
    return pd.read_sql_query(query, conn)


def load_defense_market_data():
  """국내외 방산 기술 및 수출 전망 데이터 조회"""
  with sqlite3.connect(DB_NAME) as conn:
    query = """
            SELECT id, source_scope, headline, company_or_nation, tech_domain, 
                   signal_type, strategic_implication, created_at 
            FROM defense_market_intel 
            ORDER BY id DESC
        """
    return pd.read_sql_query(query, conn)


# 1. 헤더 및 브리핑 소개
st.title("🛡️ Defense AX-Radar : 국방 R&D 및 신뢰성 시험 인텔리전스")
st.caption(
    "국방 R&D 사업 공고의 신뢰성/환경시험(MIL-STD) 요구도 진단 및 글로벌 방산 기술·수출"
    " 전망을 실시간 브리핑합니다."
)

rnd_df = load_defense_rnd_data()
market_df = load_defense_market_data()

# 2. 상단 핵심 KPI 메트릭 카드
col1, col2, col3, col4 = st.columns(4)

with col1:
  st.metric(
      label="📋 모니터링 국방 R&D 과제",
      value=f"{len(rnd_df)}건",
      delta="방사청·국기연·ADD",
  )
with col2:
  mil_count = len(
      rnd_df[rnd_df["env_standards"].str.contains("MIL-STD-810", na=False)]
  )
  st.metric(
      label="🧪 MIL-STD-810 환경시험 과제",
      value=f"{mil_count}건",
      delta="시험평가 필수",
  )
with col3:
  export_catalyst = len(
      market_df[market_df["signal_type"].str.contains("수출 기회", na=False)]
  )
  st.metric(
      label="🚀 K-방산 글로벌 수출 기회",
      value=f"{export_catalyst}건",
      delta="수주 파이프라인",
  )
with col4:
  tech_disruption = len(
      market_df[market_df["signal_type"].str.contains("기술 격차", na=False)]
  )
  st.metric(
      label="⚡ 글로벌 차세대 기술 격차",
      value=f"{tech_disruption}건",
      delta="선행 R&D 검토",
      delta_color="inverse",
  )

st.divider()

# 3. 사이드바 필터
st.sidebar.header("🔍 국방 데이터 필터")
agency_list = ["전체"] + sorted(rnd_df["agency"].dropna().unique().tolist())
selected_agency = st.sidebar.selectbox("발주 기관 필터", agency_list)

tech_domains = ["전체"] + sorted(
    market_df["tech_domain"].dropna().unique().tolist()
)
selected_domain = st.sidebar.selectbox("방산 기술 도메인", tech_domains)

if st.sidebar.button("🔄 최신 데이터 새로고침"):
  st.rerun()

# 4. 3대 전용 인텔리전스 탭 구성
tab1, tab2, tab3 = st.tabs([
    "🎯 국방 R&D & 신뢰성 시험 요구도 진단",
    "🌐 국내외 방산 기술력 & 수출 전망",
    "📊 부서별 대응 Action Item 종합",
])

# [탭 1] 국방 R&D 과제 및 신뢰성 시험 요구도
with tab1:
  st.subheader("🎯 국방 R&D 과제별 신뢰성/환경시험 요구도 분석 뷰")

  filtered_rnd = rnd_df.copy()
  if selected_agency != "전체":
    filtered_rnd = filtered_rnd[filtered_rnd["agency"] == selected_agency]

  for _, row in filtered_rnd.iterrows():
    # 적합성 상태별 배지
    status = row["feasibility_status"]
    if "적합" in status:
      badge = "🟢 [수행 적합]"
    elif "검토" in status:
      badge = "🟡 [인프라/치구 검토 요망]"
    else:
      badge = "⚪ [일반 관리]"

    with st.expander(
        f"{badge} [{row['agency']}] {row['announcement_title']}", expanded=True
    ):
      c1, c2 = st.columns(2)
      with c1:
        st.markdown(f"**🎯 목표 TRL:** `{row['target_trl']}`")
        st.markdown(f"**📜 적용 규격:** `{row['env_standards']}`")
        st.markdown(f"**🌊 환경/신뢰성 시험 범위:**")
        st.info(row["reliability_scope"])
      with c2:
        st.markdown(f"**💡 신뢰성 엔지니어 딥트윈 조치 의견:**")
        st.success(row["expert_opinion"])
        st.caption(f"등록 시점: {row['created_at']}")

# [탭 2] 국내외 방산 기술력 및 수출 전망
with tab2:
  st.subheader("🌐 글로벌 방산 기술 동향 및 국가별 수출 파이프라인")

  filtered_mkt = market_df.copy()
  if selected_domain != "전체":
    filtered_mkt = filtered_mkt[filtered_mkt["tech_domain"] == selected_domain]

  for _, row in filtered_mkt.iterrows():
    sig = row["signal_type"]
    if "기회" in sig:
      sig_badge = "🟢 [수출 기회]"
    elif "격차" in sig:
      sig_badge = "⚡ [기술 격차 경계]"
    elif "리스크" in sig:
      sig_badge = "🔴 [수출/규제 리스크]"
    else:
      sig_badge = "🔵 [시장 동향]"

    with st.expander(
        f"{sig_badge} [{row['source_scope']}] {row['headline']}", expanded=True
    ):
      m1, m2 = st.columns(2)
      with m1:
        st.markdown(f"**🎯 타깃 기업/국가:** `{row['company_or_nation']}`")
        st.markdown(f"**🛠️ 기술 분야:** `{row['tech_domain']}`")
        st.markdown(f"**📌 시그널 유형:** `{row['signal_type']}`")
      with m2:
        st.markdown(f"**💡 전략적 시사점 및 대응 방향:**")
        st.warning(row["strategic_implication"])
        st.caption(f"수집 시점: {row['created_at']}")

# [탭 3] Action Item 종합 요약
with tab3:
  st.subheader("📊 부서별 즉시 조치 Action Item 매트릭스")
  st.markdown("#### 1. 신뢰성 시험 및 평가팀 Action Plan")
  for _, r in rnd_df.iterrows():
    st.write(
        f"• **[{r['agency']}]** {r['announcement_title']} ➜ *{r['expert_opinion']}*"
    )

  st.markdown("#### 2. 전략기획 및 해외사업팀 Action Plan")
  for _, m in market_df.iterrows():
    st.write(
        f"• **[{m['company_or_nation']}]** {m['headline']} ➜"
        f" *{m['strategic_implication']}*"
    )