import sqlite3
import os
import json

db_path = os.path.expandvars(r"%APPDATA%\Wispr Flow\flow.sqlite")
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT id, title, summary, action_items, createdAt FROM Meetings ORDER BY createdAt DESC LIMIT 3")
rows = cursor.fetchall()
print("Recent Meetings in Wispr Flow:")
for r in rows:
    print(f"\n--- {r['title']} (ID: {r['id']}) ---")
    print(f"Created: {r['createdAt']}")
    if r['summary']:
        print("Summary excerpt:", str(r['summary'])[:200])
    if r['action_items']:
        print("Action Items:", r['action_items'])

print("\n--- Todos table count ---")
cursor.execute("SELECT COUNT(*) FROM Todos")
print("Total Todos in Wispr Flow:", cursor.fetchone()[0])
