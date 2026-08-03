const TelegramBot = require('node-telegram-bot-api');
const admin = require('firebase-admin');

let db;

// 1. الاتصال بـ Firebase
try {
  if (process.env.FIREBASE_SERVICE_ACCOUNT) {
    const rawAccount = process.env.FIREBASE_SERVICE_ACCOUNT.trim();
    const serviceAccount = JSON.parse(rawAccount);

    admin.initializeApp({
      credential: admin.credential.cert(serviceAccount),
      databaseURL: "https://almatariapp-default-rtdb.firebaseio.com"
    });
    db = admin.database();
    console.log("🔥 تم الاتصال بقاعدة بيانات Firebase بنجاح!");
  } else {
    console.log("⚠️ تنبيه: لم يتم إضافة متغيرة FIREBASE_SERVICE_ACCOUNT.");
  }
} catch (error) {
  console.error("خطأ في Firebase:", error.message);
}

// 2. تشغيل البوت
const rawToken = process.env.BOT_TOKEN || '';
const token = rawToken.trim();

if (!token) {
  console.error("❌ توكن البوت غير موجود!");
} else {
  const bot = new TelegramBot(token, { polling: true });

  bot.on('polling_error', (error) => {
    if (!error.message.includes('409 Conflict')) {
      console.log('Polling notice:', error.message);
    }
  });

  // 3. استقبال رسائل المستخدم وإرسالها إلى Firebase
  bot.on('message', (msg) => {
    if (msg.text && !msg.text.startsWith('/')) {
      const chatId = msg.chat.id;
      const userMessage = msg.text;

      if (db) {
        // حفظ الرسالة في Firebase تحت مسار دعم المستخدم
        db.ref(`support_chats/${chatId}/messages`).push({
          sender: 'user',
          text: userMessage,
          timestamp: Date.now()
        });
      }
    }
  });

  // 4. الاستماع للردود المكتوبة في Firebase وإرسالها للمستخدم في تليجرام
  if (db) {
    db.ref('support_chats').on('child_changed', (snapshot) => {
      const chatId = snapshot.key;
      const data = snapshot.val();
      
      // إذا تم إضافة رد من المشرف/Firebase
      if (data && data.reply_to_send) {
        bot.sendMessage(chatId, data.reply_to_send).then(() => {
          // مسح الرد بعد إرساله حتى لا يتكرر
          db.ref(`support_chats/${chatId}/reply_to_send`).remove();
        }).catch(err => console.error("خطأ في إرسال الرد:", err.message));
      }
    });
  }

  bot.onText(/\/start/, (msg) => {
    bot.sendMessage(msg.chat.id, 'أهلاً بك في دعم المطري! اكتب استفسارك وسنرد عليك فوراً.');
  });

  console.log("🚀 البوت شغال ومتصل بالردود المباشرة...");
}
  });

  // استجابة البوت عند الضغط على /start
  bot.onText(/\/start/, (msg) => {
    bot.sendMessage(msg.chat.id, 'أهلاً بك! بوت الدعم الفني جاهز ومربوط بـ Firebase بنجاح 🎉');
  });

  console.log("🚀 البوت شغال تمام وبدون أي أخطاء...");
}
