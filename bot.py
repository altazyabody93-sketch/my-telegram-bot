import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import yt_dlp

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Get the token from environment variables (Render's Environment Variable setting)
TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي رابط فيديو (تيك توك، بنترست، إلخ) وسأقوم بتحميله لك 🚀")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return
        
    await update.message.reply_text("⏳ جاري المعالجة...")
    
    file_path = "video.mp4"
    ydl_opts = {
        'outtmpl': file_path,
        'format': 'best',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        await update.message.reply_video(video=open(file_path, 'rb'), caption="✨ تم التحميل بواسطة بوت المطري 🤍")
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء التحميل.")

if __name__ == '__main__':
    if not TOKEN:
        print("Error: BOT_TOKEN environment variable not set.")
        exit(1)
        
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🤖 البوت يعمل الان على السيرفر...")
    application.run_polling()
