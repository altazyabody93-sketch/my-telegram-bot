const TelegramBot = require('node-telegram-bot-api');
const admin = require('firebase-admin');

let db = null;

// 1. الاتصال بـ Firebase بطريقة آمنة وتتحمل أخطاء التنسيق
try {
  if (process.env.FIREBASE_SERVICE_ACCOUNT) {
    let serviceAccountStr = process.env.FIREBASE_SERVICE_ACCOUNT.trim();
    
    // إصلاح الأسطر الجديدة داخل المفتاح إن وجدت
    if (serviceAccountStr.includes('\\n')) {
      serviceAccountStr = serviceAccountStr.replace(/\\n/g, '\n');
    }

    const serviceAccount = JSON.parse(serviceAccountStr);

    admin.initializeApp({
      credential: admin.credential.cert(serviceAccount),
      databaseURL: "https://almatariapp-default-rtdb.firebaseio.com"
    });
    db = admin.database();
    console.log("🔥 تم الاتصال بقاعدة بيانات Firebase بنجاح!");
  } else {
    console.log("⚠️ تنبيه: متغيرة FIREBASE_SERVICE_ACCOUNT غير موجودة.");
  }
} catch (error) {
  console.error("خطأ في تهيئة Firebase:", error.message);
}

// 2. تشغيل البوت
const rawToken = process.env.BOT_TOKEN || '';
const token = rawToken.trim();

if (!token) {
  console.error("❌ توكن البوت غير موجود في متغيرات البيئة!");
} else {
  const bot = new TelegramBot(token, { polling: true });

  bot.on('polling_error', (error) => {
    if (!error.message.includes('409 Conflict')) {
      console.log('ملاحظة Polling:', error.message);
    }
  });

  // 3. استقبال رسائل تليجرام وحفظها في Firebase
  bot.on('message', (msg) => {
    if (msg.text && !msg.text.startsWith('/')) {
      const chatId = msg.chat.id;
      if (db) {
        db.ref(`support_chats/${chatId}/messages`).push({
          sender: 'user',
          text: msg.text,
          timestamp: Date.now()
        });
      }
    }
  });

  // 4. الرد المباشر عند تغيير البيانات في Firebase
  if (db) {
    db.ref('support_chats').on('child_changed', (snapshot) => {
      const chatId = snapshot.key;
      const data = snapshot.val();
      
      if (data && data.reply_to_send) {
        bot.sendMessage(chatId, data.reply_to_send).then(() => {
          db.ref(`support_chats/${chatId}/reply_to_send`).remove();
        }).catch(err => console.error("خطأ أثناء إرسال الرد:", err.message));
      }
    });
  }

  bot.onText(/\/start/, (msg) => {
    bot.sendMessage(msg.chat.id, 'أهلاً بك في دعم المطري! البوت يعمل الآن وجاهز للاستقبال والرد 🎉');
  });

  console.log("🚀 البوت يعمل ومستعد لنقل الرسائل والردود...");
}
