import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from client_request import send_event_on_created, send_event_on_modified, send_event_on_deleted, send_event_on_moved, upload_file

class MyHandler(FileSystemEventHandler):
    # 處理檔案系統事件

    def __init__(self):
        super().__init__()
        self.count = 0

    def on_created(self, event):
        if event.is_directory:
            print(f"[建立] 新增資料夾：{event.src_path}")
            send_event_on_created("creat_directory", event.src_path)
        if not event.is_directory:  
            print(f"[建立] 檔案：{event.src_path}")
            send_event_on_created("creat_file", event.src_path)
            upload_file(event.src_path)

    def on_modified(self, event):
        # modify資料夾名稱暫定歸類在on_moved函數
        if not event.is_directory:
            print(f"[修改] 檔案：{event.src_path}")
            send_event_on_modified("modify_file", event.src_path)
            upload_file(event.src_path)

    def on_deleted(self, event):
        # 刪除資料夾與刪除檔案好像無差別
        if not event.is_directory:
            print(f"[刪除] 檔案：{event.src_path}")
            send_event_on_deleted("delete_file", event.src_path)

    def on_moved(self, event):
        # modify檔案名稱
        if event.is_directory:
            print(f"[搬移] 移動資料夾：{event.src_path} → {event.dest_path}")
            send_event_on_moved("move_directory", event.src_path, event.dest_path)
        if not event.is_directory:
            print(f"[搬移] 檔案：{event.src_path} → {event.dest_path}")
            send_event_on_moved("move_file", event.src_path, event.dest_path)
            upload_file(event.src_path)

if __name__ == "__main__":
    # 要監控的目錄（也可改成相對路徑或從命令列參數讀入）
    path_to_watch = "monitor\\"

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
