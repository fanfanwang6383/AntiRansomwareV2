from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Relay Server is up and running!"

if __name__ == "__main__":
    # debug=True 僅開發時使用
    app.run(host="0.0.0.0", port=8000, debug=True)
