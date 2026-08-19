import os
import re
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 732556792  # تم وضع الآيدي الخاص بك هنا بناءً على الصورة تلقائياً

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.first_name
    user_username = f"@{user.username}" if user.username else "ليس له معرف"
    user_id = user.id

    welcome_text = (
        f"أهلاً بك يا {user_name} 🤍 في بوت التحميل الشامل 🚀\n\n"
        "أرسل لي أي رابط فيديو (من تيك توك، بنترست، إنستغرام، وغيرها) وسأقوم بتحميله لك فوراً 🤍"
    )
    await update.message.reply_text(welcome_text)

    if ADMIN_ID:
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
    text = update.message.text
    if not text:
        return
        
    # استخراج الرابط الصحيح فقط من النص (تجنب أخطاء النصوص المصاحبة للمشاركة)
    url_match = re.search(r'https?://[^\s]+', text)
    if not url_match:
        return
        
    url = url_match.group(0)
    
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
        await update.message.reply_text("❌ عذراً، حدث خطأ أثناء التحميل. تأكد أن الرابط عام وليس خاصاً.")
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    if not TOKEN:
        print("Error: BOT_TOKEN environment variable not set.")
        exit(1)
        
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🤖 البوت يعمل الآن بكامل الميزات...")
    application.run_polling()
