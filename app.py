import os
import csv
import shutil
import json
import io
import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file, flash
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Always load .env from the same folder as this file
_BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_BASE, ".env"), override=True)

import sys
sys.path.insert(0, _BASE)

from rename_certificates import rename_certificates
from email_sender import send_certificates
from report_generator import ReportGenerator

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "smartcert-secure-2026-key")
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  

UPLOAD_CSV   = os.path.join(_BASE, "uploads", "csv")
UPLOAD_CERTS = os.path.join(_BASE, "uploads", "certificates")
RENAMED      = os.path.join(_BASE, "renamed_certificates")
DB_PATH      = os.path.join(_BASE, "smartcert.db")
AUTH_KEY     = "Shamstabraiz@911"

for folder in [UPLOAD_CSV, UPLOAD_CERTS, RENAMED]:
    os.makedirs(folder, exist_ok=True)

# ── Database Initialization ────────────────────────────────────────────────
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT, smtp_user TEXT, smtp_pass TEXT)')
        # Add columns if they don't exist in already created tables
        try: conn.execute('ALTER TABLE users ADD COLUMN smtp_user TEXT')
        except: pass
        try: conn.execute('ALTER TABLE users ADD COLUMN smtp_pass TEXT')
        except: pass
init_db()

# ── Auth Decorator ──────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ── Auth Routes ────────────────────────────────────────────────────────────
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        auth_key = request.form.get("auth_key")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        smtp_user = request.form.get("smtp_user")
        smtp_pass = request.form.get("smtp_pass")

        if auth_key != AUTH_KEY:
            flash("Invalid Authentication Key!", "error")
        elif password != confirm:
            flash("Passwords do not match!", "error")
        else:
            try:
                hashed = generate_password_hash(password)
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute('INSERT INTO users (name, email, password, smtp_user, smtp_pass) VALUES (?, ?, ?, ?, ?)', (name, email, hashed, smtp_user, smtp_pass))
                flash("Signup successful! Please login.", "success")
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash("Email already exists!", "error")
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        with sqlite3.connect(DB_PATH) as conn:
            user = conn.execute('SELECT id, name, password, smtp_user, smtp_pass FROM users WHERE email = ?', (email,)).fetchone()
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['user_email'] = email
                session['smtp_user'] = user[3]
                session['smtp_pass'] = user[4]
                return redirect(url_for('home'))
            flash("Invalid email or password", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── Main Routes (Protected) ────────────────────────────────────────────────
@app.route("/")
@login_required
def home():
    return render_template("index.html", user_name=session.get('user_name'))

@app.route("/preview-csv", methods=["POST"])
@login_required
def preview_csv():
    csv_file = request.files.get("csv_file")
    if not csv_file: return jsonify({"error": "No CSV file provided"}), 400
    try:
        content = csv_file.stream.read().decode("utf-8")
        lines = content.splitlines()
        reader = csv.DictReader(lines)
        if reader.fieldnames:
            reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]
        rows = [{"name": r.get("name","").strip(), "email": r.get("email","").strip()} for r in reader]
        rows = [r for r in rows if r["name"] or r["email"]]
        return jsonify({"rows": rows, "count": len(rows)})
    except Exception as e: return jsonify({"error": str(e)}), 400

@app.route("/compose", methods=["POST"])
@login_required
def compose():
    csv_file   = request.files.get("csv_file")
    cert_files = request.files.getlist("certificates")
    if not csv_file or not cert_files: return redirect(url_for("home"))

    for folder in [UPLOAD_CSV, UPLOAD_CERTS, RENAMED]:
        shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(folder, exist_ok=True)

    csv_path = os.path.join(UPLOAD_CSV, csv_file.filename)
    csv_file.save(csv_path)
    for f in cert_files:
        if f.filename: f.save(os.path.join(UPLOAD_CERTS, f.filename))

    participants = []
    try:
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames:
                reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]
            for row in reader:
                n, e = row.get("name","").strip(), row.get("email","").strip()
                if n and e: participants.append({"name": n, "email": e})
    except: pass

    session["csv_path"] = csv_path
    session["participants"] = participants
    session["cert_count"] = len(cert_files)

    return render_template("compose.html", participants=participants, cert_count=len(cert_files),
        default_subject=os.getenv("EMAIL_SUBJECT", "Your Certificate!"),
        default_body="Dear {name},\n\nCongratulations! Your certificate is attached.")

@app.route("/send", methods=["POST"])
@login_required
def send():
    subject, body_tpl = request.form.get("subject", "").strip(), request.form.get("body", "").strip()
    safety_enabled = request.form.get("safety_mode") == "on"
    
    csv_path = session.get("csv_path", "")
    if not csv_path or not os.path.exists(csv_path): return redirect(url_for("home"))
    
    # Use user_email for filtering only if safety mode is ON
    filter_email = session.get('user_email') if safety_enabled else None
    
    try:
        rename_certificates(csv_path, UPLOAD_CERTS, RENAMED)
        sent, failed, report = send_certificates(
            csv_path, RENAMED, subject=subject, body_template=body_tpl, 
            filter_email=filter_email,
            sender_user=session.get('smtp_user'),
            sender_pass=session.get('smtp_pass')
        )
    except Exception as e:
        sent, failed, report = 0, 0, [{"name": "-", "email": "-", "status": "failed", "reason": str(e)}]
    session["result"] = {"sent": sent, "failed": failed, "total": sent+failed, "report": report, "subject": subject}
    return redirect(url_for("result_page"))

@app.route("/result")
@login_required
def result_page():
    if "result" not in session: return redirect(url_for("home"))
    return render_template("result.html", result=session["result"])

@app.route("/download-report")
@login_required
def download_report():
    result = session.get("result")
    if not result: return redirect(url_for("home"))
    csv_bytes = ReportGenerator.generate_csv(result)
    return send_file(io.BytesIO(csv_bytes), mimetype="text/csv", as_attachment=True, download_name="SmartCert_Report.csv")

@app.route("/download-pdf-report")
@login_required
def download_pdf_report():
    result = session.get("result")
    if not result: return redirect(url_for("home"))
    try:
        pdf_bytes = ReportGenerator.generate_pdf(result)
        return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf", as_attachment=True, download_name="SmartCert_Report.pdf")
    except Exception as e: return f"Error: {str(e)}", 500

@app.route("/health")
def health():
    sender = os.getenv("SENDER_EMAIL", "")
    configured = bool(sender and sender != "your_email@gmail.com")
    return jsonify({"status": "ok", "email_configured": configured, "sender": sender if configured else "Not Set"})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
