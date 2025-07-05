import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MyHandler(FileSystemEventHandler):
    """自訂事件處理器，處理檔案系統事件"""

    def on_created(self, event):
        if not event.is_directory:
            print(f"[建立] 檔案：{event.src_path}")

    def on_modified(self, event):
        if not event.is_directory:
            print(f"[修改] 檔案：{event.src_path}")

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"[刪除] 檔案：{event.src_path}")

    def on_moved(self, event):
        if not event.is_directory:
            print(f"[搬移] 檔案：{event.src_path} → {event.dest_path}")

if __name__ == "__main__":
    # 要監控的目錄（也可改成相對路徑或從命令列參數讀入）
    path_to_watch = "monitor/"

    event_handler = MyHandler()
    observer = Observer()
    # schedule(handler, 要監控的路徑, recursive=True 表示要遞迴子目錄)
    observer.schedule(event_handler, path=path_to_watch, recursive=True)

    print(f"開始監控：{path_to_watch}")
    observer.start()

    try:
        while True:
            # 每秒檢查一次（也可做其他工作）
            time.sleep(1)
    except KeyboardInterrupt:
        # Ctrl+C 停止
        observer.stop()
    observer.join()
    print("監控結束")
