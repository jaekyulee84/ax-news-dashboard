from datetime import datetime
import yfinance as yf

# 보유 종목 정보
MY_STOCK = "TER"
MY_ENTRY_PRICE = 374.95  # 1차 매수가
STOP_LOSS_PRICE = round(MY_ENTRY_PRICE * 0.95, 2)  # $356.20 (-5%)
TARGET_TRANCHE_2 = round(MY_ENTRY_PRICE * 1.025, 2) # $384.32 (+2.5%)

# 모니터링 대상 티커
WATCH_TICKERS = {
    "QQQ": "나스닥 100 지수",
    "SOXX": "필라델피아 반도체 지수",
    "SMH": "반도체 대형주 지수",
    MY_STOCK: "내 보유 종목 (테라다인)"
}

def get_market_status():
    prices = {}
    print(f"\n[실시간 시장 및 섹터 모니터링 뷰] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print(f"{'구분':<12} | {'티커':<6} | {'현재가($)':<9} | {'등락률(%)':<9} | {'시장 상태'}")
    print("-" * 75)

    for ticker, name in WATCH_TICKERS.items():
        try:
            stock = yf.Ticker(ticker)
            info = stock.fast_info
            curr_price = float(info['lastPrice'])
            prev_close = float(info['previousClose'])
            pct_change = ((curr_price - prev_close) / prev_close) * 100
            
            prices[ticker] = {
                'curr': curr_price,
                'change': pct_change
            }

            # 지수 상태 텍스트
            if pct_change >= 1.0:
                status = "강한 상승 (Green)"
            elif pct_change >= 0.0:
                status = "보합 / 완만한 상승"
            elif pct_change >= -1.5:
                status = "일반적 눌림 / 조정"
            elif pct_change >= -2.5:
                status = "★ 주의 (약세 심화)"
            else:
                status = "🚨 경보 (섹터 투매/폭락)"

            print(f"{name:<12} | {ticker:<6} | ${curr_price:<8.2f} | {pct_change:>+7.2f}% | {status}")
        except Exception:
            continue

    print("=" * 75)
    
    # 종합 분석 및 의사결정 시그널
    if MY_STOCK in prices and "SOXX" in prices:
        ter_data = prices[MY_STOCK]
        soxx_change = prices["SOXX"]['change']
        qqq_change = prices.get("QQQ", {}).get('change', 0.0)
        
        # 내 수익률 및 상대강도 계산
        my_pnl_pct = ((ter_data['curr'] - MY_ENTRY_PRICE) / MY_ENTRY_PRICE) * 100
        relative_strength = ter_data['change'] - soxx_change

        print(f"\n[TER 포지션 종합 진단]")
        print(f" - 1차 진입가: ${MY_ENTRY_PRICE:.2f}  |  현재가: ${ter_data['curr']:.2f} (수익률: {my_pnl_pct:+.2f}%)")
        print(f" - 반도체 지수(SOXX) 대비 상대강도: {relative_strength:+.2f}%p")
        if relative_strength > 0:
            print(f"   -> [양호] TER이 반도체 전체 지수보다 {relative_strength:.2f}%p 더 강하게 움직이고 있습니다. (주도주 흐름)")
        else:
            print(f"   -> [주의] TER이 반도체 전체 지수보다 {abs(relative_strength):.2f}%p 약하게 움직이고 있습니다.")

        print(f"\n[의사결정 가이드]")
        
        # 1. 시장 전체 폭락에 따른 조기 비상 손절 검토 규칙
        if soxx_change <= -2.5 or qqq_change <= -2.5:
            print(f" 🚨 [비상 탈출 경보]: 반도체(SOXX) 또는 나스닥이 -2.5% 이상 폭락 중입니다.")
            print(f"    -> TER이 아직 -5%에 닿지 않았더라도 시장 붕괴에 대비해 조기 매도(현금화)를 고려하세요.")
        
        # 2. 개별 종목 절대 손절 규칙
        elif ter_data['curr'] <= STOP_LOSS_PRICE:
            print(f" 🚨 [원칙 손절 실행]: TER 현재가가 -5% 손절선(${STOP_LOSS_PRICE})을 터치했습니다.")
            print(f"    -> 시장과 무관하게 1차 물량을 즉시 손절하세요.")

        # 3. 2차 매수(불타기) 조건
        elif ter_data['curr'] >= TARGET_TRANCHE_2 and soxx_change >= -0.5:
            print(f" ★ [2차 매수 신호]: TER이 2차 목표가(${TARGET_TRANCHE_2})에 도달했고 시장도 안정적입니다.")
            print(f"    -> 2차 1주 추가 매수를 검토하세요. (매수 후 손절선은 본전 ${MY_ENTRY_PRICE}로 상향)")
        
        # 4. 정상 홀딩
        else:
            print(f" ▶ [보유 유지 (HOLD)]: 시장과 종목 모두 정상 범위 내에 있습니다.")
            print(f"    - 손절 마지노선: ${STOP_LOSS_PRICE} (-5%)")
            print(f"    - 2차 매수 기준 : ${TARGET_TRANCHE_2} (+2.5%)")

if __name__ == "__main__":
    get_market_status()