import sqlite3
import os

# --- Configuration ---
# 1. Set the name of your database file.
DB_NAME = "civic.db"

# 2. Set the name of the table you want to delete.
TABLE_TO_DELETE = "department_admins"
# ---------------------


def delete_table():
    """Connects to the database and deletes the specified table."""
    
    # Check if the database file actually exists in the folder
    if not os.path.exists(DB_NAME):
        print(f"Error: The database file '{DB_NAME}' was not found.")
        print("Please make sure this script is in the same folder as your database file.")
        return

    conn = None  # Initialize connection to None
    try:
        # Establish a connection to the SQLite database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        print(f"Connecting to '{DB_NAME}'...")
        
        # SQL command to delete the table if it exists
        # Using "IF EXISTS" prevents an error if the table is already gone
        sql_command = f"DROP TABLE IF EXISTS {TABLE_TO_DELETE};"
        
        # Execute the command
        cursor.execute(sql_command)
        
        # Commit the changes to the database
        conn.commit()
        
        print(f"Success! The table '{TABLE_TO_DELETE}' has been deleted from '{DB_NAME}'.")

    except sqlite3.Error as e:
        # Catch any potential SQL-related errors
        print(f"An error occurred: {e}")
    
    finally:
        # Ensure the database connection is closed, even if an error occurred
        if conn:
            conn.close()
            print("Database connection closed.")

# This part makes the script runnable from the command line
if __name__ == "__main__":
    delete_table()
