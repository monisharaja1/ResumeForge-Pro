from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import io
import base64
import os
import sqlite3
import html
import zipfile
import smtplib
import re
import urllib.parse
import urllib.request
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
from functools import wraps
import json
from flask import session, redirect, url_for, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

from database import Database
from pdf_generator import PDFGenerator
from word_generator import WordGenerator
from config import AppConfig
import utils
from resume_assistant import (
    analyze_ats,
    tailor_resume,
    enhance_resume_bullets,
    rewrite_summary_tone,
    plan_skill_gap,
    generate_cover_letter,
    generate_interview_questions,
    create_multilingual_variant,
    optimize_linkedin_profile,
    grammar_fix_resume,
    generate_email_apply_kit,
    quantify_achievement_lines,
    detect_duplicates,
    recommend_templates_ml,
    assist_resume_hybrid,
)

_APP_ROOT = os.path.dirname(os.path.abspath(__file__))


def _looks_like_placeholder_secret(value: str) -> bool:
    v = str(value or "").strip().lower()
    if not v:
        return False
    placeholders = {
        "sk-xxxx",
        "your_openai_api_key",
        "your-api-key",
        "your_api_key",
        "replace_me",
        "replace-this",
        "changeme",
    }
    if v in placeholders:
        return True
    if v.startswith("sk-") and v.endswith("xxxx"):
        return True
    if "your" in v and "key" in v:
        return True
    return False


def _should_override_existing_env(key: str, existing: str) -> bool:
    if not existing:
        return True
    low = (key or "").strip().lower()
    if any(k in low for k in ("key", "token", "secret", "password")):
        return _looks_like_placeholder_secret(existing)
    return False


def _load_env_from_file(path: str) -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                if not key:
                    continue
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                    value = value[1:-1]
                existing = (os.getenv(key) or "").strip()
                if _should_override_existing_env(key, existing):
                    os.environ[key] = value
    except Exception:
        # Keep startup robust even if .env parse fails.
        return


_load_env_from_file(os.path.join(_APP_ROOT, ".env"))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()

app = Flask(__name__, template_folder="template", static_folder="template")
CORS(app)  # Allow front-end requests
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-in-production")
app.permanent_session_lifetime = timedelta(minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", "45")))

db = Database(AppConfig.DB_PATH)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "monisharajap2003@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "monisharaja")
GOOGLE_TEMPLATES_API_KEY = (os.getenv("GOOGLE_TEMPLATES_API_KEY") or "").strip()
GOOGLE_TEMPLATES_CSE_ID = (os.getenv("GOOGLE_TEMPLATES_CSE_ID") or "").strip()
GOOGLE_TEMPLATES_DEFAULT_QUERY = (os.getenv("GOOGLE_TEMPLATES_DEFAULT_QUERY") or "resume template").strip()


def _auth_conn():
    conn = sqlite3.connect(AppConfig.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_auth_db():
    with _auth_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created TIMESTAMP,
                approved_at TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                created TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                details TEXT,
                created TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS job_tracker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'saved',
                job_link TEXT,
                notes TEXT,
                jd_text TEXT,
                follow_up_date TEXT,
                reminder_enabled INTEGER NOT NULL DEFAULT 0,
                created TIMESTAMP,
                updated TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS public_resume_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                title TEXT,
                resume_json TEXT NOT NULL,
                expires_at TIMESTAMP,
                created TIMESTAMP,
                revoked INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS score_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                resume_title TEXT,
                score INTEGER NOT NULL,
                source TEXT NOT NULL,
                created TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                display_name TEXT,
                email TEXT,
                phone TEXT,
                city TEXT,
                address TEXT,
                headline TEXT,
                linkedin TEXT,
                github TEXT,
                website TEXT,
                bio TEXT,
                profile_pic TEXT,
                created TIMESTAMP,
                updated TIMESTAMP
            )
        """)
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(job_tracker)").fetchall()}
        if "follow_up_date" not in cols:
            conn.execute("ALTER TABLE job_tracker ADD COLUMN follow_up_date TEXT")
        if "reminder_enabled" not in cols:
            conn.execute("ALTER TABLE job_tracker ADD COLUMN reminder_enabled INTEGER NOT NULL DEFAULT 0")


def _current_user_id() -> int:
    """Resolve user id for authenticated sessions and local dev mode."""
    uid = session.get("user_id")
    if uid is None:
        # React local dev uses auth bypass in auth_guard; keep profile usable.
        return 1
    try:
        return int(uid)
    except Exception:
        return 1


def _log_audit(action: str, details: str = ""):
    with _auth_conn() as conn:
        conn.execute(
            "INSERT INTO audit_logs (user_id, username, action, details, created) VALUES (?, ?, ?, ?, ?)",
            (
                session.get("user_id"),
                session.get("user_name"),
                action,
                details,
                datetime.now().isoformat(),
            ),
        )


def _quick_resume_score(resume) -> int:
    score = 0
    if getattr(resume, "full_name", ""):
        score += 10
    if getattr(resume, "email", ""):
        score += 10
    if getattr(resume, "phone", ""):
        score += 6
    if len(getattr(resume, "skills", []) or []) >= 5:
        score += 14
    if len(getattr(resume, "experiences", []) or []) >= 1:
        score += 20
    if len(getattr(resume, "educations", []) or []) >= 1:
        score += 14
    if len(getattr(resume, "projects", []) or []) >= 1:
        score += 12
    if getattr(resume, "summary", "") and len((resume.summary or "").strip()) >= 40:
        score += 14
    return min(100, score)


def _record_score_history(resume, source: str):
    try:
        with _auth_conn() as conn:
            conn.execute(
                "INSERT INTO score_history (user_id, resume_title, score, source, created) VALUES (?, ?, ?, ?, ?)",
                (
                    session.get("user_id"),
                    getattr(resume, "title", "") or getattr(resume, "full_name", "") or "Untitled",
                    _quick_resume_score(resume),
                    source,
                    datetime.now().isoformat(),
                ),
            )
    except Exception:
        pass


def _extract_text_from_uploaded_file(file_storage) -> tuple[str, str]:
    filename = (getattr(file_storage, "filename", "") or "").lower()
    raw = file_storage.read() or b""
    if not raw:
        return "", "empty"

    if filename.endswith(".pdf"):
        try:
            from pypdf import PdfReader  # optional dependency
            reader = PdfReader(io.BytesIO(raw))
            text = "\n".join([(p.extract_text() or "") for p in reader.pages]).strip()
            return text, "pdf"
        except Exception as e:
            raise ValueError(f"PDF parse failed: {e}")

    if filename.endswith(".docx"):
        try:
            from docx import Document  # optional dependency
            doc = Document(io.BytesIO(raw))
            text = "\n".join([p.text for p in doc.paragraphs if p.text]).strip()
            return text, "docx"
        except Exception as e:
            raise ValueError(f"DOCX parse failed: {e}")

    # txt/doc/rtf fallback
    try:
        text = raw.decode("utf-8", errors="ignore")
    except Exception:
        text = raw.decode("latin-1", errors="ignore")
    return text.strip(), "text"


def _parse_resume_text_light(text: str) -> dict:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    email_match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text or "", flags=re.I)
    phone_match = re.search(r"(\+?\d[\d\s\-()]{8,}\d)", text or "")
    name_guess = ""
    for ln in lines[:8]:
        if len(ln) >= 3 and len(ln) <= 48 and "@" not in ln and not re.search(r"\d{3,}", ln):
            name_guess = ln
            break
    summary = " ".join(lines[:8])[:1200]

    def _find_section_block(section_titles: list[str]) -> list[str]:
        lower = [ln.lower() for ln in lines]
        start = -1
        for i, ln in enumerate(lower):
            if any(t in ln for t in section_titles):
                start = i + 1
                break
        if start < 0:
            return []
        end = len(lines)
        next_heads = [
            "experience", "education", "project", "skill", "certification",
            "language", "achievement", "summary", "objective", "profile",
        ]
        for j in range(start, len(lines)):
            l = lower[j]
            if any(h in l for h in next_heads) and j > start + 1:
                end = j
                break
        return lines[start:end]

    exp_block = _find_section_block(["experience", "work history", "employment"])
    edu_block = _find_section_block(["education", "academic"])
    skills_block = _find_section_block(["skills", "technical skills", "core skills"])
    title_guess = ""
    for ln in lines[1:6]:
        if len(ln) <= 60 and "@" not in ln and not re.search(r"\d{3,}", ln):
            title_guess = ln
            break

    def _to_pipe_rows(rows: list[str], mode: str) -> list[str]:
        out = []
        for row in rows[:18]:
            if len(row) < 3:
                continue
            if mode == "exp":
                out.append(f"{row} |  |  |  | ")
            elif mode == "edu":
                out.append(f"{row} |  |  |  | ")
            elif mode == "skills":
                out.append(row)
        return out

    return {
        "fullName": name_guess,
        "profileTitle": title_guess,
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(1) if phone_match else "",
        "summary": summary,
        "experiences": "\n".join(_to_pipe_rows(exp_block, "exp")),
        "educations": "\n".join(_to_pipe_rows(edu_block, "edu")),
        "skills": "\n".join(_to_pipe_rows(skills_block, "skills")),
    }


def _send_email(subject: str, body: str, to_email: str):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    from_email = os.getenv("SMTP_FROM", smtp_user or ADMIN_EMAIL)
    if not smtp_host or not smtp_user or not smtp_pass:
        app.logger.warning("SMTP not configured; skipped email to %s: %s", to_email, subject)
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


def _guess_template_for_google_item(title: str, snippet: str) -> str:
    text = f"{title} {snippet}".lower()
    if any(k in text for k in ["executive", "board", "director", "leadership"]):
        return "executive_slate"
    if any(k in text for k in ["corporate", "business", "manager"]):
        return "corporate"
    if any(k in text for k in ["creative", "portfolio", "designer", "visual"]):
        return "creative_split"
    if any(k in text for k in ["minimal", "simple", "clean"]):
        return "modern"
    if any(k in text for k in ["classic", "traditional"]):
        return "classic"
    if any(k in text for k in ["ats", "plain", "machine readable"]):
        return "mono_compact"
    if any(k in text for k in ["sidebar", "two column", "split"]):
        return "metro_sidebar"
    return AppConfig.DEFAULT_TEMPLATE


def _fetch_google_templates(query: str, limit: int) -> list[dict]:
    if not GOOGLE_TEMPLATES_API_KEY or not GOOGLE_TEMPLATES_CSE_ID:
        return []

    prompt = (query or GOOGLE_TEMPLATES_DEFAULT_QUERY or "resume template").strip()
    params = urllib.parse.urlencode({
        "key": GOOGLE_TEMPLATES_API_KEY,
        "cx": GOOGLE_TEMPLATES_CSE_ID,
        "q": f"{prompt} site:docs.google.com",
        "num": max(1, min(10, int(limit or 8))),
        "safe": "active",
    })
    url = f"https://www.googleapis.com/customsearch/v1?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "ResumeForge-Pro/3.0",
        },
    )

    with urllib.request.urlopen(req, timeout=12) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    payload = json.loads(raw or "{}")
    items = payload.get("items", [])
    if not isinstance(items, list):
        items = []

    templates = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        link = str(item.get("link", "") or "").strip()
        if not link:
            continue
        title = str(item.get("title", "") or "").strip() or f"Google Template {idx + 1}"
        snippet = str(item.get("snippet", "") or "").replace("\n", " ").strip()
        display_link = str(item.get("displayLink", "") or "docs.google.com").strip()
        pagemap = item.get("pagemap", {}) if isinstance(item.get("pagemap"), dict) else {}
        thumb = ""
        cse_images = pagemap.get("cse_image", [])
        if isinstance(cse_images, list) and cse_images:
            first = cse_images[0]
            if isinstance(first, dict):
                thumb = str(first.get("src", "") or "").strip()
        template_key = _guess_template_for_google_item(title, snippet)
        templates.append({
            "id": f"google-template-{idx + 1}",
            "name": title,
            "category": "Google Templates",
            "mood": "External",
            "tagline": snippet or f"Source: {display_link}",
            "source": "google",
            "html_template": link,
            "thumbnail": thumb,
            "settings": {
                "template": template_key,
                "accent": AppConfig.ACCENT_COLOR,
                "font": AppConfig.DEFAULT_FONT,
                "pageSize": "letter",
                "compactMode": False,
            },
            "palette": [AppConfig.ACCENT_COLOR, "#e2e8f0", "#ffffff"],
        })
    return templates


def _to_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off", ""}:
        return False
    return default


def _extract_pdf_options(data: dict) -> dict:
    payload = data if isinstance(data, dict) else {}
    settings = payload.get("settings")
    if not isinstance(settings, dict):
        settings = {}

    def pick(*keys, default=None):
        for key in keys:
            value = payload.get(key)
            if value not in (None, ""):
                return value
        for key in keys:
            value = settings.get(key)
            if value not in (None, ""):
                return value
        return default

    template_name = pick(
        "template_name",
        "templateName",
        "template",
        "template_key",
        "templateKey",
        default=AppConfig.DEFAULT_TEMPLATE,
    )
    page_size = str(pick("page_size", "pageSize", default="letter") or "letter").strip().lower()
    if page_size not in {"letter", "a4"}:
        page_size = "letter"

    raw_section_order = pick("section_order", "sectionOrder", default=[])
    if isinstance(raw_section_order, list):
        section_order = [str(x).strip() for x in raw_section_order if str(x).strip()]
    elif isinstance(raw_section_order, str):
        section_order = [x.strip() for x in raw_section_order.split(",") if x.strip()]
    else:
        section_order = []

    raw_font_scale = pick("font_scale", "fontScale", default=1.0)
    try:
        font_scale = float(raw_font_scale)
    except Exception:
        font_scale = 1.0

    margin_preset = str(pick("margin_preset", "marginPreset", default="normal") or "normal").strip().lower()
    if margin_preset not in {"narrow", "compact", "normal", "wide", "relaxed"}:
        margin_preset = "normal"

    raw_section_visibility = pick("section_visibility", "sectionVisibility", default={})
    section_visibility = raw_section_visibility if isinstance(raw_section_visibility, dict) else {}

    return {
        "template_name": template_name,
        "page_size": page_size,
        "layout_override": pick("layout_override", "layoutOverride", "page_layout", "pageLayout"),
        "heading_align_override": pick(
            "heading_align_override",
            "headingAlignOverride",
            "heading_align",
            "headingAlign",
        ),
        "body_align_override": pick(
            "body_align_override",
            "bodyAlignOverride",
            "body_align",
            "bodyAlign",
        ),
        "accent_color_override": pick("accent_color_override", "accentColorOverride", "accent"),
        "font_override": pick("font_override", "fontOverride", "font"),
        "compact_mode": _to_bool(pick("compact_mode", "compactMode", default=False), False),
        "ats_safe_mode": _to_bool(pick("ats_safe_mode", "atsSafeMode", default=False), False),
        "section_order": section_order,
        "font_scale": font_scale,
        "margin_preset": margin_preset,
        "section_visibility": section_visibility,
        "header_layout": pick("header_layout", "headerLayout"),
    }


def _is_public_path(path: str) -> bool:
    public_paths = {
        "/login",
        "/register",
        "/forgot-password",
        "/reset-password",
        "/logout",
        "/admin/login",
        "/api/health",
        "/api/version",
        "/api/ai-assistant",
    }
    if path in public_paths:
        return True
    if path.startswith("/public/"):
        return True
    if path.startswith("/static") or path.startswith("/template"):
        return True
    if path.startswith("/assets") or path.startswith("/html-templates/"):
        return True
    return False

_LOCAL_LOOPBACK_IPS = {"127.0.0.1", "::1", "::ffff:127.0.0.1"}

def _is_local_react_dev_api_call() -> bool:
    """Allow local dev API calls from the same machine without login."""
    remote = (request.remote_addr or "").strip().lower()
    return remote in _LOCAL_LOOPBACK_IPS


@app.before_request
def auth_guard():
    path = request.path
    # Dev convenience: allow React dev server API calls without login.
    # Restrict only to loopback calls from local frontend origins.
    if path.startswith("/api/") and _is_local_react_dev_api_call():
        return None
    # Session timeout for user/admin sessions.
    if session.get("user_authenticated") or session.get("admin_authenticated"):
        now = _utc_now()
        last = session.get("last_activity_utc")
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                if now - last_dt > app.permanent_session_lifetime:
                    session.clear()
                    if path.startswith("/api/"):
                        return jsonify({"error": "Session expired. Please login again."}), 401
                    return redirect(url_for("login"))
            except Exception:
                pass
        session["last_activity_utc"] = _utc_now_iso()

    if _is_public_path(path):
        return None
    if path.startswith("/admin"):
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin_login"))
        return None
    # Guard app pages + APIs for authenticated users
    if not session.get("user_authenticated"):
        if path.startswith("/api/"):
            return jsonify({"error": "Unauthorized. Please login."}), 401
        return redirect(url_for("login"))
    return None


def _login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _is_local_react_dev_api_call():
            return fn(*args, **kwargs)
        if not session.get("user_authenticated"):
            return jsonify({"error": "Unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper


_init_auth_db()

# ---------- Serve Front-End ----------
@app.route('/')
def index():
    dist_dir = os.path.join("frontend", "dist")
    index_file = os.path.join(dist_dir, "index.html")
    if os.path.exists(index_file):
        return send_from_directory(dist_dir, "index.html")
    return "Frontend build not found. Run `npm run build` in `frontend`.", 503


@app.route('/templates_catalog.json')
def templates_catalog():
    """Serve template catalog from project template folder for frontend gallery."""
    return send_from_directory("template", "templates_catalog.json")


@app.route('/assets/<path:filename>')
def template_assets(filename):
    """Serve React build assets first, then template preview asset files."""
    react_assets_dir = os.path.join("frontend", "dist", "assets")
    react_asset = os.path.join(react_assets_dir, filename)
    if os.path.exists(react_asset):
        return send_from_directory(react_assets_dir, filename)
    return send_from_directory(os.path.join("template", "assets"), filename)


@app.route('/html-templates/<path:filename>')
def html_template_file(filename):
    """Serve static HTML resume templates for template previews."""
    return send_from_directory(os.path.join("template", "html_templates"), filename)


@app.route('/vite.svg')
def vite_svg():
    """Serve Vite favicon from the React build output if present."""
    dist_dir = os.path.join("frontend", "dist")
    icon_file = os.path.join(dist_dir, "vite.svg")
    if os.path.exists(icon_file):
        return send_from_directory(dist_dir, "vite.svg")
    return "", 404


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        username_or_email = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        with _auth_conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username=? OR email=?",
                (username_or_email, username_or_email)
            ).fetchone()
        if not row or not check_password_hash(row["password_hash"], password):
            error = "Invalid credentials."
        else:
            session.permanent = True
            session["user_authenticated"] = True
            session["user_id"] = row["id"]
            session["user_name"] = row["username"]
            session["user_status"] = row["status"]
            session["last_activity_utc"] = _utc_now_iso()
            return redirect(url_for("index"))
    return render_template_string("""
<!doctype html><html><head><title>ResumeForge Pro</title>
<style>
body{
  font-family:Arial,Helvetica,sans-serif;
  margin:0;
  min-height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
  padding:24px;
  background:linear-gradient(140deg,#dbeafe 0%,#cffafe 48%,#ecfeff 100%);
}
.box{
  width:min(560px,92vw);
  background:#fff;
  padding:34px 30px;
  border:1px solid #bfdbfe;
  border-radius:16px;
  box-shadow:0 18px 42px rgba(15,23,42,0.12);
}
h2{margin:0 0 14px 0;font-size:32px;color:#0f172a}
.box h1,.box h2{display:none !important}
input,button{width:100%;padding:12px 13px;margin:8px 0;border-radius:10px}
input{border:1px solid #cbd5e1;background:#f8fafc}
.password-wrap{position:relative;margin:8px 0}
.password-wrap input{margin:0;padding-right:44px}
.password-wrap .toggle-pass{
  position:absolute;
  right:8px;
  top:50%;
  transform:translateY(-50%);
  width:30px;
  height:30px;
  margin:0;
  padding:0;
  border:none;
  border-radius:8px;
  background:transparent;
  color:#475569;
  font-size:16px;
  line-height:1;
  cursor:pointer;
}
.password-wrap .toggle-pass:hover{background:#e2e8f0;color:#0f172a}
button{background:#0f766e;color:#fff;border:none;font-weight:700}
button:hover{background:#0b5f58}
a{display:block;margin-top:10px;text-align:center;color:#0f3b66;text-decoration:none}
a:hover{text-decoration:underline}
</style>
</head><body><div class="box">
{% if error %}<p style="color:#b91c1c;">{{error}}</p>{% endif %}
<form method="post">
<input name="username" placeholder="Username or Email" required />
<div class="password-wrap">
<input id="password-field" name="password" type="password" placeholder="Password" required />
<button id="toggle-password" class="toggle-pass" type="button" aria-label="Show password" aria-pressed="false">👁</button>
</div>
<button type="submit">Login</button>
</form>
<a href="/register">Create account</a>
<a href="/forgot-password">Forgot password</a>
<a href="/admin/login">Admin login</a>
<script>
(function () {
  const input = document.getElementById("password-field");
  const toggle = document.getElementById("toggle-password");
  if (!input || !toggle) return;
  toggle.addEventListener("click", function () {
    const isHidden = input.type === "password";
    input.type = isHidden ? "text" : "password";
    toggle.textContent = isHidden ? "🙈" : "👁";
    toggle.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
    toggle.setAttribute("aria-pressed", isHidden ? "true" : "false");
  });
})();
</script>
</div></body></html>
""", error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ""
    err = ""
    if request.method == 'POST':
        email = (request.form.get("email") or "").strip().lower()
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if not email or not username or len(password) < 6:
            err = "Enter email, username and password (min 6 chars)."
        else:
            try:
                with _auth_conn() as conn:
                    conn.execute(
                        "INSERT INTO users (email, username, password_hash, status, created, approved_at) VALUES (?, ?, ?, 'approved', ?, ?)",
                        (email, username, generate_password_hash(password), datetime.now().isoformat(), datetime.now().isoformat())
                    )
                msg = "Account created successfully. You can login now."
            except sqlite3.IntegrityError:
                err = "Username or email already exists."
    return render_template_string("""
<!doctype html><html><head><title>Register</title>
<style>body{font-family:Arial;margin:40px;background:#f3f4f6}.box{max-width:460px;margin:auto;background:#fff;padding:20px;border:1px solid #ddd;border-radius:10px}input,button{width:100%;padding:10px;margin:8px 0}button{background:#0f766e;color:#fff;border:none;border-radius:6px}a{display:block;margin-top:10px;text-align:center}</style>
</head><body><div class="box"><h2>Create Account</h2>
{% if msg %}<p style="color:#166534;">{{msg}}</p>{% endif %}
{% if err %}<p style="color:#b91c1c;">{{err}}</p>{% endif %}
<form method="post">
<input name="email" type="email" placeholder="Email" required />
<input name="username" placeholder="Username" required />
<input name="password" type="password" placeholder="Password (min 6)" required />
<button type="submit">Create Account</button>
</form>
<a href="/login">Back to login</a>
</div></body></html>
""", msg=msg, err=err)


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    msg = ""
    err = ""
    if request.method == 'POST':
        username_or_email = (request.form.get("username") or "").strip()
        with _auth_conn() as conn:
            row = conn.execute(
                "SELECT id, email, username FROM users WHERE username=? OR email=?",
                (username_or_email, username_or_email)
            ).fetchone()
            if row:
                code = f"{secrets.randbelow(1000000):06d}"
                expires_at = (datetime.now() + timedelta(minutes=15)).isoformat()
                conn.execute(
                    "INSERT INTO password_resets (user_id, code, expires_at, created) VALUES (?, ?, ?, ?)",
                    (row["id"], code, expires_at, datetime.now().isoformat())
                )
                _send_email(
                    subject="Resume Builder - Password Reset Code",
                    body=f"Hello {row['username']},\n\nYour reset code is: {code}\nThis code expires in 15 minutes.",
                    to_email=row["email"],
                )
        msg = "If account exists, a reset code has been sent to registered email."
    return render_template_string("""
<!doctype html><html><head><title>Forgot Password</title>
<style>body{font-family:Arial;margin:40px;background:#f3f4f6}.box{max-width:460px;margin:auto;background:#fff;padding:20px;border:1px solid #ddd;border-radius:10px}input,button{width:100%;padding:10px;margin:8px 0}button{background:#0f766e;color:#fff;border:none;border-radius:6px}a{display:block;margin-top:10px;text-align:center}</style>
</head><body><div class="box"><h2>Forgot Password</h2>
{% if msg %}<p style="color:#166534;">{{msg}}</p>{% endif %}
{% if err %}<p style="color:#b91c1c;">{{err}}</p>{% endif %}
<form method="post">
<input name="username" placeholder="Username or Email" required />
<button type="submit">Send Reset Code</button>
</form>
<a href="/reset-password">Already have code? Reset now</a>
<a href="/login">Back to login</a>
</div></body></html>
""", msg=msg, err=err)


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    msg = ""
    err = ""
    if request.method == 'POST':
        username_or_email = (request.form.get("username") or "").strip()
        code = (request.form.get("code") or "").strip()
        new_password = request.form.get("new_password") or ""
        if len(new_password) < 6:
            err = "Password must be at least 6 characters."
        else:
            with _auth_conn() as conn:
                user = conn.execute(
                    "SELECT id, email FROM users WHERE username=? OR email=?",
                    (username_or_email, username_or_email)
                ).fetchone()
                if not user:
                    err = "Invalid details."
                else:
                    reset = conn.execute(
                        "SELECT * FROM password_resets WHERE user_id=? AND code=? AND used=0 ORDER BY id DESC LIMIT 1",
                        (user["id"], code)
                    ).fetchone()
                    if not reset:
                        err = "Invalid reset code."
                    else:
                        if datetime.fromisoformat(reset["expires_at"]) < datetime.now():
                            err = "Reset code expired."
                        else:
                            conn.execute(
                                "UPDATE users SET password_hash=? WHERE id=?",
                                (generate_password_hash(new_password), user["id"])
                            )
                            conn.execute("UPDATE password_resets SET used=1 WHERE id=?", (reset["id"],))
                            msg = "Password updated successfully. You can login now."
    return render_template_string("""
<!doctype html><html><head><title>Reset Password</title>
<style>body{font-family:Arial;margin:40px;background:#f3f4f6}.box{max-width:460px;margin:auto;background:#fff;padding:20px;border:1px solid #ddd;border-radius:10px}input,button{width:100%;padding:10px;margin:8px 0}button{background:#0f766e;color:#fff;border:none;border-radius:6px}a{display:block;margin-top:10px;text-align:center}</style>
</head><body><div class="box"><h2>Reset Password</h2>
{% if msg %}<p style="color:#166534;">{{msg}}</p>{% endif %}
{% if err %}<p style="color:#b91c1c;">{{err}}</p>{% endif %}
<form method="post">
<input name="username" placeholder="Username or Email" required />
<input name="code" placeholder="6-digit code" required />
<input name="new_password" type="password" placeholder="New password" required />
<button type="submit">Reset Password</button>
</form>
<a href="/login">Back to login</a>
</div></body></html>
""", msg=msg, err=err)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    err = ""
    if request.method == 'POST':
        password = request.form.get("password") or ""
        if password == ADMIN_PASSWORD:
            session.permanent = True
            session["admin_authenticated"] = True
            session["last_activity_utc"] = _utc_now_iso()
            return redirect(url_for("admin_requests"))
        err = "Invalid admin password."
    return render_template_string("""
<!doctype html><html><head><title>Admin Login</title>
<style>body{font-family:Arial;margin:40px;background:#f3f4f6}.box{max-width:420px;margin:auto;background:#fff;padding:20px;border:1px solid #ddd;border-radius:10px}input,button{width:100%;padding:10px;margin:8px 0}button{background:#1e3a5f;color:#fff;border:none;border-radius:6px}</style>
</head><body><div class="box"><h2>Admin Login</h2>
{% if err %}<p style="color:#b91c1c;">{{err}}</p>{% endif %}
<form method="post">
<input name="password" type="password" placeholder="Admin password" required />
<button type="submit">Login</button>
</form></div></body></html>
""", err=err)


@app.route('/admin/requests', methods=['GET'])
def admin_requests():
    with _auth_conn() as conn:
        rows = conn.execute("SELECT id, username, email, status, created FROM users ORDER BY created DESC").fetchall()
    return render_template_string("""
<!doctype html><html><head><title>Access Requests</title>
<style>body{font-family:Arial;margin:20px;background:#f9fafb}table{width:100%;border-collapse:collapse;background:#fff}th,td{border:1px solid #ddd;padding:8px;text-align:left}button{padding:6px 10px;margin-right:6px} .ok{background:#166534;color:#fff;border:none}.rej{background:#b91c1c;color:#fff;border:none}</style>
</head><body><h2>Access Requests</h2><p><a href="/admin/analytics">View Analytics</a> | <a href="/admin/audit">View Export Audit</a> | <a href="/logout">Logout</a></p>
<table><tr><th>ID</th><th>Username</th><th>Email</th><th>Status</th><th>Created</th><th>Action</th></tr>
{% for r in rows %}
<tr>
<td>{{r.id}}</td><td>{{r.username}}</td><td>{{r.email}}</td><td>{{r.status}}</td><td>{{r.created}}</td>
<td>
<form style="display:inline;" method="post" action="/admin/approve/{{r.id}}"><button class="ok" type="submit">Approve</button></form>
<form style="display:inline;" method="post" action="/admin/reject/{{r.id}}"><button class="rej" type="submit">Reject</button></form>
</td>
</tr>
{% endfor %}
</table></body></html>
""", rows=rows)


@app.route('/admin/audit', methods=['GET'])
def admin_audit():
    with _auth_conn() as conn:
        logs = conn.execute(
            "SELECT id, user_id, username, action, details, created FROM audit_logs ORDER BY id DESC LIMIT 300"
        ).fetchall()
    return render_template_string("""
<!doctype html><html><head><title>Export Audit</title>
<style>body{font-family:Arial;margin:20px;background:#f9fafb}table{width:100%;border-collapse:collapse;background:#fff}th,td{border:1px solid #ddd;padding:8px;text-align:left;font-size:13px}a{margin-right:10px}</style>
</head><body><h2>Export Audit Logs</h2>
<p><a href="/admin/requests">Back to Requests</a> <a href="/admin/analytics">View Analytics</a> <a href="/logout">Logout</a></p>
<table><tr><th>ID</th><th>User</th><th>Action</th><th>Details</th><th>Time</th></tr>
{% for r in logs %}
<tr><td>{{r.id}}</td><td>{{r.username or ("id:" ~ r.user_id)}}</td><td>{{r.action}}</td><td>{{r.details}}</td><td>{{r.created}}</td></tr>
{% endfor %}
</table></body></html>
""", logs=logs)


def _build_admin_analytics():
    now = datetime.now()
    since_30 = now - timedelta(days=30)
    with _auth_conn() as conn:
        total_users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        resumes_created = conn.execute("SELECT COUNT(*) AS c FROM resumes").fetchone()["c"]

        # "Active users" = users who performed at least one action in last 30 days.
        active_rows = conn.execute(
            "SELECT user_id, created FROM audit_logs WHERE user_id IS NOT NULL ORDER BY id DESC"
        ).fetchall()
        active_users = set()
        for r in active_rows:
            ts = r["created"] or ""
            try:
                if datetime.fromisoformat(ts) >= since_30:
                    active_users.add(r["user_id"])
            except Exception:
                continue

        export_rows = conn.execute(
            """
            SELECT action, details, created
            FROM audit_logs
            WHERE action IN ('export_pdf', 'export_word', 'export_portfolio_html')
            ORDER BY id DESC
            """
        ).fetchall()

    export_count = len(export_rows)
    template_counts = {}
    export_action_counts = {"export_pdf": 0, "export_word": 0, "export_portfolio_html": 0}
    daily_export = {}

    for r in export_rows:
        action = r["action"]
        export_action_counts[action] = export_action_counts.get(action, 0) + 1

        created = r["created"] or ""
        day = created[:10] if len(created) >= 10 else "unknown"
        daily_export[day] = daily_export.get(day, 0) + 1

        if action == "export_pdf":
            details = r["details"] or ""
            tpl = "unknown"
            if "template=" in details:
                try:
                    tail = details.split("template=", 1)[1]
                    tpl = tail.split(";", 1)[0].strip() or "unknown"
                except Exception:
                    tpl = "unknown"
            template_counts[tpl] = template_counts.get(tpl, 0) + 1

    most_used_template = "-"
    if template_counts:
        most_used_template = max(template_counts.items(), key=lambda x: x[1])[0]

    template_labels = list(template_counts.keys())[:10]
    template_values = [template_counts[k] for k in template_labels]
    export_labels = ["PDF", "Word", "Portfolio"]
    export_values = [
        export_action_counts.get("export_pdf", 0),
        export_action_counts.get("export_word", 0),
        export_action_counts.get("export_portfolio_html", 0),
    ]

    # Keep recent 10 days for compact chart.
    daily_labels = sorted(daily_export.keys())[-10:]
    daily_values = [daily_export[d] for d in daily_labels]

    return {
        "total_users": total_users,
        "active_users": len(active_users),
        "resumes_created": resumes_created,
        "most_used_template": most_used_template,
        "export_count": export_count,
        "template_labels": template_labels,
        "template_values": template_values,
        "export_labels": export_labels,
        "export_values": export_values,
        "daily_labels": daily_labels,
        "daily_values": daily_values,
    }


@app.route('/admin/analytics', methods=['GET'])
def admin_analytics():
    data = _build_admin_analytics()
    return render_template_string("""
<!doctype html>
<html>
<head>
  <title>Admin Analytics</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body{font-family:Arial;margin:20px;background:#f3f4f6;color:#111827}
    .top{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:14px}
    .top a{color:#0f766e;text-decoration:none;font-weight:700}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin-bottom:14px}
    .card{background:#fff;border:1px solid #d1d5db;border-radius:10px;padding:12px}
    .k{font-size:12px;color:#6b7280}
    .v{font-size:28px;font-weight:700;margin-top:6px}
    .charts{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    .panel{background:#fff;border:1px solid #d1d5db;border-radius:10px;padding:12px}
    .panel h3{margin:0 0 10px 0}
    @media (max-width: 980px){.charts{grid-template-columns:1fr}}
  </style>
</head>
<body>
  <div class="top">
    <h2 style="margin:0;">Analytics Dashboard</h2>
    <a href="/admin/requests">Back to Requests</a>
    <a href="/admin/audit">Export Audit</a>
    <button id="sendDailyBtn" style="padding:6px 10px;border:1px solid #0f766e;border-radius:8px;background:#0f766e;color:#fff;cursor:pointer;">Send Daily Alert</button>
    <a href="/logout">Logout</a>
  </div>

  <div class="grid">
    <div class="card"><div class="k">Total Users</div><div class="v">{{data.total_users}}</div></div>
    <div class="card"><div class="k">Active Users (30d)</div><div class="v">{{data.active_users}}</div></div>
    <div class="card"><div class="k">Resumes Created</div><div class="v">{{data.resumes_created}}</div></div>
    <div class="card"><div class="k">Most Used Template</div><div class="v" style="font-size:22px">{{data.most_used_template}}</div></div>
    <div class="card"><div class="k">Export Count</div><div class="v">{{data.export_count}}</div></div>
  </div>

  <div class="charts">
    <div class="panel">
      <h3>Template Usage (PDF Exports)</h3>
      <canvas id="tplChart" height="180"></canvas>
    </div>
    <div class="panel">
      <h3>Export Type Split</h3>
      <canvas id="expChart" height="180"></canvas>
    </div>
    <div class="panel" style="grid-column:1 / -1;">
      <h3>Daily Exports (Recent)</h3>
      <canvas id="dailyChart" height="95"></canvas>
    </div>
  </div>

  <script>
    const analytics = {{ analytics_json|safe }};
    const tplCtx = document.getElementById('tplChart');
    const expCtx = document.getElementById('expChart');
    const dailyCtx = document.getElementById('dailyChart');

    new Chart(tplCtx, {
      type: 'bar',
      data: {
        labels: analytics.template_labels.length ? analytics.template_labels : ['No data'],
        datasets: [{
          label: 'PDF Exports',
          data: analytics.template_values.length ? analytics.template_values : [0],
          backgroundColor: '#0f766e'
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });

    new Chart(expCtx, {
      type: 'doughnut',
      data: {
        labels: analytics.export_labels,
        datasets: [{
          data: analytics.export_values,
          backgroundColor: ['#0ea5e9','#f59e0b','#8b5cf6']
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });

    new Chart(dailyCtx, {
      type: 'line',
      data: {
        labels: analytics.daily_labels.length ? analytics.daily_labels : ['No data'],
        datasets: [{
          label: 'Exports',
          data: analytics.daily_values.length ? analytics.daily_values : [0],
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37,99,235,0.18)',
          fill: true,
          tension: 0.3
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });

    const sendDailyBtn = document.getElementById("sendDailyBtn");
    if (sendDailyBtn) {
      sendDailyBtn.addEventListener("click", async () => {
        sendDailyBtn.disabled = true;
        sendDailyBtn.textContent = "Sending...";
        try {
          const res = await fetch("/admin/send-daily-alert", { method: "POST" });
          const data = await res.json();
          alert(data.message || "Daily alert sent.");
        } catch (e) {
          alert("Failed to send daily alert.");
        } finally {
          sendDailyBtn.disabled = false;
          sendDailyBtn.textContent = "Send Daily Alert";
        }
      });
    }
  </script>
</body>
</html>
""", data=data, analytics_json=json.dumps(data))


@app.route('/admin/send-daily-alert', methods=['POST'])
def admin_send_daily_alert():
    data = _build_admin_analytics()
    body = (
        "ResumeForge Pro - Daily Admin Summary\n\n"
        f"Total Users: {data.get('total_users', 0)}\n"
        f"Active Users (30d): {data.get('active_users', 0)}\n"
        f"Resumes Created: {data.get('resumes_created', 0)}\n"
        f"Most Used Template: {data.get('most_used_template', '-')}\n"
        f"Export Count: {data.get('export_count', 0)}\n"
    )
    try:
        _send_email(
            subject="ResumeForge Pro - Daily Analytics Summary",
            body=body,
            to_email=ADMIN_EMAIL,
        )
        return jsonify({"message": f"Daily alert sent to {ADMIN_EMAIL}."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/approve/<int:user_id>', methods=['POST'])
def admin_approve(user_id):
    with _auth_conn() as conn:
        row = conn.execute("SELECT email, username FROM users WHERE id=?", (user_id,)).fetchone()
        if row:
            conn.execute("UPDATE users SET status='approved', approved_at=? WHERE id=?", (datetime.now().isoformat(), user_id))
            _send_email(
                subject="Resume Builder - Access Approved",
                body=f"Hello {row['username']}, your access request has been approved. You can now login.",
                to_email=row["email"],
            )
    return redirect(url_for("admin_requests"))


@app.route('/admin/reject/<int:user_id>', methods=['POST'])
def admin_reject(user_id):
    with _auth_conn() as conn:
        row = conn.execute("SELECT email, username FROM users WHERE id=?", (user_id,)).fetchone()
        if row:
            conn.execute("UPDATE users SET status='rejected' WHERE id=?", (user_id,))
            _send_email(
                subject="Resume Builder - Access Request Rejected",
                body=f"Hello {row['username']}, your access request was rejected.",
                to_email=row["email"],
            )
    return redirect(url_for("admin_requests"))

@app.route('/api/health', methods=['GET'])
def health():
    """Simple health check endpoint for deployments."""
    return jsonify({"status": "ok"})

@app.route('/api/version', methods=['GET'])
def version():
    """Return app identity and version metadata."""
    return jsonify({
        "app": AppConfig.APP_NAME,
        "version": AppConfig.APP_VERSION,
    })


@app.route('/api/user-profile', methods=['GET'])
def get_user_profile():
    user_id = _current_user_id()
    with _auth_conn() as conn:
        row = conn.execute(
            """
            SELECT display_name, email, phone, city, address, headline, linkedin, github, website, bio, profile_pic, updated
            FROM user_profiles
            WHERE user_id=?
            """,
            (user_id,),
        ).fetchone()
    if not row:
        return jsonify({
            "display_name": "",
            "email": "",
            "phone": "",
            "city": "",
            "address": "",
            "headline": "",
            "linkedin": "",
            "github": "",
            "website": "",
            "bio": "",
            "profile_pic": "",
            "updated": "",
        })
    return jsonify({k: row[k] or "" for k in row.keys()})


@app.route('/api/user-profile', methods=['PUT'])
def save_user_profile():
    user_id = _current_user_id()
    data = request.json or {}
    payload = {
        "display_name": (data.get("display_name") or "").strip(),
        "email": (data.get("email") or "").strip(),
        "phone": (data.get("phone") or "").strip(),
        "city": (data.get("city") or "").strip(),
        "address": (data.get("address") or "").strip(),
        "headline": (data.get("headline") or "").strip(),
        "linkedin": (data.get("linkedin") or "").strip(),
        "github": (data.get("github") or "").strip(),
        "website": (data.get("website") or "").strip(),
        "bio": (data.get("bio") or "").strip(),
        "profile_pic": data.get("profile_pic") or "",
    }
    now = datetime.now().isoformat()
    with _auth_conn() as conn:
        exists = conn.execute("SELECT id FROM user_profiles WHERE user_id=?", (user_id,)).fetchone()
        if exists:
            conn.execute(
                """
                UPDATE user_profiles
                SET display_name=?, email=?, phone=?, city=?, address=?, headline=?,
                    linkedin=?, github=?, website=?, bio=?, profile_pic=?, updated=?
                WHERE user_id=?
                """,
                (
                    payload["display_name"], payload["email"], payload["phone"], payload["city"],
                    payload["address"], payload["headline"], payload["linkedin"], payload["github"],
                    payload["website"], payload["bio"], payload["profile_pic"], now, user_id
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO user_profiles
                (user_id, display_name, email, phone, city, address, headline, linkedin, github, website, bio, profile_pic, created, updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id, payload["display_name"], payload["email"], payload["phone"], payload["city"],
                    payload["address"], payload["headline"], payload["linkedin"], payload["github"],
                    payload["website"], payload["bio"], payload["profile_pic"], now, now
                ),
            )
    return jsonify({"message": "User profile saved", "updated": now})


@app.route('/api/import-resume-file', methods=['POST'])
def import_resume_file():
    """Parse uploaded resume file (json/txt/pdf/docx) into form-friendly fields."""
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400
        text, source = _extract_text_from_uploaded_file(file)
        if not text.strip():
            return jsonify({"error": "File text could not be extracted"}), 400
        parsed = _parse_resume_text_light(text)
        parsed["summary"] = parsed.get("summary", "")
        return jsonify({
            "source": source,
            "fields": parsed,
            "message": f"Imported from {source}. Please review and edit fields.",
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"File import failed: {e}")
        return jsonify({"error": str(e)}), 500

# ---------- API Endpoints ----------
@app.route('/api/resumes', methods=['GET'])
def get_all_resumes():
    """Return list of saved resumes."""
    resumes = db.get_all_resumes()
    return jsonify(resumes)

@app.route('/api/resumes/<int:resume_id>', methods=['GET'])
def get_resume(resume_id):
    """Return a specific resume."""
    resume = db.get_resume(resume_id)
    if resume:
        return jsonify(utils.resume_to_dict(resume))
    return jsonify({"error": "Not found"}), 404

@app.route('/api/resumes', methods=['POST'])
def save_resume():
    """Save a new resume or update existing."""
    data = request.json or {}
    resume = utils.dict_to_resume(data)
    resume.updated = datetime.now()
    if not resume.title:
        resume.title = (resume.full_name or "Untitled").strip()
    resume_id = db.save_resume(resume)
    _record_score_history(resume, "save")
    return jsonify({"id": resume_id, "message": "Saved successfully", "title": resume.title})

@app.route('/api/resumes/<int:resume_id>', methods=['DELETE'])
def delete_resume(resume_id):
    """Delete a resume."""
    db.delete_resume(resume_id)
    return jsonify({"message": "Deleted"})

@app.route('/api/export-pdf', methods=['POST'])
def export_pdf():
    """Generate PDF and return as downloadable file."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        pdf_opts = _extract_pdf_options(data)
        template_name = pdf_opts["template_name"]
        page_size = pdf_opts["page_size"]
        layout_override = pdf_opts["layout_override"]
        heading_align_override = pdf_opts["heading_align_override"]
        body_align_override = pdf_opts["body_align_override"]
        accent_color_override = pdf_opts["accent_color_override"]
        font_override = pdf_opts["font_override"]
        compact_mode = pdf_opts["compact_mode"]
        ats_safe_mode = pdf_opts["ats_safe_mode"]
        section_order = pdf_opts["section_order"]
        font_scale = pdf_opts["font_scale"]
        margin_preset = pdf_opts["margin_preset"]
        section_visibility = pdf_opts["section_visibility"]
        header_layout = pdf_opts["header_layout"]

        # Generate PDF in memory
        pdf_buffer = io.BytesIO()
        PDFGenerator.generate(
            resume,
            pdf_buffer,
            template_name=template_name,
            page_size=page_size,
            layout_override=layout_override,
            heading_align_override=heading_align_override,
            body_align_override=body_align_override,
            accent_color_override=accent_color_override,
            font_override=font_override,
            compact_mode=compact_mode,
            ats_safe_mode=ats_safe_mode,
            section_order=section_order,
            font_scale=font_scale,
            margin_preset=margin_preset,
            section_visibility=section_visibility,
            header_layout=header_layout,
        )
        pdf_buffer.seek(0)
        _log_audit(
            action="export_pdf",
            details=f"name={resume.full_name or 'resume'}; template={template_name}; page={page_size}"
        )
        _record_score_history(resume, "export_pdf")

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{resume.full_name or 'resume'}_resume.pdf"
        )
    except Exception as e:
        app.logger.error(f"PDF generation failed: {e}")
        return f"PDF generation failed: {str(e)}", 500


@app.route('/api/preview-pdf', methods=['POST'])
def preview_pdf():
    """Generate PDF and return inline for live browser preview."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        pdf_opts = _extract_pdf_options(data)
        template_name = pdf_opts["template_name"]
        page_size = pdf_opts["page_size"]
        layout_override = pdf_opts["layout_override"]
        heading_align_override = pdf_opts["heading_align_override"]
        body_align_override = pdf_opts["body_align_override"]
        accent_color_override = pdf_opts["accent_color_override"]
        font_override = pdf_opts["font_override"]
        compact_mode = pdf_opts["compact_mode"]
        ats_safe_mode = pdf_opts["ats_safe_mode"]
        section_order = pdf_opts["section_order"]
        font_scale = pdf_opts["font_scale"]
        margin_preset = pdf_opts["margin_preset"]
        section_visibility = pdf_opts["section_visibility"]
        header_layout = pdf_opts["header_layout"]

        pdf_buffer = io.BytesIO()
        PDFGenerator.generate(
            resume,
            pdf_buffer,
            template_name=template_name,
            page_size=page_size,
            layout_override=layout_override,
            heading_align_override=heading_align_override,
            body_align_override=body_align_override,
            accent_color_override=accent_color_override,
            font_override=font_override,
            compact_mode=compact_mode,
            ats_safe_mode=ats_safe_mode,
            section_order=section_order,
            font_scale=font_scale,
            margin_preset=margin_preset,
            section_visibility=section_visibility,
            header_layout=header_layout,
        )
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f"{resume.full_name or 'resume'}_preview.pdf"
        )
    except Exception as e:
        app.logger.error(f"PDF preview generation failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/export-bulk-pdf', methods=['POST'])
def export_bulk_pdf():
    """Export the same resume in multiple templates as a ZIP package."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        pdf_opts = _extract_pdf_options(data)
        templates = (
            data.get("template_names")
            or data.get("templateNames")
            or data.get("templates")
            or []
        )
        if isinstance(templates, str):
            templates = [x.strip() for x in templates.split(",") if x.strip()]
        if not isinstance(templates, list):
            templates = []
        templates = [str(t).strip() for t in templates if str(t).strip()]
        if not templates:
            templates = [pdf_opts["template_name"] or AppConfig.DEFAULT_TEMPLATE]
        # Keep only known templates and avoid huge ZIP requests.
        known = set(AppConfig.TEMPLATES.keys())
        selected = []
        for t in templates:
            resolved = PDFGenerator._resolve_template_name(t)
            if resolved in known and resolved not in selected:
                selected.append(resolved)
        selected = selected[:12]
        if not selected:
            return jsonify({"error": "No valid templates selected"}), 400

        page_size = pdf_opts["page_size"]
        layout_override = pdf_opts["layout_override"]
        heading_align_override = pdf_opts["heading_align_override"]
        body_align_override = pdf_opts["body_align_override"]
        accent_color_override = pdf_opts["accent_color_override"]
        font_override = pdf_opts["font_override"]
        compact_mode = pdf_opts["compact_mode"]
        ats_safe_mode = pdf_opts["ats_safe_mode"]
        section_order = pdf_opts["section_order"]
        font_scale = pdf_opts["font_scale"]
        margin_preset = pdf_opts["margin_preset"]
        section_visibility = pdf_opts["section_visibility"]
        header_layout = pdf_opts["header_layout"]

        zip_buffer = io.BytesIO()
        base = (resume.full_name or "resume").strip().replace(" ", "_")
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for tpl in selected:
                pdf_buffer = io.BytesIO()
                PDFGenerator.generate(
                    resume,
                    pdf_buffer,
                    template_name=tpl,
                    page_size=page_size,
                    layout_override=layout_override,
                    heading_align_override=heading_align_override,
                    body_align_override=body_align_override,
                    accent_color_override=accent_color_override,
                    font_override=font_override,
                    compact_mode=compact_mode,
                    ats_safe_mode=ats_safe_mode,
                    section_order=section_order,
                    font_scale=font_scale,
                    margin_preset=margin_preset,
                    section_visibility=section_visibility,
                    header_layout=header_layout,
                )
                pdf_buffer.seek(0)
                zf.writestr(f"{base}_{tpl}.pdf", pdf_buffer.read())

        zip_buffer.seek(0)
        _log_audit(
            action="export_bulk_pdf",
            details=f"name={resume.full_name or 'resume'}; templates={','.join(selected)}"
        )
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{base}_bulk_templates.zip"
        )
    except Exception as e:
        app.logger.error(f"Bulk PDF export failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/export-word', methods=['POST'])
def export_word():
    """Generate Word (RTF) and return as downloadable file."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)

        word_buffer = io.BytesIO()
        WordGenerator.generate(resume, word_buffer)
        word_buffer.seek(0)
        _log_audit(
            action="export_word",
            details=f"name={resume.full_name or 'resume'}"
        )
        _record_score_history(resume, "export_word")

        return send_file(
            word_buffer,
            mimetype='application/rtf',
            as_attachment=True,
            download_name=f"{resume.full_name or 'resume'}_resume.rtf"
        )
    except Exception as e:
        app.logger.error(f"Word generation failed: {e}")
        return f"Word generation failed: {str(e)}", 500


@app.route('/api/ats-score', methods=['POST'])
def ats_score():
    """Return ATS-style keyword score and suggestions."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        job_description = data.get("job_description", "")
        result = analyze_ats(resume, job_description)
        try:
            with _auth_conn() as conn:
                conn.execute(
                    "INSERT INTO score_history (user_id, resume_title, score, source, created) VALUES (?, ?, ?, ?, ?)",
                    (
                        session.get("user_id"),
                        resume.title or resume.full_name or "Untitled",
                        int(result.get("score", 0)),
                        "ats",
                        datetime.now().isoformat(),
                    ),
                )
        except Exception:
            pass
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"ATS scoring failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/template-recommend', methods=['POST'])
def template_recommend_api():
    """Recommend best templates using ML/heuristic scoring."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        job_description = data.get("job_description", "")
        top_k = int(data.get("top_k", 3) or 3)
        top_k = max(1, min(6, top_k))

        catalog_path = os.path.join(app.template_folder or "template", "templates_catalog.json")
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
            if not isinstance(catalog, list):
                catalog = []
        except Exception:
            catalog = []

        result = recommend_templates_ml(
            resume=resume,
            job_description=job_description,
            templates_catalog=catalog,
            top_k=top_k,
        )
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Template recommendation failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/google-templates', methods=['GET'])
@_login_required
def google_templates_api():
    """Fetch template ideas from Google Custom Search and normalize for gallery UI."""
    query = (request.args.get("q") or GOOGLE_TEMPLATES_DEFAULT_QUERY or "resume template").strip()
    try:
        limit = int(request.args.get("limit", "8") or 8)
    except Exception:
        limit = 8
    limit = max(1, min(10, limit))

    if not GOOGLE_TEMPLATES_API_KEY or not GOOGLE_TEMPLATES_CSE_ID:
        return jsonify({
            "enabled": False,
            "provider": "google_custom_search",
            "query": query,
            "templates": [],
            "message": "Set GOOGLE_TEMPLATES_API_KEY and GOOGLE_TEMPLATES_CSE_ID to enable Google templates.",
        })

    try:
        templates = _fetch_google_templates(query=query, limit=limit)
        return jsonify({
            "enabled": True,
            "provider": "google_custom_search",
            "query": query,
            "count": len(templates),
            "templates": templates,
        })
    except Exception as e:
        app.logger.error(f"Google templates fetch failed: {e}")
        return jsonify({
            "enabled": True,
            "provider": "google_custom_search",
            "query": query,
            "templates": [],
            "error": str(e),
        }), 502


@app.route('/api/tailor-resume', methods=['POST'])
def tailor_resume_api():
    """Return tailored summary + suggested skills for the provided job description."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        job_description = data.get("job_description", "")
        result = tailor_resume(resume, job_description)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Resume tailoring failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/enhance-bullets', methods=['POST'])
def enhance_bullets_api():
    """Enhance experience/project bullets using deterministic rewrite rules."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        result = enhance_resume_bullets(resume)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Bullet enhancement failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/rewrite-summary', methods=['POST'])
def rewrite_summary_api():
    """Rewrite summary using selected tone mode."""
    try:
        data = request.json or {}
        summary = data.get("summary", "")
        tone = data.get("tone", "formal")
        result = rewrite_summary_tone(summary, tone)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Summary rewrite failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/skill-gap', methods=['POST'])
def skill_gap_api():
    """Generate missing skills + 30-day learning plan from JD."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        job_description = data.get("job_description", "")
        result = plan_skill_gap(resume, job_description)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Skill gap planning failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/cover-letter', methods=['POST'])
def cover_letter_api():
    """Generate a tailored cover letter draft from resume + JD."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        result = generate_cover_letter(
            resume=resume,
            job_description=data.get("job_description", ""),
            company=data.get("company", ""),
            role=data.get("role", ""),
        )
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Cover letter generation failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/interview-questions', methods=['POST'])
def interview_questions_api():
    """Generate role-aware interview questions based on resume + JD."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        result = generate_interview_questions(
            resume=resume,
            job_description=data.get("job_description", ""),
            count=int(data.get("count", 20) or 20),
        )
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Interview question generation failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/multilingual-resume', methods=['POST'])
def multilingual_resume_api():
    """Create a multilingual resume variant payload for quick export/use."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        language = (data.get("language") or "english").strip().lower()
        result = create_multilingual_variant(resume=resume, language=language)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Multilingual resume variant failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/linkedin-optimize', methods=['POST'])
def linkedin_optimize_api():
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        result = optimize_linkedin_profile(resume, target_role=data.get("target_role", ""))
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"LinkedIn optimizer failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/grammar-fix', methods=['POST'])
def grammar_fix_api():
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        result = grammar_fix_resume(resume)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Grammar fix failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/email-apply-kit', methods=['POST'])
def email_apply_kit_api():
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        result = generate_email_apply_kit(
            resume=resume,
            company=data.get("company", ""),
            role=data.get("role", ""),
        )
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Email apply kit failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/achievement-quantify', methods=['POST'])
def achievement_quantify_api():
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        result = quantify_achievement_lines(resume)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Achievement quantify failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/duplicate-detector', methods=['POST'])
def duplicate_detector_api():
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        result = detect_duplicates(resume)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Duplicate detector failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/ai-assistant', methods=['POST'])
def ai_assistant_api():
    """Hybrid AI assistant: LLM-first (when configured) with deterministic fallback."""
    try:
        data = request.json or {}
        prompt = (data.get("prompt") or data.get("message") or "").strip()
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        resume = utils.dict_to_resume(data)
        jd = (data.get("job_description") or "").strip()
        prefer_llm = _to_bool(data.get("prefer_llm", data.get("use_llm", True)), True)
        if _to_bool(data.get("force_heuristic", False), False):
            prefer_llm = False
        result = assist_resume_hybrid(
            resume=resume,
            prompt=prompt,
            job_description=jd,
            company=(data.get("company") or ""),
            role=(data.get("role") or ""),
            prefer_llm=prefer_llm,
        )
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"AI assistant failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/score-history', methods=['GET'])
def score_history_api():
    try:
        user_id = session.get("user_id")
        with _auth_conn() as conn:
            if user_id is None:
                rows = conn.execute(
                    """
                    SELECT score, source, created, resume_title
                    FROM score_history
                    WHERE user_id IS NULL
                    ORDER BY id DESC
                    LIMIT 50
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT score, source, created, resume_title
                    FROM score_history
                    WHERE user_id=?
                    ORDER BY id DESC
                    LIMIT 50
                    """,
                    (user_id,),
                ).fetchall()
        items = [dict(r) for r in rows][::-1]
        return jsonify(items)
    except Exception as e:
        app.logger.error(f"Score history fetch failed: {e}")
        return jsonify({"error": str(e)}), 500


def _render_public_resume_html(payload: dict) -> str:
    """Render a public, read-only resume page."""
    p = payload or {}
    h = html.escape
    full_name = h(p.get("full_name") or "Resume")
    profile_title = h(p.get("profile_title") or "")
    summary = h(p.get("summary") or "").replace("\n", "<br/>")
    contact = " | ".join([x for x in [p.get("email"), p.get("phone"), p.get("city"), p.get("address")] if x])

    def _items(rows, fn):
        out = []
        for r in (rows or []):
            try:
                out.append(fn(r))
            except Exception:
                continue
        return "".join(out)

    exp_html = _items(
        p.get("experiences", []),
        lambda e: f"<li><strong>{h(e.get('job_title',''))}</strong> {('at ' + h(e.get('company',''))) if e.get('company') else ''}"
                  f"<div class='meta'>{h(e.get('start_date',''))} - {h(e.get('end_date','Present') or 'Present')}</div>"
                  f"{h(e.get('description','')).replace(chr(10), '<br/>')}</li>"
    )
    edu_html = _items(
        p.get("educations", []),
        lambda e: f"<li><strong>{h(e.get('degree',''))}</strong> {h(e.get('institution',''))}"
                  f"<div class='meta'>{h(e.get('start_date',''))} - {h(e.get('end_date',''))}</div>"
                  f"{h(e.get('description','')).replace(chr(10), '<br/>')}</li>"
    )
    proj_html = _items(
        p.get("projects", []),
        lambda e: f"<li><strong>{h(e.get('name',''))}</strong> {h(e.get('role',''))}"
                  f"<div class='meta'>{h(e.get('technologies',''))}</div>"
                  f"{h(e.get('description','')).replace(chr(10), '<br/>')}</li>"
    )
    skills = ", ".join([h(s) for s in (p.get("skills", []) or [])])

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{full_name} - Public Resume</title>
  <style>
    body{{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f5f7fb;color:#111827}}
    .wrap{{max-width:900px;margin:22px auto;padding:20px;background:#fff;border:1px solid #d1d5db;border-radius:12px}}
    h1{{margin:0 0 6px}} h2{{margin:20px 0 8px;border-bottom:2px solid #0f766e;padding-bottom:5px}}
    .meta{{font-size:13px;color:#6b7280;margin:4px 0 8px}} ul{{padding-left:18px}} li{{margin-bottom:10px;line-height:1.38}}
    .note{{margin-top:16px;font-size:12px;color:#6b7280}}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>{full_name}</h1>
    <div>{profile_title}</div>
    <div class="meta">{h(contact)}</div>
    <h2>Summary</h2><p>{summary or 'No summary provided.'}</p>
    <h2>Experience</h2><ul>{exp_html or '<li>No experience listed.</li>'}</ul>
    <h2>Education</h2><ul>{edu_html or '<li>No education listed.</li>'}</ul>
    <h2>Projects</h2><ul>{proj_html or '<li>No projects listed.</li>'}</ul>
    <h2>Skills</h2><p>{skills or 'No skills listed.'}</p>
    <div class="note">Public resume view generated by ResumeForge Pro.</div>
  </div>
</body>
</html>"""


@app.route('/api/public-resume', methods=['POST'])
@_login_required
def create_public_resume_link():
    """Create a public share link for the current resume payload."""
    data = request.json or {}
    user_id = session.get("user_id")
    expires_days = int(data.get("expires_days", 7) or 7)
    expires_days = max(1, min(30, expires_days))
    expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()

    token = secrets.token_urlsafe(12)
    resume_payload = data.get("resume") or data
    title = (resume_payload.get("full_name") or "Public Resume").strip()

    with _auth_conn() as conn:
        conn.execute(
            """
            INSERT INTO public_resume_links (user_id, token, title, resume_json, expires_at, created, revoked)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (user_id, token, title, json.dumps(resume_payload), expires_at, datetime.now().isoformat()),
        )
    link = request.url_root.rstrip("/") + url_for("public_resume_view", token=token)
    _log_audit("public_resume_create", f"title={title}; expires_days={expires_days}")
    return jsonify({"token": token, "url": link, "expires_at": expires_at})


@app.route('/api/public-resume', methods=['GET'])
@_login_required
def list_public_resume_links():
    user_id = session.get("user_id")
    with _auth_conn() as conn:
        rows = conn.execute(
            """
            SELECT token, title, expires_at, created, revoked
            FROM public_resume_links
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT 50
            """,
            (user_id,),
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/public-resume/<token>', methods=['DELETE'])
@_login_required
def revoke_public_resume_link(token: str):
    user_id = session.get("user_id")
    with _auth_conn() as conn:
        cur = conn.execute(
            "UPDATE public_resume_links SET revoked=1 WHERE token=? AND user_id=?",
            (token, user_id),
        )
        if cur.rowcount == 0:
            return jsonify({"error": "Link not found"}), 404
    _log_audit("public_resume_revoke", f"token={token[:8]}")
    return jsonify({"message": "Public link revoked"})


@app.route('/public/<token>', methods=['GET'])
def public_resume_view(token: str):
    """Public read-only resume view for shared links."""
    with _auth_conn() as conn:
        row = conn.execute(
            "SELECT resume_json, expires_at, revoked FROM public_resume_links WHERE token=?",
            (token,),
        ).fetchone()
    if not row or row["revoked"]:
        return "Public link not found or revoked.", 404
    try:
        if row["expires_at"] and datetime.fromisoformat(row["expires_at"]) < datetime.now():
            return "This public link has expired.", 410
    except Exception:
        pass
    try:
        payload = json.loads(row["resume_json"] or "{}")
    except Exception:
        payload = {}
    return _render_public_resume_html(payload)


@app.route('/api/job-tracker', methods=['GET'])
@_login_required
def list_job_tracker():
    """List current user's tracked jobs."""
    user_id = session.get("user_id")
    with _auth_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, company, role, status, job_link, notes, jd_text, follow_up_date, reminder_enabled, created, updated
            FROM job_tracker
            WHERE user_id=?
            ORDER BY datetime(updated) DESC, id DESC
            """,
            (user_id,),
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/job-reminders', methods=['GET'])
@_login_required
def list_job_reminders():
    user_id = session.get("user_id")
    today = datetime.now().date().isoformat()
    with _auth_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, company, role, status, follow_up_date, reminder_enabled
            FROM job_tracker
            WHERE user_id=? AND reminder_enabled=1 AND follow_up_date IS NOT NULL AND follow_up_date!=''
            ORDER BY follow_up_date ASC, id DESC
            """,
            (user_id,),
        ).fetchall()
    items = [dict(r) for r in rows]
    for r in items:
        due = str(r.get("follow_up_date") or "")
        r["is_overdue"] = bool(due and due < today)
        r["is_today"] = bool(due == today)
    return jsonify(items)


@app.route('/api/job-tracker', methods=['POST'])
@_login_required
def create_job_tracker():
    """Create a tracked job entry for current user."""
    user_id = session.get("user_id")
    data = request.json or {}
    company = (data.get("company") or "").strip()
    role = (data.get("role") or "").strip()
    status = (data.get("status") or "saved").strip().lower()
    job_link = (data.get("job_link") or "").strip()
    notes = (data.get("notes") or "").strip()
    jd_text = (data.get("jd_text") or "").strip()
    follow_up_date = (data.get("follow_up_date") or "").strip()
    reminder_enabled = 1 if bool(data.get("reminder_enabled")) else 0
    if not company or not role:
        return jsonify({"error": "company and role are required"}), 400
    if status not in {"saved", "applied", "interview", "offer", "rejected"}:
        status = "saved"

    now = datetime.now().isoformat()
    with _auth_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO job_tracker (user_id, company, role, status, job_link, notes, jd_text, follow_up_date, reminder_enabled, created, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, company, role, status, job_link, notes, jd_text, follow_up_date, reminder_enabled, now, now),
        )
        job_id = cur.lastrowid

    _log_audit("job_tracker_create", f"id={job_id}; company={company}; role={role}; status={status}; follow_up={follow_up_date}")
    return jsonify({"id": job_id, "message": "Job saved"})


@app.route('/api/job-tracker/<int:job_id>', methods=['PATCH'])
@_login_required
def update_job_tracker(job_id: int):
    """Update tracked job entry for current user."""
    user_id = session.get("user_id")
    data = request.json or {}
    fields = {}
    if "company" in data:
        fields["company"] = (data.get("company") or "").strip()
    if "role" in data:
        fields["role"] = (data.get("role") or "").strip()
    if "status" in data:
        status = (data.get("status") or "saved").strip().lower()
        fields["status"] = status if status in {"saved", "applied", "interview", "offer", "rejected"} else "saved"
    if "job_link" in data:
        fields["job_link"] = (data.get("job_link") or "").strip()
    if "notes" in data:
        fields["notes"] = (data.get("notes") or "").strip()
    if "jd_text" in data:
        fields["jd_text"] = (data.get("jd_text") or "").strip()
    if "follow_up_date" in data:
        fields["follow_up_date"] = (data.get("follow_up_date") or "").strip()
    if "reminder_enabled" in data:
        fields["reminder_enabled"] = 1 if bool(data.get("reminder_enabled")) else 0
    if not fields:
        return jsonify({"error": "No fields to update"}), 400
    fields["updated"] = datetime.now().isoformat()

    set_clause = ", ".join([f"{k}=?" for k in fields.keys()])
    params = list(fields.values()) + [job_id, user_id]
    with _auth_conn() as conn:
        cur = conn.execute(
            f"UPDATE job_tracker SET {set_clause} WHERE id=? AND user_id=?",
            params,
        )
        if cur.rowcount == 0:
            return jsonify({"error": "Job not found"}), 404

    _log_audit("job_tracker_update", f"id={job_id}; fields={','.join(fields.keys())}")
    return jsonify({"message": "Job updated"})


@app.route('/api/job-tracker/<int:job_id>', methods=['DELETE'])
@_login_required
def delete_job_tracker(job_id: int):
    """Delete tracked job entry for current user."""
    user_id = session.get("user_id")
    with _auth_conn() as conn:
        cur = conn.execute("DELETE FROM job_tracker WHERE id=? AND user_id=?", (job_id, user_id))
        if cur.rowcount == 0:
            return jsonify({"error": "Job not found"}), 404
    _log_audit("job_tracker_delete", f"id={job_id}")
    return jsonify({"message": "Job deleted"})


def _build_portfolio_html(resume):
    full_name = (resume.full_name or "Your Name").strip()
    role = (resume.profile_title or "Professional").strip()
    summary = (resume.summary or "").replace("\n", "<br/>")
    contact = " | ".join([x for x in [resume.email, resume.phone, resume.city, resume.address, resume.website, resume.linkedin, resume.github] if x])

    exp_html = "".join([
        f"<li><strong>{e.job_title}</strong> {('at ' + e.company) if e.company else ''}<br/><small>{e.start_date} - {e.end_date or 'Present'}</small><br/>{(e.description or '').replace(chr(10), '<br/>')}</li>"
        for e in (resume.experiences or [])
    ])
    proj_html = "".join([
        f"<li><strong>{p.name}</strong> {('- ' + p.role) if p.role else ''}<br/>{(p.description or '').replace(chr(10), '<br/>')}</li>"
        for p in (resume.projects or [])
    ])
    skills = ", ".join(resume.skills or [])
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{full_name} - Portfolio</title>
<style>
body{{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f5f7f9;color:#111827}}
.wrap{{max-width:900px;margin:24px auto;padding:20px;background:#fff;border:1px solid #d1d5db;border-radius:12px}}
h1{{margin:0 0 6px}} h2{{margin:22px 0 8px;border-bottom:2px solid #0f766e;padding-bottom:6px}}
.meta{{color:#4b5563}} ul{{padding-left:18px}} li{{margin-bottom:10px;line-height:1.4}}
</style></head>
<body><div class="wrap">
<h1>{full_name}</h1>
<div class="meta">{role}</div>
<div class="meta">{contact}</div>
<h2>Summary</h2><p>{summary}</p>
<h2>Experience</h2><ul>{exp_html or '<li>Add experience details</li>'}</ul>
<h2>Projects</h2><ul>{proj_html or '<li>Add project details</li>'}</ul>
<h2>Skills</h2><p>{skills or 'Add skills'}</p>
</div></body></html>"""


@app.route('/api/export-branding-pack', methods=['POST'])
def export_branding_pack():
    """Export bundled files: resume JSON, cover letter, interview Q, portfolio HTML."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        job_description = data.get("job_description", "")
        language = (data.get("language") or "english").strip().lower()

        cover = generate_cover_letter(
            resume=resume,
            job_description=job_description,
            company=data.get("company", ""),
            role=data.get("role", ""),
        )
        interview = generate_interview_questions(
            resume=resume,
            job_description=job_description,
            count=20,
        )
        localized = create_multilingual_variant(resume=resume, language=language)
        portfolio_html = _build_portfolio_html(resume)
        resume_json = json.dumps(utils.resume_to_dict(resume), ensure_ascii=False, indent=2)

        zip_buffer = io.BytesIO()
        base = (resume.full_name or "resume").strip().replace(" ", "_")
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{base}.json", resume_json)
            zf.writestr(f"{base}_cover_letter.txt", cover.get("cover_letter", ""))
            zf.writestr(f"{base}_interview_questions.txt", "\n".join(interview.get("questions", [])))
            zf.writestr(f"{base}_portfolio.html", portfolio_html)
            zf.writestr(f"{base}_language_variant.txt", localized.get("preview_text", ""))
        zip_buffer.seek(0)
        _log_audit(action="export_branding_pack", details=f"name={resume.full_name or 'resume'}; lang={language}")
        _record_score_history(resume, "export_branding_pack")
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{base}_branding_pack.zip"
        )
    except Exception as e:
        app.logger.error(f"Branding pack export failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/export-portfolio', methods=['POST'])
def export_portfolio():
    """Export a simple single-file HTML portfolio from resume data."""
    try:
        data = request.json or {}
        resume = utils.dict_to_resume(data)
        html = _build_portfolio_html(resume)
        out = io.BytesIO(html.encode("utf-8"))
        out.seek(0)
        _log_audit(action="export_portfolio_html", details=f"name={resume.full_name or 'resume'}")
        _record_score_history(resume, "export_portfolio_html")
        return send_file(
            out,
            mimetype='text/html',
            as_attachment=True,
            download_name=f"{resume.full_name or 'resume'}_portfolio.html"
        )
    except Exception as e:
        app.logger.error(f"Portfolio export failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload-profile-pic', methods=['POST'])
def upload_profile_pic():
    """Handle profile picture upload (base64)."""
    data = request.json
    image_data = base64.b64decode(data['image'].split(',')[1])  # Remove data:image/...
    # Return as bytes to be stored later
    return jsonify({"image": base64.b64encode(image_data).decode('ascii')})

if __name__ == '__main__':
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
