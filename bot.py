import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# قراءة التوكن من متغيرات البيئة في Render
TOKEN = os.getenv("BOT_TOKEN")

# ضع الآيدي (ID) الخاص بك هنا لكي يرسل لك إشعاراً عندما يدخل شخص جديد للبوت
# يمكنك معرفة الآيدي الخاص بك عبر بوت @userinfobot في تيليجرام
ADMIN_ID = 7325566792  # <--- استبدل هذا الرقم برقم الآيدي الحقيقي الخاص بك

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.first_name
    user_username = f"@{user.username}" if user.username "ليس له معرف"
    user_id = user.id

    # رسالة الترحيب للمستخدم
    welcome_text = (
        f"أهلاً بك يا {user_name} في بوت التحميل الشامل 🚀\n\n"
        "أرسل لي أي رابط فيديو (من تيك توك، بنترست، إنستغرام، وغيرها) وسأقوم بتحميله لك فوراً 🤍"
    )
    await update.message.reply_text(welcome_text)

    # إرسال إشعار لك أنت كمطور أن شخصاً جديداً دخل للبوت (إذا وضعت آيديك الصحيح)
    if ADMIN_ID and ADMIN_ID != 123456789:
        try:
            notification = (
                "🚨 **تم استخدام البوت بواسطة شخص جديد!**\n\n"
                f"👤 الاسم: {user_name}\n"
                f"🔗 المعرف: {user_username}\n"
                f"🆔 الآيدي: `{user_id}`"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=notification, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Failed to send admin notification: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    if not url or not url.startswith("http"):
        return
        
    await update.message.reply_text("⏳ ابشر يا مطري، جاري تحميل الفيديو من الرابط...")
    
    file_path = "video.mp4"
    ydl_opts = {
        'outtmpl': file_path,
        'format': 'best[ext=mp4]/best',
        'noplaylist': True,
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(file_path):
            await update.message.reply_video(
                video=open(file_path, 'rb'), 
                caption="🚀✨ تم التحميل بنجاح بواسطة بوت المطري"
            )
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ لم يتم العثور على ملف الفيديو، تأكد من صحة الرابط.")
            
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ عذراً، حدث خطأ أثناء التحميل. قد يكون الرابط محمي أو غير مدعوم.")
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    if not TOKEN:
        print("Error: BOT_TOKEN environment variable not set.")
        exit(1)
        
    application = ApplicationBuilder().token(TOKEN).build()
    
    # إضافة معالج لأمر start
    application.add_handler(CommandHandler("start", start))
    # إضافة معالج للرسائل والروابط
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🤖 البوت يعمل الآن بكامل الميزات...")
    application.run_polling()
