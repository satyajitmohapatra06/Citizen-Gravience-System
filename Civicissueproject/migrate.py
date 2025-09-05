import sqlite3

DB = "civic.db"

def ensure_column(c, table, name, coltype):
    c.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in c.fetchall()]
    if name not in cols:
        print(f"Adding column {name}...")
        c.execute(f"ALTER TABLE {table} ADD COLUMN {name} {coltype}")
    else:
        print(f"Column {name} already exists")

conn = sqlite3.connect(DB)
c = conn.cursor()

ensure_column(c, "complaints", "admin_proof", "TEXT")
ensure_column(c, "complaints", "updated_at", "TEXT")

conn.commit()
conn.close()
print("Migration complete ✅")
