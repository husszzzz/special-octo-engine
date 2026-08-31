# بيئة لينكس مع بايثون
FROM python:3.10-slim

# تثبيت أدوات النظام المطلوبة بالإضافة لـ cmake
RUN apt-get update && apt-get install -y git cmake g++ libssl-dev zip unzip curl

# بناء الأداة بنظام CMake (الطريقة الرسمية الجديدة)
RUN git clone https://github.com/zhlynn/zsign.git /zsign_src && \
    cd /zsign_src && \
    mkdir build && cd build && \
    cmake .. && make && \
    cp zsign /usr/local/bin/zsign && \
    chmod +x /usr/local/bin/zsign

# تجهيز ملفات البوت
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# تشغيل البوت
CMD ["python", "bot.py"]
