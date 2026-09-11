from datetime import datetime
import os
import sqlite3

DB_NAME = "enterprise.db"


def init_brief_table(conn):
  """executive_briefs 테이블 생성 보장"""
  cur = conn.cursor()
  cur.execute("""
        CREATE TABLE IF NOT EXISTS executive_briefs (
            brief_id INTEGER PRIMARY KEY AUTOINCREMENT,
            brief_date TEXT NOT NULL,
            brief_type TEXT,
            summary_markdown TEXT,
            created_at TEXT NOT NULL
        )
    """)
  conn.commit()


def generate_executive_brief() -> str:
  """enterprise.db 데이터를 집계하여 A4 1장 정갈한 마크다운 보고서 생성"""
  today_str = datetime.now().strftime("%Y-%m-%d")

  with sqlite3.connect(DB_NAME) as conn:
    init_brief_table(conn)
    cur = conn.cursor()

    # 1. 국방 R&D 데이터 조회 (최신 5건)
    cur.execute("""
            SELECT announcement_title, agency, target_trl, env_standards, reliability_scope, expert_opinion 
            FROM defense_rnd_radar 
            ORDER BY id DESC LIMIT 5
        """)
    rnd_rows = cur.fetchall()

    # 2. 방산 시장 및 수출 데이터 조회 (최신 5건)
    cur.execute("""
            SELECT headline, company_or_nation, tech_domain, signal_type, strategic_implication 
            FROM defense_market_intel 
            ORDER BY id DESC LIMIT 5
        """)
    market_rows = cur.fetchall()

  # 3. 마크다운 보고서 조립 (항목별 깔끔한 인덱싱)
  report_lines = []
  report_lines.append(
      "# 🛡️ [Defense AX-Radar] 국방 R&D 및 기술·수출 모닝 브리핑"
  )
  report_lines.append(
      f"**보고 일자:** {today_str} | **발행 체계:** 사내 Defense AX-Radar"
      " 자동화 허브"
  )
  report_lines.append(
      "**열람 대상:** 신뢰성시험평가팀, 첨단기술연구팀, 방산수출기획팀\n"
  )
  report_lines.append("---\n")

  # 섹션 1: 신뢰성 시험 및 R&D 요구도
  report_lines.append("## 1. 🎯 금일 핵심 국방 R&D 및 신뢰성 시험평가 요구도")
  if rnd_rows:
    for r in rnd_rows:
      title, agency, trl, standards, scope, opinion = r
      report_lines.append(f"### • [{agency}] {title}")
      report_lines.append(f"- **요구 TRL 및 적용 규격:** `{trl}` | `{standards}`")
      report_lines.append(f"- **시험 요구 범위:** {scope}")
      report_lines.append(f"- **💡 엔지니어 조치 의견:** {opinion}\n")
  else:
    report_lines.append("- 금일 신규 등록된 국방 R&D 과제가 없습니다.\n")

  # 섹션 2: 글로벌 방산 기술 및 수출 전망
  report_lines.append("## 2. 🌐 글로벌 방산 기술력 & 수출 파이프라인 시사점")
  if market_rows:
    for m in market_rows:
      headline, target, domain, sig_type, implication = m
      report_lines.append(f"### • [{sig_type}] {headline}")
      report_lines.append(f"- **타깃 및 기술 분야:** `{target}` | `{domain}`")
      report_lines.append(f"- **💡 전략적 시사점:** {implication}\n")
  else:
    report_lines.append(
        "- 금일 신규 등록된 글로벌 방산 인텔리전스가 없습니다.\n"
    )

  # 섹션 3: 부서별 즉시 조치 Action Items
  report_lines.append("## 3. 📋 부서별 즉시 대응 Action Plan (Today)")
  report_lines.append(
      "1. **신뢰성 시험평가팀**: 잠수함 도플러 센서 및 유도무기 전력제어기"
      " 관련 MIL-STD-810H 진동/염무 복합 챔버 일정 및 전용 치구(Jig) 제작"
      " 준비 점검"
  )
  report_lines.append(
      "2. **방산수출 및 사업팀**: K-방산 수출국(폴란드, 중동 등) 무기체계에"
      " 탑재되는 서브모듈의 환경시험 성적서 보유 여부 전수 조사 및 납기 단축"
      " 방안 검토"
  )
  report_lines.append(
      "3. **선행 R&D 연구팀**: 해외 선도업체 차세대 스텔스 음향/센서 기술에"
      " 대응하는 차기 핵심기술 과제 기획안 검토"
  )
  report_lines.append(
      "\n---\n*본 보고서는 Defense AX-Radar 인지 엔진을 통해 24시간 자동"
      " 분석·생성되었습니다.*"
  )

  full_report = "\n".join(report_lines)

  # 4. DB 저장
  with sqlite3.connect(DB_NAME) as conn:
    init_brief_table(conn)
    cur = conn.cursor()
    cur.execute(
        """
            INSERT INTO executive_briefs (brief_date, brief_type, summary_markdown, created_at)
            VALUES (?, ?, ?, ?)
        """,
        (
            today_str,
            "DAILY_MORNING",
            full_report,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()

  # 5. 로컬 파일 저장
  output_filename = f"daily_defense_brief_{today_str}.md"
  with open(output_filename, "w", encoding="utf-8") as f:
    f.write(full_report)

  print(f"[완료] 모닝 브리핑 정돈 완료 -> '{output_filename}'")
  return full_report


if __name__ == "__main__":
  generate_executive_brief()