import os
import io
import json

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Google Drive 相關
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

app = Flask(__name__)

# OAuth2 用戶端與 Token 存放路徑
CREDS_PATH = './google_drive_api_json/client_secret_1006222831135-tc06e0j4rnlpsd07j3ilcii7h2a5i161.apps.googleusercontent.com.json'   # 從 GCP Console 下載的 OAuth client ID 檔案
TOKEN_PATH = './google_drive_api_json/token.json'         # 程式第一次授權後儲存的使用者 token
# 權限範圍，只限操作自己的檔案
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# 建立／取得使用者憑證
def get_user_credentials():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token_file:
            token_file.write(creds.to_json())
    return creds

# 建立憑證
# creds = get_user_credentials()
# 串連服務
# drive_service = build("drive", "v3", credentials=creds)

# 暫存資料夾位置
TEMP_DIRECTORY = os.getenv("STAGING_DIR", "./backup")
os.makedirs(TEMP_DIRECTORY, exist_ok=True)

# 從drive下載回server的暫存資料夾
RECOVER_DIRECTORY = os.getenv("STAGING_DIR", "./recover")
os.makedirs(RECOVER_DIRECTORY, exist_ok=True)

# 目標 Google Drive 子資料夾 ID
UPLOAD_FOLDER = '1XcWqHS1_C3GARVP7xlCrkfWm_BT1Km3e'

# tree.json 檔案路徑
TREE_JSON_PATH = os.path.join(TEMP_DIRECTORY, "tree.json")

def update_tree_with_changes(tree_data, changes_payload):
    """
    根據變更事件更新 tree.json
    """
    def add_item_to_tree(tree, path_parts, item_data):
        """遞迴添加項目到tree中"""
        if len(path_parts) == 1:
            # 到達檔案/資料夾名稱
            if item_data['type'] == 'file':
                tree[path_parts[0]] = item_data['hash']
            else:  # folder
                tree[path_parts[0]] = {}
        else:
            # 還有更深層的路徑
            current_dir = path_parts[0]
            if current_dir not in tree:
                tree[current_dir] = {}
            add_item_to_tree(tree[current_dir], path_parts[1:], item_data)
    
    def remove_item_from_tree(tree, path_parts):
        """遞迴從tree中移除項目"""
        if len(path_parts) == 1:
            # 到達檔案/資料夾名稱
            if path_parts[0] in tree:
                del tree[path_parts[0]]
        else:
            # 還有更深層的路徑
            current_dir = path_parts[0]
            if current_dir in tree and isinstance(tree[current_dir], dict):
                remove_item_from_tree(tree[current_dir], path_parts[1:])
    
    # 處理新增項目
    for item in changes_payload.get('added_items', []):
        path_parts = item['path'].split('/')
        add_item_to_tree(tree_data, path_parts, item)
    
    # 處理修改項目
    for item in changes_payload.get('modified_items', []):
        if item.get('action') == 'renamed':
            # 處理重命名
            old_path_parts = item['old_path'].split('/')
            new_path_parts = item['path'].split('/')
            
            # 先移除舊路徑
            remove_item_from_tree(tree_data, old_path_parts)
            # 再添加新路徑
            add_item_to_tree(tree_data, new_path_parts, item)
        else:
            # 處理一般修改
            path_parts = item['path'].split('/')
            if len(path_parts) == 1:
                # 根目錄檔案
                tree_data[path_parts[0]] = item['hash']
            else:
                # 子目錄檔案
                current = tree_data
                for part in path_parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[path_parts[-1]] = item['hash']
    
    # 處理刪除項目
    for item in changes_payload.get('deleted_items', []):
        path_parts = item['path'].split('/')
        remove_item_from_tree(tree_data, path_parts)
    
    return tree_data

@app.route("/")
def index():
    return "Relay Server is up and running!"

# 讀取或創建 tree.json 檔案
@app.route("/api/v1/tree", methods=["GET"])
def get_tree():
    """
    讀取 server 資料夾底下的 tree.json，如果沒有就新增一個空的
    """
    try:
        if os.path.exists(TREE_JSON_PATH):
            # 如果檔案存在，讀取內容
            with open(TREE_JSON_PATH, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
            app.logger.info(f"Read existing tree.json: {TREE_JSON_PATH}")
        else:
            # 如果檔案不存在，創建一個空的 tree.json
            tree_data = {}
            with open(TREE_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(tree_data, f, indent=2, ensure_ascii=False)
            app.logger.info(f"Created new empty tree.json: {TREE_JSON_PATH}")
        
        return jsonify({
            "status": "success",
            "tree_data": tree_data,
            "file_path": TREE_JSON_PATH
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error handling tree.json: {e}")
        return jsonify({
            "error": "Failed to read or create tree.json",
            "detail": str(e)
        }), 500

# 處理變更事件並更新 tree.json
@app.route("/api/v1/event/changes", methods=["POST"])
def handle_changes():
    """
    接收 client 送來的變更事件，更新 tree.json
    範例 payload:
    {
        "added_items": [{"type": "file", "path": "test.txt", "hash": "abc123"}],
        "modified_items": [{"type": "file", "path": "test.txt", "hash": "def456"}],
        "deleted_items": [{"type": "file", "path": "old.txt", "hash": "ghi789"}],
        "timestamp": 1751784655
    }
    """
    try:
        payload = request.get_json(force=True)
        app.logger.info(f"Received changes: {len(payload.get('added_items', []))} added, {len(payload.get('modified_items', []))} modified, {len(payload.get('deleted_items', []))} deleted")
        
        # 讀取現有的 tree.json
        if os.path.exists(TREE_JSON_PATH):
            with open(TREE_JSON_PATH, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
        else:
            tree_data = {}
        
        # 更新 tree.json
        updated_tree = update_tree_with_changes(tree_data, payload)
        
        # 儲存更新後的 tree.json
        with open(TREE_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(updated_tree, f, indent=2, ensure_ascii=False)
        
        app.logger.info(f"Updated tree.json with changes")
        
        # TODO: 未來可以在這裡添加其他處理邏輯
        # 例如：
        # - 備份檔案到 Google Drive
        # - 發送通知
        # - 記錄審計日誌
        # - 觸發其他服務
        
        return jsonify({
            "status": "success",
            "message": "Tree updated successfully",
            "changes_processed": {
                "added": len(payload.get('added_items', [])),
                "modified": len(payload.get('modified_items', [])),
                "deleted": len(payload.get('deleted_items', []))
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error handling changes: {e}")
        return jsonify({
            "error": "Failed to process changes",
            "detail": str(e)
        }), 500

# 處理新增檔案事件
@app.route("/api/v1/event/added_files", methods=["POST"])
def handle_added_files():
    """
    接收 client 送來的新增檔案事件，更新 tree.json 並儲存檔案
    """
    try:
        # 檢查請求類型
        if request.content_type and 'multipart/form-data' in request.content_type:
            # 處理檔案上傳和metadata
            uploaded_files = request.files.getlist('files')
            metadata_str = request.form.get('metadata')
            
            app.logger.info(f"Received files: {[f.filename for f in uploaded_files]}")
            app.logger.info(f"Received metadata: {metadata_str}")
            
            if metadata_str:
                try:
                    metadata = json.loads(metadata_str)
                    added_items = metadata.get('added_items', [])
                except json.JSONDecodeError as e:
                    app.logger.error(f"Failed to parse metadata JSON: {e}")
                    raise
            else:
                added_items = []
        
        # 加密上傳的檔案後上傳drive
        for file in uploaded_files:
            if file.filename:
                safe_filename = secure_filename(file.filename)
                save_path = os.path.join(TEMP_DIRECTORY, safe_filename)
                file.save(save_path)
                app.logger.info(f"Saved file: {save_path}")
        app.logger.info(f"Received added files: {len(added_items)} files")
        
        # 讀取現有的 tree.json
        if os.path.exists(TREE_JSON_PATH):
            with open(TREE_JSON_PATH, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
        else:
            tree_data = {}
        
        # 更新 tree.json - 只處理新增項目
        changes_payload = {"added_items": added_items, "modified_items": [], "deleted_items": []}
        updated_tree = update_tree_with_changes(tree_data, changes_payload)
        
        # 儲存更新後的 tree.json
        with open(TREE_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(updated_tree, f, indent=2, ensure_ascii=False)
        
        app.logger.info(f"Updated tree.json with {len(added_items)} added files")
        
        # TODO: 未來可以在這裡添加其他處理邏輯
        # 例如：
        # - 備份新增檔案到 Google Drive
        # - 掃描新增檔案是否為惡意軟體
        # - 記錄新增檔案的審計日誌
        
        return jsonify({
            "status": "success",
            "message": "Added files processed successfully",
            "files_added": len(added_items)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error handling added files: {e}")
        return jsonify({
            "error": "Failed to process added files",
            "detail": str(e)
        }), 500

# 處理修改檔案事件
@app.route("/api/v1/event/modified_files", methods=["POST"])
def handle_modified_files():
    """
    接收 client 送來的修改檔案事件，更新 tree.json
    """
    try:
        payload = request.get_json(force=True)
        modified_items = payload.get('modified_items', [])
        app.logger.info(f"Received modified files: {len(modified_items)} files")
        
        # 讀取現有的 tree.json
        if os.path.exists(TREE_JSON_PATH):
            with open(TREE_JSON_PATH, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
        else:
            tree_data = {}
        
        # 更新 tree.json - 只處理修改項目
        changes_payload = {"added_items": [], "modified_items": modified_items, "deleted_items": []}
        updated_tree = update_tree_with_changes(tree_data, changes_payload)
        
        # 儲存更新後的 tree.json
        with open(TREE_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(updated_tree, f, indent=2, ensure_ascii=False)
        
        app.logger.info(f"Updated tree.json with {len(modified_items)} modified files")
        
        # TODO: 未來可以在這裡添加其他處理邏輯
        # 例如：
        # - 備份修改前的檔案到 Google Drive
        # - 檢查修改是否為勒索軟體行為
        # - 記錄檔案修改的審計日誌
        
        return jsonify({
            "status": "success",
            "message": "Modified files processed successfully",
            "files_modified": len(modified_items)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error handling modified files: {e}")
        return jsonify({
            "error": "Failed to process modified files",
            "detail": str(e)
        }), 500

# 處理刪除檔案事件
@app.route("/api/v1/event/deleted_files", methods=["POST"])
def handle_deleted_files():
    """
    接收 client 送來的刪除檔案事件，更新 tree.json
    """
    try:
        payload = request.get_json(force=True)
        deleted_items = payload.get('deleted_items', [])
        app.logger.info(f"Received deleted files: {len(deleted_items)} files")
        
        # 讀取現有的 tree.json
        if os.path.exists(TREE_JSON_PATH):
            with open(TREE_JSON_PATH, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
        else:
            tree_data = {}
        
        # 更新 tree.json - 只處理刪除項目
        changes_payload = {"added_items": [], "modified_items": [], "deleted_items": deleted_items}
        updated_tree = update_tree_with_changes(tree_data, changes_payload)
        
        # 儲存更新後的 tree.json
        with open(TREE_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(updated_tree, f, indent=2, ensure_ascii=False)
        
        app.logger.info(f"Updated tree.json with {len(deleted_items)} deleted files")
        
        # TODO: 未來可以在這裡添加其他處理邏輯
        # 例如：
        # - 從 Google Drive 恢復被刪除的檔案
        # - 檢查是否為大量檔案刪除（勒索軟體特徵）
        # - 記錄檔案刪除的審計日誌
        
        return jsonify({
            "status": "success",
            "message": "Deleted files processed successfully",
            "files_deleted": len(deleted_items)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error handling deleted files: {e}")
        return jsonify({
            "error": "Failed to process deleted files",
            "detail": str(e)
        }), 500

if __name__ == "__main__":
    # debug=True 僅開發時使用
    app.run(host="0.0.0.0", port=8000, debug=True)
