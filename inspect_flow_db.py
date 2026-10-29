import sqlite3
import os

db_path = os.path.expandvars(r"%APPDATA%\Wispr Flow\flow.sqlite")
print(f"Opening: {db_path} (exists: {os.path.exists(db_path)})")

conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in flow.sqlite:")
for t in tables:
    print(" -", t[0])
