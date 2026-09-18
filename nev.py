# ============================================================
# المطري خدمات - Bot Management System
# القسم 1: الاستيرادات + الإعدادات + Flask (UptimeRobot)
# ============================================================

import os
import sys
import json
import asyncio
import logging
import sqlite3
import io
import csv
import math
import zipfile
import qrcode
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    BotCommand, BufferedInputFile
)

from flask import Flask

# ============================================================
# الإعدادات (مدمجة مباشرة في الكود)
# ============================================================
BOT_TOKEN       = "8247238031:AAFLQAz7OMZVgXWVUD_u9D7VaB8ViL7YwIc"
ADMIN_IDS       = [7325566792]
DB_PATH         = "data/matri.db"
BOT_NAME        = "المطري خدمات"
LOG_LEVEL       = "INFO"
LOG_FILE        = "logs/bot.log"
REFERRAL_BONUS  = 50
NEW_USER_BONUS  = 10
BROADCAST_DELAY = 0.05
BROADCAST_BATCH = 30

# ============================================================
# التحقق من الإعدادات
# ============================================================
if not BOT_TOKEN or BOT_TOKEN == "ضع_التوكن_هنا":
    print("❌ BOT_TOKEN غير موجود")
    sys.exit(1)

if not ADMIN_IDS:
    print("❌ ADMIN_IDS غير موجود")
    sys.exit(1)

# ============================================================
# إعداد السجلات (Logging)
# ============================================================
Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("matri")

# ============================================================
# Flask app (لـ UptimeRobot على Render)
# ============================================================
flask_app = Flask(__name__)

# كتم سجلات Flask
logging.getLogger('werkzeug').setLevel(logging.ERROR)


@flask_app.route("/")
@flask_app.route("/health")
def _health():
    """مسار UptimeRobot — يُرجع 200 دائماً"""
    return "OK", 200


@flask_app.route("/status")
def _status():
    """معلومات إضافية"""
    return {"status": "running", "bot": BOT_NAME}, 200


def run_flask():
    """يشغّل Flask في Thread منفصل — يستخدم منفذ Render"""
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Flask (UptimeRobot) على المنفذ {port}")
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# ============================================================
# كائنات aiogram
# ============================================================
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# ============================================================
# أدوات مساعدة عامة
# ============================================================
def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def esc(text: str) -> str:
    """تهريب HTML"""
    if text is None:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))

def fmt(text: str, user: dict, extra: dict = None) -> str:
    """استبدال المتغيرات في الرسائل"""
    if text is None:
        return ""
    data = {
        "first_name": user.get("first_name") or "",
        "username":   user.get("username") or "",
        "user_id":    str(user.get("user_id") or ""),
        "points":     str(user.get("points") or 0),
        "balance":    str(user.get("points") or 0),
    }
    if extra:
        data.update({k: str(v) for k, v in extra.items()})
    for k, v in data.items():
        text = text.replace("{" + k + "}", v)
    return text

# ============================================================
# دالة مساعدة: تحويل style إلى قيمة Telegram
# ============================================================
def resolve_style(style_value: Optional[str]) -> Optional[str]:
    """
    تحويل قيمة style إلى القيمة الصحيحة لـ Telegram.
    القيم المسموحة: primary, success, danger
    """
    if not style_value:
        return None
    style_value = str(style_value).strip().lower()
    if style_value in ("danger", "red", "أحمر"):
        return "danger"
    if style_value in ("success", "green", "أخضر"):
        return "success"
    if style_value in ("primary", "blue", "أزرق"):
        return "primary"
    return "primary"
# ============================================================
# القسم 2: DATABASE
# قاعدة بيانات SQLite - 12 جدولًا (مع دعم style للأزرار)
# ============================================================

DB_CONN: Optional[sqlite3.Connection] = None


def db_init() -> None:
    """تهيئة الاتصال وإنشاء الجداول"""
    global DB_CONN
    DB_CONN = sqlite3.connect(DB_PATH, check_same_thread=False)
    DB_CONN.row_factory = sqlite3.Row
    DB_CONN.execute("PRAGMA journal_mode=WAL")
    DB_CONN.execute("PRAGMA foreign_keys=ON")
    _create_tables()
    _seed_defaults()
    log.info("قاعدة البيانات جاهزة: %s", DB_PATH)


def _create_tables() -> None:
    cur = DB_CONN.cursor()

    # 1. المستخدمون
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id       INTEGER PRIMARY KEY,
        first_name    TEXT,
        last_name     TEXT,
        username      TEXT,
        points        INTEGER DEFAULT 0,
        is_banned     INTEGER DEFAULT 0,
        referred_by   INTEGER,
        referral_code TEXT UNIQUE,
        joined_at     TEXT,
        last_seen     TEXT
    )
    """)

    # 2. الأدمن
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        user_id   INTEGER PRIMARY KEY,
        level     TEXT DEFAULT 'admin',
        added_by  INTEGER,
        added_at  TEXT
    )
    """)

    # 3. الخدمات
    cur.execute("""
    CREATE TABLE IF NOT EXISTS services (
        service_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        key          TEXT UNIQUE,
        name         TEXT NOT NULL,
        description  TEXT,
        icon         TEXT,
        category     TEXT DEFAULT 'عام',
        price        INTEGER DEFAULT 0,
        is_free      INTEGER DEFAULT 1,
        is_active    INTEGER DEFAULT 1,
        sort_order   INTEGER DEFAULT 100,
        created_at   TEXT
    )
    """)

    # 4. الأزرار (مع دعم style للألوان)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS buttons (
        button_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        screen       TEXT NOT NULL,
        label        TEXT NOT NULL,
        callback     TEXT,
        url          TEXT,
        web_app      TEXT,
        icon         TEXT,
        style        TEXT DEFAULT 'primary',
        row_index    INTEGER DEFAULT 0,
        col_index    INTEGER DEFAULT 0,
        style_id     INTEGER,
        is_active    INTEGER DEFAULT 1,
        created_at   TEXT
    )
    """)

    # 5. أنماط الأزرار (للألوان المخصصة في المعاينة/WebApp)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS button_styles (
        style_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT UNIQUE NOT NULL,
        primary_color   TEXT DEFAULT '#2AABEE',
        secondary_color TEXT DEFAULT '#229ED9',
        accent_color    TEXT DEFAULT '#FFFFFF',
        text_color      TEXT DEFAULT '#FFFFFF',
        icon            TEXT DEFAULT '',
        font_style      TEXT DEFAULT 'normal',
        layout          TEXT DEFAULT '2',
        is_default      INTEGER DEFAULT 0,
        enabled         INTEGER DEFAULT 1,
        created_at      TEXT
    )
    """)

    # 6. الثيمات
    cur.execute("""
    CREATE TABLE IF NOT EXISTS themes (
        theme_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT UNIQUE NOT NULL,
        primary    TEXT DEFAULT '#2AABEE',
        secondary  TEXT DEFAULT '#229ED9',
        accent     TEXT DEFAULT '#FFFFFF',
        background TEXT DEFAULT '#17212B',
        text       TEXT DEFAULT '#FFFFFF',
        success    TEXT DEFAULT '#4CAF50',
        warning    TEXT DEFAULT '#FFC107',
        error      TEXT DEFAULT '#F44336',
        is_active  INTEGER DEFAULT 0,
        is_custom  INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    # 7. التخطيطات
    cur.execute("""
    CREATE TABLE IF NOT EXISTS layouts (
        layout_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        screen     TEXT UNIQUE NOT NULL,
        columns    INTEGER DEFAULT 2,
        padding    INTEGER DEFAULT 1,
        note       TEXT,
        updated_at TEXT
    )
    """)

    # 8. الرسائل
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        message_key TEXT PRIMARY KEY,
        content     TEXT NOT NULL,
        updated_at  TEXT
    )
    """)

    # 9. الإعدادات
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key        TEXT PRIMARY KEY,
        value      TEXT,
        updated_at TEXT
    )
    """)

    # 10. السجلات
    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        log_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id   INTEGER,
        action    TEXT,
        details   TEXT,
        timestamp TEXT
    )
    """)

    # 11. العمليات المالية (النقاط)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        tx_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER,
        amount     INTEGER,
        reason     TEXT,
        actor_id   INTEGER,
        timestamp  TEXT
    )
    """)

    # 12. النسخ الاحتياطي
    cur.execute("""
    CREATE TABLE IF NOT EXISTS backups (
        backup_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        filename   TEXT,
        size_kb    INTEGER,
        created_by INTEGER,
        created_at TEXT
    )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_ref ON users(referred_by)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_user ON logs(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tx_user ON transactions(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_buttons_screen ON buttons(screen)")
    DB_CONN.commit()


def _seed_defaults() -> None:
    """زرع القيم الافتراضية لأول تشغيل"""
    cur = DB_CONN.cursor()

    # الأدمن من .env
    for admin_id in ADMIN_IDS:
        cur.execute(
            "INSERT OR IGNORE INTO admins(user_id, level, added_at) VALUES(?,?,?)",
            (admin_id, "super", now())
        )

    # ثيمات افتراضية
    default_themes = [
        ("Dark",   "#2AABEE", "#229ED9", "#FFFFFF", "#17212B", "#FFFFFF", "#4CAF50", "#FFC107", "#F44336", 1, 0),
        ("Light",  "#2AABEE", "#229ED9", "#000000", "#FFFFFF", "#000000", "#4CAF50", "#FFC107", "#F44336", 0, 0),
        ("Blue",   "#1E88E5", "#1565C0", "#FFFFFF", "#0D47A1", "#FFFFFF", "#4CAF50", "#FFC107", "#F44336", 0, 0),
        ("Green",  "#43A047", "#2E7D32", "#FFFFFF", "#1B5E20", "#FFFFFF", "#66BB6A", "#FFC107", "#F44336", 0, 0),
        ("Purple", "#8E24AA", "#6A1B9A", "#FFFFFF", "#4A148C", "#FFFFFF", "#66BB6A", "#FFC107", "#F44336", 0, 0),
    ]
    for t in default_themes:
        cur.execute("""
            INSERT OR IGNORE INTO themes
            (name, primary, secondary, accent, background, text, success, warning, error, is_active, created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (*t, now()))

    # نمط أزرار افتراضي
    cur.execute("""
        INSERT OR IGNORE INTO button_styles
        (name, icon, layout, is_default, enabled, created_at)
        VALUES('Default', '', '2', 1, 1, ?)
    """, (now(),))

    # رسائل افتراضية
    defaults_msgs = {
        "WELCOME": "مرحبًا بك {first_name} في المطري خدمات\n\nنقاطك الحالية: {points}",
        "HOME":    "القائمة الرئيسية\n\nمرحبًا {first_name}\nنقاطك: {points}",
        "PROFILE": "الملف الشخصي\n\nالاسم: {first_name}\nالمعرف: {user_id}\nالنقاط: {points}",
        "SERVICES":"مركز الخدمات\n\nاختر الخدمة التي تريدها:",
        "HELP":    "للمساعدة تواصل مع الإدارة.",
        "SUCCESS": "تمت العملية بنجاح.",
        "ERROR":   "حدث خطأ، حاول مرة أخرى.",
        "POINTS":  "نقاطك الحالية: {points}",
    }
    for k, v in defaults_msgs.items():
        cur.execute(
            "INSERT OR IGNORE INTO messages(message_key, content, updated_at) VALUES(?,?,?)",
            (k, v, now())
        )

    # إعدادات عامة
    defaults_settings = {
        "bot_name": BOT_NAME,
        "maintenance": "0",
        "referral_bonus": str(REFERRAL_BONUS),
        "new_user_bonus": str(NEW_USER_BONUS),
    }
    for k, v in defaults_settings.items():
        cur.execute(
            "INSERT OR IGNORE INTO settings(key, value, updated_at) VALUES(?,?,?)",
            (k, v, now())
        )

    # خدمات افتراضية
    default_services = [
        ("calculator",  "حاسبة",           "عمليات حسابية بسيطة",           "🧮", "أدوات", 0, 1, 1, 10),
        ("unit_convert","تحويل وحدات",      "تحويل بين وحدات القياس",         "📏", "أدوات", 0, 1, 1, 20),
        ("json_format", "تنسيق JSON",       "تنسيق والتحقق من JSON",          "🧾", "أدوات", 0, 1, 1, 30),
        ("txt_create",  "إنشاء TXT",        "إنشاء ملف نصي من نص ترسله",      "📄", "ملفات", 0, 1, 1, 40),
        ("csv_create",  "إنشاء CSV",        "تحويل جدول نصي إلى CSV",         "📊", "ملفات", 0, 1, 1, 50),
        ("wifi_card",   "كروت WiFi",        "إنشاء كرت WiFi للطباعة",         "📶", "شبكات", 5, 0, 1, 60),
        ("zip_create",  "ضغط ZIP",          "ضغط عدة نصوص في ملف ZIP",        "🗜", "ملفات", 5, 0, 1, 70),
        ("qr_create",   "إنشاء QR",         "إنشاء رمز QR من نص أو رابط",     "🔳", "أدوات", 0, 1, 1, 80),
    ]
    for s in default_services:
        cur.execute("""
            INSERT OR IGNORE INTO services
            (key, name, description, icon, category, price, is_free, is_active, sort_order, created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)
        """, (*s, now()))

    # تخطيطات افتراضية
    for screen in ["home", "services", "profile", "admin"]:
        cur.execute(
            "INSERT OR IGNORE INTO layouts(screen, columns, padding, updated_at) VALUES(?,?,?,?)",
            (screen, 2, 1, now())
        )

    DB_CONN.commit()


# ============================================================
# دوال CRUD - المستخدمون
# ============================================================
def db_get_user(user_id: int) -> Optional[dict]:
    cur = DB_CONN.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def db_upsert_user(user_id: int, first_name: str, last_name: str,
                   username: str, referred_by: Optional[int] = None) -> dict:
    user = db_get_user(user_id)
    if user:
        DB_CONN.execute(
            "UPDATE users SET first_name=?, last_name=?, username=?, last_seen=? WHERE user_id=?",
            (first_name, last_name, username, now(), user_id)
        )
        DB_CONN.commit()
        return db_get_user(user_id)

    code = f"REF{user_id}"
    DB_CONN.execute("""
        INSERT INTO users(user_id, first_name, last_name, username, points,
                          referred_by, referral_code, joined_at, last_seen)
        VALUES(?,?,?,?,?,?,?,?,?)
    """, (user_id, first_name, last_name, username, NEW_USER_BONUS,
          referred_by, code, now(), now()))
    DB_CONN.commit()

    # منح النقاط للمُحيل
    if referred_by and referred_by != user_id and db_get_user(referred_by):
        db_add_points(referred_by, REFERRAL_BONUS, "referral_bonus", actor_id=user_id)

    return db_get_user(user_id)


def db_set_ban(user_id: int, banned: bool) -> None:
    DB_CONN.execute("UPDATE users SET is_banned=? WHERE user_id=?",
                    (1 if banned else 0, user_id))
    DB_CONN.commit()


def db_get_user_by_referral_code(code: str) -> Optional[dict]:
    cur = DB_CONN.execute("SELECT * FROM users WHERE referral_code=?", (code,))
    row = cur.fetchone()
    return dict(row) if row else None


def db_count_users() -> int:
    return DB_CONN.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def db_list_users(offset: int = 0, limit: int = 10) -> List[dict]:
    cur = DB_CONN.execute(
        "SELECT * FROM users ORDER BY joined_at DESC LIMIT ? OFFSET ?",
        (limit, offset)
    )
    return [dict(r) for r in cur.fetchall()]


def db_search_users(query: str, limit: int = 10) -> List[dict]:
    q = f"%{query}%"
    cur = DB_CONN.execute("""
        SELECT * FROM users
        WHERE CAST(user_id AS TEXT) LIKE ?
           OR username LIKE ?
           OR first_name LIKE ?
        LIMIT ?
    """, (q, q, q, limit))
    return [dict(r) for r in cur.fetchall()]


# ============================================================
# دوال النقاط
# ============================================================
def db_add_points(user_id: int, amount: int, reason: str, actor_id: int = 0) -> int:
    DB_CONN.execute("UPDATE users SET points = points + ? WHERE user_id=?",
                    (amount, user_id))
    DB_CONN.execute("""
        INSERT INTO transactions(user_id, amount, reason, actor_id, timestamp)
        VALUES(?,?,?,?,?)
    """, (user_id, amount, reason, actor_id, now()))
    DB_CONN.commit()
    user = db_get_user(user_id)
    return user["points"] if user else 0


def db_get_transactions(user_id: int, limit: int = 20) -> List[dict]:
    cur = DB_CONN.execute("""
        SELECT * FROM transactions WHERE user_id=?
        ORDER BY tx_id DESC LIMIT ?
    """, (user_id, limit))
    return [dict(r) for r in cur.fetchall()]


# ============================================================
# دوال السجلات
# ============================================================
def db_log(user_id: int, action: str, details: str = "") -> None:
    DB_CONN.execute(
        "INSERT INTO logs(user_id, action, details, timestamp) VALUES(?,?,?,?)",
        (user_id, action, details, now())
    )
    DB_CONN.commit()
    log.info("[LOG] user=%s action=%s details=%s", user_id, action, details)


def db_get_logs(limit: int = 30) -> List[dict]:
    cur = DB_CONN.execute("SELECT * FROM logs ORDER BY log_id DESC LIMIT ?", (limit,))
    return [dict(r) for r in cur.fetchall()]


# ============================================================
# دوال الرسائل والإعدادات
# ============================================================
def db_get_message(key: str) -> str:
    cur = DB_CONN.execute("SELECT content FROM messages WHERE message_key=?", (key,))
    row = cur.fetchone()
    return row["content"] if row else ""


def db_set_message(key: str, content: str) -> None:
    DB_CONN.execute("""
        INSERT INTO messages(message_key, content, updated_at) VALUES(?,?,?)
        ON CONFLICT(message_key) DO UPDATE SET content=excluded.content, updated_at=excluded.updated_at
    """, (key, content, now()))
    DB_CONN.commit()


def db_all_messages() -> List[dict]:
    return [dict(r) for r in DB_CONN.execute("SELECT * FROM messages ORDER BY message_key").fetchall()]


def db_get_setting(key: str, default: str = "") -> str:
    cur = DB_CONN.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    return row["value"] if row else default


def db_set_setting(key: str, value: str) -> None:
    DB_CONN.execute("""
        INSERT INTO settings(key, value, updated_at) VALUES(?,?,?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
    """, (key, value, now()))
    DB_CONN.commit()


# ============================================================
# دوال الخدمات
# ============================================================
def db_list_services(active_only: bool = False, category: Optional[str] = None) -> List[dict]:
    sql = "SELECT * FROM services"
    conds = []
    params: list = []
    if active_only:
        conds.append("is_active=1")
    if category:
        conds.append("category=?")
        params.append(category)
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY sort_order ASC, service_id ASC"
    return [dict(r) for r in DB_CONN.execute(sql, params).fetchall()]


def db_get_service_by_key(key: str) -> Optional[dict]:
    cur = DB_CONN.execute("SELECT * FROM services WHERE key=?", (key,))
    row = cur.fetchone()
    return dict(row) if row else None


def db_get_service(service_id: int) -> Optional[dict]:
    cur = DB_CONN.execute("SELECT * FROM services WHERE service_id=?", (service_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def db_add_service(key: str, name: str, description: str, icon: str,
                   category: str, price: int, is_free: int, sort_order: int = 100) -> int:
    cur = DB_CONN.execute("""
        INSERT INTO services(key, name, description, icon, category,
                             price, is_free, is_active, sort_order, created_at)
        VALUES(?,?,?,?,?,?,?,1,?,?)
    """, (key, name, description, icon, category, price, is_free, sort_order, now()))
    DB_CONN.commit()
    return cur.lastrowid


def db_update_service(service_id: int, **fields) -> None:
    allowed = {"name", "description", "icon", "category", "price",
               "is_free", "is_active", "sort_order"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    sets = ", ".join(f"{k}=?" for k in updates)
    DB_CONN.execute(f"UPDATE services SET {sets} WHERE service_id=?",
                    (*updates.values(), service_id))
    DB_CONN.commit()


def db_delete_service(service_id: int) -> None:
    DB_CONN.execute("DELETE FROM services WHERE service_id=?", (service_id,))
    DB_CONN.commit()


def db_services_categories() -> List[str]:
    cur = DB_CONN.execute("SELECT DISTINCT category FROM services ORDER BY category")
    return [r[0] for r in cur.fetchall()]


# ============================================================
# دوال الأزرار والأنماط (مع دعم style)
# ============================================================
def db_list_buttons(screen: str, active_only: bool = True) -> List[dict]:
    sql = "SELECT * FROM buttons WHERE screen=?"
    if active_only:
        sql += " AND is_active=1"
    sql += " ORDER BY row_index, col_index, button_id"
    return [dict(r) for r in DB_CONN.execute(sql, (screen,)).fetchall()]


def db_get_button(button_id: int) -> Optional[dict]:
    cur = DB_CONN.execute("SELECT * FROM buttons WHERE button_id=?", (button_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def db_add_button(screen: str, label: str, callback: str = "",
                  url: str = "", web_app: str = "", icon: str = "",
                  style: str = "primary",
                  row_index: int = 0, col_index: int = 0,
                  style_id: Optional[int] = None) -> int:
    cur = DB_CONN.execute("""
        INSERT INTO buttons(screen, label, callback, url, web_app, icon,
                            style, row_index, col_index, style_id, is_active, created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,1,?)
    """, (screen, label, callback, url, web_app, icon,
          resolve_style(style), row_index, col_index, style_id, now()))
    DB_CONN.commit()
    return cur.lastrowid


def db_update_button(button_id: int, **fields) -> None:
    allowed = {"label", "callback", "url", "web_app", "icon", "style",
               "row_index", "col_index", "style_id", "is_active"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if "style" in updates:
        updates["style"] = resolve_style(updates["style"])
    if not updates:
        return
    sets = ", ".join(f"{k}=?" for k in updates)
    DB_CONN.execute(f"UPDATE buttons SET {sets} WHERE button_id=?",
                    (*updates.values(), button_id))
    DB_CONN.commit()


def db_delete_button(button_id: int) -> None:
    DB_CONN.execute("DELETE FROM buttons WHERE button_id=?", (button_id,))
    DB_CONN.commit()


def db_list_styles() -> List[dict]:
    return [dict(r) for r in DB_CONN.execute(
        "SELECT * FROM button_styles ORDER BY style_id").fetchall()]


def db_get_style(style_id: int) -> Optional[dict]:
    cur = DB_CONN.execute("SELECT * FROM button_styles WHERE style_id=?", (style_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def db_add_style(name: str, primary: str, secondary: str, accent: str,
                 text: str, icon: str, font: str, layout: str) -> int:
    cur = DB_CONN.execute("""
        INSERT INTO button_styles(name, primary_color, secondary_color,
            accent_color, text_color, icon, font_style, layout, created_at)
        VALUES(?,?,?,?,?,?,?,?,?)
    """, (name, primary, secondary, accent, text, icon, font, layout, now()))
    DB_CONN.commit()
    return cur.lastrowid


def db_update_style(style_id: int, **fields) -> None:
    allowed = {"name", "primary_color", "secondary_color", "accent_color",
               "text_color", "icon", "font_style", "layout", "enabled"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    sets = ", ".join(f"{k}=?" for k in updates)
    DB_CONN.execute(f"UPDATE button_styles SET {sets} WHERE style_id=?",
                    (*updates.values(), style_id))
    DB_CONN.commit()


def db_delete_style(style_id: int) -> None:
    DB_CONN.execute("DELETE FROM button_styles WHERE style_id=?", (style_id,))
    DB_CONN.commit()


def db_set_default_style(style_id: int) -> None:
    DB_CONN.execute("UPDATE button_styles SET is_default=0")
    DB_CONN.execute("UPDATE button_styles SET is_default=1 WHERE style_id=?", (style_id,))
    DB_CONN.commit()


def db_clone_style(style_id: int) -> Optional[int]:
    s = db_get_style(style_id)
    if not s:
        return None
    new_name = f"{s['name']}_copy"
    i = 1
    while DB_CONN.execute("SELECT 1 FROM button_styles WHERE name=?", (new_name,)).fetchone():
        new_name = f"{s['name']}_copy{i}"
        i += 1
    return db_add_style(new_name, s["primary_color"], s["secondary_color"],
                        s["accent_color"], s["text_color"], s["icon"],
                        s["font_style"], s["layout"])


def db_get_default_style() -> Optional[dict]:
    cur = DB_CONN.execute("SELECT * FROM button_styles WHERE is_default=1 LIMIT 1")
    row = cur.fetchone()
    return dict(row) if row else None


# ============================================================
# دوال الثيمات
# ============================================================
def db_list_themes() -> List[dict]:
    return [dict(r) for r in DB_CONN.execute(
        "SELECT * FROM themes ORDER BY theme_id").fetchall()]


def db_get_theme(theme_id: int) -> Optional[dict]:
    cur = DB_CONN.execute("SELECT * FROM themes WHERE theme_id=?", (theme_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def db_active_theme() -> dict:
    cur = DB_CONN.execute("SELECT * FROM themes WHERE is_active=1 LIMIT 1")
    row = cur.fetchone()
    if row:
        return dict(row)
    return db_get_theme(1) or {}


def db_set_active_theme(theme_id: int) -> None:
    DB_CONN.execute("UPDATE themes SET is_active=0")
    DB_CONN.execute("UPDATE themes SET is_active=1 WHERE theme_id=?", (theme_id,))
    DB_CONN.commit()


def db_update_theme(theme_id: int, **fields) -> None:
    allowed = {"name", "primary", "secondary", "accent", "background",
               "text", "success", "warning", "error"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    sets = ", ".join(f"{k}=?" for k in updates)
    DB_CONN.execute(f"UPDATE themes SET {sets} WHERE theme_id=?",
                    (*updates.values(), theme_id))
    DB_CONN.commit()


# ============================================================
# دوال التخطيطات
# ============================================================
def db_get_layout(screen: str) -> dict:
    cur = DB_CONN.execute("SELECT * FROM layouts WHERE screen=?", (screen,))
    row = cur.fetchone()
    if row:
        return dict(row)
    return {"screen": screen, "columns": 2, "padding": 1}


def db_set_layout(screen: str, columns: int, padding: int = 1, note: str = "") -> None:
    DB_CONN.execute("""
        INSERT INTO layouts(screen, columns, padding, note, updated_at)
        VALUES(?,?,?,?,?)
        ON CONFLICT(screen) DO UPDATE SET columns=excluded.columns,
            padding=excluded.padding, note=excluded.note,
            updated_at=excluded.updated_at
    """, (screen, columns, padding, note, now()))
    DB_CONN.commit()


def db_list_layouts() -> List[dict]:
    return [dict(r) for r in DB_CONN.execute("SELECT * FROM layouts ORDER BY screen").fetchall()]


# ============================================================
# دوال النسخ الاحتياطي
# ============================================================
def db_list_backups() -> List[dict]:
    return [dict(r) for r in DB_CONN.execute(
        "SELECT * FROM backups ORDER BY backup_id DESC").fetchall()]


def db_save_backup_record(filename: str, size_kb: int, created_by: int) -> int:
    cur = DB_CONN.execute("""
        INSERT INTO backups(filename, size_kb, created_by, created_at)
        VALUES(?,?,?,?)
    """, (filename, size_kb, created_by, now()))
    DB_CONN.commit()
    return cur.lastrowid


# ============================================================
# أدوات إضافية
# ============================================================
def db_get_stats() -> dict:
    total_users   = DB_CONN.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    banned_users  = DB_CONN.execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0]
    total_services= DB_CONN.execute("SELECT COUNT(*) FROM services").fetchone()[0]
    active_services = DB_CONN.execute("SELECT COUNT(*) FROM services WHERE is_active=1").fetchone()[0]
    total_points  = DB_CONN.execute("SELECT COALESCE(SUM(points),0) FROM users").fetchone()[0]
    total_tx      = DB_CONN.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    total_logs    = DB_CONN.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
    return {
        "total_users": total_users,
        "banned_users": banned_users,
        "total_services": total_services,
        "active_services": active_services,
        "total_points": total_points,
        "total_tx": total_tx,
        "total_logs": total_logs,
    }


def db_export_all() -> dict:
    """تصدير كل البيانات (للنسخ الاحتياطي)"""
    tables = ["users", "admins", "services", "buttons", "button_styles",
              "themes", "layouts", "messages", "settings", "logs",
              "transactions", "backups"]
    data = {}
    for t in tables:
        rows = DB_CONN.execute(f"SELECT * FROM {t}").fetchall()
        data[t] = [dict(r) for r in rows]
    return data


def db_import_all(data: dict) -> None:
    """استعادة نسخة احتياطية كاملة"""
    tables = ["users", "admins", "services", "buttons", "button_styles",
              "themes", "layouts", "messages", "settings", "logs",
              "transactions", "backups"]
    for t in tables:
        if t not in data:
            continue
        DB_CONN.execute(f"DELETE FROM {t}")
        rows = data[t]
        if not rows:
            continue
        cols = list(rows[0].keys())
        placeholders = ",".join(["?"] * len(cols))
        colnames = ",".join(cols)
        DB_CONN.executemany(
            f"INSERT INTO {t} ({colnames}) VALUES ({placeholders})",
            [tuple(r.get(c) for c in cols) for r in rows]
        )
    DB_CONN.commit()
    
# ============================================================
# القسم 3: THEMES + BUTTON FACTORY + LAYOUT + MESSAGES
# دعم كامل لـ style (primary / success / danger)
# ============================================================

# ------------------------------------------------------------
# 3.1 - THEME ENGINE
# ------------------------------------------------------------
class ThemeEngine:
    """إدارة الثيمات + توليد HTML/CSS حقيقي"""

    _cache: Optional[dict] = None

    @classmethod
    def reload(cls) -> None:
        cls._cache = None
        log.info("ThemeEngine: تم إعادة التحميل")

    @classmethod
    def current(cls) -> dict:
        if cls._cache is None:
            cls._cache = db_active_theme()
        return cls._cache

    @classmethod
    def get(cls, theme_id: int) -> Optional[dict]:
        return db_get_theme(theme_id)

    @classmethod
    def set_active(cls, theme_id: int) -> bool:
        t = db_get_theme(theme_id)
        if not t:
            return False
        db_set_active_theme(theme_id)
        cls.reload()
        return True

    @classmethod
    def update(cls, theme_id: int, **fields) -> bool:
        t = db_get_theme(theme_id)
        if not t:
            return False
        db_update_theme(theme_id, **fields)
        cls.reload()
        return True

    @classmethod
    def build_css(cls, theme: Optional[dict] = None) -> str:
        """CSS حقيقي يُستخدم في WebApp والمعاينة"""
        t = theme or cls.current()
        return f"""
        :root {{
            --primary:    {t.get('primary',    '#2AABEE')};
            --secondary:  {t.get('secondary',  '#229ED9')};
            --accent:     {t.get('accent',     '#FFFFFF')};
            --background: {t.get('background', '#17212B')};
            --text:       {t.get('text',       '#FFFFFF')};
            --success:    {t.get('success',    '#4CAF50')};
            --warning:    {t.get('warning',    '#FFC107')};
            --error:      {t.get('error',      '#F44336')};
        }}
        body {{
            background: var(--background);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Tahoma, sans-serif;
            direction: rtl;
            margin: 0;
            padding: 16px;
        }}
        .btn {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: var(--accent);
            border: none;
            border-radius: 10px;
            padding: 12px 18px;
            margin: 4px;
            font-size: 15px;
            cursor: pointer;
            min-width: 120px;
        }}
        .btn:active {{ opacity: 0.8; }}
        """


# ------------------------------------------------------------
# 3.2 - BUTTON FACTORY (مع دعم style الحقيقي)
# ------------------------------------------------------------
class ButtonFactory:
    """
    مصنع الأزرار.
    Telegram Bot API يدعم style بقيم: primary, success, danger.
    الألوان المخصصة (HEX) تُستخدم في المعاينة/WebApp فقط.
    """

    @staticmethod
    def list_styles() -> List[dict]:
        return db_list_styles()

    @staticmethod
    def get_style(style_id: int) -> Optional[dict]:
        return db_get_style(style_id)

    @staticmethod
    def default_style() -> Optional[dict]:
        return db_get_default_style()

    @staticmethod
    def create(name: str, primary: str = "#2AABEE", secondary: str = "#229ED9",
               accent: str = "#FFFFFF", text: str = "#FFFFFF",
               icon: str = "", font: str = "normal", layout: str = "2") -> int:
        return db_add_style(name, primary, secondary, accent, text, icon, font, layout)

    @staticmethod
    def update(style_id: int, **fields) -> bool:
        if not db_get_style(style_id):
            return False
        db_update_style(style_id, **fields)
        return True

    @staticmethod
    def delete(style_id: int) -> bool:
        if not db_get_style(style_id):
            return False
        db_delete_style(style_id)
        return True

    @staticmethod
    def clone(style_id: int) -> Optional[int]:
        return db_clone_style(style_id)

    @staticmethod
    def set_default(style_id: int) -> bool:
        if not db_get_style(style_id):
            return False
        db_set_default_style(style_id)
        return True

    @staticmethod
    def render_text(btn: dict, style: Optional[dict] = None) -> str:
        """النص النهائي للزر بعد إضافة الأيقونة"""
        style = style or {}
        icon = (btn.get("icon") or style.get("icon") or "").strip()
        label = (btn.get("label") or "").strip()
        return f"{icon} {label}".strip() if icon else label

    @staticmethod
    def to_telegram_button(btn: dict, style: Optional[dict] = None) -> InlineKeyboardButton:
        """
        تحويل سجل الأزرار إلى زر Telegram فعلي.
        يطبّق style (primary/success/danger) فعلياً.
        """
        text = ButtonFactory.render_text(btn, style)

        # قراءة style من السجل (محفوظ في قاعدة البيانات)
        tg_style = resolve_style(btn.get("style"))

        if btn.get("url"):
            return InlineKeyboardButton(text=text, url=btn["url"], style=tg_style)
        if btn.get("web_app"):
            return InlineKeyboardButton(text=text, web_app={"url": btn["web_app"]}, style=tg_style)
        cb = btn.get("callback") or "noop"
        return InlineKeyboardButton(text=text, callback_data=cb, style=tg_style)

    @staticmethod
    def preview_html(buttons: List[dict], style: Optional[dict] = None,
                     layout_cols: int = 2, theme: Optional[dict] = None) -> str:
        """معاينة HTML حقيقية بكل الألوان"""
        style = style or ButtonFactory.default_style() or {}
        css = ThemeEngine.build_css(theme)

        rows_html = ""
        row: List[str] = []
        for i, b in enumerate(buttons, 1):
            text = ButtonFactory.render_text(b, style)
            row.append(
                f'<button class="btn" style="background:linear-gradient(135deg,'
                f'{style.get("primary_color","#2AABEE")},{style.get("secondary_color","#229ED9")});'
                f'color:{style.get("accent_color","#FFFFFF")};">{esc(text)}</button>'
            )
            if i % layout_cols == 0:
                rows_html += f'<div style="display:flex;justify-content:center;">{"".join(row)}</div>'
                row = []
        if row:
            rows_html += f'<div style="display:flex;justify-content:center;">{"".join(row)}</div>'

        return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="utf-8"><title>معاينة</title>
<style>{css}</style></head>
<body>
    <h3 style="text-align:center;">معاينة التصميم</h3>
    <p style="text-align:center;opacity:0.7;">النمط: {esc(style.get('name','-'))} | الأعمدة: {layout_cols}</p>
    {rows_html}
</body></html>"""


# ------------------------------------------------------------
# 3.3 - LAYOUT ENGINE
# ------------------------------------------------------------
class LayoutEngine:
    """تحويل قائمة أزرار إلى صفوف حسب layout محفوظ"""

    _cache: Dict[str, dict] = {}

    @classmethod
    def reload(cls) -> None:
        cls._cache.clear()
        log.info("LayoutEngine: تم إعادة التحميل")

    @classmethod
    def get(cls, screen: str) -> dict:
        if screen not in cls._cache:
            cls._cache[screen] = db_get_layout(screen)
        return cls._cache[screen]

    @classmethod
    def set(cls, screen: str, columns: int, padding: int = 1, note: str = "") -> None:
        columns = max(1, min(3, int(columns)))
        db_set_layout(screen, columns, padding, note)
        cls._cache.pop(screen, None)

    @classmethod
    def build_keyboard(cls, buttons: List[dict], screen: str,
                       style: Optional[dict] = None) -> InlineKeyboardMarkup:
        """
        يبني InlineKeyboardMarkup فعلياً من سجلات الأزرار.
        يستخدم layout المحفوظ للشاشة.
        """
        layout = cls.get(screen)
        cols = max(1, min(3, int(layout.get("columns", 2))))

        rows: List[List[InlineKeyboardButton]] = []
        current: List[InlineKeyboardButton] = []

        # فرز حسب row_index ثم col_index
        buttons = sorted(buttons, key=lambda b: (b.get("row_index", 0), b.get("col_index", 0)))

        for b in buttons:
            if not b.get("is_active", 1):
                continue
            current.append(ButtonFactory.to_telegram_button(b, style))
            if len(current) >= cols:
                rows.append(current)
                current = []

        if current:
            rows.append(current)

        return InlineKeyboardMarkup(inline_keyboard=rows)


# ------------------------------------------------------------
# 3.4 - MESSAGE MANAGER
# ------------------------------------------------------------
class MessageManager:
    """مدير الرسائل مع متغيرات + كاش"""

    _cache: Dict[str, str] = {}
    ALLOWED_KEYS = ["WELCOME", "HOME", "PROFILE", "SERVICES", "HELP",
                    "SUCCESS", "ERROR", "POINTS"]

    @classmethod
    def reload(cls) -> None:
        cls._cache.clear()
        log.info("MessageManager: تم إعادة التحميل")

    @classmethod
    def get(cls, key: str) -> str:
        if key not in cls._cache:
            content = db_get_message(key)
            if not content:
                content = f"[{key}]"
            cls._cache[key] = content
        return cls._cache[key]

    @classmethod
    def set(cls, key: str, content: str) -> bool:
        if key not in cls.ALLOWED_KEYS:
            return False
        db_set_message(key, content)
        cls._cache.pop(key, None)
        return True

    @classmethod
    def all(cls) -> List[dict]:
        return db_all_messages()

    @classmethod
    def render(cls, key: str, user: dict, extra: Optional[dict] = None) -> str:
        return fmt(cls.get(key), user, extra)


# ------------------------------------------------------------
# 3.5 - GLOBAL RELOAD
# ------------------------------------------------------------
def reload_all() -> None:
    """إعادة تحميل كل الكاشات من قاعدة البيانات"""
    ThemeEngine.reload()
    LayoutEngine.reload()
    MessageManager.reload()
    log.info("تم إعادة تحميل جميع الإعدادات")


# ------------------------------------------------------------
# 3.6 - بناء لوحات جاهزة (مع style حقيقي)
# ------------------------------------------------------------
def build_main_menu(user: dict) -> InlineKeyboardMarkup:
    """
    القائمة الرئيسية.
    تُبنى فعلياً من جدول buttons إن وُجدت أزرار للشاشة 'home'،
    وإلا تستخدم القائمة الافتراضية مع style حقيقي.
    """
    rows = db_list_buttons("home", active_only=True)
    if rows:
        return LayoutEngine.build_keyboard(rows, "home")

    # القائمة الافتراضية مع style
    kb = [
        [
            InlineKeyboardButton(text="🧮 الخدمات", callback_data="menu:services", style="primary"),
            InlineKeyboardButton(text="👤 حسابي",   callback_data="menu:profile", style="primary"),
        ],
        [
            InlineKeyboardButton(text="⭐ النقاط",  callback_data="menu:points", style="success"),
            InlineKeyboardButton(text="🎁 الإحالة", callback_data="menu:referral", style="success"),
        ],
        [
            InlineKeyboardButton(text="ℹ️ المساعدة", callback_data="menu:help", style="primary"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)


def build_back_menu(back_to: str = "menu:home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 رجوع", callback_data=back_to, style="primary"),
            InlineKeyboardButton(text="🏠 الرئيسية", callback_data="menu:home", style="primary"),
        ]
    ])


def build_services_menu(page: int = 0, per_page: int = 6,
                        category: Optional[str] = None) -> InlineKeyboardMarkup:
    """قائمة الخدمات مع Pagination حقيقي"""
    services = db_list_services(active_only=True, category=category)
    total = len(services)
    pages = max(1, math.ceil(total / per_page))
    page = max(0, min(page, pages - 1))
    chunk = services[page * per_page:(page + 1) * per_page]

    rows: List[List[InlineKeyboardButton]] = []
    for s in chunk:
        icon = s.get("icon") or "•"
        label = f"{icon} {s['name']}"
        if not s.get("is_free"):
            label += f" ({s['price']} نقطة)"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"srv:open:{s['service_id']}", style="primary")])

    nav: List[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="‹ السابق", callback_data=f"srv:page:{page-1}", style="primary"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop", style="primary"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text="التالي ›", callback_data=f"srv:page:{page+1}", style="primary"))
    if nav:
        rows.append(nav)

    rows.append([
        InlineKeyboardButton(text="🔍 بحث", callback_data="srv:search", style="success"),
        InlineKeyboardButton(text="🏠 الرئيسية", callback_data="menu:home", style="primary"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
    
# ============================================================
# القسم 4: SERVICE ENGINE
# 8 خدمات حقيقية تعمل فعليًا
# ============================================================

# ------------------------------------------------------------
# 4.1 - الحالات (FSM) للخدمات
# ------------------------------------------------------------
class ServiceStates(StatesGroup):
    waiting_calculator = State()
    waiting_unit       = State()
    waiting_json       = State()
    waiting_txt        = State()
    waiting_csv        = State()
    waiting_zip        = State()
    waiting_wifi       = State()
    waiting_qr         = State()


# ------------------------------------------------------------
# 4.2 - محرك الخدمات (منطق حقيقي لكل خدمة)
# ------------------------------------------------------------
class ServiceEngine:
    """
    محرك الخدمات.
    كل service_key مرتبط بدالة Python حقيقية.
    """

    # ---------- حاسبة آمنة (AST - بدون eval) ----------
    @staticmethod
    def calculator(expr: str) -> str:
        """حاسبة آمنة بدون eval. تدعم + - * / // % ** وأقواس."""
        allowed_chars = set("0123456789+-*/%(). ")
        if not set(expr) <= allowed_chars:
            raise ValueError("تحتوي على رموز غير مسموحة")

        import ast
        import operator as op

        ops = {
            ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
            ast.Div: op.truediv, ast.FloorDiv: op.floordiv,
            ast.Mod: op.mod, ast.Pow: op.pow, ast.USub: op.neg,
        }

        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            if isinstance(node, ast.Num):
                return node.n
            if isinstance(node, ast.BinOp):
                return ops[type(node.op)](_eval(node.left), _eval(node.right))
            if isinstance(node, ast.UnaryOp):
                return ops[type(node.op)](_eval(node.operand))
            raise ValueError("تعبير غير مدعوم")

        tree = ast.parse(expr, mode="eval")
        result = _eval(tree)
        return f"{expr} = {result}"

    # ---------- تحويل وحدات ----------
    UNITS = {
        ("km", "m"): 1000.0,   ("m", "km"): 0.001,
        ("kg", "g"): 1000.0,   ("g", "kg"): 0.001,
        ("hour", "min"): 60.0, ("min", "hour"): 1 / 60,
        ("c", "f"): None,      ("f", "c"): None,
        ("mb", "kb"): 1024.0,  ("kb", "mb"): 1 / 1024,
    }

    @classmethod
    def unit_convert(cls, value: float, from_u: str, to_u: str) -> str:
        from_u = from_u.lower().strip()
        to_u = to_u.lower().strip()

        if from_u == to_u:
            return f"{value} {from_u} = {value} {to_u}"

        if from_u == "c" and to_u == "f":
            return f"{value}°C = {value * 9/5 + 32:.2f}°F"
        if from_u == "f" and to_u == "c":
            return f"{value}°F = {(value - 32) * 5/9:.2f}°C"

        key = (from_u, to_u)
        if key not in cls.UNITS or cls.UNITS[key] is None:
            raise ValueError(f"تحويل غير مدعوم: {from_u} → {to_u}")
        return f"{value} {from_u} = {value * cls.UNITS[key]:.4f} {to_u}"

    # ---------- JSON Formatter ----------
    @staticmethod
    def json_format(raw: str) -> str:
        data = json.loads(raw)
        return json.dumps(data, ensure_ascii=False, indent=2)

    # ---------- TXT ----------
    @staticmethod
    def txt_create(content: str) -> bytes:
        return content.encode("utf-8")

    # ---------- CSV ----------
    @staticmethod
    def csv_create(raw: str) -> bytes:
        """كل سطر = صف. القيم مفصولة بفاصلة أو Tab."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        for line in raw.strip().splitlines():
            if "\t" in line:
                row = line.split("\t")
            else:
                row = [c.strip() for c in line.split(",")]
            writer.writerow(row)
        return buf.getvalue().encode("utf-8-sig")

    # ---------- ZIP ----------
    @staticmethod
    def zip_create(files: List[tuple]) -> bytes:
        """files: [(name, content_bytes), ...]"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for name, content in files:
                z.writestr(name, content)
        return buf.getvalue()

    # ---------- WiFi Card ----------
    @staticmethod
    def wifi_card(ssid: str, password: str, encryption: str = "WPA") -> bytes:
        """يولّد صورة PNG لكرت WiFi جاهز للطباعة."""
        from PIL import Image, ImageDraw, ImageFont

        W, H = 900, 600
        img = Image.new("RGB", (W, H), "white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([(10, 10), (W - 10, H - 10)], outline="black", width=4)

        try:
            title_font = ImageFont.truetype("arial.ttf", 46)
            body_font  = ImageFont.truetype("arial.ttf", 34)
            small_font = ImageFont.truetype("arial.ttf", 24)
        except Exception:
            title_font = ImageFont.load_default()
            body_font  = ImageFont.load_default()
            small_font = ImageFont.load_default()

        draw.text((40, 40), "WiFi Network", fill="black", font=title_font)
        draw.line([(40, 110), (W - 40, 110)], fill="black", width=2)
        draw.text((40, 160), f"SSID: {ssid}", fill="black", font=body_font)
        draw.text((40, 220), f"Password: {password}", fill="black", font=body_font)
        draw.text((40, 280), f"Security: {encryption}", fill="black", font=body_font)

        wifi_str = f"WIFI:T:{encryption};S:{ssid};P:{password};;"
        qr = qrcode.make(wifi_str).resize((260, 260))
        img.paste(qr, (W - 320, 180))
        draw.text((40, H - 60), f"Generated by {BOT_NAME}", fill="gray", font=small_font)

        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()

    # ---------- QR ----------
    @staticmethod
    def qr_create(text: str) -> bytes:
        img = qrcode.make(text)
        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()

    # ---------- Dispatcher ----------
    @classmethod
    def run(cls, service_key: str, payload: dict) -> dict:
        if service_key == "calculator":
            return {"type": "text", "content": cls.calculator(payload["expr"])}

        if service_key == "unit_convert":
            return {"type": "text", "content": cls.unit_convert(
                float(payload["value"]), payload["from"], payload["to"])}

        if service_key == "json_format":
            return {"type": "text", "content": cls.json_format(payload["raw"])}

        if service_key == "txt_create":
            data = cls.txt_create(payload["raw"])
            return {"type": "file", "content": data, "filename": "matri.txt"}

        if service_key == "csv_create":
            data = cls.csv_create(payload["raw"])
            return {"type": "file", "content": data, "filename": "matri.csv"}

        if service_key == "zip_create":
            files = [(f"file_{i}.txt", c.encode("utf-8"))
                     for i, c in enumerate(payload["items"], 1)]
            data = cls.zip_create(files)
            return {"type": "file", "content": data, "filename": "matri.zip"}

        if service_key == "wifi_card":
            data = cls.wifi_card(payload["ssid"], payload["password"],
                                 payload.get("encryption", "WPA"))
            return {"type": "file", "content": data, "filename": "wifi_card.png"}

        if service_key == "qr_create":
            data = cls.qr_create(payload["text"])
            return {"type": "file", "content": data, "filename": "qr.png"}

        raise ValueError(f"خدمة غير معروفة: {service_key}")


# ------------------------------------------------------------
# 4.3 - نصوص الإرشاد لكل خدمة
# ------------------------------------------------------------
SERVICE_PROMPTS = {
    "calculator":   "أرسل التعبير الحسابي.\nمثال: <code>(5+3)*2</code>",
    "unit_convert": "أرسل بهذا الشكل:\n<code>القيمة من إلى</code>\nمثال: <code>5 km m</code>\n\nوحدات مدعومة: km, m, kg, g, hour, min, c, f, mb, kb",
    "json_format":  "أرسل نص JSON لتنسيقه.",
    "txt_create":   "أرسل النص لإنشاء ملف TXT.",
    "csv_create":   "أرسل الصفوف.\nكل سطر صف، والقيم مفصولة بفاصلة أو Tab.",
    "zip_create":   "أرسل النصوص، كل سطر سيصبح ملفًا داخل ZIP.",
    "wifi_card":    "أرسل بهذا الشكل:\n<code>SSID | PASSWORD | WPA</code>",
    "qr_create":    "أرسل النص أو الرابط لإنشاء QR.",
}


# ------------------------------------------------------------
# 4.4 - فتح خدمة
# ------------------------------------------------------------
def open_service(user: dict, service_id: int) -> tuple:
    service = db_get_service(service_id)
    if not service:
        return False, "الخدمة غير موجودة.", None, ""

    if not service.get("is_active"):
        return False, "هذه الخدمة معطّلة حاليًا.", None, ""

    if not service.get("is_free") and user["points"] < service.get("price", 0):
        return False, f"تحتاج {service['price']} نقطة لاستخدام هذه الخدمة.\nنقاطك: {user['points']}", None, ""

    key = service["key"]
    state_map = {
        "calculator":   ServiceStates.waiting_calculator,
        "unit_convert": ServiceStates.waiting_unit,
        "json_format":  ServiceStates.waiting_json,
        "txt_create":   ServiceStates.waiting_txt,
        "csv_create":   ServiceStates.waiting_csv,
        "zip_create":   ServiceStates.waiting_zip,
        "wifi_card":    ServiceStates.waiting_wifi,
        "qr_create":    ServiceStates.waiting_qr,
    }
    state = state_map.get(key)
    if state is None:
        return False, "هذه الخدمة غير مربوطة بمحرك تنفيذ.", None, ""

    prompt = SERVICE_PROMPTS.get(key, "أرسل المدخلات:")
    return True, prompt, state, key


# ------------------------------------------------------------
# 4.5 - خصم النقاط عند التنفيذ
# ------------------------------------------------------------
def charge_service(user: dict, service_key: str) -> bool:
    service = db_get_service_by_key(service_key)
    if not service:
        return False
    if service.get("is_free"):
        return True
    price = service.get("price", 0)
    if user["points"] < price:
        return False
    db_add_points(user["user_id"], -price, f"service_charge:{service_key}", actor_id=0)
    db_log(user["user_id"], "service_purchased", f"{service_key} | -{price}")
    return True
    
# ============================================================
# القسم 5: USER HANDLERS
# /start + القائمة الرئيسية + الملف الشخصي + النقاط + الإحالة + الخدمات
# ============================================================

# ------------------------------------------------------------
# 5.1 - /start مع دعم الإحالة
# ------------------------------------------------------------
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()

    user_id    = message.from_user.id
    first_name = message.from_user.first_name or ""
    last_name  = message.from_user.last_name or ""
    username   = message.from_user.username or ""

    # استخراج كود الإحالة
    args = message.text.split(maxsplit=1)
    referred_by = None
    if len(args) > 1:
        payload = args[1].strip()
        if payload.startswith("REF"):
            referrer = db_get_user_by_referral_code(payload)
            if referrer and referrer["user_id"] != user_id:
                referred_by = referrer["user_id"]

    # إن كان محظورًا
    existing = db_get_user(user_id)
    if existing and existing.get("is_banned"):
        await message.answer("🚫 حسابك محظور من استخدام البوت.")
        return

    user = db_upsert_user(user_id, first_name, last_name, username, referred_by)
    db_log(user_id, "start", f"ref={referred_by or '-'}")

    welcome = MessageManager.render("WELCOME", user)
    await message.answer(welcome, reply_markup=build_main_menu(user))


# ------------------------------------------------------------
# 5.2 - أمر /help
# ------------------------------------------------------------
@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    user = db_get_user(message.from_user.id)
    if not user:
        await message.answer("أرسل /start أولًا.")
        return
    text = MessageManager.render("HELP", user)
    await message.answer(text, reply_markup=build_back_menu())


# ------------------------------------------------------------
# 5.3 - القائمة الرئيسية
# ------------------------------------------------------------
@router.callback_query(F.data == "menu:home")
async def cb_home(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = db_get_user(call.from_user.id)
    if not user:
        await call.answer("أرسل /start أولًا.", show_alert=True)
        return

    text = MessageManager.render("HOME", user)
    try:
        await call.message.edit_text(text, reply_markup=build_main_menu(user))
    except Exception:
        await call.message.answer(text, reply_markup=build_main_menu(user))
    await call.answer()


# ------------------------------------------------------------
# 5.4 - الملف الشخصي
# ------------------------------------------------------------
@router.callback_query(F.data == "menu:profile")
async def cb_profile(call: CallbackQuery) -> None:
    user = db_get_user(call.from_user.id)
    if not user:
        await call.answer("أرسل /start أولًا.", show_alert=True)
        return

    text = MessageManager.render("PROFILE", user)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐ النقاط", callback_data="menu:points", style="success"),
            InlineKeyboardButton(text="🎁 الإحالة", callback_data="menu:referral", style="success"),
        ],
        [InlineKeyboardButton(text="📜 سجلي", callback_data="menu:tx", style="primary")],
        [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="menu:home", style="primary")],
    ])
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)
    await call.answer()


# ------------------------------------------------------------
# 5.5 - النقاط
# ------------------------------------------------------------
@router.callback_query(F.data == "menu:points")
async def cb_points(call: CallbackQuery) -> None:
    user = db_get_user(call.from_user.id)
    if not user:
        await call.answer("أرسل /start أولًا.", show_alert=True)
        return

    text = MessageManager.render("POINTS", user)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 سجل العمليات", callback_data="menu:tx", style="primary")],
        [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="menu:home", style="primary")],
    ])
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)
    await call.answer()


# ------------------------------------------------------------
# 5.6 - سجل العمليات
# ------------------------------------------------------------
@router.callback_query(F.data == "menu:tx")
async def cb_tx(call: CallbackQuery) -> None:
    user = db_get_user(call.from_user.id)
    if not user:
        await call.answer("أرسل /start أولًا.", show_alert=True)
        return

    txs = db_get_transactions(user["user_id"], limit=15)
    if not txs:
        body = "لا توجد عمليات بعد."
    else:
        lines = ["📜 آخر العمليات:\n"]
        for t in txs:
            sign = "+" if t["amount"] >= 0 else ""
            lines.append(
                f"• {sign}{t['amount']} | {esc(t['reason'])}\n"
                f"  <i>{esc(t['timestamp'])}</i>"
            )
        body = "\n".join(lines)

    try:
        await call.message.edit_text(body, reply_markup=build_back_menu("menu:profile"))
    except Exception:
        await call.message.answer(body, reply_markup=build_back_menu("menu:profile"))
    await call.answer()


# ------------------------------------------------------------
# 5.7 - الإحالة
# ------------------------------------------------------------
@router.callback_query(F.data == "menu:referral")
async def cb_referral(call: CallbackQuery) -> None:
    user = db_get_user(call.from_user.id)
    if not user:
        await call.answer("أرسل /start أولًا.", show_alert=True)
        return

    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={user['referral_code']}"

    invited = DB_CONN.execute(
        "SELECT COUNT(*) FROM users WHERE referred_by=?", (user["user_id"],)
    ).fetchone()[0]

    text = (
        f"🎁 <b>نظام الإحالة</b>\n\n"
        f"رابطك:\n<code>{esc(link)}</code>\n\n"
        f"عدد من دعوتهم: <b>{invited}</b>\n"
        f"مكافأة كل إحالة ناجحة: <b>{db_get_setting('referral_bonus', str(REFERRAL_BONUS))}</b> نقطة"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 مشاركة الرابط",
                              url=f"https://t.me/share/url?url={link}&text=انضم إلينا",
                              style="success")],
        [InlineKeyboardButton(text="🏠 الرئيسية", callback_data="menu:home", style="primary")],
    ])
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)
    await call.answer()


# ------------------------------------------------------------
# 5.8 - المساعدة
# ------------------------------------------------------------
@router.callback_query(F.data == "menu:help")
async def cb_help(call: CallbackQuery) -> None:
    user = db_get_user(call.from_user.id)
    text = MessageManager.render("HELP", user or {})
    try:
        await call.message.edit_text(text, reply_markup=build_back_menu())
    except Exception:
        await call.message.answer(text, reply_markup=build_back_menu())
    await call.answer()


# ------------------------------------------------------------
# 5.9 - قائمة الخدمات (Pagination)
# ------------------------------------------------------------
@router.callback_query(F.data == "menu:services")
async def cb_services(call: CallbackQuery) -> None:
    user = db_get_user(call.from_user.id)
    if not user:
        await call.answer("أرسل /start أولًا.", show_alert=True)
        return

    text = MessageManager.render("SERVICES", user)
    try:
        await call.message.edit_text(text, reply_markup=build_services_menu(0))
    except Exception:
        await call.message.answer(text, reply_markup=build_services_menu(0))
    await call.answer()


@router.callback_query(F.data.startswith("srv:page:"))
async def cb_services_page(call: CallbackQuery) -> None:
    page = int(call.data.split(":")[2])
    try:
        await call.message.edit_reply_markup(reply_markup=build_services_menu(page))
    except Exception:
        pass
    await call.answer()


# ------------------------------------------------------------
# 5.10 - فتح خدمة
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("srv:open:"))
async def cb_service_open(call: CallbackQuery, state: FSMContext) -> None:
    user = db_get_user(call.from_user.id)
    if not user:
        await call.answer("أرسل /start أولًا.", show_alert=True)
        return

    service_id = int(call.data.split(":")[2])
    ok, msg, next_state, service_key = open_service(user, service_id)
    if not ok:
        await call.answer(msg, show_alert=True)
        return

    await state.update_data(service_key=service_key, service_id=service_id)
    await state.set_state(next_state)

    service = db_get_service(service_id)
    title = f"{service.get('icon') or ''} <b>{esc(service['name'])}</b>\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data="srv:cancel", style="danger")]
    ])
    try:
        await call.message.edit_text(title + msg, reply_markup=kb)
    except Exception:
        await call.message.answer(title + msg, reply_markup=kb)
    await call.answer()


@router.callback_query(F.data == "srv:cancel")
async def cb_service_cancel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        await call.message.edit_text("تم الإلغاء.",
                                     reply_markup=build_back_menu("menu:services"))
    except Exception:
        await call.message.answer("تم الإلغاء.",
                                  reply_markup=build_back_menu("menu:services"))
    await call.answer()


# ------------------------------------------------------------
# 5.11 - زر البحث
# ------------------------------------------------------------
@router.callback_query(F.data == "srv:search")
async def cb_srv_search_placeholder(call: CallbackQuery) -> None:
    await call.answer("🔍 البحث قريبًا.", show_alert=True)
    
# ------------------------------------------------------------
# 5.12 - استقبال مدخلات الخدمات وتنفيذها فعليًا
# ------------------------------------------------------------
async def _execute_service(message: Message, state: FSMContext,
                           payload: dict) -> None:
    """ينفّذ الخدمة ويعرض النتيجة."""
    data = await state.get_data()
    key = data.get("service_key")
    if not key:
        await message.answer("انتهت الجلسة، أعد فتح الخدمة.",
                             reply_markup=build_back_menu("menu:services"))
        await state.clear()
        return

    user = db_get_user(message.from_user.id)
    if not user:
        await message.answer("أرسل /start أولًا.")
        await state.clear()
        return

    # خصم النقاط عند الحاجة
    if not charge_service(user, key):
        await message.answer("❌ لا تملك نقاطًا كافية.",
                             reply_markup=build_back_menu("menu:services"))
        await state.clear()
        return

    status = await message.answer("⏳ جاري التنفيذ...")

    try:
        result = ServiceEngine.run(key, payload)

        if result["type"] == "text":
            await status.edit_text(
                f"✅ <b>النتيجة:</b>\n<pre>{esc(result['content'])}</pre>",
                reply_markup=build_back_menu("menu:services")
            )
        else:
            await status.edit_text("✅ اكتمل التنفيذ.")
            doc = BufferedInputFile(result["content"], filename=result["filename"])
            await message.answer_document(doc,
                                          reply_markup=build_back_menu("menu:services"))

        db_log(user["user_id"], "service_executed", key)

    except json.JSONDecodeError as e:
        await status.edit_text(
            f"❌ خطأ في JSON:\n<code>{esc(str(e))}</code>",
            reply_markup=build_back_menu("menu:services")
        )
        db_log(user["user_id"], "service_error", f"{key} | JSONDecodeError")
    except Exception as e:
        log.exception("Service execution failed")
        await status.edit_text(
            f"❌ حدث خطأ:\n<code>{esc(str(e))}</code>",
            reply_markup=build_back_menu("menu:services")
        )
        db_log(user["user_id"], "service_error", f"{key} | {type(e).__name__}")

    await state.clear()


@router.message(ServiceStates.waiting_calculator)
async def srv_calculator(message: Message, state: FSMContext) -> None:
    await _execute_service(message, state, {"expr": (message.text or "").strip()})


@router.message(ServiceStates.waiting_unit)
async def srv_unit(message: Message, state: FSMContext) -> None:
    parts = (message.text or "").split()
    if len(parts) != 3:
        await message.answer("الصيغة: <code>القيمة من إلى</code>\nمثال: <code>5 km m</code>")
        return
    value, from_u, to_u = parts
    try:
        value = float(value)
    except ValueError:
        await message.answer("القيمة يجب أن تكون رقمًا.")
        return
    await _execute_service(message, state,
                           {"value": value, "from": from_u, "to": to_u})


@router.message(ServiceStates.waiting_json)
async def srv_json(message: Message, state: FSMContext) -> None:
    await _execute_service(message, state, {"raw": message.text or ""})


@router.message(ServiceStates.waiting_txt)
async def srv_txt(message: Message, state: FSMContext) -> None:
    await _execute_service(message, state, {"raw": message.text or ""})


@router.message(ServiceStates.waiting_csv)
async def srv_csv(message: Message, state: FSMContext) -> None:
    await _execute_service(message, state, {"raw": message.text or ""})


@router.message(ServiceStates.waiting_zip)
async def srv_zip(message: Message, state: FSMContext) -> None:
    items = [line for line in (message.text or "").splitlines() if line.strip()]
    if not items:
        await message.answer("أرسل نصًا واحدًا على الأقل.")
        return
    await _execute_service(message, state, {"items": items})


@router.message(ServiceStates.waiting_wifi)
async def srv_wifi(message: Message, state: FSMContext) -> None:
    parts = [p.strip() for p in (message.text or "").split("|")]
    if len(parts) < 2:
        await message.answer("الصيغة: <code>SSID | PASSWORD | WPA</code>")
        return
    ssid = parts[0]
    password = parts[1]
    encryption = parts[2] if len(parts) > 2 else "WPA"
    await _execute_service(message, state,
                           {"ssid": ssid, "password": password, "encryption": encryption})


@router.message(ServiceStates.waiting_qr)
async def srv_qr(message: Message, state: FSMContext) -> None:
    await _execute_service(message, state, {"text": message.text or ""})


# ------------------------------------------------------------
# 5.13 - زر noop
# ------------------------------------------------------------
@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery) -> None:
    await call.answer()
    
# ============================================================
# القسم 6: ADMIN HANDLERS - الجزء الأول
# لوحة التحكم + المستخدمون + النقاط + الحظر + السجلات + الإحصائيات
# ============================================================

# ------------------------------------------------------------
# 6.1 - حالات الأدمن (FSM)
# ------------------------------------------------------------
class AdminStates(StatesGroup):
    waiting_user_search       = State()
    waiting_points_user_id    = State()
    waiting_points_amount     = State()
    waiting_points_reason     = State()
    waiting_broadcast_text    = State()
    waiting_broadcast_confirm = State()
    waiting_message_key       = State()
    waiting_message_content   = State()
    waiting_style_name        = State()
    waiting_style_color       = State()
    waiting_theme_name        = State()
    waiting_theme_color       = State()
    waiting_service_name      = State()
    waiting_service_desc      = State()
    waiting_service_icon      = State()
    waiting_service_price     = State()
    waiting_button_label      = State()
    waiting_button_callback   = State()
    waiting_button_style      = State()
    waiting_layout_value      = State()
    waiting_setting_value     = State()


# ------------------------------------------------------------
# 6.2 - التحقق من الصلاحية (Decorator)
# ------------------------------------------------------------
def admin_only(func):
    """يضمن أن المستخدم أدمن فعليًا من .env أو جدول admins"""
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        is_db_admin = DB_CONN.execute(
            "SELECT 1 FROM admins WHERE user_id=?", (user_id,)
        ).fetchone() is not None
        if not (is_admin(user_id) or is_db_admin):
            if isinstance(event, CallbackQuery):
                await event.answer("⛔ هذه اللوحة للأدمن فقط.", show_alert=True)
            else:
                await event.answer("⛔ هذه اللوحة للأدمن فقط.")
            return
        return await func(event, *args, **kwargs)
    return wrapper


# ------------------------------------------------------------
# 6.3 - أمر /admin
# ------------------------------------------------------------
@router.message(Command("admin"))
@admin_only
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("🛠 <b>لوحة التحكم</b>\n\nاختر القسم:",
                         reply_markup=build_admin_panel())


@router.callback_query(F.data == "admin:home")
@admin_only
async def cb_admin_home(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        await call.message.edit_text("🛠 <b>لوحة التحكم</b>\n\nاختر القسم:",
                                     reply_markup=build_admin_panel())
    except Exception:
        await call.message.answer("🛠 <b>لوحة التحكم</b>\n\nاختر القسم:",
                                  reply_markup=build_admin_panel())
    await call.answer()


# ------------------------------------------------------------
# 6.4 - لوحة الأدمن الرئيسية
# ------------------------------------------------------------
def build_admin_panel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 المستخدمون", callback_data="admin:users:0", style="primary"),
            InlineKeyboardButton(text="🧮 الخدمات",   callback_data="admin:services:0", style="primary"),
        ],
        [
            InlineKeyboardButton(text="🎨 الثيمات",   callback_data="admin:themes", style="success"),
            InlineKeyboardButton(text="🔘 الأزرار",   callback_data="admin:buttons", style="success"),
        ],
        [
            InlineKeyboardButton(text="💬 الرسائل",   callback_data="admin:messages", style="primary"),
            InlineKeyboardButton(text="📐 Layouts",   callback_data="admin:layouts", style="primary"),
        ],
        [
            InlineKeyboardButton(text="⭐ النقاط",    callback_data="admin:points", style="success"),
            InlineKeyboardButton(text="📢 إشعار",     callback_data="admin:broadcast", style="success"),
        ],
        [
            InlineKeyboardButton(text="📊 إحصائيات",  callback_data="admin:stats", style="primary"),
            InlineKeyboardButton(text="📜 السجلات",   callback_data="admin:logs", style="primary"),
        ],
        [
            InlineKeyboardButton(text="💾 نسخ احتياطي", callback_data="admin:backup", style="primary"),
            InlineKeyboardButton(text="🔄 Reload",      callback_data="admin:reload", style="success"),
        ],
        [
            InlineKeyboardButton(text="🏠 الرئيسية", callback_data="menu:home", style="primary"),
        ],
    ])


# ------------------------------------------------------------
# 6.5 - الإحصائيات الحقيقية
# ------------------------------------------------------------
@router.callback_query(F.data == "admin:stats")
@admin_only
async def cb_admin_stats(call: CallbackQuery) -> None:
    s = db_get_stats()
    text = (
        f"📊 <b>إحصائيات حقيقية من قاعدة البيانات</b>\n\n"
        f"👥 إجمالي المستخدمين: <b>{s['total_users']}</b>\n"
        f"🚫 المحظورون: <b>{s['banned_users']}</b>\n"
        f"🧮 إجمالي الخدمات: <b>{s['total_services']}</b>\n"
        f"✅ الخدمات النشطة: <b>{s['active_services']}</b>\n"
        f"⭐ مجموع النقاط: <b>{s['total_points']}</b>\n"
        f"💳 عدد العمليات: <b>{s['total_tx']}</b>\n"
        f"📜 عدد السجلات: <b>{s['total_logs']}</b>"
    )
    try:
        await call.message.edit_text(text, reply_markup=build_back_admin())
    except Exception:
        await call.message.answer(text, reply_markup=build_back_admin())
    await call.answer()


def build_back_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:home", style="primary")]
    ])


# ------------------------------------------------------------
# 6.6 - قائمة المستخدمين + Pagination
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("admin:users:"))
@admin_only
async def cb_admin_users(call: CallbackQuery) -> None:
    page = int(call.data.split(":")[2])
    per_page = 8
    total = db_count_users()
    pages = max(1, math.ceil(total / per_page))
    page = max(0, min(page, pages - 1))

    users = db_list_users(offset=page * per_page, limit=per_page)

    lines = [f"👥 <b>المستخدمون ({total})</b> — صفحة {page+1}/{pages}\n"]
    if not users:
        lines.append("لا يوجد مستخدمون.")
    for u in users:
        ban = " 🚫" if u.get("is_banned") else ""
        lines.append(
            f"• <a href='tg://user?id={u['user_id']}'>{esc(u['first_name'] or 'مستخدم')}</a> | "
            f"<code>{u['user_id']}</code> | ⭐{u['points']}{ban}"
        )

    rows = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="‹ السابق", callback_data=f"admin:users:{page-1}", style="primary"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop", style="primary"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text="التالي ›", callback_data=f"admin:users:{page+1}", style="primary"))
    if nav:
        rows.append(nav)

    rows.append([
        InlineKeyboardButton(text="🔍 بحث", callback_data="admin:usersearch", style="success"),
        InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:home", style="primary"),
    ])

    try:
        await call.message.edit_text("\n".join(lines),
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    except Exception:
        await call.message.answer("\n".join(lines),
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()


# ------------------------------------------------------------
# 6.7 - البحث عن مستخدم
# ------------------------------------------------------------
@router.callback_query(F.data == "admin:usersearch")
@admin_only
async def cb_admin_usersearch(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.waiting_user_search)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data="admin:home", style="danger")]
    ])
    try:
        await call.message.edit_text("🔍 أرسل: ID أو username أو الاسم.",
                                     reply_markup=kb)
    except Exception:
        await call.message.answer("🔍 أرسل: ID أو username أو الاسم.",
                                  reply_markup=kb)
    await call.answer()


@router.message(AdminStates.waiting_user_search)
@admin_only
async def admin_user_search_result(message: Message, state: FSMContext) -> None:
    query = (message.text or "").strip()
    results = db_search_users(query, limit=8)
    await state.clear()

    if not results:
        await message.answer("❌ لا نتائج.",
                             reply_markup=build_back_admin())
        return

    lines = [f"🔍 نتائج البحث عن: <code>{esc(query)}</code>\n"]
    rows = []
    for u in results:
        ban = " 🚫" if u.get("is_banned") else ""
        lines.append(
            f"• {esc(u['first_name'] or '-')} | <code>{u['user_id']}</code> | ⭐{u['points']}{ban}"
        )
        rows.append([InlineKeyboardButton(
            text=f"⚙️ إدارة {u['user_id']}",
            callback_data=f"admin:user:{u['user_id']}",
            style="primary"
        )])
    rows.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:users:0", style="primary")])

    await message.answer("\n".join(lines),
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


# ------------------------------------------------------------
# 6.8 - بطاقة مستخدم
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("admin:user:"))
@admin_only
async def cb_admin_user(call: CallbackQuery) -> None:
    user_id = int(call.data.split(":")[2])
    u = db_get_user(user_id)
    if not u:
        await call.answer("المستخدم غير موجود.", show_alert=True)
        return

    invited = DB_CONN.execute(
        "SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,)
    ).fetchone()[0]

    text = (
        f"👤 <b>بطاقة المستخدم</b>\n\n"
        f"الاسم: {esc(u.get('first_name') or '-')} {esc(u.get('last_name') or '')}\n"
        f"المعرف: <code>{u['user_id']}</code>\n"
        f"username: @{esc(u.get('username') or '-')}\n"
        f"النقاط: <b>{u['points']}</b>\n"
        f"الحالة: {'🚫 محظور' if u.get('is_banned') else '✅ نشط'}\n"
        f"كود الإحالة: <code>{esc(u.get('referral_code') or '-')}</code>\n"
        f"دعا: <b>{invited}</b>\n"
        f"انضم: {esc(u.get('joined_at') or '-')}\n"
        f"آخر ظهور: {esc(u.get('last_seen') or '-')}"
    )

    ban_label = "✅ فك الحظر" if u.get("is_banned") else "🚫 حظر"
    ban_cb = f"admin:unban:{user_id}" if u.get("is_banned") else f"admin:ban:{user_id}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ إضافة نقاط", callback_data=f"admin:addp:{user_id}", style="success"),
            InlineKeyboardButton(text="➖ خصم نقاط",  callback_data=f"admin:subp:{user_id}", style="danger"),
        ],
        [
            InlineKeyboardButton(text="📜 عملياته",  callback_data=f"admin:usertx:{user_id}", style="primary"),
            InlineKeyboardButton(text=ban_label,     callback_data=ban_cb, style="danger"),
        ],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:users:0", style="primary")],
    ])
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)
    await call.answer()


# ------------------------------------------------------------
# 6.9 - عمليات المستخدم
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("admin:usertx:"))
@admin_only
async def cb_admin_usertx(call: CallbackQuery) -> None:
    user_id = int(call.data.split(":")[2])
    txs = db_get_transactions(user_id, limit=20)
    if not txs:
        body = "لا توجد عمليات."
    else:
        lines = [f"📜 <b>عمليات المستخدم {user_id}</b>\n"]
        for t in txs:
            sign = "+" if t["amount"] >= 0 else ""
            lines.append(f"• {sign}{t['amount']} | {esc(t['reason'])} | {esc(t['timestamp'])}")
        body = "\n".join(lines)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 رجوع", callback_data=f"admin:user:{user_id}", style="primary")]
    ])
    try:
        await call.message.edit_text(body, reply_markup=kb)
    except Exception:
        await call.message.answer(body, reply_markup=kb)
    await call.answer()


# ------------------------------------------------------------
# 6.10 - حظر / فك حظر
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("admin:ban:"))
@admin_only
async def cb_admin_ban(call: CallbackQuery) -> None:
    user_id = int(call.data.split(":")[2])
    db_set_ban(user_id, True)
    db_log(call.from_user.id, "admin_ban_user", str(user_id))
    await call.answer("✅ تم الحظر.", show_alert=True)
    await cb_admin_user(call)


@router.callback_query(F.data.startswith("admin:unban:"))
@admin_only
async def cb_admin_unban(call: CallbackQuery) -> None:
    user_id = int(call.data.split(":")[2])
    db_set_ban(user_id, False)
    db_log(call.from_user.id, "admin_unban_user", str(user_id))
    await call.answer("✅ تم فك الحظر.", show_alert=True)
    await cb_admin_user(call)


# ------------------------------------------------------------
# 6.11 - إضافة نقاط (3 خطوات حقيقية)
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("admin:addp:"))
@admin_only
async def cb_admin_addp(call: CallbackQuery, state: FSMContext) -> None:
    user_id = int(call.data.split(":")[2])
    await state.update_data(target_user=user_id, points_sign=1)
    await state.set_state(AdminStates.waiting_points_amount)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data=f"admin:user:{user_id}", style="danger")]
    ])
    try:
        await call.message.edit_text(f"➕ أرسل عدد النقاط لإضافتها للمستخدم <code>{user_id}</code>.",
                                     reply_markup=kb)
    except Exception:
        await call.message.answer(f"➕ أرسل عدد النقاط لإضافتها للمستخدم <code>{user_id}</code>.",
                                  reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("admin:subp:"))
@admin_only
async def cb_admin_subp(call: CallbackQuery, state: FSMContext) -> None:
    user_id = int(call.data.split(":")[2])
    await state.update_data(target_user=user_id, points_sign=-1)
    await state.set_state(AdminStates.waiting_points_amount)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data=f"admin:user:{user_id}", style="danger")]
    ])
    try:
        await call.message.edit_text(f"➖ أرسل عدد النقاط لخصمها من المستخدم <code>{user_id}</code>.",
                                     reply_markup=kb)
    except Exception:
        await call.message.answer(f"➖ أرسل عدد النقاط لخصمها من المستخدم <code>{user_id}</code>.",
                                  reply_markup=kb)
    await call.answer()


@router.message(AdminStates.waiting_points_amount)
@admin_only
async def admin_points_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = int((message.text or "").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ أرسل رقمًا موجبًا.")
        return

    data = await state.get_data()
    await state.update_data(points_amount=amount)
    await state.set_state(AdminStates.waiting_points_reason)
    await message.answer("📝 أرسل سبب العملية (أو أرسل - للتخطي).")


@router.message(AdminStates.waiting_points_reason)
@admin_only
async def admin_points_reason(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    target = data.get("target_user")
    amount = data.get("points_amount", 0) * data.get("points_sign", 1)
    reason = (message.text or "").strip()
    if reason == "-":
        reason = "admin_adjust"
    if not reason:
        reason = "admin_adjust"

    new_balance = db_add_points(target, amount, reason, actor_id=message.from_user.id)
    db_log(message.from_user.id, "admin_points_change",
           f"user={target} amount={amount} reason={reason}")

    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 عرض المستخدم", callback_data=f"admin:user:{target}", style="primary")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:users:0", style="primary")],
    ])
    sign = "+" if amount >= 0 else ""
    await message.answer(
        f"✅ تم التنفيذ\n\n"
        f"المستخدم: <code>{target}</code>\n"
        f"التغيير: <b>{sign}{amount}</b>\n"
        f"الرصيد الجديد: <b>{new_balance}</b>\n"
        f"السبب: {esc(reason)}",
        reply_markup=kb
    )


# ------------------------------------------------------------
# 6.12 - السجلات
# ------------------------------------------------------------
@router.callback_query(F.data == "admin:logs")
@admin_only
async def cb_admin_logs(call: CallbackQuery) -> None:
    logs = db_get_logs(limit=25)
    if not logs:
        body = "لا توجد سجلات."
    else:
        lines = ["📜 <b>آخر السجلات</b>\n"]
        for l in logs:
            lines.append(
                f"• <code>{l['user_id']}</code> | {esc(l['action'])} | "
                f"{esc(l['details'] or '-')} | <i>{esc(l['timestamp'])}</i>"
            )
        body = "\n".join(lines)

    try:
        await call.message.edit_text(body, reply_markup=build_back_admin())
    except Exception:
        await call.message.answer(body, reply_markup=build_back_admin())
    await call.answer()


# ------------------------------------------------------------
# 6.13 - Reload
# ------------------------------------------------------------
@router.callback_query(F.data == "admin:reload")
@admin_only
async def cb_admin_reload(call: CallbackQuery) -> None:
    reload_all()
    db_log(call.from_user.id, "admin_reload", "all caches")
    await call.answer("✅ تم إعادة تحميل الإعدادات.", show_alert=True)
    
# ============================================================
# القسم 7: ADMIN HANDLERS - الجزء الثاني
# الخدمات + الرسائل + الثيمات + مصنع الأزرار + Layouts + الإشعارات
# ============================================================

# ------------------------------------------------------------
# 7.1 - إدارة الخدمات
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("admin:services:"))
@admin_only
async def cb_admin_services(call: CallbackQuery) -> None:
    page = int(call.data.split(":")[2])
    services = db_list_services(active_only=False)
    per_page = 8
    total = len(services)
    pages = max(1, math.ceil(total / per_page))
    page = max(0, min(page, pages - 1))
    chunk = services[page * per_page:(page + 1) * per_page]

    lines = [f"🧮 <b>الخدمات ({total})</b> — صفحة {page+1}/{pages}\n"]
    rows = []
    for s in chunk:
        status = "✅" if s["is_active"] else "⛔"
        price = "مجاني" if s["is_free"] else f"{s['price']} نقطة"
        lines.append(f"{status} {esc(s['icon'] or '•')} <b>{esc(s['name'])}</b> | {price} | #{s['service_id']}")
        rows.append([InlineKeyboardButton(
            text=f"{status} {s['name']}",
            callback_data=f"admin:service:{s['service_id']}",
            style="success" if s["is_active"] else "danger"
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="‹ السابق", callback_data=f"admin:services:{page-1}", style="primary"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop", style="primary"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text="التالي ›", callback_data=f"admin:services:{page+1}", style="primary"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:home", style="primary")])

    text = "\n".join(lines)
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("admin:service:"))
@admin_only
async def cb_admin_service(call: CallbackQuery) -> None:
    service_id = int(call.data.split(":")[2])
    s = db_get_service(service_id)
    if not s:
        await call.answer("الخدمة غير موجودة.", show_alert=True)
        return

    status = "✅ مفعلة" if s["is_active"] else "⛔ معطلة"
    price_type = "مجانية" if s["is_free"] else f"مدفوعة ({s['price']} نقطة)"
    text = (
        f"🧮 <b>{esc(s['name'])}</b>\n\n"
        f"المفتاح: <code>{esc(s['key'])}</code>\n"
        f"الوصف: {esc(s['description'] or '-')}\n"
        f"الأيقونة: {esc(s['icon'] or '-')}\n"
        f"القسم: {esc(s['category'])}\n"
        f"الحالة: {status}\n"
        f"النوع: {price_type}\n"
        f"الترتيب: {s['sort_order']}\n"
        f"ID: <code>{s['service_id']}</code>"
    )

    toggle_label = "⛔ تعطيل" if s["is_active"] else "✅ تفعيل"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=toggle_label, callback_data=f"admin:srv_toggle:{service_id}", style="success" if not s["is_active"] else "danger"),
            InlineKeyboardButton(text="✏️ تعديل الاسم", callback_data=f"admin:srv_editname:{service_id}", style="primary"),
        ],
        [
            InlineKeyboardButton(text="📝 تعديل الوصف", callback_data=f"admin:srv_editdesc:{service_id}", style="primary"),
            InlineKeyboardButton(text="🎨 الأيقونة", callback_data=f"admin:srv_editicon:{service_id}", style="primary"),
        ],
        [
            InlineKeyboardButton(text="💰 السعر", callback_data=f"admin:srv_editprice:{service_id}", style="primary"),
            InlineKeyboardButton(text="⬆️ رفع", callback_data=f"admin:srv_up:{service_id}", style="primary"),
            InlineKeyboardButton(text="⬇️ خفض", callback_data=f"admin:srv_down:{service_id}", style="primary"),
        ],
        [
            InlineKeyboardButton(text="🗑 حذف", callback_data=f"admin:srv_del:{service_id}", style="danger"),
        ],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:services:0", style="primary")],
    ])
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("admin:srv_toggle:"))
@admin_only
async def cb_admin_srv_toggle(call: CallbackQuery) -> None:
    sid = int(call.data.split(":")[2])
    s = db_get_service(sid)
    if not s:
        await call.answer("غير موجودة.", show_alert=True)
        return
    new_state = 0 if s["is_active"] else 1
    db_update_service(sid, is_active=new_state)
    db_log(call.from_user.id, "admin_service_toggle", f"id={sid} -> {new_state}")
    await call.answer("✅ تم التبديل.", show_alert=True)
    await cb_admin_service(call)


@router.callback_query(F.data.startswith("admin:srv_editname:"))
@admin_only
async def cb_admin_srv_editname(call: CallbackQuery, state: FSMContext) -> None:
    sid = int(call.data.split(":")[2])
    await state.update_data(sid=sid, field="name")
    await state.set_state(AdminStates.waiting_service_name)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data=f"admin:service:{sid}", style="danger")]
    ])
    try:
        await call.message.edit_text("✏️ أرسل الاسم الجديد:", reply_markup=kb)
    except Exception:
        await call.message.answer("✏️ أرسل الاسم الجديد:", reply_markup=kb)
    await call.answer()


@router.message(AdminStates.waiting_service_name)
@admin_only
async def admin_service_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    sid = data.get("sid")
    new_val = (message.text or "").strip()[:64]
    if not new_val:
        await message.answer("❌ الاسم لا يمكن أن يكون فارغًا.")
        return
    db_update_service(sid, name=new_val)
    db_log(message.from_user.id, "admin_service_edit", f"id={sid} name={new_val}")
    await state.clear()
    s = db_get_service(sid)
    await message.answer(f"✅ تم تحديث الاسم إلى: <b>{esc(new_val)}</b>",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="🔙 الخدمة", callback_data=f"admin:service:{sid}", style="primary")]
                         ]))


@router.callback_query(F.data.startswith("admin:srv_editdesc:"))
@admin_only
async def cb_admin_srv_editdesc(call: CallbackQuery, state: FSMContext) -> None:
    sid = int(call.data.split(":")[2])
    await state.update_data(sid=sid)
    await state.set_state(AdminStates.waiting_service_desc)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data=f"admin:service:{sid}", style="danger")]
    ])
    try:
        await call.message.edit_text("📝 أرسل الوصف الجديد:", reply_markup=kb)
    except Exception:
        await call.message.answer("📝 أرسل الوصف الجديد:", reply_markup=kb)
    await call.answer()


@router.message(AdminStates.waiting_service_desc)
@admin_only
async def admin_service_desc(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    sid = data.get("sid")
    new_val = (message.text or "").strip()[:255]
    db_update_service(sid, description=new_val)
    db_log(message.from_user.id, "admin_service_edit", f"id={sid} desc")
    await state.clear()
    await message.answer("✅ تم تحديث الوصف.",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="🔙 الخدمة", callback_data=f"admin:service:{sid}", style="primary")]
                         ]))


@router.callback_query(F.data.startswith("admin:srv_editicon:"))
@admin_only
async def cb_admin_srv_editicon(call: CallbackQuery, state: FSMContext) -> None:
    sid = int(call.data.split(":")[2])
    await state.update_data(sid=sid)
    await state.set_state(AdminStates.waiting_service_icon)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data=f"admin:service:{sid}", style="danger")]
    ])
    try:
        await call.message.edit_text("🎨 أرسل الإيموجي الجديد:", reply_markup=kb)
    except Exception:
        await call.message.answer("🎨 أرسل الإيموجي الجديد:", reply_markup=kb)
    await call.answer()


@router.message(AdminStates.waiting_service_icon)
@admin_only
async def admin_service_icon(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    sid = data.get("sid")
    new_val = (message.text or "").strip()[:8]
    db_update_service(sid, icon=new_val)
    db_log(message.from_user.id, "admin_service_edit", f"id={sid} icon={new_val}")
    await state.clear()
    await message.answer(f"✅ تم تحديث الأيقونة إلى: {esc(new_val)}",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="🔙 الخدمة", callback_data=f"admin:service:{sid}", style="primary")]
                         ]))


@router.callback_query(F.data.startswith("admin:srv_editprice:"))
@admin_only
async def cb_admin_srv_editprice(call: CallbackQuery, state: FSMContext) -> None:
    sid = int(call.data.split(":")[2])
    await state.update_data(sid=sid)
    await state.set_state(AdminStates.waiting_service_price)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 جعلها مجانية", callback_data=f"admin:srv_free:{sid}", style="success")],
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data=f"admin:service:{sid}", style="danger")],
    ])
    try:
        await call.message.edit_text("💰 أرسل السعر بالنقاط (رقم):", reply_markup=kb)
    except Exception:
        await call.message.answer("💰 أرسل السعر بالنقاط (رقم):", reply_markup=kb)
    await call.answer()


@router.message(AdminStates.waiting_service_price)
@admin_only
async def admin_service_price(message: Message, state: FSMContext) -> None:
    try:
        price = int((message.text or "").strip())
        if price < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ أرسل رقمًا صحيحًا موجبًا.")
        return
    data = await state.get_data()
    sid = data.get("sid")
    is_free = 1 if price == 0 else 0
    db_update_service(sid, price=price, is_free=is_free)
    db_log(message.from_user.id, "admin_service_edit", f"id={sid} price={price}")
    await state.clear()
    await message.answer(f"✅ تم تحديث السعر إلى: <b>{price}</b>",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="🔙 الخدمة", callback_data=f"admin:service:{sid}", style="primary")]
                         ]))


@router.callback_query(F.data.startswith("admin:srv_free:"))
@admin_only
async def cb_admin_srv_free(call: CallbackQuery) -> None:
    sid = int(call.data.split(":")[2])
    db_update_service(sid, price=0, is_free=1)
    db_log(call.from_user.id, "admin_service_edit", f"id={sid} free")
    await call.answer("✅ أصبحت مجانية.", show_alert=True)
    await cb_admin_service(call)


@router.callback_query(F.data.startswith("admin:srv_up:"))
@admin_only
async def cb_admin_srv_up(call: CallbackQuery) -> None:
    sid = int(call.data.split(":")[2])
    s = db_get_service(sid)
    if not s:
        await call.answer("غير موجودة.", show_alert=True)
        return
    new_order = max(1, s["sort_order"] - 10)
    db_update_service(sid, sort_order=new_order)
    await call.answer("⬆️ تم الرفع.", show_alert=True)
    await cb_admin_service(call)


@router.callback_query(F.data.startswith("admin:srv_down:"))
@admin_only
async def cb_admin_srv_down(call: CallbackQuery) -> None:
    sid = int(call.data.split(":")[2])
    s = db_get_service(sid)
    if not s:
        await call.answer("غير موجودة.", show_alert=True)
        return
    new_order = s["sort_order"] + 10
    db_update_service(sid, sort_order=new_order)
    await call.answer("⬇️ تم الخفض.", show_alert=True)
    await cb_admin_service(call)


@router.callback_query(F.data.startswith("admin:srv_del:"))
@admin_only
async def cb_admin_srv_del(call: CallbackQuery) -> None:
    sid = int(call.data.split(":")[2])
    s = db_get_service(sid)
    if not s:
        await call.answer("غير موجودة.", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 تأكيد الحذف", callback_data=f"admin:srv_delconfirm:{sid}", style="danger")],
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data=f"admin:service:{sid}", style="primary")],
    ])
    try:
        await call.message.edit_text(f"⚠️ تأكيد حذف: <b>{esc(s['name'])}</b>", reply_markup=kb)
    except Exception:
        await call.message.answer(f"⚠️ تأكيد حذف: <b>{esc(s['name'])}</b>", reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("admin:srv_delconfirm:"))
@admin_only
async def cb_admin_srv_delconfirm(call: CallbackQuery) -> None:
    sid = int(call.data.split(":")[2])
    db_delete_service(sid)
    db_log(call.from_user.id, "admin_service_delete", f"id={sid}")
    await call.answer("🗑 تم الحذف.", show_alert=True)
    fake = call.model_copy(update={"data": "admin:services:0"})
    await cb_admin_services(fake)


# ------------------------------------------------------------
# 7.2 - إدارة الرسائل
# ------------------------------------------------------------
@router.callback_query(F.data == "admin:messages")
@admin_only
async def cb_admin_messages(call: CallbackQuery) -> None:
    msgs = MessageManager.all()
    rows = []
    for m in msgs:
        rows.append([InlineKeyboardButton(
            text=f"💬 {m['message_key']}",
            callback_data=f"admin:msg:{m['message_key']}",
            style="primary"
        )])
    rows.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:home", style="primary")])
    try:
        await call.message.edit_text("💬 <b>مدير الرسائل</b>\n\nاختر رسالة للتعديل:",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    except Exception:
        await call.message.answer("💬 <b>مدير الرسائل</b>\n\nاختر رسالة للتعديل:",
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()


@router.callback_query(F.data.startswith("admin:msg:"))
@admin_only
async def cb_admin_msg(call: CallbackQuery, state: FSMContext) -> None:
    key = call.data.split(":", 2)[2]
    content = db_get_message(key)
    await state.update_data(msg_key=key)
    await state.set_state(AdminStates.waiting_message_content)

    text = (
        f"💬 <b>الرسالة: {key}</b>\n\n"
        f"<b>الحالية:</b>\n<pre>{esc(content)}</pre>\n\n"
        f"<b>المتغيرات المدعومة:</b>\n"
        f"<code>{{first_name}}</code> <code>{{username}}</code> "
        f"<code>{{user_id}}</code> <code>{{points}}</code> <code>{{balance}}</code>\n\n"
        f"أرسل النص الجديد."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data="admin:messages", style="danger")]
    ])
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)
    await call.answer()


@router.message(AdminStates.waiting_message_content)
@admin_only
async def admin_msg_content(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    key = data.get("msg_key")
    new_content = message.text or ""
    if not new_content.strip():
        await message.answer("❌ النص لا يمكن أن يكون فارغًا.")
        return
    MessageManager.set(key, new_content)
    db_log(message.from_user.id, "admin_message_edit", key)
    await state.clear()
    await message.answer(f"✅ تم تحديث رسالة <b>{key}</b>.",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="🔙 الرسائل", callback_data="admin:messages", style="primary")]
                         ]))


# ------------------------------------------------------------
# 7.3 - إدارة الثيمات
# ------------------------------------------------------------
@router.callback_query(F.data == "admin:themes")
@admin_only
async def cb_admin_themes(call: CallbackQuery) -> None:
    themes = db_list_themes()
    lines = ["🎨 <b>الثيمات</b>\n"]
    rows = []
    for t in themes:
        marker = "🟢" if t["is_active"] else "⚪"
        lines.append(f"{marker} <b>{esc(t['name'])}</b> | {t['primary']}")
        rows.append([InlineKeyboardButton(
            text=f"{marker} {t['name']}",
            callback_data=f"admin:theme:{t['theme_id']}",
            style="success" if t["is_active"] else "primary"
        )])
    rows.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:home", style="primary")])

    try:
        await call.message.edit_text("\n".join(lines),
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    except Exception:
        await call.message.answer("\n".join(lines),
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()


@router.callback_query(F.data.startswith("admin:theme:"))
@admin_only
async def cb_admin_theme(call: CallbackQuery) -> None:
    tid = int(call.data.split(":")[2])
    t = ThemeEngine.get(tid)
    if not t:
        await call.answer("الثيم غير موجود.", show_alert=True)
        return

    text = (
        f"🎨 <b>الثيم: {esc(t['name'])}</b>\n\n"
        f"primary:    {t['primary']}\n"
        f"secondary:  {t['secondary']}\n"
        f"accent:     {t['accent']}\n"
        f"background: {t['background']}\n"
        f"text:       {t['text']}\n"
        f"success:    {t['success']}\n"
        f"warning:    {t['warning']}\n"
        f"error:      {t['error']}\n\n"
        f"الحالة: {'🟢 نشط' if t['is_active'] else '⚪ غير نشط'}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تفعيل", callback_data=f"admin:theme_act:{tid}", style="success")],
        [
            InlineKeyboardButton(text="primary",    callback_data=f"admin:theme_edit:{tid}:primary", style="primary"),
            InlineKeyboardButton(text="secondary",  callback_data=f"admin:theme_edit:{tid}:secondary", style="primary"),
        ],
        [
            InlineKeyboardButton(text="background", callback_data=f"admin:theme_edit:{tid}:background", style="primary"),
            InlineKeyboardButton(text="text",       callback_data=f"admin:theme_edit:{tid}:text", style="primary"),
        ],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:themes", style="primary")],
    ])
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("admin:theme_act:"))
@admin_only
async def cb_admin_theme_act(call: CallbackQuery) -> None:
    tid = int(call.data.split(":")[2])
    ThemeEngine.set_active(tid)
    db_log(call.from_user.id, "admin_theme_activate", str(tid))
    await call.answer("✅ تم تفعيل الثيم.", show_alert=True)
    await cb_admin_theme(call)


@router.callback_query(F.data.startswith("admin:theme_edit:"))
@admin_only
async def cb_admin_theme_edit(call: CallbackQuery, state: FSMContext) -> None:
    parts = call.data.split(":")
    tid = int(parts[2])
    field = parts[3]
    await state.update_data(tid=tid, field=field)
    await state.set_state(AdminStates.waiting_theme_color)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data=f"admin:theme:{tid}", style="danger")]
    ])
    try:
        await call.message.edit_text(
            f"🎨 أرسل قيمة HEX للـ <b>{field}</b>.\nمثال: <code>#2AABEE</code>",
            reply_markup=kb
        )
    except Exception:
        await call.message.answer(
            f"🎨 أرسل قيمة HEX للـ <b>{field}</b>.\nمثال: <code>#2AABEE</code>",
            reply_markup=kb
        )
    await call.answer()


@router.message(AdminStates.waiting_theme_color)
@admin_only
async def admin_theme_color(message: Message, state: FSMContext) -> None:
    val = (message.text or "").strip()
    if not val.startswith("#") or len(val) not in (4, 7):
        await message.answer("❌ صيغة HEX غير صحيحة. مثال: <code>#2AABEE</code>")
        return
    data = await state.get_data()
    tid = data.get("tid")
    field = data.get("field")
    ThemeEngine.update(tid, **{field: val})
    db_log(message.from_user.id, "admin_theme_edit", f"id={tid} {field}={val}")
    await state.clear()
    await message.answer(f"✅ تم تحديث <b>{field}</b> إلى <code>{val}</code>.",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="🔙 الثيم", callback_data=f"admin:theme:{tid}", style="primary")]
                         ]))


# ------------------------------------------------------------
# 7.4 - مصنع الأزرار (إدارة الأنماط)
# ------------------------------------------------------------
@router.callback_query(F.data == "admin:buttons")
@admin_only
async def cb_admin_buttons(call: CallbackQuery) -> None:
    styles = db_list_styles()
    lines = ["🔘 <b>مصنع الأزرار — الأنماط</b>\n"]
    rows = []
    for s in styles:
        marker = "⭐" if s["is_default"] else "•"
        lines.append(f"{marker} <b>{esc(s['name'])}</b> | {s['primary_color']} → {s['secondary_color']}")
        rows.append([InlineKeyboardButton(
            text=f"{marker} {s['name']}",
            callback_data=f"admin:style:{s['style_id']}",
            style="success" if s["is_default"] else "primary"
        )])
    rows.append([
        InlineKeyboardButton(text="➕ نمط جديد", callback_data="admin:style_new", style="success"),
        InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:home", style="primary"),
    ])
    try:
        await call.message.edit_text("\n".join(lines),
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    except Exception:
        await call.message.answer("\n".join(lines),
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()


@router.callback_query(F.data.startswith("admin:style:"))
@admin_only
async def cb_admin_style(call: CallbackQuery) -> None:
    sid = int(call.data.split(":")[2])
    s = ButtonFactory.get_style(sid)
    if not s:
        await call.answer("النمط غير موجود.", show_alert=True)
        return

    text = (
        f"🔘 <b>{esc(s['name'])}</b>\n\n"
        f"primary:   {s['primary_color']}\n"
        f"secondary: {s['secondary_color']}\n"
        f"accent:    {s['accent_color']}\n"
        f"text:      {s['text_color']}\n"
        f"icon: {esc(s['icon'] or '-')}\n"
        f"layout: {s['layout']}\n"
        f"افتراضي: {'⭐ نعم' if s['is_default'] else 'لا'}\n"
        f"الحالة: {'✅' if s['enabled'] else '⛔'}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ تعيين كافتراضي", callback_data=f"admin:style_def:{sid}", style="success")],
        [InlineKeyboardButton(text="📋 نسخ", callback_data=f"admin:style_clone:{sid}", style="primary"),
         InlineKeyboardButton(text="🗑 حذف", callback_data=f"admin:style_del:{sid}", style="danger")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:buttons", style="primary")],
    ])
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)
    await call.answer()


@router.callback_query(F.data == "admin:style_new")
@admin_only
async def cb_admin_style_new(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.waiting_style_name)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data="admin:buttons", style="danger")]
    ])
    try:
        await call.message.edit_text("➕ أرسل اسم النمط الجديد:", reply_markup=kb)
    except Exception:
        await call.message.answer("➕ أرسل اسم النمط الجديد:", reply_markup=kb)
    await call.answer()


@router.message(AdminStates.waiting_style_name)
@admin_only
async def admin_style_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()[:32]
    if not name:
        await message.answer("❌ اسم فارغ.")
        return
    try:
        new_id = ButtonFactory.create(name=name)
    except Exception as e:
        await message.answer(f"❌ فشل الإنشاء: {esc(str(e))}")
        return
    db_log(message.from_user.id, "admin_style_create", f"id={new_id} name={name}")
    await state.clear()
    await message.answer(f"✅ تم إنشاء النمط <b>{esc(name)}</b>.",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="🔘 النمط", callback_data=f"admin:style:{new_id}", style="primary")]
                         ]))


@router.callback_query(F.data.startswith("admin:style_def:"))
@admin_only
async def cb_admin_style_def(call: CallbackQuery) -> None:
    sid = int(call.data.split(":")[2])
    ButtonFactory.set_default(sid)
    db_log(call.from_user.id, "admin_style_default", str(sid))
    await call.answer("⭐ تم التعيين.", show_alert=True)
    await cb_admin_style(call)


@router.callback_query(F.data.startswith("admin:style_clone:"))
@admin_only
async def cb_admin_style_clone(call: CallbackQuery) -> None:
    sid = int(call.data.split(":")[2])
    new_id = ButtonFactory.clone(sid)
    if new_id:
        db_log(call.from_user.id, "admin_style_clone", f"{sid}->{new_id}")
        await call.answer("📋 تم النسخ.", show_alert=True)
    else:
        await call.answer("❌ فشل النسخ.", show_alert=True)
    await cb_admin_buttons(call)


@router.callback_query(F.data.startswith("admin:style_del:"))
@admin_only
async def cb_admin_style_del(call: CallbackQuery) -> None:
    sid = int(call.data.split(":")[2])
    ButtonFactory.delete(sid)
    db_log(call.from_user.id, "admin_style_delete", str(sid))
    await call.answer("🗑 تم الحذف.", show_alert=True)
    await cb_admin_buttons(call)


# ------------------------------------------------------------
# 7.5 - Layouts
# ------------------------------------------------------------
@router.callback_query(F.data == "admin:layouts")
@admin_only
async def cb_admin_layouts(call: CallbackQuery) -> None:
    layouts = db_list_layouts()
    lines = ["📐 <b>التخطيطات (Layouts)</b>\n"]
    rows = []
    for l in layouts:
        lines.append(f"• <b>{esc(l['screen'])}</b> | أعمدة: {l['columns']}")
        rows.append([InlineKeyboardButton(
            text=f"📐 {l['screen']} ({l['columns']})",
            callback_data=f"admin:layout:{l['screen']}",
            style="primary"
        )])
    rows.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:home", style="primary")])
    try:
        await call.message.edit_text("\n".join(lines),
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    except Exception:
        await call.message.answer("\n".join(lines),
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await call.answer()


@router.callback_query(F.data.startswith("admin:layout:"))
@admin_only
async def cb_admin_layout(call: CallbackQuery, state: FSMContext) -> None:
    screen = call.data.split(":", 2)[2]
    await state.update_data(layout_screen=screen)
    await state.set_state(AdminStates.waiting_layout_value)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data=f"admin:layout_set:{screen}:1", style="primary"),
            InlineKeyboardButton(text="2", callback_data=f"admin:layout_set:{screen}:2", style="primary"),
            InlineKeyboardButton(text="3", callback_data=f"admin:layout_set:{screen}:3", style="primary"),
        ],
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data="admin:layouts", style="danger")],
    ])
    try:
        await call.message.edit_text(
            f"📐 اختر عدد الأعمدة للشاشة <b>{esc(screen)}</b>:",
            reply_markup=kb
        )
    except Exception:
        await call.message.answer(
            f"📐 اختر عدد الأعمدة للشاشة <b>{esc(screen)}</b>:",
            reply_markup=kb
        )
    await call.answer()


@router.callback_query(F.data.startswith("admin:layout_set:"))
@admin_only
async def cb_admin_layout_set(call: CallbackQuery, state: FSMContext) -> None:
    parts = call.data.split(":")
    screen = parts[2]
    cols = int(parts[3])
    LayoutEngine.set(screen, cols)
    db_log(call.from_user.id, "admin_layout_set", f"{screen}={cols}")
    await state.clear()
    await call.answer(f"✅ تم التحديث إلى {cols} أعمدة.", show_alert=True)
    await cb_admin_layouts(call)


# ------------------------------------------------------------
# 7.6 - الإشعارات الجماعية
# ------------------------------------------------------------
@router.callback_query(F.data == "admin:broadcast")
@admin_only
async def cb_admin_broadcast(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminStates.waiting_broadcast_text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data="admin:home", style="danger")]
    ])
    try:
        await call.message.edit_text("📢 أرسل نص الإشعار لإرساله لكل المستخدمين.",
                                     reply_markup=kb)
    except Exception:
        await call.message.answer("📢 أرسل نص الإشعار لإرساله لكل المستخدمين.",
                                  reply_markup=kb)
    await call.answer()


@router.message(AdminStates.waiting_broadcast_text)
@admin_only
async def admin_broadcast_text(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    if not text.strip():
        await message.answer("❌ نص فارغ.")
        return
    await state.update_data(broadcast_text=text)
    await state.set_state(AdminStates.waiting_broadcast_confirm)

    total = db_count_users()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 إرسال الآن", callback_data="admin:broadcast_go", style="success")],
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data="admin:home", style="danger")],
    ])
    await message.answer(
        f"📢 <b>معاينة الإشعار</b>\n\n"
        f"<blockquote>{esc(text)}</blockquote>\n\n"
        f"عدد المستلمين المتوقع: <b>{total}</b>\n\n"
        f"هل تريد الإرسال؟",
        reply_markup=kb
    )


@router.callback_query(F.data == "admin:broadcast_go")
@admin_only
async def cb_admin_broadcast_go(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    await state.clear()

    if not text:
        await call.answer("لا يوجد نص.", show_alert=True)
        return

    await call.answer("بدأ الإرسال...")
    progress = await call.message.edit_text("📢 جاري الإرسال...")

    users = DB_CONN.execute("SELECT user_id FROM users WHERE is_banned=0").fetchall()
    total = len(users)
    ok, fail = 0, 0

    for i, row in enumerate(users, 1):
        uid = row["user_id"]
        try:
            await bot.send_message(uid, text)
            ok += 1
        except Exception:
            fail += 1

        if i % BROADCAST_BATCH == 0:
            try:
                await progress.edit_text(
                    f"📢 <b>التقدم</b>\n\n"
                    f"تم: {i}/{total}\n"
                    f"✅ نجح: {ok}\n"
                    f"❌ فشل: {fail}"
                )
            except Exception:
                pass

        await asyncio.sleep(BROADCAST_DELAY)

    db_log(call.from_user.id, "admin_broadcast", f"ok={ok} fail={fail}")
    try:
        await progress.edit_text(
            f"✅ <b>اكتمل الإرسال</b>\n\n"
            f"الإجمالي: {total}\n"
            f"نجح: {ok}\n"
            f"فشل: {fail}",
            reply_markup=build_back_admin()
        )
    except Exception:
        await call.message.answer(
            f"✅ اكتمل الإرسال\nنجح: {ok}\nفشل: {fail}",
            reply_markup=build_back_admin()
        )
        
# ============================================================
# القسم 8: BACKUP + RESTORE + ERROR HANDLER + MAIN
# ============================================================

# ------------------------------------------------------------
# 8.1 - حالات الاستعادة
# ------------------------------------------------------------
class BackupStates(StatesGroup):
    waiting_restore_file = State()


# ------------------------------------------------------------
# 8.2 - لوحة النسخ الاحتياطي
# ------------------------------------------------------------
@router.callback_query(F.data == "admin:backup")
@admin_only
async def cb_admin_backup(call: CallbackQuery) -> None:
    backups = db_list_backups()
    lines = ["💾 <b>النسخ الاحتياطي</b>\n"]
    if backups:
        for b in backups[:10]:
            lines.append(
                f"• <code>{esc(b['filename'])}</code> | {b['size_kb']} KB | {esc(b['created_at'])}"
            )
    else:
        lines.append("لا توجد نسخ محفوظة.")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💾 إنشاء نسخة", callback_data="admin:backup_create", style="success")],
        [InlineKeyboardButton(text="📥 استعادة نسخة", callback_data="admin:backup_restore", style="primary")],
        [InlineKeyboardButton(text="📂 إرسال آخر نسخة", callback_data="admin:backup_send", style="primary")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin:home", style="primary")],
    ])
    try:
        await call.message.edit_text("\n".join(lines), reply_markup=kb)
    except Exception:
        await call.message.answer("\n".join(lines), reply_markup=kb)
    await call.answer()


# ------------------------------------------------------------
# 8.3 - إنشاء نسخة حقيقية
# ------------------------------------------------------------
@router.callback_query(F.data == "admin:backup_create")
@admin_only
async def cb_admin_backup_create(call: CallbackQuery) -> None:
    await call.answer("⏳ جاري الإنشاء...")
    try:
        data = db_export_all()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{ts}.json"
        Path("data/backups").mkdir(parents=True, exist_ok=True)
        filepath = Path("data/backups") / filename
        content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        filepath.write_bytes(content)
        size_kb = max(1, len(content) // 1024)
        db_save_backup_record(filename, size_kb, call.from_user.id)
        db_log(call.from_user.id, "admin_backup_create", filename)

        doc = BufferedInputFile(content, filename=filename)
        await call.message.answer_document(
            doc,
            caption=f"✅ تم إنشاء النسخة\nالحجم: {size_kb} KB",
            reply_markup=build_back_admin()
        )
    except Exception as e:
        log.exception("Backup failed")
        await call.message.answer(f"❌ فشل: {esc(str(e))}",
                                  reply_markup=build_back_admin())


# ------------------------------------------------------------
# 8.4 - استعادة نسخة
# ------------------------------------------------------------
@router.callback_query(F.data == "admin:backup_restore")
@admin_only
async def cb_admin_backup_restore(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BackupStates.waiting_restore_file)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✖️ إلغاء", callback_data="admin:backup", style="danger")]
    ])
    try:
        await call.message.edit_text(
            "📥 أرسل ملف النسخة (JSON) للاستعادة.\n\n"
            "⚠️ سيتم حذف البيانات الحالية واستبدالها.",
            reply_markup=kb
        )
    except Exception:
        await call.message.answer(
            "📥 أرسل ملف النسخة (JSON) للاستعادة.",
            reply_markup=kb
        )
    await call.answer()


@router.message(BackupStates.waiting_restore_file, F.document)
@admin_only
async def admin_restore_file(message: Message, state: FSMContext) -> None:
    doc = message.document
    if not doc.file_name.endswith(".json"):
        await message.answer("❌ الملف يجب أن يكون JSON.")
        return

    try:
        file = await bot.get_file(doc.file_id)
        buf = io.BytesIO()
        await bot.download_file(file.file_path, buf)
        content = buf.getvalue().decode("utf-8")
        data = json.loads(content)

        # تحقق سريع
        if not isinstance(data, dict) or "users" not in data:
            await message.answer("❌ ملف غير صالح.")
            return

        db_import_all(data)
        reload_all()
        db_log(message.from_user.id, "admin_backup_restore", doc.file_name)
        await state.clear()
        await message.answer(
            "✅ تمت الاستعادة بنجاح.\nتم إعادة تحميل الإعدادات.",
            reply_markup=build_back_admin()
        )
    except json.JSONDecodeError:
        await message.answer("❌ الملف ليس JSON صالحًا.")
    except Exception as e:
        log.exception("Restore failed")
        await message.answer(f"❌ فشل: {esc(str(e))}")


# ------------------------------------------------------------
# 8.5 - إرسال آخر نسخة
# ------------------------------------------------------------
@router.callback_query(F.data == "admin:backup_send")
@admin_only
async def cb_admin_backup_send(call: CallbackQuery) -> None:
    backups = db_list_backups()
    if not backups:
        await call.answer("لا توجد نسخ.", show_alert=True)
        return

    last = backups[0]
    path = Path("data/backups") / last["filename"]
    if not path.exists():
        await call.answer("الملف غير موجود على القرص.", show_alert=True)
        return

    content = path.read_bytes()
    doc = BufferedInputFile(content, filename=last["filename"])
    await call.message.answer_document(
        doc,
        caption=f"📂 {last['filename']} | {last['size_kb']} KB",
        reply_markup=build_back_admin()
    )
    await call.answer()


# ------------------------------------------------------------
# 8.6 - Global Error Handler
# ------------------------------------------------------------
@dp.error()
async def global_error_handler(event, **kwargs) -> bool:
    """
    يعالج أي خطأ في البوت ويسجله، ولا يوقف البوت.
    """
    try:
        from aiogram.types import ErrorEvent
        if isinstance(event, ErrorEvent):
            update = event.update
            exception = event.exception
        else:
            return False

        log.exception("Unhandled error: %s", exception)

        try:
            user_id = None
            if update.message:
                user_id = update.message.from_user.id
            elif update.callback_query:
                user_id = update.callback_query.from_user.id

            if user_id:
                db_log(user_id, "unhandled_error", f"{type(exception).__name__}: {exception}")

            # إبلاغ المستخدم
            if update.callback_query:
                try:
                    await update.callback_query.answer("⚠️ حدث خطأ.", show_alert=False)
                except Exception:
                    pass
            elif update.message:
                try:
                    await update.message.answer(
                        "⚠️ حدث خطأ غير متوقع. تم تسجيله.\n"
                        "يمكنك المحاولة مرة أخرى."
                    )
                except Exception:
                    pass
        except Exception:
            pass

        return True
    except Exception:
        log.exception("Error handler itself failed")
        return False


# ------------------------------------------------------------
# 8.7 - أمر /myid (مفيد للمطور)
# ------------------------------------------------------------
@router.message(Command("myid"))
async def cmd_myid(message: Message) -> None:
    await message.answer(f"🆔 <code>{message.from_user.id}</code>")


# ------------------------------------------------------------
# 8.8 - أمر /reload (للأدمن فقط)
# ------------------------------------------------------------
@router.message(Command("reload"))
@admin_only
async def cmd_reload(message: Message) -> None:
    reload_all()
    db_log(message.from_user.id, "admin_reload", "command")
    await message.answer("✅ تم إعادة تحميل الإعدادات.")


# ------------------------------------------------------------
# 8.9 - قائمة الأوامر (تظهر في Telegram UI)
# ------------------------------------------------------------
async def set_bot_commands() -> None:
    commands = [
        BotCommand(command="start",  description="بدء البوت"),
        BotCommand(command="help",   description="المساعدة"),
        BotCommand(command="myid",   description="عرض معرفك"),
    ]
    await bot.set_my_commands(commands)


# ------------------------------------------------------------
# 8.10 - main()
# ------------------------------------------------------------
async def main() -> None:
    # تهيئة قاعدة البيانات
    db_init()

    # تحميل الكاشات
    reload_all()

    # ضبط الأوامر
    await set_bot_commands()

    # معلومات إقلاع
    me = await bot.get_me()
    log.info("Bot started: @%s", me.username)
    log.info("Admins: %s", ADMIN_IDS)

    # إشعار الأدمن
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"✅ <b>{BOT_NAME}</b> يعمل الآن.\n"
                f"البوت: @{me.username}\n"
                f"الخدمات النشطة: {len(db_list_services(active_only=True))}"
            )
        except Exception:
            pass

    # بدء polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


# ------------------------------------------------------------
# 8.11 - نقطة الدخول
# ------------------------------------------------------------
if __name__ == "__main__":
    try:
        # 1) شغّل Flask في Thread منفصل
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()

        # 2) شغّل البوت في الـ main thread
        asyncio.run(main())

    except (KeyboardInterrupt, SystemExit):
        log.info("Bot stopped by user")
    except Exception as e:
        log.exception("Fatal error: %s", e)