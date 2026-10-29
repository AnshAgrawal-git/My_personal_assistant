"""Wispr Flow Direct Bridge

Connects natively with the local Wispr Flow database (flow.sqlite)
to access real-time meeting notes, transcripts, summaries, and action items.
Zero external cloud lag, zero API rate limits, 100% real-time.
"""

import os
import sqlite3
from typing import Any

def get_flow_db_path() -> str:
    return os.path.expandvars(r"%APPDATA%\Wispr Flow\flow.sqlite")

def get_recent_meetings(limit: int = 5) -> list[dict[str, Any]]:
    """Retrieve the most recent meetings recorded by Wispr Flow."""
    db_path = get_flow_db_path()
    if not os.path.exists(db_path):
        return []

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, summary, notes, participantNames, createdAt 
        FROM Meetings 
        WHERE isDeleted = 0 
        ORDER BY createdAt DESC 
        LIMIT ?
    """, (limit,))
    
    meetings = []
    for r in cursor.fetchall():
        meeting = dict(r)
        
        # Pull associated action items from Todos table
        cursor.execute("""
            SELECT id, title, status 
            FROM Todos 
            WHERE meetingId = ? AND isDeleted = 0
        """, (meeting["id"],))
        meeting["todos"] = [dict(t) for t in cursor.fetchall()]
        meetings.append(meeting)

    conn.close()
    return meetings

def get_meeting_details(meeting_query: str) -> dict[str, Any] | None:
    """Find a meeting by title keyword or ID and return full notes & todos."""
    db_path = get_flow_db_path()
    if not os.path.exists(db_path):
        return None

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, summary, notes, participantNames, createdAt 
        FROM Meetings 
        WHERE isDeleted = 0 AND (LOWER(title) LIKE LOWER(?) OR id = ?)
        ORDER BY createdAt DESC 
        LIMIT 1
    """, (f"%{meeting_query}%", meeting_query))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    meeting = dict(row)
    cursor.execute("""
        SELECT id, title, status 
        FROM Todos 
        WHERE meetingId = ? AND isDeleted = 0
    """, (meeting["id"],))
    meeting["todos"] = [dict(t) for t in cursor.fetchall()]
    conn.close()
    return meeting

def get_recent_notes(limit: int = 5) -> list[dict[str, Any]]:
    """Retrieve scratchpad notes from Wispr Flow."""
    db_path = get_flow_db_path()
    if not os.path.exists(db_path):
        return []

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, content, createdAt 
        FROM Notes 
        WHERE isDeleted = 0 
        ORDER BY createdAt DESC 
        LIMIT ?
    """, (limit,))
    
    notes = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return notes
