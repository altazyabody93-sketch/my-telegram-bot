const TelegramBot = require('node-telegram-bot-api');
const admin = require('firebase-admin');
const express = require('express');

// 1. تشغيل سيرفر Express وهمي لمنع إغلاق Render لعدم وجود Port
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send('OTP Telegram Bot is Active and Running!');
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});

// 2. تهيئة Firebase Admin باستخدام متغيرة البيئة في Render
try {
  if (!process.env.FIREBASE_SERVICE_ACCOUNT) {
    throw new Error("لم يتم العثور على متغيرة البيئة FIREBASE_SERVICE_ACCOUNT في Render!");
  }

  const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);

  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    databaseURL: "https://almatariapp-default-rtdb.firebaseio.com" // رابط قاعدة بياناتك
  });

  console.log("تم الاتصال بـ Firebase بنجاح! 🔥");
} catch (error) {
  console.error("خطأ في تهيئة Firebase:", error.message);
}

// 3. قراءة توكن البوت (من متغيرة البيئة أو كتابته هنا مباشرة إذا لزم)
const token = process.env.BOT_TOKEN || 'ضع_توكن_البوت_هنا_إن_لم_تستخدم_متغير_بيئة';

// 4. تشغيل البوت عبر Polling
const bot = new TelegramBot(token, { polling: true });

// التعامل مع أخطاء Polling لتفادي توقف البوت
bot.on('polling_error', (error) => {
  if (error.code === 'ETELEGRAM' && error.message.includes('409 Conflict')) {
    console.log('تنبيه: هناك نسخة أخرى تشغل البوت حالياً بنفس التوكن!');
  } else {
    console.log('Polling error:', error.message);
  }
});

// أمر /start للبوت
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  bot.sendMessage(chatId, 'أهلاً بك في بوت الدعم الفني! كيف يمكنني مساعدتك اليوم؟');
});

console.log("🚀 بوت الدعم الفني جاهز ويعمل الآن...");
