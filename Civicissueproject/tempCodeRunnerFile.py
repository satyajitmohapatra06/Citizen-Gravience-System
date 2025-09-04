# app.py  (UPDATED)
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for servers
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"  # required for sessions

DB_NAME = "civic.db"

# -------------------- FILE UPLOAD CONFIG --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ADMIN_PROOF_FOLDER = os.path.join(BASE_DIR, "static", "admin_proofs")
CHART_FOLDER = os.path.join(BASE_DIR, "static", "admin_charts")

for d in (UPLOAD_FOLDER, ADMIN_PROOF_FOLDER, CHART_FOLDER):
    os.makedirs(d, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ADMIN_PROOF_FOLDER"] = ADMIN_PROOF_FOLDER
app.config["CHART_FOLDER"] = CHART_FOLDER

# -------------------- DATABASE INIT --------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')

    # Complaints table with status (and optional admin_proof)
    c.execute('''CREATE TABLE IF NOT EXISTS complaints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_phone TEXT NOT NULL,
                    name TEXT,
                    phone TEXT,
                    district TEXT,
                    block TEXT,
                    gp TEXT,
                    village TEXT,
                    post TEXT,
                    pincode TEXT,
                    department TEXT,
                    complaint TEXT,
                    proof TEXT,
                    status TEXT DEFAULT 'Pending',
                    admin_proof TEXT,
                    updated_at TEXT,
                    FOREIGN KEY(user_phone) REFERENCES users(phone)
                )''')

    conn.commit()
    conn.close()

init_db()

# -------------------- DB helpers --------------------
def get_db_df():
    """Return complaints table as pandas DataFrame for reporting."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM complaints", conn)
    conn.close()
    return df

def get_all_complaints():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT id, user_phone, name, phone, district, block, gp, village, post, pincode, department, complaint, proof, status, admin_proof, updated_at
        FROM complaints ORDER BY id DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_complaints(user_phone):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT id, user_phone, name, phone, district, block, gp, village, post, pincode, department, complaint, proof, status, admin_proof, updated_at
        FROM complaints WHERE user_phone=? ORDER BY id DESC
    """, (user_phone,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_complaint_by_id(cid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM complaints WHERE id=?", (cid,))
    row = c.fetchone()
    conn.close()
    return row

def update_complaint_status(cid, status, admin_proof_filename=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    updated_at = datetime.utcnow().isoformat()
    if admin_proof_filename:
        c.execute("UPDATE complaints SET status=?, admin_proof=?, updated_at=? WHERE id=?", (status, admin_proof_filename, updated_at, cid))
    else:
        c.execute("UPDATE complaints SET status=?, updated_at=? WHERE id=?", (status, updated_at, cid))
    conn.commit()
    conn.close()

# -------------------- CHART GENERATION --------------------
def generate_charts():
    """Generate charts and save to static/admin_charts/"""
    df = get_db_df()
    if df.empty:
        df = pd.DataFrame({
            'department': ['N/A'],
            'status': ['Pending'],
            'district': ['Unknown'],
            'updated_at': [datetime.utcnow().isoformat()]
        })

    chart_paths = {}

    # ---------------- Complaints by Status (Bar) ----------------
    status_counts = df['status'].fillna('Pending').value_counts()
    plt.figure(figsize=(6,4))
    status_counts.plot(kind='bar', edgecolor='black', color='#0a66ff')
    plt.title('Complaints by Status')
    plt.xlabel('Status')
    plt.ylabel('Count')
    plt.tight_layout()
    path = os.path.join(CHART_FOLDER, 'status_bar.png')
    plt.savefig(path); plt.close()
    chart_paths['status'] = 'admin_charts/status_bar.png'

    # ---------------- Complaints by Department (Pie) ----------------
    dept_counts = df['department'].fillna('Unknown').value_counts()
    plt.figure(figsize=(5,5))
    dept_counts.plot(kind='pie', autopct='%1.1f%%', startangle=140, colors=plt.cm.Set3.colors)
    plt.ylabel('')
    plt.title('Complaints by Department')
    plt.tight_layout()
    path = os.path.join(CHART_FOLDER, 'department_pie.png')
    plt.savefig(path); plt.close()
    chart_paths['department'] = 'admin_charts/department_pie.png'

    # ---------------- Top Pincodes (Horizontal Bar) ----------------
    pincode_counts = df['pincode'].fillna('Unknown').value_counts().nlargest(8)
    plt.figure(figsize=(7,4))
    pincode_counts.plot(kind='barh', edgecolor='black', color='#17a2b8')
    plt.title('Top Pincodes (most complaints)')
    plt.xlabel('Count')
    plt.tight_layout()
    path = os.path.join(CHART_FOLDER, 'pincode_bar.png')
    plt.savefig(path); plt.close()
    chart_paths['pincode'] = 'admin_charts/pincode_bar.png'

    # ---------------- Complaints Over Time (Line) ----------------
    if 'updated_at' in df.columns:
        df['updated_at'] = pd.to_datetime(df['updated_at'], errors='coerce')
        time_series = df.groupby(df['updated_at'].dt.date).size()
        plt.figure(figsize=(7,4))
        time_series.plot(kind='line', marker='o', color='#28a745')
        plt.title('Complaints Over Time')
        plt.xlabel('Date')
        plt.ylabel('Number of Complaints')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        path = os.path.join(CHART_FOLDER, 'time_line.png')
        plt.savefig(path); plt.close()
        chart_paths['time'] = 'admin_charts/time_line.png'

    # ---------------- Complaints by District (Bar) ----------------
    district_counts = df['district'].fillna('Unknown').value_counts().nlargest(10)
    plt.figure(figsize=(7,4))
    district_counts.plot(kind='bar', color='#ff7f0e', edgecolor='black')
    plt.title('Complaints by District (Top 10)')
    plt.ylabel('Count')
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    path = os.path.join(CHART_FOLDER, 'district_bar.png')
    plt.savefig(path); plt.close()
    chart_paths['district'] = 'admin_charts/district_bar.png'

    # ---------------- Complaints by Status & Department (Stacked Bar) ----------------
    pivot = pd.crosstab(df['department'].fillna('Unknown'), df['status'].fillna('Pending'))
    pivot.plot(kind='bar', stacked=True, figsize=(8,5), colormap='tab20c')
    plt.title('Complaints by Department & Status')
    plt.xlabel('Department')
    plt.ylabel('Count')
    plt.legend(title='Status', bbox_to_anchor=(1.05,1), loc='upper left')
    plt.tight_layout()
    path = os.path.join(CHART_FOLDER, 'dept_status_bar.png')
    plt.savefig(path); plt.close()
    chart_paths['dept_status'] = 'admin_charts/dept_status_bar.png'

    return chart_paths

# -------------------- ROUTES (existing) --------------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/report")
def report():
    if not session.get("user"):
        flash("Please login first to submit a report.", "warning")
        return redirect(url_for("user_login", next="report"))
    return render_template("report.html")

@app.route("/about")
def about():
    return render_template("about.html")

# existing admin_login/user_login/signup/logout/submit_complaint etc.
# (Keep your existing handlers: admin_login, user_login, signup, logout, submit_complaint)
# For brevity in this file, we'll import them from your original implementation or paste them here.
# --- PASTE YOUR EXISTING ROUTES FROM ORIGINAL app.py BELOW ---
# To avoid duplication in this snippet, re-insert your original admin_login, user_login, signup,
# logout and submit_complaint route code exactly as before (the earlier version you had).
#
# For the purpose of this delivered snippet, we re-declare user_login, signup, logout and submit_complaint:
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email == "admin@example.com" and password == "admin123":
            session["role"] = "admin"
            flash("Admin login successful!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin credentials", "danger")
            return redirect(url_for("admin_login"))
    return render_template("admin_login.html")

@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        phone = request.form["phone"]
        password = request.form["password"]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE phone=? AND password=?", (phone, password))
        user = c.fetchone()
        conn.close()
        if user:
            session["user"] = phone
            session["role"] = "user"
            flash("Login successful!", "success")
            next_page = request.args.get("next")
            if next_page == "report":
                return redirect(url_for("report"))
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for("user_login"))
    return render_template("user_login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        phone = request.form["phone"]
        password = request.form["password"]
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (phone, password) VALUES (?, ?)", (phone, password))
            conn.commit()
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("user_login"))
        except sqlite3.IntegrityError:
            flash("Phone number already registered.", "danger")
            return redirect(url_for("signup"))
        finally:
            conn.close()
    return render_template("signup_page.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("home"))

@app.route("/submit_complaint", methods=["POST"])
def submit_complaint():
    if session.get("role") != "user":
        flash("Please log in to submit a complaint.", "danger")
        return redirect(url_for("user_login"))
    name = request.form["name"]
    phone = request.form["phone"]
    district = request.form["district"]
    block = request.form["block"]
    gp = request.form["gp"]
    village = request.form["village"]
    post = request.form["post"]
    pincode = request.form["pincode"]
    department = request.form["department"]
    complaint = request.form["complaint"]
    proof_file = request.files.get("proof")
    proof_filename = None
    if proof_file and proof_file.filename != "":
        proof_filename = secure_filename(proof_file.filename)
        proof_file.save(os.path.join(app.config["UPLOAD_FOLDER"], proof_filename))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO complaints 
                 (user_phone, name, phone, district, block, gp, village, post, pincode, department, complaint, proof) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (session["user"], name, phone, district, block, gp, village, post, pincode, department, complaint, proof_filename))
    conn.commit()
    conn.close()
    flash("Complaint submitted successfully!", "success")
    return redirect(url_for("mycomplaints"))

# -------------------- ADMIN ROUTES --------------------
def admin_required(fn):
    """Simple decorator to ensure admin role."""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required", "danger")
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/admin_dashboard")
@admin_required
def admin_dashboard():
    # generate charts
    charts = generate_charts()
    # show counts and a few metrics
    df = get_db_df()
    total = len(df)
    by_status = df['status'].fillna('Pending').value_counts().to_dict()
    by_dept = df['department'].fillna('Unknown').value_counts().to_dict()
    # pass complaints list for table/list
    complaints = get_all_complaints()
    return render_template("admin_dashboard.html",
                           charts=charts, total=total,
                           by_status=by_status, by_dept=by_dept,
                           complaints=complaints)

@app.route("/admin_user/<user_phone>")
@admin_required
def admin_user_view(user_phone):
    complaints = get_user_complaints(user_phone)
    return render_template("admin_user_view.html", complaints=complaints, user_phone=user_phone)

@app.route("/admin_complaint/<int:cid>")
@admin_required
def admin_complaint_view(cid):
    complaint = get_complaint_by_id(cid)
    if not complaint:
        flash("Complaint not found", "danger")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_complaint_view.html", complaint=complaint)

@app.route("/admin_update_status", methods=["POST"])
@admin_required
def admin_update_status_route():
    cid = request.form.get("cid")
    new_status = request.form.get("status")
    proof_file = request.files.get("admin_proof")

    admin_proof_filename = None
    if new_status and new_status.lower().strip() == "resolved":
        # Require admin_proof when marking resolved
        if not proof_file or proof_file.filename == "":
            flash("Please attach proof when marking resolved.", "danger")
            return redirect(request.referrer or url_for("admin_dashboard"))
        admin_proof_filename = secure_filename(proof_file.filename)
        proof_file.save(os.path.join(app.config["ADMIN_PROOF_FOLDER"], admin_proof_filename))

    # Update DB
    update_complaint_status(cid, new_status, admin_proof_filename)
    flash("Complaint status updated.", "success")
    return redirect(request.referrer or url_for("admin_dashboard"))

# Serve admin charts and proofs (static route helpers if needed)
@app.route('/admin_charts/<path:filename>')
@admin_required
def admin_charts(filename):
    return send_from_directory(CHART_FOLDER, filename)

@app.route('/admin_proofs/<path:filename>')
@admin_required
def admin_proofs(filename):
    return send_from_directory(ADMIN_PROOF_FOLDER, filename)

# -------------------- MY COMPLAINTS (user) --------------------
@app.route("/mycomplaints")
def mycomplaints():
    if session.get("role") == "user":
        user_phone = session.get("user")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT id, district, block, gp, village, post, pincode, department, complaint, proof, status 
            FROM complaints WHERE user_phone=?
        """, (user_phone,))
        complaints = c.fetchall()
        conn.close()
        return render_template("mycomplaints.html", complaints=complaints)
    return redirect(url_for("home"))

# -------------------- MAIN --------------------
if __name__ == "__main__":
    app.run(debug=True)
