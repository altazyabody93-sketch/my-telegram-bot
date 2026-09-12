# =========================================================
# all_in_one.py
# بوت Telegram + موقع Flask + قاعدة بيانات SQLite
# ملف واحد — يشغل كل شيء
# =========================================================

import os
import sys
import json
import time
import hmac
import sqlite3
import hashlib
import logging
import threading
import traceback
import requests
import telebot
from telebot import types
from telebot.types import BotCommand, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from functools import wraps
from flask import (
    Flask, request, redirect, url_for, session, flash,
    jsonify, abort, get_flashed_messages
)

# =========================================================
# ========== الإعدادات ====================================
# =========================================================
BOT_TOKEN = os.environ.get("8971686005:AAEsGXoj4ky9FfOp3YPjNFMrDeC3wSfhhUk")
if not BOT_TOKEN:
    print("❌ خطأ: BOT_TOKEN غير موجود في Environment Variables!")
    sys.exit(1)

ADMIN_IDS = ["7325566792", "7602226699"]
DEVELOPER_USERNAME = "MO_5_H"
DB_PATH = os.environ.get("DB_PATH", "store.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-now")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "http://localhost:5000")
PORT = int(os.environ.get("PORT", 5000))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== كائنات رئيسية =====
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

# ===== متغيرات عامة =====
user_data = {}
bot_status = {
    'running': False,
    'started_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'last_activity': None
}


# =========================================================
# ========== قاعدة البيانات ================================
# =========================================================
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """إنشاء كل الجداول + الإعدادات الافتراضية"""
    with db() as conn:
        # المنتجات
        conn.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, description TEXT,
            price_usd REAL, price_stars INTEGER,
            category TEXT, stock INTEGER DEFAULT 1,
            code TEXT, status TEXT DEFAULT 'available',
            sale_type TEXT DEFAULT 'auto',
            created_at TEXT, sold_at TEXT, buyer_id TEXT, file_id TEXT
        )''')
        # المستخدمين
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE, username TEXT, first_name TEXT,
            balance_usd REAL DEFAULT 0, balance_stars INTEGER DEFAULT 0,
            total_spent REAL DEFAULT 0, orders_count INTEGER DEFAULT 0,
            created_at TEXT, last_active TEXT
        )''')
        # المبيعات
        conn.execute('''CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER, buyer_id TEXT,
            amount_usd REAL, amount_stars INTEGER,
            payment_method TEXT, status TEXT DEFAULT 'pending',
            sold_at TEXT
        )''')
        # الإعدادات
        conn.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT
        )''')
        # الأدمن
        conn.execute('''CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE, added_at TEXT
        )''')
        # الأزرار
        conn.execute('''CREATE TABLE IF NOT EXISTS buttons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            button_key TEXT UNIQUE, label TEXT,
            style TEXT DEFAULT 'default', row INTEGER DEFAULT 1,
            col INTEGER DEFAULT 1, is_active INTEGER DEFAULT 1
        )''')
        # أسعار الشحن
        conn.execute('''CREATE TABLE IF NOT EXISTS charge_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount_usd REAL, amount_stars INTEGER,
            is_active INTEGER DEFAULT 1, created_at TEXT
        )''')
        # القنوات
        conn.execute('''CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT, channel_name TEXT,
            is_activation INTEGER DEFAULT 1, created_at TEXT
        )''')
        # إحصائيات النجوم
        conn.execute('''CREATE TABLE IF NOT EXISTS star_charges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, username TEXT,
            amount_usd REAL, amount_stars INTEGER, charged_at TEXT
        )''')
        # الإحالات
        conn.execute('''CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id TEXT, referred_id TEXT UNIQUE,
            amount REAL, created_at TEXT
        )''')

        # ===== الإعدادات الافتراضية =====
        defaults = [
            ('exchange_rate', '50'),
            ('store_name', '🛍️ متجر الأرقام'),
            ('store_status', 'open'),
            ('channel_id', ''),
            ('referral_reward', '0.05'),
            ('referral_enabled', '1'),
            ('referral_daily_limit', '10'),
            ('bot_username', 'sd_5g_bot'),
        ]
        for k, v in defaults:
            conn.execute("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", (k, v))

        # ===== الأزرار الافتراضية =====
        default_buttons = [
            ("show_products", "🛍️ المنتجات", "primary", 1, 1),
            ("my_balance", "💰 رصيدي", "success", 1, 2),
            ("charge_balance", "💳 شحن الرصيد", "danger", 2, 1),
            ("my_orders", "📋 طلباتي", "primary", 2, 2),
            ("support", "📞 تواصل مع الدعم", "danger", 3, 1),
        ]
        for key, label, style, row, col in default_buttons:
            conn.execute(
                "INSERT OR IGNORE INTO buttons (button_key,label,style,row,col) VALUES (?,?,?,?,?)",
                (key, label, style, row, col)
            )

        # ===== أسعار الشحن الافتراضية =====
        default_prices = [(1, 50), (2, 100), (5, 250), (10, 500), (20, 1000), (50, 2500)]
        for usd, stars in default_prices:
            conn.execute(
                "INSERT OR IGNORE INTO charge_prices (amount_usd,amount_stars,created_at) VALUES (?,?,?)",
                (usd, stars, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )

        # ===== الأدمن =====
        for admin_id in ADMIN_IDS:
            conn.execute(
                "INSERT OR IGNORE INTO admins (user_id,added_at) VALUES (?,?)",
                (admin_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )

        conn.commit()


# =========================================================
# ========== دوال الإعدادات ===============================
# =========================================================
def get_setting(key, default=""):
    with db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


def set_setting(key, value):
    with db() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, str(value)))
        conn.commit()


def get_exchange_rate():
    return int(get_setting('exchange_rate', '50'))


def set_exchange_rate(rate):
    set_setting('exchange_rate', rate)


def get_channel_id():
    return get_setting('channel_id', '')


# =========================================================
# ========== دوال المستخدمين ==============================
# =========================================================
def get_user(user_id):
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (str(user_id),)).fetchone()
        return dict(row) if row else None


def create_user(user_id, username="", first_name=""):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db() as conn:
        try:
            conn.execute(
                "INSERT INTO users (user_id,username,first_name,created_at,last_active) VALUES (?,?,?,?,?)",
                (str(user_id), username, first_name, now, now)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def add_balance_usd(user_id, amount):
    with db() as conn:
        conn.execute("UPDATE users SET balance_usd = balance_usd + ? WHERE user_id=?",
                     (amount, str(user_id)))
        conn.commit()


def add_balance_stars(user_id, amount):
    with db() as conn:
        conn.execute("UPDATE users SET balance_stars = balance_stars + ? WHERE user_id=?",
                     (amount, str(user_id)))
        conn.commit()


def deduct_balance_usd(user_id, amount):
    with db() as conn:
        cur = conn.execute(
            "UPDATE users SET balance_usd = balance_usd - ? WHERE user_id=? AND balance_usd >= ?",
            (amount, str(user_id), amount)
        )
        conn.commit()
        return cur.rowcount > 0


def get_all_users():
    with db() as conn:
        total = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        rows = conn.execute(
            "SELECT * FROM users ORDER BY id DESC LIMIT 20"
        ).fetchall()
        return {"total": total, "users": [dict(r) for r in rows]}


def count_users():
    with db() as conn:
        return conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]


# =========================================================
# ========== دوال الأدمن ==================================
# =========================================================
def add_admin(user_id):
    with db() as conn:
        try:
            conn.execute("INSERT INTO admins (user_id,added_at) VALUES (?,?)",
                         (str(user_id), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def get_all_admins():
    with db() as conn:
        rows = conn.execute("SELECT user_id FROM admins").fetchall()
        return [r["user_id"] for r in rows]


def is_admin(user_id):
    return str(user_id) in ADMIN_IDS or str(user_id) in get_all_admins()


# =========================================================
# ========== دوال المنتجات ================================
# =========================================================
def add_product(name="", description="", price_usd=0, price_stars=0,
                category="", code="", stock=1, sale_type="auto", file_id=None):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db() as conn:
        conn.execute(
            """INSERT INTO products
            (name,description,price_usd,price_stars,category,stock,code,sale_type,file_id,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (name, description, price_usd, price_stars, category,
             stock, code, sale_type, file_id, now)
        )
        conn.commit()


def get_available_products():
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM products WHERE status='available' AND stock>0 ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_products():
    with db() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def get_product(pid):
    with db() as conn:
        row = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        return dict(row) if row else None


def get_product_count():
    with db() as conn:
        avail = conn.execute(
            "SELECT COUNT(*) c FROM products WHERE status='available' AND stock>0"
        ).fetchone()["c"]
        total = conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
        return {"available": avail, "total": total}


def mark_sold(pid, buyer_id):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db() as conn:
        conn.execute(
            "UPDATE products SET status='sold', stock=0, sold_at=?, buyer_id=? WHERE id=?",
            (now, str(buyer_id), pid)
        )
        conn.commit()


def update_stock(pid, stock):
    with db() as conn:
        conn.execute("UPDATE products SET stock=? WHERE id=?", (stock, pid))
        conn.commit()


def delete_product(pid):
    with db() as conn:
        conn.execute("DELETE FROM products WHERE id=?", (pid,))
        conn.commit()


# =========================================================
# ========== دوال المبيعات ================================
# =========================================================
def add_sale(pid, buyer_id, amount_usd, amount_stars, method, status="completed"):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO sales
            (product_id,buyer_id,amount_usd,amount_stars,payment_method,status,sold_at)
            VALUES (?,?,?,?,?,?,?)""",
            (pid, str(buyer_id), amount_usd, amount_stars, method, status, now)
        )
        conn.commit()
        return cur.lastrowid


def update_sale_status(sale_id, status):
    with db() as conn:
        conn.execute("UPDATE sales SET status=? WHERE id=?", (status, sale_id))
        conn.commit()


def get_recent_sales(limit=10):
    with db() as conn:
        rows = conn.execute("SELECT * FROM sales ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_all_sales():
    with db() as conn:
        rows = conn.execute("SELECT * FROM sales ORDER BY id DESC LIMIT 100").fetchall()
        return [dict(r) for r in rows]


def get_user_sales(user_id):
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM sales WHERE buyer_id=? ORDER BY id DESC LIMIT 50",
            (str(user_id),)
        ).fetchall()
        return [dict(r) for r in rows]


# =========================================================
# ========== دوال أسعار الشحن =============================
# =========================================================
def get_charge_prices():
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM charge_prices WHERE is_active=1 ORDER BY amount_usd ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def add_charge_price(amount_usd, amount_stars):
    with db() as conn:
        conn.execute(
            "INSERT INTO charge_prices (amount_usd,amount_stars,created_at) VALUES (?,?,?)",
            (amount_usd, amount_stars, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()


def delete_charge_price(pid):
    with db() as conn:
        conn.execute("UPDATE charge_prices SET is_active=0 WHERE id=?", (pid,))
        conn.commit()


def get_charge_price_by_id(pid):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM charge_prices WHERE id=? AND is_active=1", (pid,)
        ).fetchone()
        return dict(row) if row else None


def update_charge_price(pid, amount_usd, amount_stars):
    with db() as conn:
        conn.execute(
            "UPDATE charge_prices SET amount_usd=?, amount_stars=? WHERE id=?",
            (amount_usd, amount_stars, pid)
        )
        conn.commit()


# =========================================================
# ========== دوال إحصائيات النجوم =========================
# =========================================================
def add_star_charge(user_id, username, amount_usd, amount_stars):
    with db() as conn:
        conn.execute(
            "INSERT INTO star_charges (user_id,username,amount_usd,amount_stars,charged_at) VALUES (?,?,?,?,?)",
            (str(user_id), username, amount_usd, amount_stars,
             datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()


def get_star_charge_stats():
    with db() as conn:
        unique_users = conn.execute("SELECT COUNT(DISTINCT user_id) c FROM star_charges").fetchone()["c"]
        total_charges = conn.execute("SELECT COUNT(*) c FROM star_charges").fetchone()["c"]
        total_stars = conn.execute("SELECT COALESCE(SUM(amount_stars),0) s FROM star_charges").fetchone()["s"]
        total_usd = conn.execute("SELECT COALESCE(SUM(amount_usd),0) s FROM star_charges").fetchone()["s"]
        recent = conn.execute(
            "SELECT * FROM star_charges ORDER BY id DESC LIMIT 10"
        ).fetchall()
        return {
            "unique_users": unique_users,
            "total_charges": total_charges,
            "total_stars": total_stars,
            "total_usd": total_usd,
            "recent": [dict(r) for r in recent]
        }


# =========================================================
# ========== دوال الإحالات ================================
# =========================================================
def get_referral_reward():
    return float(get_setting('referral_reward', '0.05'))


def set_referral_reward(amount):
    set_setting('referral_reward', str(amount))


def is_referral_enabled():
    return get_setting('referral_enabled', '1') == '1'


def get_referral_daily_limit():
    return int(get_setting('referral_daily_limit', '10'))


def add_referral(referrer_id, referred_id, amount):
    with db() as conn:
        try:
            conn.execute(
                "INSERT INTO referrals (referrer_id,referred_id,amount,created_at) VALUES (?,?,?,?)",
                (str(referrer_id), str(referred_id), amount,
                 datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def get_user_referrals(user_id):
    with db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) c, COALESCE(SUM(amount),0) s FROM referrals WHERE referrer_id=?",
            (str(user_id),)
        ).fetchone()
        return {"count": row["c"], "total_earned": row["s"]}


def get_daily_referrals(user_id):
    today = datetime.now().strftime('%Y-%m-%d')
    with db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) c FROM referrals WHERE referrer_id=? AND DATE(created_at)=?",
            (str(user_id), today)
        ).fetchone()
        return row["c"]


def get_recent_referrals(user_id, limit=10):
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM referrals WHERE referrer_id=? ORDER BY id DESC LIMIT ?",
            (str(user_id), limit)
        ).fetchall()
        return [dict(r) for r in rows]


def get_referral_stats():
    with db() as conn:
        unique_referrers = conn.execute("SELECT COUNT(DISTINCT referrer_id) c FROM referrals").fetchone()["c"]
        total_referrals = conn.execute("SELECT COUNT(*) c FROM referrals").fetchone()["c"]
        total_paid = conn.execute("SELECT COALESCE(SUM(amount),0) s FROM referrals").fetchone()["s"]
        recent = conn.execute("SELECT * FROM referrals ORDER BY id DESC LIMIT 10").fetchall()
        return {
            "unique_referrers": unique_referrers,
            "total_referrals": total_referrals,
            "total_paid": total_paid,
            "recent": [dict(r) for r in recent]
        }


# =========================================================
# ========== دوال الأزرار ================================
# =========================================================
def get_all_buttons():
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM buttons ORDER BY row ASC, col ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def update_button(key, label=None, style=None, row=None, col=None, is_active=None):
    with db() as conn:
        if label:
            conn.execute("UPDATE buttons SET label=? WHERE button_key=?", (label, key))
        if style:
            conn.execute("UPDATE buttons SET style=? WHERE button_key=?", (style, key))
        if row is not None:
            conn.execute("UPDATE buttons SET row=? WHERE button_key=?", (row, key))
        if col is not None:
            conn.execute("UPDATE buttons SET col=? WHERE button_key=?", (col, key))
        if is_active is not None:
            conn.execute("UPDATE buttons SET is_active=? WHERE button_key=?", (is_active, key))
        conn.commit()


# =========================================================
# ========== دوال القنوات =================================
# =========================================================
def add_channel(channel_id, channel_name=""):
    with db() as conn:
        try:
            if not channel_name:
                channel_name = f"قناة {channel_id}"
            conn.execute(
                "INSERT INTO channels (channel_id,channel_name,created_at) VALUES (?,?,?)",
                (channel_id, channel_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            conn.commit()
            return True
        except:
            return False


def get_activation_channels():
    with db() as conn:
        rows = conn.execute("SELECT * FROM channels WHERE is_activation=1").fetchall()
        return [dict(r) for r in rows]


def set_activation_channel(channel_id):
    with db() as conn:
        conn.execute("UPDATE channels SET is_activation=0")
        conn.execute("UPDATE channels SET is_activation=1 WHERE channel_id=?", (channel_id,))
        conn.commit()


def get_activation_channel():
    with db() as conn:
        row = conn.execute(
            "SELECT channel_id FROM channels WHERE is_activation=1 LIMIT 1"
        ).fetchone()
        return row["channel_id"] if row else None


# =========================================================
# ========== دوال مساعدة =================================
# =========================================================
def usd_to_stars(usd_amount):
    rate = get_exchange_rate()
    return int(usd_amount * rate)


def get_user_mention(user_id, first_name):
    return f'<a href="tg://user?id={user_id}">{first_name}</a>'


def get_username(user_id, username):
    if username:
        return f"@{username}"
    return f'<a href="tg://user?id={user_id}">لا يوجد يوزر</a>'


# =========================================================
# ========== بناء الأزرار =================================
# =========================================================
def main_menu(user_id):
    """القائمة العلوية للبوت"""
    is_admin_user = is_admin(user_id)
    buttons = get_all_buttons()
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    row_dict = {}
    for b in buttons:
        if not b['is_active']:
            continue
        r = b['row']
        if r not in row_dict:
            row_dict[r] = []
        row_dict[r].append(b)
    
    for row_num in sorted(row_dict.keys()):
        btn_list = []
        for b in sorted(row_dict[row_num], key=lambda x: x['col']):
            btn_list.append(
                types.InlineKeyboardButton(b['label'], callback_data=b['button_key'], style=b['style'])
            )
        markup.row(*btn_list)
    
    # زر قناة التفعيل
    activation = get_activation_channel()
    if activation:
        channel_name = activation.replace('@', '')
        markup.row(types.InlineKeyboardButton(
            "📢 قناة التفعيل والمشتريات",
            url=f"https://t.me/{channel_name}",
            style="primary"
        ))
    
    # زر الموقع
    if WEBAPP_URL and not WEBAPP_URL.startswith("http://localhost"):
        markup.row(types.InlineKeyboardButton(
            "🌐 فتح الموقع",
            url=WEBAPP_URL,
            style="success"
        ))
    
    if is_admin_user:
        markup.row(types.InlineKeyboardButton(
            "⚙️ لوحة التحكم",
            callback_data="admin_panel",
            style="danger"
        ))
    
    return markup


def admin_panel_keyboard():
    """لوحة تحكم الأدمن في البوت"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    markup.add(types.InlineKeyboardButton("➕ إضافة منتج", callback_data="admin_add_product", style="success"))
    markup.add(
        types.InlineKeyboardButton("📦 المنتجات", callback_data="admin_products", style="primary"),
        types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats", style="primary"),
    )
    markup.add(
        types.InlineKeyboardButton("📋 المبيعات", callback_data="admin_sales", style="primary"),
        types.InlineKeyboardButton("💰 شحن رصيد", callback_data="admin_charge", style="primary"),
    )
    markup.add(
        types.InlineKeyboardButton("💱 سعر الصرف", callback_data="admin_exchange", style="primary"),
        types.InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users", style="primary"),
    )
    markup.add(
        types.InlineKeyboardButton("🗑️ حذف منتج", callback_data="admin_delete_product", style="primary"),
        types.InlineKeyboardButton("🎨 تخصيص الأزرار", callback_data="admin_edit_buttons", style="primary"),
    )
    markup.add(
        types.InlineKeyboardButton("💲 أسعار الشحن", callback_data="admin_charge_prices", style="danger"),
        types.InlineKeyboardButton("👑 إدارة المطورين", callback_data="admin_developers", style="danger"),
    )
    markup.add(
        types.InlineKeyboardButton("📢 إدارة القنوات", callback_data="admin_channels", style="danger"),
        types.InlineKeyboardButton("⭐ إحصائيات النجوم", callback_data="admin_star_stats", style="danger"),
    )
    markup.add(types.InlineKeyboardButton("🎁 إدارة الإحالات", callback_data="admin_referral_panel", style="success"))
    markup.add(types.InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel", style="success"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main", style="danger"))
    
    return markup


def back_admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🔙 رجوع للوحة التحكم", callback_data="admin_panel", style="danger"))
    return markup


# =========================================================
# ========== معالجات أوامر البوت ==========================
# =========================================================
@bot.message_handler(commands=['start', 'menu'])
def start_cmd(message):
    user_id = str(message.from_user.id)
    
    # ✅ معالجة الإحالة
    referrer_id = None
    if message.text and 'ref_' in message.text:
        try:
            referrer_id = message.text.split('ref_')[1].strip()
        except:
            pass
    
    is_new_user = not get_user(user_id)
    if is_new_user:
        create_user(user_id, message.from_user.username or "", message.from_user.first_name or "")
        
        if referrer_id and referrer_id != user_id and is_referral_enabled():
            referrer = get_user(referrer_id)
            if referrer:
                daily = get_daily_referrals(referrer_id)
                daily_limit = get_referral_daily_limit()
                
                if daily < daily_limit:
                    reward = get_referral_reward()
                    if add_referral(referrer_id, user_id, reward):
                        add_balance_usd(referrer_id, reward)
                        try:
                            bot.send_message(
                                int(referrer_id),
                                f"🎉 <b>مبروك!</b>\n\n"
                                f"👤 صديق جديد انضم عبر رابطك:\n"
                                f"<b>{message.from_user.first_name}</b>\n\n"
                                f"💰 <b>ربحت:</b> {reward:.2f}$\n"
                                f"📊 <b>إحالاتك اليوم:</b> {daily + 1}/{daily_limit}\n"
                                f"💵 <b>رصيدك الجديد:</b> {get_user(referrer_id)['balance_usd']:.2f}$",
                                parse_mode="HTML"
                            )
                        except:
                            pass
    
    store_name = get_setting('store_name', '🛍️ متجر الأرقام')
    user = get_user(user_id)
    
    text = f"""
<b>🌟 أهـــلاً وســـهـــلاً بـــك 🌟</b>

<blockquote>✨ <b>{store_name}</b> ✨</blockquote>

<b>👋 مرحباً</b> <i>{message.from_user.first_name}</i>!

<blockquote>💎 <b>نـــورت الـــمـــتـــجـــر</b>
🎁 هــنــا تــجــد كــل مــا تــحــتــاجــه
🚀 بأفضل الأسعار وأسرع خدمة</blockquote>

<b>💰 رصيدك:</b> <code>{user['balance_usd']:.2f}$</code>
<b>📦 المنتجات:</b> <code>{get_product_count()['available']}</code>

<s>━━━━━━━━━━━━━━━━━━━━</s>

<b>🔹 اخـــتـــر مـــن الـــقـــائـــمـــة:</b>
"""
    
    # القائمة السفلية
    reply_markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    reply_markup.add(
        KeyboardButton("💰 رصيدي"),
        KeyboardButton("📋 طلباتي")
    )
    reply_markup.add(
        KeyboardButton("💳 شحن رصيد"),
        KeyboardButton("❓ مساعدة")
    )
    reply_markup.add(
        KeyboardButton("🎁 شارك واربح"),
        KeyboardButton("🔄 تشغيل البوت")
    )
    reply_markup.add(KeyboardButton("🌐 الموقع"))
    
    bot.reply_to(message, text, parse_mode="HTML", reply_markup=reply_markup)
    
    # القائمة العلوية
    bot.send_message(
        message.chat.id,
        "<u><b>🔹 الـــقـــائـــمـــة الـــرئـــيـــســـيـــة 🔹</b></u>",
        parse_mode="HTML",
        reply_markup=main_menu(user_id)
    )


@bot.message_handler(commands=['id'])
def send_id(message):
    bot.reply_to(
        message,
        f"🆔 <b>معلوماتك:</b>\n\n"
        f"👤 <b>الاسم:</b> {message.from_user.first_name}\n"
        f"🆔 <b>الآيدي:</b> <code>{message.from_user.id}</code>\n"
        f"👤 <b>اليوزر:</b> @{message.from_user.username or 'لا يوجد'}",
        parse_mode="HTML"
    )


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(
        message,
        f"❓ <b>المساعدة</b>\n\n"
        f"🔹 /start - القائمة الرئيسية\n"
        f"🔹 /id - عرض آيديك\n"
        f"🔹 /help - المساعدة\n\n"
        f"🌐 <b>الموقع:</b> {WEBAPP_URL}\n"
        f"للتواصل: @{DEVELOPER_USERNAME}",
        parse_mode="HTML"
    )


# =========================================================
# ========== معالجات القائمة السفلية =====================
# =========================================================
@bot.message_handler(func=lambda m: m.text == "💰 رصيدي")
def btn_balance(message):
    user = get_user(str(message.from_user.id))
    if not user:
        bot.reply_to(message, "❌ حدث خطأ")
        return
    bot.reply_to(
        message,
        f"💰 <b>رصيدك:</b> <code>{user['balance_usd']:.2f}$</code>\n"
        f"📦 <b>طلباتك:</b> {user['orders_count']}\n"
        f"💵 <b>إجمالي المشتريات:</b> {user['total_spent']:.2f}$",
        parse_mode="HTML"
    )


@bot.message_handler(func=lambda m: m.text == "📋 طلباتي")
def btn_orders(message):
    sales = get_user_sales(str(message.from_user.id))
    if not sales:
        bot.reply_to(message, "📭 لا توجد طلبات سابقة")
        return
    
    text = "📋 <b>طلباتك:</b>\n\n"
    for s in sales[:10]:
        status = "✅ مكتمل" if s['status'] == 'completed' else "⏳ قيد المراجعة" if s['status'] == 'pending' else "❌ مرفوض"
        text += f"🆔 #{s['id']}\n💵 {s['amount_usd']}$\n📊 {status}\n🕒 {s['sold_at']}\n\n"
    
    bot.reply_to(message, text, parse_mode="HTML")


@bot.message_handler(func=lambda m: m.text == "❓ مساعدة")
def btn_help(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    if WEBAPP_URL and not WEBAPP_URL.startswith("http://localhost"):
        markup.add(types.InlineKeyboardButton("🌐 فتح الموقع", url=WEBAPP_URL, style="success"))
    markup.add(
        types.InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEVELOPER_USERNAME}", style="primary"),
        types.InlineKeyboardButton("👑 الأدمن", url="https://t.me/E_E_72", style="danger")
    )
    bot.reply_to(
        message,
        f"❓ <b>المساعدة</b>\n\n🌐 <b>الموقع:</b> {WEBAPP_URL}\n\n👇 <b>للتواصل:</b>",
        parse_mode="HTML",
        reply_markup=markup
    )


@bot.message_handler(func=lambda m: m.text == "🎁 شارك واربح")
def btn_share(message):
    user_id = str(message.from_user.id)
    
    if not is_referral_enabled():
        bot.reply_to(message, "❌ الميزة معطلة حالياً")
        return
    
    bot_info = bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    stats = get_user_referrals(user_id)
    daily = get_daily_referrals(user_id)
    daily_limit = get_referral_daily_limit()
    reward = get_referral_reward()
    
    text = f"""
🎁 <b>شارك واربح</b>

💰 <b>المكافأة/صديق:</b> {reward:.2f}$
👥 <b>إحالاتك:</b> {stats['count']}
💵 <b>إجمالي الأرباح:</b> {stats['total_earned']:.2f}$
📅 <b>إحالات اليوم:</b> {daily}/{daily_limit}

🔗 <b>رابطك:</b>
<code>{referral_link}</code>
"""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(
        "📤 مشاركة الرابط",
        url=f"https://t.me/share/url?url={referral_link}&text=انضم!",
        style="success"
    ))
    
    bot.reply_to(message, text, parse_mode="HTML", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "🔄 تشغيل البوت")
def btn_restart(message):
    start_cmd(message)


@bot.message_handler(func=lambda m: m.text == "🌐 الموقع")
def btn_website(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🌐 فتح الموقع", url=WEBAPP_URL, style="success"))
    bot.reply_to(
        message,
        f"🌐 <b>الموقع الرسمي</b>\n\nاضغط الزر:",
        parse_mode="HTML",
        reply_markup=markup
    )


# =========================================================
# ========== معالجات الأزرار (Callback) ===================
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == 'show_products')
def cb_show_products(call):
    products = get_available_products()
    user_id = str(call.from_user.id)
    
    if not products:
        bot.edit_message_text(
            "📭 لا توجد منتجات متاحة حالياً.",
            call.message.chat.id, call.message.message_id,
            reply_markup=main_menu(user_id)
        )
        return
    
    text = "🛍️ <b>العروض المتاحة</b>\n\n"
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    # عناوين
    markup.row(
        types.InlineKeyboardButton("📌 التوفر", callback_data="noop", style="primary"),
        types.InlineKeyboardButton("📌 الاسم", callback_data="noop", style="success"),
        types.InlineKeyboardButton("📌 السعر", callback_data="noop", style="danger")
    )
    
    for p in products:
        availability = "♾️ عند طلب" if p['sale_type'] == 'manual' else f"✅ متوفر ({p['stock']})"
        markup.row(
            types.InlineKeyboardButton(availability, callback_data=f"buy_{p['id']}", style="primary"),
            types.InlineKeyboardButton(f"📦 {p['name']}", callback_data=f"product_info_{p['id']}", style="success"),
            types.InlineKeyboardButton(f"{p['price_usd']}$", callback_data=f"product_info_{p['id']}", style="danger")
        )
    
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main", style="danger"))
    
    bot.edit_message_text(
        text, call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'noop')
def cb_noop(call):
    bot.answer_callback_query(call.id, "هذا زر عنوان فقط")


@bot.callback_query_handler(func=lambda call: call.data.startswith('product_info_'))
def cb_product_info(call):
    pid = int(call.data.split('_')[2])
    p = get_product(pid)
    if not p:
        bot.answer_callback_query(call.id, "❌ المنتج غير موجود")
        return
    
    user = get_user(str(call.from_user.id))
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(
        f"💳 شراء ({p['price_usd']}$)",
        callback_data=f"pay_usd_{pid}",
        style="success"
    ))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="show_products", style="primary"))
    
    bot.edit_message_text(
        f"💳 <b>تأكيد الشراء</b>\n\n"
        f"📦 <b>المنتج:</b> {p['name']}\n"
        f"📝 {p['description']}\n"
        f"💰 <b>السعر:</b> {p['price_usd']}$\n"
        f"💵 <b>رصيدك:</b> {user['balance_usd']:.2f}$",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def cb_buy(call):
    pid = int(call.data.split('_')[1])
    p = get_product(pid)
    if not p or p['status'] != 'available' or p['stock'] <= 0:
        bot.answer_callback_query(call.id, "❌ غير متوفر")
        return
    
    user = get_user(str(call.from_user.id))
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(
        f"💳 شراء ({p['price_usd']}$)",
        callback_data=f"pay_usd_{pid}",
        style="success"
    ))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="show_products", style="primary"))
    
    bot.edit_message_text(
        f"💳 <b>تأكيد الشراء</b>\n\n"
        f"📦 <b>المنتج:</b> {p['name']}\n"
        f"💰 <b>السعر:</b> {p['price_usd']}$\n"
        f"💵 <b>رصيدك:</b> {user['balance_usd']:.2f}$",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_usd_'))
def cb_pay_usd(call):
    pid = int(call.data.split('_')[2])
    p = get_product(pid)
    user_id = str(call.from_user.id)
    
    if not p or p['status'] != 'available' or p['stock'] <= 0:
        bot.answer_callback_query(call.id, "❌ غير متوفر")
        return
    
    user = get_user(user_id)
    if not user or user['balance_usd'] < p['price_usd']:
        bot.answer_callback_query(call.id, f"❌ رصيدك غير كافٍ")
        return
    
    if deduct_balance_usd(user_id, p['price_usd']):
        process_purchase(pid, user_id, call, "دولار")


def process_purchase(pid, user_id, call, method):
    p = get_product(pid)
    user = get_user(user_id)
    
    if p['sale_type'] == 'manual':
        # بيع يدوي
        sale_id = add_sale(pid, user_id, p['price_usd'], 0, method, "pending")
        
        bot.edit_message_text(
            f"⏳ <b>طلبك قيد المراجعة!</b>\n\n"
            f"📦 <b>المنتج:</b> {p['name']}\n"
            f"💰 <b>السعر:</b> {p['price_usd']}$\n"
            f"🔔 سيتم التسليم بعد تأكيد الأدمن",
            call.message.chat.id, call.message.message_id,
            parse_mode="HTML"
        )
        
        # إشعار الأدمن
        for admin_id in ADMIN_IDS:
            try:
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("✅ تأكيد",
                        callback_data=f"confirm_sale_{pid}_{user_id}_{method}_{sale_id}",
                        style="success"),
                    types.InlineKeyboardButton("❌ رفض",
                        callback_data=f"reject_sale_{pid}_{user_id}_{method}_{sale_id}",
                        style="danger")
                )
                bot.send_message(
                    admin_id,
                    f"🤝 <b>طلب بيع يدوي!</b>\n\n"
                    f"📦 {p['name']}\n"
                    f"👤 {get_user_mention(user_id, call.from_user.first_name)}\n"
                    f"💰 {p['price_usd']}$",
                    parse_mode="HTML", reply_markup=markup
                )
            except:
                pass
    else:
        # بيع تلقائي
        new_stock = p['stock'] - 1
        if new_stock <= 0:
            mark_sold(pid, user_id)
        else:
            update_stock(pid, new_stock)
        
        add_sale(pid, user_id, p['price_usd'], 0, method, "completed")
        
        with db() as conn:
            conn.execute(
                "UPDATE users SET orders_count=orders_count+1, total_spent=total_spent+? WHERE user_id=?",
                (p['price_usd'], user_id)
            )
            conn.commit()
        
        # رسالة النجاح
        success_text = (
            f"✅ <b>تم الشراء بنجاح!</b>\n\n"
            f"📦 <b>المنتج:</b> {p['name']}\n"
            f"🔑 <b>الكود:</b> <code>{p['code']}</code>\n"
            f"💰 {p['price_usd']}$"
        )
        try:
            bot.edit_message_text(
                success_text, call.message.chat.id, call.message.message_id,
                parse_mode="HTML"
            )
        except:
            bot.send_message(call.message.chat.id, success_text, parse_mode="HTML")
        
        # إرسال الملف
        if p.get('file_id'):
            try:
                bot.send_document(
                    call.from_user.id, p['file_id'],
                    caption=f"📎 ملف المنتج: {p['name']}"
                )
            except:
                try:
                    bot.send_photo(
                        call.from_user.id, p['file_id'],
                        caption=f"📎 صورة المنتج: {p['name']}"
                    )
                except:
                    pass


@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_sale_'))
def cb_confirm_sale(call):
    user_id = str(call.from_user.id)
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    
    parts = call.data.split('_')
    pid = int(parts[2])
    buyer_id = parts[3]
    method = parts[4]
    sale_id = int(parts[5])
    
    p = get_product(pid)
    if not p:
        bot.answer_callback_query(call.id, "❌ المنتج غير موجود")
        return
    
    new_stock = p['stock'] - 1
    if new_stock <= 0:
        mark_sold(pid, buyer_id)
    else:
        update_stock(pid, new_stock)
    
    update_sale_status(sale_id, "completed")
    
    try:
        bot.send_message(
            int(buyer_id),
            f"✅ <b>تم تأكيد طلبك!</b>\n\n"
            f"📦 {p['name']}\n"
            f"🔑 <code>{p.get('code', 'لا يوجد')}</code>\n"
            f"💰 {p.get('price_usd', 0)}$",
            parse_mode="HTML"
        )
    except:
        pass
    
    if p.get('file_id'):
        try:
            bot.send_document(int(buyer_id), p['file_id'],
                            caption=f"📎 ملف المنتج: {p['name']}")
        except:
            pass
    
    bot.answer_callback_query(call.id, "✅ تم التأكيد")
    bot.edit_message_text("✅ <b>تم تأكيد البيع!</b>",
                         call.message.chat.id, call.message.message_id,
                         parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_sale_'))
def cb_reject_sale(call):
    user_id = str(call.from_user.id)
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    
    parts = call.data.split('_')
    pid = int(parts[2])
    buyer_id = parts[3]
    sale_id = int(parts[5])
    
    p = get_product(pid)
    if p:
        add_balance_usd(buyer_id, p['price_usd'])
        update_sale_status(sale_id, "rejected")
        
        try:
            bot.send_message(
                buyer_id,
                f"❌ <b>تم رفض طلبك</b>\n\n"
                f"📦 {p['name']}\n"
                f"💰 تم إرجاع المبلغ",
                parse_mode="HTML"
            )
        except:
            pass
    
    bot.answer_callback_query(call.id, "❌ تم الرفض")
    bot.edit_message_text("❌ <b>تم رفض الطلب</b>",
                         call.message.chat.id, call.message.message_id,
                         parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == 'my_balance')
def cb_my_balance(call):
    user = get_user(str(call.from_user.id))
    bot.edit_message_text(
        f"💰 <b>رصيدك:</b> <code>{user['balance_usd']:.2f}$</code>\n"
        f"📦 <b>طلباتك:</b> {user['orders_count']}",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=main_menu(str(call.from_user.id))
    )


@bot.callback_query_handler(func=lambda call: call.data == 'my_orders')
def cb_my_orders(call):
    sales = get_user_sales(str(call.from_user.id))
    if not sales:
        bot.edit_message_text("📭 لا توجد طلبات",
                             call.message.chat.id, call.message.message_id,
                             reply_markup=main_menu(str(call.from_user.id)))
        return
    
    text = "📋 <b>طلباتك:</b>\n\n"
    for s in sales[:10]:
        status = "✅" if s['status'] == 'completed' else "⏳" if s['status'] == 'pending' else "❌"
        text += f"{status} #{s['id']} - {s['amount_usd']}$\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="HTML", reply_markup=main_menu(str(call.from_user.id)))


@bot.callback_query_handler(func=lambda call: call.data == 'charge_balance')
def cb_charge_balance(call):
    prices = get_charge_prices()
    if not prices:
        bot.answer_callback_query(call.id, "❌ لا توجد أسعار")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    for p in prices:
        markup.add(types.InlineKeyboardButton(
            f"💵 {p['amount_usd']}$ = ⭐ {p['amount_stars']}",
            callback_data=f"charge_{p['amount_usd']}_{p['amount_stars']}",
            style="success" if p['amount_usd'] <= 5 else "primary"
        ))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main", style="danger"))
    
    rate = get_exchange_rate()
    bot.edit_message_text(
        f"💳 <b>شحن الرصيد</b>\n\n"
        f"💱 سعر الصرف: 1$ = {rate} ⭐\n\n"
        f"اختر المبلغ:",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('charge_'))
def cb_process_charge(call):
    parts = call.data.split('_')
    amount_usd = float(parts[1])
    amount_stars = int(parts[2])
    user_id = str(call.from_user.id)
    
    try:
        bot.send_invoice(
            call.message.chat.id,
            title=f"💳 شحن {amount_usd}$",
            description=f"شحن {amount_usd}$ = {amount_stars} نجمة",
            invoice_payload=json.dumps({
                'type': 'charge',
                'amount_usd': amount_usd,
                'amount_stars': amount_stars,
                'user_id': user_id
            }),
            provider_token="",
            currency="XTR",
            prices=[types.LabeledPrice("⭐", amount_stars)],
            start_parameter="charge"
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {e}")


@bot.pre_checkout_query_handler(func=lambda q: True)
def pre_checkout(q):
    bot.answer_pre_checkout_query(q.id, True)


@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    try:
        payload = json.loads(message.successful_payment.invoice_payload)
        if payload.get('type') == 'charge':
            user_id = payload['user_id']
            amount_usd = payload['amount_usd']
            amount_stars = payload['amount_stars']
            
            add_balance_usd(user_id, amount_usd)
            add_balance_stars(user_id, amount_stars)
            add_star_charge(user_id, message.from_user.username or "", amount_usd, amount_stars)
            
            user = get_user(user_id)
            bot.send_message(
                message.chat.id,
                f"✅ <b>تم شحن رصيدك!</b>\n\n"
                f"⭐ {amount_stars} نجمة\n"
                f"💵 {amount_usd}$\n"
                f"💰 <b>رصيدك:</b> {user['balance_usd']:.2f}$",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Payment error: {e}")


@bot.callback_query_handler(func=lambda call: call.data == 'support')
def cb_support(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEVELOPER_USERNAME}", style="primary"),
        types.InlineKeyboardButton("👑 الأدمن", url="https://t.me/E_E_72", style="danger"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main", style="danger")
    )
    bot.edit_message_text(
        "📞 <b>الدعم الفني</b>\n\n👇 اضغط للتواصل:",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'back_main')
def cb_back_main(call):
    user_id = str(call.from_user.id)
    store_name = get_setting('store_name', '🛍️ متجر الأرقام')
    user = get_user(user_id)
    bot.edit_message_text(
        f"<b>{store_name}</b>\n\n"
        f"💰 رصيدك: {user['balance_usd']:.2f}$\n"
        f"📦 المنتجات: {get_product_count()['available']}",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=main_menu(user_id)
    )


# =========================================================
# ========== لوحة تحكم الأدمن ============================
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == 'admin_panel')
def cb_admin_panel(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    
    stats = get_product_count()
    bot.edit_message_text(
        f"⚙️ <b>لوحة التحكم</b>\n\n"
        f"📦 المتاحة: {stats['available']}\n"
        f"📦 الإجمالي: {stats['total']}\n"
        f"💱 سعر الصرف: {get_exchange_rate()} ⭐ = 1$\n\n"
        f"🔹 اختر الإجراء:",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=admin_panel_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data == 'admin_stats')
def cb_admin_stats(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    
    stats = get_product_count()
    rate = get_exchange_rate()
    users_count = count_users()
    
    bot.edit_message_text(
        f"📊 <b>الإحصائيات</b>\n\n"
        f"📦 المتاحة: {stats['available']}\n"
        f"📦 الإجمالي: {stats['total']}\n"
        f"👥 المستخدمين: {users_count}\n"
        f"💱 سعر الصرف: {rate} ⭐ = 1$",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=back_admin_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data == 'admin_products')
def cb_admin_products(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    
    products = get_available_products()
    if not products:
        bot.edit_message_text("📭 لا توجد منتجات",
                             call.message.chat.id, call.message.message_id,
                             reply_markup=back_admin_keyboard())
        return
    
    text = "📦 <b>المنتجات:</b>\n\n"
    for p in products[:15]:
        st = "⚡" if p['sale_type'] == 'auto' else "🤝"
        text += f"🆔 {p['id']} | {st} {p['name']}\n💰 {p['price_usd']}$ | 📦 {p['stock']}\n\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="HTML", reply_markup=back_admin_keyboard())


@bot.callback_query_handler(func=lambda call: call.data == 'admin_users')
def cb_admin_users(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    
    data = get_all_users()
    text = f"👥 <b>المستخدمين: {data['total']}</b>\n\n"
    for u in data['users'][:10]:
        text += f"🆔 <code>{u['user_id']}</code>\n👤 {u['first_name'] or u['username'] or 'مستخدم'}\n💰 {u['balance_usd']:.2f}$\n\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="HTML", reply_markup=back_admin_keyboard())


@bot.callback_query_handler(func=lambda call: call.data == 'admin_sales')
def cb_admin_sales(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    
    sales = get_recent_sales(15)
    if not sales:
        bot.edit_message_text("📭 لا توجد مبيعات",
                             call.message.chat.id, call.message.message_id,
                             reply_markup=back_admin_keyboard())
        return
    
    text = "📋 <b>آخر المبيعات:</b>\n\n"
    for s in sales:
        st = "✅" if s['status'] == 'completed' else "⏳" if s['status'] == 'pending' else "❌"
        text += f"{st} #{s['id']} - {s['amount_usd']}$\n🆔 {s['buyer_id'][:10]}...\n\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="HTML", reply_markup=back_admin_keyboard())


@bot.callback_query_handler(func=lambda call: call.data == 'admin_exchange')
def cb_admin_exchange(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    
    rate = get_exchange_rate()
    markup = types.InlineKeyboardMarkup(row_width=3)
    for r in ["25", "50", "75", "100", "125", "150", "200", "250", "500"]:
        markup.add(types.InlineKeyboardButton(f"{r}", callback_data=f"set_rate_{r}", style="primary"))
    markup.add(types.InlineKeyboardButton("✏️ مخصص", callback_data="set_rate_custom", style="success"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="danger"))
    
    bot.edit_message_text(
        f"💱 <b>سعر الصرف الحالي:</b> {rate} ⭐ = 1$\n\nاختر السعر الجديد:",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('set_rate_'))
def cb_set_rate(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    
    if call.data == "set_rate_custom":
        msg = bot.edit_message_text("✏️ أرسل السعر الجديد:",
                                     call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(msg, save_custom_rate)
        return
    
    rate = int(call.data.split('_')[2])
    set_exchange_rate(rate)
    bot.answer_callback_query(call.id, f"✅ {rate} ⭐ = 1$")
    cb_admin_exchange(call)


def save_custom_rate(message):
    try:
        rate = int(message.text.strip())
        if rate < 1:
            raise ValueError
        set_exchange_rate(rate)
        bot.send_message(message.chat.id, f"✅ تم التحديث: {rate} ⭐ = 1$",
                        reply_markup=admin_panel_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ رقم غير صحيح",
                        reply_markup=admin_panel_keyboard())


@bot.callback_query_handler(func=lambda call: call.data == 'admin_charge')
def cb_admin_charge(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    msg = bot.send_message(call.message.chat.id,
                          "💰 أرسل: <code>آيدي, المبلغ</code>",
                          parse_mode="HTML")
    bot.register_next_step_handler(msg, admin_charge_step)


def admin_charge_step(message):
    try:
        data = message.text.split(',')
        uid = data[0].strip()
        amount = float(data[1].strip())
        add_balance_usd(uid, amount)
        bot.send_message(message.chat.id, f"✅ تم إضافة {amount}$ للمستخدم {uid}",
                        reply_markup=admin_panel_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ صيغة خطأ",
                        reply_markup=admin_panel_keyboard())


@bot.callback_query_handler(func=lambda call: call.data == 'admin_delete_product')
def cb_admin_delete_product(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    
    products = get_available_products()
    if not products:
        bot.answer_callback_query(call.id, "لا توجد منتجات")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for p in products[:20]:
        markup.add(types.InlineKeyboardButton(
            f"🗑️ {p['id']} - {p['name']}",
            callback_data=f"del_{p['id']}",
            style="danger"
        ))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
    
    bot.edit_message_text("🗑️ اختر منتجاً للحذف:",
                         call.message.chat.id, call.message.message_id,
                         reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('del_'))
def cb_delete(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    pid = int(call.data.split('_')[1])
    delete_product(pid)
    bot.answer_callback_query(call.id, "✅ تم الحذف")
    bot.edit_message_text("🗑️ تم الحذف",
                         call.message.chat.id, call.message.message_id,
                         reply_markup=admin_panel_keyboard())


# =========================================================
# ========== إضافة منتج ===================================
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == 'admin_add_product')
def cb_admin_add_product(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚡ تلقائي", callback_data="add_product_auto", style="success"),
        types.InlineKeyboardButton("🤝 يدوي", callback_data="add_product_manual", style="danger")
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="danger"))
    
    bot.edit_message_text("➕ <b>إضافة منتج</b>\n\nاختر نوع البيع:",
                         call.message.chat.id, call.message.message_id,
                         parse_mode="HTML", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'add_product_auto')
def cb_add_auto(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    uid = str(call.from_user.id)
    user_data[uid] = {'sale_type': 'auto', 'step': 'name'}
    msg = bot.edit_message_text("📦 <b>الخطوة 1/5</b>\nأرسل اسم المنتج:",
                                 call.message.chat.id, call.message.message_id,
                                 parse_mode="HTML", reply_markup=back_admin_keyboard())
    bot.register_next_step_handler(msg, step_name)


@bot.callback_query_handler(func=lambda call: call.data == 'add_product_manual')
def cb_add_manual(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    uid = str(call.from_user.id)
    user_data[uid] = {'sale_type': 'manual', 'step': 'name'}
    msg = bot.edit_message_text("📦 <b>الخطوة 1/5</b>\nأرسل اسم المنتج:",
                                 call.message.chat.id, call.message.message_id,
                                 parse_mode="HTML", reply_markup=back_admin_keyboard())
    bot.register_next_step_handler(msg, step_name)


def step_name(message):
    uid = str(message.from_user.id)
    if uid not in user_data:
        return
    user_data[uid]['name'] = message.text.strip()
    user_data[uid]['step'] = 'description'
    msg = bot.send_message(message.chat.id, "📝 أرسل الوصف:")
    bot.register_next_step_handler(msg, step_description)


def step_description(message):
    uid = str(message.from_user.id)
    if uid not in user_data:
        return
    user_data[uid]['description'] = message.text.strip()
    user_data[uid]['step'] = 'price'
    msg = bot.send_message(message.chat.id, "💰 أرسل السعر بالدولار:")
    bot.register_next_step_handler(msg, step_price)


def step_price(message):
    uid = str(message.from_user.id)
    if uid not in user_data:
        return
    try:
        user_data[uid]['price_usd'] = float(message.text.strip())
        user_data[uid]['step'] = 'category'
        msg = bot.send_message(message.chat.id, "🏷️ أرسل التصنيف:")
        bot.register_next_step_handler(msg, step_category)
    except:
        msg = bot.send_message(message.chat.id, "❌ رقم خطأ، أعد الإرسال:")
        bot.register_next_step_handler(msg, step_price)


def step_category(message):
    uid = str(message.from_user.id)
    if uid not in user_data:
        return
    user_data[uid]['category'] = message.text.strip()
    user_data[uid]['step'] = 'code'
    msg = bot.send_message(message.chat.id, "🔑 أرسل الكود:")
    bot.register_next_step_handler(msg, step_code)


def step_code(message):
    uid = str(message.from_user.id)
    if uid not in user_data:
        return
    user_data[uid]['code'] = message.text.strip()
    user_data[uid]['step'] = 'file'
    msg = bot.send_message(message.chat.id,
                          "📎 أرسل صورة/ملف (اختياري) أو اكتب 'تخطي':")
    bot.register_next_step_handler(msg, step_file)


def step_file(message):
    uid = str(message.from_user.id)
    if uid not in user_data:
        return
    
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.video:
        file_id = message.video.file_id
    
    user_data[uid]['file_id'] = file_id
    user_data[uid]['step'] = 'stock'
    msg = bot.send_message(message.chat.id, "📊 أرسل المخزون:")
    bot.register_next_step_handler(msg, step_stock)


def step_stock(message):
    uid = str(message.from_user.id)
    if uid not in user_data:
        return
    try:
        stock = int(message.text.strip())
        data = user_data[uid]
        add_product(
            name=data['name'],
            description=data['description'],
            price_usd=data['price_usd'],
            category=data['category'],
            code=data['code'],
            stock=stock,
            sale_type=data.get('sale_type', 'auto'),
            file_id=data.get('file_id')
        )
        bot.send_message(
            message.chat.id,
            f"✅ تم إضافة المنتج!\n\n"
            f"📦 {data['name']}\n"
            f"💰 {data['price_usd']}$\n"
            f"📊 المخزون: {stock}",
            reply_markup=admin_panel_keyboard()
        )
        del user_data[uid]
    except:
        msg = bot.send_message(message.chat.id, "❌ رقم خطأ:")
        bot.register_next_step_handler(msg, step_stock)


# =========================================================
# ========== إدارة الإحالات (أدمن) ========================
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == 'admin_referral_panel')
def cb_admin_referral(call):
    if not is_admin(str(call.from_user.id)):
        bot.answer_callback_query(call.id, "❌ غير مصرح")
        return
    
    reward = get_referral_reward()
    enabled = "✅" if is_referral_enabled() else "❌"
    limit = get_referral_daily_limit()
    stats = get_referral_stats()
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("💰 تغيير المكافأة", callback_data="admin_ref_set_reward", style="success"))
    markup.add(types.InlineKeyboardButton("📅 تغيير الحد", callback_data="admin_ref_set_limit", style="primary"))
    markup.add(types.InlineKeyboardButton("🔄 تفعيل/تعطيل", callback_data="admin_ref_toggle", style="danger"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="danger"))
    
    bot.edit_message_text(
        f"🎁 <b>إدارة الإحالات</b>\n\n"
        f"💰 المكافأة: {reward:.2f}$\n"
        f"🔘 الحالة: {enabled}\n"
        f"📅 الحد اليومي: {limit}\n\n"
        f"👥 المُحيلين: {stats['unique_referrers']}\n"
        f"🔄 الإحالات: {stats['total_referrals']}\n"
        f"💵 المدفوع: {stats['total_paid']:.2f}$",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'admin_ref_set_reward')
def cb_ref_set_reward(call):
    if not is_admin(str(call.from_user.id)):
        return
    msg = bot.send_message(call.message.chat.id, "💰 أرسل المكافأة الجديدة:")
    bot.register_next_step_handler(msg, save_ref_reward)


def save_ref_reward(message):
    try:
        amount = float(message.text.strip())
        set_referral_reward(amount)
        bot.send_message(message.chat.id, f"✅ المكافأة: {amount:.2f}$",
                        reply_markup=admin_panel_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ رقم خطأ",
                        reply_markup=admin_panel_keyboard())


@bot.callback_query_handler(func=lambda call: call.data == 'admin_ref_set_limit')
def cb_ref_set_limit(call):
    if not is_admin(str(call.from_user.id)):
        return
    msg = bot.send_message(call.message.chat.id, "📅 أرسل الحد اليومي:")
    bot.register_next_step_handler(msg, save_ref_limit)


def save_ref_limit(message):
    try:
        limit = int(message.text.strip())
        set_setting('referral_daily_limit', str(limit))
        bot.send_message(message.chat.id, f"✅ الحد: {limit}",
                        reply_markup=admin_panel_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ رقم خطأ",
                        reply_markup=admin_panel_keyboard())


@bot.callback_query_handler(func=lambda call: call.data == 'admin_ref_toggle')
def cb_ref_toggle(call):
    if not is_admin(str(call.from_user.id)):
        return
    new_state = "0" if is_referral_enabled() else "1"
    set_setting('referral_enabled', new_state)
    bot.answer_callback_query(call.id, "✅ تم التبديل")
    cb_admin_referral(call)


# =========================================================
# ========== إحصائيات النجوم ==============================
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == 'admin_star_stats')
def cb_star_stats(call):
    if not is_admin(str(call.from_user.id)):
        return
    
    stats = get_star_charge_stats()
    text = (
        f"⭐ <b>إحصائيات النجوم</b>\n\n"
        f"👥 عدد الأشخاص: {stats['unique_users']}\n"
        f"🔄 عدد العمليات: {stats['total_charges']}\n"
        f"⭐ مجموع النجوم: {stats['total_stars']}\n"
        f"💵 مجموع الدولار: {stats['total_usd']:.2f}$\n"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="HTML", reply_markup=back_admin_keyboard())


# =========================================================
# ========== إدارة القنوات ================================
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == 'admin_channels')
def cb_admin_channels(call):
    if not is_admin(str(call.from_user.id)):
        return
    
    activation = get_activation_channel()
    channels = get_activation_channels()
    
    text = f"📢 <b>إدارة القنوات</b>\n\n"
    text += f"🎯 قناة التفعيل: {activation or 'غير محددة'}\n\n"
    for ch in channels:
        text += f"└ {ch['channel_id']} | {ch['channel_name']}\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel", style="success"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="danger"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="HTML", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'add_channel')
def cb_add_channel(call):
    if not is_admin(str(call.from_user.id)):
        return
    msg = bot.send_message(call.message.chat.id,
                          "📢 أرسل معرف القناة (مثال: @my_channel):")
    bot.register_next_step_handler(msg, save_channel)


def save_channel(message):
    try:
        cid = message.text.strip()
        add_channel(cid)
        bot.send_message(message.chat.id, f"✅ تمت الإضافة: {cid}",
                        reply_markup=admin_panel_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ خطأ",
                        reply_markup=admin_panel_keyboard())


# =========================================================
# ========== إدارة المطورين ===============================
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == 'admin_developers')
def cb_admin_developers(call):
    if not is_admin(str(call.from_user.id)):
        return
    
    admins = get_all_admins()
    text = "👑 <b>المطورين:</b>\n\n"
    for a in admins:
        text += f"🆔 <code>{a}</code>\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ إضافة", callback_data="add_developer", style="success"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="danger"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="HTML", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'add_developer')
def cb_add_dev(call):
    if not is_admin(str(call.from_user.id)):
        return
    msg = bot.send_message(call.message.chat.id, "🆔 أرسل آيدي المطور الجديد:")
    bot.register_next_step_handler(msg, save_dev)


def save_dev(message):
    try:
        uid = message.text.strip()
        add_admin(uid)
        bot.send_message(message.chat.id, f"✅ تمت الإضافة: {uid}",
                        reply_markup=admin_panel_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ خطأ",
                        reply_markup=admin_panel_keyboard())


# =========================================================
# ========== أسعار الشحن ==================================
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == 'admin_charge_prices')
def cb_admin_charge_prices(call):
    if not is_admin(str(call.from_user.id)):
        return
    
    prices = get_charge_prices()
    text = "💲 <b>أسعار الشحن:</b>\n\n"
    for p in prices:
        text += f"🆔 {p['id']} | {p['amount_usd']}$ = ⭐ {p['amount_stars']}\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ إضافة سعر", callback_data="admin_add_price", style="success"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="danger"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="HTML", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'admin_add_price')
def cb_add_price(call):
    if not is_admin(str(call.from_user.id)):
        return
    msg = bot.send_message(call.message.chat.id,
                          "💲 أرسل: <code>الدولار, النجوم</code>",
                          parse_mode="HTML")
    bot.register_next_step_handler(msg, save_price)


def save_price(message):
    try:
        parts = message.text.split(',')
        usd = float(parts[0].strip())
        stars = int(parts[1].strip())
        add_charge_price(usd, stars)
        bot.send_message(message.chat.id, f"✅ {usd}$ = ⭐ {stars}",
                        reply_markup=admin_panel_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ صيغة خطأ",
                        reply_markup=admin_panel_keyboard())


# =========================================================
# ========== تخصيص الأزرار ================================
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == 'admin_edit_buttons')
def cb_admin_edit_buttons(call):
    if not is_admin(str(call.from_user.id)):
        return
    
    buttons = get_all_buttons()
    text = "🎨 <b>الأزرار:</b>\n\n"
    for b in buttons:
        status = "✅" if b['is_active'] else "❌"
        text += f"{status} <code>{b['button_key']}</code>\n└ {b['label']} | {b['style']}\n\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="HTML", reply_markup=back_admin_keyboard())


# =========================================================
# ========== تشغيل البوت في Thread ========================
# =========================================================
def run_bot():
    """تشغيل polling في Thread منفصل"""
    try:
        # انتظر الموقع
        time.sleep(2)
        
        print("🤖 [BOT] تشغيل البوت...")
        
        # حذف webhook
        try:
            bot.delete_webhook(drop_pending_updates=False)
            print("✅ [BOT] تم حذف webhook")
        except Exception as e:
            print(f"⚠️ [BOT] {e}")
        
        # تسجيل الأوامر
        try:
            bot.set_my_commands([
                BotCommand("start", "🏠 بدء البوت"),
                BotCommand("id", "🆔 عرض آيديك"),
                BotCommand("help", "❓ المساعدة"),
            ])
            print("✅ [BOT] تم تسجيل الأوامر")
        except Exception as e:
            print(f"⚠️ [BOT] {e}")
        
        bot_status['running'] = True
        print("🚀 [BOT] البوت شغال...")
        
        while True:
            try:
                bot.infinity_polling(
                    timeout=30,
                    long_polling_timeout=20,
                    none_stop=True,
                    skip_pending=False
                )
            except Exception as e:
                print(f"❌ [BOT] خطأ: {e}")
                time.sleep(5)
    except Exception as e:
        print(f"❌ [BOT] خطأ فادح: {e}")
        traceback.print_exc()


# =========================================================
# ========== Flask Routes =================================
# =========================================================
def verify_telegram_auth(data):
    """التحقق من Telegram Login Widget"""
    check_hash = data.pop('hash', None)
    if not check_hash:
        return False
    data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac_hash == check_hash


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if 'user_id' not in session:
            flash("الرجاء تسجيل الدخول", "error")
            return redirect(url_for('login'))
        return f(*a, **kw)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if not is_admin(session['user_id']):
            abort(403)
        return f(*a, **kw)
    return wrapper


@app.context_processor
def inject_globals():
    user = None
    if 'user_id' in session:
        user = get_user(session['user_id'])
    return {
        "current_user": user,
        "is_admin": is_admin(session['user_id']) if user else False,
        "store_name": get_setting('store_name', '🛍️ متجر الأرقام'),
        "developer": DEVELOPER_USERNAME,
    }


# ===== Health check =====
@app.route('/ping')
def ping():
    return "pong", 200


@app.route('/health')
def health():
    return {
        'status': 'ok' if bot_status['running'] else 'starting',
        'bot_running': bot_status['running'],
        'started_at': bot_status['started_at'],
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, 200


# ===== دالة عرض HTML =====
def render_page(content, title="", extra_css="", extra_js=""):
    user_name = "مستخدم"
    if 'user_id' in session:
        u = get_user(session['user_id'])
        if u:
            user_name = u['first_name'] or u['username'] or "مستخدم"
    
    user_html = ""
    if session.get('user_id'):
        user_html = f'''
        <div class="user-info">
            <span>👤 {user_name}</span>
            <a href="/logout" class="btn btn-danger" style="padding:8px 16px;font-size:12px;">خروج</a>
        </div>
        '''
    
    flashes = ''.join([f'<div class="flash {cat}">{msg}</div>' for cat, msg in get_flashed_messages(with_categories=True)])
    
    return f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title or get_setting('store_name', 'متجر الأرقام')}</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Cairo', sans-serif;
            background: #0a0e1a;
            color: #fff;
            direction: rtl;
            min-height: 100vh;
            line-height: 1.6;
        }}
        body::before {{
            content: '';
            position: fixed;
            inset: 0;
            background: 
                radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.15), transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(16, 185, 129, 0.1), transparent 50%);
            z-index: -1;
        }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
        .header {{
            display: flex; justify-content: space-between; align-items: center;
            padding: 20px;
            background: linear-gradient(135deg, #151b2e, #1e2740);
            border-radius: 16px; margin-bottom: 20px;
            border: 1px solid #2d3748;
            flex-wrap: wrap; gap: 12px;
        }}
        .header h1 {{
            font-size: 22px;
            background: linear-gradient(135deg, #3b82f6, #10b981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .user-info {{ display: flex; align-items: center; gap: 10px; font-size: 14px; color: #94a3b8; }}
        .card {{
            background: linear-gradient(135deg, #151b2e, #1a2338);
            border-radius: 16px; padding: 24px; margin-bottom: 16px;
            border: 1px solid #2d3748;
            animation: slideIn 0.5s ease;
        }}
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .card:hover {{ border-color: #3b82f6; }}
        .btn {{
            display: inline-flex; align-items: center; justify-content: center; gap: 8px;
            padding: 14px 20px; border: none; border-radius: 12px;
            font-size: 16px; font-weight: 700;
            cursor: pointer; text-decoration: none;
            transition: all 0.3s; font-family: inherit; color: #fff;
        }}
        .btn:hover {{ transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.4); }}
        .btn-primary {{ background: linear-gradient(135deg, #3b82f6, #2563eb); }}
        .btn-success {{ background: linear-gradient(135deg, #10b981, #059669); }}
        .btn-danger {{ background: linear-gradient(135deg, #ef4444, #dc2626); }}
        .btn-warning {{ background: linear-gradient(135deg, #f59e0b, #d97706); }}
        .btn-block {{ width: 100%; }}
        .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
        .input {{
            width: 100%; padding: 14px;
            background: #0a0e1a; border: 2px solid #2d3748;
            border-radius: 12px; color: #fff; font-size: 16px;
            font-family: inherit; margin-bottom: 12px;
        }}
        .input:focus {{ outline: none; border-color: #3b82f6; }}
        .flash {{
            padding: 14px 20px; border-radius: 12px; margin-bottom: 16px;
            font-weight: 700;
        }}
        .flash.success {{ background: rgba(16,185,129,0.15); border: 2px solid #10b981; color: #10b981; }}
        .flash.error {{ background: rgba(239,68,68,0.15); border: 2px solid #ef4444; color: #ef4444; }}
        .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 12px; }}
        .stat {{
            text-align: center; padding: 16px;
            background: #0a0e1a; border-radius: 12px;
            border: 1px solid #2d3748;
        }}
        .stat .num {{ font-size: 24px; font-weight: 900; color: #10b981; }}
        .stat .label {{ font-size: 12px; color: #94a3b8; margin-top: 4px; }}
        .footer {{ text-align: center; margin-top: 40px; padding: 20px; color: #64748b; font-size: 14px; }}
        @media (max-width: 600px) {{
            .grid, .stats {{ grid-template-columns: 1fr; }}
            .header {{ flex-direction: column; }}
        }}
        {extra_css}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✨ {get_setting('store_name', 'متجر الأرقام')}</h1>
            {user_html}
        </div>
        {flashes}
        {content}
        <div class="footer">
            <p>💙 {get_setting('store_name', 'متجر الأرقام')}</p>
            <p style="font-size: 12px;">تطوير: @{DEVELOPER_USERNAME}</p>
        </div>
    </div>
    <script>{extra_js}</script>
</body>
</html>'''


# ===== الصفحات =====
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uid = request.form.get('user_id', '').strip()
        if not uid.isdigit():
            flash("الآيدي يجب أن يكون أرقاماً", "error")
            return redirect(url_for('login'))
        if not get_user(uid):
            create_user(uid, "", f"مستخدم {uid}")
        session['user_id'] = uid
        flash("✅ تم تسجيل الدخول", "success")
        return redirect(url_for('index'))
    
    content = '''
    <div class="card" style="max-width: 500px; margin: 40px auto;">
        <h2 style="text-align: center; margin-bottom: 30px; color: #3b82f6;">🔐 تسجيل الدخول</h2>
        <p style="color: #94a3b8; margin-bottom: 20px; text-align: center;">
            أدخل الآيدي الخاص بك في Telegram
        </p>
        <div style="background: #0a0e1a; padding: 16px; border-radius: 12px; margin-bottom: 20px;">
            <p style="color: #10b981; font-weight: 700;">💡 كيف أحصل على الآيدي؟</p>
            <p style="font-size: 14px; color: #94a3b8; margin-top: 8px;">
                افتح البوت وأرسل <code>/id</code>
            </p>
        </div>
        <form method="POST">
            <input type="text" name="user_id" class="input" placeholder="مثال: 123456789" required pattern="[0-9]+">
            <button type="submit" class="btn btn-primary btn-block">🚀 دخول</button>
        </form>
    </div>
    '''
    return render_page(content, title="تسجيل الدخول")


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    user = get_user(session['user_id'])
    pc = get_product_count()
    
    content = f'''
    <div class="card" style="text-align: center;">
        <h2 style="font-size: 28px; margin-bottom: 12px;">🌟 أهلاً وسهلاً 🌟</h2>
        <p style="font-size: 20px; color: #3b82f6; font-weight: 700;">{user['first_name']}</p>
    </div>
    <div class="card">
        <h3 style="margin-bottom: 16px;">📊 إحصائيات</h3>
        <div class="stats">
            <div class="stat"><div class="num">{pc['available']}</div><div class="label">منتج</div></div>
            <div class="stat"><div class="num">{user['balance_usd']:.2f}$</div><div class="label">رصيدك</div></div>
            <div class="stat"><div class="num">{user['orders_count']}</div><div class="label">طلباتك</div></div>
        </div>
    </div>
    <div class="card">
        <h3 style="margin-bottom: 16px;">🔹 القائمة</h3>
        <div class="grid">
            <a href="/products" class="btn btn-primary">🛍️ المنتجات</a>
            <a href="/balance" class="btn btn-success">💰 رصيدي</a>
            <a href="/charge" class="btn btn-danger">💳 شحن الرصيد</a>
            <a href="/orders" class="btn btn-primary">📋 طلباتي</a>
            <a href="/share" class="btn btn-success">🎁 شارك واربح</a>
            <a href="/help" class="btn btn-danger">❓ مساعدة</a>
        </div>
    </div>
    '''
    
    if is_admin(session['user_id']):
        content += '''
        <div class="card" style="border-color: #f59e0b;">
            <h3 style="color: #f59e0b;">⚙️ لوحة التحكم</h3>
            <a href="/admin" class="btn btn-warning btn-block" style="margin-top: 12px;">🔧 فتح</a>
        </div>
        '''
    
    return render_page(content, title="الرئيسية")


@app.route('/products')
@login_required
def products():
    items = get_available_products()
    if not items:
        content = '''
        <div class="card" style="text-align: center;">
            <p style="font-size: 60px;">📭</p>
            <p>لا توجد منتجات</p>
            <a href="/" class="btn btn-primary" style="margin-top: 20px;">🔙 رجوع</a>
        </div>
        '''
        return render_page(content, title="المنتجات")
    
    html = ""
    for p in items:
        availability = "♾️ عند طلب" if p['sale_type'] == 'manual' else f"✅ متوفر ({p['stock']})"
        html += f'''
        <div class="card">
            <h3 style="color: #3b82f6;">📦 {p['name']}</h3>
            <p style="color: #94a3b8; margin: 8px 0;">{p['description'][:100]}</p>
            <p style="color: #10b981;">{availability}</p>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px;">
                <span style="font-size: 24px; font-weight: 900; color: #10b981;">{p['price_usd']}$</span>
                <a href="/product/{p['id']}" class="btn btn-primary">🛒 شراء</a>
            </div>
        </div>
        '''
    
    content = f'<div class="card"><h2>🛍️ المنتجات ({len(items)})</h2></div>{html}<a href="/" class="btn btn-danger btn-block">🔙 رجوع</a>'
    return render_page(content, title="المنتجات")


@app.route('/product/<int:pid>')
@login_required
def product_detail(pid):
    p = get_product(pid)
    if not p or p['status'] != 'available' or p['stock'] <= 0:
        flash("❌ المنتج غير متوفر", "error")
        return redirect(url_for('products'))
    
    user = get_user(session['user_id'])
    can_buy = user['balance_usd'] >= p['price_usd']
    
    content = f'''
    <div class="card">
        <h2 style="color: #3b82f6;">📦 {p['name']}</h2>
        <p style="color: #94a3b8; margin: 16px 0;">{p['description']}</p>
        <div style="background: #0a0e1a; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <p>💰 السعر: <b style="color: #10b981;">{p['price_usd']}$</b></p>
            <p>📊 المتوفر: <b>{p['stock']}</b></p>
            <p>💵 رصيدك: <b style="color: {'#10b981' if can_buy else '#ef4444'};">{user['balance_usd']:.2f}$</b></p>
        </div>
        <form method="POST" action="/buy/{p['id']}">
            <button type="submit" class="btn btn-success btn-block" {'disabled' if not can_buy else ''}>
                💳 شراء الآن
            </button>
        </form>
        <a href="/products" class="btn btn-danger btn-block" style="margin-top: 12px;">🔙 رجوع</a>
    </div>
    '''
    return render_page(content, title=p['name'])


@app.route('/buy/<int:pid>', methods=['POST'])
@login_required
def buy(pid):
    p = get_product(pid)
    if not p or p['status'] != 'available' or p['stock'] <= 0:
        flash("❌ المنتج غير متوفر", "error")
        return redirect(url_for('products'))
    
    uid = session['user_id']
    user = get_user(uid)
    
    if user['balance_usd'] < p['price_usd']:
        flash(f"❌ رصيدك غير كافٍ", "error")
        return redirect(url_for('product_detail', pid=pid))
    
    if not deduct_balance_usd(uid, p['price_usd']):
        flash("❌ فشل الخصم", "error")
        return redirect(url_for('product_detail', pid=pid))
    
    method = "دولار"
    
    if p['sale_type'] == 'manual':
        add_sale(pid, uid, p['price_usd'], 0, method, "pending")
        
        # إشعار الأدمن
        for admin_id in ADMIN_IDS:
            try:
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": admin_id,
                        "text": f"🤝 <b>طلب بيع يدوي (موقع)!</b>\n\n"
                                f"📦 {p['name']}\n"
                                f"👤 {user['first_name']}\n"
                                f"🆔 <code>{uid}</code>\n"
                                f"💰 {p['price_usd']}$",
                        "parse_mode": "HTML"
                    },
                    timeout=5
                )
            except:
                pass
        
        flash("⏳ تم إرسال طلبك للمراجعة", "success")
        return redirect(url_for('orders'))
    
    # بيع تلقائي
    new_stock = p['stock'] - 1
    if new_stock <= 0:
        mark_sold(pid, uid)
    else:
        update_stock(pid, new_stock)
    
    add_sale(pid, uid, p['price_usd'], 0, method, "completed")
    
    with db() as conn:
        conn.execute(
            "UPDATE users SET orders_count=orders_count+1, total_spent=total_spent+? WHERE user_id=?",
            (p['price_usd'], uid)
        )
        conn.commit()
    
    # إشعار المشتري في تيليجرام
    try:
        text = (f"✅ <b>تم الشراء من الموقع!</b>\n\n"
                f"📦 {p['name']}\n"
                f"🔑 <code>{p['code']}</code>\n"
                f"💰 {p['price_usd']}$")
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": uid, "text": text, "parse_mode": "HTML"},
            timeout=5
        )
    except:
        pass
    
    content = f'''
    <div class="card" style="text-align: center; border-color: #10b981;">
        <p style="font-size: 80px;">✅</p>
        <h2 style="color: #10b981;">تم الشراء بنجاح!</h2>
        <div style="background: #0a0e1a; padding: 20px; border-radius: 12px; margin: 20px 0;">
            <p>📦 {p['name']}</p>
            <p style="color: #94a3b8; margin-top: 12px;">🔑 الكود:</p>
            <code style="color: #10b981; font-size: 18px; font-weight: 700; word-break: break-all;">{p['code']}</code>
            <p style="margin-top: 12px;">💰 <b style="color: #10b981;">{p['price_usd']}$</b></p>
        </div>
        <div class="grid">
            <a href="/products" class="btn btn-primary">🛍️ منتجات أخرى</a>
            <a href="/" class="btn btn-success">🏠 الرئيسية</a>
        </div>
    </div>
    '''
    return render_page(content, title="تم الشراء")


@app.route('/balance')
@login_required
def balance():
    user = get_user(session['user_id'])
    content = f'''
    <div class="card" style="text-align: center; border-color: #10b981;">
        <p style="font-size: 60px;">💰</p>
        <h2 style="color: #10b981;">رصيدك</h2>
        <p style="font-size: 48px; font-weight: 900; color: #10b981; margin: 20px 0;">
            {user['balance_usd']:.2f}$
        </p>
    </div>
    <div class="card">
        <div class="stats">
            <div class="stat"><div class="num">{user['orders_count']}</div><div class="label">طلبات</div></div>
            <div class="stat"><div class="num">{user['total_spent']:.2f}$</div><div class="label">مشتريات</div></div>
            <div class="stat"><div class="num">{user['balance_stars']}</div><div class="label">نجوم</div></div>
        </div>
    </div>
    <div class="grid">
        <a href="/charge" class="btn btn-success">💳 شحن</a>
        <a href="/" class="btn btn-primary">🏠 الرئيسية</a>
    </div>
    '''
    return render_page(content, title="رصيدي")


@app.route('/charge')
@login_required
def charge():
    prices = get_charge_prices()
    rate = get_exchange_rate()
    bot_username = get_setting('bot_username', 'sd_5g_bot')
    
    if not prices:
        content = '<div class="card" style="text-align: center;"><p>❌ لا توجد أسعار</p></div>'
        return render_page(content, title="شحن")
    
    html = ""
    for p in prices:
        html += f'<a href="https://t.me/{bot_username}" target="_blank" class="btn btn-success btn-block" style="margin-bottom: 12px;">💵 {p["amount_usd"]}$ = ⭐ {p["amount_stars"]}</a>'
    
    content = f'''
    <div class="card" style="text-align: center;">
        <h2 style="color: #3b82f6;">💳 شحن الرصيد</h2>
        <p style="color: #94a3b8; margin-top: 12px;">💱 1$ = {rate} ⭐</p>
    </div>
    <div class="card">
        <h3 style="margin-bottom: 16px;">اختر المبلغ:</h3>
        {html}
    </div>
    <a href="/" class="btn btn-danger btn-block">🔙 رجوع</a>
    '''
    return render_page(content, title="شحن")


@app.route('/orders')
@login_required
def orders():
    items = get_user_sales(session['user_id'])
    if not items:
        content = '<div class="card" style="text-align: center;"><p>📭 لا توجد طلبات</p></div>'
        return render_page(content, title="طلباتي")
    
    html = ""
    for s in items:
        if s['status'] == 'completed':
            st, c = "✅ مكتمل", "#10b981"
        elif s['status'] == 'pending':
            st, c = "⏳ قيد المراجعة", "#f59e0b"
        else:
            st, c = "❌ مرفوض", "#ef4444"
        
        html += f'''
        <div class="card">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <p>🆔 #{s['id']}</p>
                    <p style="font-size: 20px; font-weight: 700; color: #10b981;">{s['amount_usd']}$</p>
                    <p style="font-size: 12px; color: #64748b;">🕒 {s['sold_at']}</p>
                </div>
                <span style="color: {c};">{st}</span>
            </div>
        </div>
        '''
    
    content = f'<div class="card"><h2>📋 طلباتي ({len(items)})</h2></div>{html}<a href="/" class="btn btn-primary btn-block">🔙 رجوع</a>'
    return render_page(content, title="طلباتي")


@app.route('/share')
@login_required
def share():
    uid = session['user_id']
    if not is_referral_enabled():
        flash("❌ الميزة معطلة", "error")
        return redirect(url_for('index'))
    
    stats = get_user_referrals(uid)
    daily = get_daily_referrals(uid)
    limit = get_referral_daily_limit()
    reward = get_referral_reward()
    bot_username = get_setting('bot_username', 'sd_5g_bot')
    ref_link = f"https://t.me/{bot_username}?start=ref_{uid}"
    
    content = f'''
    <div class="card" style="text-align: center;">
        <p style="font-size: 60px;">🎁</p>
        <h2 style="color: #10b981;">شارك واربح</h2>
        <p style="color: #94a3b8;">{reward:.2f}$ عن كل صديق</p>
    </div>
    <div class="card">
        <div class="stats">
            <div class="stat"><div class="num">{stats['count']}</div><div class="label">إحالاتك</div></div>
            <div class="stat"><div class="num">{stats['total_earned']:.2f}$</div><div class="label">أرباحك</div></div>
            <div class="stat"><div class="num">{daily}/{limit}</div><div class="label">اليوم</div></div>
        </div>
    </div>
    <div class="card">
        <h3>🔗 رابطك:</h3>
        <div style="background: #0a0e1a; padding: 16px; border-radius: 12px; margin: 12px 0;">
            <code style="color: #3b82f6; word-break: break-all;">{ref_link}</code>
        </div>
        <a href="https://t.me/share/url?url={ref_link}&text=انضم!" target="_blank" class="btn btn-success btn-block">
            📤 مشاركة
        </a>
    </div>
    <a href="/" class="btn btn-danger btn-block">🔙 رجوع</a>
    '''
    return render_page(content, title="شارك واربح")


@app.route('/help')
@login_required
def help_page():
    content = f'''
    <div class="card" style="text-align: center;">
        <p style="font-size: 60px;">❓</p>
        <h2 style="color: #3b82f6;">المساعدة</h2>
    </div>
    <div class="card">
        <h3>📖 الأوامر</h3>
        <p><code>/start</code> - القائمة الرئيسية</p>
        <p><code>/id</code> - عرض آيديك</p>
        <p><code>/help</code> - المساعدة</p>
    </div>
    <div class="card">
        <h3>📞 تواصل</h3>
        <div class="grid">
            <a href="https://t.me/{DEVELOPER_USERNAME}" class="btn btn-primary" target="_blank">👨‍💻 المطور</a>
            <a href="https://t.me/E_E_72" class="btn btn-danger" target="_blank">👑 الأدمن</a>
        </div>
    </div>
    <a href="/" class="btn btn-danger btn-block">🔙 رجوع</a>
    '''
    return render_page(content, title="المساعدة")


# ===== لوحة الأدمن =====
@app.route('/admin')
@admin_required
def admin_dashboard():
    pc = get_product_count()
    users_count = count_users()
    rate = get_exchange_rate()
    
    with db() as conn:
        sales_count = conn.execute("SELECT COUNT(*) c FROM sales").fetchone()["c"]
        sales_sum = conn.execute("SELECT COALESCE(SUM(amount_usd),0) s FROM sales WHERE status='completed'").fetchone()["s"]
    
    content = f'''
    <div class="card" style="border-color: #f59e0b;">
        <h2 style="color: #f59e0b;">⚙️ لوحة التحكم</h2>
    </div>
    <div class="card">
        <div class="stats">
            <div class="stat"><div class="num">{pc['available']}</div><div class="label">منتج</div></div>
            <div class="stat"><div class="num">{users_count}</div><div class="label">مستخدم</div></div>
            <div class="stat"><div class="num">{sales_count}</div><div class="label">بيع</div></div>
            <div class="stat"><div class="num">{sales_sum:.2f}$</div><div class="label">المبيعات</div></div>
        </div>
    </div>
    <div class="card">
        <div class="grid">
            <a href="/admin/products" class="btn btn-primary">📦 المنتجات</a>
            <a href="/admin/users" class="btn btn-success">👥 المستخدمين</a>
            <a href="/admin/sales" class="btn btn-primary">📋 المبيعات</a>
            <a href="/admin/charge_prices" class="btn btn-success">💲 أسعار الشحن</a>
            <a href="/admin/settings" class="btn btn-warning">⚙️ الإعدادات</a>
        </div>
    </div>
    <a href="/" class="btn btn-danger btn-block">🔙 رجوع</a>
    '''
    return render_page(content, title="لوحة التحكم")


@app.route('/admin/products')
@admin_required
def admin_products():
    products = get_all_products()
    
    html = ""
    for p in products:
        html += f'''
        <div class="card">
            <p style="color: #3b82f6; font-weight: 700;">🆔 {p['id']} - {p['name']}</p>
            <p style="color: #10b981;">💰 {p['price_usd']}$</p>
            <p style="color: #94a3b8; font-size: 12px;">📦 {p['stock']} | {p['sale_type']}</p>
            <form method="POST" action="/admin/products/delete/{p['id']}" style="margin-top: 8px;" onsubmit="return confirm('حذف؟')">
                <button type="submit" class="btn btn-danger" style="padding: 8px 14px; font-size: 12px;">🗑️ حذف</button>
            </form>
        </div>
        '''
    
    content = f'''
    <div class="card"><h2>📦 المنتجات ({len(products)})</h2></div>
    <div class="card" style="border-color: #10b981;">
        <h3>➕ إضافة منتج</h3>
        <form method="POST" action="/admin/products/add" style="margin-top: 12px;">
            <input type="text" name="name" class="input" placeholder="الاسم" required>
            <textarea name="description" class="input" placeholder="الوصف" rows="2"></textarea>
            <input type="number" step="0.01" name="price_usd" class="input" placeholder="السعر بالدولار" required>
            <input type="number" name="stock" class="input" value="1" required>
            <input type="text" name="category" class="input" value="عام">
            <select name="sale_type" class="input">
                <option value="auto">⚡ تلقائي</option>
                <option value="manual">🤝 يدوي</option>
            </select>
            <input type="text" name="code" class="input" placeholder="الكود">
            <input type="text" name="file_id" class="input" placeholder="file_id (اختياري)">
            <button type="submit" class="btn btn-success btn-block">➕ إضافة</button>
        </form>
    </div>
    {html}
    <a href="/admin" class="btn btn-danger btn-block">🔙 رجوع</a>
    '''
    return render_page(content, title="إدارة المنتجات")


@app.route('/admin/products/add', methods=['POST'])
@admin_required
def admin_add_product_route():
    try:
        add_product(
            name=request.form.get('name', '').strip(),
            description=request.form.get('description', '').strip(),
            price_usd=float(request.form.get('price_usd', 0)),
            category=request.form.get('category', 'عام'),
            code=request.form.get('code', '').strip(),
            stock=int(request.form.get('stock', 1)),
            sale_type=request.form.get('sale_type', 'auto'),
            file_id=request.form.get('file_id') or None
        )
        flash("✅ تمت الإضافة", "success")
    except Exception as e:
        flash(f"❌ خطأ: {e}", "error")
    return redirect(url_for('admin_products'))


@app.route('/admin/products/delete/<int:pid>', methods=['POST'])
@admin_required
def admin_delete_product_route(pid):
    delete_product(pid)
    flash("✅ تم الحذف", "success")
    return redirect(url_for('admin_products'))


@app.route('/admin/users')
@admin_required
def admin_users():
    data = get_all_users()
    html = ""
    for u in data['users']:
        html += f'''
        <div class="card">
            <p style="color: #3b82f6;">🆔 {u['user_id']}</p>
            <p style="color: #94a3b8; font-size: 12px;">👤 {u['first_name'] or u['username'] or 'مستخدم'}</p>
            <p style="color: #10b981; font-weight: 700;">💰 {u['balance_usd']:.2f}$</p>
        </div>
        '''
    
    content = f'''
    <div class="card"><h2>👥 المستخدمين ({data['total']})</h2></div>
    <div class="card" style="border-color: #10b981;">
        <h3>💰 شحن رصيد</h3>
        <form method="POST" action="/admin/users/charge">
            <input type="text" name="user_id" class="input" placeholder="آيدي المستخدم" required>
            <input type="number" step="0.01" name="amount" class="input" placeholder="المبلغ" required>
            <button type="submit" class="btn btn-success btn-block">💰 شحن</button>
        </form>
    </div>
    {html}
    <a href="/admin" class="btn btn-danger btn-block">🔙 رجوع</a>
    '''
    return render_page(content, title="المستخدمين")


@app.route('/admin/users/charge', methods=['POST'])
@admin_required
def admin_charge_user_route():
    uid = request.form.get('user_id', '').strip()
    try:
        amount = float(request.form.get('amount', 0))
        if uid and amount > 0 and get_user(uid):
            add_balance_usd(uid, amount)
            flash(f"✅ تم إضافة {amount}$ لـ {uid}", "success")
        else:
            flash("❌ بيانات غير صحيحة", "error")
    except:
        flash("❌ خطأ", "error")
    return redirect(url_for('admin_users'))


@app.route('/admin/sales')
@admin_required
def admin_sales():
    sales = get_all_sales()
    html = ""
    for s in sales:
        st = "✅" if s['status'] == 'completed' else "⏳" if s['status'] == 'pending' else "❌"
        html += f'''
        <div class="card">
            <p>🆔 #{s['id']} {st}</p>
            <p style="color: #94a3b8; font-size: 12px;">👤 {s['buyer_id']}</p>
            <p style="color: #10b981;">💰 {s['amount_usd']}$</p>
            <p style="font-size: 11px; color: #64748b;">{s['sold_at']}</p>
        </div>
        '''
    content = f'<div class="card"><h2>📋 المبيعات ({len(sales)})</h2></div>{html}<a href="/admin" class="btn btn-danger btn-block">🔙 رجوع</a>'
    return render_page(content, title="المبيعات")


@app.route('/admin/charge_prices')
@admin_required
def admin_charge_prices():
    prices = get_charge_prices()
    html = ""
    for p in prices:
        html += f'''
        <div class="card">
            <p style="color: #10b981; font-weight: 700;">💵 {p['amount_usd']}$ = ⭐ {p['amount_stars']}</p>
            <form method="POST" action="/admin/charge_prices/delete/{p['id']}" style="margin-top: 8px;" onsubmit="return confirm('حذف؟')">
                <button type="submit" class="btn btn-danger" style="padding: 8px 14px;">🗑️</button>
            </form>
        </div>
        '''
    
    content = f'''
    <div class="card"><h2>💲 أسعار الشحن</h2></div>
    <div class="card" style="border-color: #10b981;">
        <h3>➕ إضافة</h3>
        <form method="POST" action="/admin/charge_prices/add">
            <input type="number" step="0.01" name="amount_usd" class="input" placeholder="الدولار" required>
            <input type="number" name="amount_stars" class="input" placeholder="النجوم" required>
            <button type="submit" class="btn btn-success btn-block">➕ إضافة</button>
        </form>
    </div>
    {html}
    <a href="/admin" class="btn btn-danger btn-block">🔙 رجوع</a>
    '''
    return render_page(content, title="أسعار الشحن")


@app.route('/admin/charge_prices/add', methods=['POST'])
@admin_required
def admin_add_charge_price_route():
    try:
        add_charge_price(float(request.form.get('amount_usd', 0)), int(request.form.get('amount_stars', 0)))
        flash("✅ تمت الإضافة", "success")
    except:
        flash("❌ خطأ", "error")
    return redirect(url_for('admin_charge_prices'))


@app.route('/admin/charge_prices/delete/<int:pid>', methods=['POST'])
@admin_required
def admin_delete_charge_price_route(pid):
    delete_charge_price(pid)
    flash("✅ تم الحذف", "success")
    return redirect(url_for('admin_charge_prices'))


@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    if request.method == 'POST':
        for key in ['store_name', 'exchange_rate', 'referral_reward',
                    'referral_daily_limit', 'referral_enabled', 'bot_username']:
            val = request.form.get(key)
            if val is not None:
                set_setting(key, val)
        flash("✅ تم الحفظ", "success")
        return redirect(url_for('admin_settings'))
    
    content = f'''
    <div class="card"><h2>⚙️ الإعدادات</h2></div>
    <form method="POST">
        <div class="card">
            <h3>🏪 المتجر</h3>
            <input type="text" name="store_name" class="input" value="{get_setting('store_name', '')}">
            <input type="text" name="bot_username" class="input" value="{get_setting('bot_username', '')}">
            <input type="number" name="exchange_rate" class="input" value="{get_setting('exchange_rate', '50')}">
        </div>
        <div class="card">
            <h3>🎁 الإحالات</h3>
            <input type="number" step="0.01" name="referral_reward" class="input" value="{get_setting('referral_reward', '0.05')}">
            <input type="number" name="referral_daily_limit" class="input" value="{get_setting('referral_daily_limit', '10')}">
            <select name="referral_enabled" class="input">
                <option value="1" {'selected' if get_setting('referral_enabled') == '1' else ''}>✅ مفعلة</option>
                <option value="0" {'selected' if get_setting('referral_enabled') == '0' else ''}>❌ معطلة</option>
            </select>
        </div>
        <button type="submit" class="btn btn-success btn-block">💾 حفظ</button>
    </form>
    <a href="/admin" class="btn btn-danger btn-block" style="margin-top: 12px;">🔙 رجوع</a>
    '''
    return render_page(content, title="الإعدادات")


@app.route('/api/me')
def api_me():
    if 'user_id' not in session:
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "user": get_user(session['user_id'])})


# =========================================================
# ========== التشغيل الرئيسي ==============================
# =========================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 بدء النظام الكامل")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 المنفذ: {PORT}")
    print(f"🌐 URL: {WEBAPP_URL}")
    print("=" * 60)
    
    # 1. قاعدة البيانات
    print("\n📌 [1/3] تهيئة قاعدة البيانات...")
    init_db()
    print("✅ قاعدة البيانات جاهزة")
    
    # 2. البوت
    print("\n📌 [2/3] تشغيل البوت...")
    bot_thread = threading.Thread(target=run_bot, name="BotThread", daemon=True)
    bot_thread.start()
    
    # 3. الموقع
    print("\n📌 [3/3] تشغيل الموقع...")
    print(f"🌐 الموقع على http://0.0.0.0:{PORT}")
    print("=" * 60)
    print("\n✅ كل شيء شغال!")
    print("⚠️ اضغط Ctrl+C للإيقاف\n")
    
    try:
        app.run(
            host="0.0.0.0",
            port=PORT,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n🛑 إيقاف...")