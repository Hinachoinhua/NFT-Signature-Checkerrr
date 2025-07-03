import json
import os

def remove_url(url):
    files = [
        "signatures/hash_data.json",
        "nft_info.json",
        "alerted_hashes.json"
    ]
    backup_path = None
    media_path = None

    # Đọc thông tin file gốc từ nft_info.json (nếu có)
    try:
        with open("nft_info.json", "r", encoding="utf-8") as f:
            nft_data = json.load(f)
        info = nft_data.get(url)
        if isinstance(info, dict):
            backup_path = info.get("ORIGINAL_PATH")
            media_path = info.get("MEDIA_PATH")  # Nếu bạn có trường này
    except Exception as e:
        print(f"Lỗi đọc nft_info.json: {e}")

    # Xóa url khỏi các file json
    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if url in data:
                del data[url]
                with open(file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"Đã xóa {url} khỏi {file}")
            else:
                print(f"{url} không có trong {file}")
        except Exception as e:
            print(f"Lỗi với {file}: {e}")

    # Xóa file trong media_backup nếu có
    if backup_path and os.path.isfile(backup_path):
        try:
            os.remove(backup_path)
            print(f"Đã xóa file backup: {backup_path}")
        except Exception as e:
            print(f"Lỗi xóa file backup: {e}")
    else:
        print("Không tìm thấy file backup hoặc không có thông tin.")

    # Xóa file trong media nếu có (nếu bạn lưu đường dẫn)
    if media_path and os.path.isfile(media_path):
        try:
            os.remove(media_path)
            print(f"Đã xóa file media: {media_path}")
        except Exception as e:
            print(f"Lỗi xóa file media: {e}")

if __name__ == "__main__":
    url = input("Nhập URL muốn xóa: ").strip()
    remove_url(url)