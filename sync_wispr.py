import os
import sqlite3
import httpx
from dotenv import load_dotenv

load_dotenv()

RENDER_URL = os.getenv("RENDER_URL", "https://my-personal-assistant-atkn.onrender.com")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9288553367:AAHCsaRkubxdIbygEMPgmG6nz5ZaRp-AoPQ")
DB_PATH = os.path.expandvars(r"%APPDATA%\Wispr Flow\flow.sqlite")

def sync():
    if not os.path.exists(DB_PATH):
        print(f"[Wispr Sync] Error: Wispr Flow database not found at: {DB_PATH}")
        return

    print("[Wispr Sync] Reading local Wispr Flow meetings and notes...")
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch all non-deleted meetings
    cursor.execute("""
        SELECT id, title, summary, notes, participantNames, createdAt 
        FROM Meetings 
        WHERE isDeleted = 0 
        ORDER BY createdAt DESC
    """)
    meetings = []
    for r in cursor.fetchall():
        m = dict(r)
        cursor.execute("""
            SELECT id, title, status 
            FROM Todos 
            WHERE meetingId = ? AND isDeleted = 0
        """, (m["id"],))
        m["todos"] = [dict(t) for t in cursor.fetchall()]
        meetings.append(m)

    # Fetch all non-deleted notes
    cursor.execute("""
        SELECT id, title, content, createdAt 
        FROM Notes 
        WHERE isDeleted = 0 
        ORDER BY createdAt DESC
    """)
    notes = [dict(r) for r in cursor.fetchall()]
    conn.close()

    print(f"[Wispr Sync] Uploading {len(meetings)} meetings and {len(notes)} notes to Cloud Bot...")
    payload = {
        "sync_token": BOT_TOKEN,
        "meetings": meetings,
        "notes": notes
    }

    try:
        response = httpx.post(f"{RENDER_URL}/sync-wispr", json=payload, timeout=30.0)
        if response.status_code == 200:
            data = response.json()
            print(f"[Wispr Sync] SUCCESS! Synced {data.get('synced_meetings')} meetings and {data.get('synced_notes')} notes to Render Cloud!")
        else:
            print(f"[Wispr Sync] Server returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[Wispr Sync] Failed to reach cloud bot: {e}")

if __name__ == "__main__":
    sync()
