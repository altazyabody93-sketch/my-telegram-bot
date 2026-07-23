"""Single-file social platform — Render-ready.

This is a Render-Web-Service-ready single-file build of the social platform.
It bundles configuration, models, auth, posts, admin, main, forms, and utils
into one `app.py` so it can be deployed to Render.com as a Web Service with
no extra files (other than templates, static, and requirements.txt).

Render-specific features wired in here:
  - Reads all config from environment variables (SECRET_KEY, DATABASE_URL,
    ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD, FLASK_DEBUG, etc.)
  - Auto-converts `postgres://` URIs to `postgresql://` for SQLAlchemy.
  - Binds to 0.0.0.0:$PORT for gunicorn / Render.
  - Health check endpoints: /healthz (liveness) and / (root).
  - Safe static serving via WhiteNoise in production.
  - Bootstrap admin user is created on first run from env vars.
  - Auto-creates tables on first run (and can run lightweight migrations
    via the `/admin/migrate` route guarded by a secret token).
  - Graceful shutdown, request size limits, security headers, caching.

Local dev:
    pip install -r requirements.txt
    python app.py

Production (Render):
    Build:  pip install -r requirements.txt
    Start:  gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
    Health: /healthz
"""

import logging
import os
import secrets
import sys
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from flask import (
    Blueprint, Flask, abort, current_app, flash, jsonify, redirect,
    render_template, request, url_for,
)
from flask_login import (
    LoginManager, UserMixin, current_user, login_required, login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from PIL import Image, UnidentifiedImageError
from sqlalchemy import or_, text
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from wtforms import (
    BooleanField, PasswordField, StringField, SubmitField, TextAreaField,
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, Regexp, ValidationError,
)


# =============================================================================
# Bootstrap logging early so config issues surface in Render logs.
# =============================================================================
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("app")


# =============================================================================
# config
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent


def _env_bool(key: str, default: bool = False) -> bool:
    """Parse a boolean-ish env var (1/true/yes/on => True)."""
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on", "y", "t")


class Config:
    # ---- Core Flask ----
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production-2026")

    # Render sets IS_RENDER=true on hosted services; we use it to switch on
    # production defaults.
    IS_RENDER = _env_bool("IS_RENDER", default=False)
    DEBUG = _env_bool("FLASK_DEBUG", default=False)

    # ---- Database ----
    # Render provides DATABASE_URL for managed Postgres. Fall back to a local
    # SQLite file for development.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'social.db'}",
    )
    # Render's DATABASE_URL starts with postgres:// but SQLAlchemy 1.4+ wants
    # postgresql://. Normalize it.
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://", "postgresql://", 1
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Engine options useful for serverless / free-tier Postgres on Render.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,  # seconds; Render closes idle conns aggressively
    }

    # ---- Uploads ----
    UPLOAD_FOLDER_IMAGES = str(BASE_DIR / "static" / "uploads" / "images")
    UPLOAD_FOLDER_VIDEOS = str(BASE_DIR / "static" / "uploads" / "videos")
    UPLOAD_FOLDER_AVATARS = str(BASE_DIR / "static" / "avatars")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", "200")) * 1024 * 1024

    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "ogg", "mov", "avi", "mkv"}

    # ---- Bootstrap admin ----
    BOOTSTRAP_ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    BOOTSTRAP_ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    BOOTSTRAP_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123456")

    # ---- Security / proxy ----
    # Set to 1 on Render (or any setup behind a proxy / load balancer).
    PREFER_PROXY_FIX = _env_bool("RENDER", default=False) or _env_bool("PREFER_PROXY_FIX", default=False)
    # Render's external URL (e.g. https://myapp.onrender.com). Used for safe
    # redirects and absolute URL generation.
    EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("EXTERNAL_URL")
    # Optional shared secret that lets a one-off `/admin/migrate` call perform
    # lightweight DB maintenance. If unset, the route is disabled.
    MIGRATE_TOKEN = os.environ.get("MIGRATE_TOKEN")

    # ---- Session / cookie hardening ----
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", default=False)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)


# =============================================================================
# models
# =============================================================================
db = SQLAlchemy()


# ---------------------- Association table: likes ----------------------
post_likes = db.Table(
    "post_likes",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    db.Column("post_id", db.Integer, db.ForeignKey("post.id", ondelete="CASCADE"), primary_key=True),
    db.Column("created_at", db.DateTime, default=datetime.utcnow),
)


# ---------------------- User ----------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    bio = db.Column(db.String(500))
    avatar = db.Column(db.String(200), default="default_avatar.png")
    role = db.Column(db.String(20), default="user", nullable=False)  # "admin" | "user"
    is_active_flag = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    posts = db.relationship(
        "Post", backref="author", lazy="dynamic",
        cascade="all, delete-orphan", foreign_keys="Post.user_id",
    )
    comments = db.relationship(
        "Comment", backref="author", lazy="dynamic",
        cascade="all, delete-orphan", foreign_keys="Comment.user_id",
    )
    liked_posts = db.relationship(
        "Post", secondary=post_likes,
        back_populates="liked_by", lazy="dynamic",
    )

    def set_password(self, raw: str) -> None:
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_active(self) -> bool:  # noqa: D401
        return self.is_active_flag

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


# ---------------------- Post ----------------------
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    media_type = db.Column(db.String(10))  # "image" | "video" | None
    media_filename = db.Column(db.String(255))  # relative path under /static/uploads/...
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    comments = db.relationship(
        "Comment", backref="post", lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="Comment.created_at.asc()",
    )
    liked_by = db.relationship(
        "User", secondary=post_likes,
        back_populates="liked_posts", lazy="dynamic",
    )

    @property
    def like_count(self) -> int:
        return self.liked_by.count()

    @property
    def comment_count(self) -> int:
        return self.comments.count()

    def is_liked_by(self, user) -> bool:
        if user is None or not user.is_authenticated:
            return False
        return self.liked_by.filter_by(id=user.id).count() > 0

    def __repr__(self) -> str:
        return f"<Post #{self.id} by user {self.user_id}>"


# ---------------------- Comment ----------------------
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Comment #{self.id} on post {self.post_id}>"


# =============================================================================
# forms
# =============================================================================

# -------- Custom validators --------
class UniqueUsername:
    def __init__(self, exclude_user_id=None):
        self.exclude_user_id = exclude_user_id

    def __call__(self, form, field):
        q = User.query.filter_by(username=field.data)
        if self.exclude_user_id is not None:
            q = q.filter(User.id != self.exclude_user_id)
        if q.first():
            raise ValidationError("اسم المستخدم مستخدم بالفعل.")


class UniqueEmail:
    def __init__(self, exclude_user_id=None):
        self.exclude_user_id = exclude_user_id

    def __call__(self, form, field):
        q = User.query.filter_by(email=field.data)
        if self.exclude_user_id is not None:
            q = q.filter(User.id != self.exclude_user_id)
        if q.first():
            raise ValidationError("البريد الإلكتروني مستخدم بالفعل.")


class SignupForm(FlaskForm):
    username = StringField(
        "اسم المستخدم",
        validators=[
            DataRequired(message="اسم المستخدم مطلوب."),
            Length(min=3, max=64, message="يجب أن يكون بين 3 و 64 حرفًا."),
            Regexp(r"^[A-Za-z0-9_.\-]+$",
                   message="مسموح فقط بالحروف الإنجليزية والأرقام و _ . -"),
            UniqueUsername(),
        ],
    )
    email = StringField(
        "البريد الإلكتروني",
        validators=[
            DataRequired(message="البريد الإلكتروني مطلوب."),
            Email(message="صيغة البريد غير صحيحة."),
            Length(max=120),
            UniqueEmail(),
        ],
    )
    full_name = StringField("الاسم الكامل", validators=[Length(max=120)])
    password = PasswordField(
        "كلمة المرور",
        validators=[
            DataRequired(),
            Length(min=6, max=128, message="يجب أن تكون 6 أحرف على الأقل."),
        ],
    )
    confirm = PasswordField(
        "تأكيد كلمة المرور",
        validators=[DataRequired(), EqualTo("password", message="كلمتا المرور غير متطابقتين.")],
    )
    submit = SubmitField("إنشاء الحساب")


class LoginForm(FlaskForm):
    identifier = StringField(
        "اسم المستخدم أو البريد الإلكتروني",
        validators=[DataRequired(), Length(max=120)],
    )
    password = PasswordField("كلمة المرور", validators=[DataRequired()])
    remember = BooleanField("تذكرني")
    submit = SubmitField("تسجيل الدخول")


class PostForm(FlaskForm):
    content = TextAreaField(
        "النص",
        validators=[
            DataRequired(message="لا يمكن نشر منشور فارغ."),
            Length(min=1, max=5000, message="النص طويل جدًا (الحد 5000 حرف)."),
        ],
    )
    media = FileField(
        "صورة أو فيديو (اختياري)",
        validators=[
            FileAllowed(
                ["png", "jpg", "jpeg", "gif", "webp", "bmp",
                 "mp4", "webm", "ogg", "mov", "avi", "mkv"],
                message="نوع الملف غير مدعوم.",
            ),
        ],
    )
    submit = SubmitField("نشر")


class CommentForm(FlaskForm):
    content = TextAreaField(
        "أضف تعليقًا",
        validators=[
            DataRequired(message="لا يمكن إرسال تعليق فارغ."),
            Length(min=1, max=1000),
        ],
    )
    submit = SubmitField("إرسال")


class ProfileForm(FlaskForm):
    full_name = StringField("الاسم الكامل", validators=[Length(max=120)])
    bio = TextAreaField("نبذة", validators=[Length(max=500)])
    avatar = FileField(
        "الصورة الشخصية",
        validators=[FileAllowed(["png", "jpg", "jpeg", "gif", "webp"], "صورة فقط.")],
    )
    submit = SubmitField("حفظ التغييرات")


class ChangePasswordForm(FlaskForm):
    current = PasswordField("كلمة المرور الحالية", validators=[DataRequired()])
    new = PasswordField("كلمة المرور الجديدة", validators=[
        DataRequired(), Length(min=6, max=128),
    ])
    confirm = PasswordField("تأكيد كلمة المرور الجديدة", validators=[
        DataRequired(), EqualTo("new", message="كلمتا المرور غير متطابقتين."),
    ])
    submit = SubmitField("تغيير كلمة المرور")


# =============================================================================
# utils (file handling, render-specific helpers)
# =============================================================================
def _ext(filename: str, default: str = "") -> str:
    if "." not in filename:
        return default
    return filename.rsplit(".", 1)[1].lower()


def save_media(file_storage, kind: str):
    """Save an image or video. Returns (relative_path, error)."""
    if file_storage is None or not file_storage.filename:
        return None, ""

    original = secure_filename(file_storage.filename)
    if not original:
        return None, "اسم الملف غير صالح."

    ext = _ext(original)
    image_exts = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    video_exts = current_app.config["ALLOWED_VIDEO_EXTENSIONS"]

    if kind == "image" and ext not in image_exts:
        return None, "نوع الصورة غير مدعوم."
    if kind == "video" and ext not in video_exts:
        return None, "نوع الفيديو غير مدعوم."

    target_dir = Path(
        current_app.config["UPLOAD_FOLDER_IMAGES"] if kind == "image"
        else current_app.config["UPLOAD_FOLDER_VIDEOS"]
    )
    target_dir.mkdir(parents=True, exist_ok=True)

    new_name = f"{secrets.token_hex(8)}.{ext}"
    dest = target_dir / new_name
    file_storage.save(dest)

    if kind == "image":
        try:
            with Image.open(dest) as im:
                im.verify()  # cheap validation
        except (UnidentifiedImageError, Exception):
            dest.unlink(missing_ok=True)
            return None, "الملف ليس صورة صالحة."

    relative = f"uploads/{'images' if kind == 'image' else 'videos'}/{new_name}"
    return relative, ""


def save_avatar(file_storage):
    """Save an avatar image. Returns (relative_path, error)."""
    if file_storage is None or not file_storage.filename:
        return None, ""

    original = secure_filename(file_storage.filename)
    ext = _ext(original)
    if ext not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return None, "نوع الصورة غير مدعوم."

    target_dir = Path(current_app.config["UPLOAD_FOLDER_AVATARS"])
    target_dir.mkdir(parents=True, exist_ok=True)

    new_name = f"avatar_{secrets.token_hex(6)}.{ext}"
    dest = target_dir / new_name
    file_storage.save(dest)

    try:
        with Image.open(dest) as im:
            im.thumbnail((512, 512))
            im.save(dest)
    except Exception:
        dest.unlink(missing_ok=True)
        return None, "الصورة غير صالحة."

    return f"avatars/{new_name}", ""


def remove_media(relative_path) -> None:
    """Best-effort delete a media file given its static-relative path."""
    if not relative_path:
        return
    if relative_path.startswith("static/"):
        relative_path = relative_path[len("static/"):]
    if ".." in relative_path:
        return
    abs_path = Path(current_app.root_path) / "static" / relative_path
    try:
        if abs_path.exists():
            abs_path.unlink()
    except OSError:
        pass


# =============================================================================
# auth blueprint
# =============================================================================
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.feed"))

    form = SignupForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            full_name=(form.full_name.data or "").strip(),
            role="user",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("تم إنشاء الحساب بنجاح! مرحبًا بك 👋", "success")
        next_url = request.args.get("next") or url_for("main.feed")
        return redirect(next_url)

    return render_template("auth/signup.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.feed"))

    form = LoginForm()
    if form.validate_on_submit():
        ident = form.identifier.data.strip()
        user = User.query.filter(
            (User.username == ident) | (User.email == ident.lower())
        ).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("هذا الحساب معطّل.", "warning")
                return redirect(url_for("auth.login"))
            login_user(user, remember=form.remember.data)
            flash(f"أهلًا بك، {user.username}!", "success")
            next_url = request.args.get("next")
            if next_url and not next_url.startswith("/"):
                next_url = None
            return redirect(next_url or url_for("main.feed"))
        flash("بيانات الدخول غير صحيحة.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("تم تسجيل الخروج.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    pw_form = ChangePasswordForm()

    if form.validate_on_submit():
        current_user.full_name = (form.full_name.data or "").strip()
        current_user.bio = (form.bio.data or "").strip()

        if form.avatar.data and form.avatar.data.filename:
            path, err = save_avatar(form.avatar.data)
            if err:
                flash(err, "danger")
            else:
                current_user.avatar = path
        db.session.commit()
        flash("تم تحديث الملف الشخصي.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", form=form, pw_form=pw_form)


@auth_bp.route("/profile/password", methods=["POST"])
@login_required
def change_password():
    pw_form = ChangePasswordForm()
    if pw_form.validate_on_submit():
        if not current_user.check_password(pw_form.current.data):
            flash("كلمة المرور الحالية غير صحيحة.", "danger")
            return redirect(url_for("auth.profile"))
        current_user.set_password(pw_form.new.data)
        db.session.commit()
        flash("تم تغيير كلمة المرور بنجاح.", "success")
        logout_user()
        return redirect(url_for("auth.login"))

    form = ProfileForm(obj=current_user)
    for errs in pw_form.errors.values():
        for e in errs:
            flash(e, "danger")
    return render_template("auth/profile.html", form=form, pw_form=pw_form)


# =============================================================================
# posts blueprint
# =============================================================================
posts_bp = Blueprint("posts", __name__, url_prefix="/posts")


@posts_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if not current_user.is_admin:
        flash("النشر متاح للمديرين فقط.", "warning")
        return redirect(url_for("main.feed"))

    form = PostForm()
    if form.validate_on_submit():
        media_rel = None
        media_type = None

        media = form.media.data
        if media and media.filename:
            filename = media.filename.lower()
            if filename.endswith(tuple(current_app.config["ALLOWED_IMAGE_EXTENSIONS"])):
                rel, err = save_media(media, "image")
                media_type = "image" if rel else None
            else:
                rel, err = save_media(media, "video")
                media_type = "video" if rel else None
            if err:
                flash(err, "danger")
                return render_template("posts/create.html", form=form)
            media_rel = rel

        post = Post(
            user_id=current_user.id,
            content=form.content.data.strip(),
            media_type=media_type,
            media_filename=media_rel,
        )
        db.session.add(post)
        db.session.commit()
        flash("تم نشر المنشور بنجاح.", "success")
        return redirect(url_for("main.feed"))

    return render_template("posts/create.html", form=form)


@posts_bp.route("/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id: int):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    media_rel = post.media_filename
    db.session.delete(post)
    db.session.commit()
    remove_media(media_rel)
    flash("تم حذف المنشور.", "info")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(ok=True)
    return redirect(request.referrer or url_for("main.feed"))


@posts_bp.route("/<int:post_id>/like", methods=["POST"])
@login_required
def toggle_like(post_id: int):
    post = Post.query.get_or_404(post_id)
    if post.is_liked_by(current_user):
        post.liked_by.remove(current_user)
        liked = False
    else:
        post.liked_by.append(current_user)
        liked = True
    db.session.commit()
    return jsonify(ok=True, liked=liked, like_count=post.like_count)


@posts_bp.route("/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id: int):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        c = Comment(
            post_id=post.id,
            user_id=current_user.id,
            content=form.content.data.strip(),
        )
        db.session.add(c)
        db.session.commit()
        flash("تم إضافة تعليقك.", "success")
    else:
        for errs in form.errors.values():
            for e in errs:
                flash(e, "danger")
    return redirect(url_for("main.post_detail", post_id=post.id)
                    + f"#comment-{post.comment_count}")


@posts_bp.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id: int):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id
    if comment.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash("تم حذف التعليق.", "info")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(ok=True)
    return redirect(url_for("main.post_detail", post_id=post_id))


# =============================================================================
# admin blueprint
# =============================================================================
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "users": User.query.count(),
        "posts": Post.query.count(),
        "comments": Comment.query.count(),
        "admins": User.query.filter_by(role="admin").count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/users")
@admin_required
def users():
    q = (request.args.get("q") or "").strip()
    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            User.username.ilike(like),
            User.email.ilike(like),
            User.full_name.ilike(like),
        ))
    users = query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users, q=q)


@admin_bp.route("/users/<int:user_id>/promote", methods=["POST"])
@admin_required
def promote(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("لا يمكنك تعديل صلاحياتك بنفسك.", "warning")
        return redirect(url_for("admin.users"))
    user.role = "admin"
    db.session.commit()
    flash(f"تمت ترقية {user.username} إلى مدير.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/demote", methods=["POST"])
@admin_required
def demote(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("لا يمكنك تعديل صلاحياتك بنفسك.", "warning")
        return redirect(url_for("admin.users"))
    user.role = "user"
    db.session.commit()
    flash(f"تم تخفيض {user.username} إلى مستخدم عادي.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle_active", methods=["POST"])
@admin_required
def toggle_active(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("لا يمكنك تعطيل حسابك بنفسك.", "warning")
        return redirect(url_for("admin.users"))
    user.is_active_flag = not user.is_active_flag
    db.session.commit()
    state = "مفعّل" if user.is_active_flag else "معطّل"
    flash(f"حساب {user.username} الآن {state}.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("لا يمكنك حذف حسابك من هنا.", "warning")
        return redirect(url_for("admin.users"))
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f"تم حذف المستخدم {username} (ومحتواه).", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/posts")
@admin_required
def posts():
    q = (request.args.get("q") or "").strip()
    query = Post.query
    if q:
        like = f"%{q}%"
        query = query.filter(Post.content.ilike(like))
    posts = query.order_by(Post.created_at.desc()).all()
    return render_template("admin/posts.html", posts=posts, q=q)


@admin_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
@admin_required
def delete_post(post_id: int):
    post = Post.query.get_or_404(post_id)
    media_rel = post.media_filename
    db.session.delete(post)
    db.session.commit()
    remove_media(media_rel)
    flash("تم حذف المنشور.", "info")
    return redirect(url_for("admin.posts"))


@admin_bp.route("/comments")
@admin_required
def comments():
    q = (request.args.get("q") or "").strip()
    query = Comment.query
    if q:
        like = f"%{q}%"
        query = query.filter(Comment.content.ilike(like))
    comments = query.order_by(Comment.created_at.desc()).all()
    return render_template("admin/comments.html", comments=comments, q=q)


@admin_bp.route("/comments/<int:comment_id>/delete", methods=["POST"])
@admin_required
def delete_comment(comment_id: int):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash("تم حذف التعليق.", "info")
    return redirect(url_for("admin.comments"))


# =============================================================================
# main blueprint
# =============================================================================
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.feed"))
    return redirect(url_for("auth.login"))


@main_bp.route("/feed")
@login_required
def feed():
    posts = Post.query.order_by(Post.created_at.desc()).limit(50).all()
    return render_template("feed.html", posts=posts, active_nav="feed")


@main_bp.route("/posts/<int:post_id>")
@login_required
def post_detail(post_id: int):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    return render_template(
        "posts/detail.html",
        post=post,
        form=form,
        active_nav="feed",
    )


@main_bp.route("/u/<username>")
@login_required
def user_profile(username: str):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id)\
                     .order_by(Post.created_at.desc()).all()
    return render_template("user_profile.html", profile_user=user, posts=posts)


# =============================================================================
# Render health / ops blueprint
# =============================================================================
ops_bp = Blueprint("ops", __name__)


@ops_bp.route("/healthz")
def healthz():
    """Liveness probe used by Render's health check.

    Returns 200 with a small JSON payload. Does not touch the DB on purpose
    so it stays cheap and won't flap if the DB is briefly down.
    """
    return jsonify(
        status="ok",
        service="social-platform",
        version=os.environ.get("RENDER_SERVICE_VERSION", "dev"),
        render=current_app.config.get("IS_RENDER", False),
        time=datetime.utcnow().isoformat() + "Z",
    ), 200


@ops_bp.route("/readyz")
def readyz():
    """Readiness probe: verifies the DB is reachable."""
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify(status="ready", db="ok"), 200
    except Exception as exc:  # noqa: BLE001
        log.warning("readyz failed: %s", exc)
        return jsonify(status="not-ready", db="error", error=str(exc)), 503


@ops_bp.route("/migrate", methods=["POST", "GET"])
def migrate():
    """Lightweight maintenance endpoint.

    Run on demand from Render (or curl) to apply schema changes. Protected
    by `MIGRATE_TOKEN` env var. If `MIGRATE_TOKEN` is not set the endpoint
    is disabled and returns 404.
    """
    token = current_app.config.get("MIGRATE_TOKEN")
    if not token:
        abort(404)
    supplied = (
        request.headers.get("X-Migrate-Token")
        or request.args.get("token")
        or (request.form.get("token") if request.form else None)
    )
    if not supplied or not secrets.compare_digest(str(supplied), str(token)):
        abort(403)

    # For now: re-run create_all. Swap to Alembic in a follow-up if needed.
    db.create_all()
    _bootstrap_admin(current_app._get_current_object())  # type: ignore[attr-defined]
    return jsonify(status="ok", action="create_all+bootstrap", time=datetime.utcnow().isoformat() + "Z")


# =============================================================================
# app factory + entry point
# =============================================================================
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "الرجاء تسجيل الدخول للوصول إلى هذه الصفحة."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


def _ensure_default_avatar(static_dir: Path) -> None:
    """Generate a default avatar PNG so /static/avatars/... never 404s."""
    avatar_dir = static_dir / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    default = avatar_dir / "default_avatar.png"
    if default.exists():
        return
    try:
        from PIL import ImageDraw  # local import to keep top imports clean
        size = 256
        img = Image.new("RGB", (size, size), (66, 99, 235))
        draw = ImageDraw.Draw(img)
        draw.ellipse((10, 10, size - 10, size - 10), fill=(255, 255, 255))
        draw.ellipse((30, 30, size - 30, size - 30), fill=(200, 215, 245))
        draw.ellipse((90, 70, 166, 146), fill=(120, 150, 220))
        draw.pieslice((60, 140, 196, 280), start=180, end=360, fill=(120, 150, 220))
        img.save(default, "PNG")
    except Exception:
        default.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
            b"\x89\x00\x00\x00\rIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01"
            b"\xc7\x9b\x16\x1c\x00\x00\x00\x00IEND\xaeB`\x82"
        )


def _bootstrap_admin(app: Flask) -> None:
    """Create the first admin user from env vars if no admin exists yet."""
    if User.query.filter_by(role="admin").first():
        return
    username = app.config["BOOTSTRAP_ADMIN_USERNAME"]
    email = app.config["BOOTSTRAP_ADMIN_EMAIL"]
    password = app.config["BOOTSTRAP_ADMIN_PASSWORD"]
    if not (username and email and password):
        log.info("Bootstrap admin skipped: missing env vars.")
        return
    if User.query.filter((User.username == username) | (User.email == email)).first():
        log.info("Bootstrap admin skipped: user/email already exists.")
        return
    admin = User(
        username=username,
        email=email.lower(),
        full_name="مدير النظام",
        role="admin",
    )
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    log.info("Bootstrap admin '%s' created.", username)


# Optional: load .env when present (local dev). On Render this is a no-op
# because env vars are provided by the platform.
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(BASE_DIR / ".env")
except Exception:
    pass


def _attach_static_server(app: Flask) -> None:
    """Serve static files efficiently in production if WhiteNoise is available."""
    try:
        from whitenoise import WhiteNoise  # type: ignore
        app.wsgi_app = WhiteNoise(app.wsgi_app, root=str(app.static_folder))  # type: ignore[assignment]
        log.info("WhiteNoise static server attached.")
    except Exception as e:
        log.info("WhiteNoise not installed (%s); using Flask static handler.", e)


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)

    # Trust the X-Forwarded-* headers from Render's load balancer.
    if app.config.get("PREFER_PROXY_FIX"):
        app.wsgi_app = ProxyFix(  # type: ignore[assignment]
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
        )

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Make sure upload + static dirs exist on every boot.
    for key in ("UPLOAD_FOLDER_IMAGES", "UPLOAD_FOLDER_VIDEOS", "UPLOAD_FOLDER_AVATARS"):
        Path(app.config[key]).mkdir(parents=True, exist_ok=True)
    _ensure_default_avatar(Path(app.static_folder))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(ops_bp)

    # Lightweight security headers (no extra dependency).
    @app.after_request
    def _security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("X-XSS-Protection", "1; mode=block")
        return resp

    # Error handlers
    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(_e):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("errors/500.html"), 500

    @app.context_processor
    def inject_globals():
        return {"now": datetime.utcnow()}

    # Static files (prefer WhiteNoise on prod)
    if not app.config.get("DEBUG"):
        _attach_static_server(app)

    # DB + admin bootstrap
    with app.app_context():
        try:
            db.create_all()
        except Exception as exc:
            log.error("db.create_all() failed: %s", exc)
        try:
            _bootstrap_admin(app)
        except Exception as exc:
            log.error("_bootstrap_admin() failed: %s", exc)

    log.info(
        "App ready. render=%s debug=%s db=%s",
        app.config.get("IS_RENDER"),
        app.config.get("DEBUG"),
        app.config.get("SQLALCHEMY_DATABASE_URI", "").split("@")[-1],
    )
    return app


# WSGI entry point for gunicorn
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
