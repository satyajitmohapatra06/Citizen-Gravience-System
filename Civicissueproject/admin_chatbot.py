# admin_chatbot.py

import re
from datetime import datetime, timedelta
from database import get_db_connection

def get_chatbot_response(question: str) -> str:
    """
    Analyzes a question and returns a response by querying the database.
    """
    question = question.lower().strip()
    conn = get_db_connection()
    
    # Default response if no keywords are matched
    response = "Sorry, I can't quite understand that. Please try one of the suggestions or rephrase your question."

    try:
        # --- Basic KPI Questions ---
        if 'total' in question and 'complaint' in question:
            count = conn.execute("SELECT COUNT(id) FROM complaints").fetchone()[0]
            response = f"There are a total of <strong>{count}</strong> complaints in the database."
        
        elif 'pending' in question:
            count = conn.execute("SELECT COUNT(id) FROM complaints WHERE status = 'Pending'").fetchone()[0]
            response = f"There are currently <strong>{count}</strong> pending complaints."
            
        elif 'resolved' in question:
            count = conn.execute("SELECT COUNT(id) FROM complaints WHERE status = 'Resolved'").fetchone()[0]
            response = f"A total of <strong>{count}</strong> complaints have been resolved."

        # --- NEW: Time-based Questions ---
        elif 'today' in question:
            # Assumes 'updated_at' is stored in a format SQLite's date() function can parse (like ISO 8601)
            today_str = datetime.now().strftime('%Y-%m-%d')
            count = conn.execute("SELECT COUNT(id) FROM complaints WHERE DATE(updated_at) = ?", (today_str,)).fetchone()[0]
            response = f"There have been <strong>{count}</strong> complaints registered today."

        # --- NEW: Department/District Specific Questions ---
        elif 'department' in question and ('top' in question or 'most' in question):
            top_dept_query = conn.execute("""
                SELECT department, COUNT(id) as c_count FROM complaints GROUP BY department ORDER BY c_count DESC LIMIT 1
            """).fetchone()
            if top_dept_query:
                response = f"The department with the most complaints is <strong>{top_dept_query['department']}</strong> with {top_dept_query['c_count']} cases."
            else:
                response = "I couldn't determine the top department."

        elif 'from' in question or 'in' in question and 'district' in question:
            # Tries to find a district name in the query, e.g., "complaints from Khordha district"
            match = re.search(r"(?:from|in)\s+([a-zA-Z\s]+?)\s+district", question)
            if match:
                district_name = match.group(1).strip().title()
                count = conn.execute("SELECT COUNT(id) FROM complaints WHERE district = ?", (district_name,)).fetchone()[0]
                response = f"There are <strong>{count}</strong> complaints from <strong>{district_name}</strong> district."
            else:
                response = "Please specify a district name, like 'how many complaints from Khordha district?'"

        # --- NEW: Listing specific data ---
        elif 'recent' in question or 'latest' in question:
            recents = conn.execute("SELECT id, complaint FROM complaints ORDER BY id DESC LIMIT 3").fetchall()
            if recents:
                response = "Here are the 3 most recent complaints:<ul>"
                for row in recents:
                    # Slicing the complaint text to keep it short
                    complaint_preview = (row['complaint'] or '')[:50] + '...'
                    response += f"<li><strong>#{row['id']}:</strong> {complaint_preview}</li>"
                response += "</ul>"
            else:
                response = "There are no complaints to show."
        
        elif 'hello' in question or 'hi' in question:
            response = 'Hello! How can I help you with the dashboard data?'

    except Exception as e:
        print(f"Chatbot Error: {e}")
        response = "I encountered an error while trying to find an answer."
        
    finally:
        conn.close()
        
    return response