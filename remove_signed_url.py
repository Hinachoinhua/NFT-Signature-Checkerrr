import json

def remove_url(url):
    files = [
        "signatures/hash_data.json",
        "nft_info.json",
        "alerted_hashes.json"
    ]
    for file in files:
        try:
            with open(file, "r") as f:
                data = json.load(f)
            if url in data:
                del data[url]
                with open(file, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"Đã xóa {url} khỏi {file}")
            else:
                print(f"{url} không có trong {file}")
        except Exception as e:
            print(f"Lỗi với {file}: {e}")

if __name__ == "__main__":
    url = input("Nhập URL muốn xóa: ").strip()
    remove_url(url)