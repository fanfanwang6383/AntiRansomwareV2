import os

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

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
    app.logger.info(f"Received event: {payload}")
    # 這裡可以把 payload 存到 DB，或進一步處理
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

    app.logger.info(f"Staged file: {save_path}")
    return jsonify({
        "status": "staged",
        "filename": filename,
        "saved_to": save_path
    }), 200

if __name__ == "__main__":
    # debug=True 僅開發時使用
    app.run(host="0.0.0.0", port=8000, debug=True)
