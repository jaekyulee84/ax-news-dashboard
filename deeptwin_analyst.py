from datetime import datetime
import json
import sqlite3

DB_NAME = "news.db"

# 1. 딥트윈 페르소나 및 판단 원칙 (암묵지 정의)
INVESTOR_TACIT_KNOWLEDGE = """
당신은 20년 경력의 보수적이고 날카로운 펀더멘털 테크/시장 전문 투자자 'Deeptwin-Investor'입니다.
당신은 화려한 보도자료나 일시적 유행에 속지 않으며, 오직 기업의 지속 가능한 현금흐름, 규제/보안 리스크, 밸류체인 독점력 관점에서만 뉴스를 평가합니다.

[판단 기준 (Decision Rubric)]
1. 노이즈(Noise): 기업의 단순 마케팅, 클릭베이트, 수치적 근거 없는 호언장담은 과감히 가치 없다고 평가할 것.
2. 촉매(Catalyst): 실제 대규모 CAPEX(설비투자), 독점적 기술 공급, 실질적 매출/이익 구조 전환이 확인되는 경우만 인정.
3. 리스크(Risk): 보안 취약점, 규제 당국 조사, 소송, 경영진 도덕적 해이, 원가 상승 압박은 주가에 치명적이므로 최우선 경고.
4. 시장 기대치 괴리: 호재라도 이미 시장에 충분히 반영된 것이라면 '재료 소멸(Sell on News)' 가능성을 짚을 것.
"""


def init_deeptwin_db():
  """딥트윈 분석 결과를 저장할 테이블 생성"""
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS deeptwin_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER UNIQUE,
                signal_type TEXT,       -- Catalyst, Risk, Neutral, Noise
                impact_horizon TEXT,    -- Short-term, Long-term, None
                risk_score INTEGER,     -- 1(최저) ~ 5(최고 위험)
                key_thesis TEXT,        -- 베테랑 투자자의 1줄 분석 코멘트
                analyzed_at TEXT,
                FOREIGN KEY(article_id) REFERENCES articles(id)
            )
        """)
    conn.commit()


def analyze_article_mock_engine(title: str, url: str) -> dict:
  """
  딥트윈 추론 엔진 (실습용 핵심 로직)
  - LLM API 연동 시에는 INVESTOR_TACIT_KNOWLEDGE를 시스템 프롬프트로 주입하여 결과를 JSON으로 받습니다.
  - 본 실습에서는 암묵지 규칙이 실제 데이터에 어떻게 적용되는지 시뮬레이션합니다.
  """
  t = title.lower()

  # 1. 리스크(Risk) 감지: 보안, 규제, 소송, 연령 제한 등
  if any(
      kw in t
      for kw in [
          "security",
          "vulnerable",
          "restriction",
          "lawsuit",
          "regulation",
          "over 18",
          "crackdown",
      ]
  ):
    return {
        "signal_type": "Risk (경고)",
        "impact_horizon": "Short-term",
        "risk_score": 4,
        "key_thesis": (
            "규제 대응 및 보안 감사 비용 증가 가능성. 단기 센티먼트 악화 요인으로"
            " 작용할 수 있어 보수적 접근 필요."
        ),
    }

  # 2. 촉매(Catalyst) 감지: 인프라 규모(petabyte), 아키텍처 혁신, 상용화 릴리즈
  elif any(
      kw in t
      for kw in [
          "released",
          "petabyte",
          "architecture",
          "breakthrough",
          "patent",
          "cluster",
      ]
  ):
    return {
        "signal_type": "Catalyst (촉매)",
        "impact_horizon": "Long-term",
        "risk_score": 2,
        "key_thesis": (
            "실질적 기술 인프라 확장 및 상용화 신호. 기술적 진입장벽 구축 여부를"
            " 지속 추적해야 함."
        ),
    }

  # 3. 노이즈(Noise) 감지: 단순 견해, 흥미 위주, 밈
  elif any(
      kw in t
      for kw in ["spent", "bread", "glacier", "humor", "oddities", "opinion"]
  ):
    return {
        "signal_type": "Noise (소음)",
        "impact_horizon": "None",
        "risk_score": 1,
        "key_thesis": (
            "투자 판단과 무관한 개인적 경험담 또는 일반 교양성 데이터. 포트폴리오"
            " 의사결정에서 배제."
        ),
    }

  # 4. 일반 기술 분석 (Neutral / Watch)
  else:
    return {
        "signal_type": "Neutral (관망)",
        "impact_horizon": "Mid-term",
        "risk_score": 2,
        "key_thesis": (
            "유의미한 기술 흐름이나 즉각적인 시장 가격 변동 요인은 부족함."
            " 생태계 점유율 추이 관찰 필요."
        ),
    }


def run_deeptwin_batch():
  """수집된 기사들을 딥트윈 엔진으로 분석하여 저장"""
  init_deeptwin_db()

  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    # 아직 딥트윈 분석이 되지 않은 기사 조회
    cursor.execute("""
            SELECT a.id, a.title, a.url 
            FROM articles a
            LEFT JOIN deeptwin_insights d ON a.id = d.article_id
            WHERE d.id IS NULL
            LIMIT 10
        """)
    unanalized_articles = cursor.fetchall()

    if not unanalized_articles:
      print("[알림] 분석할 신규 기사가 없습니다.")
      return

    print(
        f"=== 딥트윈 투자 분석 엔진 가동 (총 {len(unanalized_articles)}건 분석) ==="
    )

    for aid, title, url in unanalized_articles:
      result = analyze_article_mock_engine(title, url)
      cursor.execute(
          """
                INSERT OR REPLACE INTO deeptwin_insights 
                (article_id, signal_type, impact_horizon, risk_score, key_thesis, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
          (
              aid,
              result["signal_type"],
              result["impact_horizon"],
              result["risk_score"],
              result["key_thesis"],
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          ),
      )
      print(f"[{result['signal_type']}] 기사 #{aid}: {title[:40]}...")
      print(f"  └ 투자 코멘트: {result['key_thesis']}\n")

    conn.commit()
    print("[완료] 딥트윈 분석 결과가 deeptwin_insights 테이블에 저장되었습니다.")


if __name__ == "__main__":
  run_deeptwin_batch()