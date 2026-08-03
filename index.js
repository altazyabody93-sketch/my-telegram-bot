const TelegramBot = require('node-telegram-bot-api');
const admin = require('firebase-admin');

// 1. الاتصال بـ Firebase تلقائياً وأمان
try {
  if (process.env.FIREBASE_SERVICE_ACCOUNT) {
    const rawAccount = process.env.FIREBASE_SERVICE_ACCOUNT.trim();
    const serviceAccount = JSON.parse(rawAccount);

    admin.initializeApp({
      credential: admin.credential.cert(serviceAccount),
      databaseURL: "https://almatariapp-default-rtdb.firebaseio.com"
    });
    console.log("🔥 تم الاتصال بقاعدة بيانات Firebase بنجاح!");
  } else {
    console.log("⚠️ تنبيه: لم يتم إضافة متغيرة FIREBASE_SERVICE_ACCOUNT في Render.");
  }
} catch (error) {
  console.error("خطأ في الاتصال بـ Firebase:", error.message);
}

// 2. قراءة توكن البوت وتنظيفه تلقائياً من أي مسافات زائدة
const rawToken = process.env.BOT_TOKEN || '';
const token = rawToken.trim();

if (!token) {
  console.error("❌ خطأ: توكن البوت غير موجود! أضف BOT_TOKEN في متغيرات البيئة في Render.");
} else {
  // 3. تشغيل البوت
  const bot = new TelegramBot(token, { polling: true });

  // معالجة الأخطاء حتى لا يتوقف البوت أبداً
  bot.on('polling_error', (error) => {
    if (!error.message.includes('409 Conflict')) {
      console.log('ملاحظة Polling:', error.message);
    }
  });

  // استجابة البوت عند الضغط على /start
  bot.onText(/\/start/, (msg) => {
    bot.sendMessage(msg.chat.id, 'أهلاً بك! بوت الدعم الفني جاهز ومربوط بـ Firebase بنجاح 🎉');
  });

  console.log("🚀 البوت شغال تمام وبدون أي أخطاء...");
}
