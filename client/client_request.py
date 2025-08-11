import os
import time
import json
import requests

RECEIVE_API  = "http://localhost:8000/api/v1/event/receive"
DELETE_FILE_API    = "http://localhost:8000/api/v1/event/delete_file"
UPLOAD_FILE_API    = "http://localhost:8000/api/v1/event/upload_file"
UPLOAD_FOLDER_API  = "http://localhost:8000/api/v1/event/upload_folder"

def send_event_on_created(event_type, src_path):
    payload = {
        "event_type": event_type,
        "src_path": src_path,
        "timestamp": int(time.time())
    }
    _post(payload)

def send_event_on_modified(event_type, src_path):
    payload = {
        "event_type": event_type,
        "src_path": src_path,
        "timestamp": int(time.time())
    }
    _post(payload)

def send_event_on_deleted(event_type, src_path):
    payload = {
        "event_type": event_type,
        "src_path": src_path,
        "timestamp": int(time.time())
    }
    _post(payload)

def send_event_on_moved(event_type, src_path, dest_path):
    payload = {
        "event_type": event_type,
        "src_path": src_path,
        "dest_path": dest_path,
        "timestamp": int(time.time())
    }
    _post(payload)

# 上傳檔案至server
def upload_file(src_path):
    if not os.path.isfile(src_path):
        print(f"[ERROR] File not found: {src_path}")
        return
    
    # 不含路徑的檔案名稱
    files = {'file': (os.path.basename(src_path), open(src_path, 'rb'))}
    # 不含檔案名稱的路徑
    data = {'file_path': os.path.dirname(src_path)}
    try:
        resp = requests.post(
            UPLOAD_FILE_API,
            files=files,
            data = data,
            timeout=10
        )
        resp.raise_for_status()
        print(f"[OK] Uploaded {os.path.basename(src_path)} → server: {resp.json()}")
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")

# 上傳資料夾至server
def upload_folder(src_path):
    if not os.path.isdir(src_path):
       print(f"[ERROR] Folder not found: {src_path}")
       return
    
    folder_name = os.path.basename(src_path.rstrip(os.sep))
    try:
        resp = requests.post(
            UPLOAD_FOLDER_API,
            json={"folder_name": folder_name},
            timeout=10
        )
        resp.raise_for_status()
        print(f"[OK] Folder uploaded {os.path.basename(src_path)} → server: {resp.json()}")
    except Exception as e:
        print(f"[ERROR] Folder upload failed: {e}")

def delete_file(src_path):
    file_name = os.path.basename(src_path.rstrip(os.sep))
    try:
        resp = requests.post(
            DELETE_FILE_API,
            json={"file_name": file_name},
            timeout=10
        )
        resp.raise_for_status()
        print(f"[OK] Folder uploaded {os.path.basename(src_path)} → server: {resp.json()}")
    except Exception as e:
        print(f"[ERROR] Folder upload failed: {e}")

def _post(payload):
    try:
        resp = requests.post(
            RECEIVE_API,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=5
        )
        resp.raise_for_status()
        print(f"[OK] Sent {payload['event_type']} → server")
    except Exception as e:
        print(f"[ERROR] Failed to send event: {e}")