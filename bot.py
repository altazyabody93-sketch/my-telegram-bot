import time
import re
import json
import os
import html
import random
import uuid
import pickle
import cloudscraper
import requests
import phonenumbers
from phonenumbers import geocoder
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from threading import Thread, Event
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus
import shutil

BOT_TOKEN ="8651333494:AAHqfzAWBnGu1OvPss10rbV932QFGPj2V5o"
MAIN_ADMIN_ID = 7325566792
# ── Multilang helper ──────────────────────────────────────────────────────────
_ML = {
    "not_subscribed": {
        "en": "⚠️ You haven't joined all channels yet!",
        "ar": "⚠️ لم تنضم إلى جميع القنوات بعد!",
        "ru": "⚠️ Вы ещё не вступили во все каналы!",
        "bn": "⚠️ আপনি এখনো সব চ্যানেলে যোগ দেননি!",
    },
    "join_first": {
        "en": "❌ Join all channels first!",
        "ar": "❌ انضم إلى جميع القنوات أولاً!",
        "ru": "❌ Сначала вступите во все каналы!",
        "bn": "❌ আগে সব চ্যানেলে যোগ দিন!",
    },
    "subscribe_first": {
        "en": "❌ Please subscribe to all channels first!",
        "ar": "❌ يرجى الاشتراك في جميع القنوات أولاً!",
        "ru": "❌ Пожалуйста, подпишитесь на все каналы сначала!",
        "bn": "❌ অনুগ্রহ করে আগে সব চ্যানেলে সাবস্ক্রাইব করুন!",
    },
    "country_not_found": {
        "en": "❌ Country not found!",
        "ar": "❌ الدولة غير موجودة!",
        "ru": "❌ Страна не найдена!",
        "bn": "❌ দেশ পাওয়া যায়নি!",
    },
    "no_numbers": {
        "en": "❌ No numbers available for this country!",
        "ar": "❌ لا توجد أرقام متاحة لهذه الدولة!",
        "ru": "❌ Нет доступных номеров для этой страны!",
        "bn": "❌ এই দেশের জন্য কোনো নম্বর পাওয়া যাচ্ছে না!",
    },
    "no_countries": {
        "en": "❌ No countries available!",
        "ar": "❌ لا توجد دول متاحة!",
        "ru": "❌ Нет доступных стран!",
        "bn": "❌ কোনো দেশ পাওয়া যাচ্ছে না!",
    },
    "no_country_selected": {
        "en": "❌ No country selected!",
        "ar": "❌ لم يتم اختيار دولة!",
        "ru": "❌ Страна не выбрана!",
        "bn": "❌ কোনো দেশ নির্বাচন করা হয়নি!",
    },
    "number_changed": {
        "en": "✅ Number changed!",
        "ar": "✅ تم تغيير الرقم!",
        "ru": "✅ Номер изменён!",
        "bn": "✅ নম্বর পরিবর্তিত হয়েছে!",
    },
    "choose_country": {
        "en": "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji><b> Select a country </b><tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
        "ar": "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji><b> اختر دولة </b><tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
        "ru": "<b><tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji></b><b> Выберите страну </b><b><tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji></b>",
        "bn": "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji><b> একটি দেশ বেছে নিন </b><tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
    },
    "change_number": {
        "en": "Change Number",
        "ar": "تغيير الرقم",
        "ru": "Сменить номер",
        "bn": "নম্বর পরিবর্তন",
    },
    "change_country": {
        "en": "Change Country",
        "ar": "تغيير الدولة",
        "ru": "Сменить страну",
        "bn": "দেশ পরিবর্তন",
    },
    "back": {
        "en": "Back",
        "ar": "رجوع",
        "ru": "Назад",
        "bn": "ফিরে যান",
    },
    "banned": {
        "en": "⛔ You have been banned from using this bot.",
        "ar": "⛔ لقد تم حظرك من استخدام هذا البوت.",
        "ru": "⛔ Вы заблокированы в этом боте.",
        "bn": "⛔ আপনাকে এই বটে নিষিদ্ধ করা হয়েছে।",
    },
    "waiting_otp": {
        "en": "⏳ Status: Waiting For OTP..",
        "ar": "⏳ الحالة: في انتظار كود التحقق..",
        "ru": "⏳ Статус: Ожидание OTP..",
        "bn": "⏳ অবস্থা: OTP-এর জন্য অপেক্ষা করছি..",
    },
    "tap_copy": {
        "en": "Tap any number to copy it",
        "ar": "اضغط على أي رقم لنسخه",
        "ru": "Нажмите на любой номер, чтобы скопировать",
        "bn": "কপি করতে যেকোনো নম্বর ট্যাপ করুন",
    },
    "numbers_assigned": {
        "en": "Numbers Assigned!",
        "ar": "تم تعيين الأرقام!",
        "ru": "Номера назначены!",
        "bn": "নম্বর নির্ধারিত!",
    },
    "numbers_changed": {
        "en": "Numbers Changed!",
        "ar": "تم تغيير الأرقام!",
        "ru": "Номера изменены!",
        "bn": "নম্বর পরিবর্তিত!",
    },
    "number_selected": {
        "en": "Number Selected!",
        "ar": "تم اختيار الرقم!",
        "ru": "Номер выбран!",
        "bn": "নম্বর নির্বাচিত!",
    },
    "otp_group": {
        "en": "OTP Group",
        "ar": "جروب OTP",
        "ru": "OTP Группа",
        "bn": "OTP গ্রুপ",
    },
    "get_number_btn": {
        "en": "📲 Take a number",
        "ar": "📲 احصل على رقم",
        "ru": "📲 Получить номер",
        "bn": "📲 নম্বর নিন",
    },
    "my_account_btn": {
        "en": "👤 My Account",
        "ar": "👤 حسابي",
        "ru": "👤 Мой аккаунт",
        "bn": "👤 আমার অ্যাকাউন্ট",
    },
    "change_lang_btn": {
        "en": "🌍 Language",
        "ru": "🌍 Язык",
        "bn": "🌍 ভাষা",
    },
}

def ml(user_id_or_lang, key):
    """Get multilang string by user_id or lang code"""
    if isinstance(user_id_or_lang, str) and user_id_or_lang in ("en","ru","bn","ar"):
        lang = user_id_or_lang
    else:
        lang = get_user_language(user_id_or_lang)
    return _ML.get(key, {}).get(lang, _ML.get(key, {}).get("en", key))

# ─────────────────────────────────────────────────────────────────────────────

def create_backup(source_files, backup_dir="backups"):
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_backup_dir = os.path.join(backup_dir, f"backup_{timestamp}")
    os.makedirs(current_backup_dir, exist_ok=True)
    
    for file in source_files:
        if file and os.path.exists(file):
            try:
                dest_path = os.path.join(current_backup_dir, os.path.basename(file))
                if os.path.isdir(file):
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path)
                    shutil.copytree(file, dest_path)
                else:
                    shutil.copy2(file, current_backup_dir)
            except Exception as e:
                print(f"Error backing up {file}: {e}")
    
    
    zip_name = f"{current_backup_dir}.zip"
    try:
        shutil.make_archive(current_backup_dir, 'zip', current_backup_dir)
       
        shutil.rmtree(current_backup_dir)
        return zip_name
    except Exception as e:
        print(f"Error zipping backup: {e}")
        return current_backup_dir

class BackupManager:
    def create_backup(self):
        
        files_to_backup = []
        for var in ['SETTINGS_FILE', 'SESSIONS_FILE', 'USERS_FILE', 'ADMINS_FILE', 'GROUPS_FILE', 'COUNTRIES_FILE', 'CHANNELS_FILE']:
            val = globals().get(var)
            if val: files_to_backup.append(val)
        
        
        if os.path.exists("database"): files_to_backup.append("database")
        
        return create_backup(files_to_backup)
    
    def restore_backup(self, zip_path):
        return False

backup_manager = BackupManager()

# ── Live Traffic Log ─────────────────────────────────────────────────────────
# قائمة عالمية لتخزين سجل الـ OTPs مع الدولة والوقت (آخر 500 مدخل)
LIVE_TRAFFIC_LOG = []
LIVE_TRAFFIC_LOCK = threading.Lock()

def log_live_traffic(number, country_name=None):
    """تسجيل OTP جديد في سجل الـ Live Traffic"""
    global LIVE_TRAFFIC_LOG
    try:
        # استخراج اسم الدولة من الرقم إذا لم يُعطَ
        if not country_name:
            try:
                import phonenumbers
                parsed = phonenumbers.parse("+" + str(number).lstrip("+"))
                from phonenumbers import geocoder as pgeo
                country_name = pgeo.description_for_number(parsed, "en") or "Unknown"
            except Exception:
                country_name = "Unknown"
        
        entry = {
            "country": country_name,
            "time": datetime.now()
        }
        with LIVE_TRAFFIC_LOCK:
            LIVE_TRAFFIC_LOG.append(entry)
            # الاحتفاظ بآخر 500 مدخل فقط
            if len(LIVE_TRAFFIC_LOG) > 500:
                LIVE_TRAFFIC_LOG = LIVE_TRAFFIC_LOG[-500:]
    except Exception as e:
        print(f"⚠️ log_live_traffic error: {e}")

def get_live_traffic_stats(minutes=5):
    """حساب إحصائيات الـ Live Traffic لآخر X دقائق"""
    now = datetime.now()
    cutoff = now - timedelta(minutes=minutes)
    
    with LIVE_TRAFFIC_LOCK:
        recent = [e for e in LIVE_TRAFFIC_LOG if e["time"] >= cutoff]
    
    total = len(recent)
    if total == 0:
        return total, 0, {}, None
    
    # حساب Results Sent %
    results_sent_pct = 100  # كل الـ OTPs اللي اتسجلت = اتبعتت
    
    # حساب توزيع الدول
    country_counts = {}
    for e in recent:
        c = e["country"] or "Unknown"
        country_counts[c] = country_counts.get(c, 0) + 1
    
    # ترتيب الدول تنازلياً
    sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    
    # حساب النسب المئوية
    country_pcts = [(c, round(cnt / total * 100, 1)) for c, cnt in sorted_countries]
    
    top_country = sorted_countries[0][0] if sorted_countries else None
    
    return total, results_sent_pct, country_pcts, top_country

# ─────────────────────────────────────────────────────────────────────────────

def list_backups(backup_dir="backups"):
   
    if not os.path.exists(backup_dir):
        return []
    return sorted([d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))], reverse=True)


import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
def tg_button(text, callback=None, url=None, style="primary"):

    btn = InlineKeyboardButton(
        text=text,
        callback_data=callback,
        url=url
    )

    try:
        btn.style = style
    except:
        try:
            btn.__dict__["style"] = style
        except:
            pass

    return btn

SETTINGS_FILE = "ii287.json"
SESSIONS_FILE = "bendary.json"
def get_country_flags(country_name):
    
    country_name_lower = country_name.lower()
    flags = {
        "egypt": "<tg-emoji emoji-id='5293992082212409502'>🇪🇬</tg-emoji>", "libya": "<tg-emoji emoji-id='5291858711826946840'>🇱🇾</tg-emoji>", "syria": "<tg-emoji emoji-id='5294013428199869487'>🇸🇾</tg-emoji>", "iraq": "<tg-emoji emoji-id='5294325010897327367'>🇮🇶</tg-emoji>", "saudi": "<tg-emoji emoji-id='5294163983983463099'>🇸🇦</tg-emoji>",
        "yemen": "<tg-emoji emoji-id='5294058972033076492'>🇾🇪</tg-emoji>", "jordan": "<tg-emoji emoji-id='5291988613112814801'>🇯🇴</tg-emoji>", "uae": "<tg-emoji emoji-id='5294314831824835370'>🇦🇪</tg-emoji>", "kuwait": "<tg-emoji emoji-id='5292066437920218075'>🇰🇼</tg-emoji>", "qatar": "<tg-emoji emoji-id='5292166360334357676'>🇶🇦</tg-emoji>",
        "oman": "<tg-emoji emoji-id='5291813666209946812'>🇴🇲</tg-emoji>", "bahrain": "<tg-emoji emoji-id='5294108398516720753'>🇧🇭</tg-emoji>", "lebanon": "<tg-emoji emoji-id='5294193108156699621'>🇱🇧</tg-emoji>", "palestine": "<tg-emoji emoji-id='5294289826525238172'>🇵🇸</tg-emoji>", "algeria": "<tg-emoji emoji-id='5294048127240655242'>🇩🇿</tg-emoji>",
        "morocco": "<tg-emoji emoji-id='5292108962391414885'>🇲🇦</tg-emoji>", "tunisia": "<tg-emoji emoji-id='5294484680601521871'>🇹🇳</tg-emoji>", "sudan": "<tg-emoji emoji-id='5294177148058228060'>🇸🇩</tg-emoji>", "somalia": "<tg-emoji emoji-id='5294058817414255960'>🇸🇴</tg-emoji>", "djibouti": "<tg-emoji emoji-id='5294127214768468283'>🇩🇯</tg-emoji>",
        "mauritania": "<tg-emoji emoji-id='5294429743674840973'>🇲🇷</tg-emoji>", "liber": "<tg-emoji emoji-id='5291858711826946840'>🇱🇾</tg-emoji>", "مصر": "<tg-emoji emoji-id='5293992082212409502'>🇪🇬</tg-emoji>", "ليبيا": "<tg-emoji emoji-id='5291858711826946840'>🇱🇾</tg-emoji>", "سوريا": "<tg-emoji emoji-id='5294013428199869487'>🇸🇾</tg-emoji>",
        "العراق": "<tg-emoji emoji-id='5294325010897327367'>🇮🇶</tg-emoji>", "السعودية": "<tg-emoji emoji-id='5294163983983463099'>🇸🇦</tg-emoji>", "اليمن": "<tg-emoji emoji-id='5294058972033076492'>🇾🇪</tg-emoji>", "الأردن": "<tg-emoji emoji-id='5291988613112814801'>🇯🇴</tg-emoji>", "الإمارات": "<tg-emoji emoji-id='5294314831824835370'>🇦🇪</tg-emoji>",
        "الكويت": "<tg-emoji emoji-id='5292066437920218075'>🇰🇼</tg-emoji>", "قطر": "<tg-emoji emoji-id='5292166360334357676'>🇶🇦</tg-emoji>", "عمان": "<tg-emoji emoji-id='5291813666209946812'>🇴🇲</tg-emoji>", "البحرين": "<tg-emoji emoji-id='5294108398516720753'>🇧🇭</tg-emoji>", "لبنان": "<tg-emoji emoji-id='5294193108156699621'>🇱🇧</tg-emoji>",
        "فلسطين": "<tg-emoji emoji-id='5294289826525238172'>🇵🇸</tg-emoji>", "الجزائر": "<tg-emoji emoji-id='5294048127240655242'>🇩🇿</tg-emoji>", "المغرب": "<tg-emoji emoji-id='5292108962391414885'>🇲🇦</tg-emoji>", "تونس": "<tg-emoji emoji-id='5294484680601521871'>🇹🇳</tg-emoji>", "السودان": "<tg-emoji emoji-id='5294177148058228060'>🇸🇩</tg-emoji>",
        "الصومال": "<tg-emoji emoji-id='5294058817414255960'>🇸🇴</tg-emoji>", "جيبوتي": "<tg-emoji emoji-id='5294127214768468283'>🇩🇯</tg-emoji>", "موريتانيا": "<tg-emoji emoji-id='5294429743674840973'>🇲🇷</tg-emoji>"
    }
    for name, flag in flags.items():
        if name in country_name_lower:
            return flag
    return "🌐"

def load_env():
    
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()



DEFAULT_SETTINGS = {
    "GROUP": {
        "name": "GROUP",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "http://139.99.63.204",
        "login_page_url": "http://139.99.63.204/ints/login",
        "login_post_url": "http://139.99.63.204/ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "Fly sms": {
        "name": "Fly sms",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "http://193.70.33.154",
        "login_page_url": "http://193.70.33.154/ints/login",
        "login_post_url": "http://193.70.33.154/ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 60,
        "enabled": True
    },
    "Number_Panel": {
        "name": "Number Panel",
        "accounts": [
            {
                "id": "",
                "api_token": ""
            }
        ],
        "base_url": "http://147.135.212.197/crapi/st/viewstats",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "Bolt": {
        "name": "Bolt",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "http://93.190.143.35/ints",
        "login_page_url": "http://93.190.143.35/ints/Login",
        "login_post_url": "http://93.190.143.35/ints/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "iVASMS": {
        "name": "iVAS SMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": "",
                "api_key": "sk_4b5ff02b42635e4c4891bd5d2f8fcb7aff2f7af6d5daecf8498ba91092dfcbb6"
            }
        ],
        "api_url": "https://maroon-wombat-183778.hostingersite.com/apiivasms/api.php",
        "check_interval": 5,
        "timeout": 15,
        "enabled": True
    },
    "MSI": {
        "name": "MSI",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "admin123",
                "password": "733723"
            }
        ],
        "base_url": "http://145.239.130.45/ints",
        "login_page_url": "http://145.239.130.45/ints/login",
        "login_post_url": "http://145.239.130.45/ints/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "proton SMS": {
        "name": "proton SMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "http://109.236.84.81/ints",
        "login_page_url": "http://109.236.84.81/ints/login",
        "login_post_url": "http://109.236.84.81/ints/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 60,
        "enabled": True
    },
    "IMS": {
        "name": "IMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "http://45.82.67.20",
        "login_page_url": "http://45.82.67.20/ints/login",
        "login_post_url": "http://45.82.67.20/ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 16,
        "timeout": 30,
        "enabled": True
    },
    "Roxy SMS": {
        "name": "Roxy SMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "http://www.roxysms.net",
        "login_page_url": "http://www.roxysms.net/Login",
        "login_post_url": "http://www.roxysms.net/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True,
        "use_scraper": True
    },
    "TimeSMS": {
        "name": "TimeSMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "https://timesms.org",
        "login_page_url": "https://timesms.org/login",
        "login_post_url": "https://timesms.org/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "Konekta": {
        "name": "Konekta",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "https://konektapremium.net",
        "login_page_url": "https://konektapremium.net/sign-in",
        "login_post_url": "https://konektapremium.net/signin",
        "ajax_path": "/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "hadi": {
        "name": "hadi",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "http://2.59.169.96",
        "login_page_url": "http://2.59.169.96/ints/login",
        "login_post_url": "http://2.59.169.96/ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "fire": {
        "name": "fire",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "http://54.39.104.241",
        "login_page_url": "http://54.39.104.241/ints/login",
        "login_post_url": "http://54.39.104.241/ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 60,
        "enabled": True
    },
    "Seven1Tel": {
        "name": "Seven1Tel",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "http://94.23.120.156",
        "login_page_url": "http://94.23.120.156/ints/login",
        "login_post_url": "http://94.23.120.156/ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "Gaza SMS": {
        "name": "Gaza SMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "modybasha12",
                "password": "modybasha12"
            }
        ],
        "base_url": "http://144.217.71.192",
        "login_page_url": "http://144.217.71.192/ints/login",
        "login_post_url": "http://144.217.71.192/ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "Km sms": {
        "name": "Km sms",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "http://",
        "login_page_url": "http:///ints/login",
        "login_post_url": "http:///ints/signin",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "Grand SMS": {
        "name": "Grand SMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "http://grand-panel.com",
        "login_page_url": "http://grand-panel.com/login",
        "login_post_url": "http://grand-panel.com/login",
        "ajax_path": "/ints/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    },
    "Purple SMS": {
        "name": "Purple SMS",
        "accounts": [
            {
                "id": str(uuid.uuid4()),
                "username": "",
                "password": ""
            }
        ],
        "base_url": "http://85.195.94.50",
        "login_page_url": "http://85.195.94.50/sms/SignIn",
        "login_post_url": "http://85.195.94.50/sms/SignIn",
        "ajax_path": "/sms/agent/res/data_smscdr.php",
        "check_interval": 5,
        "timeout": 30,
        "enabled": True
    }
}

def migrate_old_settings(settings):
    migrated = False
    for site_key in ["GROUP", "Fly sms", "Number_Panel", "Bolt", "iVASMS", "MSI", "proton SMS", "IMS", "Roxy SMS", "TimeSMS", "Konekta", "hadi", "fire", "Seven1Tel", "Gaza SMS", "Km sms", "Grand SMS", "Purple SMS"]:
        if site_key in settings:
            if "username" in settings[site_key] and "accounts" not in settings[site_key]:
                old_username = settings[site_key]["username"]
                old_password = settings[site_key]["password"]
                settings[site_key]["accounts"] = [
                    {
                        "id": str(uuid.uuid4()),
                        "username": old_username,
                        "password": old_password
                    }
                ]
                del settings[site_key]["username"]
                del settings[site_key]["password"]
                migrated = True
            
            if settings[site_key].get("check_interval", 5) == 7:
                settings[site_key]["check_interval"] = 5
                migrated = True
                print(f"✅ تحديث سرعة {site_key} من 7 إلى 5 ثواني")
    
    if "iVASMS" not in settings:
        settings["iVASMS"] = DEFAULT_SETTINGS["iVASMS"].copy()
        migrated = True
        print("✅ تم إضافة موقع iVASMS للإعدادات")
    
    if "MSI" not in settings:
        settings["MSI"] = DEFAULT_SETTINGS["MSI"].copy()
        migrated = True
    
    if "proton SMS" not in settings:
        settings["proton SMS"] = DEFAULT_SETTINGS["proton SMS"].copy()
        migrated = True
    
    if "IMS" not in settings:
        settings["IMS"] = DEFAULT_SETTINGS["IMS"].copy()
        migrated = True

    if "Roxy SMS" not in settings:
        settings["Roxy SMS"] = DEFAULT_SETTINGS["Roxy SMS"].copy()
        migrated = True

    if "TimeSMS" not in settings:
        settings["TimeSMS"] = DEFAULT_SETTINGS["TimeSMS"].copy()
        migrated = True

    if "Konekta" not in settings:
        settings["Konekta"] = DEFAULT_SETTINGS["Konekta"].copy()
        migrated = True

    if "hadi" not in settings:
        settings["hadi"] = DEFAULT_SETTINGS["hadi"].copy()
        migrated = True
        print("✅ تم إضافة موقع hadi للإعدادات")

    if "Seven1Tel" not in settings:
        settings["Seven1Tel"] = DEFAULT_SETTINGS["Seven1Tel"].copy()
    if "Gaza SMS" not in settings:
        settings["Gaza SMS"] = DEFAULT_SETTINGS["Gaza SMS"].copy()
        print("✅ تم إضافة موقع Gaza SMS للإعدادات")
        migrated = True
        print("✅ تم إضافة موقع Seven1Tel للإعدادات")

    if "Km sms" not in settings:
        settings["Km sms"] = DEFAULT_SETTINGS["Km sms"].copy()
        migrated = True
        print("✅ تم إضافة موقع Km sms للإعدادات")

    if "fire" not in settings:
        settings["fire"] = DEFAULT_SETTINGS["fire"].copy()
        migrated = True
        print("✅ تم إضافة موقع fire للإعدادات")

    if "Grand SMS" not in settings:
        settings["Grand SMS"] = DEFAULT_SETTINGS["Grand SMS"].copy()
        migrated = True
        print("✅ تم إضافة موقع Grand SMS للإعدادات")

    if "Purple SMS" not in settings:
        settings["Purple SMS"] = DEFAULT_SETTINGS["Purple SMS"].copy()
        migrated = True
        print("✅ تم إضافة موقع Purple SMS للإعدادات")
    
    if "Share" in settings and "proton SMS" not in settings:
        settings["proton SMS"] = settings["Share"].copy()
        settings["proton SMS"]["name"] = "proton SMS"
        del settings["Share"]
        migrated = True
    elif "Share" in settings:
        del settings["Share"]
        migrated = True
    
    return settings, migrated

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                settings, migrated = migrate_old_settings(settings)
                if migrated:
                    save_settings(settings)
                return settings
        except:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

def get_site_accounts(site_key):
    return SETTINGS.get(site_key, {}).get("accounts", [])

def add_account(site_key, username, password):
    if site_key not in SETTINGS:
        return False
    account = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password": password
    }
    if "accounts" not in SETTINGS[site_key]:
        SETTINGS[site_key]["accounts"] = []
    SETTINGS[site_key]["accounts"].append(account)
    save_settings(SETTINGS)
    return account

def delete_account(site_key, account_id):
    global account_stop_events
    if site_key not in SETTINGS or "accounts" not in SETTINGS[site_key]:
        return False
    accounts = SETTINGS[site_key]["accounts"]
    initial_count = len(accounts)
    SETTINGS[site_key]["accounts"] = [acc for acc in accounts if acc["id"] != account_id]
    if len(SETTINGS[site_key]["accounts"]) < initial_count:
        stop_key = f"{site_key}_{account_id}"
        if stop_key in account_stop_events:
            account_stop_events[stop_key].set()
            print(f"🛑 تم إيقاف مراقبة الحساب: {stop_key}")
            del account_stop_events[stop_key]
        
        cookies_file = f"cookies_{site_key}_{account_id}.pkl"
        last_message_file = f"last_message_{site_key}_{account_id}.txt"
        sent_messages_file = f"sent_messages_{site_key}_{account_id}.json"
        
        for file_path in [cookies_file, last_message_file, sent_messages_file]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"🗑️ تم حذف ملف: {file_path}")
                except Exception as e:
                    print(f"⚠️ خطأ في حذف {file_path}: {e}")
        
        if stop_key in account_sessions:
            del account_sessions[stop_key]
        if stop_key in account_last_seen:
            del account_last_seen[stop_key]
        
        save_settings(SETTINGS)
        return True
    return False

def get_account_by_id(site_key, account_id):
    accounts = get_site_accounts(site_key)
    for acc in accounts:
        if acc["id"] == account_id or acc["id"].startswith(account_id):
            return acc
    return None

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_sessions(sessions):
    with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)

SETTINGS = load_settings()
SESSIONS = load_sessions()

def get_first_account(site_key):
    accounts = get_site_accounts(site_key)
    return accounts[0] if accounts else {"username": "", "password": ""}

USERNAME = get_first_account("GROUP").get("username", "")
PASSWORD = get_first_account("GROUP").get("password", "")
BASE_URL = SETTINGS["GROUP"]["base_url"]
LOGIN_PAGE_URL = SETTINGS["GROUP"]["login_page_url"]
LOGIN_POST_URL = SETTINGS["GROUP"]["login_post_url"]
AJAX_PATH = SETTINGS["GROUP"]["ajax_path"]
HTTP_TIMEOUT = SETTINGS["GROUP"]["timeout"]
CHECK_INTERVAL = SETTINGS["GROUP"]["check_interval"]

USERNAME2 = get_first_account("Fly sms").get("username", "")
PASSWORD2 = get_first_account("Fly sms").get("password", "")
BASE_URL2 = SETTINGS["Fly sms"]["base_url"]
LOGIN_PAGE_URL2 = SETTINGS["Fly sms"]["login_page_url"]
LOGIN_POST_URL2 = SETTINGS["Fly sms"]["login_post_url"]
AJAX_PATH2 = SETTINGS["Fly sms"]["ajax_path"]
HTTP_TIMEOUT2 = SETTINGS["Fly sms"]["timeout"]
CHECK_INTERVAL2 = SETTINGS["Fly sms"]["check_interval"]

USERNAME3 = get_first_account("Number_Panel").get("username", "")
PASSWORD3 = get_first_account("Number_Panel").get("password", "")
BASE_URL3 = SETTINGS["Number_Panel"]["base_url"]
LOGIN_PAGE_URL3 = SETTINGS["Number_Panel"].get("login_page_url", "")
LOGIN_POST_URL3 = SETTINGS["Number_Panel"].get("login_post_url", "")
AJAX_PATH3 = SETTINGS["Number_Panel"].get("ajax_path", "")
HTTP_TIMEOUT3 = SETTINGS["Number_Panel"]["timeout"]
CHECK_INTERVAL3 = SETTINGS["Number_Panel"]["check_interval"]

USERNAME4 = get_first_account("Bolt").get("username", "")
PASSWORD4 = get_first_account("Bolt").get("password", "")
BASE_URL4 = SETTINGS["Bolt"]["base_url"]
LOGIN_PAGE_URL4 = SETTINGS["Bolt"]["login_page_url"]
LOGIN_POST_URL4 = SETTINGS["Bolt"]["login_post_url"]
AJAX_PATH4 = SETTINGS["Bolt"]["ajax_path"]
HTTP_TIMEOUT4 = SETTINGS["Bolt"]["timeout"]
CHECK_INTERVAL4 = SETTINGS["Bolt"]["check_interval"]

USERNAME5 = get_first_account("iVASMS").get("username", "")
PASSWORD5 = get_first_account("iVASMS").get("password", "")
IVASMS_API_URL = SETTINGS["iVASMS"].get("api_url", "https://maroon-wombat-183778.hostingersite.com/apiivasms/api.php")
IVASMS_API_KEY = get_first_account("iVASMS").get("api_key", "")
HTTP_TIMEOUT5 = SETTINGS["iVASMS"]["timeout"]
CHECK_INTERVAL5 = SETTINGS["iVASMS"]["check_interval"]
LOGIN_PAGE_URL5 = ""
LOGIN_POST_URL5 = ""
SMS_RECEIVED_URL5 = ""
GET_SMS_URL5 = ""
GET_SMS_NUMBER_URL5 = ""
GET_SMS_MESSAGE_URL5 = ""

USERNAME6 = get_first_account("MSI").get("username", "")
PASSWORD6 = get_first_account("MSI").get("password", "")
BASE_URL6 = SETTINGS["MSI"]["base_url"]
LOGIN_PAGE_URL6 = SETTINGS["MSI"]["login_page_url"]
LOGIN_POST_URL6 = SETTINGS["MSI"]["login_post_url"]
AJAX_PATH6 = SETTINGS["MSI"]["ajax_path"]
HTTP_TIMEOUT6 = SETTINGS["MSI"]["timeout"]
CHECK_INTERVAL6 = SETTINGS["MSI"]["check_interval"]

USERNAME7 = get_first_account("proton SMS").get("username", "")
PASSWORD7 = get_first_account("proton SMS").get("password", "")
BASE_URL7 = SETTINGS["proton SMS"]["base_url"]
LOGIN_PAGE_URL7 = SETTINGS["proton SMS"]["login_page_url"]
LOGIN_POST_URL7 = SETTINGS["proton SMS"]["login_post_url"]
AJAX_PATH7 = SETTINGS["proton SMS"]["ajax_path"]
HTTP_TIMEOUT7 = SETTINGS["proton SMS"]["timeout"]
CHECK_INTERVAL7 = SETTINGS["proton SMS"]["check_interval"]

USERNAME8 = get_first_account("IMS").get("username", "")
PASSWORD8 = get_first_account("IMS").get("password", "")
BASE_URL8 = SETTINGS["IMS"]["base_url"]
LOGIN_PAGE_URL8 = SETTINGS["IMS"]["login_page_url"]
LOGIN_POST_URL8 = SETTINGS["IMS"]["login_post_url"]
AJAX_PATH8 = SETTINGS["IMS"]["ajax_path"]
HTTP_TIMEOUT8 = SETTINGS["IMS"]["timeout"]
CHECK_INTERVAL8 = SETTINGS["IMS"]["check_interval"]

USERNAME9 = get_first_account("Roxy SMS").get("username", "")
PASSWORD9 = get_first_account("Roxy SMS").get("password", "")
BASE_URL9 = SETTINGS["Roxy SMS"]["base_url"]
LOGIN_PAGE_URL9 = SETTINGS["Roxy SMS"]["login_page_url"]
LOGIN_POST_URL9 = SETTINGS["Roxy SMS"]["login_post_url"]
AJAX_PATH9 = SETTINGS["Roxy SMS"]["ajax_path"]
HTTP_TIMEOUT9 = SETTINGS["Roxy SMS"]["timeout"]
CHECK_INTERVAL9 = SETTINGS["Roxy SMS"]["check_interval"]


USERNAME11 = get_first_account("Konekta").get("username", "")
PASSWORD11 = get_first_account("Konekta").get("password", "")
BASE_URL11 = SETTINGS["Konekta"]["base_url"]
LOGIN_PAGE_URL11 = SETTINGS["Konekta"]["login_page_url"]
LOGIN_POST_URL11 = SETTINGS["Konekta"]["login_post_url"]
AJAX_PATH11 = SETTINGS["Konekta"]["ajax_path"]
HTTP_TIMEOUT11 = SETTINGS["Konekta"]["timeout"]
CHECK_INTERVAL11 = SETTINGS["Konekta"]["check_interval"]

USERNAME10 = get_first_account("TimeSMS").get("username", "")
PASSWORD10 = get_first_account("TimeSMS").get("password", "")
BASE_URL10 = SETTINGS["TimeSMS"]["base_url"]
LOGIN_PAGE_URL10 = SETTINGS["TimeSMS"]["login_page_url"]
LOGIN_POST_URL10 = SETTINGS["TimeSMS"]["login_post_url"]
AJAX_PATH10 = SETTINGS["TimeSMS"]["ajax_path"]
HTTP_TIMEOUT10 = SETTINGS["TimeSMS"]["timeout"]
CHECK_INTERVAL10 = SETTINGS["TimeSMS"]["check_interval"]

USERNAME12 = get_first_account("hadi").get("username", "")
PASSWORD12 = get_first_account("hadi").get("password", "")
BASE_URL12 = SETTINGS["hadi"]["base_url"]
LOGIN_PAGE_URL12 = SETTINGS["hadi"]["login_page_url"]
LOGIN_POST_URL12 = SETTINGS["hadi"]["login_post_url"]
AJAX_PATH12 = SETTINGS["hadi"]["ajax_path"]
HTTP_TIMEOUT12 = SETTINGS["hadi"]["timeout"]
CHECK_INTERVAL12 = SETTINGS["hadi"]["check_interval"]

USERNAME13 = get_first_account("fire").get("username", "")
USERNAME14 = get_first_account("Seven1Tel").get("username", "")
PASSWORD14 = get_first_account("Seven1Tel").get("password", "")
BASE_URL14 = SETTINGS["Seven1Tel"]["base_url"]
LOGIN_PAGE_URL14 = SETTINGS["Seven1Tel"]["login_page_url"]
LOGIN_POST_URL14 = SETTINGS["Seven1Tel"]["login_post_url"]
AJAX_PATH14 = SETTINGS["Seven1Tel"]["ajax_path"]
HTTP_TIMEOUT14 = SETTINGS["Seven1Tel"]["timeout"]
CHECK_INTERVAL14 = SETTINGS["Seven1Tel"]["check_interval"]

USERNAME15 = get_first_account("Gaza SMS").get("username", "")
PASSWORD15 = get_first_account("Gaza SMS").get("password", "")
BASE_URL15 = SETTINGS["Gaza SMS"]["base_url"]
LOGIN_PAGE_URL15 = SETTINGS["Gaza SMS"]["login_page_url"]
LOGIN_POST_URL15 = SETTINGS["Gaza SMS"]["login_post_url"]
AJAX_PATH15 = SETTINGS["Gaza SMS"]["ajax_path"]
HTTP_TIMEOUT15 = SETTINGS["Gaza SMS"]["timeout"]
CHECK_INTERVAL15 = SETTINGS["Gaza SMS"]["check_interval"]
is_logged_in_site15 = False
session15 = requests.Session()
session15.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

USERNAME16 = get_first_account("Km sms").get("username", "")
PASSWORD16 = get_first_account("Km sms").get("password", "")
BASE_URL16 = SETTINGS["Km sms"]["base_url"]
LOGIN_PAGE_URL16 = SETTINGS["Km sms"]["login_page_url"]
LOGIN_POST_URL16 = SETTINGS["Km sms"]["login_post_url"]
AJAX_PATH16 = SETTINGS["Km sms"]["ajax_path"]
HTTP_TIMEOUT16 = SETTINGS["Km sms"]["timeout"]
CHECK_INTERVAL16 = SETTINGS["Km sms"]["check_interval"]

USERNAME17 = get_first_account("Grand SMS").get("username", "")
PASSWORD17 = get_first_account("Grand SMS").get("password", "")
BASE_URL17 = SETTINGS["Grand SMS"]["base_url"]
LOGIN_PAGE_URL17 = SETTINGS["Grand SMS"]["login_page_url"]
LOGIN_POST_URL17 = SETTINGS["Grand SMS"]["login_post_url"]
AJAX_PATH17 = SETTINGS["Grand SMS"]["ajax_path"]
HTTP_TIMEOUT17 = SETTINGS["Grand SMS"]["timeout"]
CHECK_INTERVAL17 = SETTINGS["Grand SMS"]["check_interval"]

USERNAME18 = get_first_account("Purple SMS").get("username", "")
PASSWORD18 = get_first_account("Purple SMS").get("password", "")
BASE_URL18 = SETTINGS["Purple SMS"]["base_url"]
LOGIN_PAGE_URL18 = SETTINGS["Purple SMS"]["login_page_url"]
LOGIN_POST_URL18 = SETTINGS["Purple SMS"]["login_post_url"]
AJAX_PATH18 = SETTINGS["Purple SMS"]["ajax_path"]
HTTP_TIMEOUT18 = SETTINGS["Purple SMS"]["timeout"]
CHECK_INTERVAL18 = SETTINGS["Purple SMS"]["check_interval"]

PASSWORD13 = get_first_account("fire").get("password", "")
BASE_URL13 = SETTINGS["fire"]["base_url"]
LOGIN_PAGE_URL13 = SETTINGS["fire"]["login_page_url"]
LOGIN_POST_URL13 = SETTINGS["fire"]["login_post_url"]
AJAX_PATH13 = SETTINGS["fire"]["ajax_path"]
HTTP_TIMEOUT13 = SETTINGS["fire"]["timeout"]
CHECK_INTERVAL13 = SETTINGS["fire"]["check_interval"]

COOKIES_FILE = "cookies.pkl"
COOKIES_FILE_SITE3 = "cookies_site3.pkl"
COOKIES_FILE_SITE4 = "cookies_site4.pkl"
COOKIES_FILE_SITE5 = "cookies_ivasms.json"
COOKIES_FILE_SITE6 = "cookies_msi.pkl"
COOKIES_FILE_SITE7 = "cookies_share.pkl"
COOKIES_FILE_SITE8 = "cookies_ims.pkl"
COOKIES_FILE_SITE9 = "cookies_roxy.pkl"
COOKIES_FILE_SITE10 = "cookies_timesms.pkl"
COOKIES_FILE_SITE10 = "cookies_timesms.pkl"
LAST_MESSAGE_FILE = "last_message.txt"
LAST_MESSAGE_FILE_SITE2 = "last_message_site2.txt"
LAST_MESSAGE_FILE_SITE3 = "last_message_site3.txt"
LAST_MESSAGE_FILE_SITE4 = "last_message_site4.txt"
LAST_MESSAGE_FILE_SITE5 = "last_message_ivasms.txt"
LAST_MESSAGE_FILE_SITE6 = "last_message_msi.txt"
LAST_MESSAGE_FILE_SITE7 = "last_message_share.txt"
LAST_MESSAGE_FILE_SITE8 = "last_message_ims.txt"
LAST_MESSAGE_FILE_SITE9 = "last_message_roxy.txt"
LAST_MESSAGE_FILE_SITE10 = "last_message_timesms.txt"
LAST_MESSAGE_FILE_SITE10 = "last_message_timesms.txt"

account_scrapers = {}
account_sessions = {}
account_last_seen = {}
account_stop_events = {}

IDX_DATE_SITE3 = 0
IDX_NUMBER_SITE3 = 2
IDX_SMS_SITE3 = 5

def create_session_group():
    
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })
    return sess

session1 = create_session_group()
is_logged_in_site1 = False
bot = telebot.TeleBot(BOT_TOKEN)
last_seen_key = ""
last_seen_key_site2 = ""
last_seen_key_site3 = ""
last_seen_key_site4 = ""

account_sessions = {}

session2 = requests.Session()
session2.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL2 + "/ints/agent/SMSCDRReports",
    "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8"
})
is_logged_in_site2 = False
sesskey_site2 = None # متغير عالمي لتخزين sesskey لـ Fly sms

session3 = requests.Session()
session3.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
})
is_logged_in_site3 = False

session4 = requests.Session()
session4.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
})
is_logged_in_site4 = False

session6 = requests.Session()
session6.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL6 + "/agent/SMSCDRReports",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
})
is_logged_in_site6 = False
last_seen_key_site6 = ""

session7 = requests.Session()
session7.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL7 + "/agent/SMSCDRReports",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
})
is_logged_in_site7 = False
last_seen_key_site7 = ""

session8 = requests.Session()
session8.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
})
is_logged_in_site8 = False
last_seen_key_site8 = ""

session9 = requests.Session()
session9.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
})
is_logged_in_site9 = False
last_seen_key_site9 = ""


session11 = requests.Session()
session11.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})
is_logged_in_site11 = False
last_seen_key_site11 = ""

session12 = requests.Session()
session12.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL12 + "/ints/agent/SMSCDRReports",
    "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8"
})
is_logged_in_site12 = False
last_seen_key_site12 = ""

session13 = requests.Session()
session13.headers.update({
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL13 + "/ints/agent/SMSCDRReports",
    "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8"
})
is_logged_in_site13 = False
last_seen_key_site13 = ""
session10 = requests.Session()
session10.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})
is_logged_in_site10 = False
last_seen_key_site10 = ""

session14 = requests.Session()
session14.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL14 + "/ints/agent/SMSCDRReports",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
})
is_logged_in_site14 = False
last_seen_key_site14 = ""

session5 = requests.Session()
session5.verify = False
session5.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive"
})
is_logged_in_site5 = False
csrf_token_site5 = None
last_seen_key_site5 = ""

COUNTRIES_FILE = "countriesi.json"
CHANNELS_FILE = "channelsi.json"
SUBSCRIPTION_IMAGE_FILE = "sub_image.json"
SUBSCRIPTION_SETTINGS_FILE = "sub_settings.json"
USERS_FILE = "usersiy.json"
ADMINS_FILE = "admins.ijson"
BANNED_FILE = "bannedi.json"
OTP_GROUP_FILE = "otp_groupi.json"
GROUPS_FILE = "groupsi.json"
STATISTICS_FILE = "statisticsi.json"
REFERRALS_FILE = "referralsi.json"
REFERRAL_SETTINGS_FILE = "referral_settings.json"
WITHDRAWAL_REQUESTS_FILE = "withdrawal_requests.json"
WITHDRAWAL_METHODS_FILE = "withdrawal_methods.json"
WELCOME_MESSAGES_FILE = "welcome_messages.json"
NUMBERS_ADMINS_FILE = "numbers_admins.json"
COUNTRIES = {}
CHANNELS = []
USERS = {}
number_color_state = {}
ADMINS = [8512662719]
BANNED = []
OTP_GROUP = -1003953419808
GROUPS = []
REFERRALS = {}
NUMBERS_ADMINS = []

def load_numbers_admins():
    global NUMBERS_ADMINS
    if os.path.exists(NUMBERS_ADMINS_FILE):
        try:
            with open(NUMBERS_ADMINS_FILE, "r", encoding="utf-8") as f:
                NUMBERS_ADMINS = json.load(f)
        except:
            NUMBERS_ADMINS = []
    return NUMBERS_ADMINS

def save_numbers_admins():
    with open(NUMBERS_ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(NUMBERS_ADMINS, f, indent=2, ensure_ascii=False)

def is_numbers_admin(user_id):
    return user_id in NUMBERS_ADMINS or is_admin(user_id)

DEFAULT_REFERRAL_SETTINGS = {
    "codes_required_for_referral": 5,
    "referral_bonus": 0.05,
    "code_bonus": 0.003,
    "min_withdrawal": 18.0,
    "enabled": True
}

DEFAULT_WELCOME_MESSAGES = {
    "ar": (
        "<b><tg-emoji emoji-id='5112033864277033811'>✅</tg-emoji></b><b> ~ بوت الأرقام المؤقتة </b><b><tg-emoji emoji-id='5116309444090661129'>🏴‍☠️</tg-emoji></b>\n\n"
        "<tg-emoji emoji-id='5219711713749788252'>🏴‍☠️</tg-emoji> <b>مرحباً بك في أفضل بوت للأرقام المؤقتة! </b><b><tg-emoji emoji-id='5931344368282636710'>🔥</tg-emoji></b>\n\n"
        "• <tg-emoji emoji-id='5366201992970518798'>🛟</tg-emoji> <b>المميزات :~</b>\n"
        "  <tg-emoji emoji-id='5116093437300442328'>⚡️</tg-emoji> <b>استلام الأكواد بسرعة</b>\n"
        "  <tg-emoji emoji-id='5116599934203724812'>🧠</tg-emoji> <b>عدة دول</b>\n"
        "  <tg-emoji emoji-id='5116517977637782262'>🫣</tg-emoji> <b>أرقام خاصة</b>\n"
        "  <tg-emoji emoji-id='5123344136665039833'>♻️</tg-emoji> <b>خدمات مصنفة</b>\n"
        "  <tg-emoji emoji-id='5123248930124989216'>✅</tg-emoji> <b>سهل الاستخدام</b>\n\n"
        "• <tg-emoji emoji-id='5472111548572900003'>⌨️</tg-emoji> <b>المطور ~ </b><b>@MA_X_001</b>\n\n"
        "<b><tg-emoji emoji-id='5298877105000439431'>🥢</tg-emoji></b><b> ~ اختر الخدمة ~</b>"
    ),
    "en": (
        "<b><tg-emoji emoji-id='5112033864277033811'>✅</tg-emoji></b><b> ~ MA-X BOT </b><b><tg-emoji emoji-id='5116309444090661129'>🏴‍☠️</tg-emoji></b>\n\n"
        "• <tg-emoji emoji-id='5219711713749788252'>🏴‍☠️</tg-emoji> <b>Welcome To The Best OTP Bot! </b><b><tg-emoji emoji-id='5931344368282636710'>🔥</tg-emoji></b>\n\n"
        "• <tg-emoji emoji-id='5366201992970518798'>🛟</tg-emoji> <b>Features :~</b>\n"
        "  <tg-emoji emoji-id='5116093437300442328'>⚡️</tg-emoji> <b>Fast OTP Receiving</b>\n"
        "  <tg-emoji emoji-id='5116599934203724812'>🧠</tg-emoji> <b>Multiple Countries</b>\n"
        "  <tg-emoji emoji-id='5116517977637782262'>🫣</tg-emoji> <b>Private Numbers</b>\n"
        "  <tg-emoji emoji-id='5123344136665039833'>♻️</tg-emoji> <b>Categorized Services</b>\n"
        "  <tg-emoji emoji-id='5123248930124989216'>✅</tg-emoji> <b>Easy To Use</b>\n\n"
        "• <tg-emoji emoji-id='5472111548572900003'>⌨️</tg-emoji> <b>Developer ~ </b><b>@YS_9N</b>\n\n"
        "• <tg-emoji emoji-id='5298877105000439431'>🥢</tg-emoji> <b>Choose Service Category ~</b>"
    )
}

DEFAULT_BUTTON_LINKS = {
    "group_link": "https://t.me/UltronX_MegaBo",
    "channel_link": "https://t.me/TXA_V",
}

BUTTON_LINKS_FILE = "button_links.json"
OTP_BUTTONS_FILE = "otp_buttons.json"

DEFAULT_OTP_BUTTONS = [
    {"name": "Number Chaanel", "url": "https://t.me/TXA_V"},
    {"name": "Bot Panel", "url": "https://t.me/Sms_Arabawy_bot"}
]

def load_otp_buttons():
    if os.path.exists(OTP_BUTTONS_FILE):
        try:
            with open(OTP_BUTTONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_OTP_BUTTONS.copy()

def save_otp_buttons(buttons):
    with open(OTP_BUTTONS_FILE, "w", encoding="utf-8") as f:
        json.dump(buttons, f, indent=2, ensure_ascii=False)

OTP_BUTTONS = load_otp_buttons()

def format_decimal(value):
    
    if value == 0:
        return "0"
    
    formatted = f"{value:.10f}".rstrip('0').rstrip('.')
    
    if '.' in formatted:
        integer_part, decimal_part = formatted.split('.')
        if len(decimal_part) > 5:
            decimal_part = decimal_part[:5]
        return f"{integer_part}.{decimal_part}"
    return formatted

def load_button_links():
    if os.path.exists(BUTTON_LINKS_FILE):
        try:
            with open(BUTTON_LINKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_BUTTON_LINKS.copy()

def save_button_links(links):
    with open(BUTTON_LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(links, f, indent=2, ensure_ascii=False)

BUTTON_LINKS = load_button_links()
STATISTICS = {
    "total_codes": 0,
    "codes_today": 0,
    "codes_this_week": 0,
    "codes_this_month": 0,
    "last_reset_day": None,
    "last_reset_week": None,
    "last_reset_month": None,
    "daily_history": {}
}

user_states = {}
broadcast_state = {}
change_number_cooldown = {}  # {user_id: last_change_timestamp}

TEXTS = {
    "ar": {
        "welcome": "🌐 <b>مرحباً بك في بوت الأرقام!</b>",
        "instructions": "📖 <b>دليل البوت</b>\n\n<b>📱 استلام الأكواد:</b>\n1️⃣ اضغط Take a number\n2️⃣ اختر الدولة والرقم\n3️⃣ استخدم الرقم للتسجيل\n4️⃣ الكود يصلك تلقائياً\n\n<b>💰 الأرباح:</b>\n• بونص عن كل كود\n• بونص إحالة الأصدقاء\n\n<b>💵 السحب:</b>\nفودافون كاش - USDT - Binance",
        "subscription_locked": "🔒 <b>الوصول مقفل. انضم للقنوات ثم تحقق.</b>",
        "subscription_verified": "✅ <b>تم التحقق من الاشتراك!</b>\n\n🌐 <b>مرحباً بك في بوت الأرقام!</b>",
        "subscription_not_verified": "❌ لم تنضم لجميع القنوات بعد!",
        "choose_country": "📲 𝗧𝗮𝗸𝗲 𝗮 𝗻𝘂𝗺𝗯𝗲𝗿",
        "my_account": "👤 𝗠𝘆 𝗔𝗰𝗰𝗼𝘂𝗻𝘁",
        "admin_panel": "🎛 لوحة الإدارة",
        "help": "❓ مساعدة",
        "verify_subscription": "✅ تحقق من الاشتراك",
        "banned": "🚫 أنت محظور من استخدام هذا البوت.",
        "unauthorized": "❌ غير مصرح لك!",
        "select_country": "📱 <b>اختر المنصة:</b>",
        "back": "🔙 رجوع",
        "select_number": "📞 <b>اختر رقم لـ {country}:</b>",
        "number_locked": "⚠️ هذا الرقم مستخدم حالياً من شخص آخر. اختر رقم آخر.",
        "your_number": "📞 <b>رقمك لـ {country}:</b>\n<code>+{number}</code>\n\n⏳ <b>في انتظار الكود...</b> 📱\n\n💬 سيتم إرسال الكود هنا مباشرة!",
        "change_number": "🔄 تغيير الرقم",
        "change_country": "🌍 تغيير الدولة",
        "account_info": "👤 <b>معلومات حسابك:</b>\n\n🆔 <b>معرفك:</b> <code>{user_id_value}</code>\n📅 <b>تاريخ الانضمام:</b> {join_date}\n📊 <b>الأكواد المستلمة:</b> {activations}\n🌐 <b>اللغة:</b> {language}\n\n💡 <b>حالة رقمك:</b>\n{number_status}",
        "no_number": "❌ لا يوجد رقم حالياً",
        "has_number": "✅ رقم نشط لـ {country}",
        "change_language": "🌐 تغيير اللغة",
        "language_changed": "✅ تم تغيير اللغة إلى العربية",
        "add_channel": "➕ إضافة قناة اشتراك",
        "remove_channel": "🗑 حذف قناة",
        "statistics": "📊 الإحصائيات",
        "broadcast": "📣 إذاعة",
        "add_admin": "🔧 إضافة مشرف",
        "remove_admin": "🗑 حذف مشرف",
        "ban_user": "🚫 حظر مستخدم",
        "unban_user": "✅ إلغاء حظر",
        "set_otp_group": "📱 تعيين مجموعة OTP",
        "close": "❌ إغلاق",
        "new_code": "🔔 <b>كود جديد!</b>\n\n📞 <b>الرقم:</b> <code>+{number}</code>\n💬 <b>الكود:</b> <code>{code}</code>\n\n⏰ <b>الوقت:</b> {time}",
        "no_countries_available": "❌ لا توجد دول متاحة حالياً!",
        "country_not_available": "❌ دولة غير متاحة!",
        "no_numbers_available": "❌ لا توجد أرقام متاحة!",
        "number_reserved": "❌ هذا الرقم محجوز حالياً!",
        "select_country_first": "❌ اختر المنصة أولاً!",
        "number_changed": "✅ تم تغيير الرقم!",
        "admin_panel_title": "🎛 <b>لوحة الإدارة</b>",
        "statistics_title": "📊 <b>إحصائيات البوت</b>\n\n👥 <b>إجمالي المستخدمين:</b> {users_count}\n🔢 <b>إجمالي الأكواد:</b> {total_codes}\n\n📅 <b>أكواد اليوم:</b> {codes_today}\n📆 <b>أكواد هذا الأسبوع:</b> {codes_this_week}\n📊 <b>أكواد هذا الشهر:</b> {codes_this_month}",
        "broadcast_prompt": "📣 <b>إذاعة رسالة</b>\n\nأرسل الرسالة التي تريد إذاعتها لجميع المستخدمين:",
        "broadcast_sent": "✅ <b>تم الإرسال!</b>\n\n📤 نجح: {success}\n❌ فشل: {failed}",
        "set_otp_group_prompt": "📱 <b>تعيين مجموعة OTP</b>\n\nأرسل معرف المجموعة (Group ID) التي تريد إرسال الأكواد إليها:",
        "otp_group_set": "✅ <b>تم تعيين مجموعة OTP!</b>\n\n🆔 Group ID: <code>{group_id}</code>",
        "invalid_id": "❌ معرف غير صحيح! أرسل رقم ID صحيح",
        "add_channel_id_prompt": "➕ <b>إضافة قناة اشتراك إجباري</b>\n\n⚠️ يقبل فقط القنوات (لا مجموعات)\n\nأرسل معرف أو رابط القناة:\n• @channel_name\n• https://t.me/channel_name",
        "add_channel_name_prompt": "",
        "add_channel_url_prompt": "",
        "channel_added": "✅ <b>تم إضافة القناة!</b>\n\n📢 القناة: {channel_name}\n🔗 الرابط: {channel_url}",
        "user_banned": "✅ <b>تم حظر المستخدم!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "user_unbanned": "✅ <b>تم إلغاء حظر المستخدم!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "admin_added": "✅ <b>تم إضافة المشرف!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "admin_removed": "✅ <b>تم حذف المشرف!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "channel_removed": "✅ <b>تم حذف القناة!</b>\n\n📢 القناة: {channel_name}",
        "no_channels": "⚠️ لا توجد قنوات!",
        "no_banned_users": "⚠️ لا يوجد مستخدمون محظورون!",
        "no_admins": "⚠️ لا يوجد مشرفون!",
        "owner_only": "❌ هذه الميزة للمالك فقط!",
        "ban_user_prompt": "🚫 <b>حظر مستخدم</b>\n\nأرسل معرف المستخدم (User ID) الذي تريد حظره:",
        "unban_user_prompt": "✅ <b>إلغاء حظر مستخدم</b>\n\n📋 <b>المستخدمون المحظورون:</b>\n{banned_list}\n\nأرسل معرف المستخدم لإلغاء حظره:",
        "add_moderator_prompt": "🔧 <b>إضافة مشرف</b>\n\nأرسل معرف المستخدم (User ID) الذي تريد جعله مشرفاً:",
        "remove_moderator_prompt": "🗑 <b>حذف مشرف</b>\n\n📋 <b>المشرفون الحاليون:</b>\n{admins_list}\n\nأرسل معرف المشرف لحذفه:",
        "remove_channel_prompt": "🗑 <b>حذف قناة</b>\n\n📋 <b>القنوات الحالية:</b>\n{channels_list}\n\nأرسل رقم القناة أو معرفها لحذفها:",
        "channel_not_found": "❌ قناة غير موجودة!",
        "otp_group_status": "📱 <b>مجموعة الأكواد:</b>\n{status}",
        "otp_group_set_status": "✅ مجموعة محددة: <code>{group_id}</code>",
        "otp_group_not_set": "❌ لم يتم تحديد مجموعة",
        "delete_otp_group": "🗑 حذف المجموعة",
        "otp_group_deleted": "✅ تم حذف مجموعة الأكواد!",
        "top_users": "👥 أفضل 10 مستخدمين",
        "top_users_title": "👥 <b>أفضل 10 مستخدمين</b>\n<i>حسب عدد الأكواد المستلمة</i>\n\n",
        "no_users_yet": "⚠️ لا يوجد مستخدمون بعد!",
        "user_joined": "🎉 <b>انضم مستخدم جديد!</b>\n\n👤 الاسم: {name}\n🆔 ID: <code>{user_id}</code>\n📅 الوقت: {time}",
        "edit_button_labels_ar": "<tg-emoji emoji-id='5294163983983463099'>🇸🇦</tg-emoji> تعديل الأزرار بالعربية",
        "edit_button_labels_en": "<tg-emoji emoji-id='5293993521026453119'>🇬🇧</tg-emoji> تعديل الأزرار بالإنجليزية",
        "edit_button_labels_lang": "🏷️ <b>تعديل أسماء الأزرار</b>\n\nاختر اللغة:",
        "edit_labels_ar_menu": "<tg-emoji emoji-id='5294163983983463099'>🇸🇦</tg-emoji> <b>تعديل الأزرار بالعربية</b>\n\nاختر الزر الذي تريد تعديله:",
        "edit_labels_en_menu": "<tg-emoji emoji-id='5293993521026453119'>🇬🇧</tg-emoji> <b>Edit Button Labels (English)</b>\n\nChoose the button you want to edit:",
        "edit_choose_country_ar": "تعديل \"اختر دولة\"",
        "edit_my_account_ar": "تعديل \"حسابي\"",
        "edit_help_ar": "تعديل \"𝗛𝗲𝗹𝗽❓\"",
        "edit_choose_country_en": "Edit \"Choose Country\"",
        "edit_my_account_en": "Edit \"My Account\"",
        "edit_help_en": "Edit \"Help\"",
        "send_new_label": "📝 أرسل الاسم الجديد للزر:",
        "label_updated": "✅ تم تحديث اسم الزر بنجاح!",
        "manage_otp_group": "📱 إدارة مجموعة الأكواد",
        "welcome_admin": "🌐 <b>مرحباً بك في بوت OTP!</b>\n\nاختر دولة لاستقبال رقم وانتظر الأكواد.\n\nكمشرف، يمكنك أيضاً الوصول للوحة الأدمن.",
        "choose_language": "🌍 <b>اختر اللغة / Choose Language</b>",
        "group_hello_admin": "👋 مرحباً! أنا بوت OTP.\n\n⚠️ <b>ملاحظة:</b> لا يمكن إضافة الجروبات تلقائياً.\nيجب على المشرف إضافة هذا الجروب من لوحة الأدمن.",
        "group_hello": "👋 مرحباً! أنا بوت OTP.\n\nللاستخدام، تواصل معي بشكل خاص.",
        "total_users": "👥 <b>إجمالي المستخدمين:</b>",
        "total_codes": "🔢 <b>إجمالي الأكواد:</b>",
        "codes_today": "📅 <b>أكواد اليوم:</b>",
        "codes_week": "📆 <b>أكواد هذا الأسبوع:</b>",
        "codes_month": "📊 <b>أكواد هذا الشهر:</b>",
        "users_text": "users / مستخدم",
        "developer_btn": "🆘 المطور",
        "verify_btn": "✅ تحقق",
        "select_server_title": "🖥️ <b>اختر السيرفر</b>",
        "select_server_desc": "📌 كل سيرفر يحتوي على مجموعة مختلفة من الدول والأرقام:",
        "select_server_hint": "🔻 <i>اختر السيرفر لعرض الدول المتاحة</i>",
        "select_platform_title": "📱 <b>اختر المنصة في {server}</b>",
        "select_platform_hint": "🔻 <i>اختر المنصة التي تريد استقبال أكوادها</i>",
        "no_numbers_here": "❌ <b>لا يوجد أرقام هنا</b>",
        "no_countries_title": "❌ <b>لا توجد دول متاحة</b>",
        "server_label": "🖥️ <b>السيرفر:</b>",
        "platform_label": "📱 <b>المنصة:</b>",
        "no_countries_hint": "🔻 <i>لا توجد دول متاحة لهذه المنصة في هذا السيرفر حالياً</i>",
        "available_countries_title": "🌍 <b>الدول المتاحة</b>",
        "select_country_hint": "🔻 <i>اختر الدولة التي تريد استقبال أكوادها</i>",
        "number_selected_success": "✅ <b>تم اختيار الرقم بنجاح!</b>",
        "waiting_for_code": "⏳ 𝓦𝓪𝓲𝓽𝓲𝓷𝓰 𝓯𝓸𝓻 𝓽𝓱𝓮 𝓬𝓸𝓭𝓮... 📱",
        "code_will_be_sent": "سيتم إرسال الكود لك مباشرة عند وصوله!",
        "change_number_btn": "🔄 تغيير الرقم",
        "change_country_btn": "🌍 تغيير الدولة",
        "back_to_servers": "𝗕𝗮𝗰𝗸 𝘁𝗼 𝘀𝗲𝗿𝘃𝗲𝗿𝘀",
        "error_msg": "❌ خطأ: {error}",
        "referral_success": "🎉 <b>تم تسجيلك بنجاح عبر رابط الإحالة!</b>\n\nاستمتع باستخدام البوت!"
    },
    "en": {
        "welcome": "╔════✦  𝓑𝓞𝓣𝓟  ✦════╗\n\n❖  𝗚𝗿𝗮𝗯 𝗮 𝘁𝗲𝗺𝗽𝗼𝗿𝗮𝗿𝘆 𝗻𝘂𝗺𝗯𝗲𝗿 𝗶𝗻𝘀𝘁𝗮𝗻𝘁𝗹𝘆\n❖  𝗟𝗶𝗴𝗵𝘁𝗻𝗶𝗻𝗴-𝗳𝗮𝘀𝘁 & 𝗳𝘂𝗹𝗹𝘆 𝘀𝗲𝗰𝘂𝗿𝗲\n❖  𝗪𝗼𝗿𝗸𝘀 𝗳𝗼𝗿 𝗮𝗹𝗹 𝗰𝗼𝘂𝗻𝘁𝗿𝗶𝗲𝘀\n\n•  𝗦𝗲𝗹𝗲𝗰𝘁 𝘆𝗼𝘂𝗿 𝗰𝗼𝘂𝗻𝘁𝗿𝘆\n•  𝗚𝗲𝘁 𝘆𝗼𝘂𝗿 𝗻𝘂𝗺𝗯𝗲𝗿 𝗶𝗺𝗺𝗲𝗱𝗶𝗮𝘁𝗲𝗹𝘆\n\n╚════✦  𝓑𝓞𝓣𝓟  ✦════╝",
        "instructions": "📖 <b>Bot Guide</b>\n\n<b>📱 Receiving Codes:</b>\n1️⃣ Click Take a number\n2️⃣ Choose country and number\n3️⃣ Use number to register\n4️⃣ Code arrives automatically\n\n<b>💰 Earnings:</b>\n• Bonus for each code\n• Referral bonus for friends\n\n<b>💵 Withdrawal:</b>\nVodafone Cash - USDT - Binance",
        "subscription_locked": "🔒 <b>Access locked. Join channels then verify.</b>",
        "subscription_verified": "✅ <b>Subscription verified!</b>\n\n🌐 <b>Welcome to Numbers Bot!</b>",
        "subscription_not_verified": "❌ You haven't joined all channels yet!",
        "choose_country": "📲 𝗧𝗮𝗸𝗲 𝗮 𝗻𝘂𝗺𝗯𝗲𝗿",
        "my_account": "👤 𝗠𝘆 𝗔𝗰𝗰𝗼𝘂𝗻𝘁",
        "admin_panel": "🎛 Admin Panel",
        "help": "❓ Help",
        "verify_subscription": "✅ Verify Subscription",
        "banned": "🚫 You are banned from using this bot.",
        "unauthorized": "❌ Unauthorized!",
        "select_country": "🌍 <b>Select Country:</b>",
        "back": "🔙 Back",
        "select_number": "📞 <b>Select a number for {country}:</b>",
        "number_locked": "⚠️ This number is currently used by someone else. Choose another number.",
        "your_number": "📞 <b>Your number for {country}:</b>\n<code>+{number}</code>\n\n⏳ <b>Waiting for code...</b> 📱\n\n💬 Code will be sent here directly!",
        "change_number": " Change Number",
        "change_country": " Change Country",
        "account_info": "👤 <b>Your Account Info:</b>\n\n🆔 <b>ID:</b> <code>{user_id_value}</code>\n📅 <b>Join Date:</b> {join_date}\n📊 <b>Codes Received:</b> {activations}\n🌐 <b>Language:</b> {language}\n\n💡 <b>Number Status:</b>\n{number_status}",
        "no_number": "❌ No number currently",
        "has_number": "✅ Active number for {country}",
        "change_language": "🌐 Change Language",
        "language_changed": "✅ Language changed to English",
        "add_channel": "➕ Add Channel",
        "remove_channel": "🗑 Remove Channel",
        "statistics": "📊 Statistics",
        "broadcast": "📣 Broadcast",
        "add_admin": "🔧 Add Admin",
        "remove_admin": "🗑 Remove Admin",
        "ban_user": "🚫 Ban User",
        "unban_user": "✅ Unban User",
        "set_otp_group": "📱 Set OTP Group",
        "close": "❌ Close",
        "new_code": "🔔 <b>New Code!</b>\n\n📞 <b>Number:</b> <code>+{number}</code>\n💬 <b>Code:</b> <code>{code}</code>\n\n⏰ <b>Time:</b> {time}",
        "no_countries_available": "❌ No countries available!",
        "country_not_available": "❌ Country not available!",
        "no_numbers_available": "❌ No numbers available!",
        "number_reserved": "❌ This number is reserved!",
        "select_country_first": "❌ Select a country first!",
        "number_changed": "✅ Number changed!",
        "admin_panel_title": "🎛 <b>Admin Panel</b>",
        "statistics_title": "📊 <b>Bot Statistics</b>\n\n👥 <b>Total Users:</b> {users_count}\n🔢 <b>Total Codes:</b> {total_codes}\n\n📅 <b>Today's Codes:</b> {codes_today}\n📆 <b>This Week's Codes:</b> {codes_this_week}\n📊 <b>This Month's Codes:</b> {codes_this_month}",
        "broadcast_prompt": "📣 <b>Broadcast Message</b>\n\nSend the message you want to broadcast to all users:",
        "broadcast_sent": "✅ <b>Sent!</b>\n\n📤 Success: {success}\n❌ Failed: {failed}",
        "set_otp_group_prompt": "📱 <b>Set OTP Group</b>\n\nSend the Group ID where you want to receive OTP codes:",
        "otp_group_set": "✅ <b>OTP Group set!</b>\n\n🆔 Group ID: <code>{group_id}</code>",
        "invalid_id": "❌ Invalid ID! Send a valid ID number",
        "add_channel_id_prompt": "➕ <b>Add Subscription Channel</b>\n\nSend the channel ID (example: @channelname or -100...):",
        "add_channel_name_prompt": "✅ <b>Channel ID saved!</b>\n\nNow send the channel name:",
        "add_channel_url_prompt": "✅ <b>Channel name saved!</b>\n\nNow send the channel link (https://t.me/...):",
        "channel_added": "✅ <b>Channel added!</b>\n\n📢 Channel: {channel_name}\n🔗 Link: {channel_url}",
        "user_banned": "✅ <b>User banned!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "user_unbanned": "✅ <b>User unbanned!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "admin_added": "✅ <b>Admin added!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "admin_removed": "✅ <b>Admin removed!</b>\n\n🆔 User ID: <code>{target_user_id}</code>",
        "channel_removed": "✅ <b>Channel removed!</b>\n\n📢 Channel: {channel_name}",
        "no_channels": "⚠️ No channels!",
        "no_banned_users": "⚠️ No banned users!",
        "no_admins": "⚠️ No admins!",
        "owner_only": "❌ This feature is for owner only!",
        "ban_user_prompt": "🚫 <b>Ban User</b>\n\nSend the User ID you want to ban:",
        "unban_user_prompt": "✅ <b>Unban User</b>\n\n📋 <b>Banned Users:</b>\n{banned_list}\n\nSend the User ID to unban:",
        "add_moderator_prompt": "🔧 <b>Add Admin</b>\n\nSend the User ID you want to make admin:",
        "remove_moderator_prompt": "🗑 <b>Remove Admin</b>\n\n📋 <b>Current Admins:</b>\n{admins_list}\n\nSend the admin ID to remove:",
        "remove_channel_prompt": "🗑 <b>Remove Channel</b>\n\n📋 <b>Current Channels:</b>\n{channels_list}\n\nSend the channel number or ID to remove it:",
        "channel_not_found": "❌ Channel not found!",
        "otp_group_status": "📱 <b>OTP Group:</b>\n{status}",
        "otp_group_set_status": "✅ Group set: <code>{group_id}</code>",
        "otp_group_not_set": "❌ No group set",
        "delete_otp_group": "🗑 Delete Group",
        "otp_group_deleted": "✅ OTP group deleted!",
        "top_users": "👥 Top 10 Users",
        "top_users_title": "👥 <b>Top 10 Users</b>\n<i>By codes received</i>\n\n",
        "no_users_yet": "⚠️ No users yet!",
        "user_joined": "🎉 <b>New User Joined!</b>\n\n👤 Name: {name}\n🆔 ID: <code>{user_id}</code>\n📅 Time: {time}",
        "edit_button_labels_ar": "<tg-emoji emoji-id='5294163983983463099'>🇸🇦</tg-emoji> Edit Arabic Buttons",
        "edit_button_labels_en": "<tg-emoji emoji-id='5293993521026453119'>🇬🇧</tg-emoji> Edit English Buttons",
        "edit_button_labels_lang": "🏷️ <b>Edit Button Labels</b>\n\nChoose language:",
        "edit_labels_ar_menu": "<tg-emoji emoji-id='5294163983983463099'>🇸🇦</tg-emoji> <b>تعديل الأزرار بالعربية</b>\n\nاختر الزر الذي تريد تعديله:",
        "edit_labels_en_menu": "<tg-emoji emoji-id='5293993521026453119'>🇬🇧</tg-emoji> <b>Edit Button Labels (English)</b>\n\nChoose the button you want to edit:",
        "edit_choose_country_ar": "تعديل \"اختر دولة\"",
        "edit_my_account_ar": "تعديل \"حسابي\"",
        "edit_help_ar": "تعديل \"𝗛𝗲𝗹𝗽❓\"",
        "edit_choose_country_en": "Edit \"Choose Country\"",
        "edit_my_account_en": "Edit \"My Account\"",
        "edit_help_en": "Edit \"Help\"",
        "send_new_label": "📝 Send the new button name:",
        "label_updated": "✅ Button label updated successfully!",
        "manage_otp_group": "📱 Manage OTP Group",
        "welcome_admin": "🌐 <b>Welcome to OTP Bot!</b>\n\nChoose a country to receive a number and wait for OTP.\n\nAs an admin, you can also access the Admin Panel.",
        "choose_language": "🌍 <b>اختر اللغة / Choose Language</b>",
        "group_hello_admin": "👋 Hello! I'm the OTP Bot.\n\n⚠️ <b>Note:</b> Groups cannot be added automatically.\nThe admin must add this group from the admin panel.",
        "group_hello": "👋 Hello! I'm the OTP Bot.\n\nTo use me, contact me privately.",
        "total_users": "👥 <b>Total Users:</b>",
        "total_codes": "🔢 <b>Total Codes:</b>",
        "codes_today": "📅 <b>Codes Today:</b>",
        "codes_week": "📆 <b>Codes This Week:</b>",
        "codes_month": "📊 <b>Codes This Month:</b>",
        "users_text": "users",
        "developer_btn": "🆘 Developer",
        "verify_btn": "✅ Verify",
        "select_server_title": "🖥️ <b>Select Server</b>",
        "select_server_desc": "📌 Each server contains a different set of countries and numbers:",
        "select_server_hint": "🔻 <i>Select a server to view available countries</i>",
        "select_platform_title": "📱 <b>Select Platform in {server}</b>",
        "select_platform_hint": "🔻 <i>Select the platform you want to receive codes for</i>",
        "no_numbers_here": "❌ <b>No numbers available here</b>",
        "no_countries_title": "❌ <b>No countries available</b>",
        "server_label": "🖥️ <b>Server:</b>",
        "platform_label": "📱 <b>Platform:</b>",
        "no_countries_hint": "🔻 <i>No countries available for this platform in this server currently</i>",
        "available_countries_title": "🌍 <b>Available Countries</b>",
        "select_country_hint": "🔻 <i>Select the country you want to receive codes for</i>",
        "number_selected_success": "✅ <b>Number selected successfully!</b>",
        "waiting_for_code": "⏳ 𝓦𝓪𝓲𝓽𝓲𝓷𝓰 𝓯𝓸𝓻 𝓽𝓱𝓮 𝓬𝓸𝓭𝓮... 📱",
        "code_will_be_sent": "The code will be sent to you directly when it arrives!",
        "change_number_btn": " Change Number",
        "change_country_btn": " Change Country",
        "back_to_servers": "𝗕𝗮𝗰𝗸 𝘁𝗼 𝘀𝗲𝗿𝘃𝗲𝗿𝘀",
        "sticker_duration_error": "❌ Duration must be between 0.1 and 30 seconds!",
        "sticker_duration_set": "✅ <b>Sticker display duration set!</b>\n\n⏱ New duration: {duration} seconds",
        "invalid_number": "❌ Please send a valid number!\n\nExample: 0.5 or 1 or 2.5",
        "error_msg": "❌ Error: {error}",
        "referral_success": "🎉 <b>You've registered successfully via referral link!</b>\n\nEnjoy using the bot!"
    }
}

def get_user_language(user_id):
    lang = USERS.get(str(user_id), {}).get("language", "en")
    if not lang or lang not in ("en", "ar", "ru", "bn"):
        return "en"
    return lang

def set_user_language(user_id, lang):
    if str(user_id) not in USERS:
        USERS[str(user_id)] = {}
    USERS[str(user_id)]["language"] = lang
    save_users()

def t(user_id, key):
    lang = get_user_language(user_id)
    # For ru/bn use en as base since we don't have full translations
    if lang in ("ru", "bn"):
        return TEXTS.get("en", TEXTS["ar"]).get(key, key)
    return TEXTS.get(lang, TEXTS["en"]).get(key, key)

def save_pickle(path, obj):
    with open(path, "wb") as f:
        pickle.dump(obj, f)

def load_pickle(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return None

def save_cookies():
    cookies_dict = session1.cookies.get_dict()
    save_pickle(COOKIES_FILE, cookies_dict)

def load_cookies():
    d = load_pickle(COOKIES_FILE)
    if isinstance(d, dict) and d:
        session1.cookies.update(d)
        return True
    return False

def clear_cookies():
    session1.cookies.clear()
    if os.path.exists(COOKIES_FILE):
        try:
            os.remove(COOKIES_FILE)
            return True
        except:
            return False
    return True

def save_cookies_site3():
    cookies_dict = session3.cookies.get_dict()
    save_pickle(COOKIES_FILE_SITE3, cookies_dict)
    print("[Site3/Number_Panel] 💾 تم حفظ الجلسة")

def load_cookies_site3():
    d = load_pickle(COOKIES_FILE_SITE3)
    if isinstance(d, dict) and d:
        session3.cookies.update(d)
        print("[Site3/Number_Panel] 📥 تم تحميل الجلسة المحفوظة")
        return True
    print("[Site3/Number_Panel] ⚠️ لا توجد جلسة محفوظة")
    return False

def save_cookies_site4():
    cookies_dict = session4.cookies.get_dict()
    save_pickle(COOKIES_FILE_SITE4, cookies_dict)
    print("[Site4/Bolt] 💾 تم حفظ الجلسة")

def load_cookies_site4():
    d = load_pickle(COOKIES_FILE_SITE4)
    if isinstance(d, dict) and d:
        session4.cookies.update(d)
        print("[Site4/Bolt] 📥 تم تحميل الجلسة المحفوظة")
        return True
    print("[Site4/Bolt] ⚠️ لا توجد جلسة محفوظة")
    return False

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ]
    return random.choice(user_agents)

def login_attempt_group():
    
    global session1, is_logged_in_site1
    
    try:
        print(f"[GROUP] 🔄 جلب صفحة تسجيل الدخول...")
        resp = session1.get(LOGIN_PAGE_URL, timeout=HTTP_TIMEOUT)
        
        if resp.status_code != 200:
            print(f"[GROUP] ⚠️ فشل فتح صفحة الدخول: {resp.status_code}")
            return False
        
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            print("[GROUP] ❌ لم يتم العثور على captcha في صفحة تسجيل الدخول")
            return False
        
        num1, num2 = int(match.group(1)), int(match.group(2))
        captcha_answer = num1 + num2
        print(f"[GROUP] 🧮 حل captcha: {num1} + {num2} = {captcha_answer}")
        
        payload = {
            "username": USERNAME,
            "password": PASSWORD,
            "capt": str(captcha_answer)
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LOGIN_PAGE_URL,
            "Origin": BASE_URL,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        print(f"[GROUP] 📤 إرسال طلب تسجيل الدخول لـ: {USERNAME}")
        
        resp = session1.post(LOGIN_POST_URL, data=payload, headers=headers, timeout=HTTP_TIMEOUT, allow_redirects=True)
        
        print(f"[GROUP] 📊 حالة الاستجابة: {resp.status_code}")
        
        if ("dashboard" in resp.text.lower() or 
            "logout" in resp.text.lower() or 
            "agent" in resp.url.lower() or
            "/ints/agent" in resp.url or
            resp.url != LOGIN_PAGE_URL):
            print("[GROUP] ✅ تم تسجيل الدخول بنجاح")
            is_logged_in_site1 = True
            save_cookies()
            
            print("[GROUP] 🔄 زيارة صفحة SMSCDRReports بعد تسجيل الدخول...")
            try:
                session1.get(BASE_URL + "/ints/agent/SMSCDRReports", timeout=HTTP_TIMEOUT)
                print("[GROUP] ✅ تم زيارة صفحة SMSCDRReports بنجاح")
                time.sleep(1)
            except Exception as e:
                print(f"[GROUP] ⚠️ خطأ في زيارة صفحة SMSCDRReports: {e}")
            
            return True
        else:
            print("[GROUP] ❌ فشل تسجيل الدخول")
            if "incorrect" in resp.text.lower() or "invalid" in resp.text.lower():
                print("[GROUP] ⚠️ اسم المستخدم أو كلمة المرور غير صحيحة")
            return False
            
    except requests.exceptions.Timeout:
        print(f"[GROUP] ⏱️ انتهى وقت الاتصال")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"[GROUP] 🔌 خطأ في الاتصال: {e}")
        return False
    except Exception as e:
        print(f"[GROUP] ❌ خطأ في تسجيل الدخول: {e}")
        return False

def login(max_retries=10):
    
    global session1, is_logged_in_site1
    print(f"🔐 GROUP: بدء تسجيل الدخول...")
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n🔄 GROUP: المحاولة {attempt}/{max_retries}")
            
            if attempt > 1:
                print(f"🔄 GROUP: تجديد الجلسة...")
                session1 = create_session_group()
                time.sleep(2)
            
            if login_attempt_group():
                print(f"✅ GROUP: نجح تسجيل الدخول في المحاولة {attempt}")
                return True
            
            backoff_time = min(30, 5 * attempt)
            print(f"⏳ GROUP: الانتظار {backoff_time}s قبل المحاولة التالية...")
            time.sleep(backoff_time)
            
        except Exception as e:
            print(f"❌ GROUP (محاولة {attempt}): خطأ - {str(e)}")
            time.sleep(5)
    
    print(f"❌ GROUP: فشل تسجيل الدخول بعد {max_retries} محاولات")
    return False

def check_login_valid():
    try:
        test_url = BASE_URL + "/ints/agent/res/data_smscdr.php?per-page=10"
        ajax_headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": BASE_URL + "/ints/agent/SMSCDRReports"
        }
        r = session1.get(test_url, headers=ajax_headers, timeout=15)
        if r.status_code == 200:
            if "login" in r.text.lower() or "sign in" in r.text.lower():
                return False
            if "direct script access not allowed" in r.text.lower():
                return False
            return True
        return False
    except Exception as e:
        return False


def _bolt_type_login(site_key, account):
    username = account.get("username")
    password = account.get("password")

    if site_key == "MSI":
        session_obj = session6
        base_url = BASE_URL6
        login_page = LOGIN_PAGE_URL6
        login_post = LOGIN_POST_URL6
        timeout = HTTP_TIMEOUT6
    elif site_key == "proton SMS":
        session_obj = session7
        base_url = BASE_URL7
        login_page = LOGIN_PAGE_URL7
        login_post = LOGIN_POST_URL7
        timeout = HTTP_TIMEOUT7
    elif site_key == "IMS":
        session_obj = session8
        base_url = BASE_URL8
        login_page = LOGIN_PAGE_URL8
        login_post = LOGIN_POST_URL8
        timeout = HTTP_TIMEOUT8
    elif site_key == "Roxy SMS":
        try:
            scraper = cloudscraper.create_scraper()
            login_url = "http://www.roxysms.net/signin"
            payload = {"username": username, "password": password}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "http://www.roxysms.net/Login"
            }
            resp = scraper.post(login_url, data=payload, headers=headers, timeout=20)
            if resp.status_code == 200 and ("success" in resp.text.lower() or "logout" in resp.text.lower()):
                print(f"[{site_key}] ({username}) ✅ تسجيل الدخول نجح")
                return True
            else:
                print(f"[{site_key}] ({username}) ❌ فشل تسجيل الدخول")
                return False
        except Exception as e:
            print(f"[{site_key}] ({username}) ❌ خطأ في تسجيل الدخول: {e}")
            return False
    else:
        return False

    print(f"[{site_key}] ({username}) 🔐 محاولة تسجيل الدخول (Bolt-type)...")
    
    try:
        session_obj.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
        })
        
        resp = session_obj.get(login_page, timeout=timeout)
        
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            print(f"[{site_key}] ({username}) ⚠️ لم يتم العثور على captcha")
            return False
        
        num1, num2 = int(match.group(1)), int(match.group(2))
        captcha_answer = num1 + num2
        
        crlf_match = re.search(r"name=['\"]crlf['\"].*?value=['\"]([^'\"]+)['\"]", resp.text)
        
        payload = {
            "username": username,
            "password": password,
            "capt": str(captcha_answer)
        }
        
        if crlf_match:
            payload["crlf"] = crlf_match.group(1)
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": login_page,
            "Origin": base_url
        }
        
        resp = session_obj.post(login_post, data=payload, headers=headers, timeout=timeout, allow_redirects=True)
        
        if ("dashboard" in resp.text.lower() or 
            "logout" in resp.text.lower() or 
            "agent" in resp.url.lower() or 
            "reports" in resp.url.lower()):
            print(f"[{site_key}] ({username}) ✅ تسجيل الدخول نجح")
            return True
        else:
            print(f"[{site_key}] ({username}) ❌ فشل تسجيل الدخول")
            return False
            
    except Exception as e:
        print(f"[{site_key}] ({username}) ❌ خطأ في تسجيل الدخول: {e}")
        return False

def extract_sms(html_text, debug_mode=False):
    try:
        test_session = requests.Session()
        test_session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
        })
        
        resp = test_session.get(login_page_url, timeout=timeout)
        print(f"[{site_key}] 📄 حالة GET: {resp.status_code}")
        
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            print(f"[{site_key}] ⚠️ لم يتم العثور على captcha في الصفحة")
            return False
        
        num1, num2 = int(match.group(1)), int(match.group(2))
        captcha_answer = num1 + num2
        print(f"[{site_key}] 🧮 حل captcha: {num1} + {num2} = {captcha_answer}")
        
        crlf_match = re.search(r"name='crlf' value='([^']+)'", resp.text)
        
        payload = {
            "username": username,
            "password": password,
            "capt": str(captcha_answer)
        }
        
        if crlf_match:
            payload["crlf"] = crlf_match.group(1)
            print(f"[{site_key}] 🔑 استخراج crlf token")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": login_page_url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Origin": base_url
        }
        
        print(f"[{site_key}] 📤 إرسال طلب تسجيل الدخول لـ: {username}")
        resp = test_session.post(login_post_url, data=payload, headers=headers, timeout=timeout, allow_redirects=True)
        
        print(f"[{site_key}] 📊 حالة POST: {resp.status_code}")
        print(f"[{site_key}] 🔗 URL النهائي: {resp.url}")
        
        if ("dashboard" in resp.text.lower() or 
            "logout" in resp.text.lower() or 
            "agent" in resp.url.lower() or 
            "reports" in resp.url.lower() or
            resp.url != login_page_url):
            print(f"[{site_key}] ✅ تسجيل الدخول نجح")
            return True
        else:
            print(f"[{site_key}] ❌ فشل تسجيل الدخول")
            return False
            
    except Exception as e:
        print(f"[{site_key}] ❌ خطأ في تسجيل الدخول: {e}")
        return False

def test_site_login(chat_id, site_key, account_id=None):
    global is_logged_in_site2, is_logged_in_site3, is_logged_in_site4, is_logged_in_site5, USERNAME, PASSWORD, USERNAME2, PASSWORD2, USERNAME3, PASSWORD3, USERNAME4, PASSWORD4, USERNAME5, PASSWORD5
    
    site_name = SETTINGS[site_key]["name"]
    account = get_account_by_id(site_key, account_id) if account_id else get_site_accounts(site_key)[0]
    
    if not account:
        bot.send_message(chat_id, "❌ الحساب غير موجود!", parse_mode="HTML")
        return
    
    try:
        if site_key == "IMS":
            success, _ = login_site8(account)
            if success:
                bot.send_message(
                    chat_id,
                    f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                    f"👤 الحساب: <code>{account.get('username')}</code>\n"
                    f"🔓 تم تسجيل الدخول بنجاح\n"
                    f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    parse_mode="HTML"
                )
            else:
                bot.send_message(
                    chat_id,
                    f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                    f"👤 الحساب: <code>{account.get('username')}</code>\n"
                    f"⚠️ تأكد من صحة البيانات (Username, Password, Captcha)",
                    parse_mode="HTML"
                )
            return

        if site_key == "GROUP":
            old_username, old_password = USERNAME, PASSWORD
            try:
                USERNAME = account.get("username")
                PASSWORD = account.get("password")
                
                result = login()
                
                if result:
                    SESSIONS[site_key] = {"logged_in": True, "time": datetime.now().isoformat()}
                    save_sessions(SESSIONS)
                    bot.send_message(
                        chat_id,
                        f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"🔓 تم تسجيل الدخول بنجاح\n"
                        f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"⚠️ تحقق من اليوزر والباسورد",
                        parse_mode="HTML"
                    )
            finally:
                USERNAME, PASSWORD = old_username, old_password
        
        elif site_key == "Roxy SMS":
            try:
                scraper = cloudscraper.create_scraper()
                login_url = "http://www.roxysms.net/signin"
                payload = {"username": account["username"], "password": account["password"]}
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "http://www.roxysms.net/Login"
                }
                resp = scraper.post(login_url, data=payload, headers=headers, timeout=20)
                if resp.status_code == 200 and ("success" in resp.text.lower() or "logout" in resp.text.lower()):
                    SESSIONS[site_key] = {"logged_in": True, "time": datetime.now().isoformat()}
                    save_sessions(SESSIONS)
                    bot.send_message(
                        chat_id,
                        f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"🔓 تم تسجيل الدخول بنجاح\n"
                        f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"⚠️ تحقق من اليوزر والباسورد",
                        parse_mode="HTML"
                    )
            except Exception as e:
                bot.send_message(chat_id, f"❌ خطأ في تسجيل الدخول: {e}")
            return
        
        elif site_key == "Fly sms":
            old_username, old_password = USERNAME2, PASSWORD2
            try:
                USERNAME2 = account.get("username")
                PASSWORD2 = account.get("password")
                
                is_logged_in_site2 = False
                result = login_site2()
                
                if result:
                    SESSIONS[site_key] = {"logged_in": True, "time": datetime.now().isoformat()}
                    save_sessions(SESSIONS)
                    bot.send_message(
                        chat_id,
                        f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"🔓 تم تسجيل الدخول بنجاح\n"
                        f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"⚠️ تحقق من اليوزر والباسورد",
                        parse_mode="HTML"
                    )
            finally:
                USERNAME2, PASSWORD2 = old_username, old_password
        
        elif site_key == "Number_Panel":
            old_username, old_password = USERNAME3, PASSWORD3
            try:
                USERNAME3 = account.get("username")
                PASSWORD3 = account.get("password")
                
                is_logged_in_site3 = False
                result = login_site3()
                
                if result:
                    SESSIONS[site_key] = {"logged_in": True, "time": datetime.now().isoformat()}
                    save_sessions(SESSIONS)
                    bot.send_message(
                        chat_id,
                        f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"🔓 تم تسجيل الدخول بنجاح\n"
                        f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"⚠️ تحقق من اليوزر والباسورد",
                        parse_mode="HTML"
                    )
            finally:
                USERNAME3, PASSWORD3 = old_username, old_password
        
        elif site_key == "Bolt":
            old_username, old_password = USERNAME4, PASSWORD4
            try:
                USERNAME4 = account.get("username")
                PASSWORD4 = account.get("password")
                
                is_logged_in_site4 = False
                result = login_site4()
                
                if result:
                    SESSIONS[site_key] = {"logged_in": True, "time": datetime.now().isoformat()}
                    save_sessions(SESSIONS)
                    bot.send_message(
                        chat_id,
                        f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"🔓 تم تسجيل الدخول بنجاح\n"
                        f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"⚠️ تحقق من اليوزر والباسورد",
                        parse_mode="HTML"
                    )
            finally:
                USERNAME4, PASSWORD4 = old_username, old_password
        
        elif site_key == "iVASMS":
            old_username, old_password = USERNAME5, PASSWORD5
            try:
                USERNAME5 = account.get("username")
                PASSWORD5 = account.get("password")
                
                is_logged_in_site5 = False
                result = login_site5()
                
                if result:
                    SESSIONS[site_key] = {"logged_in": True, "time": datetime.now().isoformat()}
                    save_sessions(SESSIONS)
                    bot.send_message(
                        chat_id,
                        f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"🔓 تم تسجيل الدخول بنجاح\n"
                        f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"⚠️ تحقق من اليوزر والباسورد",
                        parse_mode="HTML"
                    )
            finally:
                USERNAME5, PASSWORD5 = old_username, old_password
        
        elif site_key in ["MSI", "proton SMS", "IMS", "Roxy SMS"]:
            result = test_bolt_type_login(site_key, account)
            if result:
                SESSIONS[site_key] = {"logged_in": True, "time": datetime.now().isoformat()}
                save_sessions(SESSIONS)
                bot.send_message(
                    chat_id,
                    f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                    f"👤 الحساب: <code>{account.get('username')}</code>\n"
                    f"🔓 تم تسجيل الدخول بنجاح\n"
                    f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    parse_mode="HTML"
                )
            else:
                bot.send_message(
                    chat_id,
                    f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                    f"👤 الحساب: <code>{account.get('username')}</code>\n"
                    f"⚠️ تحقق من اليوزر والباسورد",
                    parse_mode="HTML"
                )

        elif site_key == "hadi":
            old_username, old_password = USERNAME12, PASSWORD12
            try:
                globals()["USERNAME12"] = account.get("username")
                globals()["PASSWORD12"] = account.get("password")
                is_logged_in_site12 = False
                result = login_site12(account)
                if result:
                    SESSIONS[site_key] = {"logged_in": True, "time": datetime.now().isoformat()}
                    save_sessions(SESSIONS)
                    bot.send_message(
                        chat_id,
                        f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"🔓 تم تسجيل الدخول بنجاح\n"
                        f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"⚠️ تحقق من اليوزر والباسورد",
                        parse_mode="HTML"
                    )
            finally:
                globals()["USERNAME12"], globals()["PASSWORD12"] = old_username, old_password

        elif site_key == "fire":
            old_username, old_password = USERNAME13, PASSWORD13
            try:
                globals()["USERNAME13"] = account.get("username")
                globals()["PASSWORD13"] = account.get("password")
                is_logged_in_site13 = False
                result = login_site13(account)
                if result:
                    SESSIONS[site_key] = {"logged_in": True, "time": datetime.now().isoformat()}
                    save_sessions(SESSIONS)
                    bot.send_message(
                        chat_id,
                        f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"🔓 تم تسجيل الدخول بنجاح\n"
                        f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"⚠️ تحقق من اليوزر والباسورد",
                        parse_mode="HTML"
                    )
            finally:
                globals()["USERNAME13"], globals()["PASSWORD13"] = old_username, old_password
        elif site_key == "Seven1Tel":
            old_username, old_password = USERNAME14, PASSWORD14
            try:
                globals()["USERNAME14"] = account.get("username")
                globals()["PASSWORD14"] = account.get("password")
                is_logged_in_site14 = False
                result = login_site14(account)
                if result:
                    SESSIONS[site_key] = {"logged_in": True, "time": datetime.now().isoformat()}
                    save_sessions(SESSIONS)
                    bot.send_message(
                        chat_id,
                        f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"🔓 تم تسجيل الدخول بنجاح\n"
                        f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"⚠️ تحقق من اليوزر والباسورد",
                        parse_mode="HTML"
                    )
            finally:
                globals()["USERNAME14"], globals()["PASSWORD14"] = old_username, old_password
        elif site_key == "Gaza SMS":
            old_username, old_password = USERNAME15, PASSWORD15
            try:
                globals()["USERNAME15"] = account.get("username")
                globals()["PASSWORD15"] = account.get("password")
                is_logged_in_site15 = False
                result = login_site15(account)
                if result:
                    SESSIONS[site_key] = {"logged_in": True, "time": datetime.now().isoformat()}
                    save_sessions(SESSIONS)
                    bot.send_message(
                        chat_id,
                        f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"🔓 تم تسجيل الدخول بنجاح\n"
                        f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"⚠️ تحقق من اليوزر والباسورد",
                        parse_mode="HTML"
                    )
            finally:
                globals()["USERNAME15"], globals()["PASSWORD15"] = old_username, old_password
        elif site_key == "Km sms":
            old_username, old_password = USERNAME16, PASSWORD16
            try:
                globals()["USERNAME16"] = account.get("username")
                globals()["PASSWORD16"] = account.get("password")
                result = login_generic_ints(site_key, account)
                if result:
                    SESSIONS[site_key] = {"logged_in": True, "time": datetime.now().isoformat()}
                    save_sessions(SESSIONS)
                    bot.send_message(
                        chat_id,
                        f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"🔓 تم تسجيل الدخول بنجاح\n"
                        f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"⚠️ تحقق من اليوزر والباسورد",
                        parse_mode="HTML"
                    )
            finally:
                globals()["USERNAME16"], globals()["PASSWORD16"] = old_username, old_password

        elif site_key in ["Grand SMS", "Purple SMS"]:
            result = login_generic_ints(site_key, account)
            if result:
                SESSIONS[site_key] = {"logged_in": True, "time": datetime.now().isoformat()}
                save_sessions(SESSIONS)
                bot.send_message(
                    chat_id,
                    f"✅ <b>نجح تسجيل الدخول - {site_name}</b>\n\n"
                    f"👤 الحساب: <code>{account.get('username')}</code>\n"
                    f"🔓 تم تسجيل الدخول بنجاح\n"
                    f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    parse_mode="HTML"
                )
            else:
                bot.send_message(
                    chat_id,
                    f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                    f"👤 الحساب: <code>{account.get('username')}</code>\n"
                    f"⚠️ تحقق من اليوزر والباسورد",
                    parse_mode="HTML"
                )

    except Exception as e:
        bot.send_message(
            chat_id,
            f"❌ <b>خطأ أثناء اختبار تسجيل الدخول - {site_name}</b>\n\n"
            f"⚠️ الخطأ: {str(e)}",
            parse_mode="HTML"
        )

def test_site_fetch(chat_id, site_key, account_id=None):
    global is_logged_in_site2, is_logged_in_site3, is_logged_in_site4, is_logged_in_site5, USERNAME, PASSWORD, USERNAME2, PASSWORD2, USERNAME3, PASSWORD3, USERNAME4, PASSWORD4, USERNAME5, PASSWORD5
    site_name = SETTINGS[site_key]["name"]
    account = get_account_by_id(site_key, account_id) if account_id else get_site_accounts(site_key)[0]
    
    if not account:
        bot.send_message(chat_id, "❌ الحساب غير موجود!", parse_mode="HTML")
        return
    
    try:
        if site_key == "GROUP":
            old_username, old_password = USERNAME, PASSWORD
            try:
                USERNAME = account.get("username")
                PASSWORD = account.get("password")
                
                if not check_login_valid():
                    print(f"[GROUP] الجلسة غير صالحة لـ {account.get('username')}، محاولة تسجيل الدخول...")
                    if not login():
                        bot.send_message(
                            chat_id,
                            f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                            f"👤 الحساب: <code>{account.get('username')}</code>\n"
                            f"⚠️ يجب تسجيل الدخول أولاً قبل اختبار جلب الكود",
                            parse_mode="HTML"
                        )
                        return
                    time.sleep(2)
            
                sms_url = BASE_URL + AJAX_PATH
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": BASE_URL + "/ints/agent/SMSCDRReports"
                }
                
                r = session1.get(sms_url, headers=headers, timeout=HTTP_TIMEOUT)
                
                if r.status_code == 200:
                    messages = extract_sms(r.text)
                    if messages:
                        last_msg = messages[0]
                        otp, decoded_text = extract_from_message(last_msg.get('raw', ''))
                        
                        bot.send_message(
                            chat_id,
                            f"✅ <b>نجح جلب الكود - {site_name}</b>\n\n"
                            f"👤 الحساب: <code>{account.get('username')}</code>\n"
                            f"📱 الرقم: <code>{last_msg.get('source', 'N/A')}</code>\n"
                            f"📝 الرسالة: {decoded_text[:100] if decoded_text else 'N/A'}...\n"
                            f"⏰ الوقت: {last_msg.get('date', 'N/A')}",
                            parse_mode="HTML"
                        )
                    else:
                        bot.send_message(
                            chat_id,
                            f"⚠️ <b>لا توجد رسائل - {site_name}</b>\n\n"
                            f"👤 الحساب: <code>{account.get('username')}</code>",
                            parse_mode="HTML"
                        )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>خطأ في جلب البيانات - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"HTTP Status: {r.status_code}",
                        parse_mode="HTML"
                    )
            finally:
                USERNAME, PASSWORD = old_username, old_password
        
        elif site_key == "Fly sms":
            old_username, old_password = USERNAME2, PASSWORD2
            try:
                USERNAME2 = account.get("username")
                PASSWORD2 = account.get("password")
                
                if not is_logged_in_site2:
                    print(f"[Fly sms] غير مسجل دخول لـ {account.get('username')}، محاولة تسجيل الدخول...")
                    if not login_site2():
                        bot.send_message(
                            chat_id,
                            f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                            f"👤 الحساب: <code>{account.get('username')}</code>\n"
                            f"⚠️ يجب تسجيل الدخول أولاً قبل اختبار جلب الكود",
                            parse_mode="HTML"
                        )
                        return
                    time.sleep(2)
                
                url = build_ajax_url_site2()
                
                data = None
                max_retries = 5
                for attempt in range(1, max_retries + 1):
                    try:
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "Accept": "application/json, text/javascript, */*; q=0.01",
                            "X-Requested-With": "XMLHttpRequest",
                            "Referer": BASE_URL2 + "/ints/agent/SMSCDRReports"
                        }
                        r = session2.get(url, timeout=HTTP_TIMEOUT2, headers=headers)
                        
                        if r.status_code in [502, 503, 504]:
                            print(f"[Fly sms] ⚠️ السيرفر مشغول ({r.status_code}) - محاولة {attempt}/{max_retries}")
                            if attempt < max_retries:
                                time.sleep(15 * attempt)
                                continue
                            else:
                                bot.send_message(
                                    chat_id,
                                    f"⚠️ <b>السيرفر مشغول - {site_name}</b>\n\n"
                                    f"👤 الحساب: <code>{account.get('username')}</code>\n"
                                    f"⏳ الخطأ: {r.status_code} - السيرفر تحت ضغط\n"
                                    f"💡 حاول مرة أخرى بعد دقيقة",
                                    parse_mode="HTML"
                                )
                                return
                        
                        if r.status_code == 200:
                            data = r.json()
                            break
                        else:
                            if attempt < max_retries:
                                time.sleep(10)
                                continue
                    except Exception as e:
                        print(f"[Fly sms] ⚠️ خطأ في المحاولة {attempt}: {e}")
                        if attempt < max_retries:
                            time.sleep(10)
                            continue
                
                if data:
                    messages = data.get("data", [])
                    if messages:
                        last_msg = messages[0]
                        sms_text = last_msg[5] if len(last_msg) > 5 else "N/A"
                        number = last_msg[2] if len(last_msg) > 2 else "N/A"
                        date_str = last_msg[0] if len(last_msg) > 0 else "N/A"
                        
                        otp, decoded_text = extract_from_message(sms_text)
                        
                        bot.send_message(
                            chat_id,
                            f"✅ <b>نجح جلب الكود - {site_name}</b>\n\n"
                            f"👤 الحساب: <code>{account.get('username')}</code>\n"
                            f"📱 الرقم: <code>{number}</code>\n"
                            f"📝 الرسالة: {decoded_text[:100] if decoded_text else sms_text[:100]}...\n"
                            f"⏰ الوقت: {date_str}",
                            parse_mode="HTML"
                        )
                    else:
                        bot.send_message(
                            chat_id,
                            f"⚠️ <b>لا توجد رسائل - {site_name}</b>\n\n"
                            f"👤 الحساب: <code>{account.get('username')}</code>",
                            parse_mode="HTML"
                        )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>خطأ في جلب البيانات - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"⚠️ فشل الاتصال بالسيرفر",
                        parse_mode="HTML"
                    )
            except Exception as e:
                bot.send_message(
                    chat_id,
                    f"❌ <b>خطأ في معالجة البيانات - {site_name}</b>\n\n"
                    f"👤 الحساب: <code>{account.get('username')}</code>\n"
                    f"⚠️ التفاصيل: {str(e)}",
                    parse_mode="HTML"
                )
            finally:
                USERNAME2, PASSWORD2 = old_username, old_password
        
        elif site_key == "Number_Panel":
            old_username, old_password = USERNAME3, PASSWORD3
            try:
                USERNAME3 = account.get("username")
                PASSWORD3 = account.get("password")
                api_token = account.get("api_token") or SETTINGS[site_key].get("api_token")
                
                if api_token:
                    api_url = "http://147.135.212.197/crapi/st/viewstats"
                    r = session3.get(api_url, params={"token": api_token, "records": 10}, timeout=HTTP_TIMEOUT3)
                    if r.status_code == 200:
                        try:
                            data = r.json()
                            if isinstance(data, list) and data:
                                last_msg = data[0]
                                sms_text = last_msg[2]
                                number = last_msg[1]
                                date_str = last_msg[3]
                                
                                otp, decoded_text = extract_from_message(sms_text)
                                
                                bot.send_message(
                                    chat_id,
                                    f"✅ <b>نجح جلب الكود - {site_name} (API)</b>\n\n"
                                    f"👤 الحساب: <code>{account.get('username')}</code>\n"
                                    f"📱 الرقم: <code>{number}</code>\n"
                                    f"📝 الرسالة: {decoded_text[:100] if decoded_text else sms_text[:100]}...\n"
                                    
                                    f"⏰ الوقت: {date_str}",
                                    parse_mode="HTML"
                                )
                                return
                        except Exception as e:
                            print(f"API parse error: {e}")

                if not is_logged_in_site3:
                    print(f"[Number_Panel] غير مسجل دخول لـ {account.get('username')}، محاولة تسجيل الدخول...")
                    if not login_site3():
                        bot.send_message(
                            chat_id,
                            f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                            f"👤 الحساب: <code>{account.get('username')}</code>\n"
                            f"⚠️ يجب تسجيل الدخول أولاً قبل اختبار جلب الكود",
                            parse_mode="HTML"
                        )
                        return
                    time.sleep(2)
                
                url = BASE_URL3 + AJAX_PATH3
                params = {
                    "draw": 1,
                    "start": 0,
                    "length": 10
                }
                
                r = session3.get(url, params=params, timeout=HTTP_TIMEOUT3)
                
                if r.status_code == 200:
                    try:
                        data = r.json()
                        messages = data.get("data", []) or data.get("aaData", [])
                        if messages:
                            last_msg = messages[0]
                            sms_text = last_msg[IDX_SMS_SITE3] if len(last_msg) > IDX_SMS_SITE3 else "N/A"
                            number = last_msg[IDX_NUMBER_SITE3] if len(last_msg) > IDX_NUMBER_SITE3 else "N/A"
                            date_str = last_msg[IDX_DATE_SITE3] if len(last_msg) > IDX_DATE_SITE3 else "N/A"
                            
                            otp, decoded_text = extract_from_message(sms_text)
                            
                            bot.send_message(
                                chat_id,
                                f"✅ <b>نجح جلب الكود - {site_name}</b>\n\n"
                                f"👤 الحساب: <code>{account.get('username')}</code>\n"
                                f"📱 الرقم: <code>{number}</code>\n"
                                f"📝 الرسالة: {decoded_text[:100] if decoded_text else sms_text[:100]}...\n"
                                f"⏰ الوقت: {date_str}",
                                parse_mode="HTML"
                            )
                        else:
                            bot.send_message(
                                chat_id,
                                f"⚠️ <b>لا توجد رسائل - {site_name}</b>\n\n"
                                f"👤 الحساب: <code>{account.get('username')}</code>",
                                parse_mode="HTML"
                            )
                    except Exception as e:
                        bot.send_message(
                            chat_id,
                            f"❌ <b>خطأ في معالجة البيانات - {site_name}</b>\n\n"
                            f"👤 الحساب: <code>{account.get('username')}</code>\n"
                            f"⚠️ التفاصيل: {str(e)}",
                            parse_mode="HTML"
                        )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>خطأ في جلب البيانات - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"HTTP Status: {r.status_code}",
                        parse_mode="HTML"
                    )
            finally:
                USERNAME3, PASSWORD3 = old_username, old_password
        
        elif site_key == "Bolt":
            # Bolt uses same /ints/ structure with sesskey
            sess = requests.Session()
            sess.verify = False
            sess.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            })
            base_url = SETTINGS[site_key]["base_url"]
            login_page = SETTINGS[site_key]["login_page_url"]
            login_post = SETTINGS[site_key]["login_post_url"]
            ajax_path = SETTINGS[site_key]["ajax_path"]
            timeout = SETTINGS[site_key]["timeout"]
            username_b = account.get("username")
            password_b = account.get("password")
            try:
                resp = sess.get(login_page, timeout=timeout)
                match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
                captcha = str(int(match.group(1)) + int(match.group(2))) if match else ""
                crlf = re.search(r"name=['\"]crlf['\"].*?value=['\"]([^'\"]+)['\"]", resp.text)
                payload = {'username': username_b, 'password': password_b}
                if captcha: payload['capt'] = captcha
                if crlf: payload['crlf'] = crlf.group(1)
                headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Referer': login_page, 'Origin': base_url}
                r = sess.post(login_post, data=payload, headers=headers, timeout=timeout, allow_redirects=True)
                success = any(k in r.text.lower() for k in ["dashboard", "logout", "agent", "smscdr"]) or any(k in r.url.lower() for k in ["agent", "reports"])
                if not success:
                    bot.send_message(chat_id, f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n👤 الحساب: <code>{username_b}</code>\n⚠️ تحقق من اليوزر والباسورد", parse_mode="HTML")
                    return
                # Get sesskey
                sms_page = base_url + "/ints/agent/SMSCDRReports"
                page_resp = sess.get(sms_page, timeout=timeout)
                sesskey = None
                sk = re.search(r'sesskey=([A-Za-z0-9=]+)', page_resp.text)
                if sk: sesskey = sk.group(1)
                today = datetime.now().strftime('%Y-%m-%d')
                ajax_url = base_url + ajax_path
                if sesskey:
                    ajax_payload = {'fdate1': f'{today} 00:00:00', 'fdate2': f'{today} 23:59:59', 'frange': '', 'fclient': '', 'fnum': '', 'fcli': '', 'fgdate': '', 'fgmonth': '', 'fgrange': '', 'fgclient': '', 'fgnumber': '', 'fgcli': '', 'fg': '0', 'sesskey': sesskey}
                    ajax_headers = {'Accept': 'application/json, text/javascript, */*; q=0.01', 'X-Requested-With': 'XMLHttpRequest', 'Referer': sms_page}
                    r2 = sess.get(ajax_url, params=ajax_payload, headers=ajax_headers, timeout=timeout)
                else:
                    r2 = sess.get(ajax_url, params={'draw': 1, 'start': 0, 'length': 10}, timeout=timeout)
                if r2.status_code == 200:
                    try:
                        data = r2.json()
                        rows = data.get('aaData', data.get('data', []))
                        if rows:
                            last_msg = rows[0]
                            sms_text = last_msg[5] if len(last_msg) > 5 else str(last_msg)
                            number = last_msg[2] if len(last_msg) > 2 else "N/A"
                            date_str = last_msg[0] if len(last_msg) > 0 else "N/A"
                            otp, decoded_text = extract_from_message(sms_text)
                            bot.send_message(chat_id, f"✅ <b>نجح جلب الكود - {site_name}</b>\n\n👤 الحساب: <code>{username_b}</code>\n📱 الرقم: <code>{number}</code>\n📝 الرسالة: {(decoded_text or sms_text)[:100]}...\n⏰ الوقت: {date_str}", parse_mode="HTML")
                        else:
                            bot.send_message(chat_id, f"⚠️ <b>لا توجد رسائل - {site_name}</b>\n\n👤 الحساب: <code>{username_b}</code>", parse_mode="HTML")
                    except Exception as e:
                        bot.send_message(chat_id, f"❌ <b>خطأ في معالجة البيانات - {site_name}</b>\n\n⚠️ {str(e)}", parse_mode="HTML")
                else:
                    bot.send_message(chat_id, f"❌ <b>خطأ في جلب البيانات - {site_name}</b>\n\nHTTP Status: {r2.status_code}", parse_mode="HTML")
            except Exception as e:
                bot.send_message(chat_id, f"❌ <b>خطأ - {site_name}</b>\n\n⚠️ {str(e)}", parse_mode="HTML")
        
        elif site_key == "iVASMS":
            old_username, old_password = USERNAME5, PASSWORD5
            try:
                USERNAME5 = account.get("username")
                PASSWORD5 = account.get("password")
                
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                test_session = requests.Session()
                test_session.verify = False
                test_session.headers.update({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Connection": "keep-alive"
                })
                
                resp = test_session.get(LOGIN_PAGE_URL5, timeout=HTTP_TIMEOUT5)
                soup = BeautifulSoup(resp.text, 'html.parser')
                csrf_input = soup.find('input', {'name': '_token'})
                if not csrf_input:
                    bot.send_message(chat_id, f"❌ <b>فشل الاتصال - {site_name}</b>\n\n⚠️ لم يتم العثور على CSRF token", parse_mode="HTML")
                    return
                
                csrf = csrf_input.get('value')
                payload = {'_token': csrf, 'email': USERNAME5, 'password': PASSWORD5}
                headers = {"Content-Type": "application/x-www-form-urlencoded", "Referer": LOGIN_PAGE_URL5}
                
                resp = test_session.post(LOGIN_POST_URL5, data=payload, headers=headers, timeout=HTTP_TIMEOUT5, allow_redirects=True)
                
                if 'portal' not in resp.url and 'login' in resp.url:
                    bot.send_message(chat_id, f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n👤 الحساب: <code>{account.get('username')}</code>", parse_mode="HTML")
                    return
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                csrf_input = soup.find('input', {'name': '_token'})
                if csrf_input:
                    csrf = csrf_input.get('value')
                
                today = date.today()
                from_date = (today - timedelta(days=7)).strftime("%d/%m/%Y")
                to_date = today.strftime("%d/%m/%Y")
                
                payload = {'from': from_date, 'to': to_date, '_token': csrf}
                headers = {'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Referer': SMS_RECEIVED_URL5}
                
                resp = test_session.post(GET_SMS_URL5, data=payload, headers=headers, timeout=HTTP_TIMEOUT5)
                
                if resp.status_code != 200:
                    bot.send_message(chat_id, f"❌ <b>خطأ في جلب البيانات - {site_name}</b>\n\nHTTP Status: {resp.status_code}", parse_mode="HTML")
                    return
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                items = soup.select("div.item div.card.card-body")
                ranges = []
                for item in items:
                    onclick = item.get('onclick', '')
                    match = re.search(r"getDetials\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", str(onclick) if onclick else "")
                    if match:
                        ranges.append(match.group(1))
                
                if not ranges:
                    bot.send_message(chat_id, f"⚠️ <b>لا توجد رسائل - {site_name}</b>\n\n👤 الحساب: <code>{account.get('username')}</code>", parse_mode="HTML")
                    return
                
                first_range = ranges[0]
                start_datetime = f"{today.strftime('%Y-%m-%d')} 00:00:00"
                end_datetime = f"{today.strftime('%Y-%m-%d')} 23:59:59"
                
                payload = {'_token': csrf, 'start': start_datetime, 'end': end_datetime, 'range': first_range}
                resp = test_session.post(GET_SMS_NUMBER_URL5, data=payload, headers=headers, timeout=HTTP_TIMEOUT5)
                
                numbers = []
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for item in soup.select("[onclick]"):
                        onclick = item.get('onclick', '')
                        phone_match = re.search(r"getNumber[^\(]*\(['\"]([^'\"]+)['\"]", str(onclick) if onclick else "")
                        if phone_match:
                            phone = phone_match.group(1)
                            if phone and len(phone) > 5:
                                numbers.append(phone)
                    if not numbers:
                        all_numbers = re.findall(r'["\']?(\d{10,15})["\']?', resp.text)
                        numbers.extend(all_numbers[:10])
                
                if not numbers:
                    bot.send_message(chat_id, f"⚠️ <b>لا توجد أرقام - {site_name}</b>\n\n👤 الحساب: <code>{account.get('username')}</code>\nRange: {first_range}", parse_mode="HTML")
                    return
                
                first_phone = numbers[0]
                payload = {'_token': csrf, 'start': start_datetime, 'end': end_datetime, 'Number': first_phone, 'Range': first_range}
                resp = test_session.post(GET_SMS_MESSAGE_URL5, data=payload, headers=headers, timeout=HTTP_TIMEOUT5)
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    message = None
                    for selector in [".col-9.col-sm-6 p", ".col-sm-6 p"]:
                        el = soup.select_one(selector)
                        if el:
                            message = el.text.strip()
                            break
                    if not message:
                        for p in soup.find_all('p'):
                            text = p.text.strip()
                            if len(text) > 15:
                                message = text
                                break
                    
                    if message:
                        otp, decoded_text = extract_from_message(message)
                        bot.send_message(
                            chat_id,
                            f"✅ <b>نجح جلب الكود - {site_name}</b>\n\n"
                            f"👤 الحساب: <code>{account.get('username')}</code>\n"
                            f"📱 الرقم: <code>{first_phone}</code>\n"
                            f"📝 الرسالة: {(decoded_text[:100] if decoded_text else message[:100])}...\n"
                            
                            f"📊 Ranges: {len(ranges)} | Numbers: {len(numbers)}",
                            parse_mode="HTML"
                        )
                    else:
                        bot.send_message(chat_id, f"⚠️ <b>لا توجد رسالة - {site_name}</b>\n\n📱 الرقم: {first_phone}", parse_mode="HTML")
                else:
                    bot.send_message(chat_id, f"❌ <b>خطأ في جلب الرسالة - {site_name}</b>\n\nHTTP Status: {resp.status_code}", parse_mode="HTML")
                    
            except Exception as e:
                bot.send_message(chat_id, f"❌ <b>خطأ - {site_name}</b>\n\n⚠️ {str(e)}", parse_mode="HTML")
            finally:
                USERNAME5, PASSWORD5 = old_username, old_password
        
        elif site_key in ["MSI", "proton SMS", "IMS", "Roxy SMS"]:
            session_obj = session6 if site_key == "MSI" else (session7 if site_key == "proton SMS" else (session8 if site_key == "IMS" else session9))
            base_url = BASE_URL6 if site_key == "MSI" else (BASE_URL7 if site_key == "proton SMS" else (BASE_URL8 if site_key == "IMS" else BASE_URL9))
            ajax_path = AJAX_PATH6 if site_key == "MSI" else (AJAX_PATH7 if site_key == "proton SMS" else (AJAX_PATH8 if site_key == "IMS" else AJAX_PATH9))
            timeout = HTTP_TIMEOUT6 if site_key == "MSI" else (HTTP_TIMEOUT7 if site_key == "proton SMS" else (HTTP_TIMEOUT8 if site_key == "IMS" else HTTP_TIMEOUT9))
            
            result = test_bolt_type_login(site_key, account)
            if not result:
                bot.send_message(
                    chat_id,
                    f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                    f"👤 الحساب: <code>{account.get('username')}</code>\n"
                    f"⚠️ يجب تسجيل الدخول أولاً قبل اختبار جلب الكود",
                    parse_mode="HTML"
                )
                return
            
            time.sleep(2)
            url = base_url + ajax_path
            params = {
                "draw": 1,
                "start": 0,
                "length": 10
            }
            
            try:
                
                for attempt in range(3):
                    try:
                        r = session_obj.get(url, params=params, timeout=timeout)
                        break
                    except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
                        if attempt == 2: raise
                        time.sleep(2)
                
                if r.status_code == 200:
                    try:
                        data = r.json()
                        messages = data.get("data", [])
                        if messages:
                            last_msg = messages[0]
                            sms_text = last_msg[5] if len(last_msg) > 5 else "N/A"
                            number = last_msg[2] if len(last_msg) > 2 else "N/A"
                            date_str = last_msg[0] if len(last_msg) > 0 else "N/A"
                            
                            otp, decoded_text = extract_from_message(sms_text)
                            
                            bot.send_message(
                                chat_id,
                                f"✅ <b>نجح جلب الكود - {site_name}</b>\n\n"
                                f"👤 الحساب: <code>{account.get('username')}</code>\n"
                                f"📱 الرقم: <code>{number}</code>\n"
                                f"📝 الرسالة: {decoded_text[:100] if decoded_text else sms_text[:100]}...\n"
                                
                                f"⏰ الوقت: {date_str}",
                                parse_mode="HTML"
                            )
                        else:
                            bot.send_message(
                                chat_id,
                                f"⚠️ <b>لا توجد رسائل - {site_name}</b>\n\n"
                                f"👤 الحساب: <code>{account.get('username')}</code>",
                                parse_mode="HTML"
                            )
                    except Exception as e:
                        bot.send_message(
                            chat_id,
                            f"❌ <b>خطأ في معالجة البيانات - {site_name}</b>\n\n"
                            f"👤 الحساب: <code>{account.get('username')}</code>\n"
                            f"⚠️ التفاصيل: {str(e)}",
                            parse_mode="HTML"
                        )
                else:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>خطأ في جلب البيانات - {site_name}</b>\n\n"
                        f"👤 الحساب: <code>{account.get('username')}</code>\n"
                        f"HTTP Status: {r.status_code}",
                        parse_mode="HTML"
                    )
            except Exception as e:
                bot.send_message(
                    chat_id,
                    f"❌ <b>خطأ في الاتصال - {site_name}</b>\n\n"
                    f"👤 الحساب: <code>{account.get('username')}</code>\n"
                    f"⚠️ التفاصيل: {str(e)}",
                    parse_mode="HTML"
                )

        elif site_key in ["hadi", "fire", "Seven1Tel", "Gaza SMS", "Km sms", "Grand SMS", "Purple SMS"]:
            if site_key == "hadi":
                sess = login_site12(account)
            elif site_key == "fire":
                sess = login_site13(account)
            elif site_key == "Seven1Tel":
                sess = login_site14(account)
            elif site_key == "Gaza SMS":
                sess = login_site15(account)
            else:  # Km sms
                sess = login_generic_ints(site_key, account)
            if not sess:
                bot.send_message(
                    chat_id,
                    f"❌ <b>فشل تسجيل الدخول - {site_name}</b>\n\n"
                    f"👤 الحساب: <code>{account.get('username')}</code>\n"
                    f"⚠️ يجب تسجيل الدخول أولاً قبل اختبار جلب الكود",
                    parse_mode="HTML"
                )
                return
            time.sleep(2)
            if site_key == "hadi":
                base_url, ajax_path, timeout = BASE_URL12, AJAX_PATH12, HTTP_TIMEOUT12
            elif site_key == "fire":
                base_url, ajax_path, timeout = BASE_URL13, AJAX_PATH13, HTTP_TIMEOUT13
            elif site_key == "Seven1Tel":
                base_url, ajax_path, timeout = BASE_URL14, AJAX_PATH14, HTTP_TIMEOUT14
            elif site_key == "Gaza SMS":
                base_url, ajax_path, timeout = BASE_URL15, AJAX_PATH15, HTTP_TIMEOUT15
            else:  # Km sms
                base_url = SETTINGS[site_key]["base_url"]
                ajax_path = SETTINGS[site_key]["ajax_path"]
                timeout = SETTINGS[site_key]["timeout"]
            ajax_url = base_url + ajax_path
            today = datetime.now().strftime('%Y-%m-%d')

            try:
                # محاولة جلب sesskey من صفحة التقارير
                sms_page = base_url + "/ints/agent/SMSCDRReports"
                page_resp = sess.get(sms_page, timeout=timeout)
                sesskey = None
                if page_resp.status_code == 200:
                    m = re.search(r'sesskey=([A-Za-z0-9=]+)', page_resp.text)
                    if m:
                        sesskey = m.group(1)

                if sesskey:
                    payload = {
                        'fdate1': f'{today} 00:00:00',
                        'fdate2': f'{today} 23:59:59',
                        'frange': '', 'fclient': '', 'fnum': '', 'fcli': '',
                        'fgdate': '', 'fgmonth': '', 'fgrange': '',
                        'fgclient': '', 'fgnumber': '', 'fgcli': '',
                        'fg': '0', 'sesskey': sesskey
                    }
                    ajax_headers = {
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Referer': sms_page,
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                    }
                    if site_key == "fire":
                        r = sess.post(ajax_url, data=payload, headers=ajax_headers, timeout=timeout)
                    else:
                        r = sess.get(ajax_url, params=payload, headers=ajax_headers, timeout=timeout)
                else:
                    params = {'draw': 1, 'start': 0, 'length': 10}
                    r = sess.get(ajax_url, params=params, timeout=timeout)

                if r.status_code == 200:
                    try:
                        data = r.json()
                        rows = data.get('aaData', data.get('data', data if isinstance(data, list) else []))
                        if rows:
                            last_msg = rows[0]
                            if isinstance(last_msg, list):
                                sms_text = last_msg[5] if len(last_msg) > 5 else str(last_msg)
                                number = last_msg[2] if len(last_msg) > 2 else "N/A"
                                date_str = last_msg[0] if len(last_msg) > 0 else "N/A"
                            else:
                                sms_text = last_msg.get('message', last_msg.get('sms', str(last_msg)))
                                number = last_msg.get('phone', last_msg.get('number', 'N/A'))
                                date_str = last_msg.get('date', last_msg.get('time', 'N/A'))
                            otp, decoded_text = extract_from_message(sms_text)
                            bot.send_message(
                                chat_id,
                                f"✅ <b>نجح جلب الكود - {site_name}</b>\n\n"
                                f"👤 الحساب: <code>{account.get('username')}</code>\n"
                                f"📱 الرقم: <code>{number}</code>\n"
                                f"📝 الرسالة: {(decoded_text or sms_text)[:100]}...\n"
                                f"⏰ الوقت: {date_str}",
                                parse_mode="HTML"
                            )
                        else:
                            bot.send_message(
                                chat_id,
                                f"⚠️ <b>لا توجد رسائل - {site_name}</b>\n\n"
                                f"👤 الحساب: <code>{account.get('username')}</code>",
                                parse_mode="HTML"
                            )
                    except Exception as e:
                        bot.send_message(chat_id,
                            f"❌ <b>خطأ في معالجة البيانات - {site_name}</b>\n\n⚠️ {str(e)}",
                            parse_mode="HTML")
                else:
                    bot.send_message(chat_id,
                        f"❌ <b>خطأ في جلب البيانات - {site_name}</b>\n\nHTTP Status: {r.status_code}",
                        parse_mode="HTML")
            except Exception as e:
                bot.send_message(chat_id,
                    f"❌ <b>خطأ في الاتصال - {site_name}</b>\n\n⚠️ {str(e)}",
                    parse_mode="HTML")
    
    except Exception as e:
        bot.send_message(
            chat_id,
            f"❌ <b>خطأ أثناء اختبار جلب الكود - {site_name}</b>\n\n"
            f"⚠️ الخطأ: {str(e)}",
            parse_mode="HTML"
        )

def extract_sms(html_text, debug_mode=False):
    soup = BeautifulSoup(html_text, "html.parser")
    messages = []
    
    table = soup.find("table", class_="table")
    if not table:
        all_tables = soup.find_all("table")
        if all_tables:
            table = all_tables[0]
        else:
            return []
        
    tbody = table.find("tbody")
    if not tbody:
        rows = table.find_all("tr")
    else:
        rows = tbody.find_all("tr")
    
    row_count = 0
    for row in rows:
        tds = row.find_all("td")
        if not tds:
            continue
        
        row_count += 1
        cols = [td.get_text(separator=" ", strip=True) for td in tds]
        
        if debug_mode and row_count <= 3:
            print(f"  صف {row_count}: {len(cols)} عمود - {cols[:8] if len(cols) > 7 else cols}")
        
        if not cols or len(cols) < 5:
            continue
        
        msg = {
            "date": cols[0] if len(cols) > 0 else "",
            "ref": cols[1] if len(cols) > 1 else "",
            "source": cols[2] if len(cols) > 2 else "",
            "client": cols[3] if len(cols) > 3 else "",
            "destination": cols[4] if len(cols) > 4 else "",
            "raw": cols[5] if len(cols) > 5 else (cols[4] if len(cols) > 4 else "")
        }
        
        if msg["date"] and msg["raw"] and len(msg["raw"]) > 3:
            messages.append(msg)
    
    return messages

def normalize_otp_from_text(text):
    if not text: 
        return None
    
    candidates = []
    
    telegram_pattern = r'(?:telegram|تيليجرام|تلجرام)\s*(?:code|كود)?\s*[:\s]*(\d{4,6})'
    match = re.search(telegram_pattern, text, re.IGNORECASE)
    if match:
        digits = match.group(1)
        candidates.append({
            'otp': digits,
            'position': match.start(),
            'confidence': 100
        })
    
    instagram_pattern = r'(\d{3})\s+(\d{3})\s+is\s+your\s+Instagram\s+code'
    match = re.search(instagram_pattern, text, re.IGNORECASE)
    if match:
        digits = match.group(1) + match.group(2)
        candidates.append({
            'otp': f"{digits[:3]} {digits[3:]}",
            'position': match.start(),
            'confidence': 99
        })
    
    code_keyword_pattern = r'(?:code|كود|رمز|verification|تحقق)[:\s]*(\d{4,8})'
    for match in re.finditer(code_keyword_pattern, text, re.IGNORECASE):
        digits = match.group(1)
        if 4 <= len(digits) <= 8:
            candidates.append({
                'otp': digits,
                'position': match.start(),
                'confidence': 95
            })
    
    spaced_triple_pattern = r'(\d{3})\s+(\d{3})'
    for match in re.finditer(spaced_triple_pattern, text):
        digits = match.group(1) + match.group(2)
        if len(digits) == 6:
            candidates.append({
                'otp': f"{digits[:3]} {digits[3:]}",
                'position': match.start(),
                'confidence': 90
            })
    
    high_confidence_pattern = r'(\d)\s+(\d)\s+(\d)\s*-\s*(\d)\s+(\d)\s+(\d)'
    for match in re.finditer(high_confidence_pattern, text):
        digits = re.sub(r'\D', '', match.group(0))
        if len(digits) == 6:
            candidates.append({
                'otp': f"{digits[:3]} {digits[3:]}",
                'position': match.start(),
                'confidence': 85
            })
    
    spaced_digits_pattern = r'(\d)\s+(\d)\s+(\d)\s+(\d)\s+(\d)\s+(\d)'
    for match in re.finditer(spaced_digits_pattern, text):
        digits = re.sub(r'\D', '', match.group(0))
        if len(digits) == 6:
            candidates.append({
                'otp': f"{digits[:3]} {digits[3:]}",
                'position': match.start(),
                'confidence': 80
            })
    
    hyphen_pattern = r'(\d{3})\s*-\s*(\d{3})'
    for match in re.finditer(hyphen_pattern, text):
        digits = re.sub(r'\D', '', match.group(0))
        if len(digits) == 6:
            candidates.append({
                'otp': f"{digits[:3]}-{digits[3:]}",
                'position': match.start(),
                'confidence': 98
            })
    
    
    rtl_whatsapp_pattern = r'[\u200e\u200f\u202a-\u202e]?(\d{3})\s*-\s*(\d{3})'
    for match in re.finditer(rtl_whatsapp_pattern, text):
        digits = match.group(1) + match.group(2)
        if len(digits) == 6:
            candidates.append({
                'otp': f"{match.group(1)}-{match.group(2)}",
                'position': match.start(),
                'confidence': 110
            })

    six_digits_pattern = r'\b\d{6}\b'
    for match in re.finditer(six_digits_pattern, text):
        digits = match.group(0)
        candidates.append({
            'otp': f"{digits[:3]} {digits[3:]}",
            'position': match.start(),
            'confidence': 70
        })
    
    five_digits_pattern = r'\b\d{5}\b'
    for match in re.finditer(five_digits_pattern, text):
        digits = match.group(0)
        candidates.append({
            'otp': digits,
            'position': match.start(),
            'confidence': 65
        })
    
    four_digits_pattern = r'\b\d{4}\b'
    for match in re.finditer(four_digits_pattern, text):
        digits = match.group(0)
        candidates.append({
            'otp': digits,
            'position': match.start(),
            'confidence': 60
        })
    
    if candidates:
        candidates.sort(key=lambda x: (-x['confidence'], x['position']))
        return candidates[0]['otp']
    
    all_digits = re.findall(r'\d+', text)
    for digit_group in reversed(all_digits):
        if len(digit_group) >= 4:
            return digit_group
    
    return None

def extract_from_message(raw_text):
    if not raw_text: 
        return None, None
    
    decoded_text = try_decode(raw_text)
    text = html.unescape(decoded_text)
    otp = normalize_otp_from_text(text)
    
    return otp, text

def clean_number(num_str: str) -> str:
    if num_str is None:
        return ""
    if isinstance(num_str, (int, float)):
        return str(int(num_str))
    return re.sub(r'\D', '', str(num_str))

IDX_DATE_SITE2 = 0
IDX_NUMBER_SITE2 = 2
IDX_SMS_SITE2 = 5

def retry_request_site2(func, max_retries=5, retry_delay=10):
    attempt = 0
    last_error = None
    while attempt < max_retries:
        attempt += 1
        try:
            return func()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_error = e
            backoff = min(60, retry_delay * attempt)
            print(f"⚠️ [Fly sms] محاولة {attempt}/{max_retries} فشلت: {type(e).__name__}")
            print(f"⏳ [Fly sms] انتظار {backoff} ثانية قبل إعادة المحاولة...")
            time.sleep(backoff)
        except requests.exceptions.HTTPError as e:
            last_error = e
            status_code = e.response.status_code if e.response else 0
            if status_code in [502, 503, 504]:
                backoff = min(60, 10 + (attempt * 5))
                print(f"⚠️ [Fly sms] خطأ {status_code} - محاولة {attempt}/{max_retries}")
                print(f"⏳ [Fly sms] السيرفر مشغول، انتظار {backoff} ثانية...")
                time.sleep(backoff)
            elif status_code == 404:
                backoff = min(60, 15 + (attempt * 5))
                print(f"⚠️ [Fly sms] خطأ 404 - محاولة {attempt}/{max_retries}")
                print(f"⏳ [Fly sms] انتظار {backoff} ثانية...")
                time.sleep(backoff)
            else:
                print(f"❌ [Fly sms] خطأ HTTP {status_code}: {e}")
                raise
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "502" in error_str or "504" in error_str or "Service" in error_str:
                last_error = e
                backoff = min(60, 10 + (attempt * 5))
                print(f"⚠️ [Fly sms] خطأ سيرفر - محاولة {attempt}/{max_retries}: {error_str[:100]}")
                print(f"⏳ [Fly sms] انتظار {backoff} ثانية...")
                time.sleep(backoff)
            elif "404" in error_str or "Not Found" in error_str:
                last_error = e
                backoff = min(60, 15 + (attempt * 5))
                print(f"⚠️ [Fly sms] خطأ 404 - محاولة {attempt}/{max_retries}")
                print(f"⏳ [Fly sms] انتظار {backoff} ثانية...")
                time.sleep(backoff)
            else:
                print(f"❌ [Fly sms] خطأ غير متوقع: {e}")
                raise
    
    print(f"❌ [Fly sms] استنفدت جميع المحاولات ({max_retries})")
    if last_error:
        raise last_error
    raise Exception("Max retries exceeded")

def try_decode_site2(raw):
    if raw is None:
        return ""
    
    if isinstance(raw, str):
        cleaned = raw.replace('\x00', '').strip()
        if cleaned:
            return cleaned
        return ""
    
    if isinstance(raw, bytes):
        b = raw
    else:
        text_str = str(raw)
        cleaned = text_str.replace('\x00', '').strip()
        if cleaned:
            return cleaned
        return ""
    
    for enc in ("utf-8", "cp1256", "windows-1256", "iso-8859-6", "utf-16-be", "utf-16-le", "latin-1"):
        try:
            s = b.decode(enc, errors='ignore')
            cleaned = s.replace('\x00', '').strip()
            if cleaned:
                return cleaned
        except:
            continue
    
    return b.decode('utf-8', errors='replace').replace('\x00', '').strip()

def clean_html_site2(text):
    if text is None or text == "":
        return ""
    try:
        text = str(text) if not isinstance(text, str) else text
        text = re.sub(r'<[^>]+>', '', text)
        text = html.unescape(text)
        text = text.replace('\x00', '').strip()
        return text
    except Exception as e:
        print(f"[Site2] ⚠️ خطأ في clean_html: {e} - القيمة: {repr(text)}")
        try:
            return str(text) if text else ""
        except:
            return ""




def solve_captcha_timesms(html_content):
    match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)\s*=?\s*\?', html_content)
    if match:
        n1, op, n2 = int(match.group(1)), match.group(2), int(match.group(3))
        if op == '+': return str(n1 + n2)
        elif op == '-': return str(n1 - n2)
        elif op == '*': return str(n1 * n2)
        elif op == '/': return str(n1 // n2) if n2 else '0'
    return None

def login_site10(account=None):
    global is_logged_in_site10, session10
    print("[TimeSMS] 🔄 محاولة تسجيل الدخول...")
    
    site_key = "TimeSMS"
    if account:
        user = account.get("username")
        pw = account.get("password")
        sess = requests.Session()
        sess.headers.update(session10.headers)
    else:
        user = USERNAME10
        pw = PASSWORD10
        sess = session10

    login_url = SETTINGS[site_key]["login_page_url"]
    submit_url = SETTINGS[site_key]["login_post_url"]

    try:
        resp = sess.get(login_url, timeout=15)
        captcha = solve_captcha_timesms(resp.text)
        if not captcha:
            print("[TimeSMS] ❌ فشل حل الكابتشا")
            return False
        
        data = {'username': user, 'password': pw, 'capt': captcha}
        login_resp = sess.post(submit_url, data=data, headers={'Referer': login_url}, timeout=15, allow_redirects=True)
        
        if 'login' not in str(login_resp.url).lower():
            if not account: is_logged_in_site10 = True
            print("[TimeSMS] ✅ تم تسجيل الدخول بنجاح")
            return sess if account else True
    except Exception as e:
        print(f"[TimeSMS] ❌ خطأ في تسجيل الدخول: {e}")
    return False

def login_site14(account=None):
    global is_logged_in_site14, session14
    site_label = "Seven1Tel"
    print(f"[{site_label}] 🔄 محاولة تسجيل الدخول...")

    user = account.get("username") if account else USERNAME14
    pw   = account.get("password") if account else PASSWORD14
    sess = requests.Session() if account else session14
    sess.headers.update(session14.headers)

    try:
        resp = sess.get(LOGIN_PAGE_URL14, timeout=HTTP_TIMEOUT14)
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if match:
            captcha = str(int(match.group(1)) + int(match.group(2)))
        else:
            captcha = None

        csrf_token = None
        m = re.search(r'name=["\'"]_token["\'"].*?value=["\'"]([^"\']+)["\'"]', resp.text)
        if m:
            csrf_token = m.group(1)
        else:
            m = re.search(r'value=["\'"]([^"\']+)["\'"].*?name=["\'"]_token["\'"]', resp.text)
            if m:
                csrf_token = m.group(1)

        payload = {'username': user, 'password': pw}
        if captcha:
            payload['capt'] = captcha
        if csrf_token:
            payload['_token'] = csrf_token

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': LOGIN_PAGE_URL14,
            'Origin': BASE_URL14,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        r = sess.post(LOGIN_POST_URL14, data=payload, headers=headers,
                      timeout=HTTP_TIMEOUT14, allow_redirects=True)

        success = ("agent" in r.url.lower() or
                   any(k in r.text.lower() for k in ["dashboard", "logout", "smscdr"]) or
                   ("login" not in r.url.lower() and "signin" not in r.url.lower()))
        if success:
            if not account:
                is_logged_in_site14 = True
            print(f"[{site_label}] ✅ تم تسجيل الدخول بنجاح")
            return sess if account else True
        else:
            print(f"[{site_label}] ❌ فشل تسجيل الدخول")
            return False
    except Exception as e:
        print(f"[{site_label}] ❌ خطأ في تسجيل الدخول: {e}")
        return False


def login_site15(account=None):
    global is_logged_in_site15, session15
    site_label = "Gaza SMS"
    print(f"[{site_label}] 🔄 محاولة تسجيل الدخول...")

    user = account.get("username") if account else USERNAME15
    pw   = account.get("password") if account else PASSWORD15
    sess = requests.Session() if account else session15
    sess.headers.update(session15.headers)

    try:
        resp = sess.get(LOGIN_PAGE_URL15, timeout=HTTP_TIMEOUT15)
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if match:
            captcha = str(int(match.group(1)) + int(match.group(2)))
        else:
            captcha = None

        csrf_token = None
        m = re.search(r'name=["\'"]_token["\'"].*?value=["\'"]([^"\'"]+)["\'"]', resp.text)
        if m:
            csrf_token = m.group(1)
        else:
            m = re.search(r'value=["\'"]([^"\'"]+)["\'"].*?name=["\'"]_token["\'"]', resp.text)
            if m:
                csrf_token = m.group(1)

        payload = {'username': user, 'password': pw}
        if captcha:
            payload['capt'] = captcha
        if csrf_token:
            payload['_token'] = csrf_token

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': LOGIN_PAGE_URL15,
            'Origin': BASE_URL15,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        r = sess.post(LOGIN_POST_URL15, data=payload, headers=headers,
                      timeout=HTTP_TIMEOUT15, allow_redirects=True)

        success = ("agent" in r.url.lower() or
                   any(k in r.text.lower() for k in ["dashboard", "logout", "smscdr"]) or
                   ("login" not in r.url.lower() and "signin" not in r.url.lower()))
        if success:
            if not account:
                is_logged_in_site15 = True
            print(f"[{site_label}] ✅ تم تسجيل الدخول بنجاح")
            return sess if account else True
        else:
            print(f"[{site_label}] ❌ فشل تسجيل الدخول")
            return False
    except Exception as e:
        print(f"[{site_label}] ❌ خطأ في تسجيل الدخول: {e}")
        return False




def login_generic_ints(site_key, account=None):
    """Generic login function for standard /ints/ panels like Km sms"""
    site_label = SETTINGS[site_key]["name"]
    print(f"[{site_label}] 🔄 محاولة تسجيل الدخول...")

    user = account.get("username") if account else SETTINGS[site_key].get("accounts", [{}])[0].get("username", "")
    pw   = account.get("password") if account else SETTINGS[site_key].get("accounts", [{}])[0].get("password", "")
    base_url = SETTINGS[site_key]["base_url"]
    login_page = SETTINGS[site_key]["login_page_url"]
    login_post = SETTINGS[site_key]["login_post_url"]
    timeout = SETTINGS[site_key].get("timeout", 30)

    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": base_url + "/ints/agent/SMSCDRReports",
        "Accept-Language": "ar-EG,ar;q=0.9,en-US;q=0.8"
    })

    try:
        resp = sess.get(login_page, timeout=timeout)
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        captcha = str(int(match.group(1)) + int(match.group(2))) if match else None

        payload = {'username': user, 'password': pw}
        if captcha:
            payload['capt'] = captcha

        crlf = re.search(r"name=['\"]crlf['\"].*?value=['\"]([^'\"]+)['\"]", resp.text)
        if not crlf:
            crlf = re.search(r"value=['\"]([^'\"]+)['\"].*?name=['\"]crlf['\"]", resp.text)
        if crlf:
            payload['crlf'] = crlf.group(1)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': login_page,
            'Origin': base_url,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        r = sess.post(login_post, data=payload, headers=headers, timeout=timeout, allow_redirects=True)

        success = (any(k in r.text.lower() for k in ["dashboard", "logout", "agent", "reports", "smscdr"]) or
                   any(k in r.url.lower() for k in ["dashboard", "agent", "reports"]) or
                   r.url != login_page)
        if success:
            print(f"[{site_label}] ✅ تم تسجيل الدخول بنجاح")
            return sess if account else True
        else:
            print(f"[{site_label}] ❌ فشل تسجيل الدخول")
            return False
    except Exception as e:
        print(f"[{site_label}] ❌ خطأ في تسجيل الدخول: {e}")
        return False


def login_site12(account=None):
    global is_logged_in_site12, session12
    site_label = "hadi"
    print(f"[{site_label}] 🔄 محاولة تسجيل الدخول...")

    user = account.get("username") if account else USERNAME12
    pw   = account.get("password") if account else PASSWORD12
    sess = requests.Session() if account else session12
    sess.headers.update(session12.headers)

    try:
        resp = sess.get(LOGIN_PAGE_URL12, timeout=HTTP_TIMEOUT12)
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if match:
            captcha = str(int(match.group(1)) + int(match.group(2)))
        else:
            captcha = None

        payload = {'username': user, 'password': pw}
        if captcha:
            payload['capt'] = captcha

        crlf = re.search(r"name=['\"]crlf['\"].*?value=['\"]([^'\"]+)['\"]", resp.text)
        if not crlf:
            crlf = re.search(r"value=['\"]([^'\"]+)['\"].*?name=['\"]crlf['\"]", resp.text)
        if crlf:
            payload['crlf'] = crlf.group(1)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': LOGIN_PAGE_URL12,
            'Origin': BASE_URL12,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        r = sess.post(LOGIN_POST_URL12, data=payload, headers=headers,
                      timeout=HTTP_TIMEOUT12, allow_redirects=True)

        success = (any(k in r.text.lower() for k in ["dashboard", "logout", "agent", "reports", "smscdr"]) or
                   any(k in r.url.lower() for k in ["dashboard", "agent", "reports"]) or
                   r.url != LOGIN_PAGE_URL12)
        if success:
            if not account:
                is_logged_in_site12 = True
            print(f"[{site_label}] ✅ تم تسجيل الدخول بنجاح")
            return sess if account else True
        else:
            print(f"[{site_label}] ❌ فشل تسجيل الدخول")
            return False
    except Exception as e:
        print(f"[{site_label}] ❌ خطأ في تسجيل الدخول: {e}")
        return False


def login_site13(account=None):
    global is_logged_in_site13, session13
    site_label = "fire"
    print(f"[{site_label}] 🔄 محاولة تسجيل الدخول...")

    user = account.get("username") if account else USERNAME13
    pw   = account.get("password") if account else PASSWORD13
    sess = requests.Session() if account else session13
    sess.headers.update(session13.headers)

    try:
        resp = sess.get(LOGIN_PAGE_URL13, timeout=HTTP_TIMEOUT13)
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if match:
            captcha = str(int(match.group(1)) + int(match.group(2)))
        else:
            captcha = None

        payload = {'username': user, 'password': pw}
        if captcha:
            payload['capt'] = captcha

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': LOGIN_PAGE_URL13,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        r = sess.post(LOGIN_POST_URL13, data=payload, headers=headers,
                      timeout=HTTP_TIMEOUT13, allow_redirects=True)

        success = (any(k in r.text.lower() for k in ["dashboard", "logout", "agent", "reports", "smscdr"]) or
                   any(k in r.url.lower() for k in ["dashboard", "agent", "reports"]) or
                   r.url != LOGIN_PAGE_URL13)
        if success:
            if not account:
                is_logged_in_site13 = True
            print(f"[{site_label}] ✅ تم تسجيل الدخول بنجاح")
            return sess if account else True
        else:
            print(f"[{site_label}] ❌ فشل تسجيل الدخول")
            return False
    except Exception as e:
        print(f"[{site_label}] ❌ خطأ في تسجيل الدخول: {e}")
        return False


def get_sesskey_site2():
    """استخراج sesskey أو _token من صفحة التقارير لـ Fly sms"""
    try:
        resp = session2.get(BASE_URL2 + "/ints/agent/SMSCDRReports", timeout=HTTP_TIMEOUT2)
        if resp.status_code != 200:
            print(f"[Fly sms] ⚠️ فشل جلب صفحة التقارير: {resp.status_code}")
            return None
        
        # البحث عن sesskey في الروابط (نمط قديم)
        match = re.search(r'sesskey=([A-Za-z0-9=]+)', resp.text)
        if match:
            print(f"[Fly sms] ✅ تم استخراج sesskey: {match.group(1)[:10]}...")
            return match.group(1)
        
        # البحث عن CSRF token (نمط جديد)
        match = re.search(r'name="_token".*?value="([^"]+)"', resp.text)
        if match:
            print(f"[Fly sms] ✅ تم استخراج _token: {match.group(1)[:10]}...")
            return match.group(1)
            
        print("[Fly sms] ❌ لم يتم العثور على sesskey أو _token في صفحة التقارير")
        return None
    except Exception as e:
        print(f"[Fly sms] ❌ خطأ في جلب sesskey: {e}")
        return None

def login_site2():
    global is_logged_in_site2, sesskey_site2
    print("[Fly sms] 🔄 محاولة تسجيل الدخول...")
    
    session2.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    })
    
    def do_login():
        try:
            resp = session2.get(LOGIN_PAGE_URL2, timeout=HTTP_TIMEOUT2)
            
            if resp.status_code in [502, 503, 504]:
                print(f"[Fly sms] ⚠️ السيرفر مشغول ({resp.status_code})")
                raise requests.exceptions.HTTPError(f"{resp.status_code} Server Error", response=resp)
            
            match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
            if not match:
                print("[Fly sms] ⚠️ لم يتم العثور على captcha في صفحة تسجيل الدخول")
                if resp.status_code != 200:
                    raise Exception(f"HTTP {resp.status_code}")
                return False
            
            num1, num2 = int(match.group(1)), int(match.group(2))
            captcha_answer = num1 + num2
            print(f"[Fly sms] 🧮 حل captcha: {num1} + {num2} = {captcha_answer}")
            
            payload = {
                "username": USERNAME2,
                "password": PASSWORD2,
                "capt": str(captcha_answer)
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": LOGIN_PAGE_URL2,
                "Origin": BASE_URL2,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            
            print(f"[Fly sms] 📤 إرسال طلب تسجيل الدخول لـ: {USERNAME2}")
            
            resp = session2.post(LOGIN_POST_URL2, data=payload, headers=headers, timeout=HTTP_TIMEOUT2, allow_redirects=True)
            
            print(f"[Fly sms] 📊 حالة الاستجابة: {resp.status_code}")
            
            if resp.status_code in [502, 503, 504]:
                print(f"[Fly sms] ⚠️ السيرفر مشغول ({resp.status_code})")
                raise requests.exceptions.HTTPError(f"{resp.status_code} Server Error", response=resp)
            
            if ("dashboard" in resp.text.lower() or 
                "logout" in resp.text.lower() or 
                "agent" in resp.url.lower() or
                "/ints/agent" in resp.url or
                resp.url != LOGIN_PAGE_URL2):
                print("[Fly sms] ✅ تم تسجيل الدخول بنجاح")
                is_logged_in_site2 = True
                
                # استخراج sesskey فوراً بعد تسجيل الدخول
                global sesskey_site2
                sesskey_site2 = get_sesskey_site2()
                
                return True
            else:
                print("[Fly sms] ❌ فشل تسجيل الدخول")
                if "incorrect" in resp.text.lower() or "invalid" in resp.text.lower():
                    print("[Fly sms] ⚠️ اسم المستخدم أو كلمة المرور غير صحيحة")
                return False
                
        except requests.exceptions.HTTPError as e:
            print(f"[Fly sms] ⚠️ خطأ HTTP: {e}")
            raise
        except Exception as e:
            print(f"[Fly sms] ❌ خطأ في تسجيل الدخول: {e}")
            raise
    
    try:
        return retry_request_site2(do_login, max_retries=5, retry_delay=15)
    except:
        return False

def build_ajax_url_site2(wide_range=False):
    if wide_range:
        start_date = date.today() - timedelta(days=5)
        end_date = date.today() + timedelta(days=1)
    else:
        start_date = date.today()
        end_date = date.today() + timedelta(days=1)
    
    fdate1 = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
    fdate2 = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"
    
    # بناء بيانات POST بدلاً من GET لـ Fly sms
    post_data = {
        "fdate1": fdate1,
        "fdate2": fdate2,
        "frange": "",
        "fclient": "",
        "fnum": "",
        "fcli": "",
        "fgdate": "",
        "fgmonth": "",
        "fgrange": "",
        "fgclient": "",
        "fgnumber": "",
        "fgcli": "",
        "fg": "0",
        "sesskey": sesskey_site2 if sesskey_site2 else ""
    }
    return BASE_URL2 + AJAX_PATH2, post_data

def fetch_ajax_json_site2(url_data):
    global is_logged_in_site2, sesskey_site2
    
    def do_fetch():
        global sesskey_site2
        # التأكد من وجود sesskey قبل جلب البيانات
        if not sesskey_site2:
            print("[Fly sms] ⚠️ لا يوجد sesskey متاح. محاولة استخراجه.")
            sesskey_site2 = get_sesskey_site2()
            if not sesskey_site2:
                raise Exception("Session expired")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": BASE_URL2 + "/ints/agent/SMSCDRReports",
            "Origin": BASE_URL2
        }
        
        ajax_url, post_data = url_data
        # تحديث sesskey في البيانات قبل الإرسال
        post_data["sesskey"] = sesskey_site2 if sesskey_site2 else ""
        
        r = session2.post(ajax_url, data=post_data, timeout=HTTP_TIMEOUT2, headers=headers)
        
        if r.status_code == 403:
            raise Exception("Session expired")
        
        if r.status_code in [502, 503, 504]:
            raise requests.exceptions.HTTPError(f"{r.status_code} Server Error", response=r)
        
        if r.status_code == 401:
            raise Exception("Session expired")
        
        r.raise_for_status()
        
        try:
            data = r.json()
            if not isinstance(data, (dict, list)):
                raise Exception("Invalid JSON response")
            return data
        except (json.JSONDecodeError, ValueError) as e:
            if "login" in r.text.lower() and r.url and "login" in r.url.lower():
                raise Exception("Session expired")
            raise
    
    try:
        return retry_request_site2(do_fetch, max_retries=5, retry_delay=10)
    except Exception as e:
        error_str = str(e)
        if "Session expired" in error_str:
            print("[Fly sms] ⚠️ انتهت صلاحية الجلسة. إعادة تسجيل الدخول...")
            is_logged_in_site2 = False
            if login_site2():
                is_logged_in_site2 = True
                try:
                    return retry_request_site2(do_fetch, max_retries=5, retry_delay=10)
                except:
                    return None
            else:
                return None
        if "503" in error_str or "502" in error_str or "504" in error_str:
            print(f"[Fly sms] ⚠️ السيرفر مشغول، المحاولة مرة أخرى بعد فترة...")
            time.sleep(30)
            try:
                return retry_request_site2(do_fetch, max_retries=3, retry_delay=15)
            except:
                return None
        print(f"[Fly sms] ❌ خطأ في جلب/تحليل AJAX: {e}")
        return None

def extract_rows_from_json_site2(j):
    if j is None:
        return []
    for key in ("data", "aaData", "rows", "aa_data"):
        if isinstance(j, dict) and key in j:
            return j[key]
    if isinstance(j, list):
        return j
    if isinstance(j, dict):
        for v in j.values():
            if isinstance(v, list):
                return v
    return []

def row_to_tuple_site2(row):
    date_str = ""
    number_str = ""
    sms_str = ""
    try:
        if isinstance(row, (list, tuple)):
            if len(row) > IDX_DATE_SITE2:
                val = row[IDX_DATE_SITE2]
                date_str = clean_html_site2(str(val) if val is not None else "")
            if len(row) > IDX_NUMBER_SITE2:
                val = row[IDX_NUMBER_SITE2]
                number_str = clean_number(str(val) if val is not None else "")
            if len(row) > IDX_SMS_SITE2:
                val = row[IDX_SMS_SITE2]
                sms_str = try_decode_site2(val) if val is not None else ""
                sms_str = clean_html_site2(sms_str)
        elif isinstance(row, dict):
            for k in ("date","time","datetime","dt","created_at"):
                if k in row and not date_str:
                    val = row[k]
                    date_str = clean_html_site2(str(val) if val is not None else "")
            for k in ("number","msisdn","cli","from","sender"):
                if k in row and not number_str:
                    val = row[k]
                    number_str = clean_number(str(val) if val is not None else "")
            for k in ("sms","message","msg","body","text"):
                if k in row and not sms_str:
                    val = row[k]
                    sms_str = try_decode_site2(val) if val is not None else ""
                    sms_str = clean_html_site2(sms_str)
            if not sms_str:
                vals = list(row.values())
                if len(vals) > IDX_SMS_SITE2:
                    val = vals[IDX_SMS_SITE2]
                    sms_str = try_decode_site2(val) if val is not None else ""
                    sms_str = clean_html_site2(sms_str)
                elif vals:
                    val = vals[-1]
                    sms_str = try_decode_site2(val) if val is not None else ""
                    sms_str = clean_html_site2(sms_str)
    except Exception as e:
        print(f"[Site2] ⚠️ خطأ في row_to_tuple: {e}")
        print(f"[Site2] Row data: {row}")
    
    unique_key = f"{date_str}|{number_str}|{sms_str}"
    return date_str, number_str, sms_str, unique_key

def load_last_seen_key_site2():
    global last_seen_key_site2
    if os.path.exists(LAST_MESSAGE_FILE_SITE2):
        try:
            with open(LAST_MESSAGE_FILE_SITE2, "r", encoding="utf-8") as f:
                last_seen_key_site2 = f.read().strip()
                print(f"[Site2] 📋 تم تحميل آخر رسالة مشاهدة: {last_seen_key_site2[:50]}..." if last_seen_key_site2 else "[Site2] 📋 لا توجد رسائل سابقة")
        except:
            last_seen_key_site2 = ""
    else:
        last_seen_key_site2 = ""

def save_last_seen_key_site2():
    try:
        with open(LAST_MESSAGE_FILE_SITE2, "w", encoding="utf-8") as f:
            f.write(last_seen_key_site2)
        print(f"[Site2] 💾 تم حفظ آخر رسالة مشاهدة")
    except Exception as e:
        print(f"[Site2] ❌ خطأ في حفظ آخر رسالة: {str(e)}")

def load_data():
    global COUNTRIES, CHANNELS, USERS, ADMINS, BANNED, OTP_GROUP, GROUPS, REFERRALS, NUMBERS_ADMINS

    if os.path.exists(COUNTRIES_FILE):
        with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
            COUNTRIES = json.load(f)

    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            CHANNELS = json.load(f)

    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            USERS = json.load(f)

    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            ADMINS = json.load(f)

    if MAIN_ADMIN_ID != 0 and MAIN_ADMIN_ID not in ADMINS:
        ADMINS.append(MAIN_ADMIN_ID)
        save_admins()

    if os.path.exists(BANNED_FILE):
        with open(BANNED_FILE, "r", encoding="utf-8") as f:
            BANNED = json.load(f)

    if os.path.exists(OTP_GROUP_FILE):
        with open(OTP_GROUP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            OTP_GROUP = data.get("group_id")

    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            GROUPS = json.load(f)
    
    if os.path.exists(REFERRALS_FILE):
        with open(REFERRALS_FILE, "r", encoding="utf-8") as f:
            REFERRALS = json.load(f)
    
    load_numbers_admins()
    load_statistics()


def save_countries():
    with open(COUNTRIES_FILE, "w", encoding="utf-8") as f:
        json.dump(COUNTRIES, f, indent=2, ensure_ascii=False)

def save_channels():
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(CHANNELS, f, indent=2, ensure_ascii=False)

def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(USERS, f, indent=2, ensure_ascii=False)

def save_admins():
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(ADMINS, f, indent=2, ensure_ascii=False)

def save_banned():
    with open(BANNED_FILE, "w", encoding="utf-8") as f:
        json.dump(BANNED, f, indent=2, ensure_ascii=False)

def save_otp_group():
    with open(OTP_GROUP_FILE, "w", encoding="utf-8") as f:
        json.dump({"group_id": OTP_GROUP}, f, indent=2)

def save_groups():
    with open(GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(GROUPS, f, indent=2)

def cleanup_old_numbers_files(country_code):
   
    pass

def load_referrals():
    global REFERRALS
    if os.path.exists(REFERRALS_FILE):
        try:
            with open(REFERRALS_FILE, "r", encoding="utf-8") as f:
                REFERRALS = json.load(f)
        except:
            REFERRALS = {}
    return REFERRALS

def save_referrals(data=None):
    global REFERRALS
    if data:
        REFERRALS = data
    with open(REFERRALS_FILE, "w", encoding="utf-8") as f:
        json.dump(REFERRALS, f, indent=2, ensure_ascii=False)

def load_referral_settings():
    if os.path.exists(REFERRAL_SETTINGS_FILE):
        try:
            with open(REFERRAL_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_REFERRAL_SETTINGS.copy()

def save_referral_settings(settings):
    with open(REFERRAL_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

def load_withdrawal_requests():
    if os.path.exists(WITHDRAWAL_REQUESTS_FILE):
        try:
            with open(WITHDRAWAL_REQUESTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_withdrawal_requests(requests):
    with open(WITHDRAWAL_REQUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(requests, f, indent=2, ensure_ascii=False)

DEFAULT_WITHDRAWAL_METHODS = {
    "vodafone": {"name_ar": "فودافون كاش", "name_en": "Vodafone Cash", "enabled": True, "details_ar": "رقم الهاتف", "details_en": "Phone number"},
    "usdt_trc20": {"name_ar": "USDT (TRC20)", "name_en": "USDT (TRC20)", "enabled": True, "details_ar": "عنوان محفظة TRC20", "details_en": "TRC20 wallet address"},
    "usdt_bep20": {"name_ar": "USDT (BEP20)", "name_en": "USDT (BEP20)", "enabled": True, "details_ar": "عنوان محفظة BEP20", "details_en": "BEP20 wallet address"},
    "binance_id": {"name_ar": "Binance ID", "name_en": "Binance ID", "enabled": True, "details_ar": "Binance Pay ID أو Email", "details_en": "Binance Pay ID or Email"}
}

def load_withdrawal_methods():
    if os.path.exists(WITHDRAWAL_METHODS_FILE):
        try:
            with open(WITHDRAWAL_METHODS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_WITHDRAWAL_METHODS.copy()

def save_withdrawal_methods(methods):
    with open(WITHDRAWAL_METHODS_FILE, "w", encoding="utf-8") as f:
        json.dump(methods, f, indent=2, ensure_ascii=False)

def load_welcome_messages():
    if os.path.exists(WELCOME_MESSAGES_FILE):
        try:
            with open(WELCOME_MESSAGES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_WELCOME_MESSAGES.copy()

def save_welcome_messages(messages):
    with open(WELCOME_MESSAGES_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

def load_subscription_image():
    """Load subscription image URL"""
    if os.path.exists(SUBSCRIPTION_IMAGE_FILE):
        try:
            with open(SUBSCRIPTION_IMAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"image_url": None}

def save_subscription_image(data):
    with open(SUBSCRIPTION_IMAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def load_subscription_settings():
    """Load subscription message and button settings"""
    if os.path.exists(SUBSCRIPTION_SETTINGS_FILE):
        try:
            with open(SUBSCRIPTION_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "message": None,  # None = use default
        "button_text": "Subscribed",
        "button_color": "danger"
    }

def save_subscription_settings(data):
    with open(SUBSCRIPTION_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def generate_referral_code(user_id):
    
    import hashlib
    hash_input = f"{user_id}_{datetime.now().timestamp()}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:8].upper()

def get_user_referral_data(user_id):
    
    global REFERRALS
    REFERRALS = load_referrals()
    user_key = str(user_id)
    if user_key not in REFERRALS:
        REFERRALS[user_key] = {
            "referral_code": generate_referral_code(user_id),
            "referred_by": None,
            "referrals": [],
            "referred_users_codes": {},
            "active_referrals": 0,
            "active_referrals_list": [],
            "codes_received": 0,
            "balance": 0.0,
            "total_earned": 0.0,
            "referral_used": False
        }
        save_referrals(REFERRALS)
    else:
        if "referral_code" not in REFERRALS[user_key]:
            REFERRALS[user_key]["referral_code"] = generate_referral_code(user_id)
            save_referrals(REFERRALS)
        if "referred_users_codes" not in REFERRALS[user_key]:
            REFERRALS[user_key]["referred_users_codes"] = {}
            save_referrals(REFERRALS)
        if "active_referrals_list" not in REFERRALS[user_key]:
            REFERRALS[user_key]["active_referrals_list"] = []
            save_referrals(REFERRALS)
    return REFERRALS[user_key]

def process_referral(user_id, referrer_id):
    
    global REFERRALS
    REFERRALS = load_referrals()
    settings = load_referral_settings()
    
    user_key = str(user_id)
    referrer_key = str(referrer_id)
    
    if user_key not in REFERRALS:
        REFERRALS[user_key] = {
            "referred_by": referrer_key,
            "referrals": [],
            "active_referrals": 0,
            "codes_received": 0,
            "balance": 0.0,
            "total_earned": 0.0
        }
    else:
        if REFERRALS[user_key].get("referred_by"):
            return False
        REFERRALS[user_key]["referred_by"] = referrer_key
    
    if referrer_key not in REFERRALS:
        REFERRALS[referrer_key] = {
            "referred_by": None,
            "referrals": [],
            "active_referrals": 0,
            "codes_received": 0,
            "balance": 0.0,
            "total_earned": 0.0
        }
    
    if user_key not in REFERRALS[referrer_key]["referrals"]:
        REFERRALS[referrer_key]["referrals"].append(user_key)
    
    save_referrals(REFERRALS)
    return True

def add_code_bonus(user_id):
    
    global REFERRALS
    REFERRALS = load_referrals()
    settings = load_referral_settings()
    
    user_key = str(user_id)
    if user_key not in REFERRALS:
        REFERRALS[user_key] = {
            "referred_by": None,
            "referrals": [],
            "active_referrals": 0,
            "codes_received": 0,
            "balance": 0.0,
            "total_earned": 0.0
        }
    
    REFERRALS[user_key]["codes_received"] += 1
    code_bonus = settings.get("code_bonus", 0.01)
    REFERRALS[user_key]["balance"] += code_bonus
    REFERRALS[user_key]["total_earned"] += code_bonus
    
    referrer_key = REFERRALS[user_key].get("referred_by")
    if referrer_key and referrer_key in REFERRALS:
        codes_required = settings.get("codes_required_for_referral", 3)
        user_codes = REFERRALS[user_key]["codes_received"]
        
        if user_codes == codes_required:
            REFERRALS[referrer_key]["active_referrals"] += 1
            referral_bonus = settings.get("referral_bonus", 0.50)
            REFERRALS[referrer_key]["balance"] += referral_bonus
            REFERRALS[referrer_key]["total_earned"] += referral_bonus
                     
            try:
                referrer_lang = get_user_language(int(referrer_key))
                if referrer_lang == "ar":
                    notify_msg = (
                        f"🎉 <b>تهانينا! إحالة جديدة نشطة!</b>\n\n"
                        f"👤 المستخدم <code>{user_id}</code> أصبح إحالة نشطة!\n"
                        f"💰 تم إضافة <b>${referral_bonus:.2f}</b> لرصيدك!\n\n"
                        f"📊 إجمالي الإحالات النشطة: <b>{REFERRALS[referrer_key]['active_referrals']}</b>\n"
                        f"💵 رصيدك الحالي: <b>${REFERRALS[referrer_key]['balance']:.2f}</b>"
                    )
                else:
                    notify_msg = (
                        f"🎉 <b>Congratulations! New Active Referral!</b>\n\n"
                        f"👤 User <code>{user_id}</code> became an active referral!\n"
                        f"💰 <b>${referral_bonus:.2f}</b> added to your balance!\n\n"
                        f"📊 Total active referrals: <b>{REFERRALS[referrer_key]['active_referrals']}</b>\n"
                        f"💵 Your current balance: <b>${REFERRALS[referrer_key]['balance']:.2f}</b>"
                    )
                bot.send_message(int(referrer_key), notify_msg, parse_mode="HTML")
            except Exception as notify_err:
                print(f"⚠️ خطأ في إرسال إشعار الإحالة: {notify_err}")
    
    save_referrals(REFERRALS)

REFERRAL_SETTINGS = load_referral_settings()
WELCOME_MESSAGES = load_welcome_messages()

def load_statistics():
    global STATISTICS
    if os.path.exists(STATISTICS_FILE):
        try:
            with open(STATISTICS_FILE, 'r', encoding='utf-8') as f:
                STATISTICS = json.load(f)
        except:
            pass

def save_statistics():
    with open(STATISTICS_FILE, 'w', encoding='utf-8') as f:
        json.dump(STATISTICS, f, indent=2, ensure_ascii=False)

def update_statistics():
    global STATISTICS
    today = datetime.now().date().isoformat()
    week_num = datetime.now().isocalendar()[1]
    month = datetime.now().strftime('%Y-%m')
    
    if STATISTICS.get("last_reset_day") != today:
        STATISTICS["codes_today"] = 0
        STATISTICS["last_reset_day"] = today
    
    if STATISTICS.get("last_reset_week") != week_num:
        STATISTICS["codes_this_week"] = 0
        STATISTICS["last_reset_week"] = week_num
    
    if STATISTICS.get("last_reset_month") != month:
        STATISTICS["codes_this_month"] = 0
        STATISTICS["last_reset_month"] = month
    
    STATISTICS["total_codes"] += 1
    STATISTICS["codes_today"] += 1
    STATISTICS["codes_this_week"] += 1
    STATISTICS["codes_this_month"] += 1
    
    if today not in STATISTICS.get("daily_history", {}):
        if "daily_history" not in STATISTICS:
            STATISTICS["daily_history"] = {}
        STATISTICS["daily_history"][today] = 0
    STATISTICS["daily_history"][today] += 1
    
    save_statistics()

def get_statistics_text():
    total_users = len(USERS)
    total_codes = STATISTICS.get("total_codes", 0)
    codes_today = STATISTICS.get("codes_today", 0)
    codes_week = STATISTICS.get("codes_this_week", 0)
    codes_month = STATISTICS.get("codes_this_month", 0)
    
    text = f"📊 <b>إحصائيات البوت</b>\n\n"
    text += f"👥 <b>إجمالي المستخدمين:</b> {total_users}\n"
    text += f"🔢 <b>إجمالي الأكواد:</b> {total_codes}\n\n"
    text += f"📅 <b>أكواد اليوم:</b> {codes_today}\n"
    text += f"📆 <b>أكواد هذا الأسبوع:</b> {codes_week}\n"
    text += f"📊 <b>أكواد هذا الشهر:</b> {codes_month}\n"
    
    return text

def is_admin(user_id):
    return user_id in ADMINS

def is_banned(user_id):
    return user_id in BANNED

def check_subscription(user_id):

    if not CHANNELS:
        return []

    not_joined = []

    for channel in CHANNELS:

        try:

            member = bot.get_chat_member(
                channel['id'],
                user_id
            )

            if member.status not in [
                'member',
                'administrator',
                'creator'
            ]:

                not_joined.append(channel)

        except Exception as e:

            err_msg = str(e).lower()

            if (
                "member list is inaccessible" in err_msg
                or "chat not found" in err_msg
            ):

                print(
                    f"⚠️ Warning: Channel {channel['id']} inaccessible: {e}"
                )

                continue

            not_joined.append(channel)

    return not_joined

def get_subscription_message(user_id=None):
    settings = load_subscription_settings()
    custom_msg = settings.get("message")
    if custom_msg:
        return custom_msg
    lang = get_user_language(user_id) if user_id else "en"
    msgs = {
        "ar": (
            "═══《 <tg-emoji emoji-id='5244807637157029775'>🚫</tg-emoji> مطلوب 》═══\n\n"
            "<tg-emoji emoji-id='5197304993920616826'>📣</tg-emoji> يجب عليك الاشتراك في جميع القنوات المطلوبة للمتابعة\n\n"
            "<tg-emoji emoji-id='5237828920891427376'>💡</tg-emoji> بعد الانضمام، اضغط زر الاشتراك أدناه للمتابعة"
        ),
        "ru": (
            "═══《 <tg-emoji emoji-id='5244807637157029775'>🚫</tg-emoji> ТРЕБОВАНИЕ 》═══\n\n"
            "<tg-emoji emoji-id='5197304993920616826'>📣</tg-emoji> Вы должны подписаться на все необходимые каналы для продолжения\n\n"
            "<tg-emoji emoji-id='5237828920891427376'>💡</tg-emoji> После вступления нажмите кнопку ниже для продолжения"
        ),
        "bn": (
            "═══《 <tg-emoji emoji-id='5244807637157029775'>🚫</tg-emoji> প্রয়োজন 》═══\n\n"
            "<tg-emoji emoji-id='5197304993920616826'>📣</tg-emoji> চালিয়ে যেতে সকল প্রয়োজনীয় চ্যানেলে যোগ দিতে হবে\n\n"
            "<tg-emoji emoji-id='5237828920891427376'>💡</tg-emoji> যোগ দেওয়ার পরে নিচের বোতামটি চাপুন"
        ),
    }
    return msgs.get(lang, "═══《 <tg-emoji emoji-id='5244807637157029775'>🚫</tg-emoji> REQUIREMENT 》═══\n\n<tg-emoji emoji-id='5197304993920616826'>📣</tg-emoji> You must subscribe to all required channels to continue  \n\n<tg-emoji emoji-id='5237828920891427376'>💡</tg-emoji> After joining, press the Subscribed button below to proceed")

def get_full_subscription_keyboard(user_id=None):
    settings = load_subscription_settings()
    btn_text = settings.get("button_text", "Subscribed")
    btn_color = settings.get("button_color", "danger")
    markup = InlineKeyboardMarkup(row_width=1)
    for ch in CHANNELS:
        try:
            chat = bot.get_chat(ch['id'])
            url = None
            if chat.invite_link:
                url = chat.invite_link
            elif chat.username:
                url = f"https://t.me/{chat.username}"
            if url:
                try:
                    markup.add(InlineKeyboardButton(f" {ch['name']}", url=url, icon_custom_emoji_id="5458603043203327669", style="primary"))
                except:
                    markup.add(InlineKeyboardButton(ch['name'], url=url))
        except Exception as e:
            print(f"Error getting channel link: {e}")
            continue
    try:
        markup.add(InlineKeyboardButton(
            f" {btn_text}",
            callback_data="check_sub",
            icon_custom_emoji_id="5285533062518566401",
            style=btn_color
        ))
    except:
        markup.add(InlineKeyboardButton(btn_text, callback_data="check_sub"))
    return markup


def send_subscription_message_with_image(chat_id, user_id=None):
    """Send subscription message, with image if set"""
    msg_text = get_subscription_message(user_id)
    channels = check_subscription(user_id)

    if channels:
        markup = get_single_channel_keyboard(
            channels[0],
            user_id
        )
    else:
        markup = get_main_reply_keyboard(user_id)
    image_data = load_subscription_image()
    image_url = image_data.get("image_url")
    if image_url:
        try:
            bot.send_photo(chat_id, image_url, caption=msg_text, parse_mode="HTML", reply_markup=markup)
            return
        except Exception as e:
            print(f"Error sending subscription image: {e}")
    bot.send_message(chat_id, msg_text, parse_mode="HTML", reply_markup=markup)
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):

    user_id = call.from_user.id

    channels = check_subscription(user_id)

    # المستخدم مشترك في كل القنوات
    if not channels:
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass

        user_lang_set = USERS.get(str(user_id), {}).get("lang_chosen", False)
        if not user_lang_set:
            lang_markup = InlineKeyboardMarkup(row_width=2)
            lang_markup.add(
                InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
                InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar")
            )
            bot.send_message(
                call.message.chat.id,
                "🌍 <b>Choose Language / اختر اللغة</b>",
                parse_mode="HTML",
                reply_markup=lang_markup
            )
            return

        first_name = call.from_user.first_name or "User"
        lang = get_user_language(user_id)
        welcome_msg = get_mody_welcome_msg(first_name, lang)
        
        markup = get_country_buttons_all(user_id)
        # إرسال الأزرار الأرضية أولاً
        bot.send_message(call.message.chat.id, welcome_msg, parse_mode="HTML", reply_markup=get_main_reply_keyboard(user_id))
        
        # عرض قائمة الخدمات (المنصات)
        if markup:
            service_text = "❓ <b>Select a Service:</b>" if lang != "ar" else "❓ <b>اختر خدمة:</b>"
            bot.send_message(call.message.chat.id, service_text, parse_mode="HTML", reply_markup=markup)

    # لسه باقي قنوات
    else:

        next_channel = channels[0]
        lang = get_user_language(user_id)

        # حساب عدد القنوات المنجزة وإجمالي القنوات
        total = len(CHANNELS)
        remaining = len(channels)
        done = total - remaining

        # رسالة مع عداد التقدم
        base_msg = get_subscription_message(user_id)
        if lang == "ar":
            progress_text = f"\n\n📊 <b>التقدم: {done}/{total}</b>"
            channel_name = next_channel.get("name_ar", next_channel.get("name", "القناة"))
            next_text = f"📢 <b>القناة التالية:</b> {channel_name}"
        else:
            progress_text = f"\n\n📊 <b>Progress: {done}/{total}</b>"
            channel_name = next_channel.get("name_en", next_channel.get("name", "Channel"))
            next_text = f"📢 <b>Next channel:</b> {channel_name}"

        full_text = base_msg + progress_text + "\n" + next_text

        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=full_text,
                parse_mode="HTML",
                reply_markup=get_single_channel_keyboard(
                    next_channel,
                    user_id
                )
            )

        except:
            pass

        alert_msg = (
            f"✅ {done}/{total} — اشترك في القناة التالية!"
            if lang == "ar"
            else f"✅ {done}/{total} — Join the next channel!"
        )
        bot.answer_callback_query(
            call.id,
            alert_msg,
            show_alert=True
        )

def get_first_unjoined_channel(user_id):
    if not CHANNELS: return None
    for channel in CHANNELS:
        try:
            status = bot.get_chat_member(channel['id'], user_id).status
            if status not in ['member', 'administrator', 'creator']: return channel
        except: return channel
    return None

def get_subscription_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    for channel in CHANNELS:
        channel_name = channel.get("name", "Channel")
        channel_url = channel.get("url", "")
        btn = InlineKeyboardButton(f"🔗 Join {channel_name}", url=channel_url)
        markup.add(btn)
    markup.add(InlineKeyboardButton(
        " Verify",
        callback_data="verify_subscription",
        icon_custom_emoji_id="5285533062518566401",
        style="danger"
    ))
    return markup

def get_all_channels_keyboard(user_id=None):
    markup = InlineKeyboardMarkup(row_width=1)
    lang = get_user_language(user_id) if user_id else "ar"
    
    for channel in CHANNELS:
        channel_name = channel.get(f"name_{lang}", channel.get("name", "Channel"))
        channel_url = channel.get("url", "")
        markup.add(InlineKeyboardButton(f"📢 {channel_name}", url=channel_url))
    
    try:
        markup.add(InlineKeyboardButton(
            " Subscribed",
            callback_data="check_sub",
            icon_custom_emoji_id="5285533062518566401",
            style="danger"
        ))
    except:
        markup.add(InlineKeyboardButton("Subscribed", callback_data="check_sub"))
    return markup

def get_single_channel_keyboard(channel, user_id=None):
    lang = get_user_language(user_id) if user_id else "en"
    markup = InlineKeyboardMarkup(row_width=1)
    btn_name = channel.get(f"name_{lang}", channel.get("name", "Join"))
    try:
        markup.add(InlineKeyboardButton(f" {btn_name}", url=channel['url'], icon_custom_emoji_id="5458603043203327669", style="primary"))
    except:
        markup.add(InlineKeyboardButton(btn_name, url=channel['url']))
    
    # زر التحقق يبيّن اسم القناة
    verify_text = "✅ اشتركت، التالي" if lang == "ar" else "✅ Subscribed, Next"
    try:
        markup.add(InlineKeyboardButton(
            f" {verify_text}",
            callback_data="check_sub",
            icon_custom_emoji_id="5285533062518566401",
            style="danger"
        ))
    except:
        markup.add(InlineKeyboardButton(verify_text, callback_data="check_sub"))
    return markup

def get_all_channels_message(user_id):
    lang = get_user_language(user_id)
    
    if lang == "ar":
        text = "🔒 <b>انضم للقنوات التالية للمتابعة</b>\n\n"
        for i, channel in enumerate(CHANNELS, 1):
            channel_name = channel.get("name_ar", channel.get("name", "Channel"))
            text += f"{i}. 📢 <b>{channel_name}</b>\n"
        return text
    else:
        text = "🔒 <b>Join the following channels to continue</b>\n\n"
        for i, channel in enumerate(CHANNELS, 1):
            channel_name = channel.get("name_en", channel.get("name", "Channel"))
            text += f"{i}. 📢 <b>{channel_name}</b>\n"
        return text

def get_main_menu_lang(user_id):
    lang = get_user_language(user_id)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(t(user_id, "choose_country"), callback_data="choose_country")
    )
    
    withdraw_text = "💰 سحب الرصيد" if lang == "ar" else "💰 Withdraw"
    help_text = "❓ مساعدة" if lang == "ar" else "❓ Help"
    markup.add(
        InlineKeyboardButton(withdraw_text, callback_data="withdraw_balance"),
        InlineKeyboardButton(help_text, callback_data="show_instructions")
    )
    
    links = load_button_links()
    dev_text = "👨‍💻 المطور" if lang == "ar" else "👨‍💻 Developer"
    markup.add(
        InlineKeyboardButton(dev_text, url=links.get("developer_link", f"tg://user?id={MAIN_ADMIN_ID}"))
    )
    return markup

# ── زر الرجوع الديناميكي ── سيتم تعريفه كاملاً لاحقاً، هنا stub مبكر
def make_back_button(text, callback_data):
    """Create a back button with the configured color and emoji - dynamic"""
    try:
        import json as _j
        _s = {}
        if os.path.exists("back_btn_settings.json"):
            with open("back_btn_settings.json", "r") as _f:
                _s = _j.load(_f)
        color = _s.get("color")
        eid = "5321334093126842469"
        kw = {"callback_data": callback_data, "icon_custom_emoji_id": eid}
        if color: kw["style"] = color
        return InlineKeyboardButton(f" {text}", **kw)
    except:
        return InlineKeyboardButton(f"◀ {text}", callback_data=callback_data)

def get_admin_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⚙️ إعدادات المواقع", callback_data="admin_sites_menu"),
        InlineKeyboardButton("👥 إدارة الحسابات", callback_data="admin_accounts_menu")
    )
    markup.add(
        InlineKeyboardButton("➕ إضافة دولة", callback_data="admin_add_country"),
        InlineKeyboardButton("➖ حذف دولة", callback_data="admin_remove_country")
    )
    markup.add(
        InlineKeyboardButton("📋 الدول المتاحة", callback_data="admin_list_countries")
    )
    markup.add(
        InlineKeyboardButton("📢 إضافة قناة", callback_data="admin_add_channel"),
        InlineKeyboardButton("🗑 حذف قناة", callback_data="admin_remove_channel")
    )
    markup.add(
        InlineKeyboardButton("📊 القنوات المضافة", callback_data="admin_list_channels"),
        InlineKeyboardButton("📱 إدارة الجروبات", callback_data="admin_groups_menu")
    )
    markup.add(
        InlineKeyboardButton("🖼 تعيين صور الاشتراك", callback_data="admin_set_sub_image"),
        InlineKeyboardButton("🗑 حذف صور الاشتراك", callback_data="admin_del_sub_image")
    )
    markup.add(
        InlineKeyboardButton("✏️ تغيير رسالة الاشتراك", callback_data="admin_edit_sub_msg"),
        InlineKeyboardButton("🔘 تغيير اسم زر Subscribe", callback_data="admin_edit_sub_btn")
    )

    markup.add(
        InlineKeyboardButton("📈 الإحصائيات", callback_data="admin_statistics")
    )
    markup.add(
        InlineKeyboardButton("📣 إذاعة", callback_data="admin_broadcast_menu")
    )
    markup.add(
        InlineKeyboardButton("🔧 إضافة مشرف", callback_data="admin_add_admin"),
        InlineKeyboardButton("🗑 حذف مشرف", callback_data="admin_remove_admin")
    )
    markup.add(
        InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban_user"),
        InlineKeyboardButton("✅ إلغاء حظر", callback_data="admin_unban_user")
    )
    markup.add(
        InlineKeyboardButton("📝 رسائل الترحيب", callback_data="admin_welcome_messages")
    )
    markup.add(
        InlineKeyboardButton("🌍 الشكل الافتراضي/MODY", callback_data="admin_set_default_layout"),
        InlineKeyboardButton("🔄 الشكل الأصلي/MODY", callback_data="admin_set_original_layout")
    )
    markup.add(
        InlineKeyboardButton("🔗 روابط الأزرار", callback_data="admin_button_links"),
        InlineKeyboardButton("🔘 أزرار رسالة OTP", callback_data="admin_otp_buttons")
    )
    markup.add(
        InlineKeyboardButton("📱 إضافة منصة", callback_data="admin_add_platform"),
        InlineKeyboardButton("🗑 حذف منصة", callback_data="admin_del_platform")
    )
    markup.add(
        InlineKeyboardButton("⚙️ إعدادات المنصات", callback_data="admin_platform_settings")
    )
    markup.add(
        InlineKeyboardButton("🎨 ألوان الدول / المنصات", callback_data="admin_country_colors"),
        InlineKeyboardButton("📐 أماكن الأزرار", callback_data="admin_btn_layout")
    )
    markup.add(
        InlineKeyboardButton("🔙 زر الرجوع من الدول", callback_data="admin_back_btn_settings")
    )
    markup.add(
        InlineKeyboardButton("🎨 ألوان الكيبورد", callback_data="admin_keyboard_colors")
    )
    markup.add(
        InlineKeyboardButton("📥 إنشاء نسخة احتياطية", callback_data="admin_create_backup"),
        InlineKeyboardButton("📤 استعادة نسخة احتياطية", callback_data="admin_restore_backup")
    )
    markup.add(make_back_button("رجوع للقائمة الرئيسية", "back_to_main"))
    return markup

def get_sites_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🏢 GROUP", callback_data="site_config_GROUP"),
        InlineKeyboardButton("🔷 Fly sms", callback_data="site_config_Fly sms")
    )
    markup.add(
        InlineKeyboardButton("🏢 hadi", callback_data="site_config_hadi"),
        InlineKeyboardButton("🔷 fire", callback_data="site_config_fire")
    )
    markup.add(
        InlineKeyboardButton("📱 Number Panel", callback_data="site_config_Number_Panel"),
        InlineKeyboardButton("⚡ Bolt", callback_data="site_config_Bolt"),
        InlineKeyboardButton("🌐 IMS", callback_data="site_config_IMS"),
        InlineKeyboardButton("🌸 Roxy SMS", callback_data="site_config_Roxy SMS")
    )
    markup.add(
        InlineKeyboardButton("🌐 iVAS SMS", callback_data="site_config_iVASMS")
    )
    markup.add(
        InlineKeyboardButton("🔵 MSI", callback_data="site_config_MSI"),
        InlineKeyboardButton(" proton SMS", callback_data="site_config_proton SMS")
    )
    markup.add(
        InlineKeyboardButton("🆕 TimeSMS", callback_data="site_config_TimeSMS"),
        InlineKeyboardButton("🔗 Konekta", callback_data="site_config_Konekta")
    )
    markup.add(
        InlineKeyboardButton("📡 Seven1Tel", callback_data="site_config_Seven1Tel")
    )
    markup.add(InlineKeyboardButton("🕊 Gaza SMS", callback_data="site_config_Gaza SMS"))
    markup.add(InlineKeyboardButton("📶 Km sms", callback_data="site_config_Km sms"))
    markup.add(
        InlineKeyboardButton("🟣 Grand SMS", callback_data="site_config_Grand SMS"),
        InlineKeyboardButton("💜 Purple SMS", callback_data="site_config_Purple SMS")
    )
    markup.add(InlineKeyboardButton(
        "رجوع للوحة الأدمن",
        callback_data="admin",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    return markup

def get_site_config_menu(site_key, account_id=None):
    site_name = SETTINGS[site_key]["name"]
    short_id = account_id[:8] if account_id else ""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👤 تغيير اليوزر", callback_data=f"site_change_user_{site_key}_{short_id}"),
        InlineKeyboardButton("🔑 تغيير الباسورد", callback_data=f"site_change_pass_{site_key}_{short_id}")
    )
    markup.add(
        InlineKeyboardButton("⏱ فترة البحث", callback_data=f"site_change_interval_{site_key}"),
        InlineKeyboardButton("⏳ وقت الانتظار", callback_data=f"site_change_timeout_{site_key}")
    )
    markup.add(
        InlineKeyboardButton("🔓 اختبار تسجيل الدخول", callback_data=f"site_test_login_{site_key}_{short_id}"),
        InlineKeyboardButton("📥 اختبار جلب كود", callback_data=f"site_test_fetch_{site_key}_{short_id}")
    )
    markup.add(InlineKeyboardButton(
        "رجوع لقائمة المواقع",
        callback_data="admin_sites_menu",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    return markup

def get_site_accounts_selection_menu(site_key):
    site_name = SETTINGS[site_key]["name"]
    accounts = get_site_accounts(site_key)
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    buttons = []
    for idx, account in enumerate(accounts, 1):
        username = account.get("username", "N/A")
        account_id = account.get("id", "")
        short_id = account_id[:8] if account_id else ""
        buttons.append(
            InlineKeyboardButton(
                f"👤 {idx}. {username[:15]}",
                callback_data=f"select_account_config_{site_key}_{short_id}"
            )
        )
    
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.add(buttons[i], buttons[i+1])
        else:
            markup.add(buttons[i])
    
    markup.add(InlineKeyboardButton(
        "رجوع لقائمة المواقع",
        callback_data="admin_sites_menu",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    return markup

def get_accounts_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🏢 GROUP", callback_data="accounts_site_GROUP"),
        InlineKeyboardButton("🔷 Fly sms", callback_data="accounts_site_Fly sms")
    )
    markup.add(
        InlineKeyboardButton("🏢 hadi", callback_data="accounts_site_hadi"),
        InlineKeyboardButton("🔷 fire", callback_data="accounts_site_fire")
    )
    markup.add(
        InlineKeyboardButton("📱 Number Panel", callback_data="accounts_site_Number_Panel"),
        InlineKeyboardButton("⚡ Bolt", callback_data="accounts_site_Bolt"),
        InlineKeyboardButton("🌐 IMS", callback_data="accounts_site_IMS"),
        InlineKeyboardButton("🌸 Roxy SMS", callback_data="accounts_site_Roxy SMS")
    )
    markup.add(
        InlineKeyboardButton("🌐 iVAS SMS", callback_data="accounts_site_iVASMS")
    )
    markup.add(
        InlineKeyboardButton("🔵 MSI", callback_data="accounts_site_MSI"),
        InlineKeyboardButton("proton SMS", callback_data="accounts_site_proton SMS")
    )
    markup.add(
        InlineKeyboardButton("🆕 TimeSMS", callback_data="accounts_site_TimeSMS"),
        InlineKeyboardButton("🔗 Konekta", callback_data="accounts_site_Konekta")
    )
    markup.add(
        InlineKeyboardButton("📡 Seven1Tel", callback_data="accounts_site_Seven1Tel")
    )
    markup.add(InlineKeyboardButton("🕊 Gaza SMS", callback_data="accounts_site_Gaza SMS"))
    markup.add(InlineKeyboardButton("📶 Km sms", callback_data="accounts_site_Km sms"))
    markup.add(
        InlineKeyboardButton("🟣 Grand SMS", callback_data="accounts_site_Grand SMS"),
        InlineKeyboardButton("💜 Purple SMS", callback_data="accounts_site_Purple SMS")
    )
    markup.add(InlineKeyboardButton(
        "رجوع للوحة الأدمن",
        callback_data="admin_panel",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    return markup

def get_site_accounts_menu(site_key):
    site_name = SETTINGS[site_key]["name"]
    accounts = get_site_accounts(site_key)
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    if accounts:
        buttons = []
        for idx, account in enumerate(accounts, 1):
            username = account.get("username", "N/A")
            account_id = account.get("id", "")
            short_id = account_id[:8] if account_id else ""
            buttons.append(
                InlineKeyboardButton(
                    f"👤 {idx}. {username[:15]}",
                    callback_data=f"view_account_{site_key}_{short_id}"
                )
            )
        
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                markup.add(buttons[i], buttons[i+1])
            else:
                markup.add(buttons[i])
    
    markup.add(
        InlineKeyboardButton("➕ إضافة حساب جديد", callback_data=f"add_account_{site_key}")
    )
    markup.add(InlineKeyboardButton(
        "رجوع لقائمة المواقع",
        callback_data="admin_accounts_menu",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    return markup

def get_account_details_menu(site_key, account_id):
    short_id = account_id[:8] if account_id else ""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🗑 حذف الحساب", callback_data=f"delete_account_{site_key}_{short_id}"),
        InlineKeyboardButton(
            "رجوع",
            callback_data=f"accounts_site_{site_key}",
            icon_custom_emoji_id="5321334093126842469",
            style="primary"
        )
    )
    return markup

def try_decode(raw):
    if raw is None:
        return ""
    
    if isinstance(raw, str):
        
        return raw.replace('\x00', '').strip()
    
    if not isinstance(raw, bytes):
        try:
            
            return str(raw).replace('\x00', '').strip()
        except:
            return ""

  
    encodings = (
        "utf-8", 
        "utf-16", "utf-16-be", "utf-16-le",
        "cp1256", "windows-1256", "iso-8859-6", 
        "cp1251", "windows-1251", "koi8-r",    
        "latin-1", "iso-8859-1"
    )
    
    for enc in encodings:
        try:
            s = raw.decode(enc)
            
            return s.replace('\x00', '').strip()
        except:
            continue
    
    return raw.decode('utf-8', errors='replace').replace('\x00', '').strip()

def mask_number(num):
    s = str(num)
    digits = re.sub(r'\D', '', s)
    if len(digits) <= 6:
        return s
    
    if len(digits) >= 11:
        return digits[:2] + "XXXXXX" + digits[-3:]
    return digits[:2] + "•••" + digits[-2:]

import phonenumbers
from phonenumbers.phonenumberutil import region_code_for_number
import pycountry

SPECIAL_FLAGS = {
    "US": "<tg-emoji emoji-id='5434076031164103400'>🇺🇸</tg-emoji>",
    "RU": "<tg-emoji emoji-id='5433865586356531140'>🇷🇺</tg-emoji>",
    "EG": "<tg-emoji emoji-id='5431619494554383246'>🇪🇬</tg-emoji>",
    "ZA": "<tg-emoji emoji-id='5431855966863766753'>🇿🇦</tg-emoji>",
    "GR": "<tg-emoji emoji-id='5434054805435724481'>🇬🇷</tg-emoji>",
    "NL": "<tg-emoji emoji-id='5434026158003862063'>🇳🇱</tg-emoji>",
    "BE": "<tg-emoji emoji-id='5433598052843665552'>🇧🇪</tg-emoji>",
    "FR": "<tg-emoji emoji-id='5434067424049639550'>🇫🇷</tg-emoji>",
    "ES": "<tg-emoji emoji-id='5434045605615777483'>🇪🇸</tg-emoji>",
    "HU": "<tg-emoji emoji-id='5434036689263670086'>🇭🇺</tg-emoji>",
    "IT": "<tg-emoji emoji-id='5434067655977874913'>🇮🇹</tg-emoji>",
    "RO": "<tg-emoji emoji-id='5433738201921500487'>🇷🇴</tg-emoji>",
    "CH": "<tg-emoji emoji-id='5434009493530752727'>🇨🇭</tg-emoji>",
    "AT": "<tg-emoji emoji-id='5431640943621060829'>🇦🇹</tg-emoji>",
    "GB": "<tg-emoji emoji-id='5435996255207567113'>🇬🇧</tg-emoji>",
    "DK": "<tg-emoji emoji-id='5433708502222649633'>🇩🇰</tg-emoji>",
    "SE": "<tg-emoji emoji-id='5434132406904830055'>🇸🇪</tg-emoji>",
    "NO": "<tg-emoji emoji-id='5434147542369579483'>🇳🇴</tg-emoji>",
    "PL": "<tg-emoji emoji-id='5433920471743607048'>🇵🇱</tg-emoji>",
    "DE": "<tg-emoji emoji-id='5431695798943363996'>🇩🇪</tg-emoji>",
    "PE": "<tg-emoji emoji-id='5434098446598419585'>🇵🇪</tg-emoji>",
    "MX": "<tg-emoji emoji-id='5434064563601421981'>🇲🇽</tg-emoji>",
    "CU": "<tg-emoji emoji-id='5431551436502611633'>🇨🇺</tg-emoji>",
    "AR": "<tg-emoji emoji-id='5433754239329383923'>🇦🇷</tg-emoji>",
    "BR": "<tg-emoji emoji-id='5431769908604056769'>🇧🇷</tg-emoji>",
    "CL": "<tg-emoji emoji-id='5431561302042488884'>🇨🇱</tg-emoji>",
    "CO": "<tg-emoji emoji-id='5433630999537792332'>🇨🇴</tg-emoji>",
    "VE": "<tg-emoji emoji-id='5434009132753499322'>🇻🇪</tg-emoji>",
    "MY": "<tg-emoji emoji-id='5434150334098327966'>🇲🇾</tg-emoji>",
    "AU": "<tg-emoji emoji-id='5431556723607352698'>🇦🇺</tg-emoji>",
    "ID": "<tg-emoji emoji-id='5433884376838454074'>🇮🇩</tg-emoji>",
    "PH": "<tg-emoji emoji-id='5433855712226718930'>🇵🇭</tg-emoji>",
    "NZ": "<tg-emoji emoji-id='5431350891594658893'>🇳🇿</tg-emoji>",
    "SG": "<tg-emoji emoji-id='5431588626624427422'>🇸🇬</tg-emoji>",
    "TH": "<tg-emoji emoji-id='5434029851675734900'>🇹🇭</tg-emoji>",
    "JP": "<tg-emoji emoji-id='5431626087329182684'>🇯🇵</tg-emoji>",
    "KR": "<tg-emoji emoji-id='5431696408828720537'>🇰🇷</tg-emoji>",
    "VN": "<tg-emoji emoji-id='5976537109387810524'>🇻🇳</tg-emoji>",
    "CN": "<tg-emoji emoji-id='5433827537241258614'>🇨🇳</tg-emoji>",
    "TR": "<tg-emoji emoji-id='5431529734032865031'>🇹🇷</tg-emoji>",
    "IN": "<tg-emoji emoji-id='5433601609076586221'>🇮🇳</tg-emoji>",
    "PK": "<tg-emoji emoji-id='5431434686406604479'>🇵🇰</tg-emoji>",
    "AF": "<tg-emoji emoji-id='5433636707549331311'>🇦🇫</tg-emoji>",
    "LK": "<tg-emoji emoji-id='5431755073787016798'>🇱🇰</tg-emoji>",
    "MM": "<tg-emoji emoji-id='5433666360003540231'>🇲🇲</tg-emoji>",
    "IR": "<tg-emoji emoji-id='5433882955204279044'>🇮🇷</tg-emoji>",
    "MA": "<tg-emoji emoji-id='5434012796360604182'>🇲🇦</tg-emoji>",
    "DZ": "<tg-emoji emoji-id='5433627189901801019'>🇩🇿</tg-emoji>",
    "TN": "<tg-emoji emoji-id='5434152992683079729'>🇹🇳</tg-emoji>",
    "LY": "<tg-emoji emoji-id='5433876972314836083'>🇱🇾</tg-emoji>",
    "GM": "<tg-emoji emoji-id='5433596974806873997'>🇬🇲</tg-emoji>",
    "SN": "<tg-emoji emoji-id='5434001565021123877'>🇸🇳</tg-emoji>",
    "MR": "<tg-emoji emoji-id='5433859405898594234'>🇲🇷</tg-emoji>",
    "ML": "<tg-emoji emoji-id='5433943093336356065'>🇲🇱</tg-emoji>",
    "GN": "<tg-emoji emoji-id='5434115081006756195'>🇬🇳</tg-emoji>",
    "CI": "<tg-emoji emoji-id='5411283953984218884'>🇨🇮</tg-emoji>",
    "BF": "<tg-emoji emoji-id='5434013938821902926'>🇧🇫</tg-emoji>",
    "NE": "<tg-emoji emoji-id='5433737613510981562'>🇳🇪</tg-emoji>",
    "TG": "<tg-emoji emoji-id='5433772127868172193'>🇹🇬</tg-emoji>",
    "BJ": "<tg-emoji emoji-id='5433838931789492934'>🇧🇯</tg-emoji>",
    "MU": "<tg-emoji emoji-id='5431519649449653173'>🇲🇺</tg-emoji>",
    "LR": "<tg-emoji emoji-id='5431414444225738871'>🇱🇷</tg-emoji>",
    "SL": "<tg-emoji emoji-id='5433691077540330355'>🇸🇱</tg-emoji>",
    "GH": "<tg-emoji emoji-id='5434041611296192616'>🇬🇭</tg-emoji>",
    "NG": "<tg-emoji emoji-id='5433836092816108548'>🇳🇬</tg-emoji>",
    "TD": "<tg-emoji emoji-id='5433825269498525925'>🇹🇩</tg-emoji>",
    "CF": "<tg-emoji emoji-id='5431374711483282830'>🇨🇫</tg-emoji>",
    "CM": "<tg-emoji emoji-id='5433774971136521802'>🇨🇲</tg-emoji>",
    "CV": "<tg-emoji emoji-id='5431865097964237519'>🇨🇻</tg-emoji>",
    "ST": "<tg-emoji emoji-id='5976699343187482779'>🇸🇹</tg-emoji>",
    "GQ": "<tg-emoji emoji-id='5976814525620426462'>🇬🇶</tg-emoji>",
    "GA": "<tg-emoji emoji-id='5433982207603520017'>🇬🇦</tg-emoji>",
    "CG": "<tg-emoji emoji-id='5433861570562111275'>🇨🇬</tg-emoji>",
    "CD": "<tg-emoji emoji-id='5431703839122141424'>🇨🇩</tg-emoji>",
    "AO": "<tg-emoji emoji-id='5433750193470191473'>🇦🇴</tg-emoji>",
    "GW": "<tg-emoji emoji-id='5976526294660159661'>??🇼</tg-emoji>",
    "SC": "<tg-emoji emoji-id='5433721073591926542'>🇸🇨</tg-emoji>",
    "SD": "<tg-emoji emoji-id='5431384383749633710'>🇸🇩</tg-emoji>",
    "RW": "<tg-emoji emoji-id='5431484894574295376'>🇷🇼</tg-emoji>",
    "ET": "<tg-emoji emoji-id='5433804408842368654'>🇪🇹</tg-emoji>",
    "SO": "<tg-emoji emoji-id='5433785261878162812'>🇸🇴</tg-emoji>",
    "DJ": "<tg-emoji emoji-id='5976613946352736850'>🇩🇯</tg-emoji>",
    "KE": "<tg-emoji emoji-id='5433792670696748414'>🇰🇪</tg-emoji>",
    "TZ": "<tg-emoji emoji-id='5434131504961696728'>🇹🇿</tg-emoji>",
    "UG": "<tg-emoji emoji-id='5433895436379240198'>🇺🇬</tg-emoji>",
    "BI": "<tg-emoji emoji-id='5433792911214917126'>🇧🇮</tg-emoji>",
    "MZ": "<tg-emoji emoji-id='5976389130584594356'>🇲🇿</tg-emoji>",
    "ZM": "<tg-emoji emoji-id='5976750457593272380'>🇿🇲</tg-emoji>",
    "MG": "<tg-emoji emoji-id='5433833485770964033'>🇲🇬</tg-emoji>",
    "RE": "<tg-emoji emoji-id='5420322107068267129'>🇷🇪</tg-emoji>",
    "ZW": "<tg-emoji emoji-id='5433735143904786332'>🇿🇼</tg-emoji>",
    "NA": "<tg-emoji emoji-id='5431656358258685474'>🇳🇦</tg-emoji>",
    "MW": "<tg-emoji emoji-id='5433968339154122439'>🇲🇼</tg-emoji>",
    "LS": "<tg-emoji emoji-id='5431620340662940910'>🇱🇸</tg-emoji>",
    "BW": "<tg-emoji emoji-id='5433895109961725692'>🇧🇼</tg-emoji>",
    "SZ": "<tg-emoji emoji-id='5976741725924759442'>🇸🇿</tg-emoji>",
    "KM": "<tg-emoji emoji-id='5431790266749040145'>🇰🇲</tg-emoji>",
    "SH": "<tg-emoji emoji-id='5454076894997659542'>🇸🇭</tg-emoji>",
    "ER": "<tg-emoji emoji-id='5433723401464198287'>🇪🇷</tg-emoji>",
    "AW": "<tg-emoji emoji-id='5231044964212817289'>🇦🇼</tg-emoji>",
    "FO": "<tg-emoji emoji-id='5280985770188885026'>🇫🇴</tg-emoji>",
    "GL": "<tg-emoji emoji-id='5221969376193816323'>🇬🇱</tg-emoji>",
    "GI": "<tg-emoji emoji-id='5226496954623603888'>🇬🇮</tg-emoji>",
    "PT": "<tg-emoji emoji-id='5431353614603926322'>🇵🇹</tg-emoji>",
    "LU": "<tg-emoji emoji-id='5431669247455540884'>🇱🇺</tg-emoji>",
    "IE": "<tg-emoji emoji-id='5434155397864764491'>🇮🇪</tg-emoji>",
    "IS": "<tg-emoji emoji-id='5433628435442316429'>🇮🇸</tg-emoji>",
    "AL": "<tg-emoji emoji-id='5433845881046578644'>🇦🇱</tg-emoji>",
    "MT": "<tg-emoji emoji-id='5433598722858562967'>🇲🇹</tg-emoji>",
    "CY": "<tg-emoji emoji-id='5434096943359866241'>🇨🇾</tg-emoji>",
    "FI": "<tg-emoji emoji-id='5431380440969654931'>🇫🇮</tg-emoji>",
    "BG": "<tg-emoji emoji-id='5431663303220804322'>🇧🇬</tg-emoji>",
    "LT": "<tg-emoji emoji-id='5434119663736862995'>🇱🇹</tg-emoji>",
    "LV": "<tg-emoji emoji-id='5433727778035872782'>🇱🇻</tg-emoji>",
    "EE": "<tg-emoji emoji-id='5433727662071755290'>🇪🇪</tg-emoji>",
    "MD": "<tg-emoji emoji-id='5431428076451934112'>🇲🇩</tg-emoji>",
    "AM": "<tg-emoji emoji-id='5433804400252434985'>🇦🇲</tg-emoji>",
    "BY": "<tg-emoji emoji-id='5431739800883312139'>🇧🇾</tg-emoji>",
    "AD": "<tg-emoji emoji-id='5433946537900128161'>🇦🇩</tg-emoji>",
    "MC": "<tg-emoji emoji-id='5433798752370439037'>🇲🇨</tg-emoji>",
    "SM": "<tg-emoji emoji-id='5431830051031103147'>🇸🇲</tg-emoji>",
    "UA": "<tg-emoji emoji-id='5431788596006762529'>🇺🇦</tg-emoji>",
    "RS": "<tg-emoji emoji-id='5431894290856949874'>🇷🇸</tg-emoji>",
    "ME": "<tg-emoji emoji-id='5976333948844776590'>🇲🇪</tg-emoji>",
    "XK": "<tg-emoji emoji-id='5433884162090088194'>🇽🇰</tg-emoji>",
    "HR": "<tg-emoji emoji-id='5431489619038320862'>🇭🇷</tg-emoji>",
    "SI": "<tg-emoji emoji-id='5434129692485498098'>🇸🇮</tg-emoji>",
    "BA": "<tg-emoji emoji-id='5433991338703991663'>🇧🇦</tg-emoji>",
    "MK": "<tg-emoji emoji-id='5433626051735467592'>🇲🇰</tg-emoji>",
    "CZ": "<tg-emoji emoji-id='5433958877341169005'>🇨🇿</tg-emoji>",
    "SK": "<tg-emoji emoji-id='5433902785068283672'>🇸🇰</tg-emoji>",
    "LI": "<tg-emoji emoji-id='5433852744404317916'>🇱🇮</tg-emoji>",
    "FK": "<tg-emoji emoji-id='5454214681843481342'>🇫🇰</tg-emoji>",
    "BZ": "<tg-emoji emoji-id='5431431529605642522'>🇧🇿</tg-emoji>",
    "GT": "<tg-emoji emoji-id='5433935894971168754'>🇬🇹</tg-emoji>",
    "SV": "<tg-emoji emoji-id='5434134189316257066'>🇸🇻</tg-emoji>",
    "HN": "<tg-emoji emoji-id='5434072118448894385'>🇭🇳</tg-emoji>",
    "NI": "<tg-emoji emoji-id='5426842228200847679'>🇳🇮</tg-emoji>",
    "CR": "<tg-emoji emoji-id='5976659120818755766'>🇨🇷</tg-emoji>",
    "PA": "<tg-emoji emoji-id='5433851438734259274'>🇵🇦</tg-emoji>",
    "PM": "<tg-emoji emoji-id='5231258308123313128'>🇵🇲</tg-emoji>",
    "HT": "<tg-emoji emoji-id='5976439987292346381'>🇭🇹</tg-emoji>",
    "GP": "<tg-emoji emoji-id='5467664243081886165'>🇬🇵</tg-emoji>",
    "BO": "<tg-emoji emoji-id='5433609855413794108'>🇧🇴</tg-emoji>",
    "GY": "<tg-emoji emoji-id='5431676201007592926'>🇬🇾</tg-emoji>",
    "EC": "<tg-emoji emoji-id='5431462560744353934'>🇪🇨</tg-emoji>",
    "GF": "<tg-emoji emoji-id='5433979415874779870'>🇬🇫</tg-emoji>",
    "PY": "<tg-emoji emoji-id='5433748668756802256'>🇵🇾</tg-emoji>",
    "MQ": "<tg-emoji emoji-id='5976284878843418502'>🇲🇶</tg-emoji>",
    "SR": "<tg-emoji emoji-id='5431520783321019240'>🇸🇷</tg-emoji>",
    "UY": "<tg-emoji emoji-id='5433852276252883640'>🇺🇾</tg-emoji>",
    "CW": "<tg-emoji emoji-id='5233622988267472134'>🇨🇼</tg-emoji>",
    "TL": "<tg-emoji emoji-id='5433629779767081651'>🇹🇱</tg-emoji>",
    "AQ": "<tg-emoji emoji-id='5222477234601732139'>🇦🇶</tg-emoji>",
    "BN": "<tg-emoji emoji-id='5433789964867352475'>🇧🇳</tg-emoji>",
    "NR": "<tg-emoji emoji-id='5434131139889478358'>🇳🇷</tg-emoji>",
    "PG": "<tg-emoji emoji-id='5433972762970437003'>🇵🇬</tg-emoji>",
    "TO": "<tg-emoji emoji-id='5433640100573491806'>🇹🇴</tg-emoji>",
    "SB": "<tg-emoji emoji-id='5433867115364889538'>🇸🇧</tg-emoji>",
    "VU": "<tg-emoji emoji-id='5434153928985949656'>🇻🇺</tg-emoji>",
    "FJ": "<tg-emoji emoji-id='5433640560134994324'>🇫🇯</tg-emoji>",
    "PW": "<tg-emoji emoji-id='5433852121634060293'>🇵🇼</tg-emoji>",
    "WF": "<tg-emoji emoji-id='5231000034559934302'>🇼🇫</tg-emoji>",
    "CK": "<tg-emoji emoji-id='5454192094610473874'>🇨🇰</tg-emoji>",
    "NU": "<tg-emoji emoji-id='5454251094576218954'>🇳🇺</tg-emoji>",
    "WS": "<tg-emoji emoji-id='5433613703704490463'>🇼🇸</tg-emoji>",
    "KI": "<tg-emoji emoji-id='5434004021742417775'>🇰🇮</tg-emoji>",
    "NC": "<tg-emoji emoji-id='5233223766762338378'>🇳🇨</tg-emoji>",
    "TV": "<tg-emoji emoji-id='5433684690923961019'>🇹🇻</tg-emoji>",
    "PF": "<tg-emoji emoji-id='5467450310760874001'>🇵🇫</tg-emoji>",
    "TK": "<tg-emoji emoji-id='5231066898610798438'>🇹🇰</tg-emoji>",
    "FM": "<tg-emoji emoji-id='5433773682646332733'>🇫🇲</tg-emoji>",
    "MH": "<tg-emoji emoji-id='5434130474169544969'>🇲🇭</tg-emoji>",
    "KP": "<tg-emoji emoji-id='5434142701941437163'>🇰🇵</tg-emoji>",
    "HK": "<tg-emoji emoji-id='5222395857856374392'>🇭🇰</tg-emoji>",
    "MO": "<tg-emoji emoji-id='5420505321783179067'>🇲🇴</tg-emoji>",
    "KH": "<tg-emoji emoji-id='5433696429069580735'>🇰🇭</tg-emoji>",
    "LA": "<tg-emoji emoji-id='5431785473565537213'>🇱🇦</tg-emoji>",
    "BD": "<tg-emoji emoji-id='5433854239052935880'>🇧🇩</tg-emoji>",
    "TW": "<tg-emoji emoji-id='5434058864179822603'>🇹🇼</tg-emoji>",
    "MV": "<tg-emoji emoji-id='5434010919459894038'>🇲🇻</tg-emoji>",
    "LB": "<tg-emoji emoji-id='5433872853441196535'>🇱🇧</tg-emoji>",
    "JO": "<tg-emoji emoji-id='5433643519367461444'>🇯🇴</tg-emoji>",
    "SY": "<tg-emoji emoji-id='5433910876786670092'>🇸🇾</tg-emoji>",
    "IQ": "<tg-emoji emoji-id='5433749102548496991'>🇮🇶</tg-emoji>",
    "KW": "<tg-emoji emoji-id='5433820583689205435'>🇰🇼</tg-emoji>",
    "SA": "<tg-emoji emoji-id='5434125517777286321'>🇸🇦</tg-emoji>",
    "YE": "<tg-emoji emoji-id='5434078960331796980'>🇾🇪</tg-emoji>",
    "OM": "<tg-emoji emoji-id='5433714227414054291'>🇴🇲</tg-emoji>",
    "PS": "<tg-emoji emoji-id='5433776225266972326'>🇵🇸</tg-emoji>",
    "AE": "<tg-emoji emoji-id='5433887336070919773'>🇦🇪</tg-emoji>",
    "IL": "<tg-emoji emoji-id='5433810168393511493'>🇮🇱</tg-emoji>",
    "BH": "<tg-emoji emoji-id='5976668522502166844'>🇧??</tg-emoji>",
    "QA": "<tg-emoji emoji-id='5431394721735914525'>🇶🇦</tg-emoji>",
    "BT": "<tg-emoji emoji-id='5976318160544994744'>🇧🇹</tg-emoji>",
    "MN": "<tg-emoji emoji-id='5433674924168328689'>🇲🇳</tg-emoji>",
    "NP": "<tg-emoji emoji-id='5433895144321462723'>🇳🇵</tg-emoji>",
    "TJ": "<tg-emoji emoji-id='5433834847275594263'>🇹🇯</tg-emoji>",
    "TM": "<tg-emoji emoji-id='5433811229250434478'>🇹🇲</tg-emoji>",
    "AZ": "<tg-emoji emoji-id='5976582940983827573'>🇦🇿</tg-emoji>",
    "GE": "<tg-emoji emoji-id='5433814347396692144'>🇬🇪</tg-emoji>",
    "KG": "<tg-emoji emoji-id='5433652375590025431'>🇰🇬</tg-emoji>",
    "UZ": "<tg-emoji emoji-id='5433992296481700344'>🇺🇿</tg-emoji>",
    "KZ": "<tg-emoji emoji-id='5433865586356531140'>🇷🇺</tg-emoji>",
    "CA": "<tg-emoji emoji-id='5433960238845802718'>🇨🇦</tg-emoji>",
}

def get_flag(country_code):
    if not country_code: return "🌍"
    code = country_code.upper()
    if code in SPECIAL_FLAGS:
        return SPECIAL_FLAGS[code]
    return ''.join([chr(0x1F1E6 + ord(c) - ord('A')) for c in code])

def extract_tg_emoji_id(flag_str):
    import re as _re
    m = _re.search(r"emoji-id='(\d+)'", str(flag_str))
    return m.group(1) if m else None

def extract_plain_emoji(flag_str):
    """Extract the plain Unicode emoji from a tg-emoji tag or return as-is"""
    import re as _re
    # Match the emoji character inside the tg-emoji tag
    m = _re.search(r'<tg-emoji[^>]*>(.+?)</tg-emoji>', str(flag_str))
    if m:
        return m.group(1)
    return str(flag_str)

def make_flag_button(text, callback_data, flag_str, style=None):
    """Create an InlineKeyboardButton with proper flag - uses icon_custom_emoji_id if available"""
    eid = extract_tg_emoji_id(flag_str)
    plain = extract_plain_emoji(flag_str)
    try:
        kw = {"callback_data": callback_data}
        if eid:
            kw["icon_custom_emoji_id"] = eid
        if style:
            kw["style"] = style
        btn_text = f" {text}" if eid else f"{plain} {text}"
        return InlineKeyboardButton(btn_text, **kw)
    except:
        return InlineKeyboardButton(f"{plain} {text}", callback_data=callback_data)

def detect_country_from_number(number, user_id=None):
    try:
        s = str(number).strip()
        if not s.startswith('+'):
            s = '+' + s
        
       
        try:
            parsed = phonenumbers.parse(s)
        except phonenumbers.NumberParseException:
            
            parsed = phonenumbers.parse(s + "00000000")
            
        region = phonenumbers.region_code_for_number(parsed)
        if not region:
            return "Unknown", "🌍", "UN"
        
        lang = get_user_language(user_id) if user_id else "ar"
        
       
        country_name = geocoder.description_for_number(parsed, lang)
        
       
        if not country_name or country_name == "Unknown":
            try:
                py_country = pycountry.countries.get(alpha_2=region)
                if py_country:
                    
                    country_name = py_country.name
            except:
                pass

       
        if not country_name or country_name == "Unknown":
            country_name = geocoder.description_for_number(parsed, "en")
            
        if not country_name or country_name == "Unknown":
            country_name = region

        # بدّل كازاخستان بـ روسيا في الاسم والعلم
        if region == "KZ":
            country_name = "روسيا" if lang == "ar" else "Russia"
            flag = get_flag("RU")
            region = "RU"
        flag = get_flag(region)
        return country_name, flag, region
    except Exception as e:
        print(f"Error detecting country: {e}")
        return "Unknown", "🌍", "UN"

def format_otp_message(number, sms_text, service_name="[TG]", otp_code=None, user_id=None):
    country_name, flag, region_code = detect_country_from_number(number, user_id)
    masked = mask_number(number)

    otp_text = otp_code if otp_code and otp_code != "N/A" else "----"

    # استخراج تفاعل الخدمة
    raw_service = str(service_name).strip()
    if raw_service.startswith("[") and raw_service.endswith("]"):
        service_icon = raw_service[1:-1]
    else:
        service_icon = raw_service
    if not service_icon.startswith("<tg-emoji"):
        service_icon = "<tg-emoji emoji-id='5334998226636390258'>📱</tg-emoji>"

    message = (
        f"↠ {flag} #{region_code} [{service_icon}] <code>{masked}</code> ┤\n"
        f"<tg-emoji emoji-id='5307843983102204243'>🔑</tg-emoji>~ OTP Code ~ <code>{otp_text}</code>"
    )

    return message




def detect_service(text, source_addr=None):
    if not text:
        return "Unknown 🌐"
    t = text.lower()
    source_lower = source_addr.lower() if source_addr else ""
    
   
    if any(k in t for k in ["whatsapp", "واتساب", "واتس"]):
        return "<tg-emoji emoji-id='5188683998125106802'>📞</tg-emoji>"
    if any(k in t for k in ["telegram", "تيليجرام", "تلجرام"]):
        return "<tg-emoji emoji-id='5471949924658588235'>👉</tg-emoji>"
    if any(k in t for k in ["facebook", "فيسبوك", "meta"]):
        return "<tg-emoji emoji-id='5323261730283863478'>📱</tg-emoji>"
    if any(k in t for k in ["instagram", "انستقرام", "انستا"]):
        return "<tg-emoji emoji-id='5319160079465857105'>📱</tg-emoji>"
    if any(k in t for k in ["tiktok", "تيك توك", "تيكتوك"]):
        return "<tg-emoji emoji-id='5327982530702359565'>📱</tg-emoji>"
    if any(k in t for k in ["google", "جوجل", "gmail"]):
        return "<tg-emoji emoji-id='5359758030198031389'>📱</tg-emoji>"
    if any(k in t for k in ["imo", "ايمو"]):
        return "IM"
    if any(k in t for k in ["viber", "فايبر"]):
        return "VB"
    if any(k in t for k in ["snapchat", "سناب"]):
        return "<tg-emoji emoji-id='5330248916224983855'>📱</tg-emoji>"

    services = {
        "whatsapp": "<tg-emoji emoji-id='5188683998125106802'>📞</tg-emoji>",
        "واتساب": "WS",
        "واتس": "WS",
        "facebook": "<tg-emoji emoji-id='5323261730283863478'>📱</tg-emoji>",
        "فيسبوك": "<tg-emoji emoji-id='5323261730283863478'>📱</tg-emoji>",
        "meta": "<tg-emoji emoji-id='5323261730283863478'>📱</tg-emoji>",
        "instagram": "<tg-emoji emoji-id='5319160079465857105'>📱</tg-emoji>",
        "انستقرام": "<tg-emoji emoji-id='5319160079465857105'>📱</tg-emoji>",
        "انستا": "<tg-emoji emoji-id='5319160079465857105'>📱</tg-emoji>",
        "telegram": "<tg-emoji emoji-id='5471949924658588235'>👉</tg-emoji>",
        "تيليجرام": "<tg-emoji emoji-id='5471949924658588235'>👉</tg-emoji>",
        "تلجرام": "<tg-emoji emoji-id='5471949924658588235'>👉</tg-emoji>",
        "twitter": "TW",
        "تويتر": "TW",
        "x.com": "TW",
        "snapchat": "<tg-emoji emoji-id='5330248916224983855'>📱</tg-emoji>",
        "سناب": "<tg-emoji emoji-id='5330248916224983855'>📱</tg-emoji>",
        "tiktok": "<tg-emoji emoji-id='5327982530702359565'>📱</tg-emoji>",
        "تيك توك": "<tg-emoji emoji-id='5327982530702359565'>📱</tg-emoji>",
        "google": "GG",
        "جوجل": "GG",
        "gmail": "GG",
        "linkedin": "LN",
        "لينكد": "LN",
        "discord": "DC",
        "ديسكورد": "DC",
        "uber": "UB",
        "bolt": "BT",
        "careem": "CR",
        "amazon": "AZ",
        "netflix": "<tg-emoji emoji-id='5318911503938634641'>📱</tg-emoji>",
        "spotify": "SP",
        "apple": "<tg-emoji emoji-id='5334955749409834455'>📱</tg-emoji>",
        "microsoft": "MS",
        "paypal": "<tg-emoji emoji-id='5364111181415996352'>📱</tg-emoji>",
        "binance": "BN",
        "coinbase": "CB",
    }

    for keyword, service in services.items():
        if keyword in t:
            return service
    
    for keyword, service in services.items():
        if keyword in source_lower:
            return service

    if source_addr and source_addr.strip():
        cleaned_source = source_addr.replace('#', '').strip()
        if cleaned_source:
            return cleaned_source.upper()
    return "Unknown 🌐"

def get_country_flags(country_name):
    
    flags = {
        "مصر": "<tg-emoji emoji-id='5293992082212409502'>🇪🇬</tg-emoji>", "Egypt": "<tg-emoji emoji-id='5293992082212409502'>🇪🇬</tg-emoji>",
        "السعودية": "<tg-emoji emoji-id='5294163983983463099'>🇸🇦</tg-emoji>", "Saudi Arabia": "<tg-emoji emoji-id='5294163983983463099'>🇸🇦</tg-emoji>",
        "ليبيا": "<tg-emoji emoji-id='5291858711826946840'>🇱🇾</tg-emoji>", "Libya": "<tg-emoji emoji-id='5291858711826946840'>🇱🇾</tg-emoji>",
        "الجزائر": "<tg-emoji emoji-id='5294048127240655242'>🇩🇿</tg-emoji>", "Algeria": "<tg-emoji emoji-id='5294048127240655242'>🇩🇿</tg-emoji>",
        "المغرب": "<tg-emoji emoji-id='5292108962391414885'>🇲🇦</tg-emoji>", "Morocco": "<tg-emoji emoji-id='5292108962391414885'>🇲🇦</tg-emoji>",
        "تونس": "<tg-emoji emoji-id='5294484680601521871'>🇹🇳</tg-emoji>", "Tunisia": "<tg-emoji emoji-id='5294484680601521871'>🇹🇳</tg-emoji>",
        "العراق": "<tg-emoji emoji-id='5294325010897327367'>🇮🇶</tg-emoji>", "Iraq": "<tg-emoji emoji-id='5294325010897327367'>🇮🇶</tg-emoji>",
        "الأردن": "<tg-emoji emoji-id='5291988613112814801'>🇯🇴</tg-emoji>", "Jordan": "<tg-emoji emoji-id='5291988613112814801'>🇯🇴</tg-emoji>",
        "فلسطين": "<tg-emoji emoji-id='5294289826525238172'>🇵🇸</tg-emoji>", "Palestine": "<tg-emoji emoji-id='5294289826525238172'>🇵🇸</tg-emoji>",
        "الإمارات": "<tg-emoji emoji-id='5294314831824835370'>🇦🇪</tg-emoji>", "UAE": "<tg-emoji emoji-id='5294314831824835370'>🇦🇪</tg-emoji>",
        "الكويت": "<tg-emoji emoji-id='5292066437920218075'>🇰🇼</tg-emoji>", "Kuwait": "<tg-emoji emoji-id='5292066437920218075'>🇰🇼</tg-emoji>",
        "قطر": "<tg-emoji emoji-id='5292166360334357676'>🇶🇦</tg-emoji>", "Qatar": "<tg-emoji emoji-id='5292166360334357676'>🇶🇦</tg-emoji>",
        "لبنان": "<tg-emoji emoji-id='5294193108156699621'>🇱🇧</tg-emoji>", "Lebanon": "<tg-emoji emoji-id='5294193108156699621'>🇱🇧</tg-emoji>",
        "سوريا": "<tg-emoji emoji-id='5294013428199869487'>🇸🇾</tg-emoji>", "Syria": "<tg-emoji emoji-id='5294013428199869487'>🇸🇾</tg-emoji>",
        "روسيا": "<tg-emoji emoji-id='5294335323113807278'>🇷🇺</tg-emoji>", "Russia": "<tg-emoji emoji-id='5294335323113807278'>🇷🇺</tg-emoji>",
        "أمريكا": "<tg-emoji emoji-id='5294244076533600593'>🇺🇸</tg-emoji>", "USA": "<tg-emoji emoji-id='5294244076533600593'>🇺🇸</tg-emoji>",
        "فرنسا": "<tg-emoji emoji-id='5291817660529533837'>🇫🇷</tg-emoji>", "France": "<tg-emoji emoji-id='5291817660529533837'>🇫🇷</tg-emoji>",
        "ألمانيا": "<tg-emoji emoji-id='5292013274815028523'>🇩🇪</tg-emoji>", "Germany": "<tg-emoji emoji-id='5292013274815028523'>🇩🇪</tg-emoji>",
        "تركيا": "<tg-emoji emoji-id='5293993400767367408'>🇹🇷</tg-emoji>", "Turkey": "<tg-emoji emoji-id='5293993400767367408'>🇹🇷</tg-emoji>"
    }
    return flags.get(country_name, "🌍")

def detect_country_code_from_file(file_path):
   
    try:
        prefixes = {}
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line: continue
            first_part = line.split()[0] if line.split() else line
            digits = ''.join(c for c in first_part if c.isdigit())
            
            if len(digits) >= 8:
               
                for i in range(1, 4):
                    prefix = digits[:i]
                    prefixes[prefix] = prefixes.get(prefix, 0) + 1
        
        if not prefixes:
            return None
            
        
        sorted_prefixes = sorted(prefixes.items(), key=lambda x: (x[1], len(x[0])), reverse=True)
        return sorted_prefixes[0][0] 
    except Exception as e:
        print(f"Error detecting country code: {e}")
        return None

def clean_and_filter_numbers(file_path, country_code):
    
    cleaned_numbers = []
    total_lines = 0
    rejected_lines = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            total_lines += 1

            parts = re.split(r'\s+', line)
            if not parts:
                rejected_lines += 1
                continue

            first_part = parts[0].strip()
            digits = re.sub(r'\D', '', first_part)

            if not digits:
                rejected_lines += 1
                continue

            if digits.startswith(country_code):
                cleaned_numbers.append(digits)
            else:
                rejected_lines += 1

        with open(file_path, 'w', encoding='utf-8') as f:
            for number in cleaned_numbers:
                f.write(number + '\n')

        return (len(cleaned_numbers), total_lines, rejected_lines)

    except Exception as e:
        print(f"❌ خطأ في تنظيف الملف: {e}")
        return (0, 0, 0)

def get_platform_buttons(country_name):
   
    markup = InlineKeyboardMarkup(row_width=2)
    buttons_found = False
    
    
    if country_name in COUNTRIES:
        info = COUNTRIES[country_name]
        platforms = info.get('platforms', [])
        platform_icons = {
            "Facebook": "📘 Facebook",
            "WhatsApp": "💬 WhatsApp",
            "Telegram": "✈️ Telegram",
            "Instagram": "📸 Instagram",
            "Twitter": "🐦 Twitter/X",
            "TikTok": "📱 TikTok",
            "Discord": "🎮 Discord",
            "Gmail": "📧 Gmail"
        }
        for platform in platforms:
            display_name = platform_icons.get(platform, f"📱 {platform}")
            markup.add(InlineKeyboardButton(display_name, callback_data=f"platform_{country_name}_{platform}"))
            buttons_found = True
    else:
        
        platform_icons = {
            "Facebook": "📘 Facebook",
            "WhatsApp": "💬 WhatsApp",
            "Telegram": "✈️ Telegram",
            "Instagram": "📸 Instagram",
            "Twitter": "🐦 Twitter/X",
            "TikTok": "📱 TikTok",
            "Discord": "🎮 Discord",
            "Gmail": "📧 Gmail"
        }
        for cid, info in COUNTRIES.items():
            if info.get("display_name") == country_name or cid == country_name:
                platforms = info.get('platforms', [])
                for platform in platforms:
                    display_name = platform_icons.get(platform, f"📱 {platform}")
                    markup.add(InlineKeyboardButton(display_name, callback_data=f"platform_{cid}_{platform}"))
                    buttons_found = True

    if not buttons_found:
        return None
    
    markup.add(InlineKeyboardButton("𝗕𝗮𝗰𝗸", callback_data="choose_country", icon_custom_emoji_id="5321334093126842469"))
    return markup

def load_bot_settings():
    import json as _j
    try:
        with open("bot_settings.json","r") as f: return _j.load(f)
    except: return {}

def save_bot_settings(s):
    import json as _j
    try:
        with open("bot_settings.json","w") as f: _j.dump(s, f, ensure_ascii=False)
    except: pass

def get_bot_layout():
    """Returns 'default' (MODY layout) or 'original' """
    return load_bot_settings().get("bot_layout", "default")

def set_bot_layout(layout):
    s = load_bot_settings()
    s["bot_layout"] = layout
    save_bot_settings(s)

def get_main_reply_keyboard(user_id=None):

    from telebot.types import ReplyKeyboardMarkup, KeyboardButton

    markup = ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2,
        input_field_placeholder="Tg"
    )

    lang = get_user_language(user_id)

    if lang == "ar":
        take_txt      = "احصل على رقم "
        countries_txt = "الدول المتاحة "
        stat_txt      = "الإحصائيات "
        balance_txt   = "الرصيد "
        withdraw_txt  = "سحب الرصيد "
        live_txt      = "حركة المرور  "
    else:
        take_txt      = "Get Number "
        countries_txt = "Available Country "
        stat_txt      = "Status "
        balance_txt   = "Balance "
        withdraw_txt  = "Withdraw "
        live_txt      = "Live Traffic "

    try:
        btn_take = KeyboardButton(
            take_txt,
            style="primary",
            icon_custom_emoji_id="5947265786279104211"
        )
        btn_countries = KeyboardButton(
            countries_txt,
            style="success",
            icon_custom_emoji_id="5447410659077661506"
        )
        btn_stat = KeyboardButton(
            stat_txt,
            style="success",
            icon_custom_emoji_id="5451882707875276247"
        )
        btn_balance = KeyboardButton(
            balance_txt,
            style="primary",
            icon_custom_emoji_id="5409048419211682843"
        )
        btn_withdraw = KeyboardButton(
            withdraw_txt,
            style="danger",
            icon_custom_emoji_id="5444962231366201677"
        )
        btn_live = KeyboardButton(
            live_txt,
            style="success",
              icon_custom_emoji_id="5451882707875276247"
        )
    except:
        btn_take      = KeyboardButton(take_txt)
        btn_countries = KeyboardButton(countries_txt)
        btn_stat      = KeyboardButton(stat_txt)
        btn_balance   = KeyboardButton(balance_txt)
        btn_withdraw  = KeyboardButton(withdraw_txt)
        btn_live      = KeyboardButton(live_txt)

    # Row 1: Get Number | Available Country
    markup.row(btn_take, btn_countries)
    # Row 2: Status | Balance
    markup.row(btn_stat, btn_balance)
    # Row 3: Withdraw | Live Traffic
    markup.row(btn_withdraw, btn_live)

    return markup

def get_mody_welcome_msg(user_obj, lang="en"):
    # التحقق إذا كان user_obj نصاً أو كائناً
    if isinstance(user_obj, str):
        name = user_obj if user_obj.strip() not in [".", "", "None"] else "User"
    elif not user_obj:
        name = "User"
    else:
        # محاولة الحصول على الاسم الأول، وإذا كان نقطة أو غير موجود نستخدم اسم المستخدم
        first_name = getattr(user_obj, 'first_name', None)
        username = getattr(user_obj, 'username', None)

        if first_name and first_name.strip() not in [".", "", "None"]:
            name = first_name
        elif username:
            name = username
        else:
            name = "User"

    return (
        f"Welcome to {name} 🌍\n\n"
        "Use the menu below to get started:"
    )

MODY_WELCOME_MSG = get_mody_welcome_msg("User")

MODY_WELCOME_MSG = get_mody_welcome_msg("User")


def get_country_btn_color(cid=None):
    s = load_bot_settings()
    if cid and "country_colors" in s and cid in s["country_colors"]:
        c = s["country_colors"][cid]
        return c if c != "none" else None
    c = s.get("country_btn_color","success")
    return c if c != "none" else None

def get_country_btn_layout():
    return load_bot_settings().get("country_btn_layout","single")

def get_platforms_list(user_id=None):
    return get_country_buttons_all(user_id)

def load_platforms():
    """Load custom platforms from platforms.json"""
    try:
        if os.path.exists("platforms.json"):
            with open("platforms.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}

PLATFORM_WELCOME_FILE = "platform_welcome.json"
BACK_BTN_SETTINGS_FILE = "back_btn_settings.json"

def load_platform_welcome():
    """Load per-platform welcome messages"""
    try:
        if os.path.exists(PLATFORM_WELCOME_FILE):
            with open(PLATFORM_WELCOME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {}

def save_platform_welcome(data):
    with open(PLATFORM_WELCOME_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_back_btn_settings():
    """Load back button color settings"""
    try:
        if os.path.exists(BACK_BTN_SETTINGS_FILE):
            with open(BACK_BTN_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {"color": None}

def save_back_btn_settings(data):
    with open(BACK_BTN_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def get_platform_welcome_msg(plt_name):
    """Get welcome message for a specific platform"""
    data = load_platform_welcome()
    entry = data.get(plt_name, {})
    return entry.get("message", ""), entry.get("emoji_id", "")

def get_platform_welcome_text(plt_name, user_id=None):
    """Get welcome text to show when a platform is selected"""
    msg, eid = get_platform_welcome_msg(plt_name)
    if msg:
        if eid:
            return f"<tg-emoji emoji-id='{eid}'>{plt_name[:1]}</tg-emoji> {msg}"
        return msg
    # Default
    return (
        f"<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji> "
        f"<b>| Select your country below</b> "
        f"<tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>"
    )

def get_platform_numbers_count(plt_name):
    """Count total numbers across all countries linked to this platform"""
    total = 0
    for cid, info in COUNTRIES.items():
        if plt_name in info.get("platforms", []):
            fname = info.get("file", "")
            if fname and os.path.exists(fname):
                try:
                    with open(fname, "r", encoding="utf-8") as f:
                        total += sum(1 for l in f if l.strip())
                except: pass
            else:
                total += info.get("numbers_count", 0)
    return total

def get_country_buttons_all(user_id=None):
    """Show platforms if any exist, else show countries directly"""
    platforms = load_platforms()
    
    # Emoji IDs للمنصات الرئيسية (زي الصورة)
    PLATFORM_EMOJI_IDS = {
        "WhatsApp":  "5334998226636390258",
        "Facebook":  "5323261730283863478",
        "Telegram":  "5330237710655306682",
        "Instagram": "5319160079465857105",
        "Twitter":   "5330337435500951363",
        "TikTok":    "5327982530702359565",
        "Discord":   "5325612636467903082",
        "Gmail":     "5303416490295304868",
    }
    # أيقونات fallback نصية
    PLATFORM_ICONS = {
        "WhatsApp":  "WhatsApp",
        "Facebook":  "Facebook",
        "Telegram":  "Telegram",
        "Instagram": "Instagram",
        "Twitter":   "Twitter",
        "TikTok":    "TikTok",
        "Discord":   "Discord",
        "Gmail":     "Gmail",
    }

    if platforms:
        s = load_bot_settings()
        rw = 1  # المنصات دايماً صف واحد زي الصورة
        markup = InlineKeyboardMarkup(row_width=1)
        plt_color = s.get("platform_btn_color")
        btns = []
        for plt_name, plt_info in platforms.items():
            # Count numbers for this platform
            count = get_platform_numbers_count(plt_name)
            # Hide platform if no numbers
            if count == 0:
                continue
            # استخدم emoji_id من platforms.json أو من القاموس المدمج
            eid = plt_info.get("emoji_id") or PLATFORM_EMOJI_IDS.get(plt_name, "5334998226636390258")
            platform_colors = s.get("platform_colors", {})
            per_color = platform_colors.get(plt_name)
            color_to_use = per_color if per_color else (plt_color if plt_color and plt_color != "none" else None)
            # اسم المنصة بدون عداد — زي الصورة
            display_name = PLATFORM_ICONS.get(plt_name, plt_name)
            btn_label = display_name
            try:
                kw = {"callback_data": f"show_plt_countries_{plt_name}"}
                if eid: kw["icon_custom_emoji_id"] = eid
                kw["style"] = color_to_use if color_to_use and color_to_use != "none" else "primary"
                btns.append(InlineKeyboardButton(btn_label, **kw))
            except:
                btns.append(InlineKeyboardButton(f"📱 {plt_name}", callback_data=f"show_plt_countries_{plt_name}"))
        if not btns:
            # مفيش منصات بأرقام → عرض الدول مباشرة
            platforms = {}  # force fall-through to countries block below
        else:
            for b in btns:
                markup.add(b)
            return markup
    if not platforms:
        # لو مفيش منصات (أو كلهم فاضيين) → عرض الدول مباشرة
        lyt = get_country_btn_layout()
        rw = 1 if lyt == "single" else (2 if lyt == "double" else 3)
        markup = InlineKeyboardMarkup(row_width=rw)
        cbtns = []
        for cid, info in COUNTRIES.items():
            flag = info.get("flag","🌍")
            dname = info.get("display_name", cid)
            count = info.get("numbers_count",0)
            fname = info.get("file","")
            if count==0 and fname and os.path.exists(fname):
                try:
                    with open(fname,"r",encoding="utf-8") as f:
                        count = sum(1 for l in f if l.strip())
                except: pass
            flag_eid = extract_tg_emoji_id(flag)
            btn_text = f" {dname}" if flag_eid else f"{extract_plain_emoji(flag)} {dname}"
            color = get_country_btn_color(cid)
            try:
                kw = {"callback_data": f"direct_country_{cid}"}
                if flag_eid: kw["icon_custom_emoji_id"] = flag_eid
                if color: kw["style"] = color
                cbtns.append(InlineKeyboardButton(btn_text, **kw))
            except:
                cbtns.append(InlineKeyboardButton(f"{extract_plain_emoji(flag)} {dname}", callback_data=f"direct_country_{cid}"))
        if rw == 1:
            for b in cbtns:
                markup.add(b)
        elif rw == 2:
            for i in range(0, len(cbtns), 2):
                markup.add(*cbtns[i:i+2])
        else:
            for i in range(0, len(cbtns), 3):
                markup.add(*cbtns[i:i+3])
        return markup if COUNTRIES else None



def get_welcome_text(user_id=None):
    """Get the welcome text shown above country/platform buttons - multilingual"""
    s = load_bot_settings()
    custom = s.get("custom_welcome_msg")
    if custom:
        return custom
    platforms = load_platforms()
    if platforms:
        # رسالة SERVICE MENU حسب لغة المستخدم
        lang = get_user_language(user_id) if user_id else "en"
        service_menu_titles = {
            "en": "<b>Select a Service</b> ❓",
            "ar": "<b>اختر خدمة</b> ❓",
            "ru": "<b>Выберите сервис</b> ❓",
            "bn": "<b>একটি সেবা বেছে নিন</b> ❓",
}
        return service_menu_titles.get(lang, service_menu_titles["en"])
    return get_select_country_title(user_id)


def get_countries_for_platform(platform, user_id=None):
    
    lang = get_user_language(user_id)
    # صفين زي الصورة الثانية
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    
    display_name_counts = {}
    total_counts = {}
    for info in COUNTRIES.values():
        if platform in info.get("platforms", []):
            dname = info.get("display_name")
            total_counts[dname] = total_counts.get(dname, 0) + 1

    btn_index = 0
    for cid, info in COUNTRIES.items():
        if platform in info.get("platforms", []):
            display_name = info.get("display_name", cid)
            flag = info.get("flag", "🌍")
            count = info.get("numbers_count", 0)
            # جلب العدد الحقيقي من الملف لو كان صفر
            fname = info.get("file", "")
            if count == 0 and fname and os.path.exists(fname):
                try:
                    with open(fname, "r", encoding="utf-8") as f:
                        count = sum(1 for l in f if l.strip())
                except: pass
            code = info.get("code", "")
            
            display_name_counts[display_name] = display_name_counts.get(display_name, 0) + 1
            entry_number = display_name_counts[display_name]
            
            label = f"{display_name}"
            if total_counts.get(display_name, 0) > 1:
                label += f" {entry_number}"
            if code:
                label += f" (+{code})"
            if count > 0:
                label += f" ({count})"

            emoji_id = extract_tg_emoji_id(flag)
            if not emoji_id and code:
                fresh_flag = get_flag_for_country_code(code)
                emoji_id = extract_tg_emoji_id(fresh_flag)
            
            # تبادل بين أخضر وأزرق زي الصورة
            btn_color = "success" if btn_index % 2 == 0 else "primary"
            btn_index += 1
            
            try:
                if emoji_id:
                    btn = InlineKeyboardButton(label, callback_data=f"country_{cid}", icon_custom_emoji_id=emoji_id, style=btn_color)
                else:
                    btn = InlineKeyboardButton(f"{extract_plain_emoji(flag)} {label}", callback_data=f"country_{cid}", style=btn_color)
            except Exception:
                btn = InlineKeyboardButton(f"{extract_plain_emoji(flag)} {label}", callback_data=f"country_{cid}")
            buttons.append(btn)
    
    # إضافة الأزرار في صفين
    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i:i+2])
    
    # زر الرجوع للخدمات — أحمر (danger) وعرض كامل
    back_text = "الرجوع للخدمات ←" if lang == "ar" else "← Back to Services"
    try:
        markup.add(InlineKeyboardButton(back_text, callback_data="choose_country", style="danger"))
    except:
        markup.add(InlineKeyboardButton(back_text, callback_data="choose_country"))
    return markup

def get_countries_list(user_id=None):
    lang = get_user_language(user_id)
    settings = load_bot_settings()
    row_width = settings.get("country_row_width", 1)
    markup = InlineKeyboardMarkup(row_width=row_width)
    found = False

    for cid, info in COUNTRIES.items():
        display_name = info.get("display_name", cid)
        flag = info.get("flag", "🌍")
        code = info.get("code", "??")
        btn_color = info.get("btn_color", settings.get("button_color", "danger"))

        # الاسم بدون عدد
        label = display_name

        emoji_id = extract_tg_emoji_id(flag)
        if not emoji_id and code and str(code) != "??":
            fresh_flag = get_flag_for_country_code(code)
            emoji_id = extract_tg_emoji_id(fresh_flag)
        try:
            if emoji_id:
                if btn_color and btn_color != "none":
                    btn = InlineKeyboardButton(label, callback_data=f"country_{cid}", icon_custom_emoji_id=emoji_id, style=btn_color)
                else:
                    btn = InlineKeyboardButton(label, callback_data=f"country_{cid}", icon_custom_emoji_id=emoji_id)
            else:
                plain = extract_plain_emoji(flag)
                if btn_color and btn_color != "none":
                    btn = InlineKeyboardButton(f"{plain} {label}", callback_data=f"country_{cid}", style=btn_color)
                else:
                    btn = InlineKeyboardButton(f"{plain} {label}", callback_data=f"country_{cid}")
        except Exception:
            btn = InlineKeyboardButton(f"{extract_plain_emoji(flag)} {label}", callback_data=f"country_{cid}")
        markup.add(btn)
        found = True

    return markup if found else None


def get_select_country_title(user_id=None):
    """رسالة اختر دولتك حسب اللغة"""
    lang = get_user_language(user_id) if user_id else "en"
    titles = {
        "en": "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji> | Select your country below <tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
        "ru": "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji> | Выберите страну ниже <tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
        "bn": "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji> | নিচে আপনার দেশ বেছে নিন <tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
        "hi": "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji> | नीचे अपना देश चुनें <tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
        "fr": "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji> | Choisissez votre pays ci-dessous <tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
        "es": "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji> | Selecciona tu país abajo <tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
        "tr": "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji> | Aşağıdan ülkenizi seçin <tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
        "id": "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji> | Pilih negara Anda di bawah <tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
        "fa": "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji> | کشور خود را در زیر انتخاب کنید <tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>",
    }
    return titles.get(lang, titles["en"])

def get_country_buttons(user_id=None):
    return get_platforms_list(user_id)

def remove_numbers_from_file(country_id, numbers_to_remove):
    """Remove specific numbers from the country file permanently"""
    if country_id not in COUNTRIES:
        return
    fname = COUNTRIES[country_id].get("file","")
    if not fname or not os.path.exists(fname):
        return
    try:
        with open(fname,"r",encoding="utf-8") as f:
            all_lines = [l.strip() for l in f if l.strip()]
        remove_set = set(str(n).strip() for n in numbers_to_remove)
        remaining = [l for l in all_lines if l not in remove_set]
        with open(fname,"w",encoding="utf-8") as f:
            f.write("\n".join(remaining) + ("\n" if remaining else ""))
        COUNTRIES[country_id]["numbers_count"] = len(remaining)
        print(f"🗑 Removed {len(all_lines)-len(remaining)} numbers from {country_id}, {len(remaining)} left")
    except Exception as e:
        print(f"❌ Error removing numbers: {e}")

def remove_single_number_from_file(country_id, number):
    """Remove one number from country file after OTP received"""
    remove_numbers_from_file(country_id, [number])

def get_random_number(country_name):
    if country_name not in COUNTRIES:
        return None

    filename = COUNTRIES[country_name]["file"]

    if not os.path.exists(filename):
        return None

    with open(filename, "r", encoding="utf-8") as f:
        numbers = [line.strip() for line in f if line.strip()]

    if not numbers:
        return None

    return random.choice(numbers)

def create_message_buttons(user_id=None):
    user_id = user_id or telebot.types.User(0, False, "Dummy").id
    lang = get_user_language(user_id)
    links = load_button_links()
    markup = InlineKeyboardMarkup(row_width=1)
    
    change_number_text = "تغيير الرقم" if lang == "ar" else "Change Number"
    change_country_text = "تغيير الدولة" if lang == "ar" else "Change Country"
    group_link_text = "جروب البوت" if lang == "ar" else "Group Link"
    
    try:
        markup.row(
            InlineKeyboardButton(f" {change_number_text}", callback_data="change_number", icon_custom_emoji_id="5258420634785947640", style="success"),
            InlineKeyboardButton(" Send Prefix", callback_data=f"send_prefix_{user_id}", icon_custom_emoji_id="5413879192267805083", style="danger")
        )
    except:
        markup.add(InlineKeyboardButton(f" {change_number_text}", callback_data="change_number", icon_custom_emoji_id="5258420634785947640", style="success"))
        markup.add(InlineKeyboardButton("Send Prefix", callback_data=f"send_prefix_{user_id}"))
    markup.add(InlineKeyboardButton(f" {change_country_text}", callback_data="choose_country", icon_custom_emoji_id="5447410659077661506", style="primary"))
    markup.add(InlineKeyboardButton(f" {group_link_text}", url=links.get("group_link", "https://t.me/UltronX_MegaBo"), icon_custom_emoji_id="5258513401784573443", style="success"))
    
    return markup

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CopyTextButton

def create_group_otp_keyboard(otp_code=None, mv_number=None):
    markup = InlineKeyboardMarkup(row_width=2)
    otp_buttons = load_otp_buttons()
    
    # زر النسخ: يعرض الكود بس - مش الرقم
    if otp_code and str(otp_code).strip() not in ("N/A", "----", "", None):
        otp_str = str(otp_code).replace("-", "").replace(" ", "")
        mid = len(otp_str) // 2
        btn_label = f"{otp_str[:mid]}-{otp_str[mid:]}" if mid > 0 else otp_str
        try:
            markup.add(InlineKeyboardButton(
                f" {btn_label}",
                copy_text=CopyTextButton(text=otp_str),
                icon_custom_emoji_id="5330115548900501467",
                style="primary"
            ))
        except:
            markup.add(InlineKeyboardButton(btn_label, callback_data=f"copy_{otp_str}"))
    
    btn1_name = otp_buttons[0]["name"] if len(otp_buttons) > 0 else "Number Chaanel"
    btn1_url  = otp_buttons[0]["url"]  if len(otp_buttons) > 0 else "https://t.me/UltronX_MegaBo"
    btn2_name = otp_buttons[1]["name"] if len(otp_buttons) > 1 else "Bot Panel"
    btn2_url  = otp_buttons[1]["url"]  if len(otp_buttons) > 1 else "https://t.me/TEAM_VO7EX_bot"
    
    try:
        markup.add(
            InlineKeyboardButton(
                f" {btn1_name}",
                url=btn1_url,
                icon_custom_emoji_id="5467539229468793355",
                style="success"
            ),
            InlineKeyboardButton(
                f" {btn2_name}",
                url=btn2_url,
                icon_custom_emoji_id="5314391089514291948",
                style="danger"
            )
        )
    except:
        markup.add(
            InlineKeyboardButton(btn1_name, url=btn1_url),
            InlineKeyboardButton(btn2_name, url=btn2_url)
        )
    
    return markup



@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_"))
def handle_copy_callback(call):
    otp = call.data.split("_", 1)[1]
    
    bot.answer_callback_query(call.id, f"{otp}", show_alert=True)

def create_otp_message_keyboard(otp_code):
    markup = InlineKeyboardMarkup(row_width=1)
    
    if otp_code and otp_code not in ("N/A", "----", None):
        try:
            markup.add(
                InlineKeyboardButton(
                    text=f" Copy code",
                    copy_text=CopyTextButton(text=str(otp_code)),
                    icon_custom_emoji_id="5330115548900501467"
                )
            )
        except Exception:
            markup.add(
                InlineKeyboardButton(
                    "Copy code",
                    callback_data=f"copy_otp_{otp_code}"
                )
            )
    
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_otp_"))
def copy_otp_callback(call):
    otp_code = call.data.replace("copy_otp_", "")
    bot.answer_callback_query(call.id, f"✅ Code: {otp_code}", show_alert=True)

def auto_delete_message(chat_id, message_id, delay=180):
    def delete():
        time.sleep(delay)
        try: bot.delete_message(chat_id, message_id)
        except: pass
    threading.Thread(target=delete, daemon=True).start()

def safe_send_message(chat_id, text, **kwargs):
    msg = bot.send_message(chat_id, text, **kwargs)
    if isinstance(chat_id, (int, str)) and (int(chat_id) < 0 or str(chat_id).startswith("-100")):
        auto_delete_message(int(chat_id), msg.message_id)
    return msg


original_send = bot.send_message
def hooked_send(chat_id, *args, **kwargs):
    msg = original_send(chat_id, *args, **kwargs)
    if isinstance(chat_id, (int, str)) and (int(chat_id) < 0 or str(chat_id).startswith("-100")):
        auto_delete_message(int(chat_id), msg.message_id)
    return msg
bot.send_message = hooked_send

def format_otp_message(country_name, country_flag, service_detected, number, otp, message_text, server_key="GROUP", is_group=False, show_full_number=True, user_id=None):

    SERVICE_ICONS = {
        "WHATSAPP":  "<tg-emoji emoji-id='5188683998125106802'>📞</tg-emoji>",
        "TELEGRAM":  "<tg-emoji emoji-id='5471949924658588235'>👉</tg-emoji>",
        "FACEBOOK":  "<tg-emoji emoji-id='5323261730283863478'>📱</tg-emoji>",
        "INSTAGRAM": "<tg-emoji emoji-id='5319160079465857105'>📱</tg-emoji>",
        "TIKTOK":    "<tg-emoji emoji-id='5327982530702359565'>📱</tg-emoji>",
        "SNAPCHAT":  "<tg-emoji emoji-id='5330248916224983855'>📱</tg-emoji>",
        "NETFLIX":   "<tg-emoji emoji-id='5318911503938634641'>📱</tg-emoji>",
        "APPLE":     "<tg-emoji emoji-id='5334955749409834455'>📱</tg-emoji>",
        "GOOGLE":    "<tg-emoji emoji-id='5334998226636390258'>📱</tg-emoji>",
        "GMAIL":     "<tg-emoji emoji-id='5334998226636390258'>📱</tg-emoji>",
        "TWITTER":   "<tg-emoji emoji-id='5334998226636390258'>📱</tg-emoji>",
        "MICROSOFT": "<tg-emoji emoji-id='5334998226636390258'>📱</tg-emoji>",
        "YOUTUBE":   "<tg-emoji emoji-id='5334998226636390258'>📱</tg-emoji>",
        "DISCORD":   "<tg-emoji emoji-id='5334998226636390258'>📱</tg-emoji>",
        "AMAZON":    "<tg-emoji emoji-id='5334998226636390258'>📱</tg-emoji>",
        "PAYPAL":    "<tg-emoji emoji-id='5364111181415996352'>📱</tg-emoji>",
    }

    service_upper = str(service_detected).upper()
    service_icon = "<tg-emoji emoji-id='5334998226636390258'>📱</tg-emoji>"
    for key, icon in SERVICE_ICONS.items():
        if key in service_upper:
            service_icon = icon
            break

    # شكل المستخدم (بدون is_group)
    service_name_user = f"[{service_icon}]"
    formatted = format_otp_message_v2(number, message_text, service_name_user, otp, is_group=False)

    if OTP_GROUP:
        try:
            # شكل الجروب
            service_name_group = f"[{service_icon}]"
            _grp_result = format_otp_message_v2(number, message_text, service_name_group, otp, is_group=True)
            if isinstance(_grp_result, tuple) and len(_grp_result) == 3:
                group_formatted, mv_num, grp_otp = _grp_result
            elif isinstance(_grp_result, tuple):
                group_formatted, mv_num = _grp_result
                grp_otp = otp
            else:
                group_formatted, mv_num, grp_otp = _grp_result, None, otp
            msg = original_send(OTP_GROUP, group_formatted, parse_mode="HTML", reply_markup=create_group_otp_keyboard(otp_code=grp_otp, mv_number=mv_num))
            auto_delete_message(OTP_GROUP, msg.message_id)
        except:
            pass
    return formatted

def detect_text_language(text):
    if not text: return "English"
    import re as _r
    t = text.strip()
    if _r.search(r'[\u0600-\u06FF]', t): return "Arabic"
    if _r.search(r'[\u4e00-\u9fff]', t): return "Chinese"
    if _r.search(r'[\u0900-\u097F]', t): return "Hindi"
    if _r.search(r'[\u0400-\u04FF]', t): return "Russian"
    if _r.search(r'[\u3040-\u30FF]', t): return "Japanese"
    if _r.search(r'[\uAC00-\uD7AF]', t): return "Korean"
    if _r.search(r'[\u0E00-\u0E7F]', t): return "Thai"
    if _r.search(r'[\u1000-\u109F]', t): return "Burmese"
    tl = t.lower()
    if any(c in tl for c in ['ñ','á','é','í','ó','ú','¿']): return "Spanish"
    if any(c in tl for c in ['à','â','ç','è','ê','ë']): return "French"
    if any(c in tl for c in ['ä','ö','ü','ß']): return "German"
    return "English"

SERVICE_MAP_OTP = {
    "whatsapp":   ("WS",  "5334998226636390258"),
    "واتساب":     ("WS",  "5334998226636390258"),
    "telegram":   ("TG",  "5330237710655306682"),
    "تيليجرام":   ("TG",  "5330237710655306682"),
    "facebook":   ("FB",  "5323261730283863478"),
    "فيسبوك":     ("FB",  "5323261730283863478"),
    "instagram":  ("IG", "5319160079465857105"),
    "انستقرام":   ("IG", "5319160079465857105"),
    "tiktok":     ("TT",    "5327982530702359565"),
    "تيك توك":    ("TT",    "5327982530702359565"),
    "snapchat":   ("SC",  "5330248916224983855"),
    "سناب شات":   ("SC",  "5330248916224983855"),
    "google":     ("GG",    "5303416490295304868"),
    "gmail":      ("GG",    "5303416490295304868"),
    "twitter":    ("TW",   "5346172593374248407"),
    "discord":    ("DC",   "5325612636467903082"),
    "apple":      ("AP",     "5334955749409834455"),
    "netflix":    ("NF",   "5318911503938634641"),
    "paypal":     ("PP",    "5364111181415996352"),
    "microsoft":  ("MS", "5334998226636390258"),
    "amazon":     ("AZ",    "5346056560537779652"),
    "imo":        ("IM",       "6300798614725727117"),
    "ايمو":       ("IM",       "6300798614725727117"),
    "viber":      ("VB",     "5332449498553663205"),
    "line":       ("LN",      "5323608076446613036"),
    "kakaotalk":  ("KK", "5334933574493683027"),
    "kakao":      ("KK", "5334933574493683027"),
    "wechat":     ("WC",    "5333252412361043082"),
    "reddit":     ("RD",    "5330321861949539755"),
    "linkedin":   ("LI",  "5346024520081751155"),
    "spotify":    ("SP",   "5346074681004801565"),
    "youtube":    ("YT",   "5348407822146225472"),
    "twitch":     ("TV",    "5334678011054669335"),
    "zoom":       ("ZM",      "5349328830039496657"),
    "uber":       ("UB",      "5332806467195189606"),
    "bitcoin":    ("BTC",   "5359584650958226302"),
    "ethereum":   ("ETH",  "5359321266383766546"),
    "visa":       ("VISA",      "5364075889669718872"),
    "mastercard": ("MC","5364036341610858181"),
    "airbnb":     ("AB",    "5336606809736506670"),
    "github":     ("GH",    "5346181118884331907"),
    "slack":      ("SL",     "5363899233369868662"),
    "notion":     ("NT",    "5364199932620194408"),
    "figma":      ("FG",     "5357286671656176924"),
    "blender":    ("BL",   "5364290083983736876"),
}

def format_otp_message_v2(number, sms_text, service_name="[TG]", otp_code=None, is_group=False, user_lang=None, bot_uid="", tg_user_id="", reward=None, balance=None):
    country_name, flag, region_code = detect_country_from_number(number)
    masked = mask_number(number)
    otp_text = otp_code if otp_code and otp_code != "N/A" else "----"
    lbl, eid = "Service", "5233354831984353090"
    for kw,(l,e) in SERVICE_MAP_OTP.items():
        if kw in (sms_text or "").lower():
            lbl, eid = l, e
            break
    else:
        raw = str(service_name).strip("[]").strip()
        if raw and not raw.startswith("<"): lbl = raw.upper()
        for kw,(l,e) in SERVICE_MAP_OTP.items():
            if kw in str(service_name).lower():
                lbl, eid = l, e
                break
    sico = f"<tg-emoji emoji-id='{eid}'>📞</tg-emoji>"
    plain_flag = extract_plain_emoji(flag)
    flag_eid = extract_tg_emoji_id(flag)
    flag_display = f"<tg-emoji emoji-id='{flag_eid}'>{plain_flag}</tg-emoji>" if flag_eid else plain_flag
    mlang = detect_text_language(sms_text or "")

    # ─── شكل الجروب ───
    if is_group:
        full_number = str(number).lstrip("+")
        q = max(4, len(full_number) // 4)
        # شكل MA-X زي الصورة: 「🇦🇴 #AO[WS]2449MA-X1886 」
        mx_number = full_number[:q] + "MA-X" + full_number[-q:]

        svc_label = lbl if lbl != "Service" else "📱"

        msg_text = f"「{flag_display} #{region_code}[{svc_label}]{mx_number} 」"
        return (msg_text, full_number, otp_code)

    # ─── شكل المستخدم الجديد ───
    full_num_display = str(number).lstrip("+")

    # تنسيق الـ OTP بشرطة في المنتصف
    if otp_text != "----":
        otp_clean = str(otp_text).replace("-", "").replace(" ", "")
        mid = len(otp_clean) // 2
        otp_formatted = f"{otp_clean[:mid]}-{otp_clean[mid:]}" if mid > 0 else otp_clean
    else:
        otp_formatted = "----"

    # قيمة الـ reward من الإعدادات لو مش متبعتة
    if reward is None:
        try:
            _ref_settings = load_referral_settings()
            reward = _ref_settings.get("code_bonus", 0.0020)
        except Exception:
            reward = 0.0020
    if balance is None:
        balance = reward  # fallback

    reward_str = f"{float(reward):.4f}"
    balance_str = f"{float(balance):.4f}"

    return (
        f"<tg-emoji emoji-id='5397575638146110953'>🌎</tg-emoji>"
        f"Country: {country_name} {flag_display} - "
        f"<tg-emoji emoji-id='{eid}'>📱</tg-emoji>\n"
        f"<tg-emoji emoji-id='5465169893580086142'>☎️</tg-emoji>"
        f"Number: {full_num_display}\n"
        f"<tg-emoji emoji-id='5330115548900501467'>🔑</tg-emoji>"
        f"OTP Code: {otp_formatted}\n"
        f"<tg-emoji emoji-id='5188344996356448758'>🏆</tg-emoji> - &gt; Reward: {reward_str}\n"
        f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> - &gt; Balance: {balance_str}"
    )


@bot.message_handler(commands=["start"])
def start(msg):
    threading.Thread(target=_start_handler, args=(msg,), daemon=True).start()

def _start_handler(msg):
    user_id = msg.from_user.id
    if is_banned(user_id):
        bot.reply_to(msg, t(user_id, "banned"))
        return
    if msg.chat.type == "private":
        referrer_id = None
        if msg.text and len(msg.text.split()) > 1:
            param = msg.text.split()[1]
            if param.startswith("ref_"):
                try:
                    referrer_id = int(param.replace("ref_",""))
                    if referrer_id == user_id: referrer_id = None
                except: referrer_id = None

        is_new_user = str(user_id) not in USERS
        if is_new_user:
            if referrer_id:
                USERS[str(user_id)] = {"selected_country":None,"selected_number":None,"join_date":datetime.now().strftime('%Y-%m-%d'),"activations":0,"language":"en","pending_referrer":referrer_id}
            else:
                USERS[str(user_id)] = {"selected_country":None,"selected_number":None,"join_date":datetime.now().strftime('%Y-%m-%d'),"activations":0,"language":"en"}
            save_users()

        # 1️⃣ أول حاجة: الاشتراك الإجباري
        channels = check_subscription(user_id)
        if channels:
            send_subscription_message_with_image(msg.chat.id, user_id)
            return

        # 2️⃣ لو مستخدم جديد ولسه ما اختارش لغة: اختيار اللغة
        user_lang_set = USERS.get(str(user_id), {}).get("lang_chosen", False)
        if not user_lang_set:
            lang_markup = InlineKeyboardMarkup(row_width=2)
            lang_markup.add(
                InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
                InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar")
            )
            bot.send_message(
                msg.chat.id,
                "🌍 <b>Choose Language / اختر اللغة</b>",
                parse_mode="HTML",
                reply_markup=lang_markup
            )
            return

        # 3️⃣ معالجة الإحالة للمستخدم الجديد
        if referrer_id and is_new_user:
            process_referral(user_id, referrer_id)
            try:
                settings_ref = load_referral_settings()
                _cb = settings_ref.get("code_bonus", 0.003)
                bot.send_message(user_id,
                    f"🎉 <b>Welcome!</b> You joined via a referral link!\n\n"
                    f"<tg-emoji emoji-id='5888663955412359816'>🔥</tg-emoji> Earn <b>+${_cb:.3f}</b> for each OTP you receive!",
                    parse_mode="HTML")
            except: pass

        if str(user_id) in USERS:
            USERS[str(user_id)]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_users()

        if is_admin(user_id):
            bot.send_message(msg.chat.id, "🎛 <b>Admin Panel</b>\n\nChoose action:", parse_mode="HTML", reply_markup=get_admin_menu())
            return

        USERS.setdefault(str(user_id), {})
        USERS[str(user_id)]["welcome_shown"] = True
        save_users()

        # 4️⃣ الخدمات — أول الأزرار الأرضية بعدين المنصات
        user_obj = msg.from_user
        lang = get_user_language(user_id)
        welcome_msg = get_mody_welcome_msg(user_obj, lang)
        
        # إرسال الأزرار الأرضية فقط مع رسالة الترحيب
        bot.send_message(msg.chat.id, welcome_msg, parse_mode="HTML", reply_markup=get_main_reply_keyboard(user_id))
    else:
        if is_admin(user_id):
            bot.send_message(msg.chat.id, t(user_id,"group_hello_admin"), parse_mode="HTML")
        else:
            bot.send_message(msg.chat.id, t(user_id,"group_hello"), parse_mode="HTML")


@bot.message_handler(commands=["takenumber"])
def getnumber_command(msg):
    user_id = msg.from_user.id
    if is_banned(user_id):
        bot.reply_to(msg, t(user_id, "banned"))
        return
    if msg.chat.type != "private":
        return
    channels = check_subscription(user_id)

    if channels:
        send_subscription_message_with_image(msg.chat.id, user_id)
        return
    welcome_text = get_welcome_text(user_id)
    markup = get_country_buttons_all(user_id)
    if markup:
        bot.send_message(msg.chat.id, welcome_text, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(msg.chat.id, welcome_text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_lang_"))
def set_language_callback(call):
    user_id = call.from_user.id
    selected_lang = call.data.replace("set_lang_", "")  # en / ar / ru / bn

    if str(user_id) not in USERS:
        USERS[str(user_id)] = {"selected_country": None, "selected_number": None, "language": selected_lang, "activations": 0, "join_date": datetime.now().strftime('%Y-%m-%d'), "lang_chosen": True}
    else:
        USERS[str(user_id)]["language"] = selected_lang
        USERS[str(user_id)]["lang_chosen"] = True
    save_users()

    pending_referrer = USERS[str(user_id)].pop("pending_referrer", None)
    if pending_referrer:
        process_referral(user_id, pending_referrer)

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    if is_admin(user_id):
        bot.send_message(call.message.chat.id, "🎛 <b>Admin Panel</b>\n\nChoose action:", parse_mode="HTML", reply_markup=get_admin_menu())
        return

    USERS[str(user_id)]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_users()

    user_obj = call.from_user
    lang = get_user_language(user_id)
    welcome_msg = get_mody_welcome_msg(user_obj, lang)
    
    # إرسال الأزرار الأرضية فقط مع رسالة الترحيب بعد اختيار اللغة
    bot.send_message(call.message.chat.id, welcome_msg, parse_mode="HTML", reply_markup=get_main_reply_keyboard(user_id))


@bot.callback_query_handler(func=lambda call: call.data == "show_instructions")
def show_instructions_callback(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    
    settings = load_referral_settings()
    code_bonus = settings.get("code_bonus", 0.01)
    referral_bonus = settings.get("referral_bonus", 0.50)
    codes_required = settings.get("codes_required_for_referral", 3)
    min_withdrawal = settings.get("min_withdrawal", 5.0)
    
    if lang == 'ar':
        instructions_text = f"""📖 <b>دليل استخدام البوت</b>

━━━━━━ <b>📱 استلام الأكواد</b> ━━━━━━

1️⃣ <b>اختيار الدولة:</b>
   • اضغط على "Take a number"
   • اختر الدولة التي تريدها

2️⃣ <b>اختيار الرقم:</b>
   • ستظهر لك الأرقام المتاحة
   • اختر الرقم المناسب

3️⃣ <b>استلام الكود:</b>
   • استخدم الرقم للتسجيل في أي موقع/تطبيق
   • سيصلك الكود تلقائياً هنا في البوت

━━━━━━ <b>💰 نظام الأرباح</b> ━━━━━━

💎 <b>بونص الكود:</b>
   • تحصل على <b>${format_decimal(code_bonus)}</b> عن كل كود تستلمه

👥 <b>بونص الإحالة:</b>
   • شارك رابط الإحالة مع أصدقائك
   • عندما يستلم صديقك <b>{codes_required} أكواد</b>
   • تحصل على <b>${referral_bonus:.2f}</b> مباشرة!

━━━━━━ <b>💵 السحب</b> ━━━━━━

💰 <b>الحد الأدنى:</b> ${min_withdrawal:.2f}
📝 <b>طرق السحب:</b>
   • فودافون كاش
   • USDT (TRC20/BEP20)
   • Binance ID

⚡ <b>خطوات السحب:</b>
   1. اذهب إلى "حسابي"
   2. اضغط "سحب الرصيد"
   3. اختر طريقة السحب
   4. أدخل بياناتك
   5. سيتم التحويل خلال 24 ساعة

━━━━━━ <b>📋 ملاحظات</b> ━━━━━━

⏰ انتظر الكود بعد طلب التحقق من الموقع
🔄 يمكنك تغيير الرقم في أي وقت
✅ الأرباح تُضاف تلقائياً لرصيدك

━━━━━━ شكراً لثقتك ━━━━━━

🆘 للمساعدة تواصل مع المطور"""
    else:
        instructions_text = f"""📖 <b>Bot Guide</b>

━━━━━━ <b>📱 Receiving Codes</b> ━━━━━━

1️⃣ <b>Choose Country:</b>
   • Click on "Take a number"
   • Select your desired country

2️⃣ <b>Choose Number:</b>
   • Available numbers will appear
   • Select the number you want

3️⃣ <b>Receive Code:</b>
   • Use the number to register on any site/app
   • The code will arrive automatically here in the bot

━━━━━━ <b>💰 Earning System</b> ━━━━━━

💎 <b>Code Bonus:</b>
   • Earn <b>${format_decimal(code_bonus)}</b> for each code you receive

👥 <b>Referral Bonus:</b>
   • Share your referral link with friends
   • When your friend receives <b>{codes_required} codes</b>
   • You get <b>${referral_bonus:.2f}</b> instantly!

━━━━━━ <b>💵 Withdrawal</b> ━━━━━━

💰 <b>Minimum:</b> ${min_withdrawal:.2f}
📝 <b>Withdrawal Methods:</b>
   • Vodafone Cash
   • USDT (TRC20/BEP20)
   • Binance ID

⚡ <b>How to Withdraw:</b>
   1. Go to "My Account"
   2. Click "Withdraw Balance"
   3. Choose withdrawal method
   4. Enter your details
   5. Transfer within 24 hours

━━━━━━ <b>📋 Notes</b> ━━━━━━

⏰ Wait for code after verification request from the site
🔄 You can change the number anytime
✅ Earnings are added automatically

━━━━━━ Thanks for your trust ━━━━━━

🆘 For help, contact the developer"""
    
    markup = InlineKeyboardMarkup(row_width=1)
    developer_btn_text = "🆘 Contact Developer" if get_user_language(user_id) == "en" else "🆘 تواصل مع المطور"
    markup.add(
        InlineKeyboardButton(developer_btn_text, url="t.me/JTF_l")
    )
    markup.add(
        InlineKeyboardButton(
            "رجوع" if get_user_language(user_id) == "ar" else "Back",
            callback_data="back_to_main_user",
            icon_custom_emoji_id="5321334093126842469",
            style="primary"
        )
    )
    
    bot.edit_message_text(
        instructions_text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "my_account")
def my_account_callback(call):
    user_id = call.from_user.id
    
    user_data = USERS.get(str(user_id), {})
    activations = user_data.get("activations", 0)
    join_date = user_data.get("join_date", datetime.now().strftime('%Y-%m-%d'))
    lang = get_user_language(user_id)
    
    selected_country = user_data.get("selected_country")
    selected_number = user_data.get("selected_number")
    
    if selected_number and selected_country:
        number_status = f"✅ رقم نشط: <code>+{selected_number.lstrip('+')}</code>" if lang == "ar" else f"✅ Active number: <code>+{selected_number.lstrip('+')}</code>"
    else:
        number_status = "❌ لا يوجد رقم حالياً" if lang == "ar" else "❌ No number currently"
    
    if lang == "ar":
        account_text = (
            f"👤 <b>معلومات حسابك:</b>\n\n"
            f"🆔 <b>معرفك:</b> <code>{user_id}</code>\n"
            f"📅 <b>تاريخ الانضمام:</b> {join_date}\n"
            f"📊 <b>الأكواد المستلمة:</b> {activations}\n"
            f"🌐 <b>اللغة:</b> العربية\n\n"
            f"💡 <b>حالة رقمك:</b>\n{number_status}"
        )
    else:
        account_text = (
            f"👤 <b>Your Account Info:</b>\n\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"📅 <b>Join Date:</b> {join_date}\n"
            f"📊 <b>Codes Received:</b> {activations}\n"
            f"🌐 <b>Language:</b> English\n\n"
            f"💡 <b>Number Status:</b>\n{number_status}"
        )
    
    markup = InlineKeyboardMarkup(row_width=1)
    back_text = "رجوع" if lang == "ar" else "Back"
    markup.add(InlineKeyboardButton(back_text, callback_data="back_to_main_user", icon_custom_emoji_id="5321334093126842469"))
    
    try:
        bot.edit_message_text(account_text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, account_text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "bonus_info")
def bonus_info_callback(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    settings = load_referral_settings()
    
    code_bonus = settings.get("code_bonus", 0.01)
    referral_bonus = settings.get("referral_bonus", 0.50)
    codes_required = settings.get("codes_required_for_referral", 3)
    min_withdrawal = settings.get("min_withdrawal", 5.0)
    
    if lang == "ar":
        info_text = (
            "📖 <b>نظام البونص والإحالات</b>\n\n"
            "━━━━━━ <b>كيف تربح؟</b> ━━━━━━\n\n"
            f"💎 <b>بونص الكود:</b>\n"
            f"   • تحصل على <b>${format_decimal(code_bonus)}</b> عن كل كود تستلمه\n\n"
            f"👥 <b>بونص الإحالة:</b>\n"
            f"   • شارك رابط الإحالة مع أصدقائك\n"
            f"   • عندما ينضم صديق عبر رابطك\n"
            f"   • ويستلم <b>{codes_required} أكواد</b>\n"
            f"   • تحصل على <b>${referral_bonus:.2f}</b> مباشرة!\n\n"
            "━━━━━━ <b>السحب</b> ━━━━━━\n\n"
            f"💰 <b>الحد الأدنى للسحب:</b> ${min_withdrawal:.2f}\n"
            "📝 <b>طرق السحب المتاحة:</b>\n"
            "   • فودافون كاش\n"
            "   • USDT (TRC20/BEP20)\n"
            "   • Binance ID\n\n"
            "━━━━━━ <b>ملاحظات مهمة</b> ━━━━━━\n\n"
            "✅ الأرباح تُضاف تلقائياً لرصيدك\n"
            "✅ يمكنك تتبع إحالاتك من صفحة حسابك\n"
            "✅ طلبات السحب تُعالج خلال 24 ساعة"
        )
    else:
        info_text = (
            "📖 <b>Bonus & Referral System</b>\n\n"
            "━━━━━━ <b>How to Earn?</b> ━━━━━━\n\n"
            f"💎 <b>Code Bonus:</b>\n"
            f"   • Get <b>${format_decimal(code_bonus)}</b> for each code you receive\n\n"
            f"👥 <b>Referral Bonus:</b>\n"
            f"   • Share your referral link with friends\n"
            f"   • When a friend joins via your link\n"
            f"   • And receives <b>{codes_required} codes</b>\n"
            f"   • You get <b>${referral_bonus:.2f}</b> instantly!\n\n"
            "━━━━━━ <b>Withdrawal</b> ━━━━━━\n\n"
            f"💰 <b>Minimum Withdrawal:</b> ${min_withdrawal:.2f}\n"
            "📝 <b>Available Methods:</b>\n"
            "   • Vodafone Cash\n"
            "   • USDT (TRC20/BEP20)\n"
            "   • Binance ID\n\n"
            "━━━━━━ <b>Important Notes</b> ━━━━━━\n\n"
            "✅ Earnings are added automatically to your balance\n"
            "✅ Track your referrals from your account page\n"
            "✅ Withdrawal requests are processed within 24 hours"
        )
    
    markup = InlineKeyboardMarkup()
    back_text = "رجوع" if lang == "ar" else "Back"
    markup.add(InlineKeyboardButton(f" {back_text}", callback_data="my_account", icon_custom_emoji_id="5321334093126842469"))
    
    bot.edit_message_text(
        info_text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "change_lang")
def change_language_callback(call):
    user_id = call.from_user.id
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
        InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar")
    )
    
    bot.edit_message_text(
        "🌍 <b>Choose Language / اختر اللغة</b>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main_user")
def back_to_main_user_callback(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    
    markup = get_country_buttons(user_id)
    if markup:
        if lang == "ar":
            welcome_text = get_welcome_text()
        else:
            welcome_text = get_welcome_text()
        try:
            bot.edit_message_text(
                welcome_text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=markup
            )
        except:
            bot.send_message(call.message.chat.id, welcome_text, parse_mode="HTML", reply_markup=markup)
    else:
        try:
            text = t(user_id, "welcome")
            if not text: text = "🌐 <b>مرحباً بك!</b>"
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=get_main_menu_lang(user_id)
            )
        except:
            pass

def get_single_channel_keyboard(channel, lang="en"):
    markup = InlineKeyboardMarkup(row_width=1)
    btn_name = channel.get(f"name_{lang}", channel.get("name", "Join"))
    try:
        markup.add(InlineKeyboardButton(f" {btn_name}", url=channel['url'], icon_custom_emoji_id="5458603043203327669", style="primary"))
    except:
        markup.add(InlineKeyboardButton(btn_name, url=channel['url']))
    try:
        markup.add(InlineKeyboardButton(
            " Subscribed",
            callback_data="check_sub",
            icon_custom_emoji_id="5285533062518566401",
            style="danger"
        ))
    except:
        markup.add(InlineKeyboardButton("Subscribed", callback_data="check_sub"))
    return markup

def get_subscription_message_for_channel(channel, user_id):
    lang = get_user_language(user_id)
    if lang == "ru":
        return ("<b><tg-emoji emoji-id='5418159410646099061'>🚫</tg-emoji></b><b> Вы ещё не верифицированы!</b>\n\n<i><tg-emoji emoji-id='5803175856905917502'>📣</tg-emoji></i><i> Подпишитесь на все каналы для продолжения.</i>\n\n<i><tg-emoji emoji-id='5332336747072208845'>🔥</tg-emoji></i><i> Подпишитесь сейчас для доступа ко всем функциям.</i>\n\n<tg-emoji emoji-id='5805205259018048822'>⏰</tg-emoji><b> После подписки нажмите &quot;Подписан&quot; для проверки.</b>\n━━━━━━━━━━━━━━━\n<tg-emoji emoji-id='5116444615301399317'>🔘</tg-emoji> Подпишитесь и нажмите &quot;Подписан&quot;")
    return ("═══《 <tg-emoji emoji-id='5244807637157029775'>🚫</tg-emoji> REQUIREMENT 》═══\n\n<tg-emoji emoji-id='5197304993920616826'>📣</tg-emoji> You must subscribe to all required channels to continue  \n\n<tg-emoji emoji-id='5237828920891427376'>💡</tg-emoji> After joining, press the Subscribed button below to proceed")

@bot.callback_query_handler(func=lambda call: call.data == "verify_subscription")
def verify_subscription_callback(call):
    user_id = call.from_user.id
    channels = check_subscription(user_id)

    if not channels:
        # اشترك — نشوف هل اختار لغة قبل كده
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass

        lang_chosen = USERS.get(str(user_id), {}).get("lang_chosen", False)
        if not lang_chosen:
            # وجهه لاختيار اللغة
            lang_markup = InlineKeyboardMarkup(row_width=2)
            lang_markup.add(
                InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
                InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar")
            )
            lang_markup.add(
                InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
                InlineKeyboardButton("🇧🇩 বাংলা", callback_data="set_lang_bn")
            )
            bot.send_message(
                call.message.chat.id,
                "🌍 <b>Choose Language / اختر اللغة</b>",
                parse_mode="HTML",
                reply_markup=lang_markup
            )
        else:
            start(call.message)
    else:
        bot.answer_callback_query(call.id, ml(user_id, "join_first"), show_alert=True)
        try:
            bot.edit_message_text(
                get_subscription_message(user_id),
                call.message.chat.id, call.message.message_id,
                parse_mode="HTML",
                reply_markup=get_full_subscription_keyboard(user_id)
            )
        except: pass

    if str(user_id) not in USERS:
        USERS[str(user_id)] = {"selected_country": None, "selected_number": None}
        save_users()

    markup = get_country_buttons(user_id)
    welcome_text = get_welcome_text(user_id)
    
    # إرسال الأزرار الأرضية أولاً
    bot.send_message(call.message.chat.id, get_welcome_text(user_id), parse_mode="HTML", reply_markup=get_main_reply_keyboard(user_id))
    if markup:
        bot.send_message(call.message.chat.id, welcome_text, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, t(user_id, "welcome"), parse_mode="HTML", reply_markup=get_main_menu_lang(user_id))

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel_callback(call):
    user_id = call.from_user.id

    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "⛔️ غير مصرح لك بالوصول لهذه اللوحة", show_alert=True)
        return

    bot.edit_message_text(
        "🎛 <b>لوحة الإدارة</b>\n\nاختر الإجراء المطلوب:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=get_admin_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("na_add_country_srv_"))
def na_add_country_server_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    state = user_states.get(user_id, {})
    if not state.get("numbers_file"):
        bot.answer_callback_query(call.id, "❌ Session expired!", show_alert=True)
        return
    
    server = call.data.replace("na_add_country_srv_", "")
    
    # حفظ السيرفر وإنهاء الإضافة
    user_states[user_id] = {
        "action": "na_add_country_finish_ready",
        "numbers_file": state.get("numbers_file"),
        "country_code": state.get("country_code"),
        "country_name": state.get("country_name"),
        "num_cleaned": state.get("num_cleaned"),
        "server": server,
        "selected_platform": state.get("selected_platform"),
    }
    
    state = user_states[user_id]
    country_name = state.get("country_name")
    num_cleaned = state.get("num_cleaned", 0)
    country_code = state.get("country_code")
    selected_platform = state.get("selected_platform", "General")
    flag = get_flag_for_country_code(country_code)
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("✅ تأكيد الإضافة", callback_data="na_add_country_finish"))
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="admin"))
    
    try:
        bot.edit_message_text(
            f"✅ <b>تأكيد إضافة الدولة</b>\n\n"
            f"🌍 الاسم: <b>{flag} {country_name}</b>\n"
            f"🔢 رمز الدولة: <b>+{country_code}</b>\n"
            f"📊 عدد الأرقام: <b>{num_cleaned}</b>\n"
            f"🖥️ السيرفر: <b>{server}</b>\n"
            f"📱 المنصة: <b>{selected_platform}</b>\n\n"
            f"اضغط تأكيد للإضافة:",
            call.message.chat.id, call.message.message_id,
            parse_mode="HTML", reply_markup=markup
        )
    except:
        bot.send_message(call.message.chat.id,
            f"✅ <b>تأكيد:</b> {flag} {country_name} ({num_cleaned} أرقام)\nاضغط تأكيد:",
            parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "na_add_country_edit_name")
def na_add_country_edit_name_callback(call):
    user_id = call.from_user.id
    if not is_numbers_admin(user_id):
        return
    
    lang = get_user_language(user_id)
    state = user_states.get(user_id)
    if not state:
        bot.answer_callback_query(call.id, "❌ انتهت الجلسة!", show_alert=True)
        return
    
    state["action"] = "na_add_country_edit_name_input"
    text = "📝 يرجى إرسال الاسم الجديد للدولة:" if lang == "ar" else "📝 Please send the new country name:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("na_add_country_plt_"))
def na_add_country_platform_callback(call):
    user_id = call.from_user.id
    if not is_numbers_admin(user_id):
        return
    
    if user_id not in user_states or user_states[user_id].get("action") != "na_add_country_platforms":
        bot.answer_callback_query(call.id, "❌ انتهت الجلسة!", show_alert=True)
        return
    
    platform = call.data.replace("na_add_country_plt_", "")
    state = user_states[user_id]
    selected_platforms = state.get("selected_platforms", [])
    
    if platform == "ALL":
        selected_platforms = ["Facebook", "WhatsApp", "Telegram", "Instagram", "Twitter", "TikTok", "Discord", "Gmail"]
    elif platform in selected_platforms:
        selected_platforms.remove(platform)
    else:
        selected_platforms.append(platform)
    
    user_states[user_id]["selected_platforms"] = selected_platforms
    
    platform_icons = {
        "Facebook": "📘", "WhatsApp": "💬", "Telegram": "✈️",
        "Instagram": "📸", "Twitter": "🐦", "TikTok": "📱",
        "Discord": "🎮", "Gmail": "📧"
    }
    
    def get_btn_text(name, icon):
        check = "✅" if name in selected_platforms else ""
        return f"{check} {icon} {name}"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(get_btn_text("Facebook", "📘"), callback_data="na_add_country_plt_Facebook"),
        InlineKeyboardButton(get_btn_text("WhatsApp", "💬"), callback_data="na_add_country_plt_WhatsApp")
    )
    markup.add(
        InlineKeyboardButton(get_btn_text("Telegram", "✈️"), callback_data="na_add_country_plt_Telegram"),
        InlineKeyboardButton(get_btn_text("Instagram", "📸"), callback_data="na_add_country_plt_Instagram")
    )
    markup.add(
        InlineKeyboardButton(get_btn_text("Twitter", "🐦"), callback_data="na_add_country_plt_Twitter"),
        InlineKeyboardButton(get_btn_text("TikTok", "📱"), callback_data="na_add_country_plt_TikTok")
    )
    markup.add(
        InlineKeyboardButton(get_btn_text("Discord", "🎮"), callback_data="na_add_country_plt_Discord"),
        InlineKeyboardButton(get_btn_text("Gmail", "📧"), callback_data="na_add_country_plt_Gmail")
    )
    markup.add(
        InlineKeyboardButton("🌐 جميع المنصات", callback_data="na_add_country_plt_ALL")
    )
    markup.add(InlineKeyboardButton("✅ تأكيد وإنهاء", callback_data="na_add_country_finish"))
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="numbers_admin_panel"))
    
    
    platform_icons = {
        "Facebook": "📘", "WhatsApp": "💬", "Telegram": "✈️",
        "Instagram": "📸", "Twitter": "🐦", "TikTok": "📱",
        "Discord": "🎮", "Gmail": "📧"
    }
    
    platforms_text = ", ".join([f"{platform_icons.get(p, '📱')} {p}" for p in selected_platforms]) if selected_platforms else "لا يوجد"
    
    bot.edit_message_text(
        f"✅ <b>الخطوة 5/5 - اختيار المنصات</b>\n\n"
        f"🌍 الدولة: <b>{state.get('country_name')}</b>\n"
        f"🔢 رمز الدولة: <b>{state.get('country_code')}</b>\n"
        f"📱 <b>المنصات المختارة:</b> {platforms_text}\n\n"
        f"اختر المنصات التي تعمل عليها هذه الأرقام:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "na_add_country_finish")
def na_add_country_finish_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    state = user_states.get(user_id, {})
    country_name = state.get("country_name")
    country_code = state.get("country_code")
    numbers_file = state.get("numbers_file")
    server = state.get("server")
    selected_platform = state.get("selected_platform")  # منصة واحدة من platforms.json
    num_cleaned = state.get("num_cleaned", 0)
    
    if not country_name or not numbers_file or not server:
        bot.answer_callback_query(call.id, "❌ Session expired!", show_alert=True)
        return
    
    flag = get_flag_for_country_code(country_code)
    country_id = f"{country_name}_{uuid.uuid4().hex[:6]}"
    
    # المنصات: لو في منصة مختارة → [plt_name] وإلا ["General"]
    platforms_list = [selected_platform] if selected_platform else ["General"]
    
    COUNTRIES[country_id] = {
        "display_name": country_name,
        "file": numbers_file,
        "code": country_code,
        "flag": flag,
        "server": server,
        "platforms": platforms_list,
        "numbers_count": num_cleaned,
        "added_by": user_id,
        "added_at": datetime.now().isoformat()
    }
    save_countries()
    
    # ═══ إذاعة تلقائية لجميع المستخدمين عند إضافة دولة جديدة ═══
    def _broadcast_new_country():
        try:
            # إيموجي المنصات
            PLATFORM_EMOJIS = {
                "WhatsApp":  "💬",
                "Facebook":  "📘",
                "Telegram":  "✈️",
                "Instagram": "📸",
                "Twitter":   "🐦",
                "TikTok":    "📱",
                "Discord":   "🎮",
                "Gmail":     "📧",
            }
            # بناء نص المنصات مع إيموجي
            if platforms_list and platforms_list != ["General"]:
                platforms_display = "\n".join(
                    f"{PLATFORM_EMOJIS.get(p, '📱')} | <b>{p}</b>"
                    for p in platforms_list
                )
            else:
                platforms_display = "📱 | <b>General</b>"

            # استخراج الفلاق كنص عادي للرسالة
            plain_flag = extract_plain_emoji(flag) if flag else "🌍"

            broadcast_text = (
                f"🆕 <b>New Stock Added</b> 🔥\n\n"
                f"{plain_flag} {platforms_display}\n"
                f"💲 Rate per OTP: 0.001$"
            )
            broadcast_markup = InlineKeyboardMarkup()
            try:
                broadcast_markup.add(InlineKeyboardButton(
                    "📲 GET NUMBER",
                    callback_data="choose_country",
                    style="success"
                ))
            except:
                broadcast_markup.add(InlineKeyboardButton(
                    "📲 GET NUMBER",
                    callback_data="choose_country"
                ))
            sent = 0
            for uid in list(USERS.keys()):
                try:
                    bot.send_message(
                        int(uid),
                        broadcast_text,
                        parse_mode="HTML",
                        reply_markup=broadcast_markup
                    )
                    sent += 1
                    time.sleep(0.05)
                except:
                    pass
            print(f"✅ تم إرسال إشعار إضافة الدولة '{country_name}' لـ {sent} مستخدم")
        except Exception as e:
            print(f"⚠️ خطأ في إذاعة الدولة الجديدة: {e}")

    Thread(target=_broadcast_new_country, daemon=True).start()
    # ════════════════════════════════════════════════════════════

    if user_id in user_states:
        del user_states[user_id]
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ إضافة دولة أخرى", callback_data="admin_add_country"),
    )
    try:
        markup.add(make_back_button("رجوع للوحة", "admin"))
    except:
        markup.add(InlineKeyboardButton("◀ رجوع", callback_data="admin"))
    
    plt_text = selected_platform if selected_platform else "General"
    try:
        bot.edit_message_text(
            f"✅ <b>Country Added Successfully!</b>\n\n"
            f"🌍 Name: <b>{flag} {country_name}</b>\n"
            f"🔢 Code: <b>+{country_code}</b>\n"
            f"📊 Numbers: <b>{num_cleaned}</b>\n"
            f"🖥️ Server: <b>{server}</b>\n"
            f"📱 Platform: <b>{plt_text}</b>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
    except:
        bot.send_message(call.message.chat.id,
            f"✅ <b>Country Added!</b>\n🌍 {flag} {country_name} | {num_cleaned} numbers",
            parse_mode="HTML", reply_markup=markup)

def get_flag_for_country_code(country_code):
    try:
       
        code_str = str(country_code).replace('+', '').strip()
        if not code_str.isdigit():
            return "🌍"
            
        import phonenumbers
        from phonenumbers.phonenumberutil import region_code_for_country_code
        
       
        region = region_code_for_country_code(int(code_str))
        if region and region != 'ZZ':
            return get_flag(region)
    except Exception as e:
        print(f"Error getting flag for code {country_code}: {e}")
        
    return "🌍"

@bot.callback_query_handler(func=lambda call: call.data == "na_list_countries")
def na_list_countries_callback(call):
    user_id = call.from_user.id
    if not is_numbers_admin(user_id):
        return
    
    if not COUNTRIES:
        text = "📋 <b>الدول المتاحة</b>\n\n❌ لا توجد دول مضافة بعد!"
    else:
        text = "📋 <b>الدول المتاحة</b>\n\n"
        for idx, (country_name, info) in enumerate(sorted(COUNTRIES.items()), 1):
            flag = info.get("flag", "🌍")
            server = info.get("server", "N/A")
            platforms = info.get("platforms", [])
            platforms_count = len(platforms)
            text += f"{idx}. {flag} <b>{country_name}</b> - {server} ({platforms_count} منصات)\n"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="numbers_admin_panel",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "na_ban_user")
def na_ban_user_callback(call):
    user_id = call.from_user.id
    if not is_numbers_admin(user_id):
        return
    
    user_states[user_id] = {"mode": "na_ban_user"}
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="numbers_admin_panel"))
    
    bot.edit_message_text(
        "🚫 <b>حظر مستخدم</b>\n\n"
        "📝 أرسل معرف المستخدم (ID) الذي تريد حظره:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "na_unban_user")
def na_unban_user_callback(call):
    user_id = call.from_user.id
    if not is_numbers_admin(user_id):
        return
    
    user_states[user_id] = {"mode": "na_unban_user"}
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="numbers_admin_panel"))
    
    bot.edit_message_text(
        "✅ <b>إلغاء حظر مستخدم</b>\n\n"
        "📝 أرسل معرف المستخدم (ID) الذي تريد إلغاء حظره:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "na_banned_list")
def na_banned_list_callback(call):
    user_id = call.from_user.id
    if not is_numbers_admin(user_id):
        return
    
    if not BANNED:
        text = "📊 <b>قائمة المحظورين</b>\n\n✅ لا يوجد مستخدمين محظورين!"
    else:
        text = "📊 <b>قائمة المحظورين</b>\n\n"
        for idx, banned_id in enumerate(BANNED[:50], 1):
            text += f"{idx}. <code>{banned_id}</code>\n"
        if len(BANNED) > 50:
            text += f"\n... و {len(BANNED) - 50} آخرين"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="numbers_admin_panel",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_manage_numbers_admins")
def admin_manage_numbers_admins_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "⛔️ غير مصرح لك!", show_alert=True)
        return
    
    text = "🧮 <b>إدارة أدمن الأرقام</b>\n\n"
    text += f"👥 عدد أدمن الأرقام: {len(NUMBERS_ADMINS)}\n\n"
    
    if NUMBERS_ADMINS:
        text += "<b>القائمة الحالية:</b>\n"
        for idx, admin_id in enumerate(NUMBERS_ADMINS, 1):
            text += f"{idx}. <code>{admin_id}</code>\n"
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ إضافة أدمن أرقام", callback_data="add_numbers_admin"),
        InlineKeyboardButton("➖ حذف أدمن أرقام", callback_data="remove_numbers_admin")
    )
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin_panel",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "add_numbers_admin")
def add_numbers_admin_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    user_states[user_id] = {"mode": "add_numbers_admin"}
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="admin_manage_numbers_admins"))
    
    bot.edit_message_text(
        "➕ <b>إضافة أدمن أرقام جديد</b>\n\n"
        "📝 أرسل معرف المستخدم (User ID) الذي تريد تعيينه كأدمن أرقام:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "remove_numbers_admin")
def remove_numbers_admin_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    if not NUMBERS_ADMINS:
        bot.answer_callback_query(call.id, "❌ لا يوجد أدمن أرقام!", show_alert=True)
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    for admin_id in NUMBERS_ADMINS:
        markup.add(
            InlineKeyboardButton(
                f"🗑 حذف {admin_id}",
                callback_data=f"del_numbers_admin_{admin_id}"
            )
        )
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin_manage_numbers_admins",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        "➖ <b>حذف أدمن أرقام</b>\n\n"
        "اختر الأدمن الذي تريد حذفه:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_numbers_admin_"))
def del_numbers_admin_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    admin_to_remove = int(call.data.replace("del_numbers_admin_", ""))
    
    if admin_to_remove in NUMBERS_ADMINS:
        NUMBERS_ADMINS.remove(admin_to_remove)
        save_numbers_admins()
        bot.answer_callback_query(call.id, f"✅ تم حذف {admin_to_remove} من أدمن الأرقام!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ الأدمن غير موجود!", show_alert=True)
    
    admin_manage_numbers_admins_callback(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_statistics")
def admin_statistics_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    stats_text = get_statistics_text()
    bot.send_message(call.message.chat.id, stats_text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_referral_settings")
def admin_referral_settings_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    settings = load_referral_settings()
    
    text = (
        "💰 <b>إعدادات نظام الإحالات والبونص</b>\n\n"
        f"🎁 بونص الكود: <b>${settings.get('code_bonus', 0.01)}</b>\n"
        f"👥 بونص الإحالة: <b>${settings.get('referral_bonus', 0.50)}</b>\n"
        f"📊 عدد الأكواد المطلوبة للإحالة النشطة: <b>{settings.get('codes_required_for_referral', 3)}</b>\n"
        f"💵 الحد الأدنى للسحب: <b>${settings.get('min_withdrawal', 5.0)}</b>\n\n"
        "اختر الإعداد الذي تريد تعديله:"
    )
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎁 بونص الكود", callback_data="edit_code_bonus"),
        InlineKeyboardButton("👥 بونص الإحالة", callback_data="edit_referral_bonus")
    )
    markup.add(
        InlineKeyboardButton("📊 أكواد الإحالة", callback_data="edit_codes_required"),
        InlineKeyboardButton("💵 حد السحب", callback_data="edit_min_withdrawal")
    )
    markup.add(
        InlineKeyboardButton("➕ إضافة رصيد لمستخدم", callback_data="admin_add_balance"),
        InlineKeyboardButton("➖ خصم رصيد من مستخدم", callback_data="admin_subtract_balance")
    )
    markup.add(
        InlineKeyboardButton("📋 طلبات السحب", callback_data="view_withdrawal_requests"),
        InlineKeyboardButton("⚙️ طرق السحب", callback_data="admin_withdrawal_methods")
    )
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "edit_code_bonus")
def edit_code_bonus_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    user_states[user_id] = {"action": "edit_code_bonus"}
    bot.send_message(
        call.message.chat.id,
        "🎁 <b>تعديل بونص الكود</b>\n\n"
        "أرسل القيمة الجديدة (مثال: 0.01 أو 0.02):",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "edit_referral_bonus")
def edit_referral_bonus_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    user_states[user_id] = {"action": "edit_referral_bonus"}
    bot.send_message(
        call.message.chat.id,
        "👥 <b>تعديل بونص الإحالة</b>\n\n"
        "أرسل القيمة الجديدة (مثال: 0.50 أو 1.00):",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "edit_codes_required")
def edit_codes_required_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    user_states[user_id] = {"action": "edit_codes_required"}
    bot.send_message(
        call.message.chat.id,
        "📊 <b>تعديل عدد الأكواد المطلوبة</b>\n\n"
        "أرسل العدد الجديد (مثال: 3 أو 5):",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "edit_min_withdrawal")
def edit_min_withdrawal_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    user_states[user_id] = {"action": "edit_min_withdrawal"}
    bot.send_message(
        call.message.chat.id,
        "💵 <b>تعديل الحد الأدنى للسحب</b>\n\n"
        "أرسل القيمة الجديدة (مثال: 5.00 أو 10.00):",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_balance")
def admin_add_balance_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    user_states[user_id] = {"action": "admin_add_balance"}
    bot.send_message(
        call.message.chat.id,
        "➕ <b>إضافة رصيد لمستخدم</b>\n\n"
        "أرسل معرف المستخدم والمبلغ بالصيغة التالية:\n"
        "<code>USER_ID AMOUNT</code>\n\n"
        "مثال: <code>123456789 5.00</code>",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_subtract_balance")
def admin_subtract_balance_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    user_states[user_id] = {"action": "admin_subtract_balance"}
    bot.send_message(
        call.message.chat.id,
        "➖ <b>خصم رصيد من مستخدم</b>\n\n"
        "أرسل معرف المستخدم والمبلغ بالصيغة التالية:\n"
        "<code>USER_ID AMOUNT</code>\n\n"
        "مثال: <code>123456789 5.00</code>",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "view_withdrawal_requests")
def view_withdrawal_requests_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    requests = load_withdrawal_requests()
    pending_requests = [r for r in requests if r.get("status") == "pending"]
    
    if not pending_requests:
        bot.answer_callback_query(call.id, "📭 لا توجد طلبات سحب معلقة!", show_alert=True)
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    for req in pending_requests[:10]:
        req_id = req.get("id", "")[:8]
        user_req_id = req.get("user_id")
        amount = req.get("amount", 0)
        markup.add(
            InlineKeyboardButton(
                f"👤 {user_req_id} | ${amount:.2f}",
                callback_data=f"view_wd_req_{req_id}"
            )
        )
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin_referral_settings",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        f"📋 <b>طلبات السحب المعلقة</b>\n\nعدد الطلبات: {len(pending_requests)}",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_wd_req_"))
def view_wd_request_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    req_id = call.data.replace("view_wd_req_", "")
    requests = load_withdrawal_requests()
    
    req = None
    for r in requests:
        if r.get("id", "").startswith(req_id):
            req = r
            break
    
    if not req:
        bot.answer_callback_query(call.id, "❌ الطلب غير موجود!", show_alert=True)
        return
    
    target_user_id = req.get('user_id')
    target_user_data = USERS.get(str(target_user_id), {})
    target_referral_data = get_user_referral_data(target_user_id)
    
    join_date = target_user_data.get("join_date", "غير محدد")
    total_codes = target_user_data.get("activations", 0)
    total_referrals = len(target_referral_data.get("referrals", []))
    active_referrals = target_referral_data.get("active_referrals", 0)
    total_earned = target_referral_data.get("total_earned", 0.0)
    current_balance = target_referral_data.get("balance", 0.0)
    
    text = (
        f"📋 <b>تفاصيل طلب السحب</b>\n\n"
        f"🆔 معرف الطلب: <code>{req.get('id', '')[:8]}</code>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 <b>بيانات المستخدم:</b>\n"
        f"├ 🆔 ID: <code>{target_user_id}</code>\n"
        f"├ 📅 تاريخ الانضمام: {join_date}\n"
        f"├ 📊 إجمالي الأكواد: {total_codes}\n"
        f"├ 👥 إجمالي الإحالات: {total_referrals}\n"
        f"├ ✅ إحالات نشطة: {active_referrals}\n"
        f"├ 💰 إجمالي الأرباح: ${total_earned:.2f}\n"
        f"└ 💵 الرصيد الحالي: ${current_balance:.2f}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💳 <b>تفاصيل السحب:</b>\n"
        f"├ 💵 المبلغ: <b>${req.get('amount', 0):.2f}</b>\n"
        f"├ 📝 الطريقة: {req.get('method', 'غير محدد')}\n"
        f"├ 📋 التفاصيل: <code>{req.get('details', 'غير محدد')}</code>\n"
        f"├ 📅 التاريخ: {req.get('date', 'غير محدد')}\n"
        f"└ 📊 الحالة: {req.get('status', 'pending')}"
    )
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ تأكيد الدفع", callback_data=f"approve_wd_{req_id}"),
        InlineKeyboardButton("❌ رفض", callback_data=f"reject_wd_{req_id}")
    )
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="view_withdrawal_requests",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_wd_") or call.data.startswith("wd_approve_"))
def approve_withdrawal_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    if call.data.startswith("wd_approve_"):
        req_id = call.data.replace("wd_approve_", "")
    else:
        req_id = call.data.replace("approve_wd_", "")
    
    requests = load_withdrawal_requests()
    
    for i, req in enumerate(requests):
        if req.get("id", "").startswith(req_id):
            requests[i]["status"] = "approved"
            save_withdrawal_requests(requests)
            
            target_user_id = req.get("user_id")
            user_lang = get_user_language(target_user_id)
            
            try:
                if user_lang == "ar":
                    bot.send_message(
                        target_user_id,
                        f"✅ <b>تم إرسال المبلغ بنجاح!</b>\n\n"
                        f"🆔 رقم الطلب: <code>{req.get('id', '')[:8]}</code>\n"
                        f"💵 المبلغ: <b>${req.get('amount', 0):.2f}</b>\n"
                        f"📝 الطريقة: {req.get('method', '')}\n"
                        f"📋 التفاصيل: <code>{req.get('details', '')}</code>\n\n"
                        f"💰 تم تحويل المبلغ إلى حسابك بنجاح.\n"
                        f"شكراً لاستخدامك البوت! 🎉",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        target_user_id,
                        f"✅ <b>Payment sent successfully!</b>\n\n"
                        f"🆔 Request ID: <code>{req.get('id', '')[:8]}</code>\n"
                        f"💵 Amount: <b>${req.get('amount', 0):.2f}</b>\n"
                        f"📝 Method: {req.get('method', '')}\n"
                        f"📋 Details: <code>{req.get('details', '')}</code>\n\n"
                        f"💰 The amount has been successfully transferred to your account.\n"
                        f"Thank you for using the bot! 🎉",
                        parse_mode="HTML"
                    )
            except:
                pass
            
            try:
                bot.edit_message_text(
                    f"✅ <b>تم تأكيد الدفع!</b>\n\n"
                    f"🆔 رقم الطلب: <code>{req.get('id', '')[:8]}</code>\n"
                    f"👤 المستخدم: <code>{target_user_id}</code>\n"
                    f"💵 المبلغ: <b>${req.get('amount', 0):.2f}</b>\n"
                    f"📝 الطريقة: {req.get('method', '')}\n"
                    f"📋 التفاصيل: <code>{req.get('details', '')}</code>\n\n"
                    f"✅ تم إشعار المستخدم بإرسال المبلغ",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML"
                )
            except:
                bot.answer_callback_query(call.id, "✅ تم تأكيد الدفع!", show_alert=True)
            break

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_wd_") or call.data.startswith("wd_reject_"))
def reject_withdrawal_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    if call.data.startswith("wd_reject_"):
        req_id = call.data.replace("wd_reject_", "")
    else:
        req_id = call.data.replace("reject_wd_", "")
    
    requests = load_withdrawal_requests()
    
    for i, req in enumerate(requests):
        if req.get("id", "").startswith(req_id):
            requests[i]["status"] = "rejected"
            
            global REFERRALS
            REFERRALS = load_referrals()
            target_user_id = req.get("user_id")
            user_key = str(target_user_id)
            if user_key in REFERRALS:
                REFERRALS[user_key]["balance"] += req.get("amount", 0)
                save_referrals(REFERRALS)
            
            save_withdrawal_requests(requests)
            
            user_lang = get_user_language(target_user_id)
            
            try:
                if user_lang == "ar":
                    bot.send_message(
                        target_user_id,
                        f"❌ <b>تم رفض طلب السحب</b>\n\n"
                        f"🆔 رقم الطلب: <code>{req.get('id', '')[:8]}</code>\n"
                        f"💵 المبلغ: <b>${req.get('amount', 0):.2f}</b>\n\n"
                        f"تم إرجاع المبلغ إلى رصيدك.",
                        parse_mode="HTML"
                    )
                else:
                    bot.send_message(
                        target_user_id,
                        f"❌ <b>Withdrawal request rejected</b>\n\n"
                        f"🆔 Request ID: <code>{req.get('id', '')[:8]}</code>\n"
                        f"💵 Amount: <b>${req.get('amount', 0):.2f}</b>\n\n"
                        f"The amount has been returned to your balance.",
                        parse_mode="HTML"
                    )
            except:
                pass
            
            try:
                bot.edit_message_text(
                    f"❌ <b>تم رفض الطلب!</b>\n\n"
                    f"🆔 رقم الطلب: <code>{req.get('id', '')[:8]}</code>\n"
                    f"👤 المستخدم: <code>{target_user_id}</code>\n"
                    f"💵 المبلغ: <b>${req.get('amount', 0):.2f}</b>\n"
                    f"تم إرجاع المبلغ للمستخدم.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML"
                )
            except:
                bot.answer_callback_query(call.id, "❌ تم رفض الطلب وإرجاع المبلغ!", show_alert=True)
            break

@bot.callback_query_handler(func=lambda call: call.data == "admin_withdrawal_methods")
def admin_withdrawal_methods_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    methods = load_withdrawal_methods()
    
    text = "⚙️ <b>إدارة طرق السحب</b>\n\n"
    text += "اضغط على طريقة السحب لتفعيلها أو تعطيلها:\n\n"
    
    method_icons = {"vodafone": "💳", "usdt_trc20": "📱", "usdt_bep20": "🔗", "binance_id": "🅱️"}
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for method_key, method_data in methods.items():
        enabled = method_data.get("enabled", True)
        name = method_data.get("name_ar", method_key)
        icon = method_icons.get(method_key, "💰")
        status = "✅" if enabled else "❌"
        markup.add(InlineKeyboardButton(f"{status} {icon} {name}", callback_data=f"toggle_wd_method_{method_key}"))
    
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin_referral_settings",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_wd_method_"))
def toggle_withdrawal_method_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    method_key = call.data.replace("toggle_wd_method_", "")
    methods = load_withdrawal_methods()
    
    if method_key in methods:
        methods[method_key]["enabled"] = not methods[method_key].get("enabled", True)
        save_withdrawal_methods(methods)
        
        status = "مفعّل ✅" if methods[method_key]["enabled"] else "معطّل ❌"
        bot.answer_callback_query(call.id, f"تم تغيير الحالة إلى: {status}", show_alert=True)
    
    admin_withdrawal_methods_callback(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_welcome_messages")
def admin_welcome_messages_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    # الرسالة الحالية هي النص الذي يظهر فوق الدول/الخدمات
    bot_settings = load_bot_settings()
    current_welcome = bot_settings.get("custom_welcome_msg", 
        get_welcome_text())
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("✏️ تعديل الرسالة", callback_data="edit_main_welcome_msg"))
    try:
        markup.add(make_back_button("رجوع للوحة", "admin"))
    except:
        markup.add(InlineKeyboardButton("◀ رجوع", callback_data="admin"))
    
    try:
        bot.edit_message_text(
            f"📝 <b>رسالة الترحيب (فوق الخدمات)</b>\n\n"
            f"<b>الرسالة الحالية:</b>\n{current_welcome[:300]}",
            call.message.chat.id, call.message.message_id,
            parse_mode="HTML", reply_markup=markup
        )
    except:
        bot.send_message(call.message.chat.id,
            f"📝 <b>رسالة الترحيب (فوق الخدمات)</b>\n\n"
            f"<b>الرسالة الحالية:</b>\n{current_welcome[:300]}",
            parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "edit_main_welcome_msg")
def edit_main_welcome_msg_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="admin"))
    bot.send_message(call.message.chat.id,
        "📝 أرسل الرسالة الجديدة (تدعم tg-emoji وHTML):",
        parse_mode="HTML", reply_markup=markup)
    user_states[user_id] = {"action": "edit_main_welcome"}

@bot.callback_query_handler(func=lambda call: call.data == "edit_welcome_ar")
def edit_welcome_ar_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    user_states[user_id] = {"action": "edit_welcome_ar"}
    messages = load_welcome_messages()
    
    bot.send_message(
        call.message.chat.id,
        f"<tg-emoji emoji-id='5294163983983463099'>🇸🇦</tg-emoji> <b>تعديل رسالة الترحيب العربية</b>\n\n"
        f"الرسالة الحالية:\n<code>{messages.get('ar', '')}</code>\n\n"
        f"أرسل الرسالة الجديدة (يمكنك استخدام HTML):",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "edit_welcome_en")
def edit_welcome_en_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    user_states[user_id] = {"action": "edit_welcome_en"}
    messages = load_welcome_messages()
    
    bot.send_message(
        call.message.chat.id,
        f"<tg-emoji emoji-id='5293993521026453119'>🇬🇧</tg-emoji> <b>Edit English Welcome Message</b>\n\n"
        f"Current message:\n<code>{messages.get('en', '')}</code>\n\n"
        f"Send the new message (HTML supported):",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_button_links")
def admin_button_links_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    links = load_button_links()
    
    text = (
        "🔗 <b>إعدادات روابط الأزرار</b>\n"
        "🔗 <b>Button Links Settings</b>\n\n"
        f"📢 <b>رابط الجروب / Group Link:</b>\n<code>{links.get('group_link', 'Not set')}</code>\n\n"
        f"📺 <b>رابط القناة / Channel Link:</b>\n<code>{links.get('channel_link', 'Not set')}</code>\n\n"
        f"👨‍💻 <b>رابط المطور / Developer Link:</b>\n<code>{links.get('developer_link', 'Not set')}</code>\n\n"
        "اختر الرابط لتعديله:\nChoose a link to edit:"
    )
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📢 تعديل رابط الجروب / Edit Group Link", callback_data="edit_link_group"),
        InlineKeyboardButton("📺 تعديل رابط القناة / Edit Channel Link", callback_data="edit_link_channel"),
        InlineKeyboardButton("👨‍💻 تعديل رابط المطور / Edit Developer Link", callback_data="edit_link_developer")
    )
    markup.add(InlineKeyboardButton(
        "رجوع / Back",
        callback_data="admin",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_link_"))
def edit_link_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    link_type = call.data.replace("edit_link_", "")
    link_names = {
        "group": ("رابط الجروب", "Group Link", "group_link"),
        "channel": ("رابط القناة", "Channel Link", "channel_link"),
        "developer": ("رابط المطور", "Developer Link", "developer_link")
    }
    
    ar_name, en_name, key = link_names.get(link_type, ("Link", "Link", "group_link"))
    links = load_button_links()
    current = links.get(key, "")
    
    user_states[user_id] = {"action": f"edit_button_link_{key}"}
    
    bot.send_message(
        call.message.chat.id,
        f"🔗 <b>تعديل {ar_name}</b>\n"
        f"🔗 <b>Edit {en_name}</b>\n\n"
        f"الرابط الحالي / Current link:\n<code>{current}</code>\n\n"
        f"أرسل الرابط الجديد / Send the new link:",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_create_backup")
def admin_create_backup_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    bot.answer_callback_query(call.id, "جاري إنشاء النسخة الاحتياطية... ⏳")
    try:
        backup_file = backup_manager.create_backup()
        with open(backup_file, 'rb') as f:
            bot.send_document(call.message.chat.id, f, caption=f"✅ تم إنشاء النسخة الاحتياطية بنجاح!\n📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        os.remove(backup_file)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ حدث خطأ أثناء إنشاء النسخة الاحتياطية: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_restore_backup")
def admin_restore_backup_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    msg = bot.send_message(call.message.chat.id, "📤 من فضلك أرسل ملف النسخة الاحتياطية (zip).")
    bot.register_next_step_handler(msg, process_restore_backup)

def process_restore_backup(message):
    if not is_admin(message.from_user.id): return
    if not message.document or not message.document.file_name.endswith('.zip'):
        bot.reply_to(message, "❌ عذراً، يجب إرسال ملف بصيغة zip فقط.")
        return
    
    bot.reply_to(message, "جاري استعادة النسخة الاحتياطية... ⏳")
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open("restore_temp.zip", 'wb') as f:
            f.write(downloaded_file)
            
        if backup_manager.restore_backup("restore_temp.zip"):
            bot.reply_to(message, "✅ تم استعادة النسخة الاحتياطية بنجاح! سيتم إعادة تحميل البيانات الآن.")
            load_data() 
        else:
            bot.reply_to(message, "❌ فشل استعادة النسخة الاحتياطية.")
        
        if os.path.exists("restore_temp.zip"):
            os.remove("restore_temp.zip")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء الاستعادة: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_otp_buttons")
def admin_otp_buttons_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    global OTP_BUTTONS
    OTP_BUTTONS = load_otp_buttons()
    
    text = "🔘 <b>إعدادات أزرار رسالة OTP</b>\n\n"
    if OTP_BUTTONS:
        for i, btn in enumerate(OTP_BUTTONS, 1):
            text += f"{i}. <b>{btn['name']}</b>\n   🔗 <code>{btn['url']}</code>\n\n"
    else:
        text += "لا توجد أزرار مضافة\n\n"
    
    text += "اختر الإجراء المطلوب:"
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("➕ إضافة زر جديد", callback_data="otp_btn_add"),
        InlineKeyboardButton("✏️ تعديل زر", callback_data="otp_btn_edit_list"),
        InlineKeyboardButton("🗑 حذف زر", callback_data="otp_btn_delete_list")
    )
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "otp_btn_add")
def otp_btn_add_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    user_states[user_id] = {"action": "otp_btn_add_name"}
    
    bot.send_message(
        call.message.chat.id,
        "➕ <b>إضافة زر جديد</b>\n\n"
        "أرسل اسم الزر:\n"
        "(مثال: 𝕮𝖍𝖆𝖓𝖓𝖊𝖑 أو Channel)",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "otp_btn_edit_list")
def otp_btn_edit_list_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    global OTP_BUTTONS
    OTP_BUTTONS = load_otp_buttons()
    
    if not OTP_BUTTONS:
        bot.answer_callback_query(call.id, "❌ لا توجد أزرار للتعديل!", show_alert=True)
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    for i, btn in enumerate(OTP_BUTTONS):
        markup.add(InlineKeyboardButton(f"✏️ {btn['name']}", callback_data=f"otp_btn_edit_{i}"))
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin_otp_buttons",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        "✏️ <b>اختر الزر للتعديل:</b>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("otp_btn_edit_") and not call.data.startswith("otp_btn_edit_name_") and not call.data.startswith("otp_btn_edit_url_") and not call.data.startswith("otp_btn_edit_list"))
def otp_btn_edit_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    btn_idx = int(call.data.replace("otp_btn_edit_", ""))
    global OTP_BUTTONS
    OTP_BUTTONS = load_otp_buttons()
    
    if btn_idx >= len(OTP_BUTTONS):
        bot.answer_callback_query(call.id, "❌ الزر غير موجود!", show_alert=True)
        return
    
    btn = OTP_BUTTONS[btn_idx]
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("✏️ تغيير الاسم", callback_data=f"otp_btn_edit_name_{btn_idx}"),
        InlineKeyboardButton("🔗 تغيير الرابط", callback_data=f"otp_btn_edit_url_{btn_idx}")
    )
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="otp_btn_edit_list",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        f"✏️ <b>تعديل الزر:</b>\n\n"
        f"📝 <b>الاسم:</b> {btn['name']}\n"
        f"🔗 <b>الرابط:</b> <code>{btn['url']}</code>\n\n"
        f"اختر ما تريد تعديله:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("otp_btn_edit_name_"))
def otp_btn_edit_name_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    btn_idx = int(call.data.replace("otp_btn_edit_name_", ""))
    user_states[user_id] = {"action": "otp_btn_edit_name", "btn_idx": btn_idx}
    
    bot.send_message(
        call.message.chat.id,
        "✏️ أرسل الاسم الجديد للزر:",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("otp_btn_edit_url_"))
def otp_btn_edit_url_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    btn_idx = int(call.data.replace("otp_btn_edit_url_", ""))
    user_states[user_id] = {"action": "otp_btn_edit_url", "btn_idx": btn_idx}
    
    bot.send_message(
        call.message.chat.id,
        "🔗 أرسل الرابط الجديد للزر:",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "otp_btn_delete_list")
def otp_btn_delete_list_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    global OTP_BUTTONS
    OTP_BUTTONS = load_otp_buttons()
    
    if not OTP_BUTTONS:
        bot.answer_callback_query(call.id, "❌ لا توجد أزرار للحذف!", show_alert=True)
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    for i, btn in enumerate(OTP_BUTTONS):
        markup.add(InlineKeyboardButton(f"🗑 {btn['name']}", callback_data=f"otp_btn_delete_{i}"))
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin_otp_buttons",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        "🗑 <b>اختر الزر للحذف:</b>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("otp_btn_delete_") and not call.data.startswith("otp_btn_delete_list"))
def otp_btn_delete_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    btn_idx = int(call.data.replace("otp_btn_delete_", ""))
    global OTP_BUTTONS
    OTP_BUTTONS = load_otp_buttons()
    
    if btn_idx >= len(OTP_BUTTONS):
        bot.answer_callback_query(call.id, "❌ الزر غير موجود!", show_alert=True)
        return
    
    deleted_btn = OTP_BUTTONS.pop(btn_idx)
    save_otp_buttons(OTP_BUTTONS)
    
    bot.answer_callback_query(call.id, f"✅ تم حذف الزر: {deleted_btn['name']}", show_alert=True)
    
    text = "🔘 <b>إعدادات أزرار رسالة OTP</b>\n\n"
    if OTP_BUTTONS:
        for i, btn in enumerate(OTP_BUTTONS, 1):
            text += f"{i}. <b>{btn['name']}</b>\n   🔗 <code>{btn['url']}</code>\n\n"
    else:
        text += "لا توجد أزرار مضافة\n\n"
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("➕ إضافة زر جديد", callback_data="otp_btn_add"),
        InlineKeyboardButton("✏️ تعديل زر", callback_data="otp_btn_edit_list"),
        InlineKeyboardButton("🗑 حذف زر", callback_data="otp_btn_delete_list")
    )
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "withdraw_balance")
def withdraw_balance_callback(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    
    referral_data = get_user_referral_data(user_id)
    balance = referral_data.get("balance", 0.0)
    settings = load_referral_settings()
    min_withdrawal = settings.get("min_withdrawal", 5.0)
    
    if balance < min_withdrawal:
        msg = f"❌ رصيدك ({balance:.2f}$) أقل من الحد الأدنى للسحب ({min_withdrawal}$)" if lang == "ar" else f"❌ Your balance (${balance:.2f}) is below minimum withdrawal (${min_withdrawal})"
        bot.answer_callback_query(call.id, msg, show_alert=True)
        return
    
    user_states[user_id] = {"action": "withdraw_method"}
    
    methods = load_withdrawal_methods()
    markup = InlineKeyboardMarkup(row_width=2)
    
    method_icons = {"vodafone": "💳", "usdt_trc20": "📱", "usdt_bep20": "🔗", "binance_id": "🅱️"}
    
    for method_key, method_data in methods.items():
        if method_data.get("enabled", True):
            name = method_data.get(f"name_{lang}", method_data.get("name_en", method_key))
            icon = method_icons.get(method_key, "💰")
            markup.add(InlineKeyboardButton(f"{icon} {name}", callback_data=f"wd_method_{method_key}"))
    
    back_text = "رجوع" if lang == "ar" else "Back"
    markup.add(InlineKeyboardButton(f" {back_text}", callback_data="my_account", icon_custom_emoji_id="5321334093126842469"))
    
    if lang == "ar":
        text = f"💰 <b>سحب الرصيد</b>\n\n💵 رصيدك الحالي: <b>${balance:.2f}</b>\n\nاختر طريقة السحب:"
    else:
        text = f"💰 <b>Withdraw Balance</b>\n\n💵 Your balance: <b>${balance:.2f}</b>\n\nChoose withdrawal method:"
    
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("wd_method_"))
def withdraw_method_callback(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    method_key = call.data.replace("wd_method_", "")
    
    methods = load_withdrawal_methods()
    method_data = methods.get(method_key, {})
    
    if not method_data.get("enabled", True):
        msg = "❌ طريقة السحب هذه غير متاحة حالياً" if lang == "ar" else "❌ This withdrawal method is not available"
        bot.answer_callback_query(call.id, msg, show_alert=True)
        return
    
    method_name = method_data.get(f"name_{lang}", method_data.get("name_en", method_key))
    details_prompt = method_data.get(f"details_{lang}", method_data.get("details_en", "Account details"))
    
    user_states[user_id] = {"action": "withdraw_details", "method": method_name, "method_key": method_key}
    
    if lang == "ar":
        text = f"📝 أرسل <b>{details_prompt}</b> الخاص بك لـ {method_name}:"
    else:
        text = f"📝 Send your <b>{details_prompt}</b> for {method_name}:"
    
    bot.send_message(call.message.chat.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_admins_menu")
def admin_admins_menu_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔧 إضافة مشرف", callback_data="admin_add_admin"),
        InlineKeyboardButton("🗑 حذف مشرف", callback_data="admin_remove_admin")
    )
    markup.add(
        InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban_user"),
        InlineKeyboardButton("✅ إلغاء حظر", callback_data="admin_unban_user")
    )
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin_panel",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        "👥 <b>إدارة المشرفين والمستخدمين</b>\n\nاختر الإجراء المطلوب:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_channels_menu")
def admin_channels_menu_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ إضافة قناة", callback_data="admin_add_channel"),
        InlineKeyboardButton("🗑 حذف قناة", callback_data="admin_remove_channel")
    )
    markup.add(
        InlineKeyboardButton("📊 القنوات المضافة", callback_data="admin_list_channels")
    )
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin_panel",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        "📢 <b>إدارة القنوات</b>\n\nاختر الإجراء المطلوب:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_countries_menu")
def admin_countries_menu_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ إضافة دولة", callback_data="admin_add_country"),
        InlineKeyboardButton("➖ حذف دولة", callback_data="admin_remove_country")
    )
    markup.add(
        InlineKeyboardButton("📋 الدول المتاحة", callback_data="admin_list_countries")
    )
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin_panel",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        "🌍 <b>إدارة الدول</b>\n\nاختر الإجراء المطلوب:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_groups_menu")
def admin_groups_menu_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ إضافة جروب", callback_data="admin_add_group_start"),
        InlineKeyboardButton("➖ حذف جروب", callback_data="admin_remove_group")
    )
    markup.add(
        InlineKeyboardButton("📋 عرض الجروبات", callback_data="admin_list_groups")
    )
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin_panel",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        "📱 <b>إدارة الجروبات</b>\n\nاختر الإجراء المطلوب:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_group_start")
def admin_add_group_start_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    from telebot.types import ReplyKeyboardMarkup, KeyboardButton
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("🔘 اختر جروب", request_chat=telebot.types.KeyboardButtonRequestChat(request_id=1, chat_is_channel=False)))
    
    bot.send_message(
        call.message.chat.id,
        "➕ <b>إضافة جروب جديد</b>\n\n"
        "إضغط على الزر بالأسفل لاختيار الجروب أو أرسل ID الجروب مباشرة:",
        parse_mode="HTML",
        reply_markup=markup
    )
    user_states[user_id] = {"action": "add_group"}

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "add_group", content_types=['text', 'chat_shared'])
def handle_add_group_message(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return

    group_id = None
    if message.content_type == 'chat_shared':
        group_id = message.chat_shared.chat_id
    else:
        text = message.text.strip()
        if text.startswith('-') and text[1:].isdigit() or text.isdigit():
            group_id = int(text)
    
    if group_id:
        if group_id not in GROUPS:
            GROUPS.append(group_id)
            save_groups()
            bot.send_message(message.chat.id, f"✅ تم إضافة الجروب بنجاح!\nID: <code>{group_id}</code>", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
        else:
            bot.send_message(message.chat.id, "⚠️ هذا الجروب مضاف بالفعل.", reply_markup=ReplyKeyboardRemove())
        user_states[user_id] = {}
    else:
        bot.send_message(message.chat.id, "❌ ID غير صالح. يرجى إرسال ID صحيح أو اختيار جروب من الزر.")

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_group")
def admin_add_group_callback(call):
   
    admin_add_group_start_callback(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_remove_group")
def admin_remove_group_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    if not GROUPS:
        bot.answer_callback_query(call.id, "⚠️ لا توجد جروبات مضافة", show_alert=True)
        return
    
    groups_list = "\n".join([f"• <code>{gid}</code>" for gid in GROUPS])
    
    user_states[user_id] = {"action": "remove_group"}
    
    bot.send_message(
        call.message.chat.id,
        f"🗑 <b>حذف جروب</b>\n\n"
        f"<b>الجروبات المضافة:</b>\n{groups_list}\n\n"
        f"أرسل ID الجروب الذي تريد حذفه:",
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("action") == "remove_group")
def handle_remove_group_message(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return

    try:
        group_id = int(message.text.strip())
        if group_id in GROUPS:
            GROUPS.remove(group_id)
            save_groups()
            bot.send_message(message.chat.id, f"✅ تم حذف الجروب <code>{group_id}</code> بنجاح!", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ هذا الجروب غير موجود في القائمة.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ يرجى إرسال ID صحيح (رقم).")
    
    user_states[user_id] = {}

@bot.callback_query_handler(func=lambda call: call.data == "admin_list_groups")
def admin_list_groups_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    if not GROUPS:
        bot.answer_callback_query(call.id, "⚠️ لا توجد جروبات مضافة", show_alert=True)
        return
    
    groups_text = "📋 <b>الجروبات المضافة:</b>\n\n"
    for idx, gid in enumerate(GROUPS, 1):
        try:
            chat = bot.get_chat(gid)
            groups_text += f"{idx}. <b>{chat.title}</b>\n"
            groups_text += f"   🆔 <code>{gid}</code>\n\n"
        except:
            groups_text += f"{idx}. جروب غير معروف\n"
            groups_text += f"   🆔 <code>{gid}</code>\n\n"
    
    bot.send_message(call.message.chat.id, groups_text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_menu")
def admin_broadcast_menu_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📣 إذاعة", callback_data="admin_broadcast_normal"),
        InlineKeyboardButton("📤 إذاعة توجيهية", callback_data="admin_broadcast_forward")
    )
    markup.add(InlineKeyboardButton(
        "رجوع",
        callback_data="admin_panel",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    bot.edit_message_text(
        "📣 <b>نظام الإذاعة</b>\n\n"
        "اختر نوع الإذاعة:\n\n"
        "• <b>إذاعة:</b> رسالة جديدة لكل مستخدم\n"
        "• <b>إذاعة توجيهية:</b> إعادة توجيه رسالتك",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_normal")
def admin_broadcast_normal_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    broadcast_state[user_id] = {"type": "normal", "step": "waiting_message"}
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(" إلغاء", callback_data="cancel_broadcast", icon_custom_emoji_id="5321334093126842469"))
    bot.send_message(call.message.chat.id, "📣 <b>إذاعة عادية</b>\n\nأرسل الرسالة التي تريد إذاعتها:", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_forward")
def admin_broadcast_forward_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    broadcast_state[user_id] = {"type": "forward", "step": "waiting_message"}
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(" إلغاء", callback_data="cancel_broadcast", icon_custom_emoji_id="5321334093126842469"))
    bot.send_message(call.message.chat.id, "📤 <b>إذاعة توجيهية</b>\n\nأرسل الرسالة التي تريد توجيهها:", parse_mode="HTML", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.from_user.id in broadcast_state and broadcast_state[msg.from_user.id].get("step") == "waiting_message", content_types=["text", "photo", "video", "document"])
def handle_broadcast_message(msg):
    user_id = msg.from_user.id
    state = broadcast_state[user_id]
    state["step"] = "confirm"
    state["message"] = msg
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ تأكيد الإرسال", callback_data="confirm_broadcast"), InlineKeyboardButton("❌ إلغاء", callback_data="cancel_broadcast"))
    bot.reply_to(msg, "❓ <b>هل أنت متأكد من إرسال هذه الرسالة للجميع؟</b>", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_broadcast")
def cancel_broadcast_callback(call):
    user_id = call.from_user.id
    if user_id in broadcast_state:
        del broadcast_state[user_id]
    bot.answer_callback_query(call.id, "✅ تم الإلغاء")
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "confirm_broadcast")
def confirm_broadcast_callback(call):
    user_id = call.from_user.id
    if user_id not in broadcast_state: return
    state = broadcast_state[user_id]
    msg = state["message"]
    success, failed = 0, 0
    progress = bot.send_message(call.message.chat.id, "⏳ جاري الإرسال...")
    for uid in list(USERS.keys()):
        try:
            if state["type"] == "forward":
                bot.forward_message(int(uid), msg.chat.id, msg.message_id)
            else:
                bot.copy_message(int(uid), msg.chat.id, msg.message_id)
            success += 1
        except: failed += 1
    bot.delete_message(progress.chat.id, progress.message_id)
    bot.send_message(call.message.chat.id, f"✅ <b>تم الإرسال!</b>\n\n📊 نجح: {success}\n❌ فشل: {failed}", parse_mode="HTML")
    del broadcast_state[user_id]

def send_saved_message(target_bot, target_uid, saved_msg):
    
    content_type = saved_msg.get("content_type")
    
    if content_type == "text":
        target_bot.send_message(target_uid, saved_msg.get("text"), parse_mode="HTML" if saved_msg.get("has_entities") else None)
    elif content_type == "photo":
        target_bot.send_photo(target_uid, saved_msg.get("file_id"), caption=saved_msg.get("caption"))
    elif content_type == "video":
        target_bot.send_video(target_uid, saved_msg.get("file_id"), caption=saved_msg.get("caption"))
    elif content_type == "document":
        target_bot.send_document(target_uid, saved_msg.get("file_id"), caption=saved_msg.get("caption"))
    elif content_type == "audio":
        target_bot.send_audio(target_uid, saved_msg.get("file_id"), caption=saved_msg.get("caption"))
    elif content_type == "voice":
        target_bot.send_voice(target_uid, saved_msg.get("file_id"), caption=saved_msg.get("caption"))
    elif content_type == "sticker":
        target_bot.send_sticker(target_uid, saved_msg.get("file_id"))

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main_callback(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name or "User"
    lang = get_user_language(user_id)
    welcome_msg = get_mody_welcome_msg(first_name, lang)
    bot.answer_callback_query(call.id)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass
    bot.send_message(call.message.chat.id, welcome_msg, parse_mode="HTML", reply_markup=get_main_reply_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_country")
def admin_add_country_callback(call):
    user_id = call.from_user.id

    if not is_admin(user_id):
        return

    user_states[user_id] = {"action": "na_add_country_file"}

    bot.send_message(
        call.message.chat.id,
        "📝 <b>Add New Country - Step 1/3</b>\n\n"
        "📤 Send the numbers file (.txt)\n\n"
        "<i>The file will be cleaned automatically and numbers extracted from each line</i>",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_remove_country")
def admin_remove_country_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    if not COUNTRIES:
        bot.answer_callback_query(call.id, "❌ No countries added!", show_alert=True)
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    for cid in sorted(COUNTRIES.keys()):
        info = COUNTRIES[cid]
        cname = info.get("display_name", cid)
        flag = info.get("flag", "🌍")
        count = info.get("numbers_count", 0)
        plain_flag = extract_plain_emoji(flag)
        eid = extract_tg_emoji_id(flag)
        btn_text = f" {cname} ({count})" if eid else f"❌ {plain_flag} {cname} ({count})"
        try:
            kw = {"callback_data": f"delete_country_btn_{cid}"}
            if eid:
                kw["icon_custom_emoji_id"] = eid
                kw["style"] = "danger"
            markup.add(InlineKeyboardButton(btn_text, **kw))
        except:
            markup.add(InlineKeyboardButton(f"❌ {plain_flag} {cname} ({count})", callback_data=f"delete_country_btn_{cid}"))
    
    markup.add(InlineKeyboardButton(
        "Back",
        callback_data="admin_panel",
        icon_custom_emoji_id="5321334093126842469",
        style="primary"
    ))
    
    try:
        bot.edit_message_text(
            "🗑 <b>Delete Country</b>\n\nChoose the country to delete:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
    except:
        bot.send_message(
            call.message.chat.id,
            "🗑 <b>Delete Country</b>\n\nChoose the country to delete:",
            parse_mode="HTML",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_country_btn_"))
def delete_country_confirm_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    
    country_name = call.data.replace("delete_country_btn_", "")
    if country_name in COUNTRIES:
        
        file_path = COUNTRIES[country_name].get("file")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        del COUNTRIES[country_name]
        save_countries()
        bot.answer_callback_query(call.id, f"✅ تم حذف {country_name} بنجاح!", show_alert=True)
        
        admin_remove_country_callback(call)
    else:
        bot.answer_callback_query(call.id, "❌ هذه الدولة غير موجودة!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_list_countries")
def admin_list_countries_callback(call):
    user_id = call.from_user.id

    if not is_admin(user_id):
        return

    if not COUNTRIES:
        bot.answer_callback_query(call.id, "⚠️ لا توجد دول مضافة حالياً", show_alert=True)
        return

    countries_text = "📋 <b>الدول المتاحة:</b>\n\n"
    for cid, info in COUNTRIES.items():
        cname = info.get("display_name", cid)
        countries_text += f"🌍 <b>{cname}</b> {info.get('flag', '🌐')}\n"
        countries_text += f"   🆔 المعرف: <code>{cid}</code>\n"
        countries_text += f"   📊 الأرقام: {info.get('numbers_count', 0)}\n"
        countries_text += f"   ⚙️ الخدمة: {info.get('service', 'N/A')}\n"
        countries_text += f"   📄 الملف: {info.get('file', 'N/A')}\n"
        if info.get('server'):
            countries_text += f"   🖥️ السيرفر: {info.get('server')}\n"
        if info.get('platforms'):
            countries_text += f"   📱 المنصات: {', '.join(info.get('platforms', []))}\n"
        countries_text += "\n"

    bot.send_message(call.message.chat.id, countries_text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_country_srv_"))
def add_country_server_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    if user_id not in user_states or user_states[user_id].get("action") != "add_country_server":
        bot.answer_callback_query(call.id, "❌ انتهت الجلسة!", show_alert=True)
        return
    
    server = call.data.replace("add_country_srv_", "")
    state = user_states[user_id]
    
    user_states[user_id] = {
        "action": "add_country_platforms",
        "temp_file": state.get("temp_file"),
        "country_code": state.get("country_code"),
        "country_name": state.get("country_name"),
        "num_cleaned": state.get("num_cleaned"),
        "server": server,
        "selected_platforms": []
    }
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📘 Facebook", callback_data="add_country_plt_Facebook"),
        InlineKeyboardButton("💬 WhatsApp", callback_data="add_country_plt_WhatsApp")
    )
    markup.add(
        InlineKeyboardButton("✈️ Telegram", callback_data="add_country_plt_Telegram"),
        InlineKeyboardButton("📸 Instagram", callback_data="add_country_plt_Instagram")
    )
    markup.add(
        InlineKeyboardButton("🐦 Twitter/X", callback_data="add_country_plt_Twitter"),
        InlineKeyboardButton("📱 TikTok", callback_data="add_country_plt_TikTok")
    )
    markup.add(
        InlineKeyboardButton("🎮 Discord", callback_data="add_country_plt_Discord"),
        InlineKeyboardButton("📧 Gmail", callback_data="add_country_plt_Gmail")
    )
    markup.add(
        InlineKeyboardButton("🌐 جميع المنصات", callback_data="add_country_plt_ALL")
    )
    markup.add(InlineKeyboardButton("✅ تأكيد وإنهاء", callback_data="add_country_finish"))
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="admin_countries"))
    
    server_names = {
        "GROUP": "🏢 GROUP",
        "Fly sms": "🔷 Fly sms",
        "hadi": "🏢 hadi",
        "fire": "🔷 fire",
        "Seven1Tel": "📡 Seven1Tel",
        "Gaza SMS": "🕊 Gaza SMS",
        "Km sms": "📶 Km sms",
        "Number_Panel": "📱 Number Panel",
        "Bolt": "⚡ Bolt",
        "iVASMS": "🌐 iVASMS",
        "Grand SMS": "🟣 Grand SMS",
        "Purple SMS": "💜 Purple SMS"
    }
    
    bot.edit_message_text(
        f"✅ <b>الخطوة 5/5 - اختيار المنصات</b>\n\n"
        f"🌍 الدولة: <b>{state.get('country_name')}</b>\n"
        f"🔢 رمز الدولة: <b>{state.get('country_code')}</b>\n"
        f"🖥️ السيرفر: <b>{server_names.get(server, server)}</b>\n\n"
        f"📱 <b>المنصات المختارة:</b> لا يوجد\n\n"
        f"اختر المنصات التي تعمل عليها هذه الأرقام:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_country_plt_"))
def add_country_platform_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    if user_id not in user_states or user_states[user_id].get("action") != "add_country_platforms":
        bot.answer_callback_query(call.id, "❌ انتهت الجلسة!", show_alert=True)
        return
    
    platform = call.data.replace("add_country_plt_", "")
    state = user_states[user_id]
    selected_platforms = state.get("selected_platforms", [])
    
    if platform == "ALL":
        selected_platforms = ["Facebook", "WhatsApp", "Telegram", "Instagram", "Twitter", "TikTok", "Discord", "Gmail"]
    elif platform in selected_platforms:
        selected_platforms.remove(platform)
    else:
        selected_platforms.append(platform)
    
    user_states[user_id]["selected_platforms"] = selected_platforms
    
    platform_icons = {
        "Facebook": "📘", "WhatsApp": "💬", "Telegram": "✈️",
        "Instagram": "📸", "Twitter": "🐦", "TikTok": "📱",
        "Discord": "🎮", "Gmail": "📧"
    }
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    def get_btn_text(name, icon):
        check = "✅" if name in selected_platforms else ""
        return f"{check} {icon} {name}"
    
    markup.add(
        InlineKeyboardButton(get_btn_text("Facebook", "📘"), callback_data="add_country_plt_Facebook"),
        InlineKeyboardButton(get_btn_text("WhatsApp", "💬"), callback_data="add_country_plt_WhatsApp")
    )
    markup.add(
        InlineKeyboardButton(get_btn_text("Telegram", "✈️"), callback_data="add_country_plt_Telegram"),
        InlineKeyboardButton(get_btn_text("Instagram", "📸"), callback_data="add_country_plt_Instagram")
    )
    markup.add(
        InlineKeyboardButton(get_btn_text("Twitter", "🐦"), callback_data="add_country_plt_Twitter"),
        InlineKeyboardButton(get_btn_text("TikTok", "📱"), callback_data="add_country_plt_TikTok")
    )
    markup.add(
        InlineKeyboardButton(get_btn_text("Discord", "🎮"), callback_data="add_country_plt_Discord"),
        InlineKeyboardButton(get_btn_text("Gmail", "📧"), callback_data="add_country_plt_Gmail")
    )
    markup.add(
        InlineKeyboardButton("🌐 جميع المنصات", callback_data="add_country_plt_ALL")
    )
    markup.add(InlineKeyboardButton("✅ تأكيد وإنهاء", callback_data="add_country_finish"))
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="admin_countries"))
    
    server_names = {
        "GROUP": "🏢 GROUP",
        "Fly sms": "🔷 Fly sms",
        "hadi": "🏢 hadi",
        "fire": "🔷 fire",
        "Seven1Tel": "📡 Seven1Tel",
        "Gaza SMS": "🕊 Gaza SMS",
        "Km sms": "📶 Km sms",
        "Number_Panel": "📱 Number Panel",
        "Bolt": "⚡ Bolt",
        "iVASMS": "🌐 iVASMS",
        "Grand SMS": "🟣 Grand SMS",
        "Purple SMS": "💜 Purple SMS"
    }

    platform_icons = {
        "Facebook": "📘", "WhatsApp": "💬", "Telegram": "✈️",
        "Instagram": "📸", "Twitter": "🐦", "TikTok": "📱",
        "Discord": "🎮", "Gmail": "📧"
    }
    
    platforms_text = ", ".join([f"{platform_icons.get(p, '📱')} {p}" for p in selected_platforms]) if selected_platforms else "لا يوجد"
    
    try:
        bot.edit_message_text(
            f"✅ <b>الخطوة 5/5 - اختيار المنصات</b>\n\n"
            f"🌍 الدولة: <b>{state.get('country_name')}</b>\n"
            f"🔢 رمز الدولة: <b>{state.get('country_code')}</b>\n"
            f"🖥️ السيرفر: <b>{server_names.get(state.get('server'), state.get('server'))}</b>\n\n"
            f"📱 <b>المنصات المختارة:</b> {platforms_text}\n\n"
            f"اختر المنصات التي تعمل عليها هذه الأرقام:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
    except:
        pass
    
    bot.answer_callback_query(call.id)

def format_otp_message(number, sms_text, service_name="[TG]", otp_code=None, user_id=None, is_group=False):
    country_name, flag, region_code = detect_country_from_number(number, user_id)
    masked = mask_number(number)

    otp_text = otp_code if otp_code and otp_code != "N/A" else "----"

    # استخراج تفاعل الخدمة
    raw_service = str(service_name).strip()
    if raw_service.startswith("[") and raw_service.endswith("]"):
        service_icon = raw_service[1:-1]
    else:
        service_icon = raw_service
    if not service_icon.startswith("<tg-emoji"):
        service_icon = "<tg-emoji emoji-id='5334998226636390258'>📱</tg-emoji>"

    if is_group:
        message = (
            f"↠ {flag} #{region_code} {service_icon} <b>{masked}</b> ┨"
            f"<tg-emoji emoji-id='5122933683820430249'>⭕️</tg-emoji>"
        )
    else:
        message = (
            f"↠ {flag} #{region_code} {service_icon} <code>{masked}</code> ┨\n"
            f"<blockquote><tg-emoji emoji-id='5330115548900501467'>🔑</tg-emoji> ~ OTP Code | <code>{otp_text}</code></blockquote>"
        )

    return message

@bot.callback_query_handler(func=lambda call: call.data == "add_country_finish")
def add_country_finish_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    if user_id not in user_states or user_states[user_id].get("action") != "add_country_platforms":
        bot.answer_callback_query(call.id, "❌ انتهت الجلسة!", show_alert=True)
        return
    
    state = user_states[user_id]
    temp_file = state.get("temp_file")
    server = state.get("server")
    selected_platforms = state.get("selected_platforms", ["WhatsApp"])
    
    bot.edit_message_text("🔍 جاري فحص الملف وتحديد الدولة تلقائياً...", call.message.chat.id, call.message.message_id)
    
    prefix = detect_country_code_from_file(temp_file)
    if not prefix:
        bot.send_message(call.message.chat.id, "❌ لم أتمكن من تحديد رمز الدولة من الملف.")
        return

    country_name, flag, region_code = detect_country_from_number(prefix)
    count, total, rejected = clean_and_filter_numbers(temp_file, prefix)
    
    if count == 0:
        bot.send_message(call.message.chat.id, f"❌ الملف لا يحتوي على أرقام تبدأ بـ +{prefix}")
        return

    final_country_name = country_name
    if region_code == "EG": final_country_name = "مصر"
    
    final_filename = f"numbers_{prefix}_{uuid.uuid4().hex[:8]}.txt"
    if os.path.exists(temp_file):
        os.rename(temp_file, final_filename)

    
    unique_id = uuid.uuid4().hex[:12]
    country_id = f"{final_country_name}_{unique_id}"
    
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_filename = f"numbers_{prefix}_{timestamp_str}_{unique_id}.txt"
    
    if os.path.exists(temp_file):
        
        while os.path.exists(final_filename):
            unique_id = uuid.uuid4().hex[:12]
            final_filename = f"numbers_{prefix}_{timestamp_str}_{unique_id}.txt"
            country_id = f"{final_country_name}_{unique_id}"
            
        os.rename(temp_file, final_filename)
        print(f"✅ تم حفظ الملف باسم فريد: {final_filename}")

    COUNTRIES[country_id] = {
        "display_name": final_country_name,
        "file": final_filename,
        "code": prefix,
        "flag": flag,
        "server": server,
        "platforms": selected_platforms,
        "numbers_count": state.get("admin_count", count),
        "added_by": user_id,
        "added_at": datetime.now().isoformat()
    }
    
   
    with open(COUNTRIES_FILE, "w", encoding="utf-8") as f:
        json.dump(COUNTRIES, f, indent=2, ensure_ascii=False)
    
    del user_states[user_id]
    bot.send_message(
        call.message.chat.id,
        f"✅ <b>تم إضافة الدولة بنجاح!</b>\n\n"
        f"🌍 الدولة: {flag} {final_country_name} (#{region_code})\n"
        f"🔢 الرمز: +{prefix}\n"
        f"📱 العدد: {count} رقم\n"
        f"🖥 السيرفر: {server}\n"
        f"✨ تم التحديد تلقائياً من محتوى الملف",
        parse_mode="HTML"
    )


@bot.callback_query_handler(func=lambda call: call.data == "admin_add_channel")
def admin_add_channel_callback(call):
    user_id = call.from_user.id

    if not is_admin(user_id):
        return

    user_states[user_id] = {"action": "add_channel"}

    bot.send_message(
        call.message.chat.id,
        "📢 <b>إضافة قناة اشتراك إجباري</b>\n\n"
        "أرسل رابط القناة أو معرفها:\n\n"
        "<b>أمثلة:</b>\n"
        "• <code>@mody_6_otp</code>\n"
        "• <code>https://t.me/mody</code>\n"
        "• <code>-1001234567890</code> (ID)\n\n"
        "<b>ملاحظة:</b> يجب أن يكون البوت مشرفاً في القناة!",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_remove_channel")
def admin_remove_channel_callback(call):
    user_id = call.from_user.id

    if not is_admin(user_id):
        return

    if not CHANNELS:
        bot.answer_callback_query(call.id, "⚠️ لا توجد قنوات مضافة حالياً", show_alert=True)
        return

    channels_list = "\n".join([f"{idx+1}. {ch['name']} ({ch['username']})" for idx, ch in enumerate(CHANNELS)])

    user_states[user_id] = {"action": "remove_channel"}

    bot.send_message(
        call.message.chat.id,
        f"🗑 <b>حذف قناة</b>\n\n"
        f"<b>القنوات المضافة:</b>\n{channels_list}\n\n"
        f"أرسل رقم القناة التي تريد حذفها:",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_list_channels")
def admin_list_channels_callback(call):
    user_id = call.from_user.id

    if not is_admin(user_id):
        return

    if not CHANNELS:
        bot.answer_callback_query(call.id, "⚠️ لا توجد قنوات مضافة حالياً", show_alert=True)
        return

    channels_text = "📊 <b>القنوات المضافة:</b>\n\n"
    for idx, ch in enumerate(CHANNELS, 1):
        channels_text += f"{idx}. 📢 <b>{ch['name']}</b>\n"
        channels_text += f"   🔗 {ch['username']}\n"
        channels_text += f"   🆔 ID: <code>{ch['id']}</code>\n\n"

    bot.send_message(call.message.chat.id, channels_text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_admin")
def admin_add_admin_callback(call):
    user_id = call.from_user.id
    if user_id != MAIN_ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ عذراً، المالك فقط يمكنه إضافة مشرفين!", show_alert=True)
        return
    user_states[user_id] = {"action": "add_admin"}
    bot.send_message(call.message.chat.id, "🔧 <b>إضافة مشرف جديد</b>\n\nأرسل معرف المستخدم (User ID) الذي تريد جعله مشرفاً:", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "admin_remove_admin")
def admin_remove_admin_callback(call):
    user_id = call.from_user.id
    if user_id != MAIN_ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ عذراً، المالك فقط يمكنه حذف مشرفين!", show_alert=True)
        return
    
    admins_list = ""
    for aid in ADMINS:
        status = " (المالك 👑)" if aid == MAIN_ADMIN_ID else ""
        admins_list += f"• <code>{aid}</code>{status}\n"
    
    user_states[user_id] = {"action": "remove_admin"}
    bot.send_message(
        call.message.chat.id, 
        f"🗑 <b>حذف مشرف</b>\n\n📋 <b>المشرفون الحاليون:</b>\n{admins_list}\n\nأرسل معرف المشرف الذي تريد حذفه:", 
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban_user")
def admin_ban_user_callback(call):
    user_id = call.from_user.id

    if not is_admin(user_id):
        return

    user_states[user_id] = {"action": "ban_user"}

    bot.send_message(
        call.message.chat.id,
        "🚫 <b>حظر مستخدم</b>\n\n"
        "أرسل ID المستخدم:",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_unban_user")
def admin_unban_user_callback(call):
    user_id = call.from_user.id

    if not is_admin(user_id):
        return

    if not BANNED:
        bot.answer_callback_query(call.id, "⚠️ لا يوجد مستخدمين محظورين!", show_alert=True)
        return

    banned_list = "\n".join([f"• <code>{uid}</code>" for uid in BANNED])

    user_states[user_id] = {"action": "unban_user"}

    bot.send_message(
        call.message.chat.id,
        f"✅ <b>إلغاء حظر مستخدم</b>\n\n"
        f"<b>المحظورين:</b>\n{banned_list}\n\n"
        f"أرسل ID المستخدم:",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_set_otp_group")
def admin_set_otp_group_callback(call):
    user_id = call.from_user.id

    if not is_admin(user_id):
        return

    user_states[user_id] = {"action": "set_otp_group"}

    bot.send_message(
        call.message.chat.id,
        "📬 <b>تعيين مجموعة OTP</b>\n\n"
        "أرسل ID المجموعة التي سيتم إرسال رسائل OTP إليها:",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_accounts_menu")
def admin_accounts_menu_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "⛔️ غير مصرح لك بالوصول", show_alert=True)
        return
    
    bot.edit_message_text(
        "👥 <b>إدارة الحسابات</b>\n\nاختر الموقع لإدارة حساباته:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=get_accounts_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("accounts_site_"))
def accounts_site_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    site_key = call.data.replace("accounts_site_", "")
    site_name = SETTINGS[site_key]["name"]
    accounts = get_site_accounts(site_key)
    
    accounts_text = f"👥 <b>حسابات {site_name}</b>\n\n"
    if accounts:
        accounts_text += f"📊 عدد الحسابات: {len(accounts)}\n\n"
        for idx, account in enumerate(accounts, 1):
            username = account.get("username", "N/A")
            accounts_text += f"{idx}. 👤 <code>{username}</code>\n"
    else:
        accounts_text += "⚠️ لا توجد حسابات مضافة\n"
    
    accounts_text += "\nاختر حساباً لعرض تفاصيله أو أضف حساباً جديداً:"
    
    bot.edit_message_text(
        accounts_text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=get_site_accounts_menu(site_key)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_account_"))
def view_account_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    data = call.data.replace("view_account_", "")
    parts = data.rsplit("_", 1)
    if len(parts) < 2:
        return
    
    site_key, account_id = parts[0], parts[1]
    account = get_account_by_id(site_key, account_id)
    
    if not account:
        bot.answer_callback_query(call.id, "❌ الحساب غير موجود", show_alert=True)
        return
    
    site_name = SETTINGS[site_key]["name"]
    full_id = account.get("id", "")
    
    account_text = (
        f"👤 <b>تفاصيل الحساب - {site_name}</b>\n\n"
        f"📛 <b>اليوزر:</b> <code>{account.get('username', 'N/A')}</code>\n"
        f"🔑 <b>الباسورد:</b> <code>{account.get('password', 'N/A')}</code>\n"
        f"🆔 <b>ID:</b> <code>{full_id[:8]}...</code>\n"
    )
    
    bot.edit_message_text(
        account_text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=get_account_details_menu(site_key, full_id)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_account_"))
def add_account_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    site_key = call.data.replace("add_account_", "")
    site_name = SETTINGS[site_key]["name"]
    
    user_states[user_id] = {"action": "add_account_username", "site_key": site_key}
    
    bot.send_message(
        call.message.chat.id,
        f"➕ <b>إضافة حساب جديد - {site_name}</b>\n\n"
        f"📝 الخطوة 1/2: أرسل اسم المستخدم (Username):",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_account_"))
def delete_account_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    data = call.data.replace("delete_account_", "")
    parts = data.rsplit("_", 1)
    if len(parts) < 2:
        return
    
    site_key, account_id = parts[0], parts[1]
    site_name = SETTINGS[site_key]["name"]
    account = get_account_by_id(site_key, account_id)
    
    if not account:
        bot.answer_callback_query(call.id, "❌ الحساب غير موجود", show_alert=True)
        return
    
    accounts = get_site_accounts(site_key)
    if len(accounts) <= 1:
        bot.answer_callback_query(
            call.id, 
            "⚠️ لا يمكن حذف الحساب الوحيد!\nيجب أن يبقى حساب واحد على الأقل لكل موقع.", 
            show_alert=True
        )
        return
    
    username = account.get("username", "N/A")
    full_id = account.get("id", "")
    success = delete_account(site_key, full_id)
    
    if success:
        bot.answer_callback_query(call.id, f"✅ تم حذف الحساب {username} بنجاح!", show_alert=True)
        
        accounts = get_site_accounts(site_key)
        accounts_text = f"👥 <b>حسابات {site_name}</b>\n\n"
        accounts_text += f"📊 عدد الحسابات: {len(accounts)}\n\n"
        for idx, acc in enumerate(accounts, 1):
            acc_username = acc.get("username", "N/A")
            accounts_text += f"{idx}. 👤 <code>{acc_username}</code>\n"
        accounts_text += "\nاختر حساباً لعرض تفاصيله أو أضف حساباً جديداً:"
        
        bot.edit_message_text(
            accounts_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_site_accounts_menu(site_key)
        )
    else:
        bot.answer_callback_query(call.id, "❌ فشل حذف الحساب", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_sites_menu" or call.data == "admin")
def sites_menu_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "⛔️ غير مصرح لك بالوصول", show_alert=True)
        return
    
    if call.data == "admin":
        bot.edit_message_text(
            "🎛 <b>لوحة الإدارة</b>\n\nاختر الإجراء المطلوب:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_admin_menu()
        )
    else:
        bot.edit_message_text(
            "⚙️ <b>إعدادات المواقع</b>\n\nاختر الموقع لتعديل إعداداته:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_sites_menu()
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("site_config_"))
def site_config_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    site_key = call.data.replace("site_config_", "")
    site_config = SETTINGS.get(site_key, {})
    site_name = site_config.get("name", site_key)
    accounts = get_site_accounts(site_key)
    
    if len(accounts) > 1:
        accounts_text = f"⚙️ <b>إعدادات {site_name}</b>\n\n"
        accounts_text += f"👥 <b>عدد الحسابات:</b> {len(accounts)}\n\n"
        accounts_text += "اختر الحساب الذي تريد التحكم فيه:"
        
        bot.edit_message_text(
            accounts_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_site_accounts_selection_menu(site_key)
        )
    else:
        first_account = accounts[0] if accounts else {"username": "N/A", "password": "", "id": ""}
        account_id = first_account.get("id", "")
        
        info_text = (
            f"⚙️ <b>إعدادات {site_name}</b>\n\n"
            f"👤 <b>الحساب:</b> <code>{first_account.get('username', 'N/A')}</code>\n"
            f"🔑 <b>الباسورد:</b> <code>{'*' * len(first_account.get('password', ''))}</code>\n"
            f"⏱ <b>فترة البحث:</b> {site_config.get('check_interval', 0)} ثانية\n"
            f"⏳ <b>وقت الانتظار:</b> {site_config.get('timeout', 0)} ثانية\n\n"
            f"اختر الإجراء المطلوب:"
        )
        
        bot.edit_message_text(
            info_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_site_config_menu(site_key, account_id)
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_account_config_"))
def select_account_config_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    data = call.data.replace("select_account_config_", "")
    parts = data.rsplit("_", 1)
    if len(parts) < 2:
        return
    
    site_key, account_id = parts[0], parts[1]
    site_config = SETTINGS.get(site_key, {})
    site_name = site_config.get("name", site_key)
    account = get_account_by_id(site_key, account_id)
    
    if not account:
        bot.answer_callback_query(call.id, "❌ الحساب غير موجود", show_alert=True)
        return
    
    info_text = (
        f"⚙️ <b>إعدادات {site_name}</b>\n\n"
        f"👤 <b>الحساب:</b> <code>{account.get('username', 'N/A')}</code>\n"
        f"🔑 <b>الباسورد:</b> <code>{'*' * len(account.get('password', ''))}</code>\n"
        f"⏱ <b>فترة البحث:</b> {site_config.get('check_interval', 0)} ثانية\n"
        f"⏳ <b>وقت الانتظار:</b> {site_config.get('timeout', 0)} ثانية\n\n"
        f"اختر الإجراء المطلوب:"
    )
    
    bot.edit_message_text(
        info_text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=get_site_config_menu(site_key, account_id)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("site_change_user_"))
def site_change_user_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    data_parts = call.data.replace("site_change_user_", "").rsplit("_", 1)
    site_key = data_parts[0]
    account_id = data_parts[1] if len(data_parts) > 1 else None
    
    # Handle TimeSMS special case for single account sites or direct access
    if not account_id and site_key == "TimeSMS":
        accounts = get_site_accounts(site_key)
        if accounts:
            account = accounts[0]
            account_id = account.get("id", "")[:8]
        else:
            bot.answer_callback_query(call.id, "❌ لا يوجد حساب مسجل", show_alert=True)
            return

    account = get_account_by_id(site_key, account_id) if account_id else None
    
    if not account:
        bot.answer_callback_query(call.id, "❌ الحساب غير موجود", show_alert=True)
        return
    
    full_id = account.get("id", "")
    
    user_states[user_id] = {
        "action": "change_site_username",
        "site_key": site_key,
        "account_id": full_id
    }
    
    bot.send_message(
        call.message.chat.id,
        f"👤 <b>تغيير اليوزر - {site_name}</b>\n\n"
        f"الحساب الحالي: <code>{account.get('username', 'N/A')}</code>\n\n"
        f"أرسل اسم المستخدم الجديد:",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("site_change_pass_"))
def site_change_pass_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    data_parts = call.data.replace("site_change_pass_", "").rsplit("_", 1)
    site_key = data_parts[0]
    account_id = data_parts[1] if len(data_parts) > 1 else None
    # Handle TimeSMS special case for single account sites or direct access
    if not account_id and site_key == "TimeSMS":
        accounts = get_site_accounts(site_key)
        if accounts:
            account = accounts[0]
            account_id = account.get("id", "")[:8]
        else:
            bot.answer_callback_query(call.id, "❌ لا يوجد حساب مسجل", show_alert=True)
            return

    account = get_account_by_id(site_key, account_id) if account_id else None
    
    if not account:
        bot.answer_callback_query(call.id, "❌ الحساب غير موجود", show_alert=True)
        return
    
    full_id = account.get("id", "")
    
    user_states[user_id] = {
        "action": "change_site_password",
        "site_key": site_key,
        "account_id": full_id
    }
    
    bot.send_message(
        call.message.chat.id,
        f"🔑 <b>تغيير الباسورد - {site_name}</b>\n\n"
        f"الحساب: <code>{account.get('username', 'N/A')}</code>\n\n"
        f"أرسل كلمة المرور الجديدة:",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("site_change_interval_"))
def site_change_interval_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    site_key = call.data.replace("site_change_interval_", "")
    site_name = SETTINGS[site_key]["name"]
    current = SETTINGS[site_key]["check_interval"]
    
    user_states[user_id] = {"action": "change_site_interval", "site_key": site_key}
    
    bot.send_message(
        call.message.chat.id,
        f"⏱ <b>تغيير فترة البحث - {site_name}</b>\n\n"
        f"📊 الفترة الحالية: {current} ثانية\n\n"
        f"أرسل الفترة الجديدة بالثواني:",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("site_change_timeout_"))
def site_change_timeout_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    site_key = call.data.replace("site_change_timeout_", "")
    site_name = SETTINGS[site_key]["name"]
    current = SETTINGS[site_key]["timeout"]
    
    user_states[user_id] = {"action": "change_site_timeout", "site_key": site_key}
    
    bot.send_message(
        call.message.chat.id,
        f"⏳ <b>تغيير وقت الانتظار - {site_name}</b>\n\n"
        f"📊 الوقت الحالي: {current} ثانية\n\n"
        f"أرسل الوقت الجديد بالثواني:",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("site_test_login_"))
def site_test_login_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    data_parts = call.data.replace("site_test_login_", "").rsplit("_", 1)
    site_key = data_parts[0]
    account_id = data_parts[1] if len(data_parts) > 1 else None
    # Handle TimeSMS special case for single account sites or direct access
    if not account_id and site_key == "TimeSMS":
        accounts = get_site_accounts(site_key)
        if accounts:
            account = accounts[0]
            account_id = account.get("id", "")[:8]
        else:
            bot.answer_callback_query(call.id, "❌ لا يوجد حساب مسجل", show_alert=True)
            return

    account = get_account_by_id(site_key, account_id) if account_id else None
    
    if not account:
        bot.answer_callback_query(call.id, "❌ الحساب غير موجود", show_alert=True)
        return
    
    bot.answer_callback_query(call.id, f"🔄 جاري اختبار تسجيل الدخول ل {account.get('username')}...")
    
    bot.send_message(
        call.message.chat.id,
        f"🔓 <b>اختبار تسجيل الدخول - {site_name}</b>\n\n"
        f"👤 الحساب: <code>{account.get('username')}</code>\n\n"
        f"⏳ جاري الاتصال والتحقق...",
        parse_mode="HTML"
    )
    
    Thread(target=test_site_login, args=(call.message.chat.id, site_key, account_id)).start()

@bot.callback_query_handler(func=lambda call: call.data.startswith("site_test_fetch_"))
def site_test_fetch_callback(call):
    user_id = call.from_user.id
    
    if not is_admin(user_id):
        return
    
    data_parts = call.data.replace("site_test_fetch_", "").rsplit("_", 1)
    site_key = data_parts[0]
    account_id = data_parts[1] if len(data_parts) > 1 else None
    # Handle TimeSMS special case for single account sites or direct access
    if not account_id and site_key == "TimeSMS":
        accounts = get_site_accounts(site_key)
        if accounts:
            account = accounts[0]
            account_id = account.get("id", "")[:8]
        else:
            bot.answer_callback_query(call.id, "❌ لا يوجد حساب مسجل", show_alert=True)
            return

    account = get_account_by_id(site_key, account_id) if account_id else None
    
    if not account:
        bot.answer_callback_query(call.id, "❌ الحساب غير موجود", show_alert=True)
        return
    
    bot.answer_callback_query(call.id, f"🔄 جاري جلب آخر كود من {account.get('username')}...")
    
    bot.send_message(
        call.message.chat.id,
        f"📥 <b>اختبار جلب الكود - {site_name}</b>\n\n"
        f"👤 الحساب: <code>{account.get('username')}</code>\n\n"
        f"⏳ جاري جلب آخر رسالة...",
        parse_mode="HTML"
    )
    
    Thread(target=test_site_fetch, args=(call.message.chat.id, site_key, account_id)).start()

@bot.callback_query_handler(func=lambda call: call.data.startswith("country_"))
def country_selection_callback(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    channels = check_subscription(user_id)
    if channels:
        bot.answer_callback_query(call.id, ml(user_id, "subscribe_first"), show_alert=True)
        return
    country_name = call.data.replace("country_", "")
    if country_name not in COUNTRIES:
        bot.answer_callback_query(call.id, ml(user_id, "country_not_found"), show_alert=True)
        return
    bot.answer_callback_query(call.id)
    _assign_number(call.message, user_id, country_name, lang)


@bot.callback_query_handler(func=lambda call: call.data == "change_number")
def change_number_callback(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)

    # Cooldown check: 9 seconds between changes
    import time as _time
    now = _time.time()
    last_change = change_number_cooldown.get(user_id, 0)
    remaining = int(9 - (now - last_change))
    if remaining > 0:
        bot.answer_callback_query(call.id, f"⏳ Please wait {remaining} seconds.", show_alert=True)
        return
    change_number_cooldown[user_id] = now

    channels = check_subscription(user_id)

    if channels:
        bot.answer_callback_query(call.id, ml(user_id, "subscribe_first"), show_alert=True)
        return

    user_data = USERS.get(str(user_id))
    if not user_data:
        bot.answer_callback_query(call.id, "❌ User data not found!", show_alert=True)
        return
        
    country_name = user_data.get("country") or user_data.get("selected_country")
    if not country_name:
        bot.answer_callback_query(call.id, ml(user_id, "no_country_selected"), show_alert=True)
        return
    number = get_random_number(country_name)

    if not number:
        bot.answer_callback_query(call.id, ml(user_id, "no_numbers"), show_alert=True)
        return

    country_info = COUNTRIES.get(country_name, {})
    service_type = country_info.get("service", "WS")
    flag = country_info.get("flag", "🌍")
    country_code = country_info.get("code", "")
    platform = user_data.get("platform", country_info.get("platforms", ["General"])[0] if country_info.get("platforms") else "General")

    display_number = f'+{number.lstrip("+")}'

    USERS[str(user_id)]["selected_number"] = number
    save_users()

    localized_country_name, _, _ = detect_country_from_number(country_code, user_id) if country_code else ("", "", "")
    if not localized_country_name:
        localized_country_name = country_info.get("display_name", country_name)

    flag_emoji_id = extract_tg_emoji_id(flag)
    links = load_button_links()

    # نص "Waiting for otp 🔥" زي الصورة الثالثة
    # جلب 4 أرقام جديدة
    country_name2 = user_data.get("country") or user_data.get("selected_country", "")
    new_display4 = []
    fname4 = COUNTRIES.get(country_name2, {}).get("file", "")
    if fname4 and os.path.exists(fname4):
        try:
            with open(fname4, "r", encoding="utf-8") as fh4:
                all4 = [l.strip() for l in fh4 if l.strip()]
            new_display4 = random.sample(all4, min(4, len(all4)))
        except: pass
    if not new_display4:
        new_display4 = [number]
    
    USERS[str(user_id)]["selected_number"] = new_display4[0]
    USERS[str(user_id)]["display_numbers"] = new_display4
    USERS[str(user_id)]["selected_numbers"] = new_display4
    USERS[str(user_id)]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_users()
    
    flag4 = COUNTRIES.get(country_name2, {}).get("flag", "🌍")
    feid4 = extract_tg_emoji_id(flag4)
    plain_flag4 = extract_plain_emoji(flag4)
    flag_display4 = f"<tg-emoji emoji-id='{feid4}'>{plain_flag4}</tg-emoji>" if feid4 else plain_flag4
    new_msg = f"{flag_display4} | <b>NEW NUMBERS</b> ⬇"

    new_mu = InlineKeyboardMarkup(row_width=1)

    # أزرار الأرقام القابلة للنسخ
    for n4 in new_display4:
        dn4 = f"+{n4.lstrip('+ ')}"
        try:
            new_mu.add(InlineKeyboardButton(
                f"📋 {dn4}",
                copy_text=CopyTextButton(text=dn4),
                icon_custom_emoji_id=feid4 if feid4 else "5406809207947142040"
            ))
        except:
            new_mu.add(InlineKeyboardButton(f"📋 {dn4}", callback_data=f"pick_num_{n4}"))

    # أزرار زي الصورة الأولى
    _cn_txt = "Change Number" if lang == "en" else "تغيير الرقم"
    _cc_txt = "Change Country" if lang == "en" else "تغيير الدولة"
    _grp_txt = "OTP Group" if lang == "en" else "جروب البوت"
    try:
        new_mu.row(
            InlineKeyboardButton(_cn_txt, callback_data="change_number", style="success"),
            InlineKeyboardButton("Send Prefix", callback_data=f"send_prefix_{user_id}", style="danger")
        )
    except:
        new_mu.add(InlineKeyboardButton(_cn_txt, callback_data="change_number"))
    try:
        new_mu.add(InlineKeyboardButton(_cc_txt, callback_data="choose_country", style="primary"))
    except:
        new_mu.add(InlineKeyboardButton(_cc_txt, callback_data="choose_country"))
    try:
        new_mu.add(InlineKeyboardButton(_grp_txt, url=links.get("group_link", "https://t.me/UltronX_MegaBo")))
    except:
        new_mu.add(InlineKeyboardButton(_grp_txt, url=links.get("group_link", "https://t.me/UltronX_MegaBo")))

    try:
        bot.edit_message_text(new_msg, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=new_mu)
    except:
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, new_msg, parse_mode="HTML", reply_markup=new_mu)
    bot.answer_callback_query(call.id, "✅ Numbers changed!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_plt_"))
def select_platform_main_callback(call):
    user_id = call.from_user.id
    platform = call.data.replace("select_plt_", "")
    lang = get_user_language(user_id)
    
    markup = get_countries_for_platform(platform, user_id)
    if not markup:
        bot.answer_callback_query(call.id, "❌ No countries available for this platform!", show_alert=True)
        return
    
    title = f"🟢 اختر الدولة لـ {platform}" if lang == "ar" else f"🟢 Choose Country for {platform}"
    bot.edit_message_text(title, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "choose_country")
def choose_country_callback(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    channels = check_subscription(user_id)
    if channels:
        bot.answer_callback_query(call.id, "❌ Subscribe first!", show_alert=True)
        return
    markup = get_country_buttons_all(user_id)
    txt = get_welcome_text(user_id)
    bot.answer_callback_query(call.id)
    if markup:
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except: bot.send_message(call.message.chat.id, txt, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, txt, parse_mode="HTML", reply_markup=get_main_reply_keyboard(user_id))


@bot.callback_query_handler(func=lambda call: call.data.startswith("platform_"))
def select_platform_callback(call):
    user_id = call.from_user.id

    bot.answer_callback_query(call.id)

    channels = check_subscription(user_id)

    if channels:
        bot.answer_callback_query(call.id, ml(user_id, "subscribe_first"), show_alert=True)
        return

    parts = call.data.split("_", 2)
    if len(parts) < 3:
        bot.answer_callback_query(call.id, "❌ Invalid selection!", show_alert=True)
        return
    
    country_name = parts[1]
    platform = parts[2]
    
    if country_name not in COUNTRIES:
        bot.answer_callback_query(call.id, ml(user_id, "country_not_found"), show_alert=True)
        return
    
    country_info = COUNTRIES[country_name]
    selected_number = get_random_number(country_name)
    
    if not selected_number:
        bot.answer_callback_query(call.id, ml(user_id, "no_numbers"), show_alert=True)
        return
    
    USERS[str(user_id)] = {
        "selected_number": selected_number,
        "selected_country": country_name,
        "country": country_name,
        "platform": platform,
        "joined": str(datetime.now()),
        "activations": USERS.get(str(user_id), {}).get("activations", 0),
        "language": USERS.get(str(user_id), {}).get("language", "ar")
    }
    save_users()
    
    country_flag = country_info.get("flag", "🌍")
    display_number = f'+{selected_number.lstrip("+")}'
    user_lang = get_user_language(user_id)
    localized_country_name, _, _ = detect_country_from_number(country_info.get("code", ""), user_id)
    
    if user_lang == "ar":
        msg_text = (
            f"<tg-emoji emoji-id='5972010570340112281'>😀</tg-emoji> <b>تم اختيار الرقم بنجاح!</b>\n\n"
            f"<tg-emoji emoji-id='5224450179368767019'>🌎</tg-emoji> <b>الدولة:</b> {country_flag} {localized_country_name}\n"
            f"<tg-emoji emoji-id='5782668844061430712'>🗣</tg-emoji> <b>المنصة:</b> {platform}\n"
            f"<tg-emoji emoji-id='5453965363286925977'>📞</tg-emoji> <b>الرقم:</b> <code>{display_number}</code>\n\n"
            f"<tg-emoji emoji-id='5458603043203327669'>😀</tg-emoji> <b>ستستلم الرسائل تلقائياً عند وصولها</b>"
        )
    else:
        msg_text = (
            f"<tg-emoji emoji-id='5972010570340112281'>😀</tg-emoji> <b>Number selected successfully!</b>\n\n"
            f"<tg-emoji emoji-id='5224450179368767019'>🌎</tg-emoji> <b>Country:</b> {country_flag} {localized_country_name}\n"
            f"<tg-emoji emoji-id='5782668844061430712'>🗣</tg-emoji> <b>Platform:</b> {platform}\n"
            f"<tg-emoji emoji-id='5453965363286925977'>📞</tg-emoji> <b>Number:</b> <code>{display_number}</code>\n\n"
            f"<tg-emoji emoji-id='5458603043203327669'>😀</tg-emoji> <b>You will receive messages automatically when they arrive</b>"
        )
    
    bot.edit_message_text(
        msg_text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=create_message_buttons(user_id)
    )


def process_country_code_logic(msg, user_id, country_code, state):
    
    country_code = str(country_code).replace('+', '').strip()
    
   
    import phonenumbers
    from phonenumbers import COUNTRY_CODE_TO_REGION_CODE
    
    
    potential_code = ""
    for i in range(min(len(country_code), 4), 0, -1):
        prefix = country_code[:i]
        if int(prefix) in COUNTRY_CODE_TO_REGION_CODE:
            potential_code = prefix
            break
            
    if potential_code:
        country_code = potential_code

    if not country_code.isdigit():
        bot.reply_to(msg, "❌ رمز الدولة يجب أن يحتوي على أرقام فقط!")
        return

    temp_file = state.get("temp_file")
    if not temp_file or not os.path.exists(temp_file):
        bot.reply_to(msg, "❌ لم يتم العثور على الملف! يرجى البدء من جديد.")
        if user_id in user_states: del user_states[user_id]
        return

    try:
        with open(temp_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        bot.reply_to(msg, f"❌ خطأ في قراءة الملف: {e}")
        return

    cleaned_numbers = []
    total_lines = 0
    rejected_lines = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        total_lines += 1
        first_part = line.split()[0] if line.split() else line
        digits_only = ''.join(c for c in first_part if c.isdigit())

        if digits_only.startswith(country_code) and len(digits_only) >= 8:
            cleaned_numbers.append(digits_only)
        else:
            rejected_lines += 1

    num_cleaned = len(cleaned_numbers)

    if num_cleaned == 0:
        bot.reply_to(
            msg,
            f"❌ <b>لم يتم العثور على أي أرقام تبدأ برمز الدولة {country_code}!</b>\n\n"
            f"📊 إجمالي الأسطر المعالجة: {total_lines}\n"
            f"❌ أرقام مرفوضة: {rejected_lines}\n\n"
            f"<i>تأكد من جودة الملف</i>",
            parse_mode="HTML"
        )
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if user_id in user_states: del user_states[user_id]
        return

    cleanup_old_numbers_files(country_code)
    
    cleaned_filename = f"numbers_{country_code}_{uuid.uuid4().hex[:8]}.txt"
    with open(cleaned_filename, "w", encoding="utf-8") as f:
        for num in cleaned_numbers:
            f.write(num + "\n")

    if os.path.exists(temp_file):
        os.remove(temp_file)

    user_states[user_id] = {
        "action": "na_add_country_name",
        "numbers_file": cleaned_filename,
        "country_code": country_code,
        "num_cleaned": num_cleaned,
        "total_lines": total_lines,
        "rejected_lines": rejected_lines
    }

    bot.reply_to(
        msg,
        f"✅ <b>File processed successfully!</b>\n\n"
        f"📊 Total lines: <b>{total_lines}</b>\n"
        f"✅ Accepted numbers: <b>{num_cleaned}</b>\n"
        f"🔢 Detected country code: <b>+{country_code}</b>\n\n"
        f"🔍 <b>Detecting country automatically...</b>",
        parse_mode="HTML"
    )

   
    country_name, flag, region_code = detect_country_from_number(country_code, user_id)
    
    
    lang = get_user_language(user_id)
    if lang == "ar":
       
        country_name_ar = geocoder.description_for_number(phonenumbers.parse("+" + country_code + "0000000"), "ar")
        if country_name_ar:
            country_name = country_name_ar

    # يسأل عن الاسم الذي سيظهر به الزر
    user_states[user_id] = {
        "action": "na_add_country_display_name",
        "numbers_file": cleaned_filename,
        "country_code": country_code,
        "country_name": country_name,  # الاسم التلقائي
        "num_cleaned": num_cleaned,
    }
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(f"✅ Use auto-detected name: {country_name}", callback_data="na_use_auto_name"))
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="admin"))
    
    bot.send_message(
        msg.chat.id,
        f"✅ <b>تم معالجة الأرقام بنجاح!</b>\n\n"
        f"🌍 الدولة المكتشفة: <b>{flag} {country_name} (+{country_code})</b>\n"
        f"📊 عدد الأرقام: <b>{num_cleaned}</b>\n\n"
        "📝 <b>Send the name to show on the button:</b>\n"
        "<i>Example: Egypt | Egypt WS | Pakistan 2</i>\n"
        "<i>Optional: add count like Egypt [5000]</i>",
        parse_mode="HTML",
        reply_markup=markup
    )
    return



def _send_balance(chat_id, user_id):
    REFERRALS_data = load_referrals()
    ref_data = REFERRALS_data.get(str(user_id), {})
    settings = load_referral_settings()
    balance = ref_data.get('balance', 0.0)
    count = len(ref_data.get('referrals', []))
    min_w = settings.get('min_withdrawal', 5.0)
    bonus = settings.get('referral_bonus', 0.005)
    lang = get_user_language(user_id)
    if lang == "ar":
        txt = (
            "<tg-emoji emoji-id='5417924076503062111'>💰</tg-emoji> <b>الرصيد</b>\n\n"
            f"<tg-emoji emoji-id='5204242830687494041'>🧾</tg-emoji> <b>رصيدك :</b> {balance:.3f} USDT\n"
            f"<tg-emoji emoji-id='5256143829672672750'>👤</tg-emoji> <b>الإحالات    :</b> {count}\n"
            f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> <b>الحد الأدنى للسحب :</b> {min_w} USDT\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"<tg-emoji emoji-id='5427168083074628963'>😀</tg-emoji> <b>ربح لكل إحالة:</b> {bonus} USDT\n"
            "<tg-emoji emoji-id='5445284980978621387'>🚀</tg-emoji> <b>ادعُ أصدقاءك لزيادة رصيدك</b>"
        )
    elif lang == "ru":
        txt = (
            "<tg-emoji emoji-id='5417924076503062111'>💰</tg-emoji> <b>БАЛАНС</b>\n\n"
            f"<tg-emoji emoji-id='5204242830687494041'>🧾</tg-emoji> <b>Ваш баланс :</b> {balance:.3f} USDT\n"
            f"<tg-emoji emoji-id='5256143829672672750'>👤</tg-emoji> <b>Рефералы    :</b> {count}\n"
            f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> <b>Мин. вывод :</b> {min_w} USDT\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"<tg-emoji emoji-id='5427168083074628963'>😀</tg-emoji> <b>Доход за реферала:</b> {bonus} USDT\n"
            "<tg-emoji emoji-id='5445284980978621387'>🚀</tg-emoji> <b>Приглашайте друзей для увеличения баланса</b>"
        )
    elif lang == "bn":
        txt = (
            "<tg-emoji emoji-id='5417924076503062111'>💰</tg-emoji> <b>ব্যালেন্স</b>\n\n"
            f"<tg-emoji emoji-id='5204242830687494041'>🧾</tg-emoji> <b>আপনার ব্যালেন্স :</b> {balance:.3f} USDT\n"
            f"<tg-emoji emoji-id='5256143829672672750'>👤</tg-emoji> <b>রেফারেল    :</b> {count}\n"
            f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> <b>সর্বনিম্ন উত্তোলন :</b> {min_w} USDT\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"<tg-emoji emoji-id='5427168083074628963'>😀</tg-emoji> <b>প্রতি রেফারেলে আয়:</b> {bonus} USDT\n"
            "<tg-emoji emoji-id='5445284980978621387'>🚀</tg-emoji> <b>বন্ধুদের আমন্ত্রণ জানান ব্যালেন্স বাড়াতে</b>"
        )
    else:
        txt = (
            "<tg-emoji emoji-id='5417924076503062111'>💰</tg-emoji> <b>BALANCE</b>\n\n"
            f"<tg-emoji emoji-id='5204242830687494041'>🧾</tg-emoji> <b>Your Balance :</b> {balance:.3f} USDT\n"
            f"<tg-emoji emoji-id='5256143829672672750'>👤</tg-emoji> <b>Referrals    :</b> {count}\n"
            f"<tg-emoji emoji-id='5264895611517300926'>🏦</tg-emoji> <b>Min Withdraw :</b> {min_w} USDT\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"<tg-emoji emoji-id='5427168083074628963'>😀</tg-emoji> <b>Earn per referral:</b> {bonus} USDT\n"
            "<tg-emoji emoji-id='5445284980978621387'>🚀</tg-emoji> <b>Invite friends to increase your balance</b>"
        )
    bot.send_message(chat_id, txt, parse_mode='HTML')

def _send_stat(chat_id, user_id):
    if str(user_id) not in USERS:
        USERS[str(user_id)] = {"selected_country": None, "selected_number": None,
                               "language": "en", "activations": 0,
                               "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        save_users()
    user_data = USERS.get(str(user_id), {})
    lang = user_data.get("language", "en") or "en"
    requests_count = user_data.get('activations', 0)
    numbers_received = user_data.get('numbers_received', requests_count)
    join_date = user_data.get("join_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_seen = user_data.get("last_seen", join_date)
    countries_used = len(set(user_data.get('countries_used', [])))
    if countries_used == 0 and user_data.get('selected_country'):
        countries_used = 1

    dot = "<b><tg-emoji emoji-id='5287664371319722275'>🔹</tg-emoji></b><b>"

    if lang == "ar":
        txt = (
            "╔═══《 <tg-emoji emoji-id='5974047364090957805'>📊</tg-emoji> إحصائياتك 》═══╗\n\n"
            f"{dot} إجمالي الطلبات: {requests_count}\n</b>"
            f"{dot} الأرقام المستلمة: {numbers_received}\n</b>"
            f"{dot} الدول المستخدمة: {countries_used}\n</b>"
            f"{dot} أول ظهور: {join_date}\n</b>"
            f"{dot} آخر ظهور: {last_seen}\n</b>\n"
            "╚══════════════════════╝"
        )
    elif lang == "ru":
        txt = (
            "╔═══《 <tg-emoji emoji-id='5974047364090957805'>📊</tg-emoji> СТАТИСТИКА 》═══╗\n\n"
            f"{dot} Всего запросов: {requests_count}\n</b>"
            f"{dot} Номеров получено: {numbers_received}\n</b>"
            f"{dot} Стран использовано: {countries_used}\n</b>"
            f"{dot} Первый вход: {join_date}\n</b>"
            f"{dot} Последний вход: {last_seen}\n</b>\n"
            "╚══════════════════════╝"
        )
    elif lang == "bn":
        txt = (
            "╔═══《 <tg-emoji emoji-id='5974047364090957805'>📊</tg-emoji> আপনার পরিসংখ্যান 》═══╗\n\n"
            f"{dot} মোট অনুরোধ: {requests_count}\n</b>"
            f"{dot} নম্বর পেয়েছেন: {numbers_received}\n</b>"
            f"{dot} ব্যবহৃত দেশ: {countries_used}\n</b>"
            f"{dot} প্রথম দেখা: {join_date}\n</b>"
            f"{dot} শেষ দেখা: {last_seen}\n</b>\n"
            "╚══════════════════════╝"
        )
    else:
        txt = (
            "━━━〔 <tg-emoji emoji-id='5231200819986047254'>😀</tg-emoji> USER STATISTICS 〕━━━\n\n"
            f"<b><tg-emoji emoji-id='5474572869776189434'>🚘</tg-emoji></b><b> Requests  : {requests_count}\n</b>"
            f"<b><tg-emoji emoji-id='5406809207947142040'>📲</tg-emoji></b><b> Numbers   : {numbers_received}\n</b>"
            f"<b><tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji></b><b> Countries  : {countries_used}\n</b>"
            f"<b><tg-emoji emoji-id='4981190601887188725'>🔴</tg-emoji></b><b> First Seen : {join_date}\n</b>"
            f"<b><tg-emoji emoji-id='5188234920639632382'>🟢</tg-emoji></b><b> Last Seen  : {last_seen}</b>"
        )
    bot.send_message(chat_id, txt, parse_mode='HTML')

def _send_withdraw(chat_id, user_id):
    REFERRALS_data = load_referrals()
    ref_data = REFERRALS_data.get(str(user_id), {})
    settings = load_referral_settings()
    balance = ref_data.get('balance', 0.0)
    min_w = settings.get('min_withdrawal', 30.0)
    lang = get_user_language(user_id)
    if balance >= min_w:
        try:
            admins_list = load_admins() if callable(load_admins) else []
            for admin_id in admins_list[:1]:
                bot.send_message(int(admin_id),
                    f'💸 <b>Withdrawal Request!</b>\n\n'
                    f'👤 User: <code>{user_id}</code>\n'
                    f'💰 Amount: {balance:.3f} USDT\n'
                    f'📅 Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                    parse_mode='HTML')
        except Exception as e:
            print(f'withdraw notify error: {e}')
        if lang == "ar":
            txt = (
                "<tg-emoji emoji-id='5287664371319722275'>🔹</tg-emoji> <b>سحب الرصيد</b>\n\n"
                f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> <b>الحد الأدنى للسحب :</b> {min_w} USDT\n"
                f"<tg-emoji emoji-id='5472250091332993630'>💳</tg-emoji> <b>الرصيد الحالي     :</b> {balance:.3f} USDT\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "<tg-emoji emoji-id='5386367538735104399'>⌛</tg-emoji> <b>تم إرسال طلب السحب!\nسيتواصل معك أحد المشرفين قريباً.</b>"
            )
        elif lang == "ru":
            txt = (
                "<tg-emoji emoji-id='5287664371319722275'>🔹</tg-emoji> <b>ВЫВОД</b>\n\n"
                f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> <b>Мин. вывод :</b> {min_w} USDT\n"
                f"<tg-emoji emoji-id='5472250091332993630'>💳</tg-emoji> <b>Текущий баланс     :</b> {balance:.3f} USDT\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "<tg-emoji emoji-id='5386367538735104399'>⌛</tg-emoji> <b>Запрос на вывод отправлен!\nАдмин свяжется с вами скоро.</b>"
            )
        elif lang == "bn":
            txt = (
                "<tg-emoji emoji-id='5287664371319722275'>🔹</tg-emoji> <b>উত্তোলন</b>\n\n"
                f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> <b>সর্বনিম্ন উত্তোলন :</b> {min_w} USDT\n"
                f"<tg-emoji emoji-id='5472250091332993630'>💳</tg-emoji> <b>বর্তমান ব্যালেন্স     :</b> {balance:.3f} USDT\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "<tg-emoji emoji-id='5386367538735104399'>⌛</tg-emoji> <b>উত্তোলনের অনুরোধ পাঠানো হয়েছে!\nএকজন অ্যাডমিন শীঘ্রই যোগাযোগ করবেন।</b>"
            )
        else:
            txt = (
                "<tg-emoji emoji-id='5287664371319722275'>🔹</tg-emoji> <b>WITHDRAW</b>\n\n"
                f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> <b>Minimum Withdrawal :</b> {min_w} USDT\n"
                f"<tg-emoji emoji-id='5472250091332993630'>💳</tg-emoji> <b>Current Balance     :</b> {balance:.3f} USDT\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "<tg-emoji emoji-id='5386367538735104399'>⌛</tg-emoji> <b>Withdrawal request sent!\nAn admin will contact you soon.</b>"
            )
    else:
        if lang == "ar":
            txt = (
                "<tg-emoji emoji-id='5287664371319722275'>🔹</tg-emoji> <b>سحب الرصيد</b>\n\n"
                f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> <b>الحد الأدنى للسحب :</b> {min_w} USDT\n"
                f"<tg-emoji emoji-id='5472250091332993630'>💳</tg-emoji> <b>الرصيد الحالي     :</b> {balance:.3f} USDT\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "<tg-emoji emoji-id='5386367538735104399'>⌛</tg-emoji> <b>عند الوصول للحد الأدنى،\nستتمكن من السحب.</b>"
            )
        elif lang == "ru":
            txt = (
                "<tg-emoji emoji-id='5287664371319722275'>🔹</tg-emoji> <b>ВЫВОД</b>\n\n"
                f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> <b>Мин. вывод :</b> {min_w} USDT\n"
                f"<tg-emoji emoji-id='5472250091332993630'>💳</tg-emoji> <b>Текущий баланс     :</b> {balance:.3f} USDT\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "<tg-emoji emoji-id='5386367538735104399'>⌛</tg-emoji> <b>Достигните минимума,\nчтобы вывести средства.</b>"
            )
        elif lang == "bn":
            txt = (
                "<tg-emoji emoji-id='5287664371319722275'>🔹</tg-emoji> <b>উত্তোলন</b>\n\n"
                f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> <b>সর্বনিম্ন উত্তোলন :</b> {min_w} USDT\n"
                f"<tg-emoji emoji-id='5472250091332993630'>💳</tg-emoji> <b>বর্তমান ব্যালেন্স     :</b> {balance:.3f} USDT\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "<tg-emoji emoji-id='5386367538735104399'>⌛</tg-emoji> <b>সর্বনিম্নে পৌঁছালে,\nআপনি উত্তোলন করতে পারবেন।</b>"
            )
        else:
            txt = (
                "<tg-emoji emoji-id='5287664371319722275'>🔹</tg-emoji> <b>WITHDRAW</b>\n\n"
                f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> <b>Minimum Withdrawal :</b> {min_w} USDT\n"
                f"<tg-emoji emoji-id='5472250091332993630'>💳</tg-emoji> <b>Current Balance     :</b> {balance:.3f} USDT\n\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "<tg-emoji emoji-id='5386367538735104399'>⌛</tg-emoji> <b>When you reach the minimum,\nyou will be able to withdraw.</b>"
            )
    bot.send_message(chat_id, txt, parse_mode='HTML')


# ═══════════════════════════════════════════════════
# دالة مساعدة لعرض الدول المتاحة
# ═══════════════════════════════════════════════════
def _send_available_countries(msg):
    user_id = msg.from_user.id
    lang = get_user_language(user_id)

    if not COUNTRIES:
        if lang == "ar":
            no_countries_msg = "<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> لا توجد دول متاحة حالياً."
        elif lang == "ru":
            no_countries_msg = "<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> Нет доступных стран."
        elif lang == "bn":
            no_countries_msg = "<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> কোনো দেশ পাওয়া যাচ্ছে না।"
        else:
            no_countries_msg = "<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji> No countries available yet."
        bot.send_message(
            msg.chat.id,
            no_countries_msg,
            parse_mode="HTML"
        )
        return

    lines = []
    for cid, info in COUNTRIES.items():
        dname = info.get("display_name", cid)
        flag  = info.get("flag", "🌍")
        count = info.get("numbers_count", 0)
        fname = info.get("file", "")
        if count == 0 and fname and os.path.exists(fname):
            try:
                with open(fname, "r", encoding="utf-8") as fh:
                    count = sum(1 for l in fh if l.strip())
            except:
                pass
        plain_flag = extract_plain_emoji(flag)
        eid = extract_tg_emoji_id(flag)
        if eid:
            flag_display = f"<tg-emoji emoji-id=\'{eid}\'>{plain_flag}</tg-emoji>"
        else:
            flag_display = plain_flag
        lines.append(
            f"<tg-emoji emoji-id=\'4981190601887188725\'>🔴</tg-emoji> "
            f"<b>{flag_display} {dname} | ({count:,})</b>"
        )

    if lang == "ar":
        header = "═══《 <tg-emoji emoji-id=\'5447410659077661506\'>🌐</tg-emoji> الدول المتاحة 》═══"
    elif lang == "ru":
        header = "═══《 <tg-emoji emoji-id=\'5447410659077661506\'>🌐</tg-emoji> ДОСТУПНЫЕ СТРАНЫ 》═══"
    elif lang == "bn":
        header = "═══《 <tg-emoji emoji-id=\'5447410659077661506\'>🌐</tg-emoji> উপলব্ধ দেশসমূহ 》═══"
    else:
        header = "═══《 <tg-emoji emoji-id=\'5447410659077661506\'>🌐</tg-emoji> AVAILABLE COUNTRIES 》═══"
    txt = f"{header}\n\n" + "\n".join(lines)
    bot.send_message(msg.chat.id, txt, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("avail_country_"))
def avail_country_cb(call):
    bot.answer_callback_query(call.id)


def _send_refer(chat_id, user_id):
    if str(user_id) not in USERS:
        USERS[str(user_id)] = {"selected_country": None, "selected_number": None,
                               "language": "en", "activations": 0,
                               "join_date": datetime.now().strftime("%Y-%m-%d")}
        save_users()
    REFERRALS_data = load_referrals()
    ref_data = REFERRALS_data.get(str(user_id), {})
    settings = load_referral_settings()
    code_bonus = settings.get("code_bonus", 0.003)
    friends   = len(ref_data.get("referrals", []))
    active    = ref_data.get("active_referrals", 0)
    earned    = ref_data.get("total_earned", 0.0)
    balance   = ref_data.get("balance", 0.0)
    lang = get_user_language(user_id)
    try:
        bot_info = bot.get_me()
        bot_username = bot_info.username
    except:
        bot_username = 'MA-X BOT'
    ref_link  = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    if lang == "ar":
        txt = (
            "╭─〔 <tg-emoji emoji-id='5449468596952507859'>💜</tg-emoji>"
            " نظام الإحالة "
            "<tg-emoji emoji-id='5449468596952507859'>💜</tg-emoji>〕─╮\n\n"
            "├─ <tg-emoji emoji-id='5258362837411045098'>👤</tg-emoji> <b>الإحصائيات</b>\n"
            f"│<tg-emoji emoji-id='5395695537687123235'>🚨</tg-emoji> • الأصدقاء : {friends}\n"
            f"│<tg-emoji emoji-id='5395695537687123235'>🚨</tg-emoji> • النشطين  : {active}\n"
            f"│<tg-emoji emoji-id='5395695537687123235'>🚨</tg-emoji> • الأرباح  : +{earned:.3f}$\n\n"
            "├─ <tg-emoji emoji-id='5271604874419647061'>🔗</tg-emoji> <b>رابط الدعوة الخاص بك</b>\n"
            f"│ {ref_link}\n\n"
            "├─ <tg-emoji emoji-id='5974082522693248507'>😀</tg-emoji> <b>كيف يعمل النظام</b>\n"
            f"│<tg-emoji emoji-id='5888663955412359816'>🔥</tg-emoji> • قم بدعوة أصدقائك\n"
            f"│<tg-emoji emoji-id='5888663955412359816'>🔥</tg-emoji> • تفعيل 5 أرقام\n"
            f"│<tg-emoji emoji-id='5888663955412359816'>🔥</tg-emoji> • اربح +{code_bonus:.3f}$ لكل كود\n\n"
            "╰───────────────╯\n"
            "<tg-emoji emoji-id='5445284980978621387'>🚀</tg-emoji> <b>ابدأ الربح الآن!</b>"
        )
        btn_text = "👥 دعوة صديق"
        share_msg = "انضم واربح معي!"
    else:
        txt = (
            "╭─〔 <tg-emoji emoji-id='5449468596952507859'>💜</tg-emoji>"
            " REFERRAL "
            "<tg-emoji emoji-id='5449468596952507859'>💜</tg-emoji>〕─╮\n\n"
            "├─ <tg-emoji emoji-id='5258362837411045098'>👤</tg-emoji> <b>Stats</b>\n"
            f"│<tg-emoji emoji-id='5395695537687123235'>🚨</tg-emoji> • Friends : {friends}\n"
            f"│<tg-emoji emoji-id='5395695537687123235'>🚨</tg-emoji> • Active  : {active}\n"
            f"│<tg-emoji emoji-id='5395695537687123235'>🚨</tg-emoji> • Earned  : +{earned:.3f}$\n\n"
            "├─ <tg-emoji emoji-id='5271604874419647061'>🔗</tg-emoji> <b>Your Link</b>\n"
            f"│ {ref_link}\n\n"
            "├─ <tg-emoji emoji-id='5974082522693248507'>😀</tg-emoji> <b>How It Works</b>\n"
            f"│<tg-emoji emoji-id='5888663955412359816'>🔥</tg-emoji> • Invite friends\n"
            f"│<tg-emoji emoji-id='5888663955412359816'>🔥</tg-emoji> • Activate 5 numbers\n"
            f"│<tg-emoji emoji-id='5888663955412359816'>🔥</tg-emoji> • Earn +{code_bonus:.3f}$ per OTP\n\n"
            "╰───────────────╯\n"
            "<tg-emoji emoji-id='5445284980978621387'>🚀</tg-emoji> <b>Start Earning!</b>"
        )
        btn_text = " Invite a friend"
        share_msg = "Join and earn with me!"

    markup = InlineKeyboardMarkup(row_width=1)
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_msg}"
    try:
        markup.add(InlineKeyboardButton(
            btn_text,
            url=share_url,
            icon_custom_emoji_id="5967432491684860012"
        ))
    except:
        markup.add(InlineKeyboardButton(f"👥 {btn_text}", url=share_url))
    bot.send_message(chat_id, txt, parse_mode="HTML", reply_markup=markup)


def _send_invite(chat_id, user_id):
    if str(user_id) not in USERS:
        USERS[str(user_id)] = {"selected_country": None, "selected_number": None,
                               "language": "en", "activations": 0,
                               "join_date": datetime.now().strftime("%Y-%m-%d")}
        save_users()
    REFERRALS_data = load_referrals()
    ref_data = REFERRALS_data.get(str(user_id), {})
    settings = load_referral_settings()
    code_bonus = settings.get("code_bonus", 0.003)
    friends   = len(ref_data.get("referrals", []))
    active    = ref_data.get("active_referrals", 0)
    earned    = ref_data.get("total_earned", 0.0)
    try:
        bot_info = bot.get_me()
        bot_username = bot_info.username
    except:
        bot_username = 'MA-X BOT'
    ref_link  = f"https://t.me/{bot_username}?start=ref_{user_id}"
    txt = (
        "╭─〔 <tg-emoji emoji-id='5449468596952507859'>💜</tg-emoji>"
        " Invite"
        "<tg-emoji emoji-id='5449468596952507859'>💜</tg-emoji>〕─╮\n\n"
        "├─ <tg-emoji emoji-id='5258362837411045098'>👤</tg-emoji> <b>Stats</b>\n"
        f"│<tg-emoji emoji-id='5395695537687123235'>🚨</tg-emoji> • Friends : {friends}\n"
        f"│<tg-emoji emoji-id='5395695537687123235'>🚨</tg-emoji> • Active  : {active}\n"
        f"│<tg-emoji emoji-id='5395695537687123235'>🚨</tg-emoji> • Earned  : +{earned:.3f}$\n\n"
        "├─ <tg-emoji emoji-id='5271604874419647061'>🔗</tg-emoji> <b>Your Link</b>\n"
        f"│ {ref_link}\n\n"
        "├─ <tg-emoji emoji-id='5974082522693248507'>😀</tg-emoji> <b>How It Works</b>\n"
        f"│<tg-emoji emoji-id='5888663955412359816'>🔥</tg-emoji> • Invite friends\n"
        f"│<tg-emoji emoji-id='5888663955412359816'>🔥</tg-emoji> • Activate 5 numbers\n"
        f"│<tg-emoji emoji-id='5888663955412359816'>🔥</tg-emoji> • Earn +{code_bonus:.3f}$ per OTP\n\n"
        "╰───────────────╯\n"
        "<tg-emoji emoji-id='5445284980978621387'>🚀</tg-emoji> <b>Start Earning!</b>"
    )
    markup = InlineKeyboardMarkup(row_width=1)
    try:
        markup.add(InlineKeyboardButton(
            " Invite a friend",
            url=share_url,
            icon_custom_emoji_id="5967432491684860012"
        ))
    except:
        markup.add(InlineKeyboardButton("👥 Invite a friend", url=share_url))
    bot.send_message(chat_id, txt, parse_mode="HTML", reply_markup=markup)


def _send_my_rewards(chat_id, user_id):
    """My Rewards screen"""
    REFERRALS_data = load_referrals()
    ref_data  = REFERRALS_data.get(str(user_id), {})
    settings  = load_referral_settings()
    balance   = ref_data.get("balance", 0.0)
    total_earned = ref_data.get("total_earned", 0.0)
    otps_recv = USERS.get(str(user_id), {}).get("activations", 0)
    min_w     = settings.get("min_withdrawal", 18.0)
    remaining = max(min_w - balance, 0.0)
    txt = (
        "╭━━━〔 <tg-emoji emoji-id='5188344996356448758'>🏆</tg-emoji> YOUR REWARDS 〕━━━╮\n\n"
        f"<tg-emoji emoji-id='5417924076503062111'>💰</tg-emoji> <b>Balance:</b> {balance:.3f}$\n"
        f"<tg-emoji emoji-id='5472308992514464048'>🔐</tg-emoji> <b>Received OTPs:</b> {otps_recv}\n\n"
        f"<tg-emoji emoji-id='5431449001532594346'>⚡️</tg-emoji> <b>Total Earnings:</b> {total_earned:.3f}$\n"
        f"<tg-emoji emoji-id='5350460637182993292'>🎯</tg-emoji> <b>Withdrawal Target:</b> {min_w:.1f}$\n\n"
        f"<tg-emoji emoji-id='5231200819986047254'>📊</tg-emoji> <b>Remaining:</b> {remaining:.3f}$\n\n"
        "<tg-emoji emoji-id='5188481279963715781'>🚀</tg-emoji> <b>Keep going to reach your goal!</b>"
    )
    bot.send_message(chat_id, txt, parse_mode="HTML")

# ═══════════════════════════════════════════════════
# /refer command
# ═══════════════════════════════════════════════════




@bot.message_handler(func=lambda msg: msg.chat.type == "private" and msg.text and msg.text.strip() == "My Balance")
def amount_handler(msg):
    user_id = msg.from_user.id
    if is_banned(user_id): return
    channels = check_subscription(user_id)

    if channels:
        send_subscription_message_with_image(msg.chat.id, user_id)
        return
    _send_amount(msg.chat.id, user_id)

@bot.message_handler(func=lambda msg: msg.chat.type == "private" and msg.text and msg.text.strip() == "Withdraw")
def withdraw_keyboard_handler(msg):
    user_id = msg.from_user.id
    if is_banned(user_id): return
    channels = check_subscription(user_id)

    if channels:
        send_subscription_message_with_image(msg.chat.id, user_id)
        return
    _send_withdraw_kb(msg.chat.id, user_id)

def _clear_prefix(chat_id, user_id):
    """مسح الرقم المختار للمستخدم"""
    uid_str = str(user_id)
    if uid_str in USERS:
        USERS[uid_str]["selected_number"] = None
        USERS[uid_str]["selected_country"] = None
        USERS[uid_str]["selected_numbers"] = []
        USERS[uid_str]["display_numbers"] = []
        save_users()
    bot.send_message(chat_id,
        "<tg-emoji emoji-id='5273806972871787310'>✅</tg-emoji> Prefix cleared.",
        parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.chat.type == "private" and msg.text and msg.text.strip() == "Clear Prefix")
def clear_prefix_handler(msg):
    user_id = msg.from_user.id
    if is_banned(user_id): return
    channels = check_subscription(user_id)

    if channels:
        send_subscription_message_with_image(msg.chat.id, user_id)
        return
    _clear_prefix(msg.chat.id, user_id)

def _send_invite(chat_id, user_id):
    _send_invite_earn(chat_id, user_id)

def _send_invite_earn(chat_id, user_id):
    REFERRALS_data = load_referrals()
    ref_data = REFERRALS_data.get(str(user_id), {})
    settings = load_referral_settings()
    code_bonus = settings.get("code_bonus", 0.003)
    friends = len(ref_data.get("referrals", []))
    active  = ref_data.get("active_referrals", 0)
    total_earned = ref_data.get("total_earned", 0.0)
    try:
        bot_info = bot.get_me()
        bot_username = bot_info.username
    except:
        bot_username = 'MA-X BOT'
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    txt = (
        f"<tg-emoji emoji-id='5372926953978341366'>👥</tg-emoji> <b>Invite &amp; Earn</b> "
        f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji>\n\n"
        f"<tg-emoji emoji-id='5271604874419647061'>🔗</tg-emoji> Your Referral Link:\n"
        f"{ref_link}\n\n"
        f"<tg-emoji emoji-id='5373012449597335010'>👤</tg-emoji> Total Invites: {friends}\n"
        f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> Reward per Invite: ${settings.get('referral_bonus', 0.018):.3f}\n\n"
        f"<tg-emoji emoji-id='4967558156646352261'>👍</tg-emoji> Share your link and start earning now!"
    )
    markup = InlineKeyboardMarkup(row_width=1)
    try:
        markup.add(InlineKeyboardButton(
            " Invite a friend",
            url=share_url,
            icon_custom_emoji_id="5967432491684860012"
        ))
    except:
        markup.add(InlineKeyboardButton("👥 Invite a friend", url=share_url))
    bot.send_message(chat_id, txt, parse_mode="HTML", reply_markup=markup)

def _send_amount(chat_id, user_id):
    REFERRALS_data = load_referrals()
    ref_data = REFERRALS_data.get(str(user_id), {})
    settings = load_referral_settings()
    balance = ref_data.get("balance", 0.0)
    friends = len(ref_data.get("referrals", []))
    try:
        bot_info = bot.get_me()
        bot_username = bot_info.username
    except:
        bot_username = 'MA-X BOT'
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    txt = (
        f"╭─ <tg-emoji emoji-id='5417924076503062111'>💰</tg-emoji> Account Overview ─╮\n"
        f"│ Wallet: ${balance:.4f} (≈ {int(balance * 110)} BDT)\n"
        f"│\n"
        f"│ <tg-emoji emoji-id='5271604874419647061'>🔗</tg-emoji> Your Link:\n"
        f"│ {ref_link}\n"
        f"│\n"
        f"│ <tg-emoji emoji-id='5372926953978341366'>👥</tg-emoji> Referrals: {friends}\n"
        f"│ <tg-emoji emoji-id='5193085063998224234'>🎁</tg-emoji> Per Referral: ${settings.get('referral_bonus', 0.02):.4f}\n"
        f"╰────────────────────╯"
    )
    share_text = f"🎁 Join this bot and earn money!\n{ref_link}"
    markup = InlineKeyboardMarkup(row_width=1)
    try:
        markup.add(InlineKeyboardButton(
            " Share & Earn",
            url=share_url,
            icon_custom_emoji_id="5271604874419647061"
        ))
    except:
        markup.add(InlineKeyboardButton("🔗 Share & Earn", url=share_url))
    bot.send_message(chat_id, txt, parse_mode="HTML", reply_markup=markup)

def _send_withdraw_kb(chat_id, user_id):
    REFERRALS_data = load_referrals()
    ref_data = REFERRALS_data.get(str(user_id), {})
    settings = load_referral_settings()
    balance = ref_data.get("balance", 0.0)
    min_w = settings.get("min_withdrawal", 18.0)
    if balance < min_w:
        txt = (
            f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji>"
            f" You need at least <b>${min_w:.2f}</b> to withdraw."
        )
        bot.send_message(chat_id, txt, parse_mode="HTML")
    else:
        txt = (
            f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> <b>WITHDRAW</b>\n\n"
            f"<tg-emoji emoji-id='5417924076503062111'>💰</tg-emoji> <b>Your Balance: ${balance:.4f}</b>\n"
            f"<tg-emoji emoji-id='5350460637182993292'>🎯</tg-emoji> <b>Withdrawal Target: ${min_w:.2f}</b>\n\n"
            f"<tg-emoji emoji-id='5273806972871787310'>✅</tg-emoji> <b>You reached the target! Press below to request.</b>"
        )
        markup = InlineKeyboardMarkup(row_width=1)
        try:
            markup.add(InlineKeyboardButton(
                " Request Withdrawal",
                callback_data=f"withdraw_req_{user_id}",
                icon_custom_emoji_id="5409048419211682843",
                style="success"
            ))
        except:
            markup.add(InlineKeyboardButton("💵 Request Withdrawal", callback_data=f"withdraw_req_{user_id}"))
        bot.send_message(chat_id, txt, parse_mode="HTML", reply_markup=markup)


def _send_withdraw(chat_id, user_id):
    REFERRALS_data = load_referrals()
    ref_data = REFERRALS_data.get(str(user_id), {})
    settings = load_referral_settings()
    balance = ref_data.get("balance", 0.0)
    min_w   = settings.get("min_withdrawal", 18.0)

    if balance >= min_w:
        txt = (
            "<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> <b>WITHDRAW</b>\n\n"
            f"<tg-emoji emoji-id='5417924076503062111'>💰</tg-emoji> <b>Your Balance: {balance:.3f}$</b>\n"
            f"<tg-emoji emoji-id='5350460637182993292'>🎯</tg-emoji> <b>Withdrawal Target: ${min_w:.2f}</b>\n\n"
            "<tg-emoji emoji-id='5273806972871787310'>✅</tg-emoji> <b>You reached the target! Press below to request.</b>"
        )
        markup = InlineKeyboardMarkup(row_width=1)
        try:
            markup.add(InlineKeyboardButton(
                " to request",
                callback_data=f"withdraw_req_{user_id}",
                icon_custom_emoji_id="5409048419211682843",
                style="success"
            ))
        except:
            markup.add(InlineKeyboardButton("💵 to request", callback_data=f"withdraw_req_{user_id}"))
        bot.send_message(chat_id, txt, parse_mode="HTML", reply_markup=markup)
    else:
        txt = (
            f"<tg-emoji emoji-id='5210952531676504517'>❌</tg-emoji>"
            f" You need at least <b>${min_w:.2f}</b> to withdraw."
        )
        bot.send_message(chat_id, txt, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("send_prefix_"))
def send_prefix_callback(call):
    user_id = call.from_user.id
    bot_uid = get_user_bot_id(user_id)
    bot.answer_callback_query(
        call.id,
        f"Prefix ID:\n{bot_uid}",
        show_alert=True
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_req_"))
def withdraw_req_callback(call):
    requester_id = call.from_user.id
    REFERRALS_data = load_referrals()
    ref_data  = REFERRALS_data.get(str(requester_id), {})
    settings  = load_referral_settings()
    balance   = ref_data.get("balance", 0.0)
    min_w     = settings.get("min_withdrawal", 18.0)
    if balance < min_w:
        bot.answer_callback_query(call.id, f"❌ Balance ${balance:.3f} is below minimum ${min_w:.2f}", show_alert=True)
        return
    total_earned = ref_data.get("total_earned", 0.0)
    otps_recv    = USERS.get(str(requester_id), {}).get("activations", 0)
    uname = call.from_user.username or "N/A"
    fname = call.from_user.first_name or "N/A"
    # Notify admins
    try:
        admins_list = load_admins()
        for admin_id in admins_list:
            try:
                bot.send_message(int(admin_id),
                    f"💸 <b>Withdrawal Request!</b>\n\n"
                    f"👤 Name: {fname}\n"
                    f"🆔 User ID: <code>{requester_id}</code>\n"
                    f"📎 Username: @{uname}\n"
                    f"💰 Balance: <b>{balance:.3f}$</b>\n"
                    f"⚡️ Total Earned: {total_earned:.3f}$\n"
                    f"🔐 OTPs Received: {otps_recv}\n"
                    f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    parse_mode="HTML")
            except: pass
    except Exception as e:
        print(f"withdraw notify error: {e}")
    bot.answer_callback_query(call.id, "✅ Request sent to admin!", show_alert=True)
    try:
        bot.edit_message_text(
            f"<tg-emoji emoji-id='5409048419211682843'>💵</tg-emoji> <b>WITHDRAW</b>\n\n"
            f"<tg-emoji emoji-id='5273806972871787310'>✅</tg-emoji> <b>Your request has been sent!</b>\n"
            f"<tg-emoji emoji-id='5386367538735104399'>⌛</tg-emoji> An admin will contact you soon.\n\n"
            f"💰 Amount: <b>{balance:.3f}$</b>",
            call.message.chat.id, call.message.message_id,
            parse_mode="HTML"
        )
    except: pass

# ═══════════════════════════════════════════════════
# /withdraw command
# ═══════════════════════════════════════════════════

# /support command removed from sidebar - button in keyboard triggers _send_support_msg directly
@bot.callback_query_handler(func=lambda call: call.data == "admin_set_default_layout")
def admin_set_default_layout_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("✅ تأكيد", callback_data="confirm_default_layout"))
    try:
        markup.add(make_back_button("رجوع", "admin"))
    except:
        markup.add(InlineKeyboardButton("◀ رجوع", callback_data="admin"))
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text(
            "🌍 <b>الشكل الافتراضي/MODY</b>\n\n"
            "سيتم تفعيل الكيبورد الأرضي مع رسالة ترحيب مخصصة.\n"
            "اضغط تأكيد للتفعيل:",
            call.message.chat.id, call.message.message_id,
            parse_mode="HTML", reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id, "اضغط تأكيد:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_default_layout")
def confirm_default_layout_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    set_bot_layout("default")
    bot.answer_callback_query(call.id, "✅ تم تعيين الشكل الافتراضي!", show_alert=True)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    # إخفاء الكيبورد الأصلي أولاً ثم إرسال الكيبورد الافتراضي
    first_name = call.from_user.first_name or "User"
    welcome_msg = get_mody_welcome_msg(first_name, "en")
    try:
        hide_msg = bot.send_message(call.message.chat.id, "⏳", reply_markup=ReplyKeyboardRemove())
        bot.delete_message(call.message.chat.id, hide_msg.message_id)
    except:
        pass
    bot.send_message(
        call.message.chat.id,
        welcome_msg,
        parse_mode="HTML",
        reply_markup=get_main_reply_keyboard(user_id)
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_set_original_layout")
def admin_set_original_layout_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    set_bot_layout("original")
    bot.answer_callback_query(call.id, "✅ تم تعيين الشكل الأصلي!", show_alert=True)
    # إخفاء الكيبورد وإظهار قائمة الخدمات مباشرة بدون رسالة ترحيب
    welcome_text = get_welcome_text(user_id)
    markup = get_country_buttons_all(user_id)
    # أولاً نحذف الكيبورد الأرضي بإرسال رسالة مؤقتة
    try:
        hide_msg = bot.send_message(
            call.message.chat.id,
            "⏳",
            reply_markup=ReplyKeyboardRemove()
        )
        bot.delete_message(call.message.chat.id, hide_msg.message_id)
    except:
        pass
    if markup:
        bot.send_message(
            call.message.chat.id,
            welcome_text,
            parse_mode="HTML",
            reply_markup=markup
        )
    else:
        bot.send_message(
            call.message.chat.id,
            welcome_text,
            parse_mode="HTML"
        )


# ═══════════════════════════════════════════════════
# pick_num callback
# ═══════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda call: call.data.startswith("pick_num_"))
def pick_num_callback(call):
    user_id = call.from_user.id
    num = call.data.replace("pick_num_", "")
    if str(user_id) not in USERS:
        bot.answer_callback_query(call.id, "❌ No session!", show_alert=True)
        return
    USERS[str(user_id)]["selected_number"] = num
    USERS[str(user_id)]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_users()
    dn = f"+{num.lstrip('+ ')}"
    bot.answer_callback_query(call.id, f"✅ Selected: {dn}", show_alert=False)
    display_numbers = USERS[str(user_id)].get("display_numbers", [num])
    cid = USERS[str(user_id)].get("selected_country", "")
    info = COUNTRIES.get(cid, {})
    flag = info.get("flag", "🌍")
    flag_eid_a = extract_tg_emoji_id(flag)
    plain_flag_a = extract_plain_emoji(flag)
    flag_display_a = f"<tg-emoji emoji-id='{flag_eid_a}'>{plain_flag_a}</tg-emoji>" if flag_eid_a else plain_flag_a
    loc = info.get("display_name", cid)
    lang_ns = get_user_language(user_id)
    if lang_ns == "ar":
        txt = f"{flag_display_a} <b>{loc} — تم اختيار الرقم!</b>\n\n⏳ <b>في انتظار كود التحقق..</b>\n<i>اضغط على أي رقم لنسخه</i>"
    elif lang_ns == "ru":
        txt = f"{flag_display_a} <b>{loc} — Номер выбран!</b>\n\n⏳ <b>Ожидание OTP..</b>\n<i>Нажмите на любой номер, чтобы скопировать</i>"
    elif lang_ns == "bn":
        txt = f"{flag_display_a} <b>{loc} — নম্বর নির্বাচিত!</b>\n\n⏳ <b>OTP-এর জন্য অপেক্ষা করছি..</b>\n<i>কপি করতে যেকোনো নম্বর ট্যাপ করুন</i>"
    else:
        txt = f"{flag_display_a} <b>{loc} — Number Selected!</b>\n\n⏳ <b>Waiting For OTP..</b>\n<i>Tap any number to copy / select</i>"
    mu = InlineKeyboardMarkup(row_width=1)
    for n in display_numbers:
        dn2 = f"+{n.lstrip('+').lstrip()}"
        try:
            mu.add(InlineKeyboardButton(
                text=f" {dn2}",
                copy_text=CopyTextButton(text=dn2),
                icon_custom_emoji_id=flag_eid_a if flag_eid_a else "5406809207947142040"
            ))
        except:
            mu.add(InlineKeyboardButton(f"{plain_flag_a} {dn2}", callback_data=f"pick_num_{n}"))

    # تغيير الرقم — أحمر
    _cn_txt2 = "تغيير الرقم" if lang_ns == "ar" else "Change Number"
    try:
        mu.add(InlineKeyboardButton(
            text=f" {_cn_txt2}",
            callback_data=f"direct_reroll_{country_name}",
            icon_custom_emoji_id="5258420634785947640",
            style="danger"
        ))
    except:
        mu.add(InlineKeyboardButton(f"🔄 {_cn_txt2}", callback_data=f"direct_reroll_{country_name}"))

    # تغيير الدولة — أزرق
    _cc_txt2 = "تغيير الدولة" if lang_ns == "ar" else "Change Country"
    try:
        mu.add(InlineKeyboardButton(
            text=f" {_cc_txt2}",
            callback_data="back_to_countries",
            icon_custom_emoji_id="5447410659077661506",
            style="primary"
        ))
    except:
        mu.add(InlineKeyboardButton(f"🌍 {_cc_txt2}", callback_data="back_to_countries"))

    # جروب البوت — أخضر
    _grp_txt2 = "جروب البوت" if lang_ns == "ar" else "OTP Group"
    _grp_links2 = load_button_links()
    try:
        mu.add(InlineKeyboardButton(
            text=f" {_grp_txt2}",
            url=_grp_links2.get("group_link", "https://t.me/UltronX_MegaBo"),
            icon_custom_emoji_id="5458603043203327669",
            style="success"
        ))
    except:
        mu.add(InlineKeyboardButton(f"📨 {_grp_txt2}", url=_grp_links2.get("group_link", "https://t.me/EMRAITE_5")))

    # القائمة الرئيسية — شفاف
    _mm_txt2 = "القائمة الرئيسية" if lang_ns == "ar" else "Main Menu"
    try:
        mu.add(InlineKeyboardButton(
            text=f" {_mm_txt2}",
            callback_data="back_to_countries",
            icon_custom_emoji_id="5321334093126842469"
        ))
    except:
        mu.add(InlineKeyboardButton(f"◀ {_mm_txt2}", callback_data="back_to_countries"))
    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=mu)
    except:
        pass



# ═══════════════════════════════════════════════════
# ReplyKeyboard text button handlers
# ═══════════════════════════════════════════════════
@bot.message_handler(func=lambda msg: msg.chat.type == "private" and msg.text and (msg.text.strip() in [
    # EN buttons (no emoji prefix)
    "Take Number", "Balance", "Refer & Earn", "Withdraw", "Statistics", "Countries",
    # New button names (matching image)
    "Get Number", "Available Country", "Status", "Live Traffic",
    # AR buttons (no emoji prefix)
    "الحصول على رقم", "الرصيد", "شارك واربح", "سحب الرصيد", "الإحصائيات", "الدول المتاحة", "📲 الحصول على رقم", "💰 الرصيد", "🎁 شارك واربح", "💸 سحب الرصيد", "📊 الإحصائيات", "🌍 الدول المتاحة",
    # EN with emoji (old)
    "📮 Take Number", "💸 Balance", "🎁 Refer & Earn", "💰 Withdraw", "📊 Statistics", "❓ Countries",
    # AR with emoji (old)
    "📮 الحصول على رقم", "💸 الرصيد", "🎁 شارك واربح", "💰 سحب الرصيد", "📊 الإحصائيات", "❓ الدول المتاحة",
    # AR with new emoji
    "📲 الحصول على رقم", "💰 الرصيد", "🎁 شارك واربح", "💸 سحب الرصيد", "📊 الإحصائيات", "🌍 الدول المتاحة",
    # EN with new emoji
    "📲 Take Number", "💰 Balance", "🎁 Refer & Earn", "💸 Withdraw", "📊 Statistics", "🌍 Countries",
    # Legacy
    "Take a number", "Statistics", "Status", "Available/countries",
    "Available countries", "Added/country",
    "Balance", "Refer", "🔗 Refer", "Withdraw",
    "💵 Balance", "💸 Withdraw",
    "Referral", "💜 Referral", "Invite", "💜 Invite",
    "My Rewards", "🏆 My Rewards",
    "Support", "👨‍💻 Support",
    "احصل على رقم", "إحصائياتي", "الدول المتاحة",
    " Take a number", " Statistics", " Status", " Available countries",
] or any(k in msg.text for k in ["Referral", "My Rewards", "Withdraw", "سحب", "Take a number", "Take Number", "Get Number", "Status", "Added/country", "Support", "Refer & Earn", "شارك واربح", "الرصيد", "Balance", "Statistics", "الإحصائيات", "Countries", "Available Country", "الدول المتاحة", "الحصول على رقم", "احصل على رقم", "Live Traffic", "حركة المرور", "حركه المرور"])))
def handle_keyboard_buttons(msg):
    user_id = msg.from_user.id
    if is_banned(user_id):
        return
    channels = check_subscription(user_id)

    if channels:
        send_subscription_message_with_image(msg.chat.id, user_id)
        return
    text = msg.text.strip()
    lang = get_user_language(user_id)

    # Take Number / Get Number / الحصول على رقم
    if any(k in text for k in [
        "Take Number", "Get Number", "الحصول على رقم",
        "📮 Take Number", "📮 الحصول على رقم",
        "📲 الحصول على رقم", "📲 Take Number",
        "Take a number", "احصل على رقم",
        "Получить номер", "নম্বর নিন"
    ]):
        markup = get_country_buttons_all(user_id)
        lang = get_user_language(user_id)
        service_text = "❓ <b>Select a Service:</b>" if lang != "ar" else "❓ <b>اختر خدمة:</b>"
        if markup:
            bot.send_message(msg.chat.id, service_text, parse_mode="HTML", reply_markup=markup)
        else:
            welcome_text = get_welcome_text(user_id)
            bot.send_message(msg.chat.id, welcome_text, parse_mode="HTML")
        return

    # Balance / الرصيد
    elif any(k in text for k in ["Balance", "الرصيد"]) and not any(k in text for k in ["Refer", "Earn", "شارك"]):
        _send_balance(msg.chat.id, user_id)
        return

    # Withdraw / سحب الرصيد
    elif any(k in text for k in ["Withdraw", "سحب الرصيد", "سحب"]):
        withdraw_keyboard_handler(msg)
        return

    # Statistics / Status / الإحصائيات
    elif any(k in text for k in [
        "Statistics", "Status", "الإحصائيات", "إحصائياتي",
        "📊 الإحصائيات", "📊 Statistics", "Статистика", "পরিসংখ্যান"
    ]):
        _send_stat(msg.chat.id, user_id)
        return

    # Countries / Available Country / الدول المتاحة
    elif any(k in text for k in [
        "Countries", "Available Country", "Available countries",
        "الدول المتاحة", "🌍 الدول المتاحة", "🌍 Countries",
        "Доступные страны", "দেশসমূহ"
    ]):
        _send_available_countries(msg)
        return

    # Live Traffic / حركة المرور
    elif any(k in text for k in ["Live Traffic", "live traffic", "حركة المرور", "حركه المرور"]):
        _send_live_traffic(msg.chat.id, user_id)
        return

    # Refer & Earn / شارك واربح
    elif any(k in text for k in ["Refer", "شارك واربح", "Referral", "Invite", "My Rewards"]):
        _send_refer(msg.chat.id, user_id)
        return

    # Support
    elif "Support" in text:
        _send_support_msg(msg.chat.id)
        return

    # My account ID
    elif "ID - Prefix" in text:
        my_account_id_handler(msg)
        return




def _send_support_msg(chat_id):
    text = (
        "═══《 <tg-emoji emoji-id='5287598387737147554'>👨‍💻</tg-emoji> SUPPORT CENTER 》═══\n\n"
        "<tg-emoji emoji-id='4981190601887188725'>🔴</tg-emoji><b> Need help? We're here for you</b>\n\n"
        "<tg-emoji emoji-id='4981190601887188725'>🔴</tg-emoji> <b>Contact:</b> @Yasin_to_supportBot\n\n"
        "<tg-emoji emoji-id='4981190601887188725'>🔴</tg-emoji> <b>For any issues or questions, feel free to reach out anytime </b>"
        "<b><tg-emoji emoji-id='5443038326535759644'>💬</tg-emoji></b>"
    )
    bot.send_message(chat_id, text, parse_mode="HTML")


def _send_live_traffic(chat_id, user_id=None):
    """إرسال رسالة Live Traffic زي الصورة"""
    total, results_pct, country_pcts, top_country = get_live_traffic_stats(minutes=5)

    # رموز الأرقام ١-١٠
    num_emojis = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

    lines = []
    lines.append("<tg-emoji emoji-id='5282843764451376242'>🟢</tg-emoji> <b>Live Traffic</b>\n")
    lines.append(f"📅 <b>Window:</b> Last 5 minutes")
    lines.append(f"✅ <b>Results Sent:</b> {results_pct}%")

    if top_country:
        top_flag = get_country_flags(top_country)
        lines.append(f"🏆 <b>Top Country:</b> {top_flag} {top_country}\n")
    else:
        lines.append(f"🏆 <b>Top Country:</b> —\n")

    lines.append("🌍 <b>Top Countries:</b>")

    if country_pcts:
        for i, (cname, pct) in enumerate(country_pcts[:10]):
            emoji_num = num_emojis[i] if i < len(num_emojis) else f"{i+1}."
            flag = get_country_flags(cname)
            lines.append(f"{emoji_num} {flag} {cname} → {pct}%")
    else:
        lines.append("📭 No data yet in the last 5 minutes")

    text = "\n".join(lines)

    # زر Refresh
    mu = InlineKeyboardMarkup()
    try:
        mu.add(InlineKeyboardButton(
            "🔄 Refresh",
            callback_data="live_traffic_refresh",
            style="success"
        ))
    except:
        mu.add(InlineKeyboardButton("🔄 Refresh", callback_data="live_traffic_refresh"))

    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=mu)


@bot.callback_query_handler(func=lambda call: call.data == "live_traffic_refresh")
def live_traffic_refresh_cb(call):
    user_id = call.from_user.id
    if is_banned(user_id):
        bot.answer_callback_query(call.id)
        return
    bot.answer_callback_query(call.id, "🔄 Refreshing...")

    total, results_pct, country_pcts, top_country = get_live_traffic_stats(minutes=5)

    num_emojis = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

    lines = []
    lines.append("<tg-emoji emoji-id='5282843764451376242'>🟢</tg-emoji> <b>Live Traffic</b>\n")
    lines.append(f"📅 <b>Window:</b> Last 5 minutes")
    lines.append(f"✅ <b>Results Sent:</b> {results_pct}%")

    if top_country:
        top_flag = get_country_flags(top_country)
        lines.append(f"🏆 <b>Top Country:</b> {top_flag} {top_country}\n")
    else:
        lines.append(f"🏆 <b>Top Country:</b> —\n")

    lines.append("🌍 <b>Top Countries:</b>")

    if country_pcts:
        for i, (cname, pct) in enumerate(country_pcts[:10]):
            emoji_num = num_emojis[i] if i < len(num_emojis) else f"{i+1}."
            flag = get_country_flags(cname)
            lines.append(f"{emoji_num} {flag} {cname} → {pct}%")
    else:
        lines.append("📭 No data yet in the last 5 minutes")

    text = "\n".join(lines)

    mu = InlineKeyboardMarkup()
    try:
        mu.add(InlineKeyboardButton(
            "🔄 Refresh",
            callback_data="live_traffic_refresh",
            style="success"
        ))
    except:
        mu.add(InlineKeyboardButton("🔄 Refresh", callback_data="live_traffic_refresh"))

    try:
        bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id,
            parse_mode="HTML", reply_markup=mu
        )
    except Exception:
        bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=mu)




def setlang_cb(call):
    bot.answer_callback_query(call.id)
    # Language change disabled
    user_id = call.from_user.id
    lang = call.data.replace("setlang_", "")
    if lang not in ("en","ru","bn","ar"): lang = "en"
    USERS.setdefault(str(user_id), {})
    USERS[str(user_id)]["language"] = lang
    save_users()

    # رسالة تأكيد تغيير اللغة
    lang_changed_msgs = {
        "en": "<tg-emoji emoji-id='5273806972871787310'>✅</tg-emoji><b> Language changed to English</b> <tg-emoji emoji-id='5447183459602669338'>🔽</tg-emoji>",
        "ar": "<tg-emoji emoji-id='5273806972871787310'>✅</tg-emoji><b> تم تغيير اللغة إلى العربية</b> <tg-emoji emoji-id='5447183459602669338'>🔽</tg-emoji>",
        "ru": "<tg-emoji emoji-id='5273806972871787310'>✅</tg-emoji><b> Язык изменён на Русский</b> <tg-emoji emoji-id='5447183459602669338'>🔽</tg-emoji>",
        "bn": "<tg-emoji emoji-id='5273806972871787310'>✅</tg-emoji><b> ভাষা বাংলায় পরিবর্তিত হয়েছে</b> <tg-emoji emoji-id='5447183459602669338'>🔽</tg-emoji>",
    }
    bot.answer_callback_query(call.id, "✅", show_alert=False)
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

    channels = check_subscription(user_id)

    if channels:
        send_subscription_message_with_image(call.message.chat.id, user_id)
        return
    if is_admin(user_id):
        bot.send_message(call.message.chat.id, "🎛 <b>Admin Panel</b>", parse_mode="HTML", reply_markup=get_admin_menu())
        return

    # إرسال رسالة تغيير اللغة + الأزرار الأرضية
    lang_msg = lang_changed_msgs.get(lang, lang_changed_msgs["en"])
    bot.send_message(call.message.chat.id, lang_msg, parse_mode="HTML", reply_markup=get_main_reply_keyboard(user_id))
    USERS.setdefault(str(user_id), {})
    USERS[str(user_id)]["welcome_shown"] = True
    save_users()
    # إرسال المنصات/الدول بعد الأزرار الأرضية
    markup2 = get_country_buttons_all(user_id)
    welcome2 = get_welcome_text(user_id)
    if markup2:
        bot.send_message(call.message.chat.id, welcome2, parse_mode="HTML", reply_markup=markup2)


def my_lang_keyboard_handler(msg):
    pass



@bot.message_handler(func=lambda msg: msg.chat.type == "private" and msg.text and "ID - Prefix" in msg.text)
def my_account_id_handler(msg):
    user_id = msg.from_user.id
    if is_banned(user_id):
        return
    channels = check_subscription(user_id)

    if channels:
        send_subscription_message_with_image(msg.chat.id, user_id)
        return
    bot_uid = get_user_bot_id(user_id)
    # رسالة أولى
    bot.send_message(msg.chat.id,
        "<b><tg-emoji emoji-id='5273806972871787310'>✅</tg-emoji></b>"
        "<b> Prefix has been started</b>",
        parse_mode="HTML")
    # رسالة ثانية
    bot.send_message(msg.chat.id,
        f"The prefix was started <tg-emoji emoji-id='5273806972871787310'>✅</tg-emoji>\n"
        f"Look below<tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>\n"
        f"<blockquote>ID - Prefix: {bot_uid}</blockquote>",
        parse_mode="HTML")

@bot.message_handler(content_types=["text", "document", "photo", "video", "audio", "voice", "sticker"])
def handle_messages(msg):
    user_id = msg.from_user.id
    
    if msg.chat.type != "private":
        return

    # تجاهل الأوامر - تُعالج بواسطة handlers الخاصة بها
    if msg.content_type == "text" and msg.text and msg.text.startswith("/"):
        return

    # ═══ معالجة الكيبورد الأرضي (MODY default layout) ═══
    # تجاهل الـ layout check لو الأدمن/المستخدم في حالة انتظار إدخال
    if msg.content_type == "text" and msg.text and get_bot_layout() == "default" and user_id not in user_states:
        txt = msg.text.strip()
        if is_banned(user_id):
            return
        # تحقق من الاشتراك لكل الأزرار قبل أي شيء
        channels = check_subscription(user_id)

        if channels:
            send_subscription_message_with_image(msg.chat.id, user_id)
            return
        STATS_KEYWORDS    = ["Statistics", "Status", "الإحصائيات", "إحصائياتي", "Статистика", "পরিসংখ্যান"]

        if any(k in txt for k in STATS_KEYWORDS):
            _send_stat(msg.chat.id, user_id)
            return
        elif txt == "Clear Prefix":
            _clear_prefix(msg.chat.id, user_id)
            return
        elif "ID - Prefix" in txt:
            my_account_id_handler(msg)
            return
        elif txt == "My Balance":
            _send_amount(msg.chat.id, user_id)
            return
        elif txt == "Withdraw":
            _send_withdraw(msg.chat.id, user_id)
            return
        elif any(x in txt for x in ["My account", "My Account", "👤"]):
            return

    if user_id not in user_states and user_id not in broadcast_state:
        return

    state = user_states.get(user_id, {})
    action = state.get("action")
    
    # تحويل لـ handler المنصات لو الأدمن في وضع تعيين رسالة ترحيب
    if action in ("plt_welcome_msg", "plt_welcome_confirm_pending"):
        plt_welcome_text_handler(msg)
        return
    mode = state.get("mode")
    
    if mode == "add_numbers_admin":
        if msg.content_type != "text":
            bot.reply_to(msg, "❌ يرجى إرسال معرف رقمي!")
            return
        
        try:
            new_admin_id = int(msg.text.strip())
        except ValueError:
            bot.reply_to(msg, "❌ المعرف يجب أن يكون رقماً!")
            return
        
        if new_admin_id in NUMBERS_ADMINS:
            bot.reply_to(msg, "⚠️ هذا المستخدم أدمن أرقام بالفعل!")
        else:
            NUMBERS_ADMINS.append(new_admin_id)
            save_numbers_admins()
            bot.reply_to(msg, f"✅ تم إضافة <code>{new_admin_id}</code> كأدمن أرقام!", parse_mode="HTML")
        
        del user_states[user_id]
        return
    
    elif action == "na_add_country_edit_name_input":
        new_name = msg.text.strip()
        if not new_name:
            bot.reply_to(msg, "❌ يرجى إرسال اسم صالح!")
            return
        
        state["country_name"] = new_name
        
        lang = get_user_language(user_id)
        markup = InlineKeyboardMarkup(row_width=2)
        platforms = ["Facebook", "WhatsApp", "Telegram", "Instagram", "Twitter", "TikTok", "Discord", "Gmail"]
        for p in platforms:
            prefix = "✅ " if p in state.get("selected_platforms", []) else ""
            markup.add(InlineKeyboardButton(f"{prefix}{p}", callback_data=f"na_add_country_plt_{p}"))
        
        edit_name_text = "✏️ تعديل الاسم" if lang == "ar" else "✏️ Edit Name"
        confirm_text = "✅ إكمال" if lang == "ar" else "✅ Continue"
        
        markup.add(
            InlineKeyboardButton(edit_name_text, callback_data="na_add_country_edit_name"),
            InlineKeyboardButton(confirm_text, callback_data="na_add_country_finish")
        )
        
        bot.send_message(
            msg.chat.id,
            f"✅ تم تحديث الاسم إلى: <b>{new_name}</b>\n\n"
            f"📱 اختر المنصات التي تعمل عليها هذه الأرقام:",
            parse_mode="HTML",
            reply_markup=markup
        )
        state["action"] = "na_add_country_platforms"
        return

    elif action == "na_add_country_display_name":
        if msg.content_type != "text":
            bot.reply_to(msg, "❌ Send a text name!")
            return
        display_name = msg.text.strip()
        if not display_name or len(display_name) < 1:
            bot.reply_to(msg, "❌ Name is empty!")
            return
        # Check if admin included [count] in name
        count_match = re.search(r'\[(\d+)\]', display_name)
        if count_match:
            state["admin_count"] = int(count_match.group(1))
            display_name = display_name[:display_name.rfind('[')].strip()
        state["country_name"] = display_name
        state["action"] = "na_add_country_pick_platform"
        user_states[user_id] = state
        _ask_platform_or_server(msg.chat.id, user_id, state)
        return

    elif action == "na_add_country_paste":
        if msg.content_type != "text":
            bot.reply_to(msg, "❌ يرجى إرسال الأرقام كنص!")
            return
        
        text = msg.text.strip()
        numbers_raw = re.findall(r'\d+', text)
        
        if not numbers_raw:
            bot.reply_to(msg, "❌ لم يتم العثور على أرقام في النص المرسل!")
            return
        
        
        guessed_code = ""
        
        first_num_digits = "".join(filter(str.isdigit, numbers_raw[0])) if numbers_raw else ""
        
        if first_num_digits:
           
            for length in [3, 2, 1]:
                prefix = first_num_digits[:length]
               
                if prefix in ["966", "971", "965", "974", "973", "968", "212", "213", "216", "961", "962", "963", "964", "967", "249", "218", "222", "20", "7", "1", "44"]:
                    guessed_code = prefix
                    break
            if not guessed_code:
                guessed_code = first_num_digits[:2] 
        else:
            guessed_code = "218" 

        temp_filename = f"temp_{uuid.uuid4().hex[:8]}.txt"
        with open(temp_filename, "w", encoding="utf-8") as f:
            for num in numbers_raw:
                if len(num) >= 8:
                    f.write(num + "\n")
        
    
        state = {"temp_file": temp_filename, "paste_mode": True}
        process_country_code_logic(msg, user_id, guessed_code, state)
        return
    
    elif action == "na_add_country_file":
        if msg.content_type != "document":
            bot.reply_to(msg, "❌ يرجى إرسال ملف txt!")
            return

        try:
            file_info = bot.get_file(msg.document.file_id)
            if not file_info.file_path:
                bot.reply_to(msg, "❌ خطأ في تحميل الملف!")
                return
            downloaded_file = bot.download_file(file_info.file_path)
        except Exception as e:
            bot.reply_to(msg, f"❌ خطأ في تحميل الملف: {e}")
            return

        temp_filename = f"temp_{uuid.uuid4().hex[:8]}.txt"
        with open(temp_filename, "wb") as f:
            f.write(downloaded_file)

        
        try:
            with open(temp_filename, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                
                all_numbers = re.findall(r'\d+', content)
                if all_numbers:
                   
                    likely_phones = [n for n in all_numbers if 8 <= len(n) <= 15]
                    if likely_phones:
                        
                        prefixes = {}
                        for num in likely_phones:
                           
                            for i in range(1, 4):
                                if len(num) > i:
                                    pref = num[:i]
                                    prefixes[pref] = prefixes.get(pref, 0) + 1
                        
                        
                        sorted_prefixes = sorted(prefixes.items(), key=lambda x: (x[1], len(x[0])), reverse=True)
                        guessed_code = sorted_prefixes[0][0] if sorted_prefixes else "20"
                    else:
                        guessed_code = "20"
                else:
                    guessed_code = "20"
        except Exception as e:
            print(f"Error guessing code: {e}")
            guessed_code = "20"

        state = {"temp_file": temp_filename}
        process_country_code_logic(msg, user_id, guessed_code, state)
        return

    elif action == "na_add_country_code":
        country_code = msg.text.strip()
        process_country_code_logic(msg, user_id, country_code, state)
        return

    elif action == "na_add_country_name":
        country_name = msg.text.strip()
        numbers_file = state.get("numbers_file")
        country_code = state.get("country_code")
        num_cleaned = state.get("num_cleaned")

        user_states[user_id] = {
            "action": "na_add_country_server",
            "numbers_file": numbers_file,
            "country_code": country_code,
            "country_name": country_name,
            "num_cleaned": num_cleaned,
            "selected_platforms": []
        }
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🏢 GROUP", callback_data="na_add_country_srv_GROUP"),
            InlineKeyboardButton("🔷 Fly sms", callback_data="na_add_country_srv_Fly sms")
        )
        markup.add(
            InlineKeyboardButton("🏢 hadi", callback_data="na_add_country_srv_hadi"),
            InlineKeyboardButton("🔷 fire", callback_data="na_add_country_srv_fire")
        )
        markup.add(
            InlineKeyboardButton("📱 Number Panel", callback_data="na_add_country_srv_Number_Panel"),
            InlineKeyboardButton("⚡ Bolt", callback_data="na_add_country_srv_Bolt")
        )
        markup.add(
            InlineKeyboardButton("🌐 iVASMS", callback_data="na_add_country_srv_iVASMS"),
            InlineKeyboardButton("🔵 MSI", callback_data="na_add_country_srv_MSI")
        )
        markup.add(
            InlineKeyboardButton("🟣 proton SMS", callback_data="na_add_country_srv_proton SMS"),
            InlineKeyboardButton("🌐 IMS", callback_data="na_add_country_srv_IMS")
        )
        markup.add(
            InlineKeyboardButton("🌸 Roxy SMS", callback_data="na_add_country_srv_Roxy SMS"),
            InlineKeyboardButton("🆕 TimeSMS", callback_data="na_add_country_srv_TimeSMS")
        )
        markup.add(InlineKeyboardButton("🔗 Konekta", callback_data="na_add_country_srv_Konekta"))
        markup.add(InlineKeyboardButton("📡 Seven1Tel", callback_data="na_add_country_srv_Seven1Tel"))
        markup.add(InlineKeyboardButton("🕊 Gaza SMS", callback_data="na_add_country_srv_Gaza SMS"))
        markup.add(InlineKeyboardButton("📶 Km sms", callback_data="na_add_country_srv_Km sms"))
        markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="numbers_admin_panel"))

        bot.reply_to(
            msg,
            f"✅ <b>الخطوة 3/4 - اختيار السيرفر</b>\n\n"
            f"🌍 الدولة: <b>{country_name}</b>\n"
            f"🔢 رمز الدولة: <b>{country_code}</b>\n"
            f"📊 عدد الأرقام: <b>{num_cleaned}</b>\n\n"
            f"🖥️ <b>اختر السيرفر الذي تنتمي إليه هذه الأرقام:</b>",
            parse_mode="HTML",
            reply_markup=markup
        )
        return
    
    elif mode == "na_ban_user":
        if msg.content_type != "text":
            bot.reply_to(msg, "❌ يرجى إرسال معرف رقمي!")
            return
        
        try:
            ban_id = int(msg.text.strip())
        except ValueError:
            bot.reply_to(msg, "❌ المعرف يجب أن يكون رقماً!")
            return
        
        if ban_id in BANNED:
            bot.reply_to(msg, "⚠️ هذا المستخدم محظور بالفعل!")
        else:
            BANNED.append(ban_id)
            save_banned()
            bot.reply_to(msg, f"✅ تم حظر المستخدم <code>{ban_id}</code>!", parse_mode="HTML")
        
        del user_states[user_id]
        return
    
    elif mode == "na_unban_user":
        if msg.content_type != "text":
            bot.reply_to(msg, "❌ يرجى إرسال معرف رقمي!")
            return
        
        try:
            unban_id = int(msg.text.strip())
        except ValueError:
            bot.reply_to(msg, "❌ المعرف يجب أن يكون رقماً!")
            return
        
        if unban_id not in BANNED:
            bot.reply_to(msg, "⚠️ هذا المستخدم غير محظور!")
        else:
            BANNED.remove(unban_id)
            save_banned()
            bot.reply_to(msg, f"✅ تم إلغاء حظر المستخدم <code>{unban_id}</code>!", parse_mode="HTML")
        
        del user_states[user_id]
        return
    
    if user_id in broadcast_state:
        bc_mode = broadcast_state[user_id].get("mode")
        
        if bc_mode == "na_global_broadcast":
            success = 0
            failed = 0
            
            for uid in USERS.keys():
                try:
                    bot.copy_message(int(uid), msg.chat.id, msg.message_id)
                    success += 1
                except:
                    failed += 1
            
            bot.reply_to(msg, f"✅ تم إرسال الإذاعة الشاملة!\n\n📊 نجح: {success}\n❌ فشل: {failed}")
            del broadcast_state[user_id]
            return

    elif action == "na_add_country_file":
        if msg.content_type != "document":
            bot.reply_to(msg, "❌ يرجى إرسال ملف txt!")
            return

        try:
            file_info = bot.get_file(msg.document.file_id)
            if not file_info.file_path:
                bot.reply_to(msg, "❌ خطأ في تحميل الملف!")
                return
            downloaded_file = bot.download_file(file_info.file_path)
        except Exception as e:
            bot.reply_to(msg, f"❌ خطأ في تحميل الملف: {e}")
            return

        temp_filename = f"temp_{uuid.uuid4().hex[:8]}.txt"

        with open(temp_filename, "wb") as f:
            f.write(downloaded_file)

        user_states[user_id] = {"action": "na_add_country_code", "temp_file": temp_filename}

        bot.reply_to(
            msg,
            "✅ <b>تم رفع الملف بنجاح!</b>\n\n"
            "📝 <b>الخطوة 2/4</b>\n\n"
            "أرسل رمز الدولة (مثال: 20 لمصر، 7 لروسيا، 966 للسعودية)\n\n"
            "<i>سيتم الاحتفاظ فقط بالأرقام التي تبدأ برمز الدولة هذا</i>",
            parse_mode="HTML"
        )
        return

    elif action == "na_add_country_name":
        country_name = msg.text.strip()
        numbers_file = state.get("numbers_file")
        country_code = state.get("country_code")
        num_cleaned = state.get("num_cleaned")

        user_states[user_id] = {
            "action": "na_add_country_server",
            "numbers_file": numbers_file,
            "country_code": country_code,
            "country_name": country_name,
            "num_cleaned": num_cleaned,
            "selected_platforms": []
        }
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🏢 GROUP", callback_data="na_add_country_srv_GROUP"),
            InlineKeyboardButton("🔷 Fly sms", callback_data="na_add_country_srv_Fly sms")
        )
        markup.add(
            InlineKeyboardButton("🏢 hadi", callback_data="na_add_country_srv_hadi"),
            InlineKeyboardButton("🔷 fire", callback_data="na_add_country_srv_fire")
        )
        markup.add(
            InlineKeyboardButton("📱 Number Panel", callback_data="na_add_country_srv_Number_Panel"),
            InlineKeyboardButton("⚡ Bolt", callback_data="na_add_country_srv_Bolt")
        )
        markup.add(
            InlineKeyboardButton("🌐 iVASMS", callback_data="na_add_country_srv_iVASMS"),
            InlineKeyboardButton("🔵 MSI", callback_data="na_add_country_srv_MSI")
        )
        markup.add(
            InlineKeyboardButton("🟣 proton SMS", callback_data="na_add_country_srv_proton SMS"),
            InlineKeyboardButton("🌐 IMS", callback_data="na_add_country_srv_IMS")
        )
        markup.add(
            InlineKeyboardButton("🌸 Roxy SMS", callback_data="na_add_country_srv_Roxy SMS"),
            InlineKeyboardButton("🆕 TimeSMS", callback_data="na_add_country_srv_TimeSMS")
        )
        markup.add(InlineKeyboardButton("🔗 Konekta", callback_data="na_add_country_srv_Konekta"))
        markup.add(InlineKeyboardButton("📡 Seven1Tel", callback_data="na_add_country_srv_Seven1Tel"))
        markup.add(InlineKeyboardButton("🕊 Gaza SMS", callback_data="na_add_country_srv_Gaza SMS"))
        markup.add(InlineKeyboardButton("📶 Km sms", callback_data="na_add_country_srv_Km sms"))
        markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="numbers_admin_panel"))

        bot.reply_to(
            msg,
            f"✅ <b>الخطوة 3/4 - اختيار السيرفر</b>\n\n"
            f"🌍 الدولة: <b>{country_name}</b>\n"
            f"🔢 رمز الدولة: <b>{country_code}</b>\n"
            f"📊 عدد الأرقام: <b>{num_cleaned}</b>\n\n"
            f"🖥️ <b>اختر السيرفر الذي تنتمي إليه هذه الأرقام:</b>",
            parse_mode="HTML",
            reply_markup=markup
        )
        return

    elif action == "remove_country":
        country_name = msg.text.strip()

        if country_name in COUNTRIES:
            country_data = COUNTRIES[country_name]
            numbers_file = country_data.get("file", "")
            
            if numbers_file and os.path.exists(numbers_file):
                try:
                    os.remove(numbers_file)
                    print(f"🗑️ تم حذف ملف الأرقام: {numbers_file}")
                except Exception as e:
                    print(f"⚠️ خطأ في حذف ملف الأرقام {numbers_file}: {e}")
            
            del COUNTRIES[country_name]
            save_countries()
            del user_states[user_id]
            
            file_status = f"\n📄 تم حذف ملف الأرقام: {numbers_file}" if numbers_file else ""
            bot.reply_to(msg, f"✅ تم حذف الدولة: {country_name}{file_status}")
        else:
            bot.reply_to(msg, f"❌ الدولة غير موجودة: {country_name}")

    elif action == "add_channel":
        try:
            channel_input = msg.text.strip()
            if channel_input.startswith("https://t.me/"):
                channel_username = "@" + channel_input.replace("https://t.me/", "")
            elif channel_input.startswith("@"):
                channel_username = channel_input
            elif channel_input.startswith("-") or channel_input.isdigit():
                channel_username = channel_input
            else:
                channel_username = "@" + channel_input

            try:
                chat = bot.get_chat(channel_username)
                channel_id = chat.id
                
                if chat.username:
                    channel_url = f"https://t.me/{chat.username}"
                else:
                    channel_url = f"https://t.me/c/{str(channel_id)[4:]}/1"

                user_states[user_id] = {
                    "action": "add_channel_name_ar",
                    "channel_id": channel_id,
                    "channel_username": channel_username,
                    "channel_url": channel_url
                }
                bot.reply_to(msg, "📝 أرسل الآن اسم القناة الذي سيظهر على الزر (باللغة العربية):")
            except Exception as e:
                bot.reply_to(msg, f"❌ خطأ في الوصول للقناة: {e}\n\nتأكد أن:\n• البوت مشرف في القناة\n• الرابط أو المعرف صحيح")
        except Exception as e:
            bot.reply_to(msg, f"❌ خطأ: {e}")

    elif action == "add_channel_name_ar":
        name_ar = msg.text.strip()
        state["name_ar"] = name_ar
        user_states[user_id]["action"] = "add_channel_name_en"
        bot.reply_to(msg, "📝 أرسل الآن اسم القناة الذي سيظهر على الزر (باللغة الإنجليزية):")

    elif action == "add_channel_name_en":
        name_en = msg.text.strip()
        channel_id = state.get("channel_id")
        channel_username = state.get("channel_username")
        channel_url = state.get("channel_url")
        name_ar = state.get("name_ar")

        CHANNELS.append({
            "name": name_en, 
            "name_ar": name_ar,
            "name_en": name_en,
            "id": channel_id,
            "username": channel_username,
            "url": channel_url
        })
        save_channels()
        del user_states[user_id]

        bot.reply_to(
            msg,
            f"✅ <b>تم إضافة القناة بنجاح!</b>\n\n"
            f"📢 الاسم (عربي): {name_ar}\n"
            f"📢 الاسم (إنجليزي): {name_en}\n"
            f"🔗 المعرف: {channel_username}\n"
            f"🆔 ID: <code>{channel_id}</code>",
            parse_mode="HTML"
        )

    elif action == "remove_channel":
        try:
            index = int(msg.text.strip()) - 1

            if 0 <= index < len(CHANNELS):
                removed = CHANNELS.pop(index)
                save_channels()
                del user_states[user_id]
                bot.reply_to(msg, f"✅ تم حذف القناة: {removed['name']}")
            else:
                bot.reply_to(msg, "❌ رقم غير صحيح!")
        except ValueError:
            bot.reply_to(msg, "❌ يرجى إرسال رقم صحيح!")

    elif action == "add_admin":
        if user_id != MAIN_ADMIN_ID:
            bot.reply_to(msg, "❌ عذراً، المالك فقط يمكنه إضافة مشرفين!")
            return
        try:
            new_admin_id = int(msg.text.strip())

            if new_admin_id in ADMINS:
                bot.reply_to(msg, "⚠️ هذا المستخدم مشرف بالفعل!")
                return

            ADMINS.append(new_admin_id)
            save_admins()
            del user_states[user_id]
            bot.reply_to(msg, f"✅ تم إضافة المشرف بنجاح!\n\nID: <code>{new_admin_id}</code>", parse_mode="HTML")
        except ValueError:
            bot.reply_to(msg, "❌ ID غير صحيح!")

    elif action == "remove_admin":
        if user_id != MAIN_ADMIN_ID:
            bot.reply_to(msg, "❌ عذراً، المالك فقط يمكنه حذف مشرفين!")
            return
        try:
            target_id = int(msg.text.strip())
            if target_id == MAIN_ADMIN_ID:
                bot.reply_to(msg, "❌ لا يمكن حذف المشرف الأساسي (المالك)!")
                return
            
            if target_id in ADMINS:
                ADMINS.remove(target_id)
                save_admins()
                del user_states[user_id]
                bot.reply_to(msg, f"✅ تم حذف المشرف بنجاح!\n\nID: <code>{target_id}</code>", parse_mode="HTML")
            else:
                bot.reply_to(msg, "❌ هذا المستخدم ليس مشرفاً!")
        except ValueError:
            bot.reply_to(msg, "❌ ID غير صحيح!")

    elif action == "ban_user":
        try:
            ban_user_id = int(msg.text.strip())

            if ban_user_id in ADMINS:
                bot.reply_to(msg, "❌ لا يمكن حظر المشرفين!")
                return

            if ban_user_id in BANNED:
                bot.reply_to(msg, "⚠️ هذا المستخدم محظور بالفعل!")
                return

            BANNED.append(ban_user_id)
            save_banned()
            del user_states[user_id]
            bot.reply_to(msg, f"✅ تم حظر المستخدم!\n\nID: <code>{ban_user_id}</code>", parse_mode="HTML")
        except ValueError:
            bot.reply_to(msg, "❌ ID غير صحيح!")

    elif action == "unban_user":
        try:
            unban_user_id = int(msg.text.strip())

            if unban_user_id in BANNED:
                BANNED.remove(unban_user_id)
                save_banned()
                del user_states[user_id]
                bot.reply_to(msg, f"✅ تم إلغاء حظر المستخدم!\n\nID: <code>{unban_user_id}</code>", parse_mode="HTML")
            else:
                bot.reply_to(msg, "❌ هذا المستخدم غير محظور!")
        except ValueError:
            bot.reply_to(msg, "❌ ID غير صحيح!")

    elif action == "set_otp_group":
        global OTP_GROUP
        try:
            group_id = int(msg.text.strip())
            OTP_GROUP = group_id
            save_otp_group()
            del user_states[user_id]
            bot.reply_to(msg, f"✅ تم تعيين مجموعة OTP!\n\nID: <code>{group_id}</code>", parse_mode="HTML")
        except ValueError:
            bot.reply_to(msg, "❌ ID غير صحيح!")
    
    elif action == "edit_code_bonus":
        try:
            new_value = float(msg.text.strip())
            if new_value <= 0 or new_value > 10:
                bot.reply_to(msg, "❌ القيمة يجب أن تكون بين 0.01 و 10!")
                return
            settings = load_referral_settings()
            settings["code_bonus"] = new_value
            save_referral_settings(settings)
            del user_states[user_id]
            bot.reply_to(msg, f"✅ تم تحديث بونص الكود إلى <b>${new_value}</b>", parse_mode="HTML")
        except ValueError:
            bot.reply_to(msg, "❌ يرجى إدخال رقم صحيح!")
    
    elif action == "edit_referral_bonus":
        try:
            new_value = float(msg.text.strip())
            if new_value <= 0 or new_value > 100:
                bot.reply_to(msg, "❌ القيمة يجب أن تكون بين 0.01 و 100!")
                return
            settings = load_referral_settings()
            settings["referral_bonus"] = new_value
            save_referral_settings(settings)
            del user_states[user_id]
            bot.reply_to(msg, f"✅ تم تحديث بونص الإحالة إلى <b>${new_value}</b>", parse_mode="HTML")
        except ValueError:
            bot.reply_to(msg, "❌ يرجى إدخال رقم صحيح!")
    
    elif action == "edit_codes_required":
        try:
            new_value = int(msg.text.strip())
            if new_value < 1 or new_value > 100:
                bot.reply_to(msg, "❌ العدد يجب أن يكون بين 1 و 100!")
                return
            settings = load_referral_settings()
            settings["codes_required_for_referral"] = new_value
            save_referral_settings(settings)
            del user_states[user_id]
            bot.reply_to(msg, f"✅ تم تحديث عدد الأكواد المطلوبة إلى <b>{new_value}</b>", parse_mode="HTML")
        except ValueError:
            bot.reply_to(msg, "❌ يرجى إدخال رقم صحيح!")
    
    elif action == "edit_min_withdrawal":
        try:
            new_value = float(msg.text.strip())
            if new_value <= 0 or new_value > 1000:
                bot.reply_to(msg, "❌ القيمة يجب أن تكون بين 0.01 و 1000!")
                return
            settings = load_referral_settings()
            settings["min_withdrawal"] = new_value
            save_referral_settings(settings)
            del user_states[user_id]
            bot.reply_to(msg, f"✅ تم تحديث الحد الأدنى للسحب إلى <b>${new_value}</b>", parse_mode="HTML")
        except ValueError:
            bot.reply_to(msg, "❌ يرجى إدخال رقم صحيح!")
    
    elif action == "admin_add_balance":
        try:
            parts = msg.text.strip().split()
            if len(parts) != 2:
                bot.reply_to(msg, "❌ الصيغة غير صحيحة! استخدم: USER_ID AMOUNT")
                return
            target_user_id = int(parts[0])
            amount = float(parts[1])
            if amount <= 0 or amount > 10000:
                bot.reply_to(msg, "❌ المبلغ يجب أن يكون بين 0.01 و 10000!")
                return
            
            referrals_data = load_referrals()
            target_key = str(target_user_id)
            if target_key not in referrals_data:
                referrals_data[target_key] = {
                    "referred_by": None,
                    "referrals": [],
                    "active_referrals": 0,
                    "codes_received": 0,
                    "balance": 0.0,
                    "total_earned": 0.0
                }
            
            old_balance = referrals_data[target_key].get("balance", 0.0)
            referrals_data[target_key]["balance"] = old_balance + amount
            referrals_data[target_key]["total_earned"] = referrals_data[target_key].get("total_earned", 0.0) + amount
            save_referrals(referrals_data)
            del user_states[user_id]
            
            new_balance = referrals_data[target_key]["balance"]
            bot.reply_to(msg, f"✅ <b>تم إضافة الرصيد بنجاح!</b>\n\n👤 المستخدم: <code>{target_user_id}</code>\n💰 المبلغ المضاف: <b>${amount:.2f}</b>\n💵 الرصيد السابق: <b>${old_balance:.2f}</b>\n💵 الرصيد الجديد: <b>${new_balance:.2f}</b>", parse_mode="HTML")
            
            try:
                target_lang = get_user_language(target_user_id)
                if target_lang == "ar":
                    notify_msg = f"💰 <b>تم إضافة رصيد!</b>\n\nتم إضافة <b>${amount:.2f}</b> إلى رصيدك بواسطة الأدمن.\n💵 رصيدك الحالي: <b>${new_balance:.2f}</b>"
                else:
                    notify_msg = f"💰 <b>Balance Added!</b>\n\n<b>${amount:.2f}</b> has been added to your balance by admin.\n💵 Your current balance: <b>${new_balance:.2f}</b>"
                bot.send_message(target_user_id, notify_msg, parse_mode="HTML")
            except:
                pass
        except ValueError:
            bot.reply_to(msg, "❌ الصيغة غير صحيحة! استخدم: USER_ID AMOUNT\n\nمثال: 123456789 5.00")
    
    elif action == "admin_subtract_balance":
        try:
            parts = msg.text.strip().split()
            if len(parts) != 2:
                bot.reply_to(msg, "❌ الصيغة غير صحيحة! استخدم: USER_ID AMOUNT")
                return
            target_user_id = int(parts[0])
            amount = float(parts[1])
            if amount <= 0 or amount > 10000:
                bot.reply_to(msg, "❌ المبلغ يجب أن يكون بين 0.01 و 10000!")
                return
            
            referrals_data = load_referrals()
            target_key = str(target_user_id)
            if target_key not in referrals_data:
                bot.reply_to(msg, "❌ المستخدم غير موجود في نظام الإحالات!")
                del user_states[user_id]
                return
            
            old_balance = referrals_data[target_key].get("balance", 0.0)
            if amount > old_balance:
                bot.reply_to(msg, f"❌ رصيد المستخدم غير كافي!\n💵 رصيده الحالي: ${old_balance:.2f}")
                return
            
            referrals_data[target_key]["balance"] = old_balance - amount
            save_referrals(referrals_data)
            del user_states[user_id]
            
            new_balance = referrals_data[target_key]["balance"]
            bot.reply_to(msg, f"✅ <b>تم خصم الرصيد بنجاح!</b>\n\n👤 المستخدم: <code>{target_user_id}</code>\n💰 المبلغ المخصوم: <b>${amount:.2f}</b>\n💵 الرصيد السابق: <b>${old_balance:.2f}</b>\n💵 الرصيد الجديد: <b>${new_balance:.2f}</b>", parse_mode="HTML")
            
            try:
                target_lang = get_user_language(target_user_id)
                if target_lang == "ar":
                    notify_msg = f"⚠️ <b>تم خصم رصيد!</b>\n\nتم خصم <b>${amount:.2f}</b> من رصيدك بواسطة الأدمن.\n💵 رصيدك الحالي: <b>${new_balance:.2f}</b>"
                else:
                    notify_msg = f"⚠️ <b>Balance Deducted!</b>\n\n<b>${amount:.2f}</b> has been deducted from your balance by admin.\n💵 Your current balance: <b>${new_balance:.2f}</b>"
                bot.send_message(target_user_id, notify_msg, parse_mode="HTML")
            except:
                pass
        except ValueError:
            bot.reply_to(msg, "❌ الصيغة غير صحيحة! استخدم: USER_ID AMOUNT\n\nمثال: 123456789 5.00")
    
    elif action == "edit_main_welcome":
        # Accept message with tg-emoji entities
        if msg.content_type == "text":
            # Try to get HTML text including entities
            new_msg = msg.html_text if hasattr(msg, 'html_text') and msg.html_text else msg.text
        else:
            new_msg = msg.text or ""
        if not new_msg or len(new_msg.strip()) < 1:
            bot.reply_to(msg, "❌ الرسالة فارغة!")
            return
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("✅ تأكيد تعيين رسالة الترحيب", callback_data="confirm_main_welcome"))
        markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="admin"))
        user_states[user_id]["pending_welcome"] = new_msg
        user_states[user_id]["action"] = "confirm_main_welcome"
        bot.reply_to(msg, "✅ هذه الرسالة ستظهر فوق الخدمات — تأكيد؟", reply_markup=markup)
        return

    elif action == "edit_welcome_ar":
        new_message = msg.text.strip() if msg.text else ""
        if len(new_message) < 2:
            bot.reply_to(msg, "❌ الرسالة قصيرة جداً!")
            return
        messages = load_welcome_messages()
        messages["ar"] = new_message
        save_welcome_messages(messages)
        del user_states[user_id]
        bot.reply_to(msg, "✅ تم تحديث رسالة الترحيب العربية!")
    
    elif action == "edit_welcome_en":
        new_message = msg.text.strip() if msg.text else ""
        if len(new_message) < 2:
            bot.reply_to(msg, "❌ Message is too short!")
            return
        messages = load_welcome_messages()
        messages["en"] = new_message
        save_welcome_messages(messages)
        del user_states[user_id]
        bot.reply_to(msg, "✅ English welcome message updated!")
    
    elif action and action.startswith("edit_button_link_"):
        link_key = action.replace("edit_button_link_", "")
        new_link = msg.text.strip()
        if not new_link.startswith("https://"):
            bot.reply_to(msg, "❌ الرابط يجب أن يبدأ بـ https://\n❌ Link must start with https://")
            return
        links = load_button_links()
        links[link_key] = new_link
        save_button_links(links)
        del user_states[user_id]
        bot.reply_to(msg, f"✅ تم تحديث الرابط بنجاح!\n✅ Link updated successfully!\n\n🔗 {new_link}")
    
    elif action == "otp_btn_add_name":
        btn_name = msg.text.strip()
        if len(btn_name) < 1:
            bot.reply_to(msg, "❌ اسم الزر قصير جداً!")
            return
        user_states[user_id] = {"action": "otp_btn_add_url", "btn_name": btn_name}
        bot.reply_to(msg, f"✅ اسم الزر: <b>{btn_name}</b>\n\nالآن أرسل رابط الزر:\n(مثال: https://t.me/YourChannel)", parse_mode="HTML")
    
    elif action == "otp_btn_add_url":
        btn_url = msg.text.strip()
        if not btn_url.startswith("https://"):
            bot.reply_to(msg, "❌ الرابط يجب أن يبدأ بـ https://")
            return
        btn_name = state.get("btn_name", "Button")
        otp_buttons = load_otp_buttons()
        otp_buttons.append({"name": btn_name, "url": btn_url})
        save_otp_buttons(otp_buttons)
        del user_states[user_id]
        bot.reply_to(msg, f"✅ تم إضافة الزر بنجاح!\n\n📝 الاسم: <b>{btn_name}</b>\n🔗 الرابط: {btn_url}", parse_mode="HTML")
    
    elif action == "otp_btn_edit_name":
        btn_idx = state.get("btn_idx", 0)
        new_name = msg.text.strip()
        if len(new_name) < 1:
            bot.reply_to(msg, "❌ اسم الزر قصير جداً!")
            return
        otp_buttons = load_otp_buttons()
        if btn_idx < len(otp_buttons):
            otp_buttons[btn_idx]["name"] = new_name
            save_otp_buttons(otp_buttons)
            del user_states[user_id]
            bot.reply_to(msg, f"✅ تم تحديث اسم الزر إلى: <b>{new_name}</b>", parse_mode="HTML")
        else:
            bot.reply_to(msg, "❌ الزر غير موجود!")
            del user_states[user_id]
    
    elif action == "otp_btn_edit_url":
        btn_idx = state.get("btn_idx", 0)
        new_url = msg.text.strip()
        if not new_url.startswith("https://"):
            bot.reply_to(msg, "❌ الرابط يجب أن يبدأ بـ https://")
            return
        otp_buttons = load_otp_buttons()
        if btn_idx < len(otp_buttons):
            otp_buttons[btn_idx]["url"] = new_url
            save_otp_buttons(otp_buttons)
            del user_states[user_id]
            bot.reply_to(msg, f"✅ تم تحديث رابط الزر إلى:\n🔗 {new_url}", parse_mode="HTML")
        else:
            bot.reply_to(msg, "❌ الزر غير موجود!")
            del user_states[user_id]
    
    elif action == "withdraw_details":
        method = state.get("method", "Unknown")
        method_key = state.get("method_key", "unknown")
        details = msg.text.strip()
        lang = get_user_language(user_id)
        
        if len(details) < 5:
            msg_text = "❌ التفاصيل غير صحيحة!" if lang == "ar" else "❌ Invalid details!"
            bot.reply_to(msg, msg_text)
            return
        
        referral_data = get_user_referral_data(user_id)
        balance = referral_data.get("balance", 0.0)
        settings = load_referral_settings()
        min_withdrawal = settings.get("min_withdrawal", 5.0)
        
        if balance < min_withdrawal:
            msg_text = f"❌ رصيدك غير كافي! الحد الأدنى: ${min_withdrawal}" if lang == "ar" else f"❌ Insufficient balance! Minimum: ${min_withdrawal}"
            bot.reply_to(msg, msg_text)
            del user_states[user_id]
            return
        
        global REFERRALS
        REFERRALS = load_referrals()
        REFERRALS[str(user_id)]["balance"] = 0.0
        save_referrals(REFERRALS)
        
        request_id = str(uuid.uuid4())[:8]
        withdrawal_request = {
            "id": request_id,
            "user_id": user_id,
            "amount": balance,
            "method": method,
            "method_key": method_key,
            "details": details,
            "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "status": "pending"
        }
        
        requests_list = load_withdrawal_requests()
        requests_list.append(withdrawal_request)
        save_withdrawal_requests(requests_list)
        
        del user_states[user_id]
        
        if lang == "ar":
            bot.reply_to(
                msg,
                f"✅ <b>تم إرسال طلب السحب!</b>\n\n"
                f"🆔 رقم الطلب: <code>{request_id}</code>\n"
                f"💵 المبلغ: <b>${balance:.2f}</b>\n"
                f"📝 الطريقة: {method}\n"
                f"📋 التفاصيل: <code>{details}</code>\n\n"
                f"⏳ <b>الحالة:</b> قيد المعالجة\n"
                f"سيتم إشعارك عند الموافقة أو الرفض.",
                parse_mode="HTML"
            )
        else:
            bot.reply_to(
                msg,
                f"✅ <b>Withdrawal request submitted!</b>\n\n"
                f"🆔 Request ID: <code>{request_id}</code>\n"
                f"💵 Amount: <b>${balance:.2f}</b>\n"
                f"📝 Method: {method}\n"
                f"📋 Details: <code>{details}</code>\n\n"
                f"⏳ <b>Status:</b> Processing\n"
                f"You will be notified when approved or rejected.",
                parse_mode="HTML"
            )
        
        admin_markup = InlineKeyboardMarkup(row_width=2)
        admin_markup.add(
            InlineKeyboardButton("✅ تأكيد الدفع", callback_data=f"wd_approve_{request_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"wd_reject_{request_id}")
        )
        
        user_data_for_admin = USERS.get(str(user_id), {})
        user_referral_for_admin = get_user_referral_data(user_id)
        
        admin_join_date = user_data_for_admin.get("join_date", "غير محدد")
        admin_total_codes = user_data_for_admin.get("activations", 0)
        admin_total_referrals = len(user_referral_for_admin.get("referrals", []))
        admin_active_referrals = user_referral_for_admin.get("active_referrals", 0)
        admin_total_earned = user_referral_for_admin.get("total_earned", 0.0)
        
        admin_notification = (
            f"📋 <b>طلب سحب جديد!</b>\n\n"
            f"🆔 رقم الطلب: <code>{request_id}</code>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👤 <b>بيانات المستخدم:</b>\n"
            f"├ 🆔 ID: <code>{user_id}</code>\n"
            f"├ 📅 تاريخ الانضمام: {admin_join_date}\n"
            f"├ 📊 إجمالي الأكواد: {admin_total_codes}\n"
            f"├ 👥 إجمالي الإحالات: {admin_total_referrals}\n"
            f"├ ✅ إحالات نشطة: {admin_active_referrals}\n"
            f"└ 💰 إجمالي الأرباح: ${admin_total_earned:.2f}\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"💳 <b>تفاصيل السحب:</b>\n"
            f"├ 💵 المبلغ: <b>${balance:.2f}</b>\n"
            f"├ ?? الطريقة: {method}\n"
            f"└ 📋 التفاصيل: <code>{details}</code>\n\n"
            f"⏳ الحالة: قيد الانتظار"
        )
        
        for admin_id in ADMINS:
            try:
                bot.send_message(
                    admin_id,
                    admin_notification,
                    parse_mode="HTML",
                    reply_markup=admin_markup
                )
            except:
                pass
    

    elif action == "set_sub_image":
        url = msg.text.strip() if msg.content_type == "text" else ""
        # Check if it's a valid image URL
        valid_exts = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
        if not url.startswith("https://") or not any(e in url.lower() for e in valid_exts + ["image", "photo", "img", "pic"]):
            bot.reply_to(msg, "❌ الرابط غير صحيح! يجب أن يبدأ بـ https:// ويكون رابط صورة صحيح.")
            return
        # Test if image loads
        try:
            test_msg = bot.send_photo(msg.chat.id, url, caption="✅ <b>تم التحقق من الصورة!</b>\n\nالصورة ستظهر مع رسالة الاشتراك الإجباري.", parse_mode="HTML")
            save_subscription_image({"image_url": url})
            del user_states[user_id]
        except Exception as e:
            bot.reply_to(msg, f"❌ فشل تحميل الصورة: {e}\n\nتأكد من صحة الرابط.")
        return

    elif action == "set_sub_msg_text":
        # Accept any message content type including ones with special telegram reactions
        new_msg_text = msg.html_text if hasattr(msg, 'html_text') and msg.html_text else (msg.text or "")
        if not new_msg_text or len(new_msg_text) < 5:
            bot.reply_to(msg, "❌ الرسالة قصيرة جداً!")
            return
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("✅ تأكيد تعيين الرسالة", callback_data="confirm_sub_msg"))
        markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="admin"))
        
        user_states[user_id]["pending_sub_msg"] = new_msg_text
        user_states[user_id]["action"] = "confirm_sub_msg"
        
        bot.reply_to(msg, "📋 هذه هي الرسالة الجديدة — تأكيد التعيين؟", reply_markup=markup)
        return

    elif action == "set_sub_btn_text":
        new_btn_text = msg.text.strip() if msg.content_type == "text" else ""
        if not new_btn_text or len(new_btn_text) < 1:
            bot.reply_to(msg, "❌ الاسم قصير جداً!")
            return
        settings = load_subscription_settings()
        settings["button_text"] = new_btn_text
        save_subscription_settings(settings)
        del user_states[user_id]
        bot.reply_to(msg, f"✅ <b>تم تغيير اسم الزر إلى:</b> {new_btn_text}", parse_mode="HTML")
        return

    elif action == "change_site_username":
        global USERNAME, USERNAME2, USERNAME3
        site_key = state.get("site_key")
        account_id = state.get("account_id")
        new_username = msg.text.strip()
        
        accounts = get_site_accounts(site_key)
        account_found = False
        
        for idx, acc in enumerate(accounts):
            if acc.get("id") == account_id:
                accounts[idx]["username"] = new_username
                account_found = True
                
                if idx == 0:
                    if site_key == "GROUP":
                        USERNAME = new_username
                    elif site_key == "Fly sms":
                        USERNAME2 = new_username
                    elif site_key == "hadi":
                        USERNAME12 = new_username
                    elif site_key == "fire":
                        USERNAME13 = new_username
                    elif site_key == "Seven1Tel":
                        USERNAME14 = new_username
                    elif site_key == "Gaza SMS":
                        USERNAME15 = new_username
                    elif site_key == "Number_Panel":
                        USERNAME3 = new_username
                break
        
        if account_found:
            SETTINGS[site_key]["accounts"] = accounts
            save_settings(SETTINGS)
            
            del user_states[user_id]
            site_name = SETTINGS[site_key]["name"]
            bot.reply_to(
                msg,
                f"✅ <b>تم تحديث اليوزر - {site_name}</b>\n\n"
                f"👤 اليوزر الجديد: <code>{new_username}</code>",
                parse_mode="HTML"
            )
        else:
            bot.reply_to(msg, "❌ الحساب غير موجود!")
    
    elif action == "change_site_password":
        global PASSWORD, PASSWORD2, PASSWORD3
        site_key = state.get("site_key")
        account_id = state.get("account_id")
        new_password = msg.text.strip()
        
        accounts = get_site_accounts(site_key)
        account_found = False
        
        for idx, acc in enumerate(accounts):
            if acc.get("id") == account_id:
                accounts[idx]["password"] = new_password
                account_found = True
                
                if idx == 0:
                    if site_key == "GROUP":
                        PASSWORD = new_password
                    elif site_key == "Fly sms":
                        PASSWORD2 = new_password
                    elif site_key == "hadi":
                        PASSWORD12 = new_password
                    elif site_key == "fire":
                        PASSWORD13 = new_password
                    elif site_key == "Seven1Tel":
                        PASSWORD14 = new_password
                    elif site_key == "Gaza SMS":
                        PASSWORD15 = new_password
                    elif site_key == "Number_Panel":
                        PASSWORD3 = new_password
                break
        
        if account_found:
            SETTINGS[site_key]["accounts"] = accounts
            save_settings(SETTINGS)
            
            del user_states[user_id]
            site_name = SETTINGS[site_key]["name"]
            bot.reply_to(
                msg,
                f"✅ <b>تم تحديث الباسورد - {site_name}</b>\n\n"
                f"🔑 تم حفظ كلمة المرور الجديدة",
                parse_mode="HTML"
            )
        else:
            bot.reply_to(msg, "❌ الحساب غير موجود!")
    
    elif action == "add_account_username":
        site_key = state.get("site_key")
        site_name = SETTINGS[site_key]["name"]
        new_username = msg.text.strip()
        
        if not new_username:
            bot.reply_to(msg, "❌ اسم المستخدم لا يمكن أن يكون فارغاً!")
            return
        
        if site_key == "iVASMS":
            user_states[user_id] = {
                "action": "add_account_password",
                "site_key": site_key,
                "username": new_username
            }
            bot.reply_to(
                msg,
                f"➕ <b>إضافة حساب جديد - {site_name}</b>\n\n"
                f"✅ اليوزر: <code>{new_username}</code>\n\n"
                f"📝 الخطوة 2/3: أرسل كلمة المرور (Password):",
                parse_mode="HTML"
            )
        else:
            user_states[user_id] = {
                "action": "add_account_password",
                "site_key": site_key,
                "username": new_username
            }
            bot.reply_to(
                msg,
                f"➕ <b>إضافة حساب جديد - {site_name}</b>\n\n"
                f"✅ اليوزر: <code>{new_username}</code>\n\n"
                f"📝 الخطوة 2/2: أرسل كلمة المرور (Password):",
                parse_mode="HTML"
            )
    
    elif action == "add_account_password":
        site_key = state.get("site_key")
        site_name = SETTINGS[site_key]["name"]
        username = state.get("username")
        password = msg.text.strip()
        
        if not password:
            bot.reply_to(msg, "❌ كلمة المرور لا يمكن أن تكون فارغة!")
            return
        
        if site_key == "iVASMS":
            user_states[user_id] = {
                "action": "add_account_api_key",
                "site_key": site_key,
                "username": username,
                "password": password
            }
            bot.reply_to(
                msg,
                f"➕ <b>إضافة حساب جديد - {site_name}</b>\n\n"
                f"✅ اليوزر: <code>{username}</code>\n"
                f"✅ الباسورد: <code>{password}</code>\n\n"
                f"📝 الخطوة 3/3: أرسل مفتاح API (API Key):",
                parse_mode="HTML"
            )
            return
        
        new_account = add_account(site_key, username, password)
        
        if new_account:
            del user_states[user_id]
            
            if SETTINGS[site_key]["enabled"]:
                thread = Thread(target=start_monitoring_for_account, args=(site_key, new_account), daemon=True)
                thread.start()
                print(f"🚀 بدء مراقبة فورية للحساب الجديد: {username} ({site_name})")
                
                bot.reply_to(
                    msg,
                    f"✅ <b>تم إضافة الحساب بنجاح - {site_name}</b>\n\n"
                    f"👤 اليوزر: <code>{username}</code>\n"
                    f"🔑 الباسورد: <code>{password}</code>\n"
                    f"🆔 ID: <code>{new_account['id'][:8]}...</code>\n\n"
                    f"🚀 <b>تم بدء المراقبة فوراً!</b>",
                    parse_mode="HTML"
                )
            else:
                bot.reply_to(
                    msg,
                    f"✅ <b>تم إضافة الحساب بنجاح - {site_name}</b>\n\n"
                    f"👤 اليوزر: <code>{username}</code>\n"
                    f"🔑 الباسورد: <code>{password}</code>\n"
                    f"🆔 ID: <code>{new_account['id'][:8]}...</code>\n\n"
                    f"⚠️ الموقع غير مفعل حالياً",
                    parse_mode="HTML"
                )
        else:
            bot.reply_to(msg, "❌ فشل إضافة الحساب!")
    
    elif action == "add_account_api_key":
        site_key = state.get("site_key")
        site_name = SETTINGS[site_key]["name"]
        username = state.get("username")
        password = state.get("password")
        api_key = msg.text.strip()
        
        if not api_key:
            bot.reply_to(msg, "❌ مفتاح API لا يمكن أن يكون فارغاً!")
            return
        
        new_account = add_account(site_key, username, password)
        
        if new_account:
            for idx, acc in enumerate(SETTINGS[site_key]["accounts"]):
                if acc["id"] == new_account["id"]:
                    SETTINGS[site_key]["accounts"][idx]["api_key"] = api_key
                    save_settings(SETTINGS)
                    break
            
            del user_states[user_id]
            
            if SETTINGS[site_key]["enabled"]:
                new_account["api_key"] = api_key
                thread = Thread(target=start_monitoring_for_account, args=(site_key, new_account), daemon=True)
                thread.start()
                print(f"🚀 بدء مراقبة فورية للحساب الجديد: {username} ({site_name})")
                
                bot.reply_to(
                    msg,
                    f"✅ <b>تم إضافة الحساب بنجاح - {site_name}</b>\n\n"
                    f"👤 اليوزر: <code>{username}</code>\n"
                    f"🔑 الباسورد: <code>{password}</code>\n"
                    f"🔐 مفتاح API: <code>{api_key[:10]}...</code>\n"
                    f"🆔 ID: <code>{new_account['id'][:8]}...</code>\n\n"
                    f"🚀 <b>تم بدء المراقبة فوراً!</b>",
                    parse_mode="HTML"
                )
            else:
                bot.reply_to(
                    msg,
                    f"✅ <b>تم إضافة الحساب بنجاح - {site_name}</b>\n\n"
                    f"👤 اليوزر: <code>{username}</code>\n"
                    f"🔑 الباسورد: <code>{password}</code>\n"
                    f"🔐 مفتاح API: <code>{api_key[:10]}...</code>\n"
                    f"🆔 ID: <code>{new_account['id'][:8]}...</code>\n\n"
                    f"⚠️ الموقع غير مفعل حالياً",
                    parse_mode="HTML"
                )
        else:
            bot.reply_to(msg, "❌ فشل إضافة الحساب!")
    
    elif action == "change_site_interval":
        global CHECK_INTERVAL, CHECK_INTERVAL2, CHECK_INTERVAL3
        site_key = state.get("site_key")
        
        try:
            new_interval = int(msg.text.strip())
            
            if new_interval < 1 or new_interval > 300:
                bot.reply_to(msg, "❌ الفترة يجب أن تكون بين 1 و 300 ثانية!")
                return
            
            SETTINGS[site_key]["check_interval"] = new_interval
            save_settings(SETTINGS)
            
            if site_key == "GROUP":
                CHECK_INTERVAL = new_interval
            elif site_key == "Fly sms":
                CHECK_INTERVAL2 = new_interval
            elif site_key == "hadi":
                CHECK_INTERVAL12 = new_interval
            elif site_key == "fire":
                CHECK_INTERVAL13 = new_interval
            elif site_key == "Seven1Tel":
                CHECK_INTERVAL14 = new_interval
            elif site_key == "Gaza SMS":
                CHECK_INTERVAL15 = new_interval
            elif site_key == "Number_Panel":
                CHECK_INTERVAL3 = new_interval
            
            del user_states[user_id]
            site_name = SETTINGS[site_key]["name"]
            bot.reply_to(
                msg,
                f"✅ <b>تم تحديث فترة البحث - {site_name}</b>\n\n"
                f"⏱ الفترة الجديدة: {new_interval} ثانية\n\n"
                f"⚠️ سيتم تطبيق التغيير في الدورة القادمة",
                parse_mode="HTML"
            )
        except ValueError:
            bot.reply_to(msg, "❌ يرجى إدخال رقم صحيح!")
    
    elif action == "change_site_timeout":
        global HTTP_TIMEOUT, HTTP_TIMEOUT2, HTTP_TIMEOUT3
        site_key = state.get("site_key")
        
        try:
            new_timeout = int(msg.text.strip())
            
            if new_timeout < 5 or new_timeout > 300:
                bot.reply_to(msg, "❌ وقت الانتظار يجب أن يكون بين 5 و 300 ثانية!")
                return
            
            SETTINGS[site_key]["timeout"] = new_timeout
            save_settings(SETTINGS)
            
            if site_key == "GROUP":
                HTTP_TIMEOUT = new_timeout
            elif site_key == "Fly sms":
                HTTP_TIMEOUT2 = new_timeout
            elif site_key == "hadi":
                HTTP_TIMEOUT12 = new_timeout
            elif site_key == "fire":
                HTTP_TIMEOUT13 = new_timeout
            elif site_key == "Seven1Tel":
                HTTP_TIMEOUT14 = new_timeout
            elif site_key == "Gaza SMS":
                HTTP_TIMEOUT15 = new_timeout
            elif site_key == "Number_Panel":
                HTTP_TIMEOUT3 = new_timeout
            
            del user_states[user_id]
            site_name = SETTINGS[site_key]["name"]
            bot.reply_to(
                msg,
                f"✅ <b>تم تحديث وقت الانتظار - {site_name}</b>\n\n"
                f"⏳ الوقت الجديد: {new_timeout} ثانية",
                parse_mode="HTML"
            )
        except ValueError:
            bot.reply_to(msg, "❌ يرجى إدخال رقم صحيح!")
    
    elif action == "add_group":
        try:
            group_id = int(msg.text.strip())
            
            try:
                chat = bot.get_chat(group_id)
                admins = bot.get_chat_administrators(group_id)
                
                bot_is_admin = False
                for admin in admins:
                    if admin.user.id == bot.get_me().id:
                        bot_is_admin = True
                        break
                
                if not bot_is_admin:
                    bot.reply_to(msg, "❌ البوت ليس admin في هذا الجروب!")
                    return
                
                if group_id in GROUPS:
                    bot.reply_to(msg, "⚠️ هذا الجروب مضاف بالفعل!")
                    return
                
                GROUPS.append(group_id)
                save_groups()
                del user_states[user_id]
                
                bot.reply_to(
                    msg,
                    f"✅ <b>تم إضافة الجروب بنجاح!</b>\n\n"
                    f"📱 الاسم: <b>{chat.title}</b>\n"
                    f"🆔 ID: <code>{group_id}</code>",
                    parse_mode="HTML"
                )
            except Exception as e:
                bot.reply_to(msg, f"❌ خطأ: {e}\n\nتأكد أن:\n• البوت admin في الجروب\n• ID الجروب صحيح")
        except ValueError:
            bot.reply_to(msg, "❌ ID غير صحيح!")
    
    elif action == "remove_group":
        try:
            group_id = int(msg.text.strip())
            
            if group_id in GROUPS:
                GROUPS.remove(group_id)
                save_groups()
                del user_states[user_id]
                bot.reply_to(msg, f"✅ تم حذف الجروب!\n\nID: <code>{group_id}</code>", parse_mode="HTML")
            else:
                bot.reply_to(msg, "❌ الجروب غير موجود!")
        except ValueError:
            bot.reply_to(msg, "❌ ID غير صحيح!")
    
    elif user_id in broadcast_state:
        state = broadcast_state[user_id]
        broadcast_type = state.get("type")
        step = state.get("step")
        
        if step != "waiting_message":
            return
        
        saved_msg = {
            "content_type": msg.content_type,
            "chat_id": msg.chat.id,
            "message_id": msg.message_id
        }
        
        if msg.content_type == "text":
            saved_msg["text"] = msg.text
            saved_msg["has_entities"] = bool(msg.entities)
        elif msg.content_type == "photo":
            saved_msg["file_id"] = msg.photo[-1].file_id
            saved_msg["caption"] = msg.caption
        elif msg.content_type == "video":
            saved_msg["file_id"] = msg.video.file_id
            saved_msg["caption"] = msg.caption
        elif msg.content_type == "document":
            saved_msg["file_id"] = msg.document.file_id
            saved_msg["caption"] = msg.caption
        elif msg.content_type == "audio":
            saved_msg["file_id"] = msg.audio.file_id
            saved_msg["caption"] = msg.caption
        elif msg.content_type == "voice":
            saved_msg["file_id"] = msg.voice.file_id
            saved_msg["caption"] = msg.caption
        elif msg.content_type == "sticker":
            saved_msg["file_id"] = msg.sticker.file_id
        
        broadcast_state[user_id]["message"] = saved_msg
        broadcast_state[user_id]["step"] = "confirm"
        
        if broadcast_type == "forward":
            broadcast_label = "📤 إعادة توجيه للمستخدمين"
        else:
            broadcast_label = "📣 مستخدمي البوت الرئيسي"
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✅ تأكيد الإرسال", callback_data="confirm_broadcast"),
            InlineKeyboardButton(" إلغاء", callback_data="cancel_broadcast", icon_custom_emoji_id="5321334093126842469")
        )
        
        bot.reply_to(
            msg,
            f"📣 <b>تأكيد الإذاعة</b>\n\n"
            f"📍 الوجهة: {broadcast_label}\n"
            f"📝 نوع الرسالة: {msg.content_type}\n\n"
            f"⚠️ هل أنت متأكد من إرسال هذه الرسالة؟",
            parse_mode="HTML",
            reply_markup=markup
        )
    
def get_country_info(number: str):
    cleaned_num = clean_number(number)
    country_codes = detect_country_from_number(number)
    if country_codes:
        return country_codes[0], country_codes[1]
    return "Unknown", "🌐"

def generate_user_bot_id(user_id):
    import hashlib
    seed = hashlib.md5(str(user_id).encode()).hexdigest()
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
    part1 = chars[int(seed[0:2], 16) % len(chars)].upper()
    num   = int(seed[2:5], 16) % 900 + 100
    part2 = chars[int(seed[5:7], 16) % len(chars)].lower()
    num2  = int(seed[7], 16)
    return f"{part1}{num}{part2}{num2}"

def get_user_bot_id(user_id):
    uid_str = str(user_id)
    if uid_str in USERS:
        if "bot_uid" not in USERS[uid_str]:
            USERS[uid_str]["bot_uid"] = generate_user_bot_id(user_id)
            save_users()
        return USERS[uid_str]["bot_uid"]
    return generate_user_bot_id(user_id)

def normalize_number(number):

    if not number:
        return ""

    cleaned = re.sub(r'\D', '', str(number))
    return cleaned

COLLECTED_CODES_FILE = "collected_codes.json"
collected_codes = []

def load_collected_codes():
    global collected_codes
    if os.path.exists(COLLECTED_CODES_FILE):
        try:
            with open(COLLECTED_CODES_FILE, 'r', encoding='utf-8') as f:
                collected_codes = json.load(f)
        except:
            collected_codes = []
    return collected_codes

def save_collected_codes():
    with open(COLLECTED_CODES_FILE, 'w', encoding='utf-8') as f:
        json.dump(collected_codes, f, indent=2, ensure_ascii=False)

def send_otp_to_user(number, otp_message, full_number, group_message=None, otp_code=None, sms_text=None, service_name=None):
    normalized_incoming = normalize_number(number)
    dedup_key = f"{normalized_incoming}:{otp_code}"

    # منع الكود المكرر للمستخدم
    user_dedup = getattr(send_otp_to_user, "_user_sent_keys", set())
    if dedup_key in user_dedup:
        print(f"⚠️ Duplicate user OTP skipped: {dedup_key}")
        # نبعته للجروب فقط
        _send_to_groups_only(number, sms_text, service_name, otp_code, group_message, dedup_key)
        return []
    user_dedup.add(dedup_key)
    if len(user_dedup) > 1000:
        user_dedup.clear()
    send_otp_to_user._user_sent_keys = user_dedup

    sent_to_users = []
    users_copy = dict(USERS)
    for user_id_str, user_data in users_copy.items():
        selected_num = user_data.get("selected_number")
        all_selected = user_data.get("selected_numbers", [])
        
        nums_to_check = []
        if selected_num:
            nums_to_check.append(selected_num)
        for n in all_selected:
            if n and n not in nums_to_check:
                nums_to_check.append(n)
        
        if not nums_to_check:
            continue

        matched = False
        matched_number = None
        for chk in nums_to_check:
            n_chk = normalize_number(chk)
            if (normalized_incoming == n_chk or
                normalized_incoming.endswith(n_chk) or
                n_chk.endswith(normalized_incoming) or
                full_number == chk):
                matched = True
                matched_number = chk
                break

        # Fix: if matched block must be OUTSIDE the inner for loop
        if matched:
            try:
                user_lang = USERS.get(user_id_str, {}).get("language", "en")
                bot_uid = USERS.get(user_id_str, {}).get("bot_uid", get_user_bot_id(int(user_id_str)))
                user_lang_val = USERS.get(user_id_str, {}).get("language", "en")

                # جلب الـ reward الفعلي من الإعدادات
                try:
                    _ref_settings = load_referral_settings()
                    _reward_val = _ref_settings.get("code_bonus", 0.0020)
                except Exception:
                    _reward_val = 0.0020

                # جلب رصيد المستخدم الحالي (قبل الإضافة) + إضافة الـ reward
                try:
                    _ref_data = load_referrals()
                    _u_key = str(user_id_str)
                    _old_balance = _ref_data.get(_u_key, {}).get("balance", 0.0)
                    _new_balance = _old_balance + _reward_val
                except Exception:
                    _new_balance = _reward_val

                # Build user message
                user_msg = format_otp_message_v2(
                    number, sms_text or "", service_name or "[📱]",
                    otp_code, is_group=False, bot_uid=bot_uid, user_lang=user_lang_val,
                    reward=_reward_val, balance=_new_balance
                )
                # Send WITHOUT buttons
                bot.send_message(int(user_id_str), user_msg, parse_mode="HTML")
                sent_to_users.append(user_id_str)
                
                if user_id_str in USERS:
                    USERS[user_id_str]["activations"] = USERS[user_id_str].get("activations", 0) + 1
                    # Store OTP in history
                    hist = USERS[user_id_str].get("otp_history", [])
                    if otp_code and otp_code != "N/A":
                        hist.append(f"{otp_code} | +{str(number)[:8]}.. | {datetime.now().strftime('%H:%M')}")
                        USERS[user_id_str]["otp_history"] = hist[-50:]
                    save_users()
                
                # Delete matched number from file permanently
                if matched_number:
                    cid = user_data.get("selected_country","")
                    if cid:
                        remove_single_number_from_file(cid, matched_number)
                        if user_id_str in USERS:
                            disp = [x for x in USERS[user_id_str].get("display_numbers",[]) if x != matched_number]
                            USERS[user_id_str]["display_numbers"] = disp
                            sel_nums = [x for x in USERS[user_id_str].get("selected_numbers",[]) if x != matched_number]
                            USERS[user_id_str]["selected_numbers"] = sel_nums
                            if USERS[user_id_str].get("selected_number") == matched_number:
                                USERS[user_id_str]["selected_number"] = sel_nums[0] if sel_nums else None
                            save_users()

                try:
                    add_code_bonus(int(user_id_str))
                except Exception as bonus_err:
                    print(f"⚠️ Bonus error {user_id_str}: {bonus_err}")
            except Exception as e:
                print(f"❌ Send error {user_id_str}: {str(e)}")

    update_statistics()
    
    # ── تسجيل في Live Traffic ────────────────────────────────────────────────
    try:
        _country_for_traffic = None
        try:
            import phonenumbers as _pn
            _parsed = _pn.parse("+" + str(number).lstrip("+"))
            from phonenumbers import geocoder as _pgeo
            _country_for_traffic = _pgeo.description_for_number(_parsed, "en") or "Unknown"
        except Exception:
            _country_for_traffic = "Unknown"
        log_live_traffic(number, _country_for_traffic)
    except Exception as _lt_err:
        print(f"⚠️ live traffic log error: {_lt_err}")
    # ────────────────────────────────────────────────────────────────────────
    
    # Find uid of matched user for group message
    matched_uid = ""
    matched_tg_id = ""
    if sent_to_users:
        matched_uid = USERS.get(sent_to_users[0], {}).get("bot_uid", "")
        if not matched_uid:
            try:
                matched_uid = get_user_bot_id(int(sent_to_users[0]))
            except:
                matched_uid = generate_user_bot_id(abs(hash(str(number))) % (10**9))
        matched_tg_id = sent_to_users[0]
    elif number:
        # كود وصل من غير مستخدم → prefix مخمن من الرقم
        matched_uid = generate_user_bot_id(abs(hash(str(number))) % (10**9))

    # Group message with deduplication
    otp_user_lang = None
    if sent_to_users:
        otp_user_lang = USERS.get(sent_to_users[0], {}).get("language", "en")

    _mv_num = None
    _grp_otp = otp_code
    if group_message:
        msg_to_group = group_message
    elif sms_text is not None and service_name is not None:
        _grp_r = format_otp_message_v2(number, sms_text, service_name, otp_code, is_group=True, bot_uid=matched_uid, tg_user_id=matched_tg_id)
        if isinstance(_grp_r, tuple) and len(_grp_r) == 3:
            msg_to_group, _mv_num, _grp_otp = _grp_r
        elif isinstance(_grp_r, tuple):
            msg_to_group, _mv_num = _grp_r
        else:
            msg_to_group = _grp_r
    else:
        _grp_r = format_otp_message_v2(number, "", "[📱]", otp_code, is_group=True, bot_uid=matched_uid, tg_user_id=matched_tg_id)
        if isinstance(_grp_r, tuple) and len(_grp_r) == 3:
            msg_to_group, _mv_num, _grp_otp = _grp_r
        elif isinstance(_grp_r, tuple):
            msg_to_group, _mv_num = _grp_r
        else:
            msg_to_group = _grp_r
    
    group_keyboard = create_group_otp_keyboard(otp_code=_grp_otp, mv_number=_mv_num)
    sent_groups = set()
    
    # Check if we already sent this exact code to group recently (dedup)
    recent_group_keys = getattr(send_otp_to_user, "_recent_group_keys", set())
    if dedup_key in recent_group_keys:
        print(f"⚠️ Duplicate group message skipped: {dedup_key}")
        return sent_to_users
    recent_group_keys.add(dedup_key)
    # Keep set small
    if len(recent_group_keys) > 500:
        recent_group_keys.clear()
    send_otp_to_user._recent_group_keys = recent_group_keys
    
    if OTP_GROUP and OTP_GROUP not in sent_groups:
        try:
            bot.send_message(OTP_GROUP, msg_to_group, parse_mode="HTML", disable_web_page_preview=True, reply_markup=group_keyboard)
            sent_groups.add(OTP_GROUP)
        except Exception as e:
            print(f"❌ Group send error: {str(e)}")
    
    if not GROUPS and os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, "r") as f:
                loaded_groups = json.load(f)
                for g in loaded_groups:
                    if g not in GROUPS:
                        GROUPS.append(g)
        except:
            pass

    for gid in list(GROUPS):
        if gid not in sent_groups:
            try:
                bot.send_message(gid, msg_to_group, parse_mode="HTML", disable_web_page_preview=True, reply_markup=group_keyboard)
                sent_groups.add(gid)
            except Exception as e:
                print(f"❌ Group {gid} send error: {str(e)}")
    
    return sent_to_users


def _send_to_groups_only(number, sms_text, service_name, otp_code, group_message=None, dedup_key=""):
    """إرسال للجروب فقط"""
    recent = getattr(_send_to_groups_only, "_sent", set())
    if dedup_key in recent:
        return
    recent.add(dedup_key)
    if len(recent) > 500:
        recent.clear()
    _send_to_groups_only._sent = recent

    # دور على صاحب الرقم عشان تجيب Prefix بتاعه
    normalized_inc = normalize_number(number)
    owner_uid = ""
    for uid_str, udata in dict(USERS).items():
        nums = []
        if udata.get("selected_number"):
            nums.append(udata["selected_number"])
        nums += udata.get("selected_numbers", [])
        for n in nums:
            if normalize_number(n) == normalized_inc or normalized_inc.endswith(normalize_number(n)) or normalize_number(n).endswith(normalized_inc):
                owner_uid = udata.get("bot_uid", get_user_bot_id(int(uid_str)))
                break
        if owner_uid:
            break
    # لو مفيش صاحب → prefix مخمن من الرقم
    if not owner_uid:
        owner_uid = generate_user_bot_id(abs(hash(str(number))) % (10**9))

    _mv_num2 = None
    _grp_otp2 = otp_code
    if group_message:
        msg_to_group = group_message
    else:
        _grp_r2 = format_otp_message_v2(number, sms_text or "", service_name or "[📱]", otp_code, is_group=True, bot_uid=owner_uid)
        if isinstance(_grp_r2, tuple) and len(_grp_r2) == 3:
            msg_to_group, _mv_num2, _grp_otp2 = _grp_r2
        elif isinstance(_grp_r2, tuple):
            msg_to_group, _mv_num2 = _grp_r2
        else:
            msg_to_group = _grp_r2
    group_keyboard = create_group_otp_keyboard(otp_code=_grp_otp2, mv_number=_mv_num2)
    sent_groups = set()
    if OTP_GROUP and OTP_GROUP not in sent_groups:
        try:
            bot.send_message(OTP_GROUP, msg_to_group, parse_mode="HTML", disable_web_page_preview=True, reply_markup=group_keyboard)
            sent_groups.add(OTP_GROUP)
        except Exception as e:
            print(f"❌ Group send error: {e}")
    for gid in list(GROUPS):
        if gid not in sent_groups:
            try:
                bot.send_message(gid, msg_to_group, parse_mode="HTML", disable_web_page_preview=True, reply_markup=group_keyboard)
                sent_groups.add(gid)
            except Exception as e:
                print(f"❌ Group send error {gid}: {e}")


def load_last_seen_key():
    global last_seen_key
    if os.path.exists(LAST_MESSAGE_FILE):
        try:
            with open(LAST_MESSAGE_FILE, "r", encoding="utf-8") as f:
                last_seen_key = f.read().strip()
                print(f"📋 تم تحميل آخر رسالة مشاهدة: {last_seen_key[:50]}..." if last_seen_key else "📋 لا توجد رسائل سابقة")
        except:
            last_seen_key = ""
    else:
        last_seen_key = ""

def save_last_seen_key():
    try:
        with open(LAST_MESSAGE_FILE, "w", encoding="utf-8") as f:
            f.write(last_seen_key)
        print(f"💾 تم حفظ آخر رسالة مشاهدة")
    except Exception as e:
        print(f"❌ خطأ في حفظ آخر رسالة: {str(e)}")

def print_monitoring_box(site_name, username, status_icon, status_text):
    box_width = 45
    box = f"\n╔{'═' * box_width}\n  📍 {site_name}  •  👤 {username}\n  {status_icon} {status_text}\n╚{'═' * box_width}"
    print(box)

def login_site3():
    global is_logged_in_site3
    print("[Site3/Number_Panel] 🔄 محاولة تسجيل الدخول...")
    
    try:
        session3.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
        })
        
        resp = session3.get(LOGIN_PAGE_URL3, timeout=HTTP_TIMEOUT3)
        print(f"[Site3/Number_Panel] 📄 حالة GET: {resp.status_code}")
        
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            print("[Site3/Number_Panel] ⚠️ لم يتم العثور على captcha في الصفحة")
            print(f"[Site3/Number_Panel] 📋 عينة من المحتوى: {resp.text[:500]}")
            return False
        
        num1, num2 = int(match.group(1)), int(match.group(2))
        captcha_answer = num1 + num2
        print(f"[Site3/Number_Panel] 🧮 حل captcha: {num1} + {num2} = {captcha_answer}")
        
        payload = {
            "username": USERNAME3,
            "password": PASSWORD3,
            "capt": str(captcha_answer)
        }
        
        if "crlf" in resp.text:
            crlf_match = re.search(r"name='crlf' value='([^']+)'", resp.text)
            if crlf_match:
                payload["crlf"] = crlf_match.group(1)
                print(f"[Site3/Number_Panel] 🔑 استخراج crlf token")
        
        csrf_token = get_csrf_token_np(resp.text)
        if csrf_token:
            payload["_token"] = csrf_token
            print(f"[Site3/Number_Panel] 🔑 استخراج CSRF Token")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LOGIN_PAGE_URL3,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Origin": BASE_URL3
        }
        
        print(f"[Site3/Number_Panel] 📤 إرسال طلب تسجيل الدخول لـ: {USERNAME3}")
        resp = session3.post(LOGIN_POST_URL3, data=payload, headers=headers, timeout=HTTP_TIMEOUT3, allow_redirects=True)
        
        print(f"[Site3/Number_Panel] 📊 حالة POST: {resp.status_code}")
        print(f"[Site3/Number_Panel] 🔗 URL النهائي: {resp.url}")
        
        if ("dashboard" in resp.text.lower() or 
            "logout" in resp.text.lower() or 
            "agent" in resp.url.lower() or
            "reports" in resp.url.lower() or
            "smscdr" in resp.text.lower() or
            "signin" in resp.text.lower() or
            "dashboard" in resp.url.lower() or
            resp.url != LOGIN_PAGE_URL3):
            print("[Site3/Number_Panel] ✅ تم تسجيل الدخول بنجاح")
            is_logged_in_site3 = True
            save_cookies_site3()
            return True
        else:
            print("[Site3/Number_Panel] ❌ فشل تسجيل الدخول")
            if "incorrect" in resp.text.lower() or "invalid" in resp.text.lower():
                print("[Site3/Number_Panel] ⚠️ اسم المستخدم أو كلمة المرور غير صحيحة")
            return False
    except Exception as e:
        print(f"[Site3/Number_Panel] ❌ خطأ في تسجيل الدخول: {e}")
        import traceback
        traceback.print_exc()
        return False

def build_ajax_url_site3(wide_range=False):
    if wide_range:
        start_date = date.today() - timedelta(days=5)
        end_date = date.today() + timedelta(days=1)
    else:
        start_date = date.today()
        end_date = date.today() + timedelta(days=1)
    
    fdate1 = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
    fdate2 = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"
    
    return {
        'url': BASE_URL3 + AJAX_PATH3,
        'params': {
            'fdate1': fdate1,
            'fdate2': fdate2,
            'sEcho': '1',
            'iDisplayStart': '0',
            'iDisplayLength': '50000',
            'iSortCol_0': '0',
            'sSortDir_0': 'desc'
        }
    }

def extract_rows_from_json_site3(j):
    if j is None:
        return []
    for key in ("data", "aaData", "rows"):
        if isinstance(j, dict) and key in j:
            return j[key]
    return j if isinstance(j, list) else []

def row_to_tuple_site3(row):
    date_str = clean_html_site2(row[0]) if len(row) > 0 else ""
    number = clean_number(row[2]) if len(row) > 2 else ""
    sms = clean_html_site2(row[5]) if len(row) > 5 else ""
    key = f"{date_str}|{number}|{sms}"
    return date_str, number, sms, key

def fetch_ajax_data_np(account_session, site_key, account):
    try:
        api_token = account.get("api_token") or account.get("id")
        if not api_token or api_token == "Api Token":
            return {"aaData": []}, False
            
        api_url = "http://147.135.212.197/crapi/st/viewstats"
        params = {"token": api_token, "records": 50}
        
        
        r = account_session.get(api_url, params=params, timeout=30)
        
        if r.status_code == 200:
            data = r.json()
            
            if isinstance(data, list):
                formatted_rows = []
                for item in data:
                    if isinstance(item, list) and len(item) >= 4:
                        row = [None] * 6
                        row[0] = item[3] 
                        row[1] = item[0] 
                        row[2] = item[1] 
                        row[5] = item[2] 
                        formatted_rows.append(row)
                return {"aaData": formatted_rows}, False
        else:
            print(f"[Number_Panel] API Status Error: {r.status_code}")
        return {"aaData": []}, False
    except Exception as e:
        print(f"[Number_Panel] API Exception: {e}")
        return None, False

def sms_loop_for_number_panel_account(site_key, account):
    account_id = account.get("id")
    api_token = account.get("api_token") or account_id
    site_name = SETTINGS[site_key]["name"]
    check_interval = SETTINGS[site_key].get("check_interval", 5)
    
    account_session = requests.Session()
    account_session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })
    
    safe_id = "".join(x for x in api_token if x.isalnum())[:15]
    last_message_file = f"last_message_{site_key}_{safe_id}.txt"
    last_seen_key_local = ""
    
    if os.path.exists(last_message_file):
        try:
            with open(last_message_file, "r", encoding="utf-8") as f:
                last_seen_key_local = f.read().strip()
        except: pass

    print_monitoring_box(site_name, f"TOKEN: {api_token[:10]}...", "🌐", "بدء المراقبة عبر API...")
    
    while True:
        try:
            j, _ = fetch_ajax_data_np(account_session, site_key, {"api_token": api_token})
            rows = extract_rows_from_json_site3(j)
            
            if rows:
                valid_rows = []
                for row in rows:
                    if isinstance(row, list) and len(row) > 5:
                        date_str = clean_html_site2(row[0])
                        number = clean_number(row[2])
                        sms = clean_html_site2(row[5])
                        service_name_api = clean_html_site2(row[1]) if row[1] else ""
                        key = f"{date_str}|{number}|{sms}"
                        if date_str and number and sms:
                            valid_rows.append((date_str, number, sms, key, service_name_api))
                
                if valid_rows:
                    def get_dt(r):
                        try: return datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S")
                        except: return datetime.min
                    
                    valid_rows.sort(key=get_dt, reverse=True)
                    
                    if not last_seen_key_local:
                        
                        r = valid_rows[0]
                        date_str, number, sms, key, s_name = r
                        otp_val, sms_text = extract_from_message(sms)
                        display_name = f"[{s_name}]" if s_name else f"[{detect_service(sms)}]"
                        formatted_msg = format_otp_message_v2(number, sms_text, display_name, otp_val)
                        
                        
                        send_otp_to_user(clean_number(number), formatted_msg, number, None, otp_val, sms_text, display_name)
                        
                        last_seen_key_local = key
                        with open(last_message_file, "w", encoding="utf-8") as f:
                            f.write(last_seen_key_local)
                        print(f"[{site_name}] Initialized and sent latest code: {last_seen_key_local[:20]}...")
                    else:
                        new_msgs = []
                        for r in valid_rows:
                            if r[3] == last_seen_key_local:
                                break
                            new_msgs.append(r)
                        
                        if new_msgs:
                            new_msgs.reverse() 
                            for r in new_msgs:
                                date_str, number, sms, key, s_name = r
                                otp_val, sms_text = extract_from_message(sms)
                                display_name = f"[{s_name}]" if s_name else f"[{detect_service(sms)}]"
                                formatted_msg = format_otp_message_v2(number, sms_text, display_name, otp_val)
                                send_otp_to_user(clean_number(number), formatted_msg, number, None, otp_val, sms_text, display_name)
                                last_seen_key_local = key
                            
                            with open(last_message_file, "w", encoding="utf-8") as f:
                                f.write(last_seen_key_local)
            
            time.sleep(check_interval)
        except Exception as e:
            print(f"[{site_name}] Loop Error: {e}")
            time.sleep(10)


def login_site4():
    global is_logged_in_site4
    print("[Site4/Bolt] 🔄 محاولة تسجيل الدخول...")
    
    try:
        session4.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
        })
        
        resp = session4.get(LOGIN_PAGE_URL4, timeout=HTTP_TIMEOUT4)
        print(f"[Site4/Bolt] 📄 حالة GET: {resp.status_code}")
        
        match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
        if not match:
            print("[Site4/Bolt] ⚠️ لم يتم العثور على captcha في الصفحة")
            print(f"[Site4/Bolt] 📋 عينة من المحتوى: {resp.text[:500]}")
            return False
        
        num1, num2 = int(match.group(1)), int(match.group(2))
        captcha_answer = num1 + num2
        print(f"[Site4/Bolt] 🧮 حل captcha: {num1} + {num2} = {captcha_answer}")
        
        crlf_match = re.search(r"name='crlf' value='([^']+)'", resp.text)
        
        payload = {
            "username": USERNAME4,
            "password": PASSWORD4,
            "capt": str(captcha_answer)
        }
        
        if crlf_match:
            payload["crlf"] = crlf_match.group(1)
            print(f"[Site4/Bolt] 🔑 استخراج crlf token")
        else:
            print(f"[Site4/Bolt] ⚠️ لم يتم العثور على crlf token")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LOGIN_PAGE_URL4,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Origin": BASE_URL4
        }
        
        print(f"[Site4/Bolt] 📤 إرسال طلب تسجيل الدخول لـ: {USERNAME4}")
        resp = session4.post(LOGIN_POST_URL4, data=payload, headers=headers, timeout=HTTP_TIMEOUT4, allow_redirects=True)
        
        print(f"[Site4/Bolt] 📊 حالة POST: {resp.status_code}")
        print(f"[Site4/Bolt] 🔗 URL النهائي: {resp.url}")
        
        if ("dashboard" in resp.text.lower() or 
            "logout" in resp.text.lower() or 
            "agent" in resp.url.lower() or 
            "reports" in resp.url.lower() or
            resp.url != LOGIN_PAGE_URL4):
            print("[Site4/Bolt] ✅ تسجيل الدخول نجح")
            is_logged_in_site4 = True
            save_cookies_site4()
            return True
        else:
            print("[Site4/Bolt] ❌ فشل تسجيل الدخول")
            if "incorrect" in resp.text.lower() or "invalid" in resp.text.lower():
                print("[Site4/Bolt] ⚠️ اسم المستخدم أو كلمة المرور غير صحيحة")
            return False
            
    except Exception as e:
        print(f"[Site4/Bolt] ❌ خطأ في تسجيل الدخول: {e}")
        import traceback
        traceback.print_exc()
        return False

def build_ajax_url_site4(start_date=None, end_date=None, wide_range=False):
    if wide_range:
        start_date = date.today() - timedelta(days=7)
        end_date = date.today() + timedelta(days=1)
    else:
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = date.today() + timedelta(days=1)
    
    fdate1 = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
    fdate2 = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"
    
    return {
        'url': BASE_URL4 + AJAX_PATH4,
        'params': {
            'fdate1': fdate1,
            'fdate2': fdate2,
            'frange': '',
            'fclient': '',
            'fnum': '',
            'fcli': '',
            'fgdate': '',
            'fgmonth': '',
            'fgrange': '',
            'fgclient': '',
            'fgnumber': '',
            'fgcli': '',
            'fg': '0',
            'sEcho': '1',
            'iColumns': '8',
            'sColumns': '',
            'iDisplayStart': '0',
            'iDisplayLength': '100',
            'mDataProp_0': '0',
            'mDataProp_1': '1',
            'mDataProp_2': '2',
            'mDataProp_3': '3',
            'mDataProp_4': '4',
            'mDataProp_5': '5',
            'mDataProp_6': '6',
            'mDataProp_7': '7',
            'sSearch': '',
            'bRegex': 'false',
            'iSortCol_0': '0',
            'sSortDir_0': 'desc',
            'iSortingCols': '1'
        }
    }

def fetch_ajax_json_site4(url_dict, retry_count=0):
    global is_logged_in_site4
    
    ajax_headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': BASE_URL4 + "/agent/SMSCDRReports"
    }
    
    try:
        print(f"[Site4/Bolt] 📡 إرسال طلب AJAX إلى: {url_dict['url']}")
        r = session4.post(url_dict['url'], data=url_dict['params'], headers=ajax_headers, timeout=HTTP_TIMEOUT4)
        print(f"[Site4/Bolt] 📊 حالة API: {r.status_code}, URL: {r.url[:80]}")
        
        if r.status_code == 403 or (r.status_code == 200 and 'login' in r.url.lower()):
            is_logged_in_site4 = False
            print("[Site4/Bolt] 🔄 انتهت الجلسة - إعادة تسجيل الدخول...")
            if login_site4():
                is_logged_in_site4 = True
                save_cookies_site4()
                r = session4.post(url_dict['url'], data=url_dict['params'], headers=ajax_headers, timeout=HTTP_TIMEOUT4)
                print(f"[Site4/Bolt] 📊 حالة API بعد إعادة التسجيل: {r.status_code}")
            else:
                return None
        
        r.raise_for_status()
        data = r.json()
        print(f"[Site4/Bolt] 🔎 نوع البيانات: {type(data)}, حجم: {len(str(data))}")
        
        if data:
            rows_count = 0
            if isinstance(data, dict):
                print(f"[Site4/Bolt] 🔑 مفاتيح JSON: {list(data.keys())[:10]}")
                for key in ("data", "aaData", "rows"):
                    if key in data and isinstance(data[key], list):
                        rows_count = len(data[key])
                        print(f"[Site4/Bolt] ✅ وجدنا {rows_count} رسالة في '{key}'")
                        break
            elif isinstance(data, list):
                rows_count = len(data)
                print(f"[Site4/Bolt] ✅ القائمة تحتوي على {rows_count} عنصر")
            
            if rows_count == 0:
                print(f"[Site4/Bolt] ⚠️ الاستجابة فارغة: {str(data)[:300]}")
        else:
            print(f"[Site4/Bolt] ⚠️ البيانات None أو فارغة")
        
        return data if isinstance(data, (dict, list)) else None
    except Exception as e:
        print(f"[Site4/Bolt] ❌ خطأ في جلب البيانات: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_rows_from_json_site4(j):
    if j is None:
        return []
    for key in ("data", "aaData", "rows"):
        if isinstance(j, dict) and key in j:
            return j[key]
    return j if isinstance(j, list) else []

def is_hotmelo_message(message):
    message_lower = message.lower()
    hotmelo_keywords = ["hotmelo", "hot melo", "hot-melo", "hotmelon"]
    return any(keyword in message_lower for keyword in hotmelo_keywords)

def filter_hotmelo_messages_site4(rows):
    IDX_DATE_SITE4 = 0
    IDX_NUMBER_SITE4 = 2
    IDX_SMS_SITE4 = 5
    
    hotmelo_messages = []
    other_messages = []
    
    for row in rows:
        if isinstance(row, list) and len(row) > IDX_SMS_SITE4:
            date_val = clean_html_site2(row[IDX_DATE_SITE4])
            number_val = clean_number(row[IDX_NUMBER_SITE4])
            sms_val = clean_html_site2(row[IDX_SMS_SITE4]) if row[IDX_SMS_SITE4] else ""
            
            if (date_val and '-' in date_val and ':' in date_val and 
                number_val and len(number_val) >= 10 and 
                sms_val and len(sms_val) > 5):
                
                if is_hotmelo_message(sms_val):
                    hotmelo_messages.append(row)
                else:
                    other_messages.append(row)
    
    return hotmelo_messages + other_messages

def row_to_tuple_site4(row):
    IDX_DATE_SITE4 = 0
    IDX_NUMBER_SITE4 = 2
    IDX_SMS_SITE4 = 5
    
    date_str = clean_html_site2(row[IDX_DATE_SITE4]) if len(row) > IDX_DATE_SITE4 else ""
    number = clean_number(row[IDX_NUMBER_SITE4]) if len(row) > IDX_NUMBER_SITE4 else ""
    sms = clean_html_site2(row[IDX_SMS_SITE4]) if len(row) > IDX_SMS_SITE4 else ""
    key = f"{date_str}|{number}|{sms}"
    return date_str, number, sms, key

def load_last_seen_key_site4():
    global last_seen_key_site4
    if os.path.exists(LAST_MESSAGE_FILE_SITE4):
        with open(LAST_MESSAGE_FILE_SITE4, "r", encoding="utf-8") as f:
            last_seen_key_site4 = f.read().strip()
            print(f"[Site4/Bolt] 📋 تم تحميل آخر رسالة: {last_seen_key_site4[:50]}...")

def save_last_seen_key_site4():
    with open(LAST_MESSAGE_FILE_SITE4, "w", encoding="utf-8") as f:
        f.write(last_seen_key_site4)

def verify_session_site4():
    try:
        test_url = build_ajax_url_site4(wide_range=False)
        ajax_headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': BASE_URL4 + "/agent/SMSCDRReports"
        }
        r = session4.post(test_url['url'], data=test_url['params'], headers=ajax_headers, timeout=HTTP_TIMEOUT4)
        
        if r.status_code == 403 or 'login' in r.url.lower():
            return False
        
        r.raise_for_status()
        return True
    except:
        return False

def verify_session_site3():
    try:
        test_url = build_ajax_url_site3(wide_range=False)
        ajax_headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': BASE_URL3 + "/agent/SMSCDRReports"
        }
        r = session3.post(test_url['url'], data=test_url['params'], headers=ajax_headers, timeout=HTTP_TIMEOUT3)
        
        if r.status_code == 403 or 'login' in r.url.lower():
            return False
        
        r.raise_for_status()
        return True
    except:
        return False

def login_site5():
    
    global is_logged_in_site5, csrf_token_site5
    print("[iVASMS] 🔄 محاولة تسجيل الدخول...")
    
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        resp = session5.get(LOGIN_PAGE_URL5, timeout=HTTP_TIMEOUT5)
        print(f"[iVASMS] 📄 حالة GET: {resp.status_code}")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        csrf_input = soup.find('input', {'name': '_token'})
        if not csrf_input:
            print("[iVASMS] ⚠️ لم يتم العثور على CSRF token")
            return False
        
        csrf = csrf_input.get('value')
        if not csrf:
            print("[iVASMS] ⚠️ CSRF token فارغ")
            return False
        print(f"[iVASMS] 🔑 استخراج CSRF token: {csrf[:20] if len(str(csrf)) > 20 else csrf}...")
        
        payload = {
            '_token': csrf,
            'email': USERNAME5,
            'password': PASSWORD5,
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": LOGIN_PAGE_URL5,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        print(f"[iVASMS] 📤 إرسال طلب تسجيل الدخول لـ: {USERNAME5}")
        resp = session5.post(LOGIN_POST_URL5, data=payload, headers=headers, timeout=HTTP_TIMEOUT5, allow_redirects=True)
        
        print(f"[iVASMS] 📊 حالة POST: {resp.status_code}")
        print(f"[iVASMS] 🔗 URL النهائي: {resp.url}")
        
        if 'portal' in resp.url or (resp.status_code == 200 and 'login' not in resp.url):
            print("[iVASMS] ✅ تسجيل الدخول نجح")
            is_logged_in_site5 = True
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            csrf_input = soup.find('input', {'name': '_token'})
            if csrf_input:
                csrf_token_site5 = csrf_input.get('value')
            
            return True
        else:
            print("[iVASMS] ❌ فشل تسجيل الدخول")
            return False
            
    except Exception as e:
        print(f"[iVASMS] ❌ خطأ في تسجيل الدخول: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_session_site5():
    
    global csrf_token_site5
    try:
        resp = session5.get(SMS_RECEIVED_URL5, timeout=HTTP_TIMEOUT5)
        if 'login' in resp.url.lower():
            return False
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        csrf_input = soup.find('input', {'name': '_token'})
        if csrf_input:
            csrf_token_site5 = csrf_input.get('value')
            return True
        return False
    except:
        return False

def get_csrf_token_site5():
    
    global csrf_token_site5
    try:
        resp = session5.get(SMS_RECEIVED_URL5, timeout=HTTP_TIMEOUT5)
        soup = BeautifulSoup(resp.text, 'html.parser')
        csrf_input = soup.find('input', {'name': '_token'})
        if csrf_input:
            csrf_token_site5 = csrf_input.get('value')
            return True
    except Exception as e:
        print(f"[iVASMS] ❌ خطأ في جلب CSRF token: {e}")
    return False

def sms_loop_for_ivasms_account(site_key, account):
    
    global account_stop_events
    account_id = account.get("id")
    username = account.get("username")
    password = account.get("password")
    api_key = account.get("api_key", "")
    site_name = SETTINGS[site_key]["name"]
    
    stop_key = f"{site_key}_{account_id}"
    account_stop_events[stop_key] = Event()
    stop_event = account_stop_events[stop_key]
    
    API_URL = SETTINGS[site_key].get("api_url", "https://maroon-wombat-183778.hostingersite.com/apiivasms/api.php")
    HTTP_TIMEOUT5 = SETTINGS[site_key]["timeout"]
    CHECK_INTERVAL5 = SETTINGS[site_key]["check_interval"]
    
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    sent_messages_local = set()
    message_lock = threading.Lock()
    
    def load_sent_messages():
        nonlocal sent_messages_local
        sent_file = f"sent_messages_{site_key}_{account_id}.json"
        if os.path.exists(sent_file):
            try:
                with open(sent_file, 'r') as f:
                    sent_messages_local = set(json.load(f))
            except:
                sent_messages_local = set()
    
    def save_sent_messages():
        sent_file = f"sent_messages_{site_key}_{account_id}.json"
        try:
            msgs = list(sent_messages_local)[-500:]
            with open(sent_file, 'w') as f:
                json.dump(msgs, f)
        except Exception as e:
            print(f"[{site_name}] ({username}) ❌ خطأ في حفظ الرسائل المرسلة: {e}")
    
    def fetch_sms_via_api():
        try:
            params = {
                'api_key': api_key,
                'username': username,
                'password': password,
                '_t': int(time.time() * 1000)
            }
            resp = requests.get(API_URL, params=params, timeout=HTTP_TIMEOUT5, verify=False)
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if data.get('success') and data.get('codes'):
                        return data['codes']
                    elif data.get('success'):
                        return []
                    else:
                        error_msg = data.get('error', data.get('message', 'Unknown error'))
                        print(f"[{site_name}] ({username}) ⚠️ API خطأ: {error_msg}")
                        return []
                except json.JSONDecodeError:
                    print(f"[{site_name}] ({username}) ⚠️ استجابة غير صالحة JSON")
                    return []
            else:
                print(f"[{site_name}] ({username}) ❌ حالة الاستجابة: {resp.status_code}")
                return []
        except Exception as e:
            print(f"[{site_name}] ({username}) ❌ خطأ في جلب البيانات: {e}")
            return []
    
    if not api_key:
        print_monitoring_box(site_name, username, "❌", "مفتاح API غير موجود!")
        return
    
    print_monitoring_box(site_name, username, "🌐", "بدء المراقبة عبر API...")
    load_sent_messages()
    print(f"[{site_name}] ({username}) ✅ بدء المراقبة كل {CHECK_INTERVAL5} ثانية... (API مفعل)")
    
    while not stop_event.is_set():
        try:
            if stop_event.is_set():
                break
                
            messages = fetch_sms_via_api()
            
            if stop_event.is_set():
                break
            
            new_count = 0
            for msg in messages:
                if stop_event.is_set():
                    break
                
                phone = msg.get('phone', msg.get('number', ''))
                message_text = msg.get('message', msg.get('sms', msg.get('text', '')))
                msg_time = msg.get('time', msg.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                
                if not phone or not message_text:
                    continue
                    
                msg_key = f"{phone}|{message_text[:50]}"
                
                if msg_key not in sent_messages_local:
                    otp_val, sms_text = extract_from_message(message_text)
                    service_name = f"[{detect_service(message_text)}]"
                    formatted_msg = format_otp_message_v2(phone, sms_text, service_name, otp_val)
                    
                    send_otp_to_user(clean_number(phone), formatted_msg, phone, None, otp_val, sms_text, service_name)
                    if True:
                        print(f"✅ {site_name} ({username}): تم إرسال الكود لـ {mask_number(phone)}")
                    
                    sent_messages_local.add(msg_key)
                    new_count += 1
            
            if new_count > 0:
                save_sent_messages()
                print(f"[{site_name}] ({username}) 📨 تم إرسال {new_count} رسالة جديدة")
            else:
                print_monitoring_box(site_name, username, "📭", "لا توجد أكواد")
            
        except Exception as e:
            if stop_event.is_set():
                break
            print_monitoring_box(site_name, username, "❌", f"خطأ غير متوقع: {str(e)}")
            time.sleep(10)
        
        if stop_event.wait(CHECK_INTERVAL5):
            break
    
    print(f"[{site_name}] ({username}) 🛑 تم إيقاف المراقبة بنجاح")

def sms_loop_requests_based(site_key, account):
    
    global account_stop_events
    
    account_id = account.get("id")
    username = account.get("username")
    password = account.get("password")
    site_name = SETTINGS[site_key]["name"]
    
    stop_key = f"{site_key}_{account_id}"
    account_stop_events[stop_key] = Event()
    stop_event = account_stop_events[stop_key]
    
    BASE_URL = SETTINGS[site_key]["base_url"]
    if not BASE_URL.startswith("http"):
        BASE_URL = "http://" + BASE_URL.lstrip(":")
    
    LOGIN_PAGE_URL = SETTINGS[site_key]["login_page_url"]
    LOGIN_POST_URL = SETTINGS[site_key]["login_post_url"]
    AJAX_PATH = SETTINGS[site_key].get("ajax_path", "/agent/res/data_smscdr.php")
    CHECK_INTERVAL = SETTINGS[site_key]["check_interval"]
    TIMEOUT_LOCAL = SETTINGS[site_key].get("timeout", 60)
    
    if "/ints" in BASE_URL:
        AJAX_URL = BASE_URL + AJAX_PATH
    elif "/ints" in AJAX_PATH:
        AJAX_URL = BASE_URL + AJAX_PATH
    else:
        AJAX_URL = BASE_URL + AJAX_PATH
    
    print(f"[{site_name}] ({username}) 🔗 AJAX URL: {AJAX_URL}")
    
    last_message_file = f"last_message_{site_key}_{account_id}.txt"
    sent_messages_file = f"sent_messages_{site_key}_{account_id}.json"
    last_seen_key_local = ""
    sent_messages_local = set()
    session = requests.Session()
    session.verify = False
    is_logged_in = False
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    })
    
    def load_last_seen():
        nonlocal last_seen_key_local
        if os.path.exists(last_message_file):
            try:
                with open(last_message_file, "r", encoding="utf-8") as f:
                    last_seen_key_local = f.read().strip()
            except:
                last_seen_key_local = ""
    
    def save_last_seen():
        try:
            with open(last_message_file, "w", encoding="utf-8") as f:
                f.write(last_seen_key_local)
        except:
            pass
    
    def load_sent_messages():
        nonlocal sent_messages_local
        if os.path.exists(sent_messages_file):
            try:
                with open(sent_messages_file, 'r') as f:
                    sent_messages_local = set(json.load(f))
            except:
                sent_messages_local = set()
    
    def save_sent_messages():
        try:
            msgs = list(sent_messages_local)[-500:]
            with open(sent_messages_file, 'w') as f:
                json.dump(msgs, f)
        except:
            pass
    
    def login():
        nonlocal is_logged_in
        print(f"[{site_name}] ({username}) 🔐 تسجيل الدخول...")
        
        try:
            resp = session.get(LOGIN_PAGE_URL, timeout=TIMEOUT_LOCAL)
            
            if resp.status_code != 200:
                print(f"[{site_name}] ({username}) ⚠️ فشل فتح صفحة الدخول: {resp.status_code}")
                return False
            
            match = re.search(r'What is (\d+) \+ (\d+)', resp.text)
            if not match:
                match = re.search(r'(\d+)\s*\+\s*(\d+)', resp.text)
            
            if not match:
                print(f"[{site_name}] ({username}) ⚠️ لم يتم العثور على Captcha، محاولة بدون captcha...")
                captcha_answer = ""
            else:
                captcha_answer = str(int(match.group(1)) + int(match.group(2)))
                print(f"[{site_name}] ({username}) 🧮 Captcha: {match.group(1)} + {match.group(2)} = {captcha_answer}")
            
            crlf_match = re.search(r"name=['\"]crlf['\"].*?value=['\"]([^'\"]+)['\"]", resp.text)
            if not crlf_match:
                crlf_match = re.search(r"value=['\"]([^'\"]+)['\"].*?name=['\"]crlf['\"]", resp.text)
            
            payload = {
                'username': username,
                'password': password,
            }
            if captcha_answer:
                payload['capt'] = captcha_answer
            
            if crlf_match and site_key != "Fly sms":
                payload['crlf'] = crlf_match.group(1)
                print(f"[{site_name}] ({username}) 🔑 تم استخراج crlf token")
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': LOGIN_PAGE_URL,
            }
            
            if site_key != "Fly sms":
                headers.update({
                    'Origin': BASE_URL.rstrip('/'),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                })
            
            resp = session.post(LOGIN_POST_URL, data=payload, headers=headers, timeout=TIMEOUT_LOCAL, allow_redirects=True)
            
            print(f"[{site_name}] ({username}) 📊 Response URL: {resp.url}")
            
            # تحسين كشف نجاح الدخول لـ Fly sms وباقي اللوحات
            success_keywords = ["dashboard", "logout", "agent", "reports", "smscdr"]
            is_success = any(kw in resp.text.lower() for kw in success_keywords) or \
                         any(kw in resp.url.lower() for kw in success_keywords) or \
                         resp.url != LOGIN_PAGE_URL
            
            if is_success:
                print(f"[{site_name}] ({username}) ✅ تسجيل الدخول نجح")
                is_logged_in = True
                return True
            
            if 'dashboard' in resp.text.lower() or 'logout' in resp.text.lower() or 'reports' in resp.url.lower():
                print(f"[{site_name}] ({username}) ✅ تسجيل الدخول نجح (dashboard detected)")
                is_logged_in = True
                return True
            
            if resp.url != LOGIN_PAGE_URL and 'login' not in resp.url.lower():
                print(f"[{site_name}] ({username}) ✅ تسجيل الدخول نجح (redirected)")
                is_logged_in = True
                return True
            
            sms_page_path = "/agent/SMSCDRReports" if "/ints" in BASE_URL else "/ints/agent/SMSCDRReports"
            test_resp = session.get(BASE_URL.rstrip('/') + sms_page_path, timeout=15)
            if test_resp.status_code == 200 and 'login' not in test_resp.url.lower():
                print(f"[{site_name}] ({username}) ✅ تسجيل الدخول نجح (verified)")
                is_logged_in = True
                return True
            
            print(f"[{site_name}] ({username}) ❌ فشل تسجيل الدخول")
            return False
            
        except Exception as e:
            print(f"[{site_name}] ({username}) ❌ خطأ في تسجيل الدخول: {e}")
            return False
    
    def get_sesskey_from_page(html_text):
        match = re.search(r'sesskey=([A-Za-z0-9=]+)', html_text)
        if match:
            return match.group(1)
        return None
    
    current_sesskey = None
    
    def fetch_sms_data():
        nonlocal is_logged_in, current_sesskey
        
        sms_page_path = "/agent/SMSCDRReports" if "/ints" in BASE_URL else "/ints/agent/SMSCDRReports"
        referer_url = BASE_URL.rstrip('/') + sms_page_path
        
        if site_key in ["GROUP", "Fly sms", "hadi", "fire", "Seven1Tel", "Gaza SMS", "Bolt", "Km sms", "Grand SMS", "Purple SMS"]:
            for retry in range(3):
                try:
                    page_resp = session.get(referer_url, timeout=TIMEOUT_LOCAL)
                    
                    if page_resp.status_code == 200:
                        if 'login' in page_resp.text.lower() and 'password' in page_resp.text.lower():
                            soup = BeautifulSoup(page_resp.text, 'html.parser')
                            login_form = soup.find('input', {'name': 'password'})
                            if login_form:
                                is_logged_in = False
                                print(f"[{site_name}] ({username}) ⚠️ الجلسة انتهت، إعادة تسجيل الدخول...")
                                return []
                        
                        sesskey = get_sesskey_from_page(page_resp.text)
                        if not sesskey and site_key in ["Fly sms", "fire"]:
                            # محاولة استخراج sesskey من أي رابط في الصفحة
                            match = re.search(r'sesskey=([A-Za-z0-9=]+)', page_resp.text)
                            if match:
                                sesskey = match.group(1)
                                print(f"[{site_name}] ({username}) 🔑 تم استخراج sesskey (طريقة بديلة)")
                        
                        if sesskey:
                            current_sesskey = sesskey
                            print(f"[{site_name}] ({username}) 🔑 تم استخراج sesskey")
                            
                            today = datetime.now().strftime('%Y-%m-%d')
                            ajax_url = BASE_URL + AJAX_PATH
                            
                            payload = {
                                'fdate1': f'{today} 00:00:00',
                                'fdate2': f'{today} 23:59:59',
                                'frange': '',
                                'fclient': '',
                                'fnum': '',
                                'fcli': '',
                                'fgdate': '',
                                'fgmonth': '',
                                'fgrange': '',
                                'fgclient': '',
                                'fgnumber': '',
                                'fgcli': '',
                                'fg': '0',
                                'sesskey': sesskey
                            }
                            
                            ajax_headers = {
                                'Accept': 'application/json, text/javascript, */*; q=0.01',
                                'X-Requested-With': 'XMLHttpRequest',
                                'Referer': referer_url,
                                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                            }
                            
                            if site_key in ["Fly sms", "fire"]:
                                ajax_resp = session.post(ajax_url, data=payload, headers=ajax_headers, timeout=TIMEOUT_LOCAL)
                            else:
                                ajax_resp = session.get(ajax_url, params=payload, headers=ajax_headers, timeout=TIMEOUT_LOCAL)
                            
                            if ajax_resp.status_code == 200:
                                try:
                                    data = ajax_resp.json()
                                    if 'aaData' in data:
                                        rows = data['aaData']
                                        if rows:
                                            print(f"[{site_name}] ({username}) ✅ تم جلب {len(rows)} رسالة عبر AJAX")
                                            return rows
                                    elif isinstance(data, list):
                                        if data:
                                            print(f"[{site_name}] ({username}) ✅ تم جلب {len(data)} رسالة عبر AJAX")
                                            return data
                                except:
                                    pass
                        
                        soup = BeautifulSoup(page_resp.text, 'html.parser')
                        table = soup.find('table')
                        if table:
                            tbody = table.find('tbody')
                            rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]
                            data_rows = []
                            for row in rows:
                                cells = row.find_all('td')
                                if len(cells) >= 6:
                                    data_rows.append([cell.get_text(strip=True) for cell in cells])
                            if data_rows:
                                print(f"[{site_name}] ({username}) 📄 استخدام HTML parsing كبديل")
                                return data_rows
                        return []
                        
                    elif page_resp.status_code in [502, 503, 504]:
                        if retry < 2:
                            print(f"[{site_name}] ({username}) ⚠️ السيرفر مشغول ({page_resp.status_code}) - محاولة {retry+1}/3...")
                            time.sleep(3 + retry * 2)
                            continue
                        print(f"[{site_name}] ({username}) ⚠️ السيرفر مشغول ({page_resp.status_code})")
                        return []
                    else:
                        print(f"[{site_name}] ({username}) ⚠️ HTTP {page_resp.status_code}")
                        return []
                    
                except Exception as e:
                    if retry < 2 and ('Connection' in str(e) or 'Timeout' in str(e)):
                        time.sleep(2)
                        continue
                    print(f"[{site_name}] ({username}) ❌ خطأ في جلب البيانات: {e}")
                    is_logged_in = False
                    return []
            return []
        
        for retry in range(3):
            try:
                headers = {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Referer': referer_url,
                    'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
                }
                
                today = datetime.now()
                start_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
                end_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
                
                payload = {
                    'fdate1': f'{start_date} 00:00:00',
                    'fdate2': f'{end_date} 23:59:59',
                    'frange': '',
                    'fclient': '',
                    'fnum': '',
                    'fcli': '',
                    'fgdate': '',
                    'fgmonth': '',
                    'fgrange': '',
                    'fgclient': '',
                    'fgnumber': '',
                    'fgcli': '',
                    'fg': '0',
                    'sEcho': '1',
                    'iColumns': '8',
                    'sColumns': '',
                    'iDisplayStart': '0',
                    'iDisplayLength': '100',
                    'mDataProp_0': '0',
                    'mDataProp_1': '1',
                    'mDataProp_2': '2',
                    'mDataProp_3': '3',
                    'mDataProp_4': '4',
                    'mDataProp_5': '5',
                    'mDataProp_6': '6',
                    'mDataProp_7': '7',
                    'sSearch': '',
                    'bRegex': 'false',
                    'iSortCol_0': '0',
                    'sSortDir_0': 'desc',
                    'iSortingCols': '1'
                }
                
                resp = session.post(AJAX_URL, data=payload, headers=headers, timeout=TIMEOUT_LOCAL)
                
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        for key in ['data', 'aaData', 'rows']:
                            if key in data and isinstance(data[key], list):
                                return data[key]
                        is_logged_in = False
                    except Exception as je:
                        if 'login' in resp.text.lower() or 'signin' in resp.text.lower():
                            is_logged_in = False
                            print(f"[{site_name}] ({username}) ⚠️ الجلسة انتهت، إعادة تسجيل الدخول...")
                        else:
                            try:
                                soup = BeautifulSoup(resp.text, 'html.parser')
                                table = soup.find('table')
                                if table:
                                    tbody = table.find('tbody')
                                    rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]
                                    data_rows = []
                                    for row in rows:
                                        cells = row.find_all('td')
                                        if len(cells) >= 6:
                                            data_rows.append([cell.get_text(strip=True) for cell in cells])
                                    if data_rows:
                                        print(f"[{site_name}] ({username}) 📄 استخدام HTML parsing")
                                        return data_rows
                            except:
                                pass
                elif resp.status_code == 503:
                    if retry < 2:
                        time.sleep(3 + retry * 2)
                        continue
                    print(f"[{site_name}] ({username}) ⚠️ السيرفر مشغول (503) - جاري المحاولة بطريقة بديلة...")
                    try:
                        page_resp = session.get(referer_url, timeout=TIMEOUT_LOCAL)
                        if page_resp.status_code == 200:
                            soup = BeautifulSoup(page_resp.text, 'html.parser')
                            table = soup.find('table')
                            if table:
                                tbody = table.find('tbody')
                                rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]
                                data_rows = []
                                for row in rows:
                                    cells = row.find_all('td')
                                    if len(cells) >= 6:
                                        data_rows.append([cell.get_text(strip=True) for cell in cells])
                                if data_rows:
                                    print(f"[{site_name}] ({username}) 📄 استخدام HTML parsing (بديل)")
                                    return data_rows
                    except Exception as html_e:
                        print(f"[{site_name}] ({username}) ⚠️ فشل HTML parsing: {html_e}")
                else:
                    print(f"[{site_name}] ({username}) ⚠️ HTTP {resp.status_code}")
                
                return []
                
            except Exception as e:
                if retry < 2 and ('Connection' in str(e) or 'Timeout' in str(e)):
                    time.sleep(2)
                    continue
                print(f"[{site_name}] ({username}) ❌ خطأ في جلب البيانات: {e}")
                is_logged_in = False
                return []
        return []
    
    print_monitoring_box(site_name, username, "🚀", "بدء المراقبة بـ Requests (خفيف وسريع)...")
    
    load_last_seen()
    load_sent_messages()
    
    if not login():
        print_monitoring_box(site_name, username, "❌", "فشل تسجيل الدخول الأولي")
        return
    
    errors = 0
    print(f"[{site_name}] ({username}) ✅ بدء المراقبة كل {CHECK_INTERVAL} ثانية...")
    
    while not stop_event.is_set():
        try:
            if stop_event.is_set():
                break
            
            if not is_logged_in:
                if not login():
                    time.sleep(30)
                    continue
            
            raw_data = fetch_sms_data()
            
            if not raw_data:
                print_monitoring_box(site_name, username, "📭", "لا توجد أكواد")
            else:
                data = []
                for row in raw_data:
                    if isinstance(row, list) and len(row) >= 6:
                        # Fly sms أحياناً بتغير ترتيب الأعمدة، فبنتأكد من سحب البيانات صح
                        if site_key == "Fly sms":
                            date_str = str(row[0]).strip() if row[0] else ""
                            number = re.sub(r'\D', '', str(row[2])) if row[2] else ""
                            # في Fly sms الرسالة أحياناً بتكون في العمود 5 أو 6
                            sms = str(row[5]).strip() if len(row) > 5 and row[5] else ""
                            if not sms and len(row) > 6:
                                sms = str(row[6]).strip()
                        else:
                            date_str = str(row[0]).strip() if row[0] else ""
                            number = re.sub(r'\D', '', str(row[2])) if row[2] else ""
                            sms = str(row[5]).strip() if row[5] else ""
                        
                        if date_str and number and len(number) >= 7 and sms:
                            
                            # فلترة أقل تشدداً لـ Fly sms لضمان وصول الأكواد
                            if site_key == "Fly sms":
                                if any(x in sms.lower() for x in ["currency", "payout", "nan%", "100%", "0.008"]):
                                    continue
                            else:
                                if any(x in sms.lower() for x in ["currency", "payout", "nan%", "100%", "0.008", "my payout", "client payout", "range", "number", "cli", "client"]):
                                    continue
                            
                            if site_key != "Fly sms":
                                if sms.count(',') >= 5 and ('%' in sms or 'nan' in sms.lower()):
                                    continue

                            
                            otp_val, _ = extract_from_message(sms)
                            if not otp_val and len(sms) < 5: 
                                continue
                                
                            data.append({'date': date_str, 'number': number, 'sms': sms})
                
                if not data:
                    print_monitoring_box(site_name, username, "📭", "لا توجد أكواد")
                else:
                    data.sort(key=lambda x: x['date'], reverse=False) 
                    
                    new_messages = []
                    for msg in data:
                        key = f"{msg['date']}|{msg['number']}"
                        # Fly sms أحياناً بتبعت الرسايل بترتيب عشوائي، فبنعتمد على الـ sent_messages_local أكتر
                        if site_key == "Fly sms":
                            # بنعمل مفتاح فريد أكتر بالرسالة نفسها عشان لو الرقم جاله كودين ورا بعض
                            unique_key = f"{msg['date']}|{msg['number']}|{msg['sms'][:20]}"
                            if unique_key not in sent_messages_local:
                                new_messages.append(msg)
                                sent_messages_local.add(unique_key)
                        else:
                            if key == last_seen_key_local:
                                new_messages = [] 
                                continue
                            if key not in sent_messages_local:
                                new_messages.append(msg)
                    
                    if new_messages:
                        print(f"[{site_name}] ({username}) 📨 {len(new_messages)} رسالة جديدة")
                        
                        
                        for msg in new_messages:
                            date_str = msg['date']
                            number = msg['number']
                            sms = msg['sms']
                            
                            otp_val, sms_text = extract_from_message(sms)
                            service_name = f"[{detect_service(sms)}]"
                            formatted_msg = format_otp_message_v2(number, sms_text, service_name, otp_val)
                            
                            if otp_val:
                                print(f"🔑 {site_name} ({username}): لقيت كود {otp_val}")
                            
                            send_otp_to_user(clean_number(number), formatted_msg, number, None, otp_val, sms_text, service_name)
                            # المفتاح الفريد تم إضافته بالفعل فوق
                            last_seen_key_local = f"{date_str}|{number}"
                        
                        save_last_seen()
                        save_sent_messages()
                    else:
                        print_monitoring_box(site_name, username, "📭", "لا توجد أكواد")
            
            errors = 0
            
        except Exception as e:
            errors += 1
            print_monitoring_box(site_name, username, "❌", f"خطأ ({errors}/5): {str(e)[:40]}")
            if errors >= 5:
                print(f"[{site_name}] ({username}) 🔄 إعادة تسجيل الدخول...")
                if login():
                    errors = 0
                else:
                    time.sleep(30)
            time.sleep(5)
        
        if stop_event.wait(CHECK_INTERVAL):
            break
    
    print(f"[{site_name}] ({username}) 🛑 تم إيقاف المراقبة")

def login_site8(account):
    username = account.get("username")
    password = account.get("password")
    
    
    session = requests.Session()
    session.verify = False
    
    print(f"[Site8/IMS] ({username}) 🔄 تسجيل الدخول...")
    try:
       
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        })
        
        response = session.get(LOGIN_PAGE_URL8, timeout=HTTP_TIMEOUT8)
        if response.status_code == 403:
            
            response = session.get(LOGIN_PAGE_URL8, timeout=HTTP_TIMEOUT8, headers={"User-Agent": "Mozilla/5.0"})
        
        if response.status_code != 200:
            print(f"[Site8/IMS] ({username}) [!] فشل فتح صفحة الدخول: {response.status_code}")
            return False, None
        
        html_content = response.text
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        csrf_token = None
        csrf_input = soup.find('input', {'name': '_token'})
        if csrf_input:
            csrf_token = str(csrf_input.get('value'))
        if not csrf_token:
            csrf_input = soup.find('input', {'name': 'csrf_token'})
            if csrf_input:
                csrf_token = str(csrf_input.get('value'))
        if not csrf_token:
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if csrf_meta:
                csrf_token = str(csrf_meta.get('content'))
        if not csrf_token:
            match = re.search(r'name=["\']_token["\'].*?value=["\']([^"\']+)["\']', html_content)
            if match:
                csrf_token = match.group(1)
        
        if csrf_token:
            print(f"[Site8/IMS] ({username}) [*] CSRF Token: {csrf_token[:20]}...")
        
        
        captcha_answer = None
        
        patterns = [
            r'(\d+)\s*\+\s*(\d+)\s*=', 
            r'What is (\d+) \+ (\d+)', 
            r'(\d+)\s*plus\s*(\d+)'
        ]
        
        
        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                captcha_answer = str(int(match.group(1)) + int(match.group(2)))
                break
        
        
        if not captcha_answer:
            b_tags = soup.find_all('b')
            nums = []
            for b in b_tags:
                text = b.get_text().strip()
                if text.isdigit():
                    nums.append(int(text))
            if len(nums) >= 2:
                captcha_answer = str(nums[0] + nums[1])
        
        if not captcha_answer:
            
            text = soup.get_text()
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    captcha_answer = str(int(match.group(1)) + int(match.group(2)))
                    break
        
        if not captcha_answer:
            print(f"[Site8/IMS] ({username}) [!] لم يتم العثور على الكابتشا")
            return False, None
        
        print(f"[Site8/IMS] ({username}) [*] Captcha: {captcha_answer}")
        
        login_data = {
            "username": username,
            "password": password,
            "capt": captcha_answer,
        }
        
        if csrf_token:
            login_data["_token"] = csrf_token
        
        form = soup.find('form')
        if form:
            for hidden in form.find_all('input', type='hidden'):
                name = hidden.get('name')
                value = hidden.get('value')
                if name and isinstance(name, str) and name not in login_data:
                    login_data[name] = str(value) if value is not None else ''

        
        login_headers = {
            "Referer": LOGIN_PAGE_URL8,
            "Origin": BASE_URL8,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = session.post(
            LOGIN_POST_URL8,
            data=login_data,
            headers=login_headers,
            timeout=HTTP_TIMEOUT8,
            allow_redirects=True
        )
        
        print(f"[Site8/IMS] ({username}) [DEBUG] Final URL: {response.url}")
        
        if any(x in response.url.lower() for x in ["/agent", "/dashboard", "/home"]) or \
           (response.status_code == 200 and "login" not in response.url.lower() and "signin" not in response.url.lower()):
            print(f"[Site8/IMS] ({username}) [+] تسجيل الدخول نجح (Landed on: {response.url})")
            return True, session
        
        content_lower = response.text.lower()
        if "logout" in content_lower or "smscdr" in content_lower or "agent" in content_lower:
            print(f"[Site8/IMS] ({username}) [+] تسجيل الدخول نجح (Detected via content)")
            return True, session

        print(f"[Site8/IMS] ({username}) [!] فشل تسجيل الدخول")
        return False, None
    except Exception as e:
        print(f"[Site8/IMS] ({username}) [!] خطأ في تسجيل الدخول: {e}")
        return False, None

def sms_loop_for_ims_account(site_key, account):
    site_name = SETTINGS[site_key]["name"]
    username = account.get("username")
    password = account.get("password")
    account_id = account.get("id")
    stop_event = account_stop_events.get(f"{site_key}_{account_id}", Event())
    
    session = requests.Session()
    session.verify = False
    is_logged_in = False
    
    last_message_file = f"last_message_{site_key}_{account_id}.txt"
    last_seen_key_local = ""
    
    def load_last_seen():
        nonlocal last_seen_key_local
        if os.path.exists(last_message_file):
            try:
                with open(last_message_file, "r", encoding="utf-8") as f:
                    last_seen_key_local = f.read().strip()
            except: pass
    def save_last_seen():
        try:
            with open(last_message_file, "w", encoding="utf-8") as f:
                f.write(last_seen_key_local)
        except: pass

    print_monitoring_box(site_name, username, "🚀", "بدء المراقبة...")
    
    success, new_session = login_site8(account)
    if success:
        session = new_session
        is_logged_in = True
    else:
        print_monitoring_box(site_name, username, "❌", "فشل تسجيل الدخول")
    
    load_last_seen()
    errors = 0
    
    while not stop_event.is_set():
        try:
            
            current_account = get_account_by_id(site_key, account_id)
            if current_account and current_account.get("password") != password:
                print(f"[Site8/IMS] ({username}) 🔑 تم اكتشاف تغيير كلمة المرور، جاري إعادة الدخول...")
                password = current_account.get("password")
                success, new_session = login_site8(current_account)
                if success:
                    session = new_session
                    is_logged_in = True
                else:
                    is_logged_in = False
                    time.sleep(30)
                    continue

            if not is_logged_in:
                success, new_session = login_site8(current_account or account)
                if success:
                    session = new_session
                    is_logged_in = True
                else:
                    time.sleep(30)
                    continue

            today = datetime.now().strftime('%Y-%m-%d')
            
            codes_html = ""
            try:
                resp_codes = session.get(BASE_URL8 + "/ints/agent/SMSCDRReports", timeout=HTTP_TIMEOUT8)
                codes_html = resp_codes.text
                if 'login' in resp_codes.url.lower():
                    is_logged_in = False
                    continue
            except Exception as e:
                print(f"[Site8/IMS] ({username}) [!] Error loading codes page: {e}")
                is_logged_in = False
                continue

            sesskey = ""
            sesskey_match = re.search(r'sesskey=([A-Za-z0-9=]+)', codes_html)
            if sesskey_match:
                sesskey = sesskey_match.group(1)
            else:
                is_logged_in = False
                continue

            params = {
                'fdate1': f'{today} 00:00:00',
                'fdate2': f'{today} 23:59:59',
                'frange': '', 'fclient': '', 'fnum': '', 'fcli': '',
                'fgdate': '', 'fgmonth': '', 'fgrange': '', 'fgclient': '',
                'fgnumber': '', 'fgcli': '', 'fg': '0', 'sesskey': sesskey
            }

            ajax_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': BASE_URL8 + "/ints/agent/SMSCDRReports"
            }
            
            r = session.get("http://45.82.67.20/ints/agent/res/data_smscdr.php", params=params, headers=ajax_headers, timeout=HTTP_TIMEOUT8)
            
            if r.status_code != 200 or 'login' in r.url.lower():
                is_logged_in = False
                continue

            data_json = r.json()
            if data_json.get('aaData'):
                rows = data_json['aaData']
            else:
                rows = data_json if isinstance(data_json, list) else []
            
            if not rows:
                print_monitoring_box(site_name, username, "📭", "لا توجد أكواد")
            else:
                
                try:
                    rows.sort(key=lambda x: str(x[0]) if isinstance(x, list) and len(x) > 0 else "", reverse=True)
                except:
                    pass

                new_messages = []
                for row in rows:
                    if isinstance(row, list) and len(row) >= 6:
                        date_str = str(row[0]).strip()
                        number = re.sub(r'\D', '', str(row[2]))
                        sms = str(row[5]).strip()
                        
                        
                        if sms.count(',') > 3 or sms.count('%') > 1 or 'NAN%' in sms:
                            continue
                        
                        
                        if re.match(r'^[\d.,%|NAN/]+$', sms):
                            continue
                            
                        key = f"{date_str}|{number}"
                        if key == last_seen_key_local: break
                        new_messages.append({'date': date_str, 'number': number, 'sms': sms})
                
                if new_messages:
                    
                    last_seen_key_local = f"{new_messages[0]['date']}|{new_messages[0]['number']}"
                    save_last_seen()
                    
                    print(f"[{site_name}] ({username}) 📨 {len(new_messages)} رسالة جديدة")
                   
                    
                    for msg in reversed(new_messages):
                        otp_val, sms_text = extract_from_message(msg['sms'])
                        
                        
                        service_name = f"[{detect_service(sms_text)}]"
                        formatted_msg = format_otp_message_v2(msg['number'], sms_text, service_name, otp_val)
                        
                        print(f"🔑 {site_name} ({username}): لقيت كود {otp_val}")
                        
                        success = False
                        for retry in range(3):
                            try:
                                send_otp_to_user(clean_number(msg['number']), formatted_msg, msg['number'], None, otp_val, sms_text, service_name)
                                success = True
                                break
                            except Exception as e:
                                if "429" in str(e):
                                    wait_time = 35 
                                    match = re.search(r'after (\d+)', str(e))
                                    if match: wait_time = int(match.group(1)) + 2
                                    print(f"⚠️ Telegram 429 (Flood Control): Waiting {wait_time}s...")
                                    time.sleep(wait_time)
                                else:
                                    print(f"❌ Error sending: {e}")
                                    break
                else:
                    print_monitoring_box(site_name, username, "📭", "لا توجد أكواد")
            
            errors = 0
        except Exception as e:
            errors += 1
            if errors >= 5:
                is_logged_in = False
            time.sleep(10)

        if stop_event.wait(SETTINGS[site_key].get("check_interval", 16)):
            break



# ═══════════════════════════════════════════════════
# Grand SMS - دالة المراقبة
# ═══════════════════════════════════════════════════
def sms_loop_for_grand_sms_account(site_key, account):
    site_name = SETTINGS[site_key]["name"]
    username = account.get("username")
    password = account.get("password")
    account_id = account.get("id")
    stop_event = account_stop_events.get(f"{site_key}_{account_id}", Event())

    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    is_logged_in = False

    last_message_file = f"last_message_{site_key}_{account_id}.txt"
    last_seen_key_local = ""

    def load_last_seen():
        nonlocal last_seen_key_local
        if os.path.exists(last_message_file):
            try:
                with open(last_message_file, "r", encoding="utf-8") as f:
                    last_seen_key_local = f.read().strip()
            except: pass

    def save_last_seen():
        try:
            with open(last_message_file, "w", encoding="utf-8") as f:
                f.write(last_seen_key_local)
        except: pass

    print_monitoring_box(site_name, username, "🚀", "بدء المراقبة...")
    load_last_seen()

    base_url = SETTINGS[site_key]["base_url"]
    login_url = SETTINGS[site_key]["login_page_url"]
    submit_url = SETTINGS[site_key]["login_post_url"]

    while not stop_event.is_set():
        try:
            if not is_logged_in:
                try:
                    resp = sess.get(login_url, timeout=SETTINGS[site_key].get("timeout", 30))
                    # حل الكابتشا لو موجودة
                    captcha = None
                    match_cap = re.search(r'What is (\d+) \+ (\d+)', resp.text)
                    if match_cap:
                        captcha = str(int(match_cap.group(1)) + int(match_cap.group(2)))
                    # استخراج CSRF token
                    csrf = None
                    csrf_match = re.search(r'name=["\']_token["\'][^>]*value=["\']([^"\']+)["\']', resp.text) or \
                                 re.search(r'value=["\']([^"\']+)["\'][^>]*name=["\']_token["\']', resp.text)
                    if csrf_match:
                        csrf = csrf_match.group(1)
                    # بناء بيانات الدخول
                    login_data = {"username": username, "password": password}
                    if captcha:
                        login_data["capt"] = captcha
                    if csrf:
                        login_data["_token"] = csrf
                    # محاولة الدخول
                    login_headers = {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Referer": login_url,
                        "Origin": base_url
                    }
                    r = sess.post(submit_url, data=login_data, headers=login_headers,
                                  timeout=SETTINGS[site_key].get("timeout", 30), allow_redirects=True)
                    if any(k in r.text.lower() for k in ["dashboard", "logout", "agent", "smscdr"]) or \
                       any(k in r.url.lower() for k in ["dashboard", "agent", "reports"]) or \
                       ("login" not in r.url.lower() and "signin" not in r.url.lower() and r.url != login_url):
                        is_logged_in = True
                        print_monitoring_box(site_name, username, "✅", "تم تسجيل الدخول بنجاح")
                    else:
                        print_monitoring_box(site_name, username, "❌", "فشل تسجيل الدخول")
                        time.sleep(30)
                        continue
                except Exception as e:
                    print(f"[{site_name}] Login error: {e}")
                    time.sleep(30)
                    continue

            # جلب الرسائل
            today = datetime.now()
            fdate1 = today.strftime('%Y-%m-%d') + " 00:00:00"
            fdate2 = today.strftime('%Y-%m-%d') + " 23:59:59"
            ajax_url = base_url + SETTINGS[site_key].get("ajax_path", "/ints/agent/res/data_smscdr.php")
            params = {
                'fdate1': fdate1, 'fdate2': fdate2,
                'fg': '0', 'sEcho': '1',
                'iDisplayStart': '0', 'iDisplayLength': '500',
                'iSortCol_0': '0', 'sSortDir_0': 'desc'
            }
            r = sess.get(ajax_url, params=params, headers={
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': base_url + "/ints/agent/SMSCDRReports"
            }, timeout=SETTINGS[site_key].get("timeout", 30))

            if r.status_code != 200 or 'login' in r.url.lower():
                is_logged_in = False
                continue

            try:
                data = r.json()
            except Exception as e:
                print(f"[{site_name}] JSON Error: {e} | Response: {r.text[:200]}")
                is_logged_in = False
                continue

            rows = data.get('aaData', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

            if rows:
                new_messages = []
                try:
                    rows.sort(key=lambda x: str(x[0]).strip() if len(x) > 0 else "", reverse=True)
                except: pass

                for row in rows:
                    if len(row) >= 6:
                        msg_date = str(row[0]).strip()
                        msg_num = re.sub(r'\D', '', str(row[2]))
                        msg_text = str(row[5]).strip()
                        if not re.match(r'\d{4}-\d{2}-\d{2}', msg_date):
                            continue
                        if msg_text == "$" or len(msg_text) < 2:
                            for idx in [4, 6, 3]:
                                if len(row) > idx:
                                    pot = str(row[idx]).strip()
                                    if pot and pot != "$":
                                        msg_text = pot
                                        break
                        msg_key = f"{msg_date}_{msg_num}_{msg_text[:20]}"
                        if msg_key == last_seen_key_local:
                            break
                        new_messages.append({'date': msg_date, 'number': msg_num, 'sms': msg_text, 'key': msg_key})

                if new_messages:
                    is_initial = not os.path.exists(last_message_file) or os.path.getsize(last_message_file) == 0
                    last_seen_key_local = new_messages[0]['key']
                    save_last_seen()
                    if is_initial:
                        print_monitoring_box(site_name, username, "🔔", "تم بدء المراقبة: جلب أحدث كود فقط")
                        msgs_to_process = [new_messages[0]]
                    else:
                        print_monitoring_box(site_name, username, "🔔", f"لقيت {len(new_messages)} كود جديد")
                        msgs_to_process = list(reversed(new_messages))
                    for msg in msgs_to_process:
                        otp_val, clean_sms = extract_from_message(msg['sms'])
                        service_name = f"[{detect_service(clean_sms)}]"
                        formatted = format_otp_message_v2(msg['number'], clean_sms, service_name, otp_val)
                        send_otp_to_user(clean_number(msg['number']), formatted, msg['number'], None, otp_val, clean_sms, service_name)
                else:
                    print_monitoring_box(site_name, username, "📭", "لا توجد أكواد جديدة")
            else:
                print_monitoring_box(site_name, username, "📭", "لا توجد أكواد")

        except Exception as e:
            print(f"[{site_name}] Error: {e}")
            is_logged_in = False
            time.sleep(10)

        if stop_event.wait(SETTINGS[site_key].get("check_interval", 5)):
            break


# ═══════════════════════════════════════════════════
# Purple SMS - دالة المراقبة
# ═══════════════════════════════════════════════════
def sms_loop_for_purple_sms_account(site_key, account):
    site_name = SETTINGS[site_key]["name"]
    username = account.get("username")
    password = account.get("password")
    account_id = account.get("id")
    stop_event = account_stop_events.get(f"{site_key}_{account_id}", Event())

    sess = requests.Session()
    sess.verify = False
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    is_logged_in = False

    last_message_file = f"last_message_{site_key}_{account_id}.txt"
    last_seen_key_local = ""

    def load_last_seen():
        nonlocal last_seen_key_local
        if os.path.exists(last_message_file):
            try:
                with open(last_message_file, "r", encoding="utf-8") as f:
                    last_seen_key_local = f.read().strip()
            except: pass

    def save_last_seen():
        try:
            with open(last_message_file, "w", encoding="utf-8") as f:
                f.write(last_seen_key_local)
        except: pass

    print_monitoring_box(site_name, username, "🚀", "بدء المراقبة...")
    load_last_seen()

    base_url = SETTINGS[site_key]["base_url"]
    login_url = SETTINGS[site_key]["login_page_url"]
    submit_url = SETTINGS[site_key]["login_post_url"]

    while not stop_event.is_set():
        try:
            if not is_logged_in:
                try:
                    resp = sess.get(login_url, timeout=SETTINGS[site_key].get("timeout", 30), verify=False)
                    # استخراج CSRF/hidden tokens
                    csrf = None
                    soup_login = BeautifulSoup(resp.text, 'html.parser')
                    csrf_inp = soup_login.find('input', {'name': '_token'}) or \
                               soup_login.find('input', {'name': 'csrf_token'})
                    if csrf_inp:
                        csrf = csrf_inp.get('value')
                    if not csrf:
                        csrf_m = re.search(r'name=["\']_token["\'][^>]*value=["\']([^"\']+)["\']', resp.text) or \
                                 re.search(r'value=["\']([^"\']+)["\'][^>]*name=["\']_token["\']', resp.text)
                        if csrf_m:
                            csrf = csrf_m.group(1)

                    # حل الكابتشا لو موجودة
                    captcha = None
                    cap_m = re.search(r'What is (\d+) \+ (\d+)', resp.text) or \
                            re.search(r'(\d+)\s*\+\s*(\d+)\s*=', resp.text)
                    if cap_m:
                        captcha = str(int(cap_m.group(1)) + int(cap_m.group(2)))

                    login_data = {"username": username, "password": password}
                    if captcha:
                        login_data["capt"] = captcha
                    if csrf:
                        login_data["_token"] = csrf

                    # جمع hidden inputs تانية
                    form = soup_login.find('form')
                    if form:
                        for hidden in form.find_all('input', type='hidden'):
                            nm = hidden.get('name')
                            val = hidden.get('value', '')
                            if nm and nm not in login_data:
                                login_data[nm] = str(val) if val else ''

                    login_headers = {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Referer": login_url,
                        "Origin": base_url
                    }
                    r = sess.post(submit_url, data=login_data, headers=login_headers,
                                  timeout=SETTINGS[site_key].get("timeout", 30), allow_redirects=True, verify=False)
                    if any(k in r.text.lower() for k in ["dashboard", "logout", "agent", "smscdr"]) or \
                       any(k in r.url.lower() for k in ["dashboard", "agent", "reports", "sms"]) or \
                       ("signin" not in r.url.lower() and "login" not in r.url.lower() and r.url != login_url):
                        is_logged_in = True
                        print_monitoring_box(site_name, username, "✅", "تم تسجيل الدخول بنجاح")
                    else:
                        print_monitoring_box(site_name, username, "❌", "فشل تسجيل الدخول")
                        time.sleep(30)
                        continue
                except Exception as e:
                    print(f"[{site_name}] Login error: {e}")
                    time.sleep(30)
                    continue

            # جلب الرسائل - نجرب مسارات مختلفة
            today = datetime.now()
            fdate1 = today.strftime('%Y-%m-%d') + " 00:00:00"
            fdate2 = today.strftime('%Y-%m-%d') + " 23:59:59"

            # المسار الأساسي من الإعدادات
            ajax_path = SETTINGS[site_key].get("ajax_path", "/sms/agent/res/data_smscdr.php")
            ajax_url = base_url + ajax_path

            params = {
                'fdate1': fdate1, 'fdate2': fdate2,
                'fg': '0', 'sEcho': '1',
                'iDisplayStart': '0', 'iDisplayLength': '500',
                'iSortCol_0': '0', 'sSortDir_0': 'desc'
            }
            ajax_headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': base_url + "/sms/agent/SMSCDRReports"
            }

            try:
                r = sess.get(ajax_url, params=params, headers=ajax_headers,
                             timeout=SETTINGS[site_key].get("timeout", 30), verify=False)
            except Exception as e:
                print(f"[{site_name}] Request error: {e}")
                is_logged_in = False
                time.sleep(10)
                continue

            if r.status_code != 200 or 'login' in r.url.lower() or 'signin' in r.url.lower():
                is_logged_in = False
                continue

            try:
                data = r.json()
            except Exception as e:
                print(f"[{site_name}] JSON Error: {e} | Response: {r.text[:300]}")
                is_logged_in = False
                continue

            rows = data.get('aaData', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

            if rows:
                new_messages = []
                try:
                    rows.sort(key=lambda x: str(x[0]).strip() if len(x) > 0 else "", reverse=True)
                except: pass

                for row in rows:
                    if len(row) >= 6:
                        msg_date = str(row[0]).strip()
                        msg_num = re.sub(r'\D', '', str(row[2]))
                        msg_text = str(row[5]).strip()
                        if not re.match(r'\d{4}-\d{2}-\d{2}', msg_date):
                            continue
                        if msg_text == "$" or len(msg_text) < 2:
                            for idx in [4, 6, 3]:
                                if len(row) > idx:
                                    pot = str(row[idx]).strip()
                                    if pot and pot != "$":
                                        msg_text = pot
                                        break
                        msg_key = f"{msg_date}_{msg_num}_{msg_text[:20]}"
                        if msg_key == last_seen_key_local:
                            break
                        new_messages.append({'date': msg_date, 'number': msg_num, 'sms': msg_text, 'key': msg_key})

                if new_messages:
                    is_initial = not os.path.exists(last_message_file) or os.path.getsize(last_message_file) == 0
                    last_seen_key_local = new_messages[0]['key']
                    save_last_seen()
                    if is_initial:
                        print_monitoring_box(site_name, username, "🔔", "تم بدء المراقبة: جلب أحدث كود فقط")
                        msgs_to_process = [new_messages[0]]
                    else:
                        print_monitoring_box(site_name, username, "🔔", f"لقيت {len(new_messages)} كود جديد")
                        msgs_to_process = list(reversed(new_messages))
                    for msg in msgs_to_process:
                        otp_val, clean_sms = extract_from_message(msg['sms'])
                        service_name = f"[{detect_service(clean_sms)}]"
                        formatted = format_otp_message_v2(msg['number'], clean_sms, service_name, otp_val)
                        send_otp_to_user(clean_number(msg['number']), formatted, msg['number'], None, otp_val, clean_sms, service_name)
                else:
                    print_monitoring_box(site_name, username, "📭", "لا توجد أكواد جديدة")
            else:
                print_monitoring_box(site_name, username, "📭", "لا توجد أكواد")

        except Exception as e:
            print(f"[{site_name}] Error: {e}")
            is_logged_in = False
            time.sleep(10)

        if stop_event.wait(SETTINGS[site_key].get("check_interval", 5)):
            break


def start_monitoring_for_account(site_key, account):
    
    if site_key == "Number_Panel":
        sms_loop_for_number_panel_account(site_key, account)
    elif site_key == "iVASMS":
        sms_loop_for_ivasms_account(site_key, account)
    elif site_key == "IMS":
        sms_loop_for_ims_account(site_key, account)
    elif site_key == "Roxy SMS":
        sms_loop_for_roxy_account(site_key, account)
    elif site_key == "TimeSMS":
        sms_loop_for_timesms_account(site_key, account)
    elif site_key == "Konekta":
        sms_loop_for_konekta_account(site_key, account)
    elif site_key == "Grand SMS":
        sms_loop_for_grand_sms_account(site_key, account)
    elif site_key == "Purple SMS":
        sms_loop_for_purple_sms_account(site_key, account)
    else:
        sms_loop_requests_based(site_key, account)


def sms_loop_for_timesms_account(site_key, account):
    site_name = SETTINGS[site_key]["name"]
    username = account.get("username")
    password = account.get("password")
    account_id = account.get("id")
    stop_event = account_stop_events.get(f"{site_key}_{account_id}", Event())
    
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    is_logged_in = False
    
    last_message_file = f"last_message_{site_key}_{account_id}.txt"
    last_seen_key_local = ""
    
    def load_last_seen():
        nonlocal last_seen_key_local
        if os.path.exists(last_message_file):
            try:
                with open(last_message_file, "r", encoding="utf-8") as f:
                    last_seen_key_local = f.read().strip()
            except: pass
    def save_last_seen():
        try:
            with open(last_message_file, "w", encoding="utf-8") as f:
                f.write(last_seen_key_local)
        except: pass

    print_monitoring_box(site_name, username, "🚀", "بدء المراقبة...")
    load_last_seen()
    
    base_url = SETTINGS[site_key]["base_url"]
    login_url = SETTINGS[site_key]["login_page_url"]
    submit_url = SETTINGS[site_key]["login_post_url"]
    smscdr_page_url = base_url + "/agent/SMSCDRReports"
    ajax_url = base_url + "/agent/res/data_smscdr.php"
    current_sesskey = None
    
    while not stop_event.is_set():
        try:
            if not is_logged_in:
                resp = sess.get(login_url, timeout=15)
                captcha = solve_captcha_timesms(resp.text)
                if captcha:
                    csrf_token = None
                    cm = re.search(r"""name=["']_token["'][^>]*value=["']([^"']+)["']""", resp.text) or \
                         re.search(r"""value=["']([^"']+)["'][^>]*name=["']_token["']""", resp.text)
                    if cm:
                        csrf_token = cm.group(1)
                    login_data = {'username': username, 'password': password, 'capt': captcha}
                    if csrf_token:
                        login_data['_token'] = csrf_token
                    login_headers = {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Origin': base_url,
                        'Referer': login_url,
                    }
                    login_resp = sess.post(submit_url, data=login_data, headers=login_headers, timeout=15, allow_redirects=True)
                    final_url = str(login_resp.url).lower()
                    if 'agent' in final_url or ('login' not in final_url and 'signin' not in final_url):
                        is_logged_in = True
                        print_monitoring_box(site_name, username, "✅", "تم تسجيل الدخول بنجاح")
                        try:
                            page = sess.get(smscdr_page_url, timeout=15)
                            sk = re.search(r'sesskey=([A-Za-z0-9=]+)', page.text)
                            if sk:
                                current_sesskey = sk.group(1)
                        except Exception:
                            pass
                    else:
                        print_monitoring_box(site_name, username, "❌", "فشل تسجيل الدخول")
                        time.sleep(30); continue
                else:
                    print_monitoring_box(site_name, username, "❌", "فشل حل الكابتشا")
                    time.sleep(30); continue

            today = datetime.now()
            fdate1 = today.strftime('%Y-%m-%d') + " 00:00:00"
            fdate2 = today.strftime('%Y-%m-%d') + " 23:59:59"
            params = {
                'fdate1': fdate1, 'fdate2': fdate2,
                'frange': '', 'fclient': '', 'fnum': '', 'fcli': '',
                'fgdate': '', 'fgmonth': '', 'fgrange': '', 'fgclient': '', 'fgnumber': '', 'fgcli': '',
                'fg': '0',
            }
            if current_sesskey:
                params['sesskey'] = current_sesskey
            else:
                params.update({'sEcho': '1', 'iDisplayStart': '0', 'iDisplayLength': '500', 'iSortCol_0': '0', 'sSortDir_0': 'desc'})
            
            r = sess.get(ajax_url, params=params, headers={
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Referer': smscdr_page_url,
                'X-Requested-With': 'XMLHttpRequest'
            }, timeout=30)
            if r.status_code != 200 or 'login' in r.url.lower():
                try:
                    page = sess.get(smscdr_page_url, timeout=15)
                    if 'login' in page.url.lower():
                        is_logged_in = False; current_sesskey = None; continue
                    sk = re.search(r'sesskey=([A-Za-z0-9=]+)', page.text)
                    if sk:
                        current_sesskey = sk.group(1)
                        time.sleep(1); continue
                except Exception:
                    pass
                is_logged_in = False; current_sesskey = None; continue

            try:
                data = r.json()
            except Exception as e:
                print(f"[{site_name}] JSON Decode Error: {e}")
                is_logged_in = False; continue
                
            rows = data.get('aaData', [])
            
            if rows:
                new_messages = []
                try:
                    rows.sort(key=lambda x: str(x[0]).strip() if len(x) > 0 else "", reverse=True)
                except:
                    pass
                
                for row in rows:
                    if len(row) >= 6:
                        msg_date = str(row[0]).strip()
                        msg_num = str(row[2]).strip()
                        msg_cli = str(row[3]).strip()
                        msg_text = str(row[5]).strip()
                        
                        if not re.match(r'\d{4}-\d{2}-\d{2}', msg_date):
                            continue

                        if msg_text == "$" or len(msg_text) < 2:
                            for idx in [4, 6, 3]: 
                                if len(row) > idx:
                                    potential_msg = str(row[idx]).strip()
                                    if potential_msg and potential_msg != "$":
                                        msg_text = potential_msg
                                        break
                        
                        msg_key = f"{msg_date}_{msg_num}_{msg_text[:20]}"
                        if msg_key == last_seen_key_local: break
                        new_messages.append({'date': msg_date, 'number': msg_num, 'cli': msg_cli, 'sms': msg_text, 'key': msg_key})
                
                if new_messages:
                    is_initial = not os.path.exists(last_message_file) or os.path.getsize(last_message_file) == 0
                    last_seen_key_local = new_messages[0]['key']
                    save_last_seen()
                    
                    if is_initial:
                        print_monitoring_box(site_name, username, "🔔", "تم بدء المراقبة: جلب أحدث كود فقط")
                        messages_to_process = [new_messages[0]]
                    else:
                        print_monitoring_box(site_name, username, "🔔", f"لقيت كود: {len(new_messages)} رسائل جديدة")
                        messages_to_process = reversed(new_messages)
                    
                    for msg in messages_to_process:
                        otp_val, clean_sms = extract_from_message(msg['sms'])
                        service_name = f"[{detect_service(clean_sms)}]"
                        formatted = format_otp_message_v2(msg['number'], clean_sms, service_name, otp_val)
                        send_otp_to_user(clean_number(msg['number']), formatted, msg['number'], None, otp_val, clean_sms, service_name)
                        
                        sent_file = f"sent_messages_{site_key}_{account_id}.json"
                        try:
                            sent_msgs = []
                            if os.path.exists(sent_file):
                                with open(sent_file, 'r', encoding='utf-8') as f:
                                    sent_msgs = json.load(f)
                            sent_msgs.append({
                                'date': msg['date'],
                                'number': msg['number'],
                                'text': msg['sms'],
                                'otp': otp_val,
                                'timestamp': time.time()
                            })
                            if len(sent_msgs) > 100:
                                sent_msgs = sent_msgs[-100:]
                            with open(sent_file, 'w', encoding='utf-8') as f:
                                json.dump(sent_msgs, f, indent=2, ensure_ascii=False)
                        except Exception as e:
                            print(f"[{site_name}] Error saving sent messages: {e}")
                else:
                    print_monitoring_box(site_name, username, "🟢", "لا توجد اكواد")
            else:
                print_monitoring_box(site_name, username, "🟢", "لا توجد اكواد")

        except Exception as e:
            print(f"[{site_name}] Error: {e}")
            is_logged_in = False
        time.sleep(SETTINGS[site_key].get("check_interval", 5))

def sms_loop_for_konekta_account(site_key, account):
    site_name = SETTINGS[site_key]["name"]
    username = account.get("username")
    password = account.get("password")
    account_id = account.get("id")
    stop_event = account_stop_events.get(f"{site_key}_{account_id}", Event())

    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    is_logged_in = False

    last_message_file = f"last_message_{site_key}_{account_id}.txt"
    last_seen_key_local = ""

    def load_last_seen():
        nonlocal last_seen_key_local
        if os.path.exists(last_message_file):
            try:
                with open(last_message_file, "r", encoding="utf-8") as f:
                    last_seen_key_local = f.read().strip()
            except: pass
    def save_last_seen():
        try:
            with open(last_message_file, "w", encoding="utf-8") as f:
                f.write(last_seen_key_local)
        except: pass

    print_monitoring_box(site_name, username, "🚀", "بدء المراقبة...")
    load_last_seen()

    login_url = SETTINGS[site_key]["login_page_url"]
    submit_url = SETTINGS[site_key]["login_post_url"]
    ajax_url = SETTINGS[site_key]["base_url"] + SETTINGS[site_key].get("ajax_path", "/agent/res/data_smscdr.php")

    while not stop_event.is_set():
        try:
            if not is_logged_in:
                resp = sess.get(login_url, timeout=20, verify=False)
                captcha = solve_captcha_timesms(resp.text)
                if captcha:
                    data = {'username': username, 'password': password, 'capt': captcha}
                    login_resp = sess.post(submit_url, data=data, headers={'Referer': login_url}, timeout=20, allow_redirects=True, verify=False)
                    if 'sign-in' not in str(login_resp.url).lower() and 'login' not in str(login_resp.url).lower():
                        is_logged_in = True
                        print_monitoring_box(site_name, username, "✅", "تم تسجيل الدخول بنجاح")
                    else:
                        # Try without captcha if captcha not required
                        data2 = {'username': username, 'password': password}
                        login_resp2 = sess.post(submit_url, data=data2, headers={'Referer': login_url}, timeout=20, allow_redirects=True, verify=False)
                        if 'sign-in' not in str(login_resp2.url).lower() and 'login' not in str(login_resp2.url).lower():
                            is_logged_in = True
                            print_monitoring_box(site_name, username, "✅", "تم تسجيل الدخول بنجاح")
                        else:
                            print_monitoring_box(site_name, username, "❌", "فشل تسجيل الدخول")
                            time.sleep(30); continue
                else:
                    # Try login without captcha
                    data2 = {'username': username, 'password': password}
                    login_resp2 = sess.post(submit_url, data=data2, headers={'Referer': login_url}, timeout=20, allow_redirects=True, verify=False)
                    if 'sign-in' not in str(login_resp2.url).lower() and 'login' not in str(login_resp2.url).lower():
                        is_logged_in = True
                        print_monitoring_box(site_name, username, "✅", "تم تسجيل الدخول بنجاح")
                    else:
                        print_monitoring_box(site_name, username, "❌", "فشل حل الكابتشا / فشل تسجيل الدخول")
                        time.sleep(30); continue

            today = datetime.now()
            fdate1 = today.strftime('%Y-%m-%d') + " 00:00:00"
            fdate2 = today.strftime('%Y-%m-%d') + " 23:59:59"
            params = {'fdate1': fdate1, 'fdate2': fdate2, 'fg': '0', 'sEcho': '1', 'iDisplayStart': '0', 'iDisplayLength': '500', 'iSortCol_0': '0', 'sSortDir_0': 'desc'}

            r = sess.get(ajax_url, params=params, headers={'Referer': SETTINGS[site_key]["base_url"] + "/agent/SMSCDRReports", 'X-Requested-With': 'XMLHttpRequest'}, timeout=30, verify=False)
            if r.status_code != 200 or 'sign-in' in r.url.lower() or 'login' in r.url.lower():
                is_logged_in = False; continue

            try:
                data = r.json()
            except Exception as e:
                print(f"[{site_name}] JSON Decode Error: {e}")
                is_logged_in = False; continue

            rows = data.get('aaData', [])

            if rows:
                new_messages = []
                try:
                    rows.sort(key=lambda x: str(x[0]).strip() if len(x) > 0 else "", reverse=True)
                except:
                    pass

                for row in rows:
                    if len(row) >= 6:
                        msg_date = str(row[0]).strip()
                        msg_num = str(row[2]).strip()
                        msg_cli = str(row[3]).strip()
                        msg_text = str(row[5]).strip()

                        if not re.match(r'\d{4}-\d{2}-\d{2}', msg_date):
                            continue

                        if msg_text == "$" or len(msg_text) < 2:
                            for idx in [4, 6, 3]:
                                if len(row) > idx:
                                    potential_msg = str(row[idx]).strip()
                                    if potential_msg and potential_msg != "$":
                                        msg_text = potential_msg
                                        break

                        msg_key = f"{msg_date}_{msg_num}_{msg_text[:20]}"
                        if msg_key == last_seen_key_local: break
                        new_messages.append({'date': msg_date, 'number': msg_num, 'cli': msg_cli, 'sms': msg_text, 'key': msg_key})

                if new_messages:
                    is_initial = not os.path.exists(last_message_file) or os.path.getsize(last_message_file) == 0

                    last_seen_key_local = new_messages[0]['key']
                    save_last_seen()

                    if is_initial:
                        print_monitoring_box(site_name, username, "🔔", "تم بدء المراقبة: جلب أحدث كود فقط")
                        messages_to_process = [new_messages[0]]
                    else:
                        print_monitoring_box(site_name, username, "🔔", f"لقيت كود: {len(new_messages)} رسائل جديدة")
                        messages_to_process = reversed(new_messages)

                    for msg in messages_to_process:
                        otp_val, clean_sms = extract_from_message(msg['sms'])
                        service_name = f"[{detect_service(clean_sms)}]"
                        formatted = format_otp_message_v2(msg['number'], clean_sms, service_name, otp_val)
                        send_otp_to_user(clean_number(msg['number']), formatted, msg['number'], None, otp_val, clean_sms, service_name)

                        sent_file = f"sent_messages_{site_key}_{account_id}.json"
                        try:
                            sent_msgs = []
                            if os.path.exists(sent_file):
                                with open(sent_file, 'r', encoding='utf-8') as f:
                                    sent_msgs = json.load(f)
                            sent_msgs.append({
                                'date': msg['date'],
                                'number': msg['number'],
                                'text': msg['sms'],
                                'otp': otp_val,
                                'timestamp': time.time()
                            })
                            if len(sent_msgs) > 100:
                                sent_msgs = sent_msgs[-100:]
                            with open(sent_file, 'w', encoding='utf-8') as f:
                                json.dump(sent_msgs, f, indent=2, ensure_ascii=False)
                        except Exception as e:
                            print(f"[{site_name}] Error saving sent messages: {e}")
                else:
                    print_monitoring_box(site_name, username, "🟢", "لا توجد اكواد")
            else:
                print_monitoring_box(site_name, username, "🟢", "لا توجد اكواد")

        except Exception as e:
            print(f"[{site_name}] Error: {e}")
            is_logged_in = False
        time.sleep(SETTINGS[site_key].get("check_interval", 5))

def sms_loop_for_roxy_account(site_key, account):
    site_name = SETTINGS[site_key]["name"]
    username = account.get("username")
    password = account.get("password")
    account_id = account.get("id")
    stop_event = account_stop_events.get(f"{site_key}_{account_id}", Event())
    
    scraper = cloudscraper.create_scraper()
    is_logged_in = False
    
    last_message_file = f"last_message_{site_key}_{account_id}.txt"
    last_seen_key_local = ""
    
    def load_last_seen():
        nonlocal last_seen_key_local
        if os.path.exists(last_message_file):
            try:
                with open(last_message_file, "r", encoding="utf-8") as f:
                    last_seen_key_local = f.read().strip()
            except: pass
    def save_last_seen():
        try:
            with open(last_message_file, "w", encoding="utf-8") as f:
                f.write(last_seen_key_local)
        except: pass

    print_monitoring_box(site_name, username, "🚀", "بدء المراقبة...")
    load_last_seen()
    
    login_url = "http://www.roxysms.net/signin"
    ajax_url = "http://www.roxysms.net/agent/res/data_smscdr.php"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "http://www.roxysms.net/agent/SMSCDRReports"
    }
    
    while not stop_event.is_set():
        try:
            if not is_logged_in:
                payload = {"username": username, "password": password}
                try:
                    login_resp = scraper.post(login_url, data=payload, headers=headers, timeout=30)
                    if login_resp.status_code == 200 and ("success" in login_resp.text.lower() or "logout" in login_resp.text.lower()):
                        is_logged_in = True
                        print_monitoring_box(site_name, username, "✅", "تم تسجيل الدخول بنجاح")
                    else:
                        print_monitoring_box(site_name, username, "❌", "فشل تسجيل الدخول، إعادة المحاولة...")
                        time.sleep(30)
                        continue
                except Exception as e:
                    print(f"[{site_name}] Login Error: {e}")
                    time.sleep(30)
                    continue

            today = datetime.now().strftime('%Y-%m-%d')
            params = {
                'fdate1': f'{today} 00:00:00',
                'fdate2': f'{today} 23:59:59',
                'fg': '0'
            }
            
            try:
                r = scraper.get(ajax_url, params=params, headers=headers, timeout=30)
                
                if r.status_code != 200 or 'login' in r.url.lower():
                    is_logged_in = False
                    continue

                data = r.json()
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                print(f"[{site_name}] Connection issue, retrying: {e}")
                is_logged_in = False
                time.sleep(10)
                continue
            except Exception as e:
                print(f"[{site_name}] Request Error: {e}")
                is_logged_in = False
                time.sleep(10)
                continue
            rows = data.get('aaData', []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            
            if rows:
                new_messages = []
                for row in rows:
                    if isinstance(row, list) and len(row) >= 6:
                        d_str, num, msg_txt = str(row[0]), re.sub(r'\D', '', str(row[2])), str(row[5])
                        
                        if msg_txt == "$" or len(msg_txt) < 2:
                            
                            for idx in [4, 6, 3]: 
                                if len(row) > idx:
                                    potential_msg = str(row[idx]).strip()
                                    if potential_msg and potential_msg != "$":
                                        msg_txt = potential_msg
                                        break
                        
                        key = f"{d_str}|{num}"
                        if key == last_seen_key_local: break
                        new_messages.append({'date': d_str, 'number': num, 'sms': msg_txt})
                
                if new_messages:
                    last_seen_key_local = f"{new_messages[0]['date']}|{new_messages[0]['number']}"
                    save_last_seen()
                    
                    
                    for msg in reversed(new_messages):
                        otp_val, clean_sms = extract_from_message(msg['sms'])
                        service_name = f"[{detect_service(clean_sms)}]"
                        formatted = format_otp_message_v2(msg['number'], clean_sms, service_name, otp_val)
                        send_otp_to_user(clean_number(msg['number']), formatted, msg['number'], None, otp_val, clean_sms, service_name)
                else:
                    print_monitoring_box(site_name, username, "📭", "لا توجد أكواد جديدة")
            else:
                print_monitoring_box(site_name, username, "📭", "لا توجد أكواد")
                
        except Exception as e:
            print(f"[{site_name}] Error: {e}")
            is_logged_in = False
            time.sleep(10)

        if stop_event.wait(SETTINGS[site_key].get("check_interval", 5)):
            break


# getnumber handler is defined earlier at line 5111

@bot.callback_query_handler(func=lambda call: call.data.startswith("direct_country_"))
def direct_country_callback(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    channels = check_subscription(user_id)

    if channels:
        bot.answer_callback_query(call.id, "❌ Subscribe first!", show_alert=True)
        return
    cid = call.data.replace("direct_country_","")
    info = COUNTRIES.get(cid,{})
    if not info:
        bot.answer_callback_query(call.id, "❌ Not found!", show_alert=True)
        return
    platforms = info.get("platforms",[])
    if len(platforms) > 1:
        SVC = {"WhatsApp":"5334998226636390258","Facebook":"5323261730283863478","Telegram":"5330237710655306682","Instagram":"5319160079465857105","Twitter":"5330337435500951363","TikTok":"5327982530702359565","Discord":"5325612636467903082","Gmail":"5303416490295304868","Apple":"5947405256752107961"}
        flag = info.get("flag","🌍")
        mu = InlineKeyboardMarkup(row_width=2)
        for p in platforms:
            eid = SVC.get(p,"5334998226636390258")
            try: mu.add(InlineKeyboardButton(f" {p}", callback_data=f"cplt_{cid}_{p}", icon_custom_emoji_id=eid))
            except: mu.add(InlineKeyboardButton(f"📱 {p}", callback_data=f"cplt_{cid}_{p}"))
        try: mu.add(make_back_button("Back", "back_to_countries"))
        except: mu.add(InlineKeyboardButton("◀", callback_data="back_to_countries"))
        title = f"📱 {flag} Выберите сервис:" if lang=="ru" else f"📱 {flag} Choose platform:"
        bot.answer_callback_query(call.id)
        try: bot.edit_message_text(title, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=mu)
        except: bot.send_message(call.message.chat.id, title, parse_mode="HTML", reply_markup=mu)
        return
    bot.answer_callback_query(call.id)
    _assign_number(call.message, user_id, cid, lang)

@bot.callback_query_handler(func=lambda call: call.data.startswith("cplt_"))
def country_platform_callback(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    parts = call.data[5:].rsplit("_",1)
    cid = parts[0]
    bot.answer_callback_query(call.id)
    _assign_number(call.message, user_id, cid, lang)


@bot.callback_query_handler(func=lambda call: call.data.startswith("show_plt_countries_"))
def show_plt_countries_callback(call):
    user_id = call.from_user.id
    channels = check_subscription(user_id)
    if channels:
        bot.answer_callback_query(call.id, "❌ Subscribe first!", show_alert=True)
        return
    plt_name = call.data.replace("show_plt_countries_", "")
    lang = get_user_language(user_id)

    # بناء أزرار الدول لهذه المنصة — صف واحد دايماً زي الصورة
    markup = InlineKeyboardMarkup(row_width=1)
    plt_btns = []
    for cid, info in COUNTRIES.items():
        if plt_name not in info.get("platforms", []):
            continue
        flag = info.get("flag", "🌍")
        dname = info.get("display_name", cid)
        count = info.get("numbers_count", 0)
        fname = info.get("file", "")
        if count == 0 and fname and os.path.exists(fname):
            try:
                with open(fname, "r", encoding="utf-8") as _f:
                    count = sum(1 for l in _f if l.strip())
            except: pass
        if count == 0:
            continue  # إخفاء الدول الفارغة
        flag_eid = extract_tg_emoji_id(flag)
        color = get_country_btn_color(cid)
        btn_text = f" {dname}" if flag_eid else f"{extract_plain_emoji(flag)} {dname}"
        try:
            kw = {"callback_data": f"plt_assign_{plt_name}|{cid}"}
            if flag_eid: kw["icon_custom_emoji_id"] = flag_eid
            kw["style"] = color if color else "primary"
            plt_btns.append(InlineKeyboardButton(btn_text, **kw))
        except:
            plt_btns.append(InlineKeyboardButton(f"{extract_plain_emoji(flag)} {dname}", callback_data=f"plt_assign_{plt_name}|{cid}"))

    if not plt_btns:
        bot.answer_callback_query(call.id, "❌ No numbers available for this platform!", show_alert=True)
        return

    for b in plt_btns:
        markup.add(b)

    # زر رجوع للمنصات
    back_txt = "الرجوع للخدمات ←" if lang == "ar" else "← Back to Services"
    try:
        markup.add(InlineKeyboardButton(back_txt, callback_data="back_to_countries", style="danger"))
    except:
        markup.add(InlineKeyboardButton(back_txt, callback_data="back_to_countries"))

    # Header: "اختر الدولة لـ WhatsApp" / "Choose country for WhatsApp"
    if lang == "ar":
        txt = f"<b>اختر الدولة لـ {plt_name}</b> <tg-emoji emoji-id='5334998226636390258'>📱</tg-emoji>"
    else:
        txt = f"<b>Choose country for {plt_name}</b> <tg-emoji emoji-id='5334998226636390258'>📱</tg-emoji>"

    bot.answer_callback_query(call.id)

    try:
        bot.edit_message_text(
            txt,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )
    except:
        bot.send_message(
            call.message.chat.id,
            txt,
            parse_mode="HTML",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("plt_assign_"))
def plt_assign_callback(call):
    """Handle country selection from platform screen — saves platform before assigning number"""
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    channels = check_subscription(user_id)
    if channels:
        bot.answer_callback_query(call.id, "❌ Subscribe first!", show_alert=True)
        return
    # format: plt_assign_{plt_name}|{cid}
    raw = call.data[len("plt_assign_"):]
    if "|" not in raw:
        bot.answer_callback_query(call.id, "❌ Invalid selection!", show_alert=True)
        return
    plt_name, cid = raw.split("|", 1)
    if cid not in COUNTRIES:
        bot.answer_callback_query(call.id, ml(user_id, "country_not_found"), show_alert=True)
        return
    # حفظ المنصة في بيانات المستخدم قبل إعطاء الرقم
    USERS.setdefault(str(user_id), {})
    USERS[str(user_id)]["platform"] = plt_name
    save_users()
    bot.answer_callback_query(call.id)
    _assign_number(call.message, user_id, cid, lang)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_countries")
def back_to_countries_cb(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    markup = get_country_buttons_all(user_id)
    txt = get_welcome_text(user_id)
    bot.answer_callback_query(call.id)
    if markup:
        try: bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except: bot.send_message(call.message.chat.id, txt, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, txt, parse_mode="HTML", reply_markup=get_main_reply_keyboard(user_id))

# قاموس لتتبع آخر وقت تغيير الرقم لكل مستخدم
number_change_cooldowns = {}
CHANGE_NUMBER_COOLDOWN = 9  # ثواني

@bot.callback_query_handler(func=lambda call: call.data.startswith("direct_reroll_"))
def direct_reroll_cb(call):
    user_id = call.from_user.id
    lang = get_user_language(user_id)
    cid = call.data.replace("direct_reroll_","")
    
    now = time.time()
    last_change = number_change_cooldowns.get(user_id, 0)
    elapsed = now - last_change
    
    if elapsed < CHANGE_NUMBER_COOLDOWN:
        remaining = int(CHANGE_NUMBER_COOLDOWN - elapsed) + 1
        bot.answer_callback_query(call.id, f"⏳ Wait {remaining} seconds before changing!", show_alert=True)
        return
    
    number_change_cooldowns[user_id] = now
    bot.answer_callback_query(call.id)
    _assign_number(call.message, user_id, cid, lang)

def _ask_platform_or_server(chat_id, user_id, state):
    """After country name: ask which platform (or server if no platforms)"""
    import json as _j
    platforms = load_platforms()
    country_name = state.get("country_name", "Unknown")
    num_cleaned = state.get("num_cleaned", 0)
    
    if platforms:
        # يسأل عن المنصة
        markup = InlineKeyboardMarkup(row_width=2)
        for plt_name in platforms.keys():
            markup.add(
                InlineKeyboardButton(f"📱 {plt_name}", callback_data=f"na_pick_plt_{plt_name}"),
                InlineKeyboardButton(f"➕ إضافة", callback_data=f"na_add_as_country_{plt_name}")
            )
        markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="admin"))
        bot.send_message(chat_id,
            f"✅ الاسم: <b>{country_name}</b> | الأرقام: <b>{num_cleaned}</b>\n\n"
            f"📱 <b>اختر المنصة التي ستضاف تحتها هذه الدولة:</b>\n"
            f"<i>أو اضغط ➕ إضافة بجانب المنصة لإضافة الدولة مباشرة</i>",
            parse_mode="HTML", reply_markup=markup)
    else:
        # لو مفيش منصات → يسأل عن السيرفر مباشرة
        markup = _build_server_markup("na_add_country_srv")
        bot.send_message(chat_id,
            f"✅ الاسم: <b>{country_name}</b> | الأرقام: <b>{num_cleaned}</b>\n\n"
            f"🖥️ <b>اختر السيرفر:</b>\n<i>لو عايز تضيف منصات أضفها أولاً من لوحة الأدمن</i>",
            parse_mode="HTML", reply_markup=markup)
        user_states[user_id]["action"] = "na_add_country_server"

def _build_server_markup(prefix):
    """Build server selection markup"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🏢 GROUP", callback_data=f"{prefix}_GROUP"),
        InlineKeyboardButton("🔷 Fly sms", callback_data=f"{prefix}_Fly sms")
    )
    markup.add(
        InlineKeyboardButton("🏢 hadi", callback_data=f"{prefix}_hadi"),
        InlineKeyboardButton("🔷 fire", callback_data=f"{prefix}_fire")
    )
    markup.add(
        InlineKeyboardButton("📱 Number Panel", callback_data=f"{prefix}_Number_Panel"),
        InlineKeyboardButton("⚡ Bolt", callback_data=f"{prefix}_Bolt")
    )
    markup.add(
        InlineKeyboardButton("🌐 iVASMS", callback_data=f"{prefix}_iVASMS"),
        InlineKeyboardButton("🔵 MSI", callback_data=f"{prefix}_MSI")
    )
    markup.add(
        InlineKeyboardButton("🟣 proton SMS", callback_data=f"{prefix}_proton SMS"),
        InlineKeyboardButton("🌐 IMS", callback_data=f"{prefix}_IMS")
    )
    markup.add(
        InlineKeyboardButton("🌸 Roxy SMS", callback_data=f"{prefix}_Roxy SMS"),
        InlineKeyboardButton("🆕 TimeSMS", callback_data=f"{prefix}_TimeSMS")
    )
    markup.add(InlineKeyboardButton("🔗 Konekta", callback_data=f"{prefix}_Konekta"))
    markup.add(InlineKeyboardButton("📡 Seven1Tel", callback_data=f"{prefix}_Seven1Tel"))
    markup.add(InlineKeyboardButton("🕊 Gaza SMS", callback_data=f"{prefix}_Gaza SMS"))
    markup.add(InlineKeyboardButton("📶 Km sms", callback_data=f"{prefix}_Km sms"))
    markup.add(
        InlineKeyboardButton("🟣 Grand SMS", callback_data=f"{prefix}_Grand SMS"),
        InlineKeyboardButton("💜 Purple SMS", callback_data=f"{prefix}_Purple SMS")
    )
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="admin"))
    return markup


def _assign_number(msg_obj, user_id, cid, lang):
    info = COUNTRIES.get(cid, {})
    flag = info.get("flag", "🌍")
    cc   = info.get("code", "")
    fname = info.get("file", "")

    # تحميل الأرقام من الملف
    all_nums = []
    if fname and os.path.exists(fname):
        try:
            with open(fname, "r", encoding="utf-8") as fh:
                all_nums = [l.strip() for l in fh if l.strip()]
        except: pass

    if not all_nums:
        bot.send_message(msg_obj.chat.id, "❌ No numbers available!")
        return

    # استبعاد الأرقام القديمة عند تغيير الرقم لنفس الدولة
    old_display = USERS.get(str(user_id), {}).get("display_numbers", [])
    old_cid     = USERS.get(str(user_id), {}).get("selected_country", "")
    if old_display and old_cid == cid:
        old_set  = set(str(n).strip() for n in old_display)
        all_nums = [n for n in all_nums if n not in old_set]

    # اختيار 4 أرقام
    pick_count = min(4, len(all_nums))
    if pick_count == 0:
        bot.send_message(msg_obj.chat.id, "❌ No numbers available!")
        return

    display_numbers = random.sample(all_nums, pick_count)
    selected = display_numbers[0]

    USERS.setdefault(str(user_id), {})
    # حفظ المنصة: لو مش محفوظة مسبقاً، خذها من بيانات الدولة
    current_platform = USERS[str(user_id)].get("platform", "")
    country_platforms = info.get("platforms", [])
    if not current_platform and country_platforms:
        current_platform = country_platforms[0]
    USERS[str(user_id)].update({
        "selected_country": cid,
        "selected_number":  selected,
        "selected_numbers": display_numbers,
        "display_numbers":  display_numbers,
        "flag": flag,
        "platform": current_platform
    })
    cu = USERS[str(user_id)].get("countries_used", [])
    if cid not in cu: cu.append(cid)
    USERS[str(user_id)]["countries_used"]    = cu
    USERS[str(user_id)]["last_seen"]         = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    USERS[str(user_id)]["activations"]       = USERS[str(user_id)].get("activations", 0) + 1
    USERS[str(user_id)]["numbers_received"]  = USERS[str(user_id)].get("numbers_received", 0) + pick_count
    save_users()

    lang_a      = get_user_language(user_id)
    links       = load_button_links()
    flag_eid_a  = extract_tg_emoji_id(flag)
    plain_flag_a = extract_plain_emoji(flag)

    # ══════════════════════════════════════════════
    # HEADER — "Waiting for otp 🔥" زي الصورة
    # ══════════════════════════════════════════════
    if lang_a == "ar":
        header = (
            "<b>في انتظار الـ OTP "
            "<tg-emoji emoji-id='5888663955412359816'>🔥</tg-emoji></b>"
        )
    else:
        header = (
            "<b>Waiting for otp "
            "<tg-emoji emoji-id='5888663955412359816'>🔥</tg-emoji></b>"
        )

    mu = InlineKeyboardMarkup(row_width=1)

    # ══════════════════════════════════════════════
    # 4 أزرار أرقام — علم الدولة + أيقونة نسخ + الرقم
    # ══════════════════════════════════════════════
    for num in display_numbers:          # كل الـ 4 أرقام
        dn = f"+{num.lstrip('+').lstrip()}"
        try:
            if flag_eid_a:
                mu.add(InlineKeyboardButton(
                    text=f" {dn}",
                    copy_text=CopyTextButton(text=dn),
                    icon_custom_emoji_id=flag_eid_a
                ))
            else:
                mu.add(InlineKeyboardButton(
                    text=f"{plain_flag_a} 📋 {dn}",
                    copy_text=CopyTextButton(text=dn)
                ))
        except:
            mu.add(InlineKeyboardButton(f"{plain_flag_a} {dn}", callback_data=f"pick_num_{num}"))

    # ══════════════════════════════════════════════
    # تغيير الرقم — أحمر — صف كامل  (زي الصورة)
    # ══════════════════════════════════════════════
    cn_text = "تغيير الرقم" if lang_a == "ar" else "Change Number"
    try:
        mu.add(InlineKeyboardButton(
            text=f" {cn_text}",
            callback_data=f"direct_reroll_{cid}",
            icon_custom_emoji_id="5258420634785947640",
            style="danger"
        ))
    except:
        mu.add(InlineKeyboardButton(f"🔄 {cn_text}", callback_data=f"direct_reroll_{cid}"))

    # ══════════════════════════════════════════════
    # تغيير الدولة — أزرق — صف كامل
    # ══════════════════════════════════════════════
    cc_text = "تغيير الدولة" if lang_a == "ar" else "Change Country"
    try:
        mu.add(InlineKeyboardButton(
            text=f" {cc_text}",
            callback_data="back_to_countries",
            icon_custom_emoji_id="5447410659077661506",
            style="primary"
        ))
    except:
        mu.add(InlineKeyboardButton(f"🌍 {cc_text}", callback_data="back_to_countries"))

    # ══════════════════════════════════════════════
    # جروب البوت — أخضر — صف كامل
    # ══════════════════════════════════════════════
    otp_text = "جروب البوت" if lang_a == "ar" else "OTP Group"
    try:
        mu.add(InlineKeyboardButton(
            text=f" {otp_text}",
            url=links.get("group_link", "https://t.me/EMRAITE_5"),
            icon_custom_emoji_id="5458603043203327669",
            style="success"
        ))
    except:
        mu.add(InlineKeyboardButton(f"📨 {otp_text}", url=links.get("group_link", "https://t.me/UltronX_MegaBo")))

    # ══════════════════════════════════════════════
    # القائمة الرئيسية — شفاف — صف كامل
    # ══════════════════════════════════════════════
    main_text = "القائمة الرئيسية" if lang_a == "ar" else "Main Menu"
    try:
        mu.add(InlineKeyboardButton(
            text=f" {main_text}",
            callback_data="back_to_countries",
            icon_custom_emoji_id="5321334093126842469"
        ))
    except:
        mu.add(InlineKeyboardButton(f"◀ {main_text}", callback_data="back_to_countries"))

    try:
        bot.edit_message_text(header, msg_obj.chat.id, msg_obj.message_id, parse_mode="HTML", reply_markup=mu)
    except:
        bot.send_message(msg_obj.chat.id, header, parse_mode="HTML", reply_markup=mu)

# ════ Admin: ألوان + أماكن + منصات ════
@bot.callback_query_handler(func=lambda call: call.data == "admin_country_colors")
def admin_colors_cb(call):
    if not is_admin(call.from_user.id): return
    mu = InlineKeyboardMarkup(row_width=2)
    try:
        mu.add(
            InlineKeyboardButton("🌍 ألوان الدول", callback_data="admin_color_countries"),
            InlineKeyboardButton("📱 ألوان المنصات", callback_data="admin_color_platforms")
        )
        mu.add(make_back_button("رجوع للوحة", "admin"))
    except:
        mu.add(InlineKeyboardButton("🌍 دول", callback_data="admin_color_countries"))
        mu.add(InlineKeyboardButton("📱 منصات", callback_data="admin_color_platforms"))
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "🎨 <b>هتلون أيه؟</b>", parse_mode="HTML", reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data == "admin_color_countries")
def admin_color_countries_cb(call):
    if not is_admin(call.from_user.id): return
    mu = InlineKeyboardMarkup(row_width=3)
    try:
        mu.add(InlineKeyboardButton("🟢 أخضر",callback_data="colact_success"), InlineKeyboardButton("🔴 أحمر",callback_data="colact_danger"), InlineKeyboardButton("🔵 أزرق",callback_data="colact_primary"))
        mu.add(InlineKeyboardButton("⬜ شفاف",callback_data="colact_none"))
        mu.add(make_back_button("رجوع", "admin_country_colors"))
    except: mu.add(InlineKeyboardButton("🎨 اختر",callback_data="colact_success"))
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,"🎨 <b>اختر لون أزرار الدول:</b>",parse_mode="HTML",reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data == "admin_color_platforms")
def admin_color_platforms_cb(call):
    if not is_admin(call.from_user.id): return
    # أولاً: اختار المنصة اللي عايز تلونها
    platforms = load_platforms()
    if not platforms:
        bot.answer_callback_query(call.id, "❌ لا توجد منصات مضافة!", show_alert=True)
        return
    mu = InlineKeyboardMarkup(row_width=2)
    for pname in platforms.keys():
        mu.add(InlineKeyboardButton(f"📱 {pname}", callback_data=f"plt_pick_color_{pname}"))
    mu.add(InlineKeyboardButton("🌐 تلوين الكل", callback_data="plt_color_all"))
    try: mu.add(make_back_button("رجوع", "admin_country_colors"))
    except: mu.add(InlineKeyboardButton("◀",callback_data="admin_country_colors"))
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,"🎨 <b>اختر المنصة التي تريد تلوينها:</b>",parse_mode="HTML",reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data.startswith("plt_pick_color_"))
def plt_pick_color_name_cb(call):
    if not is_admin(call.from_user.id): return
    pname = call.data.replace("plt_pick_color_", "")
    mu = InlineKeyboardMarkup(row_width=3)
    try:
        mu.add(InlineKeyboardButton("🟢 أخضر",callback_data=f"plt_color_one_{pname}_success"),
               InlineKeyboardButton("🔴 أحمر",callback_data=f"plt_color_one_{pname}_danger"),
               InlineKeyboardButton("🔵 أزرق",callback_data=f"plt_color_one_{pname}_primary"))
        mu.add(InlineKeyboardButton("⬜ شفاف",callback_data=f"plt_color_one_{pname}_none"))
    except: pass
    try: mu.add(make_back_button("رجوع", "admin_color_platforms"))
    except: mu.add(InlineKeyboardButton("◀",callback_data="admin_color_platforms"))
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,f"🎨 <b>اختر لون زر المنصة: {pname}</b>",parse_mode="HTML",reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data.startswith("plt_color_one_"))
def plt_color_one_cb(call):
    if not is_admin(call.from_user.id): return
    # format: plt_color_one_<pname>_<color>
    data = call.data.replace("plt_color_one_", "")
    # color is last part after last _
    parts = data.rsplit("_", 1)
    if len(parts) < 2:
        bot.answer_callback_query(call.id, "❌ خطأ!", show_alert=True)
        return
    pname, color = parts[0], parts[1]
    s = load_bot_settings()
    s.setdefault("platform_colors", {})[pname] = color
    save_bot_settings(s)
    names = {"success":"أخضر","danger":"أحمر","primary":"أزرق","none":"شفاف"}
    bot.answer_callback_query(call.id, f"✅ تم تلوين {pname}: {names.get(color,color)}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "plt_color_all")
def plt_color_all_cb(call):
    if not is_admin(call.from_user.id): return
    mu = InlineKeyboardMarkup(row_width=3)
    try:
        mu.add(InlineKeyboardButton("🟢 أخضر",callback_data="plt_color_success"),
               InlineKeyboardButton("🔴 أحمر",callback_data="plt_color_danger"),
               InlineKeyboardButton("🔵 أزرق",callback_data="plt_color_primary"))
        mu.add(InlineKeyboardButton("⬜ شفاف",callback_data="plt_color_none"))
        mu.add(make_back_button("رجوع", "admin_color_platforms"))
    except: mu.add(InlineKeyboardButton("🎨 اختر",callback_data="plt_color_success"))
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,"🎨 <b>اختر لون كل أزرار المنصات:</b>",parse_mode="HTML",reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data.startswith("plt_color_"))
def plt_color_cb(call):
    if not is_admin(call.from_user.id): return
    color = call.data.replace("plt_color_", "")
    s = load_bot_settings()
    s["platform_btn_color"] = color
    save_bot_settings(s)
    names={"success":"أخضر","danger":"أحمر","primary":"أزرق","none":"شفاف"}
    bot.answer_callback_query(call.id, f"✅ لون المنصات: {names.get(color,color)}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("colact_"))
def colact_cb(call):
    if not is_admin(call.from_user.id): return
    color = call.data[7:]
    mu = InlineKeyboardMarkup(row_width=2)
    mu.add(InlineKeyboardButton("🌍 Color All", callback_data=f"colall_{color}"))
    for cid, info in COUNTRIES.items():
        flag = info.get("flag", "🌍")
        name = info.get("display_name", cid)
        plain_flag = extract_plain_emoji(flag)
        eid = extract_tg_emoji_id(flag)
        btn_text = f" {name}" if eid else f"{plain_flag} {name}"
        try:
            kw = {"callback_data": f"colone_{cid}_{color}"}
            if eid: kw["icon_custom_emoji_id"] = eid
            mu.add(InlineKeyboardButton(btn_text, **kw))
        except:
            mu.add(InlineKeyboardButton(f"{plain_flag} {name}", callback_data=f"colone_{cid}_{color}"))
    try: mu.add(make_back_button("Back", "admin_country_colors"))
    except: mu.add(InlineKeyboardButton("◀", callback_data="admin_country_colors"))
    names = {"success": "Green", "danger": "Red", "primary": "Blue", "none": "Transparent"}
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"🎨 Color: <b>{names.get(color, color)}</b>\nChoose a country to color or all:", parse_mode="HTML", reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data.startswith("colall_"))
def colall_cb(call):
    if not is_admin(call.from_user.id): return
    color = call.data[7:]
    s = load_bot_settings(); s["country_btn_color"]=color; s["country_colors"]={}; save_bot_settings(s)
    bot.answer_callback_query(call.id,"✅ تم تلوين الكل!",show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("colone_"))
def colone_cb(call):
    if not is_admin(call.from_user.id): return
    parts = call.data[7:].rsplit("_",1); cid,color=parts[0],parts[1]
    s = load_bot_settings(); s.setdefault("country_colors",{})[cid]=color; save_bot_settings(s)
    bot.answer_callback_query(call.id,"✅ تم!",show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_btn_layout")
def admin_layout_cb(call):
    if not is_admin(call.from_user.id): return
    mu = InlineKeyboardMarkup(row_width=2)
    try:
        mu.add(
            InlineKeyboardButton("📱 أزرار المنصات", callback_data="layout_platforms"),
            InlineKeyboardButton("🌍 أزرار الدول", callback_data="layout_countries")
        )
        mu.add(make_back_button("رجوع للوحة", "admin"))
    except:
        mu.add(InlineKeyboardButton("📱 منصات", callback_data="layout_platforms"))
        mu.add(InlineKeyboardButton("🌍 دول", callback_data="layout_countries"))
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        "📐 <b>أماكن الأزرار</b>\n\nاختر نوع الأزرار:",
        parse_mode="HTML", reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data == "layout_platforms")
def layout_platforms_cb(call):
    if not is_admin(call.from_user.id): return
    mu = InlineKeyboardMarkup(row_width=1)
    s = load_bot_settings()
    cur = s.get("platform_btn_layout", "single")
    for name, val in [("تحت بعض (زر واحد)", "single"), ("يمين شمال (زرين)", "double"), ("ثلاثة في الصف", "triple")]:
        check = "✅ " if val == cur else ""
        mu.add(InlineKeyboardButton(f"{check}{name}", callback_data=f"setpltlyt_{val}"))
    try: mu.add(make_back_button("رجوع", "admin_btn_layout"))
    except: mu.add(InlineKeyboardButton("◀", callback_data="admin_btn_layout"))
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "📐 <b>شكل عرض أزرار المنصات:</b>", parse_mode="HTML", reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data == "layout_countries")
def layout_countries_cb(call):
    if not is_admin(call.from_user.id): return
    mu = InlineKeyboardMarkup(row_width=1)
    s = load_bot_settings()
    cur = s.get("country_btn_layout", "single")
    for name, val in [("تحت بعض (زر واحد)", "single"), ("يمين شمال (زرين)", "double"), ("ثلاثة في الصف", "triple")]:
        check = "✅ " if val == cur else ""
        mu.add(InlineKeyboardButton(f"{check}{name}", callback_data=f"setlyt_{val}"))
    try: mu.add(make_back_button("رجوع", "admin_btn_layout"))
    except: mu.add(InlineKeyboardButton("◀", callback_data="admin_btn_layout"))
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "📐 <b>شكل عرض أزرار الدول:</b>", parse_mode="HTML", reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data.startswith("setpltlyt_"))
def setpltlyt_cb(call):
    if not is_admin(call.from_user.id): return
    lyt = call.data[10:]
    s = load_bot_settings()
    s["platform_btn_layout"] = lyt
    save_bot_settings(s)
    names = {"single": "تحت بعض", "double": "يمين شمال", "triple": "ثلاثة في الصف"}
    bot.answer_callback_query(call.id, f"✅ تم: {names.get(lyt,lyt)}", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("setlyt_"))
def setlyt_cb(call):
    if not is_admin(call.from_user.id): return
    lyt=call.data[7:]; s=load_bot_settings(); s["country_btn_layout"]=lyt; save_bot_settings(s)
    names={"single":"زر واحد","double":"زرين","triple":"ثلاثة"}
    bot.answer_callback_query(call.id,f"✅ تم: {names.get(lyt,lyt)}",show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_platform")
def admin_add_plt_cb(call):
    if not is_admin(call.from_user.id): return
    mu = InlineKeyboardMarkup(row_width=1)
    try: mu.add(InlineKeyboardButton(" تأكيد إضافة منصة",callback_data="confirm_add_plt")); mu.add(make_back_button("رجوع للوحة", "admin_panel"))
    except: mu.add(InlineKeyboardButton("✅ تأكيد",callback_data="confirm_add_plt"))
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,"📱 <b>إضافة منصة جديدة</b>\n\nاضغط تأكيد للمتابعة.",parse_mode="HTML",reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_add_plt")
def confirm_add_plt_cb(call):
    if not is_admin(call.from_user.id): return
    bot.answer_callback_query(call.id)
    m=bot.send_message(call.message.chat.id,"📝 أرسل <b>اسم المنصة</b>:",parse_mode="HTML")
    bot.register_next_step_handler(m,_plt_name)

def _plt_name(msg):
    name=msg.text.strip()
    m2=bot.send_message(msg.chat.id,f"✅ المنصة: <b>{name}</b>\n\nأرسل <b>ID تفاعل</b> (أو 0 للتخطي):",parse_mode="HTML")
    bot.register_next_step_handler(m2,lambda m: _plt_emoji(m,name))

def _plt_emoji(msg,name):
    eid=msg.text.strip() or "5334998226636390258"
    import json as _j
    try:
        with open("platforms.json","r") as f: p=_j.load(f)
    except: p={}
    p[name]={"emoji_id":eid}
    with open("platforms.json","w") as f: _j.dump(p,f,ensure_ascii=False)

    # سأل الأدمن: هل عايز يربط دول موجودة بالمنصة دي؟
    if COUNTRIES:
        mu = InlineKeyboardMarkup(row_width=1)
        try:
            mu.add(InlineKeyboardButton(f" ربط دول بـ {name}", callback_data=f"link_countries_to_{name}", icon_custom_emoji_id="5447410659077661506", style="primary"))
        except:
            mu.add(InlineKeyboardButton(f"🔗 ربط دول بـ {name}", callback_data=f"link_countries_to_{name}"))
        try: mu.add(make_back_button("تخطي", "admin_panel"))
        except: mu.add(InlineKeyboardButton("⏭ تخطي", callback_data="admin_panel"))
        bot.send_message(msg.chat.id,
            f"✅ تمت إضافة منصة <b>{name}</b>!\n\n"
            f"📱 <b>عايز تربط الدول الموجودة بالمنصة دي؟</b>",
            parse_mode="HTML", reply_markup=mu)
    else:
        mu=InlineKeyboardMarkup(row_width=1)
        try: mu.add(make_back_button("رجوع للوحة", "admin_panel"))
        except: mu.add(InlineKeyboardButton("◀",callback_data="admin_panel"))
        bot.send_message(msg.chat.id,f"✅ تمت إضافة منصة <b>{name}</b>!",parse_mode="HTML",reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data == "admin_del_platform")
def admin_del_plt_cb(call):
    if not is_admin(call.from_user.id): return
    import json as _j
    try:
        with open("platforms.json","r") as f: p=_j.load(f)
    except: p={}
    mu=InlineKeyboardMarkup(row_width=2)
    for pn in p: mu.add(InlineKeyboardButton(f"🗑 {pn}",callback_data=f"delplt_{pn}"))
    try: mu.add(make_back_button("رجوع للوحة", "admin_panel"))
    except: mu.add(InlineKeyboardButton("◀",callback_data="admin_panel"))
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,"🗑 <b>اختر منصة لحذفها:</b>",parse_mode="HTML",reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delplt_"))
def delplt_cb(call):
    if not is_admin(call.from_user.id): return
    pn=call.data[7:]
    import json as _j
    try:
        with open("platforms.json","r") as f: p=_j.load(f)
        p.pop(pn,None)
        with open("platforms.json","w") as f: _j.dump(p,f,ensure_ascii=False)
    except: pass
    bot.answer_callback_query(call.id,f"✅ تم حذف {pn}",show_alert=True)



# ═══════ Subscription Image & Settings Admin Handlers ═══════

@bot.callback_query_handler(func=lambda call: call.data == "admin_set_sub_image")
def admin_set_sub_image_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    markup = InlineKeyboardMarkup()
    try:
        markup.add(make_back_button("رجوع للوحة", "admin"))
    except:
        markup.add(InlineKeyboardButton("◀ رجوع", callback_data="admin"))
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id,
        "🖼 <b>تعيين صورة الاشتراك الإجباري</b>\n\n"
        "أرسل <b>رابط الصورة</b> (يجب أن يبدأ بـ https و ينتهي بـ .jpg أو .png أو .bmp أو .gif):\n"
        "<i>مثال: https://example.com/image.jpg</i>",
        parse_mode="HTML", reply_markup=markup)
    user_states[user_id] = {"action": "set_sub_image"}

@bot.callback_query_handler(func=lambda call: call.data == "admin_del_sub_image")
def admin_del_sub_image_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    img_data = load_subscription_image()
    img_url = img_data.get("image_url")
    if not img_url:
        bot.answer_callback_query(call.id, "❌ لا توجد صورة مضافة!", show_alert=True)
        return
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("✅ حذف الصورة", callback_data="confirm_del_sub_image"),
        InlineKeyboardButton("❌ إلغاء", callback_data="admin")
    )
    bot.answer_callback_query(call.id)
    try:
        bot.send_photo(call.message.chat.id, img_url,
            caption=f"🖼 <b>الصورة الحالية</b>\nهل تريد حذفها؟",
            parse_mode="HTML", reply_markup=markup)
    except:
        bot.send_message(call.message.chat.id,
            f"🖼 <b>الصورة الحالية:</b>\n<code>{img_url}</code>\nهل تريد حذفها؟",
            parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "confirm_del_sub_image")
def confirm_del_sub_image_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    save_subscription_image({"image_url": None})
    bot.answer_callback_query(call.id, "✅ تم حذف الصورة!", show_alert=True)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "admin_edit_sub_msg")
def admin_edit_sub_msg_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    bot.answer_callback_query(call.id)
    settings = load_subscription_settings()
    current_msg = settings.get("message") or get_subscription_message()
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("✏️ تعيين رسالة جديدة", callback_data="set_new_sub_msg"))
    try:
        markup.add(make_back_button("رجوع للوحة", "admin"))
    except:
        markup.add(InlineKeyboardButton("◀ رجوع", callback_data="admin"))
    bot.send_message(call.message.chat.id,
        f"✏️ <b>تغيير رسالة الاشتراك الإجباري</b>\n\n"
        f"<b>الرسالة الحالية:</b>\n{current_msg[:200]}...",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "set_new_sub_msg")
def set_new_sub_msg_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="admin"))
    msg = bot.send_message(call.message.chat.id,
        "📝 أرسل الرسالة الجديدة (يمكنك استخدام HTML والتفاعلات المميزة من تيليجرام):",
        parse_mode="HTML", reply_markup=markup)
    user_states[user_id] = {"action": "set_sub_msg_text"}

@bot.callback_query_handler(func=lambda call: call.data == "admin_edit_sub_btn")
def admin_edit_sub_btn_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    settings = load_subscription_settings()
    current_btn = settings.get("button_text", "Subscribed")
    bot.answer_callback_query(call.id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ إلغاء", callback_data="admin"))
    bot.send_message(call.message.chat.id,
        f"🔘 <b>تغيير اسم زر Subscribe</b>\n\n"
        f"<b>الاسم الحالي:</b> {current_btn}\n\n"
        f"أرسل الاسم الجديد للزر:",
        parse_mode="HTML", reply_markup=markup)
    user_states[user_id] = {"action": "set_sub_btn_text"}

@bot.callback_query_handler(func=lambda call: call.data == "admin_sub_btn_color")
def admin_sub_btn_color_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    settings = load_subscription_settings()
    current_color = settings.get("button_color", "danger")
    markup = InlineKeyboardMarkup(row_width=2)
    colors = [("🔴 لون أحمر", "danger"), ("🔵 لون أزرق", "primary"), ("🟢 لون أخضر", "success"), ("⬜ شفافة", "none")]
    for label, val in colors:
        markup.add(InlineKeyboardButton(f"{'✅ ' if val == current_color else ''}{label}", callback_data=f"set_sub_btn_color_{val}"))
    try:
        markup.add(make_back_button("رجوع للوحة", "admin"))
    except:
        markup.add(InlineKeyboardButton("◀ رجوع", callback_data="admin"))
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        f"🎨 <b>لون زر التحقق</b>\n\nالحالي: <b>{current_color}</b>\n\nاختر اللون:",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_sub_btn_color_"))
def set_sub_btn_color_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    color = call.data.replace("set_sub_btn_color_", "")
    settings = load_subscription_settings()
    settings["button_color"] = color
    save_subscription_settings(settings)
    bot.answer_callback_query(call.id, f"✅ تم تعيين اللون: {color}", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == "confirm_sub_msg")
def confirm_sub_msg_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    state = user_states.get(user_id, {})
    new_msg = state.get("pending_sub_msg", "")
    if not new_msg:
        bot.answer_callback_query(call.id, "❌ لا توجد رسالة!", show_alert=True)
        return
    settings = load_subscription_settings()
    settings["message"] = new_msg
    save_subscription_settings(settings)
    if user_id in user_states:
        del user_states[user_id]
    bot.answer_callback_query(call.id, "✅ تم تعيين الرسالة!", show_alert=True)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("na_add_as_country_"))
def na_add_as_country_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    if user_id not in user_states:
        bot.answer_callback_query(call.id, "❌ Session expired!", show_alert=True)
        return
    plt_name = call.data.replace("na_add_as_country_", "")
    user_states[user_id]["selected_platform"] = plt_name
    user_states[user_id]["action"] = "na_add_country_server"
    bot.answer_callback_query(call.id)
    markup = _build_server_markup("na_add_country_srv")
    try:
        bot.send_message(call.message.chat.id,
            f"✅ المنصة: <b>{plt_name}</b>\n\n🖥️ <b>اختر السيرفر:</b>",
            parse_mode="HTML", reply_markup=markup)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("na_pick_plt_"))
def na_pick_plt_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    if user_id not in user_states:
        bot.answer_callback_query(call.id, "❌ Session expired!", show_alert=True)
        return
    
    plt_name = call.data.replace("na_pick_plt_", "")
    user_states[user_id]["selected_platform"] = plt_name
    user_states[user_id]["action"] = "na_add_country_server"
    
    bot.answer_callback_query(call.id)
    markup = _build_server_markup("na_add_country_srv")
    try:
        bot.edit_message_text(
            f"✅ المنصة: <b>{plt_name}</b>\n\n🖥️ <b>اختر السيرفر:</b>",
            call.message.chat.id, call.message.message_id,
            parse_mode="HTML", reply_markup=markup
        )
    except:
        bot.send_message(call.message.chat.id,
            f"✅ المنصة: <b>{plt_name}</b>\n\n🖥️ <b>اختر السيرفر:</b>",
            parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "na_use_auto_name")
def na_use_auto_name_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        return
    if user_id not in user_states:
        bot.answer_callback_query(call.id, "❌ Session expired!", show_alert=True)
        return
    state = user_states[user_id]
    state["action"] = "na_add_country_pick_platform"
    bot.answer_callback_query(call.id)
    _ask_platform_or_server(call.message.chat.id, user_id, state)


@bot.callback_query_handler(func=lambda call: call.data == "confirm_main_welcome")
def confirm_main_welcome_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    state = user_states.get(user_id, {})
    new_msg = state.get("pending_welcome", "")
    if not new_msg:
        bot.answer_callback_query(call.id, "❌ لا توجد رسالة!", show_alert=True)
        return
    s = load_bot_settings()
    s["custom_welcome_msg"] = new_msg
    save_bot_settings(s)
    if user_id in user_states:
        del user_states[user_id]
    bot.answer_callback_query(call.id, "✅ تم تعيين رسالة الترحيب!", show_alert=True)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass




# ─── ألوان الكيبورد ───────────────────────────────────────────────────────────

KEYBOARD_COLORS_FILE = "keyboard_colors.json"

_DEFAULT_KEYBOARD_COLORS = {
    "take":      "danger",
    "stat":      "primary",
    "countries": "success",
    "lang":      None,
    "referral":  "primary",
    "rewards":   "success",
    "withdraw":  "success",
    "support":   "primary"
}

def load_keyboard_colors():
    if os.path.exists(KEYBOARD_COLORS_FILE):
        try:
            with open(KEYBOARD_COLORS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return dict(_DEFAULT_KEYBOARD_COLORS)

def save_keyboard_colors(data):
    with open(KEYBOARD_COLORS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

@bot.callback_query_handler(func=lambda call: call.data == "admin_keyboard_colors")
def admin_keyboard_colors_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    bot.answer_callback_query(call.id)
    colors = load_keyboard_colors()
    cn = {"danger": "🔴 أحمر", "primary": "🔵 أزرق", "success": "🟢 أخضر", None: "⬜ بدون لون"}
    txt = (
        "🎨 <b>ألوان الكيبورد الحالية</b>\n\n"
        f"• Take a number: <b>{cn.get(colors.get('take'), '🔴 أحمر')}</b>\n"
        f"• Status: <b>{cn.get(colors.get('stat'), '🔵 أزرق')}</b>\n"
        f"• Added/country: <b>{cn.get(colors.get('countries'), '🟢 أخضر')}</b>\n"
        f"• Support: <b>{cn.get(colors.get('support'), '🔵 أزرق')}</b>"
    )
    markup = InlineKeyboardMarkup(row_width=1)
    try:
        markup.add(InlineKeyboardButton(" إلغاء الألوان", callback_data="keyboard_colors_off", icon_custom_emoji_id="5321334093126842469", style="danger"))
        markup.add(InlineKeyboardButton(" إرجاع الألوان", callback_data="keyboard_colors_reset", icon_custom_emoji_id="6217663806110175239", style="success"))
        markup.add(make_back_button(" رجوع", "admin"))
    except:
        markup.add(InlineKeyboardButton("🚫 إلغاء الألوان", callback_data="keyboard_colors_off"))
        markup.add(InlineKeyboardButton("✅ إرجاع الألوان", callback_data="keyboard_colors_reset"))
        markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="admin"))
    bot.send_message(call.message.chat.id, txt, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "keyboard_colors_off")
def keyboard_colors_off_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    save_keyboard_colors({"take": None, "stat": None, "countries": None})
    bot.answer_callback_query(call.id, "✅ تم إلغاء ألوان الكيبورد!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "keyboard_colors_reset")
def keyboard_colors_reset_callback(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    save_keyboard_colors({"take": "danger", "stat": "primary", "countries": "success"})
    bot.answer_callback_query(call.id, "✅ تم إرجاع ألوان الكيبورد للوضع الأصلي!", show_alert=True)



# ═══════ إعدادات المنصات - Platform Settings ═══════

@bot.callback_query_handler(func=lambda call: call.data == "admin_platform_settings")
def admin_platform_settings_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    bot.answer_callback_query(call.id)
    platforms = load_platforms()
    if not platforms:
        bot.answer_callback_query(call.id, "❌ لا توجد منصات مضافة! أضف منصة أولاً.", show_alert=True)
        return
    mu = InlineKeyboardMarkup(row_width=1)
    for plt_name in platforms:
        msg, eid = get_platform_welcome_msg(plt_name)
        label = f"📱 {plt_name}"
        try:
            plt_info = platforms[plt_name]
            plt_eid = plt_info.get("emoji_id", "")
            if plt_eid:
                mu.add(InlineKeyboardButton(f" {plt_name}", callback_data=f"plt_settings_{plt_name}", icon_custom_emoji_id=plt_eid))
            else:
                mu.add(InlineKeyboardButton(label, callback_data=f"plt_settings_{plt_name}"))
        except:
            mu.add(InlineKeyboardButton(label, callback_data=f"plt_settings_{plt_name}"))
    try:
        mu.add(make_back_button(" رجوع للوحة", "admin"))
    except:
        mu.add(InlineKeyboardButton("◀ رجوع", callback_data="admin"))
    try:
        bot.edit_message_text(
            "⚙️ <b>إعدادات المنصات</b>\n\nاختر المنصة التي تريد تعديل إعداداتها:",
            call.message.chat.id, call.message.message_id,
            parse_mode="HTML", reply_markup=mu
        )
    except:
        bot.send_message(call.message.chat.id,
            "⚙️ <b>إعدادات المنصات</b>\n\nاختر المنصة التي تريد تعديل إعداداتها:",
            parse_mode="HTML", reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data.startswith("plt_settings_"))
def plt_settings_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    plt_name = call.data[len("plt_settings_"):]
    bot.answer_callback_query(call.id)
    msg, eid = get_platform_welcome_msg(plt_name)
    platforms = load_platforms()
    plt_info = platforms.get(plt_name, {})
    plt_eid = plt_info.get("emoji_id", "")
    
    # Show welcome message preview
    default_welcome = (
        "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji>"
        " | Select your country below "
        "<tg-emoji emoji-id='5406745015365943482'>⬇️</lg-emoji>"
    )
    preview = msg if msg else f"❌ لم تُعيَّن بعد\n\n<b>الافتراضية:</b>\n{default_welcome}"
    eid_preview = f"\n<b>ID التفاعل:</b> <code>{eid}</code>" if eid else ""
    
    text = (
        f"📱 <b>إعدادات منصة: {plt_name}</b>\n\n"
        f"<b>رسالة الترحيب الحالية:</b>\n{preview}{eid_preview}\n\n"
        f"💡 <i>هذه الرسالة تظهر فوق الدول عند اختيار هذه المنصة</i>"
    )
    mu = InlineKeyboardMarkup(row_width=1)
    try:
        mu.add(InlineKeyboardButton(" تعيين رسالة ترحيب", callback_data=f"plt_set_welcome_{plt_name}", icon_custom_emoji_id="5116094575811279558"))
    except:
        mu.add(InlineKeyboardButton("✏️ تعيين رسالة ترحيب", callback_data=f"plt_set_welcome_{plt_name}"))
    try:
        mu.add(make_back_button(" رجوع للمنصات", "admin_platform_settings"))
    except:
        mu.add(InlineKeyboardButton("◀ رجوع", callback_data="admin_platform_settings"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
            parse_mode="HTML", reply_markup=mu)
    except:
        bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data.startswith("plt_set_welcome_"))
def plt_set_welcome_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    plt_name = call.data[len("plt_set_welcome_"):]
    bot.answer_callback_query(call.id)
    
    msg, eid = get_platform_welcome_msg(plt_name)
    preview = msg if msg else "❌ لم تُعيَّن بعد"
    
    mu = InlineKeyboardMarkup()
    try:
        mu.add(InlineKeyboardButton("❌ إلغاء", callback_data=f"plt_settings_{plt_name}"))
    except:
        pass
    
    default_welcome = (
        "<tg-emoji emoji-id='5447410659077661506'>🌐</tg-emoji>"
        " | Select your country below "
        "<tg-emoji emoji-id='5406745015365943482'>⬇️</tg-emoji>"
    )
    current_display = preview if msg else f"❌ لم تُعيَّن بعد\n<i>(الافتراضية: {default_welcome})</i>"
    sent = bot.send_message(call.message.chat.id,
        f"📝 <b>تعيين رسالة ترحيب لمنصة: {plt_name}</b>\n\n"
        f"<b>الرسالة الحالية:</b>\n{current_display}\n\n"
        f"📌 <b>يمكنك أيضاً إرسال ايموجي مميز من التليجرام مع الرسالة</b>\n"
        f"اكتب رسالتك وأرسلها (تدعم HTML وtg-emoji):",
        parse_mode="HTML", reply_markup=mu)
    user_states[user_id] = {"action": "plt_welcome_msg", "platform": plt_name, "step": "message"}

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id, {}).get("action") in ("plt_welcome_msg", "plt_welcome_confirm_pending"))
def plt_welcome_text_handler(msg):
    user_id = msg.from_user.id
    if not is_admin(user_id): return
    state = user_states.get(user_id, {})
    plt_name = state.get("platform", "")
    
    new_msg_text = msg.text or msg.caption or ""
    
    # استخراج emoji مميز من الرسالة
    custom_emoji_id = ""
    entities = msg.entities or msg.caption_entities or []
    for ent in entities:
        if hasattr(ent, 'type') and ent.type == "custom_emoji":
            custom_emoji_id = str(ent.custom_emoji_id)
            break
    
    # حفظ مؤقت في state (مش في الملف لحد ما يأكد)
    user_states[user_id]["pending_msg"] = new_msg_text
    user_states[user_id]["pending_eid"] = custom_emoji_id
    user_states[user_id]["action"] = "plt_welcome_confirm_pending"
    
    # بناء معاينة الرسالة بالتفاعل
    if custom_emoji_id:
        preview_line = f"<tg-emoji emoji-id='{custom_emoji_id}'>☀️</tg-emoji> {new_msg_text}"
    else:
        preview_line = new_msg_text
    
    mu = InlineKeyboardMarkup(row_width=1)
    try:
        mu.add(InlineKeyboardButton(f"✅ إضافة لمنصة {plt_name} فقط", callback_data=f"plt_welcome_confirm_{plt_name}_one"))
        mu.add(InlineKeyboardButton("🌐 إضافة لجميع المنصات", callback_data=f"plt_welcome_confirm_{plt_name}_all"))
        mu.add(InlineKeyboardButton("❌ إلغاء", callback_data=f"plt_settings_{plt_name}"))
    except:
        pass
    
    bot.send_message(msg.chat.id,
        f"📋 <b>معاينة الرسالة:</b>\n\n"
        f"{preview_line}\n\n"
        f"هل تريد تطبيق هذه الرسالة على:",
        parse_mode="HTML", reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data.startswith("plt_welcome_confirm_"))
def plt_welcome_confirm_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    # Parse: plt_welcome_confirm_{plt_name}_{scope}
    parts = call.data[len("plt_welcome_confirm_"):].rsplit("_", 1)
    if len(parts) != 2:
        bot.answer_callback_query(call.id, "❌ خطأ", show_alert=True)
        return
    plt_name, scope = parts
    bot.answer_callback_query(call.id)
    
    # جلب البيانات من state (مخزنة مؤقتاً)
    state = user_states.get(user_id, {})
    new_msg = state.get("pending_msg", "")
    eid = state.get("pending_eid", "")
    
    if not new_msg:
        # fallback: جرب من الملف
        data = load_platform_welcome()
        entry = data.get(plt_name, {})
        new_msg = entry.get("message", "")
        eid = entry.get("emoji_id", "")
    
    data = load_platform_welcome()
    
    if scope == "all":
        platforms = load_platforms()
        for pn in platforms:
            data[pn] = {"message": new_msg, "emoji_id": eid}
        save_platform_welcome(data)
        result_text = f"✅ <b>تم تعيين رسالة الترحيب لجميع المنصات!</b>"
    else:
        data[plt_name] = {"message": new_msg, "emoji_id": eid}
        save_platform_welcome(data)
        result_text = f"✅ <b>تم تعيين رسالة الترحيب لمنصة {plt_name}!</b>"
    
    # مسح state
    if user_id in user_states:
        del user_states[user_id]
    
    # معاينة الرسالة بتفاعلها
    if eid:
        preview = f"<tg-emoji emoji-id='{eid}'>☀️</tg-emoji> {new_msg}"
    else:
        preview = new_msg
    
    mu = InlineKeyboardMarkup()
    try:
        mu.add(make_back_button(" رجوع للمنصات", "admin_platform_settings"))
    except:
        mu.add(InlineKeyboardButton("◀ رجوع", callback_data="admin_platform_settings"))
    
    # تأكيد التعيين مع عرض الرسالة كاملة
    confirm_text = (
        f"{result_text}\n\n"
        f"<tg-emoji emoji-id='5444862611168928701'>✅</tg-emoji> <b>تم التحقق بنجاح!</b>\n\n"
        f"<b>رسالتك التي تم تعيينها:</b>\n{preview}"
    )
    bot.send_message(call.message.chat.id,
        confirm_text,
        parse_mode="HTML", reply_markup=mu)


# ═══════ زر الرجوع من الدول - Back Button Settings ═══════

@bot.callback_query_handler(func=lambda call: call.data == "admin_back_btn_settings")
def admin_back_btn_settings_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    bot.answer_callback_query(call.id)
    settings = load_back_btn_settings()
    color = settings.get("color")
    color_names = {"success": "🟢 أخضر", "danger": "🔴 أحمر", "primary": "🔵 أزرق", None: "⬜ شفاف (بدون لون)"}
    current_color_name = color_names.get(color, "⬜ شفاف")
    
    text = (
        "🔙 <b>إعدادات زر الرجوع</b>\n\n"
        f"<b>اللون الحالي:</b> {current_color_name}\n\n"
        "اختر لون زر الرجوع الذي يظهر في كل مكان:"
    )
    mu = InlineKeyboardMarkup(row_width=1)
    try:
        mu.add(InlineKeyboardButton(" أخضر", callback_data="back_btn_color_success", icon_custom_emoji_id="5321334093126842469", style="success"))
        mu.add(InlineKeyboardButton(" أحمر", callback_data="back_btn_color_danger", icon_custom_emoji_id="5321334093126842469", style="danger"))
        mu.add(InlineKeyboardButton(" أزرق", callback_data="back_btn_color_primary", icon_custom_emoji_id="5321334093126842469", style="primary"))
        mu.add(InlineKeyboardButton(" شفاف", callback_data="back_btn_color_none", icon_custom_emoji_id="5321334093126842469"))
        mu.add(make_back_button(" رجوع للوحة", "admin"))
    except:
        mu.add(InlineKeyboardButton("🟢 أخضر", callback_data="back_btn_color_success"))
        mu.add(InlineKeyboardButton("🔴 أحمر", callback_data="back_btn_color_danger"))
        mu.add(InlineKeyboardButton("🔵 أزرق", callback_data="back_btn_color_primary"))
        mu.add(InlineKeyboardButton("⬜ شفاف", callback_data="back_btn_color_none"))
        mu.add(InlineKeyboardButton("◀ رجوع", callback_data="admin"))
    bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=mu)

@bot.callback_query_handler(func=lambda call: call.data.startswith("back_btn_color_"))
def back_btn_color_cb(call):
    user_id = call.from_user.id
    if not is_admin(user_id): return
    color_key = call.data[len("back_btn_color_"):]
    color = None if color_key == "none" else color_key
    settings = load_back_btn_settings()
    settings["color"] = color
    save_back_btn_settings(settings)
    color_names = {"success": "🟢 أخضر", "danger": "🔴 أحمر", "primary": "🔵 أزرق", None: "⬜ شفاف"}
    color_name = color_names.get(color, "⬜ شفاف")
    bot.answer_callback_query(call.id, f"✅ تم تغيير لون زر الرجوع: {color_name}", show_alert=True)
    # إرسال رسالة تأكيد جديدة
    mu = InlineKeyboardMarkup(row_width=1)
    try:
        kw = {"callback_data": "admin_back_btn_settings", "icon_custom_emoji_id": "5321334093126842469"}
        kw["style"] = color if color else "primary"
        mu.add(InlineKeyboardButton(f" زر الرجوع الحالي ({color_name})", **kw))
        mu.add(make_back_button(" رجوع للوحة", "admin"))
    except:
        mu.add(InlineKeyboardButton(f"🔙 زر الرجوع ({color_name})", callback_data="admin_back_btn_settings"))
        mu.add(InlineKeyboardButton("◀ رجوع", callback_data="admin"))
    bot.send_message(call.message.chat.id,
        f"✅ <b>تم تعيين لون زر الرجوع: {color_name}</b>\n\n"
        f"الآن جميع أزرار الرجوع في البوت ستظهر باللون {color_name}",
        parse_mode="HTML", reply_markup=mu)


if __name__ == "__main__":
    load_data()
    
    monitoring_threads = []
    print("🚀 بدء تشغيل نظام المراقبة متعدد الحسابات...")
    
    for site_key in ["GROUP", "Fly sms", "Number_Panel", "Bolt", "iVASMS", "MSI", "proton SMS", "IMS", "Roxy SMS", "TimeSMS", "Konekta", "hadi", "fire", "Seven1Tel", "Gaza SMS", "Km sms", "Grand SMS", "Purple SMS"]:
        if SETTINGS[site_key]["enabled"]:
            accounts = get_site_accounts(site_key)
            site_name = SETTINGS[site_key]["name"]
            
            if accounts:
                print(f"\n📋 {site_name}: وجدت {len(accounts)} حساب")
                for account in accounts:
                    username = account.get('username', 'N/A')
                    thread = Thread(target=start_monitoring_for_account, args=(site_key, account), daemon=True)
                    monitoring_threads.append(thread)
                    thread.start()
                    print(f"  ✅ بدء مراقبة: {username}")
            else:
                print(f"  ⚠️ {site_name}: لا توجد حسابات")
    
    print(f"\n🎯 إجمالي Threads النشطة: {len(monitoring_threads)}")
    
    import requests
    try:
        bot_token = BOT_TOKEN
        delete_webhook_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook?drop_pending_updates=true"
        response = requests.get(delete_webhook_url)
        print(f"🔄 تم حذف webhook وتنظيف التحديثات المعلقة: {response.json()}")
    except Exception as e:
        print(f"⚠️ خطأ في حذف webhook: {e}")
    
    print("\n✨ البوت جاهز للعمل!\n")
    
    try:
        from telebot.types import BotCommand
        commands = [
            BotCommand("start",       "♻️ Start / Bot entry"),
            BotCommand("takenumber",  "☎️ Takenumber / Pull number"),
        ]
        bot.set_my_commands(commands)
        print("✅ تم تسجيل الأوامر بنجاح!")
    except Exception as e:
        print(f"⚠️ خطأ في تسجيل الأوامر: {e}")
    
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            print(f"🚀 محاولة بدء polling (محاولة {attempt + 1}/{max_retries})...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
            break
        except Exception as e:
            if "409" in str(e) or "Conflict" in str(e):
                if attempt < max_retries - 1:
                    print(f"⚠️ تعارض polling (409) - إعادة المحاولة بعد {retry_delay} ثواني...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"❌ فشل بدء البوت بعد {max_retries} محاولات!")
                    raise
            else:
                raise
