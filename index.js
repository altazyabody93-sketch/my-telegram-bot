const TelegramBot = require('node-telegram-bot-api');
const admin = require('firebase-admin');

// تهيئة Firebase بأمان من متغيرة البيئة
try {
  if (process.env.FIREBASE_SERVICE_ACCOUNT) {
    const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
    admin.initializeApp({
      credential: admin.credential.cert(serviceAccount),
      databaseURL: "https://almatariapp-default-rtdb.firebaseio.com"
    });
    console.log("تم الاتصال بـ Firebase بنجاح! 🔥");
  } else {
    console.log("تنبيه: لم يتم العثور على متغيرة FIREBASE_SERVICE_ACCOUNT في Render");
  }
} catch (e) {
  console.error("خطأ في Firebase:", e.message);
}

// التوكن الخاص بالبوت
const token = process.env.BOT_TOKEN || 'ضع_توكن_البوت_هنا';

// تشغيل البوت
const bot = new TelegramBot(token, { polling: true });

bot.on('polling_error', (error) => {
  if (!error.message.includes('409 Conflict')) {
    console.log('Polling error:', error.message);
  }
});

bot.onText(/\/start/, (msg) => {
  bot.sendMessage(msg.chat.id, 'أهلاً بك في بوت الدعم الفني لمطري! كيف أقدر أساعدك اليوم؟');
});

console.log("🚀 البوت شغال تمام وبدون مشاكل...");
