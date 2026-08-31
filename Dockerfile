# استخدام بيئة مستقرة ومتوافقة 100% مع أداة التوقيع
FROM python:3.9-buster

# تثبيت الحزم وأدوات النظام الأساسية
RUN apt-get update && apt-get install -y git g++ libssl-dev zip unzip curl make

# جلب الأداة وبنائها باستخدام أمر make الرسمي
RUN git clone https://github.com/zhlynn/zsign.git /zsign_src && \
    cd /zsign_src && \
    make && \
    cp zsign /usr/local/bin/zsign && \
    chmod +x /usr/local/bin/zsign

# إعداد بيئة عمل البوت
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# تشغيل البوت
CMD ["python", "bot.py"]
