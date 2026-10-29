import sqlite3
import os

db_path = os.path.expandvars(r"%APPDATA%\Wispr Flow\flow.sqlite")
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(Meetings);")
cols = cursor.fetchall()
print("Meetings columns:")
for c in cols:
    print(f" - {c[1]} ({c[2]})")

print("\nTodos columns:")
cursor.execute("PRAGMA table_info(Todos);")
for c in cursor.fetchall():
    print(f" - {c[1]} ({c[2]})")
