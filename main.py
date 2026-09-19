"""
╔══════════════════════════════════════════════════════════════╗
║           المطري خدمات - Almutairi Services Bot              ║
║           Parts 1-4 (مُصحّحة)                                 ║
╚══════════════════════════════════════════════════════════════╝
"""

# ═══════════════════════════════════════════════════════════════
# SECTION 1: CONFIG
# ═══════════════════════════════════════════════════════════════
import os
import sys
import math
import re
import csv
import io
import json
import random
import string
import sqlite3
import asyncio
import logging
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional


# ---------- الإعدادات ----------
BOT_TOKEN   = os.environ.get("BOT_TOKEN", "8247238031:AAGqWzTkJyDLCXh89yqE4c3Ch3VEsj13Uq4").strip()
ADMIN_IDS   = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", "7325566792").split(",") if x.strip().isdigit()]
DB_PATH     = os.environ.get("DB_PATH", "data/database.db")
REFERRAL_REWARD = int(os.environ.get("REFERRAL_REWARD", "50"))
DEFAULT_POINTS  = int(os.environ.get("DEFAULT_POINTS", "100"))
# ------------------------------

if not BOT_TOKEN or ":" not in BOT_TOKEN:
    print("❌ ضع BOT_TOKEN صحيحاً في أعلى الملف")
    sys.exit(1)
if not ADMIN_IDS:
    print("❌ ضع على الأقل رقم أدمن واحد في ADMIN_IDS")
    sys.exit(1)

Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("almutairi")


# ═══════════════════════════════════════════════════════════════
# SECTION 2: DATABASE
# ═══════════════════════════════════════════════════════════════
class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        if self.conn is not None:
            return
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self._create_schema()

    def _create_schema(self):
        cur = self.conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id      INTEGER PRIMARY KEY,
            username     TEXT,
            first_name   TEXT,
            last_name    TEXT,
            language     TEXT DEFAULT 'ar',
            points       INTEGER DEFAULT 0,
            is_banned    INTEGER DEFAULT 0,
            referrer_id  INTEGER,
            created_at   TEXT,
            last_seen    TEXT
        );
        CREATE TABLE IF NOT EXISTS admins (
            user_id   INTEGER PRIMARY KEY,
            role      TEXT DEFAULT 'admin',
            added_by  INTEGER,
            added_at  TEXT
        );
        CREATE TABLE IF NOT EXISTS services (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            key          TEXT UNIQUE NOT NULL,
            name         TEXT NOT NULL,
            description  TEXT,
            icon         TEXT DEFAULT '',
            category     TEXT DEFAULT 'general',
            sort_order   INTEGER DEFAULT 100,
            is_enabled   INTEGER DEFAULT 1,
            is_free      INTEGER DEFAULT 1,
            price        INTEGER DEFAULT 0,
            created_at   TEXT
        );
        CREATE TABLE IF NOT EXISTS buttons (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            screen      TEXT NOT NULL,
            label       TEXT NOT NULL,
            callback    TEXT,
            url         TEXT,
            webapp      TEXT,
            style       TEXT DEFAULT 'primary',
            sort_order  INTEGER DEFAULT 100,
            style_id    INTEGER,
            enabled     INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS button_styles (
            style_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT UNIQUE NOT NULL,
            primary    TEXT DEFAULT 'primary',
            success    TEXT DEFAULT 'success',
            danger     TEXT DEFAULT 'danger',
            icon       TEXT DEFAULT '',
            font_style TEXT DEFAULT 'sans',
            layout     TEXT DEFAULT '2',
            is_default INTEGER DEFAULT 0,
            enabled    INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS themes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT UNIQUE NOT NULL,
            primary     TEXT DEFAULT '#3498db',
            secondary   TEXT DEFAULT '#2c3e50',
            accent      TEXT DEFAULT '#e74c3c',
            background  TEXT DEFAULT '#ffffff',
            text        TEXT DEFAULT '#000000',
            success     TEXT DEFAULT '#27ae60',
            warning     TEXT DEFAULT '#f39c12',
            error       TEXT DEFAULT '#e74c3c',
            is_active   INTEGER DEFAULT 0,
            is_builtin  INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS layouts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            screen      TEXT UNIQUE NOT NULL,
            columns     INTEGER DEFAULT 2,
            spacing     INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS messages (
            key        TEXT PRIMARY KEY,
            text       TEXT NOT NULL,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS settings (
            key        TEXT PRIMARY KEY,
            value      TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER,
            action    TEXT,
            details   TEXT,
            timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            amount     INTEGER,
            reason     TEXT,
            admin_id   INTEGER,
            kind       TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS backups (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            filename   TEXT,
            size       INTEGER,
            created_at TEXT,
            created_by INTEGER
        );
        """)
        self.conn.commit()

    def execute(self, sql: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        return cur

    def fetchone(self, sql: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchone()

    def fetchall(self, sql: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    @staticmethod
    def now() -> str:
        return datetime.utcnow().isoformat(timespec="seconds")

    def close(self):
        if self.conn:
            self.conn.close()


db = Database(DB_PATH)


# ═══════════════════════════════════════════════════════════════
# SECTION 3: SEED DATA
# ═══════════════════════════════════════════════════════════════
def seed_defaults():
    now = Database.now()

    for aid in ADMIN_IDS:
        db.execute(
            "INSERT OR IGNORE INTO admins(user_id, role, added_by, added_at) VALUES(?,?,?,?)",
            (aid, "super", aid, now)
        )

    builtin = [
        ("Dark",   "#1abc9c", "#2c3e50", "#e74c3c", "#1a1a1a", "#ffffff", "#27ae60", "#f39c12", "#e74c3c", 1),
        ("Light",  "#3498db", "#ecf0f1", "#e67e22", "#ffffff", "#2c3e50", "#27ae60", "#f39c12", "#e74c3c", 0),
        ("Blue",   "#2980b9", "#34495e", "#9b59b6", "#ecf0f1", "#2c3e50", "#27ae60", "#f39c12", "#e74c3c", 0),
        ("Green",  "#27ae60", "#16a085", "#f39c12", "#f0fff4", "#1e5631", "#27ae60", "#f39c12", "#c0392b", 0),
        ("Purple", "#8e44ad", "#2c3e50", "#e84393", "#f8f4ff", "#2c3e50", "#27ae60", "#f39c12", "#c0392b", 0),
    ]
    for t in builtin:
        db.execute(
            """INSERT OR IGNORE INTO themes
               (name,primary,secondary,accent,background,text,success,warning,error,is_active,is_builtin)
               VALUES(?,?,?,?,?,?,?,?,?,?,1)""",
            t
        )

    for screen, cols in [("home", 2), ("services", 2), ("admin_home", 2), ("profile", 2)]:
        db.execute(
            "INSERT OR IGNORE INTO layouts(screen, columns, spacing) VALUES(?,?,1)",
            (screen, cols)
        )

    default_msgs = {
        "WELCOME":  "مرحباً {first_name} في المطري خدمات.\nنقاطك: {points}",
        "HOME":     "القائمة الرئيسية",
        "PROFILE":  "الملف الشخصي\n\nالاسم: {first_name}\nالمعرف: @{username}\nالرقم: {user_id}\nالنقاط: {points}",
        "SERVICES": "مركز الخدمات",
        "HELP":     "للمساعدة تواصل مع الدعم.",
        "SUCCESS":  "تم بنجاح.",
        "ERROR":    "حدث خطأ، حاول لاحقاً.",
        "POINTS":   "رصيدك الحالي: {points} نقطة",
    }
    for k, v in default_msgs.items():
        db.execute("INSERT OR IGNORE INTO messages(key, text, updated_at) VALUES(?,?,?)",
                   (k, v, now))

    for k, v in {
        "bot_name": "المطري خدمات",
        "referral_reward": str(REFERRAL_REWARD),
        "default_points": str(DEFAULT_POINTS),
    }.items():
        db.execute("INSERT OR IGNORE INTO settings(key, value, updated_at) VALUES(?,?,?)",
                   (k, v, now))

    db.execute("""INSERT OR IGNORE INTO button_styles
        (name, primary, success, danger, icon, font_style, layout, is_default, enabled)
        VALUES('Default', 'primary', 'success', 'danger', '', 'sans', '2', 1, 1)""")

    services = [
        ("calculator", "حاسبة",         "عمليات حسابية بسيطة",  "🧮", "tools", 10, 1, 1, 0),
        ("unit_conv",  "تحويل وحدات",    "تحويل بين الوحدات",     "📏", "tools", 20, 1, 1, 0),
        ("json_fmt",   "تنسيق JSON",     "تنسيق وتنظيم JSON",     "🧩", "tools", 30, 1, 1, 0),
        ("txt_make",   "إنشاء TXT",      "إنشاء ملف نصي",         "📝", "files", 40, 1, 1, 0),
        ("txt_read",   "قراءة TXT",      "قراءة ملف نصي",         "📖", "files", 50, 1, 1, 0),
        ("csv_gen",    "CSV Generator",  "توليد ملف CSV",         "📊", "files", 60, 1, 1, 0),
        ("zip_make",   "ضغط ملفات",      "ضغط ملفات ZIP",         "🗜️", "files", 70, 1, 1, 0),
        ("wifi_card",  "كروت WiFi",      "إنشاء كروت طباعة",      "📶", "tools", 80, 1, 1, 0),
    ]
    for s in services:
        db.execute("""INSERT OR IGNORE INTO services
            (key,name,description,icon,category,sort_order,is_enabled,is_free,price,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)""", (*s, now))

    db.conn.commit()
    log.info("✅ Seed data ready.")


# ═══════════════════════════════════════════════════════════════
# SECTION 4: REPOSITORIES
# ═══════════════════════════════════════════════════════════════
class SettingsRepo:
    @staticmethod
    def get(key: str, default: str = "") -> str:
        row = db.fetchone("SELECT value FROM settings WHERE key=?", (key,))
        return row["value"] if row else default

    @staticmethod
    def set(key: str, value: str):
        db.execute(
            """INSERT INTO settings(key, value, updated_at) VALUES(?,?,?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
            (key, value, Database.now())
        )

    @staticmethod
    def all():
        return db.fetchall("SELECT * FROM settings ORDER BY key")


class UserRepo:
    @staticmethod
    def get_or_create(tg_user) -> sqlite3.Row:
        row = db.fetchone("SELECT * FROM users WHERE user_id=?", (tg_user.id,))
        now = Database.now()
        if row is None:
            default_pts = int(SettingsRepo.get("default_points", str(DEFAULT_POINTS)))
            db.execute(
                """INSERT INTO users(user_id, username, first_name, last_name, points, created_at, last_seen)
                   VALUES(?,?,?,?,?,?,?)""",
                (tg_user.id, tg_user.username, tg_user.first_name, tg_user.last_name,
                 default_pts, now, now)
            )
        else:
            db.execute(
                "UPDATE users SET username=?, first_name=?, last_name=?, last_seen=? WHERE user_id=?",
                (tg_user.username, tg_user.first_name, tg_user.last_name, now, tg_user.id)
            )
        return db.fetchone("SELECT * FROM users WHERE user_id=?", (tg_user.id,))

    @staticmethod
    def get(user_id: int):
        return db.fetchone("SELECT * FROM users WHERE user_id=?", (user_id,))

    @staticmethod
    def search(q: str, limit: int = 20):
        like = f"%{q}%"
        return db.fetchall(
            """SELECT * FROM users
               WHERE CAST(user_id AS TEXT) LIKE ?
                  OR username LIKE ?
                  OR first_name LIKE ?
               ORDER BY last_seen DESC LIMIT ?""",
            (like, like, like, limit)
        )

    @staticmethod
    def count() -> int:
        return db.fetchone("SELECT COUNT(*) AS c FROM users")["c"]

    @staticmethod
    def all(limit: int = 50, offset: int = 0):
        return db.fetchall("SELECT * FROM users ORDER BY user_id LIMIT ? OFFSET ?",
                           (limit, offset))

    @staticmethod
    def set_ban(user_id: int, banned: bool):
        db.execute("UPDATE users SET is_banned=? WHERE user_id=?",
                   (1 if banned else 0, user_id))

    @staticmethod
    def set_referrer(user_id: int, referrer_id: int):
        db.execute("UPDATE users SET referrer_id=? WHERE user_id=?",
                   (referrer_id, user_id))

    @staticmethod
    def add_points(user_id: int, delta: int, reason: str,
                   admin_id: Optional[int], kind: str = "manual") -> int:
        row = UserRepo.get(user_id)
        if not row:
            return 0
        new_balance = max(0, row["points"] + delta)
        db.execute("UPDATE users SET points=? WHERE user_id=?", (new_balance, user_id))
        db.execute(
            """INSERT INTO transactions(user_id, amount, reason, admin_id, kind, created_at)
               VALUES(?,?,?,?,?,?)""",
            (user_id, delta, reason, admin_id, kind, Database.now())
        )
        return new_balance

    @staticmethod
    def transactions(user_id: int, limit: int = 15):
        return db.fetchall(
            "SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )


class ServiceRepo:
    @staticmethod
    def all_enabled():
        return db.fetchall("SELECT * FROM services WHERE is_enabled=1 ORDER BY sort_order, id")

    @staticmethod
    def all():
        return db.fetchall("SELECT * FROM services ORDER BY sort_order, id")

    @staticmethod
    def get_by_key(key: str):
        return db.fetchone("SELECT * FROM services WHERE key=?", (key,))

    @staticmethod
    def get(sid: int):
        return db.fetchone("SELECT * FROM services WHERE id=?", (sid,))

    @staticmethod
    def toggle(sid: int):
        s = ServiceRepo.get(sid)
        if s:
            db.execute("UPDATE services SET is_enabled=? WHERE id=?",
                       (0 if s["is_enabled"] else 1, sid))

    @staticmethod
    def update_field(sid: int, field: str, value):
        allowed = {"name", "description", "icon", "category",
                   "sort_order", "is_free", "price", "is_enabled"}
        if field not in allowed:
            raise ValueError(f"Field {field} غير مسموح")
        db.execute(f"UPDATE services SET {field}=? WHERE id=?", (value, sid))

    @staticmethod
    def delete(sid: int):
        db.execute("DELETE FROM services WHERE id=?", (sid,))

    @staticmethod
    def add(key: str, name: str, description: str, icon: str,
            category: str, sort_order: int, is_free: int, price: int):
        db.execute(
            """INSERT INTO services(key,name,description,icon,category,
                                    sort_order,is_enabled,is_free,price,created_at)
               VALUES(?,?,?,?,?,?,1,?,?,?)""",
            (key, name, description, icon, category, sort_order, is_free, price, Database.now())
        )

    @staticmethod
    def categories():
        rows = db.fetchall("SELECT DISTINCT category FROM services ORDER BY category")
        return [r["category"] for r in rows if r["category"]]


class MessageRepo:
    @staticmethod
    def get(key: str) -> str:
        row = db.fetchone("SELECT text FROM messages WHERE key=?", (key,))
        return row["text"] if row else ""

    @staticmethod
    def set(key: str, text: str):
        db.execute(
            """INSERT INTO messages(key, text, updated_at) VALUES(?,?,?)
               ON CONFLICT(key) DO UPDATE SET text=excluded.text, updated_at=excluded.updated_at""",
            (key, text, Database.now())
        )

    @staticmethod
    def all():
        return db.fetchall("SELECT * FROM messages ORDER BY key")


class ThemeRepo:
    @staticmethod
    def all():
        return db.fetchall("SELECT * FROM themes ORDER BY id")

    @staticmethod
    def get(tid: int):
        return db.fetchone("SELECT * FROM themes WHERE id=?", (tid,))

    @staticmethod
    def active():
        return (db.fetchone("SELECT * FROM themes WHERE is_active=1")
                or db.fetchone("SELECT * FROM themes WHERE name='Dark'"))

    @staticmethod
    def activate(tid: int):
        db.execute("UPDATE themes SET is_active=0")
        db.execute("UPDATE themes SET is_active=1 WHERE id=?", (tid,))

    @staticmethod
    def update_field(tid: int, field: str, value: str):
        allowed = {"primary", "secondary", "accent", "background",
                   "text", "success", "warning", "error"}
        if field not in allowed:
            raise ValueError(f"Field {field} غير مسموح")
        db.execute(f"UPDATE themes SET {field}=? WHERE id=?", (value, tid))

    @staticmethod
    def create_custom(name: str):
        db.execute(
            """INSERT INTO themes(name,primary,secondary,accent,background,text,
                                  success,warning,error,is_active,is_builtin)
               VALUES(?,?,?,?,?,?,?,?,?,0,0)""",
            (name, "#3498db", "#2c3e50", "#e74c3c", "#ffffff",
             "#000000", "#27ae60", "#f39c12", "#e74c3c")
        )

    @staticmethod
    def delete(tid: int):
        row = ThemeRepo.get(tid)
        if row and row["is_builtin"]:
            return False
        db.execute("DELETE FROM themes WHERE id=?", (tid,))
        return True


class StyleRepo:
    @staticmethod
    def all():
        return db.fetchall("SELECT * FROM button_styles ORDER BY style_id")

    @staticmethod
    def get(sid: int):
        return db.fetchone("SELECT * FROM button_styles WHERE style_id=?", (sid,))

    @staticmethod
    def default():
        return (db.fetchone("SELECT * FROM button_styles WHERE is_default=1")
                or db.fetchone("SELECT * FROM button_styles LIMIT 1"))

    @staticmethod
    def set_default(sid: int):
        db.execute("UPDATE button_styles SET is_default=0")
        db.execute("UPDATE button_styles SET is_default=1 WHERE style_id=?", (sid,))

    @staticmethod
    def update_field(sid: int, field: str, value):
        allowed = {"name", "primary", "success", "danger",
                   "icon", "font_style", "layout", "enabled"}
        if field not in allowed:
            raise ValueError(f"Field {field} غير مسموح")
        db.execute(f"UPDATE button_styles SET {field}=? WHERE style_id=?", (value, sid))

    @staticmethod
    def delete(sid: int):
        db.execute("DELETE FROM button_styles WHERE style_id=?", (sid,))

    @staticmethod
    def clone(sid: int) -> int:
        src = StyleRepo.get(sid)
        if not src:
            raise ValueError("Style غير موجود")
        new_name = f"{src['name']} Copy"
        cur = db.execute(
            """INSERT INTO button_styles
               (name,primary,success,danger,icon,font_style,layout,is_default,enabled)
               VALUES(?,?,?,?,?,?,?,0,1)""",
            (new_name, src["primary"], src["success"], src["danger"],
             src["icon"], src["font_style"], src["layout"])
        )
        return cur.lastrowid

    @staticmethod
    def create(name: str):
        db.execute(
            """INSERT INTO button_styles
               (name,primary,success,danger,icon,font_style,layout,is_default,enabled)
               VALUES(?,?,?,?,?,?,?,0,1)""",
            (name, "primary", "success", "danger", "", "sans", "2")
        )


class LayoutRepo:
    @staticmethod
    def get(screen: str) -> int:
        row = db.fetchone("SELECT columns FROM layouts WHERE screen=?", (screen,))
        return row["columns"] if row else 2

    @staticmethod
    def set(screen: str, cols: int):
        cols = max(1, min(cols, 4))
        db.execute(
            """INSERT INTO layouts(screen, columns, spacing) VALUES(?,?,1)
               ON CONFLICT(screen) DO UPDATE SET columns=excluded.columns""",
            (screen, cols)
        )

    @staticmethod
    def all():
        return db.fetchall("SELECT * FROM layouts ORDER BY screen")


class LogRepo:
    @staticmethod
    def add(user_id: Optional[int], action: str, details: str = ""):
        db.execute(
            "INSERT INTO logs(user_id, action, details, timestamp) VALUES(?,?,?,?)",
            (user_id, action, details, Database.now())
        )

    @staticmethod
    def recent(limit: int = 30):
        return db.fetchall("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))


class BackupRepo:
    @staticmethod
    def register(filename: str, size: int, created_by: int):
        db.execute(
            "INSERT INTO backups(filename, size, created_at, created_by) VALUES(?,?,?,?)",
            (filename, size, Database.now(), created_by)
        )

    @staticmethod
    def all():
        return db.fetchall("SELECT * FROM backups ORDER BY id DESC LIMIT 20")


class AdminRepo:
    @staticmethod
    def is_admin(user_id: int) -> bool:
        if user_id in ADMIN_IDS:
            return True
        return db.fetchone("SELECT 1 FROM admins WHERE user_id=?", (user_id,)) is not None

    @staticmethod
    def add(user_id: int, role: str, added_by: int):
        db.execute(
            """INSERT OR REPLACE INTO admins(user_id, role, added_by, added_at)
               VALUES(?,?,?,?)""",
            (user_id, role, added_by, Database.now())
        )

    @staticmethod
    def remove(user_id: int):
        db.execute("DELETE FROM admins WHERE user_id=? AND role!='super'", (user_id,))

    @staticmethod
    def all():
        return db.fetchall("SELECT * FROM admins ORDER BY user_id")

    @staticmethod
    def role(user_id: int) -> Optional[str]:
        row = db.fetchone("SELECT role FROM admins WHERE user_id=?", (user_id,))
        return row["role"] if row else None


# ═══════════════════════════════════════════════════════════════
# SECTION 5: BOOTSTRAP
# ═══════════════════════════════════════════════════════════════
_db_initialized = False

def init_db():
    global _db_initialized
    if _db_initialized:
        return
    db.connect()
    seed_defaults()
    _db_initialized = True


# ═══════════════════════════════════════════════════════════════
# SECTION 6: UTILITIES
# ═══════════════════════════════════════════════════════════════
def render_message(key: str, user_row, extra: Optional[dict] = None) -> str:
    template = MessageRepo.get(key) or ""
    ctx = {
        "first_name": (user_row["first_name"] if user_row else "") or "",
        "username":   (user_row["username"]   if user_row else "") or "—",
        "user_id":    user_row["user_id"]     if user_row else 0,
        "points":     user_row["points"]      if user_row else 0,
        "balance":    user_row["points"]      if user_row else 0,
    }
    if extra:
        ctx.update(extra)
    try:
        return template.format(**ctx)
    except (KeyError, IndexError, ValueError):
        return template


def paginate(items: list, page: int, per_page: int = 8):
    total = len(items)
    pages = max(1, math.ceil(total / per_page))
    page = max(1, min(page, pages))
    start = (page - 1) * per_page
    return items[start:start + per_page], page, pages


def fmt_points(n: int) -> str:
    return f"{n:,}"


def is_valid_color(s: str) -> bool:
    if not isinstance(s, str) or not s.startswith("#"):
        return False
    if len(s) not in (4, 7):
        return False
    try:
        int(s[1:], 16)
        return True
    except ValueError:
        return False


def escape_html(t: str) -> str:
    return (t.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def safe_slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_\-]", "_", s.strip())
    return s.lower()[:40] or "item"


def random_code(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ═══════════════════════════════════════════════════════════════
# SECTION 7: TELEGRAM IMPORTS
# ═══════════════════════════════════════════════════════════════
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ButtonStyle
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    BufferedInputFile, BotCommand, WebAppInfo
)
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError

router = Router()

# فحص توفّر دعم ButtonStyle في هذا الإصدار
BUTTON_STYLE_SUPPORTED = True
try:
    InlineKeyboardButton(text="x", callback_data="y", style=ButtonStyle.PRIMARY)
except TypeError:
    BUTTON_STYLE_SUPPORTED = False
    log.warning("⚠️ إصدار aiogram لا يدعم ButtonStyle — سيتم تجاهل الألوان.")


# ═══════════════════════════════════════════════════════════════
# SECTION 8: KEYBOARD BUILDER
# ═══════════════════════════════════════════════════════════════
VALID_STYLES = {"primary", "success", "danger"}


class KeyboardBuilder:
    @staticmethod
    def _make_button(b: dict) -> InlineKeyboardButton:
        label = b.get("label", "—")
        icon = b.get("icon", "")
        if icon:
            label = f"{icon} {label}"

        kwargs = {"text": label}

        style = (b.get("style") or "").lower()
        if style in VALID_STYLES and BUTTON_STYLE_SUPPORTED:
            try:
                kwargs["style"] = ButtonStyle(style)
            except (TypeError, ValueError, AttributeError):
                pass

        if b.get("url"):
            kwargs["url"] = b["url"]
        elif b.get("webapp"):
            kwargs["web_app"] = WebAppInfo(url=b["webapp"])
        else:
            kwargs["callback_data"] = b.get("callback", "noop")

        return InlineKeyboardButton(**kwargs)

    @staticmethod
    def build(buttons: list[dict],
              columns: int = 2,
              footer: Optional[list[dict]] = None) -> InlineKeyboardMarkup:
        rows: list[list[InlineKeyboardButton]] = []
        columns = max(1, min(columns, 4))
        for i in range(0, len(buttons), columns):
            chunk = buttons[i:i + columns]
            rows.append([KeyboardBuilder._make_button(b) for b in chunk])
        if footer:
            for b in footer:
                rows.append([KeyboardBuilder._make_button(b)])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    @staticmethod
    def simple(*rows: list[dict]) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[[KeyboardBuilder._make_button(b) for b in row]
                             for row in rows]
        )


def nav_footer(extra: Optional[list[dict]] = None) -> list[dict]:
    items = list(extra or [])
    items.append({"label": "رجوع", "callback": "nav:back", "icon": "◀️", "style": "primary"})
    items.append({"label": "الرئيسية", "callback": "nav:home", "icon": "🏠", "style": "primary"})
    return items


def pagination_row(prefix: str, page: int, pages: int) -> list[dict]:
    row = []
    if page > 1:
        row.append({"label": "السابق", "callback": f"{prefix}:{page-1}", "icon": "‹", "style": "primary"})
    row.append({"label": f"{page}/{pages}", "callback": "noop", "style": "success"})
    if page < pages:
        row.append({"label": "التالي", "callback": f"{prefix}:{page+1}", "icon": "›", "style": "primary"})
    return row


# ═══════════════════════════════════════════════════════════════
# SECTION 9: FSM STATES
# ═══════════════════════════════════════════════════════════════
class UserStates(StatesGroup):
    waiting_calc_expr   = State()
    waiting_unit_value  = State()
    waiting_json_input  = State()
    waiting_txt_content = State()
    waiting_csv_rows    = State()
    waiting_wifi_data   = State()
    searching_service   = State()


class AdminStates(StatesGroup):
    user_search          = State()
    user_add_points      = State()
    user_remove_points   = State()
    user_ban_confirm     = State()
    service_new_key      = State()
    service_new_name     = State()
    service_new_desc     = State()
    service_new_icon     = State()
    service_new_category = State()
    service_new_price    = State()
    service_edit_value   = State()
    service_search       = State()
    style_new_name       = State()
    style_edit_value     = State()
    theme_new_name       = State()
    theme_edit_value     = State()
    layout_set_value     = State()
    message_edit         = State()
    broadcast_compose    = State()
    broadcast_confirm    = State()
    admin_add_id         = State()


# ═══════════════════════════════════════════════════════════════
# SECTION 10: SERVICE ENGINE
# ═══════════════════════════════════════════════════════════════
import qrcode
from PIL import Image, ImageDraw, ImageFont


class ServiceEngine:
    @staticmethod
    async def calculator(message: Message, expr: str):
        expr = expr.strip().replace("×", "*").replace("÷", "/").replace("^", "**")
        if not expr:
            await message.answer("أرسل تعبيراً مثل: 12+5*3")
            return
        if len(expr) > 200:
            await message.answer("التعبير طويل جداً.")
            return
        allowed = set("0123456789+-*/(). %")
        if not set(expr) <= allowed:
            await message.answer("❌ التعبير يحتوي رموزاً غير مسموحة.")
            return
        try:
            result = eval(expr, {"__builtins__": {}}, {})
            await message.answer(
                f"<b>النتيجة:</b> <code>{result}</code>",
                parse_mode=ParseMode.HTML
            )
        except ZeroDivisionError:
            await message.answer("❌ القسمة على صفر.")
        except Exception as e:
            await message.answer(f"❌ خطأ: {escape_html(str(e))}", parse_mode=ParseMode.HTML)

    UNITS = {
        "km": ("length", 1000.0), "m": ("length", 1.0), "cm": ("length", 0.01),
        "mm": ("length", 0.001), "mi": ("length", 1609.344), "ft": ("length", 0.3048),
        "in": ("length", 0.0254),
        "kg": ("weight", 1.0), "g": ("weight", 0.001), "mg": ("weight", 1e-6),
        "lb": ("weight", 0.453592), "oz": ("weight", 0.0283495),
        "c": ("temp", 0), "f": ("temp", 0), "k": ("temp", 0),
    }

    @staticmethod
    def _conv_temp(v: float, src: str, dst: str) -> float:
        if src == "c":   c = v
        elif src == "f": c = (v - 32) * 5 / 9
        elif src == "k": c = v - 273.15
        else: raise ValueError("unit")
        if dst == "c":   return c
        if dst == "f":   return c * 9 / 5 + 32
        if dst == "k":   return c + 273.15
        raise ValueError("unit")

    @staticmethod
    async def unit_conv(message: Message, raw: str):
        parts = raw.strip().lower().split()
        if len(parts) != 3:
            await message.answer("الصيغة: <code>100 km mi</code>", parse_mode=ParseMode.HTML)
            return
        try:
            value = float(parts[0])
        except ValueError:
            await message.answer("القيمة الأولى يجب أن تكون رقماً.")
            return
        src, dst = parts[1], parts[2]
        if src not in ServiceEngine.UNITS or dst not in ServiceEngine.UNITS:
            await message.answer("وحدة غير معروفة. مثال: km, m, cm, mi, ft, in, kg, g, lb, oz, c, f, k")
            return
        s_cat = ServiceEngine.UNITS[src][0]
        d_cat = ServiceEngine.UNITS[dst][0]
        try:
            if s_cat == "temp" and d_cat == "temp":
                result = ServiceEngine._conv_temp(value, src, dst)
            elif s_cat == d_cat:
                result = value * ServiceEngine.UNITS[src][1] / ServiceEngine.UNITS[dst][1]
            else:
                await message.answer("لا يمكن التحويل بين فئتين مختلفتين.")
                return
            await message.answer(
                f"<b>{value} {src}</b> = <b>{result:.4f} {dst}</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            await message.answer(f"❌ {escape_html(str(e))}", parse_mode=ParseMode.HTML)

    @staticmethod
    async def json_format(message: Message, raw: str):
        if not raw.strip():
            await message.answer("أرسل نص JSON.")
            return
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            await message.answer(
                f"❌ JSON غير صالح:\n<code>{escape_html(str(e))}</code>",
                parse_mode=ParseMode.HTML
            )
            return
        pretty = json.dumps(data, ensure_ascii=False, indent=2)
        if len(pretty) > 3500:
            file = BufferedInputFile(pretty.encode("utf-8"), filename="formatted.json")
            await message.answer_document(file, caption="📎 الملف كبير، أُرسل كمرفق.")
        else:
            await message.answer(f"<pre>{escape_html(pretty)}</pre>",
                                 parse_mode=ParseMode.HTML)

    @staticmethod
    async def txt_make(message: Message, content: str):
        if not content.strip():
            await message.answer("أرسل المحتوى الذي تريد وضعه في الملف.")
            return
        data = content.encode("utf-8")
        file = BufferedInputFile(data, filename=f"note_{random_code(4)}.txt")
        await message.answer_document(file, caption=f"📄 تم إنشاء الملف ({human_size(len(data))})")

    @staticmethod
    async def txt_read(message: Message):
        if not message.document:
            await message.answer("أرسل ملف TXT.")
            return
        if not (message.document.file_name or "").lower().endswith(".txt"):
            await message.answer("❌ الملف ليس TXT.")
            return
        if (message.document.file_size or 0) > 5 * 1024 * 1024:
            await message.answer("❌ الحد 5MB.")
            return
        try:
            file = await message.bot.get_file(message.document.file_id)
            buf = io.BytesIO()
            await message.bot.download_file(file.file_path, buf)
            text = buf.getvalue().decode("utf-8", errors="replace")
            preview = text[:3500]
            suffix = "\n\n… (مقتطف)" if len(text) > 3500 else ""
            await message.answer(
                f"<b>محتوى الملف:</b>\n<pre>{escape_html(preview)}{suffix}</pre>",
                parse_mode=ParseMode.HTML
            )
        except TelegramAPIError as e:
            await message.answer(f"❌ فشل التحميل: {escape_html(str(e))}",
                                 parse_mode=ParseMode.HTML)

    @staticmethod
    async def csv_generate(message: Message, raw: str):
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        if not lines:
            await message.answer("أرسل بيانات. كل سطر صف، والفاصل <code>|</code> أو <code>,</code>",
                                 parse_mode=ParseMode.HTML)
            return
        rows = []
        for ln in lines:
            if "|" in ln:
                rows.append([c.strip() for c in ln.split("|")])
            else:
                rows.append([c.strip() for c in ln.split(",")])
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerows(rows)
        data = buf.getvalue().encode("utf-8-sig")
        file = BufferedInputFile(data, filename=f"data_{random_code(4)}.csv")
        await message.answer_document(file, caption=f"📊 CSV جاهز ({len(rows)} صف)")

    @staticmethod
    async def zip_make(message: Message, files: list):
        if not files:
            await message.answer("أرسل ملفاً واحداً على الأقل بعد اختيار الخدمة.")
            return
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, f in enumerate(files[:20]):
                try:
                    tgf = await message.bot.get_file(f.file_id)
                    b = io.BytesIO()
                    await message.bot.download_file(tgf.file_path, b)
                    name = f.file_name or f"file_{i}.bin"
                    zf.writestr(name, b.getvalue())
                except Exception as e:
                    log.warning("zip skip file %s: %s", i, e)
        data = buf.getvalue()
        file = BufferedInputFile(data, filename=f"archive_{random_code(4)}.zip")
        await message.answer_document(
            file,
            caption=f"🗜️ الأرشيف جاهز ({len(files)} ملف · {human_size(len(data))})"
        )

    @staticmethod
    async def wifi_card(message: Message, raw: str):
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 2:
            await message.answer("الصيغة: <code>SSID | password</code>",
                                 parse_mode=ParseMode.HTML)
            return
        ssid, password = parts[0], parts[1]
        enc = parts[2] if len(parts) > 2 else "WPA"

        qr_text = f"WIFI:T:{enc};S:{ssid};P:{password};;"

        img = Image.new("RGB", (600, 400), "white")
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 26)
            font_small = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()

        d.rectangle([0, 0, 600, 80], fill="#2c3e50")
        d.text((20, 25), "WiFi Card - المطري خدمات", fill="white", font=font)
        d.text((20, 110), f"SSID: {ssid}", fill="black", font=font)
        d.text((20, 150), f"Password: {password}", fill="black", font=font)
        d.text((20, 190), f"Encryption: {enc}", fill="black", font=font_small)

        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(qr_text)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_img = qr_img.resize((180, 180))
        img.paste(qr_img, (400, 130))

        out = io.BytesIO()
        img.save(out, format="PNG")
        out.seek(0)
        file = BufferedInputFile(out.getvalue(), filename=f"wifi_{safe_slug(ssid)}.png")
        await message.answer_document(file, caption="📶 بطاقة WiFi جاهزة للطباعة")


SERVICE_HANDLERS = {
    "calculator": ServiceEngine.calculator,
    "unit_conv":  ServiceEngine.unit_conv,
    "json_fmt":   ServiceEngine.json_format,
    "txt_make":   ServiceEngine.txt_make,
    "csv_gen":    ServiceEngine.csv_generate,
    "wifi_card":  ServiceEngine.wifi_card,
}


# ═══════════════════════════════════════════════════════════════
# SECTION 12: HELPERS
# ═══════════════════════════════════════════════════════════════
def is_admin(user_id: int) -> bool:
    return AdminRepo.is_admin(user_id)


def log_action(user_id: int, action: str, details: str = ""):
    LogRepo.add(user_id, action, details)


# ═══════════════════════════════════════════════════════════════
# SECTION 13: USER — /start + الإحالة
# ═══════════════════════════════════════════════════════════════
async def send_home(target, user_row, edit: bool = False):
    text = render_message("HOME", user_row)
    text += f"\n\n👤 {user_row['first_name'] or ''}\n⭐ النقاط: {fmt_points(user_row['points'])}"

    buttons = [
        {"label": "الخدمات",   "callback": "user:services",   "icon": "🧰", "style": "primary"},
        {"label": "حسابي",     "callback": "user:profile",    "icon": "👤", "style": "primary"},
        {"label": "النقاط",    "callback": "user:points",     "icon": "⭐", "style": "success"},
        {"label": "الإحالة",   "callback": "user:referral",   "icon": "🔗", "style": "success"},
        {"label": "البحث",     "callback": "user:search",     "icon": "🔍", "style": "primary"},
        {"label": "المساعدة",  "callback": "user:help",       "icon": "❓", "style": "primary"},
    ]
    cols = LayoutRepo.get("home")
    kb = KeyboardBuilder.build(buttons, columns=cols)

    if edit and hasattr(target, "message"):
        try:
            await target.message.edit_text(text, reply_markup=kb)
            return
        except TelegramAPIError:
            pass
    if hasattr(target, "answer"):
        await target.answer(text, reply_markup=kb)
    else:
        await target.message.answer(text, reply_markup=kb)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    tg_user = message.from_user

    existing = UserRepo.get(tg_user.id)
    if existing and existing["is_banned"]:
        await message.answer("🚫 حسابك محظور من استخدام البوت.")
        return

    user_row = UserRepo.get_or_create(tg_user)

    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        payload = args[1].strip()
        if payload.startswith("REF") and not existing:
            try:
                referrer_id = int(payload[3:])
            except ValueError:
                referrer_id = 0
            if referrer_id and referrer_id != tg_user.id and UserRepo.get(referrer_id):
                UserRepo.set_referrer(tg_user.id, referrer_id)
                reward = int(SettingsRepo.get("referral_reward", str(REFERRAL_REWARD)))
                UserRepo.add_points(referrer_id, reward,
                                    f"إحالة مستخدم {tg_user.id}",
                                    None, kind="referral")
                log_action(tg_user.id, "referral_registered", f"referrer={referrer_id}")
                try:
                    await message.bot.send_message(
                        referrer_id,
                        f"🎉 مستخدم جديد سجّل عبر رابطك!\n+{reward} نقطة"
                    )
                except TelegramAPIError:
                    pass

    log_action(tg_user.id, "start")
    await send_home(message, user_row)


# ═══════════════════════════════════════════════════════════════
# SECTION 14: USER — التنقل
# ═══════════════════════════════════════════════════════════════
NAV_STACK: dict[int, list[str]] = {}


def push_nav(uid: int, screen: str):
    NAV_STACK.setdefault(uid, []).append(screen)
    if len(NAV_STACK[uid]) > 20:
        NAV_STACK[uid] = NAV_STACK[uid][-20:]


def pop_nav(uid: int) -> Optional[str]:
    stack = NAV_STACK.get(uid, [])
    if not stack:
        return None
    return stack.pop()


@router.callback_query(F.data == "nav:home")
async def cb_nav_home(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    user_row = UserRepo.get(cb.from_user.id)
    if not user_row:
        await cb.answer("ابدأ بـ /start", show_alert=True)
        return
    await cb.answer()
    await send_home(cb, user_row, edit=True)


@router.callback_query(F.data == "nav:back")
async def cb_nav_back(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    user_row = UserRepo.get(cb.from_user.id)
    if not user_row:
        await cb.answer("ابدأ بـ /start", show_alert=True)
        return
    await cb.answer()
    await send_home(cb, user_row, edit=True)


@router.callback_query(F.data == "noop")
async def cb_noop(cb: CallbackQuery):
    await cb.answer()


# ═══════════════════════════════════════════════════════════════
# SECTION 15: USER — الملف الشخصي
# ═══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "user:profile")
async def cb_profile(cb: CallbackQuery):
    user_row = UserRepo.get(cb.from_user.id)
    if not user_row:
        await cb.answer("ابدأ بـ /start", show_alert=True)
        return
    await cb.answer()
    push_nav(cb.from_user.id, "home")

    text = render_message("PROFILE", user_row)
    rows = [
        [{"label": "سجل العمليات", "callback": "user:transactions", "icon": "📜", "style": "primary"}],
        [{"label": "رجوع",  "callback": "nav:back",  "icon": "◀️", "style": "primary"},
         {"label": "الرئيسية", "callback": "nav:home", "icon": "🏠", "style": "primary"}],
    ]
    kb = KeyboardBuilder.simple(*rows)
    try:
        await cb.message.edit_text(text, reply_markup=kb)
    except TelegramAPIError:
        await cb.message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "user:points")
async def cb_points(cb: CallbackQuery):
    user_row = UserRepo.get(cb.from_user.id)
    if not user_row:
        await cb.answer("ابدأ بـ /start", show_alert=True)
        return
    await cb.answer()
    text = render_message("POINTS", user_row)
    text += "\n\nكيف تكسب النقاط؟\n• دعوة أصدقائك عبر رابط الإحالة\n• مكافآت الأدمن"
    rows = [
        [{"label": "رابط الإحالة", "callback": "user:referral", "icon": "🔗", "style": "success"}],
        [{"label": "سجل العمليات", "callback": "user:transactions", "icon": "📜", "style": "primary"}],
        [{"label": "رجوع", "callback": "nav:back", "icon": "◀️", "style": "primary"},
         {"label": "الرئيسية", "callback": "nav:home", "icon": "🏠", "style": "primary"}],
    ]
    kb = KeyboardBuilder.simple(*rows)
    try:
        await cb.message.edit_text(text, reply_markup=kb)
    except TelegramAPIError:
        await cb.message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "user:transactions")
async def cb_transactions(cb: CallbackQuery):
    user_row = UserRepo.get(cb.from_user.id)
    if not user_row:
        await cb.answer("ابدأ بـ /start", show_alert=True)
        return
    await cb.answer()
    txs = UserRepo.transactions(cb.from_user.id, limit=15)
    if not txs:
        body = "لا توجد عمليات بعد."
    else:
        lines = []
        for t in txs:
            sign = "+" if t["amount"] > 0 else ""
            lines.append(f"{sign}{t['amount']} · {t['reason']} · {t['created_at'][:16]}")
        body = "\n".join(lines)
    text = f"📜 <b>آخر العمليات</b>\n\n<pre>{escape_html(body)}</pre>"
    rows = [
        [{"label": "رجوع", "callback": "nav:back", "icon": "◀️", "style": "primary"},
         {"label": "الرئيسية", "callback": "nav:home", "icon": "🏠", "style": "primary"}],
    ]
    kb = KeyboardBuilder.simple(*rows)
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        await cb.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════════════════════
# SECTION 16: USER — الإحالة
# ═══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "user:referral")
async def cb_referral(cb: CallbackQuery):
    user_row = UserRepo.get(cb.from_user.id)
    if not user_row:
        await cb.answer("ابدأ بـ /start", show_alert=True)
        return
    await cb.answer()

    me = await cb.bot.get_me()
    link = f"https://t.me/{me.username}?start=REF{cb.from_user.id}"
    reward = SettingsRepo.get("referral_reward", str(REFERRAL_REWARD))
    invited = db.fetchone("SELECT COUNT(*) AS c FROM users WHERE referrer_id=?",
                          (cb.from_user.id,))["c"]

    text = (
        "🔗 <b>نظام الإحالة</b>\n\n"
        f"رابطك:\n<code>{link}</code>\n\n"
        f"🎁 مكافأة كل إحالة: <b>{reward}</b> نقطة\n"
        f"👥 عدد من دعوتهم: <b>{invited}</b>"
    )
    rows = [
        [{"label": "نسخ الرابط", "callback": "user:referral_copy", "icon": "📋", "style": "success"}],
        [{"label": "مشاركة",     "url": f"https://t.me/share/url?url={link}",
          "icon": "📤", "style": "primary"}],
        [{"label": "رجوع", "callback": "nav:back", "icon": "◀️", "style": "primary"},
         {"label": "الرئيسية", "callback": "nav:home", "icon": "🏠", "style": "primary"}],
    ]
    kb = KeyboardBuilder.simple(*rows)
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        await cb.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "user:referral_copy")
async def cb_referral_copy(cb: CallbackQuery):
    me = await cb.bot.get_me()
    link = f"https://t.me/{me.username}?start=REF{cb.from_user.id}"
    await cb.answer(f"الرابط: {link}", show_alert=True)


# ═══════════════════════════════════════════════════════════════
# SECTION 17: USER — مركز الخدمات
# ═══════════════════════════════════════════════════════════════
SERVICES_PER_PAGE = 6


def _service_button(s) -> dict:
    price_tag = "مجاني" if s["is_free"] else f"{s['price']} نقطة"
    label = f"{s['name']} · {price_tag}"
    return {
        "label": label,
        "callback": f"svc:open:{s['id']}",
        "icon": s["icon"] or "•",
        "style": "success" if s["is_free"] else "primary",
    }


def build_services_view(page: int = 1,
                        category: Optional[str] = None,
                        query: Optional[str] = None) -> tuple[str, InlineKeyboardMarkup]:
    all_svcs = ServiceRepo.all_enabled()
    if category:
        all_svcs = [s for s in all_svcs if s["category"] == category]
    if query:
        q = query.lower()
        all_svcs = [s for s in all_svcs
                    if q in (s["name"] or "").lower()
                    or q in (s["description"] or "").lower()]

    page_items, page, pages = paginate(all_svcs, page, SERVICES_PER_PAGE)

    title = "🧰 <b>مركز الخدمات</b>"
    if category:
        title += f"\n📂 التصنيف: <b>{escape_html(category)}</b>"
    if query:
        title += f"\n🔍 البحث: <b>{escape_html(query)}</b>"
    title += f"\n\nعدد النتائج: {len(all_svcs)}"

    rows: list[list[dict]] = []
    rows.append([
        {"label": "بحث", "callback": "svc:search", "icon": "🔍", "style": "primary"},
        {"label": "الكل", "callback": "svc:list:1:all", "icon": "📋", "style": "primary"},
    ])

    for s in page_items:
        rows.append([_service_button(s)])

    rows.append(pagination_row("svc:page", page, pages))

    rows.append([
        {"label": "رجوع", "callback": "nav:back", "icon": "◀️", "style": "primary"},
        {"label": "الرئيسية", "callback": "nav:home", "icon": "🏠", "style": "primary"},
    ])

    kb = KeyboardBuilder.simple(*rows)
    return title, kb


@router.callback_query(F.data == "user:services")
async def cb_services(cb: CallbackQuery):
    user_row = UserRepo.get(cb.from_user.id)
    if not user_row:
        await cb.answer("ابدأ بـ /start", show_alert=True)
        return
    await cb.answer()
    push_nav(cb.from_user.id, "home")
    title, kb = build_services_view(page=1)
    try:
        await cb.message.edit_text(title, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        await cb.message.answer(title, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("svc:page:"))
async def cb_services_page(cb: CallbackQuery):
    try:
        page = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        page = 1
    title, kb = build_services_view(page=page)
    await cb.answer()
    try:
        await cb.message.edit_text(title, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        pass


@router.callback_query(F.data.startswith("svc:list:"))
async def cb_services_list(cb: CallbackQuery):
    parts = cb.data.split(":")
    try:
        page = int(parts[2])
        cat = parts[3] if len(parts) > 3 else "all"
    except (IndexError, ValueError):
        page, cat = 1, "all"
    title, kb = build_services_view(page=page,
                                    category=None if cat == "all" else cat)
    await cb.answer()
    try:
        await cb.message.edit_text(title, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        pass


@router.callback_query(F.data == "svc:search")
async def cb_service_search(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await state.set_state(UserStates.searching_service)
    kb = KeyboardBuilder.simple(
        [{"label": "إلغاء", "callback": "svc:search_cancel", "icon": "✖️", "style": "danger"}]
    )
    try:
        await cb.message.edit_text("🔍 أرسل كلمة للبحث في الخدمات:", reply_markup=kb)
    except TelegramAPIError:
        await cb.message.answer("🔍 أرسل كلمة للبحث في الخدمات:", reply_markup=kb)


@router.callback_query(F.data == "svc:search_cancel")
async def cb_search_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.answer()
    await cb_services(cb)


@router.message(StateFilter(UserStates.searching_service))
async def msg_service_search(message: Message, state: FSMContext):
    await state.clear()
    q = (message.text or "").strip()
    if not q:
        await message.answer("أرسل كلمة صحيحة.")
        return
    title, kb = build_services_view(page=1, query=q)
    await message.answer(title, reply_markup=kb, parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════════════════════
# SECTION 18: USER — فتح خدمة
# ═══════════════════════════════════════════════════════════════
SERVICE_INPUT_PROMPTS = {
    "calculator": ("🧮 أرسل التعبير الحسابي:\nمثال: <code>(12+5)*3</code>",
                   UserStates.waiting_calc_expr),
    "unit_conv":  ("📏 أرسل بصيغة: <code>القيمة الوحدة_المصدر الوحدة_الهدف</code>\nمثال: <code>100 km mi</code>",
                   UserStates.waiting_unit_value),
    "json_fmt":   ("🧩 أرسل نص JSON لتنسيقه.",
                   UserStates.waiting_json_input),
    "txt_make":   ("📝 أرسل المحتوى الذي تريد تحويله إلى ملف TXT.",
                   UserStates.waiting_txt_content),
    "csv_gen":    ("📊 أرسل بيانات CSV. كل سطر صف، الفاصل <code>|</code> أو <code>,</code>",
                   UserStates.waiting_csv_rows),
    "wifi_card":  ("📶 أرسل بصيغة: <code>SSID | password</code>",
                   UserStates.waiting_wifi_data),
}


@router.callback_query(F.data.startswith("svc:open:"))
async def cb_service_open(cb: CallbackQuery, state: FSMContext):
    try:
        sid = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("خدمة غير معروفة", show_alert=True)
        return
    svc = ServiceRepo.get(sid)
    if not svc or not svc["is_enabled"]:
        await cb.answer("الخدمة غير متاحة حالياً.", show_alert=True)
        return

    user_row = UserRepo.get(cb.from_user.id)
    if not user_row:
        await cb.answer("ابدأ بـ /start", show_alert=True)
        return

    if not svc["is_free"]:
        if user_row["points"] < svc["price"]:
            await cb.answer(
                f"❌ تحتاج {svc['price']} نقطة. رصيدك: {user_row['points']}",
                show_alert=True
            )
            return

    await cb.answer()

    if svc["key"] == "txt_read":
        await state.set_state(UserStates.waiting_txt_content)
        await state.update_data(service="txt_read", price=svc["price"], free=svc["is_free"])
        kb = KeyboardBuilder.simple(
            [{"label": "إلغاء", "callback": "svc:cancel", "icon": "✖️", "style": "danger"}]
        )
        try:
            await cb.message.edit_text("📖 أرسل ملف TXT الآن.", reply_markup=kb)
        except TelegramAPIError:
            await cb.message.answer("📖 أرسل ملف TXT الآن.", reply_markup=kb)
        return

    if svc["key"] == "zip_make":
        await state.set_state(UserStates.waiting_txt_content)
        await state.update_data(service="zip_make", price=svc["price"],
                                free=svc["is_free"], zip_files=[])
        kb = KeyboardBuilder.simple(
            [{"label": "إنهاء وإنشاء ZIP", "callback": "svc:zip_done", "icon": "✅", "style": "success"}],
            [{"label": "إلغاء", "callback": "svc:cancel", "icon": "✖️", "style": "danger"}],
        )
        try:
            await cb.message.edit_text(
                "🗜️ أرسل الملفات واحداً تلو الآخر، ثم اضغط <b>إنهاء</b>.",
                reply_markup=kb, parse_mode=ParseMode.HTML
            )
        except TelegramAPIError:
            await cb.message.answer(
                "🗜️ أرسل الملفات واحداً تلو الآخر، ثم اضغط <b>إنهاء</b>.",
                reply_markup=kb, parse_mode=ParseMode.HTML
            )
        return

    prompt = SERVICE_INPUT_PROMPTS.get(svc["key"])
    if not prompt:
        await cb.answer("هذه الخدمة غير مفعّلة بعد.", show_alert=True)
        return

    text, st = prompt
    await state.set_state(st)
    await state.update_data(service=svc["key"], price=svc["price"], free=svc["is_free"])
    kb = KeyboardBuilder.simple(
        [{"label": "إلغاء", "callback": "svc:cancel", "icon": "✖️", "style": "danger"}]
    )
    header = f"<b>{svc['icon']} {svc['name']}</b>\n"
    if not svc["is_free"]:
        header += f"💠 السعر: {svc['price']} نقطة\n"
    try:
        await cb.message.edit_text(header + text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        await cb.message.answer(header + text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "svc:cancel")
async def cb_service_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.answer("أُلغيت العملية")
    await cb_services(cb)


async def _finalize_service(message: Message, state: FSMContext, service_key: str):
    data = await state.get_data()
    price = int(data.get("price", 0))
    is_free = bool(data.get("free", True))
    uid = message.from_user.id

    if not is_free and price > 0:
        user_row = UserRepo.get(uid)
        if user_row["points"] < price:
            await message.answer("❌ رصيدك غير كافٍ.")
            await state.clear()
            return False
        UserRepo.add_points(uid, -price, f"استخدام خدمة {service_key}",
                            None, kind="service")
        log_action(uid, "service_paid", f"{service_key} -{price}")
    else:
        log_action(uid, "service_used", service_key)

    await state.clear()
    return True


@router.message(StateFilter(UserStates.waiting_calc_expr))
async def handle_calculator(message: Message, state: FSMContext):
    ok = await _finalize_service(message, state, "calculator")
    if ok:
        await ServiceEngine.calculator(message, message.text or "")


@router.message(StateFilter(UserStates.waiting_unit_value))
async def handle_unit_conv(message: Message, state: FSMContext):
    ok = await _finalize_service(message, state, "unit_conv")
    if ok:
        await ServiceEngine.unit_conv(message, message.text or "")


@router.message(StateFilter(UserStates.waiting_json_input))
async def handle_json_fmt(message: Message, state: FSMContext):
    ok = await _finalize_service(message, state, "json_fmt")
    if ok:
        await ServiceEngine.json_format(message, message.text or "")


@router.message(StateFilter(UserStates.waiting_txt_content))
async def handle_txt_flexible(message: Message, state: FSMContext):
    data = await state.get_data()
    service = data.get("service")

    if service == "txt_make":
        ok = await _finalize_service(message, state, "txt_make")
        if ok:
            await ServiceEngine.txt_make(message, message.text or "")
        return

    if service == "txt_read":
        if not message.document:
            await message.answer("أرسل ملف TXT.")
            return
        ok = await _finalize_service(message, state, "txt_read")
        if ok:
            await ServiceEngine.txt_read(message)
        return

    if service == "zip_make":
        if message.document:
            files = data.get("zip_files", [])
            files.append({
                "file_id": message.document.file_id,
                "file_name": message.document.file_name,
            })
            await state.update_data(zip_files=files)
            await message.answer(f"✅ أُضيف. المجموع: {len(files)}")
        else:
            await message.answer("أرسل ملفاً أو اضغط إنهاء.")


@router.callback_query(F.data == "svc:zip_done")
async def cb_zip_done(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    service = data.get("service")
    if service != "zip_make":
        await cb.answer("لا توجد عملية ضغط جارية.")
        return
    files = data.get("zip_files", [])
    if not files:
        await cb.answer("أرسل ملفاً واحداً على الأقل.", show_alert=True)
        return

    price = int(data.get("price", 0))
    is_free = bool(data.get("free", True))
    uid = cb.from_user.id
    if not is_free and price > 0:
        u = UserRepo.get(uid)
        if u["points"] < price:
            await cb.answer("❌ رصيدك غير كافٍ", show_alert=True)
            await state.clear()
            return
        UserRepo.add_points(uid, -price, "استخدام خدمة zip_make", None, kind="service")

    await cb.answer("جاري التنفيذ...")
    try:
        await cb.message.edit_text("⏳ جاري ضغط الملفات...")
    except TelegramAPIError:
        pass

    class _MsgProxy:
        def __init__(self, base): self.base = base
        @property
        def bot(self): return self.base.bot
        async def answer_document(self, *a, **k):
            return await self.base.answer_document(*a, **k)
        async def answer(self, *a, **k):
            return await self.base.answer(*a, **k)

    await ServiceEngine.zip_make(_MsgProxy(cb.message), files)
    log_action(uid, "service_used", "zip_make")
    await state.clear()


@router.message(StateFilter(UserStates.waiting_csv_rows))
async def handle_csv(message: Message, state: FSMContext):
    ok = await _finalize_service(message, state, "csv_gen")
    if ok:
        await ServiceEngine.csv_generate(message, message.text or "")


@router.message(StateFilter(UserStates.waiting_wifi_data))
async def handle_wifi(message: Message, state: FSMContext):
    ok = await _finalize_service(message, state, "wifi_card")
    if ok:
        await ServiceEngine.wifi_card(message, message.text or "")


# ═══════════════════════════════════════════════════════════════
# SECTION 19: USER — المساعدة
# ═══════════════════════════════════════════════════════════════
@router.callback_query(F.data == "user:help")
async def cb_help(cb: CallbackQuery):
    user_row = UserRepo.get(cb.from_user.id)
    if not user_row:
        await cb.answer("ابدأ بـ /start", show_alert=True)
        return
    await cb.answer()
    text = render_message("HELP", user_row)
    text += (
        "\n\n<b>الأوامر المتاحة:</b>\n"
        "/start — بدء\n"
        "/help — مساعدة\n"
    )
    rows = [
        [{"label": "رجوع", "callback": "nav:back", "icon": "◀️", "style": "primary"},
         {"label": "الرئيسية", "callback": "nav:home", "icon": "🏠", "style": "primary"}],
    ]
    kb = KeyboardBuilder.simple(*rows)
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        await cb.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.message(Command("help"))
async def cmd_help(message: Message):
    user_row = UserRepo.get_or_create(message.from_user)
    text = render_message("HELP", user_row)
    await message.answer(text)


# ═══════════════════════════════════════════════════════════════
# SECTION 20: ADMIN — الدخول للوحة
# ═══════════════════════════════════════════════════════════════
async def deny_admin(cb: CallbackQuery):
    await cb.answer("🚫 غير مصرّح لك.", show_alert=True)
    log_action(cb.from_user.id, "admin_denied", cb.data or "")


def admin_home_text() -> str:
    total_users = UserRepo.count()
    total_services = len(ServiceRepo.all())
    active_services = len(ServiceRepo.all_enabled())
    txs = db.fetchone("SELECT COUNT(*) AS c FROM transactions")["c"]
    return (
        "🛠️ <b>لوحة التحكم — المطري خدمات</b>\n\n"
        f"👥 المستخدمون: <b>{total_users}</b>\n"
        f"🧰 الخدمات: <b>{active_services}/{total_services}</b>\n"
        f"💠 العمليات: <b>{txs}</b>"
    )


def admin_home_kb() -> InlineKeyboardMarkup:
    rows = [
        [{"label": "المستخدمون", "callback": "adm:users:1", "icon": "👥", "style": "primary"},
         {"label": "الخدمات",    "callback": "adm:svc:1",   "icon": "🧰", "style": "primary"}],
        [{"label": "مصنع الأزرار", "callback": "adm:styles", "icon": "🎨", "style": "success"},
         {"label": "الثيمات",       "callback": "adm:themes", "icon": "🌗", "style": "success"}],
        [{"label": "التخطيطات",   "callback": "adm:layouts", "icon": "📐", "style": "primary"},
         {"label": "الرسائل",     "callback": "adm:messages", "icon": "✉️", "style": "primary"}],
        [{"label": "الإشعارات",   "callback": "adm:broadcast", "icon": "📢", "style": "danger"},
         {"label": "السجلات",     "callback": "adm:logs",      "icon": "📜", "style": "primary"}],
        [{"label": "النسخ الاحتياطي", "callback": "adm:backup", "icon": "💾", "style": "success"},
         {"label": "الإعدادات",       "callback": "adm:settings", "icon": "⚙️", "style": "primary"}],
        [{"label": "الأدمنز",   "callback": "adm:admins", "icon": "🛡️", "style": "primary"},
         {"label": "إعادة تحميل", "callback": "adm:reload", "icon": "🔄", "style": "success"}],
        [{"label": "الرئيسية", "callback": "nav:home", "icon": "🏠", "style": "primary"}],
    ]
    return KeyboardBuilder.simple(*rows)


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    if not is_admin(message.from_user.id):
        await message.answer("🚫 غير مصرّح.")
        return
    await message.answer(admin_home_text(),
                         reply_markup=admin_home_kb(),
                         parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "adm:home")
async def cb_admin_home(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    await cb.answer()
    try:
        await cb.message.edit_text(admin_home_text(),
                                   reply_markup=admin_home_kb(),
                                   parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        await cb.message.answer(admin_home_text(),
                                reply_markup=admin_home_kb(),
                                parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "adm:reload")
async def cb_admin_reload(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    log_action(cb.from_user.id, "admin_reload")
    await cb.answer("✅ تم إعادة تحميل الإعدادات من قاعدة البيانات")
    try:
        await cb.message.edit_text(admin_home_text(),
                                   reply_markup=admin_home_kb(),
                                   parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        pass


# ═══════════════════════════════════════════════════════════════
# SECTION 21: ADMIN — المستخدمون
# ═══════════════════════════════════════════════════════════════
USERS_PER_PAGE = 8


def build_users_view(page: int = 1) -> tuple[str, InlineKeyboardMarkup]:
    total = UserRepo.count()
    all_users = UserRepo.all(limit=USERS_PER_PAGE, offset=(page - 1) * USERS_PER_PAGE)
    pages = max(1, math.ceil(total / USERS_PER_PAGE))
    page = max(1, min(page, pages))

    text = f"👥 <b>المستخدمون</b>\n\nالإجمالي: <b>{total}</b>\nالصفحة {page}/{pages}"

    rows: list[list[dict]] = []
    rows.append([
        {"label": "بحث", "callback": "adm:user_search", "icon": "🔍", "style": "primary"},
    ])
    for u in all_users:
        name = u["first_name"] or u["username"] or str(u["user_id"])
        ban = "🚫" if u["is_banned"] else ""
        label = f"{ban}{name} · {u['points']}p"
        rows.append([{
            "label": label,
            "callback": f"adm:user:{u['user_id']}",
            "icon": "•",
            "style": "danger" if u["is_banned"] else "primary",
        }])
    rows.append(pagination_row("adm:users", page, pages))
    rows.append([
        {"label": "رجوع", "callback": "adm:home", "icon": "◀️", "style": "primary"},
        {"label": "الرئيسية", "callback": "nav:home", "icon": "🏠", "style": "primary"},
    ])
    return text, KeyboardBuilder.simple(*rows)


@router.callback_query(F.data.startswith("adm:users:"))
async def cb_admin_users(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    try:
        page = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        page = 1
    await cb.answer()
    text, kb = build_users_view(page)
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        pass


@router.callback_query(F.data == "adm:user_search")
async def cb_user_search(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    await cb.answer()
    await state.set_state(AdminStates.user_search)
    kb = KeyboardBuilder.simple(
        [{"label": "إلغاء", "callback": "adm:users:1", "icon": "✖️", "style": "danger"}]
    )
    try:
        await cb.message.edit_text("🔍 أرسل ID أو @username أو اسم للبحث:", reply_markup=kb)
    except TelegramAPIError:
        await cb.message.answer("🔍 أرسل ID أو @username أو اسم للبحث:", reply_markup=kb)


@router.message(StateFilter(AdminStates.user_search))
async def msg_user_search(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    q = (message.text or "").strip().lstrip("@")
    if not q:
        await message.answer("أرسل كلمة صحيحة.")
        return
    results = UserRepo.search(q, limit=10)
    if not results:
        await message.answer("لا نتائج.")
        return
    rows = []
    for u in results:
        name = u["first_name"] or u["username"] or str(u["user_id"])
        rows.append([{
            "label": f"{name} · {u['user_id']}",
            "callback": f"adm:user:{u['user_id']}",
            "icon": "•",
            "style": "primary",
        }])
    rows.append([{"label": "رجوع", "callback": "adm:users:1", "icon": "◀️", "style": "primary"}])
    await message.answer(f"🔎 النتائج ({len(results)}):",
                         reply_markup=KeyboardBuilder.simple(*rows))


# ═══════════════════════════════════════════════════════════════
# SECTION 22: ADMIN — بطاقة مستخدم
# ═══════════════════════════════════════════════════════════════
def build_user_card(uid: int) -> tuple[str, InlineKeyboardMarkup]:
    u = UserRepo.get(uid)
    if not u:
        return "❌ المستخدم غير موجود.", KeyboardBuilder.simple(
            [{"label": "رجوع", "callback": "adm:users:1", "icon": "◀️", "style": "primary"}]
        )
    txs = UserRepo.transactions(uid, limit=3)
    tx_lines = "\n".join(f"  {t['amount']:+d} · {t['reason']}" for t in txs) or "  لا يوجد"
    text = (
        f"👤 <b>بطاقة المستخدم</b>\n\n"
        f"ID: <code>{u['user_id']}</code>\n"
        f"الاسم: {escape_html(u['first_name'] or '—')}\n"
        f"المعرف: @{escape_html(u['username'] or '—')}\n"
        f"النقاط: <b>{fmt_points(u['points'])}</b>\n"
        f"محظور: {'نعم 🚫' if u['is_banned'] else 'لا ✅'}\n"
        f"آخر ظهور: {u['last_seen'][:16] if u['last_seen'] else '—'}\n\n"
        f"آخر العمليات:\n<pre>{escape_html(tx_lines)}</pre>"
    )
    ban_label = "فك الحظر" if u["is_banned"] else "حظر"
    ban_style = "success" if u["is_banned"] else "danger"
    rows = [
        [{"label": "+100", "callback": f"adm:addp:{uid}:100", "icon": "➕", "style": "success"},
         {"label": "+500", "callback": f"adm:addp:{uid}:500", "icon": "➕", "style": "success"}],
        [{"label": "-100", "callback": f"adm:addp:{uid}:-100", "icon": "➖", "style": "danger"},
         {"label": "-500", "callback": f"adm:addp:{uid}:-500", "icon": "➖", "style": "danger"}],
        [{"label": "مبلغ مخصص", "callback": f"adm:addp_custom:{uid}", "icon": "✏️", "style": "primary"}],
        [{"label": ban_label, "callback": f"adm:ban:{uid}", "icon": "🚫", "style": ban_style}],
        [{"label": "رجوع", "callback": "adm:users:1", "icon": "◀️", "style": "primary"}],
    ]
    return text, KeyboardBuilder.simple(*rows)


@router.callback_query(F.data.startswith("adm:user:"))
async def cb_user_card(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    try:
        uid = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("ID غير صحيح", show_alert=True)
        return
    await cb.answer()
    text, kb = build_user_card(uid)
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        await cb.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm:addp:"))
async def cb_add_points_quick(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    parts = cb.data.split(":")
    try:
        uid = int(parts[2])
        amount = int(parts[3])
    except (IndexError, ValueError):
        await cb.answer("صيغة خاطئة", show_alert=True)
        return
    if not UserRepo.get(uid):
        await cb.answer("المستخدم غير موجود", show_alert=True)
        return
    reason = "تعديل يدوي من الأدمن" if amount > 0 else "خصم يدوي من الأدمن"
    new_balance = UserRepo.add_points(uid, amount, reason, cb.from_user.id, kind="admin")
    log_action(cb.from_user.id, "admin_add_points",
               f"uid={uid} delta={amount} new={new_balance}")
    await cb.answer(f"✅ الرصيد الجديد: {new_balance}", show_alert=True)
    try:
        await cb.bot.send_message(uid,
            f"💠 تم {'إضافة' if amount>0 else 'خصم'} {abs(amount)} نقطة.\n"
            f"رصيدك الآن: {new_balance}")
    except TelegramAPIError:
        pass
    text, kb = build_user_card(uid)
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        pass


@router.callback_query(F.data.startswith("adm:addp_custom:"))
async def cb_add_points_custom(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    try:
        uid = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("ID غير صحيح", show_alert=True)
        return
    await cb.answer()
    await state.set_state(AdminStates.user_add_points)
    await state.update_data(target_uid=uid)
    kb = KeyboardBuilder.simple(
        [{"label": "إلغاء", "callback": f"adm:user:{uid}", "icon": "✖️", "style": "danger"}]
    )
    try:
        await cb.message.edit_text(
            "✏️ أرسل المبلغ (موجب للإضافة، سالب للخصم). مثال: <code>+250</code> أو <code>-75</code>",
            reply_markup=kb, parse_mode=ParseMode.HTML
        )
    except TelegramAPIError:
        pass


@router.message(StateFilter(AdminStates.user_add_points))
async def msg_add_points_custom(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    uid = data.get("target_uid")
    if not uid:
        await state.clear()
        return
    try:
        amount = int((message.text or "").strip().replace("+", ""))
    except ValueError:
        await message.answer("❌ أرسل رقماً صحيحاً.")
        return
    await state.clear()
    new_balance = UserRepo.add_points(uid, amount,
                                      "تعديل مخصص من الأدمن",
                                      message.from_user.id, kind="admin")
    log_action(message.from_user.id, "admin_add_points",
               f"uid={uid} delta={amount} new={new_balance}")
    await message.answer(f"✅ تم. الرصيد الجديد: <b>{new_balance}</b>",
                         parse_mode=ParseMode.HTML)
    text, kb = build_user_card(uid)
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm:ban:"))
async def cb_ban_toggle(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    try:
        uid = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("ID خاطئ", show_alert=True)
        return
    u = UserRepo.get(uid)
    if not u:
        await cb.answer("غير موجود", show_alert=True)
        return
    if uid in ADMIN_IDS:
        await cb.answer("🚫 لا يمكن حظر أدمن.", show_alert=True)
        return

    new_state = 0 if u["is_banned"] else 1
    UserRepo.set_ban(uid, bool(new_state))
    log_action(cb.from_user.id, "admin_ban" if new_state else "admin_unban", f"uid={uid}")
    await cb.answer("✅ تم الحظر" if new_state else "✅ تم فك الحظر", show_alert=True)

    text, kb = build_user_card(uid)
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        pass


# ═══════════════════════════════════════════════════════════════
# SECTION 23: ADMIN — الخدمات
# ═══════════════════════════════════════════════════════════════
SVC_PER_PAGE = 6


def build_services_admin_view(page: int = 1) -> tuple[str, InlineKeyboardMarkup]:
    all_svcs = ServiceRepo.all()
    page_items, page, pages = paginate(all_svcs, page, SVC_PER_PAGE)

    text = (f"🧰 <b>إدارة الخدمات</b>\n\n"
            f"الإجمالي: {len(all_svcs)}\nالصفحة {page}/{pages}")

    rows: list[list[dict]] = []
    rows.append([
        {"label": "إضافة خدمة", "callback": "adm:svc_new", "icon": "➕", "style": "success"},
        {"label": "بحث", "callback": "adm:svc_search", "icon": "🔍", "style": "primary"},
    ])
    for s in page_items:
        flag = "🟢" if s["is_enabled"] else "🔴"
        price_tag = "مجاني" if s["is_free"] else f"{s['price']}p"
        label = f"{flag} {s['name']} · {price_tag}"
        rows.append([{
            "label": label,
            "callback": f"adm:svc_view:{s['id']}",
            "icon": s["icon"] or "•",
            "style": "success" if s["is_enabled"] else "danger",
        }])
    rows.append(pagination_row("adm:svc", page, pages))
    rows.append([
        {"label": "رجوع", "callback": "adm:home", "icon": "◀️", "style": "primary"},
        {"label": "الرئيسية", "callback": "nav:home", "icon": "🏠", "style": "primary"},
    ])
    return text, KeyboardBuilder.simple(*rows)


@router.callback_query(F.data.startswith("adm:svc:"))
async def cb_admin_services(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    try:
        page = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        page = 1
    await cb.answer()
    text, kb = build_services_admin_view(page)
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        pass


@router.callback_query(F.data.startswith("adm:svc_view:"))
async def cb_admin_service_card(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    try:
        sid = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("ID خاطئ", show_alert=True)
        return
    s = ServiceRepo.get(sid)
    if not s:
        await cb.answer("غير موجود", show_alert=True)
        return
    await cb.answer()

    price_str = "مجاني" if s["is_free"] else f"{s['price']} نقطة"
    text = (
        f"🧰 <b>{escape_html(s['name'])}</b>\n\n"
        f"المفتاح: <code>{s['key']}</code>\n"
        f"الوصف: {escape_html(s['description'] or '—')}\n"
        f"الأيقونة: {s['icon'] or '—'}\n"
        f"التصنيف: {escape_html(s['category'] or '—')}\n"
        f"الترتيب: {s['sort_order']}\n"
        f"الحالة: {'🟢 مفعّلة' if s['is_enabled'] else '🔴 معطّلة'}\n"
        f"التسعير: {price_str}"
    )
    toggle_label = "تعطيل" if s["is_enabled"] else "تفعيل"
    toggle_style = "danger" if s["is_enabled"] else "success"
    rows = [
        [{"label": "تعديل الاسم",    "callback": f"adm:svc_edit:{sid}:name",        "icon": "✏️", "style": "primary"}],
        [{"label": "تعديل الوصف",    "callback": f"adm:svc_edit:{sid}:description", "icon": "✏️", "style": "primary"}],
        [{"label": "تعديل الأيقونة", "callback": f"adm:svc_edit:{sid}:icon",        "icon": "✏️", "style": "primary"}],
        [{"label": "تعديل الترتيب",  "callback": f"adm:svc_edit:{sid}:sort_order",  "icon": "✏️", "style": "primary"}],
        [{"label": "تعديل السعر",    "callback": f"adm:svc_edit:{sid}:price",       "icon": "💠", "style": "success"}],
        [{"label": "تبديل مجاني/مدفوع", "callback": f"adm:svc_free_toggle:{sid}", "icon": "🔁", "style": "primary"}],
        [{"label": toggle_label, "callback": f"adm:svc_toggle:{sid}", "icon": "🔄", "style": toggle_style}],
        [{"label": "حذف", "callback": f"adm:svc_del:{sid}", "icon": "🗑️", "style": "danger"}],
        [{"label": "رجوع", "callback": "adm:svc:1", "icon": "◀️", "style": "primary"}],
    ]
    kb = KeyboardBuilder.simple(*rows)
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        await cb.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "adm:svc_new")
async def cb_svc_new(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    await cb.answer()
    await state.set_state(AdminStates.service_new_key)
    kb = KeyboardBuilder.simple(
        [{"label": "إلغاء", "callback": "adm:svc:1", "icon": "✖️", "style": "danger"}]
    )
    try:
        await cb.message.edit_text(
            "➕ <b>إضافة خدمة</b>\n\n"
            "أرسل <b>المفتاح</b> (بالإنجليزية، بدون مسافات).\n"
            "مثال: <code>my_service</code>",
            reply_markup=kb, parse_mode=ParseMode.HTML
        )
    except TelegramAPIError:
        pass


@router.message(StateFilter(AdminStates.service_new_key))
async def msg_svc_key(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    key = (message.text or "").strip()
    if not key or not re.match(r"^[a-z0-9_]{2,40}$", key):
        await message.answer("❌ المفتاح يجب أن يكون أحرف صغيرة/أرقام/شرطة سفلية (2-40 حرف).")
        return
    if ServiceRepo.get_by_key(key):
        await message.answer("❌ المفتاح مستخدم مسبقاً.")
        return
    await state.update_data(new_svc_key=key)
    await state.set_state(AdminStates.service_new_name)
    await message.answer(f"✅ المفتاح: <code>{key}</code>\n\nأرسل الآن <b>اسم الخدمة</b>:",
                         parse_mode=ParseMode.HTML)


@router.message(StateFilter(AdminStates.service_new_name))
async def msg_svc_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    name = (message.text or "").strip()[:60]
    if not name:
        await message.answer("❌ الاسم مطلوب.")
        return
    await state.update_data(new_svc_name=name)
    await state.set_state(AdminStates.service_new_desc)
    await message.answer("أرسل <b>الوصف</b> (أو /skip):", parse_mode=ParseMode.HTML)


@router.message(StateFilter(AdminStates.service_new_desc))
async def msg_svc_desc(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    desc = "" if (message.text or "").strip() == "/skip" else (message.text or "").strip()[:200]
    await state.update_data(new_svc_desc=desc)
    await state.set_state(AdminStates.service_new_icon)
    await message.answer("أرسل <b>الأيقونة</b> (إيموجي) أو /skip:", parse_mode=ParseMode.HTML)


@router.message(StateFilter(AdminStates.service_new_icon))
async def msg_svc_icon(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    icon = "" if (message.text or "").strip() == "/skip" else (message.text or "").strip()[:4]
    await state.update_data(new_svc_icon=icon)
    await state.set_state(AdminStates.service_new_category)
    await message.answer("أرسل <b>التصنيف</b> (مثال: tools, files) أو /skip:",
                         parse_mode=ParseMode.HTML)


@router.message(StateFilter(AdminStates.service_new_category))
async def msg_svc_cat(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    cat = "general" if (message.text or "").strip() == "/skip" else safe_slug(message.text)
    await state.update_data(new_svc_cat=cat)
    await state.set_state(AdminStates.service_new_price)
    await message.answer("أرسل <b>السعر</b> بالنقاط (0 = مجاني):", parse_mode=ParseMode.HTML)


@router.message(StateFilter(AdminStates.service_new_price))
async def msg_svc_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        price = int((message.text or "").strip())
        if price < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ أرسل رقماً ≥ 0.")
        return
    data = await state.get_data()
    await state.clear()

    is_free = 1 if price == 0 else 0
    try:
        ServiceRepo.add(
            key=data["new_svc_key"],
            name=data["new_svc_name"],
            description=data.get("new_svc_desc", ""),
            icon=data.get("new_svc_icon", ""),
            category=data.get("new_svc_cat", "general"),
            sort_order=200,
            is_free=is_free,
            price=price,
        )
        log_action(message.from_user.id, "admin_service_add", data["new_svc_key"])
        await message.answer(
            f"✅ أُضيفت الخدمة <b>{escape_html(data['new_svc_name'])}</b>.",
            parse_mode=ParseMode.HTML
        )
    except sqlite3.IntegrityError:
        await message.answer("❌ المفتاح مستخدم.")

    text, kb = build_services_admin_view(1)
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


EDITABLE_FIELDS = {
    "name":        "الاسم",
    "description": "الوصف",
    "icon":        "الأيقونة",
    "sort_order":  "الترتيب",
    "price":       "السعر",
}


@router.callback_query(F.data.startswith("adm:svc_edit:"))
async def cb_svc_edit(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    parts = cb.data.split(":")
    try:
        sid = int(parts[2])
        field = parts[3]
    except (IndexError, ValueError):
        await cb.answer("صيغة خاطئة", show_alert=True)
        return
    if field not in EDITABLE_FIELDS:
        await cb.answer("حقل غير مدعوم", show_alert=True)
        return
    await cb.answer()
    await state.set_state(AdminStates.service_edit_value)
    await state.update_data(sid=sid, field=field)
    kb = KeyboardBuilder.simple(
        [{"label": "إلغاء", "callback": f"adm:svc_view:{sid}", "icon": "✖️", "style": "danger"}]
    )
    hint = "أرسل القيمة الجديدة:"
    if field == "price":
        hint = "أرسل السعر بالنقاط (0 = مجاني):"
    elif field == "sort_order":
        hint = "أرسل رقماً للترتيب (الأصغر أولاً):"
    try:
        await cb.message.edit_text(f"✏️ تعديل <b>{EDITABLE_FIELDS[field]}</b>\n\n{hint}",
                                   reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        pass


@router.message(StateFilter(AdminStates.service_edit_value))
async def msg_svc_edit_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    sid = data.get("sid")
    field = data.get("field")
    if not isinstance(sid, int) or not field:
        await state.clear()
        return
    val = (message.text or "").strip()
    if field in ("sort_order", "price"):
        try:
            val = int(val)
            if field == "price" and val < 0:
                raise ValueError
        except ValueError:
            await message.answer("❌ أرسل رقماً صحيحاً.")
            return
        if field == "price":
            ServiceRepo.update_field(sid, "is_free", 1 if val == 0 else 0)
    if field == "icon":
        val = val[:4]
    ServiceRepo.update_field(sid, field, val)
    log_action(message.from_user.id, "admin_service_edit", f"sid={sid} {field}={val}")
    await state.clear()
    await message.answer("✅ تم التعديل.")

    s = ServiceRepo.get(sid)
    if s:
        price_str = "مجاني" if s["is_free"] else f"{s['price']} نقطة"
        text = (
            f"🧰 <b>{escape_html(s['name'])}</b>\n\n"
            f"المفتاح: <code>{s['key']}</code>\n"
            f"الوصف: {escape_html(s['description'] or '—')}\n"
            f"الأيقونة: {s['icon'] or '—'}\n"
            f"الترتيب: {s['sort_order']}\n"
            f"التسعير: {price_str}"
        )
        rows = [
            [{"label": "رجوع", "callback": f"adm:svc_view:{sid}", "icon": "◀️", "style": "primary"}],
        ]
        await message.answer(text,
                             reply_markup=KeyboardBuilder.simple(*rows),
                             parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm:svc_toggle:"))
async def cb_svc_toggle(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    try:
        sid = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("ID خاطئ", show_alert=True)
        return
    ServiceRepo.toggle(sid)
    log_action(cb.from_user.id, "admin_service_toggle", f"sid={sid}")
    await cb.answer("✅ تم التبديل")
    cb.data = f"adm:svc_view:{sid}"
    await cb_admin_service_card(cb)


@router.callback_query(F.data.startswith("adm:svc_free_toggle:"))
async def cb_svc_free_toggle(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    try:
        sid = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("ID خاطئ", show_alert=True)
        return
    s = ServiceRepo.get(sid)
    if not s:
        await cb.answer("غير موجود", show_alert=True)
        return
    new_free = 0 if s["is_free"] else 1
    ServiceRepo.update_field(sid, "is_free", new_free)
    log_action(cb.from_user.id, "admin_service_free_toggle", f"sid={sid} free={new_free}")
    await cb.answer("✅ تم التبديل")
    cb.data = f"adm:svc_view:{sid}"
    await cb_admin_service_card(cb)


@router.callback_query(F.data.startswith("adm:svc_del:"))
async def cb_svc_del(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    try:
        sid = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("ID خاطئ", show_alert=True)
        return
    s = ServiceRepo.get(sid)
    if not s:
        await cb.answer("غير موجود", show_alert=True)
        return
    kb = KeyboardBuilder.simple(
        [{"label": "تأكيد الحذف", "callback": f"adm:svc_del_ok:{sid}", "icon": "🗑️", "style": "danger"}],
        [{"label": "إلغاء", "callback": f"adm:svc_view:{sid}", "icon": "✖️", "style": "primary"}],
    )
    await cb.answer()
    try:
        await cb.message.edit_text(
            f"⚠️ هل أنت متأكد من حذف الخدمة <b>{escape_html(s['name'])}</b>؟",
            reply_markup=kb, parse_mode=ParseMode.HTML
        )
    except TelegramAPIError:
        pass


@router.callback_query(F.data.startswith("adm:svc_del_ok:"))
async def cb_svc_del_ok(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    try:
        sid = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("ID خاطئ", show_alert=True)
        return
    ServiceRepo.delete(sid)
    log_action(cb.from_user.id, "admin_service_delete", f"sid={sid}")
    await cb.answer("🗑️ تم الحذف")
    text, kb = build_services_admin_view(1)
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        pass


@router.callback_query(F.data == "adm:svc_search")
async def cb_svc_search(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    await cb.answer()
    await state.set_state(AdminStates.service_search)
    kb = KeyboardBuilder.simple(
        [{"label": "إلغاء", "callback": "adm:svc:1", "icon": "✖️", "style": "danger"}]
    )
    try:
        await cb.message.edit_text("🔍 أرسل كلمة للبحث في الخدمات:", reply_markup=kb)
    except TelegramAPIError:
        pass


@router.message(StateFilter(AdminStates.service_search))
async def msg_svc_search(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    q = (message.text or "").strip().lower()
    all_svcs = [s for s in ServiceRepo.all()
                if q in (s["name"] or "").lower() or q in (s["key"] or "").lower()]
    if not all_svcs:
        await message.answer("لا نتائج.")
        return
    rows = []
    for s in all_svcs:
        flag = "🟢" if s["is_enabled"] else "🔴"
        rows.append([{
            "label": f"{flag} {s['name']}",
            "callback": f"adm:svc_view:{s['id']}",
            "icon": s["icon"] or "•",
            "style": "primary",
        }])
    rows.append([{"label": "رجوع", "callback": "adm:svc:1", "icon": "◀️", "style": "primary"}])
    await message.answer(f"🔎 نتائج البحث ({len(all_svcs)}):",
                         reply_markup=KeyboardBuilder.simple(*rows))


# ═══════════════════════════════════════════════════════════════
# SECTION 24: ADMIN — الأدمنز
# ═══════════════════════════════════════════════════════════════
def build_admins_view() -> tuple[str, InlineKeyboardMarkup]:
    admins = AdminRepo.all()
    lines = []
    for a in admins:
        role = a["role"]
        badge = "👑" if role == "super" else "🛡️"
        lines.append(f"{badge} <code>{a['user_id']}</code> · {role}")
    text = "🛡️ <b>الأدمنز</b>\n\n" + ("\n".join(lines) or "لا يوجد")
    rows = [
        [{"label": "إضافة أدمن", "callback": "adm:admin_add", "icon": "➕", "style": "success"}],
    ]
    for a in admins:
        if a["role"] != "super":
            rows.append([{
                "label": f"إزالة {a['user_id']}",
                "callback": f"adm:admin_del:{a['user_id']}",
                "icon": "🗑️",
                "style": "danger",
            }])
    rows.append([
        {"label": "رجوع", "callback": "adm:home", "icon": "◀️", "style": "primary"},
        {"label": "الرئيسية", "callback": "nav:home", "icon": "🏠", "style": "primary"},
    ])
    return text, KeyboardBuilder.simple(*rows)


@router.callback_query(F.data == "adm:admins")
async def cb_admins(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    await cb.answer()
    text, kb = build_admins_view()
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        pass


@router.callback_query(F.data == "adm:admin_add")
async def cb_admin_add(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    await cb.answer()
    await state.set_state(AdminStates.admin_add_id)
    kb = KeyboardBuilder.simple(
        [{"label": "إلغاء", "callback": "adm:admins", "icon": "✖️", "style": "danger"}]
    )
    try:
        await cb.message.edit_text("🛡️ أرسل <b>Telegram user ID</b> للأدمن الجديد:",
                                   reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        pass


@router.message(StateFilter(AdminStates.admin_add_id))
async def msg_admin_add(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        new_id = int((message.text or "").strip())
    except ValueError:
        await message.answer("❌ أرسل رقم ID صحيح.")
        return
    if AdminRepo.is_admin(new_id):
        await message.answer("هذا المستخدم أدمن بالفعل.")
        await state.clear()
        return
    AdminRepo.add(new_id, "admin", message.from_user.id)
    log_action(message.from_user.id, "admin_add", f"uid={new_id}")
    await state.clear()
    await message.answer(f"✅ أُضيف <code>{new_id}</code> كأدمن.", parse_mode=ParseMode.HTML)
    text, kb = build_admins_view()
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@router.callback_query(F.data.startswith("adm:admin_del:"))
async def cb_admin_del(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await deny_admin(cb)
    try:
        uid = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("ID خاطئ", show_alert=True)
        return
    if uid in ADMIN_IDS:
        await cb.answer("🚫 لا يمكن إزالة أدمن أساسي.", show_alert=True)
        return
    AdminRepo.remove(uid)
    log_action(cb.from_user.id, "admin_remove", f"uid={uid}")
    await cb.answer("✅ تمت الإزالة")
    text, kb = build_admins_view()
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except TelegramAPIError:
        pass

# ═══════════════════════════════════════════════════════════════
# SECTION 25: ERROR HANDLER
# ═══════════════════════════════════════════════════════════════
from aiogram.types import ErrorEvent


@router.errors()
async def global_error_handler(event: ErrorEvent):
    log.exception("Global error: %s", event.exception)
    try:
        update = event.update
        user_id = None
        if update.message:
            user_id = update.message.from_user.id
            await update.message.answer("⚠️ حدث خطأ غير متوقع. تم تسجيله، حاول لاحقاً.")
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
            await update.callback_query.answer("⚠️ حدث خطأ، حاول لاحقاً", show_alert=True)
        LogRepo.add(user_id, "error", str(event.exception)[:500])
    except Exception:
        log.exception("Error handler failed")


# ═══════════════════════════════════════════════════════════════
# SECTION 26: HEALTH SERVER (لـ Render)
# ═══════════════════════════════════════════════════════════════
from aiohttp import web


async def start_health_server():
    async def health(request):
        return web.Response(text="المطري خدمات - Bot is running!")

    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"✅ Health server running on port {port}")


async def set_bot_commands(bot: Bot):
    cmds = [
        BotCommand(command="start", description="بدء"),
        BotCommand(command="help",  description="مساعدة"),
        BotCommand(command="admin", description="لوحة التحكم (للأدمنز)"),
    ]
    try:
        await bot.set_my_commands(cmds)
    except TelegramAPIError as e:
        log.warning("set_my_commands failed: %s", e)


# ═══════════════════════════════════════════════════════════════
# SECTION 27: MAIN
# ═══════════════════════════════════════════════════════════════
async def main():
    init_db()

    bot = Bot(token=BOT_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await start_health_server()
    await set_bot_commands(bot)

    me = await bot.get_me()
    log.info("🤖 Bot started: @%s (id=%s)", me.username, me.id)
    log.info("👥 ADMIN_IDS: %s", ADMIN_IDS)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        db.close()


# ═══════════════════════════════════════════════════════════════
# SECTION 28: CLI
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if "--test-services" in sys.argv:
        init_db()
        async def _t():
            class M:
                def __init__(self): self.log = []
                async def answer(self, *a, **k): self.log.append(("a", a, k))
                async def answer_document(self, *a, **k): self.log.append(("d", a, k))
            m = M(); await ServiceEngine.calculator(m, "12+5*3")
            print("calc:", m.log[-1])
            m = M(); await ServiceEngine.unit_conv(m, "100 km mi")
            print("unit:", m.log[-1])
            m = M(); await ServiceEngine.json_format(m, '{"a":1}')
            print("json:", m.log[-1])
        asyncio.run(_t())
        db.close()
        sys.exit(0)

    if "--test-user" in sys.argv or "--test-admin" in sys.argv:
        init_db()
        print("✅ DB ready")
        if "--test-user" in sys.argv:
            t, kb = build_services_view(1)
            print("services view:", t.replace("\n", " | ")[:80])
        if "--test-admin" in sys.argv:
            print("admin:", admin_home_text().replace("\n", " | ")[:80])
        db.close()
        sys.exit(0)

    if not BOT_TOKEN or ":" not in BOT_TOKEN:
        log.error("❌ BOT_TOKEN مفقود. ضعه في Environment Variables.")
        sys.exit(1)
    if not ADMIN_IDS:
        log.error("❌ ADMIN_IDS فارغة. ضعها في Environment Variables.")
        sys.exit(1)

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("👋 Bot stopped by user")
