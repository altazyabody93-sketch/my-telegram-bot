"""
🌟 بوت المطري OTP - نسخة نظيفة بدون لوحات
- إدارة الكومبوهات والأرقام
- بث الأكواد من قناة تليجرام
- لوحة تحكم إدارية كاملة
- شعارات SVG حقيقية مدمجة
"""

import time
import requests
import json
import re
import os
import io
import base64
from datetime import datetime, date, timedelta
from urllib.parse import quote_plus, unquote
from pathlib import Path
import sqlite3
import telebot
from telebot import types
import threading
import traceback
import random
import logging

# ======================
# 🔧 إعدادات عامة
# ======================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8814038881:AAGyuACUYA4YPKlJQhAyUMkpRNiV0u1gNuU")

# ✅ التعديل هنا: معالجة CHAT_IDS بشكل آمن
CHAT_IDS_RAW = os.environ.get("CHAT_IDS", "-1003539412026")
if "," in CHAT_IDS_RAW:
    CHAT_IDS = CHAT_IDS_RAW.split(",")
else:
    CHAT_IDS = [CHAT_IDS_RAW]

ADMIN_IDS = [7602226699, 7325566792]
DB_PATH = "bot.db"
SENT_MESSAGES_FILE = "sent_messages.json"
CHANNEL_USERNAME = "@jsjsgsjsvh"
REFRESH_INTERVAL = 5

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN يجب تعيينه في Environment Variables على Render")

# ======================
# 🎨 شعارات SVG مدمجة (ما تنحجب أبداً)
# ======================
SERVICE_SVGS = {
    "whatsapp": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='22' fill='%2325D366'/><path fill='%23fff' d='M50 18c-17.6 0-32 14.4-32 32 0 6 1.7 11.8 4.8 16.8L18 82l15.6-4.7C38.6 80.1 44.2 82 50 82c17.6 0 32-14.4 32-32S67.6 18 50 18zm18.6 45.6c-.8 2.2-4.6 4.2-6.4 4.5-1.6.3-3.7.4-5.9-.4-1.4-.5-3.1-1.1-5.4-2.2-9.5-4.1-15.7-13.7-16.2-14.3-.5-.7-3.9-5.1-3.9-9.7s2.4-6.9 3.3-7.9c.9-.9 1.9-1.2 2.6-1.2.6 0 1.2 0 1.7 0 .6 0 1.3-.2 2 .1 1.6.7 2.6 3 2.9 3.9.3.9.5 1.5 0 2.4-.4.9-1.5 2.4-2.2 3.4 0 0 .7.7 1.4 1.5 2.4 2.7 5.3 5.5 9.6 7.1 1.5.5 2.3.6 3-.4.6-1 2.5-3 3.2-4 .7-1 1.4-.8 2.3-.5.9.3 5.8 2.7 6.8 3.2 1 .5 1.6.7 1.8 1.1.2.5.2 2.5-.6 4.7z'/></svg>",
    "telegram": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='22' fill='%2326A5E4'/><path fill='%23fff' d='M22 50l50-22-7 48-18-8-7 12-3-17 31-26-37 24-9-4z'/></svg>",
    "tiktok": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='48' fill='%23000'/><path fill='%2325F4EE' d='M62 22c2 8 8 14 16 15v9c-6 0-12-2-16-5v22c0 12-9 20-20 20s-20-8-20-20 9-21 20-21v9c-6 0-11 5-11 12s5 12 11 12 12-6 12-12V22h8z'/><path fill='%23FE2C55' d='M70 22c2 8 8 14 16 15v9c-6 0-12-2-16-5v22c0 12-9 20-20 20v-9c6 0 12-6 12-12V22h8z'/></svg>",
    "facebook": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='22' fill='%231877F2'/><path fill='%23fff' d='M58 84V52h10l1-12H58v-7c0-3 1-5 5-5h6V17h-9c-10 0-15 6-15 14v9H36v12h9v32h13z'/></svg>",
    "instagram": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><defs><radialGradient id='ig' cx='30%25' cy='30%25' r='80%25'><stop offset='0%25' stop-color='%23FEDA75'/><stop offset='50%25' stop-color='%23FA7E1E'/><stop offset='100%25' stop-color='%23D62976'/></radialGradient></defs><rect width='100' height='100' rx='22' fill='url(%23ig)'/><rect x='22' y='22' width='56' height='56' rx='14' fill='none' stroke='%23fff' stroke-width='5'/><circle cx='50' cy='50' r='13' fill='none' stroke='%23fff' stroke-width='5'/><circle cx='72' cy='28' r='4' fill='%23fff'/></svg>",
    "snapchat": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='22' fill='%23FFFC00'/><path fill='%23000' d='M50 16c-13 0-23 9-23 21 0 6 1 11 2 16-2 1-4 2-7 2-1 0-2 1-2 2 0 4 8 5 11 7 1 1 1 4 2 6 1 3 4 5 8 5 3 0 5-1 7-1 3 0 6 6 13 6 7 0 10-6 13-6 2 0 4 1 7 1 4 0 7-2 8-5 1-2 1-5 2-6 3-2 11-3 11-7 0-1-1-2-2-2-3 0-5-1-7-2 1-5 2-10 2-16 0-12-10-21-23-21-3 0-6 1-8 2-2-1-5-2-8-2z'/></svg>",
    "google": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='22' fill='%23fff'/><path fill='%234285F4' d='M58 50c0-1-.1-2-.2-3H50v6h5.5c-.5 2-2 4-4.5 5l4 3c3-2 5-6 5-10z'/><path fill='%2334A853' d='M40 56c1 4 4 7 9 7 3 0 5-1 7-3l-4-3c-1 1-2 1-4 1-3 0-5-2-6-4z'/><path fill='%23FBBC04' d='M40 44l-4 2c-1 1-1 3-1 4s0 3 1 4l4-2c-.5-1-.5-2-.5-3z'/><path fill='%23EA4335' d='M50 36c3 0 5 1 6 2l-3 3c-1-1-2-1-4-1-5 0-9 4-9 4l-4-2c0-3 4-6 14-6z'/></svg>",
    "twitter": "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='22' fill='%23000'/><path fill='%23fff' d='M70 35c-2 1-4 1-6 1 2-1 4-3 5-5-2 1-4 2-7 2-2-2-5-3-8-3-6 0-11 5-11 11 0 1 0 2 .3 3-9 0-17-5-22-12-1 2-1 4-1 6 0 4 2 7 5 9-2 0-4-1-5-2v.1c0 5 4 10 9 11-1 0-3 .5-4 .5-1 0-2 0-3-.1 2 4 6 7 11 7-4 3-9 5-15 5-1 0-2 0-3-.1 5 3 11 5 18 5 21 0 33-18 33-33v-1c2-2 4-3 6-6z'/></svg>",
}

# ربط كود الخدمة بالشعار الصحيح
SERVICE_TO_KEY = {
    "#WP": "whatsapp", "#TG": "telegram", "#TT": "tiktok", "#FB": "facebook",
    "#IG": "instagram", "#SC": "snapchat", "#GG": "google", "#TW": "twitter",
    "#DC": "telegram", "#AMZ": "google", "#APL": "google", "#MS": "google",
    "#IN": "google", "#UB": "telegram", "#NF": "google", "#SP": "google",
    "#YT": "google", "#GH": "google", "#PP": "google", "#BK": "telegram",
    "#AB": "google", "#OLX": "google", "#STC": "whatsapp", "#TL": "telegram",
}

SERVICE_NAMES_AR = {
    "#WP": "واتساب", "#TG": "تيليجرام", "#TT": "تيك توك",
    "#FB": "فيسبوك", "#IG": "انستقرام", "#SC": "سناب شات",
    "#GG": "جوجل", "#TW": "تويتر/X", "#DC": "ديسكورد",
    "#AMZ": "امازون", "#APL": "ابل", "#MS": "مايكروسوفت",
    "#IN": "لينكدإن", "#UB": "اوبر", "#NF": "نتفلكس",
    "#SP": "سبوتيفاي", "#YT": "يوتيوب", "#GH": "جيت هاب",
    "#PP": "باي بال", "#BK": "بوكينج", "#AB": "ايربنب",
    "#OLX": "اوليكس", "#STC": "اس تي سي", "#TL": "تالا",
}

def get_service_logo(service_code):
    key = SERVICE_TO_KEY.get(service_code, "")
    return SERVICE_SVGS.get(key)

def get_service_name(service_code):
    return SERVICE_NAMES_AR.get(service_code, service_code.replace("#", ""))

def make_platforms_grid_svg():
    """توليد صورة PNG جميلة فيها شعارات المنصات الحقيقية"""
    from PIL import Image, ImageDraw, ImageFont
    import io
    
    added_platforms = get_platforms()
    
    # ترتيب المنصات مع ألوانها وأيقوناتها المرسومة
    platform_icons = {
        "whatsapp": ("#25D366", "WA", "واتساب"),
        "telegram": ("#26A5E4", "TG", "تيليجرام"),
        "facebook": ("#1877F2", "FB", "فيسبوك"),
        "instagram": ("#DD2A7B", "IG", "انستقرام"),
        "tiktok": ("#FE2C55", "TT", "تيك توك"),
        "snapchat": ("#FFFC00", "SC", "سناب شات"),
        "google": ("#4285F4", "G", "جوجل"),
        "twitter": ("#000000", "X", "تويتر"),
    }
    
    # المنصات المعروضة
    shown = [(p, *platform_icons[p]) for p in platform_icons if p in added_platforms]
    if not shown:
        return None
    
    # أبعاد الصورة
    cols = 2
    rows = (len(shown) + cols - 1) // cols
    item_w = 220
    item_h = 110
    padding = 20
    title_h = 70
    width = cols * item_w + padding * 3
    height = rows * item_h + padding * (rows + 1) + title_h
    
    # إنشاء الصورة بخلفية متدرجة
    img = Image.new('RGB', (width, height), color='#0a0e1a')
    draw = ImageDraw.Draw(img)
    
    # رسم خلفية متدرجة بسيطة
    for y in range(height):
        ratio = y / height
        r = int(10 + (26 - 10) * ratio)
        g = int(14 + (31 - 14) * ratio)
        b = int(26 + (46 - 26) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # محاولة استخدام خط افتراضي
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        icon_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    except:
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        icon_font = ImageFont.load_default()
    
    # العنوان
    title = "📱 المنصات المتاحة"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = bbox[2] - bbox[0]
    draw.text(((width - title_w) / 2, 20), title, font=title_font, fill='#00ffc8')
    
    # رسم المنصات
    for idx, (key, color, abbr, name_ar) in enumerate(shown):
        row = idx // cols
        col = idx % cols
        x = padding + col * (item_w + padding)
        y = title_h + padding + row * (item_h + padding)
        
        # بطاقة لكل منصة
        # خلفية شبه شفافة
        draw.rounded_rectangle([x, y, x + item_w, y + item_h], radius=15, fill=(31, 41, 55))
        # إطار متوهج
        glow_color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        draw.rounded_rectangle([x, y, x + item_w, y + item_h], radius=15, outline=glow_color, width=3)
        
        # دائرة الأيقونة
        icon_size = 70
        icon_x = x + 15
        icon_y = y + (item_h - icon_size) // 2
        draw.ellipse([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size], fill=glow_color)
        
        # رمز المنصة داخل الدائرة
        bbox = draw.textbbox((0, 0), abbr, font=icon_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(
            (icon_x + (icon_size - text_w) / 2, icon_y + (icon_size - text_h) / 2 - 4),
            abbr, font=icon_font, fill='#fff'
        )
        
        # اسم المنصة بالعربي
        name_x = icon_x + icon_size + 20
        name_y = y + (item_h // 2) - 10
        draw.text((name_x, name_y), name_ar, font=name_font, fill='#fff')
        
        # الاسم الإنجليزي تحت
        eng_font = name_font
        try:
            eng_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except: pass
        draw.text((name_x, name_y + 25), key.capitalize(), font=eng_font, fill='#9ca3af')
    
    # حفظ في BytesIO
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

# ======================
# 🌍 رموز الدول
# ======================
COUNTRY_CODES = {
    "1": ("USA/Canada", "🇺🇸", "US"),
    "7": ("Russia", "🇷🇺", "RU"),
    "20": ("Egypt", "🇪🇬", "EG"),
    "27": ("South Africa", "🇿🇦", "ZA"),
    "30": ("Greece", "🇬🇷", "GR"),
    "31": ("Netherlands", "🇳🇱", "NL"),
    "32": ("Belgium", "🇧🇪", "BE"),
    "33": ("France", "🇫🇷", "FR"),
    "34": ("Spain", "🇪🇸", "ES"),
    "36": ("Hungary", "🇭🇺", "HU"),
    "39": ("Italy", "🇮🇹", "IT"),
    "40": ("Romania", "🇷🇴", "RO"),
    "41": ("Switzerland", "🇨🇭", "CH"),
    "43": ("Austria", "🇦🇹", "AT"),
    "44": ("United Kingdom", "🇬🇧", "UK"),
    "45": ("Denmark", "🇩🇰", "DK"),
    "46": ("Sweden", "🇸🇪", "SE"),
    "47": ("Norway", "🇳🇴", "NO"),
    "48": ("Poland", "🇵🇱", "PL"),
    "49": ("Germany", "🇩🇪", "DE"),
    "51": ("Peru", "🇵🇪", "PE"),
    "52": ("Mexico", "🇲🇽", "MX"),
    "53": ("Cuba", "🇨🇺", "CU"),
    "54": ("Argentina", "🇦🇷", "AR"),
    "55": ("Brazil", "🇧🇷", "BR"),
    "56": ("Chile", "🇨🇱", "CL"),
    "57": ("Colombia", "🇨🇴", "CO"),
    "58": ("Venezuela", "🇻🇪", "VE"),
    "60": ("Malaysia", "🇲🇾", "MY"),
    "61": ("Australia", "🇦🇺", "AU"),
    "62": ("Indonesia", "🇮🇩", "ID"),
    "63": ("Philippines", "🇵🇭", "PH"),
    "64": ("New Zealand", "🇳🇿", "NZ"),
    "65": ("Singapore", "🇸🇬", "SG"),
    "66": ("Thailand", "🇹🇭", "TH"),
    "81": ("Japan", "🇯🇵", "JP"),
    "82": ("South Korea", "🇰🇷", "KR"),
    "84": ("Vietnam", "🇻🇳", "VN"),
    "86": ("China", "🇨🇳", "CN"),
    "90": ("Turkey", "🇹🇷", "TR"),
    "91": ("India", "🇮🇳", "IN"),
    "92": ("Pakistan", "🇵🇰", "PK"),
    "93": ("Afghanistan", "🇦🇫", "AF"),
    "94": ("Sri Lanka", "🇱🇰", "LK"),
    "95": ("Myanmar", "🇲🇲", "MM"),
    "98": ("Iran", "🇮🇷", "IR"),
    "211": ("South Sudan", "🇸🇸", "SS"),
    "212": ("Morocco", "🇲🇦", "MA"),
    "213": ("Algeria", "🇩🇿", "DZ"),
    "216": ("Tunisia", "🇹🇳", "TN"),
    "218": ("Libya", "🇱🇾", "LY"),
    "220": ("Gambia", "🇬🇲", "GM"),
    "221": ("Senegal", "🇸🇳", "SN"),
    "222": ("Mauritania", "🇲🇷", "MR"),
    "223": ("Mali", "🇲🇱", "ML"),
    "224": ("Guinea", "🇬🇳", "GN"),
    "225": ("Ivory Coast", "🇨🇮", "CI"),
    "226": ("Burkina Faso", "🇧🇫", "BF"),
    "227": ("Niger", "🇳🇪", "NE"),
    "228": ("Togo", "🇹🇬", "TG"),
    "229": ("Benin", "🇧🇯", "BJ"),
    "230": ("Mauritius", "🇲🇺", "MU"),
    "231": ("Liberia", "🇱🇷", "LR"),
    "232": ("Sierra Leone", "🇸🇱", "SL"),
    "233": ("Ghana", "🇬🇭", "GH"),
    "234": ("Nigeria", "🇳🇬", "NG"),
    "235": ("Chad", "🇹🇩", "TD"),
    "236": ("Central African Rep", "🇨🇫", "CF"),
    "237": ("Cameroon", "🇨🇲", "CM"),
    "238": ("Cape Verde", "🇨🇻", "CV"),
    "239": ("Sao Tome", "🇸🇹", "ST"),
    "240": ("Equatorial Guinea", "🇬🇶", "GQ"),
    "241": ("Gabon", "🇬🇦", "GA"),
    "242": ("Congo", "🇨🇬", "CG"),
    "243": ("DR Congo", "🇨🇩", "CD"),
    "244": ("Angola", "🇦🇴", "AO"),
    "245": ("Guinea-Bissau", "🇬🇼", "GW"),
    "248": ("Seychelles", "🇸🇨", "SC"),
    "249": ("Sudan", "🇸🇩", "SD"),
    "250": ("Rwanda", "🇷🇼", "RW"),
    "251": ("Ethiopia", "🇪🇹", "ET"),
    "252": ("Somalia", "🇸🇴", "SO"),
    "253": ("Djibouti", "🇩🇯", "DJ"),
    "254": ("Kenya", "🇰🇪", "KE"),
    "255": ("Tanzania", "🇹🇿", "TZ"),
    "256": ("Uganda", "🇺🇬", "UG"),
    "257": ("Burundi", "🇧🇮", "BI"),
    "258": ("Mozambique", "🇲🇿", "MZ"),
    "260": ("Zambia", "🇿🇲", "ZM"),
    "261": ("Madagascar", "🇲🇬", "MG"),
    "262": ("Reunion", "🇷🇪", "RE"),
    "263": ("Zimbabwe", "🇿🇼", "ZW"),
    "264": ("Namibia", "🇳🇦", "NA"),
    "265": ("Malawi", "🇲🇼", "MW"),
    "266": ("Lesotho", "🇱🇸", "LS"),
    "267": ("Botswana", "🇧🇼", "BW"),
    "268": ("Eswatini", "🇸🇿", "SZ"),
    "269": ("Comoros", "🇰🇲", "KM"),
    "350": ("Gibraltar", "🇬🇮", "GI"),
    "351": ("Portugal", "🇵🇹", "PT"),
    "352": ("Luxembourg", "🇱🇺", "LU"),
    "353": ("Ireland", "🇮🇪", "IE"),
    "354": ("Iceland", "🇮🇸", "IS"),
    "355": ("Albania", "🇦🇱", "AL"),
    "356": ("Malta", "🇲🇹", "MT"),
    "357": ("Cyprus", "🇨🇾", "CY"),
    "358": ("Finland", "🇫🇮", "FI"),
    "359": ("Bulgaria", "🇧🇬", "BG"),
    "370": ("Lithuania", "🇱🇹", "LT"),
    "371": ("Latvia", "🇱🇻", "LV"),
    "372": ("Estonia", "🇪🇪", "EE"),
    "373": ("Moldova", "🇲🇩", "MD"),
    "374": ("Armenia", "🇦🇲", "AM"),
    "375": ("Belarus", "🇧🇾", "BY"),
    "376": ("Andorra", "🇦🇩", "AD"),
    "377": ("Monaco", "🇲🇨", "MC"),
    "378": ("San Marino", "🇸🇲", "SM"),
    "380": ("Ukraine", "🇺🇦", "UA"),
    "381": ("Serbia", "🇷🇸", "RS"),
    "382": ("Montenegro", "🇲🇪", "ME"),
    "383": ("Kosovo", "🇽🇰", "XK"),
    "385": ("Croatia", "🇭🇷", "HR"),
    "386": ("Slovenia", "🇸🇮", "SI"),
    "387": ("Bosnia", "🇧🇦", "BA"),
    "389": ("North Macedonia", "🇲🇰", "MK"),
    "420": ("Czech Republic", "🇨🇿", "CZ"),
    "421": ("Slovakia", "🇸🇰", "SK"),
    "423": ("Liechtenstein", "🇱🇮", "LI"),
    "500": ("Falkland Islands", "🇫🇰", "FK"),
    "501": ("Belize", "🇧🇿", "BZ"),
    "502": ("Guatemala", "🇬🇹", "GT"),
    "503": ("El Salvador", "🇸🇻", "SV"),
    "504": ("Honduras", "🇭🇳", "HN"),
    "505": ("Nicaragua", "🇳🇮", "NI"),
    "506": ("Costa Rica", "🇨🇷", "CR"),
    "507": ("Panama", "🇵🇦", "PA"),
    "509": ("Haiti", "🇭🇹", "HT"),
    "591": ("Bolivia", "🇧🇴", "BO"),
    "592": ("Guyana", "🇬🇾", "GY"),
    "593": ("Ecuador", "🇪🇨", "EC"),
    "595": ("Paraguay", "🇵🇾", "PY"),
    "597": ("Suriname", "🇸🇷", "SR"),
    "598": ("Uruguay", "🇺🇾", "UY"),
    "670": ("Timor-Leste", "🇹🇱", "TL"),
    "673": ("Brunei", "🇧🇳", "BN"),
    "674": ("Nauru", "🇳🇷", "NR"),
    "675": ("Papua New Guinea", "🇵🇬", "PG"),
    "676": ("Tonga", "🇹🇴", "TO"),
    "677": ("Solomon Islands", "🇸🇧", "SB"),
    "678": ("Vanuatu", "🇻🇺", "VU"),
    "679": ("Fiji", "🇫🇯", "FJ"),
    "680": ("Palau", "🇵🇼", "PW"),
    "685": ("Samoa", "🇼🇸", "WS"),
    "686": ("Kiribati", "🇰🇮", "KI"),
    "687": ("New Caledonia", "🇳🇨", "NC"),
    "688": ("Tuvalu", "🇹🇻", "TV"),
    "689": ("French Polynesia", "🇵🇫", "PF"),
    "691": ("Micronesia", "🇫🇲", "FM"),
    "692": ("Marshall Islands", "🇲🇭", "MH"),
    "850": ("North Korea", "🇰🇵", "KP"),
    "852": ("Hong Kong", "🇭🇰", "HK"),
    "853": ("Macau", "🇲🇴", "MO"),
    "855": ("Cambodia", "🇰🇭", "KH"),
    "856": ("Laos", "🇱🇦", "LA"),
    "960": ("Maldives", "🇲🇻", "MV"),
    "961": ("Lebanon", "🇱🇧", "LB"),
    "962": ("Jordan", "🇯🇴", "JO"),
    "963": ("Syria", "🇸🇾", "SY"),
    "964": ("Iraq", "🇮🇶", "IQ"),
    "965": ("Kuwait", "🇰🇼", "KW"),
    "966": ("Saudi Arabia", "🇸🇦", "SA"),
    "967": ("Yemen", "🇾🇪", "YE"),
    "968": ("Oman", "🇴🇲", "OM"),
    "970": ("Palestine", "🇵🇸", "PS"),
    "971": ("UAE", "🇦🇪", "AE"),
    "972": ("Israel", "🇮🇱", "IL"),
    "973": ("Bahrain", "🇧🇭", "BH"),
    "974": ("Qatar", "🇶🇦", "QA"),
    "975": ("Bhutan", "🇧🇹", "BT"),
    "976": ("Mongolia", "🇲🇳", "MN"),
    "977": ("Nepal", "🇳🇵", "NP"),
    "992": ("Tajikistan", "🇹🇯", "TJ"),
    "993": ("Turkmenistan", "🇹🇲", "TM"),
    "994": ("Azerbaijan", "🇦🇿", "AZ"),
    "995": ("Georgia", "🇬🇪", "GE"),
    "996": ("Kyrgyzstan", "🇰🇬", "KG"),
    "998": ("Uzbekistan", "🇺🇿", "UZ"),
}

# ======================
# 🗄️ دوال قاعدة البيانات
# ======================
def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM bot_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT, first_name TEXT, last_name TEXT,
            country_code TEXT, assigned_number TEXT,
            is_banned INTEGER DEFAULT 0, private_combo_country TEXT DEFAULT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS combos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT, country_code TEXT, numbers TEXT,
            UNIQUE(platform, country_code)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS otp_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT, otp TEXT, full_message TEXT,
            timestamp TEXT, assigned_to INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY, value TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS private_combos (
            user_id INTEGER, country_code TEXT, numbers TEXT,
            PRIMARY KEY (user_id, country_code)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS force_sub_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_url TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '', enabled INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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
    if existing_data:
        if country_code is None: country_code = existing_data[4]
        if assigned_number is None: assigned_number = existing_data[5]
        if private_combo_country is None: private_combo_country = existing_data[7]
    c.execute("""
        REPLACE INTO users (user_id, username, first_name, last_name, country_code, assigned_number, is_banned, private_combo_country)
        VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT is_banned FROM users WHERE user_id=?), 0), ?)
    """, (user_id, username, first_name, last_name, country_code, assigned_number, user_id, private_combo_country))
    conn.commit()
    conn.close()

def ban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_banned(user_id):
    user = get_user(user_id)
    return user and user[6] == 1

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned=0")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_combo(platform, country_code, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("SELECT numbers FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
        row = c.fetchone()
        if row:
            conn.close()
            return json.loads(row[0])
    c.execute("SELECT numbers FROM combos WHERE platform=? AND country_code=?", (platform, country_code))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

def save_combo(platform, country_code, numbers, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("REPLACE INTO private_combos (user_id, country_code, numbers) VALUES (?, ?, ?)",
                  (user_id, country_code, json.dumps(numbers)))
    else:
        c.execute("INSERT INTO combos (platform, country_code, numbers) VALUES (?, ?, ?)",
                  (platform, country_code, json.dumps(numbers)))
    conn.commit()
    conn.close()

def delete_combo(platform, country_code, user_id=None):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
        c = conn.cursor()
        if user_id:
            c.execute("DELETE FROM private_combos WHERE user_id=? AND country_code=?", (user_id, country_code))
        else:
            c.execute("DELETE FROM combos WHERE platform=? AND country_code=?", (platform, country_code))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ خطأ delete_combo: {e}")
        return False
    finally:
        if conn: conn.close()

def get_all_combos():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT platform, country_code FROM combos ORDER BY platform, country_code")
    combos = c.fetchall()
    conn.close()
    return combos

def get_platforms():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT platform FROM combos")
    return [row[0] for row in c.fetchall()]

def get_countries_by_platform(platform):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT country_code FROM combos WHERE platform=?", (platform,))
    return [row[0] for row in c.fetchall()]

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

def log_otp(number, otp, full_message, assigned_to=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO otp_logs (number, otp, full_message, timestamp, assigned_to) VALUES (?, ?, ?, ?, ?)",
              (number, otp, full_message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), assigned_to))
    conn.commit()
    conn.close()

def release_number(old_number):
    if not old_number: return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET assigned_number=NULL WHERE assigned_number=?", (old_number,))
    conn.commit()
    conn.close()

def get_otp_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM otp_logs")
    logs = c.fetchall()
    conn.close()
    return logs

def get_user_info(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_all_force_sub_channels(enabled_only=True):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if enabled_only:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels WHERE enabled = 1 ORDER BY id")
    else:
        c.execute("SELECT id, channel_url, description FROM force_sub_channels ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

def add_force_sub_channel(channel_url, description=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO force_sub_channels (channel_url, description, enabled) VALUES (?, ?, 1)",
                  (channel_url.strip(), description.strip()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_force_sub_channel(channel_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM force_sub_channels WHERE id = ?", (channel_id,))
    changed = c.rowcount > 0
    conn.commit()
    conn.close()
    return changed

def toggle_force_sub_channel(channel_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE force_sub_channels SET enabled = 1 - enabled WHERE id = ?", (channel_id,))
    conn.commit()
    conn.close()

# ======================
# 🤖 إنشاء بوت Telegram
# ======================
bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS

def safe_html(text):
    if not text: return ""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def get_platform_color(platform):
    """إرجاع إيموجي شعار المنصة الحقيقي للزر في تليجرام"""
    # في تليجرام لا تدعم الأزرار صوراً، نستخدم إيموجيات رسمية ملونة
    # كتطبيق للإيقونات، هذه أحسن ما يمكن في تلجرام
    colors = {
        "whatsapp": "💚",    # واتساب - قلب أخضر
        "telegram": "🩵",    # تيليجرام - قلب أزرق فاتح
        "tiktok": "🎵",      # تيك توك - نوتة موسيقى
        "facebook": "👍",    # فيسبوك - إبهام أزرق
        "instagram": "📷",   # انستقرام - كاميرا
        "snapchat": "👻",    # سناب شات - شبح
        "google": "🔴",      # جوجل - G أحمر (نستخدم دائرة حمراء)
        "twitter": "✖️",     # تويتر/X - X
    }
    return colors.get(platform.lower(), "📱")

# ======================
# 🔐 الاشتراك الإجباري
# ======================
def force_sub_check(user_id):
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return True
    for _, url, _ in channels:
        try:
            if url.startswith("https://t.me/"):
                ch = "@" + url.split("/")[-1]
            elif url.startswith("@"):
                ch = url
            else:
                continue
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            print(f"[!] خطأ في التحقق من القناة {url}: {e}")
            return False
    return True

def force_sub_markup():
    channels = get_all_force_sub_channels(enabled_only=True)
    if not channels:
        return None
    markup = types.InlineKeyboardMarkup()
    for _, url, desc in channels:
        text = f"📢 {desc}" if desc else "📢 اشترك في القناة"
        markup.add(types.InlineKeyboardButton(text, url=url))
    markup.add(types.InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub"))
    return markup

# ======================
# 🎮 أوامر البوت
# ======================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if is_banned(user_id):
        bot.reply_to(message, "<b>🚫 عذراً، لقد تم حظرك من استخدام البوت.</b>", parse_mode="HTML")
        return

    if not force_sub_check(user_id):
        markup = force_sub_markup()
        if markup:
            bot.send_message(chat_id, "<b>🔒 يجب الاشتراك في القنوات لاستخدام البوت.</b>", parse_mode="HTML", reply_markup=markup)
        return

    if not get_user(user_id):
        save_user(
            user_id, username=message.from_user.username or "",
            first_name=message.from_user.first_name or "",
            last_name=message.from_user.last_name or ""
        )
        for admin in ADMIN_IDS:
            try:
                bot.send_message(admin, f"🆕 مستخدم جديد: <code>{user_id}</code> @{safe_html(message.from_user.username or 'None')}", parse_mode="HTML")
            except: pass

    markup = types.InlineKeyboardMarkup(row_width=2)
    platforms = get_platforms()

    if not platforms:
        if is_admin(user_id):
            markup.add(types.InlineKeyboardButton("➕ إضافة كومبو (أدمن)", callback_data="admin_panel"))
            bot.send_message(chat_id, "⚠️ لا توجد منصات. أضف كومبو عبر الأدمن.", parse_mode="HTML", reply_markup=markup)
        else:
            bot.send_message(chat_id, "⚠️ البوت قيد التهيئة. حاول لاحقاً.", parse_mode="HTML")
        return

    # أولاً: إرسال صورة فيها شعارات المنصات الجميلة (PNG مرسوم بـ Pillow)
    try:
        platforms_img = make_platforms_grid_svg()
        if platforms_img:
            platforms_img.name = "platforms.png"
            bot.send_photo(chat_id, platforms_img, caption="<b>📱 الشعارات الحقيقية للمنصات المتاحة</b>", parse_mode="HTML")
    except Exception as e:
        print(f"[!] فشل إرسال صورة الشعارات: {e}")

    for platform in platforms:
        emoji = get_platform_color(platform)
        # زر كبير بإيموجي جذابة
        markup.add(types.InlineKeyboardButton(f"{emoji}  {platform.upper()}  {emoji}", callback_data=f"plat_{platform}"))

    if is_admin(user_id):
        markup.add(types.InlineKeyboardButton("🔐 Admin Panel", callback_data="admin_panel"))

    # النص الترحيبي مع إيموجيات الشعارات بشكل بارز
    emojis_row = " | ".join([get_platform_color(p) for p in platforms])
    fancy_text = (
        "<b>❍─── <u>𝐁𝐎𝐓 𝐌𝐎𝐇𝐀𝐌𝐌𝐄𝐃 𝐎𝐓𝐏</u> ───❍</b>\n\n"
        f"<b>{emojis_row}</b>\n\n"
        "<b>🔋 <u>𝐅𝐚𝐬𝐭 • 𝐒𝐞𝐜𝐮𝐫𝐞 • 𝐨𝐧𝐥𝐢𝐧𝐞</u></b>\n\n"
        f"<b>عدد المنصات المتاحة: {len(platforms)} ⬇️</b>"
    )
    bot.send_message(chat_id, fancy_text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    if force_sub_check(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم التحقق!", show_alert=True)
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ لم تشترك بعد!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("plat_"))
def handle_platform_selection(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if is_banned(user_id):
        return
    if not force_sub_check(user_id):
        return

    platform = call.data.split("_")[1]
    countries = get_countries_by_platform(platform)

    if not countries:
        bot.answer_callback_query(call.id, "❌ لا توجد دول.", show_alert=True)
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    for country_code in countries:
        if country_code in COUNTRY_CODES:
            name, flag, _ = COUNTRY_CODES[country_code]
            markup.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"cnt_{platform}_{country_code}"))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_platforms"))

    bot.edit_message_text(f"🌍 اختر الدولة لمنصة {platform.capitalize()}:", chat_id, message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, f"✅ {platform.capitalize()}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cnt_"))
def handle_country_selection(call):
    user_id = call.from_user.id
    parts = call.data.split("_")
    platform = parts[1]
    country_code = parts[2]
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    available_numbers = get_available_numbers(platform, country_code, user_id)
    if not available_numbers:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data=f"plat_{platform}"))
        bot.edit_message_text("<b>❌ عذراً، الأرقام كلها مستخدمة.</b>", chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        return

    assigned = random.choice(available_numbers)
    old_user = get_user(user_id)
    if old_user and old_user[5]:
        release_number(old_user[5])
    assign_number_to_user(user_id, assigned)
    save_user(user_id, country_code=country_code, assigned_number=assigned)

    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    msg_text = (
        f"╭────────────────────────────╮\n"
        f"│  📱 <b><u>رقمك المخصص</u></b>      │\n"
        f"├────────────────────────────┤\n"
        f"<blockquote>💻 <b>المنصة:</b> {platform.capitalize()}</blockquote>\n"
        f"<blockquote>📞 <b>الرقم:</b> <code>+{assigned}</code></blockquote>\n"
        f"<blockquote>🌍 <b>الدولة:</b> {flag} {name}</blockquote>\n"
        f"<blockquote>⏳ <b>الحالة:</b> في انتظار الكود...</blockquote>\n"
        f"╰────────────────────────────╯"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("𝑉𝑖𝑒𝑤 𝑂𝑡𝑝👀", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"))
    markup.row(
        types.InlineKeyboardButton("🔄 Change Number", callback_data=f"change_num_{platform}_{country_code}"),
        types.InlineKeyboardButton("🔙 Back", callback_data="back_to_platforms")
    )
    try:
        bot.edit_message_text(msg_text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id, "✅ تم استلام الرقم")
    except Exception as e: print(e)

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_num_"))
def change_number(call):
    user_id = call.from_user.id
    parts = call.data.split("_")
    platform = parts[2]
    country_code = parts[3]
    
    available_numbers = get_available_numbers(platform, country_code, user_id)
    if not available_numbers:
        bot.answer_callback_query(call.id, "❌ لا توجد أرقام متاحة.", show_alert=True)
        return
    
    old_user = get_user(user_id)
    if old_user and old_user[5]: release_number(old_user[5])
    assigned = random.choice(available_numbers)
    assign_number_to_user(user_id, assigned)
    save_user(user_id, assigned_number=assigned)
    
    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    msg_text = (
        f"╭────────────────────────────╮\n"
        f"│  📱 <b><u>رقمك المخصص</u></b>      │\n"
        f"├────────────────────────────┤\n"
        f"<blockquote>💻 <b>المنصة:</b> {platform.capitalize()}</blockquote>\n"
        f"<blockquote>📞 <b>الرقم:</b> <code>+{assigned}</code></blockquote>\n"
        f"<blockquote>🌍 <b>الدولة:</b> {flag} {name}</blockquote>\n"
        f"<blockquote>⏳ <b>الحالة:</b> في انتظار الكود...</blockquote>\n"
        f"╰────────────────────────────╯"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("𝑉𝑖𝑒𝑤 𝑂𝑡𝑝👀", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"))
    markup.row(
        types.InlineKeyboardButton("🔄 Change Number", callback_data=f"change_num_{platform}_{country_code}"),
        types.InlineKeyboardButton("🔙 Back", callback_data="back_to_platforms")
    )
    try:
        bot.edit_message_text(msg_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id, "✅ تم التغيير")
    except: pass

@bot.callback_query_handler(func=lambda call: call.data == "back_to_platforms")
def back_to_platforms(call):
    send_welcome(call.message)

# ======================
# 🆕 الأرقام المتاحة
# ======================
def get_available_numbers(platform, country_code, user_id=None):
    all_numbers = get_combo(platform, country_code, user_id)
    if not all_numbers: return []
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT assigned_number FROM users WHERE assigned_number IS NOT NULL AND assigned_number != ''")
    used_numbers = set(row[0] for row in c.fetchall())
    conn.close()
    return [num for num in all_numbers if num not in used_numbers]

# ======================
# 🔐 لوحة الأدمن
# ======================
def admin_main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("📥 إضافة كومبو", callback_data="admin_add_combo"),
        types.InlineKeyboardButton("🗑️ حذف كومبو", callback_data="admin_del_combo")
    )
    markup.row(
        types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
        types.InlineKeyboardButton("📄 تقرير شامل", callback_data="admin_full_report")
    )
    markup.row(
        types.InlineKeyboardButton("📢 إذاعة عامة", callback_data="admin_broadcast_all"),
        types.InlineKeyboardButton("📨 إذاعة مخصصة", callback_data="admin_broadcast_user")
    )
    markup.row(
        types.InlineKeyboardButton("🚫 حظر", callback_data="admin_ban"),
        types.InlineKeyboardButton("✅ رفع حظر", callback_data="admin_unban"),
        types.InlineKeyboardButton("👤 معلومات", callback_data="admin_user_info")
    )
    markup.row(
        types.InlineKeyboardButton("🔗 اشتراك إجباري", callback_data="admin_force_sub"),
        types.InlineKeyboardButton("🔑 برايفت", callback_data="admin_private_combo")
    )
    markup.add(types.InlineKeyboardButton("🔙 خروج", callback_data="back_to_platforms"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def show_admin_panel(call):
    if not is_admin(call.from_user.id):
        return
    text = "<b>❍─── <u>𝐋𝐎𝐆𝐈𝐍 𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋</u> ───❍</b>\n\n<b>👋 مرحباً بك يا مطور.</b>\n<b>────────────────────</b>"
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=admin_main_menu())
    except: pass

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_combo")
def admin_add_combo_step1(call):
    if not is_admin(call.from_user.id): return
    markup = types.InlineKeyboardMarkup()
    for p in ["whatsapp", "telegram", "facebook", "instagram", "tiktok", "snapchat", "google", "twitter"]:
        color = get_platform_color(p)
        markup.add(types.InlineKeyboardButton(f"{color} {p.capitalize()}", callback_data=f"add_plat_{p}"))
    bot.edit_message_text("اختر المنصة لإضافة كومبو:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_plat_"))
def admin_add_combo_step2(call):
    if not is_admin(call.from_user.id): return
    platform = call.data.split("_")[2]
    user_states[call.from_user.id] = {"action": "add_combo", "platform": platform}
    bot.send_message(call.message.chat.id, f"📤 أرسل ملف TXT بأرقام منصة {platform.capitalize()}:\nكل رقم في سطر، سيُحدد الدولة تلقائياً من أول رقم.")

@bot.message_handler(content_types=['document'])
def handle_combo_file(message):
    state = user_states.get(message.from_user.id)
    if not state or state.get("action") != "add_combo": return
    platform = state.get("platform")
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8')
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            bot.reply_to(message, "❌ الملف فارغ!")
            return
        first_num = clean_number(lines[0])
        country_code = None
        for code in COUNTRY_CODES:
            if first_num.startswith(code):
                country_code = code
                break
        if not country_code:
            bot.reply_to(message, "❌ لا يمكن تحديد الدولة!")
            return
        save_combo(platform, country_code, lines)
        name, flag, _ = COUNTRY_CODES[country_code]
        bot.reply_to(message, f"✅ تم حفظ الكومبو لمنصة {platform.capitalize()} في دولة {flag} {name}\n🔢 عدد الأرقام: {len(lines)}")
        del user_states[message.from_user.id]
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "admin_del_combo")
def admin_del_combo(call):
    if not is_admin(call.from_user.id): return
    combos = get_all_combos()
    if not combos:
        bot.answer_callback_query(call.id, "لا توجد كومبوهات!")
        return
    markup = types.InlineKeyboardMarkup()
    for platform, country_code in combos:
        if country_code in COUNTRY_CODES:
            name, flag, _ = COUNTRY_CODES[country_code]
            markup.add(types.InlineKeyboardButton(f"{flag} {name} ({platform.capitalize()})", callback_data=f"del_combo_{platform}_{country_code}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text("اختر الكومبو للحذف:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_combo_"))
def confirm_del_combo(call):
    if not is_admin(call.from_user.id): return
    parts = call.data.split("_")
    platform = parts[2]
    country_code = parts[3]
    success = delete_combo(platform, country_code)
    name, flag, _ = COUNTRY_CODES.get(country_code, ("Unknown", "🌍", ""))
    bot.answer_callback_query(call.id, f"{'✅' if success else '❌'} {flag} {name}", show_alert=True)
    admin_del_combo(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if not is_admin(call.from_user.id): return
    total_users = len(get_all_users())
    combos = get_all_combos()
    unique_countries = set(c[1] for c in combos)
    total_numbers = sum(len(get_combo(p, c)) for p, c in combos)
    otp_count = len(get_otp_logs())
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text(
        f"📊 <b>الإحصائيات:</b>\n\n"
        f"👥 المستخدمين: {total_users}\n"
        f"🌐 الدول: {len(unique_countries)}\n"
        f"📦 الكومبوهات: {len(combos)}\n"
        f"📞 إجمالي الأرقام: {total_numbers}\n"
        f"🔑 إجمالي الأكواد: {otp_count}",
        call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_all")
def admin_broadcast_all_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "broadcast_all"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text("أرسل الرسالة للإرسال للجميع:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "broadcast_all")
def admin_broadcast_all_step2(message):
    users = get_all_users()
    success = 0
    for uid in users:
        try:
            bot.send_message(uid, message.text)
            success += 1
        except: pass
    bot.reply_to(message, f"✅ تم الإرسال لـ {success}/{len(users)} مستخدم")
    del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban")
def admin_ban_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "ban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text("أدخل ID المستخدم لحظره:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "ban_user")
def admin_ban_step2(message):
    try:
        uid = int(message.text)
        ban_user(uid)
        bot.reply_to(message, f"✅ تم حظر {uid}")
    except: bot.reply_to(message, "❌ ID غير صحيح!")
    if message.from_user.id in user_states: del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_unban")
def admin_unban_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "unban_user"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text("أدخل ID المستخدم لرفع الحظر:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "unban_user")
def admin_unban_step2(message):
    try:
        uid = int(message.text)
        unban_user(uid)
        bot.reply_to(message, f"✅ تم رفع الحظر عن {uid}")
    except: bot.reply_to(message, "❌ ID غير صحيح!")
    if message.from_user.id in user_states: del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_user_info")
def admin_user_info_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "get_user_info"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text("أدخل ID المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "get_user_info")
def admin_user_info_step2(message):
    try:
        uid = int(message.text)
        user = get_user_info(uid)
        if not user:
            bot.reply_to(message, "❌ غير موجود!")
            return
        status = "محظور" if user[6] else "نشط"
        info = f"👤 المعلومات:\n🆔: {user[0]}\n@{user[1] or 'N/A'}\nالاسم: {user[2] or ''} {user[3] or ''}\n📞 الرقم: {user[5] or 'N/A'}\n🚦 الحالة: {status}"
        bot.reply_to(message, info)
    except Exception as e: bot.reply_to(message, f"❌ خطأ: {e}")
    if message.from_user.id in user_states: del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data == "admin_force_sub")
def admin_force_sub(call):
    if not is_admin(call.from_user.id): return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ إضافة قناة", callback_data="add_force_sub"))
    channels = get_all_force_sub_channels(enabled_only=False)
    for ch_id, url, desc in channels:
        markup.add(types.InlineKeyboardButton(f"🗑️ {desc or url}", callback_data=f"del_force_{ch_id}"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text("📡 إدارة قنوات الاشتراك الإجباري:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_force_sub")
def add_force_sub_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "add_force_sub_url"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_force_sub"))
    bot.edit_message_text("أرسل رابط القناة (@channel أو https://t.me/channel):", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_force_sub_url")
def add_force_sub_step2(message):
    url = message.text.strip()
    if add_force_sub_channel(url, url):
        bot.reply_to(message, f"✅ تم إضافة القناة: {url}")
    else:
        bot.reply_to(message, "❌ القناة مكررة أو خطأ!")
    if message.from_user.id in user_states: del user_states[message.from_user.id]

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_force_"))
def del_force_sub(call):
    if not is_admin(call.from_user.id): return
    ch_id = int(call.data.split("_")[2])
    delete_force_sub_channel(ch_id)
    bot.answer_callback_query(call.id, "✅ تم الحذف", show_alert=True)
    admin_force_sub(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_private_combo")
def admin_private_combo(call):
    if not is_admin(call.from_user.id): return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ تعيين دولة خاصة", callback_data="add_private_combo"))
    markup.add(types.InlineKeyboardButton("🗑️ إزالة دولة خاصة", callback_data="del_private_combo"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
    bot.edit_message_text("🔑 إدارة الكومبو الخاص:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_private_combo")
def add_private_combo_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "add_private_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_private_combo"))
    bot.edit_message_text("أرسل ID المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "add_private_user_id")
def add_private_combo_step2(message):
    try:
        uid = int(message.text)
        user_states[message.from_user.id] = f"add_private_country_{uid}"
        markup = types.InlineKeyboardMarkup(row_width=2)
        all_combos = get_all_combos()
        for country_code in set(c[1] for c in all_combos):
            if country_code in COUNTRY_CODES:
                name, flag, _ = COUNTRY_CODES[country_code]
                markup.add(types.InlineKeyboardButton(f"{flag} {name}", callback_data=f"set_priv_{uid}_{country_code}"))
        bot.reply_to(message, "اختر الدولة:", reply_markup=markup)
    except: bot.reply_to(message, "❌ ID غير صحيح!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_priv_"))
def set_private(call):
    if not is_admin(call.from_user.id): return
    parts = call.data.split("_")
    uid = int(parts[2])
    cc = parts[3]
    save_user(uid, private_combo_country=cc)
    bot.answer_callback_query(call.id, f"✅ تم التعيين", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "del_private_combo")
def del_private_step1(call):
    if not is_admin(call.from_user.id): return
    user_states[call.from_user.id] = "del_private_user_id"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_private_combo"))
    bot.edit_message_text("أرسل ID المستخدم:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda msg: user_states.get(msg.from_user.id) == "del_private_user_id")
def del_private_step2(message):
    try:
        uid = int(message.text)
        save_user(uid, private_combo_country=None)
        bot.reply_to(message, f"✅ تم الإزالة عن {uid}")
    except: bot.reply_to(message, "❌ ID غير صحيح!")
    if message.from_user.id in user_states: del user_states[message.from_user.id]

# ======================
# 🔄 دوال التنظيف والمعالجة
# ======================
def clean_html(text):
    if not text: return ""
    return re.sub(r'<[^>]+>', '', str(text)).strip()

def clean_number(number):
    if not number: return ""
    return re.sub(r'\D', '', str(number))

def get_country_info(number):
    number = number.strip().replace("+", "").replace(" ", "").replace("-", "")
    for code, (name, flag, short) in COUNTRY_CODES.items():
        if number.startswith(code):
            return name, flag, short
    return "Unknown", "🌍", "UN"

def mask_number(number):
    number = number.strip()
    if len(number) > 8:
        return number[:4] + "••••" + number[-3:]
    return number

def extract_otp(message):
    patterns = [
        r'(?:code|رمز|كود|verification|تحقق|otp|pin)[:\s]+(\d{3,8}(?:[- ]\d{3,4})?)',
        r'(\d{3})[- ](\d{3,4})',
        r'\b(\d{4,8})\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            if len(match.groups()) > 1:
                return ''.join(match.groups()).replace(' ', '').replace('-', '')
            return match.group(1).replace(' ', '').replace('-', '')
    all_numbers = re.findall(r'\d{4,8}', message)
    if all_numbers:
        return all_numbers[0]
    return "N/A"

def detect_service(message):
    message_lower = message.lower()
    services = {
        "#WP": ["whatsapp", "واتساب", "واتس"],
        "#FB": ["facebook", "فيسبوك", "fb"],
        "#IG": ["instagram", "انستقرام", "انستا"],
        "#TG": ["telegram", "تيليجرام", "تلي"],
        "#TW": ["twitter", "تويتر", "x"],
        "#GG": ["google", "gmail", "جوجل"],
        "#DC": ["discord", "ديسكورد"],
        "#SC": ["snapchat", "سناب"],
        "#TT": ["tiktok", "تيك توك", "تيك"],
        "#AMZ": ["amazon", "امازون"],
        "#APL": ["apple", "ابل", "icloud"],
        "#MS": ["microsoft", "مايكروسوفت"],
        "#IN": ["linkedin", "لينكد"],
        "#UB": ["uber", "اوبر"],
        "#NF": ["netflix", "نتفلكس"],
        "#SP": ["spotify", "سبوتيفاي"],
        "#YT": ["youtube", "يوتيوب"],
        "#GH": ["github", "جيت هاب"],
        "#PP": ["paypal", "باي بال"],
        "#BK": ["booking", "بوكينج"],
    }
    for code, keywords in services.items():
        for kw in keywords:
            if kw in message_lower:
                return code
    return "Unknown"

def format_message(date_str, number, sms):
    country_name, country_flag, country_code = get_country_info(number)
    masked_num = mask_number(number)
    otp_code = extract_otp(sms)
    service = detect_service(sms)
    return (
        f"╭───────────────╮\n"
        f"│ {country_flag} {service} {masked_num}\n"
        f"╰───────────────╯"
    )

# ======================
# 📤 إرسال الأكواد للمستخدمين والقنوات
# ======================
def delete_message_after_delay(chat_id, message_id, delay=150):
    time.sleep(delay)
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
        requests.post(url, data={"chat_id": chat_id, "message_id": message_id}, timeout=5)
    except: pass

def send_to_telegram_group(text, otp_code, service_code=""):
    """إرسال الكود للجروب مع شعار المنصة الحقيقي"""
    success_count = 0
    logo_svg = get_service_logo(service_code) if service_code else None
    service_name = get_service_name(service_code) if service_code else "OTP"
    
    keyboard = {
        "inline_keyboard": [
            [{"text": f"🔑 {otp_code} — اضغط للنسخ", "copy_text": {"text": str(otp_code)}}],
            [
                {"text": "💬 𝐶ℎ𝑎𝑡 ↗️", "url": f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"},
                {"text": "🤖 𝑂𝑝𝑒𝑛 𝐵𝑜𝑡 ↗️", "url": "https://t.me/MO_5_H_ABOT"}
            ],
            [{"text": "𝑀𝑟: 𝐶𝑜𝑚𝑚𝑎𝑛𝑑𝑜 ↗️", "url": "https://t.me/CM_ED871"}]
        ]
    }
    
    # محاولة إرسال صورة مع شعار
    if logo_svg:
        try:
            svg_content = unquote(logo_svg.split(',', 1)[1])
            svg_bytes = svg_content.encode('utf-8')
            for chat_id in CHAT_IDS:
                chat_id = chat_id.strip()
                if not chat_id: continue
                try:
                    url_photo = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                    caption = (
                        f"<b>✨ {service_name} ✨</b>\n\n"
                        f"<b>{text}</b>\n\n"
                        f"🔐 <b>الكود:</b> <code>{otp_code}</code>"
                    )
                    files = {'photo': ('logo.svg', io.BytesIO(svg_bytes), 'image/svg+xml')}
                    data = {
                        'chat_id': chat_id,
                        'caption': caption,
                        'parse_mode': 'HTML',
                        'reply_markup': json.dumps(keyboard)
                    }
                    resp = requests.post(url_photo, files=files, data=data, timeout=15)
                    if resp.status_code == 200:
                        success_count += 1
                        msg_id = resp.json()["result"]["message_id"]
                        threading.Thread(target=delete_message_after_delay, args=(chat_id, msg_id, 150), daemon=True).start()
                        continue
                except Exception as e:
                    print(f"[!] خطأ إرسال الصورة: {e}")
        except Exception as e:
            print(f"[!] خطأ معالجة SVG: {e}")
    
    # fallback للنص
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        chat_id = chat_id.strip()
        if not chat_id: continue
        try:
            payload = {
                "chat_id": chat_id,
                "text": f"<b>✨ {service_name} ✨</b>\n\n{text}",
                "parse_mode": "HTML",
                "reply_markup": json.dumps(keyboard)
            }
            resp = requests.post(url, data=payload, timeout=10)
            if resp.status_code == 200:
                success_count += 1
                msg_id = resp.json()["result"]["message_id"]
                threading.Thread(target=delete_message_after_delay, args=(chat_id, msg_id, 150), daemon=True).start()
        except Exception as e:
            print(f"[!] خطأ إرسال نص: {e}")
    
    return success_count > 0

def send_otp_to_user_and_group(number, sms, otp_code, service_code):
    """يرسل الكود للمستخدم المخصص + القنوات"""
    country_name, country_flag, _ = get_country_info(number)
    user_id = get_user_by_number(number)
    
    if user_id:
        try:
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("𝑂𝑤𝑛𝑒𝑟🤴🏻", url="https://t.me/CM_ED871"),
                types.InlineKeyboardButton("𝐶ℎ𝑎𝑛𝑛𝑒𝑙🫀", url="https://t.me/CommandoOTP65")
            )
            bot.send_message(
                user_id,
                f"✨ <b><u>𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐎 𝐎𝐓𝐏 𝐑𝐄𝐂𝐈𝐕𝐄𝐃✨</u></b>\n\n"
                f"🌍 <b>الدولة:</b> {safe_html(country_name)} {country_flag}\n"
                f"⚙ <b>الخدمة:</b> {safe_html(service_code)}\n"
                f"☎ <b>الرقم:</b> <code>{safe_html(number)}</code>\n\n"
                f"🔐 <b>الكود:</b> <code>{safe_html(otp_code)}</code>\n\n"
                f"<b>لا تشارك هذا الكود مع أحد!</b>",
                reply_markup=markup,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"[!] فشل إرسال للمستخدم {user_id}: {e}")
    
    # إرسال للجروب
    log_otp(number, otp_code, sms, user_id)
    masked = mask_number(number)
    text = f"╭───────────────╮\n│ {country_flag} {service_code} {masked}\n╰───────────────╯"
    send_to_telegram_group(text, otp_code, service_code)

def scan_channel_post(message):
    """معالجة رسالة من قناة تليجرام لاستخراج OTP"""
    try:
        text = message.text
        if not text: return
        
        clean_text = re.sub(r'[\u200B-\u200F\u202A-\u202E‏‎]', '', text)
        
        hidden_numbers = re.findall(r'•+(\d{4})', clean_text)
        if not hidden_numbers:
            first_line = clean_text.split('\n')[0]
            hidden_numbers = re.findall(r'\b\d{4}\b', first_line)
        if not hidden_numbers: return
        
        last_four = hidden_numbers[0]
        otp_code = None
        
        # البحث عن OTP
        m = re.search(r'\b(\d{3}-\d{3})\b', clean_text)
        if m:
            otp_code = m.group(1).replace('-', '')
        if not otp_code:
            m = re.search(r'(?:رمز|كود|code|otp|verification)[:\s\-]*(\d{4,8})', clean_text, re.IGNORECASE)
            if m: otp_code = m.group(1)
        if not otp_code:
            ln = re.findall(r'\b\d{5,8}\b', clean_text)
            if ln: otp_code = ln[0]
        if not otp_code:
            af = re.findall(r'\b\d{4}\b', clean_text)
            for n in af:
                if n != last_four:
                    otp_code = n
                    break
        if not otp_code: return
        
        # محاولة إيجاد الرقم الكامل المرتبط
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id, assigned_number FROM users WHERE assigned_number LIKE ?", (f"%{last_four}",))
        row = c.fetchone()
        conn.close()
        
        if row:
            user_id, full_number = row
            service = detect_service(clean_text)
            send_otp_to_user_and_group(full_number, clean_text, otp_code, service)
            release_number(full_number)
            print(f"✅ OTP {otp_code} → User {user_id}")
    except Exception as e:
        print(f"[!] خطأ scan: {e}")

# ======================
# 🌐 HTTP Server (عشان Render ما يوقف البوت)
# ======================
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args): pass

def run_health_server():
    port = int(os.environ.get('PORT', 8080))
    try:
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        server.serve_forever()
    except Exception as e:
        print(f"[!] خطأ HTTP server: {e}")

# ======================
# 🚀 التشغيل
# ======================
def run_bot():
    print("[*] بدء البوت...")
    bot.polling(none_stop=True)

def main_loop():
    """يراقب الرسائل في القناة لإعادة توجيه الأكواد"""
    print("[*] بدء مراقبة القناة...")
    # إضافة القناة كمسؤول للوصول للرسائل
    offset = None
    last_update_id = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"timeout": 30, "allowed_updates": ["channel_post", "message"]}
            if last_update_id:
                params["offset"] = last_update_id + 1
            resp = requests.get(url, params=params, timeout=35)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        last_update_id = update["update_id"]
                        if "channel_post" in update:
                            # محاكاة كائن message
                            class FakeMsg:
                                def __init__(self, d):
                                    self.text = d.get("text", "")
                                    self.chat = type('obj', (object,), {'username': d.get("chat", {}).get("username", "")})()
                            scan_channel_post(FakeMsg(update["channel_post"]))
            time.sleep(2)
        except Exception as e:
            print(f"[!] خطأ main_loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # تأكد أن البوت موجود في القناة كمسؤول
    print("[*] تأكد أن البوت أدمن في القناة المستهدفة!")
    
    # تشغيل HTTP server
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # تشغيل البوت + المراقبة
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    
    # الحلقة الرئيسية
    try:
        main_loop()
    except KeyboardInterrupt:
        print("[*] توقف")
