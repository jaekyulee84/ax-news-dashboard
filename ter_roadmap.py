from datetime import datetime
import yfinance as yf

# 기본 설정값
TICKER = "TER"
BASE_PRICE = 374.95       # 1차 매수 체결가 ($)
USD_KRW_RATE = 1380       # 환율
TOTAL_CAPITAL = 33_000_000

# 4단계 분할 매수 계획 (비율: 1주 -> 1주 -> 2주 -> 2주 = 총 6주, 약 325만 원)
ROADMAP = [
    {
        "tranche": 1,
        "trigger_pct": 0.0,
        "shares": 1,
        "desc": "오늘 1차 진입 (완료)",
        "stop_rule": "진입가 대비 -5% 이탈 시 칼손절"
    },
    {
        "tranche": 2,
        "trigger_pct": 2.5,
        "shares": 1,
        "desc": "추세 지속 확인 (+2.5% 도달 시)",
        "stop_rule": "손절선을 1차 매수가(본전)로 상향"
    },
    {
        "tranche": 3,
        "trigger_pct": 5.0,
        "shares": 2,
        "desc": "시세 안착 (+5.0% 돌파 시)",
        "stop_rule": "손절선을 2차 매수가 부근으로 상향"
    },
    {
        "tranche": 4,
        "trigger_pct": 7.5,
        "shares": 2,
        "desc": "최종 비중 완성 (+7.5% 도달 시)",
        "stop_rule": "손절선을 +3% 수익 보전선으로 올려 이익 확보"
    }
]

def show_roadmap():
    # 실시간 현재가 조회
    curr_price = BASE_PRICE
    curr_change = 0.0
    try:
        stock = yf.Ticker(TICKER)
        curr_price = float(stock.fast_info['lastPrice'])
        curr_change = ((curr_price - BASE_PRICE) / BASE_PRICE) * 100
    except Exception:
        pass

    print(f"\n==========================================================================================================")
    print(f"      [TER(테라다인) 4회차 분할 매수 로드맵] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   * 1차 매수가: ${BASE_PRICE:.2f}  |  현재 실시간 가격: ${curr_price:.2f} ({curr_change:+.2f}%)")
    print(f"   * 계좌 총액: {TOTAL_CAPITAL:,}원  |  종목 최대 한도: 3,300,000원 (총 6주 완결 목표)")
    print(f"==========================================================================================================")
    print(f"{'회차':<4} | {'진입 조건':<13} | {'매수가($)':<9} | {'주수':<4} | {'누적주수':<6} | {'새 평단가':<9} | {'누적투자금(원)':<13} | {'방어 손절가':<10} | {'손절 시 손익(원)'}")
    print("-" * 106)

    cum_shares = 0
    cum_cost = 0.0

    # 각 단계별 방어 손절 기준가
    stop_prices = [
        round(BASE_PRICE * 0.95, 2),  # 1차 손절: $356.20 (-5%)
        round(BASE_PRICE * 1.00, 2),  # 2차 손절: $374.95 (본전 방어)
        384.32,                       # 3차 손절: 2차 매수가 지점
        393.70                        # 4차 손절: 수익 확정 라인
    ]

    for item, stop_p in zip(ROADMAP, stop_prices):
        t = item['tranche']
        target_p = round(BASE_PRICE * (1 + item['trigger_pct'] / 100), 2)
        sh = item['shares']
        
        cum_shares += sh
        cum_cost += target_p * sh
        avg_p = cum_cost / cum_shares
        cum_krw = cum_cost * USD_KRW_RATE
        
        # 해당 단계에서 손절 시 예상 손익
        pnl_at_stop = (stop_p - avg_p) * cum_shares * USD_KRW_RATE
        sign = "+" if pnl_at_stop >= 0 else ""

        print(f"{t}차  | {item['desc']:<14} | ${target_p:<8.2f} | {sh}주  | {cum_shares}주    | ${avg_p:<8.2f} | {cum_krw:>11,.0f}원 | ${stop_p:<8.2f} | {sign}{pnl_at_stop:>10,.0f}원")

    # 최종 +10% 익절 목표
    take_profit_10 = round(BASE_PRICE * 1.10, 2)
    final_profit_krw = (take_profit_10 - avg_p) * cum_shares * USD_KRW_RATE
    
    print("-" * 106)
    print(f"★ 최종 목표가 (+10% 익절) : ${take_profit_10:.2f} (프리마켓/본장 도달 시 전량/분할 익절)")
    print(f"★ 6주 비중 완성 후 +10% 달성 시 예상 순수익: 약 +{final_profit_krw:,.0f}원")
    print(f"==========================================================================================================\n")

    # 다음 행동 가이드
    next_target = round(BASE_PRICE * 1.025, 2)
    diff = next_target - curr_price
    if curr_price < next_target:
        print(f"▶ [현재 상황]: 1차 1주 보유 중입니다.")
        print(f"▶ [2차 매수 가격]: ${next_target:.2f} (현재가 대비 +${diff:.2f} 추가 상승 시 1주 추가 매수)")
        print(f"▶ [1차 손절 라인]: ${stop_prices[0]:.2f} (-5% 이탈 시에만 매도, 그전엔 편안히 홀딩)")
    else:
        print(f"▶ 2차 매수 목표가(${next_target:.2f})에 도달했습니다! 내일장 확인 후 1주 추가 매수를 검토하세요.")

if __name__ == "__main__":
    show_roadmap()