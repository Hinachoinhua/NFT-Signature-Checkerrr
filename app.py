from flask import Flask, request, jsonify, send_from_directory
from utils import download_file, create_hash, save_signature, save_nft_info, verify_url
import json, os
import threading
from monitor import monitor

app = Flask(__name__)

@app.route("/sign", methods=["POST"])
def sign_url():
    url = request.json.get("url")
    file_path = download_file(url)
    hash_val = create_hash(file_path)
    save_signature(url, hash_val)
    save_nft_info(url, hash_val)
    return jsonify({"status": "signed", "hash": hash_val})

@app.route("/verify", methods=["POST"])
def verify():
    url = request.json.get("url")
    match, current, expected = verify_url(url)
    result = {
        "KIỂM TRA": match,
        "HASH HIỆN TẠI": current,
        "HASH BAN ĐẦU": expected,
        "KẾT QUẢ": "✔️ Trùng khớp nội dung đã ký." if match else "❌ Nội dung đã bị thay đổi hoặc giả mạo!"
    }
    try:
        with open("nft_info.json") as f:
            nft_data = json.load(f)
        result["nft_info"] = nft_data.get(url, {})
    except:
        result["nft_info"] = {}
    return jsonify(result)


@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("web", path)

# Phần còn lại của ứng dụng (web/server/CLI...)
print("Ứng dụng chính đang chạy. Giám sát đang hoạt động nền...")

# Giữ cho app chạy liên tục nếu cần
#while True:
 #   pass

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()
    app.run(debug=True, use_reloader=False)