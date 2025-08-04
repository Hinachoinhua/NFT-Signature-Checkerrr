FROM python:3.10

WORKDIR /app

# Copy toàn bộ mã nguồn vào image
COPY . /app

# Cài đặt các thư viện cần thiết
RUN pip install --upgrade pip
RUN pip install flask werkzeug
RUN pip install requests


# Nếu bạn có requirements.txt thì dùng dòng sau thay cho pip install flask werkzeug:
# RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]