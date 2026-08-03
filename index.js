const TelegramBot = require('node-telegram-bot-api');
const admin = require('firebase-admin');

// استدعاء ملف مفتاح الفايربيس
const serviceAccount = require('./serviceAccountKey.json');

// تهيئة تطبيق Firebase Admin
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://almatariapp-default-rtdb.firebaseio.com"
});

const db = admin.database();

// التوكين الجديد وآيدي الجروب الخاص بك
const token = '8645315475:AAHvn0mU_IAqa3ItSiBamh-rZ6Ap9kX4RuE';
const GROUP_CHAT_ID = '-1004470276950';

const bot = new TelegramBot(token, { polling: true });

console.log("🚀 بوت الدعم الفني للمطري يعمل الآن وجاهز للمحادثات...");

// 1. استماع الرسائل القادمة من الفايربيس وتوجيهها للجروب (Firebase -> Telegram)
db.ref().on('child_added', (snapshot) => {
  const userToken = snapshot.key;
  
  // الاستماع للرسائل الجديدة داخل كل مستخدم
  db.ref(`${userToken}/messages`).limitToLast(1).on('child_added', async (msgSnap) => {
    const msg = msgSnap.val();

    // نتحقق أن الرسالة مرسلة من التطبيق (isUser == true)
    if (msg && msg.isUser) {
      const captionText = `💬 **رسالة جديدة من التطبيق**\n👤 **المستخدم ID:** \`${userToken}\`\n\nالرسالة:\n${msg.text || ''}`;

      try {
        if (msg.type === 'image' && msg.text) {
          await bot.sendPhoto(GROUP_CHAT_ID, msg.text, { caption: captionText, parse_mode: 'Markdown' });
        } else if (msg.type === 'video' && msg.text) {
          await bot.sendVideo(GROUP_CHAT_ID, msg.text, { caption: captionText, parse_mode: 'Markdown' });
        } else {
          await bot.sendMessage(GROUP_CHAT_ID, captionText, { parse_mode: 'Markdown' });
        }
        console.log(`✅ تم تحويل رسالة من ${userToken} إلى الجروب`);
      } catch (err) {
        console.error("❌ خطأ أثناء الإرسال للجروب:", err.message);
      }
    }
  });
});

// 2. استماع الردود من التليجرام وتحويلها للتطبيق (Telegram -> Firebase)
bot.on('message', async (msg) => {
  try {
    // التأكد من أن الرسالة عبارة عن رد (Reply)
    if (msg.reply_to_message) {
      const originalText = msg.reply_to_message.caption || msg.reply_to_message.text || "";
      
      // استخراج الـ ID الخاص بالمستخدم من النص الأصلي للرسالة
      const match = originalText.match(/user_[a-zA-Z0-9-]+/);
      if (!match) {
        console.log("⚠️ لم يتم العثور على معرّف userToken في الرسالة المردود عليها!");
        return;
      }

      const userToken = match[0];
      const userRef = db.ref(`${userToken}/messages`);

      // إذا كان الرد فيديو
      if (msg.video) {
        const fileId = msg.video.file_id;
        const fileUrl = await bot.getFileLink(fileId);
        await userRef.push({
          text: fileUrl,
          type: 'video',
          isUser: false,
          timestamp: Date.now()
        });
        console.log(`🎥 تم إرسال فيديو إلى ${userToken}`);
      } 
      // إذا كان الرد صورة
      else if (msg.photo) {
        const fileId = msg.photo[msg.photo.length - 1].file_id;
        const fileUrl = await bot.getFileLink(fileId);
        await userRef.push({
          text: fileUrl,
          type: 'image',
          isUser: false,
          timestamp: Date.now()
        });
        console.log(`📸 تم إرسال صورة إلى ${userToken}`);
      } 
      // إذا كان الرد نص عادي
      else if (msg.text) {
        await userRef.push({
          text: msg.text,
          type: 'text',
          isUser: false,
          timestamp: Date.now()
        });
        console.log(`✉️ تم إرسال نص إلى ${userToken}`);
      }
    }
  } catch (error) {
    console.error("❌ حدث خطأ في معالجة الرد:", error);
  }
});
