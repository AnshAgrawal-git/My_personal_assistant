import os
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
    """)
    conn.commit()
    try:
        conn.execute("ALTER TABLE teammates ADD COLUMN email TEXT DEFAULT ''")
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
        "UPDATE tasks SET status='completed', completed_at=? WHERE id=?",
        (datetime.now().isoformat(), task_id)
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

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

init_db()
