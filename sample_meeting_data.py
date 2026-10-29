import sqlite3
import os
import json

db_path = os.path.expandvars(r"%APPDATA%\Wispr Flow\flow.sqlite")
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT id, title, summary, createdAt FROM Meetings WHERE isDeleted=0 ORDER BY createdAt DESC LIMIT 3")
for r in cursor.fetchall():
    print("------------------------------------------")
    print(f"TITLE: {r['title']} | ID: {r['id']}")
    print(f"CREATED: {r['createdAt']}")
    summary_text = r['summary'] or ""
    print(f"SUMMARY ({len(summary_text)} chars):")
    print(summary_text[:300] + "...")
    
    # Check linked Todos
    cursor.execute("SELECT id, title, status FROM Todos WHERE meetingId=? AND isDeleted=0", (r['id'],))
    todos = cursor.fetchall()
    print("LINKED TODOS:", [dict(t) for t in todos])
