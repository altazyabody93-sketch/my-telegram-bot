const TelegramBot = require('node-telegram-bot-api');
const admin = require('firebase-admin');

// 1. تهيئة مفتاح Firebase Admin SDK
const serviceAccount = require('./serviceAccountKey.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://almatariapp-default-rtdb.firebaseio.com"
});

const db = admin.database();

// 2. بيانات بوت التليجرام الخاص بك
const token = '8293095450:AAFM_dU1yMkijpE1Tf9qoH19jzNOsXd46Ug';
const bot = new TelegramBot(token, { polling: true });

console.log("🚀 بوت الدعم الفني يعقوب يعمل الآن وجاهز لمراقبة الرسائل...");

// 3. مراقبة الردود في قناة/جروب التليجرام
bot.on('message', async (msg) => {
  try {
    // التحقق من أن الرسالة عبارة عن رد (Reply) على منشور سابق
    if (msg.reply_to_message) {
      const replyCaption = msg.reply_to_message.caption || msg.reply_to_message.text || "";
      
      // البحث عن ID المستخدم (مثال: user_a1b2c3d4) داخل المنشور الأصلي
      const match = replyCaption.match(/user_[a-zA-Z0-9-]+/);
      if (!match) {
        console.log("⚠️ لم يتم العثور على معرّف المستخدم (userToken) في الرسالة الأصلية.");
        return;
      }
      
      const userToken = match[0];
      const userRef = db.ref(`${userToken}/messages`);

      // 🎥 حالة 1: إذا أرسلت أنت فيديو رداً على المستخدم
      if (msg.video) {
        const fileId = msg.video.file_id;
        const fileUrl = await bot.getFileLink(fileId);
        
        await userRef.push({
          text: fileUrl,
          type: 'video',
          isUser: false,
          timestamp: Date.now()
        });
        console.log(`✅ تم سحب الفيديو وإرساله للمستخدم: ${userToken}`);
      } 
      // 🖼️ حالة 2: إذا أرسلت صورة
      else if (msg.photo) {
        const fileId = msg.photo[msg.photo.length - 1].file_id;
        const fileUrl = await bot.getFileLink(fileId);

        await userRef.push({
          text: fileUrl,
          type: 'image',
          isUser: false,
          timestamp: Date.now()
        });
        console.log(`✅ تم سحب الصورة وإرسالها للمستخدم: ${userToken}`);
      } 
      // 📝 حالة 3: إذا أرسلت نصاً عادياً
      else if (msg.text) {
        await userRef.push({
          text: msg.text,
          type: 'text',
          isUser: false,
          timestamp: Date.now()
        });
        console.log(`✅ تم إرسال النص للمستخدم: ${userToken}`);
      }
    }
  } catch (error) {
    console.error("❌ حدث خطأ أثناء معالجة الرسالة:", error);
  }
});
