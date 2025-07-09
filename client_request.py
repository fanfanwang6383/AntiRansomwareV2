import os
import time
import json
import requests

SERVER_EVENT_receive_URL = "http://localhost:8000/api/v1/event/receive"
SERVER_EVENT_upload_URL  = "http://localhost:8000/api/v1/event/upload_file"

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

def upload_file(src_path):
    if not os.path.isfile(src_path):
        print(f"[ERROR] File not found: {src_path}")
        return
    
    files = {'file': (os.path.basename(src_path), open(src_path, 'rb'))}
    try:
        resp = requests.post(
            SERVER_EVENT_upload_URL,
            files=files,
            timeout=10
        )
        resp.raise_for_status()
        print(f"[OK] Uploaded {os.path.basename(src_path)} → server: {resp.json()}")
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")

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