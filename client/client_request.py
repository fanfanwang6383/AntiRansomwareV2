import os
import time
import json
import requests
from config_manager import *

config = load_config()

monitor_path = config["client"]["MONITOR_PATH"]
SERVER_IP = config['server']['SERVER_IP']
SERVER_PORT = config['server']['SERVER_PORT']
BASE_API_URL = f"http://{SERVER_IP}:{SERVER_PORT}/api/v1/event"
RECEIVE_API = f"{BASE_API_URL}/receive"
DELETE_FILE_API = f"{BASE_API_URL}/delete_file"
UPLOAD_FILE_API = f"{BASE_API_URL}/upload_file"
UPLOAD_FOLDER_API = f"{BASE_API_URL}/upload_folder"
TREE_API = f"http://{SERVER_IP}:{SERVER_PORT}/api/v1/tree"

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
        print(f"[OK] File recovery requested for {file_name} → server: {resp.json()}")
    except Exception as e:
        print(f"[ERROR] File recovery request failed: {e}")

def get_tree_from_server():
    """
    從server獲取最新的tree.json資料
    """
    try:
        resp = requests.get(TREE_API, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if result.get("status") == "success":
            return result.get("tree_data", {})
        else:
            print(f"[ERROR] Server returned error: {result}")
            raise Exception(f"Server returned error: {result}")
    except Exception as e:
        print(f"[ERROR] Failed to get tree from server: {e}")
        raise  # 重新拋出異常，讓上層處理

def send_added_files_to_server(added_items):
    """
    發送新增檔案事件給server
    同時上傳檔案和metadata
    """
    files = []
    
    # 對每個新增項目處理檔案上傳
    for item in added_items:
        if item['type'] == 'file':
            file_path = os.path.join(monitor_path, item['path'])
            if os.path.exists(file_path):
                files.append(
                    ('files', (item['path'], open(file_path, 'rb')))
                )

    # 準備metadata
    metadata = {
        "added_items": added_items,
        "timestamp": int(time.time())
    }
    
    try:
        # 移除 Content-Type header，讓 requests 自動設定
        resp = requests.post(
            f"{BASE_API_URL}/added_files",
            files=files,
            data={'metadata': json.dumps(metadata)},
            timeout=30  # 增加timeout以處理多個檔案上傳
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("status") == "success":
            print(f"[OK] Added files sent to server: {len(added_items)} files")
        else:
            print(f"[ERROR] Server returned error: {result}")
    except Exception as e:
        print(f"[ERROR] Failed to send added files to server: {e}")

def send_modified_files_to_server(modified_items):
    """
    發送修改檔案事件給server
    """
    payload = {
        "modified_items": modified_items,
        "timestamp": int(time.time())
    }
    
    try:
        resp = requests.post(
            f"{BASE_API_URL}/modified_files",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("status") == "success":
            print(f"[OK] Modified files sent to server: {len(modified_items)} files")
        else:
            print(f"[ERROR] Server returned error: {result}")
    except Exception as e:
        print(f"[ERROR] Failed to send modified files to server: {e}")

def send_deleted_files_to_server(deleted_items):
    """
    發送刪除檔案事件給server
    """
    payload = {
        "deleted_items": deleted_items,
        "timestamp": int(time.time())
    }
    
    try:
        resp = requests.post(
            f"{BASE_API_URL}/deleted_files",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("status") == "success":
            print(f"[OK] Deleted files sent to server: {len(deleted_items)} files")
        else:
            print(f"[ERROR] Server returned error: {result}")
    except Exception as e:
        print(f"[ERROR] Failed to send deleted files to server: {e}")

def send_changes_to_server(added_items, modified_items, deleted_items):
    """
    發送變更事件給server (保留舊函數以向後相容)
    """
    payload = {
        "added_items": added_items,
        "modified_items": modified_items,
        "deleted_items": deleted_items,
        "timestamp": int(time.time())
    }
    
    try:
        resp = requests.post(
            f"{BASE_API_URL}/changes",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("status") == "success":
            print(f"[OK] Changes sent to server: {len(added_items)} added, {len(modified_items)} modified, {len(deleted_items)} deleted")
        else:
            print(f"[ERROR] Server returned error: {result}")
    except Exception as e:
        print(f"[ERROR] Failed to send changes to server: {e}")

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