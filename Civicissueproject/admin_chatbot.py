# admin_chatbot.py

import re
from datetime import datetime, timedelta
from database import get_db_connection

def get_chatbot_response(question: str, department: str = None) -> str:
    """
    Analyzes a question and returns a response by querying the database.
    Filters by the provided department if one is given.
    """
    question = question.lower().strip()
    conn = get_db_connection()
    
    # --- Base query parameters based on the admin's role ---
    base_where_clauses = []
    base_params = []
    
    if department:
        base_where_clauses.append("department = ?")
        base_params.append(department)

    # --- Helper function to build WHERE clauses ---
    def build_query_parts(extra_clause: str = None, extra_params: list = []):
        """Builds the WHERE clause and param list."""
        clauses = list(base_where_clauses)
        params = list(base_params)
        
        if extra_clause:
            clauses.append(extra_clause)
            params.extend(extra_params)
            
        if not clauses:
            return "", []
            
        return " WHERE " + " AND ".join(clauses), params
    # --- END HELPER ---

    # Default response if no keywords are matched
    response = "Sorry, I can't quite understand that. Please try one of the suggestions or rephrase your question."
    dept_context_str = f" for <strong>{department}</strong>" if department else " in the system"

    try:
        # --- KPI & Count Questions ---
        if 'total' in question and 'complaint' in question:
            where_clause, params = build_query_parts()
            count = conn.execute(f"SELECT COUNT(id) FROM complaints {where_clause}", params).fetchone()[0]
            response = f"There are <strong>{count}</strong> total complaints{dept_context_str}."
        
        elif 'pending' in question or 'unresolved' in question:
            where_clause, params = build_query_parts("status = 'Pending'")
            count = conn.execute(f"SELECT COUNT(id) FROM complaints {where_clause}", params).fetchone()[0]
            response = f"There are <strong>{count}</strong> pending complaints{dept_context_str}."
            
        elif 'resolved' in question:
            where_clause, params = build_query_parts("status = 'Resolved'")
            count = conn.execute(f"SELECT COUNT(id) FROM complaints {where_clause}", params).fetchone()[0]
            response = f"A total of <strong>{count}</strong> complaints have been resolved{dept_context_str}."

        elif 'escalated' in question:
            where_clause, params = build_query_parts("status = 'Escalated'")
            count = conn.execute(f"SELECT COUNT(id) FROM complaints {where_clause}", params).fetchone()[0]
            response = f"There are <strong>{count}</strong> escalated complaints{dept_context_str}."

        elif 'in progress' in question:
            where_clause, params = build_query_parts("status = 'In Progress'")
            count = conn.execute(f"SELECT COUNT(id) FROM complaints {where_clause}", params).fetchone()[0]
            response = f"There are <strong>{count}</strong> complaints 'In Progress'{dept_context_str}."

        elif 'rejected' in question:
            where_clause, params = build_query_parts("status = 'Rejected'")
            count = conn.execute(f"SELECT COUNT(id) FROM complaints {where_clause}", params).fetchone()[0]
            response = f"There are <strong>{count}</strong> rejected complaints{dept_context_str}."

        # --- Time-based Questions ---
        elif 'today' in question:
            today_str = datetime.now().strftime('%Y-%m-%d')
            where_clause, params = build_query_parts("DATE(updated_at) = ?", [today_str])
            count = conn.execute(f"SELECT COUNT(id) FROM complaints {where_clause}", params).fetchone()[0]
            response = f"There have been <strong>{count}</strong> complaints registered today{dept_context_str}."
        
        elif 'last 7 days' in question or 'last week' in question:
            seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            where_clause, params = build_query_parts("DATE(updated_at) >= ?", [seven_days_ago])
            count = conn.execute(f"SELECT COUNT(id) FROM complaints {where_clause}", params).fetchone()[0]
            response = f"There have been <strong>{count}</strong> complaints in the last 7 days{dept_context_str}."
        
        elif 'last 30 days' in question or 'last month' in question:
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            where_clause, params = build_query_parts("DATE(updated_at) >= ?", [thirty_days_ago])
            count = conn.execute(f"SELECT COUNT(id) FROM complaints {where_clause}", params).fetchone()[0]
            response = f"There have been <strong>{count}</strong> complaints in the last 30 days{dept_context_str}."

        # --- Location-based Questions ---
        elif 'hotspot' in question or 'top district' in question:
            where_clause, params = build_query_parts()
            query = f"SELECT district, COUNT(id) as c_count FROM complaints {where_clause} GROUP BY district ORDER BY c_count DESC LIMIT 3"
            districts = conn.execute(query, params).fetchall()
            if districts:
                response = f"The top 3 district hotspots{dept_context_str} are:<ul>"
                for i, row in enumerate(districts):
                    response += f"<li><strong>#{i+1} {row['district'] or 'Unknown'}:</strong> {row['c_count']} complaints</li>"
                response += "</ul>"
            else:
                response = f"There is not enough location data to show hotspots{dept_context_str}."

        # --- Specific Complaint Status ---
        elif 'status of' in question or 'complaint #' in question:
            match = re.search(r"(?:status of|complaint)\s*#?(\d+)", question)
            if match:
                complaint_id = match.group(1)
                complaint = conn.execute("SELECT status, department FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
                if complaint:
                    if not department or complaint['department'] == department:
                        response = f"The status of complaint <strong>#{complaint_id}</strong> is: <strong>{complaint['status']}</strong>."
                    else:
                        response = f"Sorry, complaint #{complaint_id} is for a different department."
                else:
                    response = f"Sorry, I could not find a complaint with ID #{complaint_id}."
            else:
                response = "Please ask using the format 'status of #123'."

        # --- Feedback Questions ---
        elif 'feedback' in question or 'rating' in question:
            fb_where_clauses = []
            fb_params = []
            fb_context_str = " in total"
            
            if department:
                fb_where_clauses.append("type = ?")
                fb_params.append(department)
                fb_context_str = f" for <strong>{department}</strong>"
            
            fb_where_clause = " WHERE " + " AND ".join(fb_where_clauses) if fb_where_clauses else ""
            stats = conn.execute(f"SELECT COUNT(id) as c, AVG(rating) as r FROM feedback {fb_where_clause}", fb_params).fetchone()
            
            if stats and stats['c'] > 0:
                avg_rating = stats['r'] or 0
                response = f"There are <strong>{stats['c']}</strong> feedback submissions{fb_context_str}, with an average rating of <strong>{avg_rating:.1f}</strong> out of 5."
            else:
                response = f"There is no feedback{fb_context_str} yet."

        # --- User-based Questions ---
        elif 'top user' in question or 'most active user' in question:
            where_clause, params = build_query_parts()
            query = f"SELECT name, user_phone, COUNT(id) as c_count FROM complaints {where_clause} GROUP BY user_phone ORDER BY c_count DESC LIMIT 1"
            top_user = conn.execute(query, params).fetchone()
            if top_user:
                user_name = top_user['name'] or f"User ({top_user['user_phone']})"
                response = f"The most active user{dept_context_str} is <strong>{user_name}</strong> with <strong>{top_user['c_count']}</strong> complaints."
            else:
                response = f"There are no users to show{dept_context_str}."

        # --- General Questions ---
        elif 'recent' in question or 'latest' in question:
            where_clause, params = build_query_parts()
            recents = conn.execute(f"SELECT id, complaint FROM complaints {where_clause} ORDER BY id DESC LIMIT 3", params).fetchall()
            if recents:
                response = f"Here are the 3 most recent complaints{dept_context_str}:<ul>"
                for row in recents:
                    complaint_preview = (row['complaint'] or '')[:50] + '...'
                    response += f"<li><strong>#{row['id']}:</strong> {complaint_preview}</li>"
                response += "</ul>"
            else:
                response = f"There are no complaints to show{dept_context_str}."
        
        elif 'hello' in question or 'hi' in question:
            response = 'Hello! How can I help you with the dashboard data?'

    except Exception as e:
        print(f"Chatbot Error: {e}")
        response = "I encountered an error while trying to find an answer."
        
    finally:
        conn.close()
        
    return response