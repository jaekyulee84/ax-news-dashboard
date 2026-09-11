from datetime import datetime
import json
import sqlite3

DB_NAME = "enterprise.db"


def init_defense_db():
  """국방 R&D 및 신뢰성 시험 전용 테이블 초기화"""
  with sqlite3.connect(DB_NAME) as conn:
    cur = conn.cursor()
    cur.execute("""
            CREATE TABLE IF NOT EXISTS defense_rnd_radar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                announcement_title TEXT NOT NULL,
                agency TEXT NOT NULL,                  -- 발주기관 (방사청, 국기연, ADD 등)
                target_trl TEXT,                       -- 요구 TRL 단계
                env_standards TEXT,                    -- 적용 환경/전자기 규격 (MIL-STD 등)
                reliability_scope TEXT,                -- 환경/신뢰성 시험 요구 범위
                feasibility_status TEXT,               -- '수행 적합', '인프라 보완 필요', '검토 요망'
                expert_opinion TEXT,                   -- 신뢰성 엔지니어 딥트윈 총평
                created_at TEXT NOT NULL
            )
        """)
    conn.commit()


def deeptwin_defense_evaluator(doc: dict) -> dict:
  """
  국방 신뢰성 엔지니어의 암묵지를 이식한 진단 추론 로직
  """
  title = doc.get("title", "")
  text = doc.get("text", "")
  combined = (title + " " + text).upper()

  # 1. TRL 요구도 분석
  trl = "TRL 6 (체계통합 입증)" if "TRL 6" in combined or "시작품" in combined else \
          "TRL 5 (시험평가 환경)" if "TRL 5" in combined or "환경시험" in combined else \
          "TRL 4 이하 (개념연구)"

  # 2. 적용 환경시험 규격 식별
  standards = []
  if "MIL-STD-810" in combined or "환경시험" in combined:
    standards.append("MIL-STD-810 (환경공학 시험)")
  if "MIL-STD-461" in combined or "EMI" in combined or "EMC" in combined:
    standards.append("MIL-STD-461 (전자파 적합성)")
  if "MIL-HDBK-217" in combined or "MTBF" in combined or "수명" in combined:
    standards.append("MIL-HDBK-217 / 가속수명시험(ALT)")
  if not standards:
    standards.append("국방규격(KDS) 일반 요건 준용")

  # 3. 환경 가혹도 및 신뢰성 시험 항목 추출
  scope_items = []
  if any(k in combined for k in ["함정", "잠수함", "수중", "염무", "방수"]):
    scope_items.append("해양 환경 (염무, 침수, 충격진동, 조진 규격)")
  if any(k in combined for k in ["고온", "저온", "열충격", "열피로"]):
    scope_items.append("온습도 스트레스 (고온/저온 작동 및 열충격)")
  if any(k in combined for k in ["진동", "충격", "발사충격"]):
    scope_items.append("기계적 스트레스 (랜덤진동, 기능충격, 화약충격)")
  if not scope_items:
    scope_items.append("기본 신뢰도 시험 및 번인(Burn-in)")

  # 4. 사내 시험실 인프라 적합성 판정 및 조치 의견
  if "해양 환경" in scope_items and "기계적 스트레스" in scope_items:
    status = "검토 요망 (복합 스트레스)"
    opinion = (
        "복합 내환경성(함정 진동/충격 및 염무) 테일러링 계획 수립 필수. "
        "사내 대형 복합 진동챔버 가용 일정 확인 및 사전 치구(Jig) 제작 검토 요망."
    )
  elif "MIL-STD-810" in standards[0]:
    status = "수행 적합"
    opinion = (
        "통상적인 MIL-STD-810 환경시험 챔버 및 진동시험기로 평가 수행 가능. "
        "LCEP(수명주기 환경프로파일) 기반 시험 절차 테일러링 즉시 착수 가능."
    )
  else:
    status = "일반 관리"
    opinion = "기본 성능 검증 및 기초 규격 적합성 확인 중심 모니터링."

  return {
      "target_trl": trl,
      "env_standards": ", ".join(standards),
      "reliability_scope": ", ".join(scope_items),
      "feasibility_status": status,
      "expert_opinion": opinion,
  }


def run_defense_intelligence():
  """국방 R&D 사업 공고 가상 유입 및 진단 실행"""
  init_defense_db()

  # 실제 수집될 가상 공고 데이터셋 (방사청/국기연/ADD 공고 패턴)
  sample_announcements = [
      {
          "title": (
              "[국기연 부품국산화] 차기 잠수함용 초음파 도플러 로그 모듈 신뢰성"
              " 향상 및 국산화 개발"
          ),
          "agency": "국방기술진흥연구소(KRIT)",
          "text": (
              "목표: 잠수함 탑재 센서 모듈의 국내 개발 및 환경시험평가. TRL 6"
              " 단계 달성 필수. MIL-STD-810H 해양 환경(수밀, 염무, 충격) 및"
              " MTBF 5,000시간 이상 입증 요건 포함."
          ),
      },
      {
          "title": (
              "[방사청 핵심기술] 유도무기 구동제어용 전력변환장치 환경 적응형"
              " 고신뢰성 제어기술"
          ),
          "agency": "방위사업청",
          "text": (
              "고온 및 급격한 발사 진동/열충격 환경에서 동작하는 전력제어기"
              " 개발. MIL-STD-461 전자파 차폐 및 MIL-STD-810 진동시험 충족"
              " 요함."
          ),
      },
      {
          "title": "[ADD 개념연구] 차세대 복합 전자기 차폐 복합소재 물성 분석",
          "agency": "국방과학연구소(ADD)",
          "text": (
              "기초 원천기술 연구로 TRL 3 단계 목표. 시험평가보다는 시뮬레이션"
              " 및 기본 시편 물성 측정이 주를 이룸."
          ),
      },
  ]

  print(
      "=== 국방 R&D 기술력 및 신뢰성 시험 요구도 딥트윈 진단 가동 ==="
  )

  with sqlite3.connect(DB_NAME) as conn:
    cur = conn.cursor()
    for item in sample_announcements:
      eval_res = deeptwin_defense_evaluator(item)

      cur.execute(
          """
                INSERT INTO defense_rnd_radar 
                (announcement_title, agency, target_trl, env_standards, reliability_scope, feasibility_status, expert_opinion, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
          (
              item["title"],
              item["agency"],
              eval_res["target_trl"],
              eval_res["env_standards"],
              eval_res["reliability_scope"],
              eval_res["feasibility_status"],
              eval_res["expert_opinion"],
              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          ),
      )

      print(f"\n[발주처: {item['agency']}] {item['title']}")
      print(f"  ├ 요구 TRL: {eval_res['target_trl']}")
      print(f"  ├ 적용 규격: {eval_res['env_standards']}")
      print(f"  ├ 환경시험 범위: {eval_res['reliability_scope']}")
      print(f"  ├ 적합성 판정: [{eval_res['feasibility_status']}]")
      print(f"  └ 엔지니어 조치 의견: {eval_res['expert_opinion']}")

    conn.commit()
    print(
        "\n[완료] 국방 R&D 신뢰성 분석 데이터가 defense_rnd_radar 테이블에"
        " 저장되었습니다."
    )


if __name__ == "__main__":
  run_defense_intelligence()