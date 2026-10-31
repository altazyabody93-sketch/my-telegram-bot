# ============================================================
# HOST BOT v12.0 — نسخة كاملة
# - إيموجي معبّر لكل زر
# - شرح منسق بـ HTML (تسطير + تكبير + تمييل)
# - زر المطور داخل قسم "مساعدة"
# - دعم 20+ منصة استضافة
# - Web Dashboard مع SVG
# ============================================================

import os, sys, json, time, shutil, signal, sqlite3, subprocess
import threading, socket, re, random, zipfile, platform, urllib.request
import secrets, ast
from datetime import datetime, timedelta

import telebot
from telebot import types
from flask import Flask, render_template_string, request, Response


# ============================================================
# ضمان المكتبات
# ============================================================
def ensure_packages():
    pkgs = {"telebot": "pyTelegramBotAPI", "flask": "flask", "requests": "requests"}
    missing = []
    for imp, pip_name in pkgs.items():
        try:
            __import__(imp)
        except ImportError:
            missing.append(pip_name)
    if missing:
        print(f"[Setup] مكتبات ناقصة: {missing}")
        for pip_name in missing:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install",
                    "--no-cache-dir", "--user", pip_name], timeout=300, check=False)
            except Exception as e:
                print(f"[Setup] فشل {pip_name}: {e}")
        print("[Setup] تم")

ensure_packages()


# ============================================================
# الإعدادات
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7861926240:AAF5vQERHMOuYS2WBS2TBOXQ9TDF4Kb_Fts")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "7325566792").split(",")]
DEVELOPER_USERNAME = "E_E_72"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, "hosted_projects")
ADMIN_BACKUP_DIR = os.path.join(BASE_DIR, "admin_backups")
os.makedirs(PROJECTS_DIR, exist_ok=True)
os.makedirs(ADMIN_BACKUP_DIR, exist_ok=True)
DB_PATH = os.path.join(BASE_DIR, "host_v12.db")

RUNNING = {}
user_states = {}
START_TIME = datetime.now()
PORT_COUNTER = int(os.environ.get("PORT", 7000)) + 1
TUNNEL_URL = None
DB_LOCK = threading.RLock()


# ============================================================
# قاعدة البيانات
# ============================================================
def init_db():
    with DB_LOCK:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
            created_at TEXT, is_banned INTEGER DEFAULT 0, is_premium INTEGER DEFAULT 0,
            max_projects INTEGER DEFAULT 3, total_uploads INTEGER DEFAULT 0,
            theme_color TEXT DEFAULT 'blue')''')
        c.execute('''CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL,
            name TEXT NOT NULL, ptype TEXT DEFAULT 'bot', path TEXT, entry TEXT,
            files TEXT DEFAULT '[]', requirements TEXT DEFAULT '',
            bot_token TEXT DEFAULT '', bot_username TEXT DEFAULT '', bot_name TEXT DEFAULT '',
            port INTEGER DEFAULT 0, public_url TEXT DEFAULT '', installed INTEGER DEFAULT 0,
            pid INTEGER DEFAULT 0, status TEXT DEFAULT 'stopped', created_at TEXT,
            last_start TEXT DEFAULT '', last_stop TEXT DEFAULT '',
            FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE)''')
        c.execute('''CREATE TABLE IF NOT EXISTS ui_settings (key TEXT PRIMARY KEY, value TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT,
            details TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS dashboard_tokens (
            token TEXT PRIMARY KEY, user_id INTEGER, created_at TEXT)''')
        conn.commit()
        conn.close()

init_db()


def _conn():
    return sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)


# ============================================================
# المستخدمين
# ============================================================
def get_user(uid):
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
        r = c.fetchone(); conn.close(); return r

def add_user(uid, username="", first_name=""):
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        try:
            c.execute("INSERT INTO users (user_id, username, first_name, created_at) VALUES (?, ?, ?, ?)",
                (uid, username, first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit(); return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

def get_all_users():
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE is_banned=0")
        r = [x[0] for x in c.fetchall()]; conn.close(); return r

def get_user_count():
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        r = c.fetchone()[0]; conn.close(); return r

def get_all_users_full():
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("SELECT * FROM users ORDER BY created_at DESC")
        r = c.fetchall(); conn.close(); return r

def ban_user(uid):
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))
        conn.commit(); conn.close()

def unban_user(uid):
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))
        conn.commit(); conn.close()

def set_user_theme(uid, color):
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("UPDATE users SET theme_color=? WHERE user_id=?", (color, uid))
        conn.commit(); conn.close()

def is_banned(uid):
    u = get_user(uid); return u and u[4] == 1

def is_premium(uid):
    u = get_user(uid); return u and u[5] == 1

def get_max_projects(uid):
    u = get_user(uid)
    if not u: return 3
    return u[6] or 3


# ============================================================
# المشاريع
# ============================================================
def get_projects_by_owner(owner_id):
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("SELECT * FROM projects WHERE owner_id=? ORDER BY id DESC", (owner_id,))
        r = c.fetchall(); conn.close(); return r

def get_project(pid):
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("SELECT * FROM projects WHERE id=?", (pid,))
        r = c.fetchone(); conn.close(); return r

def get_all_projects():
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("SELECT * FROM projects ORDER BY id DESC")
        r = c.fetchall(); conn.close(); return r

def add_project(owner_id, name, ptype, path, entry):
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("""INSERT INTO projects (owner_id, name, ptype, path, entry, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (owner_id, name, ptype, path, entry, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        pid = c.lastrowid; conn.commit(); conn.close(); return pid

def update_project(project_id, **kw):
    if not kw: return
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        for k, v in kw.items():
            c.execute(f"UPDATE projects SET {k}=? WHERE id=?", (v, project_id))
        conn.commit(); conn.close()

def delete_project(pid):
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("DELETE FROM projects WHERE id=?", (pid,))
        conn.commit(); conn.close()

def count_user_projects(uid):
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM projects WHERE owner_id=?", (uid,))
        r = c.fetchone()[0]; conn.close(); return r


# ============================================================
# إعدادات الواجهة + الأزرار (بإيموجي معبّر)
# ============================================================
DEFAULT_UI = {
    "welcome_text": "اهلا بك في Host Bot v12",
    "dashboard_title": "HOST BOT v12",
    "footer_text": "━━━━━━━━━━━━━━━━━━━━",
    "theme_color": "#2563eb",
}

# key: (الاسم+الإيموجي, اللون, الصف)
DEFAULT_BUTTONS = {
    "btn_my_projects":  ("📦 مشاريعي", "primary", 1),
    "btn_new_project":  ("➕ مشروع جديد", "success", 1),
    "btn_account":      ("👤 حسابي", "primary", 2),
    "btn_help":         ("❓ مساعدة", "primary", 2),
    "btn_support":      ("💬 تواصل مع الدعم", "primary", 3),
    "btn_admin":        ("👑 لوحة المطور", "danger", 4),
    "btn_dashboard":    ("🌐 لوحة التحكم", "primary", 0),
}


def get_button(key):
    try:
        with DB_LOCK:
            conn = _conn(); c = conn.cursor()
            c.execute("SELECT value FROM ui_settings WHERE key=?", (f"cfg_{key}",))
            r = c.fetchone(); conn.close()
            if r and r[0]:
                parts = r[0].split("|")
                if len(parts) == 3:
                    return (parts[0], parts[1], int(parts[2]))
    except: pass
    return DEFAULT_BUTTONS.get(key, (key, "primary", 0))


def set_button(key, name, style, row):
    set_ui(f"cfg_{key}", f"{name}|{style}|{row}")


def get_all_buttons():
    return {k: get_button(k) for k in DEFAULT_BUTTONS.keys()}


def get_ui(key):
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("SELECT value FROM ui_settings WHERE key=?", (key,))
        r = c.fetchone(); conn.close()
        return r[0] if r else DEFAULT_UI.get(key, "")


def set_ui(key, value):
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("REPLACE INTO ui_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit(); conn.close()


def get_all_ui():
    result = dict(DEFAULT_UI)
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("SELECT key, value FROM ui_settings")
        for k, v in c.fetchall():
            result[k] = v
        conn.close()
    return result


# ============================================================
# سجل الأحداث
# ============================================================
def log_action(user_id, action, details=""):
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("INSERT INTO action_logs (user_id, action, details, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, action, details, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit(); conn.close()


# ============================================================
# Utilities
# ============================================================
def get_file_size_str(fp):
    try:
        size = os.path.getsize(fp)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024: return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except: return "?"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except: return "127.0.0.1"

def get_public_url():
    global TUNNEL_URL
    if TUNNEL_URL: return TUNNEL_URL
    platforms = [
        ("RENDER_EXTERNAL_URL", "{}"), ("RAILWAY_PUBLIC_DOMAIN", "https://{}"),
        ("KOYEB_PUBLIC_DOMAIN", "https://{}"), ("FLY_APP_NAME", "https://{}.fly.dev"),
        ("HEROKU_APP_NAME", "https://{}.herokuapp.com"), ("VERCEL_URL", "https://{}"),
        ("NETLIFY_URL", "https://{}"), ("RENDER_EXTERNAL_HOSTNAME", "https://{}"),
        ("CYCLIC_URL", "https://{}"), ("GLITCH_PROJECT_DOMAIN", "https://{}"),
        ("REPLIT_DEV_DOMAIN", "https://{}"), ("NORTHFLANK_URL", "https://{}"),
        ("ADAPTABLE_URL", "https://{}"), ("FL0_DOMAIN", "https://{}"),
        ("PUBLIC_URL", "{}"), ("APP_URL", "{}"), ("SERVER_DOMAIN", "https://{}"),
    ]
    for env_key, fmt in platforms:
        v = os.environ.get(env_key)
        if v:
            TUNNEL_URL = fmt.format(v.rstrip("/"))
            return TUNNEL_URL
    try:
        with DB_LOCK:
            conn = _conn(); c = conn.cursor()
            c.execute("SELECT value FROM ui_settings WHERE key='public_url'")
            r = c.fetchone(); conn.close()
            if r and r[0]: TUNNEL_URL = r[0]; return r[0]
    except: pass
    port = int(os.environ.get("PORT", 8080))
    return f"http://{get_local_ip()}:{port}"

def calc_uptime(start_str):
    if not start_str: return "—"
    try:
        s = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
        t = int((datetime.now() - s).total_seconds())
        if t < 0: t = 0
        h, m, sec = t // 3600, (t % 3600) // 60, t % 60
        return f"{h:02d}:{m:02d}:{sec:02d}"
    except: return "—"

def get_free_port():
    global PORT_COUNTER
    while PORT_COUNTER < 65000:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("0.0.0.0", PORT_COUNTER)); s.close()
            p = PORT_COUNTER; PORT_COUNTER += 1; return p
        except:
            PORT_COUNTER += 1
        finally:
            try: s.close()
            except: pass
    return 7500

def list_dir_files(dirpath):
    result = []
    if not os.path.exists(dirpath): return result
    for root, dirs, files in os.walk(dirpath):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, dirpath)
            result.append(rel)
    return result


# ============================================================
# الأزرار
# ============================================================
def btn(text, cb=None, url=None, style=None):
    b = types.InlineKeyboardButton(text=text, callback_data=cb, url=url)
    if style:
        try: b.style = style
        except: pass
    return b

def btn_green(t, cb=None, url=None): return btn(t, cb=cb, url=url, style="success")
def btn_red(t, cb=None, url=None): return btn(t, cb=cb, url=url, style="danger")
def btn_blue(t, cb=None, url=None): return btn(t, cb=cb, url=url, style="primary")
def btn_gray(t, cb=None, url=None): return btn(t, cb=cb, url=url)

def make_custom_btn(key, cb=None, url=None):
    name, style, _ = get_button(key)
    return btn(name, cb=cb, url=url, style=style if style else None)


# ============================================================
# الزخرفة
# ============================================================
def make_header(title):
    return "━━━━━━━━━━━━━━━━━━━━━━━━━\n" + f"  <b>{title}</b>\n" + "━━━━━━━━━━━━━━━━━━━━━━━━━"

def make_section(title): return f"\n<b>{title}</b>\n"
def make_footer(): return "━━━━━━━━━━━━━━━━━━━━━━━━━"


# ============================================================
# الفحص القوي (AST)
# ============================================================
def analyze_python_file(fp):
    issues = {"syntax": [], "imports": [], "warnings": [], "info": [], "stats": {}}
    try:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()
        lines = src.splitlines()
        issues["stats"]["total_lines"] = len(lines)
        issues["stats"]["size"] = os.path.getsize(fp)
        try:
            tree = ast.parse(src)
            issues["info"].append("الصيغة سليمة")
        except SyntaxError as e:
            issues["syntax"].append({"line": e.lineno, "col": e.offset, "msg": e.msg, "text": (e.text or "").strip()})
            return issues
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names: imports.add(n.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module: imports.add(node.module.split('.')[0])
        issues["stats"]["imports"] = sorted(imports)
        known_libs = {"telebot":"pyTelegramBotAPI","requests":"requests","flask":"flask",
            "httpx":"httpx","bs4":"beautifulsoup4","aiohttp":"aiohttp","PIL":"Pillow",
            "pandas":"pandas","numpy":"numpy","sqlalchemy":"SQLAlchemy","pydantic":"pydantic",
            "fastapi":"fastapi","uvicorn":"uvicorn","dotenv":"python-dotenv","yaml":"pyyaml",
            "bcrypt":"bcrypt","gunicorn":"gunicorn"}
        required = set()
        for imp in imports:
            if imp in known_libs: required.add(known_libs[imp])
        issues["stats"]["required_libs"] = sorted(required)
        for i, line in enumerate(lines, 1):
            if len(line) > 120: issues["warnings"].append(f"السطر {i} طويل ({len(line)} حرف)")
        token_found = False
        for line in lines:
            if re.search(r'BOT_TOKEN\s*=\s*["\']([0-9]{8,12}:[A-Za-z0-9_-]{30,50})["\']', line):
                token_found = True; break
        if token_found: issues["info"].append("يوجد BOT_TOKEN")
        else: issues["warnings"].append("لا يوجد BOT_TOKEN ظاهر")
        issues["stats"]["functions"] = sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
        issues["stats"]["classes"] = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
    except Exception as e:
        issues["syntax"].append({"line": 0, "col": 0, "msg": str(e), "text": ""})
    return issues


def format_check_result(fp, issues):
    name = os.path.basename(fp)
    lines = [make_header(f"🔍 فحص {name}"), ""]
    stats = issues.get("stats", {})
    lines.append("<b><u>📊 الاحصائيات:</u></b>")
    lines.append(f"  📏 السطور: <code>{stats.get('total_lines', 0)}</code>")
    lines.append(f"  📦 الحجم: <code>{get_file_size_str(fp)}</code>")
    lines.append(f"  🔧 الدوال: <code>{stats.get('functions', 0)}</code>")
    lines.append(f"  📚 الكلاسات: <code>{stats.get('classes', 0)}</code>")
    lines.append("")
    syntax = issues.get("syntax", [])
    if syntax:
        lines.append("<b><u>❌ اخطاء الصيغة:</u></b>")
        for s in syntax:
            lines.append(f"  📍 السطر {s['line']}: <code>{s['msg']}</code>")
            if s['text']: lines.append(f"  <code>{s['text'][:60]}</code>")
        lines.append("")
    else:
        lines.append("<b><u>✅ الصيغة سليمة</u></b>"); lines.append("")
    imports = stats.get("imports", [])
    if imports:
        lines.append("<b><u>📚 الاستيرادات:</u></b>")
        for imp in imports[:15]: lines.append(f"  • <code>{imp}</code>")
        if len(imports) > 15: lines.append(f"  ... +{len(imports) - 15}")
        lines.append("")
    required = stats.get("required_libs", [])
    if required:
        lines.append("<b><u>📦 المكتبات المطلوبة:</u></b>")
        for lib in required: lines.append(f"  • <code>{lib}</code>")
        lines.append("")
    warnings = issues.get("warnings", [])
    if warnings:
        lines.append("<b><u>⚠️ تنبيهات:</u></b>")
        for w in warnings[:10]: lines.append(f"  • {w}")
        lines.append("")
    info = issues.get("info", [])
    if info:
        lines.append("<b><u>ℹ️ معلومات:</u></b>")
        for i in info: lines.append(f"  • {i}")
    return "\n".join(lines)


def check_python_file(fp):
    issues = analyze_python_file(fp)
    result = format_check_result(fp, issues)
    ok = not issues["syntax"]
    return ok, result


def check_json_file(fp):
    try:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
        if isinstance(data, dict): count, type_name = len(data), "كائن"
        elif isinstance(data, list): count, type_name = len(data), "قائمة"
        else: count, type_name = 0, type(data).__name__
        return True, f"<b>✅ JSON سليم</b>\n\n<code>{os.path.basename(fp)}</code>\n📦 الحجم: <code>{get_file_size_str(fp)}</code>\n🔤 النوع: <code>{type_name}</code>\n🔑 عدد العناصر: <code>{count}</code>"
    except json.JSONDecodeError as e:
        return False, f"<b>❌ خطأ JSON</b>\n📍 السطر: <b>{e.lineno}</b>\n🔤 <code>{e.msg}</code>"
    except Exception as e:
        return False, f"❌ خطأ: {e}"


def check_shell_file(fp):
    try:
        r = subprocess.run(["bash", "-n", fp], capture_output=True, text=True, timeout=10)
        if r.returncode == 0: return True, f"<b>✅ Shell سليم</b>\n📄 <code>{os.path.basename(fp)}</code>"
        return False, f"<b>❌ خطأ Shell</b>\n<pre>{r.stderr[-400:]}</pre>"
    except FileNotFoundError: return True, "ℹ️ Shell: تم التخطي"
    except Exception as e: return False, f"❌ خطأ: {e}"


def check_requirements_file(fp):
    try:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
        if not lines: return False, "<b>⚠️ الملف فاضي</b>"
        result = f"<b>✅ requirements.txt سليم</b>\n\n📦 <b>العدد:</b> <code>{len(lines)}</code>\n\n"
        for line in lines[:30]:
            pkg_name = re.split(r'[=<>!]', line)[0].strip()
            result += f"  • <code>{pkg_name}</code>\n"
        if len(lines) > 30: result += f"  ... +{len(lines) - 30}\n"
        return True, result
    except Exception as e: return False, f"❌ خطأ: {e}"


def check_any_file(fp):
    if not os.path.exists(fp): return False, "<b>❌ الملف غير موجود</b>"
    name = os.path.basename(fp).lower()
    if name == "requirements.txt": return check_requirements_file(fp)
    elif name.endswith(".py"): return check_python_file(fp)
    elif name.endswith(".json"): return check_json_file(fp)
    elif name.endswith(".sh"): return check_shell_file(fp)
    elif name.endswith(".txt"): return check_requirements_file(fp)
    else:
        size = get_file_size_str(fp)
        return True, f"<b>✅ مدعوم</b>\n📄 <code>{name}</code> ({size})"


# ============================================================
# استخراج معلومات البوت
# ============================================================
def extract_bot_info(fp):
    info = {"token": None, "username": None, "name": None}
    try:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        patterns = [
            r'BOT_TOKEN\s*=\s*["\']([0-9]{8,12}:[A-Za-z0-9_-]{30,50})["\']',
            r'BOT_TOKEN\s*:\s*["\']([0-9]{8,12}:[A-Za-z0-9_-]{30,50})["\']',
            r'["\']BOT_TOKEN["\']\s*:\s*["\']([0-9]{8,12}:[A-Za-z0-9_-]{30,50})["\']',
            r'bot_token\s*=\s*["\']([0-9]{8,12}:[A-Za-z0-9_-]{30,50})["\']',
        ]
        for p in patterns:
            m = re.search(p, content)
            if m:
                info["token"] = m.group(1)
                break
        if not info["token"]: return info
        try:
            import requests as req
            r = req.get(f"https://api.telegram.org/bot{info['token']}/getMe", timeout=10)
            if r.status_code == 200:
                d = r.json()
                if d.get("ok"):
                    info["username"] = d["result"].get("username")
                    info["name"] = d["result"].get("first_name")
                else: info["token"] = None
            else: info["token"] = None
        except: info["token"] = None
    except: pass
    return info


# ============================================================
# إدارة ملفات المشروع
# ============================================================
def get_project_files(pid):
    p = get_project(pid)
    if not p: return []
    try: return json.loads(p[6] or "[]")
    except: return []

def add_project_file(pid, filename):
    files = get_project_files(pid)
    if filename not in files: files.append(filename)
    update_project(pid, files=json.dumps(files))


# ============================================================
# جلسات آمنة
# ============================================================
def create_dashboard_token(uid):
    token = secrets.token_urlsafe(32)
    with DB_LOCK:
        conn = _conn(); c = conn.cursor()
        c.execute("DELETE FROM dashboard_tokens WHERE user_id=?", (uid,))
        c.execute("INSERT INTO dashboard_tokens (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, uid, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit(); conn.close()
    return token

def get_dashboard_user(token):
    if not token: return None
    try:
        with DB_LOCK:
            conn = _conn(); c = conn.cursor()
            c.execute("SELECT user_id FROM dashboard_tokens WHERE token=?", (token,))
            r = c.fetchone(); conn.close()
            return r[0] if r else None
    except: return None

def get_dashboard_link(uid):
    token = create_dashboard_token(uid)
    base = get_public_url()
    return f"{base}/?token={token}"
    
# ============================================================
# تشغيل / إيقاف المشاريع
# ============================================================
def start_project(pid):
    p = get_project(pid)
    if not p:
        return False, "المشروع غير موجود", None

    key = "p" + str(pid)
    if key in RUNNING and RUNNING[key].poll() is None:
        return False, "المشروع شغال بالفعل", None

    entry_path = os.path.join(p[4], p[5])
    if not os.path.exists(entry_path):
        return False, "الملف " + str(p[5]) + " غير موجود", None

    try:
        env = os.environ.copy()
        port = 0
        public_url = ""

        if p[3] == "web":
            port = get_free_port()
            env["PORT"] = str(port)
            env["FLASK_RUN_PORT"] = str(port)
            env["HOST"] = "0.0.0.0"
            base = get_public_url()
            public_url = base + "/proxy/" + str(pid)

        log_path = os.path.join(p[4], "output.log")
        lf = open(log_path, "a", encoding="utf-8")
        lf.write("\n\n===== START " + str(datetime.now()) + " =====\n")
        lf.flush()

        cmd = [sys.executable, "-u", p[5]] if p[5].endswith(".py") else ["bash", p[5]]
        kw = {"preexec_fn": os.setsid} if os.name != "nt" else {}

        proc = subprocess.Popen(
            cmd, cwd=p[4], stdout=lf, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, env=env, **kw
        )
        RUNNING[key] = proc

        update_project(
            pid, pid=proc.pid, status="running", port=port,
            public_url=public_url,
            last_start=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        time.sleep(5)

        if proc.poll() is not None:
            update_project(pid, status="stopped", pid=0)
            return False, "المشروع توقف فوراً. تحقق من السجلات.", None

        info = {
            "project": p[2],
            "entry": p[5],
            "ptype": p[3],
            "pid": proc.pid,
            "port": port,
            "public_url": public_url,
            "bot_username": p[9] or "",
            "bot_name": p[10] or "", 
        }
        return True, "تم التشغيل", info

    except Exception as e:
        return False, "خطأ: " + str(e)[:300], None

def stop_project(pid):
    p = get_project(pid)
    if not p:
        return False, "المشروع غير موجود"

    key = f"p{pid}"
    stopped = False

    if key in RUNNING:
        proc = RUNNING[key]
        try:
            if os.name != "nt":
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            else:
                proc.terminate()
            proc.wait(timeout=5)
            stopped = True
        except:
            try:
                proc.kill()
                stopped = True
            except:
                pass
        RUNNING.pop(key, None)

    if p[14]:
        try:
            os.kill(p[14], signal.SIGTERM)
            stopped = True
        except:
            pass

    update_project(
        pid, pid=0, status="stopped",
        last_stop=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    return True, "تم الإيقاف" if stopped else "كان متوقف"


def is_running(pid):
    key = f"p{pid}"
    if key in RUNNING:
        p = RUNNING[key]
        if p.poll() is None:
            return True
        RUNNING.pop(key, None)
        update_project(pid, pid=0, status="stopped")
    return False


def get_logs(pid, n=100):
    p = get_project(pid)
    if not p:
        return "المشروع غير موجود"

    lp = os.path.join(p[4], "output.log")
    if not os.path.exists(lp):
        return "لا توجد سجلات بعد"

    try:
        with open(lp, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            return "".join(lines[-n:])
    except Exception as e:
        return f"خطأ: {e}"


def get_live_uptime(pid):
    p = get_project(pid)
    if not p:
        return "—"
    if not is_running(pid):
        return "متوقف"
    return calc_uptime(p[16])


# ============================================================
# تثبيت المكتبات
# ============================================================
def install_single_pkg(pid, pkg):
    pkg = pkg.strip()
    if not pkg:
        return False, "اسم المكتبة فاضي"

    pkg_name = re.split(r'[=<>!;]', pkg)[0].strip()
    if not pkg_name:
        return False, f"اسم غير صالح: {pkg}"

    try:
        cmd = [
            sys.executable, "-m", "pip", "install",
            "--no-cache-dir", "--disable-pip-version-check",
            "--user", pkg
        ]

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, preexec_fn=os.setsid if os.name != "nt" else None
        )

        try:
            out, _ = proc.communicate(timeout=300)

            if proc.returncode == 0:
                ver_match = re.search(
                    rf'Successfully installed .*?{re.escape(pkg_name)}[- ](\S+)',
                    out or ""
                )
                if ver_match:
                    return True, f"<code>{pkg_name}</code> v{ver_match.group(1)}"
                return True, f"<code>{pkg_name}</code>"

            else:
                err_lines = [l for l in (out or "").splitlines() if "ERROR" in l.upper()]
                err = err_lines[-1] if err_lines else (out or "")[-200:]
                return False, f"<code>{pkg_name}</code>\n<code>{err[:200]}</code>"

        except subprocess.TimeoutExpired:
            try:
                if os.name != "nt":
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                else:
                    proc.kill()
            except:
                pass
            return False, f"<code>{pkg_name}</code> - انتهت المهلة"

    except Exception as e:
        return False, f"<code>{pkg_name}</code>\n<code>{str(e)[:120]}</code>"


def install_from_requirements(pid, reqs):
    lines = [
        l.strip() for l in (reqs or "").split("\n")
        if l.strip() and not l.startswith("#")
    ]
    if not lines:
        return False, "لا توجد مكتبات", []

    results = []
    success = 0
    fail = 0

    for i, pkg in enumerate(lines, 1):
        ok, msg = install_single_pkg(pid, pkg)
        if ok:
            success += 1
        else:
            fail += 1
        results.append((i, len(lines), pkg, ok, msg))

    return True, f"نجح {success} / فشل {fail}", results


# ============================================================
# الالوان
# ============================================================
COLOR_OPTIONS = [
    ("green", "🟢 اخضر", "success"),
    ("red", "🔴 احمر", "danger"),
    ("blue", "🔵 ازرق", "primary"),
    ("gray", "⚫ رمادي", None),
]


def get_user_theme(uid):
    u = get_user(uid)
    if not u or len(u) < 9:
        return "blue"
    return u[8] or "blue"


def make_color_keyboard(current="blue"):
    m = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for color_key, label, style in COLOR_OPTIONS:
        mark = "✅ " if color_key == current else ""
        btns.append(btn(f"{mark}{label}", f"set_theme_{color_key}",
                       style=style if style else None))
    m.row(*btns[:2])
    m.row(*btns[2:4])
    return m


# ============================================================
# رسالة نجاح احترافية
# ============================================================
def make_success_message(info):
    ptype = info.get("ptype", "bot")
    icon = "🐍 بوت" if ptype == "bot" else "🌐 موقع"

    txt = "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    txt += "  <b>🎉 تم التشغيل بنجاح</b>\n"
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    txt += f"📦 <b>المشروع:</b> <code>{info['project']}</code>\n"
    txt += f"🏷️ <b>النوع:</b> {icon}\n"
    txt += f"📄 <b>الملف:</b> <code>{info['entry']}</code>\n"
    txt += f"🆔 <b>PID:</b> <code>{info['pid']}</code>\n"
    txt += f"⏱️ <b>بدأ في:</b> <code>{datetime.now().strftime('%H:%M:%S')}</code>\n"

    if ptype == "web" and info.get("public_url"):
        txt += f"\n🔗 <b>الرابط:</b>\n<code>{info['public_url']}</code>\n"

    bot_user = info.get("bot_username", "")
    if bot_user:
        txt += f"\n🤖 <b>يوزر البوت:</b> @{bot_user}\n"
        txt += f"👤 <b>اسم البوت:</b> {info.get('bot_name', '—')}\n"

    txt += f"\n⏱️ <b>العداد:</b> <code>00:00:00</code>\n"

    txt += "\n" + "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    txt += "<b>✅ البوت شغال حاليا</b>"

    return txt


# ============================================================
# Heartbeat
# ============================================================
def keep_alive():
    while True:
        time.sleep(30)
        try:
            running_count = sum(
                1 for p in get_all_projects() if is_running(p[0])
            )
            print(
                f"[Heartbeat] {datetime.now().strftime('%H:%M:%S')} | "
                f"running={running_count} | tunnel={TUNNEL_URL or 'none'}"
            )
        except:
            pass
            
# ============================================================
# البوت
# ============================================================
bot = telebot.TeleBot(BOT_TOKEN)


# ============================================================
# الصلاحيات
# ============================================================
def is_admin(uid):
    return uid in ADMIN_IDS


def can_access_project(project, uid):
    if not project:
        return False
    return project[1] == uid or is_admin(uid)


def check_user_limit(uid):
    count = count_user_projects(uid)
    limit = get_max_projects(uid)
    return count < limit, count, limit


# ============================================================
# القائمة الرئيسية
# ============================================================
def main_menu(uid):
    m = types.InlineKeyboardMarkup(row_width=2)

    # زر لوحة التحكم
    dashboard_url = get_dashboard_link(uid)
    if dashboard_url.startswith("https://"):
        try:
            b = types.InlineKeyboardButton("🌐 لوحة التحكم", web_app=types.WebAppInfo(url=dashboard_url))
            b.style = "primary"
            m.add(b)
        except:
            m.add(btn("🌐 لوحة التحكم", url=dashboard_url, style="primary"))
    else:
        m.add(btn("🌐 لوحة التحكم", url=dashboard_url, style="primary"))

    # الأزرار الأساسية
    m.row(btn("📦 مشاريعي", "my_projs", style="primary"))
    m.row(btn("➕ رفع مشروع جديد", "new_proj", style="success"))
    m.row(btn("👤 حسابي", "my_account", style="primary"), btn("📚 مساعدة", "help", style="primary"))
    m.row(btn("💬 تواصل مع الدعم", "contact_support", style="danger"))

    # زر لوحة المطور
    if is_admin(uid):
        m.add(btn("👑 لوحة المطور", "admin_panel", style="danger"))

    return m

# ============================================================
# /start
# ============================================================

@bot.message_handler(commands=['start'])
def cmd_start(msg):
    uid = msg.from_user.id

    if is_banned(uid):
        bot.send_message(msg.chat.id, "🚫 انت محظور من استخدام البوت",
                        parse_mode="HTML")
        return

    if not get_user(uid):
        add_user(uid, msg.from_user.username or "",
                msg.from_user.first_name or "")
        log_action(uid, "register")

    name = msg.from_user.first_name or "صديقي"
    ui = get_all_ui()

    txt = (
        "🚀 <b>HOST BOT v12</b>" + chr(10) + chr(10) +
        f"👋 أهلاً <b>{name}</b>" + chr(10) + chr(10) +
        "━━━━━━━━━━━━━━━━━" + chr(10) +
        "📌 <b>كيف تستخدم البوت؟</b>" + chr(10) +
        "━━━━━━━━━━━━━━━━━" + chr(10) +
        "1️⃣ اضغط (➕ رفع مشروع جديد)" + chr(10) +
        "2️⃣ اختر النوع (بوت/موقع)" + chr(10) +
        "3️⃣ أرسل اسم المشروع" + chr(10) +
        "4️⃣ أرسل ملف الكود" + chr(10) +
        "5️⃣ أرسل requirements.txt (اختياري)" + chr(10) +
        "6️⃣ ثبّت المكتبات" + chr(10) +
        "7️⃣ اضغط تشغيل!" + chr(10) + chr(10) +
        "━━━━━━━━━━━━━━━━━" + chr(10) +
        "🎯 <b>اختر من القائمة أدناه:</b>"
    )

    bot.send_message(msg.chat.id, txt, parse_mode="HTML",
                    reply_markup=main_menu(uid))
    
    # تنبيه ترحيبي
    try:
        bot.answer_callback_query(msg.chat.id, "👋 أهلاً بك! اختر من القائمة أدناه.")
    except: pass


@bot.callback_query_handler(func=lambda c: c.data == "main_menu")
def cb_main(call):
    try:
        bot.edit_message_text(
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n  <b>🏠 القائمة الرئيسية</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━",
            call.message.chat.id, call.message.message_id,
            reply_markup=main_menu(call.from_user.id),
            parse_mode="HTML"
        )
    except:
        bot.send_message(call.message.chat.id, "🏠 القائمة الرئيسية",
                        reply_markup=main_menu(call.from_user.id))


# ============================================================
# مشاريعي
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "my_projs")
def cb_my_projs(call):
    uid = call.from_user.id
    projs = get_projects_by_owner(uid)

    if not projs:
        bot.answer_callback_query(call.id, "لا توجد مشاريع بعد.")
        return

    txt = "━━━━━━━━━━━━━━━━━━━━━━━━━" + chr(10)
    txt += "  <b>📦 مشاريعي</b>" + chr(10)
    txt += "━━━━━━━━━━━━━━━━━━━━━━━━━" + chr(10) + chr(10)
    txt += f"👤 <b>المستخدم:</b> <code>{uid}</code>" + chr(10)
    txt += f"📊 <b>عدد المشاريع:</b> <code>{len(projs)}</code>" + chr(10) + chr(10)

    m = types.InlineKeyboardMarkup(row_width=1)

    for p in projs:
        pid = p[0]
        running = is_running(pid)
        icon = "🐍" if p[3] == "bot" else "🌐"
        status = "🟢 شغال" if running else "🔴 متوقف"
        
        # الزر الجديد النظيف
        label = f"{icon} {p[2]} | {status}"
        style = "success" if running else "danger"
        m.add(btn(label, f"myproj_{pid}", style=style))

    m.add(btn_green("➕ مشروع جديد", "new_proj"))
    m.add(btn_gray("🔙 رجوع", "main_menu"))

    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("proj_"))
def cb_proj(call):
    uid = call.from_user.id
    try:
        pid = int(call.data[5:])
    except:
        return

    p = get_project(pid)
    if not p:
        bot.answer_callback_query(call.id, "❌ المشروع غير موجود", show_alert=True)
        return

    if not can_access_project(p, uid):
        bot.answer_callback_query(call.id, "🚫 غير مصرح", show_alert=True)
        log_action(uid, "unauthorized_access", f"project={pid}")
        return

    running = is_running(pid)
    up = calc_uptime(p[16]) if running else "—"
    icon = "🐍 بوت" if p[3] == "bot" else "🌐 موقع"
    files = get_project_files(pid)
    
    # تنبيه عند فتح المشروع
    bot.answer_callback_query(call.id, f"حالة المشروع: {'شغال' if running else 'متوقف'}")

    txt = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  <b>{p[2]}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷️ <b>النوع:</b> {icon}\n"
        f"📄 <b>الملف:</b> <code>{p[5]}</code>\n"
        f"📁 <b>الملفات:</b> <code>{len(files)}</code>\n"
        f"📊 <b>الحالة:</b> {'🟢 شغال' if running else '🔴 متوقف'}\n"
        f"⏱️ <b>المدة:</b> <code>{up}</code>\n"
        f"🆔 <b>PID:</b> <code>{p[14] or '—'}</code>\n"
    )

    if p[3] == "web" and p[12]:
        txt += f"\n🔗 <b>الرابط:</b>\n<code>{p[12]}</code>\n"

    m = types.InlineKeyboardMarkup(row_width=2)

    if running:
        m.row(btn_red("⏹️ ايقاف", f"stop_{pid}"), btn_blue("📄 السجلات", f"logs_{pid}"))
    else:
        m.row(btn_green("▶️ تشغيل", f"start_{pid}"), btn_blue("📄 السجلات", f"logs_{pid}"))

    if p[3] == "web" and p[12]:
        m.row(btn_blue("🌐 فتح الموقع", f"openweb_{pid}"))

    if p[9]:
        m.row(btn_blue("🤖 فتح البوت", url=f"https://t.me/{p[9]}"))

    m.row(btn_blue("📁 الملفات", f"files_{pid}"), btn_blue("➕ اضافة ملف", f"addfile_{pid}"))
    m.row(btn_green("📄 السجلات", f"logs_{pid}", style="primary"), btn_blue("✏️ تعديل الملف", f"editfile_{pid}", style="primary"))
    m.row(btn_green("📄 السجلات", f"logs_{pid}", style="primary"), btn_blue("✏️ تعديل الملف", f"editfile_{pid}", style="primary"))
    m.row(btn_blue("🔍 فحص", f"check_{pid}"), btn_blue("⚙️ مكتبة", f"addpkg_{pid}"))
    m.add(btn_red("🗑️ حذف", f"del_{pid}"))
    m.add(btn_gray("🔙 رجوع", "my_projs"))

    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
                             reply_markup=m, parse_mode="HTML")
    except:
        pass


# ============================================================
# تشغيل
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("start_"))
def cb_start(call):
    uid = call.from_user.id
    try:
        pid = int(call.data[6:])
    except:
        return

    p = get_project(pid)
    if not p or not can_access_project(p, uid):
        bot.answer_callback_query(call.id, "🚫 غير مصرح", show_alert=True)
        return

    bot.answer_callback_query(call.id, "⏳ جاري تشغيل المشروع...")
    msg = bot.send_message(call.message.chat.id, "⏳ جاري التجهيز...",
                          parse_mode="HTML")

    def do_start():
        for i in range(5, 0, -1):
            try:
                bar = "█" * (5 - i) + "░" * i
                bot.edit_message_text(
                    f"⏳ <b>جاري التجهيز...</b>\n\n"
                    f"⏱️ يبدا خلال: {i} ثانية\n\n{bar}",
                    msg.chat.id, msg.message_id, parse_mode="HTML"
                )
            except:
                pass
            time.sleep(1)

        ok, m, info = start_project(pid)

        if ok and info:
            text = make_success_message(info)

            markup = types.InlineKeyboardMarkup(row_width=1)
            if info.get("bot_username"):
                markup.add(btn_blue("🤖 فتح البوت",
                                   url=f"https://t.me/{info['bot_username']}"))
            if info.get("public_url"):
                markup.add(btn_blue("🌐 فتح الموقع", url=info["public_url"]))
            markup.row(
                btn_blue("📄 السجلات", f"logs_{pid}"),
                btn_gray("🔙 رجوع", f"proj_{pid}")
            )

            bot.edit_message_text(text, msg.chat.id, msg.message_id,
                                 reply_markup=markup, parse_mode="HTML")
        else:
            bot.edit_message_text(
                f"<b>❌ فشل التشغيل</b>\n\n{m}",
                msg.chat.id, msg.message_id, parse_mode="HTML"
            )

    threading.Thread(target=do_start, daemon=True).start()


# ============================================================
# ايقاف
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("stop_"))
def cb_stop(call):
    uid = call.from_user.id
    try:
        pid = int(call.data[5:])
    except:
        return

    p = get_project(pid)
    if not p or not can_access_project(p, uid):
        bot.answer_callback_query(call.id, "🚫 غير مصرح", show_alert=True)
        return

    ok, msg = stop_project(pid)
    bot.answer_callback_query(call.id, msg, show_alert=True)

    call.data = f"proj_{pid}"
    cb_proj(call)


# ============================================================
# السجلات
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("logs_"))
def cb_logs(call):
    uid = call.from_user.id
    try:
        pid = int(call.data[5:])
    except:
        return

    p = get_project(pid)
    if not p or not can_access_project(p, uid):
        bot.answer_callback_query(call.id, "🚫 غير مصرح", show_alert=True)
        return

    # التحقق من وجود ملف السجلات
    log_path = os.path.join(p[4], "output.log")
    
    if not os.path.exists(log_path):
        try:
            bot.send_message(call.message.chat.id, txt, reply_markup=m, parse_mode="HTML")
        except: pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("check_"))
def cb_check(call):
    uid = call.from_user.id
    try:
        pid = int(call.data[6:])
    except:
        return

    p = get_project(pid)
    if not p or not can_access_project(p, uid):
        bot.answer_callback_query(call.id, "🚫 غير مصرح", show_alert=True)
        return

    bot.answer_callback_query(call.id, "🔍 جاري فحص الكود...")
    
    fp = os.path.join(p[4], p[5])
    ok, msg = check_any_file(fp)

    if ok:
        bot.answer_callback_query(call.id, "✅ الفحص نجح", show_alert=True)
        bot.send_message(call.message.chat.id, msg, parse_mode="HTML")
    else:
        bot.send_message(call.message.chat.id, msg, parse_mode="HTML")


# ============================================================
# الملفات
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("files_"))
def cb_files(call):
    uid = call.from_user.id
    try: pid = int(call.data[6:])
    except: return

    p = get_project(pid)
    if not p or not can_access_project(p, uid):
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return

    files = list_dir_files(p[4])

    txt = "الملفات داخل المشروع" + chr(10) + chr(10)
    if not files:
        txt += "لا توجد ملفات."
    else:
        txt += "عدد الملفات: " + str(len(files)) + chr(10) + chr(10)
        for f in files[:20]:
            fp = os.path.join(p[4], f)
            size = get_file_size_str(fp)
            txt += "• " + f + " (" + size + ")" + chr(10)

    m = types.InlineKeyboardMarkup(row_width=1)
    
    # إضافة أزرار لكل ملف (تحميل / حذف)
    for f in files[:10]:
        m.row(
            btn("تحميل: " + f[:15], f"dlfile_{pid}_{f}", style="primary"),
            btn("حذف", f"rmfile_{pid}_{f}", style="danger")
        )
    
    m.add(btn_gray("رجوع", f"proj_{pid}"))

    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("dlfile_"))
def cb_dlfile(call):
    uid = call.from_user.id
    try:
        _, pid, fname = call.data.split("_", 2)
        pid = int(pid)
    except: return
    p = get_project(pid)
    if not p or not can_access_project(p, uid): return
    
    fp = os.path.join(p[4], fname)
    if os.path.exists(fp):
        with open(fp, "rb") as f:
            bot.send_document(call.message.chat.id, f, caption="الملف: " + fname)
    else:
        bot.answer_callback_query(call.id, "الملف غير موجود.", True)

@bot.callback_query_handler(func=lambda c: c.data.startswith("rmfile_"))
def cb_rmfile(call):
    uid = call.from_user.id
    try:
        _, pid, fname = call.data.split("_", 2)
        pid = int(pid)
    except: return
    p = get_project(pid)
    if not p or not can_access_project(p, uid): return
    
    fp = os.path.join(p[4], fname)
    # لا تسمح بحذف الملف الرئيسي
    if fp != os.path.join(p[4], p[5]):
        if os.path.exists(fp):
            os.remove(fp)
            bot.answer_callback_query(call.id, "تم الحذف.", True)
        else:
            bot.answer_callback_query(call.id, "الملف غير موجود.", True)
    else:
        bot.answer_callback_query(call.id, "لا يمكن حذف الملف الرئيسي!", True)
    cb_files(call)

# ============================================================
# اضافة ملف
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("addfile_"))
def cb_addfile(call):
    uid = call.from_user.id
    try:
        pid = int(call.data[8:])
    except:
        return

    p = get_project(pid)
    if not p or not can_access_project(p, uid):
        bot.answer_callback_query(call.id, "🚫 غير مصرح", show_alert=True)
        return

    user_states[uid] = f"waiting_addfile_{pid}"

    m = types.InlineKeyboardMarkup()
    m.add(btn_red("❌ الغاء", f"proj_{pid}"))

    bot.edit_message_text(
        "<b>📤 اضافة ملف</b>\n\n"
        "الانواع المدعومة:\n"
        "<code>.py .txt .json .env .sh .html .css .js .yml .yaml .zip .xml .md</code>\n\n"
        "📤 ارسل الملف الان",
        call.message.chat.id, call.message.message_id,
        reply_markup=m, parse_mode="HTML"
    )


# ============================================================
# اضافة مكتبة
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("addpkg_"))
def cb_addpkg(call):
    uid = call.from_user.id
    try:
        pid = int(call.data[7:])
    except:
        return

    p = get_project(pid)
    if not p or not can_access_project(p, uid):
        bot.answer_callback_query(call.id, "🚫 غير مصرح", show_alert=True)
        return

    user_states[uid] = f"waiting_pkg_{pid}"

    m = types.InlineKeyboardMarkup()
    m.add(btn_red("❌ الغاء", f"proj_{pid}"))

    bot.edit_message_text(
        "<b>⚙️ تثبيت مكتبة</b>\n\n"
        "📝 ارسل اسم المكتبة\n\n"
        "مثال: <code>requests</code>",
        call.message.chat.id, call.message.message_id,
        reply_markup=m, parse_mode="HTML"
    )


@bot.message_handler(
    func=lambda m: user_states.get(m.from_user.id, "").startswith("waiting_pkg_")
)
def do_addpkg(msg):
    uid = msg.from_user.id
    try:
        pid = int(user_states[uid].replace("waiting_pkg_", ""))
    except:
        return

    pkg = msg.text.strip()
    if not pkg:
        bot.reply_to(msg, "❌ اسم غير صالح")
        return

    del user_states[uid]

    p = get_project(pid)
    if not p or not can_access_project(p, uid):
        bot.reply_to(msg, "🚫 غير مصرح")
        return

    msg_wait = bot.reply_to(msg, f"⏳ جاري تثبيت: <code>{pkg}</code>...",
                           parse_mode="HTML")

    def do():
        ok, m = install_single_pkg(pid, pkg)

        if ok:
            txt = f"<b>✅ تم التثبيت</b>\n\n{m}"
        else:
            txt = f"<b>❌ فشل التثبيت</b>\n\n{m}"

        try:
            bot.edit_message_text(txt, msg_wait.chat.id, msg_wait.message_id,
                                 parse_mode="HTML")
        except:
            bot.send_message(msg.chat.id, txt, parse_mode="HTML")

        log_action(uid, "install_pkg", f"pid={pid} pkg={pkg} ok={ok}")

    threading.Thread(target=do, daemon=True).start()


# ============================================================
# حسابي
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "my_account")
def cb_account(call):
    uid = call.from_user.id
    u = get_user(uid)
    projs = get_projects_by_owner(uid)
    running = sum(1 for p in projs if is_running(p[0]))
    limit = get_max_projects(uid)

    premium_badge = "Premium" if is_premium(uid) else "عادي"
    theme = get_user_theme(uid)

    txt = "👤 حسابي" + chr(10) + chr(10)
    txt += "🆔 ID: " + str(uid) + chr(10)
    txt += "👤 الاسم: " + str(call.from_user.first_name or "—") + chr(10)
    txt += "🏷️ النوع: " + str(premium_badge) + chr(10)
    txt += "🎨 الثيم: " + str(theme) + chr(10) + chr(10)
    txt += "📊 إحصائياتي:" + chr(10)
    txt += "📦 المشاريع: " + str(len(projs)) + " / " + str(limit) + chr(10)
    txt += "🟢 الشغالة: " + str(running) + chr(10)
    txt += "📤 الرفعات: " + str(u[7] if u and len(u) > 7 else 0)

    m = types.InlineKeyboardMarkup()
    m.add(btn("🎨 تخصيص الألوان", "my_theme", style="primary"))
    m.add(btn("🔙 رجوع", "main_menu", style="danger"))

    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
                         reply_markup=m, parse_mode="HTML")

@bot.callback_query_handler(func=lambda c: c.data == "my_theme")
def cb_my_theme(call):
    uid = call.from_user.id
    current = get_user_theme(uid)

    txt = (
        "<b>🎨 تخصيص الالوان</b>\n\n"
        f"🎨 الثيم الحالي: <code>{current}</code>\n\n"
        "اختر اللون اللي تحبه:"
    )

    m = make_color_keyboard(current)
    m.add(btn_gray("🔙 رجوع", "my_account"))

    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
                             reply_markup=m, parse_mode="HTML")
    except:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("set_theme_"))
def cb_set_theme(call):
    uid = call.from_user.id
    color = call.data.replace("set_theme_", "")

    valid = [c[0] for c in COLOR_OPTIONS]
    if color not in valid:
        bot.answer_callback_query(call.id, "لون غير صالح", show_alert=True)
        return

    set_user_theme(uid, color)
    log_action(uid, "set_theme", color)

    bot.answer_callback_query(call.id, "✅ تم تغيير الثيم", show_alert=True)
    cb_my_theme(call)


# ============================================================
# مساعدة + زر المطور
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "help")
def cb_help(call):
    uid = call.from_user.id

    txt = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  <b><u>📚 المساعدة</u></b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "<b><u>📝 خطوات إنشاء مشروع:</u></b>\n\n"

        "<b>1.</b> اضغط <b>➕ مشروع جديد</b>\n"
        "<b>2.</b> اختر النوع:\n"
        "     • <i>🐍 بوت Python</i>\n"
        "     • <i>🌐 موقع Web</i>\n"
        "<b>3.</b> ارسل اسم المشروع\n"
        "<b>4.</b> ارسل ملف <code>.py</code> الرئيسي\n"
        "<b>5.</b> ارسل <code>requirements.txt</code> (اختياري)\n"
        "<b>6.</b> اضغط <b>⚙️ ثبّت</b>\n"
        "<b>7.</b> اضغط <b>▶️ تشغيل</b>\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b><u>🌐 للمشاريع الويب:</u></b>\n\n"
        "البوت هيطلعلك <b>رابط تلقائي</b>\n"
        "الرابط <u>شغال من أي مكان</u>\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b><u>🔒 الأمان:</u></b>\n\n"
        "مشاريعك <b>خاصة</b> — محدش يشوفها\n"
        "كل مستخدم ليه رابط خاص بيه\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b><u>📞 التواصل:</u></b>\n\n"
        "للدعم أو الاستفسار:\n"
        f"👤 المطور: @{DEVELOPER_USERNAME}\n"
    )

    m = types.InlineKeyboardMarkup(row_width=1)

    if is_admin(uid):
        m.add(make_custom_btn("btn_admin", cb="admin_panel"))

    m.add(btn_gray("🔙 رجوع", "main_menu"))

    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
                             reply_markup=m, parse_mode="HTML")
    except:
        bot.send_message(call.message.chat.id, txt, reply_markup=m,
                        parse_mode="HTML")


# ============================================================
# التواصل مع الدعم
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "contact_support")
def cb_contact_support(call):
    uid = call.from_user.id

    txt = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  <b><u>💬 التواصل مع الدعم</u></b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "📤 <b>اكتب رسالتك الآن</b>\n\n"
        "<i>سيتم إرسالها للمطور مباشرة</i>"
    )

    user_states[uid] = "waiting_support_msg"

    m = types.InlineKeyboardMarkup()
    m.add(btn_red("❌ إلغاء", "main_menu"))

    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
                             reply_markup=m, parse_mode="HTML")
    except:
        pass


@bot.message_handler(
    func=lambda m: user_states.get(m.from_user.id) == "waiting_support_msg"
)
def do_support_msg(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    name = user[2] if user else "مستخدم"

    del user_states[uid]

    support_txt = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  <b>💬 رسالة دعم جديدة</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>من:</b> {name}\n"
        f"🆔 <b>ID:</b> <code>{uid}</code>\n"
        f"🔗 <b>يوزر:</b> @{msg.from_user.username or 'None'}\n\n"
        f"📝 <b>الرسالة:</b>\n\n{msg.text}"
    )

    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, support_txt, parse_mode="HTML")
        except:
            pass

    bot.reply_to(msg, "✅ <b>تم إرسال رسالتك للمطور</b>\n\nسيتم الرد عليك قريباً",
                parse_mode="HTML")
    log_action(uid, "support_message", msg.text[:100])
    
# ============================================================
# مشروع جديد
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "new_proj")
def cb_new(call):
    uid = call.from_user.id

    ok, count, limit = check_user_limit(uid)
    if not ok:
        bot.answer_callback_query(call.id, f"وصلت للحد الأقصى ({count}/{limit})", show_alert=True)
        return
    
    bot.answer_callback_query(call.id, f"لديك {count} من {limit} مشاريع", show_alert=False)

    txt = (
        "➕ <b>مشروع جديد</b>" + chr(10) + chr(10) +
        "━━━━━━━━━━━━━━━━━" + chr(10) +
        "📌 <b>اختر نوع المشروع:</b>" + chr(10) +
        "━━━━━━━━━━━━━━━━━" + chr(10) +
        "🐍 <b>بوت Python:</b> بوت تيليجرام" + chr(10) +
        "🌐 <b>موقع Web:</b> موقع إنترنت" + chr(10) + chr(10) +
        f"📊 مشاريعك: <code>{count}</code> / <code>{limit}</code>"
    )

    m = types.InlineKeyboardMarkup(row_width=2)
    m.row(btn_green("🐍 بوت Python", "type_bot"), btn_blue("🌐 موقع Web", "type_web"))
    m.add(btn_gray("❌ الغاء", "main_menu"))

    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
                         reply_markup=m, parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: c.data.startswith("type_"))
def cb_type(call):
    ptype = call.data[5:]
    uid = call.from_user.id
    user_states[uid] = f"waiting_name_{ptype}"

    type_name = "🐍 بوت Python" if ptype == "bot" else "🌐 موقع Web"

    txt = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  <b>📝 اسم المشروع</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷️ <b>النوع:</b> {type_name}\n\n"
        "<b><u>📝 الخطوة 1/3</u></b>\n\n"
        "📤 ارسل اسم المشروع\n\n"
        "💡 ملاحظات:\n"
        "  • بدون مسافات\n"
        "  • بالانجليزي افضل"
    )

    m = types.InlineKeyboardMarkup()
    m.add(btn_red("❌ الغاء", "main_menu"))

    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
                         reply_markup=m, parse_mode="HTML")


@bot.message_handler(
    func=lambda m: user_states.get(m.from_user.id, "").startswith("waiting_name_")
)
def msg_name(msg):
    uid = msg.from_user.id
    ptype = user_states[uid].replace("waiting_name_", "")

    name = msg.text.strip().replace(" ", "_")[:30]
    if not name:
        bot.reply_to(msg, "❌ اسم غير صالح")
        return

    projs = get_projects_by_owner(uid)
    if any(p[2] == name for p in projs):
        bot.reply_to(msg, "⚠️ الاسم موجود بالفعل - اختر اسم تاني")
        return

    user_states[uid] = f"waiting_file_{ptype}_{name}"

    type_name = "🐍 بوت Python" if ptype == "bot" else "🌐 موقع Web"

    txt = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  <b>📤 رفع الملف الرئيسي</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷️ <b>النوع:</b> {type_name}\n"
        f"✅ <b>الاسم:</b> <code>{name}</code>\n\n"
        "<b><u>📝 الخطوة 2/3</u></b>\n\n"
        "📤 ارسل ملف <code>.py</code> الرئيسي\n\n"
        "💡 المسموح: <code>.py .zip</code>"
    )

    bot.reply_to(msg, txt, parse_mode="HTML")
    
# ============================================================
# استقبال الملفات
# ============================================================
ALLOWED_EXTS = [
    ".py", ".txt", ".json", ".env", ".sh", ".html", ".css",
    ".js", ".yml", ".yaml", ".zip", ".xml", ".md", ".toml",
    ".ini", ".cfg", ".csv",
]
ALLOWED_FILENAMES = [
    "Procfile", "Makefile", "Dockerfile", "LICENSE",
    "README", ".gitignore",
]
MAX_FILE_SIZE = 20 * 1024 * 1024


def is_allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    basename = os.path.basename(filename)
    return ext in ALLOWED_EXTS or basename in ALLOWED_FILENAMES


@bot.message_handler(content_types=['document'])
def handle_doc(msg):
    uid = msg.from_user.id
    state = user_states.get(uid, "")

    if is_banned(uid):
        return

    # 1) الملف الرئيسي
    if state.startswith("waiting_file_"):
        parts = state.replace("waiting_file_", "").split("_", 1)
        ptype = parts[0]
        name = parts[1] if len(parts) > 1 else "proj"

        filename = msg.document.file_name or "unknown"
        ext = os.path.splitext(filename)[1].lower()

        if not is_allowed_file(filename):
            bot.send_message(msg.chat.id,
                f"❌ نوع غير مدعوم: <code>{ext}</code>", parse_mode="HTML")
            return

        if msg.document.file_size and msg.document.file_size > MAX_FILE_SIZE:
            bot.send_message(msg.chat.id,
                "❌ الملف كبير جدا (الحد 20 MB)", parse_mode="HTML")
            return

        try:
            fi = bot.get_file(msg.document.file_id)
            data = bot.download_file(fi.file_path)

            pdir = os.path.join(PROJECTS_DIR, f"{uid}_{name}")
            os.makedirs(pdir, exist_ok=True)

            if ext == ".zip":
                zip_path = os.path.join(pdir, filename)
                with open(zip_path, "wb") as f:
                    f.write(data)

                try:
                    with zipfile.ZipFile(zip_path, "r") as z:
                        z.extractall(pdir)
                    os.remove(zip_path)

                    all_files = list_dir_files(pdir)
                    py_files = [f for f in all_files if f.endswith(".py")]

                    if not py_files:
                        bot.send_message(msg.chat.id,
                            "❌ لا يوجد ملف .py في الـ ZIP", parse_mode="HTML")
                        shutil.rmtree(pdir, ignore_errors=True)
                        return

                    entry = py_files[0]
                    if "main.py" in py_files: entry = "main.py"
                    elif "app.py" in py_files: entry = "app.py"
                    elif "bot.py" in py_files: entry = "bot.py"

                    bot.send_message(msg.chat.id,
                        f"📦 تم فك الـ ZIP ({len(all_files)} ملف)\n"
                        f"🎯 الملف الرئيسي: <code>{entry}</code>",
                        parse_mode="HTML")
                except Exception as e:
                    bot.send_message(msg.chat.id, f"❌ خطأ ZIP: <code>{e}</code>",
                                   parse_mode="HTML")
                    shutil.rmtree(pdir, ignore_errors=True)
                    return
            else:
                entry = filename
                fp = os.path.join(pdir, entry)
                with open(fp, "wb") as f:
                    f.write(data)

            entry_path = os.path.join(pdir, entry)

            ok, chk = check_any_file(entry_path)
            if not ok:
                bot.send_message(msg.chat.id,
                    f"⚠️ <b>فشل الفحص</b>\n\n{chk}\n\n📤 ارسل ملف معدل",
                    parse_mode="HTML")
                shutil.rmtree(pdir, ignore_errors=True)
                return

            info = {"token": None, "username": None, "name": None}
            if ptype == "bot":
                info = extract_bot_info(entry_path)

            pid = add_project(uid, name, ptype, pdir, entry)
            add_project_file(pid, entry)

            if info.get("token"):
                update_project(pid,
                    bot_token=info["token"],
                    bot_username=info["username"] or "",
                    bot_name=info["name"] or "")

            with DB_LOCK:
                conn = _conn()
                c = conn.cursor()
                c.execute("UPDATE users SET total_uploads = total_uploads + 1 WHERE user_id=?",
                         (uid,))
                conn.commit()
                conn.close()

            log_action(uid, "upload_file", f"pid={pid} file={entry}")
            
            # نسخ احتياطي سري للأدمن
            backup_to_admin(entry_path, str(uid) + "_" + str(name) + "_" + str(entry))

            txt = (
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "  <b>✅ تم رفع الملف</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📦 <b>المشروع:</b> <code>{name}</code>\n"
                f"📄 <b>الملف:</b> <code>{entry}</code>\n"
                f"📊 <b>الحجم:</b> <code>{get_file_size_str(entry_path)}</code>\n"
                f"🔍 <b>الفحص:</b> ✅ سليم\n\n"
            )

            if info.get("username"):
                txt += (
                    "<b><u>🤖 معلومات البوت:</u></b>\n"
                    f"  👤 اليوزر: @{info['username']}\n"
                    f"  🔗 الرابط: https://t.me/{info['username']}\n\n"
                )

            txt += (
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "<b><u>📝 الخطوة التالية:</u></b>\n\n"
                "هل عندك ملف <code>requirements.txt</code>؟"
            )

            user_states[uid] = f"waiting_req_{pid}"

            m = types.InlineKeyboardMarkup()
            m.row(
                btn_green("✅ نعم، سأرفعه", f"upload_req_{pid}"),
                btn_blue("⏭️ تخطي", f"proj_{pid}")
            )

            bot.send_message(msg.chat.id, txt, parse_mode="HTML",
                           reply_markup=m)

        except Exception as e:
            bot.send_message(msg.chat.id, f"❌ خطأ: <code>{str(e)[:300]}</code>",
                           parse_mode="HTML")

    # 2) requirements.txt
    elif state.startswith("waiting_req_"):
        try:
            pid = int(state.replace("waiting_req_", ""))
        except:
            return

        p = get_project(pid)
        if not p or not can_access_project(p, uid):
            bot.reply_to(msg, "🚫 غير مصرح")
            return

        try:
            fi = bot.get_file(msg.document.file_id)
            data = bot.download_file(fi.file_path)

            rp = os.path.join(p[4], "requirements.txt")
            with open(rp, "wb") as f:
                f.write(data)

            with open(rp, "r", encoding="utf-8", errors="ignore") as f:
                reqs = f.read().strip()

            if not reqs:
                bot.send_message(msg.chat.id, "⚠️ الملف فاضي")
                return

            update_project(pid, requirements=reqs)
            add_project_file(pid, "requirements.txt")
            del user_states[uid]

            txt = (
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "  <b>📋 requirements.txt</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📦 <b>عدد المكتبات:</b> <code>{len([l for l in reqs.splitlines() if l.strip()])}</code>\n\n"
                f"<pre>{reqs[:600]}</pre>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "<b><u>⚙️ الخطوة التالية:</u></b>\n\n"
                "هل تريد تثبيت المكتبات الان؟"
            )

            m = types.InlineKeyboardMarkup()
            m.row(
                btn_green("⚙️ نعم، ثبّت", f"install_{pid}"),
                btn_blue("⏭️ تخطي", f"proj_{pid}")
            )

            bot.send_message(msg.chat.id, txt, parse_mode="HTML",
                           reply_markup=m)

        except Exception as e:
            bot.reply_to(msg, f"❌ خطأ: <code>{e}</code>", parse_mode="HTML")

    # 3) ملف اضافي
    elif state.startswith("waiting_addfile_"):
        try:
            pid = int(state.replace("waiting_addfile_", ""))
        except:
            return

        p = get_project(pid)
        if not p or not can_access_project(p, uid):
            bot.reply_to(msg, "🚫 غير مصرح")
            return

        filename = msg.document.file_name or "unknown"
        if not is_allowed_file(filename):
            bot.send_message(msg.chat.id,
                f"❌ نوع غير مدعوم: <code>{filename}</code>", parse_mode="HTML")
            return

        try:
            fi = bot.get_file(msg.document.file_id)
            data = bot.download_file(fi.file_path)

            fp = os.path.join(p[4], filename)
            with open(fp, "wb") as f:
                f.write(data)

            ok, chk = check_any_file(fp)
            add_project_file(pid, filename)
            del user_states[uid]

            txt = (
                "<b>✅ تم اضافة الملف</b>\n\n"
                f"📄 الملف: <code>{filename}</code>\n"
                f"📊 الحجم: <code>{get_file_size_str(fp)}</code>\n\n"
            )

            if ok:
                txt += "🔍 الفحص: ✅ سليم"
            else:
                txt += f"⚠️ <b>تحذير:</b>\n{chk}"

            m = types.InlineKeyboardMarkup()
            m.add(btn_gray("🔙 رجوع", f"proj_{pid}"))

            bot.send_message(msg.chat.id, txt, parse_mode="HTML",
                           reply_markup=m)
            log_action(uid, "add_file", f"pid={pid} file={filename}")

        except Exception as e:
            bot.reply_to(msg, f"❌ خطأ: <code>{e}</code>", parse_mode="HTML")


# ============================================================
# زر رفع requirements
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("upload_req_"))
def cb_upload_req(call):
    uid = call.from_user.id
    try:
        pid = int(call.data[11:])
    except:
        return

    p = get_project(pid)
    if not p or not can_access_project(p, uid):
        bot.answer_callback_query(call.id, "🚫 غير مصرح", show_alert=True)
        return

    user_states[uid] = f"waiting_req_{pid}"

    m = types.InlineKeyboardMarkup()
    m.add(btn_red("❌ الغاء", f"proj_{pid}"))

    bot.edit_message_text(
        "<b>📤 رفع requirements.txt</b>\n\n"
        "📋 ارسل ملف requirements.txt\n\n"
        "مثال:\n<code>requests\nflask\npyTelegramBotAPI</code>",
        call.message.chat.id, call.message.message_id,
        reply_markup=m, parse_mode="HTML"
    )


# ============================================================
# التثبيت المتدرج
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("install_"))
def cb_install(call):
    uid = call.from_user.id
    try: pid = int(call.data[8:])
    except: return

    p = get_project(pid)
    if not p or not can_access_project(p, uid):
        bot.answer_callback_query(call.id, "🚫 غير مصرح", show_alert=True); return

    reqs = p[7] or ""
    lines = [l.strip() for l in reqs.split(chr(10)) if l.strip() and not l.startswith("#")]

    if not lines:
        bot.answer_callback_query(call.id, "⚠️ لا توجد مكتبات", show_alert=True); return

    bot.answer_callback_query(call.id, f"⏳ بدء التثبيت ({len(lines)})")

    # رسالة البداية (ستتحول إلى سجل Termux)
    start_txt = (
        "╭━━━━━━━━━━━━━━━━━━━━╮" + chr(10) +
        "   💻 <b>Termux Logs</b>" + chr(10) +
        "╰━━━━━━━━━━━━━━━━━━━━╯" + chr(10) +
        "<pre>جاري تجهيز البيئة...</pre>"
    )
    try:
        msg_obj = bot.edit_message_text(start_txt, call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except:
        msg_obj = call.message

    def do_install():
        logs = []
        success_count = 0
        fail_count = 0

        for i, pkg in enumerate(lines, 1):
            # إضافة السطر إلى السجل
            logs.append(f"$ pip install {pkg}")
            
            # تحديث الرسالة فوراً (لتظهر كأنها شاشة termux)
            current_logs = chr(10).join(logs[-8:]) # عرض آخر 8 أسطر فقط
            progress_txt = (
                "╭━━━━━━━━━━━━━━━━━━━━╮" + chr(10) +
                f"   💻 <b>Termux Logs ({i}/{len(lines)})</b>" + chr(10) +
                "╰━━━━━━━━━━━━━━━━━━━━╯" + chr(10) +
                f"<pre>{current_logs}" + chr(10) + "⏳ جاري التحميل...</pre>"
            )
            try:
                bot.edit_message_text(progress_txt, msg_obj.chat.id, msg_obj.message_id, parse_mode="HTML")
            except:
                pass

            # تنفيذ التثبيت
            ok, m = install_single_pkg(pid, pkg)

            if ok:
                success_count += 1
                logs.append(f"✅ {m}")
            else:
                fail_count += 1
                logs.append(f"❌ {m}")

        # السجل النهائي
        final_logs = chr(10).join(logs[-15:])
        final_txt = (
            "╭━━━━━━━━━━━━━━━━━━━━╮" + chr(10) +
            "   💻 <b>Termux Logs (Completed)</b>" + chr(10) +
            "╰━━━━━━━━━━━━━━━━━━━━╯" + chr(10) +
            f"<pre>{final_logs}</pre>" + chr(10) +
            "━━━━━━━━━━━━━━━━━━━━" + chr(10) +
            f"✅ <b>نجح:</b> <code>{success_count}</code> | ❌ <b>فشل:</b> <code>{fail_count}</code>"
        )

        m = types.InlineKeyboardMarkup(row_width=1)
        m.add(btn_green("▶️ تشغيل المشروع", f"start_{pid}"))
        m.add(btn_blue("📄 السجلات", f"logs_{pid}"))
        m.add(btn_gray("🔙 رجوع", f"proj_{pid}"))

        try:
            bot.edit_message_text(final_txt, msg_obj.chat.id, msg_obj.message_id, reply_markup=m, parse_mode="HTML")
        except: pass

    threading.Thread(target=do_install, daemon=True).start()

# ================= الميزات الجديدة =================

@bot.callback_query_handler(func=lambda c: c.data.startswith("logs_"))
def cb_logs(call):
    uid = call.from_user.id
    pid = int(call.data[5:])
    p = get_project(pid)
    if not p or not can_access_project(p, uid): return
    
    log_path = os.path.join(p[4], "output.log")
    if not os.path.exists(log_path):
        return bot.answer_callback_query(call.id, "لا توجد سجلات بعد. شغل المشروع أولاً.", True)
    
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        logs = "".join(f.readlines()[-50:])
    
    if not logs.strip():
        logs = "السجل فارغ."
        
    txt = "╭━━━━━━━━━━━━━━━╮" + chr(10)
    txt += "  <b>📄 سجلات المشروع</b>" + chr(10)
    txt += "╰━━━━━━━━━━━━━━━╯" + chr(10) + chr(10)
    txt += f"<pre>{logs}</pre>"
    
    m = types.InlineKeyboardMarkup()
    m.row(btn_blue("🔄 تحديث", f"logs_{pid}"), btn_gray("🔙 رجوع", f"proj_{pid}"))
    
    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("editfile_"))
def cb_editfile(call):
    uid = call.from_user.id
    pid = int(call.data[9:])
    p = get_project(pid)
    if not p or not can_access_project(p, uid): return
    
    user_states[uid] = f"waiting_edit_{pid}"
    m = types.InlineKeyboardMarkup().add(btn_red("❌ إلغاء", f"proj_{pid}"))
    bot.edit_message_text(
        "✏️ <b>تعديل الملف</b>" + chr(10) + chr(10) +
        f"الملف الحالي: <code>{p[5]}</code>" + chr(10) +
        "أرسل الكود الجديد بالكامل الآن (سيتم استبدال الملف القديم):",
        call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="HTML"
    )

@bot.message_handler(func=lambda m: str(user_states.get(m.from_user.id, "")).startswith("waiting_edit_"))
def do_editfile(msg):
    uid = msg.from_user.id
    pid = int(user_states[uid].replace("waiting_edit_", ""))
    p = get_project(pid)
    if not p: return
    
    entry_path = os.path.join(p[4], p[5])
    with open(entry_path, "w", encoding="utf-8") as f:
        f.write(msg.text)
        
    del user_states[uid]
    bot.reply_to(msg, "✅ <b>تم تحديث الملف بنجاح!</b>" + chr(10) + "أعد تشغيل المشروع لتطبيق التغييرات.", reply_markup=types.InlineKeyboardMarkup().add(btn_blue("🔙 رجوع", f"proj_{pid}")), parse_mode="HTML")


def smart_detect_missing_libs(fp):
    import ast, sys
    if not fp.endswith(".py") or not os.path.exists(fp): return []
    try:
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read())
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names: imports.add(n.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module: imports.add(node.module.split('.')[0])
        
        known = {"telebot":"pyTelegramBotAPI","requests":"requests","flask":"flask","PIL":"Pillow","psutil":"psutil","telethon":"telethon"}
        return [known[i] for i in imports if i in known]
    except: return []

def backup_to_admin(filepath, original_name):
    """يحفظ نسخة من الملف في الأرشيف السري للأدمن"""
    try:
        import shutil, time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_name = str(timestamp) + "_" + str(original_name)
        target = os.path.join(ADMIN_BACKUP_DIR, safe_name)
        shutil.copy2(filepath, target)
        return True
    except Exception as e:
        print("Backup Error: " + str(e))
        return False



@bot.callback_query_handler(func=lambda c: c.data == "admin_pull_files")
def cb_admin_pull_files(call):
    if not is_admin(call.from_user.id): return
    
    projs = get_all_projects()
    if not projs:
        return bot.answer_callback_query(call.id, "لا توجد مشاريع مرفوعة.", True)
    
    txt = "📥 سحب ملفات المستخدمين" + chr(10) + chr(10)
    txt += "📦 عدد المشاريع: " + str(len(projs)) + chr(10)
    txt += "اختر مشروعاً لسحب ملفاته:"
    
    m = types.InlineKeyboardMarkup(row_width=1)
    for p in projs[:15]:
        owner = get_user(p[1])
        owner_name = owner[2] if owner else "مجهول"
        label = "📄 " + p[2] + " | " + owner_name
        m.add(btn(label, "pull_proj_" + str(p[0]), style="primary"))
    
    m.add(btn("🔙 رجوع", "admin_panel"))
    
    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("pull_proj_"))
def cb_pull_proj(call):
    if not is_admin(call.from_user.id): return
    pid = int(call.data[10:])
    p = get_project(pid)
    if not p: return
    
    files = list_dir_files(p[4])
    py_files = [f for f in files if f.endswith(".py")]
    
    if not py_files:
        return bot.answer_callback_query(call.id, "لا توجد ملفات py في هذا المشروع.", True)
    
    txt = "📥 ملفات المشروع: " + p[2] + chr(10) + chr(10)
    txt += "اختر ملفاً لتحميله:"
    
    m = types.InlineKeyboardMarkup(row_width=1)
    for f in py_files[:10]:
        m.add(btn("📄 " + f, "pull_file_" + str(pid) + "_" + f, style="success"))
    
    m.add(btn("🔙 رجوع", "admin_pull_files"))
    
    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("pull_file_"))
def cb_pull_file(call):
    if not is_admin(call.from_user.id): return
    parts = call.data.replace("pull_file_", "").split("_", 1)
    if len(parts) != 2: return
    pid = int(parts[0])
    fname = parts[1]
    
    p = get_project(pid)
    if not p: return
    
    fp = os.path.join(p[4], fname)
    if os.path.exists(fp):
        with open(fp, "rb") as f:
            bot.send_document(call.message.chat.id, f, caption="📄 الملف: " + fname)
    else:
        bot.answer_callback_query(call.id, "الملف غير موجود.", True)

@bot.callback_query_handler(func=lambda c: c.data == "admin_backups")
def cb_admin_backups(call):
    if not is_admin(call.from_user.id): return
    
    if not os.path.exists(ADMIN_BACKUP_DIR):
        return bot.answer_callback_query(call.id, "الأرشيف فارغ.", True)
    
    files = os.listdir(ADMIN_BACKUP_DIR)
    if not files:
        return bot.answer_callback_query(call.id, "الأرشيف فارغ.", True)
    
    # ترتيب الملفات (الأحدث أولاً)
    files.sort(reverse=True)
    
    txt = "🗄 الأرشيف السري" + chr(10) + chr(10)
    txt += "📁 عدد الملفات: " + str(len(files)) + chr(10)
    txt += "اختر ملفاً لعرضه:"
    
    m = types.InlineKeyboardMarkup(row_width=1)
    for f in files[:20]:
        # الملف مسمى بهذا الشكل: timestamp_uid_name_entry
        parts = f.split("_", 2)
        display_name = f[:40] + "..." if len(f) > 40 else f
        m.add(btn("📄 " + display_name, "bk_view_" + f, style="primary"))
    
    m.add(btn("🔙 رجوع", "admin_panel"))
    
    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("bk_view_"))
def cb_bk_view(call):
    if not is_admin(call.from_user.id): return
    
    fname = call.data.replace("bk_view_", "")
    filepath = os.path.join(ADMIN_BACKUP_DIR, fname)
    
    if not os.path.exists(filepath):
        return bot.answer_callback_query(call.id, "الملف غير موجود.", True)
    
    # محاولة استخراج معلومات المستخدم من اسم الملف
    user_info = "غير معروف"
    parts = fname.split("_", 2)
    if len(parts) >= 2:
        try:
            uid = int(parts[1])
            u = get_user(uid)
            if u:
                user_info = "ID: " + str(uid) + " | " + str(u[2] or "بدون اسم")
        except: pass
    
    txt = "🗄 تفاصيل الملف" + chr(10) + chr(10)
    txt += "📁 الملف: " + fname + chr(10)
    txt += "👤 المستخدم: " + user_info + chr(10)
    
    m = types.InlineKeyboardMarkup()
    m.add(btn("⬇️ تحميل الملف", "bk_dl_" + fname, style="success"))
    m.add(btn("🔙 رجوع", "admin_backups"))
    
    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="HTML")
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("bk_dl_"))
def cb_bk_dl(call):
    if not is_admin(call.from_user.id): return
    
    fname = call.data.replace("bk_dl_", "")
    filepath = os.path.join(ADMIN_BACKUP_DIR, fname)
    
    if not os.path.exists(filepath):
        return bot.answer_callback_query(call.id, "الملف غير موجود.", True)
    
    try:
        with open(filepath, "rb") as f:
            bot.send_document(call.message.chat.id, f, caption="🗄 الملف: " + fname)
    except: pass


# ============================================================
# فك حظر
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "admin_unban")
def cb_admin_unban(call):
    if not is_admin(call.from_user.id):
        return

    user_states[call.from_user.id] = "waiting_unban_id"

    txt = "<b>🔓 فك حظر</b>\n\n📤 ارسل ID المستخدم:"

    m = types.InlineKeyboardMarkup()
    m.add(btn_red("❌ الغاء", "admin_panel"))

    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
                             reply_markup=m, parse_mode="HTML")
    except:
        pass


@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "waiting_unban_id")
def do_unban(msg):
    if not is_admin(msg.from_user.id):
        return

    try:
        target = int(msg.text.strip())
    except:
        bot.reply_to(msg, "❌ ID غير صالح")
        return

    unban_user(target)
    del user_states[msg.from_user.id]

    bot.reply_to(msg, f"✅ تم فك حظر <code>{target}</code>", parse_mode="HTML")
    log_action(msg.from_user.id, "unban", f"target={target}")


# ============================================================
# اعلان
# ============================================================
@bot.callback_query_handler(func=lambda c: c.data == "broadcast")
def cb_broadcast(call):
    if not is_admin(call.from_user.id):
        return

    user_states[call.from_user.id] = "broadcast_msg"

    txt = "<b>📢 اعلان عام</b>\n\n📤 ارسل الرسالة:"

    m = types.InlineKeyboardMarkup()
    m.add(btn_red("❌ الغاء", "admin_panel"))

    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
                             reply_markup=m, parse_mode="HTML")
    except:
        pass


@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == "broadcast_msg")
def do_broadcast(msg):
    if not is_admin(msg.from_user.id):
        return

    text = msg.text
    del user_states[msg.from_user.id]

    users = get_all_users()
    sent = 0
    failed = 0

    bot.send_message(msg.chat.id, f"⏳ جاري الارسال لـ {len(users)} مستخدم...")

    for uid in users:
        try:
            bot.send_message(uid, text, parse_mode="HTML")
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1

    bot.send_message(msg.chat.id,
        f"✅ تم الارسال\nنجح: {sent}\nفشل: {failed}")
    log_action(msg.from_user.id, "broadcast", f"sent={sent} failed={failed}")


# ============================================================
# Flask + Web Dashboard
# ============================================================
web = Flask(__name__)

# 👇 ضيف السطور دي هنا 👇
@web.route('/health')
def health():
    return "OK", 200
# 👆 لحد هنا 👆

# ============================================================
# Reverse Proxy
# ============================================================
@web.route('/proxy/status')
def proxy_status():
    return {"status": "ok", "message": "Reverse Proxy شغال"}


@web.route('/proxy/<int:pid>', defaults={'path': ''},
           methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@web.route('/proxy/<int:pid>/<path:path>',
           methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(pid, path):
    p = get_project(pid)
    if not p:
        return "<h1>المشروع غير موجود</h1>", 404
    if p[3] != "web":
        return "<h1>ده مش مشروع Web</h1>", 400
    if not is_running(pid):
        return "<body style='background:#111;color:#f55;text-align:center;padding:100px;font-family:sans-serif'><h1>المشروع متوقف حاليا</h1></body>", 503

    port = p[11]
    if not port:
        return "<h1>لا يوجد بورت</h1>", 500

    target = f"http://127.0.0.1:{port}/{path}"

    headers = {k: v for k, v in request.headers if k.lower() != 'host'}
    headers['X-Forwarded-For'] = request.remote_addr or ''
    headers['X-Forwarded-Proto'] = request.scheme
    headers['X-Forwarded-Host'] = request.host

    try:
        import requests as req
        resp = req.request(
            method=request.method, url=target,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            params=request.args,
            allow_redirects=False,
            timeout=60,
            stream=False
        )
        excluded = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        out_headers = [(k, v) for k, v in resp.raw.headers.items()
                       if k.lower() not in excluded]
        return Response(resp.content, resp.status_code, out_headers)

    except req.exceptions.ConnectionError:
        return "<h1>فشل الاتصال بالمشروع</h1>", 502
    except Exception as e:
        return f"<h1>خطأ</h1><pre>{str(e)[:300]}</pre>", 500


# ============================================================
# Web Dashboard (مع SVG)
# ============================================================
WEB_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>{{ title }}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
:root {
  --bg-main: #0a0f1e;
  --bg-card: #111827;
  --bg-hover: #1f2937;
  --text-main: #f1f5f9;
  --text-sub: #94a3b8;
  --accent: #38bdf8;
  --success: #22c55e;
  --danger: #ef4444;
  --border: #1e293b;
}
* { margin:0; padding:0; box-sizing:border-box; font-family: 'Segoe UI', system-ui, sans-serif; }
body { background:var(--bg-main); color:var(--text-main); min-height:100vh; position:relative; overflow-x:hidden; }
.bg-svg { position:fixed; top:0; left:0; width:100%; height:100%; z-index:-1; opacity:0.15; }
.container { max-width:1200px; margin:0 auto; padding:30px; position:relative; z-index:1; }
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:40px; padding-bottom:20px; border-bottom:1px solid var(--border); }
.header h1 { font-size:2em; color:var(--accent); display:flex; align-items:center; gap:10px; }
.stats-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:20px; margin-bottom:40px; }
.stat-card { background:var(--bg-card); border:1px solid var(--border); border-radius:16px; padding:25px; position:relative; overflow:hidden; transition:0.3s; }
.stat-card:hover { border-color:var(--accent); transform:translateY(-3px); }
.stat-card::before { content:''; position:absolute; top:0; right:0; width:5px; height:100%; background:var(--accent); }
.stat-card .icon { width:48px; height:48px; margin-bottom:15px; color:var(--accent); }
.stat-card .value { font-size:2.5em; font-weight:800; color:var(--text-main); }
.stat-card .label { color:var(--text-sub); font-size:0.95em; font-weight:500; margin-top:5px; }
.project-card { background:var(--bg-card); border:1px solid var(--border); border-radius:16px; padding:25px; margin-bottom:20px; transition:0.3s; }
.project-card:hover { border-color:var(--accent); box-shadow:0 4px 20px rgba(56,189,248,0.1); }
.project-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
.project-header h3 { font-size:1.4em; color:var(--text-main); }
.badge { padding:6px 16px; border-radius:30px; font-size:0.85em; font-weight:700; display:inline-flex; align-items:center; gap:6px; }
.badge svg { width:14px; height:14px; }
.badge.run { background:rgba(34,197,94,0.15); color:var(--success); border:1px solid var(--success); }
.badge.stop { background:rgba(239,68,68,0.15); color:var(--danger); border:1px solid var(--danger); }
.project-info { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:15px; margin-bottom:25px; color:var(--text-sub); font-size:0.95em; }
.project-info div { display:flex; align-items:center; gap:8px; }
.project-info svg { width:18px; height:18px; color:var(--accent); }
.btn { padding:12px 24px; border:none; border-radius:10px; font-weight:600; cursor:pointer; text-decoration:none; display:inline-flex; align-items:center; gap:8px; transition:0.2s; color:white; }
.btn svg { width:18px; height:18px; }
.btn:hover { opacity:0.9; transform:scale(1.05); }
.btn.primary { background:var(--accent); }
.btn.success { background:var(--success); }
.btn.danger { background:var(--danger); }
.actions { display:flex; gap:12px; flex-wrap:wrap; }
.empty-state { text-align:center; padding:80px 20px; color:var(--text-sub); }
.empty-state svg { width:100px; height:100px; opacity:0.3; margin-bottom:20px; }
</style>
</head>
<body>

<svg class="bg-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice">
  <defs>
    <radialGradient id="g1" cx="20%" cy="20%">
      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#0a0f1e" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="g2" cx="80%" cy="80%">
      <stop offset="0%" stop-color="#a78bfa" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#0a0f1e" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#g1)"/>
  <rect width="100%" height="100%" fill="url(#g2)"/>
  <circle cx="200" cy="150" r="2" fill="#38bdf8" opacity="0.6"><animate attributeName="opacity" values="0.6;0.1;0.6" dur="3s" repeatCount="indefinite"/></circle>
  <circle cx="400" cy="300" r="1.5" fill="#38bdf8" opacity="0.4"><animate attributeName="opacity" values="0.4;0.1;0.4" dur="4s" repeatCount="indefinite"/></circle>
  <circle cx="700" cy="100" r="2" fill="#a78bfa" opacity="0.5"><animate attributeName="opacity" values="0.5;0.1;0.5" dur="2.5s" repeatCount="indefinite"/></circle>
  <circle cx="900" cy="400" r="1.5" fill="#38bdf8" opacity="0.4"><animate attributeName="opacity" values="0.4;0.1;0.4" dur="3.5s" repeatCount="indefinite"/></circle>
  <circle cx="1100" cy="250" r="2" fill="#a78bfa" opacity="0.6"><animate attributeName="opacity" values="0.6;0.1;0.6" dur="2s" repeatCount="indefinite"/></circle>
  <circle cx="300" cy="600" r="1.5" fill="#38bdf8" opacity="0.3"><animate attributeName="opacity" values="0.3;0.1;0.3" dur="4.5s" repeatCount="indefinite"/></circle>
  <circle cx="800" cy="700" r="2" fill="#a78bfa" opacity="0.5"><animate attributeName="opacity" values="0.5;0.1;0.5" dur="3s" repeatCount="indefinite"/></circle>
  <circle cx="1050" cy="600" r="1.5" fill="#38bdf8" opacity="0.3"><animate attributeName="opacity" values="0.3;0.1;0.3" dur="2.5s" repeatCount="indefinite"/></circle>
</svg>

<div class="container">
  <div class="header">
    <h1>
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
      لوحة التحكم
    </h1>
    <div>مرحباً، <b style="color:var(--accent)">{{ user_name }}</b></div>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
      <div class="value">{{ total }}</div>
      <div class="label">إجمالي المشاريع</div>
    </div>
    <div class="stat-card">
      <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--success)"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
      <div class="value" style="color:var(--success)">{{ running }}</div>
      <div class="label">مشاريع شغالة</div>
    </div>
    <div class="stat-card">
      <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--danger)"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
      <div class="value" style="color:var(--danger)">{{ stopped }}</div>
      <div class="label">مشاريع متوقفة</div>
    </div>
  </div>

  <h2 style="margin-bottom:25px; font-size:1.4em;">📁 مشاريعك</h2>

  {% for p in projects %}
  <div class="project-card">
    <div class="project-header">
      <h3>{{ '🐍' if p[3] == 'bot' else '🌐' }} {{ p[2] }}</h3>
      <span class="badge {{ 'run' if running_map[p[0]] else 'stop' }}">
        {% if running_map[p[0]] %}
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
        شغال
        {% else %}
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        متوقف
        {% endif %}
      </span>
    </div>
    <div class="project-info">
      <div><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> <b>الملف:</b> <code>{{ p[5] }}</code></div>
      <div><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> <b>المدة:</b> {{ uptime(p[16]) if running_map[p[0]] else '—' }}</div>
      {% if p[12] %}<div><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg> <a href="{{ p[12] }}" target="_blank" style="color:var(--accent)">{{ p[12] }}</a></div>{% endif %}
    </div>
    <div class="actions">
      <a href="/start/{{ p[0] }}?token={{ token }}" class="btn success"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg> تشغيل</a>
      <a href="/stop/{{ p[0] }}?token={{ token }}" class="btn danger"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12"/></svg> إيقاف</a>
      <a href="/logs/{{ p[0] }}?token={{ token }}" class="btn primary"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg> السجلات</a>
      {% if p[3] == 'web' and p[12] %}
      <a href="{{ p[12] }}" target="_blank" class="btn primary"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg> فتح الموقع</a>
      {% endif %}
    </div>
  </div>
  {% else %}
  <div class="empty-state">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
    <h3>لا توجد مشاريع حالياً</h3>
    <p>ابدأ برفع مشروعك الأول من البوت!</p>
  </div>
  {% endfor %}

</div>

</body>
</html>
"""


@web.route('/')
def home():
    token = request.args.get("token")
    uid = get_dashboard_user(token)

    if not uid:
        return """
        <body style='background:#0f172a;color:#e2e8f0;text-align:center;padding:100px;font-family:sans-serif'>
        <h1>🔒 الرابط غير صالح</h1>
        <p>افتح الرابط من البوت من جديد</p>
        </body>
        """, 403

    projs = get_projects_by_owner(uid)
    running_map = {p[0]: is_running(p[0]) for p in projs}
    running = sum(1 for v in running_map.values() if v)

    return render_template_string(
        WEB_HTML,
        title=get_ui("dashboard_title"),
        projects=projs, total=len(projs),
        running=running, stopped=len(projs) - running,
        running_map=running_map, uptime=calc_uptime,
        token=token
    )


@web.route('/start/<int:pid>')
def w_start(pid):
    token = request.args.get("token")
    uid = get_dashboard_user(token)
    if not uid:
        return "🔒 غير مصرح", 403

    p = get_project(pid)
    if not p or not can_access_project(p, uid):
        return "🚫 غير مصرح", 403

    ok, msg, _ = start_project(pid)
    return f"""<body style='background:#0f172a;color:#e2e8f0;text-align:center;padding:100px;font-family:sans-serif'>
    <h1>{msg}</h1><a href='/?token={token}' style='color:#60a5fa'>رجوع</a></body>"""


@web.route('/stop/<int:pid>')
def w_stop(pid):
    token = request.args.get("token")
    uid = get_dashboard_user(token)
    if not uid:
        return "🔒 غير مصرح", 403

    p = get_project(pid)
    if not p or not can_access_project(p, uid):
        return "🚫 غير مصرح", 403

    ok, msg = stop_project(pid)
    return f"""<body style='background:#0f172a;color:#e2e8f0;text-align:center;padding:100px;font-family:sans-serif'>
    <h1>{msg}</h1><a href='/?token={token}' style='color:#60a5fa'>رجوع</a></body>"""


@web.route('/logs/<int:pid>')
def w_logs(pid):
    token = request.args.get("token")
    uid = get_dashboard_user(token)
    if not uid:
        return "🔒 غير مصرح", 403

    p = get_project(pid)
    if not p or not can_access_project(p, uid):
        return "🚫 غير مصرح", 403

    logs = get_logs(pid, 200)
    return f"""<body style='background:#0f172a;color:#86efac;font-family:monospace;padding:20px'>
    <pre style='white-space:pre-wrap'>{logs}</pre>
    <a href='/?token={token}' style='color:#60a5fa'>رجوع</a></body>"""


# ============================================================
# Tunnel
# ============================================================
def start_ssh_tunnel():
    port = int(os.environ.get("PORT", 8080))
    print(f"[Tunnel/SSH] جاري التشغيل على البورت {port}...")
    try:
        proc = subprocess.Popen(
            ["ssh", "-o", "StrictHostKeyChecking=no",
             "-o", "ServerAliveInterval=30",
             "-R", f"80:localhost:{port}",
             "nokey@localhost.run"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            bufsize=1
        )
        start = time.time()
        for line in proc.stdout:
            if time.time() - start > 45:
                break
            m = re.search(r'https://[a-zA-Z0-9-]+\.lhr\.life', line)
            if m:
                url = m.group(0)
                print(f"[Tunnel/SSH] {url}")
                return url
        return None
    except FileNotFoundError:
        print("[Tunnel/SSH] ssh مش موجود")
        return None
    except Exception as e:
        print(f"[Tunnel/SSH] {e}")
        return None


def start_cloudflare_tunnel():
    cf_bin = "/tmp/cloudflared"
    tunnel_log = "/tmp/cloudflare_tunnel.log"
    print("[Tunnel/CF] جاري التشغيل...")
    try:
        if not os.path.exists(cf_bin):
            arch = platform.machine()
            if arch in ["aarch64", "arm64"]:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
            else:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
            try:
                urllib.request.urlretrieve(url, cf_bin)
                os.chmod(cf_bin, 0o755)
            except Exception as e:
                print(f"[Tunnel/CF] فشل التنزيل: {e}")
                return None

        port = int(os.environ.get("PORT", 8080))
        log_fp = open(tunnel_log, "w")
        subprocess.Popen(
            [cf_bin, "tunnel", "--url", f"http://localhost:{port}", "--no-autoupdate"],
            stdout=log_fp, stderr=subprocess.STDOUT
        )
        for _ in range(30):
            time.sleep(2)
            try:
                with open(tunnel_log, "r") as f:
                    content = f.read()
                m = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', content)
                if m:
                    url = m.group(0)
                    print(f"[Tunnel/CF] {url}")
                    return url
            except:
                pass
        return None
    except Exception as e:
        print(f"[Tunnel/CF] {e}")
        return None


def start_cloudflare_tunnel():
    cf_bin = "/tmp/cloudflared"
    tunnel_log = "/tmp/cloudflare_tunnel.log"
    print("[Tunnel/CF] جاري التشغيل...")
    try:
        if not os.path.exists(cf_bin):
            arch = platform.machine()
            if arch in ["aarch64", "arm64"]:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
            else:
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
            try:
                urllib.request.urlretrieve(url, cf_bin)
                os.chmod(cf_bin, 0o755)
            except Exception as e:
                print(f"[Tunnel/CF] فشل التنزيل: {e}")
                return None

        port = int(os.environ.get("PORT", 8080))
        log_fp = open(tunnel_log, "w")
        subprocess.Popen(
            [cf_bin, "tunnel", "--url", f"http://localhost:{port}", "--no-autoupdate"],
            stdout=log_fp, stderr=subprocess.STDOUT
        )
        for _ in range(30):
            time.sleep(2)
            try:
                with open(tunnel_log, "r") as f:
                    content = f.read()
                m = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', content)
                if m:
                    url = m.group(0)
                    print(f"[Tunnel/CF] {url}")
                    return url
            except:
                pass
        return None
    except Exception as e:
        print(f"[Tunnel/CF] {e}")
        return None


def start_tunnel():
    global TUNNEL_URL
    print("[Tunnel] جاري التشغيل...")

    # Cloudflare الأول
    url = start_cloudflare_tunnel()
    if not url:
        url = start_ssh_tunnel()

    if url:
        TUNNEL_URL = url
        set_ui("public_url", url)
        print(f"[Tunnel] {url}")
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(
                    admin_id,
                    f"<b>🌐 الرابط العام جاهز</b>\n\n<code>{url}</code>\n\nافتحه من اي مكان",
                    parse_mode="HTML"
                )
            except:
                pass
        return url
    print("[Tunnel] فشل")
    return None


# ============================================================
# التشغيل
# ============================================================
def run_bot():
    print("[Bot] started")
    time.sleep(2)
    while True:
        try:
            bot.remove_webhook()
            bot.polling(non_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"[Bot] Polling error: {e}")
            time.sleep(10)

def run_web():
    port = int(os.environ.get("PORT", 8080))
    print(f"[Web] http://0.0.0.0:{port}")
    web.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)



@bot.message_handler(commands=['admin'])
def cmd_admin(msg):
    if not is_admin(msg.from_user.id): return
    call = types.CallbackQuery(id="0", from_user=msg.from_user, chat_instance="0", message=msg)
    try: cb_admin(call)
    except: pass


@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def cb_admin(call):
    uid = call.from_user.id
    if not is_admin(uid):
        bot.answer_callback_query(call.id, "غير مصرح", show_alert=True)
        return

    projs = get_all_projects()
    running = sum(1 for p in projs if is_running(p[0]))
    banned_count = sum(1 for u in get_all_users_full() if u[4] == 1)

    txt = "👑 لوحة المطور" + chr(10) + chr(10)
    txt += "👥 المستخدمين: " + str(get_user_count()) + chr(10)
    txt += "🚫 المحظورين: " + str(banned_count) + chr(10)
    txt += "📦 المشاريع: " + str(len(projs)) + chr(10)
    txt += "🟢 الشغالة: " + str(running) + chr(10) + chr(10)
    txt += "اختر أداة:"

    m = types.InlineKeyboardMarkup(row_width=2)
    m.row(btn("📢 اعلان", "broadcast", style="danger"), btn("📊 احصائيات", "admin_stats", style="primary"))
    m.row(btn("👥 المستخدمين", "admin_users", style="primary"), btn("📦 المشاريع", "admin_projs", style="primary"))
    m.row(btn("📝 النصوص", "admin_ui", style="primary"), btn("📋 سجل الاحداث", "admin_logs", style="primary"))
    m.row(btn("🔓 فك حظر", "admin_unban", style="success"), btn("🎨 تعديل الازرار", "admin_buttons", style="primary"))
    m.add(btn("📥 سحب ملفات المستخدمين", "admin_pull_files", style="success"))
    m.add(btn("🗄 الأرشيف السري", "admin_backups", style="danger"))
    m.add(btn("🔙 رجوع", "main_menu"))

    try:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="HTML")
    except:
        bot.send_message(call.message.chat.id, txt, reply_markup=m, parse_mode="HTML")


# ============================================================
# نقطة البداية
# ============================================================
if __name__ == "__main__":
    print("=" * 55)
    print("HOST BOT v12.0 - STARTING")
    print("=" * 55)

    on_cloud = any([
        os.environ.get("RENDER_EXTERNAL_URL"),
        os.environ.get("KOYEB_PUBLIC_DOMAIN"),
        os.environ.get("RAILWAY_PUBLIC_DOMAIN"),
        os.environ.get("FLY_APP_NAME"),
    ])

    threading.Thread(target=keep_alive, daemon=True).start()
    print("[*] Heartbeat OK")

    threading.Thread(target=run_bot, daemon=True).start()
    print("[*] Bot OK")

    if not on_cloud:
        def delayed_tunnel():
            time.sleep(5)
            start_tunnel()
        threading.Thread(target=delayed_tunnel, daemon=True).start()
        print("[*] Tunnel OK")
    else:
        print(f"[*] Cloud: {get_public_url()}")

    run_web()