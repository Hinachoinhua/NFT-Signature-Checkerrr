from flask import Flask, request, jsonify, send_from_directory, send_file, session, abort
from utils import download_file, create_hash, save_signature, save_nft_info, verify_url
import json, os
import threading
from monitor import monitor
import shutil
import mimetypes
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.permanent_session_lifetime = timedelta(days=7)

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    # Chỉ tạo tài khoản admin nếu chưa có user nào
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        admin_pw = generate_password_hash("admin123")
        c.execute("INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)", 
                  ("admin", "haodoctor776@gmail.com", admin_pw, 1))
        conn.commit()
        print("Đã tạo tài khoản admin mặc định.")
    conn.close()

def get_db():
    return sqlite3.connect('users.db')

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data["username"]
    email = data["email"]
    password = generate_password_hash(data["password"])
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
        conn.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "fail", "msg": str(e)})
    finally:
        conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data["username"]
    password = data["password"]
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, password, is_admin FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    if user and check_password_hash(user[1], password):
        session.permanent = True  # <-- thêm dòng này
        session["user_id"] = user[0]
        session["username"] = username
        session["is_admin"] = bool(user[2])
        return jsonify({"status": "ok", "is_admin": bool(user[2])})
    return jsonify({"status": "fail", "msg": "Sai tài khoản hoặc mật khẩu."})

@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"status": "ok"})

@app.route("/sign", methods=["POST"])
def sign_url():
    url = request.json.get("url")
    if "user_id" not in session:
        return jsonify({"error": "Bạn cần đăng nhập để sử dụng chức năng này."}), 401
    try:
        file_path = download_file(url)
        hash_val = create_hash(file_path)
        save_signature(url, hash_val)
        save_nft_info(url, hash_val)

        # Lấy đuôi file đúng
        ext = os.path.splitext(file_path)[1]
        backup_dir = "media_backup"
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, os.path.basename(file_path))
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)

        # Lưu đường dẫn bản gốc, tên file gốc, username và email vào nft_info.json
        with open("nft_info.json", "r+", encoding="utf-8") as f:
            data = json.load(f)
            if url in data:
                data[url]["ORIGINAL_PATH"] = backup_path
                data[url]["ORIGINAL_FILENAME"] = os.path.basename(file_path)
                data[url]["username"] = session["username"]
                # Lấy email từ DB
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT email FROM users WHERE id=?", (session["user_id"],))
                row = c.fetchone()
                user_email = row[0] if row else ""
                conn.close()
                data[url]["user_email"] = user_email
                f.seek(0)
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.truncate()

        return jsonify({"status": "signed", "hash": hash_val})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

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

@app.route("/history")
def history():
    if "user_id" not in session:
        return jsonify({"urls": []}), 401
    with open("nft_info.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    if session.get("is_admin"):
        # Lấy danh sách username đã từng gắn chữ ký
        usernames = list({info.get("username") for info in data.values() if info.get("username")})
        return jsonify({"usernames": usernames})
    # User thường chỉ thấy url của mình
    username = session.get("username")
    user_urls = [url for url, info in data.items() if info.get("username") == username]
    return jsonify({"urls": user_urls})

@app.route("/restore")
def restore_asset():
    url = request.args.get("url")
    if not url:
        return "Thiếu URL", 400
    try:
        with open("nft_info.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        nft = data.get(url)
        if not nft or "ORIGINAL_PATH" not in nft:
            return "Không tìm thấy bản gốc để khôi phục", 404
        backup_path = nft["ORIGINAL_PATH"]
        filename = nft.get("ORIGINAL_FILENAME", os.path.basename(backup_path))
        if not os.path.exists(backup_path):
            return "File bản gốc không tồn tại trên server", 404
        # Xác định content-type
        mimetype, _ = mimetypes.guess_type(filename)
        # Trả về file với tên và content-type đúng
        return send_file(backup_path, as_attachment=True, download_name=filename, mimetype=mimetype)
    except Exception as e:
        return f"Lỗi: {e}", 500

@app.route("/me")
def me():
    if "user_id" not in session:
        return jsonify({"status": "fail"}), 401
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT username, email, is_admin FROM users WHERE id=?", (session["user_id"],))
    user = c.fetchone()
    conn.close()
    if user:
        return jsonify({
            "username": user[0],
            "email": user[1],
            "is_admin": bool(user[2])
        })
    return jsonify({"status": "fail"}), 401

@app.route("/admin/users")
def admin_list_users():
    if not session.get("is_admin"):
        return abort(403)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, username, email, is_admin FROM users")
    users = [
        {"id": row[0], "username": row[1], "email": row[2], "is_admin": bool(row[3])}
        for row in c.fetchall()
    ]
    conn.close()
    return jsonify(users)

@app.route("/admin/delete_user", methods=["POST"])
def admin_delete_user():
    if not session.get("is_admin"):
        return abort(403)
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"status": "fail", "msg": "Thiếu user_id"}), 400
    # Không cho phép admin tự xóa chính mình
    if user_id == session.get("user_id"):
        return jsonify({"status": "fail", "msg": "Không thể tự xóa tài khoản admin đang đăng nhập"}), 400

    # Lấy username của user cần xóa
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    username = row[0] if row else None

    # Xóa user khỏi DB
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    # Nếu có username, xóa các url đã gắn chữ ký bởi user này khỏi các file liên quan
    if username:
        files = [
            "signatures/hash_data.json",
            "nft_info.json",
            "alerted_hashes.json"
        ]
        for file in files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Xóa các url do user này gắn chữ ký
                urls_to_remove = []
                for url, info in data.items():
                    # info có thể là dict hoặc string (hash_data.json)
                    if isinstance(info, dict) and info.get("username") == username:
                        urls_to_remove.append(url)
                for url in urls_to_remove:
                    del data[url]
                with open(file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Lỗi khi xóa url khỏi {file}: {e}")

    return jsonify({"status": "ok"})

@app.route("/admin/user_history/<username>")
def admin_user_history(username):
    if not session.get("is_admin"):
        return abort(403)
    with open("nft_info.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    if username == "admin":
        # Lấy các url chưa gắn cho user nào (cũ)
        admin_urls = [url for url, info in data.items() if not info.get("username")]
        return jsonify({"urls": admin_urls})
    # Lấy url của user thường
    user_urls = [url for url, info in data.items() if info.get("username") == username]
    return jsonify({"urls": user_urls})

# Phần còn lại của ứng dụng (web/server/CLI...)
print("Ứng dụng chính đang chạy. Giám sát đang hoạt động nền...")

# Giữ cho app chạy liên tục nếu cần
#while True:
 #   pass

if __name__ == "__main__":
    init_db()
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)