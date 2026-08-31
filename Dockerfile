# بيئة لينكس مع بايثون
FROM python:3.10-slim

# تثبيت أدوات النظام المطلوبة
RUN apt-get update && apt-get install -y git g++ libssl-dev zip unzip bash curl

# استنساخ وتجميع أداة zsign بطريقة آمنة باستخدام bash
RUN git clone https://github.com/zhlynn/zsign.git /zsign_src && \
    cd /zsign_src && \
    /bin/bash -c "g++ *.cpp common/*.cpp -lcrypto -O3 -o /usr/local/bin/zsign" && \
    chmod +x /usr/local/bin/zsign

# تجهيز ملفات البوت
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# تشغيل البوت
CMD ["python", "bot.py"]
