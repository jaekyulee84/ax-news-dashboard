import os
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# 1. 반도체 핵심 유니버스 티커 리스트 정의
SEMI_TICKERS = [
    # AI / 팹리스
    "NVDA", "AMD", "AVGO", "MRVL", "ARM", "QCOM",
    # 메모리 / 스토리지
    "MU", "WDC",
    # 파운드리
    "TSM", "INTC",
    # 장비 / 패키징
    "ASML", "AMAT", "LRCX", "KLAC", "TER", "AMKR",
    # 아날로그 / 전력
    "TXN", "ADI", "ON", "MPWR",
    # 벤치마크 ETF
    "SOXX", "SMH"
]

def fetch_regular_market_data(tickers, period_years=2, save_dir="market_data"):
    """
    정규장 일봉(OHLCV) 데이터를 수집하여 개별 CSV 및 통합 데이터로 저장합니다.
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    end_date = datetime.today()
    start_date = end_date - timedelta(days=period_years * 365)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 정규장 데이터 수집 시작 ({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})")
    
    collected_data = {}
    
    for ticker in tickers:
        try:
            # yfinance는 기본적으로 정규장(Regular Market) 일봉 데이터를 제공합니다.
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), interval="1d")
            
            if df.empty:
                print(f"경고: {ticker} 데이터가 비어 있습니다.")
                continue
                
            # 불필요한 배당/분할 컬럼 정리 및 날짜 포맷팅
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            df.index = pd.to_datetime(df.index).tz_localize(None) # 타임존 제거로 깔끔하게 정리
            
            # 종목별 CSV 저장
            file_path = os.path.join(save_dir, f"{ticker}.csv")
            df.to_csv(file_path)
            
            collected_data[ticker] = df
            print(f"성공: {ticker:<5} | 데이터 수: {len(df):>4}일치 수집 완료")
            
        except Exception as e:
            print(f"실패: {ticker} 수집 중 오류 발생 - {e}")
            
    print(f"\n총 {len(collected_data)}/{len(tickers)}개 종목의 데이터 수집이 완료되었습니다.")
    return collected_data

if __name__ == "__main__":
    data = fetch_regular_market_data(SEMI_TICKERS)