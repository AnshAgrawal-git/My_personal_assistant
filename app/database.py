import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent.parent))
DB_PATH = DATA_DIR / "agent.db"

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    """Create core tables if they do not exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            assigned_to TEXT DEFAULT NULL,
            due_date TEXT DEFAULT NULL,
            source TEXT DEFAULT 'manual',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT DEFAULT NULL
        );
        
        CREATE TABLE IF NOT EXISTS teammates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            email TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS followups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            teammate_name TEXT NOT NULL,
            teammate_phone TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled',
            scheduled_for TEXT NOT NULL,
            sent_at TEXT DEFAULT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        );
        
        CREATE TABLE IF NOT EXISTS wispr_meetings (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            summary TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            participant_names TEXT DEFAULT '',
            todos_json TEXT DEFAULT '[]',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS wispr_notes (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS task_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            note TEXT NOT NULL,
            progress INTEGER DEFAULT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    try:
        conn.execute("ALTER TABLE teammates ADD COLUMN email TEXT DEFAULT ''")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN progress INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()

# ─── Task Operations ───

def add_task(title: str, due_date: str = None, priority: str = "medium", assigned_to: str = None, source: str = "manual") -> int:
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO tasks (title, due_date, priority, assigned_to, source) VALUES (?, ?, ?, ?, ?)",
        (title, due_date, priority, assigned_to, source)
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id

def list_tasks(status: str = "pending", date_filter: str = None) -> list[dict]:
    conn = get_db()
    query = "SELECT * FROM tasks WHERE status = ?"
    params = [status]
    if date_filter:
        query += " AND due_date = ?"
        params.append(date_filter)
    query += " ORDER BY priority DESC, due_date ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def complete_task(task_id: int) -> bool:
    conn = get_db()
    cursor = conn.execute(
        "UPDATE tasks SET status='completed', progress=100, completed_at=? WHERE id=?",
        (datetime.now().isoformat(), task_id)
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def add_task_update(task_id: int, note: str = None, progress: int = None, status: str = None) -> bool:
    conn = get_db()
    task = conn.execute("SELECT id, status, progress FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        return False
        
    if note:
        conn.execute(
            "INSERT INTO task_updates (task_id, note, progress) VALUES (?, ?, ?)",
            (task_id, note.strip(), progress)
        )
        
    updates = []
    params = []
    if progress is not None:
        prog_val = max(0, min(100, int(progress)))
        updates.append("progress = ?")
        params.append(prog_val)
        if prog_val >= 100 and task["status"] != "completed":
            updates.append("status = 'completed'")
            updates.append("completed_at = ?")
            params.append(datetime.now().isoformat())
        elif prog_val < 100 and task["status"] == "completed":
            updates.append("status = 'pending'")
            updates.append("completed_at = NULL")
            
    if status and status != task["status"]:
        updates.append("status = ?")
        params.append(status)
        if status == "completed":
            updates.append("completed_at = ?")
            params.append(datetime.now().isoformat())
            if progress is None or progress < 100:
                updates.append("progress = 100")
        elif status == "pending":
            updates.append("completed_at = NULL")
            
    if updates:
        params.append(task_id)
        conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params)
        
    conn.commit()
    conn.close()
    return True

def get_task_details(task_id: int) -> dict | None:
    conn = get_db()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        return None
    task_dict = dict(task)
    updates = conn.execute(
        "SELECT id, note, progress, created_at FROM task_updates WHERE task_id = ? ORDER BY created_at ASC",
        (task_id,)
    ).fetchall()
    task_dict["updates"] = [dict(u) for u in updates]
    conn.close()
    return task_dict

def get_all_tasks_summary() -> dict:
    conn = get_db()
    pending = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='pending'").fetchone()[0]
    done_today = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='completed' AND date(completed_at)=date('now')"
    ).fetchone()[0]
    overdue = conn.execute(
        "SELECT * FROM tasks WHERE status='pending' AND due_date < date('now') AND due_date IS NOT NULL"
    ).fetchall()
    conn.close()
    return {
        "pending": pending,
        "done_today": done_today,
        "overdue": [dict(r) for r in overdue]
    }

# ─── Teammate Operations ───

def add_teammate(name: str, phone: str = "", email: str = "") -> bool:
    conn = get_db()
    try:
        # Check if already exists by name
        existing = conn.execute("SELECT id FROM teammates WHERE LOWER(name) = LOWER(?)", (name,)).fetchone()
        if existing:
            # Update phone/email if provided
            conn.execute(
                "UPDATE teammates SET phone = COALESCE(NULLIF(?, ''), phone), email = COALESCE(NULLIF(?, ''), email) WHERE id = ?",
                (phone, email, existing["id"])
            )
            conn.commit()
            return True
        else:
            conn.execute("INSERT INTO teammates (name, phone, email) VALUES (?, ?, ?)", (name, phone or name, email))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error in add_teammate: {e}")
        return False
    finally:
        conn.close()

def get_teammate_by_name(name: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM teammates WHERE LOWER(name) = LOWER(?)", (name,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_teammate(name: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM teammates WHERE LOWER(name) = LOWER(?)", (name,)).fetchone()
    conn.close()
    return dict(row) if row else None

def list_teammates() -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM teammates").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── Follow-Up Operations ───

def schedule_followup(teammate_name: str, teammate_phone: str, message: str, scheduled_for: str, task_id: int = None):
    conn = get_db()
    conn.execute(
        "INSERT INTO followups (task_id, teammate_name, teammate_phone, message, scheduled_for) VALUES (?, ?, ?, ?, ?)",
        (task_id, teammate_name, teammate_phone, message, scheduled_for)
    )
    conn.commit()
    conn.close()

def get_due_followups() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM followups WHERE status='scheduled' AND scheduled_for <= datetime('now')"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_followup_sent(followup_id: int):
    conn = get_db()
    conn.execute(
        "UPDATE followups SET status='sent', sent_at=? WHERE id=?",
        (datetime.now().isoformat(), followup_id)
    )
    conn.commit()
    conn.close()

# ─── Wispr Cloud Sync Operations ───

def save_synced_meetings(meetings: list[dict]):
    conn = get_db()
    for m in meetings:
        todos_str = json.dumps(m.get("todos", []))
        conn.execute("""
            INSERT OR REPLACE INTO wispr_meetings (id, title, summary, notes, participant_names, todos_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (m["id"], m.get("title", ""), m.get("summary", ""), m.get("notes", ""), m.get("participantNames", ""), todos_str, m.get("createdAt", "")))
    conn.commit()
    conn.close()

def save_synced_notes(notes: list[dict]):
    conn = get_db()
    for n in notes:
        conn.execute("""
            INSERT OR REPLACE INTO wispr_notes (id, title, content, created_at)
            VALUES (?, ?, ?, ?)
        """, (n["id"], n.get("title", ""), n.get("content", ""), n.get("createdAt", "")))
    conn.commit()
    conn.close()

def get_cloud_wispr_meetings(limit: int = 5) -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM wispr_meetings ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["todos"] = json.loads(d.get("todos_json") or "[]")
        result.append(d)
    return result

def get_cloud_meeting_details(query: str) -> dict | None:
    conn = get_db()
    row = conn.execute("""
        SELECT * FROM wispr_meetings 
        WHERE id = ? OR LOWER(title) LIKE LOWER(?) OR LOWER(summary) LIKE LOWER(?) OR LOWER(notes) LIKE LOWER(?)
        ORDER BY created_at DESC LIMIT 1
    """, (query, f"%{query}%", f"%{query}%", f"%{query}%")).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["todos"] = json.loads(d.get("todos_json") or "[]")
    return d

def get_cloud_wispr_notes(limit: int = 5) -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM wispr_notes ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_synced_tasks(tasks: list[dict]):
    conn = get_db()
    for t in tasks:
        existing = conn.execute("SELECT id FROM tasks WHERE LOWER(title) = LOWER(?)", (t.get("title", "").strip(),)).fetchone()
        if not existing:
            conn.execute("""
                INSERT INTO tasks (title, description, status, priority, assigned_to, due_date, source, created_at, completed_at, progress)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t.get("title", "").strip(),
                t.get("description", ""),
                t.get("status", "pending"),
                t.get("priority", "medium"),
                t.get("assigned_to"),
                t.get("due_date"),
                t.get("source", "manual"),
                t.get("created_at"),
                t.get("completed_at"),
                t.get("progress", 0)
            ))
        else:
            conn.execute("""
                UPDATE tasks SET status = ?, progress = ?, completed_at = ? WHERE id = ?
            """, (t.get("status", "pending"), t.get("progress", 0), t.get("completed_at"), existing["id"]))
    conn.commit()
    conn.close()

def save_synced_task_updates(updates: list[dict]):
    conn = get_db()
    for u in updates:
        conn.execute("""
            INSERT OR IGNORE INTO task_updates (id, task_id, note, progress, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (u.get("id"), u.get("task_id"), u.get("note"), u.get("progress"), u.get("created_at")))
    conn.commit()
    conn.close()

def get_all_task_updates() -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM task_updates ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_synced_teammates(teammates: list[dict]):
    conn = get_db()
    for tm in teammates:
        conn.execute("""
            INSERT OR IGNORE INTO teammates (name, phone, email)
            VALUES (?, ?, ?)
        """, (tm.get("name", "").strip(), tm.get("phone", "").strip(), tm.get("email", "").strip()))
    conn.commit()
    conn.close()

def get_all_tasks() -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM tasks ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_teammates() -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM teammates ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

init_db()
