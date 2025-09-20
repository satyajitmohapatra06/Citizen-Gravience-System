# features.py
import io
import sqlite3
import pandas as pd
from flask import Blueprint, jsonify, Response, session, flash, redirect, url_for

# --------------------
# Setup Blueprints
# --------------------
# A Blueprint is a way to organize a group of related views and other code.
# Instead of registering views and other code directly with an application,
# they are registered with a blueprint. Then the blueprint is registered
# with the application when it is available in a factory function.

# Blueprint for our new API functionality
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Blueprint for new admin features
admin_features_bp = Blueprint('admin_features', __name__, url_prefix='/admin')

DB_NAME = "civic.db"

# --------------------
# ⚙️ API Feature: Get Complaints as JSON
# --------------------
@api_bp.route('/complaints', methods=['GET'])
def get_complaints_api():
    """
    Provides a list of all complaints in JSON format.
    This is the foundation for building a mobile app or for other services to interact with your data.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    c = conn.cursor()
    c.execute("SELECT id, user_phone, name, district, department, complaint, status, updated_at FROM complaints ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    # Convert the database rows to a list of dictionaries
    complaints = [dict(row) for row in rows]
    return jsonify(complaints)

# --------------------
# 📈 Admin Feature: Export Complaints to CSV
# --------------------
@admin_features_bp.route('/export/complaints.csv')
def export_complaints_csv():
    """
    Pulls all complaint data into a Pandas DataFrame and returns it as a downloadable CSV file.
    """
    # Security check: ensure an admin is logged in
    if session.get("role") != "admin":
        flash("Admin access required for this feature.", "danger")
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect(DB_NAME)
    try:
        # Use pandas to easily read the SQL table into a DataFrame
        df = pd.read_sql_query("SELECT * FROM complaints", conn)
        
        # Use an in-memory buffer to hold the CSV data
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        csv_data = output.getvalue()

        # Create a Flask Response object to send the file to the user
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=complaints_export.csv"}
        )
    finally:
        conn.close()