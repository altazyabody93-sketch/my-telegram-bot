import html
# -*- coding: utf-8 -*-
# ============================================================
# المطري OTP — بوت تيليجرام كامل
# ملف واحد جاهز للتشغيل على Termux
# ============================================================

import os
import sys
import json
import time
import random
import string
import sqlite3
import hashlib
import threading
import base64
import re
from datetime import datetime, timedelta

import telebot
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
import requests
import html
from telebot.types import CopyTextButton, WebAppInfo, WebAppInfo, WebAppInfo, WebAppInfo

# ============================================================
# 🎨 تلوين تلقائي لكل أزرار البوت — أحمر danger / أخضر success / أزرق primary
# أي زر بلا لون صالح يأخذ لونًا حسب وظيفته (النص ثم الـ callback_data). الأزرار الملوّنة صراحةً لا تتغير.
# ============================================================
_BTN_COLORS = ("primary", "success", "danger")
_DANGER_TXT = ("حذف", "مسح", "إلغاء", "الغاء", "إيقاف", "ايقاف", "حظر", "تصفير", "إعادة تعيين", "اعادة تعيين",
               "إغلاق", "اغلاق", "رجوع", "القائمة الرئيسية", "الرئيسية", "تعطيل", "إزالة", "ازالة", "خروج",
               "❌", "🗑", "⛔", "🚫", "⏹", "⏸", "🏠")
_SUCCESS_TXT = ("إضافة", "اضافة", "➕", "حفظ", "تأكيد", "تاكيد", "نعم", "✅", "تشغيل", "تفعيل", "▶️",
                "إرسال", "ارسال", "تجربة", "اختبار", "فحص", "رفع", "استيراد", "تصدير", "نسخ", "📋",
                "احصل", "الحصول", "انضم", "جروب", "اشتراك", "موافق", "🧪", "📥", "📤", "🔎")
_DANGER_CB = {"del", "delete", "clear", "cancel", "ban", "stop", "reset", "remove", "rm", "disable",
              "off", "no", "close", "kick", "wipe"}
_SUCCESS_CB = {"add", "new", "save", "confirm", "yes", "start", "enable", "on", "test", "send", "upload",
               "export", "copy", "create", "approve", "run", "fetch", "scan", "smart", "detect",
               "import", "probe", "ok"}


def _auto_style(text, callback_data=None, url=None, copy_text=None):
    """يحدد لون الزر من وظيفته: danger للحذف/الإلغاء/الرجوع، success للإضافة/الحفظ/التأكيد/النسخ، وإلا primary"""
    if copy_text:
        return "success"
    t = str(text or "")
    if any(k in t for k in _DANGER_TXT):
        return "danger"
    if any(k in t for k in _SUCCESS_TXT):
        return "success"
    toks = set(re.split(r"[:_\-/\s]+", str(callback_data or "").lower()))
    if toks & _DANGER_CB:
        return "danger"
    if toks & _SUCCESS_CB:
        return "success"
    return "primary"


_ORIG_INLINE_BUTTON = InlineKeyboardButton


class InlineKeyboardButton(_ORIG_INLINE_BUTTON):
    """نفس زر telebot لكن لا يُترك بلا لون: يضيف style تلقائيًا عند غيابه أو عدم صلاحيته"""

    def __init__(self, text, *args, **kwargs):
        style = kwargs.get("style")
        if style not in _BTN_COLORS:
            style = _auto_style(text, kwargs.get("callback_data"), kwargs.get("url"), kwargs.get("copy_text"))
        kwargs["style"] = style
        try:
            super().__init__(text, *args, **kwargs)
        except TypeError:
            kwargs.pop("style", None)
            super().__init__(text, *args, **kwargs)


_ORIG_INLINE_MARKUP = InlineKeyboardMarkup


class InlineKeyboardMarkup(_ORIG_INLINE_MARKUP):
    """نفس لوحة telebot لكن تتجاهل الأزرار المخفية (None) بدل أن تنهار عند الإرسال"""

    def add(self, *args, **kwargs):
        args = [a for a in args if a is not None]
        if not args:
            return self
        return super().add(*args, **kwargs)

    def row(self, *args):
        args = [a for a in args if a is not None]
        if not args:
            return self
        return super().row(*args)

    def insert(self, button):
        if button is None:
            return self
        return super().insert(button)


OTP_LAST_ERROR = {"msg": ""}

OTP_STYLES = {
    "quote": "📜 اقتباس قابل للطي",
    "card": "🪪 بطاقة",
    "neon": "✨ نيون",
    "minimal": "⚡ مختصر",
}


# ============================================================
# الإعدادات
# ============================================================
BOT_TOKEN = "7798949296:AAF_S41VvNkPyQNypCva77nDktT38Y9QPfI"
MAIN_ADMIN_ID = 7325566792
DB_FILE = "data/bot.db"
DEFAULT_INTERVAL = 60
MAX_CODES = 2000

OTP_PLATFORMS = [
    ("whatsapp", "WhatsApp", "🟢"),
    ("telegram", "Telegram", "🔵"),
    ("facebook", "Facebook", "🔷"),
    ("instagram", "Instagram", "🟣"),
    ("twitter", "Twitter", "🔶"),
    ("google", "Google", "🔴"),
    ("apple", "Apple", "⚫"),
    ("tiktok", "TikTok", "⚫"),
    ("discord", "Discord", "🟪"),
    ("snapchat", "Snapchat", "🟡"),
]


os.makedirs("data", exist_ok=True)


class BTN:
    """أنماط الأزرار الرسمية"""
    PRIMARY = "primary"
    SUCCESS = "success"
    DANGER = "danger"
    DEFAULT = None



# ============================================================
# قاعدة البيانات
# ============================================================
def db():
    conn = sqlite3.connect(DB_FILE, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn



# ============================================================
# دوال الإعدادات
# ============================================================
def setting_get(key, default=""):
    conn = db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def setting_set(key, value):
    conn = db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()


def is_maintenance():
    return setting_get("maintenance", "0") == "1"



def db_init():
    conn = db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            display_name TEXT DEFAULT '',
            password_hash TEXT DEFAULT '',
            created REAL DEFAULT 0,
            avatar TEXT DEFAULT '',
            last_login REAL DEFAULT 0,
            visits INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            country TEXT NOT NULL,
            phone TEXT NOT NULL,
            added_at REAL DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT DEFAULT '',
            code TEXT DEFAULT '',
            platform TEXT DEFAULT '',
            country TEXT DEFAULT '',
            message TEXT DEFAULT '',
            received_at REAL DEFAULT 0,
            expires_at REAL DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS external_apis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            token TEXT DEFAULT '',
            username TEXT DEFAULT '',
            password TEXT DEFAULT '',
            auth_type TEXT DEFAULT 'token',
            enabled INTEGER DEFAULT 1,
            smart_bind INTEGER DEFAULT 1,
            auto_push INTEGER DEFAULT 1,
            interval_sec INTEGER DEFAULT 60,
            last_fetch REAL DEFAULT 0,
            last_count INTEGER DEFAULT 0,
            last_status TEXT DEFAULT 'idle',
            last_error TEXT DEFAULT '',
            api_path TEXT DEFAULT '',
            api_method TEXT DEFAULT 'GET',
            json_path TEXT DEFAULT '',
            field_phone TEXT DEFAULT '',
            field_code TEXT DEFAULT '',
            field_platform TEXT DEFAULT '',
            field_country TEXT DEFAULT '',
            field_message TEXT DEFAULT '',
            custom_headers TEXT DEFAULT '[]',
            custom_query TEXT DEFAULT '[]',
            body_json TEXT DEFAULT '',
            fail_count INTEGER DEFAULT 0,
            created REAL DEFAULT 0,
            updated REAL DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS contests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            kind TEXT DEFAULT 'vote',
            prize TEXT DEFAULT '',
            icon TEXT DEFAULT '🎁',
            starts_at REAL DEFAULT 0,
            ends_at REAL DEFAULT 0,
            status TEXT DEFAULT 'active',
            pinned INTEGER DEFAULT 0,
            votes TEXT DEFAULT '{}',
            voters TEXT DEFAULT '[]',
            created REAL DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT DEFAULT '',
            images TEXT DEFAULT '[]',
            contact_url TEXT DEFAULT '',
            contact_label TEXT DEFAULT 'تواصل',
            status TEXT DEFAULT 'active',
            pinned INTEGER DEFAULT 0,
            created REAL DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sender TEXT DEFAULT 'user',
            message TEXT DEFAULT '',
            media TEXT DEFAULT '',
            created REAL DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            added_at REAL DEFAULT 0,
            added_by INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS numbers_imports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            country TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            created REAL DEFAULT 0
        )
    """)

    # جداول تخصيص الأزرار وترتيب القائمة (كانت مستخدمة ولا يُنشأ لها جدول)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS channel_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            created REAL DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS button_config (
            key TEXT PRIMARY KEY,
            label_ar TEXT DEFAULT '',
            label_en TEXT DEFAULT '',
            style TEXT DEFAULT '',
            icon TEXT DEFAULT '',
            visible INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS main_menu_layout (
            button_key TEXT PRIMARY KEY,
            sort_order INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] ready")


# ============================================================
# 190 دولة كاملة
# ============================================================
COUNTRIES = {
    "+93": ("AF", "أفغانستان"),
    "+355": ("AL", "ألبانيا"),
    "+213": ("DZ", "الجزائر"),
    "+376": ("AD", "أندورا"),
    "+244": ("AO", "أنغولا"),
    "+1264": ("AI", "أنغيلا"),
    "+1268": ("AG", "أنتيغوا وبربودا"),
    "+54": ("AR", "الأرجنتين"),
    "+374": ("AM", "أرمينيا"),
    "+297": ("AW", "أروبا"),
    "+61": ("AU", "أستراليا"),
    "+43": ("AT", "النمسا"),
    "+994": ("AZ", "أذربيجان"),
    "+1242": ("BS", "الباهاما"),
    "+973": ("BH", "البحرين"),
    "+880": ("BD", "بنغلاديش"),
    "+1246": ("BB", "بربادوس"),
    "+375": ("BY", "بيلاروسيا"),
    "+32": ("BE", "بلجيكا"),
    "+501": ("BZ", "بليز"),
    "+229": ("BJ", "بنين"),
    "+1441": ("BM", "برمودا"),
    "+975": ("BT", "بوتان"),
    "+591": ("BO", "بوليفيا"),
    "+387": ("BA", "البوسنة والهرسك"),
    "+267": ("BW", "بوتسوانا"),
    "+55": ("BR", "البرازيل"),
    "+1284": ("VG", "جزر العذراء البريطانية"),
    "+673": ("BN", "بروناي"),
    "+359": ("BG", "بلغاريا"),
    "+226": ("BF", "بوركينا فاسو"),
    "+257": ("BI", "بوروندي"),
    "+855": ("KH", "كمبوديا"),
    "+237": ("CM", "الكاميرون"),
    "+1": ("US", "الولايات المتحدة"),
    "+238": ("CV", "الرأس الأخضر"),
    "+1345": ("KY", "جزر كايمان"),
    "+236": ("CF", "أفريقيا الوسطى"),
    "+235": ("TD", "تشاد"),
    "+56": ("CL", "تشيلي"),
    "+86": ("CN", "الصين"),
    "+57": ("CO", "كولومبيا"),
    "+269": ("KM", "جزر القمر"),
    "+242": ("CG", "الكونغو"),
    "+243": ("CD", "الكونغو الديمقراطية"),
    "+682": ("CK", "جزر كوك"),
    "+506": ("CR", "كوستاريكا"),
    "+225": ("CI", "ساحل العاج"),
    "+385": ("HR", "كرواتيا"),
    "+53": ("CU", "كوبا"),
    "+357": ("CY", "قبرص"),
    "+420": ("CZ", "التشيك"),
    "+45": ("DK", "الدنمارك"),
    "+253": ("DJ", "جيبوتي"),
    "+1767": ("DM", "دومينيكا"),
    "+1809": ("DO", "الدومينيكان"),
    "+593": ("EC", "الإكوادور"),
    "+20": ("EG", "مصر"),
    "+503": ("SV", "السلفادور"),
    "+240": ("GQ", "غينيا الاستوائية"),
    "+291": ("ER", "إريتريا"),
    "+372": ("EE", "إستونيا"),
    "+251": ("ET", "إثيوبيا"),
    "+500": ("FK", "جزر فوكلاند"),
    "+298": ("FO", "جزر فارو"),
    "+679": ("FJ", "فيجي"),
    "+358": ("FI", "فنلندا"),
    "+33": ("FR", "فرنسا"),
    "+594": ("GF", "غيانا الفرنسية"),
    "+689": ("PF", "بولينيزيا الفرنسية"),
    "+241": ("GA", "الغابون"),
    "+220": ("GM", "غامبيا"),
    "+995": ("GE", "جورجيا"),
    "+49": ("DE", "ألمانيا"),
    "+233": ("GH", "غانا"),
    "+350": ("GI", "جبل طارق"),
    "+30": ("GR", "اليونان"),
    "+299": ("GL", "غرينلاند"),
    "+1473": ("GD", "غرينادا"),
    "+590": ("GP", "غوادلوب"),
    "+1671": ("GU", "غوام"),
    "+502": ("GT", "غواتيمالا"),
    "+224": ("GN", "غينيا"),
    "+245": ("GW", "غينيا بيساو"),
    "+592": ("GY", "غيانا"),
    "+509": ("HT", "هايتي"),
    "+504": ("HN", "هندوراس"),
    "+852": ("HK", "هونغ كونغ"),
    "+36": ("HU", "هنغاريا"),
    "+354": ("IS", "آيسلندا"),
    "+91": ("IN", "الهند"),
    "+62": ("ID", "إندونيسيا"),
    "+98": ("IR", "إيران"),
    "+964": ("IQ", "العراق"),
    "+353": ("IE", "أيرلندا"),
    "+972": ("IL", "إسرائيل"),
    "+39": ("IT", "إيطاليا"),
    "+1876": ("JM", "جامايكا"),
    "+81": ("JP", "اليابان"),
    "+962": ("JO", "الأردن"),
    "+7": ("RU", "روسيا"),
    "+254": ("KE", "كينيا"),
    "+686": ("KI", "كيريباتي"),
    "+965": ("KW", "الكويت"),
    "+996": ("KG", "قيرغيزستان"),
    "+856": ("LA", "لاوس"),
    "+371": ("LV", "لاتفيا"),
    "+961": ("LB", "لبنان"),
    "+266": ("LS", "ليسوتو"),
    "+231": ("LR", "ليبيريا"),
    "+218": ("LY", "ليبيا"),
    "+423": ("LI", "ليختنشتاين"),
    "+370": ("LT", "ليتوانيا"),
    "+352": ("LU", "لوكسمبورغ"),
    "+853": ("MO", "ماكاو"),
    "+389": ("MK", "مقدونيا"),
    "+261": ("MG", "مدغشقر"),
    "+265": ("MW", "مالاوي"),
    "+60": ("MY", "ماليزيا"),
    "+960": ("MV", "المالديف"),
    "+223": ("ML", "مالي"),
    "+356": ("MT", "مالطا"),
    "+692": ("MH", "جزر مارشال"),
    "+596": ("MQ", "مارتينيك"),
    "+222": ("MR", "موريتانيا"),
    "+230": ("MU", "موريشيوس"),
    "+262": ("YT", "مايوت"),
    "+52": ("MX", "المكسيك"),
    "+691": ("FM", "ميكرونيزيا"),
    "+373": ("MD", "مولدوفا"),
    "+377": ("MC", "موناكو"),
    "+976": ("MN", "منغوليا"),
    "+382": ("ME", "الجبل الأسود"),
    "+1664": ("MS", "مونتسيرات"),
    "+212": ("MA", "المغرب"),
    "+258": ("MZ", "موزمبيق"),
    "+95": ("MM", "ميانمار"),
    "+264": ("NA", "ناميبيا"),
    "+674": ("NR", "ناورو"),
    "+977": ("NP", "نيبال"),
    "+31": ("NL", "هولندا"),
    "+687": ("NC", "كاليدونيا الجديدة"),
    "+64": ("NZ", "نيوزيلندا"),
    "+505": ("NI", "نيكاراغوا"),
    "+227": ("NE", "النيجر"),
    "+234": ("NG", "نيجيريا"),
    "+683": ("NU", "نييوي"),
    "+850": ("KP", "كوريا الشمالية"),
    "+1670": ("MP", "جزر ماريانا"),
    "+47": ("NO", "النرويج"),
    "+968": ("OM", "عُمان"),
    "+92": ("PK", "باكستان"),
    "+680": ("PW", "بالاو"),
    "+970": ("PS", "فلسطين"),
    "+507": ("PA", "بنما"),
    "+675": ("PG", "بابوا غينيا الجديدة"),
    "+595": ("PY", "باراغواي"),
    "+51": ("PE", "بيرو"),
    "+63": ("PH", "الفلبين"),
    "+48": ("PL", "بولندا"),
    "+351": ("PT", "البرتغال"),
    "+1787": ("PR", "بورتوريكو"),
    "+974": ("QA", "قطر"),
    "+262": ("RE", "ريونيون"),
    "+40": ("RO", "رومانيا"),
    "+966": ("SA", "السعودية"),
    "+221": ("SN", "السنغال"),
    "+381": ("RS", "صربيا"),
    "+248": ("SC", "سيشل"),
    "+232": ("SL", "سيراليون"),
    "+65": ("SG", "سنغافورة"),
    "+421": ("SK", "سلوفاكيا"),
    "+386": ("SI", "سلوفينيا"),
    "+677": ("SB", "جزر سليمان"),
    "+252": ("SO", "الصومال"),
    "+27": ("ZA", "جنوب أفريقيا"),
    "+82": ("KR", "كوريا الجنوبية"),
    "+211": ("SS", "جنوب السودان"),
    "+34": ("ES", "إسبانيا"),
    "+94": ("LK", "سريلانكا"),
    "+249": ("SD", "السودان"),
    "+597": ("SR", "سورينام"),
    "+268": ("SZ", "سوازيلاند"),
    "+46": ("SE", "السويد"),
    "+41": ("CH", "سويسرا"),
    "+963": ("SY", "سوريا"),
    "+886": ("TW", "تايوان"),
    "+992": ("TJ", "طاجيكستان"),
    "+255": ("TZ", "تنزانيا"),
    "+66": ("TH", "تايلاند"),
    "+670": ("TL", "تيمور الشرقية"),
    "+228": ("TG", "توغو"),
    "+690": ("TK", "توكيلاو"),
    "+676": ("TO", "تونغا"),
    "+1868": ("TT", "ترينيداد وتوباغو"),
    "+216": ("TN", "تونس"),
    "+90": ("TR", "تركيا"),
    "+993": ("TM", "تركمانستان"),
    "+1649": ("TC", "جزر تركس وكايكوس"),
    "+688": ("TV", "توفالو"),
    "+256": ("UG", "أوغندا"),
    "+380": ("UA", "أوكرانيا"),
    "+971": ("AE", "الإمارات"),
    "+44": ("GB", "بريطانيا"),
    "+598": ("UY", "أوروغواي"),
    "+998": ("UZ", "أوزبكستان"),
    "+678": ("VU", "فانواتو"),
    "+379": ("VA", "الفاتيكان"),
    "+58": ("VE", "فنزويلا"),
    "+84": ("VN", "فيتنام"),
    "+1284": ("VI", "جزر العذراء الأمريكية"),
    "+681": ("WF", "واليس وفوتونا"),
    "+967": ("YE", "اليمن"),
    "+260": ("ZM", "زامبيا"),
    "+263": ("ZW", "زيمبابوي"),
}


def iso_flag(iso):
    """تحويل رمز ISO إلى إيموجي علم"""
    if not iso or len(iso) != 2:
        return "🏳"
    return chr(0x1F1E6 + ord(iso[0].upper()) - ord("A")) + chr(0x1F1E6 + ord(iso[1].upper()) - ord("A"))


def detect_country(phone):
    """كشف الدولة من رقم الهاتف"""
    p = str(phone or "").strip().replace(" ", "").replace("-", "")
    if not p.startswith("+"):
        if p.startswith("00"):
            p = "+" + p[2:]
        elif p and p[0].isdigit():
            p = "+" + p
    for code in sorted(COUNTRIES.keys(), key=lambda x: -len(x)):
        if p.startswith(code):
            iso, name = COUNTRIES[code]
            return iso_flag(iso), name, code
    return "🏳", "غير معروف", ""


# ============================================================
# 10 منصات
# ============================================================
PLATFORMS = [
    ("واتساب", "🟢"),
    ("تيليجرام", "🔵"),
    ("فيسبوك", "🔷"),
    ("انستقرام", "🟣"),
    ("تويتر", "🔶"),
    ("جوجل", "🔴"),
    ("آبل", "⚫"),
    ("تيك توك", "⚫"),
    ("ديسكورد", "🟪"),
    ("سناب", "🟡"),
]

PLATFORM_ICONS = {p[0]: p[1] for p in PLATFORMS}


# ============================================================
# دوال المستخدمين
# ============================================================

def user_stats_get(uid):
    conn = db()
    row = conn.execute("SELECT total_codes, total_price FROM user_stats WHERE telegram_id=?", (uid,)).fetchone()
    conn.close()
    if row:
        return row["total_codes"], row["total_price"]
    return 0, 0.0

def user_stats_add(uid, price=1.0):
    conn = db()
    conn.execute("INSERT OR IGNORE INTO user_stats (telegram_id, total_codes, total_price) VALUES (?, 0, 0.0)", (uid,))
    conn.execute("UPDATE user_stats SET total_codes = total_codes + 1, total_price = total_price + ? WHERE telegram_id=?", (price, uid))
    conn.commit()
    conn.close()

def user_get(uid):
    conn = db()
    row = conn.execute("SELECT * FROM users WHERE telegram_id=?", (uid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def user_register(uid, username="", display_name="", password=""):
    conn = db()
    existing = conn.execute("SELECT telegram_id FROM users WHERE telegram_id=?", (uid,)).fetchone()
    if existing:
        conn.execute("UPDATE users SET username=?, display_name=?, last_login=? WHERE telegram_id=?",
                     (username, display_name, time.time(), uid))
    else:
        ph = hashlib.sha256(("otp_salt_" + str(password)).encode()).hexdigest()
        conn.execute("""
            INSERT INTO users (telegram_id, username, display_name, password_hash, created, last_login)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (uid, username, display_name, ph, time.time(), time.time()))
    conn.commit()
    conn.close()


def user_is_admin(uid):
    if int(uid) == int(MAIN_ADMIN_ID):
        return True
    conn = db()
    row = conn.execute("SELECT telegram_id FROM admins WHERE telegram_id=?", (uid,)).fetchone()
    conn.close()
    return row is not None


def user_ban(uid, val=1):
    conn = db()
    conn.execute("UPDATE users SET is_banned=? WHERE telegram_id=?", (val, uid))
    conn.commit()
    conn.close()


def users_count():
    conn = db()
    n = conn.execute("SELECT COUNT(*) as n FROM users").fetchone()["n"]
    conn.close()
    return n


def users_all(limit=50):
    conn = db()
    rows = conn.execute("SELECT * FROM users ORDER BY created DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# دوال الأرقام
# ============================================================
def numbers_platforms():
    conn = db()
    rows = conn.execute("SELECT DISTINCT platform FROM numbers ORDER BY platform").fetchall()
    conn.close()
    platforms = []
    for r in rows:
        # نشيل (Panel:...) من الاسم
        name = str(r["platform"])
        if "(Panel:" in name:
            name = name.split("(Panel:")[0].strip()
        if name not in platforms:
            platforms.append(name)
    return platforms


def numbers_countries(platform):
    conn = db()
    rows = conn.execute("SELECT DISTINCT country FROM numbers WHERE platform LIKE ? ORDER BY country", (platform + "%",)).fetchall()
    conn.close()
    return [r["country"] for r in rows]


def numbers_list(platform=None, country=None, limit=None):
    conn = db()
    q = "SELECT * FROM numbers WHERE 1=1"
    params = []
    if platform:
        # نبحث عن أي اسم منصة يحتوي على الكلمة دي (عشان يلاقي Panel:9)
        q += " AND platform LIKE ?"
        params.append(platform + "%")
    if country:
        q += " AND country=?"
        params.append(country)
    q += " ORDER BY id DESC"
    if limit:
        q += " LIMIT ?"
        params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def number_add(platform, country, phone):
    conn = db()
    conn.execute("INSERT INTO numbers (platform, country, phone, added_at) VALUES (?, ?, ?, ?)",
                 (platform, country, phone, time.time()))
    conn.commit()
    conn.close()


def number_delete(nid):
    conn = db()
    conn.execute("DELETE FROM numbers WHERE id=?", (nid,))
    conn.commit()
    conn.close()


def numbers_count():
    conn = db()
    n = conn.execute("SELECT COUNT(*) as n FROM numbers").fetchone()["n"]
    conn.close()
    return n


# ============================================================
# دوال الأكواد
# ============================================================
def code_add(phone, code, platform="", country="", message=""):
    if not phone or not code:
        return False
    conn = db()
    now = time.time()
    existing = conn.execute(
        "SELECT id FROM codes WHERE phone=? AND code=? AND received_at>?",
        (phone, code, now - 600)
    ).fetchone()
    if existing:
        conn.close()
        return False
    conn.execute("""
        INSERT INTO codes (phone, code, platform, country, message, received_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (phone, code, platform, country, message, now, now + 300))
    conn.execute("DELETE FROM codes WHERE id NOT IN (SELECT id FROM codes ORDER BY received_at DESC LIMIT ?)",
                 (12,))
    conn.commit()
    conn.close()
    return True


def codes_list(limit=50, platform=None):
    conn = db()
    if platform:
        rows = conn.execute("SELECT * FROM codes WHERE platform=? ORDER BY received_at DESC LIMIT ?",
                            (platform, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM codes ORDER BY received_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def code_get(cid):
    conn = db()
    row = conn.execute("SELECT * FROM codes WHERE id=?", (cid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def code_delete(cid):
    conn = db()
    conn.execute("DELETE FROM codes WHERE id=?", (cid,))
    conn.commit()
    conn.close()


def codes_clear():
    conn = db()
    conn.execute("DELETE FROM codes")
    conn.commit()
    conn.close()


def codes_count():
    conn = db()
    n = conn.execute("SELECT COUNT(*) as n FROM codes").fetchone()["n"]
    conn.close()
    return n


# ============================================================
# دوال اللوحات
# ============================================================
def panels_list(only_enabled=False):
    conn = db()
    if only_enabled:
        rows = conn.execute("SELECT * FROM external_apis WHERE enabled=1 ORDER BY id").fetchall()
    else:
        rows = conn.execute("SELECT * FROM external_apis ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def panel_get(pid):
    conn = db()
    row = conn.execute("SELECT * FROM external_apis WHERE id=?", (pid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def panel_add(name, url, token="", username="", password="", auth_type="token",
              api_path="", api_method="GET", json_path="",
              field_phone="", field_code="", field_platform="", field_country="", field_message="",
              interval_sec=60, custom_headers="[]", custom_query="[]", body_json=""):
    conn = db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO external_apis (
            name, url, token, username, password, auth_type,
            api_path, api_method, json_path,
            field_phone, field_code, field_platform, field_country, field_message,
            interval_sec, custom_headers, custom_query, body_json, created, updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, url, token, username, password, auth_type,
          api_path, api_method, json_path,
          field_phone, field_code, field_platform, field_country, field_message,
          interval_sec, custom_headers, custom_query, body_json,
          time.time(), time.time()))
    pid = c.lastrowid
    conn.commit()
    conn.close()
    return pid


def panel_update(pid, **fields):
    allowed = {"name", "url", "token", "username", "password", "auth_type", "enabled",
               "smart_bind", "auto_push", "interval_sec", "last_fetch", "last_count",
               "last_status", "last_error", "api_path", "api_method", "json_path",
               "field_phone", "field_code", "field_platform", "field_country", "field_message",
               "custom_headers", "custom_query", "body_json", "fail_count"}
    sets = []
    vals = []
    for k, v in fields.items():
        if k in allowed:
            sets.append(k + "=?")
            vals.append(v)
    if not sets:
        return False
    sets.append("updated=?")
    vals.append(time.time())
    vals.append(pid)
    conn = db()
    conn.execute("UPDATE external_apis SET " + ", ".join(sets) + " WHERE id=?", vals)
    conn.commit()
    conn.close()
    return True


def panel_delete(pid):
    conn = db()
    conn.execute("DELETE FROM external_apis WHERE id=?", (pid,))
    conn.commit()
    conn.close()


def panel_toggle(pid):
    p = panel_get(pid)
    if not p:
        return
    panel_update(pid, enabled=0 if p.get("enabled") else 1)


# ============================================================
# بناء الهيدرز للوحات
# ============================================================
def build_headers(panel):
    h = {"Accept": "application/json", "User-Agent": "AlmatariBot/1.0"}
    auth = (panel.get("auth_type") or "token").lower()
    token = (panel.get("token") or "").strip()
    username = (panel.get("username") or "").strip()
    password = (panel.get("password") or "")

    if auth == "token" and token:
        h["X-API-Token"] = token
        h["Authorization"] = "Bearer " + token
    elif auth == "basic" and username:
        creds = base64.b64encode((username + ":" + password).encode()).decode()
        h["Authorization"] = "Basic " + creds
    elif auth == "both":
        if token:
            h["X-API-Token"] = token
            h["Authorization"] = "Bearer " + token
        if username:
            creds = base64.b64encode((username + ":" + password).encode()).decode()
            h["Authorization"] = "Basic " + creds
    elif auth == "custom":
        try:
            items = json.loads(panel.get("custom_headers") or "[]")
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict):
                        n = (it.get("name") or "").strip()
                        v = str(it.get("value") or "")
                        if n:
                            h[n] = v
        except Exception:
            pass
    return h


def extract_codes(data, panel=None):
    if not data:
        return []
    if panel:
        jp = (panel.get("json_path") or "").strip()
        if jp:
            parts = [p for p in jp.split(".") if p]
            node = data
            for p in parts:
                if isinstance(node, dict) and p in node:
                    node = node[p]
                elif isinstance(node, list) and p.isdigit() and int(p) < len(node):
                    node = node[int(p)]
                else:
                    node = None
                    break
            if isinstance(node, list):
                return node
            if isinstance(node, dict):
                return [node]
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ("codes", "data", "messages", "items", "results", "sms", "list"):
            v = data.get(k)
            if isinstance(v, list):
                return v
            if isinstance(v, dict):
                for k2 in ("items", "list", "data", "codes", "results"):
                    v2 = v.get(k2)
                    if isinstance(v2, list):
                        return v2
        if any(k in data for k in ("code", "otp", "otp_code")):
            return [data]
    return []


def fetch_panel(panel, limit=50):
    base = (panel.get("url") or "").rstrip("/")
    if not base:
        return False, [], "URL فارغ"
    headers = build_headers(panel)
    custom_path = (panel.get("api_path") or "").strip()
    if custom_path:
        if not custom_path.startswith("/"):
            custom_path = "/" + custom_path
        paths = [custom_path]
    else:
        paths = ["/api/v1/codes", "/api/codes", "/codes"]

    method = (panel.get("api_method") or "GET").upper()
    body = None
    if method == "POST":
        try:
            body = json.loads(panel.get("body_json") or "{}")
        except Exception:
            body = {"limit": limit}
        headers["Content-Type"] = "application/json"

    qparams = {}
    try:
        for q in json.loads(panel.get("custom_query") or "[]"):
            if isinstance(q, dict) and q.get("name"):
                qparams[str(q["name"])] = str(q.get("value", ""))
    except Exception:
        pass

    last_err = ""
    for path in paths:
        try:
            url = base + path
            if method == "GET":
                r = requests.get(url, headers=headers, params=dict({"limit": limit}, **qparams), timeout=15)
            else:
                r = requests.post(url, headers=headers, params=qparams or None, json=body, timeout=15)
            if r.status_code in (401, 403):
                return False, [], "HTTP %d — التوكن أو الصلاحية غير صحيحة" % r.status_code
            if r.status_code == 429:
                return False, [], "HTTP 429 — تجاوز حد الطلبات"
            if r.status_code >= 400:
                last_err = "HTTP %d" % r.status_code
                continue
            raw = r.text
            try:
                data = json.loads(raw)
            except Exception:
                last_err = "رد غير JSON: " + raw[:80]
                continue
            codes = extract_codes(data, panel)
            return True, codes, ""
        except requests.exceptions.Timeout:
            last_err = "انتهت المدة"
        except Exception as e:
            last_err = type(e).__name__ + ": " + str(e)[:100]
    return False, [], last_err



# ============================================================
# معلومات الحساب من اللوحة (/api/v1/me)
# ============================================================
def fetch_account_info(panel):
    """يجيب معلومات الحساب من اللوحة"""
    base = (panel.get("url") or "").rstrip("/")
    if not base:
        return None
    headers = build_headers(panel)
    paths = ["/api/v1/me", "/api/me", "/me"]
    for path in paths:
        try:
            r = requests.get(base + path, headers=headers, timeout=10)
            data = r.json()
            if isinstance(data, dict):
                if "data" in data and isinstance(data["data"], dict):
                    return data["data"]
                if "balance" in data or "username" in data:
                    return data
        except Exception:
            continue
    return None


def format_account_box(account, panel_name=""):
    """يشكل صندوق معلومات الحساب"""
    if not account:
        return ""
    lines = []
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append("📊 <b>معلومات الحساب</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━")

    username = account.get("username") or account.get("name") or ""
    if username:
        lines.append("👤 الاسم: <code>" + str(username) + "</code>")

    full_name = account.get("full_name") or account.get("fullname") or ""
    if full_name and full_name != username:
        lines.append("📝 الاسم الكامل: " + str(full_name))

    balance = account.get("balance")
    if balance is not None:
        cur = account.get("currency", "")
        lines.append("💰 الرصيد: <b>" + str(balance) + " " + str(cur) + "</b>")

    total_codes = account.get("total_codes") or account.get("codes_count") or account.get("total")
    if total_codes is not None:
        lines.append("📊 إجمالي الأكواد: <b>" + str(total_codes) + "</b>")

    today_codes = account.get("today_codes") or account.get("daily_codes")
    if today_codes is not None:
        lines.append("📅 أكواد اليوم: <b>" + str(today_codes) + "</b>")

    role = account.get("role") or account.get("type")
    if role:
        lines.append("🎭 الدور: <b>" + str(role) + "</b>")

    is_active = account.get("is_active")
    if is_active is not None:
        lines.append("🟢 الحالة: " + ("✅ مفعّل" if is_active else "🚫 موقوف"))

    is_banned = account.get("is_banned") or account.get("banned")
    if is_banned:
        lines.append("🚫 <b>محظور!</b>")

    created_at = account.get("created_at") or account.get("created")
    if created_at:
        lines.append("📅 تاريخ الإنشاء: " + str(created_at)[:19])

    last_login = account.get("last_login") or account.get("last_seen")
    if last_login:
        lines.append("🕐 آخر دخول: " + str(last_login)[:19])

    lines.append("━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)


def test_panel(pid):
    p = panel_get(pid)
    if not p:
        return {"ok": False, "error": "غير موجودة"}
    ok, codes, err = fetch_panel(p, limit=5)
    result = {"ok": ok, "name": p.get("name"), "count": len(codes) if codes else 0, "error": err}
    if ok:
        panel_update(pid, last_fetch=time.time(), last_count=len(codes) if codes else 0,
                     last_status="ok", last_error="", fail_count=0)
    else:
        fail = (p.get("fail_count") or 0) + 1
        panel_update(pid, last_fetch=time.time(), last_status="error",
                     last_error=err[:200], fail_count=fail)
    return result



# ============================================================
# Poller تلقائي
# ============================================================
POLLER_STATE = {"running": False, "cycles": 0}



# ============================================================
# 🩺 API Guard — صحة الـ APIs + إعادة محاولة ذكية + تنبيهات
# ============================================================
AG_MAX_DELAY = 900   # أقصى فاصل بين محاولات API متعثر (15 دقيقة)
AG_DOWN_AFTER = 3    # بعد كم فشل متتالٍ نعتبره متعثرًا وننبّه الأدمن
AG_READY = {"ok": False}



def _dig(item, path):
    """قيمة من dict/list بمسار منقّط مثل data.phone"""
    node = item
    for part in str(path).split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            return ""
    return "" if node in (None, "", [], {}) else str(node)


def _pick(item, keys, own=None):
    """يقرأ أول مفتاح موجود من item: اسم الحقل الخاص باللوحة (own) أولًا ثم المفاتيح البديلة"""
    if not isinstance(item, dict):
        return ""
    if own:
        v = _dig(item, own)
        if v:
            return v
    for k in keys:
        v = item.get(k)
        if v not in (None, "", [], {}):
            return str(v)
    low = {str(k).lower(): v for k, v in item.items()}
    for k in keys:
        v = low.get(str(k).lower())
        if v not in (None, "", [], {}):
            return str(v)
    return ""


def _flag_from(v):
    v = str(v or "").strip()
    if len(v) == 2 and v.isalpha() and v.isascii():
        return "".join(chr(0x1F1E6 + ord(ch) - 65) for ch in v.upper())
    if v and not v.isascii() and len(v) <= 8:
        return v
    return ""


PHONE_KEYS = ("phone_number", "phone", "number", "msisdn", "to", "recipient", "num", "mobile", "receiver")
CODE_KEYS = ("otp_code", "code", "otp", "sms_code", "pin", "verification_code", "verify_code")
MSG_KEYS = ("message_text", "message", "sms", "text", "body", "msg", "content", "sms_text")
PLATFORM_KEYS = ("app_name", "platform", "service", "app", "sender", "brand", "cli", "service_name", "provider")
FLAG_KEYS = ("flag", "country_flag", "emoji")
COUNTRY_KEYS = ("country_name", "country", "countryName")


def process_panel_codes(panel, codes):
    """يقرأ الأكواد من أي لوحة (حسب حقولها الخاصة ثم المفاتيح البديلة) ويرسلها للقناة. يرجع عدد الجديد"""
    if not codes:
        return 0
    forward_id = setting_get("forward_channel_id", "")
    seed_key = "panel_seeded_" + str(panel.get("id"))
    first_run = not setting_get(seed_key, "")
    if first_run:
        setting_set(seed_key, "1")

    n = 0
    to_send = []
    for item in codes:
        try:
            # فحص تاريخ الكود (إذا كان قديماً جداً، نتخطاه)
            if isinstance(item, dict):
                # محاولة قراءة أي حقل يحتوي على وقت
                t_str = str(item.get('time') or item.get('created_at') or item.get('timestamp') or item.get('date') or '')
                # إذا كان هناك تاريخ (مثل 2023-10-19 10:00:00)
                if t_str and len(t_str) > 10:
                    try:
                        from datetime import datetime
                        # نحاول قراءة التاريخ
                        t_parsed = datetime.strptime(t_str[:19], "%Y-%m-%d %H:%M:%S")
                        # إذا مر على الكود أكثر من 5 دقائق، تجاهله
                        if (time.time() - t_parsed.timestamp()) > 300:
                            continue
                    except Exception:
                        pass
            
            if isinstance(item, dict):
                phone = _pick(item, PHONE_KEYS, panel.get("field_phone"))
                code = _pick(item, CODE_KEYS, panel.get("field_code"))
                msg_text = _pick(item, MSG_KEYS, panel.get("field_message"))
                platform = _pick(item, PLATFORM_KEYS, panel.get("field_platform"))
                api_flag = _flag_from(_pick(item, FLAG_KEYS))
                api_country = _pick(item, COUNTRY_KEYS, panel.get("field_country"))
            else:
                phone, code, platform, api_flag, api_country = "", "", "", "", ""
                msg_text = str(item)
            if not code and msg_text:
                code = (parse_otp(msg_text) or {}).get("code") or ""
            if not code:
                continue
            masked_in = ("•" in phone) or ("*" in phone)
            phone_clean = re.sub(r"\D", "", phone) or "0"
            flag, cname, _cc = detect_country(phone_clean)
            flag = api_flag or flag
            cname = api_country or cname
            if code_add(phone_clean, code, platform, cname, msg_text[:500]):
                n += 1
                to_send.append((flag, phone if masked_in else phone_clean, msg_text, code, platform, cname))
        except Exception as e:
            print("[PROCESS] item err:", e)

    if forward_id and to_send:
        support_link = setting_get("channel_link", "https://t.me/")
        bot_link = "https://t.me/" + get_bot_username()
        admin_link = setting_get("admin_link", "") or ("tg://user?id=" + str(MAIN_ADMIN_ID))
        batch = list(reversed(to_send))
        batch = batch[-5:] if first_run else batch[:15]
        for flag, phone_disp, msg_text, code, platform, cname in batch:
            try:
                lang = "en" if (msg_text and msg_text.isascii()) else "ar"
                send_otp_message(forward_id, flag, phone_disp, lang, msg_text, code, support_link, bot_link,
                                 admin_link, panel_name=panel.get("name") or "MATRUI_OTP",
                                 platform=platform, country_name=cname)
                
                # === إرسال إشعار للمستخدمين الذين يفتحون الأرقام ===
                now_ts = time.time()
                for user_id, watching in list(WATCHING_USERS.items()):
                    # التحقق الدقيق: الرقم موجود + المنصة مطابقة + الدولة مطابقة
                    clean_phone = phone_disp.replace("+", "").strip()
                    if ("current_numbers" in watching and 
                        clean_phone in watching["current_numbers"] and
                        str(watching.get("platform")).strip() == str(platform).strip() and
                        str(watching.get("country")).strip() == str(cname).strip()):
                        if (now_ts - watching.get("last_time", 0)) < 600:
                            try:
                                # تصميم الإشعار المختصر النهائي
                                flag_icon, _, _cc = detect_country(phone_disp)
                                iso_code = COUNTRIES.get(_cc, ("", ""))[0] or "XX"
                                
                                # --- تصميم الإشعار الداخلي الفخم (مطابق للقناة) ---
                                flag_icon, _, _cc = detect_country(phone_disp)
                                iso_code = COUNTRIES.get(_cc, ("", ""))[0] or "XX"
                                
                                _pcodes = {"WhatsApp":"WH","Telegram":"TG","Facebook":"FB","Instagram":"IG",
                                           "Twitter":"TW","Google":"GG","Apple":"AP","TikTok":"TT",
                                           "Discord":"DC","Snapchat":"SC"}
                                short_pname = _pcodes.get(str(platform).strip(), str(platform)[:2].upper())
                                
                                # --- تصميم الإشعار الداخلي الفخم (مصحح) ---
                                flag_icon, _, _cc = detect_country(phone_disp)
                                iso_code = COUNTRIES.get(_cc, ("", ""))[0] or "XX"
                                
                                _pcodes = {"WhatsApp":"WH","Telegram":"TG","Facebook":"FB","Instagram":"IG",
                                           "Twitter":"TW","Google":"GG","Apple":"AP","TikTok":"TT",
                                           "Discord":"DC","Snapchat":"SC"}
                                short_pname = _pcodes.get(str(platform).strip(), str(platform)[:2].upper())
                                
                                # --- تصميم الإشعار الداخلي الفخم (مطابق للقناة) ---
                                flag_icon, _, _cc = detect_country(phone_disp)
                                iso_code = COUNTRIES.get(_cc, ("", ""))[0] or "XX"
                                
                                _pcodes = {"WhatsApp":"WH","Telegram":"TG","Facebook":"FB","Instagram":"IG",
                                           "Twitter":"TW","Google":"GG","Apple":"AP","TikTok":"TT",
                                           "Discord":"DC","Snapchat":"SC"}
                                short_pname = _pcodes.get(str(platform).strip(), str(platform)[:2].upper())
                                
                                # --- تصميم الإشعار الداخلي الفخم (مطابق للقناة) ---
                                flag_icon, _, _cc = detect_country(phone_disp)
                                iso_code = COUNTRIES.get(_cc, ("", ""))[0] or "XX"
                                
                                _pcodes = {"WhatsApp":"WH","Telegram":"TG","Facebook":"FB","Instagram":"IG",
                                           "Twitter":"TW","Google":"GG","Apple":"AP","TikTok":"TT",
                                           "Discord":"DC","Snapchat":"SC"}
                                short_pname = _pcodes.get(str(platform).strip(), str(platform)[:2].upper())
                                
                                # --- بناء الإشعار الداخلي بنفس دالة القناة ---
                                safe_sms_inner = html.escape(msg_text) if msg_text else ""
                                notify_text = otp_render("quote", flag, phone_disp, "ar", safe_sms_inner, code, msg_text, 
                                                         panel_name=panel.get("name") or "MATRUI_OTP", 
                                                         platform=platform, country_name=cname)
                                
                                kb = InlineKeyboardMarkup()
                                # زر الكود الأخضر (قابل للنسخ)
                                btn_code = _kb_btn(str(code), copy_text=str(code))
                                if btn_code:
                                    kb.row(btn_code)
                                
                                # أزرار الجروب
                                group_link = setting_get("channel_link", "")
                                if _valid_url(group_link):
                                    btn_group = _kb_btn("🔑 جروب البوت", url=group_link)
                                    if btn_group:
                                        kb.row(btn_group)
                                
                                bot.send_message(user_id, notify_text, reply_markup=kb)
                                
                                # تحديث عدد الأكواد للمستخدم
                                try:
                                    conn = db()
                                    conn.execute("INSERT OR IGNORE INTO user_stats (telegram_id, total_codes) VALUES (?, 0)", (user_id,))
                                    conn.execute("UPDATE user_stats SET total_codes = total_codes + 1 WHERE telegram_id=?", (user_id,))
                                    conn.commit()
                                    conn.close()
                                except Exception:
                                    pass
                            except Exception:
                                pass
                            break # نرسل مرة واحدة فقط

                # ==================================================
                time.sleep(0.6)
            except Exception as e:
                print("[PROCESS] send err:", e)
    return n


def ag_init():
    conn = db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_health (
            panel_id INTEGER PRIMARY KEY,
            fail_streak INTEGER DEFAULT 0,
            next_retry REAL DEFAULT 0,
            last_ok REAL DEFAULT 0,
            latency_ms INTEGER DEFAULT 0,
            last_error TEXT DEFAULT '',
            notified_down INTEGER DEFAULT 0,
            total_ok INTEGER DEFAULT 0,
            total_fail INTEGER DEFAULT 0,
            total_codes INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    AG_READY["ok"] = True


def ag_get(pid):
    if not AG_READY["ok"]:
        ag_init()
    conn = db()
    row = conn.execute("SELECT * FROM api_health WHERE panel_id=?", (pid,)).fetchone()
    conn.close()
    h = {"panel_id": pid, "fail_streak": 0, "next_retry": 0.0, "last_ok": 0.0,
         "latency_ms": 0, "last_error": "", "notified_down": 0,
         "total_ok": 0, "total_fail": 0, "total_codes": 0}
    if row:
        h.update(dict(row))
    for k in ("fail_streak", "notified_down", "total_ok", "total_fail", "total_codes", "latency_ms"):
        h[k] = int(h.get(k) or 0)
    for k in ("next_retry", "last_ok"):
        h[k] = float(h.get(k) or 0)
    return h


def ag_save(pid, **fields):
    if not AG_READY["ok"]:
        ag_init()
    allowed = {"fail_streak", "next_retry", "last_ok", "latency_ms", "last_error",
               "notified_down", "total_ok", "total_fail", "total_codes"}
    sets, vals = [], []
    for k, v in fields.items():
        if k in allowed:
            sets.append(k + "=?")
            vals.append(v)
    if not sets:
        return
    vals.append(pid)
    conn = db()
    conn.execute("INSERT OR IGNORE INTO api_health (panel_id) VALUES (?)", (pid,))
    conn.execute("UPDATE api_health SET " + ", ".join(sets) + " WHERE panel_id=?", vals)
    conn.commit()
    conn.close()


def ag_delay(interval, streak):
    """فاصل المحاولة التالية: يتضاعف مع كل فشل حتى 15 دقيقة، ولا يتوقف أبدًا"""
    return min(AG_MAX_DELAY, max(int(interval), 30) * (2 ** min(int(streak), 6)))


def ag_dur(sec):
    sec = int(max(0, sec))
    if sec < 60:
        return str(sec) + "ث"
    if sec < 3600:
        return str(sec // 60) + "د"
    if sec < 86400:
        return str(sec // 3600) + "س"
    return str(sec // 86400) + "ي"


def ag_notify(text):
    ids = {MAIN_ADMIN_ID}
    try:
        conn = db()
        for r in conn.execute("SELECT telegram_id FROM admins").fetchall():
            ids.add(r[0])
        conn.close()
    except Exception:
        pass
    for i in ids:
        try:
            bot.send_message(i, text)
        except Exception as e:
            print("[AG] notify err:", e)


def _ag_one(p, limit=50):
    t0 = time.time()
    try:
        ok, codes, err = fetch_panel(p, limit=limit)
    except Exception as e:
        ok, codes, err = False, [], type(e).__name__ + ": " + str(e)[:100]
    return (p, ok, codes or [], err or "", int((time.time() - t0) * 1000))


def ag_fetch_many(panels, limit=50):
    """يسحب من كل الـ APIs بالتوازي حتى لا يعطّل بطيءٌ غيرَه"""
    if not panels:
        return []
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max(1, min(6, len(panels)))) as ex:
        return list(ex.map(lambda q: _ag_one(q, limit), panels))


def ag_apply(p, ok, codes, err, ms, now):
    pid = p["id"]
    name = html.escape(str(p.get("name") or "?"))
    h = ag_get(pid)
    try:
        iv = max(10, int(float(p.get("interval_sec") or 60)))
    except (ValueError, TypeError):
        iv = 60
    if ok:
        n = 0
        try:
            n = process_panel_codes(p, codes) or 0
        except Exception as e:
            print("[AG] process err:", e)
        ag_save(pid, fail_streak=0, next_retry=0, last_ok=now, latency_ms=ms,
                last_error="", notified_down=0,
                total_ok=h["total_ok"] + 1, total_codes=h["total_codes"] + n)
        panel_update(pid, last_fetch=now, last_count=len(codes), last_status="ok",
                     last_error="", fail_count=0)
        if h["notified_down"]:
            ag_notify("✅ <b>عاد API للعمل</b>\n\n📡 " + name + "\n⏱ " + str(ms) + "ms\n"
                      "🔁 كان متعثرًا " + str(h["fail_streak"]) + " محاولة، واستُؤنف السحب تلقائيًا.")
        if n:
            print("[POLLER] " + str(p.get("name")) + " +" + str(n))
    else:
        streak = h["fail_streak"] + 1
        delay = ag_delay(iv, streak)
        ag_save(pid, fail_streak=streak, next_retry=now + delay, latency_ms=ms,
                last_error=err[:200], total_fail=h["total_fail"] + 1)
        panel_update(pid, last_fetch=now, last_status="error", last_error=err[:200],
                     fail_count=streak)
        if streak >= AG_DOWN_AFTER and not h["notified_down"]:
            ag_save(pid, notified_down=1)
            ag_notify("⛔ <b>API متعثر</b>\n\n📡 " + name + "\n❌ " + html.escape(err[:150]) + "\n"
                      "🔁 سأعيد المحاولة تلقائيًا كل فترة (التالية بعد " + ag_dur(delay) + ").\n"
                      "باقي الـ APIs تعمل بشكل طبيعي.")


def ag_cycle():
    """دورة واحدة: يحدد المستحق، يسحب بالتوازي، يطبّق النتائج. يرجع عدد ما سُحب"""
    now = time.time()
    due = []
    for p in panels_list(only_enabled=True):
        h = ag_get(p["id"])
        try:
            iv = max(10, int(float(p.get("interval_sec") or 60)))
        except (ValueError, TypeError):
            iv = 60
        if now < h["next_retry"]:
            continue
        try:
            last = float(p.get("last_fetch") or 0)
        except (ValueError, TypeError):
            last = 0.0
        if h["fail_streak"] == 0 and last and (now - last) < iv:
            continue
        due.append(p)
    for p, ok, codes, err, ms in ag_fetch_many(due):
        try:
            ag_apply(p, ok, codes, err, ms, now)
        except Exception as e:
            print("[AG] apply err:", e)
    return len(due)


POLLER_STATE = POLLER_STATE if "POLLER_STATE" in globals() else {"running": False, "cycles": 0}



def save_channel_message(chat_id, message_id):
    try:
        conn = db()
        conn.execute("INSERT INTO channel_messages (chat_id, message_id, created) VALUES (?, ?, ?)",
                     (str(chat_id), message_id, time.time()))
        conn.commit()
        conn.close()
    except Exception as e:
        print("[CLEAN] save err:", e)

def auto_delete_channel_messages():
    print("[CLEAN] Auto-delete thread started")
    while True:
        try:
            if setting_get("auto_delete_enabled", "0") == "1":
                mins = int(setting_get("auto_delete_mins", "3"))
                cutoff = time.time() - (mins * 60)
                
                conn = db()
                rows = conn.execute("SELECT id, chat_id, message_id FROM channel_messages WHERE created < ?", (cutoff,)).fetchall()
                
                for r in rows:
                    try:
                        bot.delete_message(r["chat_id"], r["message_id"])
                    except Exception:
                        pass # تجاهل الخطأ إذا كانت الرسالة محذوفة مسبقاً
                    conn.execute("DELETE FROM channel_messages WHERE id=?", (r["id"],))
                
                conn.commit()
                conn.close()
        except Exception as e:
            print("[CLEAN] err:", e)
        time.sleep(30) # فحص كل 30 ثانية


def poller_loop():
    print("[POLLER] started (API Guard)")
    POLLER_STATE["running"] = True
    while True:
        try:
            ag_cycle()
            POLLER_STATE["cycles"] += 1
        except Exception as e:
            print("[POLLER] err:", e)
        time.sleep(10)


# ============================================================
# البوت
# ============================================================


# ============================================================
# Flood Control + Logging
# ============================================================
FLOOD_DATA = {}
FLOOD_LIMIT = 5
FLOOD_WINDOW = 3


def check_flood(uid):
    """منع السبام"""
    now = time.time()
    if uid not in FLOOD_DATA:
        FLOOD_DATA[uid] = []
    FLOOD_DATA[uid] = [t for t in FLOOD_DATA[uid] if now - t < FLOOD_WINDOW]
    if len(FLOOD_DATA[uid]) >= FLOOD_LIMIT:
        return False
    FLOOD_DATA[uid].append(now)
    return True


def log_action(uid, action, details=""):
    """تسجيل العمليات"""
    try:
        with open("data/bot.log", "a", encoding="utf-8") as f:
            t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write("[" + t + "] uid=" + str(uid) + " | " + action + " | " + str(details)[:200] + "\n")
    except Exception:
        pass



# ============================================================
# تخصيص الأزرار
# ============================================================
_BTN_CACHE = {"data": {}, "loaded_at": 0}


def btn_config_load():
    now = time.time()
    if now - _BTN_CACHE["loaded_at"] < 5:
        return _BTN_CACHE["data"]
    try:
        conn = db()
        rows = conn.execute("SELECT * FROM button_config").fetchall()
        conn.close()
        d = {}
        for r in rows:
            d[r["key"]] = {
                "label_ar": r["label_ar"] or "",
                "label_en": r["label_en"] or "",
                "style": r["style"] or "",
                "icon": r["icon"] or "",
                "visible": r["visible"],
                "sort_order": r["sort_order"],
            }
        _BTN_CACHE["data"] = d
        _BTN_CACHE["loaded_at"] = now
        return d
    except Exception:
        return {}


def btn_config_get(key):
    d = btn_config_load()
    return d.get(key, {"label_ar": "", "label_en": "", "style": "", "icon": "", "visible": 1, "sort_order": 0})


def btn_config_set(key, **fields):
    allowed = {"label_ar", "label_en", "style", "icon", "visible", "sort_order"}
    sets = []
    vals = []
    for k, v in fields.items():
        if k in allowed:
            sets.append(k + "=?")
            vals.append(v)
    if not sets:
        return False
    vals.append(key)
    conn = db()
    conn.execute("UPDATE button_config SET " + ", ".join(sets) + " WHERE key=?", vals)
    conn.commit()
    conn.close()
    # إجبار الكاش على التحديث فوراً
    _BTN_CACHE["loaded_at"] = 0
    _BTN_CACHE["data"] = {}  # تفريغ الكاش بالكامل لإجبار إعادة القراءة
    return True


def btn_config_reset():
    defaults = [
        ("btn_platforms", "المنصات", "Platforms", "primary", "📱", 1, 10),
        ("btn_codes", "الأكواد", "Codes", "primary", "💬", 1, 20),
        ("btn_contests", "المسابقات", "Contests", "", "🎁", 1, 30),
        ("btn_ads", "الإعلانات", "Ads", "", "📢", 1, 40),
        ("btn_support", "الدعم", "Support", "", "💭", 1, 50),
        ("btn_me", "ملفي", "My Profile", "", "👤", 1, 60),
        ("btn_explore", "استكشف", "Explore", "", "🌐", 1, 70),
        ("btn_settings", "الإعدادات", "Settings", "", "⚙️", 1, 80),
        ("btn_admin", "لوحة الأدمن", "Admin Panel", "danger", "👮", 1, 90),
        ("btn_countries", "الدول", "Countries", "primary", "🌍", 1, 101),
        ("btn_numbers_list", "الأرقام", "Numbers", "primary", "☎️", 1, 102),
        ("btn_copy", "نسخ", "Copy", "success", "", 1, 100),
        ("btn_refresh", "تحديث OTP", "Refresh OTP", "success", "🔔", 1, 110),
        ("btn_switch", "تبديل", "Switch", "primary", "🔄", 1, 120),
        ("btn_back", "رجوع", "Back", "", "⬅️", 1, 130),
        ("btn_save", "حفظ", "Save", "success", "✅", 1, 140),
        ("btn_delete", "حذف", "Delete", "danger", "🗑", 1, 150),
        ("btn_add", "إضافة", "Add", "primary", "➕", 1, 160),
        ("btn_get_number", "الحصول على رقم", "Get Number", "primary", "🔓", 1, 5),
        ("btn_view_codes", "الأكواد الواصلة", "Received Codes", "success", "", 1, 15),
        ("btn_test", "فحص", "Test", "primary", "🔍", 1, 170),
        ("btn_fetch", "سحب فوري", "Fetch Now", "", "🔄", 1, 180),
    ]
    conn = db()
    conn.execute("DELETE FROM button_config")
    for k, ar, en, st, ic, vis, so in defaults:
        conn.execute("""
            INSERT INTO button_config (key, label_ar, label_en, style, icon, visible, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (k, ar, en, st, ic, vis, so))
    conn.commit()
    conn.close()
    _BTN_CACHE["loaded_at"] = 0







def btn(text, cb=None, style=None, url=None, key=None, uid=None):
    """زر مع دعم التخصيص + قراءة اللون من قاعدة البيانات"""
    # تلوين أزرار الرجوع بلون موحد من الإعدادات
    if "رجوع" in str(text) or "القائمة الرئيسية" in str(text) or "⬅️" in str(text) or "🏠" in str(text):
        style = "danger"
        
    if key:
        try:
            cfg = btn_config_get(key)
            if not cfg.get("visible", 1):
                return None
            
            text = bs_apply_cfg(text, cfg)

            # قراءة اللون من الداتابيز (الأولوية للون المحفوظ)
            db_style = cfg.get("style") or ""
            if db_style:
                style = db_style
        except Exception:
            pass
    else:
        # لو مفيش key، نحاول نجيب اللون من الداتابيز باستخدام الـ callback
        try:
            if cb:
                cfg = btn_config_get(cb)
                if not cfg.get("visible", 1):
                    return None
                text = bs_apply_cfg(text, cfg)
                if cfg.get("style"):
                    style = cfg.get("style")
        except Exception:
            pass

    valid_styles = ("primary", "success", "danger")
    if style and style not in valid_styles:
        style = None


    try:
        if url:
            if style: return InlineKeyboardButton(text, url=url, style=style)
            return InlineKeyboardButton(text, url=url)
        if cb:
            if style: return InlineKeyboardButton(text, callback_data=cb, style=style)
            return InlineKeyboardButton(text, callback_data=cb)
    except TypeError:
        if url: return InlineKeyboardButton(text, url=url)
        return InlineKeyboardButton(text, callback_data=cb or "noop")

    return InlineKeyboardButton(text, callback_data="noop")

def otp_platform(text):
    t = str(text or "").lower()
    for key, name, icon in OTP_PLATFORMS:
        if key in t:
            return name, icon
    return "", "📩"


def otp_parts(flag, number, language, raw_sms):
    sn = str(number)
    digits = re.sub(r"\D", "", sn)
    try:
        _f, cname, _cc = detect_country(digits)
        iso = COUNTRIES.get(_cc, ("", ""))[0] or "XX"
    except Exception:
        cname, iso = "", "XX"
        
    # البحث عن إيموجي الدولة المخصص
    if cname:
        custom_flag = setting_get("country_emoji_" + str(cname).strip(), "")
        if custom_flag:
            flag = custom_flag
    if "•" in sn or "*" in sn:
        masked = sn
    else:
        masked = (digits[:5] + "•••" + digits[-3:]) if len(digits) > 8 else digits
    langs = {"ar": "Arabic", "en": "English"}
    lang = langs.get(str(language).lower(), str(language) or "English")
    if raw_sms:
        lang = "English" if str(raw_sms).isascii() else "Arabic"
    pname, picon = otp_platform(raw_sms)
    return {"iso": iso, "cname": cname or iso, "masked": html.escape(masked),
            "lang": lang, "pname": pname, "picon": picon}




























































def otp_render(style, flag, number, language, safe_sms, code, raw_sms, panel_name=None,
               platform=None, country_name=None):
    p = otp_parts(flag, number, language, raw_sms)
    pname = str(panel_name).strip() if panel_name else ""
    if not pname or pname == "None":
        pname = "MATRUI_OTP"
    
    _pcodes = {
        "WhatsApp": "📞 WH", "Telegram": "✈️ TG", "Facebook": "📘 FB", 
        "Instagram": "📸 IG", "Twitter": "🐦 TW", "Google": "🔍 GG", 
        "Apple": "🍏 AP", "TikTok": "⚫ TT", "Discord": "🎮 DC", "Snapchat": "👻 SC"
    }
    short_pname = _pcodes.get(str(p["pname"]), "📱 OT")
    masked_num = p["masked"]
    lang_short = p["lang"][:2].upper()
    
    custom_template = setting_get("custom_otp_template", "")
    
    if custom_template:
        text = custom_template.replace("{platform}", short_pname)
        text = text.replace("{number}", masked_num)
        text = text.replace("{country}", str(flag))
        text = text.replace("{iso}", p["iso"])
        text = text.replace("{lang}", lang_short)
        text = text.replace("{sms}", safe_sms)
        text = text.replace("{prefix}", html.escape(pname))
        text = text.replace("{code}", str(code))
        return text
    else:
        nl = chr(10)
        line = "━━━━━━━━━━━━━━━━━━"
        text = "<b><u>OTP</u></b>" + nl
        text += line + nl
        text += short_pname + " | ☎️ <b>" + masked_num + "</b>" + nl
        text += str(flag) + " <b>#" + p["iso"] + "</b> | 🌐 <b>#" + lang_short + "</b>" + nl
        text += line + nl
        if safe_sms:
            text += "<blockquote><b>SMS:</b> " + safe_sms + "</blockquote>" + nl + nl
        text += "<blockquote>⚙️ api " + html.escape(pname) + "</blockquote>"
        return text











def main_menu_text(uid):
    u = user_get(uid) or {}
    name = u.get("display_name") or u.get("username") or "User"
    
    try:
        n_count = numbers_count()
        p_count = len(numbers_platforms())
    except Exception:
        n_count = 0
        p_count = 0
        
    user_codes_count = 0
    try:
        conn = db()
        row = conn.execute("SELECT total_codes FROM user_stats WHERE telegram_id=?", (uid,)).fetchone()
        if row:
            user_codes_count = row["total_codes"]
        conn.close()
    except Exception:
        pass
        
    nl = chr(10)
    custom_welcome = setting_get("welcome_text", "")
    
    # لو في رسالة ترحيب مخصصة، نعرضها
    if custom_welcome and custom_welcome.strip():
        text = custom_welcome.replace("{name}", str(name))
        text = text.replace("{id}", str(uid))
        text = text.replace("{platforms}", str(p_count))
        text = text.replace("{numbers}", str(n_count))
        text = text.replace("{codes}", str(user_codes_count))
        text = text.replace("{visits}", str(u.get("visits", 0)))
        return text

    # القائمة الافتراضية (لو مفيش مخصص)
    txt = "╔═════════════════════╗" + nl
    txt += "   <b>✨ MATARI OTP ✨</b>   " + nl
    txt += "╚═════════════════════╝" + nl + nl
    
    txt += "👤 أهلاً بك يا <b>" + name + "</b> 😩 👋" + nl
    txt += "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈" + nl
    txt += "🆔 معرفك : <code>" + str(uid) + "</code>" + nl
    txt += "📱 الأرقام : <b>" + str(n_count) + "</b>" + nl
    txt += "🟢 الحالة : <b>متصل</b>" + nl
    txt += "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈" + nl + nl
    
    txt += "👇 <i>اختر الخدمة التي تريدها من الأزرار بالأسفل:</i>"
    return txt

def send_otp_message(chat_id, flag, number, language, sms_text, code, support_link="https://t.me/",
                     bot_link="https://t.me/", admin_link="https://t.me/", panel_name=None,
                     platform=None, country_name=None):
    safe_sms = html.escape(sms_text) if sms_text else ""
    _style = setting_get("otp_style", "quote")
    if _style not in OTP_STYLES:
        _style = "quote"
    text = otp_render(_style, flag, number, language, safe_sms, code, sms_text, panel_name=panel_name,
                      platform=platform, country_name=country_name)

    def _build(with_style):
        st = (lambda s: s) if with_style else (lambda s: None)
        kb = InlineKeyboardMarkup(row_width=2)
        # زر الكود: أخضر + copy_text فقط (بدون callback_data)
        kb.row(_kb_btn(str(code), copy_text=str(code), style=st("success")))
        # إضافة زر تخصيص القالب تحت الكود مباشرة
        row = []
        if _valid_url(bot_link):
            row.append(_kb_btn(setting_get("btn_bot_text", "🤖 Nmbr Bot"), url=bot_link, style=st("primary")))
        if _valid_url(admin_link):
            row.append(_kb_btn(setting_get("admin_btn_name", "👑 Admin"), url=admin_link, style=st("danger")))
        if row:
            kb.row(*row)
        return kb

    last = ""
    for with_style in (True, False):
        try:
            msg = bot.send_message(chat_id, text, reply_markup=_build(with_style), parse_mode="HTML")
            if str(chat_id).startswith("-100") or True: # حفظ أي رسالة ترسل للقناة
                save_channel_message(chat_id, msg.message_id)
            return True
        except Exception as e:
            last = str(e)
            print("[SEND_OTP] Error:", e)
            if "button" not in last.lower() and "parse" not in last.lower():
                break
    OTP_LAST_ERROR["msg"] = last
    return False



# ✅ تحسين استقرار الاتصال بـ Telegram (إعادة المحاولة التلقائية)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    _retry_strategy = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    _adapter = HTTPAdapter(max_retries=_retry_strategy, pool_connections=20, pool_maxsize=20)
    
    _session = requests.Session()
    _session.mount("https://", _adapter)
    _session.mount("http://", _adapter)
    print("[NET] ✅ تم تحسين إعدادات الاتصال")
except Exception as _e:
    print("[NET] ⚠️ فشل تحسين الاتصال:", _e)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ============================================================
# [FORWARD DECLARATION] تعريف مسبق لضمان عمل الدوال
# ============================================================
def show_numbers_page(chat_id, platform, country, page=0, edit_msg=None):
    if chat_id not in WATCHING_USERS:
        WATCHING_USERS[chat_id] = {}
    WATCHING_USERS[chat_id][(platform, country)] = time.time()

    nums = numbers_list(platform=platform, country=country)
    if not nums:
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(_kb_btn("⬅️ القائمة الرئيسية", "menu:home"))
        try:
            if edit_msg:
                bot.edit_message_text("لا توجد أرقام", chat_id, edit_msg.message_id, reply_markup=kb)
            else:
                bot.send_message(chat_id, "لا توجد أرقام", reply_markup=kb)
        except Exception:
            pass
        return

    per_page = 4
    total_pages = max(1, (len(nums) + per_page - 1) // per_page)
    page = int(page) % total_pages
    four = nums[page * per_page:(page + 1) * per_page]

    flag = "🌍"
    try:
        flag = detect_country(four[0]["phone"])[0]
    except Exception:
        pass
    clean_country = str(country).strip()
    flag = setting_get("country_emoji_" + clean_country, flag)

    text = ("⏳ <b>انتظار الكود...</b>" + "\n" +
            "<i>ستستقبل الرسائل تلقائياً عند وصولها</i>\n" +
            flag + " <b>" + html.escape(str(country)) + "</b> — " + html.escape(str(platform)) + "\n")

    kb = InlineKeyboardMarkup(row_width=1)
    color_mode = setting_get("numbers_color_mode", "static")
    static_color = setting_get("numbers_static_color", "success")
    
    color_palette = ["success", "primary", "danger", "success"]
    if color_mode == "auto":
        page_offset = (page * 4) % len(color_palette)
        colors_to_use = [color_palette[(i + page_offset) % len(color_palette)] for i in range(4)]
    else:
        colors_to_use = [static_color] * 4

    for idx, n in enumerate(four):
        try:
            f2 = detect_country(n["phone"])[0]
        except Exception:
            f2 = "🌍"
        f2 = setting_get("country_emoji_" + clean_country, f2)
        c_style = colors_to_use[idx] if idx < len(colors_to_use) else static_color
        kb.add(_kb_btn(f2 + " " + str(n["phone"]), copy_text=str(n["phone"]), style=c_style))

    kb.add(_kb_btn("🔄 تغيير الرقم", "sw:" + str(platform) + ":" + str(country) + ":" + str(page), style="danger"))
    kb.add(_kb_btn("🌍 تغيير الدولة", "selp:" + str(platform), style="primary"))

    group = setting_get("channel_link", "") or setting_get("support_url", "")
    gb = _kb_btn("🔑 جروب البوت", url=group, style="success") if _valid_url(group) else None
    if gb:
        kb.add(gb)
    kb.add(_kb_btn("⬅️ القائمة الرئيسية", "menu:home", style="danger"))

    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(_kb_btn("⬅️", "pg:" + str(platform) + ":" + str(country) + ":" + str(page - 1)))
        nav.append(_kb_btn(str(page + 1) + "/" + str(total_pages), "noop"))
        if page < total_pages - 1:
            nav.append(_kb_btn("➡️", "pg:" + str(platform) + ":" + str(country) + ":" + str(page + 1)))
        kb.row(*nav)

    if edit_msg:
        try:
            bot.edit_message_text(text, chat_id, edit_msg.message_id, reply_markup=kb)
            return
        except Exception as e:
            if "not modified" in str(e).lower():
                return
    bot.send_message(chat_id, text, reply_markup=kb)


# ============================================================
# البوت - بداية التعريفات
# ============================================================




def _fwd_chat(m):
    c = getattr(m, "forward_from_chat", None)
    if c is None:
        fo = getattr(m, "forward_origin", None)
        c = getattr(fo, "chat", None) if fo is not None else None
    return c


def _src_fwd_filter(m):
    try:
        if m.chat.type != "private" or _fwd_chat(m) is None:
            return False
        ts = setting_get("src_wait_" + str(m.from_user.id), "")
        return bool(ts) and (time.time() - float(ts) < 300)
    except Exception:
        return False


@bot.message_handler(func=_src_fwd_filter, content_types=["text", "photo", "video", "document", "animation"])
def on_src_forward(m):
    ch = _fwd_chat(m)
    cid = str(ch.id)
    title = getattr(ch, "title", "") or ""
    main = str(setting_get("channel_id", "")).strip()
    if not main:
        setting_set("channel_id", cid)
    elif cid != main:
        extra = [x.strip() for x in str(setting_get("src_extra_ids", "")).split(",") if x.strip()]
        if cid not in extra:
            extra.append(cid)
        setting_set("src_extra_ids", ",".join(extra))
    setting_set("src_wait_" + str(m.from_user.id), "")
    note = "" if setting_get("channel_bot_token", "") else \
        "\n\n⚠️ لم يُضبط بوت القارئ بعد: أضف توكن بوت مشرف في القناة من 📡 قناة الأكواد."
    try:
        bot.reply_to(m, "✅ أُضيف المصدر: <b>" + html.escape(title) + "</b>\n<code>" + cid + "</code>" + note)
    except Exception:
        pass


# حالات المستخدمين (للإدخال المتسلسل)
user_states = {}
WATCHING_USERS = {}


def set_state(uid, state, data=None):
    user_states[uid] = {"state": state, "data": data or {}}


def get_state(uid):
    return user_states.get(uid, {})


def clear_state(uid):
    user_states.pop(uid, None)


# ============================================================
# أزرار مشتركة
# ============================================================
def main_menu_kb(uid):
    """بناء القائمة الرئيسية (مع أزرار احتياطية لو الداتابيز فاضية)"""
    
    # قائمة الأزرار الافتراضية
    default_buttons = [
        ("btn_platforms", "📱 المنصات", "menu:getnum", "primary"),
        ("btn_last_codes", "😩 آخر الأكواد", "menu:last_codes", "success"),
        ("btn_support", "💭 الدعم", "menu:support", "success"),
        ("btn_me", "👤 ملفي", "menu:me", "primary"),
        ("btn_explore", "🌐 استكشف", "menu:explore", "primary"),
        ("btn_settings", "📊 الترافيك المباشر", "menu:traffic", "primary"),
    ]
    
    if user_is_admin(uid):
        default_buttons.append(("btn_admin", "👮 لوحة الأدمن", "admin:home", "danger"))

    # محاولة قراءة الأزرار من الداتابيز (لو موجودة)
    rows = []
    try:
        conn = db()
        rows = conn.execute("SELECT button_key, row_idx, col_idx FROM main_menu_grid ORDER BY row_idx ASC, col_idx ASC").fetchall()
        conn.close()
    except Exception:
        rows = []

    kb = InlineKeyboardMarkup(row_width=2)
    
    # لو الداتابيز فاضية، استخدم الأزرار الافتراضية
    if not rows:
        current_row = []
        for key, label, cb, style in default_buttons:
            try:
                b = InlineKeyboardButton(label, callback_data=cb, style=style)
            except TypeError:
                b = InlineKeyboardButton(label, callback_data=cb)
            
            if key == "btn_platforms":
                if current_row:
                    kb.row(*current_row)
                    current_row = []
                kb.row(b) # زر المنصات لوحده
            else:
                current_row.append(b)
                if len(current_row) == 2:
                    kb.row(*current_row)
                    current_row = []
        if current_row:
            kb.row(*current_row)
        return kb

    # لو الداتابيز فيها بيانات، ابني الأزرار منها
    callback_map = {
        "btn_platforms": "menu:getnum",
        "btn_last_codes": "menu:last_codes",
        "btn_codes": "menu:codes",
        "btn_contests": "menu:contests",
        "btn_ads": "menu:ads",
        "btn_support": "menu:support",
        "btn_me": "menu:me",
        "btn_explore": "menu:explore",
        "btn_settings": "menu:traffic",
        "btn_admin": "admin:home",
    }

    btns_map = {}
    conn2 = db()
    try:
        for r in rows:
            k = r["button_key"]
            if k in btns_map: continue
            row = conn2.execute("SELECT label_ar, style, icon, visible FROM button_config WHERE key=?", (k,)).fetchone()
            
            if not row or not row["visible"]: continue
            
            label = row["label_ar"] or k
            icon = row["icon"] or ""
            style = row["style"] or ""
            
            if icon and not label.startswith(icon):
                label = icon + " " + label
                
            if style and ":" in style: style = style.split(":")[0].strip()
            if style not in ("primary", "success", "danger"): style = None
            if "رجوع" in label or "القائمة الرئيسية" in label: style = "danger"

            cb_action = callback_map.get(k, k)
            try:
                if style: b = InlineKeyboardButton(label, callback_data=cb_action, style=style)
                else: b = InlineKeyboardButton(label, callback_data=cb_action)
            except TypeError:
                b = InlineKeyboardButton(label, callback_data=cb_action)
            btns_map[k] = b
    finally:
        conn2.close()

    current_row = -1
    current_row_btns = []
    for r in rows:
        k = r["button_key"]
        if k not in btns_map: continue
        if r["row_idx"] != current_row:
            if current_row_btns: kb.row(*current_row_btns)
            current_row_btns = []
            current_row = r["row_idx"]
        current_row_btns.append(btns_map[k])
    if current_row_btns: kb.row(*current_row_btns)
    
    return kb

def cb_traffic(call):
    try:
        hour_ago = time.time() - 3600
        conn = db()
        total_codes_hour = conn.execute("SELECT COUNT(*) FROM codes WHERE received_at >= ?", (hour_ago,)).fetchone()[0]
        total_codes_all = conn.execute("SELECT COUNT(*) FROM codes").fetchone()[0]
        
        top_countries_raw = conn.execute("SELECT country, COUNT(*) as c FROM codes WHERE country != '' AND country != 'غير معروف' GROUP BY country ORDER BY c DESC LIMIT 5").fetchall()
        conn.close()

        top_countries = ""
        if not top_countries_raw:
            top_countries = "لا توجد بيانات كافية حالياً."
        else:
            for i, row in enumerate(top_countries_raw, 1):
                c_name = row['country']
                c_count = row['c']
                percent = (c_count / total_codes_all * 100) if total_codes_all > 0 else 0
                flag = "🏳"
                for code_key, (iso, name) in COUNTRIES.items():
                    if name == c_name or c_name in name:
                        flag = iso_flag(iso)
                        break
                top_countries += f"<b>{i}.</b> {flag} {c_name} ➔ <b>{c_count}</b> ({percent:.1f}%)" + chr(10)

        custom_text = setting_get("section_text_traffic", "")
        if custom_text and custom_text.strip():
            text = custom_text.replace("{hour_codes}", str(total_codes_hour))
            text = text.replace("{total_codes}", str(total_codes_all))
            text = text.replace("{top_countries}", top_countries)
            text = text.replace("{time}", datetime.now().strftime("%H:%M:%S"))
        else:
            text = "📊 <b>الترافيك المباشر</b> 🟢" + chr(10)
            text += "━━━━━━━━━━━━━━━━━━" + chr(10)
            text += "🕐 <b>المدة:</b> آخر 60 دقيقة" + chr(10)
            text += "📥 <b>الأكواد الواصلة:</b> " + str(total_codes_hour) + chr(10)
            text += "📊 <b>إجمالي الأكواد:</b> " + str(total_codes_all) + chr(10)
            text += "━━━━━━━━━━━━━━━━━━" + chr(10)
            text += "🌍 <b>أعلى الدول:</b>" + chr(10) + chr(10) + top_countries + chr(10)
            text += "━━━━━━━━━━━━━━━━━━" + chr(10)
            text += "🕐 <b>آخر تحديث:</b> " + datetime.now().strftime("%H:%M:%S") + chr(10)
            text += "🟢 <i>متصل الآن</i>"

        kb = InlineKeyboardMarkup()
        kb.add(btn("🔄 تحديث", "menu:traffic", BTN.PRIMARY))
        kb.add(btn("⬅️ رجوع", "menu:home"))

        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ حدث خطأ: " + str(e)[:100])

@bot.callback_query_handler(func=lambda c: c.data == "menu:home")
def cb_home(call):
    uid = call.from_user.id
    user_states.pop(uid, None)
    
    # تعديل الرسالة الحالية بدل إرسال رسالة جديدة
    try:
        bot.edit_message_text(main_menu_text(uid), call.message.chat.id, call.message.message_id, reply_markup=main_menu_kb(uid), parse_mode="HTML")
    except Exception:
        # لو فشل التعديل (زي الرسالة القديمة)، نرسل رسالة جديدة
        try:
            bot.send_message(call.message.chat.id, main_menu_text(uid), reply_markup=main_menu_kb(uid))
        except Exception as e:
            print("Error sending home:", e)
        
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


# ============================================================
# قسم المنصات
# ============================================================

@bot.callback_query_handler(func=lambda c: c.data == "noop")
def cb_noop(call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



# ============================================================
# قسم الأكواد العام
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "menu:codes")
def cb_codes_menu(call):
    if user_is_admin(call.from_user.id):
        # لو أدمن، يشوف الأكواد (نفس الكود القديم)
        items = codes_list(limit=20)
        if not items:
            text = "💬 لا توجد أكواد حالياً"
        else:
            text = "💬 <b>آخر الأكواد (للأدمن)</b>\n\n"
            for i, c in enumerate(items[:10], 1):
                t = datetime.fromtimestamp(c["received_at"]).strftime("%H:%M")
                text += str(i) + ". 🔑 <code>" + c["code"] + "</code>\n"
                text += "    📱 <code>" + c["phone"] + "</code> — " + c["platform"] + " — " + t + "\n\n"
        kb = InlineKeyboardMarkup()
        kb.add(btn("🔄 تحديث", "menu:codes", BTN.PRIMARY))
        kb.add(btn("⬅️ رجوع", "menu:home"))
    else:
        # لو مستخدم عادي، يظهرله رسالة إن القسم ده للأدمن بس
        text = "🚫 <b>هذا القسم مخصص للإدارة فقط.</b>"
        kb = InlineKeyboardMarkup()
        kb.add(btn("⬅️ رجوع", "menu:home"))
        
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception as e:
        if "message is not modified" not in str(e):
            bot.send_message(call.message.chat.id, text, reply_markup=kb)


# ============================================================
# ملفي + الإعدادات
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "menu:me")
def cb_me(call):
    uid = call.from_user.id
    u = user_get(uid) or {}
    custom_text = setting_get("section_text_me", "")
    joined = datetime.fromtimestamp(u.get("created", 0)).strftime("%Y-%m-%d")
    
    codes_count = 0
    try:
        conn = db()
        row = conn.execute("SELECT total_codes FROM user_stats WHERE telegram_id=?", (uid,)).fetchone()
        if row:
            codes_count = row["total_codes"]
        conn.close()
    except Exception:
        pass

    custom_text = setting_get("section_text_me", "")
    if custom_text and custom_text.strip():
        text = custom_text.replace("{id}", str(uid))
        text = text.replace("{name}", u.get("display_name") or "—")
        text = text.replace("{username}", u.get("username") or "—")
        text = text.replace("{joined}", joined)
        text = text.replace("{visits}", str(u.get("visits", 0)))
        text = text.replace("{codes_count}", str(codes_count))
        if "<b>" in text or "<i>" in text:
            text = text.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
            text = text.replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
    else:
        text = "👤 <b>الملف الشخصي</b>" + chr(10)
        text += "━━━━━━━━━━━━━━━━━━" + chr(10)
        text += "🆔 <b>الآي دي:</b> <code>" + str(uid) + "</code>" + chr(10)
        text += "👤 <b>الاسم:</b> " + (u.get("display_name") or "—") + chr(10)
        text += "🔗 <b>المعرف:</b> @" + (u.get("username") or "—") + chr(10)
        text += "📅 <b>تاريخ الانضمام:</b> " + joined + chr(10)
        text += "━━━━━━━━━━━━━━━━━━" + chr(10)
        text += "👁 <b>الزيارات:</b> " + str(u.get("visits", 0)) + chr(10)
        text += "🔑 <b>الأكواد المسحوبة:</b> " + str(codes_count) + chr(10)
        text += "━━━━━━━━━━━━━━━━━━"

    kb = InlineKeyboardMarkup()
    kb.add(btn("🔄 تحديث", "menu:me", BTN.PRIMARY))
    kb.add(btn("⬅️ رجوع", "menu:home"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

# ============================================================
# الدعم الفني
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "menu:support")
def cb_support(call):
    uid = call.from_user.id
    set_state(uid, "support_msg", {})
    custom_text = setting_get("section_text_support", "")
    
    custom_text = setting_get("section_text_support", "")
    if custom_text and custom_text.strip():
        text = custom_text
        if "<b>" in text or "<i>" in text:
            text = text.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
            text = text.replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
    else:
        text = "💭 <b>قسم الدعم الفني</b> 💭" + chr(10)
        text += "━━━━━━━━━━━━━━━━━━" + chr(10) + chr(10)
        text += "👋 أهلاً بك في مركز المساعدة." + chr(10)
        text += "✍️ <b>قم بكتابة رسالتك الآن</b> وسيتم الرد عليك من قبل الإدارة في أقرب وقت ممكن." + chr(10) + chr(10)
        text += "━━━━━━━━━━━━━━━━━━" + chr(10)
        text += "💡 <i>للإلغاء، يمكنك إرسال الأمر /cancel في أي وقت.</i>"

    bot.send_message(call.message.chat.id, text, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "support_msg")
def handle_support(msg):
    uid = msg.from_user.id
    text = (msg.text or "").strip()
    if not text:
        return
    conn = db()
    conn.execute("INSERT INTO chats (user_id, sender, message, created) VALUES (?, ?, ?, ?)",
                 (uid, "user", text, time.time()))
    conn.commit()
    conn.close()
    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم إرسال رسالتك للإدارة.")
    # إشعار الأدمن
    try:
        bot.send_message(MAIN_ADMIN_ID,
            "💭 رسالة جديدة\n👤 " + str(uid) + "\n\n" + text)
    except Exception:
        pass


# ============================================================
# استكشف
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "menu:explore")
def cb_explore(call):
    custom_text = setting_get("section_text_explore", "")
    if custom_text and custom_text.strip():
        text = custom_text.replace("{users}", str(users_count()))
        text = text.replace("{codes}", str(codes_count()))
        text = text.replace("{numbers}", str(numbers_count()))
        text = text.replace("{panels}", str(len(panels_list())))
        if "<b>" in text or "<i>" in text:
            text = text.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
            text = text.replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
    else:
        text = "✨ <b>إحصائيات النظام المباشرة</b> ✨" + chr(10)
        text += "━━━━━━━━━━━━━━━━━━" + chr(10)
        text += "👥 <b>المستخدمين:</b> " + str(users_count()) + chr(10)
        text += "💬 <b>الأكواد المسحوبة:</b> " + str(codes_count()) + chr(10)
        text += "📱 <b>الأرقام المتاحة:</b> " + str(numbers_count()) + chr(10)
        text += "📡 <b>اللوحات النشطة:</b> " + str(len(panels_list())) + chr(10)
        text += "━━━━━━━━━━━━━━━━━━" + chr(10)
        text += "⚡ <i>النظام يعمل بكفاءة عالية</i>"
                
    kb = InlineKeyboardMarkup()
    kb.add(btn("⬅️ رجوع", "menu:home"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

# ============================================================
# الإعلانات والمسابقات (سيتم إضافتها لاحقاً)
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data in ("menu:ads", "menu:contests"))
def cb_ads_contests(call):
    text = "🔜 قريباً"
    kb = InlineKeyboardMarkup()
    kb.add(btn("⬅️ رجوع", "menu:home"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


# ============================================================
# لوحة الأدمن
# ============================================================





@bot.message_handler(commands=["admin"])
def cmd_admin(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        bot.send_message(msg.chat.id, "🚫 للأدمن فقط")
        return
    admin_panel(msg.chat.id, uid)



@bot.callback_query_handler(func=lambda c: c.data == "admin:toggle_old")
def cb_toggle_old(call):
    if not user_is_admin(call.from_user.id): return
    current = setting_get("block_old_codes", "1")
    new_val = "0" if current == "1" else "1"
    setting_set("block_old_codes", new_val)
    status = "مفعل ✅" if new_val == "1" else "معطل ❌"
    bot.answer_callback_query(call.id, "تم: " + status, show_alert=True)
    admin_panel(call.message.chat.id, call.from_user.id, call.message)

# ============================================================
# 🎛 استوديو الأزرار — تخصيص لون/اسم/إيموجي/إخفاء أي زر، مقسّم إلى أقسام
# ============================================================
BS_SECTIONS = [
    ("🏠 القائمة الرئيسية", {"menu", "home", "set", "btn_back", "btn_platforms", "btn_codes", "btn_contests",
                             "btn_ads", "btn_support", "btn_me", "btn_explore", "btn_settings", "btn_admin"}),
    ("👮 لوحة الأدمن", {"admin", "maint", "act", "aad", "bs"}),
    ("📡 اللوحات و APIs", {"ap", "ap_auth", "ap_m", "ape", "ag", "ptool"}),
    ("📱 الأرقام والمنصات", {"num", "num_panel", "nc", "colors_pl", "colors_co", "custom_color", "autodel", "plat"}),
    ("📢 القناة والرسائل", {"chf", "ch", "tpl", "ctmpl", "tp", "src", "rp"}),
    ("🧩 الترتيب والتخطيط", {"sec_edit", "bc", "srt", "ly2", "btn_first", "btn_up", "btn_down", "btn_last",
                             "btn_1", "btn_2", "btn_3", "btn_4", "btn_del", "btn_reset", "btn_edit", "btn_left",
                             "btn_right", "btn_newrow", "btn_w1", "btn_w2"}),
]
BS_OTHER = "🧩 أخرى"
BS_COLORS = {"d": ("danger", "🔴 أحمر"), "s": ("success", "🟢 أخضر"), "p": ("primary", "🔵 أزرق"), "a": ("", "⚪ تلقائي")}
BS_PER_PAGE = 8
BS_REG = {"items": None}


def bs_apply_cfg(text, cfg):
    """يطبّق اسم/إيموجي الزر المخصصين على النص الافتراضي (الإيموجي يعمل حتى بدون اسم)"""
    label = str(cfg.get("label_ar") or "").strip()
    icon = str(cfg.get("icon") or "").strip()
    if label:
        if "{text}" in label:
            return label.replace("{text}", text)
        return (icon + " " + label) if icon else label
    if icon:
        body = re.sub(r"^[^\w]+", "", str(text))
        return icon + " " + (body or str(text))
    return text


def _bs_section_of(ident, cb):
    pre = (cb or ident).split(":")[0]
    for name, prefs in BS_SECTIONS:
        if pre in prefs or ident in prefs:
            return name
    return BS_OTHER


def bs_registry():
    """يكتشف تلقائيًا كل أزرار btn(...) الثابتة في الملف ويقسمها لأقسام"""
    if BS_REG["items"] is not None:
        return BS_REG["items"]
    import ast
    found, seen = [], set()
    try:
        tree = ast.parse(open(__file__, encoding="utf-8").read())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "btn" and n.args]
        for n in sorted(calls, key=lambda x: x.lineno):
            a0 = n.args[0]
            text = a0.value if isinstance(a0, ast.Constant) and isinstance(a0.value, str) else None
            cb = None
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str):
                cb = n.args[1].value
            key = None
            for kw in n.keywords:
                if kw.arg == "key" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    key = kw.value.value
                if kw.arg == "cb" and cb is None and isinstance(kw.value, ast.Constant):
                    cb = kw.value.value
            ident = key or cb
            if not text or not ident or ident in seen:
                continue
            seen.add(ident)
            found.append({"id": ident, "text": text, "cb": cb, "key": key, "sec": _bs_section_of(ident, cb)})
    except Exception as e:
        print("[BS] registry err:", e)
    order = [s[0] for s in BS_SECTIONS] + [BS_OTHER]
    found.sort(key=lambda x: order.index(x["sec"]))
    for i, it in enumerate(found):
        it["n"] = i
    BS_REG["items"] = found
    return found


def bs_sections():
    items = bs_registry()
    out = []
    for name in [s[0] for s in BS_SECTIONS] + [BS_OTHER]:
        idx = [it["n"] for it in items if it["sec"] == name]
        if idx:
            out.append((name, idx))
    return out


def bs_cfg_set(ident, **fields):
    conn = db()
    conn.execute("INSERT OR IGNORE INTO button_config (key) VALUES (?)", (ident,))
    conn.commit()
    conn.close()
    btn_config_set(ident, **fields)


def bs_is_custom(cfg):
    return bool(cfg.get("label_ar") or cfg.get("icon") or cfg.get("style") or not cfg.get("visible", 1))


def bs_preview(it):
    """(النص، اللون) كما سيظهر الزر فعليًا"""
    cfg = btn_config_get(it["id"])
    text = bs_apply_cfg(it["text"], cfg)
    style = cfg.get("style") or ""
    if not style and any(k in text for k in ("رجوع", "القائمة الرئيسية", "⬅️", "🏠")):
        style = "danger"
    if not style:
        style = _auto_style(text, it["cb"])
    return text, style


def _bs_esc(s):
    return html.escape(str(s or ""))


def bs_home_view():
    secs = bs_sections()
    items = bs_registry()
    total_custom = sum(1 for it in items if bs_is_custom(btn_config_get(it["id"])))
    text = ("🎛 <b>استوديو الأزرار</b>\n\n"
            "خصّص أي زر في البوت: <b>اللون • الاسم • الإيموجي • الإخفاء</b>\n"
            "📦 الأزرار: <b>" + str(len(items)) + "</b> | ✏️ المخصصة: <b>" + str(total_custom) + "</b>\n\n"
            "اختر القسم 👇")
    kb = InlineKeyboardMarkup(row_width=1)
    for si, (name, idx) in enumerate(secs):
        done = sum(1 for n in idx if bs_is_custom(btn_config_get(items[n]["id"])))
        kb.add(_kb_btn(name + " (" + str(len(idx)) + (" • ✏️" + str(done) if done else "") + ")", "bs:s:" + str(si) + ":0",
                       style="primary"))
    kb.add(_kb_btn("↩️ استعادة كل الأزرار", "bs:ra", style="danger"))
    kb.add(_kb_btn("⬅️ لوحة الأدمن", "admin:home", style="danger"))
    return text, kb


def bs_section_view(si, page):
    secs = bs_sections()
    if si < 0 or si >= len(secs):
        return bs_home_view()
    name, idx = secs[si]
    items = bs_registry()
    pages = max(1, (len(idx) + BS_PER_PAGE - 1) // BS_PER_PAGE)
    page = max(0, min(int(page), pages - 1))
    chunk = idx[page * BS_PER_PAGE:(page + 1) * BS_PER_PAGE]
    text = ("🎛 <b>" + name + "</b>\n\nاضغط على أي زر لتخصيصه — لون الزر هنا هو لونه الحالي.\n"
            "الصفحة " + str(page + 1) + "/" + str(pages))
    kb = InlineKeyboardMarkup(row_width=1)
    for n in chunk:
        it = items[n]
        ptxt, pst = bs_preview(it)
        hidden = not btn_config_get(it["id"]).get("visible", 1)
        hint = (" ‹" + it["id"] + "›") if "رجوع" in it["text"] else ""
        kb.add(_kb_btn(("🙈 " if hidden else "") + ptxt + hint, "bs:e:" + str(n), style=pst))
    if pages > 1:
        nav = []
        if page > 0:
            nav.append(_kb_btn("⬅️", "bs:s:" + str(si) + ":" + str(page - 1), style="primary"))
        nav.append(_kb_btn(str(page + 1) + "/" + str(pages), "noop", style="primary"))
        if page < pages - 1:
            nav.append(_kb_btn("➡️", "bs:s:" + str(si) + ":" + str(page + 1), style="primary"))
        kb.row(*nav)
    kb.add(_kb_btn("🎨 تلوين القسم كله", "bs:sc:" + str(si), style="success"),
           _kb_btn("↩️ استعادة القسم", "bs:srs:" + str(si), style="danger"))
    kb.add(_kb_btn("⬅️ الأقسام", "bs:home", style="danger"))
    return text, kb


def bs_edit_view(n):
    items = bs_registry()
    if n < 0 or n >= len(items):
        return bs_home_view()
    it = items[n]
    cfg = btn_config_get(it["id"])
    cur = cfg.get("style") or ""
    cname = next((v[1] for v in BS_COLORS.values() if v[0] == cur), "⚪ تلقائي")
    hidden = not cfg.get("visible", 1)
    ptxt, pst = bs_preview(it)
    text = ("🎛 <b>تخصيص زر</b>\n\n"
            "🆔 <code>" + _bs_esc(it["id"]) + "</code>\n"
            "📝 الافتراضي: " + _bs_esc(it["text"]) + "\n"
            "✏️ الاسم: " + (_bs_esc(cfg.get("label_ar")) or "—") + "\n"
            "😀 الإيموجي: " + (_bs_esc(cfg.get("icon")) or "—") + "\n"
            "🎨 اللون: " + cname + "\n"
            "👁 الحالة: " + ("🙈 مخفي" if hidden else "ظاهر") + "\n\n"
            "👇 <b>المعاينة</b> (كما سيظهر للمستخدم):")
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(_kb_btn(("🙈 " if hidden else "") + ptxt, "noop", style=pst))
    row = []
    for ck, (cv, cl) in BS_COLORS.items():
        row.append(_kb_btn(("✔ " if cv == cur else "") + cl, "bs:c:" + str(n) + ":" + ck,
                           style=(cv or "primary")))
    kb.row(*row[:3])
    kb.row(row[3])
    kb.add(_kb_btn("✏️ تغيير الاسم", "bs:n:" + str(n), style="primary"),
           _kb_btn("😀 تغيير الإيموجي", "bs:i:" + str(n), style="primary"))
    kb.add(_kb_btn("👁 إظهار" if hidden else "🙈 إخفاء", "bs:v:" + str(n), style="success" if hidden else "danger"),
           _kb_btn("↩️ استعادة الافتراضي", "bs:r:" + str(n), style="danger"))
    secs = bs_sections()
    si = next((i for i, (nm, idx) in enumerate(secs) if n in idx), 0)
    pg = (secs[si][1].index(n) // BS_PER_PAGE) if secs else 0
    kb.add(_kb_btn("⬅️ رجوع للقسم", "bs:s:" + str(si) + ":" + str(pg), style="danger"))
    return text, kb


def bs_confirm_view(text, yes_cb, no_cb):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(_kb_btn("✅ نعم، تأكيد", yes_cb, style="success"), _kb_btn("❌ لا", no_cb, style="danger"))
    return text, kb


def _bs_is_emoji(s):
    return 0 < len(s) <= 12 and not re.search(r"[A-Za-z0-9]", s) and any(ord(ch) >= 0x2190 for ch in s)


def _bs_show(call, view):
    text, kb = view
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception as e:
        if "not modified" not in str(e).lower():
            bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("bs:"))
def cb_bs(call):
    if not user_is_admin(call.from_user.id):
        return
    p = call.data.split(":")
    act = p[1] if len(p) > 1 else "home"
    items = bs_registry()
    note = None
    try:
        if act == "home":
            _bs_show(call, bs_home_view())
        elif act == "s":
            _bs_show(call, bs_section_view(int(p[2]), int(p[3]) if len(p) > 3 else 0))
        elif act == "e":
            _bs_show(call, bs_edit_view(int(p[2])))
        elif act == "c":
            n = int(p[2]); it = items[n]
            bs_cfg_set(it["id"], style=BS_COLORS[p[3]][0])
            note = "🎨 " + BS_COLORS[p[3]][1]
            _bs_show(call, bs_edit_view(n))
        elif act == "v":
            n = int(p[2]); it = items[n]
            cfg = btn_config_get(it["id"])
            if cfg.get("visible", 1) and it["id"] in ("bs:home", "admin:home"):
                note = "⛔ لا يمكن إخفاء هذا الزر"
            else:
                bs_cfg_set(it["id"], visible=0 if cfg.get("visible", 1) else 1)
                note = "تم"
            _bs_show(call, bs_edit_view(n))
        elif act == "r":
            n = int(p[2]); it = items[n]
            bs_cfg_set(it["id"], label_ar="", icon="", style="", visible=1)
            note = "↩️ تمت الاستعادة"
            _bs_show(call, bs_edit_view(n))
        elif act in ("n", "i"):
            n = int(p[2]); it = items[n]
            field = "label" if act == "n" else "icon"
            set_state(call.from_user.id, "bs_input", {"n": n, "field": field})
            if field == "label":
                msg = ("✏️ <b>أرسل الاسم الجديد</b> للزر\n\nالافتراضي: " + _bs_esc(it["text"]) +
                       "\nأرسل <code>-</code> لحذف الاسم المخصص، أو /cancel للإلغاء.")
            else:
                msg = ("😀 <b>أرسل الإيموجي الجديد</b> للزر (إيموجي واحد)\n\n"
                       "أرسل <code>-</code> لحذفه، أو /cancel للإلغاء.")
            bot.send_message(call.message.chat.id, msg)
        elif act == "sc":
            si = int(p[2])
            kb = InlineKeyboardMarkup(row_width=2)
            for ck, (cv, cl) in BS_COLORS.items():
                kb.add(_kb_btn(cl, "bs:sca:" + str(si) + ":" + ck, style=(cv or "primary")))
            kb.add(_kb_btn("⬅️ رجوع", "bs:s:" + str(si) + ":0", style="danger"))
            _bs_show(call, ("🎨 <b>لوّن القسم كله</b>\n\nاختر لونًا يُطبَّق على كل أزرار هذا القسم:", kb))
        elif act == "sca":
            si = int(p[2]); secs = bs_sections()
            for n in secs[si][1]:
                bs_cfg_set(items[n]["id"], style=BS_COLORS[p[3]][0])
            note = "🎨 تم تلوين القسم"
            _bs_show(call, bs_section_view(si, 0))
        elif act == "srs":
            si = int(p[2])
            _bs_show(call, bs_confirm_view("↩️ <b>استعادة القسم</b>\n\nستعود كل أزرار هذا القسم لاسمها وإيموجيها ولونها الأصلي. متأكد؟",
                                           "bs:srsy:" + str(si), "bs:s:" + str(si) + ":0"))
        elif act == "srsy":
            si = int(p[2]); secs = bs_sections()
            for n in secs[si][1]:
                bs_cfg_set(items[n]["id"], label_ar="", icon="", style="", visible=1)
            note = "↩️ تمت استعادة القسم"
            _bs_show(call, bs_section_view(si, 0))
        elif act == "ra":
            _bs_show(call, bs_confirm_view("↩️ <b>استعادة كل الأزرار</b>\n\nسيُلغى كل تخصيص (اسم/إيموجي/لون/إخفاء) على كل الأزرار. متأكد؟",
                                           "bs:ray", "bs:home"))
        elif act == "ray":
            for it in items:
                bs_cfg_set(it["id"], label_ar="", icon="", style="", visible=1)
            note = "↩️ تمت استعادة الكل"
            _bs_show(call, bs_home_view())
    except Exception as e:
        print("[BS] err:", e)
        note = "حدث خطأ"
    try:
        bot.answer_callback_query(call.id, note) if note else bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "bs_input", content_types=["text"])
def handle_bs_input(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    d = (get_state(uid).get("data") or {})
    txt = (msg.text or "").strip()
    items = bs_registry()
    n = int(d.get("n", -1))
    if txt == "/cancel" or n < 0 or n >= len(items):
        clear_state(uid)
        bot.send_message(msg.chat.id, "تم الإلغاء")
        return
    it = items[n]
    if d.get("field") == "label":
        if txt != "-" and len(txt) > 32:
            bot.send_message(msg.chat.id, "⚠️ الاسم طويل (الحد 32 حرفًا). أرسل اسمًا أقصر أو /cancel")
            return
        bs_cfg_set(it["id"], label_ar="" if txt == "-" else txt)
    else:
        if txt != "-" and not _bs_is_emoji(txt):
            bot.send_message(msg.chat.id, "⚠️ أرسل إيموجي واحدًا فقط (بدون حروف) أو <code>-</code> للحذف، أو /cancel")
            return
        bs_cfg_set(it["id"], icon="" if txt == "-" else txt)
    clear_state(uid)
    text, kb = bs_edit_view(n)
    bot.send_message(msg.chat.id, "✅ تم الحفظ\n\n" + text, reply_markup=kb)


@bot.message_handler(commands=["buttons"])
def cmd_buttons(msg):
    if not user_is_admin(msg.from_user.id):
        return
    text, kb = bs_home_view()
    bot.send_message(msg.chat.id, text, reply_markup=kb)


def admin_panel(chat_id, uid, edit=None):
    """لوحة الأدمن"""
    text = ("👮 <b>لوحة التحكم</b>\n\n"
            "👥 المستخدمين: " + str(users_count()) + "\n"
            "💬 الأكواد: " + str(codes_count()) + "\n"
            "📱 الأرقام: " + str(numbers_count()) + "\n"
            "📡 اللوحات: " + str(len(panels_list())))

    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(btn("📡 اللوحات", "admin:panels", key="btn_panels"))
    kb.add(btn("🩺 صحة الـ APIs", "ag:view"))
    kb.add(btn("🎛 استوديو الأزرار", "bs:home"))
    kb.add(btn("📈 تقرير اليوم", "rp:today"))
    kb.add(btn("📱 إدارة الأرقام", "admin:numbers", key="btn_numbers"))
    
    kb.add(
        btn("👥 المستخدمين", "admin:users", key="btn_users"),
        btn("💬 إدارة الأكواد", "admin:codes", key="btn_admin_codes"),
        btn("💰 إدارة الرصيد", "admin:points", key="btn_points"),
        btn("📊 إحصائيات", "admin:stats", key="btn_stats"),
        btn("📢 إشعار جماعي", "admin:broadcast", key="btn_broadcast"),
        btn("🚫 الصيانة", "admin:maintenance", key="btn_maint"),
        btn("➕ إضافة زر مخصص", "admin:add_custom"),
        btn("🗑 حذف زر مخصص", "admin:del_custom"),
            )

    # زر قناة الأكواد + زر تعديل التخطيط (بدل النسخ الاحتياطي)
    kb.add(
        btn("🎨 تخصيص القائمة الرئيسية", "admin:custom_main_menu", key="btn_custom_main_menu"),
        btn("📱 تخصيص المنصات والدول", "admin:custom_pl_co", key="btn_custom_pl_co"),
        btn("📡 قناة الأكواد", "admin:channel", key="btn_channel"),
        btn("📐 تعديل التخطيط", "admin:layout_edit", key="btn_layout_edit")
    )

    kb.add(btn("🎨 تخصيص قالب الرسائل", "admin:template_custom", key="btn_template"))
    
    kb.add(btn("🏠 القائمة الرئيسية", "menu:home", key="btn_home"))

    if edit:
        try:
            bot.edit_message_text(text, chat_id, edit.message_id, reply_markup=kb)
            return
        except Exception:
            pass
    bot.send_message(chat_id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == "admin:custom_main_menu")
def cb_admin_custom_main_menu(call):
    if not user_is_admin(call.from_user.id): return
    
    main_keys = ["btn_platforms", "btn_last_codes", "btn_settings", "btn_me", "btn_explore", "btn_support", "btn_admin"]
    
    conn = db()
    text = "🎨 <b>تخصيص القائمة الرئيسية</b>\n\n"
    text += "هذه هي الأزرار اللي بتظهر للمستخدم في القائمة الرئيسية.\n"
    text += "اضغط على أي زرار لتعديله:"
    
    kb = InlineKeyboardMarkup(row_width=1)
    
    color_names = {
        "primary": "🔵 أزرق",
        "success": "🟢 أخضر",
        "danger": "🔴 أحمر",
        "default": "⚪ افتراضي",
        "": "⚪ افتراضي"
    }
    
    for key in main_keys:
        row = conn.execute("SELECT key, label_ar, style, icon FROM button_config WHERE key=?", (key,)).fetchone()
        if not row:
            continue
        label = row["label_ar"] or key
        icon = row["icon"] or ""
        style = row["style"] or ""
        
        if ":" in style:
            style = style.split(":")[0]
            
        color_ar = color_names.get(style, "⚪ افتراضي")
        display = f"{icon} {label} | {color_ar}"
        kb.add(btn(display, "bc:v:" + key))
    
    conn.close()
    kb.add(btn("⬅️ رجوع", "admin:home"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

# ============================================================
# 📱 تخصيص أزرار المنصات (داخل قسم المنصات)
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "admin:custom_platforms")
def cb_admin_custom_platforms(call):
    if not user_is_admin(call.from_user.id): return

    platforms = numbers_platforms()
    if not platforms:
        try:
            bot.answer_callback_query(call.id, "لا توجد منصات مضافة بعد.", show_alert=True)
        except Exception:
            pass
        return

    text = "📱 <b>تخصيص أزرار المنصات</b>\n\n"
    text += "هذه هي الأزرار التي تظهر داخل قسم المنصات.\n"
    text += "اضغط على أي منصة لتخصيص (الاسم، الإيموجي، اللون):"

    kb = InlineKeyboardMarkup(row_width=1)
    color_names = {
        "primary": "🔵", "success": "🟢", "danger": "🔴", "": "⚪"
    }

    for p in platforms:
        custom_label = setting_get("platform_btn_label_" + p, "")
        custom_icon = setting_get("platform_emoji_" + p, PLATFORM_ICONS.get(p, "📱"))
        custom_style = setting_get("platform_btn_style_" + p, "")
        color_dot = color_names.get(custom_style, "⚪")
        display = f"{custom_icon} {custom_label or p} | {color_dot}"
        kb.add(btn(display, "bcp:v:" + p))

    kb.add(btn("⬅️ رجوع", "admin:home", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("bcp:v:"))
def cb_bcp_view(call):
    if not user_is_admin(call.from_user.id): return
    platform = call.data.split(":", 2)[2]

    custom_label = setting_get("platform_btn_label_" + platform, platform)
    custom_icon = setting_get("platform_emoji_" + platform, PLATFORM_ICONS.get(platform, "📱"))
    custom_style = setting_get("platform_btn_style_" + platform, "")

    color_names = {
        "primary": "🔵 أزرق", "success": "🟢 أخضر", "danger": "🔴 أحمر",
        "": "⚪ افتراضي"
    }
    color_ar = color_names.get(custom_style, "⚪ افتراضي")

    text = f"📱 <b>تخصيص: {platform}</b>\n\n"
    text += f"📝 الاسم الحالي: <b>{custom_label}</b>\n"
    text += f"😀 الإيموجي: <b>{custom_icon}</b>\n"
    text += f"🎨 اللون: <b>{color_ar}</b>"

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("✏️ تغيير الاسم", "bcp:edit:" + platform + ":label", BTN.PRIMARY))
    kb.add(btn("😀 تغيير الإيموجي", "bcp:edit:" + platform + ":icon", BTN.PRIMARY))
    kb.add(btn("🎨 تغيير اللون", "bcp:color:" + platform, BTN.SUCCESS))
    kb.add(btn("🔄 إعادة تعيين", "bcp:reset:" + platform, BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "admin:custom_platforms", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("bcp:edit:"))
def cb_bcp_edit(call):
    if not user_is_admin(call.from_user.id): return
    parts = call.data.split(":", 3)
    if len(parts) < 4: return
    platform = parts[2]
    field = parts[3]

    if field == "label":
        prompt = f"📝 أرسل الاسم الجديد لزر منصة <b>{platform}</b>\n\nمثال: <code>واتساب</code> أو <code>WhatsApp</code>"
    elif field == "icon":
        prompt = f"😀 أرسل الإيموجي الجديد لزر منصة <b>{platform}</b>\n\nمثال: <code>🟢</code> أو <code>💚</code>"
    else:
        return

    set_state(call.from_user.id, "bcp_edit_field", {"platform": platform, "field": field})
    bot.send_message(call.message.chat.id, prompt + "\n\n/cancel للإلغاء", parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "bcp_edit_field")
def handle_bcp_edit_field(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    txt = (msg.text or "").strip()
    if not txt: return
    if txt == "/cancel":
        clear_state(uid)
        bot.send_message(msg.chat.id, "❌ تم الإلغاء")
        return

    s = get_state(uid)
    platform = s["data"].get("platform")
    field = s["data"].get("field")

    if field == "label":
        setting_set("platform_btn_label_" + platform, txt)
    elif field == "icon":
        setting_set("platform_emoji_" + platform, txt)

    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم الحفظ! التغيير سيظهر عند فتح قسم المنصات.")


@bot.callback_query_handler(func=lambda c: c.data.startswith("bcp:color:"))
def cb_bcp_color(call):
    if not user_is_admin(call.from_user.id): return
    platform = call.data.split(":", 2)[2]

    text = f"🎨 <b>اختر اللون لزر {platform}:</b>"

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("🔵 أزرق", "bcp:sc:" + platform + ":primary"))
    kb.add(btn("🟢 أخضر", "bcp:sc:" + platform + ":success"))
    kb.add(btn("🔴 أحمر", "bcp:sc:" + platform + ":danger"))
    kb.add(btn("⚪ افتراضي", "bcp:sc:" + platform + ":"))
    kb.add(btn("⬅️ رجوع", "bcp:v:" + platform, BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("bcp:sc:"))
def cb_bcp_set_color(call):
    if not user_is_admin(call.from_user.id): return
    parts = call.data.split(":", 3)
    if len(parts) < 4: return
    platform = parts[2]
    style = parts[3]

    setting_set("platform_btn_style_" + platform, style)
    try:
        bot.answer_callback_query(call.id, "✅ تم حفظ اللون!")
    except Exception:
        pass
    call.data = "bcp:v:" + platform
    cb_bcp_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("bcp:reset:"))
def cb_bcp_reset(call):
    if not user_is_admin(call.from_user.id): return
    platform = call.data.split(":", 2)[2]

    setting_set("platform_btn_label_" + platform, "")
    setting_set("platform_btn_style_" + platform, "")
    setting_set("platform_emoji_" + platform, "")

    try:
        bot.answer_callback_query(call.id, "✅ تم إعادة التعيين", show_alert=True)
    except Exception:
        pass
    call.data = "bcp:v:" + platform
    cb_bcp_view(call)


# ============================================================
# تطبيق التخصيص في عرض المنصات للمستخدم
# ============================================================

# ============================================================
# 📱 تخصيص أدوات المنصة (الأزرار داخل صفحة المنصة)
# ============================================================
PLATFORM_TOOLS = [
    ("tool_number", "📞 رقم (للنسخ)", "رقم الهاتف القابل للنسخ"),
    ("tool_switch", "🔄 تغيير الرقم", "زر تبديل الرقم"),
    ("tool_country", "🌍 تغيير الدولة", "زر الرجوع لاختيار الدولة"),
    ("tool_group", "🔑 جروب البوت", "زر رابط جروب البوت"),
    ("tool_home", "⬅️ القائمة الرئيسية", "زر الرجوع للقائمة"),
]


@bot.callback_query_handler(func=lambda c: c.data == "admin:custom_platform_tools")
def cb_admin_custom_platform_tools(call):
    if not user_is_admin(call.from_user.id): return

    text = "📱 <b>تخصيص أدوات المنصة</b>\n\n"
    text += "هذه الأزرار التي تظهر داخل صفحة أرقام المنصة.\n"
    text += "اضغط على أي أداة لتعديل شكلها:"

    kb = InlineKeyboardMarkup(row_width=1)
    color_names = {"primary": "🔵", "success": "🟢", "danger": "🔴", "": "⚪"}

    for key, default_label, desc in PLATFORM_TOOLS:
        custom_label = setting_get("ptool_label_" + key, "")
        custom_style = setting_get("ptool_style_" + key, "")
        color_dot = color_names.get(custom_style, "⚪")
        display = f"{custom_label or default_label} | {color_dot}"
        kb.add(btn(display, "ptool:v:" + key))

    kb.add(btn("🔄 إعادة تعيين الكل", "ptool:resetall", BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "admin:home", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("ptool:v:"))
def cb_ptool_view(call):
    if not user_is_admin(call.from_user.id): return
    key = call.data.split(":", 2)[2]

    # نجيب الاسم الافتراضي
    default_label = ""
    desc = ""
    for k, lbl, d in PLATFORM_TOOLS:
        if k == key:
            default_label = lbl
            desc = d
            break

    custom_label = setting_get("ptool_label_" + key, "")
    custom_style = setting_get("ptool_style_" + key, "")
    color_names = {"primary": "🔵 أزرق", "success": "🟢 أخضر", "danger": "🔴 أحمر", "": "⚪ افتراضي"}

    text = f"📱 <b>تخصيص: {default_label}</b>\n\n"
    text += f"📖 الوصف: <i>{desc}</i>\n\n"
    text += f"📝 الاسم الحالي: <b>{custom_label or '(افتراضي)'}</b>\n"
    text += f"🎨 اللون: <b>{color_names.get(custom_style, '⚪ افتراضي')}</b>"

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("✏️ تغيير الاسم", "ptool:edit:" + key, BTN.PRIMARY))
    kb.add(btn("🎨 تغيير اللون", "ptool:color:" + key, BTN.SUCCESS))
    kb.add(btn("🔄 إعادة تعيين", "ptool:reset:" + key, BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "admin:custom_platform_tools", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("ptool:edit:"))
def cb_ptool_edit(call):
    if not user_is_admin(call.from_user.id): return
    key = call.data.split(":", 2)[2]
    set_state(call.from_user.id, "ptool_edit_field", {"key": key})
    bot.send_message(call.message.chat.id,
        f"📝 أرسل الاسم الجديد للزر:\n\n"
        f"مثال: <code>🔄 تبديل</code> أو <code>🔙 رجوع</code>\n\n"
        f"/cancel للإلغاء", parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "ptool_edit_field")
def handle_ptool_edit_field(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    txt = (msg.text or "").strip()
    if not txt: return
    if txt == "/cancel":
        clear_state(uid)
        bot.send_message(msg.chat.id, "❌ تم الإلغاء")
        return
    s = get_state(uid)
    key = s["data"].get("key")
    setting_set("ptool_label_" + key, txt)
    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم الحفظ! التغيير سيظهر في صفحة المنصة.")


@bot.callback_query_handler(func=lambda c: c.data.startswith("ptool:color:"))
def cb_ptool_color(call):
    if not user_is_admin(call.from_user.id): return
    key = call.data.split(":", 2)[2]

    text = "🎨 <b>اختر اللون:</b>"
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("🔵 أزرق", "ptool:sc:" + key + ":primary"))
    kb.add(btn("🟢 أخضر", "ptool:sc:" + key + ":success"))
    kb.add(btn("🔴 أحمر", "ptool:sc:" + key + ":danger"))
    kb.add(btn("⚪ افتراضي", "ptool:sc:" + key + ":"))
    kb.add(btn("⬅️ رجوع", "ptool:v:" + key, BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ptool:sc:"))
def cb_ptool_set_color(call):
    if not user_is_admin(call.from_user.id): return
    parts = call.data.split(":", 3)
    if len(parts) < 4: return
    key = parts[2]
    style = parts[3]
    setting_set("ptool_style_" + key, style)
    try:
        bot.answer_callback_query(call.id, "✅ تم حفظ اللون!")
    except Exception:
        pass
    call.data = "ptool:v:" + key
    cb_ptool_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ptool:reset:"))
def cb_ptool_reset(call):
    if not user_is_admin(call.from_user.id): return
    key = call.data.split(":", 2)[2]
    setting_set("ptool_label_" + key, "")
    setting_set("ptool_style_" + key, "")
    try:
        bot.answer_callback_query(call.id, "✅ تم إعادة التعيين", show_alert=True)
    except Exception:
        pass
    call.data = "ptool:v:" + key
    cb_ptool_view(call)


@bot.callback_query_handler(func=lambda c: c.data == "ptool:resetall")
def cb_ptool_reset_all(call):
    if not user_is_admin(call.from_user.id): return
    for key, _, _ in PLATFORM_TOOLS:
        setting_set("ptool_label_" + key, "")
        setting_set("ptool_style_" + key, "")
    try:
        bot.answer_callback_query(call.id, "✅ تم إعادة تعيين كل الأدوات", show_alert=True)
    except Exception:
        pass
    call.data = "admin:custom_platform_tools"
    cb_admin_custom_platform_tools(call)


# ============================================================
# 📱 ألوان عرض المنصات والدول
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "admin:colors_pl_co")
def cb_admin_colors_pl_co(call):
    if not user_is_admin(call.from_user.id): return

    pl_style = setting_get("platform_list_style", "")
    co_style = setting_get("country_list_style", "")
    
    color_names = {"primary": "🔵 أزرق", "success": "🟢 أخضر", "danger": "🔴 أحمر", "": "⚪ افتراضي"}

    text = "📱 <b>ألوان عرض المنصات والدول</b>\n\n"
    text += "هنا يمكنك تغيير اللون الموحد لكل أزرار العرض:\n\n"
    text += f"🗂 <b>قائمة المنصات:</b> {color_names.get(pl_style, '⚪ افتراضي')}\n"
    text += f"🌍 <b>قائمة الدول:</b> {color_names.get(co_style, '⚪ افتراضي')}\n\n"
    text += "اختر القائمة لتعديل لونها:"

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("🗂 لون أزرار المنصات", "colors_pl:view", BTN.PRIMARY))
    kb.add(btn("🌍 لون أزرار الدول", "colors_co:view", BTN.PRIMARY))
    kb.add(btn("⬅️ رجوع", "admin:home", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data == "colors_pl:view")
def cb_colors_pl_view(call):
    if not user_is_admin(call.from_user.id): return
    current = setting_get("platform_list_style", "")
    color_names = {"primary": "🔵 أزرق", "success": "🟢 أخضر", "danger": "🔴 أحمر", "": "⚪ افتراضي"}

    text = "🗂 <b>لون أزرار المنصات</b>\n\n"
    text += f"اللون الحالي: <b>{color_names.get(current, '⚪ افتراضي')}</b>\n\n"
    text += "اختر اللون الجديد:"

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("🔵 أزرق", "colors_pl:sc:primary"))
    kb.add(btn("🟢 أخضر", "colors_pl:sc:success"))
    kb.add(btn("🔴 أحمر", "colors_pl:sc:danger"))
    kb.add(btn("⚪ افتراضي", "colors_pl:sc:"))
    kb.add(btn("⬅️ رجوع", "admin:colors_pl_co", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: c.data.startswith("colors_pl:sc:"))
def cb_colors_pl_set(call):
    if not user_is_admin(call.from_user.id): return
    style = call.data.split(":", 2)[2]
    setting_set("platform_list_style", style)
    try:
        bot.answer_callback_query(call.id, "✅ تم حفظ لون المنصات!")
    except Exception:
        pass
    cb_colors_pl_view(call)


@bot.callback_query_handler(func=lambda c: c.data == "colors_co:view")
def cb_colors_co_view(call):
    if not user_is_admin(call.from_user.id): return
    current = setting_get("country_list_style", "")
    color_names = {"primary": "🔵 أزرق", "success": "🟢 أخضر", "danger": "🔴 أحمر", "": "⚪ افتراضي"}

    text = "🌍 <b>لون أزرار الدول</b>\n\n"
    text += f"اللون الحالي: <b>{color_names.get(current, '⚪ افتراضي')}</b>\n\n"
    text += "اختر اللون الجديد:"

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("🔵 أزرق", "colors_co:sc:primary"))
    kb.add(btn("🟢 أخضر", "colors_co:sc:success"))
    kb.add(btn("🔴 أحمر", "colors_co:sc:danger"))
    kb.add(btn("⚪ افتراضي", "colors_co:sc:"))
    kb.add(btn("⬅️ رجوع", "admin:colors_pl_co", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: c.data.startswith("colors_co:sc:"))
def cb_colors_co_set(call):
    if not user_is_admin(call.from_user.id): return
    style = call.data.split(":", 2)[2]
    setting_set("country_list_style", style)
    try:
        bot.answer_callback_query(call.id, "✅ تم حفظ لون الدول!")
    except Exception:
        pass
    cb_colors_co_view(call)


# ============================================================
# 📱 لوحة تخصيص المنصات والدول
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "admin:custom_pl_co")
def cb_admin_custom_pl_co(call):
    if not user_is_admin(call.from_user.id): return

    text = "📱 <b>تخصيص المنصات والدول</b>\n\n"
    text += "اختر القسم الذي تريد تخصيصه:"
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("🗂 أزرار المنصات (واتساب، تيليجرام...)", "admin:edit_platforms", BTN.PRIMARY))
    kb.add(btn("🌍 أزرار الدول (اليمن، مصر...)", "admin:edit_countries", BTN.SUCCESS))
    kb.add(btn("⬅️ رجوع", "admin:home", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


# ============================================================
# 🗂 تخصيص أزرار المنصات (الاسم + الإيموجي + اللون)
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "admin:edit_platforms")
def cb_admin_edit_platforms(call):
    if not user_is_admin(call.from_user.id): return

    platforms = numbers_platforms()
    if not platforms:
        bot.answer_callback_query(call.id, "لا توجد منصات مضافة.", show_alert=True)
        return

    text = "🗂 <b>أزرار المنصات</b>\n\n"
    text += "اضغط على المنصة لتعديل (الاسم / الإيموجي / اللون):"

    kb = InlineKeyboardMarkup(row_width=1)
    color_dots = {"primary": "🔵", "success": "🟢", "danger": "🔴", "": "⚪"}

    for p in platforms:
        custom_label = setting_get("platform_btn_label_" + p, "")
        custom_icon = setting_get("platform_emoji_" + p, PLATFORM_ICONS.get(p, "📱"))
        custom_style = setting_get("platform_btn_style_" + p, "")
        dot = color_dots.get(custom_style, "⚪")
        
        display = f"{custom_icon} {custom_label or p} | {dot}"
        kb.add(btn(display, "ep:v:" + p))

    kb.add(btn("⬅️ رجوع", "admin:custom_pl_co", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("ep:v:"))
def cb_ep_view(call):
    if not user_is_admin(call.from_user.id): return
    platform = call.data.split(":", 2)[2]

    custom_label = setting_get("platform_btn_label_" + platform, "")
    custom_icon = setting_get("platform_emoji_" + platform, PLATFORM_ICONS.get(platform, "📱"))
    custom_style = setting_get("platform_btn_style_" + platform, "")
    
    color_names = {"primary": "🔵 أزرق", "success": "🟢 أخضر", "danger": "🔴 أحمر", "": "⚪ افتراضي"}

    text = f"🗂 <b>تخصيص منصة: {platform}</b>\n\n"
    text += f"📝 الاسم: <b>{custom_label or platform}</b>\n"
    text += f"😀 الإيموجي: <b>{custom_icon}</b>\n"
    text += f"🎨 اللون: <b>{color_names.get(custom_style, '⚪ افتراضي')}</b>"

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("✏️ تغيير الاسم", "ep:edit:" + platform + ":label", BTN.PRIMARY))
    kb.add(btn("😀 تغيير الإيموجي", "ep:edit:" + platform + ":icon", BTN.PRIMARY))
    kb.add(btn("🎨 تغيير اللون", "ep:color:" + platform, BTN.SUCCESS))
    kb.add(btn("🔄 إعادة تعيين", "ep:reset:" + platform, BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "admin:edit_platforms", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("ep:edit:"))
def cb_ep_edit(call):
    if not user_is_admin(call.from_user.id): return
    parts = call.data.split(":", 3)
    platform = parts[2]
    field = parts[3]

    set_state(call.from_user.id, "ep_edit_field", {"platform": platform, "field": field})
    
    if field == "label":
        prompt = f"📝 أرسل الاسم الجديد للمنصة <b>{platform}</b>:"
    else:
        prompt = f"😀 أرسل الإيموجي الجديد للمنصة <b>{platform}</b>:"
        
    bot.send_message(call.message.chat.id, prompt + "\n\n/cancel للإلغاء", parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "ep_edit_field")
def handle_ep_edit_field(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    txt = (msg.text or "").strip()
    if not txt: return
    if txt == "/cancel":
        clear_state(uid)
        bot.send_message(msg.chat.id, "❌ تم الإلغاء")
        return

    s = get_state(uid)
    platform = s["data"].get("platform")
    field = s["data"].get("field")

    if field == "label":
        setting_set("platform_btn_label_" + platform, txt)
    else:
        setting_set("platform_emoji_" + platform, txt)

    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم الحفظ بنجاح!")


@bot.callback_query_handler(func=lambda c: c.data.startswith("ep:color:"))
def cb_ep_color(call):
    if not user_is_admin(call.from_user.id): return
    platform = call.data.split(":", 2)[2]

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("🔵 أزرق", "ep:sc:" + platform + ":primary"))
    kb.add(btn("🟢 أخضر", "ep:sc:" + platform + ":success"))
    kb.add(btn("🔴 أحمر", "ep:sc:" + platform + ":danger"))
    kb.add(btn("⚪ افتراضي", "ep:sc:" + platform + ":"))
    kb.add(btn("⬅️ رجوع", "ep:v:" + platform, BTN.DANGER))

    try:
        bot.edit_message_text("🎨 اختر اللون:", call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, "🎨 اختر اللون:", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ep:sc:"))
def cb_ep_set_color(call):
    if not user_is_admin(call.from_user.id): return
    parts = call.data.split(":", 3)
    platform = parts[2]
    style = parts[3]
    
    setting_set("platform_btn_style_" + platform, style)
    try:
        bot.answer_callback_query(call.id, "✅ تم الحفظ")
    except Exception:
        pass
    call.data = "ep:v:" + platform
    cb_ep_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ep:reset:"))
def cb_ep_reset(call):
    if not user_is_admin(call.from_user.id): return
    platform = call.data.split(":", 2)[2]
    
    setting_set("platform_btn_label_" + platform, "")
    setting_set("platform_emoji_" + platform, "")
    setting_set("platform_btn_style_" + platform, "")
    
    try:
        bot.answer_callback_query(call.id, "✅ تم إعادة التعيين", show_alert=True)
    except Exception:
        pass
    call.data = "ep:v:" + platform
    cb_ep_view(call)


# ============================================================
# 🌍 تخصيص أزرار الدول (الاسم + الإيموجي + اللون)
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "admin:edit_countries")
def cb_admin_edit_countries(call):
    if not user_is_admin(call.from_user.id): return

    try:
        conn = db()
        rows = conn.execute("SELECT DISTINCT country FROM numbers WHERE country != '' ORDER BY country").fetchall()
        conn.close()
        countries = [r["country"] for r in rows]
    except Exception:
        countries = []

    if not countries:
        bot.answer_callback_query(call.id, "لا توجد دول مضافة.", show_alert=True)
        return

    text = "🌍 <b>أزرار الدول</b>\n\n"
    text += "اضغط على الدولة لتعديل (الاسم / الإيموجي / اللون):"

    kb = InlineKeyboardMarkup(row_width=1)
    color_dots = {"primary": "🔵", "success": "🟢", "danger": "🔴", "": "⚪"}

    for co in countries[:30]:  # حد أقصى 30 عشان ما يزحمش
        custom_label = setting_get("country_btn_label_" + co, "")
        custom_icon = setting_get("country_emoji_" + co, "🌍")
        custom_style = setting_get("country_btn_style_" + co, "")
        dot = color_dots.get(custom_style, "⚪")
        
        display = f"{custom_icon} {custom_label or co} | {dot}"
        kb.add(btn(display, "ec:v:" + co))

    kb.add(btn("⬅️ رجوع", "admin:custom_pl_co", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("ec:v:"))
def cb_ec_view(call):
    if not user_is_admin(call.from_user.id): return
    country = call.data.split(":", 2)[2]

    custom_label = setting_get("country_btn_label_" + country, "")
    custom_icon = setting_get("country_emoji_" + country, "🌍")
    custom_style = setting_get("country_btn_style_" + country, "")
    
    color_names = {"primary": "🔵 أزرق", "success": "🟢 أخضر", "danger": "🔴 أحمر", "": "⚪ افتراضي"}

    text = f"🌍 <b>تخصيص دولة: {country}</b>\n\n"
    text += f"📝 الاسم: <b>{custom_label or country}</b>\n"
    text += f"😀 الإيموجي: <b>{custom_icon}</b>\n"
    text += f"🎨 اللون: <b>{color_names.get(custom_style, '⚪ افتراضي')}</b>"

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("✏️ تغيير الاسم", "ec:edit:" + country + ":label", BTN.PRIMARY))
    kb.add(btn("😀 تغيير الإيموجي", "ec:edit:" + country + ":icon", BTN.PRIMARY))
    kb.add(btn("🎨 تغيير اللون", "ec:color:" + country, BTN.SUCCESS))
    kb.add(btn("🔄 إعادة تعيين", "ec:reset:" + country, BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "admin:edit_countries", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("ec:edit:"))
def cb_ec_edit(call):
    if not user_is_admin(call.from_user.id): return
    parts = call.data.split(":", 3)
    country = parts[2]
    field = parts[3]

    set_state(call.from_user.id, "ec_edit_field", {"country": country, "field": field})
    
    if field == "label":
        prompt = f"📝 أرسل الاسم الجديد للدولة <b>{country}</b>:"
    else:
        prompt = f"😀 أرسل الإيموجي الجديد للدولة <b>{country}</b>:"
        
    bot.send_message(call.message.chat.id, prompt + "\n\n/cancel للإلغاء", parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "ec_edit_field")
def handle_ec_edit_field(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    txt = (msg.text or "").strip()
    if not txt: return
    if txt == "/cancel":
        clear_state(uid)
        bot.send_message(msg.chat.id, "❌ تم الإلغاء")
        return

    s = get_state(uid)
    country = s["data"].get("country")
    field = s["data"].get("field")

    if field == "label":
        setting_set("country_btn_label_" + country, txt)
    else:
        setting_set("country_emoji_" + country, txt)

    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم الحفظ بنجاح!")


@bot.callback_query_handler(func=lambda c: c.data.startswith("ec:color:"))
def cb_ec_color(call):
    if not user_is_admin(call.from_user.id): return
    country = call.data.split(":", 2)[2]

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("🔵 أزرق", "ec:sc:" + country + ":primary"))
    kb.add(btn("🟢 أخضر", "ec:sc:" + country + ":success"))
    kb.add(btn("🔴 أحمر", "ec:sc:" + country + ":danger"))
    kb.add(btn("⚪ افتراضي", "ec:sc:" + country + ":"))
    kb.add(btn("⬅️ رجوع", "ec:v:" + country, BTN.DANGER))

    try:
        bot.edit_message_text("🎨 اختر اللون:", call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, "🎨 اختر اللون:", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ec:sc:"))
def cb_ec_set_color(call):
    if not user_is_admin(call.from_user.id): return
    parts = call.data.split(":", 3)
    country = parts[2]
    style = parts[3]
    
    setting_set("country_btn_style_" + country, style)
    try:
        bot.answer_callback_query(call.id, "✅ تم الحفظ")
    except Exception:
        pass
    call.data = "ec:v:" + country
    cb_ec_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ec:reset:"))
def cb_ec_reset(call):
    if not user_is_admin(call.from_user.id): return
    country = call.data.split(":", 2)[2]
    
    setting_set("country_btn_label_" + country, "")
    setting_set("country_emoji_" + country, "")
    setting_set("country_btn_style_" + country, "")
    
    try:
        bot.answer_callback_query(call.id, "✅ تم إعادة التعيين", show_alert=True)
    except Exception:
        pass
    call.data = "ec:v:" + country
    cb_ec_view(call)



@bot.callback_query_handler(func=lambda c: c.data == "num:upload_new")
def cb_num_upload_new(call):
    if not user_is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "num_upload_new_platform", {})
    bot.send_message(call.message.chat.id,
        "📝 أرسل <b>اسم المنصة الجديدة</b> (مثال: تيليجرام أو Telegram):\n\n"
        "/cancel للإلغاء", parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "num_upload_new_platform")
def handle_num_upload_new_platform(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    txt = (msg.text or "").strip()
    if not txt:
        return
    if txt == "/cancel":
        clear_state(uid)
        bot.send_message(msg.chat.id, "❌ تم الإلغاء")
        return
    
    # ننتقل لاختيار اللوحة
    set_state(uid, "num_upload", {"platform": txt, "step": "panel"})
    
    # عرض قائمة اللوحات
    panels = panels_list()
    if not panels:
        set_state(uid, "num_upload", {"platform": txt, "step": "file"})
        bot.send_message(msg.chat.id,
            f"📥 <b>{txt}</b>\n\n"
            f"1) أرسل ملف .txt\n"
            f"2) أو الصق الأرقام هنا\n\n"
            f"/cancel للإلغاء", parse_mode="HTML")
        return
    
    kb = InlineKeyboardMarkup(row_width=1)
    for p in panels:
        kb.add(btn("📡 " + p["name"], "num_upload_panel:" + str(p["id"]) + ":" + txt))
    kb.add(btn("🚫 بدون لوحة", "num_upload_panel:0:" + txt))
    bot.send_message(msg.chat.id, "📡 اختر اللوحة التي تنتمي إليها هذه الأرقام:", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == "admin:home")
def cb_admin_home(call):
    if not user_is_admin(call.from_user.id):
        return
    admin_panel(call.message.chat.id, call.from_user.id, call.message)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:f:"))
def cb_ap_fetch(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return
    p = panel_get(pid)
    if not p:
        return
    ok, codes, err = fetch_panel(p)
    if ok:
        n = process_panel_codes(p, codes)
        panel_update(pid, last_fetch=time.time(), last_count=len(codes), last_status="ok")
        text = "✅ تم السحب\n📊 " + str(len(codes)) + " كود\n✨ جديد: " + str(n)
    else:
        text = "❌ فشل: " + err
    bot.send_message(call.message.chat.id, text)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:tg:"))
def cb_ap_toggle(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return
    
    p = panel_get(pid)
    was_enabled = p.get("enabled") if p else 0
    
    # تبديل حالة اللوحة
    panel_toggle(pid)
    
    # تحديث الساعة في الداتابيز
    conn = db()
    now = time.time()
    row = conn.execute("SELECT * FROM panel_uptime WHERE panel_id=?", (pid,)).fetchone()
    
    if was_enabled:
        # إيقاف اللوحة
        if row and row["is_running"] == 1:
            uptime_so_far = now - row["started_at"] - row["total_paused"]
            conn.execute("UPDATE panel_uptime SET is_running=0, stopped_at=?, total_paused=? WHERE panel_id=?", (now, 0, pid))
    else:
        # تشغيل اللوحة
        if row and row["is_running"] == 0:
            conn.execute("UPDATE panel_uptime SET is_running=1, stopped_at=0 WHERE panel_id=?", (pid,))
        elif not row:
            conn.execute("INSERT INTO panel_uptime (panel_id, started_at, stopped_at, total_paused, is_running) VALUES (?, ?, 0, 0, 1)", (pid, now))
            
    conn.commit()
    conn.close()
    
    cb_ap_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:d:"))
def cb_ap_del(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return
    panel_delete(pid)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_admin_panels(call)


# إضافة لوحة
@bot.callback_query_handler(func=lambda c: c.data == "ap:testall")
def cb_ap_testall(call):
    if not user_is_admin(call.from_user.id):
        return
    panels = panels_list()
    if not panels:
        return
    bot.answer_callback_query(call.id, "جاري الفحص...")
    lines = []
    ok_count = 0
    for p in panels:
        r = test_panel(p["id"])
        if r["ok"]:
            ok_count += 1
            lines.append("✅ " + p["name"] + " — " + str(r["count"]))
        else:
            lines.append("❌ " + p["name"] + " — " + (r.get("error") or "")[:40])
    text = "🔍 <b>نتيجة الفحص</b>\n\n" + "عدد الناجحة: " + str(ok_count) + "/" + str(len(panels)) + "\n\n" + "\n".join(lines)
    bot.send_message(call.message.chat.id, text)


@bot.callback_query_handler(func=lambda c: c.data == "ap:fetchall")
def cb_ap_fetchall(call):
    if not user_is_admin(call.from_user.id):
        return
    bot.answer_callback_query(call.id, "جاري السحب...")
    total_new = 0
    total = 0
    for p in panels_list(only_enabled=True):
        ok, codes, err = fetch_panel(p)
        if ok:
            n = process_panel_codes(p, codes)
            total_new += n
            total += len(codes)
            panel_update(p["id"], last_fetch=time.time(), last_count=len(codes), last_status="ok")
    bot.send_message(call.message.chat.id,
        "🔄 تم السحب\n📊 إجمالي: " + str(total) + "\n✨ جديد: " + str(total_new))


# المستخدمين
@bot.callback_query_handler(func=lambda c: c.data == "admin:users")
def cb_admin_users(call):
    if not user_is_admin(call.from_user.id):
        return
    users = users_all(20)
    text = "👥 <b>المستخدمين</b>\n\nإجمالي: " + str(users_count()) + "\n\n"
    for u in users[:10]:
        text += "• <code>" + str(u["telegram_id"]) + "</code> — " + (u.get("display_name") or "?")[:20] + "\n"
    kb = InlineKeyboardMarkup()
    kb.add(btn("⬅️ رجوع", "admin:home"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


# الأكواد
@bot.callback_query_handler(func=lambda c: c.data == "admin:codes")
def cb_admin_codes(call):
    if not user_is_admin(call.from_user.id):
        return
    kb = InlineKeyboardMarkup(row_width=1)

    old_status = "✅ مفعل" if setting_get("block_old_codes", "1") == "1" else "❌ معطل"
    kb.add(btn("🛡 منع الأكواد القديمة: " + old_status, "admin:toggle_old", BTN.PRIMARY))
    kb.add(btn("🧹 تنظيف القناة", "admin:auto_delete", BTN.PRIMARY))
    kb.add(btn("🗑 مسح كل الأكواد", "admin:codes_clear", BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    text = "💬 <b>الأكواد</b>\n\nإجمالي: " + str(codes_count())
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == "admin:codes_clear")
def cb_admin_codes_clear(call):
    if not user_is_admin(call.from_user.id):
        return
    codes_clear()
    bot.answer_callback_query(call.id, "تم المسح")
    cb_admin_codes(call)


# إحصائيات
@bot.callback_query_handler(func=lambda c: c.data == "admin:stats")
def cb_admin_stats(call):
    if not user_is_admin(call.from_user.id):
        return
    text = ("📊 <b>الإحصائيات</b>\n\n"
            "👥 المستخدمين: " + str(users_count()) + "\n"
            "💬 الأكواد: " + str(codes_count()) + "\n"
            "📱 الأرقام: " + str(numbers_count()) + "\n"
            "📡 اللوحات: " + str(len(panels_list())) + "\n"
            "🌍 المنصات: " + str(len(numbers_platforms())))
    kb = InlineKeyboardMarkup()
    kb.add(btn("🔄 تحديث", "admin:stats"))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


# ============================================================
# الأوامر الإضافية
# ============================================================
@bot.message_handler(commands=["id"])
def cmd_id(msg):
    bot.send_message(msg.chat.id, "🆔 <code>" + str(msg.from_user.id) + "</code>")


@bot.message_handler(commands=["status"])
def cmd_status(msg):
    if not user_is_admin(msg.from_user.id):
        return
    text = ("🤖 <b>حالة البوت</b>\n\n"
            "✅ يعمل\n"
            "📅 " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n"
            "🔄 دورات: " + str(POLLER_STATE.get("cycles", 0)))
    bot.send_message(msg.chat.id, text)


# ============================================================
# fallback
# ============================================================



# ============================================================
# تشغيل
# ============================================================


# ============================================================
# إدارة الأرقام (للأدمن)
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "admin:numbers")
def cb_admin_numbers(call):
    if not user_is_admin(call.from_user.id):
        return
    text = ("📱 <b>إدارة الأرقام</b>\n\n"
            "📊 إجمالي: " + str(numbers_count()) + "\n"
            "📁 منصات: " + str(len(numbers_platforms())))
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("➕ إضافة رقم يدوياً", "num:add", BTN.SUCCESS))
    kb.add(btn("📁 رفع/لصق أرقام", "num:upload", BTN.PRIMARY))
    kb.add(btn(" عرض المنصات", "num:list"))
    kb.add(btn("🗑 حذف كل الأرقام", "num:clearall", BTN.DANGER))
    kb.add(btn("🎨 ألوان أزرار الأرقام", "admin:num_colors", key="btn_num_colors"))
    kb.add(btn("📱 إيموجي المنصات", "admin:platform_emoji", key="btn_plat_emoji"))
    kb.add(btn("🌍 إيموجي الدول", "admin:country_emoji", key="btn_country_emoji"))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



@bot.callback_query_handler(func=lambda c: c.data == "admin:num_colors" or c.data.startswith("nc:"))
def cb_num_colors(call):
    if not user_is_admin(call.from_user.id): return
    
    if call.data.startswith("nc:mode:"):
        mode = call.data.split(":")[2]
        setting_set("numbers_color_mode", mode)
        bot.answer_callback_query(call.id, "تم التغيير")
        call.data = "admin:num_colors"
        return cb_num_colors(call)
        
    if call.data.startswith("nc:color:"):
        color = call.data.split(":")[2]
        setting_set("numbers_static_color", color)
        bot.answer_callback_query(call.id, "تم التغيير")
        call.data = "admin:num_colors"
        return cb_num_colors(call)
    
    mode = setting_get("numbers_color_mode", "static")
    color = setting_get("numbers_static_color", "success")
    
    color_names = {"success": "🟢 أخضر", "primary": "🔵 أزرق", "danger": "🔴 أحمر"}
    
    nl = chr(10)
    text = "🎨 <b>ألوان أزرار الأرقام</b>" + nl
    text += "━━━━━━━━━━━━━━━━━━" + nl
    text += "الوضع الحالي: <b>" + ("تلقائي متغير" if mode == "auto" else "ثابت") + "</b>" + nl
    if mode == "static":
        text += "اللون الحالي: <b>" + color_names.get(color, color) + "</b>" + nl
    text += "━━━━━━━━━━━━━━━━━━"
    
    kb = InlineKeyboardMarkup(row_width=1)
    if mode == "static":
        kb.add(btn("🔄 تحويل إلى تلقائي (متغير)", "nc:mode:auto", BTN.PRIMARY))
    else:
        kb.add(btn("⏹ تحويل إلى ثابت", "nc:mode:static", BTN.SUCCESS))
        
    if mode == "static":
        kb.add(btn("🟢 أخضر", "nc:color:success"))
        kb.add(btn("🔵 أزرق", "nc:color:primary"))
        kb.add(btn("🔴 أحمر", "nc:color:danger"))
        
    kb.add(btn("⬅️ رجوع", "admin:numbers"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == "num:add")
def cb_num_add(call):
    if not user_is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "num_add", {"step": "platform"})
    bot.send_message(call.message.chat.id, "📝 أرسل اسم المنصة (مثال: واتساب)\n/cancel للإلغاء")



@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "num_add")
def handle_num_add(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    s = get_state(uid)
    step = s["data"].get("step")
    txt = (msg.text or "").strip()
    if not txt:
        return
    if step == "platform":
        s["data"]["platform"] = txt
        s["data"]["step"] = "phone"
        set_state(uid, "num_add", s["data"])
        bot.send_message(msg.chat.id, "📱 أرسل الرقم (مع +)")
    elif step == "phone":
        platform = s["data"].get("platform", "أخرى")
        phone = txt if txt.startswith("+") else "+" + txt
        iso, cname, code = detect_country(phone)
        
        # حفظ الرقم مؤقتاً والانتقال لاختيار اللوحة
        s["data"]["phone"] = phone
        s["data"]["cname"] = cname
        s["data"]["step"] = "panel"
        set_state(uid, "num_add", s["data"])
        
        # عرض قائمة اللوحات
        panels = panels_list()
        if not panels:
            # لو مفيش لوحات، نضيف الرقم بدون لوحة
            number_add(platform, cname, phone)
            clear_state(uid)
            bot.send_message(msg.chat.id, "✅ تمت الإضافة (بدون ربط بلوحة)\n📱 " + platform + "\n🌍 " + cname + "\n☎️ " + phone)
            return
        
        kb = InlineKeyboardMarkup(row_width=1)
        for p in panels:
            kb.add(btn("📡 " + p["name"], "num_panel:" + str(p["id"])))
        kb.add(btn("🚫 بدون لوحة", "num_panel:0"))
        bot.send_message(msg.chat.id, "📡 اختر اللوحة التي ينتمي إليها هذا الرقم:", reply_markup=kb)
        
    elif step == "panel":
        pass # سيتم التعامل معها عبر callback


@bot.callback_query_handler(func=lambda c: c.data == "num:list")
def cb_num_list(call):
    if not user_is_admin(call.from_user.id):
        return
    platforms = numbers_platforms()
    if not platforms:
        kb = InlineKeyboardMarkup()
        kb.add(btn("⬅️ رجوع", "admin:numbers"))
        try:
            bot.edit_message_text("لا توجد منصات", call.message.chat.id, call.message.message_id, reply_markup=kb)
        except Exception:
            bot.send_message(call.message.chat.id, "لا توجد منصات", reply_markup=kb)
        return
    kb = InlineKeyboardMarkup(row_width=1)
    for p in platforms:
        cnt = len(numbers_list(platform=p))
        kb.add(btn("📱 " + p + " (" + str(cnt) + ")", "num:vp:" + p))
    kb.add(btn("⬅️ رجوع", "admin:numbers"))
    try:
        bot.edit_message_text(" اختر منصة:", call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, " اختر منصة:", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("num:vp:"))
def cb_num_view_platform(call):
    if not user_is_admin(call.from_user.id):
        return
    platform = call.data.split(":", 2)[2]
    countries = numbers_countries(platform)
    kb = InlineKeyboardMarkup(row_width=1)
    for co in countries:
        cnt = len(numbers_list(platform=platform, country=co))
        kb.add(btn("🌍 " + co + " (" + str(cnt) + ")", "num:vc:" + platform + ":" + co))
    kb.add(btn("🗑 حذف المنصة كاملة", "num:dp:" + platform, BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "num:list"))
    try:
        bot.edit_message_text("📱 " + platform + " — اختر دولة:", call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, "📱 " + platform, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("num:vc:"))
def cb_num_view_country(call):
    if not user_is_admin(call.from_user.id):
        return
    parts = call.data.split(":", 3)
    platform, country = parts[2], parts[3]
    nums = numbers_list(platform=platform, country=country)
    text = "🌍 <b>" + country + "</b> — " + platform + "\n\n"
    for n in nums[:20]:
        text += "• <code>" + n["phone"] + "</code>\n"
    kb = InlineKeyboardMarkup(row_width=1)
    for n in nums[:5]:
        kb.add(btn("🗑 " + n["phone"][-8:], "num:dn:" + str(n["id"]), BTN.DANGER))
    kb.add(btn("🗑 حذف كل الأرقام", "num:dc:" + platform + ":" + country, BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "num:vp:" + platform))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("num:dn:"))
def cb_num_del_number(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        nid = int(call.data.split(":")[2])
    except Exception:
        return
    number_delete(nid)
    try:
        bot.answer_callback_query(call.id, "تم الحذف")
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("num:dc:"))
def cb_num_del_country(call):
    if not user_is_admin(call.from_user.id):
        return
    parts = call.data.split(":", 3)
    platform, country = parts[2], parts[3]
    conn = db()
    conn.execute("DELETE FROM numbers WHERE platform=? AND country=?", (platform, country))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "تم الحذف")


@bot.callback_query_handler(func=lambda c: c.data.startswith("num:dp:"))
def cb_num_del_platform(call):
    if not user_is_admin(call.from_user.id):
        return
    platform = call.data.split(":", 2)[2]
    conn = db()
    conn.execute("DELETE FROM numbers WHERE platform=?", (platform,))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "تم الحذف")


@bot.callback_query_handler(func=lambda c: c.data == "num:clearall")
def cb_num_clearall(call):
    if not user_is_admin(call.from_user.id):
        return
    conn = db()
    conn.execute("DELETE FROM numbers")
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "تم حذف كل الأرقام")



# ============================================================
# الصيانة + الإشعار الجماعي + النسخ الاحتياطي
# ============================================================


@bot.callback_query_handler(func=lambda c: c.data == "admin:maintenance")
def cb_admin_maintenance(call):
    if not user_is_admin(call.from_user.id):
        return
    on = is_maintenance()
    text = "🚫 <b>الصيانة</b>\n\nالحالة: " + ("مفعّلة" if on else "معطّلة")
    kb = InlineKeyboardMarkup(row_width=1)
    if on:
        kb.add(btn("✅ إيقاف الصيانة", "maint:off", BTN.SUCCESS))
    else:
        kb.add(btn("🚫 تفعيل الصيانة", "maint:on", BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == "maint:on")
def cb_maint_on(call):
    if not user_is_admin(call.from_user.id):
        return
    setting_set("maintenance", "1")
    bot.answer_callback_query(call.id, "تم تفعيل الصيانة")
    cb_admin_maintenance(call)


@bot.callback_query_handler(func=lambda c: c.data == "maint:off")
def cb_maint_off(call):
    if not user_is_admin(call.from_user.id):
        return
    setting_set("maintenance", "0")
    bot.answer_callback_query(call.id, "تم إيقاف الصيانة")
    cb_admin_maintenance(call)


@bot.callback_query_handler(func=lambda c: c.data == "admin:broadcast")
def cb_admin_broadcast(call):
    if not user_is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "broadcast", {})
    bot.send_message(call.message.chat.id, "📢 أرسل نص الإشعار الجماعي\n/cancel للإلغاء")


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "broadcast")
def handle_broadcast(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    text = (msg.text or "").strip()
    if not text:
        return
    clear_state(uid)
    users = users_all(10000)
    sent = 0
    failed = 0
    for u in users:
        if u.get("is_banned"):
            continue
        try:
            bot.send_message(u["telegram_id"], "📢 <b>إشعار</b>\n\n" + text)
            sent += 1
            time.sleep(0.05)
        except Exception:
            failed += 1
    bot.send_message(msg.chat.id, "✅ تم الإرسال\n✅ ناجح: " + str(sent) + "\n❌ فشل: " + str(failed))


@bot.callback_query_handler(func=lambda c: c.data == "admin:backup")
def cb_admin_backup(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        import zipfile
        fname = "data/backup_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".zip"
        with zipfile.ZipFile(fname, "w", zipfile.ZIP_DEFLATED) as z:
            if os.path.exists(DB_FILE):
                z.write(DB_FILE, "bot.db")
        with open(fname, "rb") as f:
            bot.send_document(call.message.chat.id, f)
        os.remove(fname)
        bot.answer_callback_query(call.id, "تم")
    except Exception as e:
        bot.answer_callback_query(call.id, "خطأ: " + str(e)[:50], show_alert=True)



# ============================================================
# إضافة لوحة — 9 مراحل كاملة
# ============================================================


@bot.callback_query_handler(func=lambda c: c.data == "admin:quick_guide")
def cb_quick_guide(call):
    if not user_is_admin(call.from_user.id): return
    
    nl = chr(10)
    guide = "📚 <b>دليل الإضافة السريعة (نص)</b>" + nl
    guide += "━━━━━━━━━━━━━━━━━━" + nl
    guide += "هنا تتعلم إزاي تلصق بيانات أي لوحة مرة واحدة، والبوت يفهمها ويضيفها." + nl
    guide += "━━━━━━━━━━━━━━━━━━" + nl
    guide += "📝 <b>الكلمات المفتاحية اللي البوت بيفهمها:</b>" + nl
    guide += "• <code>اسم</code> أو <code>name</code>: اسم اللوحة (إجباري)." + nl
    guide += "• <code>رابط</code> أو <code>url</code>: رابط اللوحة (إجباري)." + nl
    guide += "• <code>توكن</code> أو <code>token</code>: التوكن بتاعك." + nl
    guide += "• <code>مسار</code> أو <code>path</code>: مسار الأكواد (مثل /api/v1/codes)." + nl
    guide += "• <code>طريقة</code> أو <code>method</code>: GET أو POST." + nl
    guide += "• <code>كوكيز</code> أو <code>cookies</code>: لو اللوحة بتحتاج كوكيز." + nl
    guide += "• <code>هيدر</code> أو <code>headers</code>: لو اللوحة بتحتاج هيدرات إضافية." + nl
    guide += "• <code>user</code> و <code>pass</code>: اسم المستخدم والباسورد (لو اللوحة بتحتاج)." + nl
    guide += "━━━━━━━━━━━━━━━━━━" + nl
    guide += "💡 <b>مثال 1 (لوحة بسيطة):</b>" + nl
    guide += "<code>اسم: Palestine" + nl
    guide += "رابط: http://2.56.246.128:30194" + nl
    guide += "توكن: Palasten_ALGAML_MANO..." + nl
    guide += "مسار: /api/v1/numbers/{phone}/otp" + nl
    guide += "طريقة: POST</code>" + nl + nl
    guide += "💡 <b>مثال 2 (لوحة متقدمة):</b>" + nl
    guide += "<code>name: King" + nl
    guide += "url: http://145.239.69.111:20376" + nl
    guide += "token: ev7n..." + nl
    guide += "path: /api/v1/codes" + nl
    guide += "method: GET" + nl
    guide += "cookies: session=abc123; token=xyz</code>" + nl + nl
    guide += "⚠️ <b>ملاحظة:</b> كل سطر فيه نقطتين <code>:</code> أو يساوي <code>=</code> بين الكلمة والقيمة." + nl + nl
    guide += "👇 اضغط <b>⚡ الإضافة السريعة</b> عشان تبدأ."
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("⚡ الإضافة السريعة الآن", "admin:quick_add", BTN.SUCCESS))
    kb.add(btn("⬅️ رجوع", "admin:home", BTN.DANGER))
    
    try:
        bot.edit_message_text(guide, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, guide, reply_markup=kb, parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: c.data == "admin:quick_add")
def cb_quick_add(call):
    if not user_is_admin(call.from_user.id): return
    set_state(call.from_user.id, "quick_add_panel", {})
    msg = """⚡ <b>الإضافة السريعة (نص)</b>

أرسل بيانات اللوحة في رسالة واحدة، بأي شكل.

مثال:
<code>اسم: Palestine
رابط: http://2.56.246.128:30194
توكن: Palasten_ALGAML...
مسار: /api/v1/numbers/{phone}/otp
طريقة: POST</code>

/cancel للإلغاء"""
    bot.send_message(call.message.chat.id, msg, parse_mode="HTML")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "quick_add_panel")
def handle_quick_add(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    if (msg.text or "").strip() == "/cancel":
        clear_state(uid)
        bot.send_message(msg.chat.id, "❌ تم الإلغاء")
        return
        
    txt = msg.text
    if not txt:
        return
        
    data = {}
    lines = txt.split(chr(10))
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if ':' in line:
            parts = line.split(':', 1)
        elif '=' in line:
            parts = line.split('=', 1)
        else:
            continue
            
        key = parts[0].strip().lower()
        value = parts[1].strip()
        
        if key in ('اسم', 'name', 'الاسم'):
            data['name'] = value
        elif key in ('رابط', 'url', 'link', 'الرابط'):
            data['url'] = value
        elif key in ('توكن', 'token', 'api_key', 'key', 'التوكن'):
            data['token'] = value
        elif key in ('مسار', 'path', 'api_path', 'endpoint'):
            data['api_path'] = value
        elif key in ('طريقة', 'method', 'api_method', 'type'):
            data['api_method'] = value.upper()
        elif key in ('كوكيز', 'cookies', 'cookie'):
            data['cookies'] = value
        elif key in ('هيدر', 'headers', 'header'):
            data['headers'] = value
        elif key in ('username', 'user', 'اسم المستخدم'):
            data['username'] = value
        elif key in ('password', 'pass', 'كلمة المرور'):
            data['password'] = value
        elif key in ('json_path', 'json_path'):
            data['json_path'] = value

    if not data.get('name') or not data.get('url'):
        bot.send_message(msg.chat.id, "❌ لازم تحدد الاسم والرابط على الأقل.")
        return
    
    custom_headers = "[]"
    if data.get('headers'):
        headers_list = []
        for h in data['headers'].split(','):
            if ':' in h:
                hk, hv = h.split(':', 1)
                headers_list.append({"name": hk.strip(), "value": hv.strip()})
        custom_headers = json.dumps(headers_list)
        
    if data.get('cookies'):
        try:
            existing = json.loads(custom_headers)
            existing.append({"name": "Cookie", "value": data['cookies']})
            custom_headers = json.dumps(existing)
        except Exception:
            pass

    try:
        pid = panel_add(
            name=data.get('name', 'بدون اسم'),
            url=data.get('url', ''),
            token=data.get('token', ''),
            username=data.get('username', ''),
            password=data.get('password', ''),
            auth_type="token" if data.get('token') else ("basic" if data.get('username') else "none"),
            api_path=data.get('api_path', '/api/v1/codes'),
            api_method=data.get('api_method', 'GET'),
            json_path=data.get('json_path', ''),
            custom_headers=custom_headers,
        )
        clear_state(uid)
        
        kb = InlineKeyboardMarkup()
        kb.add(btn("🔍 فحص الآن", "ap:t:" + str(pid), BTN.SUCCESS))
        kb.add(btn("📋 قائمة اللوحات", "ap:list"))
        
        bot.send_message(msg.chat.id,
            f"✅ <b>تم إضافة اللوحة بنجاح!</b>\n"
            f"🆔 رقم: {pid}\n"
            f"📛 الاسم: {data.get('name')}\n"
            f"🔗 الرابط: {data.get('url')}\n"
            f"📁 المسار: {data.get('api_path')}\n"
            f"📡 الطريقة: {data.get('api_method')}",
            reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ خطأ: {str(e)[:100]}")

@bot.callback_query_handler(func=lambda c: c.data == "ap:add")
def cb_ap_add(call):
    if not user_is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "ap_add", {"step": 1, "data": {}})
    bot.send_message(call.message.chat.id,
        "➕ <b>إضافة لوحة جديدة</b>\n\n"
        "📝 الخطوة <b>1/9</b>: أرسل اسم اللوحة\n"
        "/cancel للإلغاء")


@bot.message_handler(commands=["cancel"])
def cmd_cancel(msg):
    clear_state(msg.from_user.id)
    bot.send_message(msg.chat.id, "❌ تم الإلغاء")


@bot.message_handler(commands=["skip"])
def cmd_skip(msg):
    uid = msg.from_user.id
    s = get_state(uid)
    if s.get("state") != "ap_add":
        return
    handle_ap_input(msg, force_value="")


@bot.message_handler(func=lambda m: (get_state(m.from_user.id).get("state") == "ap_add"
                                        and m.content_type == "text"))
def handle_ap_input(msg, force_value=None):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    s = get_state(uid)
    step = s["data"].get("step", 1)
    data = s["data"].get("data", {})
    txt = force_value if force_value is not None else (msg.text or "").strip()

    # ═══ المرحلة 1: الاسم ═══
    if step == 1:
        if not txt:
            bot.send_message(msg.chat.id, "الاسم فارغ. أعد المحاولة:")
            return
        data["name"] = txt
        s["data"]["step"] = 2
        s["data"]["data"] = data
        set_state(uid, "ap_add", s["data"])
        bot.send_message(msg.chat.id, "📝 الخطوة <b>2/9</b>: أرسل رابط اللوحة\nمثال: <code>http://78.154.103.39:11105</code>")

    # ═══ المرحلة 2: الرابط ═══
    elif step == 2:
        if not txt:
            bot.send_message(msg.chat.id, "الرابط فارغ. أعد المحاولة:")
            return
        if not txt.startswith("http"):
            txt = "http://" + txt
        data["url"] = txt.rstrip("/")
        s["data"]["step"] = 3
        s["data"]["data"] = data
        set_state(uid, "ap_add", s["data"])
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(btn("🔑 Token", "ap_auth:token", BTN.PRIMARY))
        kb.add(btn("👤 User + Pass", "ap_auth:basic"))
        kb.add(btn("🔑👤 Token + User/Pass", "ap_auth:both"))
        kb.add(btn("🛠 مخصص", "ap_auth:custom"))
        kb.add(btn("🚫 بدون", "ap_auth:none"))
        bot.send_message(msg.chat.id, "📝 الخطوة <b>3/9</b>: نوع المصادقة", reply_markup=kb)

    # ═══ المرحلة 3.5: الهيدر المخصص ═══
    elif step == 3.5:
        if txt and txt != "/skip":
            if ":" not in txt or not txt.split(":", 1)[0].strip():
                bot.send_message(msg.chat.id, "⚠️ الصيغة غير صحيحة. أرسلها هكذا:\n<code>X-API-Key: 12345</code>\nأو /skip للتخطي")
                return
            data["custom_header"] = txt
        s["data"]["step"] = 6
        s["data"]["data"] = data
        set_state(uid, "ap_add", s["data"])
        bot.send_message(msg.chat.id, "📝 الخطوة <b>6/9</b>: مسار الأكواد\nمثال: <code>/api/v1/codes</code>\nأو /skip")

    # ═══ المرحلة 4: التوكن ═══
    elif step == 4:
        data["token"] = txt
        if data.get("auth_type") == "both":
            s["data"]["step"] = 5
            s["data"]["data"] = data
            set_state(uid, "ap_add", s["data"])
            bot.send_message(msg.chat.id, "📝 الخطوة <b>5/9</b>: أرسل اسم المستخدم")
        else:
            s["data"]["step"] = 6
            s["data"]["data"] = data
            set_state(uid, "ap_add", s["data"])
            bot.send_message(msg.chat.id, "📝 الخطوة <b>6/9</b>: مسار الأكواد\nمثال: <code>/api/v1/codes</code>\nأو /skip")

    # ═══ المرحلة 5: اسم المستخدم (basic) ═══
    elif step == 5:
        data["username"] = txt
        s["data"]["step"] = 5.5
        s["data"]["data"] = data
        set_state(uid, "ap_add", s["data"])
        bot.send_message(msg.chat.id, "📝 أرسل كلمة المرور")

    elif step == 5.5:
        data["password"] = txt
        s["data"]["step"] = 6
        s["data"]["data"] = data
        set_state(uid, "ap_add", s["data"])
        bot.send_message(msg.chat.id, "📝 الخطوة <b>6/9</b>: مسار الأكواد\nأو /skip")

    # ═══ المرحلة 6: المسار ═══
    elif step == 6:
        data["api_path"] = txt
        s["data"]["step"] = 7
        s["data"]["data"] = data
        set_state(uid, "ap_add", s["data"])
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(btn("GET", "ap_m:GET", BTN.PRIMARY), btn("POST", "ap_m:POST"))
        bot.send_message(msg.chat.id, "📝 الخطوة <b>7/9</b>: طريقة الطلب", reply_markup=kb)

    # ═══ المرحلة 8: مسار JSON ═══
    elif step == 8:
        data["json_path"] = txt
        s["data"]["step"] = 9
        s["data"]["data"] = data
        set_state(uid, "ap_add", s["data"])
        bot.send_message(msg.chat.id,
            "📝 الخطوة <b>9/9</b>: أسماء الحقول (اختياري)\n\n"
            "أرسل بصيغة:\n"
            "<code>phone:phone_number,code:otp_code,platform:app_name</code>\n\n"
            "أو /skip للافتراضي")

    # ═══ المرحلة 9: الحقول — إنهاء ═══
    elif step == 9:
        if txt:
            try:
                for part in txt.split(","):
                    if ":" in part:
                        k, v = part.split(":", 1)
                        k = k.strip()
                        v = v.strip()
                        if k in ("phone", "code", "platform", "country", "message"):
                            data["field_" + k] = v
            except Exception:
                pass
        data["interval_sec"] = 60

        _ch_json = "[]"
        if data.get("custom_header") and ":" in data["custom_header"]:
            _hk, _hv = data["custom_header"].split(":", 1)
            _ch_json = json.dumps([{"name": _hk.strip(), "value": _hv.strip()}])

        pid = panel_add(
            name=data.get("name", ""),
            url=data.get("url", ""),
            token=data.get("token", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
            auth_type=data.get("auth_type", "token"),
            api_path=data.get("api_path", ""),
            api_method=data.get("api_method", "GET"),
            json_path=data.get("json_path", ""),
            field_phone=data.get("field_phone", ""),
            field_code=data.get("field_code", ""),
            field_platform=data.get("field_platform", ""),
            field_country=data.get("field_country", ""),
            field_message=data.get("field_message", ""),
            interval_sec=60,
            custom_headers=_ch_json,
        )
        clear_state(uid)
        kb = InlineKeyboardMarkup()
        kb.add(btn("🔍 فحص الآن", "ap:t:" + str(pid), BTN.SUCCESS))
        kb.add(btn(" قائمة اللوحات", "ap:list"))
        bot.send_message(msg.chat.id,
            "✅ <b>تمت إضافة اللوحة</b>\n"
            "🆔 رقم: " + str(pid) + "\n\n"
            "جرّب الفحص للتحقق:",
            reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ap_auth:"))
def cb_ap_auth(call):
    uid = call.from_user.id
    if not user_is_admin(uid):
        return
    s = get_state(uid)
    if s.get("state") != "ap_add":
        return
    auth = call.data.split(":", 1)[1]
    data = s["data"]["data"]
    data["auth_type"] = auth

    if auth == "none":
        data["token"] = ""
        data["username"] = ""
        data["password"] = ""
        s["data"]["step"] = 6
        s["data"]["data"] = data
        set_state(uid, "ap_add", s["data"])
        bot.send_message(call.message.chat.id, "📝 الخطوة <b>6/9</b>: مسار الأكواد\nأو /skip")
    elif auth == "custom":
        s["data"]["step"] = 3.5
        s["data"]["data"] = data
        set_state(uid, "ap_add", s["data"])
        bot.send_message(call.message.chat.id, 
            "أرسل الهيدر بالشكل ده:\n"
            "<code>X-API-Key: YOUR_TOKEN_HERE</code>\n\n"
            "مثال:\n"
            "<code>X-API-Key: 12345abcdef</code>\n\n"
            "/skip للتخطي", 
            parse_mode="HTML")
    else:
        s["data"]["step"] = 4
        s["data"]["data"] = data
        set_state(uid, "ap_add", s["data"])
        bot.send_message(call.message.chat.id, "📝 الخطوة <b>4/9</b>: أرسل التوكن")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("ap_m:"))
def cb_ap_method(call):
    uid = call.from_user.id
    if not user_is_admin(uid):
        return
    s = get_state(uid)
    if s.get("state") != "ap_add":
        return
    method = call.data.split(":", 1)[1]
    data = s["data"]["data"]
    data["api_method"] = method
    s["data"]["step"] = 8
    s["data"]["data"] = data
    set_state(uid, "ap_add", s["data"])
    bot.send_message(call.message.chat.id, "📝 الخطوة <b>8/9</b>: مسار JSON\nأو /skip")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



# ============================================================
# المسابقات + الإعلانات + الإحصائيات
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "menu:contests")
def cb_contests(call):
    conn = db()
    rows = conn.execute("SELECT * FROM contests WHERE status='active' ORDER BY pinned DESC, created DESC").fetchall()
    conn.close()
    if not rows:
        text = "🎁 لا توجد مسابقات حالياً"
        kb = InlineKeyboardMarkup()
        kb.add(btn("⬅️ رجوع", "menu:home"))
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)
        return
    text = "🎁 <b>المسابقات</b>\n\n"
    kb = InlineKeyboardMarkup(row_width=1)
    for r in rows:
        icon = r["icon"] or "🎁"
        kb.add(btn(icon + " " + r["title"], "ct:" + str(r["id"])))
    kb.add(btn("⬅️ رجوع", "menu:home"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ct:"))
def cb_contest_view(call):
    try:
        cid = int(call.data.split(":")[1])
    except Exception:
        return
    conn = db()
    r = conn.execute("SELECT * FROM contests WHERE id=?", (cid,)).fetchone()
    conn.close()
    if not r:
        return
    votes = {}
    try:
        votes = json.loads(r["votes"] or "{}")
    except Exception:
        pass
    text = (r["icon"] or "🎁") + " <b>" + r["title"] + "</b>\n\n"
    if r["description"]:
        text += r["description"] + "\n\n"
    if r["prize"]:
        text += "🏆 الجائزة: " + r["prize"] + "\n\n"
    kb = InlineKeyboardMarkup(row_width=1)
    if votes:
        for key, opt in votes.items():
            cnt = opt.get("count", 0)
            kb.add(btn(opt.get("label", key) + " (" + str(cnt) + ")", "cv:" + str(cid) + ":" + key))
    kb.add(btn("⬅️ رجوع", "menu:contests"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("cv:"))
def cb_contest_vote(call):
    parts = call.data.split(":", 2)
    try:
        cid = int(parts[1])
    except Exception:
        return
    key = parts[2]
    uid = call.from_user.id
    conn = db()
    r = conn.execute("SELECT * FROM contests WHERE id=?", (cid,)).fetchone()
    if not r:
        conn.close()
        return
    voters = []
    try:
        voters = json.loads(r["voters"] or "[]")
    except Exception:
        pass
    if str(uid) in voters:
        conn.close()
        try:
            bot.answer_callback_query(call.id, "صوّت مسبقاً", show_alert=True)
        except Exception:
            pass
        return
    votes = {}
    try:
        votes = json.loads(r["votes"] or "{}")
    except Exception:
        pass
    if key not in votes:
        conn.close()
        return
    votes[key]["count"] = votes[key].get("count", 0) + 1
    voters.append(str(uid))
    conn.execute("UPDATE contests SET votes=?, voters=? WHERE id=?",
                 (json.dumps(votes, ensure_ascii=False), json.dumps(voters), cid))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ تم التصويت")
    cb_contest_view(call)


@bot.callback_query_handler(func=lambda c: c.data == "menu:ads")
def cb_ads(call):
    conn = db()
    rows = conn.execute("SELECT * FROM ads WHERE status='active' ORDER BY pinned DESC, created DESC LIMIT 10").fetchall()
    conn.close()
    if not rows:
        text = "📢 لا توجد إعلانات"
        kb = InlineKeyboardMarkup()
        kb.add(btn("⬅️ رجوع", "menu:home"))
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)
        return
    text = "📢 <b>الإعلانات</b>\n\n"
    kb = InlineKeyboardMarkup(row_width=1)
    for r in rows:
        kb.add(btn("📌 " + r["title"], "ad:" + str(r["id"])))
    kb.add(btn("⬅️ رجوع", "menu:home"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ad:"))
def cb_ad_view(call):
    try:
        aid = int(call.data.split(":")[1])
    except Exception:
        return
    conn = db()
    r = conn.execute("SELECT * FROM ads WHERE id=?", (aid,)).fetchone()
    conn.close()
    if not r:
        return
    text = "📢 <b>" + r["title"] + "</b>\n\n" + (r["body"] or "")
    kb = InlineKeyboardMarkup()
    if r["contact_url"]:
        kb.add(btn(r["contact_label"] or "تواصل", url=r["contact_url"]))
    kb.add(btn("⬅️ رجوع", "menu:ads"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


# ═══ إدارة المسابقات من الأدمن ═══
@bot.callback_query_handler(func=lambda c: c.data == "admin:contests")
def cb_admin_contests(call):
    if not user_is_admin(call.from_user.id):
        return
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("➕ إضافة مسابقة", "act:add", BTN.SUCCESS))
    kb.add(btn(" عرض المسابقات", "act:list"))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    text = "🎁 <b>إدارة المسابقات</b>"
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == "act:list")
def cb_act_list(call):
    if not user_is_admin(call.from_user.id):
        return
    conn = db()
    rows = conn.execute("SELECT * FROM contests ORDER BY created DESC LIMIT 20").fetchall()
    conn.close()
    kb = InlineKeyboardMarkup(row_width=1)
    for r in rows:
        kb.add(btn((r["icon"] or "🎁") + " " + r["title"], "act:v:" + str(r["id"])))
    kb.add(btn("⬅️ رجوع", "admin:contests"))
    try:
        bot.edit_message_text(" اختر مسابقة:", call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, " اختر مسابقة:", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("act:v:"))
def cb_act_view(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        cid = int(call.data.split(":")[2])
    except Exception:
        return
    conn = db()
    r = conn.execute("SELECT * FROM contests WHERE id=?", (cid,)).fetchone()
    conn.close()
    if not r:
        return
    text = "🎁 <b>" + r["title"] + "</b>\n📝 " + (r["description"] or "") + "\n🏆 " + (r["prize"] or "")
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("🗑 حذف", "act:d:" + str(cid), BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "act:list"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("act:d:"))
def cb_act_del(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        cid = int(call.data.split(":")[2])
    except Exception:
        return
    conn = db()
    conn.execute("DELETE FROM contests WHERE id=?", (cid,))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_act_list(call)


@bot.callback_query_handler(func=lambda c: c.data == "act:add")
def cb_act_add(call):
    if not user_is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "act_add", {"step": 1, "data": {}})
    bot.send_message(call.message.chat.id, "📝 الخطوة 1: أرسل عنوان المسابقة\n/cancel للإلغاء")


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "act_add")
def handle_act_add(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    s = get_state(uid)
    step = s["data"].get("step", 1)
    data = s["data"].get("data", {})
    txt = (msg.text or "").strip()

    if step == 1:
        data["title"] = txt
        s["data"]["step"] = 2
        s["data"]["data"] = data
        set_state(uid, "act_add", s["data"])
        bot.send_message(msg.chat.id, "📝 الخطوة 2: الوصف (أو /skip)")
    elif step == 2:
        data["description"] = txt
        s["data"]["step"] = 3
        s["data"]["data"] = data
        set_state(uid, "act_add", s["data"])
        bot.send_message(msg.chat.id, "📝 الخطوة 3: الجائزة (أو /skip)")
    elif step == 3:
        data["prize"] = txt
        s["data"]["step"] = 4
        s["data"]["data"] = data
        set_state(uid, "act_add", s["data"])
        bot.send_message(msg.chat.id, "📝 الخطوة 4: خيارات التصويت (فاصلة بينهم)\nمثال: خيار1,خيار2,خيار3")
    elif step == 4:
        options = [o.strip() for o in txt.split(",") if o.strip()]
        votes = {("opt" + str(i)): {"label": o, "count": 0} for i, o in enumerate(options)}
        conn = db()
        conn.execute(
            "INSERT INTO contests (title, description, prize, votes, voters, status, created) VALUES (?, ?, ?, ?, ?, 'active', ?)",
            (data.get("title", ""), data.get("description", ""), data.get("prize", ""),
             json.dumps(votes, ensure_ascii=False), "[]", time.time())
        )
        conn.commit()
        conn.close()
        clear_state(uid)
        bot.send_message(msg.chat.id, "✅ تمت إضافة المسابقة")


# ═══ إدارة الإعلانات ═══
@bot.callback_query_handler(func=lambda c: c.data == "admin:ads")
def cb_admin_ads(call):
    if not user_is_admin(call.from_user.id):
        return
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("➕ إضافة إعلان", "aad:add", BTN.SUCCESS))
    kb.add(btn(" عرض الإعلانات", "aad:list"))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    try:
        bot.edit_message_text("📢 إدارة الإعلانات", call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, "📢 إدارة الإعلانات", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == "aad:add")
def cb_aad_add(call):
    if not user_is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "aad_add", {"step": 1, "data": {}})
    bot.send_message(call.message.chat.id, "📝 الخطوة 1: عنوان الإعلان")


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "aad_add")
def handle_aad_add(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    s = get_state(uid)
    step = s["data"].get("step", 1)
    data = s["data"].get("data", {})
    txt = (msg.text or "").strip()

    if step == 1:
        data["title"] = txt
        s["data"]["step"] = 2
        s["data"]["data"] = data
        set_state(uid, "aad_add", s["data"])
        bot.send_message(msg.chat.id, "📝 الخطوة 2: نص الإعلان")
    elif step == 2:
        data["body"] = txt
        s["data"]["step"] = 3
        s["data"]["data"] = data
        set_state(uid, "aad_add", s["data"])
        bot.send_message(msg.chat.id, "📝 الخطوة 3: رابط التواصل (أو /skip)")
    elif step == 3:
        data["contact_url"] = txt
        conn = db()
        conn.execute(
            "INSERT INTO ads (title, body, contact_url, status, created) VALUES (?, ?, ?, 'active', ?)",
            (data.get("title", ""), data.get("body", ""), data.get("contact_url", ""), time.time())
        )
        conn.commit()
        conn.close()
        clear_state(uid)
        bot.send_message(msg.chat.id, "✅ تمت إضافة الإعلان")



# ============================================================
# قناة الأكواد (اختياري)
# ============================================================
CHANNEL_STATE = {"last_id": 0, "running": False, "received": 0}


def parse_otp(text):
    """تحليل رسالة OTP"""
    if not text:
        return None
    result = {"brand": None, "phone": None, "code": None}
    m = re.match(r"^([A-Z]{2,3})\s*\|", text.strip())
    if m:
        result["brand"] = m.group(1)
    pm = re.search(r"\+?(\d{5,})[\s\|]+(\d{3,5})", text)
    if pm:
        result["phone"] = pm.group(2)
    for pat in [r"(?:رمز|كود|code|OTP|otp)\s*[^:]*[:\s]\s*([\d\-]{4,12})",
                r"\b(\d{4,9})\b"]:
        for mm in re.finditer(pat, text, re.IGNORECASE):
            c = mm.group(1).replace("-", "")
            if 4 <= len(c) <= 9:
                result["code"] = c
                return result
    return result


def src_extract(txt):
    """يستخرج (الرقم، الكود) من رسالة المصدر. الرقم قد يكون مخفيًا جزئيًا."""
    p = parse_otp(txt) or {}
    code = p.get("code")
    if not code:
        return None
    phone = ""
    for line in str(txt).splitlines()[:4]:
        for m in re.finditer(r"\+?\d[\d•\*xX\.\-\s]{5,}\d", line):
            cand = re.sub(r"[\s\-\.]", "", m.group(0)).lstrip("+")
            if len(re.sub(r"\D", "", cand)) >= 8:
                phone = cand
                break
        if phone:
            break
    return phone, code


def src_sms_part(txt):
    m = re.search(r"SMS:\s*(.*)", str(txt), re.S | re.I)
    return (m.group(1) if m else str(txt)).strip()


def src_handle_text(txt):
    """يعالج رسالة وصلت من قناة المصدر: يحفظ الكود وينشره منسّقًا للقناة"""
    r = src_extract(txt)
    if not r:
        return False
    phone, code = r
    digits = re.sub(r"\D", "", phone)
    try:
        flag, cname, _cc = detect_country(digits) if digits else ("🏳", "", "")
    except Exception:
        flag, cname = "🏳", ""
    pname, _ic = otp_platform(txt)
    if not code_add(phone or "قناة", code, pname or "قناة", cname, str(txt)[:200]):
        return False
    CHANNEL_STATE["received"] += 1
    print("[CHANNEL] +" + code)
    fwd = setting_get("forward_channel_id", "")
    if setting_get("src_repost", "1") == "1" and fwd:
        try:
            lang = "en" if str(txt).isascii() else "ar"
            send_otp_message(fwd, flag, phone or "0", lang, src_sms_part(txt), code,
                             setting_get("channel_link", "https://t.me/"),
                             "https://t.me/" + get_bot_username(),
                             setting_get("admin_link", "") or ("tg://user?id=" + str(MAIN_ADMIN_ID)))
        except Exception as e:
            print("[CHANNEL] repost err:", e)
    else:
        try:
            bot.send_message(MAIN_ADMIN_ID, "🟢 كود من القناة\n📱 " + str(phone) + "\n🔑 " + code)
        except Exception:
            pass
    return True


def channel_reader():
    """قارئ القناة في خلفية"""
    if CHANNEL_STATE.get("running"):
        return
    print("[CHANNEL] reader started")
    CHANNEL_STATE["running"] = True
    while True:
        try:
            token = setting_get("channel_bot_token", "")
            chat_id = setting_get("channel_id", "")
            if not token or not chat_id:
                time.sleep(15)
                continue
            url = "https://api.telegram.org/bot" + token + "/getUpdates"
            params = {"offset": CHANNEL_STATE["last_id"] + 1, "timeout": 25,
                      "allowed_updates": json.dumps(["channel_post", "message"])}
            r = requests.get(url, params=params, timeout=30)
            data = r.json()
            if data.get("ok") and data.get("result"):
                for upd in data["result"]:
                    CHANNEL_STATE["last_id"] = upd["update_id"]
                    msg = upd.get("channel_post") or upd.get("message") or {}
                    if not msg:
                        continue
                    _srcs = [str(chat_id)] + [x.strip() for x in str(setting_get("src_extra_ids", "")).split(",") if x.strip()]
                    if str(msg.get("chat", {}).get("id", "")) not in _srcs:
                        continue
                    txt = msg.get("text") or msg.get("caption") or ""
                    if not txt:
                        continue
                    src_handle_text(txt)
        except Exception as e:
            print("[CHANNEL] err:", e)
        time.sleep(6)


# ═══ إعدادات القناة من الأدمن ═══

@bot.callback_query_handler(func=lambda c: c.data.startswith("ch:set:"))
def cb_ch_set(call):
    """تعديل توكن بوت القناة أو ID القناة"""
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    if key == "token":
        label, hint = "توكن بوت القناة", "أرسل التوكن (من @BotFather)\nيبدأ بـ <code>1234567890:AAH...</code>"
    elif key == "id":
        label, hint = "ID القناة", "أرسل ID القناة (يبدأ بـ <code>-100</code>)\nمثال: <code>-1001234567890</code>"
    else:
        return
    set_state(call.from_user.id, "ch_set", {"key": key})
    bot.send_message(call.message.chat.id, "📝 <b>" + label + "</b>\n\n" + hint + "\n\n/cancel للإلغاء")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "ch_set")
def handle_ch_set(msg):
    """يحفظ توكن بوت القناة (بعد التحقق منه) أو ID القناة"""
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    s = get_state(uid)
    key = s["data"].get("key")
    txt = (msg.text or "").strip()
    if not txt:
        return
    if key == "token":
        try:
            data = requests.get("https://api.telegram.org/bot" + txt + "/getMe", timeout=10).json()
        except Exception as e:
            bot.send_message(msg.chat.id, "❌ خطأ: " + html.escape(str(e)[:100]))
            return
        if not data.get("ok"):
            bot.send_message(msg.chat.id, "❌ <b>التوكن غير صحيح</b>\n\nتأكد من نسخه كاملاً من @BotFather")
            return
        uname = data.get("result", {}).get("username", "")
        setting_set("channel_bot_token", txt)
        clear_state(uid)
        kb = InlineKeyboardMarkup()
        kb.add(btn("🔍 اكتشاف ID تلقائياً", "ch:detect", key="btn_detect_id"))
        kb.add(btn("⬅️ رجوع", "admin:channel", key="btn_back"))
        bot.send_message(msg.chat.id,
                         "✅ <b>تم حفظ التوكن</b>\n\n🤖 @" + uname + "\n\n"
                         "1. أضف هذا البوت أدمن في القناة\n2. اكتب أي رسالة في القناة\n"
                         "3. اضغط <b>🔍 اكتشاف ID</b>", reply_markup=kb)
    elif key == "id":
        if not re.fullmatch(r"-?\d{5,20}", txt):
            bot.send_message(msg.chat.id, "❌ الـ ID غير صحيح. مثال: <code>-1001234567890</code>")
            return
        setting_set("channel_id", txt)
        clear_state(uid)
        bot.send_message(msg.chat.id, "✅ <b>تم حفظ ID القناة</b>\n\n📻 <code>" + txt + "</code>")
    else:
        clear_state(uid)




# ============================================================
# لوحة تخصيص الأزرار (للأدمن)
# ============================================================


@bot.callback_query_handler(func=lambda c: c.data.startswith("bc:v:"))
def cb_bc_view(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    
    # قراءة مباشرة من الداتابيز
    try:
        conn = db()
        row = conn.execute("SELECT label_ar, style, icon, visible FROM button_config WHERE key=?", (key,)).fetchone()
        conn.close()
        if row:
            label_ar = row["label_ar"] or ""
            style = row["style"] or ""
            icon = row["icon"] or ""
            visible = row["visible"]
        else:
            label_ar = ""
            style = ""
            icon = ""
            visible = 1
    except Exception as e:
        print("[BC_VIEW_ERR]", e)
        label_ar = ""
        style = ""
        icon = ""
        visible = 1

    # تنظيف اللون للعرض (لو فيه تداخل)
    display_style = style.split(":")[0] if ":" in style else style
    style_names = {
        "primary": "🔵 أزرق (أساسي)",
        "success": "🟢 أخضر (نجاح)",
        "danger": "🔴 أحمر (خطر)",
        "": "⚪ افتراضي",
    }
    style_display = style_names.get(display_style, display_style or "⚪ افتراضي")
    
    text = ("🎨 <b>تخصيص زر</b>\n\n"
            "🔑 المفتاح: <code>" + key + "</code>\n"
            "📝 النص: " + (label_ar or "—") + "\n"
            "🎨 اللون الحالي: " + style_display + "\n"
            "😀 الإيموجي: " + (icon or "—") + "\n"
            "👁 الحالة: " + ("ظاهر" if visible else "مخفي"))

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("✏️ تغيير النص", "bc:set:" + key + ":label_ar", BTN.PRIMARY))
    kb.add(btn("🎨 تغيير اللون", "bc:color:" + key))
    kb.add(btn("😀 تغيير الإيموجي", "bc:set:" + key + ":icon"))
    if visible:
        kb.add(btn("👁 إخفاء الزر", "bc:hide:" + key, BTN.DANGER))
    else:
        kb.add(btn("👁 إظهار الزر", "bc:show:" + key, BTN.SUCCESS))
    kb.add(btn("👁️ معاينة القائمة الحية", "bc:preview:" + key, BTN.SUCCESS))
    kb.add(btn("⬅️ رجوع", "admin:custom_main_menu", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc:color:"))
def cb_bc_color(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    cfg = btn_config_get(key)
    current_style = cfg.get("style", "")
    
    text = "🎨 <b>اختر اللون الجديد للزر:</b>\n\n"
    text += "اللون الحالي: <b>" + (current_style or "افتراضي") + "</b>"
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("🔵 أزرق (رئيسي)", "bc:sc:" + key + ":primary"))
    kb.add(btn("🟢 أخضر (نجاح)", "bc:sc:" + key + ":success"))
    kb.add(btn("🔴 أحمر (خطر)", "bc:sc:" + key + ":danger"))
    kb.add(btn("⚪ افتراضي (بدون لون)", "bc:sc:" + key + ":"))
    kb.add(btn("⬅️ رجوع", "bc:v:" + key, BTN.DANGER))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("bc:sc:"))
def cb_bc_set_color(call):
    if not user_is_admin(call.from_user.id):
        return
    parts = call.data.split(":", 3)
    key = parts[2]
    style = parts[3] if len(parts) > 3 else ""
    # ✅ إصلاح: تمرير style فعلياً + الحفظ المباشر في الداتابيز
    try:
        conn = db()
        conn.execute("UPDATE button_config SET style=? WHERE key=?", (style, key))
        conn.commit()
        conn.close()
        _BTN_CACHE["loaded_at"] = 0
        _BTN_CACHE["data"] = {}
        print("[COLOR_SAVE] key=" + str(key) + " style=" + str(style))
    except Exception as e:
        print("[COLOR_SAVE_ERR]", e)
        bot.answer_callback_query(call.id, "❌ خطأ في الحفظ", show_alert=True)
        return
    try:
        bot.answer_callback_query(call.id, "✅ تم حفظ اللون!")
    except Exception:
        pass
    # إعادة رسم الصفحة لتعكس اللون الجديد
    call.data = "bc:v:" + key
    cb_bc_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("bc:set:"))
def cb_bc_set(call):
    if not user_is_admin(call.from_user.id):
        return
    parts = call.data.split(":", 3)
    key, field = parts[2], parts[3]
    set_state(call.from_user.id, "bc_set", {"key": key, "field": field})
    bot.send_message(call.message.chat.id, "📝 أرسل القيمة الجديدة:\n/cancel")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "bc_set")
def handle_bc_set(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    s = get_state(uid)
    key = s["data"].get("key")
    field = s["data"].get("field")
    txt = (msg.text or "").strip()
    if not txt or not key or not field:
        clear_state(uid)
        return
    btn_config_set(key, **{field: txt})
    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم الحفظ")




@bot.callback_query_handler(func=lambda c: c.data.startswith("bc:preview:"))
def cb_bc_preview(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    
    # بناء رسالة المعاينة
    text = "👁️ <b>معاينة حية للقائمة الرئيسية</b>\n\n"
    text += "هذه هي الأزرار كما ستظهر للمستخدمين الآن:\n\n"
    
    kb = main_menu_kb(call.from_user.id)
    
    # إضافة زر للرجوع للتعديل
    try:
        kb.add(btn("⬅️ رجوع للتعديل", "bc:v:" + key, BTN.DANGER))
    except Exception:
        pass
        
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id, "تم عرض المعاينة")
    except Exception:
        pass


# _cb_bc_preview_defined

@bot.callback_query_handler(func=lambda c: c.data.startswith("bc:hide:"))
def cb_bc_hide(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    btn_config_set(key, visible=0)
    bot.answer_callback_query(call.id, "تم الإخفاء")
    cb_bc_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("bc:show:"))
def cb_bc_show(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    btn_config_set(key, visible=1)
    bot.answer_callback_query(call.id, "تم الإظهار")
    cb_bc_view(call)


@bot.callback_query_handler(func=lambda c: c.data == "bc:reset")
def cb_bc_reset(call):
    if not user_is_admin(call.from_user.id):
        return
    btn_config_reset()
    bot.answer_callback_query(call.id, "تم إعادة الافتراضي", show_alert=True)
    cb_admin_custom(call)





# ============================================================
# إدارة الأكواد (الحد الأقصى 12) + إخفاء الأرقام
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "admin:codes_manage")
def cb_admin_codes_manage(call):
    if not user_is_admin(call.from_user.id):
        return
    items = codes_list(limit=12)
    if not items:
        text = "🗂 <b>إدارة الأكواد</b>\n\nلا توجد أكواد حالياً."
        kb = InlineKeyboardMarkup()
        kb.add(btn("⬅️ رجوع", "admin:home"))
    else:
        text = "🗂 <b>إدارة الأكواد (آخر 12 كود)</b>\n\n"
        kb = InlineKeyboardMarkup(row_width=1)
        for i, c in enumerate(items, 1):
            phone = str(c["phone"])
            # إخفاء الرقم (نخلي أول 5 أرقام وآخر 3 أرقام)
            digits = re.sub(r"\D", "", phone)
            if len(digits) > 8:
                masked_phone = "+" + digits[:5] + "•••" + digits[-3:]
            else:
                masked_phone = phone
            
            t = datetime.fromtimestamp(c["received_at"]).strftime("%H:%M")
            text += f"{i}. 🔑 <code>{c['code']}</code> | 📱 <code>{masked_phone}</code> | {t}\n"
            
            # زر الحذف لكل كود
            kb.add(btn(f"🗑 حذف الكود ({c['code']})", f"admin:del_code:{c['id']}", BTN.DANGER))
            
        kb.add(btn("⬅️ رجوع", "admin:home"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin:del_code:"))
def cb_admin_del_code(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        cid = int(call.data.split(":")[2])
        code_delete(cid)
        bot.answer_callback_query(call.id, "✅ تم حذف الكود")
        call.data = "admin:codes_manage"
        cb_admin_codes_manage(call)
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ حدث خطأ")



# ============================================================
# زرار آخر الأكواد للمستخدمين
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "menu:last_codes")
def cb_last_codes(call):
    import time
    from datetime import datetime
    
    now = time.time()
    cooldown = 60
    items = codes_list(limit=12)
    last_received = items[0]["received_at"] if items else (now - cooldown)
    time_passed = now - last_received
    time_left = max(0, int(cooldown - time_passed))
    btn_color = "success" if time_left == 0 else "danger"
    btn_text = "🔄 تحديث الأكواد"

    # قراءة النص المخصص
    custom_text = setting_get("section_text_last_codes", "")

    if not items:
        if custom_text and custom_text.strip():
            text = custom_text
        else:
            text = "📥 <b>آخر الأكواد</b>" + chr(10) + chr(10) + "لا توجد أكواد حالياً. انتظر قليلاً..."
        kb = InlineKeyboardMarkup()
        kb.add(_kb_btn(btn_text, "menu:last_codes", style=btn_color))
        kb.add(btn("⬅️ رجوع", "menu:home"))
    else:
        text = "📥 <b>آخر الأكواد الواصلة (12)</b>" + chr(10) + chr(10)
        for i, c in enumerate(items, 1):
            phone = str(c["phone"])
            digits = re.sub(r"[^0-9]", "", phone)
            if len(digits) > 8:
                masked_phone = "+" + digits[:5] + "•••" + digits[-3:]
            else:
                masked_phone = phone
            t = datetime.fromtimestamp(c["received_at"]).strftime("%H:%M")
            pname = c["platform"] or "غير معروف"
            text += f"{i}. 🔑 <code>{c['code']}</code> | 📱 <code>{masked_phone}</code>" + chr(10)
            text += f"     📡 {pname} | 🕐 {t}" + chr(10) + chr(10)
            
        if time_left > 0:
            text += f"⏳ <i>التحديث التلقائي متاح بعد: {time_left} ثانية</i>" + chr(10)
        else:
            text += f"✅ <i>يمكنك التحديث الآن!</i>" + chr(10)
            
        kb = InlineKeyboardMarkup()
        kb.add(_kb_btn(btn_text, "menu:last_codes", style=btn_color))
        kb.add(btn("⬅️ رجوع", "menu:home"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        if "message is not modified" not in str(e):
            try:
                bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
            except Exception:
                pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:acc:"))
def cb_ap_account(call):
    """يعرض معلومات الحساب من اللوحة"""
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return

    p = panel_get(pid)
    if not p:
        return

    try:
        bot.answer_callback_query(call.id, "جاري الجلب...")
    except Exception:
        pass

    try:
        account = fetch_account_info(p)
    except Exception as e:
        account = None

    if not account:
        text = ("💰 <b>معلومات الحساب</b>\n\n"
                "❌ لا يمكن جلب المعلومات\n"
                "المسار <code>/api/v1/me</code> غير متاح أو التوكن غير صالح.")
    else:
        text = "💰 <b>معلومات الحساب</b>\n"
        text += "🆔 اللوحة: <b>" + (p.get("name") or "?") + "</b>"
        text += format_account_box(account, p.get("name", ""))

    kb = InlineKeyboardMarkup()
    kb.add(btn("🔄 تحديث", "ap:acc:" + str(pid), BTN.PRIMARY))
    kb.add(btn("⬅️ رجوع", "ap:v:" + str(pid)))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)



# ============================================================
# دوال إضافية للوحات
# ============================================================
def panel_log_error(pid, error):
    """يسجّل خطأ في سجل اللوحة (آخر 10)"""
    try:
        p = panel_get(pid)
        if not p:
            return
        logs = json.loads(p.get("error_log") or "[]")
        logs.append({"t": time.time(), "e": str(error)[:200]})
        logs = logs[-10:]
        panel_update(pid, error_log=json.dumps(logs, ensure_ascii=False))
    except Exception:
        pass


def panel_get_errors(pid):
    """يرجع سجل أخطاء اللوحة"""
    try:
        p = panel_get(pid)
        if not p:
            return []
        return json.loads(p.get("error_log") or "[]")
    except Exception:
        return []


def panel_clear_errors(pid):
    """يمسح سجل الأخطاء"""
    panel_update(pid, error_log="[]")


def panel_reset_fail(pid):
    """يعيد تعيين عداد الفشل"""
    panel_update(pid, fail_count=0, last_status="idle", last_error="")


def panel_stats(pid):
    """إحصائيات اللوحة"""
    p = panel_get(pid)
    if not p:
        return {}
    return {
        "success": p.get("success_count") or 0,
        "total_fetches": p.get("total_fetches") or 0,
        "total_codes": p.get("total_codes_fetched") or 0,
        "fail_count": p.get("fail_count") or 0,
        "last_success": p.get("last_success_time") or 0,
    }


def panel_mark_success(pid, codes_count):
    """يحدّث إحصائيات النجاح"""
    p = panel_get(pid)
    if not p:
        return
    panel_update(pid,
                 success_count=(p.get("success_count") or 0) + 1,
                 total_fetches=(p.get("total_fetches") or 0) + 1,
                 total_codes_fetched=(p.get("total_codes_fetched") or 0) + codes_count,
                 last_success_time=time.time(),
                 fail_count=0,
                 last_status="ok",
                 last_error="")


def panel_mark_fail(pid, error):
    """يحدّث إحصائيات الفشل"""
    p = panel_get(pid)
    if not p:
        return
    panel_update(pid,
                 fail_count=(p.get("fail_count") or 0) + 1,
                 total_fetches=(p.get("total_fetches") or 0) + 1,
                 last_status="error",
                 last_error=str(error)[:200])
    panel_log_error(pid, error)


def panel_edit_field(pid, field, value):
    """تعديل حقل واحد"""
    allowed = {"name", "url", "token", "username", "password", "auth_type",
               "api_path", "api_method", "json_path",
               "field_phone", "field_code", "field_platform",
               "field_country", "field_message",
               "interval_sec", "priority", "smart_bind", "auto_push"}
    if field not in allowed:
        return False
    try:
        if field == "interval_sec":
            value = int(value)
            if value < 10:
                value = 10
            if value > 3600:
                value = 3600
        if field == "priority":
            value = int(value)
        if field in ("smart_bind", "auto_push"):
            value = 1 if value in (1, "1", True, "on") else 0
        panel_update(pid, **{field: value})
        return True
    except Exception:
        return False


def export_panels():
    """يصدر كل اللوحات JSON"""
    panels = panels_list()
    out = []
    for p in panels:
        out.append({
            "name": p.get("name"),
            "url": p.get("url"),
            "token": p.get("token"),
            "username": p.get("username"),
            "password": p.get("password"),
            "auth_type": p.get("auth_type"),
            "api_path": p.get("api_path"),
            "api_method": p.get("api_method"),
            "json_path": p.get("json_path"),
            "field_phone": p.get("field_phone"),
            "field_code": p.get("field_code"),
            "field_platform": p.get("field_platform"),
            "field_country": p.get("field_country"),
            "field_message": p.get("field_message"),
            "interval_sec": p.get("interval_sec"),
            "custom_headers": p.get("custom_headers"),
            "custom_query": p.get("custom_query"),
            "body_json": p.get("body_json"),
        })
    return out


def import_panels(data):
    """يستورد لوحات من JSON"""
    count = 0
    for p in data:
        try:
            panel_add(
                name=p.get("name", "بدون اسم"),
                url=p.get("url", ""),
                token=p.get("token", ""),
                username=p.get("username", ""),
                password=p.get("password", ""),
                auth_type=p.get("auth_type", "token"),
                api_path=p.get("api_path", ""),
                api_method=p.get("api_method", "GET"),
                json_path=p.get("json_path", ""),
                field_phone=p.get("field_phone", ""),
                field_code=p.get("field_code", ""),
                field_platform=p.get("field_platform", ""),
                field_country=p.get("field_country", ""),
                field_message=p.get("field_message", ""),
                interval_sec=int(p.get("interval_sec", 60) or 60),
                custom_headers=p.get("custom_headers", "[]"),
                custom_query=p.get("custom_query", "[]"),
                body_json=p.get("body_json", ""),
            )
            count += 1
        except Exception:
            pass
    return count



# ============================================================
# واجهة التعديل + الإحصائيات + السجل
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:edit:"))
def cb_ap_edit(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return
    p = panel_get(pid)
    if not p:
        return
    text = "✏️ <b>تعديل اللوحة</b>\n\n"
    text += "🆔 " + (p.get("name") or "")
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("📝 الاسم", "ape:" + str(pid) + ":name", BTN.PRIMARY))
    kb.add(btn("🔗 الرابط", "ape:" + str(pid) + ":url"))
    kb.add(btn("🔑 التوكن", "ape:" + str(pid) + ":token"))
    kb.add(btn("📁 المسار", "ape:" + str(pid) + ":api_path"))
    kb.add(btn("📡 الطريقة (" + (p.get("api_method") or "GET") + ")", "apem:" + str(pid)))
    kb.add(btn("🧭 JSON Path", "ape:" + str(pid) + ":json_path"))
    kb.add(btn("📱 حقل الرقم", "ape:" + str(pid) + ":field_phone"))
    kb.add(btn("🔢 حقل الكود", "ape:" + str(pid) + ":field_code"))
    kb.add(btn("🌐 حقل المنصة", "ape:" + str(pid) + ":field_platform"))
    kb.add(btn("🌍 حقل الدولة", "ape:" + str(pid) + ":field_country"))
    kb.add(btn("💬 حقل الرسالة", "ape:" + str(pid) + ":field_message"))
    kb.add(btn("⏱ فترة السحب (" + str(p.get("interval_sec") or 60) + "s)", "ape:" + str(pid) + ":interval_sec"))
    kb.add(btn("⬅️ رجوع", "ap:v:" + str(pid)))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("ape:"))
def cb_ap_edit_field(call):
    if not user_is_admin(call.from_user.id):
        return
    parts = call.data.split(":", 2)
    try:
        pid = int(parts[1])
    except Exception:
        return
    field = parts[2]
    p = panel_get(pid)
    old_value = ""
    if p:
        old_value = str(p.get(field) or "")
    
    set_state(call.from_user.id, "ap_edit_field", {"pid": pid, "field": field})
    msg_text = "✏️ <b>تعديل:</b> " + html.escape(str(field)) + "\n\n"
    msg_text += "📌 القيمة الحالية: <code>" + html.escape(old_value) + "</code>\n\n"
    msg_text += "أرسل القيمة الجديدة، أو /skip للإلغاء"
    bot.send_message(call.message.chat.id, msg_text, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "ap_edit_field")
def handle_ap_edit_field(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    s = get_state(uid)
    pid = s["data"].get("pid")
    field = s["data"].get("field")
    txt = (msg.text or "").strip()

    if not pid or not field:
        clear_state(uid)
        return

    if txt == "/skip" or not txt:
        clear_state(uid)
        bot.send_message(msg.chat.id, "تم الإلغاء")
        return

    ok = panel_edit_field(pid, field, txt)
    clear_state(uid)
    if ok:
        bot.send_message(msg.chat.id, "✅ تم التعديل\n🔍 جرّب فحص اللوحة للتأكد")
    else:
        bot.send_message(msg.chat.id, "❌ فشل التعديل")


@bot.callback_query_handler(func=lambda c: c.data.startswith("apem:"))
def cb_ap_edit_method(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(btn("GET", "apes:" + str(pid) + ":GET", BTN.PRIMARY))
    kb.add(btn("POST", "apes:" + str(pid) + ":POST"))
    kb.add(btn("⬅️ رجوع", "ap:edit:" + str(pid)))
    try:
        bot.edit_message_text("📡 اختر الطريقة:", call.message.chat.id,
                              call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, "📡 اختر الطريقة:", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("apes:"))
def cb_ap_edit_set_method(call):
    if not user_is_admin(call.from_user.id):
        return
    parts = call.data.split(":", 2)
    try:
        pid = int(parts[1])
    except Exception:
        return
    method = parts[2]
    panel_edit_field(pid, "api_method", method)
    bot.answer_callback_query(call.id, "تم")
    call.data = "ap:edit:" + str(pid)
    cb_ap_edit(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:stats:"))
def cb_ap_stats(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return
    p = panel_get(pid)
    if not p:
        return
    s = panel_stats(pid)
    last = ""
    if s.get("last_success"):
        last = datetime.fromtimestamp(s["last_success"]).strftime("%Y-%m-%d %H:%M")
    text = ("📊 <b>إحصائيات اللوحة</b>\n\n"
            "🆔 " + (p.get("name") or "") + "\n\n"
            "✅ نجاحات: <b>" + str(s.get("success", 0)) + "</b>\n"
            "❌ فشل: <b>" + str(s.get("fail_count", 0)) + "</b>\n"
            "📊 إجمالي السحبات: <b>" + str(s.get("total_fetches", 0)) + "</b>\n"
            "🔢 أكواد مسحوبة: <b>" + str(s.get("total_codes", 0)) + "</b>\n"
            "🕐 آخر نجاح: " + (last or "—"))
    kb = InlineKeyboardMarkup()
    kb.add(btn("⬅️ رجوع", "ap:v:" + str(pid)))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:errs:"))
def cb_ap_errors(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return
    errs = panel_get_errors(pid)
    if not errs:
        text = " لا توجد أخطاء مسجلة"
    else:
        text = " <b>آخر الأخطاء</b>\n\n"
        for e in errs[-10:]:
            t = datetime.fromtimestamp(e.get("t", 0)).strftime("%H:%M:%S")
            text += "🕐 " + t + "\n⚠️ " + str(e.get("e", ""))[:150] + "\n\n"
    kb = InlineKeyboardMarkup()
    kb.add(btn("🗑 مسح السجل", "ap:errc:" + str(pid), BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "ap:v:" + str(pid)))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:errc:"))
def cb_ap_errors_clear(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return
    panel_clear_errors(pid)
    bot.answer_callback_query(call.id, "تم المسح")
    call.data = "ap:v:" + str(pid)
    cb_ap_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:rf:"))
def cb_ap_reset_fail(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return
    panel_reset_fail(pid)
    bot.answer_callback_query(call.id, "تم إصلاح اللوحة")
    call.data = "ap:v:" + str(pid)
    cb_ap_view(call)


@bot.callback_query_handler(func=lambda c: c.data == "ap:export")
def cb_ap_export(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        data = export_panels()
        text = json.dumps(data, ensure_ascii=False, indent=2)
        fname = "/tmp/panels_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(text)
        with open(fname, "rb") as f:
            bot.send_document(call.message.chat.id, f, caption="📦 نسخة احتياطية من اللوحات")
        import os
        os.remove(fname)
        bot.answer_callback_query(call.id, "تم")
    except Exception as e:
        bot.answer_callback_query(call.id, "فشل: " + str(e)[:50], show_alert=True)



# ============================================================
# تخصيص الأزرار — بأقسام
# ============================================================
BTN_SECTIONS = {
    "platforms": {
        "icon": "📱",
        "name": "منصات وأرقام",
        "keys": ["btn_platforms", "btn_get_number", "btn_view_codes",
                 "btn_copy", "btn_refresh", "btn_switch", "btn_codes_platform",
                 "btn_countries", "btn_numbers_list"],
    },
    "codes": {
        "icon": "💬",
        "name": "الأكواد",
        "keys": ["btn_codes", "btn_admin_codes", "btn_codes_platform"],
    },
    "panels": {
        "icon": "📡",
        "name": "اللوحات",
        "keys": ["btn_panels", "btn_add_panel", "btn_list_panels", "btn_test_all",
                 "btn_fetch_all", "btn_export", "btn_account", "btn_edit",
                 "btn_stats_panel", "btn_errors", "btn_retest", "btn_refresh_account",
                 "btn_clear_log", "btn_fix_counter", "btn_toggle", "btn_test", "btn_fetch"],
    },
    "users": {
        "icon": "👥",
        "name": "المستخدمين",
        "keys": ["btn_users", "btn_me", "btn_admin"],
    },
    "numbers": {
        "icon": "🔢",
        "name": "إدارة الأرقام",
        "keys": ["btn_numbers", "btn_add_number", "btn_upload_numbers",
                 "btn_list_numbers", "btn_delete_all_numbers", "btn_delete_platform"],
    },
    "support": {
        "icon": "💭",
        "name": "الدعم والإعدادات",
        "keys": ["btn_support", "btn_settings", "btn_explore", "btn_stats",
                 "btn_broadcast", "btn_channel", "btn_backup"],
    },
    "admin": {
        "icon": "👮",
        "name": "أدوات الأدمن",
        "keys": ["btn_maint", "btn_custom", "btn_maint_on", "btn_maint_off",
                 "btn_edit_text", "btn_edit_color", "btn_edit_icon",
                 "btn_hide", "btn_show", "btn_reset",
                 "btn_color_primary", "btn_color_success", "btn_color_danger", "btn_color_default"],
    },
    "main": {
        "icon": "🏠",
        "name": "أزرار القائمة الرئيسية",
        "keys": ["btn_platforms", "btn_last_codes", "btn_settings", "btn_me", "btn_explore", "btn_support", "btn_admin"],
    },
    "common": {
        "icon": "🔧",
        "name": "أزرار عامة",
        "keys": ["btn_back", "btn_save", "btn_delete", "btn_add", "btn_yes", "btn_no",
                 "btn_switch", "btn_refresh", "btn_copy"],
    },
}



@bot.callback_query_handler(func=lambda c: c.data == "admin:back_color" or (c.data.startswith("bc:") and len(c.data.split(":")) == 2))
def cb_admin_back_color(call):
    if not user_is_admin(call.from_user.id): return
    
    # نتعامل فقط مع bc:primary / bc:success / bc:danger / bc:default
    if call.data.startswith("bc:") and len(call.data.split(":")) == 2:
        color = call.data.split(":")[1]
        if color in ("primary", "success", "danger", "default"):
            setting_set("global_back_color", color)
            bot.answer_callback_query(call.id, "✅ تم تغيير اللون")
            call.data = "admin:back_color"
            return cb_admin_back_color(call)

    current = setting_get("global_back_color", "danger")
    color_names = {"danger": "🔴 أحمر", "primary": "🔵 أزرق", "success": "🟢 أخضر", "": "⚪ افتراضي"}
    
    nl = chr(10)
    text = "🔙 <b>لون أزرار الرجوع</b>" + nl
    text += "━━━━━━━━━━━━━━━━━━" + nl
    text += "اللون الحالي: <b>" + color_names.get(current, current) + "</b>" + nl + nl
    text += "هذا اللون سيتم تطبيقه على:" + nl
    text += "• زر رجوع" + nl
    text += "• زر القائمة الرئيسية" + nl
    text += "• أي زر فيه كلمة رجوع" + nl
    text += "━━━━━━━━━━━━━━━━━━"
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(btn("🔴 أحمر", "bc:danger"))
    kb.add(btn("🔵 أزرق", "bc:primary"))
    kb.add(btn("🟢 أخضر", "bc:success"))
    kb.add(btn("⚪ افتراضي", "bc:default"))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)





@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") in ("back_label_edit", "back_icon_edit"))
def handle_back_custom_edit(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    if (msg.text or "").strip() == "/cancel":
        clear_state(uid)
        bot.send_message(msg.chat.id, "❌ تم الإلغاء")
        return
    s = get_state(uid)
    state = s.get("state")
    txt = (msg.text or "").strip()
    if not txt: return
    
    if state == "back_label_edit":
        pass
        bot.send_message(msg.chat.id, "✅ تم تغيير النص إلى: " + txt)
    else:
        pass
        bot.send_message(msg.chat.id, "✅ تم تغيير الإيموجي إلى: " + txt)
    
    clear_state(uid)




@bot.callback_query_handler(func=lambda c: c.data.startswith("edit_text:"))
def cb_edit_text(call):
    if not user_is_admin(call.from_user.id): return
    key = call.data.split(":")[1]
    set_state(call.from_user.id, "edit_text_val", {"key": key})
    bot.send_message(call.message.chat.id, "📝 أرسل النص الجديد (يمكنك استخدام HTML مثل <b> و <i> و <code>):")
    
@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "edit_text_val")
def handle_edit_text_val(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    s = get_state(uid)
    key = s["data"].get("key")
    txt = (msg.text or "").strip()
    if not txt: return
    if txt == "/cancel":
        clear_state(uid)
        bot.send_message(msg.chat.id, "❌ تم الإلغاء")
        return
    setting_set("custom_text_" + key, txt)
    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم حفظ النص الجديد بنجاح!")












@bot.callback_query_handler(func=lambda c: c.data == "admin:platform_emoji" or c.data.startswith("pe:"))
def cb_platform_emoji(call):
    if not user_is_admin(call.from_user.id): return
    
    if call.data.startswith("pe:set:"):
        platform = call.data.split(":")[2]
        set_state(call.from_user.id, "platform_emoji_edit", {"platform": platform})
        bot.send_message(call.message.chat.id, "📝 أرسل الإيموجي الجديد لمنصة " + platform)
        return
        
    platforms = numbers_platforms()
    if not platforms:
        bot.send_message(call.message.chat.id, "لا توجد منصات مضافة.")
        return
    
    text = "📱 <b>إيموجي المنصات</b>\n\nاختر منصة لتغيير إيموجيها:"
    kb = InlineKeyboardMarkup(row_width=2)
    default_icons = {
        "واتساب": "🟢", "تيليجرام": "🔵", "فيسبوك": "🔷", "انستقرام": "🟣",
        "تويتر": "🔶", "جوجل": "🔴", "آبل": "⚫", "تيك توك": "⚫",
        "ديسكورد": "🟪", "سناب": "🟡", "فيسبوك (Panel:9)": "🔷"
    }
    for p in platforms:
        custom = setting_get("platform_emoji_" + p, "")
        icon = custom if custom else default_icons.get(p, "📱")
        kb.add(btn(icon + " " + p, "pe:set:" + p))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "platform_emoji_edit")
def handle_platform_emoji_edit(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    s = get_state(uid)
    platform = s["data"].get("platform")
    txt = (msg.text or "").strip()
    if not txt: return
    setting_set("platform_emoji_" + platform, txt)
    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم حفظ الإيموجي لمنصة " + platform)



@bot.callback_query_handler(func=lambda c: c.data == "admin:country_emoji" or c.data.startswith("ce:"))
def cb_country_emoji(call):
    if not user_is_admin(call.from_user.id): return
    
    if call.data.startswith("ce:set:"):
        country = call.data.split(":")[2]
        set_state(call.from_user.id, "country_emoji_edit", {"country": country})
        bot.send_message(call.message.chat.id, "📝 أرسل الإيموجي الجديد لدولة " + country)
        return
        
    # جلب كل الدول من الداتابيز
    try:
        conn = db()
        rows = conn.execute("SELECT DISTINCT country FROM numbers ORDER BY country").fetchall()
        conn.close()
        countries = [r["country"] for r in rows]
    except Exception:
        countries = []
        
    if not countries:
        bot.send_message(call.message.chat.id, "لا توجد دول مضافة.")
        return
    
    text = "🌍 <b>إيموجي الدول</b>\n\nاختر دولة لتغيير إيموجيها:"
    kb = InlineKeyboardMarkup(row_width=2)
    for c in countries:
        current = setting_get("country_emoji_" + c, "🌍")
        kb.add(btn(current + " " + c, "ce:set:" + c))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "country_emoji_edit")
def handle_country_emoji_edit(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    s = get_state(uid)
    country = s["data"].get("country")
    txt = (msg.text or "").strip()
    if not txt: return
    setting_set("country_emoji_" + country, txt)
    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم حفظ الإيموجي لدولة " + country)



@bot.callback_query_handler(func=lambda c: c.data == "admin:sections")
def cb_admin_sections(call):
    if not user_is_admin(call.from_user.id): return
    text = "📝 <b>تعديل نصوص الأقسام</b>\n\nاختر القسم اللي عايز تعدل النص بتاعه:"
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("📊 شاشة الترافيك", "sec_edit:traffic", BTN.PRIMARY))
    kb.add(btn("👤 شاشة ملفي", "sec_edit:me", BTN.PRIMARY))
    kb.add(btn("🌐 شاشة استكشف", "sec_edit:explore", BTN.PRIMARY))
    kb.add(btn("💭 شاشة الدعم", "sec_edit:support", BTN.PRIMARY))
    kb.add(btn("📥 شاشة آخر الأكواد", "sec_edit:last_codes", BTN.PRIMARY))
    kb.add(btn("📱 شاشة المنصات", "sec_edit:platforms", BTN.PRIMARY))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: c.data.startswith("sec_edit:"))
def cb_sec_edit(call):
    if not user_is_admin(call.from_user.id): return
    section = call.data.split(":")[1]
    
    current = setting_get("section_text_" + section, "")
    if not current:
        if section == "traffic":
            current = "📊 <b>الترافيك المباشر</b> 🟢\n━━━━━━━━━━━━━━━━━━\n🕐 <b>المدة:</b> آخر 60 دقيقة\n📥 <b>الأكواد الواصلة:</b> {hour_codes}\n📊 <b>إجمالي الأكواد:</b> {total_codes}\n━━━━━━━━━━━━━━━━━━\n🌍 <b>أعلى الدول:</b>\n{top_countries}\n━━━━━━━━━━━━━━━━━━\n🕐 <b>آخر تحديث:</b> {time}\n🟢 <i>متصل الآن</i>"
        elif section == "me":
            current = "👤 <b>الملف الشخصي</b>\n━━━━━━━━━━━━━━━━━━\n🆔 <b>الآي دي:</b> <code>{id}</code>\n👤 <b>الاسم:</b> {name}\n🔗 <b>المعرف:</b> @{username}\n📅 <b>تاريخ الانضمام:</b> {joined}\n━━━━━━━━━━━━━━━━━━\n👁 <b>الزيارات:</b> {visits}\n🔑 <b>الأكواد المسحوبة:</b> {codes_count}\n━━━━━━━━━━━━━━━━━━"
        elif section == "explore":
            current = "✨ <b>إحصائيات النظام المباشرة</b> ✨\n━━━━━━━━━━━━━━━━━━\n👥 <b>المستخدمين:</b> {users}\n💬 <b>الأكواد المسحوبة:</b> {codes}\n📱 <b>الأرقام المتاحة:</b> {numbers}\n📡 <b>اللوحات النشطة:</b> {panels}\n━━━━━━━━━━━━━━━━━━\n⚡ <i>النظام يعمل بكفاءة عالية</i>"
        elif section == "support":
            current = "💭 <b>قسم الدعم الفني</b> 💭\n━━━━━━━━━━━━━━━━━━\n\n👋 أهلاً بك في مركز المساعدة.\n✍️ <b>قم بكتابة رسالتك الآن</b> وسيتم الرد عليك من قبل الإدارة في أقرب وقت ممكن.\n\n━━━━━━━━━━━━━━━━━━\n💡 <i>للإلغاء، يمكنك إرسال الأمر /cancel في أي وقت.</i>"
        elif section == "last_codes":
            current = "📥 <b>آخر الأكواد</b>\n\nلا توجد أكواد حالياً. انتظر قليلاً..."
        elif section == "platforms":
            current = "🔓 <b>اختر المنصة</b>"
    
    msg = f"📝 <b>تعديل نص قسم: {section}</b>\n\n"
    msg += "📌 <b>النص الحالي:</b>\n"
    msg += "<code>" + html.escape(current) + "</code>\n\n"
    msg += "💡 يمكنك استخدام المتغيرات بالأقواس { }\n"
    msg += "أرسل النص الجديد، أو /cancel للإلغاء"
    
    set_state(call.from_user.id, "section_text_edit", {"section": section})
    bot.send_message(call.message.chat.id, msg, parse_mode="HTML")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "section_text_edit")
def handle_section_text_edit(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    if (msg.text or "").strip() == "/cancel":
        clear_state(uid)
        bot.send_message(msg.chat.id, "❌ تم الإلغاء")
        return
    s = get_state(uid)
    section = s["data"].get("section")
    txt = (msg.text or "").strip()
    if not txt: return
    if txt.startswith("<code>") and txt.endswith("</code>"):
        txt = txt[6:-7].strip()
    setting_set(f"section_text_{section}", txt)
    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم حفظ النص الجديد بنجاح! جرب تفتح القسم ده.")


# ============================================================
# إضافة زر مخصص (ميزة جديدة)
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "admin:add_custom")
def cb_admin_add_custom(call):
    if not user_is_admin(call.from_user.id): return
    set_state(call.from_user.id, "add_custom_step1", {})
    bot.send_message(call.message.chat.id, "📝 <b>الخطوة 1 من 3:</b>\n\nأرسل <b>اسم الزرار</b> (مثلاً: قناة البوت):", parse_mode="HTML")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "add_custom_step1")
def handle_custom_step1(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    txt = (msg.text or "").strip()
    if not txt: return
    set_state(uid, "add_custom_step2", {"label": txt})
    bot.send_message(msg.chat.id, "📝 <b>الخطوة 2 من 3:</b>\n\nأرسل <b>الرابط</b> (لازم يبدأ بـ https:// أو tg://):", parse_mode="HTML")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "add_custom_step2")
def handle_custom_step2(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    txt = (msg.text or "").strip()
    if not txt.startswith(("http://", "https://", "tg://")): 
        bot.send_message(msg.chat.id, "❌ الرابط غير صحيح، لازم يبدأ بـ https:// أو tg://")
        return
    s = get_state(uid)
    data = s["data"]
    data["url"] = txt
    set_state(uid, "add_custom_step3", data)
    
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(btn("🔵 أزرق", "custom_color:primary"))
    kb.add(btn("🟢 أخضر", "custom_color:success"))
    kb.add(btn("🔴 أحمر", "custom_color:danger"))
    bot.send_message(msg.chat.id, "📝 <b>الخطوة 3 من 3:</b>\n\nاختر <b>لون الزرار</b>:", reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("custom_color:"))
def cb_custom_color(call):
    uid = call.from_user.id
    if not user_is_admin(uid): return
    color = call.data.split(":")[1]
    
    s = get_state(uid)
    if s.get("state") != "add_custom_step3":
        return
    data = s["data"]
    label = data["label"]
    url = data["url"]
    
    import random
    key = f"custom_{random.randint(1000, 9999)}"
    
    # حفظ في قاعدة البيانات
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO button_config (key, label_ar, style, visible) VALUES (?, ?, ?, 1)", (key, label, color))
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key + "_url", url))
    
    # إضافة في التخطيط (في آخر صف)
    c.execute("SELECT COALESCE(MAX(row_idx), 0) + 1 FROM main_menu_grid")
    new_row = c.fetchone()[0]
    c.execute("INSERT INTO main_menu_grid (button_key, row_idx, col_idx, width) VALUES (?, ?, 0, 2)", (key, new_row))
    conn.commit()
    conn.close()
    
    clear_state(uid)
    bot.send_message(call.message.chat.id, f"✅ <b>تم إضافة الزرار ({label}) بنجاح!</b>\n\nاعمل /start عشان تشوفه.", parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: c.data == "admin:del_custom")
def cb_admin_del_custom(call):
    if not user_is_admin(call.from_user.id): return
    
    conn = db()
    rows = conn.execute("SELECT key FROM settings WHERE key LIKE 'custom_%_url'").fetchall()
    conn.close()
    
    if not rows:
        bot.send_message(call.message.chat.id, "❌ لا توجد أزرار مخصصة للحذف.", reply_markup=InlineKeyboardMarkup().add(btn("⬅️ رجوع", "admin:home")))
        return
        
    kb = InlineKeyboardMarkup(row_width=1)
    for r in rows:
        btn_key = r["key"].replace("_url", "")
        cfg = btn_config_get(btn_key)
        label = cfg.get("label_ar") or btn_key
        kb.add(btn(f"🗑 {label}", f"admin:del_custom_btn:{btn_key}"))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    
    bot.send_message(call.message.chat.id, "🗑 <b>اختر الزرار اللي عايز تحذفه:</b>", reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin:del_custom_btn:"))
def cb_del_custom_btn(call):
    if not user_is_admin(call.from_user.id): return
    btn_key = call.data.split(":")[2]
    
    conn = db()
    conn.execute("DELETE FROM settings WHERE key=?", (btn_key + "_url",))
    conn.execute("DELETE FROM button_config WHERE key=?", (btn_key,))
    conn.execute("DELETE FROM main_menu_grid WHERE button_key=?", (btn_key,))
    conn.commit()
    conn.close()
    
    bot.answer_callback_query(call.id, "✅ تم حذف الزرار")
    call.data = "admin:del_custom"
    cb_admin_del_custom(call)


@bot.callback_query_handler(func=lambda c: c.data == "admin:all_buttons")
def cb_admin_all_buttons(call):
    if not user_is_admin(call.from_user.id): return
    
    conn = db()
    rows = conn.execute("SELECT key, label_ar, style, icon FROM button_config ORDER BY key").fetchall()
    conn.close()
    
    text = "📋 <b>كل أزرار البوت</b>" + chr(10) + chr(10)
    text += "إجمالي الأزرار: <b>" + str(len(rows)) + "</b>" + chr(10)
    text += "اضغط على أي زرار لتعديله:"
    
    kb = InlineKeyboardMarkup(row_width=1)
    for r in rows:
        key = r["key"]
        label = r["label_ar"] or key
        icon = r["icon"] or ""
        style = r["style"] or "افتراضي"
        
        # عرض الزر بشكل مختصر
        btn_text = f"{icon} {label} | 🎨 {style}"
        kb.add(btn(btn_text, "bc:v:" + key))
    
    kb.add(btn("⬅️ رجوع", "admin:home"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")



# ============================================================
# إدارة كل الأزرار (مرتبة بالأقسام)
# ============================================================
MASTER_SECTIONS = {
    "main": {
        "icon": "🏠",
        "name": "أزرار القائمة الرئيسية",
        "keys": ["btn_platforms", "btn_last_codes", "btn_settings", "btn_me", "btn_explore", "btn_support", "btn_admin"],
    },
    "panels": {
        "icon": "📡",
        "name": "أزرار اللوحات",
        "keys": ["btn_panels", "btn_add_panel", "btn_list_panels", "btn_test_all", "btn_fetch_all", "btn_export", "btn_account", "btn_edit", "btn_stats_panel", "btn_errors", "btn_retest", "btn_refresh_account", "btn_clear_log", "btn_fix_counter", "btn_toggle", "btn_test", "btn_fetch"],
    },
    "users": {
        "icon": "👥",
        "name": "أزرار المستخدمين",
        "keys": ["btn_users", "btn_me", "btn_admin"],
    },
    "numbers": {
        "icon": "🔢",
        "name": "أزرار الأرقام",
        "keys": ["btn_numbers", "btn_add_number", "btn_upload_numbers", "btn_list_numbers", "btn_delete_all_numbers", "btn_delete_platform"],
    },
    "admin_tools": {
        "icon": "👮",
        "name": "أدوات الأدمن",
        "keys": ["btn_panels", "btn_users", "btn_numbers", "btn_stats", "btn_broadcast", "btn_maint", "btn_custom", "btn_channel", "btn_layout_edit", "btn_template", "btn_backup", "btn_points", "btn_admin_ads", "btn_admin_contests", "btn_api_health"],
    },
    "common": {
        "icon": "🔧",
        "name": "أزرار عامة",
        "keys": ["btn_back", "btn_save", "btn_delete", "btn_add", "btn_yes", "btn_no", "btn_switch", "btn_refresh", "btn_copy"],
    },
}


@bot.callback_query_handler(func=lambda c: c.data.startswith("master_sec:"))
def cb_master_section(call):
    if not user_is_admin(call.from_user.id): return
    sk = call.data.split(":")[1]
    sv = MASTER_SECTIONS.get(sk)
    if not sv:
        return
    
    conn = db()
    text = sv["icon"] + " <b>" + sv["name"] + "</b>\n\n"
    kb = InlineKeyboardMarkup(row_width=1)
    
    for k in sv["keys"]:
        row = conn.execute("SELECT key, label_ar, style, icon FROM button_config WHERE key=?", (k,)).fetchone()
        if not row:
            continue
        key = row["key"]
        label = row["label_ar"] or key
        icon = row["icon"] or ""
        style = row["style"] or "افتراضي"
        
        # ترجمة اللون للعربي
        color_names = {
            "primary": "🔵 أزرق",
            "success": "🟢 أخضر",
            "danger": "🔴 أحمر",
            "default": "⚪ افتراضي",
            "": "⚪ افتراضي"
        }
        color_ar = color_names.get(style, "⚪ افتراضي")
        
        # عرض الزر بشكل مرتب
        display = f"{icon} {label} | {color_ar}"
        kb.add(btn(display, "bc:v:" + key))
    
    conn.close()
    
    kb.add(btn("⬅️ رجوع", "admin:master_buttons"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data.startswith("sec:"))
def cb_section(call):
    if not user_is_admin(call.from_user.id):
        return
    sk = call.data.split(":", 1)[1]

    if sk == "reset_all":
        btn_config_reset()
        bot.answer_callback_query(call.id, "تم إعادة الكل", show_alert=True)
        cb_admin_custom(call)
        return

    sv = BTN_SECTIONS.get(sk)
    if not sv:
        return

    text = sv["icon"] + " <b>" + sv["name"] + "</b>\n\n"
    text += "عدد الأزرار: " + str(len(sv["keys"])) + "\n\n"
    text += "اختر زراً للتعديل:"

    kb = InlineKeyboardMarkup(row_width=1)
    for k in sv["keys"]:
        cfg = btn_config_get(k)
        icon = cfg.get("icon", "")
        label = cfg.get("label_ar") or k
        style_tag = ""
        if cfg.get("style") == "primary":
            style_tag = " 🔵"
        elif cfg.get("style") == "success":
            style_tag = " 🟢"
        elif cfg.get("style") == "danger":
            style_tag = " 🔴"
        vis = "" if cfg.get("visible", 1) else " (مخفي)"
        kb.add(btn(icon + " " + label + style_tag + vis, "bc:v:" + k))
    kb.add(btn("⬅️ رجوع", "admin:custom"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



# ============================================================
# نظام الأرقام — نسخة نظيفة
# ============================================================

# تخزين مؤقت: user_id -> {"platform":..., "country":..., "page":...}
_user_view = {}



# ============================================================
# نظام الأرقام — مثل B-M Numbers
# ============================================================

def _valid_url(u):
    u = str(u or "").strip()
    return u if (u.startswith(("http://", "https://", "tg://")) and len(u) > 8) else ""


def _cb_safe(data):
    """callback_data لا يتجاوز 64 بايت (الأسماء العربية قد تتجاوزه)"""
    b = str(data).encode("utf-8")
    return str(data) if len(b) <= 64 else b[:64].decode("utf-8", "ignore")


def _kb_btn(text, cb=None, url=None, style=None, copy_text=None):
    """زر بحقل واحد فقط: copy_text أو url أو callback_data (شرط تلجرام) + style اختياري"""
    # === تلوين أزرار الرجوع بالأحمر الثابت ===
    txt = str(text)
    if "رجوع" in txt or "القائمة الرئيسية" in txt or "⬅️" in txt or "🏠" in txt:
        style = "danger"

    # تحقق من أن style قيمة صالحة (تيليجرام يقبل primary/success/danger فقط)
    valid_styles = ("primary", "success", "danger")
    if style and style not in valid_styles:
        style = None

    kwargs = {"text": str(text)}
    if copy_text:
        kwargs["copy_text"] = CopyTextButton(text=str(copy_text)[:256])
    elif url:
        if not _valid_url(url):
            return None
        kwargs["url"] = _valid_url(url)
    else:
        kwargs["callback_data"] = _cb_safe(cb or "noop")

    if style:
        try:
            return InlineKeyboardButton(**dict(kwargs, style=style))
        except TypeError:
            pass
    try:
        return InlineKeyboardButton(**kwargs)
    except TypeError:
        return InlineKeyboardButton(str(text), callback_data=_cb_safe(cb or "noop"))




@bot.callback_query_handler(func=lambda c: c.data.startswith("selco:"))
def cb_sel_country(call):
    parts = call.data.split(":", 2)
    platform = parts[1]
    if len(parts) < 3:
        call.data = "selp:" + platform
        cb_sel_platform(call)
        return
    country = parts[2]
    try:
        show_numbers_page(call.message.chat.id, platform, country, 0, call.message)
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.answer_callback_query(call.id, "خطأ: " + str(e)[:50], show_alert=True)



# ============================================================
# إعدادات التخطيط (أعمدة وصفوف)
# ============================================================
_LAYOUT_CACHE = {"data": {}, "loaded": 0}



# ============================================================
# لوحة تخطيط الأزرار (أعمدة وصفوف)
# ============================================================
LAYOUT_SECTIONS = {
    "menu_main": ("🏠 القائمة الرئيسية", "المنصات، الأكواد، المسابقات..."),
    "menu_getnum": ("🔓 الحصول على رقم", "المنصات داخل قسم الحصول على رقم"),
    "menu_platforms": ("📱 قائمة المنصات", "المنصات الكاملة"),
    "menu_countries": ("🌍 قائمة الدول", "190 دولة"),
    "menu_codes": ("💬 الأكواد", "أزرار الأكواد"),
    "menu_admin": ("👮 لوحة الأدمن", "أزرار الأدمن"),
    "menu_panels": ("📡 اللوحات", "أزرار اللوحات"),
    "menu_contests": ("🎁 المسابقات", "أزرار المسابقات"),
    "menu_ads": ("📢 الإعلانات", "أزرار الإعلانات"),
    "menu_numbers_admin": ("🔢 إدارة الأرقام", "أزرار إدارة الأرقام"),
}



@bot.callback_query_handler(func=lambda c: c.data == "menu:platforms")
def cb_menu_platforms_old(call):
    """معالج قديم - يحوّل للجديد"""
    platforms = numbers_platforms()
    if not platforms:
        try:
            bot.answer_callback_query(call.id, "لا توجد منصات", show_alert=True)
        except Exception:
            pass
        return

    text = "🔓 <b>اختر المنصة</b>"
    kb = InlineKeyboardMarkup(row_width=1)
    for p in platforms:
        icon = PLATFORM_ICONS.get(p, "📱")
        cnt = len(numbers_list(platform=p))
        kb.add(_kb_btn(icon + " " + p + " (" + str(cnt) + ")", "selp:" + p))
    kb.add(_kb_btn("⬅️ القائمة الرئيسية", "menu:home"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



# ============================================================
# بناء الأزرار بتخطيط مخصص
# ============================================================
# بنية button_layout: قائمة صفوف، كل صف فيه عدد أعمدة
# مثال: [[2, 2, 1], [3, 3]] يعني:
#   صف 1: زرين + زرين + زر واحد
#   صف 2: 3 أزرار + 3 أزرار



# ============================================================
# واجهة تخطيط متقدم — تحكم بالصفوف والأعمدة
# ============================================================



# ============================================================
# ترتيب الأزرار
# ============================================================


def _sort_get_all():
    """كل أزرار button_config مرتبة: قائمة (المفتاح، الترتيب)"""
    conn = db()
    try:
        rows = conn.execute("SELECT key, sort_order FROM button_config ORDER BY sort_order ASC, key ASC").fetchall()
    except Exception:
        rows = []
    finally:
        conn.close()
    return [(r["key"], r["sort_order"] or 0) for r in rows]


def _sort_save_order(pairs):
    """يحفظ الترتيب الجديد: pairs = [(المفتاح، _)] بالترتيب المطلوب"""
    conn = db()
    try:
        for i, (k, _x) in enumerate(pairs, 1):
            conn.execute("UPDATE button_config SET sort_order=? WHERE key=?", (i, k))
        conn.commit()
    finally:
        conn.close()
    try:
        _BTN_CACHE["loaded_at"] = 0
    except Exception:
        pass


def layout2_get(section):
    """يرجع قائمة أعداد الأزرار لكل صف، مثال [2, 2, 1]"""
    try:
        v = json.loads(setting_get("layout2_" + str(section), "") or "[]")
        if isinstance(v, list):
            return [int(x) for x in v if 1 <= int(x) <= 8]
    except Exception:
        pass
    return []


def layout2_set(section, rows):
    clean = []
    for x in (rows or []):
        try:
            n = int(x)
        except (ValueError, TypeError):
            continue
        if 1 <= n <= 8:
            clean.append(n)
    setting_set("layout2_" + str(section), json.dumps(clean))


@bot.callback_query_handler(func=lambda c: c.data.startswith("srt:info:"))
def cb_sort_info(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    conn = db()
    try:
        row = conn.execute("SELECT * FROM button_config WHERE key=?", (key,)).fetchone()
    except Exception:
        row = None
    finally:
        conn.close()
    if not row:
        return
    icon = row["icon"] or ""
    label = row["label_ar"] or key
    order = row["sort_order"] or 0
    text = (" <b>" + icon + " " + label + "</b>\n\n"
            "🔑 المفتاح: <code>" + key + "</code>\n"
            "📊 الترتيب الحالي: <b>" + str(order) + "</b>\n\n"
            "اختر الحركة:")
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(btn("⏫ الأول", "srt:first:" + key, key="btn_first"))
    kb.add(btn("⬆️ فوق", "srt:up:" + key, key="btn_up"))
    kb.add(btn("⬇️ تحت", "srt:down:" + key, key="btn_down"))
    kb.add(btn("⏬ الآخر", "srt:last:" + key, key="btn_last"))
    kb.add(btn("⬅️ رجوع", "admin:sort", key="btn_back"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



@bot.callback_query_handler(func=lambda c: c.data.startswith("srt:up:"))
def cb_sort_up(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    items = _sort_get_all()
    keys = [k for k, _ in items]
    if key in keys:
        i = keys.index(key)
        if i > 0:
            keys[i], keys[i - 1] = keys[i - 1], keys[i]
            _sort_save_order([(k, 0) for k in keys])
    bot.answer_callback_query(call.id, "✅")
    call.data = "srt:info:" + key
    cb_sort_info(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("srt:down:"))
def cb_sort_down(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    items = _sort_get_all()
    keys = [k for k, _ in items]
    if key in keys:
        i = keys.index(key)
        if i < len(keys) - 1:
            keys[i], keys[i + 1] = keys[i + 1], keys[i]
            _sort_save_order([(k, 0) for k in keys])
    bot.answer_callback_query(call.id, "✅")
    call.data = "srt:info:" + key
    cb_sort_info(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("srt:first:"))
def cb_sort_first(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    items = _sort_get_all()
    keys = [k for k, _ in items]
    if key in keys:
        keys.remove(key)
        keys.insert(0, key)
        _sort_save_order([(k, 0) for k in keys])
    bot.answer_callback_query(call.id, "✅ أول")
    call.data = "srt:info:" + key
    cb_sort_info(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("srt:last:"))
def cb_sort_last(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    items = _sort_get_all()
    keys = [k for k, _ in items]
    if key in keys:
        keys.remove(key)
        keys.append(key)
        _sort_save_order([(k, 0) for k in keys])
    bot.answer_callback_query(call.id, "✅ آخر")
    call.data = "srt:info:" + key
    cb_sort_info(call)



# ============================================================
# تخطيط الأزرار الحقيقي — الصفوف والأعمدة
# ============================================================
_LAYOUT2_CACHE = {"data": {}, "loaded": 0}



# ============================================================
# واجهة تخطيط الأزرار البصرية
# ============================================================
LAYOUT2_SECTIONS = {
    "menu_main": "🏠 القائمة الرئيسية",
    "menu_admin": "👮 لوحة الأدمن",
    "menu_getnum": "🔓 قائمة المنصات",
    "menu_countries": "🌍 قائمة الدول",
    "menu_panels": "📡 قائمة اللوحات",
}



@bot.callback_query_handler(func=lambda c: c.data.startswith("ly2:view:"))
def cb_layout2_view(call):
    """عرض التخطيط الحالي بصري"""
    if not user_is_admin(call.from_user.id):
        return

    sk = call.data.split(":", 2)[2]
    name = LAYOUT2_SECTIONS.get(sk, "?")
    layout = layout2_get(sk)

    # عرض بصري
    text = "📐 <b>" + name + "</b>\n\n"

    if not layout:
        text += "<i>افتراضي (عمودين)</i>\n\n"
    else:
        text += "<b>الصفوف الحالية:</b>\n\n"
        for i, n in enumerate(layout, 1):
            if n == 1:
                block = "█"
            elif n == 2:
                block = "█ █"
            elif n == 3:
                block = "█ █ █"
            elif n >= 4:
                block = "█ █ █ █"
            else:
                block = str(n)
            text += "صف " + str(i) + ": <code>" + block + "</code>  (" + str(n) + " أزرار)\n"

    text += "\n☝️ اختر التعديل:"

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(btn("➕ صف 1 زر", "ly2:add:" + sk + ":1", key="btn_1"))
    kb.add(btn("➕ صف 2 أزرار", "ly2:add:" + sk + ":2", key="btn_2"))
    kb.add(btn("➕ صف 3 أزرار", "ly2:add:" + sk + ":3", key="btn_3"))
    kb.add(btn("➕ صف 4 أزرار", "ly2:add:" + sk + ":4", key="btn_4"))
    kb.add(btn("🗑 حذف آخر صف", "ly2:del:" + sk, key="btn_del"))
    kb.add(btn("🔄 إعادة الافتراضي", "ly2:reset:" + sk, key="btn_reset"))
    kb.add(btn("✏️ تعديل كامل (نص)", "ly2:edit:" + sk, key="btn_edit"))
    kb.add(btn("⬅️ رجوع", "admin:layout", key="btn_back"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("ly2:add:"))
def cb_layout2_add(call):
    """إضافة صف"""
    if not user_is_admin(call.from_user.id):
        return
    parts = call.data.split(":", 3)
    sk = parts[2]
    try:
        n = int(parts[3])
    except Exception:
        n = 2
    layout = layout2_get(sk) or []
    layout.append(n)
    layout2_set(sk, layout)
    bot.answer_callback_query(call.id, "✅ +" + str(n))
    call.data = "ly2:view:" + sk
    cb_layout2_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ly2:del:"))
def cb_layout2_del(call):
    """حذف آخر صف"""
    if not user_is_admin(call.from_user.id):
        return
    sk = call.data.split(":", 2)[2]
    layout = layout2_get(sk) or []
    if layout:
        layout.pop()
        layout2_set(sk, layout)
    bot.answer_callback_query(call.id, "🗑")
    call.data = "ly2:view:" + sk
    cb_layout2_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ly2:reset:"))
def cb_layout2_reset(call):
    """إعادة الافتراضي"""
    if not user_is_admin(call.from_user.id):
        return
    sk = call.data.split(":", 2)[2]
    layout2_set(sk, [])
    bot.answer_callback_query(call.id, "✅")
    call.data = "ly2:view:" + sk
    cb_layout2_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ly2:edit:"))
def cb_layout2_edit(call):
    """تعديل كامل بنص"""
    if not user_is_admin(call.from_user.id):
        return
    sk = call.data.split(":", 2)[2]
    set_state(call.from_user.id, "ly2_edit", {"sk": sk})
    bot.send_message(call.message.chat.id,
        "✏️ <b>أرسل التخطيط كأرقام</b>\n\n"
        "مثال: <code>1, 2, 1, 2, 1</code>\n\n"
        "يعني:\n"
        "صف 1: زر واحد\n"
        "صف 2: زرين\n"
        "صف 3: زر واحد\n"
        "صف 4: زرين\n"
        "صف 5: زر واحد\n\n"
        "/cancel للإلغاء", parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



# ============================================================
# نظام التخطيط اليدوي — صفوف وأعمدة
# ============================================================



# ============================================================
# واجهة تخطيط الصفوف (يدوية)
# ============================================================
LAYOUT_SECTIONS = {
    "menu_main": "🏠 القائمة الرئيسية",
    "menu_admin": "👮 لوحة الأدمن",
}



# ============================================================
# إدارة اللوحات (admin:panels)
# ============================================================
# ============================================================
# 🩺 واجهة صحة الـ APIs
# ============================================================
def ag_status_icon(p, h):
    if not p.get("enabled"):
        return "⏸"
    s = h["fail_streak"]
    if s == 0:
        return "✅" if h["last_ok"] else "⚪"
    return "⚠️" if s < AG_DOWN_AFTER else "⛔"


def ag_view():
    panels = panels_list()
    if not panels:
        kb = InlineKeyboardMarkup()
        kb.add(btn("⬅️ رجوع", "admin:home"))
        return "🩺 <b>صحة الـ APIs</b>\n\nلا توجد لوحات مضافة.", kb
    now = time.time()
    cnt = {"✅": 0, "⚠️": 0, "⛔": 0, "⏸": 0, "⚪": 0}
    lines = []
    for p in panels:
        h = ag_get(p["id"])
        ic = ag_status_icon(p, h)
        cnt[ic] += 1
        if len(lines) >= 15:
            continue
        name = html.escape(str(p.get("name") or "?"))
        if ic == "⏸":
            lines.append("⏸ <b>" + name + "</b> — موقوفة يدويًا")
        elif ic == "⚪":
            lines.append("⚪ <b>" + name + "</b> — لم تُفحص بعد")
        elif ic == "✅":
            tot = h["total_ok"] + h["total_fail"]
            rate = int(100 * h["total_ok"] / tot) if tot else 100
            lines.append("✅ <b>" + name + "</b> · " + str(h["latency_ms"]) + "ms\n"
                         "   آخر نجاح: قبل " + ag_dur(now - h["last_ok"]) +
                         " · أكواد: " + str(h["total_codes"]) + " · نجاح " + str(rate) + "%")
        else:
            lines.append(ic + " <b>" + name + "</b> — فشل " + str(h["fail_streak"]) + " متتالٍ\n"
                         "   ❌ " + html.escape(str(h["last_error"] or "؟")[:120]) + "\n"
                         "   🔁 المحاولة القادمة بعد " + ag_dur(h["next_retry"] - now))
    head = ("🩺 <b>صحة الـ APIs</b>\n"
            "✅ " + str(cnt["✅"]) + " تعمل · ⚠️ " + str(cnt["⚠️"]) + " متعثر · ⛔ " +
            str(cnt["⛔"]) + " متوقف · ⏸ " + str(cnt["⏸"]) + "\n\n")
    more = ("\n\n… و" + str(len(panels) - 15) + " أخرى") if len(panels) > 15 else ""
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(btn("🔎 فحص الكل الآن", "ag:probe"), btn("🔄 تحديث", "ag:view"))
    kb.add(btn("♻️ تصفير العدادات", "ag:reset"))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    return head + "\n\n".join(lines) + more, kb


@bot.callback_query_handler(func=lambda c: c.data in ("ag:view", "ag:probe", "ag:reset"))
def cb_ag(call):
    if not user_is_admin(call.from_user.id):
        return
    act = call.data
    note = None
    if act == "ag:probe":
        try:
            bot.answer_callback_query(call.id, "⏳ جارٍ فحص كل الـ APIs...")
        except Exception:
            pass
        now = time.time()
        for p, ok, codes, err, ms in ag_fetch_many(panels_list(only_enabled=True), limit=5):
            if ok:
                ag_save(p["id"], fail_streak=0, next_retry=0, latency_ms=ms,
                        last_ok=now, last_error="")
                panel_update(p["id"], fail_count=0, last_status="ok", last_error="")
            else:
                ag_save(p["id"], latency_ms=ms, last_error=err[:200])
    elif act == "ag:reset":
        ag_init()
        conn = db()
        conn.execute("UPDATE api_health SET fail_streak=0, next_retry=0, notified_down=0, last_error=''")
        conn.execute("UPDATE external_apis SET fail_count=0, last_status='idle', last_error=''")
        conn.commit()
        conn.close()
        note = "♻️ تم تصفير العدادات"
    text, kb = ag_view()
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        pass
    try:
        bot.answer_callback_query(call.id, note) if note else bot.answer_callback_query(call.id)
    except Exception:
        pass


# ============================================================
# 🎨 قالب الرسائل / 📥 مصدر الأكواد / 📈 تقرير اليوم
# ============================================================
def _tp_menu():
    cur = setting_get("otp_style", "quote")
    if cur not in OTP_STYLES:
        cur = "quote"
    kb = InlineKeyboardMarkup(row_width=1)
    for k, label in OTP_STYLES.items():
        kb.add(btn(("✅ " if k == cur else "") + label, "tp:set:" + k))
    kb.add(btn("👁 معاينة بالقالب الحالي", "tp:prev"))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    return ("🎨 <b>قالب رسائل الأكواد</b>\n\nالحالي: <b>" + OTP_STYLES[cur] + "</b>\n"
            "اختر قالبًا ثم اضغط معاينة لترى الشكل في محادثتك."), kb



@bot.callback_query_handler(func=lambda c: c.data in ("src:view", "src:toggle", "src:add", "src:clear"))
def cb_src(call):
    if not user_is_admin(call.from_user.id):
        return
    note = None
    if call.data == "src:toggle":
        setting_set("src_repost", "0" if setting_get("src_repost", "1") == "1" else "1")
        note = "تم"
    elif call.data == "src:clear":
        setting_set("src_extra_ids", "")
        note = "🗑 تم المسح"
    elif call.data == "src:add":
        setting_set("src_wait_" + str(call.from_user.id), str(time.time()))
        try:
            bot.send_message(call.message.chat.id,
                             "↪️ <b>أعد توجيه (Forward)</b> أي رسالة من القناة المصدر إلى هنا خلال 5 دقائق.\n\n"
                             "تذكير: بوت القارئ لازم يكون مشرفًا في تلك القناة.")
        except Exception:
            pass
    text, kb = _src_menu()
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        pass
    try:
        bot.answer_callback_query(call.id, note) if note else bot.answer_callback_query(call.id)
    except Exception:
        pass


def rp_build():
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    conn = db()
    total = conn.execute("SELECT COUNT(*) FROM codes WHERE received_at>=?", (start,)).fetchone()[0]
    hour = conn.execute("SELECT COUNT(*) FROM codes WHERE received_at>=?", (time.time() - 3600,)).fetchone()[0]
    pf = conn.execute("SELECT platform, COUNT(*) c FROM codes WHERE received_at>=? AND platform!='' "
                      "GROUP BY platform ORDER BY c DESC LIMIT 5", (start,)).fetchall()
    ct = conn.execute("SELECT country, COUNT(*) c FROM codes WHERE received_at>=? AND country!='' "
                      "GROUP BY country ORDER BY c DESC LIMIT 5", (start,)).fetchall()
    conn.close()
    cnt = {"✅": 0, "⚠️": 0, "⛔": 0, "⏸": 0, "⚪": 0}
    for p in panels_list():
        cnt[ag_status_icon(p, ag_get(p["id"]))] += 1
    top_p = " · ".join(html.escape(str(r[0])) + " " + str(r[1]) for r in pf) or "—"
    top_c = " · ".join(html.escape(str(r[0])) + " " + str(r[1]) for r in ct) or "—"
    text = ("📈 <b>تقرير اليوم</b> — " + datetime.now().strftime("%Y-%m-%d") + "\n\n"
            "🔑 أكواد اليوم: <b>" + str(total) + "</b> (آخر ساعة: " + str(hour) + ")\n"
            "🏆 المنصات: " + top_p + "\n"
            "🌍 الدول: " + top_c + "\n\n"
            "🩺 APIs: ✅ " + str(cnt["✅"]) + " · ⚠️ " + str(cnt["⚠️"]) + " · ⛔ " + str(cnt["⛔"]) +
            " · ⏸ " + str(cnt["⏸"]) + "\n"
            "👥 المستخدمون: " + str(users_count()))
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(btn("🔄 تحديث", "rp:today"), btn("⬅️ رجوع", "admin:home"))
    return text, kb


@bot.callback_query_handler(func=lambda c: c.data == "rp:today")
def cb_rp(call):
    if not user_is_admin(call.from_user.id):
        return
    text, kb = rp_build()
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        pass
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



@bot.callback_query_handler(func=lambda c: c.data == "ch:restart")
def cb_ch_restart(call):
    """إعادة تشغيل قارئ القناة"""
    if not user_is_admin(call.from_user.id):
        return

    try:
        t = threading.Thread(target=channel_reader, daemon=True)
        t.start()
        bot.answer_callback_query(call.id, "✅ تم إعادة التشغيل", show_alert=False)
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ خطأ: " + str(e)[:50], show_alert=True)
        return

    # أعد تحميل الصفحة
    call.data = "admin:channel"
    cb_admin_channel(call)


@bot.callback_query_handler(func=lambda c: c.data == "ch:test")
def cb_ch_test(call):
    """اختبار الاتصال بالقناة"""
    if not user_is_admin(call.from_user.id):
        return

    token = setting_get("channel_bot_token", "")
    chat_id = setting_get("channel_id", "")

    if not token or not chat_id:
        bot.answer_callback_query(call.id, "❌ التوكن أو ID مفقود", show_alert=True)
        return

    bot.answer_callback_query(call.id, "⏳ جاري الاختبار...", show_alert=False)

    try:
        # اختبار getChat
        url = "https://api.telegram.org/bot" + token + "/getChat?chat_id=" + chat_id
        r = requests.get(url, timeout=10)
        data = r.json()

        if data.get("ok"):
            chat_info = data.get("result", {})
            title = chat_info.get("title", "بدون عنوان")
            chat_type = chat_info.get("type", "?")
            username = chat_info.get("username", "")

            text = "🧪 <b>نتيجة الاختبار</b>\n\n"
            text += "✅ <b>الاتصال ناجح</b>\n\n"
            text += "📻 <b>اسم القناة:</b> " + title + "\n"
            text += "🔧 <b>النوع:</b> " + chat_type + "\n"
            if username:
                text += "🔗 <b>المعرف:</b> @" + username + "\n"
            text += "📻 <b>ID:</b> <code>" + str(chat_info.get("id", "")) + "</code>"

            kb = InlineKeyboardMarkup()
            kb.add(btn("⬅️ رجوع", "admin:channel", key="btn_back"))

            bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
        else:
            error = data.get("description", "خطأ غير معروف")
            text = "🧪 <b>نتيجة الاختبار</b>\n\n"
            text += "❌ <b>فشل الاتصال</b>\n\n"
            text += "⚠️ " + error

            kb = InlineKeyboardMarkup()
            kb.add(btn("⬅️ رجوع", "admin:channel", key="btn_back"))

            bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ خطأ: " + str(e)[:100])


@bot.callback_query_handler(func=lambda c: c.data == "ch:clear")
def cb_ch_clear(call):
    """حذف إعدادات القناة"""
    if not user_is_admin(call.from_user.id):
        return

    text = "⚠️ <b>تأكيد الحذف</b>\n\n"
    text += "هل تريد حذف:\n"
    text += "• توكن البوت\n"
    text += "• ID القناة\n\n"
    text += "لن يؤثر على الأكواد المستلمة."

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        btn("✅ نعم", "ch:clear_yes", key="btn_yes"),
        btn("❌ لا", "admin:channel", key="btn_no"),
    )

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data == "ch:clear_yes")
def cb_ch_clear_yes(call):
    """تنفيذ الحذف"""
    if not user_is_admin(call.from_user.id):
        return

    setting_set("channel_bot_token", "")
    setting_set("channel_id", "")

    bot.answer_callback_query(call.id, "✅ تم الحذف", show_alert=True)

    call.data = "admin:channel"
    cb_admin_channel(call)



# ============================================================
# قناة الأكواد — اكتشاف تلقائي للـ ID
# ============================================================



@bot.callback_query_handler(func=lambda c: c.data == "ch:detect")
def cb_ch_detect(call):
    """اكتشاف ID القناة تلقائياً"""
    if not user_is_admin(call.from_user.id):
        return

    token = setting_get("channel_bot_token", "")
    if not token:
        bot.answer_callback_query(call.id, "❌ أضف التوكن أولاً", show_alert=True)
        return

    bot.answer_callback_query(call.id, "🔍 جاري الاكتشاف...", show_alert=False)

    try:
        # استخدم getUpdates لاكتشاف القناة
        url = "https://api.telegram.org/bot" + token + "/getUpdates"
        params = {
            "offset": -100,
            "timeout": 5,
            "allowed_updates": json.dumps(["channel_post", "my_chat_member", "message"]),
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()

        if not data.get("ok"):
            error = data.get("description", "خطأ")
            bot.send_message(call.message.chat.id, "❌ خطأ: " + error)
            return

        updates = data.get("result", [])

        # ابحث عن قناة في التحديثات
        found_chats = []
        for upd in updates:
            # channel_post
            post = upd.get("channel_post") or {}
            chat = post.get("chat", {})
            if chat and chat.get("type") == "channel":
                found_chats.append({
                    "id": chat.get("id"),
                    "title": chat.get("title", "بدون عنوان"),
                    "username": chat.get("username", ""),
                })
            # my_chat_member
            my_member = upd.get("my_chat_member") or {}
            chat2 = my_member.get("chat", {})
            if chat2 and chat2.get("type") == "channel":
                found_chats.append({
                    "id": chat2.get("id"),
                    "title": chat2.get("title", "بدون عنوان"),
                    "username": chat2.get("username", ""),
                })
            # message
            msg2 = upd.get("message") or {}
            chat3 = msg2.get("chat", {})
            if chat3 and chat3.get("type") == "channel":
                found_chats.append({
                    "id": chat3.get("id"),
                    "title": chat3.get("title", "بدون عنوان"),
                    "username": chat3.get("username", ""),
                })

        # احذف المكرر
        unique = {}
        for ch in found_chats:
            unique[ch["id"]] = ch
        found_chats = list(unique.values())

        if not found_chats:
            text = "❌ <b>لم أجد أي قناة</b>\n\n"
            text += " <b>تأكد من:</b>\n"
            text += "1. البوت مضاف كأدمن في القناة ✓\n"
            text += "2. كتبت رسالة في القناة بعد الإضافة ✓\n"
            text += "3. القناة عامة أو البوت عضو فيها ✓\n\n"
            text += "💡 <b>جرّب:</b>\n"
            text += "• اكتب رسالة جديدة في القناة\n"
            text += "• اضغط زر الاكتشاف مرة أخرى"

            kb = InlineKeyboardMarkup()
            kb.add(btn("🔄 اكتشاف مرة أخرى", "ch:detect", key="btn_detect_id"))
            kb.add(btn("⬅️ رجوع", "admin:channel", key="btn_back"))

            bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
            return

        if len(found_chats) == 1:
            # قناة واحدة → احفظها تلقائياً
            ch = found_chats[0]
            setting_set("channel_id", str(ch["id"]))

            text = "✅ <b>تم اكتشاف القناة تلقائياً!</b>\n\n"
            text += "📻 <b>الاسم:</b> " + ch["title"] + "\n"
            if ch["username"]:
                text += "🔗 <b>المعرف:</b> @" + ch["username"] + "\n"
            text += "🆔 <b>ID:</b> <code>" + str(ch["id"]) + "</code>\n\n"
            text += "🟢 <b>القناة جاهزة!</b>\n"
            text += "أي كود يُرسل في القناة سيُستقبل تلقائياً"

            kb = InlineKeyboardMarkup()
            kb.add(btn("🧪 اختبار", "ch:test", key="btn_test_channel"))
            kb.add(btn("⬅️ رجوع", "admin:channel", key="btn_back"))

            bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
        else:
            # عدة قنوات → اعرضهم للاختيار
            text = "🔍 <b>وجدت " + str(len(found_chats)) + " قناة</b>\n\n"
            text += "اختر القناة:"

            kb = InlineKeyboardMarkup(row_width=1)
            for ch in found_chats:
                label = "📻 " + ch["title"]
                if ch["username"]:
                    label += " (@" + ch["username"] + ")"
                kb.add(btn(label, "ch:pick:" + str(ch["id"]), key="btn_pick_channel"))
            kb.add(btn("⬅️ رجوع", "admin:channel", key="btn_back"))

            bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ خطأ: " + str(e)[:100])


@bot.callback_query_handler(func=lambda c: c.data.startswith("ch:pick:"))
def cb_ch_pick(call):
    """اختيار قناة من عدة قنوات"""
    if not user_is_admin(call.from_user.id):
        return

    try:
        chat_id = call.data.split(":", 2)[2]
    except Exception:
        return

    setting_set("channel_id", chat_id)

    bot.answer_callback_query(call.id, "✅ تم الحفظ", show_alert=False)

    text = "✅ <b>تم حفظ القناة</b>\n\n"
    text += "🆔 <b>ID:</b> <code>" + chat_id + "</code>\n\n"
    text += "🟢 <b>القناة جاهزة!</b>"

    kb = InlineKeyboardMarkup()
    kb.add(btn("🧪 اختبار", "ch:test", key="btn_test_channel"))
    kb.add(btn("⬅️ رجوع", "admin:channel", key="btn_back"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)



@bot.callback_query_handler(func=lambda c: c.data == "ch:clear_id")
def cb_ch_clear_id(call):
    if not user_is_admin(call.from_user.id):
        return
    setting_set("channel_id", "")
    bot.answer_callback_query(call.id, "✅ تم حذف ID")
    call.data = "admin:channel"
    cb_admin_channel(call)



# ============================================================
# قناة الاستقبال (الأكواد تُرسل للقناة)
# ============================================================


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "chf_set")
def handle_chf_set(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    txt = (msg.text or "").strip()
    if not txt:
        return

    # حفظ
    setting_set("forward_channel_id", txt)
    clear_state(uid)
    bot.send_message(msg.chat.id,
        "✅ <b>تم حفظ ID القناة</b>\n\n"
        "أي كود جديد سيُرسل إلى القناة تلقائياً.", parse_mode="HTML")



# ============================================================
# قناة الأكواد — ID + رابط
# ============================================================

@bot.callback_query_handler(func=lambda c: c.data == "chf:set")
def cb_chf_set(call):
    if not user_is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "chf_set", {})
    bot.send_message(call.message.chat.id,
        "📝 <b>أرسل ID القناة</b>\n\n"
        "تأكد أن البوت أدمن في القناة.\n"
        "مثال: <code>-1001234567890</code>\n\n"
        "/cancel للإلغاء", parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



@bot.callback_query_handler(func=lambda c: c.data == "chf:setlink")
def cb_chf_setlink(call):
    if not user_is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "chf_setlink", {})
    bot.send_message(call.message.chat.id,
        "📝 <b>أرسل رابط القناة</b>\n\n"
        "مثال: <code>https://t.me/MyChannel</code>\n\n"
        "/cancel للإلغاء", parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "chf_setlink")
def handle_chf_setlink(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    txt = (msg.text or "").strip()
    if not txt:
        return
    if not txt.startswith("http"):
        txt = "https://" + txt
    setting_set("channel_link", txt)
    clear_state(uid)
    bot.send_message(msg.chat.id,
        "✅ <b>تم حفظ رابط القناة</b>\n\n"
        "سيظهر في زر (جروب البوت) تحت الأرقام.", parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: c.data == "chf:clear")
def cb_chf_clear(call):
    if not user_is_admin(call.from_user.id):
        return
    setting_set("forward_channel_id", "")
    setting_set("channel_link", "")
    bot.answer_callback_query(call.id, "✅ تم الحذف", show_alert=True)
    call.data = "admin:channel"
    cb_admin_channel(call)



# ============================================================
# التخطيط المرئي (Visual Layout Editor)
# ============================================================

@bot.callback_query_handler(func=lambda c: c.data.startswith("lye:btn:"))
def cb_layout_edit_btn(call):
    if not user_is_admin(call.from_user.id):
        return

    key = call.data.split(":", 2)[2]
    
    names = {
        "btn_platforms": "📱 المنصات",
        "btn_codes": "💬 الأكواد",
        "btn_contests": "🎁 المسابقات",
        "btn_ads": "📢 الإعلانات",
        "btn_support": "💭 الدعم",
        "btn_me": "👤 ملفي",
        "btn_explore": "🌐 استكشف",
        "btn_settings": "⚙️ الإعدادات",
        "btn_admin": "👮 لوحة الأدمن"
    }
    
    label = names.get(key, key)

    text = "📐 <b>التحكم في: " + label + "</b>\n\n"
    text += "اختر الإجراء:"

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(btn("⬆️ تقديم (فوق)", "lye:up:" + key, key="btn_up"))
    kb.add(btn("⬇️ تأخير (تحت)", "lye:down:" + key, key="btn_down"))
    kb.add(btn("⬅️ رجوع", "admin:layout_edit", key="btn_back"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("lye:up:"))
def cb_layout_up(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]

    conn = db()
    try:
        rows = conn.execute("SELECT button_key FROM main_menu_layout ORDER BY sort_order ASC").fetchall()
        order = [r["button_key"] for r in rows]
    except Exception:
        order = []
    finally:
        conn.close()

    if not order:
        order = ["btn_platforms", "btn_codes", "btn_contests", "btn_ads", "btn_support", "btn_me", "btn_explore", "btn_settings", "btn_admin"]

    if key in order:
        idx = order.index(key)
        if idx > 0:
            order[idx], order[idx-1] = order[idx-1], order[idx]
            # حفظ في DB
            conn = db()
            conn.execute("DELETE FROM main_menu_layout")
            for i, k in enumerate(order):
                conn.execute("INSERT INTO main_menu_layout (button_key, sort_order) VALUES (?, ?)", (k, i))
            conn.commit()
            conn.close()

    bot.answer_callback_query(call.id, "✅ تم التقديم")
    call.data = "admin:layout_edit"
    cb_admin_layout_edit(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("lye:down:"))
def cb_layout_down(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]

    conn = db()
    try:
        rows = conn.execute("SELECT button_key FROM main_menu_layout ORDER BY sort_order ASC").fetchall()
        order = [r["button_key"] for r in rows]
    except Exception:
        order = []
    finally:
        conn.close()

    if not order:
        order = ["btn_platforms", "btn_codes", "btn_contests", "btn_ads", "btn_support", "btn_me", "btn_explore", "btn_settings", "btn_admin"]

    if key in order:
        idx = order.index(key)
        if idx < len(order) - 1:
            order[idx], order[idx+1] = order[idx+1], order[idx]
            # حفظ في DB
            conn = db()
            conn.execute("DELETE FROM main_menu_layout")
            for i, k in enumerate(order):
                conn.execute("INSERT INTO main_menu_layout (button_key, sort_order) VALUES (?, ?)", (k, i))
            conn.commit()
            conn.close()

    bot.answer_callback_query(call.id, "✅ تم التأخير")
    call.data = "admin:layout_edit"
    cb_admin_layout_edit(call)


@bot.callback_query_handler(func=lambda c: c.data == "lye:reset")
def cb_layout_reset(call):
    if not user_is_admin(call.from_user.id):
        return
    
    conn = db()
    conn.execute("DELETE FROM main_menu_layout")
    conn.close()

    bot.answer_callback_query(call.id, "✅ تم إعادة الافتراضي", show_alert=True)
    call.data = "admin:layout_edit"
    cb_admin_layout_edit(call)



# ============================================================
# التخطيط الشبكي — تحكم في الصف والعمود
# ============================================================

@bot.callback_query_handler(func=lambda c: c.data.startswith("grd:btn:"))
def cb_grid_btn(call):
    if not user_is_admin(call.from_user.id):
        return

    key = call.data.split(":", 2)[2]

    conn = db()
    try:
        r = conn.execute("SELECT row_idx, col_idx FROM main_menu_grid WHERE button_key=?", (key,)).fetchone()
    except Exception:
        r = None
    finally:
        conn.close()

    if not r:
        bot.answer_callback_query(call.id, "❌ غير موجود", show_alert=True)
        return

    ri = r["row_idx"]
    ci = r["col_idx"]

    names = {
        "btn_platforms": "📱 المنصات",
        "btn_codes": "💬 الأكواد",
        "btn_contests": "🎁 المسابقات",
        "btn_ads": "📢 الإعلانات",
        "btn_support": "💭 الدعم",
        "btn_me": "👤 ملفي",
        "btn_explore": "🌐 استكشف",
        "btn_settings": "⚙️ الإعدادات",
        "btn_admin": "👮 لوحة الأدمن",
    }

    text = "📐 <b>" + names.get(key, key) + "</b>\n\n"
    text += "📍 الصف الحالي: <b>" + str(ri + 1) + "</b>\n"
    text += "📍 العمود الحالي: <b>" + str(ci + 1) + "</b>\n\n"
    text += "اختر الحركة:"

    kb = InlineKeyboardMarkup(row_width=2)
    
    # حركات الصفوف
    kb.add(
        btn("⬆️ صف فوق", "grd:up:" + key, key="btn_up"),
        btn("⬇️ صف تحت", "grd:down:" + key, key="btn_down")
    )
    # حركات الأعمدة
    kb.add(
        btn("⬅️ عمود يسار", "grd:left:" + key, key="btn_left"),
        btn("➡️ عمود يمين", "grd:right:" + key, key="btn_right")
    )
    # إضافة صف جديد
    kb.add(btn("➕ صف جديد أسفل", "grd:newrow:" + key, key="btn_newrow"))
    kb.add(btn("⬅️ رجوع", "admin:layout_edit", key="btn_back"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


def _grid_move(key, dr=0, dc=0, action=None):
    """يحرك زر"""
    conn = db()
    try:
        r = conn.execute("SELECT row_idx, col_idx FROM main_menu_grid WHERE button_key=?", (key,)).fetchone()
        if not r:
            conn.close()
            return False

        ri = r["row_idx"] + dr
        ci = r["col_idx"] + dc

        if ri < 0:
            ri = 0
        if ci < 0:
            ci = 0

        if action == "newrow":
            # احسب آخر صف في القائمة
            last = conn.execute("SELECT MAX(row_idx) FROM main_menu_grid").fetchone()
            last_row = (last[0] if last[0] is not None else 0) + 1
            ri = last_row
            ci = 0

        conn.execute("UPDATE main_menu_grid SET row_idx=?, col_idx=? WHERE button_key=?", (ri, ci, key))
        conn.commit()
        return True
    finally:
        conn.close()


@bot.callback_query_handler(func=lambda c: c.data.startswith("grd:up:"))
def cb_grid_up(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    _grid_move(key, dr=-1)
    bot.answer_callback_query(call.id, "✅")
    call.data = "grd:btn:" + key
    cb_grid_btn(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("grd:down:"))
def cb_grid_down(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    _grid_move(key, dr=1)
    bot.answer_callback_query(call.id, "✅")
    call.data = "grd:btn:" + key
    cb_grid_btn(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("grd:left:"))
def cb_grid_left(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    _grid_move(key, dc=-1)
    bot.answer_callback_query(call.id, "✅")
    call.data = "grd:btn:" + key
    cb_grid_btn(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("grd:right:"))
def cb_grid_right(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    _grid_move(key, dc=1)
    bot.answer_callback_query(call.id, "✅")
    call.data = "grd:btn:" + key
    cb_grid_btn(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("grd:newrow:"))
def cb_grid_newrow(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    _grid_move(key, action="newrow")
    bot.answer_callback_query(call.id, "✅ صف جديد")
    call.data = "grd:btn:" + key
    cb_grid_btn(call)


@bot.callback_query_handler(func=lambda c: c.data == "grd:reset")
def cb_grid_reset(call):
    if not user_is_admin(call.from_user.id):
        return
    
    conn = db()
    conn.execute("DELETE FROM main_menu_grid")
    
    defaults = [
        ("btn_platforms", 0, 0),
        ("btn_codes", 0, 1),
        ("btn_contests", 1, 0),
        ("btn_ads", 1, 1),
        ("btn_support", 2, 0),
        ("btn_me", 2, 1),
        ("btn_explore", 3, 0),
        ("btn_settings", 3, 1),
        ("btn_admin", 4, 0),
    ]
    for k, r, cl in defaults:
        conn.execute("INSERT INTO main_menu_grid (button_key, row_idx, col_idx) VALUES (?, ?, ?)", (k, r, cl))
    
    conn.commit()
    conn.close()

    bot.answer_callback_query(call.id, "✅ تم إعادة الافتراضي", show_alert=True)
    call.data = "admin:layout_edit"
    cb_admin_layout_edit(call)



# ============================================================
# التخطيط الكامل — صف + عمود + عرض
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "admin:layout_edit")
def cb_admin_layout_edit(call):
    if not user_is_admin(call.from_user.id):
        return

    text = "📐 <b>تخطيط القائمة الرئيسية</b>\n\n"
    kb = InlineKeyboardMarkup(row_width=1)

    # ترتيب افتراضي منطقي (صفوف وأعمدة)
    default_layout = {
        "btn_platforms": (0, 0),
        "btn_last_codes": (0, 1),
        "btn_support": (1, 0),
        "btn_me": (1, 1),
        "btn_explore": (2, 0),
        "btn_settings": (2, 1),
        "btn_admin": (3, 0),
    }
    default_names = {
        "btn_platforms": "📱 المنصات",
        "btn_last_codes": "😩 آخر الأكواد",
        "btn_support": "💭 الدعم",
        "btn_me": "👤 ملفي",
        "btn_explore": "🌐 استكشف",
        "btn_settings": "📊 الترافيك المباشر",
        "btn_admin": "👮 لوحة الأدمن",
    }

    try:
        conn = db()
        rows = conn.execute("SELECT key, label_ar, style, icon FROM button_config WHERE visible=1 ORDER BY sort_order").fetchall()
        conn.close()

        if not rows:
            text += "☝️ اضغط أي زر لتعديله (من الأزرار الافتراضية)\n\n"
            for k, (ri, ci) in default_layout.items():
                if k == "btn_admin" and not user_is_admin(call.from_user.id):
                    continue
                label = default_names.get(k, k)
                text += "• " + label + " — صف " + str(ri + 1) + "، عمود " + str(ci + 1) + "\n"
                kb.add(btn(label, "grd2:btn:" + k))
        else:
            for r in rows:
                k = r["key"]
                label = r["label_ar"] or k
                icon = r["icon"] or ""
                display = (icon + " " + label) if icon else label
                kb.add(btn(display, "grd2:btn:" + k))
            text += "☝️ اضغط أي زر لتعديله"
    except Exception as e:
        text += "⚠️ حدث خطأ: " + str(e)[:50]

    kb.add(btn("🔄 إعادة الافتراضي", "grd2:reset", BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "admin:home", BTN.DANGER))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("grd2:btn:"))
def cb_grid2_btn(call):
    if not user_is_admin(call.from_user.id):
        return

    key = call.data.split(":", 2)[2]

    # ترتيب افتراضي
    default_layout = {
        "btn_platforms": (0, 0, 2),
        "btn_last_codes": (0, 1, 1),
        "btn_support": (1, 0, 1),
        "btn_me": (1, 1, 1),
        "btn_explore": (2, 0, 1),
        "btn_settings": (2, 1, 1),
        "btn_admin": (3, 0, 1),
    }

    conn = db()
    try:
        r = conn.execute("SELECT row_idx, col_idx, width FROM main_menu_grid WHERE button_key=?", (key,)).fetchone()
    except Exception:
        r = None
    finally:
        conn.close()

    if r:
        ri = r["row_idx"]
        ci = r["col_idx"]
        w = r["width"] if r["width"] else 1
    else:
        ri, ci, w = default_layout.get(key, (0, 0, 1))

    names = {
        "btn_platforms": "📱 المنصات",
        "btn_codes": "💬 الأكواد",
        "btn_contests": "🎁 المسابقات",
        "btn_ads": "📢 الإعلانات",
        "btn_support": "💭 الدعم",
        "btn_me": "👤 ملفي",
        "btn_explore": "🌐 استكشف",
        "btn_settings": "⚙️ الإعدادات",
        "btn_admin": "👮 لوحة الأدمن",
    }

    text = "📐 <b>" + names.get(key, key) + "</b>\n\n"
    text += "📍 الصف: <b>" + str(ri + 1) + "</b>\n"
    text += "📍 العمود: <b>" + str(ci + 1) + "</b>\n"
    text += "📏 العرض: <b>" + ("عريض (2)" if w >= 2 else "نص (1)") + "</b>\n\n"
    text += "اختر الحركة:"

    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        btn("⬆️ صف فوق", "grd2:up:" + key, key="btn_up"),
        btn("⬇️ صف تحت", "grd2:down:" + key, key="btn_down")
    )
    kb.add(
        btn("⬅️ عمود يسار", "grd2:left:" + key, key="btn_left"),
        btn("➡️ عمود يمين", "grd2:right:" + key, key="btn_right")
    )
    kb.add(btn("➕ صف جديد أسفل", "grd2:newrow:" + key, key="btn_newrow"))

    if w >= 2:
        kb.add(btn("📏 جعله نص (1)", "grd2:w1:" + key, key="btn_w1"))
    else:
        kb.add(btn("📏 جعله عريض (2)", "grd2:w2:" + key, key="btn_w2"))

    kb.add(btn("⬅️ رجوع", "admin:layout_edit", key="btn_back"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("grd2:up:"))
def cb_grd2_up(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    conn = db()
    try:
        r = conn.execute("SELECT row_idx FROM main_menu_grid WHERE button_key=?", (key,)).fetchone()
        if r:
            ri = max(0, r["row_idx"] - 1)
            conn.execute("UPDATE main_menu_grid SET row_idx=? WHERE button_key=?", (ri, key))
            conn.commit()
    finally:
        conn.close()
    bot.answer_callback_query(call.id, "✅")
    call.data = "grd2:btn:" + key
    cb_grid2_btn(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("grd2:down:"))
def cb_grd2_down(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    conn = db()
    try:
        r = conn.execute("SELECT row_idx FROM main_menu_grid WHERE button_key=?", (key,)).fetchone()
        if r:
            ri = r["row_idx"] + 1
            conn.execute("UPDATE main_menu_grid SET row_idx=? WHERE button_key=?", (ri, key))
            conn.commit()
    finally:
        conn.close()
    bot.answer_callback_query(call.id, "✅")
    call.data = "grd2:btn:" + key
    cb_grid2_btn(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("grd2:left:"))
def cb_grd2_left(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    conn = db()
    try:
        r = conn.execute("SELECT col_idx FROM main_menu_grid WHERE button_key=?", (key,)).fetchone()
        if r:
            ci = max(0, r["col_idx"] - 1)
            conn.execute("UPDATE main_menu_grid SET col_idx=? WHERE button_key=?", (ci, key))
            conn.commit()
    finally:
        conn.close()
    bot.answer_callback_query(call.id, "✅")
    call.data = "grd2:btn:" + key
    cb_grid2_btn(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("grd2:right:"))
def cb_grd2_right(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    conn = db()
    try:
        r = conn.execute("SELECT col_idx FROM main_menu_grid WHERE button_key=?", (key,)).fetchone()
        if r:
            ci = r["col_idx"] + 1
            conn.execute("UPDATE main_menu_grid SET col_idx=? WHERE button_key=?", (ci, key))
            conn.commit()
    finally:
        conn.close()
    bot.answer_callback_query(call.id, "✅")
    call.data = "grd2:btn:" + key
    cb_grid2_btn(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("grd2:newrow:"))
def cb_grd2_newrow(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    conn = db()
    try:
        last = conn.execute("SELECT MAX(row_idx) FROM main_menu_grid").fetchone()
        last_row = (last[0] if last[0] is not None else 0) + 1
        conn.execute("UPDATE main_menu_grid SET row_idx=?, col_idx=0 WHERE button_key=?", (last_row, key))
        conn.commit()
    finally:
        conn.close()
    bot.answer_callback_query(call.id, "✅ صف جديد")
    call.data = "grd2:btn:" + key
    cb_grid2_btn(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("grd2:w1:"))
def cb_grd2_w1(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    _grid2_update(key, width=1)
    bot.answer_callback_query(call.id, "✅ نص (1)")
    call.data = "grd2:btn:" + key
    cb_grid2_btn(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("grd2:w2:"))
def cb_grd2_w2(call):
    if not user_is_admin(call.from_user.id):
        return
    key = call.data.split(":", 2)[2]
    _grid2_update(key, width=2)
    bot.answer_callback_query(call.id, "✅ عريض (2)")
    call.data = "grd2:btn:" + key
    cb_grid2_btn(call)


@bot.callback_query_handler(func=lambda c: c.data == "grd2:reset")
def cb_grd2_reset(call):
    if not user_is_admin(call.from_user.id):
        return
    conn = db()
    conn.execute("DELETE FROM main_menu_grid")
    defaults = [
        ("btn_platforms", 0, 0, 2),
        ("btn_support", 1, 0, 1),
        ("btn_me", 1, 1, 1),
        ("btn_explore", 2, 0, 1),
        ("btn_settings", 2, 1, 1),
        ("btn_admin", 3, 0, 1),
    ]
    for k, r, cl, w in defaults:
        conn.execute("INSERT INTO main_menu_grid (button_key, row_idx, col_idx, width) VALUES (?, ?, ?, ?)", (k, r, cl, w))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "✅ تم", show_alert=True)
    call.data = "admin:layout_edit"
    cb_admin_layout_edit(call)



# ============================================================
# الإعدادات الحقيقية
# ============================================================

@bot.callback_query_handler(func=lambda c: c.data == "menu:my_stats")
def cb_my_stats(call):
    uid = call.from_user.id
    
    # جلب عدد الأكواد
    codes = 0
    try:
        conn = db()
        row = conn.execute("SELECT total_codes FROM user_stats WHERE telegram_id=?", (uid,)).fetchone()
        if row:
            codes = row["total_codes"]
        conn.close()
    except Exception:
        pass
        
    # جلب عدد الزيارات
    visits = 0
    try:
        conn = db()
        row = conn.execute("SELECT visits FROM users WHERE telegram_id=?", (uid,)).fetchone()
        if row:
            visits = row["visits"]
        conn.close()
    except Exception:
        pass

    nl = chr(10)
    text = "📊 <b>ملفك الشخصي وإحصائياتك</b>" + nl
    text += "━━━━━━━━━━━━━━━━━━" + nl
    text += "👤 <b>الاسم:</b> " + str(call.from_user.first_name or "User") + nl
    text += "🆔 <b>الآي دي:</b> <code>" + str(uid) + "</code>" + nl + nl
    text += "🔑 <b>الأكواد التي سحبتها:</b> " + str(codes) + nl
    text += "👁 <b>عدد زياراتك للبوت:</b> " + str(visits) + nl
    text += "━━━━━━━━━━━━━━━━━━" + nl
    text += "💡 <i>هذه إحصائيات تفاعلك مع البوت.</i>"
    
    kb = InlineKeyboardMarkup()
    kb.add(btn("🔄 تحديث", "menu:my_stats", BTN.PRIMARY))
    kb.add(btn("⬅️ رجوع", "menu:home"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == "menu:settings")
def cb_settings(call):
    uid = call.from_user.id

    # احفظ اللغة في DB
    conn = db()
    try:
        conn.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'ar'")
        conn.commit()
    except Exception:
        pass
    try:
        row = conn.execute("SELECT language FROM users WHERE telegram_id=?", (uid,)).fetchone()
        lang = (row["language"] if row and row["language"] else "ar")
    except Exception:
        lang = "ar"
    finally:
        conn.close()

    lang_name = "العربية 🇸🇦" if lang == "ar" else "English 🇬🇧"

    text = (
        "⚙️ <b>الإعدادات</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🌐 <b>اللغة الحالية:</b> " + lang_name + "\n"
        "━━━━━━━━━━━━━━━━━━━"
    )

    kb = InlineKeyboardMarkup(row_width=1)
    if lang == "ar":
        kb.add(btn("🌐 تغيير إلى English 🇬🇧", "set:lang:en", key="btn_lang"))
    else:
        kb.add(btn("🌐 تغيير إلى العربية 🇸🇦", "set:lang:ar", key="btn_lang"))

    kb.add(btn("👤 ملفي", "menu:me", key="btn_me"))
    kb.add(btn("⬅️ رجوع", "menu:home", key="btn_back"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("set:lang:"))
def cb_set_lang(call):
    uid = call.from_user.id
    lang = call.data.split(":", 2)[2]

    if lang not in ("ar", "en"):
        return

    conn = db()
    try:
        conn.execute("UPDATE users SET language=? WHERE telegram_id=?", (lang, uid))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

    bot.answer_callback_query(call.id, "✅ تم تغيير اللغة", show_alert=True)

    # أعد فتح الإعدادات
    call.data = "menu:settings"
    cb_settings(call)



# ============================================================
# /start — اختيار اللغة فقط
# ============================================================










@bot.message_handler(commands=["start"])
def cmd_start(msg):
    try:
        _cmd_start_impl(msg)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("[START_ERROR] " + str(e))
        print(tb)
        try:
            bot.send_message(msg.chat.id, "⚠️ حدث خطأ مؤقت. جرب تاني.\n\n<code>" + tb[-800:] + "</code>", parse_mode="HTML")
        except Exception:
            pass


def _cmd_start_impl(msg):
    uid = msg.from_user.id
    username = msg.from_user.username or ""
    display_name = msg.from_user.first_name or ""

    user_states.pop(uid, None)

    # فحص وضع الصيانة
    if is_maintenance() and not user_is_admin(uid):
        nl = chr(10)
        maint_text = "🛠️ <b>نظام الصيانة</b> 🛠️" + nl
        maint_text += "━━━━━━━━━━━━━━━━━━" + nl
        maint_text += "⏳ <b>نعتذر منك، البوت يخضع لأعمال صيانة وتحديث حالياً.</b>" + nl + nl
        maint_text += "🚀 <i>نعمل على تحسين الخدمة لتكون أفضل لك.</i>" + nl
        maint_text += "🔔 <i>يرجى المحاولة مرة أخرى بعد قليل.</i>" + nl
        maint_text += "━━━━━━━━━━━━━━━━━━" + nl
        maint_text += "💙 <b>شكراً لصبرك وتفهمك!</b>"
        bot.send_message(msg.chat.id, maint_text, parse_mode="HTML")
        return

    # تحقق إذا مسجل
    u = user_get(uid)
    if u:
        if u.get("is_banned"):
            bot.send_message(msg.chat.id, "🚫 أنت محظور.")
            return

        # تحديث الزيارة
        conn = db()
        conn.execute("UPDATE users SET visits=visits+1, last_login=? WHERE telegram_id=?",
                     (time.time(), uid))
        conn.commit()
        conn.close()

        # إذا عنده لغة محفوظة → القائمة مباشرة
        user_lang = None
        try:
            conn = db()
            row = conn.execute("SELECT language FROM users WHERE telegram_id=?", (uid,)).fetchone()
            if row and row["language"]:
                user_lang = row["language"]
            conn.close()
        except Exception as e:
            pass
        if not user_lang:
            # ما عنده لغة → اختر اللغة
            # print("[START] -> show_human_verification")
            show_human_verification(msg.chat.id, msg.from_user.first_name or 'User')
            return

        # عنده لغة → القائمة (الجدول أولاً ثم الأزرار)
        # print("[START] -> sending main_menu")
        bot.send_message(msg.chat.id, main_menu_text(uid), reply_markup=main_menu_kb(uid))
        # print("[START] -> sent OK")
        return

    # مستخدم جديد → اختر اللغة
    show_human_verification(msg.chat.id, msg.from_user.first_name or 'User')


def show_human_verification(chat_id, name="User"):
    # print("[HV] start chat_id=" + str(chat_id) + " name=" + str(name))
    custom_welcome = setting_get("welcome_text", "")
    nl = chr(10)

    if custom_welcome and custom_welcome.strip():
        try:
            p_count = len(numbers_platforms())
            n_count = numbers_count()
        except Exception:
            p_count = 0
            n_count = 0

        uid = chat_id

        # استبدال المتغيرات
        text = str(custom_welcome)
        text = text.replace("{name}", str(name))
        text = text.replace("{id}", str(uid))
        text = text.replace("{platforms}", str(p_count))
        text = text.replace("{numbers}", str(n_count))
        text = text.replace("{codes}", "0")
        text = text.replace("{visits}", "1")
    else:
        text = "✨ <b>أهلاً بك في Matari_OTP</b> ✨" + nl
        text += "━━━━━━━━━━━━━━━━━━" + nl + nl
        text += "👋 أهلاً وسهلاً بك يا <b><u>" + name + "</u></b>" + nl + nl
        text += "🌐 <b>اختر لغتك المفضلة للمتابعة:</b>" + nl
        text += "🌐 <i>Choose your preferred language:</i>" + nl
        text += "━━━━━━━━━━━━━━━━━━"

    import random
    num1 = random.randint(1, 15)
    num2 = random.randint(1, 15)
    answer = num1 + num2
    
    wrong1 = answer + random.randint(1, 5)
    wrong2 = answer - random.randint(1, 5)
    if wrong2 <= 0:
        wrong2 = answer + random.randint(6, 10)
        
    options = [
        (str(answer), f"verify:ok:{answer}"),
        (str(wrong1), f"verify:no:{answer}"),
        (str(wrong2), f"verify:no:{answer}")
    ]
    random.shuffle(options)
    
    kb = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(text=opt[0], callback_data=opt[1]) for opt in options]
    kb.add(*buttons)
    
    text = "🤖 <b>التحقق البشري</b>" + nl
    text += "━━━━━━━━━━━━━━━━━━" + nl
    text += "👋 أهلاً بك يا <b>" + name + "</b>" + nl + nl
    text += "من فضلك حل السؤال التالي لإثبات أنك إنسان:" + nl + nl
    text += f"❓ <b>{num1} + {num2} = ؟</b>" + nl
    text += "━━━━━━━━━━━━━━━━━━"

    # print("[HV] sending verify message to " + str(chat_id))
    try:
        bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
        # print("[HV] sent OK")
    except Exception as e:
        # print("[HV] Welcome Error: " + str(e))
        # لو النص فيه مشكلة في الـ HTML، نبعته كنص عادي عشان ميقفش
        bot.send_message(chat_id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("verify:"))
def cb_verify(call):
    uid = call.from_user.id
    parts = call.data.split(":")
    action = parts[1]
    
    if action == "ok":
        username = call.from_user.username or ""
        display_name = call.from_user.first_name or "User"
        user_register(uid, username, display_name, "")
        
        # نسجل اللغة عشان ميتسألش تاني
        try:
            conn = db()
            try:
                conn.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'ar'")
                conn.commit()
            except Exception:
                pass
            conn.execute("UPDATE users SET language='ar' WHERE telegram_id=?", (uid,))
            conn.commit()
            conn.close()
        except Exception:
            pass
        
        try:
            bot.answer_callback_query(call.id, "✅ تم التحقق بنجاح!")
        except Exception:
            pass
            
        try:
            bot.edit_message_text(main_menu_text(uid), call.message.chat.id, call.message.message_id, reply_markup=main_menu_kb(uid), parse_mode="HTML")
        except Exception:
            bot.send_message(call.message.chat.id, main_menu_text(uid), reply_markup=main_menu_kb(uid), parse_mode="HTML")
    else:
        try:
            bot.answer_callback_query(call.id, "❌ إجابة خاطئة! حاول مرة أخرى.", show_alert=True)
        except Exception:
            pass
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        show_human_verification(call.message.chat.id, call.from_user.first_name or "User")

@bot.callback_query_handler(func=lambda c: c.data.startswith("lang:"))
def cb_choose_language(call):
    """يختار المستخدم اللغة — ينشئ الحساب تلقائياً"""
    uid = call.from_user.id
    lang = call.data.split(":", 1)[1]

    if lang not in ("ar", "en"):
        lang = "ar"

    # اسم المستخدم و ID من تيليجرام
    username = call.from_user.username or ""
    display_name = call.from_user.first_name or "صديقي"

    # أنشئ/حدّث المستخدم
    user_register(uid, username, display_name, "")

    # احفظ اللغة
    try:
        conn = db()
        # تأكد من وجود العمود
        try:
            conn.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'ar'")
            conn.commit()
        except Exception:
            pass
        conn.execute("UPDATE users SET language=? WHERE telegram_id=?", (lang, uid))
        conn.commit()
        conn.close()
    except Exception as e:
        print("[LANG] " + str(e))

    try:
        bot.answer_callback_query(call.id, "✅")
    except Exception:
        pass

    # رسالة الترحيب
    nl = chr(10)
    if lang == "ar":
        welcome = "✨ <b>أهلاً بك في Matari_OTP</b> ✨" + nl
        welcome += "━━━━━━━━━━━━━━━━━━" + nl + nl
        welcome += "👋 أهلاً وسهلاً بك يا <b><u>" + display_name + "</u></b>" + nl
        welcome += "🆔 معرفك: <code>" + str(uid) + "</code>" + nl + nl
        welcome += "👇 <i>اختر من الأزرار أدناه:</i>"
    else:
        welcome = "✨ <b>Welcome to Matari_OTP</b> ✨" + nl
        welcome += "━━━━━━━━━━━━━━━━━━" + nl + nl
        welcome += "👋 Welcome <b><u>" + display_name + "</u></b>" + nl
        welcome += "🆔 ID: <code>" + str(uid) + "</code>" + nl + nl
        welcome += "👇 <i>Choose from below:</i>"

    try:
        bot.edit_message_text(welcome, call.message.chat.id, call.message.message_id,
                              reply_markup=main_menu_kb(uid), parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, welcome,
                        reply_markup=main_menu_kb(uid), parse_mode="HTML")



# ============================================================
# الترجمة الحقيقية
# ============================================================
TRANS = {
    "ar": {
        "welcome": "أهلاً بك يا ",
        "id_label": "المعرف: ",
        "choose": "اختر من الأزرار:",
        "platforms": "📱 المنصات",
        "codes": "💬 الأكواد",
        "contests": "🎁 المسابقات",
        "ads": "📢 الإعلانات",
        "support": "💭 الدعم",
        "me": "👤 ملفي",
        "explore": "🌐 استكشف",
        "settings": "⚙️ الإعدادات",
        "admin": "👮 لوحة الأدمن",
    },
    "en": {
        "welcome": "Welcome ",
        "id_label": "ID: ",
        "choose": "Choose from below:",
        "platforms": "📱 Platforms",
        "codes": "💬 Codes",
        "contests": "🎁 Contests",
        "ads": "📢 Ads",
        "support": "💭 Support",
        "me": "👤 My Profile",
        "explore": "🌐 Explore",
        "settings": "⚙️ Settings",
        "admin": "👮 Admin Panel",
    },
}


def get_user_lang(uid):
    lang = "ar"
    try:
        conn = db()
        row = conn.execute("SELECT language FROM users WHERE telegram_id=?", (uid,)).fetchone()
        if row and row["language"]:
            lang = row["language"]
        conn.close()
    except Exception:
        pass
    return lang


def T(uid, key):
    lang = get_user_lang(uid)
    return TRANS.get(lang, TRANS["ar"]).get(key, key)



# ============================================================
# تجربة إرسال كود للقناة
# ============================================================



@bot.callback_query_handler(func=lambda c: c.data == "chf:set_admin_name")
def cb_chf_set_admin_name(call):
    if not user_is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "chf_admin_name", {})
    current = setting_get("admin_btn_name", "") or "👑 لوحة المطور"
    bot.send_message(call.message.chat.id,
        "📝 <b>أرسل الاسم الجديد للزر</b>\n\n"
        "الاسم الحالي: <b>" + current + "</b>\n\n"
        "مثال: <code>Admin</code> أو <code>👑 لوحة الإدارة</code>\n\n"
        "/cancel للإلغاء", parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "chf_admin_name")
def handle_chf_admin_name(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    txt = (msg.text or "").strip()
    if not txt:
        return
    setting_set("admin_btn_name", txt)
    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ <b>تم حفظ اسم الزر:</b> " + txt, parse_mode="HTML")




@bot.callback_query_handler(func=lambda c: c.data == "admin:auto_delete" or c.data.startswith("autodel:"))
def cb_admin_auto_delete(call):
    if not user_is_admin(call.from_user.id):
        return
        
    if call.data.startswith("autodel:toggle"):
        curr = setting_get("auto_delete_enabled", "0")
        setting_set("auto_delete_enabled", "0" if curr == "1" else "1")
        bot.answer_callback_query(call.id, "تم التغيير")
        call.data = "admin:auto_delete"
        return cb_admin_auto_delete(call)
        
    if call.data.startswith("autodel:set:"):
        mins = call.data.split(":")[2]
        setting_set("auto_delete_mins", mins)
        bot.answer_callback_query(call.id, "تم تحديد الوقت: " + mins + " دقيقة")
        call.data = "admin:auto_delete"
        return cb_admin_auto_delete(call)

    if call.data == "autodel:clear_now":
        try:
            conn = db()
            rows = conn.execute("SELECT id, chat_id, message_id FROM channel_messages").fetchall()
            count = 0
            for r in rows:
                try:
                    bot.delete_message(r["chat_id"], r["message_id"])
                    count += 1
                except Exception:
                    pass
                conn.execute("DELETE FROM channel_messages WHERE id=?", (r["id"],))
            conn.commit()
            conn.close()
            bot.answer_callback_query(call.id, f"تم حذف {count} رسالة", show_alert=True)
        except Exception as e:
            bot.answer_callback_query(call.id, "خطأ: " + str(e)[:50], show_alert=True)
        return

    enabled = setting_get("auto_delete_enabled", "0") == "1"
    mins = setting_get("auto_delete_mins", "3")
    
    status = "✅ مفعل" if enabled else "❌ معطل"
    
    text = "🧹 <b>إدارة تنظيف القناة</b>\n\n"
    text += f"الحالة: <b>{status}</b>\n"
    text += f"مدة الحذف: <b>كل {mins} دقيقة</b>\n\n"
    text += "سيقوم البوت بحذف الرسائل المرسلة للقناة تلقائياً بعد المدة المحددة."
    
    kb = InlineKeyboardMarkup(row_width=2)
    
    if enabled:
        kb.add(btn("⏸ إيقاف الميزة", "autodel:toggle", key="btn_stop"))
    else:
        kb.add(btn("▶️ تشغيل الميزة", "autodel:toggle", key="btn_start"))
        
    kb.add(btn("⏱ 1 دقيقة", "autodel:set:1"), btn("⏱ 3 دقائق", "autodel:set:3"))
    kb.add(btn("⏱ 5 دقائق", "autodel:set:5"), btn("⏱ 10 دقائق", "autodel:set:10"))
    
    kb.add(btn("🗑 حذف كل الرسائل الآن", "autodel:clear_now", BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)



@bot.callback_query_handler(func=lambda c: c.data == "admin:custom_template" or c.data.startswith("ctmpl:"))
def cb_custom_template(call):
    if not user_is_admin(call.from_user.id): return
    
    if call.data == "ctmpl:edit":
        set_state(call.from_user.id, "custom_template", {})
        msg = """📝 <b>أرسل القالب الجديد الآن:</b>

يمكنك استخدام الرموز التعبيرية التالية وسيتم استبدالها تلقائياً:
<code>{platform}</code> = المنصة
<code>{number}</code> = الرقم
<code>{country}</code> = العلم
<code>{iso}</code> = رمز الدولة
<code>{lang}</code> = اللغة
<code>{sms}</code> = نص الرسالة
<code>{prefix}</code> = اسم اللوحة

مثال:
<code>{platform} | {number} | {country} {iso}
━━━━━━━━━━━━
SMS: {sms}
⚙️ api {prefix}</code>

/cancel للإلغاء"""
        bot.send_message(call.message.chat.id, msg, parse_mode="HTML")
        return
        
    if call.data == "ctmpl:reset":
        setting_set("custom_otp_template", "")
        bot.answer_callback_query(call.id, "تم إعادة القالب الافتراضي", show_alert=True)
        return

    current = setting_get("custom_otp_template", "")
    if not current:
        current = "القالب الافتراضي (غير مخصص)"
    else:
        current = "القالب المخصص الحالي"
        
    text = f"🎨 <b>تخصيص قالب الرسالة</b>\n\n"
    text += f"الحالة: {current}\n\n"
    text += "يمكنك التحكم في ترتيب النصوص والإيموجيات بالكامل."
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("✏️ تعديل القالب", "ctmpl:edit", BTN.PRIMARY))
    kb.add(btn("🔄 إعادة الافتراضي", "ctmpl:reset", BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "admin:codes"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "notify_template")
def handle_notify_template(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    txt = (msg.text or "").strip()
    if not txt: return
    
    if txt == "/cancel":
        clear_state(uid)
        bot.send_message(msg.chat.id, "❌ تم الإلغاء")
        return
        
    setting_set("notify_template", txt)
    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم حفظ قالب الإشعار بنجاح! سيتم استخدامه في الإشعارات القادمة.")


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "welcome_msg_edit")
def handle_welcome_msg_edit(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    txt = (msg.text or "").strip()
    if not txt: return
    if txt == "/cancel":
        clear_state(uid)
        bot.send_message(msg.chat.id, "❌ تم الإلغاء")
        return
    # تنظيف النص من أكواد <code> اللي بتتنسخ مع النص
    txt = txt.strip().replace("<code>", "").replace("</code>", "").strip()
    if txt.startswith("<code>") and txt.endswith("</code>"):
        txt = txt[6:-7].strip()
        
    setting_set("welcome_text", txt)
    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم حفظ رسالة الترحيب بنجاح! جرب /start لتجربتها.")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "custom_template")
def handle_custom_template(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    txt = (msg.text or "").strip()
    if not txt: return
    
    if txt == "/cancel":
        clear_state(uid)
        bot.send_message(msg.chat.id, "❌ تم الإلغاء")
        return
        
    setting_set("custom_otp_template", txt)
    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم حفظ القالب الجديد بنجاح! جربه الآن بزر تجربة الإرسال.")



@bot.callback_query_handler(func=lambda c: c.data == "admin:template_custom" or c.data.startswith("tpl:"))
def cb_template_custom(call):
    if not user_is_admin(call.from_user.id): 
        return
        




    if call.data == "tpl:welcome_edit":
        set_state(call.from_user.id, "welcome_msg_edit", {})
        current = setting_get("welcome_text", "")
        msg = "📝 <b>أرسل رسالة الترحيب الجديدة:</b>\n\n"
        msg += "يمكنك استخدام <code>{name}</code> ليتم استبدالها باسم المستخدم تلقائياً.\n\n"
        if current:
            msg += "النص الحالي:\n<code>" + html.escape(current) + "</code>\n\n"
        msg += "/cancel للإلغاء"
        
        kb = InlineKeyboardMarkup()
        kb.add(btn("👁 معاينة الشكل الافتراضي (الحالي)", "tpl:welcome_preview", BTN.SUCCESS))
        kb.add(btn("📚 معرض قوالب الترحيب الجاهزة", "tpl:welcome_gallery", BTN.PRIMARY))
        
        bot.send_message(call.message.chat.id, msg, reply_markup=kb, parse_mode="HTML")
        return

    if call.data == "tpl:welcome_gallery":
        gallery_text = "📚 <b>معرض قوالب الترحيب</b>\n\n"
        gallery_text += "اختر القالب اللي يعجبك، وانسخه عشان تعدل عليه:"
        
        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(btn("👑 القالب الملكي (فخم)", "tpl:preview_welcome:royal"))
        kb.add(btn("💻 القالب التقني (إحصائيات)", "tpl:preview_welcome:tech"))
        kb.add(btn("✨ القالب البسيط (خفيف)", "tpl:preview_welcome:simple"))
        kb.add(btn("⬅️ رجوع", "tpl:welcome_edit"))
        
        bot.edit_message_text(gallery_text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
        return

    if call.data.startswith("tpl:preview_welcome:"):
        style = call.data.split(":")[2]
        
        if style == "royal":
            txt = "╔═════════════════════╗\n   <b>✨ MATARI OTP ✨</b>   \n╚═════════════════════╝\n\n👤 أهلاً بك يا <b>{name}</b> 😩 👋\n┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n🆔 معرفك : <code>{id}</code>\n📱 المنصات : <b>{platforms}</b>\n☎️ الأرقام : <b>{numbers}</b>\n┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n👇 <i>اختر الخدمة التي تريدها من الأزرار بالأسفل:</i>"
        elif style == "tech":
            txt = "<b>⚡ SYSTEM ACTIVE ⚡</b>\n━━━━━━━━━━━━━━━━━━\n👤 المستخدم: <b>{name}</b>\n🆔 ID: <code>{id}</code>\n👁 الزيارات: <b>{visits}</b>\n🔑 أكوادك: <b>{codes}</b>\n━━━━━━━━━━━━━━━━━━\n📊 <i>النظام يعمل بكفاءة عالية</i>"
        else:
            txt = "✨ <b>مرحباً بك يا {name}!</b> ✨\n\nأنت الآن في بوت <b>MATARI OTP</b>\nاختر من الأزرار بالأسفل ما يناسبك 👇"
            
        kb = InlineKeyboardMarkup()
        kb.add(btn("📋 نسخ هذا القالب", "tpl:copy_welcome:" + style, BTN.SUCCESS))
        kb.add(btn("⬅️ رجوع للمعرض", "tpl:welcome_gallery"))
        
        # معاينة
        preview = txt.replace("{name}", "User").replace("{id}", "123456789").replace("{platforms}", "5").replace("{numbers}", "120").replace("{codes}", "3").replace("{visits}", "10")
        
        try:
            bot.edit_message_text(preview, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
        except Exception:
            bot.send_message(call.message.chat.id, preview, reply_markup=kb, parse_mode="HTML")
        return
        
    if call.data.startswith("tpl:copy_welcome:"):
        style = call.data.split(":")[2]
        
        if style == "royal":
            txt = "╔═════════════════════╗\n   <b>✨ MATARI OTP ✨</b>   \n╚═════════════════════╝\n\n👤 أهلاً بك يا <b>{name}</b> 😩 👋\n┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n🆔 معرفك : <code>{id}</code>\n📱 المنصات : <b>{platforms}</b>\n☎️ الأرقام : <b>{numbers}</b>\n┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n👇 <i>اختر الخدمة التي تريدها من الأزرار بالأسفل:</i>"
        elif style == "tech":
            txt = "<b>⚡ SYSTEM ACTIVE ⚡</b>\n━━━━━━━━━━━━━━━━━━\n👤 المستخدم: <b>{name}</b>\n🆔 ID: <code>{id}</code>\n👁 الزيارات: <b>{visits}</b>\n🔑 أكوادك: <b>{codes}</b>\n━━━━━━━━━━━━━━━━━━\n📊 <i>النظام يعمل بكفاءة عالية</i>"
        else:
            txt = "✨ <b>مرحباً بك يا {name}!</b> ✨\n\nأنت الآن في بوت <b>MATARI OTP</b>\nاختر من الأزرار بالأسفل ما يناسبك 👇"
            
        bot.send_message(call.message.chat.id, "<code>" + html.escape(txt) + "</code>", parse_mode="HTML")
        bot.answer_callback_query(call.id, "تم إرسال القالب، انسخه وعدله ثم أرسله للبوت.")
        return

    if call.data == "tpl:welcome_preview":
        name = call.from_user.first_name or "User"
        uid = call.from_user.id
        custom_welcome = setting_get("welcome_text", "")
        nl = chr(10)
        
        if custom_welcome:
            text = custom_welcome.replace("{name}", name)
        else:
            text = "╔═════════════════════╗" + nl
            text += "   <b>✨ MATARI OTP ✨</b>   " + nl
            text += "╚═════════════════════╝" + nl + nl
            text += "👤 أهلاً بك يا <b>" + name + "</b> 😩 👋" + nl
            text += "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈" + nl
            text += "🆔 معرفك : <code>" + str(uid) + "</code>" + nl
            text += "📱 الأرقام : <b>0</b>" + nl
            text += "🟢 الحالة : <b>متصل</b>" + nl
            text += "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈" + nl + nl
            text += "👇 <i>اختر الخدمة التي تريدها من الأزرار بالأسفل:</i>"
            
        kb = InlineKeyboardMarkup()
        kb.add(btn("📋 نسخ النص للتعديل", "tpl:welcome_copy", BTN.PRIMARY))
        kb.add(btn("⬅️ رجوع", "admin:template_custom"))
        
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
        return
        
    if call.data == "tpl:welcome_copy":
        nl = chr(10)
        default_text = "╔═════════════════════╗" + nl
        default_text += "   <b>✨ MATARI OTP ✨</b>   " + nl
        default_text += "╚═════════════════════╝" + nl + nl
        default_text += "👤 أهلاً بك يا <b>{name}</b> 😩 👋" + nl
        default_text += "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈" + nl
        default_text += "👇 <i>اختر الخدمة التي تريدها من الأزرار بالأسفل:</i>"
        
        bot.send_message(call.message.chat.id, "<code>" + html.escape(default_text) + "</code>", parse_mode="HTML")
        bot.answer_callback_query(call.id, "تم إرسال النص، انسخه وعدله ثم أرسله للبوت.")
        return

    if call.data == "tpl:notify_edit":
        set_state(call.from_user.id, "notify_template", {})
        msg = """📝 <b>أرسل قالب إشعار المستخدم الجديد:</b>

استخدم الرموز التالية وسيتم استبدالها تلقائياً:
<code>{platform}</code> = المنصة (تيك توك)
<code>{number}</code> = الرقم
<code>{country}</code> = الدولة
<code>{code}</code> = الكود

مثال:
<code>🔥 وصل كود جديد!
📱 {platform} | 🌍 {country}
☎️ {number}
🔑 {code}</code>

/cancel للإلغاء"""
        bot.send_message(call.message.chat.id, msg, parse_mode="HTML")
        return

    if call.data == "tpl:examples":
        examples_text = (
            "<b>📝 أمثلة وشرح القوالب (انسخ القالب والصقه في زر تعديل القالب):</b>\n\n"
            
            "<b>1️⃣ القالب البسيط (خفيف وواضح):</b>\n"
            "<i>هذا القالب يعرض البيانات في سطور منفصلة، مناسب إذا كانت الرسالة قصيرة.</i>\n"
            "<code>🔐 OTP\n"
            "📞 {platform} ⇢ {country}\n"
            "☎️ {number}\n"
            "💬 {sms}</code>\n\n"
            
            "<b>2️⃣ القالب المطور (خطوط وإطارات):</b>\n"
            "<i>هذا القالب يستخدم الخطوط المستقيمة (─) لعمل فواصل، ويعطي طابعاً تقنياً.</i>\n"
            "<code>🔐 <b><u>OTP</u></b>\n"
            "──────────────\n"
            "📞 {platform} ⇢ {country} #{iso}\n"
            "☎️ {number} | {lang}\n"
            "──────────────\n"
            "💬 {sms}\n"
            "⚙️ {prefix}</code>\n\n"
            
            "<b>3️⃣ القالب الفخم (إطار ناري):</b>\n"
            "<i>هذا القالب يستخدم الإطارات المزخرفة (╭ ╮) لإعطاء شكل فخم.</i>\n"
            "<code>╭──────🔥──────╮\n"
            "{platform} ⇢ {country}\n"
            "☎️ <b>{number}</b> | {lang}\n"
            "╰──────🔥──────╯\n"
            "SMS: {sms}\n"
            "api: {prefix}</code>"
        )
        kb = InlineKeyboardMarkup()
        kb.add(btn("⬅️ رجوع للقائمة", "admin:template_custom"))
        bot.send_message(call.message.chat.id, examples_text, parse_mode="HTML", reply_markup=kb)
        return

    if call.data == "tpl:preview":
        # 1. إرسال رسالة القناة (القالب المخصص)
        send_otp_message(call.message.chat.id, "🇾🇪", "967712345678", "en", 
                         "<#> Your WhatsApp code: 482-916. Do not share this code with anyone.", 
                         "482916", panel_name="TEST_PANEL")
        
        # 2. إرسال رسالة الإشعار الداخلي (تقرأ من القالب المخصص)
        custom_notify = setting_get("notify_template", "")
        
        # نجهز البيانات الافتراضية للمعاينة
        p_platform = "تيك توك"
        p_number = "+4741642515"
        p_country = "النرويج"
        p_code = "998877"
        
        if custom_notify:
            # إضافة دعم العلم والاختصار واللغة في المعاينة
            flag_icon, _, _cc = detect_country(p_number)
            iso_code = COUNTRIES.get(_cc, ("", ""))[0] or "XX"
            
            _pcodes = {"WhatsApp":"WH","Telegram":"TG","Facebook":"FB","Instagram":"IG",
                       "Twitter":"TW","Google":"GG","Apple":"AP","TikTok":"TT",
                       "Discord":"DC","Snapchat":"SC"}
            # ترجمة أسماء المنصات العربية للاختصارات الإنجليزية
            _ar_to_en = {
                "واتساب": "WhatsApp", "تيك توك": "TikTok", "تيليجرام": "Telegram",
                "فيسبوك": "Facebook", "انستقرام": "Instagram", "تويتر": "Twitter",
                "جوجل": "Google", "آبل": "Apple", "ديسكورد": "Discord", "سناب": "Snapchat"
            }
            eng_name = _ar_to_en.get(str(p_platform).strip(), str(p_platform))
            short_pname = _pcodes.get(eng_name, eng_name[:2].upper())
            
            notify_text = custom_notify.replace("{platform}", short_pname) # <-- هنا بنخليها تطلع TT
            notify_text = notify_text.replace("{number}", p_number)
            notify_text = notify_text.replace("{country}", p_country)
            notify_text = notify_text.replace("{code}", p_code)
            notify_text = notify_text.replace("{flag}", str(flag_icon))
            notify_text = notify_text.replace("{iso}", str(iso_code))
            notify_text = notify_text.replace("{lang}", "EN")
        else:
            # إذا لم يوجد قالب، استخدم الشكل الافتراضي
            notify_text = "🔥 <b>كود جديد وصل!</b> 🔥\n"
            notify_text += "📱 <b>" + p_platform + "</b> | " + p_country + "\n"
            notify_text += "☎️ <code>" + p_number + "</code>\n\n"
            notify_text += "🔑 <b>الكود:</b> <code>" + p_code + "</code>"
        
        kb = InlineKeyboardMarkup(row_width=1)
        # استخدام دالة _kb_btn عشان الزر يبقى زي القناة وقابل للنسخ
        btn_code = _kb_btn(" 998877", copy_text="998877")
        if btn_code:
            kb.add(btn_code)
        
        # زر الجروب
        group_link = setting_get("channel_link", "")
        if _valid_url(group_link):
            btn_group = _kb_btn("🔑 جروب البوت", url=group_link)
            if btn_group:
                kb.add(btn_group)
        
        try:
            bot.send_message(call.message.chat.id, notify_text, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            print("Error sending preview notify:", e)

        bot.answer_callback_query(call.id, "تم إرسال معاينتين (القناة + الإشعار)")
        return

    if call.data == "tpl:edit":
        set_state(call.from_user.id, "custom_template", {})
        msg = """📝 <b>أرسل القالب الجديد الآن:</b>

استخدم الرموز التالية وسيتم استبدالها تلقائياً:
<code>{platform}</code> = المنصة (WH)
<code>{number}</code> = الرقم (96771•••678)
<code>{country}</code> = العلم (🇾🇪)
<code>{iso}</code> = رمز الدولة (#YE)
<code>{lang}</code> = اللغة (#EN)
<code>{sms}</code> = نص الرسالة
<code>{prefix}</code> = اسم اللوحة

مثال:
<code>{platform} | {number}
{country} {iso} | {lang}
━━━━━━━━━━━━
SMS: {sms}
⚙️ api {prefix}</code>

/cancel للإلغاء"""
        bot.send_message(call.message.chat.id, msg, parse_mode="HTML")
        return
        
    if call.data == "tpl:reset":
        setting_set("custom_otp_template", "")
        bot.answer_callback_query(call.id, "تم إعادة القالب الافتراضي", show_alert=True)
        call.data = "admin:template_custom"
        return cb_template_custom(call)

    current = setting_get("custom_otp_template", "")
    status = "✅ القالب المخصص (مفعل)" if current else "⚪ القالب الافتراضي"
        
    text = f"🎨 <b>تخصيص قالب الرسالة</b>\n\n"
    text += f"الحالة: {status}\n\n"
    text += "يمكنك كتابة أي إيموجي (حتى المميزة) وترتيب النصوص كما تشاء."
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("✏️ تعديل القالب (للقناة)", "tpl:edit", BTN.PRIMARY))
    kb.add(btn("👋 تعديل رسالة الترحيب (/start)", "tpl:welcome_edit", BTN.PRIMARY))
    kb.add(btn("✉️ تخصيص إشعار المستخدم", "tpl:notify_edit", BTN.PRIMARY))
    kb.add(btn("📝 أمثلة وشرح القوالب", "tpl:examples", BTN.SUCCESS))
    kb.add(btn("👁 معاينة القالب", "tpl:preview", BTN.SUCCESS))
    kb.add(btn("🔄 إعادة الافتراضي", "tpl:reset", BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "admin:home"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "custom_template")
def handle_custom_template_save(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid): return
    txt = (msg.text or "").strip()
    if not txt: return
    
    if txt == "/cancel":
        clear_state(uid)
        bot.send_message(msg.chat.id, "❌ تم الإلغاء")
        return
        
    setting_set("custom_otp_template", txt)
    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم حفظ القالب الجديد بنجاح! جربه الآن بزر تجربة الإرسال.")


@bot.callback_query_handler(func=lambda c: c.data == "admin:channel")
def cb_admin_channel(call):
    if not user_is_admin(call.from_user.id):
        return

    chat_id = setting_get("forward_channel_id", "")
    channel_link = setting_get("channel_link", "")
    
    # نصوص الأزرار المخصصة
    btn_support = setting_get("btn_support_text", "🚀 Support")
    btn_bot = setting_get("btn_bot_text", "🤖 Nmbr Bot")
    btn_admin = setting_get("admin_btn_name", "👑 لوحة المطور")

    text = "📡 <b>إعدادات رسالة القناة</b>\n\n"
    text += "ID القناة: <code>" + (chat_id if chat_id else "غير محدد") + "</code>\n"
    text += "رابط القناة: <code>" + (channel_link if channel_link else "غير محدد") + "</code>\n\n"
    
    text += "━━━━ أسماء الأزرار ━━━━\n"
    text += "زر الدعم: " + btn_support + "\n"
    text += "زر البوت: " + btn_bot + "\n"
    text += "زر المطور: " + btn_admin + "\n\n"
    text += "💡 للتحكم في النصوص أو الألوان، استخدم الأزرار أدناه."

    kb = InlineKeyboardMarkup(row_width=2)
    
    # إدارة القناة الأساسية
    if chat_id:
        kb.add(btn("✏️ تعديل ID القناة", "chf:set", key="btn_edit_id"))
    else:
        kb.add(btn("➕ إضافة ID القناة", "chf:set", key="btn_add_id"))
    
    # روابط وأسماء الأزرار
    kb.add(btn("✏️ رابط الدعم", "chf:edit:link", key="btn_edit_link"))
    kb.add(btn("✏️ اسم زر الدعم", "chf:edit:btn_support", key="btn_edit_sup"))
    kb.add(btn("✏️ اسم زر البوت", "chf:edit:btn_bot", key="btn_edit_bot"))
    kb.add(btn("✏️ اسم زر المطور", "chf:edit:btn_admin", key="btn_edit_admin"))
    kb.add(btn("✏️ رابط زر المطور", "chf:edit:admin_link", key="btn_edit_admin_link"))
    
    # تجربة وإدارة
    kb.add(btn("🧪 تجربة الإرسال", "chf:test_send", key="btn_test_send"))
    if chat_id or channel_link:
        kb.add(btn("🗑 حذف كل الإعدادات", "chf:clear", key="btn_clear_channel"))
    
    kb.add(btn("⬅️ رجوع", "admin:home", key="btn_back"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("chf:edit:"))
def cb_chf_edit(call):
    if not user_is_admin(call.from_user.id):
        return
    field = call.data.split(":")[2]
    
    # تحديد ما سيتم تعديله
    if field == "link":
        key = "channel_link"
        prompt = "أرسل رابط قناة الدعم:"
    elif field == "btn_support":
        key = "btn_support_text"
        prompt = "أرسل اسم زر الدعم (مثال: 🚀 Support):"
    elif field == "btn_bot":
        key = "btn_bot_text"
        prompt = "أرسل اسم زر البوت (مثال: 🤖 Nmbr Bot):"
    elif field == "btn_admin":
        key = "admin_btn_name"
        prompt = "أرسل اسم زر المطور (مثال: 👑 Admin):"
    elif field == "admin_link":
        key = "admin_link"
        prompt = "أرسل رابط زر المطور (مثال: https://t.me/YourUsername أو tg://user?id=123):"
    else:
        return

    set_state(call.from_user.id, "chf_edit_field", {"key": key})
    bot.send_message(call.message.chat.id, "📝 " + prompt + "\n/cancel للإلغاء")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "chf_edit_field")
def handle_chf_edit_field(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        clear_state(uid)
        return
    s = get_state(uid)
    key = s["data"].get("key")
    txt = (msg.text or "").strip()
    
    if not key or not txt:
        return
        
    setting_set(key, txt)
    clear_state(uid)
    bot.send_message(msg.chat.id, "✅ تم الحفظ بنجاح.")



# ============================================================
# جلب اسم البوت (Username) تلقائياً
# ============================================================
_BOT_USERNAME_CACHE = {"name": "", "loaded": 0}


def get_bot_username():
    """يجلب اسم البوت من Telegram API"""
    now = time.time()
    if _BOT_USERNAME_CACHE["name"] and (now - _BOT_USERNAME_CACHE["loaded"]) < 3600:
        return _BOT_USERNAME_CACHE["name"]
    try:
        url = "https://api.telegram.org/bot" + BOT_TOKEN + "/getMe"
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("ok"):
            username = data.get("result", {}).get("username", "")
            _BOT_USERNAME_CACHE["name"] = username
            _BOT_USERNAME_CACHE["loaded"] = now
            return username
    except Exception:
        pass
    return ""


@bot.callback_query_handler(func=lambda c: c.data == "chf:test_send")
def cb_chf_test_send(call):
    if not user_is_admin(call.from_user.id):
        return
    forward_id = setting_get("forward_channel_id", "")
    if not forward_id:
        bot.answer_callback_query(call.id, "❌ أضف ID القناة أولاً", show_alert=True)
        return
    bot.answer_callback_query(call.id, "⏳ جاري الإرسال...")
    try:
        phone_clean = "967712345678"
        code_val = "482916"
        msg_text = "<#> Your WhatsApp code: 482-916. Do not share this code with anyone. rJbA/XP1K+V"
        country_flag, country_name, _cc = detect_country(phone_clean)
        support_link = setting_get("channel_link", "https://t.me/")
        bot_link = "https://t.me/" + get_bot_username()
        admin_link = setting_get("admin_link", "") or ("tg://user?id=" + str(MAIN_ADMIN_ID))
        OTP_LAST_ERROR["msg"] = ""
        sent_ok = send_otp_message(forward_id, country_flag, phone_clean, "en", msg_text, code_val,
                                   support_link, bot_link, admin_link, panel_name="TEST_PANEL",
                                   platform="WhatsApp", country_name=country_name)
        if sent_ok:
            bot.send_message(call.message.chat.id,
                             "✅ تم إرسال كود تجريبي للقناة!\n🎨 القالب: <b>" +
                             OTP_STYLES.get(setting_get("otp_style", "quote"), "") + "</b>")
        else:
            bot.send_message(call.message.chat.id,
                             "❌ فشل الإرسال للقناة\n<code>" + html.escape(OTP_LAST_ERROR["msg"][:200] or "؟") + "</code>\n\n"
                             "تأكد أن البوت <b>مشرف</b> في القناة وأن الـ ID صحيح. هذه معاينة الشكل هنا:")
            send_otp_message(call.message.chat.id, country_flag, phone_clean, "en", msg_text, code_val,
                             support_link, bot_link, admin_link, panel_name="TEST_PANEL",
                             platform="WhatsApp", country_name=country_name)
    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ خطأ: " + html.escape(str(e)[:150]))


# ============================================================
# إصلاح عرض صفحة اللوحة (ap:v:) - زر الفحص والتعديل
# ============================================================
def cb_ap_view_fixed(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return
    p = panel_get(pid)
    if not p:
        return
    
    # النص الأساسي
    text = (
        "🔗 " + str(p.get("url") or "") + "\n" +
        "📡 " + str(p.get("api_method") or "") + "\n" +
        "⏱ " + str(p.get("interval_sec") or 60) + "s\n" +
        "⚙️ " + str(p.get("last_status") or "idle") + "\n" +
        "📊 " + str(p.get("last_count") or 0) + " codes"
    )
    
    # الأزرار الأساسية
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(btn("🔍 فحص", "ap:t:" + str(pid), BTN.PRIMARY))
    kb.add(btn("💰 معلومات الحساب", "ap:acc:" + str(pid)))
    kb.add(btn("✏️ تعديل", "ap:edit:" + str(pid)))
    kb.add(btn("📊 إحصائيات", "ap:stats:" + str(pid)))
    kb.add(btn(" سجل الأخطاء", "ap:errs:" + str(pid)))
    kb.add(btn("🔄 سحب", "ap:f:" + str(pid)))
    if (p.get("fail_count") or 0) > 0:
        kb.add(btn("🔧 إصلاح العداد", "ap:rf:" + str(pid), BTN.SUCCESS))
    kb.add(btn("⏸ إيقاف" if p.get("enabled") else "▶️ تشغيل", "ap:tg:" + str(pid)))
    kb.add(btn("🗑 حذف", "ap:d:" + str(pid), BTN.DANGER))
    kb.add(btn("⬅️ رجوع", "ap:list"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:smart:"))
def cb_ap_smart_scan(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return
    p = panel_get(pid)
    if not p:
        return
    
    try:
        bot.answer_callback_query(call.id, "جاري الفحص الذكي...")
    except Exception:
        pass
    
    base = (p.get("url") or "").rstrip("/")
    token = p.get("token") or ""
    method = (p.get("api_method") or "GET").upper()
    
    paths_to_try = [
        "/api/v1/codes",
        "/api/codes",
        "/codes",
        "/api/v1/numbers",
        "/api/v1/me",
        "/api/v1/balance",
        "/api/v1/stats",
    ]
    
    results = []
    working_path = None
    
    for path in paths_to_try:
        try:
            url = base + path
            headers = {"Accept": "application/json"}
            if token:
                headers["X-API-Key"] = token
                headers["X-API-Token"] = token
                headers["Authorization"] = "Bearer " + token
            
            r = requests.get(url, headers=headers, timeout=5)
            
            if r.status_code == 200:
                ct = r.headers.get("content-type", "")
                if "json" in ct:
                    results.append("[OK] GET " + path + " -> 200 JSON")
                    if not working_path:
                        working_path = path
                else:
                    results.append("[HTML] GET " + path + " -> 200 HTML")
            else:
                results.append("[FAIL " + str(r.status_code) + "] GET " + path)
        except Exception as e:
            results.append("[ERR] GET " + path + " -> " + type(e).__name__)
    
    if working_path:
        panel_update(pid, api_path=working_path, api_method="GET", last_status="ok", last_error="")
        summary = "تم العثور على مسار شغال:\n" + working_path
    else:
        summary = "لم يتم العثور على مسار شغال."
    
    text = summary + "\n\nالنتائج:\n" + "\n".join(results)
    
    kb = InlineKeyboardMarkup()
    kb.add(btn("رجوع", "ap:v:" + str(pid), key="btn_back"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)




def format_uptime(seconds):
    seconds = int(max(0, seconds))
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if days > 0: parts.append(f"{days} يوم")
    if hours > 0: parts.append(f"{hours} ساعة")
    if minutes > 0 or (days == 0 and hours == 0): parts.append(f"{minutes} دقيقة")
    return " و ".join(parts)

def get_panel_uptime(pid, created_at):
    conn = db()
    row = conn.execute("SELECT * FROM panel_uptime WHERE panel_id=?", (pid,)).fetchone()
    now = time.time()
    
    if not row:
        conn.execute("INSERT INTO panel_uptime (panel_id, started_at, stopped_at, total_paused, is_running) VALUES (?, ?, 0, 0, 1)", (pid, now))
        conn.commit()
        conn.close()
        return 0
        
    is_running = row["is_running"]
    started_at = row["started_at"]
    total_paused = row["total_paused"]
    
    if is_running == 1:
        if started_at == 0:
            return 0
        uptime = now - started_at - total_paused
    else:
        uptime = row["stopped_at"] - started_at - total_paused
        
    conn.close()
    return max(0, uptime)

@bot.callback_query_handler(func=lambda c: c.data == "ap:list")
def cb_ap_list(call):
    if not user_is_admin(call.from_user.id):
        return
    import time
    panels = panels_list()
    if not panels:
        kb = InlineKeyboardMarkup()
        kb.add(btn("⬅️ رجوع", "admin:panels"))
        try:
            bot.edit_message_text("لا توجد لوحات", call.message.chat.id, call.message.message_id, reply_markup=kb)
        except Exception:
            bot.send_message(call.message.chat.id, "لا توجد لوحات", reply_markup=kb)
        return
        
    kb = InlineKeyboardMarkup(row_width=2)
    
    for p in panels:
        pid = p["id"]
        is_enabled = p["enabled"]
        
        # حساب وقت التشغيل
        uptime = get_panel_uptime(pid, p.get("created") or time.time())
        
        # تحويل الثواني لشكل ساعة (ساعة:دقيقة:ثانية)
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        timer_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # زر اللوحة
        status_icon = "🟢" if is_enabled else "🔴"
        btn_panel = _kb_btn(f"{status_icon} {p['name']}", "ap:v:" + str(pid) if is_enabled else "danger")
        
        # زر الساعة
        btn_timer = _kb_btn(f"⏱ {timer_text}", "noop" if is_enabled else "danger")
        
        if btn_panel and btn_timer:
            kb.row(btn_panel, btn_timer)
            
    kb.add(btn("⬅️ رجوع", "admin:panels"))
    
    try:
        bot.edit_message_text("📡 <b>اللوحات المتاحة:</b>" + chr(10) + "<i>الساعة الخضراء = شغالة | الحمراء = متوقفة</i>", call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, "📡 <b>اللوحات المتاحة:</b>" + chr(10) + "<i>الساعة الخضراء = شغالة | الحمراء = متوقفة</i>", reply_markup=kb, parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:v:"))
def cb_ap_view(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return
    
    p = panel_get(pid)
    if not p:
        return
    
    name = p.get("name") or "?"
    url = p.get("url") or "?"
    auth = p.get("auth_type") or "?"
    method = p.get("api_method") or "?"
    interval = p.get("interval_sec") or 60
    status = p.get("last_status") or "idle"
    count = p.get("last_count") or 0
    
    text = (
        "📡 <b>" + html.escape(str(name)) + "</b>\n\n"
        "🔗 " + html.escape(str(url)) + "\n"
        "🔑 " + html.escape(str(auth)) + "\n"
        "📡 " + html.escape(str(method)) + "\n"
        "⏱ " + str(interval) + "s\n"
        "⚙️ " + status + "\n"
        "📊 " + str(count) + " codes"
    )
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(btn("🔍 فحص", "ap:t:" + str(pid), BTN.PRIMARY))
    kb.add(btn("Smart Scan", "ap:smart:" + str(pid), BTN.SUCCESS))
    kb.add(btn("💰 معلومات الحساب", "ap:acc:" + str(pid)))
    kb.add(btn("✏️ تعديل", "ap:edit:" + str(pid)))
    kb.add(btn("📊 إحصائيات", "ap:stats:" + str(pid)))
    kb.add(btn(" سجل الأخطاء", "ap:errs:" + str(pid)))
    kb.add(btn("🔄 سحب", "ap:f:" + str(pid)))
    if (p.get("fail_count") or 0) > 0:
        kb.add(btn("🔧 إصلاح العداد", "ap:rf:" + str(pid), BTN.SUCCESS))
    kb.add(btn("⏸ إيقاف" if p.get("enabled") else "▶️ تشغيل", "ap:tg:" + str(pid)))
    kb.add(btn("🗑 حذف", "ap:d:" + str(pid), BTN.DANGER))
    kb.add(btn("🔗 Curl", "ap:curl:" + str(pid), BTN.SUCCESS))
    kb.add(btn("⬅️ رجوع", "ap:list"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:t:"))
def cb_ap_test(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return

    p = panel_get(pid)
    if not p:
        bot.answer_callback_query(call.id, "اللوحة غير موجودة", show_alert=True)
        return

    try:
        bot.answer_callback_query(call.id, "جاري الفحص...")
    except Exception:
        pass

    # ناخد البيانات من إعدادات اللوحة
    base = (p.get("url") or "").rstrip("/")
    path = (p.get("api_path") or "/api/v1/numbers")
    method = (p.get("api_method") or "GET").upper()
    token = p.get("token") or ""
    
    # نجيب أول رقم من الداتابيز (نفس اللي في الـ curl)
    test_phone = "+94761312598" # افتراضي
    try:
        nums = numbers_list(limit=1)
        if nums:
            test_phone = nums[0]["phone"]
    except Exception:
        pass
        
    test_path = path.replace("{phone}", test_phone)
    test_url = base + test_path
    
    # نجهز الهيدرز
    headers = {"Accept": "application/json"}
    if token:
        headers["X-API-Key"] = token
        headers["X-API-Token"] = token
        headers["Authorization"] = "Bearer " + token
    
    try:
        # نستخدم الطريقة من إعدادات اللوحة
        if method == "POST":
            r = requests.post(test_url, headers=headers, timeout=10)
        else:
            r = requests.get(test_url, headers=headers, timeout=10)
        
        # نحلل الرد
        status = r.status_code
        ct = r.headers.get("content-type", "")
        
        if status == 200:
            icon = "✅"
            msg = "الاتصال ناجح"
        else:
            icon = "❌"
            msg = "فشل الاتصال"
        
        # نص الفحص
        text = "🔍 <b>نتيجة الفحص</b>\n\n"
        text += "🆔 اللوحة: <b>" + html.escape(str(p.get("name") or "?")) + "</b>\n"
        text += icon + " " + msg + "\n"
        text += "📡 Method: <code>" + method + "</code>\n"
        text += "🌐 URL: <code>" + test_url + "</code>\n"
        text += "📡 HTTP: <code>" + str(status) + "</code>\n"
        
        if "json" in ct:
            try:
                data = r.json()
                codes_count = 0
                if isinstance(data, list):
                    codes_count = len(data)
                elif isinstance(data, dict):
                    for k in ("codes", "data", "items"):
                        if k in data and isinstance(data[k], list):
                            codes_count = len(data[k])
                            break
                text += "📊 عدد الأكواد: <b>" + str(codes_count) + "</b>\n"
            except Exception:
                pass
        elif "html" in ct:
            text += "⚠️ الرد HTML (مش JSON)\n"
        
        # معلومات الحساب
        try:
            account = fetch_account_info(p)
            if account:
                text += format_account_box(account)
        except Exception:
            pass
        
        # الأزرار
        kb = InlineKeyboardMarkup()
        kb.add(btn("🔄 فحص مرة أخرى", "ap:t:" + str(pid), BTN.PRIMARY))
        kb.add(btn("⬅️ رجوع", "ap:v:" + str(pid)))
        
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)
            
    except Exception as e:
        error_text = "❌ خطأ: " + str(e)[:100]
        kb = InlineKeyboardMarkup()
        kb.add(btn("⬅️ رجوع", "ap:v:" + str(pid)))
        try:
            bot.edit_message_text(error_text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        except Exception:
            bot.send_message(call.message.chat.id, error_text, reply_markup=kb)



def process_uploaded_numbers(text, platform="أخرى"):
    """يعالج نص ويضيف الأرقام مع تحديد الدولة تلقائياً. يرجع (المضاف، المكرر)"""
    added = 0
    duplicate = 0
    conn = db()
    
    # تنظيف اسم المنصة من أي (Panel:XX) عشان نمنع التكرار
    base_platform = platform
    if "(Panel:" in base_platform:
        base_platform = base_platform.split("(Panel:")[0].strip()
    
    for line in text.split(chr(10)):
        line = line.strip()
        if not line:
            continue
        if line.startswith("+") or (line and line[0].isdigit()):
            phone = line if line.startswith("+") else "+" + line
            
            # التحقق من التكرار (نفس الرقم)
            existing = conn.execute("SELECT id FROM numbers WHERE phone=?", (phone,)).fetchone()
            if existing:
                duplicate += 1
                continue
            
            iso, cname, code = detect_country(phone)
            # البحث عن المنصة إذا كانت موجودة بالاسم الأساسي
            existing_platform = conn.execute(
                "SELECT DISTINCT platform FROM numbers WHERE platform LIKE ?",
                (base_platform + "%",)
            ).fetchall()
            
            final_platform = platform
            if existing_platform:
                # استخدم اسم المنصة الموجود (حتى لو فيه Panel)
                final_platform = existing_platform[0]["platform"]
            
            conn.execute("INSERT INTO numbers (platform, country, phone, added_at) VALUES (?, ?, ?, ?)",
                         (final_platform, cname, phone, time.time()))
            added += 1
    conn.commit()
    conn.close()
    return added, duplicate



@bot.callback_query_handler(func=lambda c: c.data.startswith("num_panel:"))
def cb_num_panel(call):
    uid = call.from_user.id
    if not user_is_admin(uid):
        return
    
    s = get_state(uid)
    if s.get("state") != "num_add":
        return
    
    panel_id = int(call.data.split(":")[1])
    platform = s["data"].get("platform", "أخرى")
    phone = s["data"].get("phone", "")
    cname = s["data"].get("cname", "")
    
    # إضافة الرقم
    number_add(platform, cname, phone)
    
    # حفظ ربط الرقم باللوحة (في الداتابيز)
    if panel_id > 0:
        try:
            conn = db()
            conn.execute("UPDATE numbers SET platform=? WHERE phone=?", (platform + " (Panel:" + str(panel_id) + ")", phone))
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    clear_state(uid)
    panel_name = "بدون لوحة"
    if panel_id > 0:
        p = panel_get(panel_id)
        if p:
            panel_name = p["name"]
    
    bot.send_message(call.message.chat.id,
        "✅ تمت الإضافة\n📱 " + platform + "\n🌍 " + cname + "\n☎️ " + phone + "\n📡 اللوحة: " + panel_name)



@bot.callback_query_handler(func=lambda c: c.data == "confirm_upload")
def cb_confirm_upload(call):
    uid = call.from_user.id
    if not user_is_admin(uid): return
    
    s = get_state(uid)
    platform = s["data"].get("platform", "أخرى")
    panel_id = s["data"].get("panel_id", 0)
    text = s["data"].get("file_text", "")
    
    if not text:
        bot.answer_callback_query(call.id, "❌ لا يوجد بيانات")
        return
    
    added, duplicate = process_uploaded_numbers(text, platform)
    
    # ربط باللوحة
    panel_name = "بدون لوحة"
    if panel_id > 0:
        p = panel_get(panel_id)
        if p:
            panel_name = p["name"]
        try:
            conn = db()
            conn.execute("UPDATE numbers SET platform=? WHERE platform=?", (platform + " (Panel:" + str(panel_id) + ")", platform))
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    # إجمالي الأرقام
    conn = db()
    total = conn.execute("SELECT COUNT(*) as c FROM numbers WHERE platform LIKE ?", (platform + "%",)).fetchone()["c"]
    conn.close()
    
    clear_state(uid)
    
    nl = chr(10)
    reply = "✅ <b>تمت إضافة الأرقام بنجاح!</b>" + nl
    reply += "━━━━━━━━━━━━━━━━━━" + nl
    reply += "📱 <b>المنصة:</b> " + platform + nl
    reply += "📡 <b>اللوحة:</b> " + panel_name + nl
    reply += "➕ <b>تم إضافة:</b> " + str(added) + nl
    reply += "🔄 <b>مكرر (تم تجاهله):</b> " + str(duplicate) + nl
    reply += "🌍 <b>عدد الدول:</b> " + str(countries_count) + nl
    reply += "📊 <b>إجمالي أرقام المنصة:</b> " + str(total) + nl
    reply += "━━━━━━━━━━━━━━━━━━"
    
    kb = InlineKeyboardMarkup()
    kb.add(btn("⬅️ رجوع لوحة الأدمن", "admin:home", BTN.DANGER))
    
    try:
        bot.edit_message_text(reply, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, reply, reply_markup=kb, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "cancel_upload")
def cb_cancel_upload(call):
    uid = call.from_user.id
    clear_state(uid)
    bot.answer_callback_query(call.id, "❌ تم الإلغاء")
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda c: c.data == "num:upload")
def cb_num_upload(call):
    if not user_is_admin(call.from_user.id):
        return
    # نجيب المنصات الموجودة حالياً من الداتابيز
    existing_platforms = numbers_platforms()
    
    text = "📥 <b>رفع أرقام</b>\n\n"
    
    if existing_platforms:
        text += "🗂 <b>المنصات الموجودة حالياً:</b>\n"
        for p in existing_platforms:
            cnt = len(numbers_list(platform=p))
            text += f"  • {p} ({cnt} رقم)\n"
        text += "\n"
    
    text += "اختر المنصة التي ستُضاف لها الأرقام (أو أضف منصة جديدة):"
    
    kb = InlineKeyboardMarkup(row_width=2)
    
    # الأزرار: المنصات الموجودة أولاً
    if existing_platforms:
        for p in existing_platforms:
            cnt = len(numbers_list(platform=p))
            kb.add(btn(f"✅ {p} ({cnt})", "num:upload_plat:" + p, BTN.SUCCESS))
    
    # ثم المنصات الثابتة (للإضافة الجديدة)
    kb.add(btn("➕ منصة جديدة", "num:upload_new", BTN.PRIMARY))
    kb.add(btn("⬅️ إلغاء", "admin:numbers", BTN.DANGER))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("num:upload_plat:"))
def cb_num_upload_plat(call):
    if not user_is_admin(call.from_user.id):
        return
    platform = call.data.split(":", 2)[2]
    set_state(call.from_user.id, "num_upload", {"platform": platform, "step": "panel"})
    
    # عرض قائمة اللوحات
    panels = panels_list()
    if not panels:
        # لو مفيش لوحات، نكمل بدون ربط
        set_state(call.from_user.id, "num_upload", {"platform": platform, "step": "file"})
        text = ("📥 <b>" + html.escape(platform) + "</b>\n\n"
                "1) أرسل ملف .txt\n"
                "2) أو الصق الأرقام هنا\n\n"
                "/cancel للإلغاء")
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
        except Exception:
            bot.send_message(call.message.chat.id, text)
        return
    
    kb = InlineKeyboardMarkup(row_width=1)
    for p in panels:
        kb.add(btn("📡 " + p["name"], "num_upload_panel:" + str(p["id"]) + ":" + platform))
    kb.add(btn("🚫 بدون لوحة", "num_upload_panel:0:" + platform))
    
    bot.edit_message_text("📡 اختر اللوحة التي تنتمي إليها هذه الأرقام:", call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("num_upload_panel:"))
def cb_num_upload_panel(call):
    uid = call.from_user.id
    if not user_is_admin(uid):
        return
    parts = call.data.split(":")
    panel_id = int(parts[1])
    platform = parts[2]
    
    set_state(uid, "num_upload", {"platform": platform, "step": "file", "panel_id": panel_id})
    text = ("📥 <b>" + html.escape(platform) + "</b>\n\n"
            "1) أرسل ملف .txt\n"
            "2) أو الصق الأرقام هنا (كل رقم في سطر)\n\n"
            "/cancel للإلغاء")
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    except Exception:
        bot.send_message(call.message.chat.id, text)


@bot.message_handler(content_types=["document"], func=lambda m: get_state(m.from_user.id).get("state") == "num_upload")
def handle_num_upload_file(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        return
    s = get_state(uid)
    platform = s["data"].get("platform", "أخرى")
    panel_id = s["data"].get("panel_id", 0)
    try:
        file_info = bot.get_file(msg.document.file_id)
        content = bot.download_file(file_info.file_path)
        text = content.decode("utf-8", errors="ignore")
        added, duplicate = process_uploaded_numbers(text, platform)
        
        # ربط الأرقام باللوحة
        panel_name = "بدون لوحة"
        if panel_id > 0:
            p = panel_get(panel_id)
            if p:
                panel_name = p["name"]
            try:
                conn = db()
                conn.execute("UPDATE numbers SET platform=? WHERE platform=?", (platform + " (Panel:" + str(panel_id) + ")", platform))
                conn.commit()
                conn.close()
            except Exception:
                pass
        
        clear_state(uid)
        
        # إجمالي الأرقام في المنصة دي
        conn = db()
        total = conn.execute("SELECT COUNT(*) as c FROM numbers WHERE platform LIKE ?", (platform + "%",)).fetchone()["c"]
        conn.close()
        
        nl = chr(10)
        reply = "✅ <b>تمت إضافة الأرقام بنجاح!</b>" + nl
        reply += "━━━━━━━━━━━━━━━━━━" + nl
        reply += "📱 <b>المنصة:</b> " + platform + nl
        reply += "📡 <b>اللوحة:</b> " + panel_name + nl
        reply += "➕ <b>تم إضافة:</b> " + str(added) + nl
        reply += "🔄 <b>مكرر (تم تجاهله):</b> " + str(duplicate) + nl
        reply += "📊 <b>إجمالي أرقام المنصة:</b> " + str(total) + nl
        reply += "━━━━━━━━━━━━━━━━━━"
        
        kb = InlineKeyboardMarkup()
        kb.add(btn("⬅️ رجوع لوحة الأدمن", "admin:home", BTN.DANGER))
        
        bot.send_message(msg.chat.id, reply, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        bot.send_message(msg.chat.id, "❌ خطأ: " + str(e))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "num_upload")
def handle_num_upload_text(msg):
    uid = msg.from_user.id
    if not user_is_admin(uid):
        return
    s = get_state(uid)
    platform = s["data"].get("platform", "أخرى")
    text = (msg.text or "").strip()
    if not text:
        return
    s = get_state(uid)
    panel_id = s["data"].get("panel_id", 0)
    
    added, duplicate = process_uploaded_numbers(text, platform)
    
    panel_name = "بدون لوحة"
    if panel_id > 0:
        p = panel_get(panel_id)
        if p:
            panel_name = p["name"]
        try:
            conn = db()
            conn.execute("UPDATE numbers SET platform=? WHERE platform=?", (platform + " (Panel:" + str(panel_id) + ")", platform))
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    clear_state(uid)
    
    conn = db()
    total = conn.execute("SELECT COUNT(*) as c FROM numbers WHERE platform=?", (platform,)).fetchone()["c"]
    conn.close()
    
    nl = chr(10)
    reply = "✅ <b>تمت إضافة الأرقام بنجاح!</b>" + nl
    reply += "━━━━━━━━━━━━━━━━━━" + nl
    reply += "📱 <b>المنصة:</b> " + platform + nl
    reply += "📡 <b>اللوحة:</b> " + panel_name + nl
    reply += "➕ <b>تم إضافة:</b> " + str(added) + nl
    reply += "🔄 <b>مكرر (تم تجاهله):</b> " + str(duplicate) + nl
    reply += "📊 <b>إجمالي أرقام المنصة:</b> " + str(total) + nl
    reply += "━━━━━━━━━━━━━━━━━━"
    
    bot.send_message(msg.chat.id, reply, parse_mode="HTML")



@bot.callback_query_handler(func=lambda c: c.data.startswith("ap:curl:"))
def cb_ap_curl(call):
    if not user_is_admin(call.from_user.id):
        return
    try:
        pid = int(call.data.split(":")[2])
    except Exception:
        return
    
    p = panel_get(pid)
    if not p:
        return
    
    base = (p.get("url") or "").rstrip("/")
    path = (p.get("api_path") or "/api/v1/numbers/{phone}/otp")
    method = (p.get("api_method") or "GET").upper()
    token = p.get("token") or ""
    
    # نجيب أول رقم من الداتابيز
    test_phone = "+94761312598"
    try:
        nums = numbers_list(limit=1)
        if nums:
            test_phone = nums[0]["phone"]
    except Exception:
        pass
        
    test_url = base + path.replace("{phone}", test_phone)
    
    curl_code = "curl -X " + method + " \"" + test_url + "\""
    if token:
        curl_code += " -H \"X-API-Key: " + token + "\""
    curl_code += " -H \"Accept: application/json\""
    
    # التنسيق الجديد (الصندوق الجميل)
    text = "🔗 <b>API Curl</b>\n\n"
    text += "<pre><code class=\"language-bash\">" + html.escape(curl_code) + "</code></pre>"
    
    kb = InlineKeyboardMarkup()
    kb.add(btn("⬅️ رجوع", "ap:v:" + str(pid), key="btn_back"))
    
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb, parse_mode="HTML")
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass



@bot.callback_query_handler(func=lambda c: c.data == "menu:getnum")
def cb_getnum_menu(call):
    try:
        platforms = numbers_platforms()
        if not platforms:
            bot.answer_callback_query(call.id, "لا توجد منصات مضافة حالياً", show_alert=True)
            return

        pl_style = setting_get("platform_list_style", "")
        valid_styles = ("primary", "success", "danger")
        if pl_style not in valid_styles:
            pl_style = None

        text = "🔓 <b>اختر المنصة</b>"
        kb = InlineKeyboardMarkup(row_width=1)
        
        for p in platforms:
            # قراءة التخصيص الفردي
            custom_icon = setting_get("platform_emoji_" + p, PLATFORM_ICONS.get(p, "📱"))
            custom_label = setting_get("platform_btn_label_" + p, "")
            display_name = custom_label if custom_label else re.sub(r'\s*\(Panel:\d+\)', '', p)
            
            cnt = len(numbers_list(platform=p))
            
            # اللون المخصص للمنصة أولاً
            p_specific_style = setting_get("platform_btn_style_" + p, "")
            final_style = p_specific_style if p_specific_style in valid_styles else pl_style
            
            try:
                if final_style:
                    btn_obj = InlineKeyboardButton(custom_icon + " " + display_name + " (" + str(cnt) + ")", callback_data="selp:" + p, style=final_style)
                else:
                    btn_obj = InlineKeyboardButton(custom_icon + " " + display_name + " (" + str(cnt) + ")", callback_data="selp:" + p)
            except TypeError:
                btn_obj = InlineKeyboardButton(custom_icon + " " + display_name + " (" + str(cnt) + ")", callback_data="selp:" + p)
            kb.add(btn_obj)
        
        kb.add(InlineKeyboardButton("⬅️ القائمة الرئيسية", callback_data="menu:home"))

        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        except Exception as inner_e:
            if "message is not modified" not in str(inner_e):
                raise inner_e
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        err_msg = str(e)
        if "message is not modified" not in err_msg:
            print("========== خطأ زر المنصات ==========")
            print(e)
            print("=====================================")
            bot.answer_callback_query(call.id, "حدث خطأ، راجع Termux", show_alert=True)
        else:
            bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("selp:"))
def cb_sel_platform(call):
    try:
        platform = call.data.split(":", 1)[1]
        countries = numbers_countries(platform)
        
        if not countries:
            bot.answer_callback_query(call.id, "لا توجد دول مضافة لهذه المنصة", show_alert=True)
            return

        display_platform = str(platform)
        try:
            if "(Panel:" in str(platform):
                panel_id_str = str(platform).split("(Panel:")[1].split(")")[0]
                panel_id = int(panel_id_str)
                p = panel_get(panel_id)
                if p:
                    display_platform = str(platform).replace("(Panel:" + panel_id_str + ")", "- " + p["name"])
        except Exception:
            display_platform = str(platform)
        if "(Panel:" in str(display_platform):
            display_platform = str(display_platform).split("(Panel:")[0].strip()
        
        # تطبيق تخصيص إيموجي واسم المنصة في العنوان
        custom_icon = setting_get("platform_emoji_" + platform, "🌍")
        custom_label = setting_get("platform_btn_label_" + platform, display_platform)
        
        text = f"🌍 <b>اختر الدولة لـ {custom_icon} {custom_label}</b>"
        kb = InlineKeyboardMarkup(row_width=1)
        
        co_global_style = setting_get("country_list_style", "")
        valid_styles = ("primary", "success", "danger")
        if co_global_style not in valid_styles:
            co_global_style = None
        
        for co in countries:
            nums = numbers_list(platform=platform, country=co)
            
            # قراءة التخصيص الفردي للدولة
            custom_icon = setting_get("country_emoji_" + str(co).strip(), "🌍")
            custom_label = setting_get("country_btn_label_" + str(co).strip(), str(co))
            
            flag = "🌍"
            if nums:
                f, _, _ = detect_country(nums[0]["phone"])
                flag = f
            flag = setting_get("country_emoji_" + str(co).strip(), flag)
            
            # اللون المخصص للدولة أولاً
            co_specific_style = setting_get("country_btn_style_" + str(co).strip(), "")
            final_style = co_specific_style if co_specific_style in valid_styles else co_global_style
            
            try:
                if final_style:
                    c_btn = InlineKeyboardButton(flag + " " + custom_label + " (" + str(len(nums)) + ")", callback_data="selco:" + str(platform) + ":" + str(co), style=final_style)
                else:
                    c_btn = InlineKeyboardButton(flag + " " + custom_label + " (" + str(len(nums)) + ")", callback_data="selco:" + str(platform) + ":" + str(co))
            except TypeError:
                c_btn = InlineKeyboardButton(flag + " " + custom_label + " (" + str(len(nums)) + ")", callback_data="selco:" + str(platform) + ":" + str(co))
            kb.add(c_btn)
            
        kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="menu:getnum"))

        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=kb)
            
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        print("========== خطأ زرار المنصة ==========")
        print(e)
        print("=====================================")
        bot.answer_callback_query(call.id, "حدث خطأ، راجع Termux", show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data.startswith("sw:"))
def cb_switch_numbers(call):
    try:
        parts = call.data.split(":", 3)
        if len(parts) < 4:
            bot.answer_callback_query(call.id, "خطأ في البيانات", show_alert=True)
            return
        
        p = parts[1]
        co = parts[2]
        pg = int(parts[3] or 0) + 1
        
        # تعديل الرسالة بالصفحة الجديدة
        show_numbers_page(call.message.chat.id, p, co, pg, call.message)
        bot.answer_callback_query(call.id, "🔄 تم التبديل")
    except Exception as e:
        print("========== خطأ زر التبديل ==========")
        print(e)
        print("=====================================")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("pg:"))
def cb_nav_page(call):
    try:
        parts = call.data.split(":", 3)
        if len(parts) < 4:
            return
        
        p = parts[1]
        co = parts[2]
        pg = int(parts[3] or 0)
        
        # تعديل الرسالة بالصفحة المطلوبة
        show_numbers_page(call.message.chat.id, p, co, pg, call.message)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print("========== خطأ زر التنقل ==========")
        print(e)
        print("====================================")
        bot.answer_callback_query(call.id, "حدث خطأ", show_alert=True)



@bot.callback_query_handler(func=lambda c: c.data == "admin:panels")
def cb_admin_panels(call):
    if not user_is_admin(call.from_user.id):
        return
    panels = panels_list()
    text = "📡 <b>اللوحات</b>\n\nإجمالي: " + str(len(panels))
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(btn("➕ إضافة لوحة (خطوات)", "ap:add", key="btn_add_panel"))
    kb.add(btn("⚡ إضافة سريعة (نص)", "admin:quick_add", key="btn_quick_add"))
    kb.add(btn("📚 دليل الإضافة", "admin:quick_guide", key="btn_quick_guide"))
    if panels:
        kb.add(btn(" عرض اللوحات", "ap:list", key="btn_list_panels"))
        kb.add(btn("🔍 فحص الكل", "ap:testall", key="btn_test_all"))
        kb.add(btn("🔄 سحب فوري", "ap:fetchall", key="btn_fetch_all"))
    kb.add(btn("⬅️ رجوع", "admin:home", key="btn_back"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=kb)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass


def send_startup_message():
    """يطبع رسالة تشغيل فخمة في Termux"""
    try:
        # محاولة استخدام الألوان إذا كانت مكتبة colorama مثبتة
        try:
            from colorama import Fore, Style, init
            init(autoreset=True)
            C = Fore.CYAN
            G = Fore.GREEN
            Y = Fore.YELLOW
            W = Fore.WHITE
            R = Fore.RED
            B = Fore.BLUE
        except ImportError:
            C = G = Y = W = R = B = ""

        line = C + "━" * 50
        star = Y + "✨"
        
        print("")
        print(line)
        print(f"{C}  ____        _     _   _             _   ")
        print(f"{C} | __ )  ___ | |_  | | | | ___  _ __ | |_ ")
        print(rf"{C} |  _ \ / _ \| __| | |_| |/ _ \| '_ \| __|")
        print(f"{C} | |_) | (_) | |_  |  _  | (_) | | | | |_ ")
        print(rf"{C} |____/ \___/ \__| |_| |_|\___/|_| |_|\__|")
        print(f"{G}       [ MATRUI_OTP - Advanced System ]")
        print(line)
        print(f"{star} {W}حالة البوت      : {G}متصل ويعمل بنجاح ✅")
        print(f"{star} {W}السحب التلقائي  : {G}نشط في الخلفية 🔄")
        print(f"{star} {W}قاعدة البيانات  : {G}جاهزة ومستقرة 🗄️")
        print(f"{star} {W}حالة الاتصال    : {G}متصل بـ Telegram 🟢")
        print(line)
        print(f"{Y}  🚀 النظام جاهز الآن لاستقبال الأكواد...")
        print(line)
        print("")
    except Exception as e:
        print("[BOT] ⚠️ خطأ في رسالة التشغيل: " + str(e))





# ============================================================
# [DIAGNOSTIC] handler تشخيصي — يطبع أي رسالة في اللوج
# ============================================================



# ============================================================
# [PING] فحص اتصال Telegram API كل 60 ثانية
# ============================================================
def _ping_loop():
    import requests
    while True:
        try:
            r = requests.get(
                "https://api.telegram.org/bot" + BOT_TOKEN + "/getMe",
                timeout=10
            )
            j = r.json()
            if j.get("ok"):
                print("[PING] OK @" + (j.get("result", {}).get("username") or "?"))
            else:
                print("[PING] FAIL " + str(j)[:200])
        except Exception as e:
            print("[PING] EXC " + type(e).__name__ + ": " + str(e)[:150])
        time.sleep(60)






# ============================================================
# 🌐 سيرفر Flask (لـ Render Web Service و UptimeRobot)
# ============================================================
from flask import Flask

web_app = Flask(__name__)

@web_app.route('/')
@web_app.route('/health')
def health_check():
    return "Matari OTP Bot is running!", 200

def _run_web_server():
    port = int(os.environ.get("PORT", 8080))
    print(f"[WEB] ✅ Flask server running on port {port}")
    web_app.run(host="0.0.0.0", port=port, use_reloader=False)

# تشغيل السيرفر في الخلفية (Thread منفصل عشان ما يعطلش البوت)
threading.Thread(target=_run_web_server, daemon=True).start()


def main():
    print("=" * 50)
    print("  المطري OTP - bot.py")
    print("=" * 50)
    db_init()

    # تشغيل poller
    t = threading.Thread(target=poller_loop, daemon=True)
    t.start()
    t2 = threading.Thread(target=channel_reader, daemon=True)
    t2.start()

    print("[BOT] starting...")
    threading.Thread(target=_ping_loop, daemon=True).start()
    print("[BOT] admin id: " + str(MAIN_ADMIN_ID))
    print("")

    try:
        send_startup_message()
    except Exception:
        pass


    # ✅ فحص وحذف أي webhook قديم (وده اللي بيمنع /start من الوصول)
    try:
        info = requests.get("https://api.telegram.org/bot" + BOT_TOKEN + "/getWebhookInfo", timeout=10).json()
        wh = info.get("result", {}).get("url", "")
        if wh:
            print("[BOT] ⚠️ يوجد webhook قديم: " + wh)
            del_r = requests.get("https://api.telegram.org/bot" + BOT_TOKEN + "/deleteWebhook?drop_pending_updates=true", timeout=10).json()
            print("[BOT] ✅ تم حذف الـ webhook: " + str(del_r.get("ok")))
        else:
            print("[BOT] ✅ لا يوجد webhook (polling آمن)")
    except Exception as e:
        print("[BOT] ⚠️ فشل فحص webhook: " + str(e))

    # ✅ Infinity Polling مع معالجة الأخطاء وإعادة المحاولة تلقائياً
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=False)
        except Exception as e:
            print("[POLLING_ERROR] " + str(e)[:200])
            print("[POLLING] إعادة المحاولة بعد 10 ثوانٍ...")
            time.sleep(10)


if __name__ == "__main__":
    main()
