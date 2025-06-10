import time
import json
import smtplib
import os
import ssl

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from utils import verify_url

CHECK_INTERVAL = 60  # giây
SIGNATURE_FILE = "signatures/hash_data.json"
NFT_INFO_FILE = "nft_info.json"
ALERTED_HASHES_FILE = "alerted_hashes.json"

# Thông tin Gmail gửi cảnh báo
fromAddr = "haodoctor776@gmail.com"
toAddr = "HaoDSCE180062@fpt.edu.vn"


def send_email(subject, body):
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = fromAddr
    msg["To"] = toAddr

    # Thêm phần nội dung vào email
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(fromAddr, "cvwi boel kwpo hpif")  # App password
        server.sendmail(fromAddr, toAddr, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Lỗi gửi email: {e}")


def load_alerted_hashes():
    if os.path.exists(ALERTED_HASHES_FILE):
        with open(ALERTED_HASHES_FILE, "r") as f:
            return json.load(f)
    return {}


def save_alerted_hashes(data):
    with open(ALERTED_HASHES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def monitor():
    while True:
        try:
            with open(NFT_INFO_FILE, "r") as f:
                urls = list(json.load(f).keys())

            alerted_hashes = load_alerted_hashes()

            for url in urls:
                match, current_hash, expected_hash = verify_url(url)
                if expected_hash is None:
                   # print(f"Bỏ qua URL chưa có hash: {url}")
                    continue

                alerted_list = alerted_hashes.get(url, [])
                if isinstance(alerted_list, str):
                    alerted_list = [alerted_list]

                if not match:
                    if current_hash not in alerted_list:
                        subject = "🔴 CẢNH BÁO NỘI DUNG BỊ THAY ĐỔI"
                        body = f"URL: {url}\nHASH HIỆN TẠI: {current_hash}\nHASH BAN ĐẦU: {expected_hash}"
                        send_email(subject, body)
                        print(body)
                        alerted_list.append(current_hash)
                        alerted_hashes[url] = alerted_list
                        save_alerted_hashes(alerted_hashes)
                    else:
                        print(f"Đã cảnh báo: {url}")
                else:
                    print(f"OK: {url}")
        except Exception as e:
            print(f"Lỗi khi giám sát: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor()