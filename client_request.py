import os
import time
import json
import requests

SERVER_EVENT_receive_URL        = "http://localhost:8000/api/v1/event/receive"
SERVER_EVENT_delete_file_URL    = "http://localhost:8000/api/v1/event/delete_file"
SERVER_EVENT_upload_file_URL    = "http://localhost:8000/api/v1/event/upload_file"
SERVER_EVENT_upload_folder_URL  = "http://localhost:8000/api/v1/event/upload_folder"

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
    
    files = {'file': (os.path.basename(src_path), open(src_path, 'rb'))}
    try:
        resp = requests.post(
            SERVER_EVENT_upload_file_URL,
            files=files,
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
            SERVER_EVENT_upload_folder_URL,
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
            SERVER_EVENT_delete_file_URL,
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
            SERVER_EVENT_receive_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=5
        )
        resp.raise_for_status()
        print(f"[OK] Sent {payload['event_type']} → server")
    except Exception as e:
        print(f"[ERROR] Failed to send event: {e}")