import sqlite3

conn = sqlite3.connect("civic.db")
c = conn.cursor()

# Add status column if not exists
try:
    c.execute("ALTER TABLE complaints ADD COLUMN status TEXT DEFAULT 'Pending'")
    print("✅ Status column added")
except Exception as e:
    print("⚠️", e)

conn.commit()
conn.close()
