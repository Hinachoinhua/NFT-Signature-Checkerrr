import time
import json
import smtplib
import os
import ssl
import datetime
import urllib.parse

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from utils import verify_url

CHECK_INTERVAL = 60  # giây
SIGNATURE_FILE = "signatures/hash_data.json"
NFT_INFO_FILE = "nft_info.json"
ALERTED_HASHES_FILE = "alerted_hashes.json"

# Thông tin Gmail gửi cảnh báo
fromAddr = "haodoctor776@gmail.com"
toAddr = "haodoctor776@gmail.com"


def send_email(subject, body, toAddr):
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
                nft_data = json.load(f)
            urls = list(nft_data.keys())

            alerted_hashes = load_alerted_hashes()

            for url in urls:
                match, current_hash, expected_hash = verify_url(url)
                if expected_hash is None:
                    continue

                alerted_list = alerted_hashes.get(url, [])
                if isinstance(alerted_list, str):
                    alerted_list = [alerted_list]

                if not match:
                    if current_hash not in alerted_list:
                        subject = "🔴 CẢNH BÁO NỘI DUNG BỊ THAY ĐỔI"
                        detected_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        base_url = "http://10.18.228.237:5000"
                        url_encoded = urllib.parse.quote(url, safe='')
                        restore_link = f"{base_url}/restore?url={url_encoded}"

                        body = (
                            "Phát hiện tài sản số đã bị thay đổi!\n\n"
                            f"Tài sản: {url}\n"
                            f"Thời gian phát hiện: {detected_time}\n"
                            "Lý do: Hash không trùng khớp, nội dung đã bị thay đổi.\n\n"
                            "Bạn có thể:\n"
                            f"[Khôi phục bản gốc]: {restore_link}\n"
                            "Lưu ý: Khi tải được bản gốc, bạn vui lòng upload lên lại và gắn chữ ký trên web để tiếp tục theo dõi\n\n"
                            "Mọi thắc mắc xin vui lòng liên hệ:\n"
                            "Trung tâm CSKH 24/7: TramNKCE180138@fpt.edu.vn\n"
                            "Số điện thoại: 0765936972 (Mr. Hào)\n"
                            "Xin trân trọng cảm ơn quý khách đã tin tưởng sử dụng dịch vụ này.\n\n"
                            "DỊCH VỤ GẮN CHỮ KÝ NFT: BẢO MẬT VÌ ĐAM MÊ\n"
                            "Địa chỉ: 600 Nguyễn Văn Cừ, phường An Bình, thành phố Cần Thơ\n"
                        )
                        # Lấy email người dùng từ nft_info.json
                        user_email = nft_data[url].get("user_email")
                        if user_email:
                            send_email(subject, body, user_email)
                        else:
                            send_email(subject, body, toAddr)  # gửi về email admin nếu không có
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