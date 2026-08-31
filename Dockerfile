FROM ubuntu:20.04

# منع الأسئلة التفاعلية أثناء تنصيب الحزم
ENV DEBIAN_FRONTEND=noninteractive

# تنصيب الحزم المطلوبة
RUN apt-get update && apt-get install -y \
    python3 python3-pip git g++ clang libssl-dev zip unzip cmake make

# تحميل الأداة والرجوع لنسخة مستقرة (سنة 2023)
RUN git clone https://github.com/zhlynn/zsign.git \
    && cd zsign \
    && git checkout $(git rev-list -n 1 --before="2023-10-01" master) \
    && cmake . \
    && make \
    && cp zsign /usr/local/bin/ \
    && chmod +x /usr/local/bin/zsign

# إعداد مجلد العمل
WORKDIR /app

# نسخ ملفات المشروع وتثبيت المكتبات
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# تشغيل البوت
CMD ["python3", "bot.py"]
