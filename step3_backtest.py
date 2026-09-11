import os
import pandas as pd
import numpy as np

DATA_DIR = "market_data"
FEE_RATE = 0.0015  # 왕복 거래 수수료 0.15%

def run_backtest(vol_threshold=1.25, max_hold_days=20, take_profit=0.10, stop_loss=0.05):
    """
    미국 반도체 유니버스 대상 모멘텀 스윙 백테스트 수행
    """
    if not os.path.exists(DATA_DIR):
        print(f"오류: {DATA_DIR} 폴더를 찾을 수 없습니다.")
        return

    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
    all_trades = []

    for file in csv_files:
        ticker = file.replace('.csv', '')
        if ticker in ["SOXX", "SMH"]:
            continue
            
        df = pd.read_csv(os.path.join(DATA_DIR, file), index_col=0, parse_dates=True)
        if len(df) < 60:
            continue
            
        # 기술적 지표 계산
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()
        df['High_20_prev'] = df['High'].shift(1).rolling(window=20).max()
        df['Pct_Change'] = df['Close'].pct_change() * 100
        df['Vol_Ratio'] = df['Volume'] / df['Vol_SMA_20']

        # 조건 탐색
        in_trade = False
        entry_idx = 0
        entry_price = 0.0
        
        for i in range(50, len(df) - 1):
            if not in_trade:
                row = df.iloc[i]
                
                # 조건 체크
                cond_trend = (row['SMA_20'] > row['SMA_50']) and (row['Close'] > row['SMA_20'])
                cond_momentum = (row['Pct_Change'] >= 5.0) or (row['Close'] > row['High_20_prev'])
                cond_volume = row['Vol_Ratio'] >= vol_threshold
                candle_range = row['High'] - row['Low']
                cond_candle = (row['Close'] > row['Open']) and (
                    candle_range == 0 or ((row['Close'] - row['Low']) / candle_range >= 0.6)
                )

                if cond_trend and cond_momentum and cond_volume and cond_candle:
                    # 익일 시가로 진입
                    in_trade = True
                    entry_idx = i + 1
                    entry_price = df.iloc[i + 1]['Open']
                    entry_date = df.index[i + 1]
            else:
                # 보유 중인 경우 청산 조건 체크
                curr_bar = df.iloc[i]
                days_held = i - entry_idx + 1
                exit_price = None
                exit_reason = ""

                # 1. 손절 조건 우선 체크 (보수적 접근)
                if curr_bar['Low'] <= entry_price * (1 - stop_loss):
                    exit_price = entry_price * (1 - stop_loss)
                    exit_reason = "손절(-5%)"
                # 2. 익절 조건 체크 (+10%)
                elif curr_bar['High'] >= entry_price * (1 + take_profit):
                    exit_price = entry_price * (1 + take_profit)
                    exit_reason = "익절(+10%)"
                # 3. 최대 보유 기간 경과 (시간 청산)
                elif days_held >= max_hold_days:
                    exit_price = curr_bar['Close']
                    exit_reason = "기간만료"

                if exit_price is not None:
                    pnl_pct = ((exit_price - entry_price) / entry_price) - FEE_RATE
                    all_trades.append({
                        'Ticker': ticker,
                        'Entry_Date': entry_date.strftime('%Y-%m-%d'),
                        'Exit_Date': curr_bar.name.strftime('%Y-%m-%d'),
                        'Hold_Days': days_held,
                        'Entry_Price': entry_price,
                        'Exit_Price': exit_price,
                        'Return_Pct': pnl_pct * 100,
                        'Reason': exit_reason,
                        'Is_Win': pnl_pct > 0
                    })
                    in_trade = False

    return pd.DataFrame(all_trades)

def print_summary(trades_df, title):
    print(f"\n==================================================================")
    print(f"   {title}")
    print(f"==================================================================")
    if trades_df.empty:
        print("체결된 거래가 없습니다.")
        return

    total_trades = len(trades_df)
    wins = trades_df[trades_df['Is_Win']]
    losses = trades_df[~trades_df['Is_Win']]
    
    win_rate = (len(wins) / total_trades) * 100
    avg_return = trades_df['Return_Pct'].mean()
    total_cum_return = trades_df['Return_Pct'].sum()
    avg_hold = trades_df['Hold_Days'].mean()
    
    total_gain = wins['Return_Pct'].sum() if not wins.empty else 0
    total_loss = abs(losses['Return_Pct'].sum()) if not losses.empty else 1
    profit_factor = (total_gain / total_loss) if total_loss > 0 else 0

    print(f" - 총 매매 횟수       : {total_trades}회")
    print(f" - 승률 (Win Rate)    : {win_rate:.1f}% ({len(wins)}승 {len(losses)}패)")
    print(f" - 손익비 (Profit Factor): {profit_factor:.2f}")
    print(f" - 건당 평균 수익률   : {avg_return:+.2f}%")
    print(f" - 단순 누적 수익률   : {total_cum_return:+.2f}%")
    print(f" - 평균 보유 기간     : {avg_hold:.1f}거래일 (약 {avg_hold/5:.1f}주)")
    print(f" - 청산 유형 분석     :")
    for reason, count in trades_df['Reason'].value_counts().items():
        print(f"    * {reason:<8}: {count}회 ({count/total_trades*100:.1f}%)")

if __name__ == "__main__":
    print("과거 2년 치 반도체 유니버스 백테스팅 시뮬레이션 중...\n")
    
    # 케이스 1: 거래량 1.5배 기준 (엄격)
    df_15 = run_backtest(vol_threshold=1.5)
    print_summary(df_15, "1. 엄격 기준 (거래량 1.5배 폭발)")

    # 케이스 2: 거래량 1.25배 기준 (완화)
    df_125 = run_backtest(vol_threshold=1.25)
    print_summary(df_125, "2. 완화 기준 (거래량 1.25배 이상)")