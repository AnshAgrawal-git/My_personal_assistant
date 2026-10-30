import os
import sqlite3
import httpx
from dotenv import load_dotenv

load_dotenv()

RENDER_URL = os.getenv("RENDER_URL", "https://my-personal-assistant-atkn.onrender.com")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9288553367:AAHCsaRkubxdIbygEMPgmG6nz5ZaRp-AoPQ")
DB_PATH = os.path.expandvars(r"%APPDATA%\Wispr Flow\flow.sqlite")
LOCAL_AGENT_DB = os.path.join(os.path.dirname(__file__), "agent.db")

def sync():
    meetings = []
    notes = []
    tasks = []
    teammates = []

    # 1. Read Wispr Flow if installed
    if os.path.exists(DB_PATH):
        try:
            print("[Wispr Sync] Reading local Wispr Flow meetings and notes...")
            conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, title, summary, notes, participantNames, createdAt 
                FROM Meetings 
                WHERE isDeleted = 0 
                ORDER BY createdAt DESC
            """)
            for r in cursor.fetchall():
                m = dict(r)
                cursor.execute("""
                    SELECT id, title, status 
                    FROM Todos 
                    WHERE meetingId = ? AND isDeleted = 0
                """, (m["id"],))
                m["todos"] = [dict(t) for t in cursor.fetchall()]
                meetings.append(m)

            cursor.execute("""
                SELECT id, title, content, createdAt 
                FROM Notes 
                WHERE isDeleted = 0 
                ORDER BY createdAt DESC
            """)
            notes = [dict(r) for r in cursor.fetchall()]
            conn.close()
        except Exception as e:
            print(f"[Wispr Sync] Could not read Wispr Flow database: {e}")

    # 2. Read Local Tasks & Teammates from agent.db
    task_updates = []
    if os.path.exists(LOCAL_AGENT_DB):
        try:
            conn = sqlite3.connect(LOCAL_AGENT_DB)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM tasks;")
            tasks = [dict(r) for r in c.fetchall()]
            c.execute("SELECT * FROM teammates;")
            teammates = [dict(r) for r in c.fetchall()]
            try:
                c.execute("SELECT * FROM task_updates;")
                task_updates = [dict(r) for r in c.fetchall()]
            except Exception:
                pass
            conn.close()
        except Exception as e:
            print(f"[Wispr Sync] Could not read local agent.db: {e}")

    print(f"[Wispr Sync] Uploading {len(meetings)} meetings, {len(notes)} notes, {len(tasks)} tasks, {len(task_updates)} updates to Cloud Bot...")
    payload = {
        "sync_token": BOT_TOKEN,
        "meetings": meetings,
        "notes": notes,
        "tasks": tasks,
        "teammates": teammates,
        "task_updates": task_updates
    }

    try:
        response = httpx.post(f"{RENDER_URL}/sync-wispr", json=payload, timeout=30.0)
        if response.status_code == 200:
            data = response.json()
            print(f"[Wispr Sync] SUCCESS! Synced {data.get('synced_meetings')} meetings, {data.get('synced_notes')} notes, and {data.get('synced_tasks')} tasks to Render Cloud!")
            
            # Sync back cloud teammates and cloud tasks
            cloud_teammates = data.get("cloud_teammates", [])
            cloud_tasks = data.get("cloud_tasks", [])
            cloud_updates = data.get("cloud_task_updates", [])
            if os.path.exists(LOCAL_AGENT_DB):
                try:
                    conn = sqlite3.connect(LOCAL_AGENT_DB)
                    for tm in cloud_teammates:
                        conn.execute("""
                            INSERT OR IGNORE INTO teammates (name, phone, email)
                            VALUES (?, ?, ?)
                        """, (tm.get("name", ""), tm.get("phone", ""), tm.get("email", "")))
                    for t in cloud_tasks:
                        conn.execute("""
                            UPDATE tasks SET status = ?, progress = ?, completed_at = ? WHERE id = ?
                        """, (t.get("status", "pending"), t.get("progress", 0), t.get("completed_at"), t.get("id")))
                    for u in cloud_updates:
                        conn.execute("""
                            INSERT OR IGNORE INTO task_updates (id, task_id, note, progress, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (u.get("id"), u.get("task_id"), u.get("note"), u.get("progress"), u.get("created_at")))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"[Wispr Sync] Could not update local database: {e}")
        else:
            print(f"[Wispr Sync] Server returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[Wispr Sync] Failed to reach cloud bot: {e}")

if __name__ == "__main__":
    sync()
