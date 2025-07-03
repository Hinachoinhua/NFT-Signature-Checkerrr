import os
import json
import requests
import hashlib
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from flask import send_file

def get_filename_from_url(url, response=None):
    # Ưu tiên lấy tên file từ header nếu có
    if response:
        cd = response.headers.get("Content-Disposition")
        if cd:
            fname = re.findall('filename="(.+)"', cd)
            if fname:
                return fname[0]
    # Nếu không có, lấy từ URL
    basename = os.path.basename(url.split("?")[0])
    if "." in basename:
        return basename
    # Nếu vẫn không có đuôi, đặt tên mặc định
    return "downloaded_file"

def download_file(url, save_dir="media"):
    os.makedirs(save_dir, exist_ok=True)
    if "drive.google.com" in url:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        file_id = query_params.get("id", [None])[0]
        if not file_id and "/file/d/" in url:
            file_id = url.split("/file/d/")[1].split("/")[0]
        if not file_id:
            raise Exception("Không tìm thấy file_id trong URL Google Drive")
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    else:
        download_url = url

    response = requests.get(download_url)
    filename = get_filename_from_url(download_url, response)
    save_path = os.path.join(save_dir, filename)

    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type:
        raise Exception("ĐÂY KHÔNG PHẢI URL ẢNH, VUI LÒNG CHỌN URL HỢP LỆ")

    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        return save_path
    else:
        raise Exception(f"Tải thất bại: {url}")

def create_hash(file_path):
    with open(file_path, "rb") as f:
        content = f.read()
        return hashlib.sha256(content).hexdigest()

def save_signature(url, hash_value, file="signatures/hash_data.json"):
    os.makedirs(os.path.dirname(file), exist_ok=True)
    if os.path.exists(file):
        with open(file, "r") as f:
            data = json.load(f)
    else:
        data = {}
    data[url] = hash_value
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def save_nft_info(url, hash_value, file="nft_info.json"):
    if os.path.exists(file):
        with open(file, "r") as f:
            data = json.load(f)
    else:
        data = {}
    data[url] = {
        "HASH": hash_value,
        "OWNER": "GROUP 1 CUSC - OJT SU25 - IA1802 - FPTUCT",
        "URL ID": f"NFT{str(len(data)+1).zfill(4)}",
        "DATE": datetime.now().strftime("%Y-%m-%d")
    }
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def verify_url(url):
    with open("signatures/hash_data.json", "r") as f:
        hash_data = json.load(f)
    expected_hash = hash_data.get(url)
    if not expected_hash:
        return False, None, None
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        current_hash = hashlib.sha256(resp.content).hexdigest()
        return current_hash == expected_hash, current_hash, expected_hash
    except Exception as e:
        print(f"Lỗi tải file: {e}")
        return False, None, expected_hash

def download_nft_file(nft, backup_path):
    mimetype = "image/jpeg"  # Giả sử đây là loại MIME của tệp tin hình ảnh
    filename = nft.get("ORIGINAL_FILENAME", os.path.basename(backup_path))
    return send_file(backup_path, as_attachment=True, download_name=filename, mimetype=mimetype)