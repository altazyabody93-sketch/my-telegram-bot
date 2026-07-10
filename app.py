import time
import requests
import json
import re
import os
from datetime import datetime, date, timedelta
from pathlib import Path
import sqlite3
import telebot
from telebot import types
import threading
import random
import traceback
import hashlib
import csv
from collections import defaultdict

# ======================
# 🔀 خلط الأرقام لتجنب التكرار
# ======================
def shuffle_numbers(numbers):
    try:
        random.shuffle(numbers)
    except:
        pass
    return numbers

# ======================
# 🔐 إعدادات API الأساسية
# ======================
API_PANELS = [
    {
        "url": "http://147.135.212.197/crapi/time/viewstats",
        "token": "SVdRNEVBYoaAlVdSeU5uQnJ3VGdybFRYaYVhV2d0YIRCZItbQWM="
    },
    {
        "url": "http://147.135.212.197/crapi/time/viewstats",
        "token": "SVdRNEVBYoaAlVdSeU5uQnJ3VGdybFRYaYVhV2d0YIRCZItbQWM="
    }
]

API_URL = API_PANELS[0]["url"]
API_TOKEN = API_PANELS[0]["token"]

# ======================
# 🎨 إعدادات التصميم والألوان
# ======================
EMOJIS = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "star": "⭐",
    "fire": "🔥",
    "rocket": "🚀",
    "crown": "👑",
    "diamond": "💎",
    "heart": "❤️",
    "sparkles": "✨",
    "party": "🎉",
    "trophy": "🏆",
    "medal": "🏅",
    "gem": "💎",
    "zap": "⚡",
    "lock": "🔒",
    "unlock": "🔓",
    "key": "🔑",
    "phone": "📱",
    "message": "💬",
    "bell": "🔔",
    "check": "✔️",
    "cross": "✖️",
    "arrow": "➡️",
    "back": "🔙",
    "next": "⏭️",
    "refresh": "🔄",
    "search": "🔍",
    "settings": "⚙️",
    "user": "👤",
    "users": "👥",
    "chart": "📊",
    "calendar": "📅",
    "clock": "⏰",
    "globe": "🌍",
    "flag": "🚩",
    "mail": "📧",
    "folder": "📁",
    "trash": "🗑️",
    "edit": "✏️",
    "save": "💾",
    "download": "⬇️",
    "upload": "⬆️",
    "link": "🔗",
    "shield": "🛡️",
    "bug": "🐛",
    "gift": "🎁",
    "money": "💰",
    "credit": "💳",
    "ticket": "🎫",
    "crown": "👑",
    "vip": "💎",
    "pro": "🔱",
    "admin": "🛡️",
    "owner": "👑"
}

COLORS = {
    "primary": "🔵",
    "success": "🟢",
    "danger": "🔴",
    "warning": "🟡",
    "info": "🔷",
    "purple": "🟣",
    "orange": "🟠",
    "pink": "🌸"
}

# ======================
# 🔗 إعدادات الروابط والقنوات
# ======================
CHANNEL_1_URL = "https://t.me/f0O00"
CHANNEL_2_URL = "https://t.me/+xvDMfX16pag1ZGVi"
OWNER_1_LINK = "https://t.me/f0O00"
OWNER_2_LINK = "https://t.me/+xvDMfX16pag1ZGVi"

# ======================
# 🤖 إعدادات البوت
# ======================
BOT_TOKEN = "8991286066:AAEIbrmt328hjvSqMeBQL-eDQo2-4fk7Td8"
CHAT_IDS = ["-1003006709377"]
REFRESH_INTERVAL = 2
ADMIN_IDS = [7325566792, 8670424681]
OWNER_ID = 7325566792
DB_PATH = "bot.db"
BACKUP_PATH = "backups/"
LOGS_PATH = "logs/"

# إعدادات النظام
MAX_NUMBERS_PER_USER = 3
NUMBER_EXPIRY_HOURS = 24
DAILY_BONUS_POINTS = 10
REFERRAL_BONUS_POINTS = 50
OTP_RECEIVED_POINTS = 5
VIP_POINTS_REQUIRED = 500

# ======================
# 🗺️ أكواد الدول المحدثة
# ======================
COUNTRY_CODES = {
    "1": ("USA/Canada", "🇺🇸"),
    "7": ("Kazakhstan", "🇰🇿"),
    "20": ("Egypt", "🇪🇬"),
    "27": ("South Africa", "🇿🇦"),
    "30": ("Greece", "🇬🇷"),
    "31": ("Netherlands", "🇳🇱"),
    "32": ("Belgium", "🇧🇪"),
    "33": ("France", "🇫🇷"),
    "34": ("Spain", "🇪🇸"),
    "36": ("Hungary", "🇭🇺"),
    "39": ("Italy", "🇮🇹"),
    "40": ("Romania", "🇷🇴"),
    "41": ("Switzerland", "🇨🇭"),
    "43": ("Austria", "🇦🇹"),
    "44": ("UK", "🇬🇧"),
    "45": ("Denmark", "🇩🇰"),
    "46": ("Sweden", "🇸🇪"),
    "47": ("Norway", "🇳🇴"),
    "48": ("Poland", "🇵🇱"),
    "49": ("Germany", "🇩🇪"),
    "51": ("Peru", "🇵🇪"),
    "52": ("Mexico", "🇲🇽"),
    "53": ("Cuba", "🇨🇺"),
    "54": ("Argentina", "🇦🇷"),
    "55": ("Brazil", "🇧🇷"),
    "56": ("Chile", "🇨🇱"),
    "57": ("Colombia", "🇨🇴"),
    "58": ("Venezuela", "🇻🇪"),
    "60": ("Malaysia", "🇲🇾"),
    "61": ("Australia", "🇦🇺"),
    "62": ("Indonesia", "🇮🇩"),
    "63": ("Philippines", "🇵🇭"),
    "64": ("New Zealand", "🇳🇿"),
    "65": ("Singapore", "🇸🇬"),
    "66": ("Thailand", "🇹🇭"),
    "81": ("Japan", "🇯🇵"),
    "82": ("South Korea", "🇰🇷"),
    "84": ("Vietnam", "🇻🇳"),
    "86": ("China", "🇨🇳"),
    "90": ("Turkey", "🇹🇷"),
    "91": ("India", "🇮🇳"),
    "92": ("Pakistan", "🇵🇰"),
    "93": ("Afghanistan", "🇦🇫"),
    "94": ("Sri Lanka", "🇱🇰"),
    "95": ("Myanmar", "🇲🇲"),
    "98": ("Iran", "🇮🇷"),
    "212": ("Morocco", "🇲🇦"),
    "213": ("Algeria", "🇩🇿"),
    "216": ("Tunisia", "🇹🇳"),
    "218": ("Libya", "🇱🇾"),
    "220": ("Gambia", "🇬🇲"),
    "221": ("Senegal", "🇸🇳"),
    "222": ("Mauritania", "🇲🇷"),
    "223": ("Mali", "🇲🇱"),
    "224": ("Guinea", "🇬🇳"),
    "225": ("Ivory Coast", "🇨🇮"),
    "226": ("Burkina Faso", "🇧🇫"),
    "227": ("Niger", "🇳🇪"),
    "228": ("Togo", "🇹🇬"),
    "229": ("Benin", "🇧🇯"),
    "230": ("Mauritius", "🇲🇺"),
    "231": ("Liberia", "🇱🇷"),
    "232": ("Sierra Leone", "🇸🇱"),
    "233": ("Ghana", "🇬🇭"),
    "234": ("Nigeria", "🇳🇬"),
    "235": ("Chad", "🇹🇩"),
    "236": ("Central African Republic", "🇨🇫"),
    "237": ("Cameroon", "🇨🇲"),
    "238": ("Cape Verde", "🇨🇻"),
    "239": ("Sao Tome", "🇸🇹"),
    "240": ("Equatorial Guinea", "🇬🇶"),
    "241": ("Gabon", "🇬🇦"),
    "242": ("Congo", "🇨🇬"),
    "243": ("DR Congo", "🇨🇩"),
    "244": ("Angola", "🇦🇴"),
    "245": ("Guinea-Bissau", "🇬🇼"),
    "248": ("Seychelles", "🇸🇨"),
    "249": ("Sudan", "🇸🇩"),
    "250": ("Rwanda", "🇷🇼"),
    "251": ("Ethiopia", "🇪🇹"),
    "252": ("Somalia", "🇸🇴"),
    "253": ("Djibouti", "🇩🇯"),
    "254": ("Kenya", "🇰🇪"),
    "255": ("Tanzania", "🇹🇿"),
    "256": ("Uganda", "🇺🇬"),
    "257": ("Burundi", "🇧🇮"),
    "258": ("Mozambique", "🇲🇿"),
    "260": ("Zambia", "🇿🇲"),
    "261": ("Madagascar", "🇲🇬"),
    "262": ("Reunion", "🇷🇪"),
    "263": ("Zimbabwe", "🇿🇼"),
    "264": ("Namibia", "🇳🇦"),
    "265": ("Malawi", "🇲🇼"),
    "266": ("Lesotho", "🇱🇸"),
    "267": ("Botswana", "🇧🇼"),
    "268": ("Eswatini", "🇸🇿"),
    "269": ("Comoros", "🇰🇲"),
    "350": ("Gibraltar", "🇬🇮"),
    "351": ("Portugal", "🇵🇹"),
    "352": ("Luxembourg", "🇱🇺"),
    "353": ("Ireland", "🇮🇪"),
    "354": ("Iceland", "🇮🇸"),
    "355": ("Albania", "🇦🇱"),
    "356": ("Malta", "🇲🇹"),
    "357": ("Cyprus", "🇨🇾"),
    "358": ("Finland", "🇫🇮"),
    "359": ("Bulgaria", "🇧🇬"),
    "370": ("Lithuania", "🇱🇹"),
    "371": ("Latvia", "🇱🇻"),
    "372": ("Estonia", "🇪🇪"),
    "373": ("Moldova", "🇲🇩"),
    "374": ("Armenia", "🇦🇲"),
    "375": ("Belarus", "🇧🇾"),
    "376": ("Andorra", "🇦🇩"),
    "377": ("Monaco", "🇲🇨"),
    "378": ("San Marino", "🇸🇲"),
    "380": ("Ukraine", "🇺🇦"),
    "381": ("Serbia", "🇷🇸"),
    "382": ("Montenegro", "🇲🇪"),
    "383": ("Kosovo", "🇽🇰"),
    "385": ("Croatia", "🇭🇷"),
    "386": ("Slovenia", "🇸🇮"),
    "387": ("Bosnia", "🇧🇦"),
    "389": ("North Macedonia", "🇲🇰"),
    "420": ("Czech Republic", "🇨🇿"),
    "421": ("Slovakia", "🇸🇰"),
    "423": ("Liechtenstein", "🇱🇮"),
    "500": ("Falkland Islands", "🇫🇰"),
    "501": ("Belize", "🇧🇿"),
    "502": ("Guatemala", "🇬🇹"),
    "503": ("El Salvador", "🇸🇻"),
    "504": ("Honduras", "🇭🇳"),
    "505": ("Nicaragua", "🇳🇮"),
    "506": ("Costa Rica", "🇨🇷"),
    "507": ("Panama", "🇵🇦"),
    "509": ("Haiti", "🇭🇹"),
    "591": ("Bolivia", "🇧🇴"),
    "592": ("Guyana", "🇬🇾"),
    "593": ("Ecuador", "🇪🇨"),
    "595": ("Paraguay", "🇵🇾"),
    "597": ("Suriname", "🇸🇷"),
    "598": ("Uruguay", "🇺🇾"),
    "670": ("Timor-Leste", "🇹🇱"),
    "673": ("Brunei", "🇧🇳"),
    "674": ("Nauru", "🇳🇷"),
    "675": ("Papua New Guinea", "🇵🇬"),
    "676": ("Tonga", "🇹🇴"),
    "677": ("Solomon Islands", "🇸🇧"),
    "678": ("Vanuatu", "🇻🇺"),
    "679": ("Fiji", "🇫🇯"),
    "680": ("Palau", "🇵🇼"),
    "685": ("Samoa", "🇼🇸"),
    "686": ("Kiribati", "🇰🇮"),
    "687": ("New Caledonia", "🇳🇨"),
    "688": ("Tuvalu", "🇹🇻"),
    "689": ("French Polynesia", "🇵🇫"),
    "691": ("Micronesia", "🇫🇲"),
    "692": ("Marshall Islands", "🇲🇭"),
    "850": ("North Korea", "🇰🇵"),
    "852": ("Hong Kong", "🇭🇰"),
    "853": ("Macau", "🇲🇴"),
    "855": ("Cambodia", "🇰🇭"),
    "856": ("Laos", "🇱🇦"),
    "960": ("Maldives", "🇲🇻"),
    "961": ("Lebanon", "🇱🇧"),
    "962": ("Jordan", "🇯🇴"),
    "963": ("Syria", "🇸🇾"),
    "964": ("Iraq", "🇮🇶"),
    "965": ("Kuwait", "🇰🇼"),
    "966": ("Saudi Arabia", "🇸🇦"),
    "967": ("Yemen", "🇾🇪"),
    "968": ("Oman", "🇴🇲"),
    "970": ("Palestine", "🇵🇸"),
    "971": ("UAE", "🇦🇪"),
    "972": ("Israel", "🇮🇱"),
    "973": ("Bahrain", "🇧🇭"),
    "974": ("Qatar", "🇶🇦"),
    "975": ("Bhutan", "🇧🇹"),
    "976": ("Mongolia", "🇲🇳"),
    "977": ("Nepal", "🇳🇵"),
    "992": ("Tajikistan", "🇹🇯"),
    "993": ("Turkmenistan", "🇹🇲"),
    "994": ("Azerbaijan", "🇦🇿"),
    "995": ("Georgia", "🇬🇪"),
    "996": ("Kyrgyzstan", "🇰🇬"),
    "998": ("Uzbekistan", "🇺🇿"),
}

# ======================
# 📶 Ranges لكل دولة
# ======================
COUNTRY_RANGES = {
    "20": ["2010","2011","2012","2015"],
}

def number_matches_country_range(country_code, number):
    ranges = COUNTRY_RANGES.get(country_code)
    if not ranges:
        return True
    number = str(number)
    for r in ranges:
        if number.startswith(r):
            return True
    return False

# ======================
# 📦 متغيرات مؤقتة
# ======================
temp_combos = {}
user_states = {}
user_sessions = {}

# ======================
# 🎨 دوال التنسيق الجميل
# ======================
def format_beautiful_header(title, emoji="✨"):
    """تنسيق عنوان جميل"""
    return f"""
╔══════════════════════╗
   {emoji} <b>{title}</b> {emoji}
╚══════════════════════╝
"""

def format_beautiful_box(content, border="═"):
    """تنسيق محتوى في صندوق"""
    lines = content.split('\n')
    max_len = max(len(line) for line in lines)
    
    result = f"╔{border * (max_len + 2)}╗\n"
    for line in lines:
        result += f"║ {line:<{max_len}} ║\n"
    result += f"╚{border * (max_len + 2)}╝"
    return result

def format_progress_bar(current, total, length=10):
    """شريط تقدم جميل"""
    percentage = (current / total) * 100 if total > 0 else 0
    filled = int(length * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (length - filled)
    return f"{bar} {percentage:.1f}%"

def format_stars(count, max_stars=5):
    """تنسيق النجوم"""
    return "⭐" * count + "☆" * (max_stars - count)

def get_level_badge(level):
    """شارة المستوى"""
    badges = {
        1: "🥉 Bronze",
        2: "🥈 Silver", 
        3: "🥇 Gold",
        4: "💎 Diamond",
        5: "👑 Master",
        6: "🔱 Legend",
        7: "⚡ God"
    }
    return badges.get(min(level, 7), "🌟 Newbie")

def calculate_user_level(points):
    """حساب مستوى المستخدم من النقاط"""
    if points < 50:
        return 1
    elif points < 150:
        return 2
    elif points < 300:
        return 3
    elif points < 500:
        return 4
    elif points < 1000:
        return 5
    elif points < 2000:
        return 6
    else:
        return 7

def get_random_welcome():
    """رسالة ترحيب عشوائية"""
    welcomes = [
        "أهلاً بيك يا نجم! 🌟",
        "يا هلا والله! 🎉",
        "نورت البوت يا جميل! ✨",
        "أهلاً وسهلاً! 💫",
        "مرحباً بك يا بطل! 🏆",
        "يا مرحبا! 🌹",
        "أهلاً بيك في عالمنا! 🚀"
    ]
    return random.choice(welcomes)

# ======================
# 🎮 نظام الإنجازات
# ======================
ACHIEVEMENTS = {
    "first_otp": {"name": "أول OTP", "emoji": "🎯", "points": 20, "desc": "استلمت أول كود OTP"},
    "ten_otps": {"name": "10 أكواد", "emoji": "🔟", "points": 50, "desc": "استلمت 10 أكواد OTP"},
    "fifty_otps": {"name": "50 كود", "emoji": "🎖️", "points": 150, "desc": "استلمت 50 كود OTP"},
    "hundred_otps": {"name": "100 كود", "emoji": "💯", "points": 300, "desc": "استلمت 100 كود OTP"},
    "referral_master": {"name": "سيد الإحالة", "emoji": "👥", "points": 200, "desc": "أحلت 10 أصدقاء"},
    "vip_member": {"name": "عضو VIP", "emoji": "💎", "points": 100, "desc": "وصلت لمرحلة VIP"},
    "daily_streak_7": {"name": "7 أيام متتالية", "emoji": "🔥", "points": 100, "desc": "دخلت 7 أيام متتالية"},
    "all_countries": {"name": "مستكشف العالم", "emoji": "🌍", "points": 250, "desc": "جربت كل الدول"},
}

class AchievementSystem:
    """نظام الإنجازات"""
    
    @staticmethod
    def check_achievements(user_id):
        """فحص الإنجازات الجديدة"""
        user = get_user(user_id)
        if not user:
            return []
        
        new_achievements = []
        user_achievements = get_user_achievements(user_id)
        
        # فحص إنجاز أول OTP
        if "first_otp" not in user_achievements:
            otp_count = get_user_otp_count(user_id)
            if otp_count >= 1:
                new_achievements.append("first_otp")
        
        # فحص إنجاز 10 أكواد
        if "ten_otps" not in user_achievements:
            otp_count = get_user_otp_count(user_id)
            if otp_count >= 10:
                new_achievements.append("ten_otps")
        
        # فحص إنجاز 50 كود
        if "fifty_otps" not in user_achievements:
            otp_count = get_user_otp_count(user_id)
            if otp_count >= 50:
                new_achievements.append("fifty_otps")
        
        # فحص إنجاز 100 كود
        if "hundred_otps" not in user_achievements:
            otp_count = get_user_otp_count(user_id)
            if otp_count >= 100:
                new_achievements.append("hundred_otps")
        
        # إضافة النقاط للإنجازات الجديدة
        for ach_id in new_achievements:
            ach = ACHIEVEMENTS[ach_id]
            add_points(user_id, ach["points"])
            save_achievement(user_id, ach_id)
        
        return new_achievements

# ======================
# 🗄️ دوال قاعدة البيانات المحدثة
# ======================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # جدول المستخدمين المحدث
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            country_code TEXT,
            assigned_number TEXT,
            is_banned INTEGER DEFAULT 0,
            private_combo_country TEXT DEFAULT NULL,
            points INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            join_date TEXT,
            last_active TEXT,
            language TEXT DEFAULT 'ar',
            is_vip INTEGER DEFAULT 0,
            referral_code TEXT,
            referred_by INTEGER,
            total_otps INTEGER DEFAULT 0,
            daily_streak INTEGER DEFAULT 0,
            last_daily TEXT,
            achievements TEXT DEFAULT '[]',
            notifications_enabled INTEGER DEFAULT 1,
            rating_count INTEGER DEFAULT 0,
            rating_sum INTEGER DEFAULT 0
        )
    ''')
    
    # جدول الكومبوهات
    c.execute('''
        CREATE TABLE IF NOT EXISTS combos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT,
            custom_name TEXT,
            numbers TEXT
        )
    ''')
    
    # جدول سجلات OTP
    c.execute('''
        CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dt TEXT,
            num TEXT,
            cli TEXT,
            message TEXT,
            otp TEXT,
            country TEXT,
            service TEXT,
            sent_to_user INTEGER,
            sent_to_group INTEGER,
            timestamp TEXT
        )
    ''')
    
    # جدول الإعدادات
    c.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # جدول الأدمنز
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            role TEXT DEFAULT 'admin',
            added_by INTEGER,
            added_date TEXT,
            permissions TEXT DEFAULT '[]'
        )
    ''')
    
    # جدول سجل الأدمن
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            action TEXT,
            details TEXT,
            timestamp TEXT
        )
    ''')
    
    # جدول التذاكر
    c.execute('''
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject TEXT,
            message TEXT,
            status TEXT DEFAULT 'open',
            admin_response TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # جدول الإحالات
    c.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER,
            referral_date TEXT,
            bonus_given INTEGER DEFAULT 0
        )
    ''')
    
    # جدول النسخ الاحتياطية
    c.execute('''
        CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            size INTEGER,
            created_at TEXT,
            created_by INTEGER
        )
    ''')
    
    # جدول الرسائل المجدولة
    c.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            target_type TEXT,
            target_id TEXT,
            scheduled_time TEXT,
            sent INTEGER DEFAULT 0,
            created_by INTEGER
        )
    ''')
    
    # جدول الكلمات المحظورة
    c.execute('''
        CREATE TABLE IF NOT EXISTS blocked_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT,
            added_by INTEGER,
            added_at TEXT
        )
    ''')
    
    # جدول التقييمات
    c.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            rating INTEGER,
            comment TEXT,
            created_at TEXT
        )
    ''')
    
    # جدول المكافآت اليومية
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            reward_date TEXT,
            points_earned INTEGER,
            reward_type TEXT
        )
    ''')
    
    # جدول الأرقام المفضلة
    c.execute('''
        CREATE TABLE IF NOT EXISTS favorite_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            number TEXT,
            added_at TEXT
        )
    ''')
    
    # جدول الاقتراحات
    c.execute('''
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            suggestion TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    ''')
    
    # جدول الإعلانات
    c.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            created_by INTEGER,
            created_at TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    settings = [
        ('channel_1', CHANNEL_1_URL),
        ('channel_2', CHANNEL_2_URL),
        ('owner_1', OWNER_1_LINK),
        ('owner_2', OWNER_2_LINK),
        ('force_sub', 'on'),
        ('maintenance_mode', 'off'),
        ('welcome_message', 'أهلاً بيك في بوت OTP! 🎉'),
        ('daily_bonus', str(DAILY_BONUS_POINTS)),
        ('referral_bonus', str(REFERRAL_BONUS_POINTS))
    ]
    
    for key, value in settings:
        c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))

    try:
        c.execute("ALTER TABLE combos ADD COLUMN custom_name TEXT")
    except:
        pass

    # إضافة الأعمدة الجديدة لجدول المستخدمين
    new_columns = [
        ("points", "INTEGER DEFAULT 0"),
        ("level", "INTEGER DEFAULT 1"),
        ("join_date", "TEXT"),
        ("last_active", "TEXT"),
        ("language", "TEXT DEFAULT 'ar'"),
        ("is_vip", "INTEGER DEFAULT 0"),
        ("referral_code", "TEXT"),
        ("referred_by", "INTEGER"),
        ("total_otps", "INTEGER DEFAULT 0"),
        ("daily_streak", "INTEGER DEFAULT 0"),
        ("last_daily", "TEXT"),
        ("achievements", "TEXT DEFAULT '[]'"),
        ("notifications_enabled", "INTEGER DEFAULT 1"),
        ("rating_count", "INTEGER DEFAULT 0"),
        ("rating_sum", "INTEGER DEFAULT 0")
    ]
    
    for col_name, col_type in new_columns:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        except:
            pass

    conn.commit()
    conn.close()

init_db()

# إنشاء مجلدات النسخ الاحتياطي والسجلات
os.makedirs(BACKUP_PATH, exist_ok=True)
os.makedirs(LOGS_PATH, exist_ok=True)

# ======================
# 🗄️ دوال قاعدة البيانات الإضافية
# ======================
def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM bot_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_user(user_id, username="", first_name="", last_name="", country_code=None, assigned_number=None, private_combo_country=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    existing_data = get_user(user_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if existing_data:
        if country_code is None:
            country_code = existing_data[4]
        if assigned_number is None:
            assigned_number = existing_data[5]
        if private_combo_country is None:
            private_combo_country = existing_data[7]
        
        # تحديث آخر نشاط
        c.execute("UPDATE users SET last_active=? WHERE user_id=?", (now, user_id))
    else:
        # مستخدم جديد
        referral_code = generate_referral_code(user_id)
        c.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, country_code, assigned_number, 
                             is_banned, private_combo_country, points, level, join_date, last_active,
                             referral_code, total_otps, daily_streak, achievements)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, 0, 1, ?, ?, ?, 0, 0, '[]')
        """, (user_id, username, first_name, last_name, country_code, assigned_number,
              private_combo_country, now, now, referral_code))
    
    conn.commit()
    conn.close()

def generate_referral_code(user_id):
    """توليد كود إحالة فريد"""
    return f"REF{user_id}{random.randint(100, 999)}"

def add_points(user_id, points):
    """إضافة نقاط للمستخدم"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, user_id))
    
    # تحديث المستوى
    c.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        new_level = calculate_user_level(row[0])
        c.execute("UPDATE users SET level = ? WHERE user_id = ?", (new_level, user_id))
    
    conn.commit()
    conn.close()

def get_user_points(user_id):
    """جلب نقاط المستخدم"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def get_user_otp_count(user_id):
    """عدد OTP التي استلمها المستخدم"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM otp_logs WHERE num IN (SELECT assigned_number FROM users WHERE user_id=?)", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def get_user_achievements(user_id):
    """جلب إنجازات المستخدم"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT achievements FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except:
            return []
    return []

def save_achievement(user_id, achievement_id):
    """حفظ إنجاز جديد"""
    achievements = get_user_achievements(user_id)
    if achievement_id not in achievements:
        achievements.append(achievement_id)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE users SET achievements = ? WHERE user_id = ?", 
                 (json.dumps(achievements), user_id))
        conn.commit()
        conn.close()

def claim_daily_reward(user_id):
    """المطالبة بالمكافأة اليومية"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT last_daily, daily_streak FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return False, 0, 0
    
    last_daily = row[0]
    streak = row[1] or 0
    
    today = datetime.now().date()
    
    if last_daily:
        last_date = datetime.strptime(last_daily, "%Y-%m-%d %H:%M:%S").date()
        if last_date == today:
            conn.close()
            return False, streak, 0
        
        # حساب السلسلة
        if (today - last_date).days == 1:
            streak += 1
        else:
            streak = 1
    else:
        streak = 1
    
    # حساب النقاط (تزيد مع السلسلة)
    points = DAILY_BONUS_POINTS + (streak * 2)
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE users SET last_daily = ?, daily_streak = ?, points = points + ? WHERE user_id = ?",
             (now, streak, points, user_id))
    
    # حفظ في سجل المكافآت
    c.execute("INSERT INTO daily_rewards (user_id, reward_date, points_earned, reward_type) VALUES (?, ?, ?, ?)",
             (user_id, now, points, f"daily_streak_{streak}"))
    
    conn.commit()
    conn.close()
    
    return True, streak, points

def add_referral(referrer_id, referred_id):
    """إضافة إحالة جديدة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # التحقق من عدم وجود الإحالة مسبقاً
    c.execute("SELECT id FROM referrals WHERE referred_id = ?", (referred_id,))
    if c.fetchone():
        conn.close()
        return False
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO referrals (referrer_id, referred_id, referral_date, bonus_given) VALUES (?, ?, ?, 0)",
             (referrer_id, referred_id, now))
    
    # منح المكافأة
    c.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (REFERRAL_BONUS_POINTS, referrer_id))
    c.execute("UPDATE referrals SET bonus_given = 1 WHERE referred_id = ?", (referred_id,))
    
    conn.commit()
    conn.close()
    return True

def get_referral_count(user_id):
    """عدد الإحالات"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def create_support_ticket(user_id, subject, message):
    """إنشاء تذكرة دعم"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO support_tickets (user_id, subject, message, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
             (user_id, subject, message, now, now))
    ticket_id = c.lastrowid
    conn.commit()
    conn.close()
    return ticket_id

def get_user_tickets(user_id):
    """جلب تذاكر المستخدم"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM support_tickets WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    tickets = c.fetchall()
    conn.close()
    return tickets

def add_admin_log(admin_id, action, details):
    """إضافة سجل للأدمن"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO admin_logs (admin_id, action, details, timestamp) VALUES (?, ?, ?, ?)",
             (admin_id, action, details, now))
    conn.commit()
    conn.close()

def get_combo_name(country_code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT custom_name FROM combos WHERE country_code=?", (country_code,))
        row = c.fetchone()
    except:
        row = None
    conn.close()

    if row and row[0]:
        return row[0]

    if country_code in COUNTRY_CODES:
        return COUNTRY_CODES[country_code][0]

    return "Unknown"

def get_all_combos():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT country_code FROM combos")
    combos = [row[0] for row in c.fetchall()]
    conn.close()
    return combos

def assign_number_to_user(user_id, number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=? WHERE user_id=?", (number, user_id))
    conn.commit()
    conn.close()

def get_user_by_number(number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE assigned_number=?", (number,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def release_number(old_number):
    if not old_number:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (old_number,))
    conn.commit()
    conn.close()

def get_combo(country_code, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT numbers FROM combos WHERE country_code=?", (country_code,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

def save_combo(country_code, numbers, custom_name=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if not custom_name and country_code in COUNTRY_CODES:
        custom_name = COUNTRY_CODES[country_code][0]

    c.execute("SELECT COUNT(*) FROM combos WHERE country_code=?", (country_code,))
    count = c.fetchone()[0] + 1

    new_name = f"{custom_name} {count}"

    c.execute(
        "INSERT INTO combos (country_code, custom_name, numbers) VALUES (?, ?, ?)",
        (country_code, new_name, json.dumps(numbers))
    )

    conn.commit()
    conn.close()

def delete_combo(country_code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM combos WHERE country_code=?", (country_code,))
    conn.commit()
    conn.close()

def get_available_numbers(country_code, user_id=None):
    all_numbers = get_combo(country_code, user_id)

    filtered = []
    for n in all_numbers:
        if number_matches_country_range(country_code, n):
            filtered.append(n)

    if not filtered:
        return []

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT assigned_number FROM users WHERE assigned_number IS NOT NULL AND assigned_number != ''")
    used_numbers = set(row[0] for row in c.fetchall())
    conn.close()

    available = [num for num in filtered if num not in used_numbers]
    return available

def log_otp_to_db(dt, num, cli, message, otp, country, service, sent_to_user=0, sent_to_group=0):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO otp_logs (dt, num, cli, message, otp, country, service, sent_to_user, sent_to_group, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (dt, num, cli, message, otp, country, service, sent_to_user, sent_to_group, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    # تحديث عدد OTP للمستخدم
    user_id = get_user_by_number(num)
    if user_id:
        c.execute("UPDATE users SET total_otps = total_otps + 1 WHERE user_id = ?", (user_id,))
        add_points(user_id, OTP_RECEIVED_POINTS)
    
    conn.commit()
    conn.close()

def is_otp_already_sent(message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM otp_logs WHERE message=? LIMIT 1", (message,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def ban_user(user_id, reason="", duration=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    add_admin_log(0, "ban_user", f"Banned user {user_id}: {reason}")

def unban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    add_admin_log(0, "unban_user", f"Unbanned user {user_id}")

def get_otp_logs(limit=50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM otp_logs ORDER BY id DESC LIMIT ?", (limit,))
    logs = c.fetchall()
    conn.close()
    return logs

def get_user_otp_logs(user_id, limit=50):
    """سجل OTP للمستخدم"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT * FROM otp_logs 
        WHERE num IN (SELECT assigned_number FROM users WHERE user_id=?)
        ORDER BY id DESC LIMIT ?
    """, (user_id, limit))
    logs = c.fetchall()
    conn.close()
    return logs

def search_otp_logs(query, limit=50):
    """البحث في سجلات OTP"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT * FROM otp_logs 
        WHERE message LIKE ? OR num LIKE ? OR otp LIKE ? OR service LIKE ?
        ORDER BY id DESC LIMIT ?
    """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit))
    logs = c.fetchall()
    conn.close()
    return logs

def add_rating(user_id, rating, comment=""):
    """إضافة تقييم"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO ratings (user_id, rating, comment, created_at) VALUES (?, ?, ?, ?)",
             (user_id, rating, comment, now))
    c.execute("UPDATE users SET rating_count = rating_count + 1, rating_sum = rating_sum + ? WHERE user_id = ?",
             (rating, user_id))
    conn.commit()
    conn.close()

def get_average_rating():
    """متوسط التقييمات"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT AVG(rating) FROM ratings")
    row = c.fetchone()
    conn.close()
    return round(row[0], 1) if row and row[0] else 0

def add_favorite_number(user_id, number):
    """إضافة رقم للمفضلة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO favorite_numbers (user_id, number, added_at) VALUES (?, ?, ?)",
             (user_id, number, now))
    conn.commit()
    conn.close()

def get_favorite_numbers(user_id):
    """جلب الأرقام المفضلة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT number FROM favorite_numbers WHERE user_id = ?", (user_id,))
    numbers = [row[0] for row in c.fetchall()]
    conn.close()
    return numbers

def add_suggestion(user_id, suggestion):
    """إضافة اقتراح"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO suggestions (user_id, suggestion, created_at) VALUES (?, ?, ?)",
             (user_id, suggestion, now))
    conn.commit()
    conn.close()

def create_backup(created_by):
    """إنشاء نسخة احتياطية"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.db"
    filepath = os.path.join(BACKUP_PATH, filename)
    
    try:
        import shutil
        shutil.copy2(DB_PATH, filepath)
        
        size = os.path.getsize(filepath)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO backups (filename, size, created_at, created_by) VALUES (?, ?, ?, ?)",
                 (filename, size, now, created_by))
        conn.commit()
        conn.close()
        
        return True, filename, size
    except Exception as e:
        return False, str(e), 0

def get_backups():
    """جلب النسخ الاحتياطية"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM backups ORDER BY created_at DESC")
    backups = c.fetchall()
    conn.close()
    return backups

def restore_backup(filename):
    """استعادة نسخة احتياطية"""
    import shutil
    filepath = os.path.join(BACKUP_PATH, filename)
    if os.path.exists(filepath):
        shutil.copy2(filepath, DB_PATH)
        return True
    return False

def add_blocked_word(word, added_by):
    """إضافة كلمة محظورة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO blocked_words (word, added_by, added_at) VALUES (?, ?, ?)",
             (word, added_by, now))
    conn.commit()
    conn.close()

def get_blocked_words():
    """جلب الكلمات المحظورة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT word FROM blocked_words")
    words = [row[0] for row in c.fetchall()]
    conn.close()
    return words

def contains_blocked_word(text):
    """فحص إذا كان النص يحتوي كلمة محظورة"""
    blocked = get_blocked_words()
    text_lower = text.lower()
    for word in blocked:
        if word.lower() in text_lower:
            return True
    return False

def schedule_message(message, target_type, target_id, scheduled_time, created_by):
    """جدولة رسالة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO scheduled_messages 
                (message, target_type, target_id, scheduled_time, created_by) 
                VALUES (?, ?, ?, ?, ?)""",
             (message, target_type, target_id, scheduled_time, created_by))
    conn.commit()
    conn.close()

def get_pending_scheduled_messages():
    """جلب الرسائل المجدولة المعلقة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("SELECT * FROM scheduled_messages WHERE scheduled_time <= ? AND sent = 0", (now,))
    messages = c.fetchall()
    conn.close()
    return messages

def mark_message_sent(message_id):
    """تحديد الرسالة كمرسلة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE scheduled_messages SET sent = 1 WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()

def delete_account(user_id):
    """حذف حساب المستخدم"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM favorite_numbers WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM daily_rewards WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM referrals WHERE referred_id = ? OR referrer_id = ?", (user_id, user_id))
    c.execute("DELETE FROM support_tickets WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_advanced_stats():
    """إحصائيات متقدمة"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    stats = {}
    
    # إجمالي المستخدمين
    c.execute("SELECT COUNT(*) FROM users")
    stats['total_users'] = c.fetchone()[0]
    
    # المستخدمين النشطين
    c.execute("SELECT COUNT(*) FROM users WHERE is_banned = 0")
    stats['active_users'] = c.fetchone()[0]
    
    # المستخدمين المحظورين
    c.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
    stats['banned_users'] = c.fetchone()[0]
    
    # VIP
    c.execute("SELECT COUNT(*) FROM users WHERE is_vip = 1")
    stats['vip_users'] = c.fetchone()[0]
    
    # إجمالي OTP
    c.execute("SELECT COUNT(*) FROM otp_logs")
    stats['total_otps'] = c.fetchone()[0]
    
    # OTP اليوم
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM otp_logs WHERE timestamp LIKE ?", (f"{today}%",))
    stats['today_otps'] = c.fetchone()[0]
    
    # الإحالات
    c.execute("SELECT COUNT(*) FROM referrals")
    stats['total_referrals'] = c.fetchone()[0]
    
    # التذاكر المفتوحة
    c.execute("SELECT COUNT(*) FROM support_tickets WHERE status = 'open'")
    stats['open_tickets'] = c.fetchone()[0]
    
    # متوسط التقييم
    c.execute("SELECT AVG(rating) FROM ratings")
    row = c.fetchone()
    stats['avg_rating'] = round(row[0], 1) if row and row[0] else 0
    
    # أكثر الدول
    c.execute("""
        SELECT country, COUNT(*) as cnt 
        FROM otp_logs 
        GROUP BY country 
        ORDER BY cnt DESC 
        LIMIT 5
    """)
    stats['top_countries'] = c.fetchall()
    
    # أكثر الخدمات
    c.execute("""
        SELECT service, COUNT(*) as cnt 
        FROM otp_logs 
        GROUP BY service 
        ORDER BY cnt DESC 
        LIMIT 5
    """)
    stats['top_services'] = c.fetchall()
    
    conn.close()
    return stats

# ======================
# 🤖 إنشاء بوت Telegram
# ======================
bot = telebot.TeleBot(BOT_TOKEN)

# ======================
# 🔒 الاشتراك الإجباري
# ======================
FORCE_SUB_CHANNELS = []

OTP_GROUP_LINK = "https://t.me/Numbers_Al_Bahrawi"

def is_force_sub_enabled():
    val = get_setting("force_sub")
    return val != "off"

def check_user_joined(user_id):
    try:
        for ch in FORCE_SUB_CHANNELS:
            username = ch.split("/")[-1]
            member = bot.get_chat_member(f"@{username}", user_id)
            if member.status not in ["member","administrator","creator"]:
                return False
        return True
    except:
        return False

def send_force_sub(message):
    markup = types.InlineKeyboardMarkup()
    for i, ch in enumerate(FORCE_SUB_CHANNELS, 1):
        markup.add(types.InlineKeyboardButton(
            f"📢 القناة {i}", 
            url=ch
        ))
    markup.add(types.InlineKeyboardButton(
        "✅ تأكيد الاشتراك", 
        callback_data="check_sub"
    ))
    
    bot.send_message(
        message.chat.id,
        f"""
{EMOJIS['lock']} <b>الاشتراك مطلوب!</b> {EMOJIS['lock']}

╔══════════════════════╗
║  🌟 مرحباً بك في بوتنا  ║
║  للاشتراك في القنوات  ║
║  اضغط على الأزرار     ║
╚══════════════════════╝

{EMOJIS['arrow']} اشترك في جميع القنوات ثم اضغط تأكيد
""",
        reply_markup=markup,
        parse_mode="HTML"
    )

# ======================
# 🎯 دوال المساعدة
# ======================
def is_admin(user_id):
    return user_id in ADMIN_IDS or user_id == OWNER_ID

def is_owner(user_id):
    return user_id == OWNER_ID

def is_banned(user_id):
    user = get_user(user_id)
    return user and user[6] == 1

def extract_otp_from_message(message):
    if not message:
        return "N/A"
    
    patterns = [
        r'(?:code|رمز|كود|verification|تحقق|otp|pin)[:\s\-]*[‎]?(\d{3,8})',
        r'(\d{3,4})[\s\-]?(\d{3,4})',
        r'\b(\d{4,6})\b',
        r'(\d{3})-(\d{3})',
        r'whatsapp.*?(\d{3,6})',
    ]
    
    message_clean = message.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, message_clean, re.IGNORECASE)
        if matches:
            if isinstance(matches[0], tuple):
                combined = ''.join(str(x) for x in matches[0])
                return combined.zfill(6)
            return str(matches[0]).zfill(6)
    
    numbers = re.findall(r'\b\d{4,6}\b', message)
    return numbers[0] if numbers else "N/A"

def detect_service_from_cli(cli, message):
    cli_lower = (cli or "").lower()
    msg_lower = message.lower()
    
    services = {
        "whatsapp": ["whatsapp", "واتساب"],
        "facebook": ["facebook", "فيسبوك", "fb"],
        "instagram": ["instagram", "انستقرام"],
        "telegram": ["telegram", "تيليجرام"],
        "google": ["google", "جوجل"],
        "twitter": ["twitter", "تويتر"],
        "tiktok": ["tiktok", "تيك توك"],
        "snapchat": ["snapchat", "سناب"],
        "amazon": ["amazon", "امازون"],
        "paypal": ["paypal", "باي بال"],
        "microsoft": ["microsoft", "مايكروسوفت"],
        "apple": ["apple", "ابل"],
        "netflix": ["netflix", "نتفليكس"],
        "spotify": ["spotify", "سبوتيفاي"],
        "discord": ["discord", "ديسكورد"],
        "uber": ["uber", "اوبر"],
    }
    
    for service, keywords in services.items():
        for keyword in keywords:
            if keyword in cli_lower or keyword in msg_lower:
                return service.upper()
    
    return cli.upper() if cli else "GENERAL"

def get_country_from_number(num):
    if not num:
        return "Unknown", "🌍"
    
    clean_num = re.sub(r'\D', '', str(num))
    
    for code, (name, flag) in COUNTRY_CODES.items():
        if clean_num.startswith(code):
            return name, flag
    
    return "Unknown", "🌍"

def html_escape(text):
    if not text:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))

def mask_number(number):
    if not number or number == "N/A":
        return "N/A"
    
    number = str(number).strip()
    if len(number) > 8:
        return number[:7] + "••" + number[-4:]
    return number

# ======================
# 📨 دوال الإرسال - نسخة BODY.py المحدثة
# ======================
def format_otp_message_new(msg_data):
    """تنسيق الرسالة بنفس شكل BODY.py"""
    dt = msg_data.get('dt', 'N/A')
    num = msg_data.get('num', 'N/A')
    cli = msg_data.get('cli', 'N/A')
    message = msg_data.get('message', 'N/A')
    
    otp = extract_otp_from_message(message)
    service = detect_service_from_cli(cli, message)
    country_name, country_flag = get_country_from_number(num)
    
    try:
        dt_obj = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        formatted_time = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
    except:
        formatted_time = dt
    
    masked_num = mask_number(num)
    
    if otp != "N/A":
        otp_display = otp
    else:
        otp_display = "N/A"
    
    message_html = f"""<blockquote>{country_flag} <b>{country_name} {service} RECEIVED!</b> ✨</blockquote>
<blockquote>⏰ <b>Time:</b> {formatted_time}</blockquote>
<blockquote>🌍 <b>Country:</b> {country_name} {country_flag}</blockquote>
<blockquote>⚙️ <b>Service:</b> {service}</blockquote>
<blockquote>📞 <b>Number:</b> {masked_num}</blockquote>
<blockquote>🔑 <b>OTP:</b> {otp_display}</blockquote>
<blockquote>📩 <b>Full Message:</b>
{html_escape(message)}</blockquote>"""
    
    return message_html, otp, country_name, service

def send_to_telegram_group_new(text):
    """إرسال للجروب بنفس شكل BODY.py"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "Owner ~", 
                    "url": "t.me/X_HX1",
                },
                {
                    "text": "Channel", 
                    "url": get_setting('channel_1'),
                }
            ],
            [
                {
                    "text": "Owner 2", 
                    "url": "t.me/X_XVW",
                },
                {
                    "text": "Channel 2", 
                    "url": get_setting('channel_2'),
                }
            ]
        ]
    }
    
    success = 0
    for chat_id in CHAT_IDS:
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(keyboard)
            }
            resp = requests.post(url, data=payload, timeout=10)
            if resp.status_code == 200:
                success += 1
        except Exception as e:
            print(f"[!] خطأ Telegram لـ {chat_id}: {e}")
    
    return success > 0

def process_and_send_message_new(msg_data):
    """معالجة الرسائل بالشكل الجديد"""
    try:
        formatted_msg, otp, country, service = format_otp_message_new(msg_data)
        
        if is_otp_already_sent(msg_data.get('message', '')):
            print(f"[API] ⏭️  تم تخطي رسالة مكررة")
            return False
        
        group_sent = send_to_telegram_group_new(formatted_msg)
        
        num = msg_data.get('num', '')
        user_id = get_user_by_number(num)
        user_sent = 0
        
        if user_id:
            try:
                # فحص الإنجازات
                new_achievements = AchievementSystem.check_achievements(user_id)
                
                user_msg = f"""
{EMOJIS['bell']} <b>وصلك كود جديد!</b> {EMOJIS['sparkles']}

╔══════════════════════╗
║  📱 من: <b>{service}</b>
║  🔑 الكود: <code>{otp}</code>
║  📞 الرقم: <code>{num}</code>
║  🌍 الدولة: {country}
╚══════════════════════╝

{EMOJIS['star']} <i>+{OTP_RECEIVED_POINTS} نقاط</i>
"""
                
                # إضافة رسائل الإنجازات
                if new_achievements:
                    for ach_id in new_achievements:
                        ach = ACHIEVEMENTS[ach_id]
                        user_msg += f"\n{ach['emoji']} <b>إنجاز جديد!</b> {ach['name']}\n{ach['desc']}\n+{ach['points']} نقاط"
                
                markup = types.InlineKeyboardMarkup()
                markup.row(
                    types.InlineKeyboardButton("Owner ~", url="t.me/X_HX1"),
                    types.InlineKeyboardButton("Channel", url=get_setting('channel_1'))
                )
                
                bot.send_message(
                    user_id, 
                    user_msg,
                    reply_markup=markup, 
                    parse_mode="HTML"
                )
                user_sent = 1
            except Exception as e:
                print(f"[!] فشل إرسال OTP للمستخدم {user_id}: {e}")
        
        log_otp_to_db(
            dt=msg_data.get('dt'),
            num=num,
            cli=msg_data.get('cli', ''),
            message=msg_data.get('message', ''),
            otp=otp,
            country=country,
            service=service,
            sent_to_user=user_sent,
            sent_to_group=1 if group_sent else 0
        )
        
        print(f"[API] ✅ تم إرسال: {country} | {otp} | {service}")
        return True
        
    except Exception as e:
        print(f"[API] ❌ خطأ: {e}")
        traceback.print_exc()
        return False

# ======================
# 🎮 أوامر البوت
# ======================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_force_sub_enabled() and not check_user_joined(message.from_user.id):
        send_force_sub(message)
        return

    if is_banned(message.from_user.id):
        bot.reply_to(message, f"""
{EMOJIS['error']} <b>حسابك محظور!</b>

╔══════════════════════╗
║  🚫 لا يمكنك استخدام  ║
║  هذا البوت حالياً      ║
╚══════════════════════╝

{EMOJIS['info']} للتواصل مع الدعم: @{OWNER_1_LINK.split('/')[-1]}
""", parse_mode="HTML")
        return
    
    # التحقق من الإحالة
    referral_code = None
    if len(message.text.split()) > 1:
        referral_code = message.text.split()[1]
    
    is_new = not get_user(message.from_user.id)
    
    if is_new:
        for admin in ADMIN_IDS:
            try:
                caption = f"""
{EMOJIS['party']} <b>مستخدم جديد!</b> {EMOJIS['party']}

🆔 <code>{message.from_user.id}</code>
👤 @{message.from_user.username or 'None'}
📛 {message.from_user.first_name or ''} {message.from_user.last_name or ''}
"""
                bot.send_message(admin, caption, parse_mode="HTML")
            except:
                pass
    
    save_user(
        message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or ""
    )
    
    # معالجة الإحالة
    if referral_code and is_new:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE referral_code = ?", (referral_code,))
        row = c.fetchone()
        conn.close()
        
        if row:
            referrer_id = row[0]
            if referrer_id != message.from_user.id:
                if add_referral(referrer_id, message.from_user.id):
                    try:
                        bot.send_message(referrer_id, f"""
{EMOJIS['gift']} <b>مبروك! مكافأة إحالة!</b> {EMOJIS['gift']}

👥 أحلت صديق جديد
💰 حصلت على +{REFERRAL_BONUS_POINTS} نقطة
""", parse_mode="HTML")
                    except:
                        pass
    
    countries = get_all_combos()
    
    welcome_text = f"""
{get_random_welcome()}

{EMOJIS['crown']} <b>بوت OTP الاحترافي</b> {EMOJIS['crown']}

╔══════════════════════╗
║  🌟 أفضل بوت لأرقام   ║
║  OTP المؤقتة          ║
╚══════════════════════╝

{EMOJIS['sparkles']} <b>المميزات:</b>
{EMOJIS['check']} أرقام من أكثر من 150 دولة
{EMOJIS['check']} استقبال فوري للأكواد
{EMOJIS['check']} نظام نقاط ومستويات
{EMOJIS['check']} إنجازات ومكافآت
{EMOJIS['check']} دعم فني 24/7

{EMOJIS['arrow']} اختر دولتك من الأزرار بالأسفل
"""
    
    if not countries:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "➕ إضافة كومبو (أدمن)", 
            callback_data="admin_add_combo"
        ))
        bot.send_message(
            message.chat.id,
            f"""
{EMOJIS['warning']} <b>لا توجد دول متاحة!</b>

يرجى التواصل مع المشرفين
""",
            reply_markup=markup,
            parse_mode="HTML"
        )
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for code in countries:
        if code in COUNTRY_CODES:
            name = get_combo_name(code)
            flag = COUNTRY_CODES.get(code,("","🌍"))[1]
            available = len(get_available_numbers(code))
            button_text = f"{flag} {name} ({available})"
            markup.insert(types.InlineKeyboardButton(
                button_text, 
                callback_data=f"country_{code}"
            ))
    
    # أزرار إضافية
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['user']} بروفايلي", callback_data="my_profile"),
        types.InlineKeyboardButton(f"{EMOJIS['gift']} المكافأة اليومية", callback_data="daily_reward")
    )
    
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['users']} الإحالات", callback_data="my_referrals"),
        types.InlineKeyboardButton(f"{EMOJIS['trophy']} إنجازاتي", callback_data="my_achievements")
    )
    
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['ticket']} الدعم الفني", callback_data="support_menu"),
        types.InlineKeyboardButton(f"{EMOJIS['settings']} الإعدادات", callback_data="user_settings")
    )
    
    if is_admin(message.from_user.id):
        markup.add(types.InlineKeyboardButton(
            f"{EMOJIS['admin']} لوحة الأدمن", 
            callback_data="admin_panel"
        ))
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=markup,
        parse_mode="HTML"
    )

# ======================
# 👤 أوامر المستخدم الجديدة
# ======================

@bot.callback_query_handler(func=lambda call: call.data == "my_profile")
def show_my_profile(call):
    """عرض بروفايل المستخدم"""
    user = get_user(call.from_user.id)
    if not user:
        bot.answer_callback_query(call.id, "❌ المستخدم غير موجود!", show_alert=True)
        return
    
    user_id = call.from_user.id
    username = call.from_user.username or "N/A"
    name = f"{call.from_user.first_name or ''} {call.from_user.last_name or ''}".strip() or "N/A"
    
    points = user[8] if len(user) > 8 else 0
    level = user[9] if len(user) > 9 else 1
    join_date = user[10] if len(user) > 10 else "N/A"
    total_otps = user[16] if len(user) > 16 else 0
    daily_streak = user[17] if len(user) > 17 else 0
    is_vip = user[13] if len(user) > 13 else 0
    
    level_badge = get_level_badge(level)
    vip_badge = "💎 VIP" if is_vip else "👤 عادي"
    
    # حساب النقاط للمستوى التالي
    level_thresholds = [0, 50, 150, 300, 500, 1000, 2000, 999999]
    next_level_points = level_thresholds[min(level, 7)]
    progress = format_progress_bar(points, next_level_points)
    
    profile_text = f"""
{EMOJIS['crown']} <b>بروفايلك الشخصي</b> {EMOJIS['crown']}

╔══════════════════════╗
║  👤 <b>الاسم:</b> {name}
║  🆔 <b>ID:</b> <code>{user_id}</code>
║  📛 <b>Username:</b> @{username}
║  📅 <b>تاريخ الانضمام:</b>
║     {join_date}
╠══════════════════════╣
║  🏆 <b>المستوى:</b> {level_badge}
║  💰 <b>النقاط:</b> {points}
║  📊 <b>التقدم:</b>
║     {progress}
╠══════════════════════╣
║  🔑 <b>إجمالي OTP:</b> {total_otps}
║  🔥 <b>سلسلة يومية:</b> {daily_streak} يوم
║  🎖️ <b>الرتبة:</b> {vip_badge}
╚══════════════════════╝

{EMOJIS['star']} استمر في النشاط لتكسب المزيد!
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="back_to_main")
    )
    
    try:
        bot.edit_message_text(
            profile_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, profile_text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "daily_reward")
def claim_daily(call):
    """المطالبة بالمكافأة اليومية"""
    success, streak, points = claim_daily_reward(call.from_user.id)
    
    if success:
        text = f"""
{EMOJIS['gift']} <b>مبروك! المكافأة اليومية</b> {EMOJIS['gift']}

╔══════════════════════╗
║  💰 حصلت على: <b>{points}</b> نقطة
║  🔥 سلسلة يومية: <b>{streak}</b> يوم
╚══════════════════════╝

{EMOJIS['star']} عد غداً لمكافأة أكبر!
"""
    else:
        text = f"""
{EMOJIS['clock']} <b>عدت مبكراً!</b>

╔══════════════════════╗
║  ⏰你已经领取了今天的   ║
║  المكافأة، عد غداً!    ║
╚══════════════════════╝

🔥 سلسلتك الحالية: {streak} يوم
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="back_to_main"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "my_referrals")
def show_referrals(call):
    """عرض الإحالات"""
    user_id = call.from_user.id
    user = get_user(user_id)
    
    referral_code = user[14] if user and len(user) > 14 else generate_referral_code(user_id)
    if not referral_code:
        referral_code = generate_referral_code(user_id)
    
    referral_count = get_referral_count(user_id)
    total_earnings = referral_count * REFERRAL_BONUS_POINTS
    
    text = f"""
{EMOJIS['users']} <b>نظام الإحالات</b> {EMOJIS['users']}

╔══════════════════════╗
║  🎫 كود إحالتك:
║  <code>{referral_code}</code>
╠══════════════════════╣
║  👥 عدد الإحالات: <b>{referral_count}</b>
║  💰 إجمالي الأرباح: <b>{total_earnings}</b>
║  🎁 مكافأة كل إحالة: <b>{REFERRAL_BONUS_POINTS}</b>
╚══════════════════════╝

{EMOJIS['info']} <b>كيف تعمل الإحالة؟</b>
1️⃣ شارك كودك مع أصدقائك
2️⃣ عندما يسجل صديقك باستخدام كودك
3️⃣ تحصل على {REFERRAL_BONUS_POINTS} نقطة تلقائياً!

{EMOJIS['arrow']} رابط الإحالة:
<code>https://t.me/{bot.get_me().username}?start={referral_code}</code>
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="back_to_main")
    )
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "my_achievements")
def show_achievements(call):
    """عرض الإنجازات"""
    user_id = call.from_user.id
    user_achievements = get_user_achievements(user_id)
    
    text = f"""
{EMOJIS['trophy']} <b>إنجازاتك</b> {EMOJIS['trophy']}

"""
    
    for ach_id, ach in ACHIEVEMENTS.items():
        if ach_id in user_achievements:
            text += f"{ach['emoji']} <b>{ach['name']}</b> ✅\n   {ach['desc']}\n   +{ach['points']} نقطة\n\n"
        else:
            text += f"🔒 <b>{ach['name']}</b> ❌\n   {ach['desc']}\n\n"
    
    text += f"\n{EMOJIS['star']} أنجزت {len(user_achievements)} من {len(ACHIEVEMENTS)} إنجاز"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="back_to_main"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "my_otp_history")
def show_otp_history(call):
    """عرض سجل OTP"""
    user_id = call.from_user.id
    logs = get_user_otp_logs(user_id, limit=10)
    
    if not logs:
        text = f"""
{EMOJIS['info']} <b>لا يوجد سجل بعد!</b>

لم تستلم أي أكواد OTP حتى الآن.
"""
    else:
        text = f"""
{EMOJIS['message']} <b>آخر 10 أكواد OTP</b> {EMOJIS['message']}

"""
        for log in logs:
            dt = log[1]
            num = log[2]
            otp = log[5]
            service = log[7]
            text += f"🔑 <code>{otp}</code> | {service}\n📞 <code>{num}</code>\n⏰ {dt}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="back_to_main"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "user_settings")
def show_user_settings(call):
    """إعدادات المستخدم"""
    text = f"""
{EMOJIS['settings']} <b>الإعدادات</b> {EMOJIS['settings']}

╔══════════════════════╗
║  اختر ما تريد تعديله  ║
╚══════════════════════╝
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['bell']} الإشعارات", callback_data="toggle_notifications"),
        types.InlineKeyboardButton(f"{EMOJIS['globe']} اللغة", callback_data="change_language")
    )
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['search']} بحث في OTP", callback_data="search_otp"),
        types.InlineKeyboardButton(f"{EMOJIS['star']} تقييم البوت", callback_data="rate_bot")
    )
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['trash']} حذف الحساب", callback_data="delete_account_confirm")
    )
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="back_to_main"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "toggle_notifications")
def toggle_notifications(call):
    """تبديل الإشعارات"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT notifications_enabled FROM users WHERE user_id = ?", (call.from_user.id,))
    row = c.fetchone()
    current = row[0] if row else 1
    new_value = 0 if current else 1
    c.execute("UPDATE users SET notifications_enabled = ? WHERE user_id = ?", (new_value, call.from_user.id))
    conn.commit()
    conn.close()
    
    status = "مفعلة ✅" if new_value else "معطلة ❌"
    bot.answer_callback_query(call.id, f"الإشعارات: {status}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "rate_bot")
def rate_bot_start(call):
    """تقييم البوت"""
    text = f"""
{EMOJIS['star']} <b>قيّم البوت!</b> {EMOJIS['star']}

كم تقييمك للبوت؟
"""
    
    markup = types.InlineKeyboardMarkup(row_width=5)
    for i in range(1, 6):
        markup.insert(types.InlineKeyboardButton(
            "⭐" * i,
            callback_data=f"rate_{i}"
        ))
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="user_settings"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("rate_"))
def save_rating(call):
    """حفظ التقييم"""
    rating = int(call.data.split("_")[1])
    user_states[call.from_user.id] = f"rating_comment_{rating}"
    
    text = f"""
{EMOJIS['star']} <b>شكراً لتقييمك!</b> {EMOJIS['star']}

تقييمك: {"⭐" * rating}

{EMOJIS['message']} اكتب تعليقك (اختياري):
أو اضغط /skip لتخطي التعليق
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⏭️ تخطي", callback_data="skip_rating"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: str(user_states.get(m.from_user.id, "")).startswith("rating_comment_"))
def save_rating_comment(message):
    """حفظ تعليق التقييم"""
    state = user_states[message.from_user.id]
    rating = int(state.split("_")[2])
    comment = message.text
    
    add_rating(message.from_user.id, rating, comment)
    add_points(message.from_user.id, 10)
    
    bot.reply_to(message, f"""
{EMOJIS['party']} <b>شكراً لتقييمك!</b> {EMOJIS['party']}

تقييمك: {"⭐" * rating}
💰 حصلت على +10 نقاط
""", parse_mode="HTML")
    
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "skip_rating")
def skip_rating(call):
    """تخطي التعليق"""
    state = user_states.get(call.from_user.id, "")
    if state.startswith("rating_comment_"):
        rating = int(state.split("_")[2])
        add_rating(call.from_user.id, rating, "")
        add_points(call.from_user.id, 10)
        
        bot.edit_message_text(
            f"""
{EMOJIS['party']} <b>شكراً!</b> {EMOJIS['party']}

💰 حصلت على +10 نقاط
""",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        
        del user_states[call.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "search_otp")
def search_otp_start(call):
    """البحث في OTP"""
    user_states[call.from_user.id] = "searching_otp"
    
    text = f"""
{EMOJIS['search']} <b>البحث في سجل OTP</b> {EMOJIS['search']}

اكتب كلمة البحث:
- رقم الهاتف
- كود OTP
- اسم الخدمة
- أي نص في الرسالة
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="user_settings"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "searching_otp")
def perform_search(message):
    """تنفيذ البحث"""
    query = message.text
    results = search_otp_logs(query, limit=10)
    
    if not results:
        text = f"""
{EMOJIS['search']} <b>لا توجد نتائج!</b>

لم يتم العثور على نتائج لـ: <code>{query}</code>
"""
    else:
        text = f"""
{EMOJIS['search']} <b>نتائج البحث ({len(results)})</b> {EMOJIS['search']}

"""
        for log in results:
            dt = log[1]
            num = log[2]
            otp = log[5]
            service = log[7]
            text += f"🔑 <code>{otp}</code> | {service}\n📞 <code>{num}</code>\n⏰ {dt}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="user_settings"))
    
    bot.reply_to(message, text, reply_markup=markup, parse_mode="HTML")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "delete_account_confirm")
def delete_account_confirm(call):
    """تأكيد حذف الحساب"""
    text = f"""
{EMOJIS['warning']} <b>تحذير!</b> {EMOJIS['warning']}

╔══════════════════════╗
║  ⚠️ هل أنت متأكد من   ║
║  حذف حسابك نهائياً؟    ║
║                        ║
║  سيتم حذف:            ║
║  - جميع بياناتك       ║
║  - نقاطك وإنجازاتك    ║
║  - سجل OTP            ║
║  - إحالاتك            ║
╚══════════════════════╝

{EMOJIS['error']} هذا الإجراء لا يمكن التراجع عنه!
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['error']} نعم، احذف", callback_data="delete_account_yes"),
        types.InlineKeyboardButton(f"{EMOJIS['check']} لا، إلغاء", callback_data="user_settings")
    )
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "delete_account_yes")
def delete_account_yes(call):
    """حذف الحساب فعلياً"""
    delete_account(call.from_user.id)
    
    bot.edit_message_text(
        f"""
{EMOJIS['info']} <b>تم حذف الحساب</b>

تم حذف حسابك بنجاح.
نشكرك على استخدامك للبوت! {EMOJIS['heart']}
""",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "support_menu")
def support_menu(call):
    """قائمة الدعم الفني"""
    text = f"""
{EMOJIS['ticket']} <b>الدعم الفني</b> {EMOJIS['ticket']}

╔══════════════════════╗
║  🆘 كيف يمكننا        ║
║  مساعدتك؟             ║
╚══════════════════════╝
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['message']} تذكرة جديدة", callback_data="new_ticket"),
        types.InlineKeyboardButton(f"{EMOJIS['folder']} تذاكري", callback_data="my_tickets")
    )
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['mail']} اقتراح", callback_data="new_suggestion")
    )
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="back_to_main"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "new_ticket")
def new_ticket(call):
    """إنشاء تذكرة جديدة"""
    user_states[call.from_user.id] = "ticket_subject"
    
    text = f"""
{EMOJIS['message']} <b>تذكرة جديدة</b> {EMOJIS['message']}

اكتب عنوان التذكرة:
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} إلغاء", callback_data="support_menu"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "ticket_subject")
def ticket_subject(message):
    """عنوان التذكرة"""
    user_states[message.from_user.id] = f"ticket_msg_{message.text}"
    
    bot.reply_to(message, f"""
{EMOJIS['message']} اكتب تفاصيل المشكلة:
""")

@bot.message_handler(func=lambda m: str(user_states.get(m.from_user.id, "")).startswith("ticket_msg_"))
def ticket_message(message):
    """رسالة التذكرة"""
    state = user_states[message.from_user.id]
    subject = state.split("_", 2)[2]
    msg = message.text
    
    ticket_id = create_support_ticket(message.from_user.id, subject, msg)
    
    bot.reply_to(message, f"""
{EMOJIS['check']} <b>تم إنشاء التذكرة!</b> {EMOJIS['check']}

🎫 رقم التذكرة: <code>#{ticket_id}</code>
📝 العنوان: {subject}

سيتم الرد عليك قريباً {EMOJIS['clock']}
""", parse_mode="HTML")
    
    # إرسال للأدمن
    for admin in ADMIN_IDS:
        try:
            bot.send_message(admin, f"""
{EMOJIS['ticket']} <b>تذكرة جديدة!</b>

🎫 رقم: #{ticket_id}
👤 المستخدم: @{message.from_user.username or message.from_user.id}
📝 العنوان: {subject}
💬 الرسالة: {msg}
""", parse_mode="HTML")
        except:
            pass
    
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "my_tickets")
def my_tickets(call):
    """تذاكري"""
    tickets = get_user_tickets(call.from_user.id)
    
    if not tickets:
        text = f"""
{EMOJIS['info']} <b>لا توجد تذاكر!</b>

لم تقم بإنشاء أي تذاكر بعد.
"""
    else:
        text = f"""
{EMOJIS['folder']} <b>تذاكرك ({len(tickets)})</b> {EMOJIS['folder']}

"""
        for t in tickets:
            status_emoji = {"open": "🔴", "in_progress": "🟡", "closed": "🟢"}.get(t[4], "⚪")
            text += f"{status_emoji} <b>#{t[0]}</b> | {t[2]}\n⏰ {t[6]}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="support_menu"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "new_suggestion")
def new_suggestion(call):
    """اقتراح جديد"""
    user_states[call.from_user.id] = "suggestion_text"
    
    text = f"""
{EMOJIS['mail']} <b>اقتراح جديد</b> {EMOJIS['mail']}

اكتب اقتراحك لتحسين البوت:
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} إلغاء", callback_data="support_menu"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "suggestion_text")
def save_suggestion(message):
    """حفظ الاقتراح"""
    add_suggestion(message.from_user.id, message.text)
    add_points(message.from_user.id, 15)
    
    bot.reply_to(message, f"""
{EMOJIS['check']} <b>شكراً لاقتراحك!</b> {EMOJIS['check']}

💰 حصلت على +15 نقطة
سيتم مراجعة اقتراحك قريباً {EMOJIS['clock']}
""", parse_mode="HTML")
    
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    """الرجوع للقائمة الرئيسية"""
    countries = get_all_combos()
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for code in countries:
        if code in COUNTRY_CODES:
            name = get_combo_name(code)
            flag = COUNTRY_CODES.get(code,("","🌍"))[1]
            available = len(get_available_numbers(code))
            markup.insert(types.InlineKeyboardButton(
                f"{flag} {name} ({available})", 
                callback_data=f"country_{code}"
            ))
    
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['user']} بروفايلي", callback_data="my_profile"),
        types.InlineKeyboardButton(f"{EMOJIS['gift']} المكافأة اليومية", callback_data="daily_reward")
    )
    
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['users']} الإحالات", callback_data="my_referrals"),
        types.InlineKeyboardButton(f"{EMOJIS['trophy']} إنجازاتي", callback_data="my_achievements")
    )
    
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['ticket']} الدعم الفني", callback_data="support_menu"),
        types.InlineKeyboardButton(f"{EMOJIS['settings']} الإعدادات", callback_data="user_settings")
    )
    
    if is_admin(call.from_user.id):
        markup.add(types.InlineKeyboardButton(
            f"{EMOJIS['admin']} لوحة الأدمن", 
            callback_data="admin_panel"
        ))
    
    bot.edit_message_text(
        f"""
{get_random_welcome()}

{EMOJIS['crown']} <b>اختر دولتك:</b> {EMOJIS['crown']}
""",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="HTML"
    )

# ======================
# 🔐 لوحة التحكم الإدارية المحدثة
# ======================
def admin_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # المجموعة الأولى: إدارة الكومبوهات
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['upload']} إضافة كومبو", callback_data="admin_add_combo"),
        types.InlineKeyboardButton(f"{EMOJIS['trash']} حذف كومبو", callback_data="admin_del_combo")
    )
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['edit']} تعديل رينج", callback_data="admin_rename_range"),
        types.InlineKeyboardButton(f"{EMOJIS['refresh']} دمج كومبوهات", callback_data="admin_merge_combos")
    )
    
    # المجموعة الثانية: الإحصائيات
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['chart']} إحصائيات", callback_data="admin_stats"),
        types.InlineKeyboardButton(f"{EMOJIS['chart']} إحصائيات متقدمة", callback_data="admin_advanced_stats")
    )
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['folder']} تقرير كامل", callback_data="admin_full_report"),
        types.InlineKeyboardButton(f"{EMOJIS['download']} تصدير البيانات", callback_data="admin_export_data")
    )
    
    # المجموعة الثالثة: إدارة المستخدمين
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['error']} حظر", callback_data="admin_ban"),
        types.InlineKeyboardButton(f"{EMOJIS['check']} فك حظر", callback_data="admin_unban")
    )
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['user']} معلومات مستخدم", callback_data="admin_user_info"),
        types.InlineKeyboardButton(f"{EMOJIS['users']} كل المستخدمين", callback_data="admin_all_users")
    )
    
    # المجموعة الرابعة: الرسائل
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['mail']} إرسال للجميع", callback_data="admin_broadcast_all"),
        types.InlineKeyboardButton(f"{EMOJIS['message']} إرسال لمستخدم", callback_data="admin_broadcast_user")
    )
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['clock']} جدولة رسالة", callback_data="admin_schedule_msg"),
        types.InlineKeyboardButton(f"{EMOJIS['mail']} إعلان", callback_data="admin_announcement")
    )
    
    # المجموعة الخامسة: الإعدادات
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['lock']} الاشتراك الإجباري", callback_data="toggle_force_sub"),
        types.InlineKeyboardButton(f"{EMOJIS['shield']} كلمات محظورة", callback_data="admin_blocked_words")
    )
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['save']} نسخ احتياطي", callback_data="admin_backup"),
        types.InlineKeyboardButton(f"{EMOJIS['refresh']} استعادة", callback_data="admin_restore")
    )
    
    # المجموعة السادسة: الأدمنز
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['admin']} إضافة أدمن", callback_data="admin_add_admin"),
        types.InlineKeyboardButton(f"{EMOJIS['admin']} حذف أدمن", callback_data="admin_remove_admin")
    )
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['folder']} سجل الأدمن", callback_data="admin_logs"),
        types.InlineKeyboardButton(f"{EMOJIS['ticket']} التذاكر", callback_data="admin_tickets")
    )
    
    # المجموعة السابعة: أدوات إضافية
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['trash']} تنظيف DB", callback_data="admin_cleanup"),
        types.InlineKeyboardButton(f"{EMOJIS['search']} فحص أرقام", callback_data="admin_check_numbers")
    )
    
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel(call):
    if not is_admin(call.from_user.id):
        return
    
    text = f"""
{EMOJIS['admin']} <b>لوحة التحكم الإدارية</b> {EMOJIS['admin']}

╔══════════════════════╗
║  👑 مرحباً بك يا مدير  ║
║  اختر من القائمة      ║
╚══════════════════════╝
"""
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=admin_main_menu(),
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=admin_main_menu(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_advanced_stats")
def admin_advanced_stats(call):
    """إحصائيات متقدمة"""
    if not is_admin(call.from_user.id):
        return
    
    stats = get_advanced_stats()
    
    text = f"""
{EMOJIS['chart']} <b>الإحصائيات المتقدمة</b> {EMOJIS['chart']}

╔══════════════════════╗
║  👥 <b>المستخدمون:</b>
║  📊 الإجمالي: {stats['total_users']}
║  ✅ النشطون: {stats['active_users']}
║  🚫 المحظورون: {stats['banned_users']}
║  💎 VIP: {stats['vip_users']}
╠══════════════════════╣
║  🔑 <b>أكواد OTP:</b>
║  📊 الإجمالي: {stats['total_otps']}
║  📅 اليوم: {stats['today_otps']}
╠══════════════════════╣
║  📈 <b>أخرى:</b>
║  👥 الإحالات: {stats['total_referrals']}
║  🎫 تذاكر مفتوحة: {stats['open_tickets']}
║  ⭐ متوسط التقييم: {stats['avg_rating']}
╚══════════════════════╝
"""
    
    if stats['top_countries']:
        text += f"\n{EMOJIS['globe']} <b>أكثر الدول:</b>\n"
        for country, count in stats['top_countries']:
            text += f"  {country}: {count}\n"
    
    if stats['top_services']:
        text += f"\n{EMOJIS['zap']} <b>أكثر الخدمات:</b>\n"
        for service, count in stats['top_services']:
            text += f"  {service}: {count}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_backup")
def admin_backup(call):
    """إنشاء نسخة احتياطية"""
    if not is_admin(call.from_user.id):
        return
    
    success, filename, size = create_backup(call.from_user.id)
    
    if success:
        text = f"""
{EMOJIS['check']} <b>تم إنشاء نسخة احتياطية!</b> {EMOJIS['check']}

📁 الملف: <code>{filename}</code>
💾 الحجم: {size / 1024:.2f} KB
⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    else:
        text = f"""
{EMOJIS['error']} <b>فشل إنشاء النسخة!</b>

{filename}
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_restore")
def admin_restore(call):
    """استعادة نسخة احتياطية"""
    if not is_admin(call.from_user.id):
        return
    
    backups = get_backups()
    
    if not backups:
        text = f"""
{EMOJIS['info']} <b>لا توجد نسخ احتياطية!</b>
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    else:
        text = f"""
{EMOJIS['folder']} <b>النسخ الاحتياطية ({len(backups)})</b> {EMOJIS['folder']}

اختر نسخة للاستعادة:
"""
        markup = types.InlineKeyboardMarkup()
        for backup in backups[:10]:
            markup.add(types.InlineKeyboardButton(
                f"📁 {backup[1]} ({backup[2]/1024:.1f}KB)",
                callback_data=f"restore_{backup[1]}"
            ))
        markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("restore_"))
def confirm_restore(call):
    """تأكيد الاستعادة"""
    if not is_admin(call.from_user.id):
        return
    
    filename = call.data.split("_", 1)[1]
    user_states[call.from_user.id] = f"confirm_restore_{filename}"
    
    text = f"""
{EMOJIS['warning']} <b>تحذير!</b> {EMOJIS['warning']}

هل أنت متأكد من استعادة النسخة:
📁 <code>{filename}</code>

{EMOJIS['error']} سيتم استبدال البيانات الحالية!
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['check']} نعم", callback_data=f"do_restore_{filename}"),
        types.InlineKeyboardButton(f"{EMOJIS['cross']} لا", callback_data="admin_panel")
    )
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("do_restore_"))
def do_restore(call):
    """تنفيذ الاستعادة"""
    if not is_admin(call.from_user.id):
        return
    
    filename = call.data.split("_", 2)[2]
    
    if restore_backup(filename):
        text = f"""
{EMOJIS['check']} <b>تمت الاستعادة بنجاح!</b> {EMOJIS['check']}

⚠️ يجب إعادة تشغيل البوت الآن
"""
    else:
        text = f"""
{EMOJIS['error']} <b>فشلت الاستعادة!</b>
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_blocked_words")
def admin_blocked_words(call):
    """الكلمات المحظورة"""
    if not is_admin(call.from_user.id):
        return
    
    words = get_blocked_words()
    
    text = f"""
{EMOJIS['shield']} <b>الكلمات المحظورة ({len(words)})</b> {EMOJIS['shield']}

"""
    
    if words:
        for word in words[:20]:
            text += f"❌ <code>{word}</code>\n"
    else:
        text += "لا توجد كلمات محظورة حالياً"
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['upload']} إضافة", callback_data="admin_add_blocked"),
        types.InlineKeyboardButton(f"{EMOJIS['trash']} حذف الكل", callback_data="admin_clear_blocked")
    )
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_blocked")
def admin_add_blocked(call):
    """إضافة كلمة محظورة"""
    if not is_admin(call.from_user.id):
        return
    
    user_states[call.from_user.id] = "add_blocked_word"
    
    text = f"""
{EMOJIS['shield']} <b>إضافة كلمة محظورة</b>

اكتب الكلمة:
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} إلغاء", callback_data="admin_blocked_words"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "add_blocked_word")
def save_blocked_word(message):
    """حفظ الكلمة المحظورة"""
    if not is_admin(message.from_user.id):
        return
    
    word = message.text.strip()
    add_blocked_word(word, message.from_user.id)
    
    bot.reply_to(message, f"""
{EMOJIS['check']} <b>تمت الإضافة!</b>

❌ الكلمة: <code>{word}</code>
""", parse_mode="HTML")
    
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_clear_blocked")
def admin_clear_blocked(call):
    """حذف كل الكلمات المحظورة"""
    if not is_admin(call.from_user.id):
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM blocked_words")
    conn.commit()
    conn.close()
    
    bot.answer_callback_query(call.id, "✅ تم حذف كل الكلمات!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_merge_combos")
def admin_merge_combos(call):
    """دمج كومبوهات"""
    if not is_admin(call.from_user.id):
        return
    
    combos = get_all_combos()
    
    text = f"""
{EMOJIS['refresh']} <b>دمج الكومبوهات</b> {EMOJIS['refresh']}

اختر الدولة الأولى:
"""
    
    markup = types.InlineKeyboardMarkup()
    for code in combos:
        name = get_combo_name(code)
        markup.add(types.InlineKeyboardButton(
            name,
            callback_data=f"merge1_{code}"
        ))
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("merge1_"))
def merge_step1(call):
    """الخطوة الأولى من الدمج"""
    if not is_admin(call.from_user.id):
        return
    
    code1 = call.data.split("_")[1]
    user_states[call.from_user.id] = f"merge2_{code1}"
    
    combos = get_all_combos()
    
    text = f"""
{EMOJIS['refresh']} <b>اختر الدولة الثانية:</b>
"""
    
    markup = types.InlineKeyboardMarkup()
    for code in combos:
        if code != code1:
            name = get_combo_name(code)
            markup.add(types.InlineKeyboardButton(
                name,
                callback_data=f"merge3_{code}"
            ))
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} إلغاء", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("merge3_"))
def merge_execute(call):
    """تنفيذ الدمج"""
    if not is_admin(call.from_user.id):
        return
    
    state = user_states.get(call.from_user.id, "")
    if not state.startswith("merge2_"):
        return
    
    code1 = state.split("_")[1]
    code2 = call.data.split("_")[1]
    
    # جلب الأرقام
    numbers1 = get_combo(code1)
    numbers2 = get_combo(code2)
    
    # دمج وإزالة التكرار
    merged = list(set(numbers1 + numbers2))
    
    # حفظ في الكومبو الأول
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE combos SET numbers = ? WHERE country_code = ?", (json.dumps(merged), code1))
    c.execute("DELETE FROM combos WHERE country_code = ?", (code2,))
    conn.commit()
    conn.close()
    
    text = f"""
{EMOJIS['check']} <b>تم الدمج بنجاح!</b> {EMOJIS['check']}

📊 الإحصائيات:
• الكومبو 1: {len(numbers1)} رقم
• الكومبو 2: {len(numbers2)} رقم
• بعد الدمج: {len(merged)} رقم
• تم إزالة: {len(numbers1) + len(numbers2) - len(merged)} مكرر
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    
    if call.from_user.id in user_states:
        del user_states[call.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_all_users")
def admin_all_users(call):
    """كل المستخدمين"""
    if not is_admin(call.from_user.id):
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, points, level, is_vip FROM users ORDER BY points DESC LIMIT 50")
    users = c.fetchall()
    conn.close()
    
    text = f"""
{EMOJIS['users']} <b>أفضل 50 مستخدم</b> {EMOJIS['users']}

"""
    
    for i, u in enumerate(users, 1):
        vip = "💎" if u[5] else "👤"
        text += f"{i}. {vip} @{u[1] or 'N/A'} | {u[3]} نقطة | L{u[4]}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_schedule_msg")
def admin_schedule_msg(call):
    """جدولة رسالة"""
    if not is_admin(call.from_user.id):
        return
    
    user_states[call.from_user.id] = "schedule_msg_text"
    
    text = f"""
{EMOJIS['clock']} <b>جدولة رسالة</b> {EMOJIS['clock']}

اكتب الرسالة أولاً:
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} إلغاء", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "schedule_msg_text")
def schedule_msg_text(message):
    """نص الرسالة المجدولة"""
    if not is_admin(message.from_user.id):
        return
    
    user_states[message.from_user.id] = f"schedule_time_{message.text}"
    
    bot.reply_to(message, f"""
{EMOJIS['clock']} <b>حدد الوقت:</b>

اكتب الوقت بصيغة: YYYY-MM-DD HH:MM
مثال: 2026-06-27 15:30
""", parse_mode="HTML")

@bot.message_handler(func=lambda m: str(user_states.get(m.from_user.id, "")).startswith("schedule_time_"))
def schedule_msg_time(message):
    """وقت الرسالة المجدولة"""
    if not is_admin(message.from_user.id):
        return
    
    state = user_states[message.from_user.id]
    msg_text = state.split("_", 2)[2]
    scheduled_time = message.text
    
    try:
        datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M")
        schedule_message(msg_text, "all", "all", scheduled_time, message.from_user.id)
        
        bot.reply_to(message, f"""
{EMOJIS['check']} <b>تمت الجدولة!</b> {EMOJIS['check']}

📝 الرسالة: {msg_text[:50]}...
⏰ الوقت: {scheduled_time}
""", parse_mode="HTML")
        
        del user_states[message.from_user.id]
    except:
        bot.reply_to(message, f"""
{EMOJIS['error']} <b>صيغة الوقت خاطئة!</b>

استخدم: YYYY-MM-DD HH:MM
""", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_announcement")
def admin_announcement(call):
    """إعلان جديد"""
    if not is_admin(call.from_user.id):
        return
    
    user_states[call.from_user.id] = "announcement_title"
    
    text = f"""
{EMOJIS['mail']} <b>إعلان جديد</b> {EMOJIS['mail']}

اكتب عنوان الإعلان:
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} إلغاء", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_logs")
def admin_logs(call):
    """سجل الأدمن"""
    if not is_admin(call.from_user.id):
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM admin_logs ORDER BY id DESC LIMIT 30")
    logs = c.fetchall()
    conn.close()
    
    text = f"""
{EMOJIS['folder']} <b>سجل الأدمن (آخر 30)</b> {EMOJIS['folder']}

"""
    
    for log in logs:
        text += f"👤 {log[1]} | {log[2]}\n⏰ {log[4]}\n💬 {log[3][:50]}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_tickets")
def admin_tickets(call):
    """التذاكر للأدمن"""
    if not is_admin(call.from_user.id):
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM support_tickets ORDER BY created_at DESC LIMIT 30")
    tickets = c.fetchall()
    conn.close()
    
    text = f"""
{EMOJIS['ticket']} <b>التذاكر (آخر 30)</b> {EMOJIS['ticket']}

"""
    
    for t in tickets:
        status_emoji = {"open": "🔴", "in_progress": "🟡", "closed": "🟢"}.get(t[4], "⚪")
        text += f"{status_emoji} <b>#{t[0]}</b> | User: {t[1]}\n📝 {t[2]}\n⏰ {t[6]}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_cleanup")
def admin_cleanup(call):
    """تنظيف قاعدة البيانات"""
    if not is_admin(call.from_user.id):
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # حذف السجلات القديمة (أكثر من 30 يوم)
    old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("DELETE FROM otp_logs WHERE timestamp < ?", (old_date,))
    deleted_logs = c.rowcount
    
    # حذف التذاكر المغلقة القديمة
    c.execute("DELETE FROM support_tickets WHERE status = 'closed' AND updated_at < ?", (old_date,))
    deleted_tickets = c.rowcount
    
    # تنظيف
    c.execute("VACUUM")
    
    conn.commit()
    conn.close()
    
    text = f"""
{EMOJIS['check']} <b>تم التنظيف!</b> {EMOJIS['check']}

🗑️ سجلات OTP محذوفة: {deleted_logs}
🗑️ تذاكر مغلقة محذوفة: {deleted_tickets}
💾 تم تحسين حجم قاعدة البيانات
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_export_data")
def admin_export_data(call):
    """تصدير البيانات"""
    if not is_admin(call.from_user.id):
        return
    
    try:
        # تصدير المستخدمين
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # ملف المستخدمين
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        
        with open("export_users.csv", "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Username", "First Name", "Last Name", "Country", "Number", "Banned", "Points", "Level", "VIP", "Total OTPs"])
            for u in users:
                writer.writerow([u[0], u[1], u[2], u[3], u[4], u[5], u[6], u[8] if len(u) > 8 else 0, u[9] if len(u) > 9 else 0, u[13] if len(u) > 13 else 0, u[16] if len(u) > 16 else 0])
        
        # ملف OTP
        c.execute("SELECT * FROM otp_logs ORDER BY id DESC LIMIT 1000")
        otps = c.fetchall()
        
        with open("export_otps.csv", "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["DT", "Number", "CLI", "Message", "OTP", "Country", "Service", "Timestamp"])
            for o in otps:
                writer.writerow([o[1], o[2], o[3], o[4], o[5], o[6], o[7], o[10]])
        
        conn.close()
        
        # إرسال الملفات
        with open("export_users.csv", "rb") as f:
            bot.send_document(call.from_user.id, f, caption=f"👥 المستخدمين ({len(users)})")
        
        with open("export_otps.csv", "rb") as f:
            bot.send_document(call.from_user.id, f, caption=f"🔑 OTPs ({len(otps)})")
        
        os.remove("export_users.csv")
        os.remove("export_otps.csv")
        
        bot.answer_callback_query(call.id, "✅ تم التصدير!", show_alert=True)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {e}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_check_numbers")
def admin_check_numbers(call):
    """فحص الأرقام"""
    if not is_admin(call.from_user.id):
        return
    
    user_states[call.from_user.id] = "check_numbers"
    
    text = f"""
{EMOJIS['search']} <b>فحص الأرقام</b> {EMOJIS['search']}

أرسل ملف TXT يحتوي على الأرقام للفحص:
- سيتم فحص صلاحية الأرقام
- اكتشاف التكرار
- تصنيف حسب الدولة
"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} إلغاء", callback_data="admin_panel"))
    
    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(content_types=['document'])
def handle_combo_file(message):
    if not is_admin(message.from_user.id):
        return
    
    state = user_states.get(message.from_user.id)
    
    # فحص الأرقام
    if state == "check_numbers":
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            content = downloaded_file.decode('utf-8', errors='ignore')
            
            numbers = re.findall(r'\d{8,15}', content)
            numbers = [n for n in numbers if len(n) >= 8]
            
            # إحصائيات
            total = len(numbers)
            unique = len(set(numbers))
            duplicates = total - unique
            
            # تصنيف حسب الدولة
            country_counts = defaultdict(int)
            for num in numbers:
                for code, (name, flag) in COUNTRY_CODES.items():
                    if num.startswith(code):
                        country_counts[f"{flag} {name}"] += 1
                        break
            
            text = f"""
{EMOJIS['check']} <b>نتائج الفحص</b> {EMOJIS['check']}

📊 <b>الإحصائيات:</b>
• الإجمالي: {total}
• الفريد: {unique}
• المكرر: {duplicates}

🌍 <b>حسب الدولة:</b>
"""
            
            for country, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                text += f"  {country}: {count}\n"
            
            bot.reply_to(message, text, parse_mode="HTML")
            del user_states[message.from_user.id]
            
        except Exception as e:
            bot.reply_to(message, f"❌ خطأ: {e}")
            del user_states[message.from_user.id]
        return
    
    # إضافة كومبو (الكود الأصلي)
    if state != "waiting_combo_file":
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8', errors='ignore')
        
        all_phone_numbers = []
        
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            
            clean_line = re.sub(r'[^\d\+]', '', line)
            numbers = re.findall(r'\d{8,15}', clean_line)
            
            for phone in numbers:
                if phone.startswith('0'):
                    phone = phone[1:]
                
                if len(phone) >= 8:
                    all_phone_numbers.append(phone)
        
        if not all_phone_numbers:
            bot.reply_to(message, f"""
{EMOJIS['error']} <b>لم أعثر على أرقام!</b>
""", parse_mode="HTML")
            if message.from_user.id in user_states:
                del user_states[message.from_user.id]
            return
        
        country_code = None
        country_name = "غير معروف"
        country_flag = "🌍"
        
        sample_numbers = all_phone_numbers[:20] if len(all_phone_numbers) > 20 else all_phone_numbers
        
        sorted_codes = sorted(COUNTRY_CODES.keys(), key=len, reverse=True)
        code_counts = {}
        
        for phone in sample_numbers:
            for code in sorted_codes:
                if phone.startswith(code):
                    code_counts[code] = code_counts.get(code, 0) + 1
                    break
        
        if code_counts:
            sorted_counts = sorted(code_counts.items(), key=lambda x: x[1], reverse=True)
            winning_code, win_count = sorted_counts[0]
            
            if win_count >= len(sample_numbers) * 0.3:
                country_code = winning_code
                country_name, country_flag = COUNTRY_CODES.get(winning_code, ("غير معروف", "🌍"))
        
        if not country_code:
            full_code_counts = {}
            
            for phone in all_phone_numbers[:100]:
                for code in sorted_codes:
                    if phone.startswith(code):
                        full_code_counts[code] = full_code_counts.get(code, 0) + 1
                        break
            
            if full_code_counts:
                sorted_full = sorted(full_code_counts.items(), key=lambda x: x[1], reverse=True)
                best_code, best_count = sorted_full[0]
                
                if best_count >= 5:
                    country_code = best_code
                    country_name, country_flag = COUNTRY_CODES.get(best_code, ("غير معروف", "🌍"))
        
        if not country_code:
            sample_display = "\n".join([f"- <code>{num[:15]}...</code>" for num in sample_numbers[:5]])
            
            bot.reply_to(message, f"""
{EMOJIS['error']} <b>فشل في تحديد الدولة!</b>

📊 <b>معلومات الملف:</b>
• عدد الأرقام: {len(all_phone_numbers)}
• أول 5 أرقام:
{sample_display}
""", parse_mode="HTML")
            
            if message.from_user.id in user_states:
                del user_states[message.from_user.id]
            return
        
        save_combo(country_code, all_phone_numbers)
        
        success_msg = f"""
{EMOJIS['check']} <b>تم حفظ الكومبو!</b> {EMOJIS['check']}

{country_flag} <b>الدولة:</b> {country_name}
📞 <b>الكود:</b> +{country_code}
🔢 <b>عدد الأرقام:</b> {len(all_phone_numbers)}
🕒 <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        bot.reply_to(message, success_msg, parse_mode="HTML")
        
        if message.from_user.id in user_states:
            del user_states[message.from_user.id]
        
        print(f"🎉 تم حفظ {len(all_phone_numbers)} رقم لـ {country_code}")
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"🔥 خطأ: {error_trace}")
        
        bot.reply_to(message, f"""
{EMOJIS['error']} <b>حدث خطأ!</b>

{str(e)}
""", parse_mode="HTML")
        
        if message.from_user.id in user_states:
            del user_states[message.from_user.id]

# باقي الأكواد الأصلية (handle_country_selection, change_number, etc)
@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def handle_country_selection(call):
    if is_banned(call.from_user.id):
        bot.answer_callback_query(call.id, "🚫 You are banned.", show_alert=True)
        return
    
    country_code = call.data.split("_", 1)[1]
    country_name, flag = COUNTRY_CODES.get(country_code, ("Unknown", "🌍"))
    
    available_numbers = get_available_numbers(country_code)
    
    if not available_numbers:
        bot.answer_callback_query(call.id, "❌ All numbers are currently in use.", show_alert=True)
        return
    
    selected_number = random.choice(available_numbers)
    
    user_data = get_user(call.from_user.id)
    if user_data and user_data[5]:
        release_number(user_data[5])
    
    assign_number_to_user(call.from_user.id, selected_number)
    save_user(call.from_user.id, country_code=country_code, assigned_number=selected_number)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "👥 OTP GROUP", 
        url=OTP_GROUP_LINK
    ))
    markup.row(
        types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"change_num_{country_code}"),
        types.InlineKeyboardButton("🌍 تغيير الدولة", callback_data="back_to_countries")
    )
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['star']} المفضلة", callback_data=f"fav_{selected_number}"),
        types.InlineKeyboardButton(f"{EMOJIS['message']} سجل OTP", callback_data="my_otp_history")
    )
    
    # حساب وقت الانتهاء
    expiry_time = (datetime.now() + timedelta(hours=NUMBER_EXPIRY_HOURS)).strftime("%Y-%m-%d %H:%M")
    
    message_text = f"""
{EMOJIS['phone']} <b>رقمك جاهز!</b> {EMOJIS['phone']}

╔══════════════════════╗
║  📱 <b>الرقم:</b> <code>{selected_number}</code>
║  🌍 <b>الدولة:</b> {flag} {country_name}
║  ⏳ <b>الحالة:</b> بانتظار OTP
║  ⏰ <b>ينتهي:</b> {expiry_time}
╚══════════════════════╝

{EMOJIS['info']} <i>استخدم الرقم في الموقع الذي تريده</i>
"""
    
    try:
        bot.edit_message_text(
            message_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(
            call.message.chat.id,
            message_text,
            reply_markup=markup,
            parse_mode="HTML"
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("fav_"))
def add_to_favorites(call):
    """إضافة للمفضلة"""
    number = call.data.split("_", 1)[1]
    add_favorite_number(call.from_user.id, number)
    bot.answer_callback_query(call.id, f"✅ تمت الإضافة للمفضلة!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_num_"))
def change_number(call):
    if is_banned(call.from_user.id):
        return
    
    country_code = call.data.split("_", 2)[2]
    country_name, flag = COUNTRY_CODES.get(country_code, ("Unknown", "🌍"))
    
    available_numbers = get_available_numbers(country_code)
    
    if not available_numbers:
        bot.answer_callback_query(call.id, "❌ All numbers are currently in use.", show_alert=True)
        return
    
    user_data = get_user(call.from_user.id)
    if user_data and user_data[5]:
        release_number(user_data[5])
    
    selected_number = random.choice(available_numbers)
    assign_number_to_user(call.from_user.id, selected_number)
    save_user(call.from_user.id, assigned_number=selected_number)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👥 OTP GROUP", url=OTP_GROUP_LINK))
    markup.row(
        types.InlineKeyboardButton("🔄 تغيير الرقم", callback_data=f"change_num_{country_code}"),
        types.InlineKeyboardButton("🌍 تغيير الدولة", callback_data="back_to_countries")
    )
    
    expiry_time = (datetime.now() + timedelta(hours=NUMBER_EXPIRY_HOURS)).strftime("%Y-%m-%d %H:%M")
    
    message_text = f"""
{EMOJIS['phone']} <b>رقم جديد!</b> {EMOJIS['phone']}

╔══════════════════════╗
║  📱 <b>الرقم:</b> <code>{selected_number}</code>
║  🌍 <b>الدولة:</b> {flag} {country_name}
║  ⏳ <b>الحالة:</b> بانتظار OTP
║  ⏰ <b>ينتهي:</b> {expiry_time}
╚══════════════════════╝
"""
    
    try:
        bot.edit_message_text(
            message_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(
            call.message.chat.id,
            message_text,
            reply_markup=markup,
            parse_mode="HTML"
        )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_countries")
def back_to_countries(call):
    countries = get_all_combos()
    
    if not countries:
        bot.answer_callback_query(call.id, "❌ No countries available.", show_alert=True)
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for code in countries:
        if code in COUNTRY_CODES:
            name = get_combo_name(code)
            flag = COUNTRY_CODES.get(code,("","🌍"))[1]
            available = len(get_available_numbers(code))
            markup.insert(types.InlineKeyboardButton(
                f"{flag} {name} ({available})", 
                callback_data=f"country_{code}"
            ))
    
    markup.row(
        types.InlineKeyboardButton(f"{EMOJIS['user']} بروفايلي", callback_data="my_profile"),
        types.InlineKeyboardButton(f"{EMOJIS['gift']} المكافأة اليومية", callback_data="daily_reward")
    )
    
    if is_admin(call.from_user.id):
        markup.add(types.InlineKeyboardButton(
            f"{EMOJIS['admin']} لوحة الأدمن", 
            callback_data="admin_panel"
        ))
    
    try:
        bot.edit_message_text(
            f"""
{get_random_welcome()}

{EMOJIS['crown']} <b>اختر دولتك:</b> {EMOJIS['crown']}
""",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
    except:
        bot.send_message(
            call.message.chat.id,
            f"""
{get_random_welcome()}

{EMOJIS['crown']} <b>اختر دولتك:</b> {EMOJIS['crown']}
""",
            reply_markup=markup,
            parse_mode="HTML"
        )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    if check_user_joined(call.from_user.id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        bot.answer_callback_query(call.id, "✅ تم التحقق من الاشتراك")
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك بعد", show_alert=True)

# باقي handlers الأصلية
@bot.callback_query_handler(func=lambda call: call.data == "admin_add_combo")
def admin_add_combo(call):
    if not is_admin(call.from_user.id):
        return
    user_states[call.from_user.id] = "waiting_combo_file"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    bot.edit_message_text(f"""
{EMOJIS['upload']} <b>إضافة كومبو</b> {EMOJIS['upload']}

أرسل ملف TXT يحتوي على الأرقام
""", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_del_combo")
def admin_del_combo(call):
    if not is_admin(call.from_user.id):
        return
    
    combos = get_all_combos()
    if not combos:
        bot.answer_callback_query(call.id, "❌ لا توجد كومبوهات!", show_alert=True)
        return
    
    markup = types.InlineKeyboardMarkup()
    for code in combos:
        if code in COUNTRY_CODES:
            name, flag = COUNTRY_CODES[code]
            markup.add(types.InlineKeyboardButton(
                f"{flag} {name}", 
                callback_data=f"del_combo_{code}"
            ))
    
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    bot.edit_message_text(f"""
{EMOJIS['trash']} <b>حذف كومبو</b> {EMOJIS['trash']}

اختر الكومبو للحذف:
""", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_combo_"))
def confirm_del_combo(call):
    if not is_admin(call.from_user.id):
        return
    
    code = call.data.split("_", 2)[2]
    delete_combo(code)
    
    if code in COUNTRY_CODES:
        name, flag = COUNTRY_CODES[code]
        message = f"{EMOJIS['check']} تم حذف: {flag} {name}"
    else:
        message = f"{EMOJIS['check']} تم حذف: {code}"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    bot.edit_message_text(message, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id):
        return
    
    total_users = len(get_all_users())
    combos = get_all_combos()
    
    total_numbers = 0
    for code in combos:
        numbers = get_combo(code)
        total_numbers += len(numbers)
    
    otp_count = len(get_otp_logs())
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    
    stats_msg = f"""
{EMOJIS['chart']} <b>الإحصائيات</b> {EMOJIS['chart']}

╔══════════════════════╗
║  👥 المستخدمين: {total_users}
║  🌐 الدول: {len(combos)}
║  📞 الأرقام: {total_numbers}
║  🔑 الأكواد: {otp_count}
║  👑 الأدمنز: {len(ADMIN_IDS)}
╚══════════════════════╝

<b>الدول المتاحة:</b>
"""
    
    for code in combos:
        if code in COUNTRY_CODES:
            name, flag = COUNTRY_CODES[code]
            numbers = get_combo(code)
            stats_msg += f"{flag} {name}: {len(numbers)}\n"
    
    bot.edit_message_text(stats_msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_full_report")
def admin_full_report(call):
    if not is_admin(call.from_user.id):
        return
    
    try:
        report = f"""
{EMOJIS['chart']} تقرير شامل عن البوت
{'='*40}

{EMOJIS['users']} المستخدمون:
"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        
        for u in users:
            status = "محظور" if u[6] else "نشط"
            report += f"🆔: {u[0]} | 👤: @{u[1] or 'N/A'} | 📞: {u[5] or 'N/A'} | 🚫: {status}\n"
        
        report += "\n" + "="*40 + "\n\n"
        report += f"{EMOJIS['key']} سجل الأكواد:\n"
        
        c.execute("SELECT * FROM otp_logs ORDER BY id DESC LIMIT 50")
        logs = c.fetchall()
        
        for log in logs:
            report += f"📞: {log[2]} | 🔑: {log[5]} | 🕒: {log[10]}\n"
        
        conn.close()
        
        report += "\n" + "="*40 + "\n\n"
        report += f"⏰ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        with open("bot_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        
        with open("bot_report.txt", "rb") as f:
            bot.send_document(call.from_user.id, f)
        
        os.remove("bot_report.txt")
        bot.answer_callback_query(call.id, "✅ تم إرسال التقرير!")
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطأ: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban")
def admin_ban_step1(call):
    if not is_admin(call.from_user.id):
        return
    
    user_states[call.from_user.id] = "ban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    bot.edit_message_text(f"""
{EMOJIS['error']} <b>حظر مستخدم</b>

أدخل معرف المستخدم:
""", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "ban_user")
def admin_ban_step2(message):
    try:
        uid = int(message.text)
        ban_user(uid, "بواسطة أدمن")
        bot.reply_to(message, f"""
{EMOJIS['check']} <b>تم الحظر!</b>

🚫 المستخدم: <code>{uid}</code>
""", parse_mode="HTML")
        if message.from_user.id in user_states:
            del user_states[message.from_user.id]
    except:
        bot.reply_to(message, f"{EMOJIS['error']} معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_unban")
def admin_unban_step1(call):
    if not is_admin(call.from_user.id):
        return
    
    user_states[call.from_user.id] = "unban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    bot.edit_message_text(f"""
{EMOJIS['check']} <b>فك حظر مستخدم</b>

أدخل معرف المستخدم:
""", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "unban_user")
def admin_unban_step2(message):
    try:
        uid = int(message.text)
        unban_user(uid)
        bot.reply_to(message, f"""
{EMOJIS['check']} <b>تم فك الحظر!</b>

✅ المستخدم: <code>{uid}</code>
""", parse_mode="HTML")
        if message.from_user.id in user_states:
            del user_states[message.from_user.id]
    except:
        bot.reply_to(message, f"{EMOJIS['error']} معرف غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_all")
def admin_broadcast_all_step1(call):
    if not is_admin(call.from_user.id):
        return
    
    user_states[call.from_user.id] = "broadcast_all"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    bot.edit_message_text(f"""
{EMOJIS['mail']} <b>إرسال للجميع</b>

اكتب الرسالة:
""", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_all")
def admin_broadcast_all_step2(message):
    users = get_all_users()
    success = 0
    
    for uid in users:
        try:
            bot.send_message(uid, message.text)
            success += 1
        except:
            pass
    
    bot.reply_to(message, f"""
{EMOJIS['check']} <b>تم الإرسال!</b>

✅ نجح: {success}/{len(users)}
""", parse_mode="HTML")
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_user")
def admin_broadcast_user_step1(call):
    if not is_admin(call.from_user.id):
        return
    
    user_states[call.from_user.id] = "broadcast_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    bot.edit_message_text(f"""
{EMOJIS['message']} <b>إرسال لمستخدم</b>

أدخل معرف المستخدم:
""", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_user_id")
def admin_broadcast_user_step2(message):
    try:
        uid = int(message.text)
        user_states[message.from_user.id] = f"broadcast_msg_{uid}"
        bot.reply_to(message, f"""
{EMOJIS['message']} اكتب الرسالة:
""")
    except:
        bot.reply_to(message, f"{EMOJIS['error']} معرف غير صحيح!")

@bot.message_handler(func=lambda msg: str(user_states.get(msg.from_user.id, "")).startswith("broadcast_msg_"))
def admin_broadcast_user_step3(message):
    uid = int(user_states[message.from_user.id].split("_")[2])
    try:
        bot.send_message(uid, message.text)
        bot.reply_to(message, f"""
{EMOJIS['check']} <b>تم الإرسال!</b>

✅ للمستخدم: <code>{uid}</code>
""", parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"{EMOJIS['error']} فشل: {e}")
    
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_user_info")
def admin_user_info_step1(call):
    if not is_admin(call.from_user.id):
        return
    
    user_states[call.from_user.id] = "get_user_info"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    bot.edit_message_text(f"""
{EMOJIS['user']} <b>معلومات مستخدم</b>

أدخل معرف المستخدم:
""", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "get_user_info")
def admin_user_info_step2(message):
    try:
        uid = int(message.text)
        user = get_user(uid)
        
        if not user:
            bot.reply_to(message, f"{EMOJIS['error']} المستخدم غير موجود!")
        else:
            status = "محظور" if user[6] else "نشط"
            points = user[8] if len(user) > 8 else 0
            level = user[9] if len(user) > 9 else 1
            total_otps = user[16] if len(user) > 16 else 0
            
            info = f"""
{EMOJIS['user']} <b>معلومات المستخدم</b> {EMOJIS['user']}

╔══════════════════════╗
║  🆔 ID: <code>{user[0]}</code>
║  👤 Username: @{user[1] or 'N/A'}
║  📛 الاسم: {user[2] or ''} {user[3] or ''}
║  📞 الرقم: {user[5] or 'N/A'}
║  🌍 الدولة: {user[4] or 'N/A'}
║  🚫 الحالة: {status}
╠══════════════════════╣
║  💰 النقاط: {points}
║  🏆 المستوى: {level}
║  🔑 إجمالي OTP: {total_otps}
╚══════════════════════╝
"""
            bot.reply_to(message, info, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"{EMOJIS['error']} خطأ: {e}")
    
    if message.from_user.id in user_states:
        del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "toggle_force_sub")
def toggle_force_sub(call):
    if not is_admin(call.from_user.id):
        return
    if is_force_sub_enabled():
        set_setting("force_sub","off")
        bot.answer_callback_query(call.id,f"{EMOJIS['error']} تم تعطيل الاشتراك الإجباري", show_alert=True)
    else:
        set_setting("force_sub","on")
        bot.answer_callback_query(call.id,f"{EMOJIS['check']} تم تفعيل الاشتراك الإجباري", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_rename_range")
def admin_rename_range(call):
    if not is_admin(call.from_user.id):
        return
    combos = get_all_combos()
    markup = types.InlineKeyboardMarkup()
    for code in combos:
        name = get_combo_name(code)
        markup.add(types.InlineKeyboardButton(
            name, 
            callback_data=f"rename_{code}"
        ))
    markup.add(types.InlineKeyboardButton(f"{EMOJIS['back']} رجوع", callback_data="admin_panel"))
    bot.edit_message_text(f"""
{EMOJIS['edit']} <b>تعديل اسم الرينج</b>

اختر الرينج:
""", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("rename_"))
def rename_range(call):
    if not is_admin(call.from_user.id):
        return
    code = call.data.split("_",1)[1]
    user_states[call.from_user.id] = f"rename_range_{code}"
    bot.send_message(call.from_user.id,f"""
{EMOJIS['edit']} <b>تعديل الاسم</b>

أرسل الاسم الجديد:
""", parse_mode="HTML")

@bot.message_handler(func=lambda m: str(user_states.get(m.from_user.id,"")).startswith("rename_range_"))
def rename_range_save(message):
    code = user_states[message.from_user.id].split("_",2)[2]
    new_name = message.text.strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE combos SET custom_name=? WHERE country_code=?", (new_name,code))
    conn.commit()
    conn.close()
    bot.reply_to(message,f"""
{EMOJIS['check']} <b>تم التعديل!</b>

✅ الاسم الجديد: {new_name}
""", parse_mode="HTML")
    del user_states[message.from_user.id]

# ======================
# 🔄 الحلقة الرئيسية
# ======================
class CRAPI:
    """فئة للتعامل مع CR API"""
    
    def __init__(self):
        self.api_url = API_URL
        self.api_token = API_TOKEN
        
    def fetch_messages(self, records=100, hours_back=1):
        """جلب الرسائل من جميع لوحات API"""
        all_messages = []
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)

            dt1 = start_time.strftime("%Y-%m-%d %H:%M:%S")
            dt2 = end_time.strftime("%Y-%m-%d %H:%M:%S")

            for panel in API_PANELS:
                try:
                    params = {
                        'token': panel["token"],
                        'dt1': dt1,
                        'dt2': dt2,
                        'records': records
                    }

                    response = requests.get(panel["url"], params=params, timeout=30)

                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == 'success':
                            all_messages.extend(data.get('data', []))

                except Exception as e:
                    print(f"[API] خطأ في لوحة: {panel['url']} | {e}")

            return all_messages

        except Exception as e:
            print(f"[API] ❌ خطأ عام في جلب البيانات: {e}")
            return []
    
    def check_token_valid(self):
        """التحقق من صحة التوكن"""
        try:
            params = {'token': self.api_token, 'records': 1}
            response = requests.get(self.api_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('status') != 'error'
            return False
        except:
            return False

crapi = CRAPI()

def api_main_loop_updated():
    """الحلقة الرئيسية"""
    print("=" * 60)
    print("🚀 بدء تشغيل بوت OTP - النسخة المطورة")
    print(f"👑 المالك: {OWNER_ID}")
    print(f"👥 الأدمنز: {len(ADMIN_IDS)} مستخدم")
    print(f"📢 القناة: {CHAT_IDS[0]}")
    print(f"🔗 API: {API_URL}")
    print("=" * 60)
    
    processed_messages = set()
    error_count = 0
    
    while True:
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            
            if error_count > 10:
                print("⚠️  عدد الأخطاء تجاوز الحد، إعادة التشغيل بعد دقيقة...")
                time.sleep(60)
                error_count = 0
                continue
            
            # معالجة الرسائل المجدولة
            try:
                scheduled = get_pending_scheduled_messages()
                for msg in scheduled:
                    try:
                        if msg[3] == "all":
                            users = get_all_users()
                            for uid in users:
                                try:
                                    bot.send_message(uid, msg[1])
                                except:
                                    pass
                        mark_message_sent(msg[0])
                    except:
                        pass
            except:
                pass
            
            print(f"[{current_time}] 🔍 جلب الرسائل من API...")
            
            messages = crapi.fetch_messages(records=100, hours_back=1)
            
            if isinstance(messages, list):
                print(f"📨 تم جلب {len(messages)} رسالة")
                
                new_count = 0
                for msg in messages:
                    if not isinstance(msg, dict):
                        continue
                    
                    msg_key = f"{msg.get('dt')}_{msg.get('num')}_{hash(msg.get('message', ''))}"
                    
                    if msg_key not in processed_messages:
                        try:
                            if process_and_send_message_new(msg):
                                new_count += 1
                            processed_messages.add(msg_key)
                        except Exception as e:
                            print(f"❌ خطأ في معالجة رسالة: {e}")
                            traceback.print_exc()
                
                if new_count > 0:
                    print(f"✅ تم إرسال {new_count} رسالة جديدة")
                else:
                    print("⏭️  لا توجد رسائل جديدة")
                
                error_count = 0
            else:
                print(f"[{current_time}] ⚠️  لا توجد رسائل أو استجابة غير صالحة")
                error_count += 1
            
            if len(processed_messages) > 1000:
                processed_messages = set(list(processed_messages)[-500:])
            
        except KeyboardInterrupt:
            print("\n⛔ إيقاف البوت...")
            break
        except requests.exceptions.RequestException as e:
            print(f"❌ خطأ في اتصال الشبكة: {e}")
            error_count += 1
            time.sleep(30)
        except Exception as e:
            print(f"❌ خطأ: {e}")
            traceback.print_exc()
            error_count += 1
        
        time.sleep(REFRESH_INTERVAL)

# ======================
# ▶️ تشغيل البوت
# ======================
def run_bot():
    print("[🤖] تشغيل بوت التليجرام...")
    
    while True:
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔄 بدأ البوت...")
            bot.polling(none_stop=True, timeout=60)
        except KeyboardInterrupt:
            print("\n⛔ إوقف البوت (بواسطة المستخدم)...")
            break
        except Exception as e:
            print(f"❌ خطأ في البوت: {e}")
            traceback.print_exc()
            print("🔄 إعادة تشغيل البوت بعد 10 ثواني...")
            time.sleep(10)

def keep_alive_ping():
    while True:
        try:
            bot.get_me()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ♻️ Ping successful")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Ping failed: {e}")
        time.sleep(300)

def auto_backup():
    """نسخ احتياطي تلقائي كل 6 ساعات"""
    while True:
        try:
            time.sleep(6 * 60 * 60)  # 6 ساعات
            success, filename, size = create_backup(0)
            if success:
                print(f"💾 Auto backup created: {filename}")
        except Exception as e:
            print(f"❌ Auto backup error: {e}")

# ======================
# 🚀 تشغيل النظام الرئيسي
# ======================
if __name__ == "__main__":
    print("=" * 60)
    print("📋 معلومات الإعداد:")
    print(f"👑 المالك: {OWNER_ID}")
    print(f"👥 الأدمنز: {ADMIN_IDS}")
    print(f"📢 القناة: {CHAT_IDS[0]}")
    print(f"📢 القناة 1: {CHANNEL_1_URL}")
    print(f"📢 القناة 2: {CHANNEL_2_URL}")
    print(f"👤 Owner 1: {OWNER_1_LINK}")
    print(f"👤 Owner 2: {OWNER_2_LINK}")
    print("=" * 60)
    print("🎁 المميزات المضافة: 50 ميزة")
    print("=" * 60)
    
    try:
        bot_thread = threading.Thread(target=run_bot, daemon=True, name="TelegramBot")
        bot_thread.start()
        
        print("✅ بدأ ثريد البوت")
        time.sleep(5)
        
        ping_thread = threading.Thread(target=keep_alive_ping, daemon=True, name="KeepAlivePing")
        ping_thread.start()
        
        print("✅ بدأ ثريد Ping")
        
        backup_thread = threading.Thread(target=auto_backup, daemon=True, name="AutoBackup")
        backup_thread.start()
        
        print("✅ بدأ ثريد النسخ الاحتياطي التلقائي")
        
        api_main_loop_updated()
        
    except KeyboardInterrupt:
        print("\n\n⛔ تم إيقاف النظام بواسطة المستخدم")
    except Exception as e:
        print(f"\n\n💥 خطأ رئيسي: {e}")
        traceback.print_exc()
    finally:
        print("🔄 إعادة تشغيل النظام...")
        time.sleep(5)
