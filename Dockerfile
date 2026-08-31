# بيئة لينكس مع بايثون
FROM python:3.9-slim

# تثبيت المكاتب وأدوات البرمجة الضرورية
RUN apt-get update && apt-get install -y git g++ libssl-dev zip unzip wget curl

# استنساخ وتجميع أداة zsign من مصدرها الأصلي وتثبيتها في النظام
RUN git clone https://github.com/zhlynn/zsign.git /zsign_src && \
    cd /zsign_src && \
    g++ *.cpp common/*.cpp -lcrypto -O3 -o /usr/local/bin/zsign && \
    chmod +x /usr/local/bin/zsign

# تجهيز ملفات البوت
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# تشغيل البوت
CMD ["python", "bot.py"]
