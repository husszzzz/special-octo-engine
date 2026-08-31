import telebot
import os
import subprocess
import shutil
import urllib.request
import stat
import requests

# الإعدادات
BOT_TOKEN = os.getenv("BOT_TOKEN", "7709888774:AAFZHUqW4L8nysCutJ1PEQx2rIonYaEQd4s")
IPA_URL = "https://github.com/husszzzz/8ball-pool/releases/download/1.5/8.Ball.Pool_56.26.1_1787089904.ipa"
BASE_IPA = "8ball_base.ipa"

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

# تحميل الأدوات واللعبة تلقائياً
def setup_tools():
    zsign_path = "./zsign"
    if not os.path.exists(zsign_path):
        print("⏳ جاري تحميل أداة التوقيع...")
        urllib.request.urlretrieve("https://github.com/sign-z/zsign/releases/download/v1.0/zsign", zsign_path)
        os.chmod(zsign_path, os.stat(zsign_path).st_mode | stat.S_IEXEC)
    
    if not os.path.exists(BASE_IPA):
        print("⏳ جاري تحميل اللعبة من رابطك...")
        urllib.request.urlretrieve(IPA_URL, BASE_IPA)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    bot.send_message(chat_id, "أهلاً بك يا حساني 🎱\n\nأرسل ملف الشهادة بصيغة (.p12) الآن:")

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
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        user_data[chat_id]['p12'] = file_path
        bot.send_message(chat_id, "✅ تم استلام الشهادة.\n\nالآن أرسل ملف التوفير (.mobileprovision):")

    elif file_name.endswith('.mobileprovision'):
        file_path = os.path.join(user_folder, "profile.mobileprovision")
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        user_data[chat_id]['prov'] = file_path
        
        msg = bot.send_message(chat_id, "✅ ممتاز. الآن أرسل **باسوورد** الشهادة:")
        bot.register_next_step_handler(msg, process_password)

def process_password(message):
    chat_id = message.chat.id
    user_data[chat_id]['password'] = message.text
    
    bot.send_message(chat_id, "⏳ جاري توقيع اللعبة... يرجى الانتظار.")
    
    try:
        sign_app(chat_id)
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ:\n{str(e)}")
        if os.path.exists(f"temp_{chat_id}"):
            shutil.rmtree(f"temp_{chat_id}")

def sign_app(chat_id):
    data = user_data[chat_id]
    user_folder = f"temp_{chat_id}"
    output_ipa = os.path.join(user_folder, "signed_billiard.ipa")
    
    # التوقيع
    sign_cmd = ["./zsign", "-k", data['p12'], "-p", data['password'], "-m", data['prov'], "-o", output_ipa, BASE_IPA]
    result = subprocess.run(sign_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        bot.send_message(chat_id, "❌ فشل التوقيع! تأكد من الباسوورد والشهادة.")
        return

    bot.send_message(chat_id, "✅ تم التوقيع بنجاح! جاري رفع التطبيق الموقع وتجهيز الرابط (لأن حجم اللعبة يتجاوز حد التليجرام)...")

    # الرفع إلى سيرفر GoFile للحصول على رابط سريع للـ IPA
    try:
        server_res = requests.get("https://api.gofile.io/getServer").json()
        server = server_res['data']['server']
        with open(output_ipa, 'rb') as f:
            upload_res = requests.post(f"https://{server}.gofile.io/uploadFile", files={'file': f}).json()
        
        download_link = upload_res['data']['downloadPage']
        bot.send_message(chat_id, f"🎉 **تم توقيع التطبيق!**\n\nحمل اللعبة الموقعة من هذا الرابط:\n{download_link}\n\n*الآن يمكنك أخذ الملف واستخدامه مع ملف الـ plist الخاص بك.*", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء رفع الملف: {e}")

    # تنظيف الملفات المؤقتة
    shutil.rmtree(user_folder)
    user_data.pop(chat_id, None)

if __name__ == "__main__":
    setup_tools()
    print("🤖 البوت يعمل...")
    bot.polling(none_stop=True)
