from datetime import datetime
import json
import sqlite3

DB_NAME = "enterprise.db"


def init_market_intel_db():
  """방산 기술 및 수출 전망 전용 테이블 초기화"""
  with sqlite3.connect(DB_NAME) as conn:
    cur = conn.cursor()
    cur.execute("""
            CREATE TABLE IF NOT EXISTS defense_market_intel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_scope TEXT NOT NULL,           -- 'GLOBAL(외신)' or 'DOMESTIC(국내)'
                headline TEXT NOT NULL,
                company_or_nation TEXT,               -- 관련 기업 또는 대상국
                tech_domain TEXT,                     -- 기술 도메인
                signal_type TEXT,                     -- '수출 기회', '수출 리스크', '기술 격차', '시장 동향'
                strategic_implication TEXT,           -- 전략적 시사점 및 대응 방향
                created_at TEXT NOT NULL
            )
        """)
    conn.commit()


def deeptwin_market_evaluator(article: dict) -> dict:
  """
  방산 기술 및 수출 전문 애널리스트 딥트윈 추론 엔진
  """
  text = (
      article.get("headline", "") + " " + article.get("summary", "")
  ).upper()

  # 1. 기술 도메인 태깅
  domain = "해양/잠수함/수중센서" if any(k in text for k in ["SUBMARINE", "SONAR", "NAVAL", "DOPPLER", "잠수함", "함정"]) else \
             "유도무기/미사일" if any(k in text for k in ["MISSILE", "GUIDED", "AIR DEFENSE", "유도무기", "방공"]) else \
             "유무인복합/AI" if any(k in text for k in ["UNMANNED", "DRONE", "AI", "AUTONOMOUS", "드론", "무인"]) else \
             "지상/기동체계" if any(k in text for k in ["TANK", "ARMORED", "전차", "장갑차", "자주포"]) else "핵심부품/소재"

  # 2. 관련 기업/국가 추출
  targets = []
  for name in [
      "HANWHA",
      "LIG NEX1",
      "KAI",
      "HYUNDAI ROTEM",
      "LOCKHEED",
      "RTX",
      "RHEINMETALL",
      "POLAND",
      "ROMANIA",
      "US",
      "MIDDLE EAST",
      "방사청",
      "폴란드",
      "미국",
      "중동",
  ]:
    if name in text:
      targets.append(name)
  target_str = ", ".join(targets) if targets else "글로벌 방산 전반"

  # 3. 딥트윈 시그널 및 전략적 시사점 도출
  if any(
      k in text
      for k in ["EXPORT", "CONTRACT", "SUPPLY", "SELECTION", "수출", "수주", "도입"]
  ):
    sig = "수출 기회 (Export Catalyst)"
    imp = (
        f"[{target_str} 타깃] K-방산 무기체계 수주 파이프라인 확대. "
        "체계업체 납품을 위한 서브모듈의 환경/신뢰성 시험 성적서(MIL-STD) 사전 확보 및 납기 단축 준비 필요."
    )
  elif any(
      k in text
      for k in [
          "RESTRICTION",
          "REGULATION",
          "SANCTION",
          "LOCALIZATION",
          "규제",
          "통제",
          "오프셋",
          "관세",
      ]
  ):
    sig = "수출 리스크 (Export Risk)"
    imp = (
        f"수출 대상국의 현지화(오프셋) 요건 또는 기술 통제 규정 강화 조짐. "
        "핵심 부품 단종 리스크 점검 및 대체 부품 신뢰성 재검증 계획 수립 권고."
    )
  elif any(
      k in text
      for k in [
          "NEXT-GEN",
          "BREAKTHROUGH",
          "DEVELOPMENT",
          "PATENT",
          "신기술",
          "극초음속",
          "AI",
      ]
  ):
    sig = "기술 격차 (Tech Disruption)"
    imp = (
        f"[{domain}] 글로벌 선도 업체의 차세대 기술 발표. "
        "국내 독자 기술 확보를 위한 선행 R&D 과제 기획 및 군 요구성능(ROC) 상향 추세 대비 필요."
    )
  else:
    sig = "시장 동향 (Market Dynamic)"
    imp = "글로벌 국방 예산 및 중장기 획득 계획 모니터링 데이터베이스 유지."

  return {
      "company_or_nation": target_str,
      "tech_domain": domain,
      "signal_type": sig,
      "strategic_implication": imp,
  }


def run_market_intelligence():
  """국내외 최신 방산 기사 수집 및 분석 가동"""
  init_market_intel_db()

  # 글로벌 및 국내 주요 방산 뉴스 샘플 데이터셋
  sample_articles = [
      {
          "source_scope": "GLOBAL(외신)",
          "headline": (
              "Poland signs additional contract for K9 Howitzers and K2 Tanks"
              " amid European defense buildup"
          ),
          "summary": (
              "Hanwha Aerospace and Hyundai Rotem finalize new export deal with"
              " Polish Armament Agency with localization clauses."
          ),
      },
      {
          "source_scope": "GLOBAL(외신)",
          "headline": (
              "Naval Group unveils next-gen acoustic stealth submarine with"
              " integrated Doppler sensors"
          ),
          "summary": (
              "New underwater navigation architecture improves accuracy without"
              " GPS, requiring extreme shock and salinity test standards."
          ),
      },
      {
          "source_scope": "DOMESTIC(국내)",
          "headline": (
              "[방산수출] 중동 국가와 천궁-II(M-SAM) 다기능 레이다 및 유도탄 수출"
              " 협상 가속화"
          ),
          "summary": (
              "LIG넥스원 및 한화시스템, 사막 고온 환경 적응형 극한 환경시험"
              " 통과 기반 수출 확대 기대."
          ),
      },
      {
          "source_scope": "GLOBAL(외신)",
          "headline": (
              "US DoD expands ITAR compliance audit on foreign subcontractors"
              " for critical electronic modules"
          ),
          "summary": (
              "Stricter regulation on defense electronic components supplied"
              " from allied nations."
          ),
      },
  ]

  print(
      "=== 국내외 최신 방산 기술력 및 수출 전망 딥트윈 엔진 가동 ==="
  )

  with sqlite3.connect(DB_NAME) as conn:
    cur = conn.cursor()
    for art in sample_articles:
      res = deeptwin_market_evaluator(art)

      cur.execute(
          """
                INSERT INTO defense_market_intel 
                (source_scope, headline, company_or_nation, tech_domain, signal_type, strategic_implication, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
          (
              art["source_scope"],
              art["headline"],
              res["company_or_nation"],
              res["tech_domain"],
              res["signal_type"],
              res["strategic_implication"],
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          ),
      )

      print(f"\n[{art['source_scope']} | {res['signal_type']}]")
      print(f"  ├ 헤드라인: {art['headline']}")
      print(f"  ├ 타깃/분야: {res['company_or_nation']} | {res['tech_domain']}")
      print(f"  └ 전략적 시사점: {res['strategic_implication']}")

    conn.commit()
    print(
        "\n[완료] 방산 기술 및 수출 인텔리전스 데이터가 defense_market_intel"
        " 테이블에 저장되었습니다."
    )


if __name__ == "__main__":
  run_market_intelligence()