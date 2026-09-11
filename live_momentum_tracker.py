import os
from datetime import datetime
import pandas as pd
import yfinance as yf

# 자금 관리 및 4회 분할 매수 설정
TOTAL_CAPITAL_KRW = 33_000_000   # 총 운용 자금
MAX_POSITION_RATIO = 0.10        # 종목당 총 한도 10% (330만 원)
SPLIT_COUNT = 4                  # 4회 분할 매수
TRANCHE_KRW = (TOTAL_CAPITAL_KRW * MAX_POSITION_RATIO) / SPLIT_COUNT  # 1회차 진입금: 825,000원
USD_KRW_RATE = 1380              # 적용 환율
DATA_DIR = "market_data"

SEMI_TICKERS = [
    "NVDA", "AMD", "AVGO", "MRVL", "ARM", "QCOM",
    "MU", "WDC", "TSM", "INTC",
    "ASML", "AMAT", "LRCX", "KLAC", "TER", "AMKR",
    "TXN", "ADI", "ON", "MPWR"
]

def load_technical_baseline():
    baseline = {}
    for ticker in SEMI_TICKERS:
        file_path = os.path.join(DATA_DIR, f"{ticker}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            if len(df) >= 50:
                sma_20 = df['Close'].rolling(20).mean().iloc[-1]
                sma_50 = df['Close'].rolling(50).mean().iloc[-1]
                vol_sma_20 = df['Volume'].rolling(20).mean().iloc[-1]
                prev_high_20 = df['High'].iloc[-21:-1].max()
                prev_close = df['Close'].iloc[-1]
                
                baseline[ticker] = {
                    'SMA_20': sma_20,
                    'SMA_50': sma_50,
                    'Vol_SMA_20': vol_sma_20,
                    'Prev_High_20': prev_high_20,
                    'Prev_Close': prev_close,
                    'Trend_OK': (sma_20 > sma_50)
                }
    return baseline

def scan_safe_momentum():
    baseline = load_technical_baseline()
    
    print(f"\n==========================================================================================")
    print(f"   [안전 분할매수 모멘텀 레이더] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 기준")
    print(f"   (종목당 총 한도: 330만 원 | 1회차 진입금: {int(TRANCHE_KRW):,}원 | 총 4회 분할)")
    print(f"==========================================================================================")
    print(f"{'티커':<6} | {'현재가($)':<9} | {'등락률(%)':<9} | {'20일선추세':<8} | {'1회차 진입 추천'}")
    print("-" * 88)

    candidates = []

    for ticker in SEMI_TICKERS:
        try:
            stock = yf.Ticker(ticker)
            info = stock.fast_info
            curr_price = float(info['lastPrice'])
            prev_close = float(info['previousClose'])
            pct_change = ((curr_price - prev_close) / prev_close) * 100

            base = baseline.get(ticker, {})
            trend_ok = base.get('Trend_OK', False)
            trend_str = "우상향(정배열)" if trend_ok else "역배열/혼조"
            
            # 1회차 매수 가능 주수 계산 (1회당 82.5만 원 기준)
            price_krw = curr_price * USD_KRW_RATE
            shares_per_tranche = max(1, int(TRANCHE_KRW // price_krw))
            total_shares_limit = shares_per_tranche * SPLIT_COUNT
            
            # 안전 진입 조건 (추세 정배열 + 상승률 3.5% 이상)
            if pct_change >= 3.5 and trend_ok:
                signal_desc = f"★ 1차 진입 가능 ({shares_per_tranche}주)"
                candidates.append({
                    'Ticker': ticker,
                    'Price': curr_price,
                    'Change': pct_change,
                    'Tranche_Shares': shares_per_tranche,
                    'Tranche_KRW': int(shares_per_tranche * price_krw),
                    'Total_Shares': total_shares_limit,
                    'Stop_5': round(curr_price * 0.95, 2),
                    'Target_10': round(curr_price * 1.10, 2)
                })
            elif pct_change >= 1.5:
                signal_desc = "관찰 (상승 시동)"
            else:
                signal_desc = "대기"

            print(f"{ticker:<6} | ${curr_price:<8.2f} | {pct_change:>+7.2f}% | {trend_str:<10} | {signal_desc}")
            
        except Exception:
            continue

    print("-" * 88)
    if candidates:
        print(f"\n★ [오늘 밤 1차 분할 매수 검토 종목: 총 {len(candidates)}개]\n")
        for c in candidates:
            risk_krw = int(c['Tranche_KRW'] * 0.05)
            print(f"▶ [{c['Ticker']}] 현재가: ${c['Price']:.2f} ({c['Change']:+.2f}%)")
            print(f"   - [1차 매수량] : {c['Tranche_Shares']}주 (약 {c['Tranche_KRW']:,}원 투입)")
            print(f"   - [총 한도량]  : 최대 {c['Total_Shares']}주 (4회 분할 완료 시 약 330만 원)")
            print(f"   - [1차 손절가] : ${c['Stop_5']} (-5% 도달 시 손절 / 계좌 손실 단 {risk_krw:,}원)")
            print(f"   - [목표 익절가]: ${c['Target_10']} (+10% 도달 시 프리마켓/본장 분할 익절)")
            print(f"   - [2차 진입조건]: 1차 매수가 대비 +2% 이상 추가 상승 시 2회차({c['Tranche_Shares']}주) 불타기")
            print("-" * 65)
    else:
        print("\n현재 조건(정배열 + 3.5% 이상 상승)을 충족하는 종목이 없습니다. (본장 개장 후 확인 권장)")

if __name__ == "__main__":
    scan_safe_momentum()