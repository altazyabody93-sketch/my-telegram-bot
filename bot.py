import telebot
from telebot import types
import sqlite3
import json
import os
import time
import logging
import re
from datetime import datetime
from telebot.types import BotCommand
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


# ========== الإعدادات ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8971686005:AAEsGXoj4ky9FfOp3YPjNFMrDeC3wSfhhUk")
ADMIN_IDS = ["7325566792", "7602226699", "E_E_72"]
DEVELOPER_USERNAME = "MO_5_H"
DB_PATH = "store.db"
CHANNEL_ID = "@your_channel"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

def get_user_mention(user_id, first_name):
    return f'<a href="tg://user?id={user_id}">{first_name}</a>'

def get_username(user_id, username):
    if username:
        return f"@{username}"
    else:
        return f'<a href="tg://user?id={user_id}">لا يوجد يوزر</a>'

user_data = {}
product_data = {}

# ========== دوال الإعدادات العامة ==========
def get_setting(key, default_value=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default_value

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_exchange_rate():
    return int(get_setting('exchange_rate', '50'))

def set_exchange_rate(rate):
    set_setting('exchange_rate', rate)

def get_channel_id():
    return get_setting('channel_id', CHANNEL_ID)
    
# ========== قاعدة البيانات ==========
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        price_usd REAL,
        price_stars INTEGER,
        category TEXT,
        stock INTEGER DEFAULT 1,
        code TEXT,
        status TEXT DEFAULT 'available',
        sale_type TEXT DEFAULT 'auto',
        created_at TEXT,
        sold_at TEXT,
        buyer_id TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        username TEXT,
        first_name TEXT,
        balance_usd REAL DEFAULT 0,
        balance_stars INTEGER DEFAULT 0,
        total_spent REAL DEFAULT 0,
        orders_count INTEGER DEFAULT 0,
        created_at TEXT,
        last_active TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        buyer_id TEXT,
        amount_usd REAL,
        amount_stars INTEGER,
        payment_method TEXT,
        status TEXT DEFAULT 'pending',
        sold_at TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        added_at TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS buttons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        button_key TEXT UNIQUE,
        label TEXT,
        style TEXT DEFAULT 'default',
        row INTEGER DEFAULT 1,
        col INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS charge_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount_usd REAL,
        amount_stars INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id TEXT,
        channel_name TEXT,
        is_activation INTEGER DEFAULT 1,
        created_at TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS star_charges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        username TEXT,
        amount_usd REAL,
        amount_stars INTEGER,
        charged_at TEXT
    )''')
    
    # ✅ جدول الإحالات (شارك واربح) - جديد
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id TEXT,
        referred_id TEXT UNIQUE,
        amount REAL,
        created_at TEXT
    )''')
    
    # ✅ إضافة عمود file_id لجدول المنتجات
    try:
        c.execute("ALTER TABLE products ADD COLUMN file_id TEXT")
    except:
        pass
    
    # ✅ الإعدادات العامة
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("exchange_rate", "50"))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("store_name", "🛍️ متجر الأرقام"))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("store_status", "open"))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("channel_id", CHANNEL_ID))
    
    # ✅ إعدادات الإحالة (شارك واربح) - جديدة
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("referral_reward", "0.05"))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("referral_enabled", "1"))
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ("referral_daily_limit", "10"))
    
    # ✅ الأزرار الافتراضية
    default_buttons = [
        ("show_products", "🛍️ المنتجات", "primary", 1, 1),
        ("my_balance", "💰 رصيدي", "success", 1, 2),
        ("charge_balance", "💳 شحن الرصيد", "danger", 2, 1),
        ("my_orders", "📋 طلباتي", "primary", 2, 2),
        ("support", "📞 تواصل مع الدعم", "danger", 3, 1),
    ]
    for key, label, style, row, col in default_buttons:
        c.execute("INSERT OR IGNORE INTO buttons (button_key, label, style, row, col) VALUES (?, ?, ?, ?, ?)",
                  (key, label, style, row, col))
    
    # ✅ أسعار الشحن الافتراضية
    default_prices = [
        (1, 50), (2, 100), (5, 250), (10, 500), (20, 1000), (50, 2500)
    ]
    for usd, stars in default_prices:
        c.execute("INSERT OR IGNORE INTO charge_prices (amount_usd, amount_stars, created_at) VALUES (?, ?, ?)",
                 (usd, stars, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    # ✅ الأدمن
    for admin_id in ADMIN_IDS:
        c.execute("INSERT OR IGNORE INTO admins (user_id, added_at) VALUES (?, ?)", 
                 (admin_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()
    conn.close()
    
 # ========== دوال الأزرار ==========
def get_all_buttons():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT button_key, label, style, row, col, is_active FROM buttons ORDER BY row ASC, col ASC")
    rows = c.fetchall()
    conn.close()
    return [{'key': r[0], 'label': r[1], 'style': r[2], 'row': r[3], 'col': r[4], 'is_active': r[5]} for r in rows]

def update_button(key, label=None, style=None, row=None, col=None, is_active=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if label:
        c.execute("UPDATE buttons SET label=? WHERE button_key=?", (label, key))
    if style:
        c.execute("UPDATE buttons SET style=? WHERE button_key=?", (style, key))
    if row is not None:
        c.execute("UPDATE buttons SET row=? WHERE button_key=?", (row, key))
    if col is not None:
        c.execute("UPDATE buttons SET col=? WHERE button_key=?", (col, key))
    if is_active is not None:
        c.execute("UPDATE buttons SET is_active=? WHERE button_key=?", (is_active, key))
    conn.commit()
    conn.close()

# ========== دوال القنوات ==========
def add_channel(channel_id, channel_name=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not channel_name:
            channel_name = f"قناة {channel_id}"
        c.execute("INSERT INTO channels (channel_id, channel_name, created_at) VALUES (?, ?, ?)",
                  (channel_id, channel_name, now))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_activation_channels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_id, channel_name FROM channels WHERE is_activation = 1")
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1]} for r in rows]

def set_activation_channel(channel_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE channels SET is_activation = 0")
    c.execute("UPDATE channels SET is_activation = 1 WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()

def get_activation_channel():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel_id FROM channels WHERE is_activation = 1 LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row[0] if row else None
    
# ========== دوال إحصائيات شحن النجوم ==========
def add_star_charge(user_id, username, amount_usd, amount_stars):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO star_charges (user_id, username, amount_usd, amount_stars, charged_at) VALUES (?, ?, ?, ?, ?)",
              (user_id, username, amount_usd, amount_stars, now))
    conn.commit()
    conn.close()

def get_star_charge_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(DISTINCT user_id) FROM star_charges")
    unique_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM star_charges")
    total_charges = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(amount_stars), 0) FROM star_charges")
    total_stars = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(amount_usd), 0) FROM star_charges")
    total_usd = c.fetchone()[0]
    c.execute("SELECT user_id, username, amount_usd, amount_stars, charged_at FROM star_charges ORDER BY id DESC LIMIT 10")
    recent = c.fetchall()
    conn.close()
    return {
        'unique_users': unique_users,
        'total_charges': total_charges,
        'total_stars': total_stars,
        'total_usd': total_usd,
        'recent': recent
    }

# ========== دوال الإحالة (شارك واربح) ==========
def get_referral_reward():
    return float(get_setting('referral_reward', '0.05'))

def set_referral_reward(amount):
    set_setting('referral_reward', str(amount))

def is_referral_enabled():
    return get_setting('referral_enabled', '1') == '1'

def get_referral_daily_limit():
    return int(get_setting('referral_daily_limit', '10'))

def add_referral(referrer_id, referred_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO referrals (referrer_id, referred_id, amount, created_at) VALUES (?, ?, ?, ?)",
                  (referrer_id, referred_id, amount, now))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_user_referrals(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM referrals WHERE referrer_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return {'count': row[0], 'total_earned': row[1]}

def get_daily_referrals(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=? AND DATE(created_at)=?", (user_id, today))
    count = c.fetchone()[0]
    conn.close()
    return count

def get_referral_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(DISTINCT referrer_id) FROM referrals")
    unique_referrers = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM referrals")
    total_referrals = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM referrals")
    total_paid = c.fetchone()[0]
    c.execute("SELECT referrer_id, referred_id, amount, created_at FROM referrals ORDER BY id DESC LIMIT 10")
    recent = c.fetchall()
    conn.close()
    return {
        'unique_referrers': unique_referrers,
        'total_referrals': total_referrals,
        'total_paid': total_paid,
        'recent': recent
    }


# ========== دوال تحويل العملات ==========
def usd_to_stars(usd_amount):
    rate = get_exchange_rate()
    return int(usd_amount * rate)

# ========== دوال المستخدمين ==========
def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'user_id': row[1], 'username': row[2], 'first_name': row[3], 
                'balance_usd': row[4], 'balance_stars': row[5], 'total_spent': row[6], 'orders_count': row[7]}
    return None

def create_user(user_id, username="", first_name=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO users (user_id, username, first_name, created_at, last_active) VALUES (?, ?, ?, ?, ?)",
                  (user_id, username, first_name, now, now))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def add_balance_usd(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET balance_usd = balance_usd + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def add_balance_stars(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET balance_stars = balance_stars + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def deduct_balance_usd(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET balance_usd = balance_usd - ? WHERE user_id=? AND balance_usd >= ?", (amount, user_id, amount))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    c.execute("SELECT user_id, username, first_name, balance_usd, balance_stars, orders_count FROM users ORDER BY id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return {'total': total, 'users': rows}

def add_admin(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO admins (user_id, added_at) VALUES (?, ?)", (user_id, now))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_all_admins():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM admins")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]
    
# ========== دوال المنتجات ==========
def add_product(name="", description="", price_usd=0, price_stars=0, category="", code="", stock=1, sale_type="auto", file_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not name:
            name = f"منتج {datetime.now().strftime('%H:%M')}"
        if not description:
            description = "لا يوجد وصف"
        if not category:
            category = "عام"
        if not code:
            code = "غير محدد"
        
        c.execute("INSERT INTO products (name, description, price_usd, price_stars, category, stock, code, sale_type, file_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (name, description, price_usd, price_stars, category, stock, code, sale_type, file_id, now))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_available_products():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, description, price_usd, price_stars, category, stock, code, sale_type, file_id FROM products WHERE status='available' AND stock > 0 ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'description': r[2], 'price_usd': r[3], 'price_stars': r[4], 'category': r[5], 'stock': r[6], 'code': r[7], 'sale_type': r[8], 'file_id': r[9] if len(r) > 9 else None} for r in rows]

def get_product(product_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (product_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'name': row[1], 'description': row[2], 'price_usd': row[3], 'price_stars': row[4], 
                'category': row[5], 'stock': row[6], 'code': row[7], 'status': row[8], 'sale_type': row[9], 
                'created_at': row[10] if len(row) > 10 else None,
                'sold_at': row[11] if len(row) > 11 else None,
                'buyer_id': row[12] if len(row) > 12 else None,
                'file_id': row[13] if len(row) > 13 else None}
    return None

def mark_sold(product_id, buyer_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("UPDATE products SET status='sold', stock=0, sold_at=?, buyer_id=? WHERE id=?", (now, buyer_id, product_id))
    conn.commit()
    conn.close()

def update_stock(product_id, new_stock):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE products SET stock=? WHERE id=?", (new_stock, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()

def get_product_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM products WHERE status='available' AND stock > 0")
    available = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM products")
    total = c.fetchone()[0]
    conn.close()
    return {'available': available, 'total': total}

def get_recent_sales(limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM sales ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'product_id': r[1], 'buyer_id': r[2], 'amount_usd': r[3], 'amount_stars': r[4], 'payment_method': r[5], 'status': r[6], 'sold_at': r[7]} for r in rows]

def add_sale(product_id, buyer_id, amount_usd, amount_stars, payment_method, status="completed"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO sales (product_id, buyer_id, amount_usd, amount_stars, payment_method, status, sold_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (product_id, buyer_id, amount_usd, amount_stars, payment_method, status, now))
    conn.commit()
    conn.close()

def update_sale_status(sale_id, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE sales SET status=? WHERE id=?", (status, sale_id))
    conn.commit()
    conn.close()

# ========== دوال أسعار الشحن ==========
def get_charge_prices():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, amount_usd, amount_stars FROM charge_prices WHERE is_active = 1 ORDER BY amount_usd ASC")
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'amount_usd': r[1], 'amount_stars': r[2]} for r in rows]

def add_charge_price(amount_usd, amount_stars):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO charge_prices (amount_usd, amount_stars, created_at) VALUES (?, ?, ?)",
                  (amount_usd, amount_stars, now))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def delete_charge_price(price_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE charge_prices SET is_active = 0 WHERE id = ?", (price_id,))
    conn.commit()
    conn.close()

def update_charge_price(price_id, amount_usd, amount_stars):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE charge_prices SET amount_usd = ?, amount_stars = ? WHERE id = ?", (amount_usd, amount_stars, price_id))
    conn.commit()
    conn.close()

def get_charge_price_by_id(price_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, amount_usd, amount_stars FROM charge_prices WHERE id = ? AND is_active = 1", (price_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'id': row[0], 'amount_usd': row[1], 'amount_stars': row[2]}
    return None
    
# ========== بناء الأزرار الرئيسية ==========
def main_menu(is_admin=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT button_key, label, style, row, col FROM buttons WHERE is_active = 1 ORDER BY row ASC, col ASC")
    rows = c.fetchall()
    conn.close()
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    row_dict = {}
    
    for r in rows:
        key, label, style, row, col = r
        if row not in row_dict:
            row_dict[row] = []
        row_dict[row].append((key, label, style, col))
    
    for row_num in sorted(row_dict.keys()):
        btn_row = sorted(row_dict[row_num], key=lambda x: x[3])
        btn_list = []
        for key, label, style, col in btn_row:
            btn_list.append(types.InlineKeyboardButton(label, callback_data=key, style=style))
        markup.row(*btn_list)
    
    
    # زر قناة التفعيل
    activation_channel = get_activation_channel()
    if activation_channel:
        channel_name = activation_channel.replace('@', '')
        markup.row(types.InlineKeyboardButton("📢 قناة التفعيل والمشتريات", url=f"https://t.me/{channel_name}", style="primary"))
    
    if is_admin:
        markup.row(types.InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel", style="danger"))
    
    return markup

def admin_panel_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # 1. زر إضافة منتج (أخضر - لوحده)
    markup.add(
        types.InlineKeyboardButton("➕ إضافة منتج", callback_data="admin_add_product", style="success")
    )
    
    # 2. الصفوف المتوسطة (أزرق)
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
    
    # 3. الصفوف الأخيرة (أحمر)
    markup.add(
        types.InlineKeyboardButton("💲 أسعار الشحن", callback_data="admin_charge_prices", style="danger"),
        types.InlineKeyboardButton("👑 إدارة المطورين", callback_data="admin_developers", style="danger"),
    )
    
    markup.add(
        types.InlineKeyboardButton("📢 إدارة القنوات", callback_data="admin_channels", style="danger"),
        types.InlineKeyboardButton("⭐ إحصائيات النجوم", callback_data="admin_star_stats", style="danger"),
    )
    
    # ✅ زر "🎁 إدارة الإحالات" (جديد - أخضر)
    markup.add(
        types.InlineKeyboardButton("🎁 إدارة الإحالات", callback_data="admin_referral_panel", style="success")
    )
    
    # 4. زر إضافة قناة (أخضر - لوحده)
    markup.add(
        types.InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel", style="success")
    )
    
    # 5. زر رجوع (أحمر - لوحده)
    markup.add(
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main", style="danger")
    )
    
    return markup

def back_admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🔙 رجوع للوحة التحكم", callback_data="admin_panel", style="danger"))
    return markup

# ========== شارك واربح ==========
@bot.callback_query_handler(func=lambda call: call.data == 'share_earn')
def share_earn(call):
    """عرض رابط الإحالة وإحصائيات المستخدم"""
    user_id = str(call.from_user.id)
    user = get_user(user_id)
    
    if not user:
        bot.answer_callback_query(call.id, "❌ حدث خطأ!")
        return
    
    if not is_referral_enabled():
        bot.answer_callback_query(call.id, "❌ الميزة معطلة حالياً!")
        return
    
    # ✅ رابط الإحالة
    bot_username = bot.get_me().username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    # ✅ إحصائيات المستخدم
    stats = get_user_referrals(user_id)
    daily = get_daily_referrals(user_id)
    daily_limit = get_referral_daily_limit()
    reward = get_referral_reward()
    
    text = f"""
🎁 **شارك واربح**

💡 **كيف يعمل؟**
1️⃣ انسخ رابطك الخاص
2️⃣ شاركه مع أصدقائك
3️⃣ كل صديق ينضم ← تكسب **{reward:.2f}$**
4️⃣ الأرباح تُضاف لرصيدك فوراً

━━━━━━━━━━━━━━━━━━━━

🔗 **رابطك الخاص:**
`{referral_link}`

━━━━━━━━━━━━━━━━━━━━

📊 **إحصائياتك:**
👥 **عدد الإحالات:** {stats['count']}
💰 **إجمالي الأرباح:** {stats['total_earned']:.2f}$
📅 **إحالات اليوم:** {daily}/{daily_limit}
🎯 **المكافأة/صديق:** {reward:.2f}$

━━━━━━━━━━━━━━━━━━━━

👇 **اضغط للنسخ والمشاركة:**
"""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📋 نسخ ومشاركة الرابط", url=f"https://t.me/share/url?url={referral_link}&text=انضم%20إلى%20البوت%20الرائع!", style="success")
    )
    markup.add(
        types.InlineKeyboardButton("📊 تفاصيل أكثر", callback_data="share_earn_details", style="primary")
    )
    markup.add(
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main", style="danger")
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'share_earn_details')
def share_earn_details(call):
    """عرض تفاصيل أكثر عن الإحالات"""
    user_id = str(call.from_user.id)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT referred_id, amount, created_at FROM referrals WHERE referrer_id=? ORDER BY id DESC LIMIT 10", (user_id,))
    recent = c.fetchall()
    conn.close()
    
    stats = get_user_referrals(user_id)
    reward = get_referral_reward()
    
    text = f"""
📊 **تفاصيل الإحالات**

💰 **إجمالي الأرباح:** {stats['total_earned']:.2f}$
👥 **عدد الإحالات:** {stats['count']}
🎯 **المكافأة:** {reward:.2f}$ / صديق

━━━━━━━━━━━━━━━━━━━━

📋 **آخر الإحالات:**
"""
    
    if not recent:
        text += "\n❌ لا توجد إحالات بعد.\n"
    else:
        for r in recent:
            text += f"\n🆔 `{r[0][:10]}...`\n"
            text += f"💰 {r[1]:.2f}$\n"
            text += f"🕒 {r[2]}\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔙 رجوع", callback_data="share_earn", style="danger")
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

# ========== لوحة تحكم الإحالات (أدمن) ==========
@bot.callback_query_handler(func=lambda call: call.data == 'admin_referral_panel')
def admin_referral_panel(call):
    """لوحة تحكم إدارة الإحالات"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    reward = get_referral_reward()
    enabled = "✅ مفعلة" if is_referral_enabled() else "❌ معطلة"
    daily_limit = get_referral_daily_limit()
    
    stats = get_referral_stats()
    
    text = f"""
🎁 **إدارة الإحالات (شارك واربح)**

━━━━━━━━━━━━━━━━━━━━

⚙️ **الإعدادات الحالية:**
💰 **المكافأة/صديق:** {reward:.2f}$
🔘 **الحالة:** {enabled}
📅 **الحد اليومي:** {daily_limit} صديق

━━━━━━━━━━━━━━━━━━━━

📊 **الإحصائيات:**
👥 **عدد المُحيلين:** {stats['unique_referrers']}
🔄 **عدد الإحالات:** {stats['total_referrals']}
💵 **إجمالي المدفوع:** {stats['total_paid']:.2f}$

━━━━━━━━━━━━━━━━━━━━
"""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💰 تغيير المكافأة", callback_data="admin_ref_set_reward", style="success")
    )
    markup.add(
        types.InlineKeyboardButton("📅 تغيير الحد اليومي", callback_data="admin_ref_set_limit", style="primary")
    )
    markup.add(
        types.InlineKeyboardButton("🔄 تفعيل/تعطيل الميزة", callback_data="admin_ref_toggle", style="danger")
    )
    markup.add(
        types.InlineKeyboardButton("📋 آخر الإحالات", callback_data="admin_ref_recent", style="primary")
    )
    markup.add(
        types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="danger")
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'admin_ref_set_reward')
def admin_ref_set_reward(call):
    """تعديل مبلغ المكافأة"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    reward = get_referral_reward()
    msg = bot.edit_message_text(
        f"💰 **تغيير مكافأة الإحالة**\n\n"
        f"المكافأة الحالية: **{reward:.2f}$**\n\n"
        f"أرسل المكافأة الجديدة (بالدولار):\n"
        f"مثال: `0.05` أو `0.10`",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, save_referral_reward_step)

def save_referral_reward_step(message):
    """حفظ المكافأة الجديدة"""
    try:
        amount = float(message.text.strip())
        if amount < 0:
            bot.send_message(message.chat.id, "❌ **المبلغ يجب أن يكون 0 أو أكبر!**", reply_markup=admin_panel_keyboard())
            return
        set_referral_reward(amount)
        bot.send_message(
            message.chat.id,
            f"✅ **تم تحديث المكافأة إلى:** {amount:.2f}$",
            reply_markup=admin_panel_keyboard()
        )
    except:
        bot.send_message(message.chat.id, "❌ **أدخل رقماً صحيحاً!**", reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == 'admin_ref_set_limit')
def admin_ref_set_limit(call):
    """تعديل الحد اليومي"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    current = get_referral_daily_limit()
    msg = bot.edit_message_text(
        f"📅 **تغيير الحد اليومي**\n\n"
        f"الحد الحالي: **{current}** إحالة/يوم\n\n"
        f"أرسل الحد الجديد (رقم):\n"
        f"مثال: `10` أو `20` أو `0` (بدون حد)",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, save_referral_limit_step)

def save_referral_limit_step(message):
    """حفظ الحد اليومي الجديد"""
    try:
        limit = int(message.text.strip())
        if limit < 0:
            bot.send_message(message.chat.id, "❌ **الحد يجب أن يكون 0 أو أكبر!**", reply_markup=admin_panel_keyboard())
            return
        set_setting('referral_daily_limit', str(limit))
        bot.send_message(
            message.chat.id,
            f"✅ **تم تحديث الحد اليومي إلى:** {limit}",
            reply_markup=admin_panel_keyboard()
        )
    except:
        bot.send_message(message.chat.id, "❌ **أدخل رقماً صحيحاً!**", reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == 'admin_ref_toggle')
def admin_ref_toggle(call):
    """تفعيل/تعطيل الميزة"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    new_state = "0" if is_referral_enabled() else "1"
    set_setting('referral_enabled', new_state)
    
    bot.answer_callback_query(call.id, "✅ تم التبديل!")
    admin_referral_panel(call)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_ref_recent')
def admin_ref_recent(call):
    """عرض آخر الإحالات للأدمن"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    stats = get_referral_stats()
    
    text = "📋 **آخر 10 إحالات:**\n\n"
    
    if not stats['recent']:
        text += "❌ لا توجد إحالات بعد."
    else:
        for r in stats['recent']:
            text += f"👤 **المُحيل:** `{r[0][:10]}...`\n"
            text += f"🆕 **الصديق:** `{r[1][:10]}...`\n"
            text += f"💰 **المكافأة:** {r[2]:.2f}$\n"
            text += f"🕒 {r[3]}\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_referral_panel", style="danger")
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )
# ========== أوامر إضافية ==========
@bot.message_handler(commands=['id'])
def send_id(message):
    user_id = message.from_user.id
    username = message.from_user.username or "لا يوجد"
    first_name = message.from_user.first_name or ""
    
    bot.reply_to(
        message,
        f"🆔 **معلوماتك:**\n\n"
        f"👤 الاسم: {first_name}\n"
        f"🆔 الآيدي: `{user_id}`\n"
        f"👤 اليوزر: @{username}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(
        message,
        f"❓ **المساعدة**\n\n"
        f"🔹 /start - القائمة الرئيسية\n"
        f"🔹 /id - عرض آيديك\n"
        f"🔹 /help - المساعدة\n\n"
        f"للتواصل: @{DEVELOPER_USERNAME}",
        parse_mode="Markdown"
    )


# ========== الأوامر ==========
@bot.message_handler(commands=['start', 'menu'])
def start_cmd(message):
    user_id = str(message.from_user.id)
    is_admin = user_id in ADMIN_IDS or user_id in get_all_admins()
    
    # ✅ معالجة الإحالة
    referrer_id = None
    if message.text and 'ref_' in message.text:
        try:
            referrer_id = message.text.split('ref_')[1].strip()
        except:
            referrer_id = None
    
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
                                f"🎉 **مبروك!**\n\n"
                                f"👤 صديق جديد انضم عبر رابطك:\n"
                                f"**{message.from_user.first_name}**\n\n"
                                f"💰 **ربحت:** {reward:.2f}$\n"
                                f"📊 **إحالاتك اليوم:** {daily + 1}/{daily_limit}\n"
                                f"💵 **رصيدك الجديد:** {get_user(referrer_id)['balance_usd']:.2f}$",
                                parse_mode="Markdown"
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

<i>✦ تــمــتــع بــالــتــســوق ✦</i>
"""
    
        # ✅ القائمة السفلية الثابتة (Reply Keyboard)
    reply_markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    reply_markup.add(
        KeyboardButton("💰 رصيدي", style="success"),
        KeyboardButton("📋 طلباتي", style="success")
    )
    reply_markup.add(
        KeyboardButton("💳 شحن رصيد", style="danger"),
        KeyboardButton("❓ مساعدة", style="danger")
    )
    reply_markup.add(
        KeyboardButton("🎁 شارك واربح", style="primary"),
        KeyboardButton("🔄 تشغيل البوت", style="primary")
    )
    
    bot.reply_to(message, text, parse_mode="HTML", reply_markup=reply_markup)
    
    # ✅ القائمة العلوية (Inline)
    bot.send_message(
        message.chat.id,
        "<u><b>🔹 الـــقـــائـــمـــة الـــرئـــيـــســـيـــة 🔹</b></u>",
        parse_mode="HTML",
        reply_markup=main_menu(is_admin)
    )

# ========== عرض المنتجات ==========
@bot.callback_query_handler(func=lambda call: call.data == 'show_products')
def show_products(call):
    products = get_available_products()
    is_admin = str(call.from_user.id) in ADMIN_IDS or str(call.from_user.id) in get_all_admins()
    
    if not products:
        bot.edit_message_text(
            "📭 لا توجد منتجات متاحة حالياً.", 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=main_menu(is_admin)
        )
        return
    
    text = "🛍️ **العروض التي يمكنك شرائها**\n\n"
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    # أزرار العناوين الثابتة
    title_availability = types.InlineKeyboardButton("📌 التوفر", callback_data="noop", style="primary")
    title_name = types.InlineKeyboardButton("📌 الاسم", callback_data="noop", style="success")
    title_price = types.InlineKeyboardButton("📌 السعر", callback_data="noop", style="danger")
    
    markup.row(title_availability, title_name, title_price)
    
    for p in products:
        if p['sale_type'] == 'manual':
            availability_text = "♾️ عند طلب"
        else:
            if p['stock'] > 0:
                availability_text = "✅ متوفر"
            else:
                availability_text = "❌ نفذ"
        
        availability_btn = types.InlineKeyboardButton(
            availability_text,
            callback_data=f"buy_{p['id']}",
            style="primary"
        )
        
        name_btn = types.InlineKeyboardButton(
            f"📦 {p['name']}",
            callback_data=f"product_info_{p['id']}",
            style="success"
        )
        
        price_btn = types.InlineKeyboardButton(
            f"{p['price_usd']}$",
            callback_data=f"product_info_{p['id']}",
            style="danger"
        )
        
        markup.row(availability_btn, name_btn, price_btn)
    
    markup.add(
        types.InlineKeyboardButton("🔍 بحث عن سلعة", callback_data="search_product", style="primary")
    )
    
    markup.add(
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main", style="danger")
    )
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

# ========== دالة منع الضغط على أزرار العناوين ==========
@bot.callback_query_handler(func=lambda call: call.data == 'noop')
def noop(call):
    bot.answer_callback_query(call.id, "هذا زر عنوان فقط!")

# ========== عرض تفاصيل المنتج ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('product_info_'))
def product_info(call):
    product_id = int(call.data.split('_')[2])
    product = get_product(product_id)
    
    if not product:
        bot.answer_callback_query(call.id, "❌ المنتج غير موجود!")
        return
    
    user = get_user(str(call.from_user.id))
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(f"💳 دولار ({product['price_usd']}$)", callback_data=f"pay_usd_{product_id}", style="success")
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="show_products", style="primary"))
    
    bot.edit_message_text(
        f"💳 **تأكيد الشراء**\n\n"
        f"📦 **المنتج:** {product['name']}\n"
        f"📝 {product['description']}\n"
        f"💰 {product['price_usd']}$\n"
        f"💵 رصيدك بالدولار: {user['balance_usd']:.2f}$\n\n"
        f"اختر طريقة الدفع:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )
    
# ========== الشراء والدفع ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def buy_callback(call):
    """عرض تفاصيل المنتج وتأكيد الشراء"""
    product_id = int(call.data.split('_')[1])
    product = get_product(product_id)
    
    if not product or product['status'] == 'sold' or product['stock'] <= 0:
        bot.answer_callback_query(call.id, "❌ هذا المنتج غير متوفر!")
        return
    
    user_id = str(call.from_user.id)
    user = get_user(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(f"💳 دولار ({product['price_usd']}$)", callback_data=f"pay_usd_{product_id}", style="success")
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="show_products", style="primary"))
    
    bot.edit_message_text(
        f"💳 **تأكيد الشراء**\n\n"
        f"📦 **المنتج:** {product['name']}\n"
        f"📝 {product['description']}\n"
        f"💰 {product['price_usd']}$\n"
        f"💵 رصيدك بالدولار: {user['balance_usd']:.2f}$\n\n"
        f"اختر طريقة الدفع:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_usd_'))
def pay_usd(call):
    """خصم المبلغ من رصيد المستخدم وإتمام الشراء"""
    product_id = int(call.data.split('_')[2])
    product = get_product(product_id)
    user_id = str(call.from_user.id)
    
    if not product or product['status'] == 'sold' or product['stock'] <= 0:
        bot.answer_callback_query(call.id, "❌ غير متوفر!")
        return
    
    user = get_user(user_id)
    if not user or user['balance_usd'] < product['price_usd']:
        bot.answer_callback_query(call.id, f"❌ رصيدك بالدولار غير كافٍ!\n💵 رصيدك: {user['balance_usd']:.2f}$")
        return
    
    if deduct_balance_usd(user_id, product['price_usd']):
        process_purchase(product_id, user_id, call, "دولار")

def process_purchase(product_id, user_id, call, method):
    """معالجة عملية الشراء (يدوي أو تلقائي) وإرسال المنتج للمشتري"""
    product = get_product(product_id)
    
    if product['sale_type'] == 'manual':
        # ===== بيع يدوي =====
        sale_id = add_sale(product_id, user_id, product['price_usd'], product['price_stars'], method, status="pending")
        
        bot.edit_message_text(
            f"⏳ **طلبك قيد المراجعة!**\n\n"
            f"📦 **المنتج:** {product['name']}\n"
            f"💰 **السعر:** {product['price_usd']}$\n"
            f"💳 **طريقة الدفع:** {method}\n\n"
            f"🔔 **سيتم تسليم المنتج بعد تأكيد صاحب البوت @{DEVELOPER_USERNAME}**\n"
            f"📢 **تابع قناة التفعيل لمتابعة طلبك**",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
        
        for admin_id in ADMIN_IDS:
            try:
                markup = types.InlineKeyboardMarkup(row_width=2)
                markup.add(
                    types.InlineKeyboardButton("✅ تأكيد البيع", callback_data=f"confirm_sale_{product_id}_{user_id}_{method}_{sale_id}", style="success"),
                    types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_sale_{product_id}_{user_id}_{method}_{sale_id}", style="danger")
                )
                bot.send_message(
                    admin_id,
                    f"🤝 <b>طلب بيع يدوي جديد!</b>\n\n"
                    f"📦 <b>المنتج:</b> {product['name']}\n"
                    f"👤 <b>المشتري:</b> {get_user_mention(user_id, call.from_user.first_name)}\n"
                    f"🆔 <b>المعرف:</b> {get_username(user_id, call.from_user.username)}\n"
                    f"💰 <b>السعر:</b> {product['price_usd']}$\n"
                    f"💳 <b>طريقة الدفع:</b> {method}\n\n"
                    f"اضغط تأكيد لتسليم المنتج:",
                    parse_mode="HTML",
                    reply_markup=markup
                )
            except:
                pass
        
        channel_id = get_activation_channel()
        if channel_id:
            try:
                bot.send_message(
                    channel_id,
                    f"<b>🛒✦┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄✦</b>\n"
                    f"<b>✨ حـــديـــث شـــراء ✨</b>\n"
                    f"<b>✦┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄✦</b>\n\n"
                    f"<b>👤 المشتري:</b> {get_user_mention(user_id, call.from_user.first_name)}\n"
                    f"<b>🆔 المعرف:</b> {get_username(user_id, call.from_user.username)}\n"
                    f"<b>📦 المنتج:</b> {product['name']}\n"
                    f"<b>💰 السعر:</b> {product['price_usd']}$\n"
                    f"<b>💳 طريقة الدفع:</b> {method}\n"
                    f"<b>🕒 الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"<b>✦┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄✦</b>",
                    parse_mode="HTML",
                    reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
                        types.InlineKeyboardButton("🔙 العودة إلى البوت", url=f"https://t.me/{bot.get_me().username}", style="primary")
                    )
                )
            except:
                pass
    else:
        # ===== بيع تلقائي =====
        new_stock = product['stock'] - 1
        if new_stock <= 0:
            mark_sold(product_id, user_id)
        else:
            update_stock(product_id, new_stock)
        
        add_sale(product_id, user_id, product['price_usd'], product['price_stars'], method, status="completed")
        
        # 1. رسالة النجاح للمشتري
        try:
            bot.edit_message_text(
                f"✅ **تم الشراء بنجاح!**\n\n"
                f"📦 **المنتج:** {product['name']}\n"
                f"🔑 **الكود:** `{product['code']}`\n"
                f"💵 {product['price_usd']}$\n"
                f"💳 طريقة الدفع: {method}",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="Markdown"
            )
        except:
            bot.send_message(
                call.message.chat.id,
                f"✅ **تم الشراء بنجاح!**\n\n"
                f"📦 **المنتج:** {product['name']}\n"
                f"🔑 **الكود:** `{product['code']}`\n"
                f"💵 {product['price_usd']}$\n"
                f"💳 طريقة الدفع: {method}",
                parse_mode="Markdown"
            )
        
        # 2. إرسال الملف للمشتري (إذا وجد) - مع تنظيف قوي لـ file_id
        if product.get('file_id'):
            import re
            file_id = str(product['file_id']).strip()
            file_id = re.sub(r'[^A-Za-z0-9_\-]', '', file_id)
            caption_text = f"📎 ملف المنتج: {product['name']}"
            
            print(f"DEBUG: file_id = {file_id}")
            print(f"DEBUG: chat_id = {call.from_user.id}")
            
            # محاولة إرسال كصورة أولاً
            try:
                bot.send_photo(
                    call.from_user.id,
                    file_id,
                    caption=caption_text
                )
                print(f"DEBUG: ✅ تم إرسال الملف كصورة")
            except Exception as e1:
                print(f"DEBUG: ❌ فشل كصورة: {e1}")
                # محاولة إرسال كمستند
                try:
                    bot.send_document(
                        call.from_user.id,
                        file_id,
                        caption=caption_text
                    )
                    print(f"DEBUG: ✅ تم إرسال الملف كمستند")
                except Exception as e2:
                    print(f"DEBUG: ❌ فشل كمستند: {e2}")
                    # محاولة إرسال كفيديو
                    try:
                        bot.send_video(
                            call.from_user.id,
                            file_id,
                            caption=caption_text
                        )
                        print(f"DEBUG: ✅ تم إرسال الملف كفيديو")
                    except Exception as e3:
                        print(f"DEBUG: ❌ فشل كفيديو: {e3}")
        
        # 3. إرسال للقناة
        channel_id = get_activation_channel()
        if channel_id:
            try:
                bot.send_message(
                    channel_id,
                    f"<b>🛒✦┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄✦</b>\n"
                    f"<b>✨ حـــديـــث شـــراء ✨</b>\n"
                    f"<b>✦┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄✦</b>\n\n"
                    f"<b>👤 المشتري:</b> {get_user_mention(user_id, call.from_user.first_name)}\n"
                    f"<b>🆔 المعرف:</b> {get_username(user_id, call.from_user.username)}\n"
                    f"<b>📦 المنتج:</b> {product['name']}\n"
                    f"<b>🔑 الكود:</b> <code>{product['code']}</code>\n"
                    f"<b>💰 السعر:</b> {product['price_usd']}$\n"
                    f"<b>💳 طريقة الدفع:</b> {method}\n"
                    f"<b>🕒 الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"<b>✦┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄✦</b>",
                    parse_mode="HTML",
                    reply_markup=types.InlineKeyboardMarkup(row_width=1).add(
                        types.InlineKeyboardButton("🔙 العودة إلى البوت", url=f"https://t.me/{bot.get_me().username}", style="primary")
                    )
                )
            except:
                pass
        
        # 4. إشعار للأدمن
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(
                    admin_id, 
                    f"💰 <b>بيع جديد!</b>\n\n"
                    f"👤 {get_user_mention(user_id, call.from_user.first_name)}\n"
                    f"📦 {product['name']}\n"
                    f"💵 {product['price_usd']}$",
                    parse_mode="HTML"
                )
            except:
                pass
                
# ========== تأكيد/رفض البيع اليدوي ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_sale_'))
def confirm_sale(call):
    # 1. التحقق من صلاحيات المستخدم (هل هو أدمن؟)
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    # 2. استخراج بيانات المعاملة من الزر (Callback Data)
    parts = call.data.split('_')
    product_id = int(parts[2])
    buyer_id = parts[3]
    method = parts[4]
    sale_id = int(parts[5])
    
    # 3. جلب معلومات المنتج من قاعدة البيانات
    product = get_product(product_id)
    if not product:
        bot.answer_callback_query(call.id, "❌ المنتج غير موجود!")
        return
    
    # 4. تحديث المخزون (خصم قطعة واحدة)
    new_stock = product['stock'] - 1
    if new_stock <= 0:
        mark_sold(product_id, buyer_id)
    else:
        update_stock(product_id, new_stock)
    
    # 5. تحديث حالة البيع إلى "مكتمل"
    update_sale_status(sale_id, "completed")
    
    # 6. إرسال رسالة تفاصيل الطلب للمشتري أولاً
    try:
        bot.send_message(
            int(buyer_id),
            f"✅ **تم تأكيد طلبك وتسليم المنتج!**\n\n"
            f"📦 **المنتج:** {product['name']}\n"
            f"🔑 **الكود:** `{product.get('code', 'لا يوجد')}`\n"
            f"💰 **السعر:** {product.get('price_usd', 0)}$\n"
            f"💳 **طريقة الدفع:** {method}\n\n"
            f"👨‍💻 **تم التأكيد بواسطة:** @{DEVELOPER_USERNAME}",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"DEBUG: ❌ فشل إرسال رسالة النص للمشتري: {e}")

    # 7. تسليم الملف أو المرفق بشكل ذكي وآمن تماماً (بدون توقف البوت)
    file_id = product.get('file_id')
    if file_id and str(file_id).strip() != "" and str(file_id).strip() != "None":
        file_str = str(file_id).strip()
        sent_successfully = False
        
        # أ) إذا كان مسار محلي في الذاكرة
        if file_str.startswith('/'):
            try:
                with open(file_str, 'rb') as f:
                    bot.send_document(int(buyer_id), f, caption=f"📎 ملف المنتج: {product['name']}")
                sent_successfully = True
            except Exception as local_err:
                print(f"DEBUG: فشل الملف المحلي: {local_err}")
        
        # ب) إذا كان معرف تيليجرام (File ID) كمستند
        if not sent_successfully:
            try:
                bot.send_document(int(buyer_id), file_str, caption=f"📎 ملف المنتج: {product['name']}")
                sent_successfully = True
            except Exception:
                pass
                
        # ج) محاولة كصورة إذا فشل كمستند
        if not sent_successfully:
            try:
                bot.send_photo(int(buyer_id), file_str, caption=f"📎 صورة المنتج: {product['name']}")
                sent_successfully = True
            except Exception:
                pass
                
        # د) محاولة كفيديو كحل أخير
        if not sent_successfully:
            try:
                bot.send_video(int(buyer_id), file_str, caption=f"📎 فيديو المنتج: {product['name']}")
                sent_successfully = True
            except Exception as final_err:
                print(f"DEBUG: ❌ تعذر إرسال المرفق نهائياً: {final_err}")
                try:
                    bot.send_message(int(buyer_id), "⚠️ عذراً، ملف المنتج تالف أو غير مدعوم، تواصل مع الدعم الفني لاستلامه يدوياً.")
                except:
                    pass

    # 8. إشعار الأدمن بأن العملية تمت بنجاح
    bot.answer_callback_query(call.id, "✅ تم تأكيد البيع وإرسال الطلب بنجاح!")

    
    channel_id = get_activation_channel()
    if channel_id:
        try:
            bot.send_message(
                channel_id,
                f"✅ **تم تأكيد البيع وتسليم المنتج!**\n\n"
                f"📦 المنتج: {product['name']}\n"
                f"🔑 الكود: `{product['code']}`\n"
                f"💰 السعر: {product['price_usd']}$\n"
                f"💳 طريقة الدفع: {method}\n"
                f"👨‍💻 المطور: @{DEVELOPER_USERNAME}\n"
                f"🕒 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                parse_mode="Markdown"
            )
        except:
            pass
    
    bot.answer_callback_query(call.id, "✅ تم تأكيد البيع وتسليم المنتج!")
    bot.edit_message_text("✅ **تم تأكيد البيع!**", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reject_sale_'))
def reject_sale(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    parts = call.data.split('_')
    product_id = int(parts[2])
    buyer_id = parts[3]
    sale_id = int(parts[5])
    
    product = get_product(product_id)
    if product:
        add_balance_usd(buyer_id, product['price_usd'])
        update_sale_status(sale_id, "rejected")
        
        try:
            bot.send_message(
                buyer_id,
                f"❌ **تم رفض طلبك!**\n\n"
                f"📦 **المنتج:** {product['name']}\n"
                f"💰 **تم إرجاع المبلغ إلى رصيدك**\n\n"
                f"👨‍💻 **للتواصل مع الدعم:** @{DEVELOPER_USERNAME}",
                parse_mode="Markdown"
            )
        except:
            pass
    
    bot.answer_callback_query(call.id, "❌ تم رفض الطلب وإرجاع المبلغ!")
    bot.edit_message_text("❌ **تم رفض الطلب!**", call.message.chat.id, call.message.message_id)

# ========== رصيدي ==========
@bot.callback_query_handler(func=lambda call: call.data == 'my_balance')
def my_balance(call):
    user = get_user(str(call.from_user.id))
    if not user:
        bot.answer_callback_query(call.id, "❌ حدث خطأ!")
        return
    
    text = f"""
💰 **رصيدك الحالي:**

💵 {user['balance_usd']:.2f}$

📊 **إحصائياتك:**
📦 عدد الطلبات: {user['orders_count']}
💵 إجمالي المشتريات: {user['total_spent']:.2f}$
"""
    bot.edit_message_text(
        text, 
        call.message.chat.id, 
        call.message.message_id, 
        parse_mode="Markdown", 
        reply_markup=main_menu(str(call.from_user.id) in ADMIN_IDS or str(call.from_user.id) in get_all_admins())
    )
    
# ========== شحن الرصيد ==========
@bot.callback_query_handler(func=lambda call: call.data == 'charge_balance')
def charge_balance(call):
    prices = get_charge_prices()
    if not prices:
        bot.edit_message_text(
            "❌ **لا توجد أسعار شحن متاحة.**", 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=main_menu(str(call.from_user.id) in ADMIN_IDS or str(call.from_user.id) in get_all_admins())
        )
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    for p in prices:
        markup.add(types.InlineKeyboardButton(
            f"💵 {p['amount_usd']}$ = ⭐ {p['amount_stars']}", 
            callback_data=f"charge_{p['amount_usd']}_{p['amount_stars']}",
            style="success" if p['amount_usd'] <= 5 else "primary"
        ))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="my_balance", style="danger"))
    
    rate = get_exchange_rate()
    bot.edit_message_text(
        f"💳 **شحن الرصيد**\n\n"
        f"💱 سعر الصرف: 1$ = {rate} ⭐\n"
        f"🪙 1 سنت = {rate/100:.2f} نجمة\n\n"
        f"اختر المبلغ المناسب:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('charge_'))
def process_charge(call):
    parts = call.data.split('_')
    if len(parts) == 3:
        amount_usd = float(parts[1])
        amount_stars = int(parts[2])
    else:
        amount_usd = float(parts[1])
        rate = get_exchange_rate()
        amount_stars = int(amount_usd * rate)
    
    user_id = str(call.from_user.id)
    
    bot.send_invoice(
        call.message.chat.id,
        title=f"💳 شحن {amount_usd}$",
        description=f"شحن {amount_usd}$ إلى رصيدك\n⭐ {amount_stars} نجمة = {amount_usd}$",
        invoice_payload=json.dumps({'type': 'charge', 'amount_usd': amount_usd, 'amount_stars': amount_stars, 'user_id': user_id}),
        provider_token="",
        currency="XTR",
        prices=[types.LabeledPrice("⭐", amount_stars)],
        start_parameter="charge"
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, True)

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
            
            # تسجيل الشحن في جدول إحصائيات النجوم
            add_star_charge(user_id, message.from_user.username or "", amount_usd, amount_stars)
            
            user = get_user(user_id)
            bot.send_message(
                message.chat.id, 
                f"✅ **تم شحن رصيدك بنجاح!**\n\n"
                f"⭐ {amount_stars} نجمة\n"
                f"💵 {amount_usd}$\n"
                f"💰 رصيدك الحالي: {user['balance_usd']:.2f}$", 
                parse_mode="Markdown"
            )
            
            channel_id = get_activation_channel()
            if channel_id:
                try:
                    bot.send_message(
                        channel_id,
                        f"💳 **شحن رصيد جديد!**\n\n"
                        f"👤 المستخدم: {message.from_user.first_name}\n"
                        f"🆔 المعرف: @{message.from_user.username or 'لا يوجد'}\n"
                        f"💰 المبلغ: {amount_usd}$\n"
                        f"⭐ النجوم: {amount_stars}\n"
                        f"🕒 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        parse_mode="Markdown"
                    )
                except:
                    pass
    except Exception as e:
        logger.error(f"Payment error: {e}")

# ========== طلباتي ==========
@bot.callback_query_handler(func=lambda call: call.data == 'my_orders')
def my_orders(call):
    sales = get_recent_sales(10)
    user_sales = [s for s in sales if s['buyer_id'] == str(call.from_user.id)]
    
    if not user_sales:
        bot.edit_message_text(
            "📭 **لا توجد طلبات سابقة.**", 
            call.message.chat.id, 
            call.message.message_id, 
            parse_mode="Markdown", 
            reply_markup=main_menu(str(call.from_user.id) in ADMIN_IDS or str(call.from_user.id) in get_all_admins())
        )
        return
    
    text = "📋 **طلباتي السابقة:**\n\n"
    for s in user_sales:
        status_text = "✅ مكتمل" if s['status'] == 'completed' else "⏳ قيد المراجعة" if s['status'] == 'pending' else "❌ مرفوض"
        text += f"🆔 #{s['id']}\n"
        text += f"💵 {s['amount_usd']}$\n"
        text += f"💳 {s['payment_method']}\n"
        text += f"📊 الحالة: {status_text}\n"
        text += f"🕒 {s['sold_at']}\n\n"
    
    bot.edit_message_text(
        text, 
        call.message.chat.id, 
        call.message.message_id, 
        parse_mode="Markdown", 
        reply_markup=main_menu(str(call.from_user.id) in ADMIN_IDS or str(call.from_user.id) in get_all_admins())
    )
    
# ========== الدعم ==========
@bot.callback_query_handler(func=lambda call: call.data == 'support')
def support(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEVELOPER_USERNAME}", style="primary"),
        types.InlineKeyboardButton("👑 الأدمن", url=f"https://t.me/E_E_72", style="danger"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main", style="danger")
    )
    
    bot.edit_message_text(
        "📞 **الدعم الفني**\n\n"
        "للتواصل مع الدعم الفني:\n"
        f"👨‍💻 **المطور:** @{DEVELOPER_USERNAME}\n"
        f"👑 **الأدمن:** @E_E_72\n\n"
        "اضغط على الزر للتواصل مباشرة:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

# ========== إضافة منتج بأزرار ==========
@bot.callback_query_handler(func=lambda call: call.data == 'admin_add_product')
def admin_add_product(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚡ بيع تلقائي", callback_data="add_product_auto", style="success"),
        types.InlineKeyboardButton("🤝 بيع يدوي", callback_data="add_product_manual", style="danger")
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="danger"))
    
    bot.edit_message_text(
        "➕ **إضافة منتج جديد**\n\n"
        "اختر طريقة البيع:\n\n"
        "⚡ **تلقائي:** يتم تسليم الكود فوراً بعد الدفع\n"
        "🤝 **يدوي:** يتم تأكيد الطلب من الأدمن قبل التسليم",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'add_product_auto')
def add_product_auto(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    user_data[user_id] = {'sale_type': 'auto', 'step': 'name', 'file_id': None}
    
    msg = bot.edit_message_text(
        "📦 **إضافة منتج جديد (بيع تلقائي)**\n\n"
        "الخطوة 1/5\n"
        "أرسل **اسم المنتج**:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=back_admin_keyboard()
    )
    bot.register_next_step_handler(msg, process_product_name)

@bot.callback_query_handler(func=lambda call: call.data == 'add_product_manual')
def add_product_manual(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    user_data[user_id] = {'sale_type': 'manual', 'step': 'name', 'file_id': None}
    
    msg = bot.edit_message_text(
        "📦 **إضافة منتج جديد (بيع يدوي)**\n\n"
        "الخطوة 1/5\n"
        "أرسل **اسم المنتج**:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=back_admin_keyboard()
    )
    bot.register_next_step_handler(msg, process_product_name)

def process_product_name(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data or user_data[user_id].get('step') != 'name':
        return
    
    user_data[user_id]['name'] = message.text.strip()
    user_data[user_id]['step'] = 'description'
    
    msg = bot.send_message(
        message.chat.id,
        "📦 **الخطوة 2/5**\n"
        "أرسل **وصف المنتج**:",
        parse_mode="Markdown",
        reply_markup=back_admin_keyboard()
    )
    bot.register_next_step_handler(msg, process_product_description)

def process_product_description(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data or user_data[user_id].get('step') != 'description':
        return
    
    user_data[user_id]['description'] = message.text.strip()
    user_data[user_id]['step'] = 'price_usd'
    
    msg = bot.send_message(
        message.chat.id,
        "💰 **الخطوة 3/5**\n"
        "أرسل **السعر بالدولار**:\n"
        "مثال: `5`",
        parse_mode="Markdown",
        reply_markup=back_admin_keyboard()
    )
    bot.register_next_step_handler(msg, process_product_price_usd)

def process_product_price_usd(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data or user_data[user_id].get('step') != 'price_usd':
        return
    
    try:
        price_usd = float(message.text.strip())
        user_data[user_id]['price_usd'] = price_usd
        user_data[user_id]['step'] = 'category'
        
        msg = bot.send_message(
            message.chat.id,
            "🏷️ **الخطوة 4/5**\n"
            "أرسل **التصنيف**:\n"
            "مثال: `ارقام`, `حسابات`, `اشتراكات`, ...",
            parse_mode="Markdown",
            reply_markup=back_admin_keyboard()
        )
        bot.register_next_step_handler(msg, process_product_category)
    except:
        msg = bot.send_message(
            message.chat.id,
            "❌ **خطأ!**\n"
            "أرسل رقم صحيح للسعر بالدولار:\n"
            "مثال: `5`",
            reply_markup=back_admin_keyboard()
        )
        bot.register_next_step_handler(msg, process_product_price_usd)

def process_product_category(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data or user_data[user_id].get('step') != 'category':
        return
    
    user_data[user_id]['category'] = message.text.strip()
    user_data[user_id]['step'] = 'code'
    
    msg = bot.send_message(
        message.chat.id,
        "🔑 **الخطوة 5/5**\n"
        "أرسل **الكود أو الحساب**:\n"
        "مثال: `+123456789` أو `user:pass`",
        parse_mode="Markdown",
        reply_markup=back_admin_keyboard()
    )
    bot.register_next_step_handler(msg, process_product_code)

def process_product_code(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data or user_data[user_id].get('step') != 'code':
        return
    
    user_data[user_id]['code'] = message.text.strip()
    user_data[user_id]['step'] = 'file'
    
    msg = bot.send_message(
        message.chat.id,
        "📎 **الخطوة التالية**\n\n"
        "أرسل **صورة أو ملف** للمنتج (اختياري)\n"
        "أو أرسل `تخطي` للتخطي:",
        parse_mode="Markdown",
        reply_markup=back_admin_keyboard()
    )
    bot.register_next_step_handler(msg, process_product_file)

def process_product_file(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data or user_data[user_id].get('step') != 'file':
        return
    
    file_id = None
    file_type = "unknown"
    
    # التحقق من نوع الملف
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "صورة"
    elif message.document:
        file_id = message.document.file_id
        file_type = "مستند"
    elif message.video:
        file_id = message.video.file_id
        file_type = "فيديو"
    elif message.audio:
        file_id = message.audio.file_id
        file_type = "صوت"
    
    # ✅ طباعة للتشخيص
    print(f"DEBUG_FILE: type={file_type}, file_id={str(file_id)[:60] if file_id else 'None'}")
    
    # ✅ التحقق من صحة file_id (يجب يبدأ بأحد هذه)
    valid_starts = ('AgAC', 'BQAC', 'BAAC', 'CgAC', 'DQAC')
    
    if file_id and file_id.startswith(valid_starts):
        user_data[user_id]['file_id'] = file_id
        print(f"DEBUG_FILE: ✅ تم حفظ file_id بنجاح")
        bot.send_message(
            message.chat.id,
            f"✅ **تم رفع الملف بنجاح!**\n"
            f"📎 النوع: {file_type}",
            reply_markup=back_admin_keyboard()
        )
    else:
        user_data[user_id]['file_id'] = None
        print(f"DEBUG_FILE: ❌ file_id غير صالح أو فارغ")
        
        if message.text and message.text.strip() == 'تخطي':
            bot.send_message(
                message.chat.id,
                "⏭️ **تم التخطي.**",
                reply_markup=back_admin_keyboard()
            )
        else:
            bot.send_message(
                message.chat.id,
                f"⚠️ **الملف غير صالح!**\n"
                f"سيتم المتابعة بدون ملف.",
                reply_markup=back_admin_keyboard()
            )
    
    user_data[user_id]['step'] = 'stock'
    
    msg = bot.send_message(
        message.chat.id,
        "📊 **الخطوة الأخيرة**\n"
        "أرسل **المخزون**:\n"
        "مثال: `1` أو `5`",
        parse_mode="Markdown",
        reply_markup=back_admin_keyboard()
    )
    bot.register_next_step_handler(msg, process_product_stock)

def process_product_stock(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data or user_data[user_id].get('step') != 'stock':
        return
    
    try:
        stock = int(message.text.strip())
        user_data[user_id]['stock'] = stock
        
        data = user_data[user_id]
        sale_type = data.get('sale_type', 'auto')
        file_id = data.get('file_id', None)
        
        # ✅ طباعة للتشخيص
        print(f"DEBUG_STOCK: file_id المحفوظ = {str(file_id)[:60] if file_id else 'None'}")
        
        if add_product(
            name=data['name'],
            description=data['description'],
            price_usd=data['price_usd'],
            price_stars=0,
            category=data['category'],
            code=data['code'],
            stock=stock,
            sale_type=sale_type,
            file_id=file_id
        ):
            text = f"""
✅ **تمت إضافة المنتج بنجاح!**

📦 **الاسم:** {data['name']}
📄 **الوصف:** {data['description']}
💰 **السعر:** {data['price_usd']}$
🏷️ **التصنيف:** {data['category']}
🔑 **الكود:** `{data['code']}`
📊 **المخزون:** {stock}
⚡ **نوع البيع:** {'تلقائي' if sale_type == 'auto' else 'يدوي'}
📎 **الملف:** {'✅ مرفوع' if file_id else '❌ لا يوجد'}
"""
            bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=admin_panel_keyboard())
        else:
            bot.send_message(message.chat.id, "❌ **فشل حفظ المنتج!**", reply_markup=admin_panel_keyboard())
        
        del user_data[user_id]
        
    except:
        msg = bot.send_message(
            message.chat.id,
            "❌ **خطأ!**\n"
            "أرسل رقم صحيح للمخزون:\n"
            "مثال: `1`",
            reply_markup=back_admin_keyboard()
        )
        bot.register_next_step_handler(msg, process_product_stock)
      
# ========== أزرار الرجوع ولوحة التحكم ==========
@bot.callback_query_handler(func=lambda call: call.data == 'back_main')
def back_main(call):
    user_id = str(call.from_user.id)
    is_admin = user_id in ADMIN_IDS or user_id in get_all_admins()
    store_name = get_setting('store_name', '🛍️ متجر الأرقام')
    user = get_user(user_id)
    text = f"{store_name}\n\n👋 مرحباً بك!\n📊 عدد المنتجات: {get_product_count()['available']}\n💰 رصيدك بالدولار: {user['balance_usd']:.2f}$\n\n🔹 اختر من القائمة:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu(is_admin))

@bot.callback_query_handler(func=lambda call: call.data == 'admin_panel')
def admin_panel(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    text = f"""
⚙️ **لوحة التحكم**

📊 **الإحصائيات السريعة:**
📦 المتاحة: {get_product_count()['available']}
📦 الإجمالي: {get_product_count()['total']}
💱 سعر الصرف: {get_exchange_rate()} ⭐ = 1$

🔹 اختر الإجراء المناسب:
"""
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == 'admin_products')
def admin_products(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    products = get_available_products()
    if not products:
        bot.edit_message_text("📭 **لا توجد منتجات.**", call.message.chat.id, call.message.message_id, reply_markup=admin_panel_keyboard())
        return
    
    text = "📦 **جميع المنتجات:**\n\n"
    for p in products:
        sale_type_text = "⚡ تلقائي" if p['sale_type'] == 'auto' else "🤝 يدوي"
        text += f"🆔 {p['id']} | {p['name']}\n"
        text += f"💰 {p['price_usd']}$\n"
        text += f"📦 {p['stock']} | {sale_type_text}\n\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == 'admin_delete_product')
def admin_delete_product(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    products = get_available_products()
    if not products:
        bot.edit_message_text("📭 **لا توجد منتجات لحذفها.**", call.message.chat.id, call.message.message_id, reply_markup=admin_panel_keyboard())
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for p in products:
        markup.add(types.InlineKeyboardButton(f"🗑️ {p['id']} - {p['name']}", callback_data=f"del_{p['id']}", style="danger"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="primary"))
    
    bot.edit_message_text("🗑️ **اختر منتجاً للحذف:**", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_'))
def delete_callback(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    product_id = int(call.data.split('_')[1])
    delete_product(product_id)
    bot.answer_callback_query(call.id, "✅ تم الحذف!")
    bot.edit_message_text("🗑️ **تم حذف المنتج.**", call.message.chat.id, call.message.message_id, reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == 'admin_stats')
def admin_stats(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    stats = get_product_count()
    rate = get_exchange_rate()
    
    text = f"""
📊 **الإحصائيات الكاملة**

📦 **المنتجات:**
• المتاحة: {stats['available']}
• الإجمالي: {stats['total']}

💱 **سعر الصرف:** {rate} ⭐ = 1$
🪙 **1 سنت = {rate/100:.2f} نجمة**
"""
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=admin_panel_keyboard())
    
@bot.callback_query_handler(func=lambda call: call.data == 'admin_sales')
def admin_sales(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    sales = get_recent_sales(10)
    if not sales:
        bot.edit_message_text("📭 **لا توجد مبيعات.**", call.message.chat.id, call.message.message_id, reply_markup=admin_panel_keyboard())
        return
    
    text = "📋 **آخر المبيعات:**\n\n"
    for s in sales:
        status_text = "✅ مكتمل" if s['status'] == 'completed' else "⏳ قيد المراجعة" if s['status'] == 'pending' else "❌ مرفوض"
        text += f"🆔 #{s['id']}\n"
        text += f"👤 `{s['buyer_id'][:8]}...`\n"
        text += f"💵 {s['amount_usd']}$\n"
        text += f"💳 {s['payment_method']}\n"
        text += f"📊 {status_text}\n"
        text += f"🕒 {s['sold_at']}\n\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == 'admin_charge')
def admin_charge(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    msg = bot.send_message(call.message.chat.id, "💰 **شحن رصيد مستخدم**\n\nأرسل: `آيدي المستخدم, المبلغ بالدولار`\nمثال: `7325566792, 5`")
    bot.register_next_step_handler(msg, admin_charge_step)

def admin_charge_step(message):
    try:
        data = message.text.split(',')
        if len(data) != 2:
            bot.send_message(message.chat.id, "❌ **الصيغة غير صحيحة!**\nأرسل: `آيدي المستخدم, المبلغ`", reply_markup=admin_panel_keyboard())
            return
        user_id, amount = [x.strip() for x in data]
        amount = float(amount)
        stars = usd_to_stars(amount)
        
        add_balance_usd(user_id, amount)
        add_balance_stars(user_id, stars)
        
        user = get_user(user_id)
        bot.send_message(
            message.chat.id, 
            f"✅ **تم إضافة {amount}$ للمستخدم**\n\n"
            f"👤 `{user_id}`\n"
            f"💰 الرصيد بالدولار: {user['balance_usd']:.2f}$\n"
            f"⭐ الرصيد بالنجوم: {user['balance_stars']}", 
            parse_mode="Markdown", 
            reply_markup=admin_panel_keyboard()
        )
        
        try:
            bot.send_message(user_id, f"✅ **قام الأدمن بإضافة رصيد إلى حسابك**\nبقيمة: 💵 {amount}$+ ({stars} ⭐)!")
        except:
            pass
    except:
        bot.send_message(message.chat.id, "❌ **حدث خطأ!**", reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == 'admin_exchange')
def admin_exchange(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    rate = get_exchange_rate()
    markup = types.InlineKeyboardMarkup(row_width=3)
    rates = ["25", "50", "75", "100", "125", "150", "200", "250", "500"]
    for r in rates:
        markup.add(types.InlineKeyboardButton(f"{r} ⭐ = 1$", callback_data=f"set_rate_{r}", style="primary"))
    markup.add(types.InlineKeyboardButton("✏️ مخصص", callback_data="set_rate_custom", style="success"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="danger"))
    
    bot.edit_message_text(
        f"💱 **سعر الصرف الحالي:** {rate} ⭐ = 1$\n\n"
        f"🪙 **1 سنت = {rate/100:.2f} نجمة**\n\n"
        f"اختر السعر الجديد:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_rate_'))
def set_rate_callback(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    if call.data == "set_rate_custom":
        msg = bot.edit_message_text("✏️ **أدخل سعر الصرف الجديد:**\nمثال: `100`\n(كم نجمة = 1 دولار)", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(msg, set_rate_custom_step)
        return

    rate = int(call.data.split('_')[2])
    set_exchange_rate(rate)
    bot.answer_callback_query(call.id, f"✅ تم التحديث: {rate} ⭐ = 1$")
    admin_exchange(call)

def set_rate_custom_step(message):
    try:
        rate = int(message.text.strip())
        if rate < 1:
            bot.send_message(message.chat.id, "❌ **السعر يجب أن يكون أكبر من 0!**", reply_markup=admin_panel_keyboard())
            return
        set_exchange_rate(rate)
        bot.send_message(message.chat.id, f"✅ **تم تحديث سعر الصرف إلى {rate} ⭐ = 1$**\n🪙 **1 سنت = {rate/100:.2f} نجمة**", reply_markup=admin_panel_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ **أدخل رقماً صحيحاً!**", reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == 'admin_users')
def admin_users(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    data = get_all_users()
    total = data['total']
    users = data['users']
    
    if not users:
        bot.edit_message_text("👥 **لا توجد مستخدمين.**", call.message.chat.id, call.message.message_id, reply_markup=admin_panel_keyboard())
        return
    
    text = f"👥 **عدد المستخدمين:** {total}\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for u in users[:10]:
        text += f"🆔 `{u[0][:8]}...`\n"
        text += f"👤 **الاسم:** {u[2] or u[1] or 'مستخدم'}\n"
        text += f"💰 **رصيد:** {u[3]:.2f}$\n"
        text += f"📦 **طلبات:** {u[5]}\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=admin_panel_keyboard())
    
# ========== تخصيص الأزرار ==========
@bot.callback_query_handler(func=lambda call: call.data == 'admin_edit_buttons')
def admin_edit_buttons(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    buttons = get_all_buttons()
    
    if not buttons:
        bot.edit_message_text("❌ **لا توجد أزرار.**", call.message.chat.id, call.message.message_id, reply_markup=admin_panel_keyboard())
        return
    
    text = "🎨 **تخصيص الأزرار والألوان**\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for btn in buttons:
        status = "✅" if btn['is_active'] else "❌"
        style_name = {'primary': 'أزرق', 'success': 'أخضر', 'danger': 'أحمر'}.get(btn['style'], 'افتراضي')
        
        text += f"{status} **{btn['label']}**\n"
        text += f"└ 🆔 `{btn['key']}` | صف {btn['row']} | عمود {btn['col']}\n"
        text += f"└ 🎨 اللون: {style_name}\n\n"
        
        markup.add(types.InlineKeyboardButton(
            f"✏️ تعديل {btn['label']}", 
            callback_data=f"edit_btn_{btn['key']}",
            style=btn['style']
        ))
    
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="danger"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_btn_'))
def edit_button_callback(call):
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    key = call.data.replace('edit_btn_', '')
    btn = next((b for b in get_all_buttons() if b['key'] == key), None)
    
    if not btn:
        bot.answer_callback_query(call.id, "❌ الزر غير موجود!")
        return
    
    style_name = {'primary': 'أزرق', 'success': 'أخضر', 'danger': 'أحمر'}.get(btn['style'], 'افتراضي')
    
    text = f"""
✏️ **تعديل الزر:** `{key}`

📌 **الحالي:**
└ النص: {btn['label']}
└ الصف: {btn['row']}
└ العمود: {btn['col']}
└ 🎨 اللون: {style_name}
└ الحالة: {'مفعل' if btn['is_active'] else 'معطل'}

اختر الإجراء:
"""
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✏️ تغيير النص", callback_data=f"btn_label_{key}", style="primary"),
        types.InlineKeyboardButton("🎨 تغيير اللون", callback_data=f"btn_color_{key}", style="success"),
        types.InlineKeyboardButton("⬆️ تغيير الصف", callback_data=f"btn_row_{key}", style="primary"),
        types.InlineKeyboardButton("➡️ تغيير العمود", callback_data=f"btn_col_{key}", style="primary"),
        types.InlineKeyboardButton("🔄 تبديل الحالة", callback_data=f"btn_toggle_{key}", style="danger"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_edit_buttons", style="danger")
    )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('btn_color_'))
def change_color_menu(call):
    key = call.data.replace('btn_color_', '')
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    colors = [
        ("primary", "🔵 أزرق"),
        ("success", "🟢 أخضر"),
        ("danger", "🔴 أحمر")
    ]
    
    for style, label in colors:
        markup.add(types.InlineKeyboardButton(
            label, 
            callback_data=f"set_color_{key}_{style}",
            style=style
        ))
    
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data=f"edit_btn_{key}", style="danger"))
    
    bot.edit_message_text(
        f"🎨 **اختر اللون للزر `{key}`**\n\n"
        f"الألوان المتاحة:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_color_'))
def save_new_color(call):
    parts = call.data.replace('set_color_', '').rsplit('_', 1)
    key, style = parts[0], parts[1]
    
    update_button(key, style=style)
    
    style_name = {'primary': 'أزرق', 'success': 'أخضر', 'danger': 'أحمر'}.get(style, 'افتراضي')
    
    bot.answer_callback_query(call.id, f"✅ تم تغيير اللون إلى {style_name}!")
    
    edit_button_callback(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith('btn_label_'))
def prompt_change_label(call):
    key = call.data.replace('btn_label_', '')
    msg = bot.send_message(call.message.chat.id, f"✏️ أرسل النص الجديد للزر `{key}`:")
    bot.register_next_step_handler(msg, save_new_label, key)

def save_new_label(message, key):
    new_label = message.text.strip()
    update_button(key, label=new_label)
    bot.send_message(message.chat.id, f"✅ تم تحديث نص الزر `{key}` إلى: {new_label}", reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('btn_toggle_'))
def toggle_button_status(call):
    key = call.data.replace('btn_toggle_', '')
    btn = next((b for b in get_all_buttons() if b['key'] == key), None)
    if btn:
        new_status = 0 if btn['is_active'] else 1
        update_button(key, is_active=new_status)
        bot.answer_callback_query(call.id, "🔄 تم تغيير حالة الزر بنجاح!")
        admin_edit_buttons(call)
        
# ========== تغيير الصف ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('btn_row_'))
def btn_change_row(call):
    """عرض قائمة الصفوف لتغيير صف الزر"""
    key = call.data.replace('btn_row_', '')
    markup = types.InlineKeyboardMarkup(row_width=3)
    for row in range(1, 6):
        markup.add(types.InlineKeyboardButton(
            f"📌 صف {row}", 
            callback_data=f"set_row_{key}_{row}",
            style="primary"
        ))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data=f"edit_btn_{key}", style="danger"))
    
    bot.edit_message_text(
        f"📍 **اختر الصف الجديد للزر `{key}`**",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

# ========== حفظ الصف الجديد ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('set_row_'))
def set_btn_row(call):
    """حفظ الصف الجديد للزر في قاعدة البيانات"""
    parts = call.data.replace('set_row_', '').rsplit('_', 1)
    key = parts[0]
    row = int(parts[1])
    
    update_button(key, row=row)
    bot.answer_callback_query(call.id, f"✅ تم تغيير الصف إلى {row}!")
    bot.edit_message_text(
        "✅ **تم تغيير الصف بنجاح!**",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=admin_panel_keyboard()
    )

# ========== تغيير العمود ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('btn_col_'))
def btn_change_col(call):
    """عرض قائمة الأعمدة لتغيير عمود الزر"""
    key = call.data.replace('btn_col_', '')
    markup = types.InlineKeyboardMarkup(row_width=3)
    for col in range(1, 4):
        markup.add(types.InlineKeyboardButton(
            f"📍 عمود {col}", 
            callback_data=f"set_col_{key}_{col}",
            style="primary"
        ))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data=f"edit_btn_{key}", style="danger"))
    
    bot.edit_message_text(
        f"📍 **اختر العمود الجديد للزر `{key}`**",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

# ========== حفظ العمود الجديد ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('set_col_'))
def set_btn_col(call):
    """حفظ العمود الجديد للزر في قاعدة البيانات"""
    parts = call.data.replace('set_col_', '').rsplit('_', 1)
    key = parts[0]
    col = int(parts[1])
    
    update_button(key, col=col)
    bot.answer_callback_query(call.id, f"✅ تم تغيير العمود إلى {col}!")
    bot.edit_message_text(
        "✅ **تم تغيير العمود بنجاح!**",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=admin_panel_keyboard()
    )
    
# ========== إدارة المطورين ==========
@bot.callback_query_handler(func=lambda call: call.data == 'admin_developers')
def admin_developers(call):
    """عرض قائمة المطورين وإدارة الصلاحيات"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    admins = get_all_admins()
    text = "👑 **إدارة المطورين**\n\n"
    text += "المطورين الحاليين:\n"
    for admin in admins:
        text += f"└ 🆔 `{admin}`\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ إضافة مطور", callback_data="add_developer", style="success"),
        types.InlineKeyboardButton("➖ حذف مطور", callback_data="remove_developer", style="danger"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="danger")
    )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'add_developer')
def add_developer(call):
    """طلب آيدي المطور الجديد لإضافته"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    msg = bot.edit_message_text("📝 **أدخل آيدي المطور الجديد:**", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(msg, save_developer)

def save_developer(message):
    """حفظ آيدي المطور الجديد في قاعدة البيانات"""
    try:
        new_admin = message.text.strip()
        if add_admin(new_admin):
            bot.send_message(message.chat.id, f"✅ **تم إضافة المطور الجديد!**\n🆔 `{new_admin}`", reply_markup=admin_panel_keyboard())
        else:
            bot.send_message(message.chat.id, "❌ **فشل الإضافة!** قد يكون موجوداً مسبقاً.", reply_markup=admin_panel_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ **حدث خطأ!**", reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == 'remove_developer')
def remove_developer(call):
    """عرض قائمة المطورين لحذف أحدهم"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    admins = get_all_admins()
    if len(admins) <= 1:
        bot.answer_callback_query(call.id, "❌ لا يمكن حذف المطور الوحيد!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for admin in admins:
        if admin != user_id:
            markup.add(types.InlineKeyboardButton(f"🗑️ حذف {admin}", callback_data=f"del_dev_{admin}", style="danger"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_developers", style="danger"))
    
    bot.edit_message_text("🗑️ **اختر مطوراً للحذف:**", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_dev_'))
def delete_developer(call):
    """حذف المطور المحدد من قاعدة البيانات"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    dev_id = call.data.split('_')[2]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM admins WHERE user_id=?", (dev_id,))
    conn.commit()
    conn.close()
    
    bot.answer_callback_query(call.id, f"✅ تم حذف المطور {dev_id}!")
    admin_developers(call)
    
# ========== إدارة أسعار الشحن ==========
@bot.callback_query_handler(func=lambda call: call.data == 'admin_charge_prices')
def admin_charge_prices(call):
    """عرض أسعار الشحن وإدارتها"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    prices = get_charge_prices()
    text = "💲 **أسعار الشحن الحالية:**\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if not prices:
        text += "❌ لا توجد أسعار.\n"
    else:
        for p in prices:
            text += f"🆔 {p['id']} | {p['amount_usd']}$ = ⭐ {p['amount_stars']}\n"
            markup.add(types.InlineKeyboardButton(
                f"✏️ تعديل {p['amount_usd']}$", 
                callback_data=f"edit_price_{p['id']}",
                style="primary"
            ))
            markup.add(types.InlineKeyboardButton(
                f"🗑️ حذف {p['amount_usd']}$", 
                callback_data=f"del_price_{p['id']}",
                style="danger"
            ))
    
    markup.add(types.InlineKeyboardButton("➕ إضافة سعر جديد", callback_data="admin_add_price", style="success"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="danger"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_add_price')
def admin_add_price(call):
    """طلب بيانات سعر شحن جديد"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    msg = bot.edit_message_text(
        "➕ **إضافة سعر شحن جديد**\n\n"
        "أرسل: `المبلغ بالدولار, عدد النجوم`\n"
        "مثال: `3, 150`\n\n"
        "يعني: 3$ = 150 نجمة",
        call.message.chat.id,
        call.message.message_id
    )
    bot.register_next_step_handler(msg, add_price_step)

def add_price_step(message):
    """حفظ سعر الشحن الجديد في قاعدة البيانات"""
    try:
        data = message.text.split(',')
        if len(data) != 2:
            bot.send_message(message.chat.id, "❌ **الصيغة غير صحيحة!**\nأرسل: `المبلغ, النجوم`", reply_markup=admin_panel_keyboard())
            return
        
        amount_usd = float(data[0].strip())
        amount_stars = int(data[1].strip())
        
        if add_charge_price(amount_usd, amount_stars):
            bot.send_message(message.chat.id, f"✅ **تم إضافة السعر بنجاح!**\n\n{amount_usd}$ = ⭐ {amount_stars}", reply_markup=admin_panel_keyboard())
        else:
            bot.send_message(message.chat.id, "❌ **فشل الإضافة!**", reply_markup=admin_panel_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ **حدث خطأ!** تأكد من البيانات.", reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_price_'))
def edit_price(call):
    """طلب بيانات تعديل سعر شحن موجود"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    price_id = int(call.data.split('_')[2])
    price = get_charge_price_by_id(price_id)
    if not price:
        bot.answer_callback_query(call.id, "❌ السعر غير موجود!")
        return
    
    msg = bot.edit_message_text(
        f"✏️ **تعديل السعر**\n\n"
        f"السعر الحالي: {price['amount_usd']}$ = ⭐ {price['amount_stars']}\n\n"
        f"أرسل: `المبلغ الجديد بالدولار, عدد النجوم الجديد`\n"
        f"مثال: `5, 250`",
        call.message.chat.id,
        call.message.message_id
    )
    bot.register_next_step_handler(msg, edit_price_step, price_id)

def edit_price_step(message, price_id):
    """حفظ تعديل السعر في قاعدة البيانات"""
    try:
        data = message.text.split(',')
        if len(data) != 2:
            bot.send_message(message.chat.id, "❌ **الصيغة غير صحيحة!**\nأرسل: `المبلغ, النجوم`", reply_markup=admin_panel_keyboard())
            return
        
        amount_usd = float(data[0].strip())
        amount_stars = int(data[1].strip())
        
        update_charge_price(price_id, amount_usd, amount_stars)
        bot.send_message(message.chat.id, f"✅ **تم تحديث السعر بنجاح!**\n\n{amount_usd}$ = ⭐ {amount_stars}", reply_markup=admin_panel_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ **حدث خطأ!** تأكد من البيانات.", reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_price_'))
def delete_price(call):
    """حذف سعر شحن من القائمة"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    price_id = int(call.data.split('_')[2])
    delete_charge_price(price_id)
    bot.answer_callback_query(call.id, "✅ تم حذف السعر!")
    admin_charge_prices(call)
    
# ========== إدارة القنوات ==========
@bot.callback_query_handler(func=lambda call: call.data == 'admin_channels')
def admin_channels(call):
    """عرض قائمة القنوات وإدارتها"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    activation = get_activation_channel()
    channels = get_activation_channels()
    
    text = "📢 **إدارة القنوات**\n\n"
    text += f"🔹 قناة التفعيل الحالية: {activation or 'غير محددة'}\n\n"
    text += "الخطوات:\n"
    text += "1. أضف البوت كأدمن في القناة\n"
    text += "2. اضغط على الزر لإضافة القناة\n\n"
    text += "القنوات المضافة:\n"
    
    for ch in channels:
        text += f"└ {ch['id']} | {ch['name']}\n"
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel", style="success"),
        types.InlineKeyboardButton("🎯 تحديد قناة التفعيل", callback_data="set_activation_channel", style="primary"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel", style="danger")
    )
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'add_channel')
def add_channel_callback(call):
    """طلب معرف القناة الجديدة لإضافتها"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    msg = bot.edit_message_text(
        "📢 **إضافة قناة جديدة**\n\n"
        "أرسل معرف القناة:\n"
        "مثال: `@my_channel`",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, save_channel)

def save_channel(message):
    """حفظ القناة الجديدة في قاعدة البيانات"""
    try:
        channel_id = message.text.strip()
        add_channel(channel_id)
        bot.send_message(message.chat.id, f"✅ **تم إضافة القناة `{channel_id}`!**", reply_markup=admin_panel_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ **حدث خطأ!**", reply_markup=admin_panel_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == 'set_activation_channel')
def set_activation(call):
    """عرض القنوات لاختيار قناة التفعيل"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    channels = get_activation_channels()
    if not channels:
        bot.answer_callback_query(call.id, "❌ لا توجد قنوات مضافة!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in channels:
        markup.add(types.InlineKeyboardButton(f"🎯 {ch['id']}", callback_data=f"set_act_{ch['id']}", style="primary"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_channels", style="danger"))
    
    bot.edit_message_text("🎯 **اختر قناة التفعيل:**", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_act_'))
def set_act_channel(call):
    """تعيين القناة المختارة كقناة التفعيل الرئيسية"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    channel_id = call.data.replace('set_act_', '')
    set_activation_channel(channel_id)
    bot.answer_callback_query(call.id, f"✅ تم تحديد {channel_id} كقناة التفعيل!")
    admin_channels(call)
    
# ========== إحصائيات شحن النجوم ==========
@bot.callback_query_handler(func=lambda call: call.data == 'admin_star_stats')
def admin_star_stats(call):
    """عرض إحصائيات شحن النجوم الحقيقية"""
    user_id = str(call.from_user.id)
    if user_id not in ADMIN_IDS and user_id not in get_all_admins():
        bot.answer_callback_query(call.id, "❌ غير مصرح!")
        return
    
    stats = get_star_charge_stats()
    
    text = f"⭐ **إحصائيات شحن النجوم الحقيقية**\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    text += f"👥 **عدد الأشخاص اللي شحنوا:** {stats['unique_users']}\n"
    text += f"🔄 **عدد مرات الشحن:** {stats['total_charges']}\n"
    text += f"⭐ **مجموع النجوم:** {stats['total_stars']}\n"
    text += f"💵 **مجموع الدولار:** {stats['total_usd']:.2f}$\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if stats['recent']:
        text += "📋 **آخر عمليات الشحن:**\n\n"
        for r in stats['recent']:
            text += f"👤 {r[1] or r[0]}\n"
            text += f"💵 {r[2]:.2f}$ | ⭐ {r[3]}\n"
            text += f"🕒 {r[4]}\n"
            text += "━━━━━━━━━━━━━━━━━━━━\n"
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=admin_panel_keyboard())

# ========== معالجات القائمة السفلية ==========
@bot.message_handler(func=lambda message: message.text == "💰 رصيدي")
def btn_balance(message):
    """عرض رصيد المستخدم"""
    user = get_user(str(message.from_user.id))
    if not user:
        bot.reply_to(message, "❌ حدث خطأ!")
        return
    
    text = f"""
💰 **رصيدك الحالي:**

💵 {user['balance_usd']:.2f}$

📊 **إحصائياتك:**
📦 عدد الطلبات: {user['orders_count']}
💵 إجمالي المشتريات: {user['total_spent']:.2f}$
"""
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📋 طلباتي")
def btn_orders(message):
    """عرض طلبات المستخدم"""
    sales = get_recent_sales(10)
    user_sales = [s for s in sales if s['buyer_id'] == str(message.from_user.id)]
    
    if not user_sales:
        bot.reply_to(message, "📭 لا توجد طلبات سابقة.")
        return
    
    text = "📋 **طلباتي السابقة:**\n\n"
    for s in user_sales:
        status_text = "✅ مكتمل" if s['status'] == 'completed' else "⏳ قيد المراجعة" if s['status'] == 'pending' else "❌ مرفوض"
        text += f"🆔 #{s['id']}\n💵 {s['amount_usd']}$\n💳 {s['payment_method']}\n📊 {status_text}\n🕒 {s['sold_at']}\n\n"
    
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💳 شحن رصيد")
def btn_charge(message):
    """عرض خيارات الشحن"""
    prices = get_charge_prices()
    if not prices:
        bot.reply_to(message, "❌ لا توجد أسعار شحن متاحة.")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    for p in prices:
        markup.add(types.InlineKeyboardButton(
            f"💵 {p['amount_usd']}$ = ⭐ {p['amount_stars']}", 
            callback_data=f"charge_{p['amount_usd']}_{p['amount_stars']}",
            style="success" if p['amount_usd'] <= 5 else "primary"
        ))
    
    rate = get_exchange_rate()
    bot.reply_to(
        message,
        f"💳 **شحن الرصيد**\n\n"
        f"💱 سعر الصرف: 1$ = {rate} ⭐\n"
        f"🪙 1 سنت = {rate/100:.2f} نجمة\n\n"
        f"اختر المبلغ:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "❓ مساعدة")
def btn_help(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📞 تواصل مع الدعم", url=f"https://t.me/{DEVELOPER_USERNAME}", style="success"),
        types.InlineKeyboardButton("👑 الأدمن", url=f"https://t.me/E_E_72", style="danger")
    )
    
    bot.reply_to(
        message,
        f"❓ **المساعدة**\n\n"
        f"🔹 /start - القائمة الرئيسية\n"
        f"🔹 /id - عرض آيديك\n"
        f"🔹 /help - المساعدة\n\n"
        f"👇 **للتواصل اضغط الزر:**",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "🎁 شارك واربح")
def btn_share(message):
    """عرض رابط الإحالة"""
    user_id = str(message.from_user.id)
    user = get_user(user_id)
    
    if not user:
        bot.reply_to(message, "❌ حدث خطأ!")
        return
    
    if not is_referral_enabled():
        bot.reply_to(message, "❌ الميزة معطلة حالياً!")
        return
    
    bot_username = bot.get_me().username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    stats = get_user_referrals(user_id)
    daily = get_daily_referrals(user_id)
    daily_limit = get_referral_daily_limit()
    reward = get_referral_reward()
    
    text = f"""
🎁 **شارك واربح**

💰 **المكافأة/صديق:** {reward:.2f}$
👥 **إحالاتك:** {stats['count']}
💵 **إجمالي الأرباح:** {stats['total_earned']:.2f}$
📅 **إحالات اليوم:** {daily}/{daily_limit}

🔗 **رابطك:**
`{referral_link}`
"""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📋 نسخ ومشاركة", url=f"https://t.me/share/url?url={referral_link}&text=انضم!", style="success")
    )
    
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔄 تشغيل البوت")
def btn_restart(message):
    """إعادة تشغيل البوت"""
    start_cmd(message)

# ========== تشغيل البوت ==========
if __name__ == "__main__":
    # ===== Web Server للمراقبة =====
    from flask import Flask
    import threading
    
    bot_web = Flask(__name__)
    
    bot_status = {
        'running': False,
        'started_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    @bot_web.route('/')
    @bot_web.route('/health')
    def health():
        """Health check لـ UptimeRobot"""
        return {
            'status': 'ok' if bot_status['running'] else 'starting',
            'bot': 'running' if bot_status['running'] else 'initializing',
            'started_at': bot_status['started_at'],
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, 200
    
    @bot_web.route('/ping')
    def ping():
        """endpoint سريع جداً لـ UptimeRobot"""
        return "pong", 200
    
    def run_web():
        port = int(os.environ.get('PORT', 5000))
        print(f"🌐 Web Server شغال على المنفذ {port}")
        bot_web.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False  # مهم — يمنع تشغيل مزدوج
        )
    
    # ===== قاعدة البيانات =====
    init_db()
    
    # ===== تسجيل الأوامر =====
    try:
        bot.set_my_commands([
            BotCommand("start", "🏠 بدء البوت"),
            BotCommand("menu", "📋 عرض القائمة"),
            BotCommand("id", "🆔 عرض آيديك"),
            BotCommand("help", "❓ المساعدة"),
        ])
        print("✅ تم تسجيل الأوامر")
    except Exception as e:
        print(f"⚠️ {e}")
    
    # ===== معلومات التشغيل =====
    rate = get_exchange_rate()
    print("=" * 50)
    print("🚀 النظام يبدأ...")
    print(f"👑 الأدمن: {', '.join(ADMIN_IDS)}")
    print(f"💱 سعر الصرف: {rate} ⭐ = 1$")
    print(f"👨‍💻 المطور: @{DEVELOPER_USERNAME}")
    print("=" * 50)
    
    # ===== حذف Webhook مرة واحدة فقط (خارج الحلقة!) =====
    try:
        print("🔄 حذف Webhook...")
        bot.delete_webhook(drop_pending_updates=False)
        print("✅ تم")
    except Exception as e:
        print(f"⚠️ {e}")
    
    # ===== تشغيل Web Server في Thread =====
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    print("🌐 Web Server شغال في Thread منفصل")
    
    # ===== تشغيل Polling (بدون delete_webhook داخل الحلقة) =====
    bot_status['running'] = True
    print("🚀 البوت يبدأ استقبال الرسائل...")
    
    while True:
        try:
            bot.infinity_polling(
                timeout=30,
                long_polling_timeout=20,
                none_stop=True,
                skip_pending=False
            )
        except Exception as e:
            print(f"❌ خطأ في Polling: {e}")
            print("⏳ إعادة المحاولة بعد 5 ثوان...")
            time.sleep(5)