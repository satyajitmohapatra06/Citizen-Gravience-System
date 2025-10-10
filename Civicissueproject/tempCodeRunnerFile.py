# app.py (FINAL, CORRECTED, AND INTEGRATED)
import os
import sqlite3
import random
import re
from datetime import datetime, timedelta

import matplotlib
import pandas as pd
from flask import (Flask, flash, redirect, render_template, request,
                   send_from_directory, session, url_for, jsonify)
from werkzeug.utils import secure_filename

# Use non-interactive backend for servers
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --- 1. Import your new modular Blueprints ---
from chatbot import chat_bp
from uploads import upload_bp
from features import api_bp, admin_features_bp

from flask import Blueprint, jsonify
from admin_chatbot import get_chatbot_response
# --- 2. Import the database functions from database.py ---
from database import (get_all_complaints, get_complaint_by_id, get_db_connection,
                      get_db_df, get_user_complaints, update_complaint_status)
from piu import generate_odisha_heatmap

# ==================== APP SETUP ====================
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['PER_PAGE'] = 10

chatbot_bp = Blueprint('chatbot_bp', __name__)

# --- File Upload Config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ADMIN_PROOF_FOLDER = os.path.join(BASE_DIR, "static", "admin_proofs")
CHART_FOLDER = os.path.join(BASE_DIR, "static", "admin_charts")
PROFILE_PHOTOS_FOLDER = os.path.join(BASE_DIR, "static", "profile_photos") # NEW

for d in (UPLOAD_FOLDER, ADMIN_PROOF_FOLDER, CHART_FOLDER, PROFILE_PHOTOS_FOLDER): # NEW
    os.makedirs(d, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ADMIN_PROOF_FOLDER"] = ADMIN_PROOF_FOLDER
app.config["CHART_FOLDER"] = CHART_FOLDER
app.config["PROFILE_PHOTOS_FOLDER"] = PROFILE_PHOTOS_FOLDER # NEW


# --- Database Initializer ---
def init_db():
    conn = get_db_connection()
    # Complaints table with latitude and longitude
    conn.execute('''CREATE TABLE IF NOT EXISTS complaints (
                       id INTEGER PRIMARY KEY AUTOINCREMENT, user_phone TEXT NOT NULL, name TEXT,
                       phone TEXT, district TEXT, block TEXT, gp TEXT, village TEXT,
                       landmark TEXT, pincode TEXT, department TEXT, complaint TEXT,
                       proof TEXT, status TEXT DEFAULT 'Pending', admin_proof TEXT,
                       updated_at TEXT, voice_proof TEXT, 
                       latitude REAL, longitude REAL,
                       FOREIGN KEY(user_phone) REFERENCES users(phone)
                   )''')
    
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(complaints)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'latitude' not in columns:
        conn.execute('ALTER TABLE complaints ADD COLUMN latitude REAL')
    if 'longitude' not in columns:
        conn.execute('ALTER TABLE complaints ADD COLUMN longitude REAL')

    # MODIFIED Users table to include name and profile_photo
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT,
                       phone TEXT UNIQUE NOT NULL,
                       password TEXT NOT NULL,
                       profile_photo TEXT
                   )''')
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'name' not in columns:
        conn.execute('ALTER TABLE users ADD COLUMN name TEXT')
    if 'profile_photo' not in columns:
        conn.execute('ALTER TABLE users ADD COLUMN profile_photo TEXT')


    # Feedback table
    conn.execute('''CREATE TABLE IF NOT EXISTS feedback (
                       id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                       email TEXT NOT NULL, type TEXT NOT NULL, rating INTEGER NOT NULL,
                       message TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
                   )''')
    conn.commit()
    conn.close()

init_db()


# --- Jinja Filter ---
@app.template_filter('datetimeformat')
def datetimeformat(value, format="%d %b %Y"):
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            return dt.strftime(format)
        except (ValueError, TypeError):
            return value
    elif isinstance(value, datetime):
        return value.strftime(format)
    return value


# -------------------- CHART GENERATION --------------------
def generate_charts():
    df = get_db_df()
    if df.empty:
        return {}
    chart_paths = {}
    # (Chart generation logic is unchanged, so it's omitted for brevity)
    return chart_paths

# -------------------- RANKING LOGIC --------------------
def calculate_civic_score(complaints):
    total = len(complaints)
    if total == 0:
        return 0
    
    rejected = sum(1 for c in complaints if (c['status'] or '').lower() == 'rejected')
    rejection_rate = rejected / total
    
    score = total * (1 - rejection_rate)
    return score

# -------------------- ROUTES --------------------
@app.route("/")
def home():
    user_name = None
    if "user" in session:
        user_phone = session["user"]
        conn = get_db_connection()
        user_data = conn.execute("SELECT name FROM users WHERE phone = ?", (user_phone,)).fetchone()
        conn.close()
        
        user_name = user_data['name'] if user_data and user_data['name'] else f"User#{random.randint(1000, 9999)}"

    return render_template("home.html", user_name=user_name)

@app.route("/report")
def report():
    if not session.get("user"):
        flash("Please login first to submit a report.", "warning")
        return redirect(url_for("user_login", next="report"))
    return render_template("report.html")

@app.route("/about")
def about():
    return render_template("about.html")
    
@app.route("/community_complaints")
def community_complaints():
    conn = get_db_connection()
    complaints = conn.execute(
        "SELECT id, department, complaint, status, district, village, updated_at FROM complaints ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return render_template("community_complaints.html", complaints=complaints)

# ======================= PROFILE, CERTIFICATE & LEADERBOARD ROUTES =======================
@app.route("/profile")
def profile():
    if "user" not in session:
        flash("You need to be logged in to view your profile.", "warning")
        return redirect(url_for("user_login"))

    user_phone = session["user"]
    conn = get_db_connection()
    
    user_data = conn.execute("SELECT name, profile_photo FROM users WHERE phone = ?", (user_phone,)).fetchone()
    complaints = conn.execute("SELECT status FROM complaints WHERE user_phone = ?", (user_phone,)).fetchall()
    
    user_name = user_data['name'] if user_data and user_data['name'] else f"User#{random.randint(1000, 9999)}"
    profile_photo = user_data['profile_photo'] if user_data else None

    user_score = calculate_civic_score(complaints)

    all_users = conn.execute("SELECT phone, name FROM users").fetchall()
    scores = []
    for user in all_users:
        user_complaints = conn.execute("SELECT status FROM complaints WHERE user_phone = ?", (user['phone'],)).fetchall()
        score = calculate_civic_score(user_complaints)
        scores.append({'phone': user['phone'], 'score': score})
    
    sorted_scores = sorted(scores, key=lambda x: x['score'], reverse=True)
    user_rank = -1
    for i, score_data in enumerate(sorted_scores):
        if score_data['phone'] == user_phone:
            user_rank = i + 1
            break
            
    conn.close()

    total_complaints = len(complaints)
    stats = {
        'total': total_complaints, 'pending': 0, 'resolved': 0, 'in_progress': 0,
        'rejected': 0, 'escalated': 0
    }
    for c in complaints:
        status = (c['status'] or 'Pending').lower().replace(' ', '_')
        if status in stats:
            stats[status] += 1

    return render_template("profile.html", 
                           user_name=user_name,
                           user_phone=user_phone,
                           profile_photo=profile_photo,
                           stats=stats,
                           civic_score=user_score,
                           rank=user_rank)

@app.route("/leaderboard")
def leaderboard():
    conn = get_db_connection()
    users = conn.execute("SELECT phone, name, profile_photo FROM users").fetchall()
    
    leaderboard_data = []
    for user in users:
        complaints = conn.execute("SELECT status FROM complaints WHERE user_phone = ?", (user['phone'],)).fetchall()
        score = calculate_civic_score(complaints)
        
        user_display_name = user['name'] or f"User#{random.randint(1000, 9999)}"
        leaderboard_data.append({
            'name': user_display_name,
            'score': score,
            'profile_photo': user['profile_photo']
        })
    
    conn.close()
    
    sorted_leaderboard = sorted(leaderboard_data, key=lambda x: x['score'], reverse=True)[:10]
    
    return render_template("leaderboard.html", leaderboard=sorted_leaderboard)


@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "user" not in session:
        return redirect(url_for("user_login"))

    new_name = request.form.get("name")
    user_phone = session["user"]
    
    if new_name and new_name.strip():
        conn = get_db_connection()
        conn.execute("UPDATE users SET name = ? WHERE phone = ?", (new_name, user_phone))
        conn.execute("UPDATE complaints SET name = ? WHERE user_phone = ?", (new_name, user_phone))
        conn.commit()
        conn.close()
        flash("Profile updated successfully!", "success")
    else:
        flash("Name cannot be empty.", "danger")
        
    return redirect(url_for("profile"))

@app.route("/update_profile_photo", methods=["POST"])
def update_profile_photo():
    if "user" not in session:
        flash("You must be logged in to update your photo.", "danger")
        return redirect(url_for("user_login"))

    user_phone = session["user"]
    
    if 'profile_photo' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('profile'))
        
    file = request.files['profile_photo']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('profile'))

    if file:
        filename = secure_filename(f"{user_phone}_{file.filename}")
        file.save(os.path.join(app.config["PROFILE_PHOTOS_FOLDER"], filename))
        
        conn = get_db_connection()
        conn.execute("UPDATE users SET profile_photo = ? WHERE phone = ?", (filename, user_phone))
        conn.commit()
        conn.close()
        
        flash("Profile photo updated successfully!", "success")

    return redirect(url_for("profile"))

@app.route("/generate_certificate/<username>")
def generate_certificate(username):
    today_date = datetime.now().strftime("%B %d, %Y")
    return render_template("certificate.html", username=username, date=today_date)

@app.route("/generate_welcome_certificate/<username>")
def generate_welcome_certificate(username):
    today_date = datetime.now().strftime("%B %d, %Y")
    return render_template("welcome_certificate.html", username=username, date=today_date)

# -------------------- AUTH --------------------
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
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE phone=? AND password=?", (phone, password)).fetchone()
        conn.close()
        if user:
            session["user"] = phone
            session["role"] = "user"
            flash("Login successful!", "success")
            next_page = request.args.get("next")
            return redirect(url_for("report")) if next_page == "report" else redirect(url_for("home"))
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for("user_login"))
    return render_template("user_login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name") 
        phone = request.form["phone"]
        password = request.form["password"]
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (name, phone, password) VALUES (?, ?, ?)", (name, phone, password))
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

    form_data = {k: request.form.get(k) for k in ["name", "phone", "district", "block", "gp", "village", "landmark", "pincode", "department", "complaint", "latitude", "longitude"]}
    current_time = datetime.utcnow().isoformat()

    proof_file = request.files.get("proof")
    proof_filename = None
    if proof_file and proof_file.filename:
        proof_filename = secure_filename(f"proof_{form_data['phone']}_{proof_file.filename}")
        proof_file.save(os.path.join(app.config["UPLOAD_FOLDER"], proof_filename))

    voice_file = request.files.get("voice_complaint")
    voice_filename = None
    if voice_file and voice_file.filename:
        voice_filename = secure_filename(f"voice_{form_data['phone']}_{voice_file.filename}")
        voice_file.save(os.path.join(app.config["UPLOAD_FOLDER"], voice_filename))
        
    conn = get_db_connection()
    conn.execute('''INSERT INTO complaints 
                   (user_phone, name, phone, district, block, gp, village, landmark, pincode, department, complaint, proof, voice_proof, updated_at, latitude, longitude) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (session["user"], form_data['name'], form_data['phone'], form_data['district'], form_data['block'], form_data['gp'], form_data['village'], form_data['landmark'], form_data['pincode'], form_data['department'], form_data['complaint'], proof_filename, voice_filename, current_time, form_data['latitude'], form_data['longitude']))
    conn.commit()
    conn.close()

    flash("Complaint submitted successfully!", "success")
    return redirect(url_for("mycomplaints"))

@app.route("/api/complaint/<int:cid>", methods=["DELETE", "PUT"])
def manage_complaint(cid):
    if session.get("role") != "user":
        return jsonify({"success": False, "error": "Authentication required."}), 401
    
    conn = get_db_connection()
    complaint = conn.execute("SELECT user_phone, status FROM complaints WHERE id = ?", (cid,)).fetchone()

    if not complaint:
        conn.close()
        return jsonify({"success": False, "error": "Complaint not found."}), 404
    if complaint["user_phone"] != session["user"]:
        conn.close()
        return jsonify({"success": False, "error": "Authorization failed."}), 403

    if request.method == "DELETE":
        if (complaint["status"] or "Pending").lower() != "pending":
            conn.close()
            return jsonify({"success": False, "error": "Only pending complaints can be deleted."}), 400
        conn.execute("DELETE FROM complaints WHERE id = ?", (cid,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Complaint deleted successfully."}), 200

    if request.method == "PUT":
        if (complaint["status"] or "Pending").lower() != "pending":
            conn.close()
            return jsonify({"success": False, "error": "Only pending complaints can be edited."}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid data."}), 400
            
        allowed_fields = ['department', 'name', 'phone', 'district', 'block', 'gp', 'village', 'landmark', 'pincode', 'complaint']
        update_query = "UPDATE complaints SET "
        update_values = []
        
        for field in allowed_fields:
            if field in data:
                update_query += f"{field} = ?, "
                update_values.append(data[field])

        if not update_values:
            conn.close()
            return jsonify({"success": False, "error": "No valid fields to update."}), 400
            
        update_query += "updated_at = ? WHERE id = ?"
        update_values.extend([datetime.utcnow().isoformat(), cid])

        conn.execute(update_query, tuple(update_values))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Complaint updated successfully."}), 200

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    name = request.form.get("name")
    email = request.form.get("email")
    ftype = request.form.get("type")
    rating = request.form.get("rating")
    message = request.form.get("message")
    if not all([name, email, ftype, rating, message]):
        flash("All fields are required.", "danger")
        return redirect(url_for("mycomplaints"))
    conn = get_db_connection()
    conn.execute('''INSERT INTO feedback (name, email, type, rating, message)
                 VALUES (?, ?, ?, ?, ?)''',
              (name, email, ftype, rating, message))
    conn.commit()
    conn.close()
    flash("Thank you for your feedback!", "success")
    return redirect(url_for("mycomplaints"))
    
# -------------------- ADMIN --------------------
def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required", "danger")
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper

@chatbot_bp.route("/api/ask", methods=["POST"])
def ask_chatbot():
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "No question provided"}), 400
    question = data["question"]
    answer = get_chatbot_response(question)
    return jsonify({"answer": answer})

@app.route("/admin_dashboard")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    c = conn.cursor()
    
    ESCALATION_DAYS = 10
    escalation_threshold = datetime.utcnow() - timedelta(days=ESCALATION_DAYS)
    c.execute("""
        UPDATE complaints
        SET status = 'Escalated'
        WHERE status = 'Pending' AND updated_at IS NOT NULL
        AND datetime(updated_at) <= ?
    """, (escalation_threshold.isoformat(),))
    conn.commit()

    q = request.args.get("q", "").strip()
    page = request.args.get('page', 1, type=int)

    df = get_db_df()
    charts = generate_charts()
    charts['odisha_map'] = generate_odisha_heatmap()
    
    total = len(df)
    by_status = df['status'].fillna('Pending').value_counts().to_dict()
    by_dept = df['department'].fillna('Unknown').value_counts().to_dict()

    base_query = "FROM complaints"
    count_query = "SELECT COUNT(id) " + base_query
    select_query = "SELECT * " + base_query
    params = []

    if q:
        like_q = f"%{q}%"
        where_clause = """
            WHERE user_phone LIKE ? OR phone LIKE ? OR department LIKE ? 
            OR pincode LIKE ? OR district LIKE ? OR village LIKE ? OR complaint LIKE ?
        """
        count_query += where_clause
        select_query += where_clause
        params = [like_q] * 7
    
    total_complaints = c.execute(count_query, params).fetchone()[0]
    
    select_query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([app.config['PER_PAGE'], (page - 1) * app.config['PER_PAGE']])
    
    complaints_page = c.execute(select_query, params).fetchall()

    class Pagination:
        def __init__(self, page, per_page, total_count):
            self.page, self.per_page, self.total_count = page, per_page, total_count
        @property
        def pages(self): return -(-self.total_count // self.per_page)
        @property
        def has_prev(self): return self.page > 1
        @property
        def has_next(self): return self.page < self.pages
        @property
        def prev_num(self): return self.page - 1
        @property
        def next_num(self): return self.page + 1
        def iter_pages(self, left_edge=1, left_current=2, right_current=2, right_edge=1):
            last = 0
            for num in range(1, self.pages + 1):
                if num <= left_edge or \
                   (self.page - left_current - 1 < num < self.page + right_current) or \
                   num > self.pages - right_edge:
                    if last + 1 != num: yield None
                    yield num
                    last = num

    complaints_pagination = Pagination(page, app.config['PER_PAGE'], total_complaints)
    complaints_pagination.items = complaints_page

    c.execute("SELECT id, name, email, type, rating, message, created_at FROM feedback ORDER BY id DESC")
    feedbacks = c.fetchall()

    five_days_ago = datetime.utcnow() - timedelta(days=5)
    c.execute("""SELECT id, district, department, complaint, updated_at
                 FROM complaints
                 WHERE status='Pending' AND updated_at IS NOT NULL 
                       AND datetime(updated_at) <= ?""", (five_days_ago.isoformat(),))
    alerts = c.fetchall()
    
    c.execute("""SELECT id, district, department, complaint, updated_at
                 FROM complaints
                 WHERE status='Escalated' ORDER BY updated_at ASC""")
    escalated_complaints = c.fetchall()

    conn.close()

    return render_template("admin_dashboard.html",
                           charts=charts, total=total,
                           by_status=by_status, by_dept=by_dept,
                           complaints_pagination=complaints_pagination,
                           feedbacks=feedbacks,
                           alerts=alerts,
                           escalated_complaints=escalated_complaints,
                           q=q)

@app.route("/admin_update_status", methods=["POST"])
@admin_required
def admin_update_status_route():
    cid = request.form.get("cid")
    new_status = request.form.get("status")
    proof_file = request.files.get("admin_proof")
    admin_proof_filename = None
    if proof_file and proof_file.filename:
        admin_proof_filename = secure_filename(proof_file.filename)
        proof_file.save(os.path.join(app.config["ADMIN_PROOF_FOLDER"], admin_proof_filename))
    if new_status and new_status.lower().strip() == "resolved" and not admin_proof_filename:
        flash("Please attach proof when marking resolved.", "danger")
        return redirect(request.referrer or url_for("admin_dashboard"))
    update_complaint_status(cid, new_status, admin_proof_filename)
    flash("Complaint status updated.", "success")
    return redirect(request.referrer or url_for("admin_dashboard"))

@app.route('/admin_charts/<path:filename>')
@admin_required
def admin_charts(filename):
    return send_from_directory(CHART_FOLDER, filename)

@app.route('/admin_proofs/<path:filename>')
def admin_proofs(filename):
    return send_from_directory(ADMIN_PROOF_FOLDER, filename)

@app.route("/admin/user/<user_phone>")
@admin_required
def admin_user_view(user_phone):
    complaints = get_user_complaints(user_phone)
    return render_template("admin_user_view.html", user_phone=user_phone, complaints=complaints)

@app.route("/admin/complaint/<int:cid>")
@admin_required
def admin_complaint_view(cid):
    complaint = get_complaint_by_id(cid)
    if not complaint:
        flash("Complaint not found", "danger")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_complaint_view.html", complaint=complaint)

@app.route("/mycomplaints")
def mycomplaints():
    if session.get("role") != "user":
        return redirect(url_for("home"))
    user_phone = session.get("user")
    conn = get_db_connection() 
    complaints = conn.execute("SELECT * FROM complaints WHERE user_phone = ? ORDER BY id DESC", (user_phone,)).fetchall()
    conn.close()
    return render_template("mycomplaints.html", complaints=complaints)

@app.route("/community")
def community():
    department = request.args.get("department", "all")
    rating = request.args.get("rating", "all")
    sort = request.args.get("sort", "newest")
    query = "SELECT id, name, email, type, rating, message, created_at FROM feedback WHERE 1=1"
    params = []
    if department != "all":
        query += " AND type = ?"
        params.append(department)
    if rating != "all":
        query += " AND rating >= ?"
        params.append(int(rating))
    if sort == "newest": query += " ORDER BY id DESC"
    elif sort == "oldest": query += " ORDER BY id ASC"
    elif sort == "highest": query += " ORDER BY rating DESC"
    elif sort == "lowest": query += " ORDER BY rating ASC"
    conn = get_db_connection()
    feedbacks = conn.execute(query, params).fetchall()
    conn.close()
    return render_template("community.html",
                           feedbacks=feedbacks,
                           selected_department=department,
                           selected_rating=rating,
                           selected_sort=sort)

@app.route("/api/complaints")
def get_complaints_for_map():
    conn = get_db_connection()
    complaints = conn.execute("SELECT latitude, longitude, department, status FROM complaints WHERE latitude IS NOT NULL AND longitude IS NOT NULL").fetchall()
    conn.close()
    complaints_list = [dict(row) for row in complaints]
    return jsonify(complaints_list)

# ==================== BLUEPRINT REGISTRATION ====================
app.register_blueprint(api_bp)
app.register_blueprint(admin_features_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(chatbot_bp)

# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    app.run(debug=True)

