import os
import io

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
creds = get_user_credentials()
# 串連服務
drive_service = build("drive", "v3", credentials=creds)

# 暫存資料夾位置
TEMP_DIRECTORY = os.getenv("STAGING_DIR", "./backup")
os.makedirs(TEMP_DIRECTORY, exist_ok=True)

# 從drive下載回server的暫存資料夾
RECOVER_DIRECTORY = os.getenv("STAGING_DIR", "./recover")
os.makedirs(RECOVER_DIRECTORY, exist_ok=True)

# 目標 Google Drive 子資料夾 ID
UPLOAD_FOLDER = '1qkKgdAFA1oPj_Lx9k1hS4ANJph5Wakfk'

@app.route("/")
def index():
    return "Relay Server is up and running!"

# 處理所有檔案變更事件(目前無用)
@app.route("/api/v1/event/receive", methods=["POST"])
def receive_event():
    """
    接收 client 送來的檔案事件，修改檔案名稱也會
    範例 payload:
    {
        "event_type": 'move_file',
        "src_path": 'monitor\\001\\test.txt',
        "dest_path": 'monitor\\001\\test01.txt',
        "timestamp": 1751784655)
    }
    """
    payload = request.get_json(force=True)
    # 印出serverLog訊息
    app.logger.info(f"Received event: {payload}")
    # # 傳回client端的json檔
    return jsonify({"status": "ok"}), 200

# 處理需上傳檔案事件
@app.route("/api/v1/event/upload_file", methods=["POST"])
def upload_file_to_temp():
    """
    接收 client 上傳的檔案，並存到 ./temp。
    """
    if 'file' not in request.files:
        return jsonify({"error": "no file part"}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({"error": "empty filename"}), 400

    file_path = request.form.get('file_path', '')
    
    # 安全檔名並存檔
    filename = secure_filename(f.filename)
    save_dir = os.path.join(TEMP_DIRECTORY, file_path)
    # 卻保有此資料夾路徑
    os.makedirs(save_dir, exist_ok=True)
    # 結合成儲存在server上的真正路徑
    save_path = os.path.join(save_dir, filename)
    f.save(save_path)

    # 印出serverLog訊息
    app.logger.info(f"Staged file: {save_path}")

    upload_file_to_drive(filename, save_path)

    return jsonify({
            "status": "server_file_uploaded",
            "file_name": filename,
            "server_path": save_path
        }), 200

# 處理將drive上檔案恢復事件
@app.route("/api/v1/event/delete_file", methods=["POST"])
def recover_file_to_temp():
    """
    接收 client 刪除檔案事件，並從drive回復該檔案。
    """
    data = request.get_json(force=True)
    name = data.get('file_name')
    if not name:
        return jsonify({'error': 'file_name is required'}), 400

    # 1) 在 Drive 上搜索與名稱匹配且未被删除的文件
    escaped_name = name.replace("'", "\\'")
    results = drive_service.files().list(
        q=f"name = '{escaped_name}' and trashed = false",
        spaces='drive',
        fields='files(id, name)',
        pageSize=1
    ).execute()
    items = results.get('files', [])
    if not items:
        return jsonify({'error': f"no file named '{name}' found"}), 404

    file_id = items[0]['id']
    download_name = data.get('dest_name', items[0]['name'])
    download_name = secure_filename(download_name)
    dest_path = os.path.join(RECOVER_DIRECTORY, download_name)

    # 2) 發送下載請求
    request_drive = drive_service.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request_drive)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.close()
    app.logger.info(f"Restored file '{name}' as '{dest_path}'")

    return jsonify({
        'status': 'restored',
        'file_id': file_id,
        'local_path': dest_path
    }), 200

# 處理需上傳資料夾事件
@app.route("/api/v1/event/upload_folder", methods=["POST"])
def upload_folder_to_temp():
    """
    接收 client 上傳的資料夾，並存到 ./temp。
    """
    data = request.get_json(force=True)
    folder_name = data.get("folder_name")

    if not folder_name:
        return jsonify({"error": "folder_name is required"}), 400

    # server端創建資料夾
    server_folder_name = os.path.join(TEMP_DIRECTORY, folder_name)
    os.makedirs(server_folder_name, exist_ok=True)

    # 印出serverLog訊息
    app.logger.info(f"Created local folder: {server_folder_name}")

    upload_folder_to_drive(folder_name, UPLOAD_FOLDER)

    return jsonify({
            "status": "server_folder_uploaded",
            "file_name": folder_name,
            "server_path": server_folder_name
        }), 200

def upload_file_to_drive(file_name, file_path):
    # 上傳到 Google Drive
    try:
        file_metadata = {
            "name": file_name,
            "parents": [UPLOAD_FOLDER]
        }
        media = MediaFileUpload(file_path, resumable=True)
        uploaded = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink"
        ).execute()
        file_id = uploaded.get("id")
        web_link = uploaded.get("webViewLink", "")
        # 印出serverLog訊息
        app.logger.info(f"Uploaded to Drive: id={file_id}")

        # 傳回client端的json檔
        return jsonify({
            "status": "drive_uploaded",
            "file_id": file_id,
            "webViewLink": web_link
        }), 200

    except Exception as e:
        app.logger.error(f"Drive upload failed: {e}")
        return jsonify({"error": "drive upload failed", "detail": str(e)}), 500

# folder_name = 上傳資料夾名稱； UPLOAD_FOLDER = 上傳drive資料夾位置
def upload_folder_to_drive(folder_name, UPLOAD_FOLDER):
    try:
        folder_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [UPLOAD_FOLDER]
        }
        folder = drive_service.files().create(
            body=folder_metadata,
            fields="id",
            supportsAllDrives=True
        ).execute()
        # folder.get("id")為該新創建資料夾的資料夾ID
        app.logger.info(f"Created Drive folder: id={folder.get('id')}")
        return jsonify({
            "status": "folder_created",
            "local_path": folder_name,
            "drive_folder_id": folder.get("id")
        }), 200
    except Exception as e:
        app.logger.error(f"Drive folder creation failed: {e}")
        return jsonify({"error": "drive folder creation failed", "detail": str(e)}), 500

if __name__ == "__main__":
    # debug=True 僅開發時使用
    app.run(host="0.0.0.0", port=8000, debug=True)
