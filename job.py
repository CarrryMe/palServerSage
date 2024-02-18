import threading
import SageServer
import schedule
import time

def save_back():
    SageServer.save_back(False)

# 设置每 5 分钟执行一次任务
schedule.every(5).minutes.at(":00").do(save_back)

def start_job():
    # 主循环，保持程序运行
    while True:
        schedule.run_pending()
        time.sleep(1)

def run():
    schedule_thread = threading.Thread(target=start_job)
    schedule_thread.start()