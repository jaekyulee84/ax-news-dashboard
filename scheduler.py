from datetime import datetime
import time
from crawler import fetch_news_data, init_db, save_to_db
import schedule


def job():
  print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 정기 크롤링 실행")
  init_db()
  data = fetch_news_data()
  save_to_db(data)


# 1) 테스트용: 10초마다 실행 (정상 동작 확인 후 주석 처리)
schedule.every(10).seconds.do(job)

# 2) 실무용 설정 예시 (필요한 주기로 활성화):
# schedule.every(1).hours.do(job)              # 1시간마다
# schedule.every().day.at("09:00").do(job)       # 매일 아침 9시마다

if __name__ == "__main__":
  print("=== 크롤링 스케줄러 가동 (종료: Ctrl + C) ===")
  # 시작 시 최초 1회 즉시 실행
  job()

  while True:
    schedule.run_pending()
    time.sleep(1)