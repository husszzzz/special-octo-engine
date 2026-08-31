import telebot
import os
import subprocess
import shutil
import time
import urllib.request
import stat

# ==========================================
# 1. الإعدادات والمتغيرات
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "ضع_توكن_البوت_هنا")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "ضع_توكن_جيت_هوب_هنا")
GITHUB_USERNAME = "ضع_يوزر_حسابك_في_جيت_هوب" 
PAGES_REPO = f"{GITHUB_USERNAME}/اسم_المستودع_العام_للروابط" # مثال: Hassany/Billiard-OTA
BASE_IPA = "billiard_base.ipa" # تأكد أن هذا الملف موجود في المستودع

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

# ==========================================
# 2. التجهيز التلقائي (دمج أداة zsign)
# ==========================================
def setup_tools():
    zsign_path = "./zsign"
    if not os.path.exists(zsign_path):
        print("⏳ جاري تحميل أداة zsign التلقائية...")
        try:
            # رابط مباشر لنسخة zsign مجمّعة وتعمل على لينكس (سيرفرات Railway)
            url = "https://github.com/sign-z/zsign/releases/download/v1.0/zsign"
            urllib.request.urlretrieve(url, zsign_path)
            
            # إعطاء صلاحية التشغيل للملف (chmod +x)
            st = os.stat(zsign_path)
            os.chmod(zsign_path, st.st_mode | stat.S_IEXEC)
            print("✅ تم تحميل ودمج zsign بنجاح!")
        except Exception as e:
            print(f"❌ حدث خطأ أثناء تحميل zsign: {e}")

    # تهيئة إعدادات Git لعمليات الرفع
    subprocess.run(["git", "config", "--global", "user.email", "bot@hassany.store"])
    subprocess.run(["git", "config", "--global", "user.name", "Hassany Bot"])

# ==========================================
# 3. أوامر التليجرام
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    bot.send_message(chat_id, "أهلاً بك في بوت Hassany Store لتوقيع بلياردو VIP 🎱\n\nيرجى إرسال ملف الشهادة بصيغة (.p12) الآن:")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {}

    file_name = message.document.file_name
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    user_folder = f"temp_{chat_id}"
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    if file_name.endswith('.p12'):
        file_path = os.path.join(user_folder, "cert.p12")
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        user_data[chat_id]['p12'] = file_path
        bot.send_message(chat_id, "✅ تم استلام الشهادة.\n\nالآن أرسل ملف التوفير (.mobileprovision):")

    elif file_name.endswith('.mobileprovision'):
        file_path = os.path.join(user_folder, "profile.mobileprovision")
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        user_data[chat_id]['prov'] = file_path
        
        msg = bot.send_message(chat_id, "✅ تم استلام ملف التوفير.\n\nالآن أرسل **باسوورد** الشهادة:")
        bot.register_next_step_handler(msg, process_password)

def process_password(message):
    chat_id = message.chat.id
    user_data[chat_id]['password'] = message.text
    
    bot.send_message(chat_id, "⏳ جاري توقيع اللعبة وإنشاء رابط التثبيت، يرجى الانتظار...")
    
    try:
        sign_and_upload(chat_id)
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ:\n{str(e)}")
        if os.path.exists(f"temp_{chat_id}"):
            shutil.rmtree(f"temp_{chat_id}")

# ==========================================
# 4. عملية التوقيع والرفع لـ GitHub
# ==========================================
def sign_and_upload(chat_id):
    data = user_data[chat_id]
    user_folder = f"temp_{chat_id}"
    output_ipa = os.path.join(user_folder, "signed_billiard.ipa")
    
    # 1. التوقيع بأداة zsign
    sign_cmd = [
        "./zsign", 
        "-k", data['p12'], 
        "-p", data['password'], 
        "-m", data['prov'], 
        "-o", output_ipa, 
        BASE_IPA
    ]
    
    result = subprocess.run(sign_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        bot.send_message(chat_id, "❌ فشل التوقيع! تأكد من صحة الباسوورد وملفات الشهادة.")
        return

    bot.send_message(chat_id, "✅ تم التوقيع بنجاح! جاري بناء الروابط المباشرة...")

    # 2. استنساخ المستودع العام
    unique_id = str(int(time.time()))
    repo_url = f"https://{GITHUB_TOKEN}@github.com/{PAGES_REPO}.git"
    clone_dir = f"repo_clone_{chat_id}"
    
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)
        
    subprocess.run(["git", "clone", repo_url, clone_dir])
    
    app_dir = os.path.join(clone_dir, unique_id)
    os.makedirs(app_dir)
    
    shutil.copy(output_ipa, os.path.join(app_dir, "app.ipa"))
    
    # 3. إنشاء ملفات التحميل (Plist و HTML)
    repo_name = PAGES_REPO.split('/')[1]
    ipa_url = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/{unique_id}/app.ipa"
    plist_url = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/{unique_id}/manifest.plist"
    
    # بناء الـ plist
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict><key>items</key><array><dict><key>assets</key><array><dict>
<key>kind</key><string>software-package</string><key>url</key>
<string>{ipa_url}</string></dict></array><key>metadata</key><dict>
<key>bundle-identifier</key><string>com.hassany.billiard.vip</string>
<key>bundle-version</key><string>1.0</string><key>kind</key><string>software</string>
<key>title</key><string>Billiard VIP - Hassany Store</string>
</dict></dict></array></dict></plist>"""

    with open(os.path.join(app_dir, "manifest.plist"), "w") as f:
        f.write(plist_content)

    # بناء واجهة الويب HTML
    html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hassany Store - تثبيت</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; text-align: center; padding-top: 50px; background: #1c1c1e; color: white; }}
        .install-btn {{ display: inline-block; margin-top: 20px; padding: 15px 40px; font-size: 20px; color: #fff; background: #007aff; border-radius: 12px; text-decoration: none; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Billiard VIP 🎱</h1>
    <p>تم توقيع التطبيق وجاهز للتثبيت</p>
    <a href="itms-services://?action=download-manifest&url={plist_url}" class="install-btn">تثبيت التطبيق الآن</a>
</body>
</html>"""

    with open(os.path.join(app_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    # 4. الرفع إلى GitHub
    subprocess.run(["git", "-C", clone_dir, "add", "."])
    subprocess.run(["git", "-C", clone_dir, "commit", "-m", f"Add signed app for {unique_id}"])
    subprocess.run(["git", "-C", clone_dir, "push", "origin", "main"]) # تأكد أن اسم الفرع عندك هو main

    # 5. إرسال الرابط النهائي للمستخدم
    install_link = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/{unique_id}/index.html"
    bot.send_message(chat_id, f"🎉 **عملية ناجحة يا حساني!**\n\nرابط التثبيت المباشر الخاص بك:\n{install_link}\n\n*انسخ الرابط وافتحه في سفاري لتثبيت اللعبة.*", parse_mode="Markdown")

    # تنظيف الملفات
    shutil.rmtree(user_folder)
    shutil.rmtree(clone_dir)
    user_data.pop(chat_id, None)

# تشغيل التهيئة ثم البوت
if __name__ == "__main__":
    setup_tools()
    print("🤖 البوت يعمل الآن...")
    bot.polling(none_stop=True)
