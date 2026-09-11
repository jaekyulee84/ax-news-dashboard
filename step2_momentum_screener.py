import os
import pandas as pd
import numpy as np

# 기본 설정 (자금 관리 및 환율)
TOTAL_CAPITAL_KRW = 33_000_000  # 총 운용 자금
MAX_POSITION_RATIO = 0.10       # 종목당 최대 비중 10%
USD_KRW_RATE = 1380             # 적용 환율
DATA_DIR = "market_data"

def calculate_indicators(df):
    df = df.copy()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()
    df['High_20_prev'] = df['High'].shift(1).rolling(window=20).max()
    df['Pct_Change'] = df['Close'].pct_change() * 100
    df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA_20']
    return df

def check_condition(row):
    """조건 만족 여부 판정"""
    cond_trend = (row['SMA_20'] > row['SMA_50']) and (row['Close'] > row['SMA_20'])
    cond_momentum = (row['Pct_Change'] >= 5.0) or (row['Close'] > row['High_20_prev'])
    cond_volume = row['Vol_Ratio'] >= 1.5
    candle_range = row['High'] - row['Low']
    cond_candle = (row['Close'] > row['Open']) and (
        candle_range == 0 or ((row['Close'] - row['Low']) / candle_range >= 0.6)
    )
    is_passed = cond_trend and cond_momentum and cond_volume and cond_candle
    return is_passed, cond_trend, cond_momentum, cond_volume, cond_candle

def screen_momentum_stocks():
    max_capital_per_stock = TOTAL_CAPITAL_KRW * MAX_POSITION_RATIO
    
    if not os.path.exists(DATA_DIR):
        print(f"오류: {DATA_DIR} 폴더가 없습니다.")
        return

    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
    
    latest_date_str = ""
    latest_status_list = []
    recent_5days_hits = []

    for file in csv_files:
        ticker = file.replace('.csv', '')
        if ticker in ["SOXX", "SMH"]:
            continue
            
        file_path = os.path.join(DATA_DIR, file)
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        if len(df) < 50:
            continue
            
        df = calculate_indicators(df)
        
        # 1. 가장 최근 거래일 분석
        latest = df.iloc[-1]
        latest_date_str = latest.name.strftime('%Y-%m-%d')
        passed, c_tr, c_mo, c_vo, c_ca = check_condition(latest)
        
        latest_status_list.append({
            'Ticker': ticker,
            'Close': latest['Close'],
            'Change': latest['Pct_Change'],
            'Vol_Ratio': latest['Vol_Ratio'],
            'Trend': "O" if c_tr else "X",
            'Momentum': "O" if c_mo else "X",
            'Volume': "O" if c_vo else "X",
            'Candle': "O" if c_ca else "X",
            'Passed': passed
        })
        
        # 2. 최근 5거래일 중 조건 충족 이력 탐색
        for i in range(-5, -1):
            if abs(i) <= len(df):
                hist_row = df.iloc[i]
                h_passed, _, _, _, _ = check_condition(hist_row)
                if h_passed:
                    recent_5days_hits.append({
                        'Date': hist_row.name.strftime('%Y-%m-%d'),
                        'Ticker': ticker,
                        'Close': hist_row['Close'],
                        'Change': hist_row['Pct_Change'],
                        'Vol_Ratio': hist_row['Vol_Ratio']
                    })

    print(f"\n=========================================================================")
    print(f"  최근 정규장 마감일({latest_date_str}) 전체 종목 현황표 (상승률 순)")
    print(f"=========================================================================")
    status_df = pd.DataFrame(latest_status_list).sort_values(by='Change', ascending=False)
    
    print(f"{'티커':<6} | {'종가($)':<9} | {'등락률(%)':<9} | {'거래량배율':<8} | {'추세':<4} | {'모멘텀':<4} | {'거래량':<4} | {'캔들':<4} | {'결과'}")
    print("-" * 75)
    for _, r in status_df.iterrows():
        res_text = "★ 포착" if r['Passed'] else "대기"
        print(f"{r['Ticker']:<6} | ${r['Close']:<8.2f} | {r['Change']:>+7.2f}% | {r['Vol_Ratio']:>6.2f}배 | {r['Trend']:^4} | {r['Momentum']:^6} | {r['Volume']:^6} | {r['Candle']:^4} | {res_text}")

    # 오늘 포착 종목 출력
    today_hits = status_df[status_df['Passed'] == True]
    if not today_hits.empty:
        print(f"\n★ 당일 포착 종목:")
        for _, c in today_hits.iterrows():
            shares = int(max_capital_per_stock // (c['Close'] * USD_KRW_RATE))
            print(f" - [{c['Ticker']}] 종가: ${c['Close']:.2f} | 추천매수: {shares}주 (약 {shares*c['Close']*USD_KRW_RATE:,.0f}원)")
            print(f"   손절(-5%): ${c['Close']*0.95:.2f} | 1차익절(+10%): ${c['Close']*1.10:.2f}")

    # 최근 5일간 포착 이력 출력
    print(f"\n=========================================================================")
    print(f"  최근 5거래일 동안 조건이 포착되었던 종목 이력 (참고용)")
    print(f"=========================================================================")
    if recent_5days_hits:
        for h in recent_5days_hits:
            print(f" - [{h['Date']}] {h['Ticker']:<5} | 종가: ${h['Close']:.2f} | 등락률: {h['Change']:>+5.2f}% | 거래량: {h['Vol_Ratio']:.1f}배")
    else:
        print("최근 5거래일 동안에도 해당 조건을 모두 충족한 종목이 없었습니다.")
    print("=========================================================================\n")

if __name__ == "__main__":
    screen_momentum_stocks()