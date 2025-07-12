import os

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Google Drive 相關
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)

# Drive 憑證與授權範圍
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
# Google api .json檔案位置
SERVICE_ACCOUNT_FILE = "./google_drive_api_json/plasma-kit-465410-b6-99aebbcf18a2.json"
# 目標上傳資料夾 ID (從 Drive 網址取得)
TARGET_FOLDER_ID    = "1qkKgdAFA1oPj_Lx9k1hS4ANJph5Wakfk"

# 建立 Drive service
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=creds)

# 暫存資料夾位置
STAGING_DIR = os.getenv("STAGING_DIR", "./temp_file")
os.makedirs(STAGING_DIR, exist_ok=True)

@app.route("/")
def index():
    return "Relay Server is up and running!"

# 處理所有檔案變更事件
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
def upload_temp():
    """
    接收 client 上傳的檔案，並存到 ./temp。
    """
    if 'file' not in request.files:
        return jsonify({"error": "no file part"}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({"error": "empty filename"}), 400

    # 安全檔名並存檔
    filename = secure_filename(f.filename)
    save_path = os.path.join(STAGING_DIR, filename)
    f.save(save_path)

    # 印出serverLog訊息
    app.logger.info(f"Staged file: {save_path}")

    # 上傳到 Google Drive
    try:
        file_metadata = {
            "name": filename,
            "parents": [TARGET_FOLDER_ID]
        }
        media = MediaFileUpload(save_path, resumable=True)
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
            "status": "uploaded",
            "file_id": file_id,
            "webViewLink": web_link
        }), 200

    except Exception as e:
        app.logger.error(f"Drive upload failed: {e}")
        return jsonify({"error": "drive upload failed", "detail": str(e)}), 500

if __name__ == "__main__":
    # debug=True 僅開發時使用
    app.run(host="0.0.0.0", port=8000, debug=True)
