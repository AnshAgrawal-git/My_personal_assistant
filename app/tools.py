import re
import urllib.parse
from datetime import datetime
from langchain_core.tools import tool
from app import database as db
from app import wispr
from app import google_meet

# ─── Task Management Tools ───

@tool
def add_task(title: str, due_date: str = None, priority: str = "medium") -> str:
    """Add a new task to your task list.
    
    Args:
        title: Short description or title of the task.
        due_date: Due date as YYYY-MM-DD. None if open-ended.
        priority: Priority level (low, medium, high, urgent).
    """
    task_id = db.add_task(title, due_date, priority)
    msg = f"✅ Task #{task_id} added: '{title}'"
    if due_date:
        msg += f" (due {due_date})"
    return msg

@tool
def show_tasks(status: str = "pending") -> str:
    """View tasks filtered by status.
    
    Args:
        status: Task status — 'pending', 'completed', or 'cancelled'.
    """
    tasks = db.list_tasks(status)
    if not tasks:
        return f"No {status} tasks found! 🚀"
    
    lines = [f"📋 Your {status} tasks:"]
    for t in tasks:
        emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(t["priority"], "⚪")
        line = f"{emoji} #{t['id']} — {t['title']}"
        if t["due_date"]:
            line += f" (due {t['due_date']})"
        if t["assigned_to"]:
            line += f" → assigned to {t['assigned_to']}"
        lines.append(line)
    return "\n".join(lines)

@tool
def complete_task(task_id: int) -> str:
    """Mark an existing task as completed.
    
    Args:
        task_id: The integer ID number of the task.
    """
    success = db.complete_task(task_id)
    if success:
        return f"🎉 Task #{task_id} marked as completed!"
    return f"❌ Task #{task_id} not found."

@tool
def daily_summary() -> str:
    """Show an overview of pending tasks, completed tasks, and overdue items."""
    summary = db.get_all_tasks_summary()
    lines = [
        "📊 Daily Overview:",
        f"• Pending tasks: {summary['pending']}",
        f"• Completed today: {summary['done_today']}",
    ]
    if summary["overdue"]:
        lines.append(f"• ⚠️ Overdue ({len(summary['overdue'])}):")
        for t in summary["overdue"]:
            lines.append(f"   - #{t['id']} {t['title']} (due: {t['due_date']})")
    return "\n".join(lines)

# ─── Teammate & Assignment Tools ───

@tool
def add_teammate(name: str, phone: str) -> str:
    """Register a teammate's WhatsApp number for task assignment and follow-up.
    
    Args:
        name: Teammate's name.
        phone: Phone number with country code (e.g., 919876543210).
    """
    success = db.add_teammate(name, phone)
    if success:
        return f"👤 Registered teammate '{name}' ({phone})."
    return f"'{name}' or this phone number is already registered."

@tool
def list_teammates() -> str:
    """List all registered teammates."""
    mates = db.list_teammates()
    if not mates:
        return "No teammates registered yet. Use add_teammate first."
    lines = ["👥 Registered Teammates:"]
    for m in mates:
        lines.append(f"• {m['name']} ({m['phone']})")
    return "\n".join(lines)

@tool
def assign_task_to_teammate(title: str, teammate_name: str, due_date: str = None, followup_message: str = None) -> str:
    """Create a task and assign it to a teammate, automatically scheduling a WhatsApp ping.
    
    Args:
        title: What the task is.
        teammate_name: Registered teammate name.
        due_date: Optional due date (YYYY-MM-DD).
        followup_message: Message to send them on WhatsApp. Defaults to a concise friendly note.
    """
    teammate = db.get_teammate(teammate_name)
    if not teammate:
        return f"❌ Teammate '{teammate_name}' not found. Please register them first using add_teammate."

    task_id = db.add_task(title, due_date, assigned_to=teammate["name"])

    if not followup_message:
        followup_message = f"hey {teammate['name'].lower()}, quick heads up — assigning '{title}' to you"
        if due_date:
            followup_message += f", due by {due_date}"

    db.schedule_followup(
        teammate_name=teammate["name"],
        teammate_phone=teammate["phone"],
        message=followup_message,
        scheduled_for=datetime.now().isoformat(),
        task_id=task_id,
    )

    return f"✅ Task #{task_id} assigned to {teammate['name']}.\n📩 Follow-up queued: \"{followup_message}\""

# ─── Wispr Flow Integration Tools ───

@tool
def get_recent_wispr_meetings(limit: int = 5) -> str:
    """Retrieve recent meetings recorded by Wispr Flow with summaries and action items.
    
    Args:
        limit: Number of recent meetings to retrieve (default 5).
    """
    meetings = wispr.get_recent_meetings(limit=limit)
    if not meetings:
        return "No recent meetings found in Wispr Flow."

    output = ["🎙️ Recent Wispr Flow Meetings:"]
    for m in meetings:
        title = m.get("title") or "Untitled Meeting"
        created = m.get("createdAt", "")[:10]
        output.append(f"\n• {title} ({created}) [ID: {m['id']}]")
        
        summary = m.get("summary")
        if summary:
            # First 200 chars of summary
            output.append(f"  Summary: {summary[:200]}...")
        
        todos = m.get("todos", [])
        if todos:
            output.append(f"  Action items ({len(todos)}):")
            for t in todos:
                output.append(f"   - [ ] {t.get('title')}")
                
    return "\n".join(output)

@tool
def import_wispr_action_items(meeting_query: str) -> str:
    """Search for a Wispr Flow meeting and import all its action items as tracked tasks in your database.
    
    Args:
        meeting_query: Meeting title keyword or meeting ID.
    """
    meeting = wispr.get_meeting_details(meeting_query)
    if not meeting:
        return f"❌ Could not find any meeting matching '{meeting_query}' in Wispr Flow."

    title = meeting.get("title") or "Untitled Meeting"
    todos = meeting.get("todos", [])
    
    if not todos:
        # If no explicit todos in Todos table, see if summary mentions action items
        summary = meeting.get("summary") or ""
        return f"Meeting '{title}' found, but no explicit action items were linked in Wispr Flow.\nSummary snippet:\n{summary[:300]}"

    imported_count = 0
    for t in todos:
        task_title = t.get("title", "").strip()
        if task_title:
            db.add_task(
                title=f"[{title}] {task_title}",
                source="wispr_meeting"
            )
            imported_count += 1

    return f"✅ Successfully imported {imported_count} action items from meeting '{title}' into your task database!"

@tool
def get_wispr_notes(limit: int = 5) -> str:
    """Retrieve scratchpad notes or thoughts recorded in Wispr Flow.
    
    Args:
        limit: Number of notes to fetch.
    """
    notes = wispr.get_recent_notes(limit=limit)
    if not notes:
        return "No scratchpad notes found in Wispr Flow."

    output = ["📝 Wispr Flow Scratchpad Notes:"]
    for n in notes:
        title = n.get("title") or "Untitled Note"
        content = (n.get("content") or "")[:150]
        output.append(f"\n• {title}: {content}...")
    return "\n".join(output)

# ─── Contacts & Google Meet Tools ───

@tool
def save_contact(name: str, email: str = "", phone: str = "") -> str:
    """Save or update a contact's email address and/or phone number.
    Use this when the user mentions someone's email or phone, or wants to remember a person for meetings or tasks.
    
    Args:
        name: Name of the person (e.g. 'Rahul', 'Priya').
        email: Email address (e.g. 'rahul@example.com').
        phone: Optional phone number.
    """
    success = db.add_teammate(name=name, phone=phone, email=email)
    if success:
        details = []
        if email:
            details.append(f"email: {email}")
        if phone:
            details.append(f"phone: {phone}")
        det_str = f" ({', '.join(details)})" if details else ""
        return f"👤 Saved contact '{name}'{det_str}."
    return f"❌ Failed to save contact '{name}'."

@tool
def list_contacts() -> str:
    """List all saved contacts with their email addresses and phone numbers."""
    mates = db.list_teammates()
    if not mates:
        return "No contacts saved yet. Use save_contact to add someone."
    lines = ["👥 Saved Contacts:"]
    for m in mates:
        info = []
        if m.get("email"):
            info.append(f"📧 {m['email']}")
        if m.get("phone") and m["phone"] != m["name"]:
            info.append(f"📱 {m['phone']}")
        info_str = f" ({', '.join(info)})" if info else ""
        lines.append(f"• {m['name']}{info_str}")
    return "\n".join(lines)

@tool
def schedule_meeting(
    title: str,
    attendees: list[str],
    start_time_iso: str,
    duration_minutes: int = 30,
    description: str = ""
) -> str:
    """Schedule a Google Calendar event with a Google Meet conference link and send invitations.
    
    Args:
        title: Title/subject of the meeting (e.g. 'Sync with Rahul on Project Roadmap').
        attendees: List of attendee names or email addresses. Saved contacts will automatically have their email looked up.
        start_time_iso: Start time in ISO format (e.g. '2026-10-30T15:00:00').
        duration_minutes: Meeting duration in minutes (default 30).
        description: Optional description or agenda.
    """
    resolved_emails = []
    missing_names = []
    
    for att in attendees:
        att = att.strip()
        if not att:
            continue
        if "@" in att:
            resolved_emails.append(att)
        else:
            contact = db.get_teammate_by_name(att)
            if contact and contact.get("email"):
                resolved_emails.append(contact["email"])
            else:
                missing_names.append(att)
                
    if missing_names:
        return (
            f"⚠️ Could not find email address for: {', '.join(missing_names)}.\n"
            f"Please provide their email address so I can schedule the meeting."
        )
        
    try:
        event = google_meet.create_google_meet_event(
            summary=title,
            start_iso=start_time_iso,
            duration_minutes=duration_minutes,
            attendee_emails=resolved_emails,
            description=description
        )
        meet_link = event.get('meet_link') or "Meet link generation pending"
        invites = ", ".join(event.get('attendees', [])) or "None"
        return (
            f"📅 Meeting Scheduled Successfully!\n"
            f"• Title: {event.get('summary')}\n"
            f"• Start: {event.get('start')}\n"
            f"• Duration: {duration_minutes} mins\n"
            f"• Invites sent to: {invites}\n"
            f"• Google Meet: {meet_link}"
        )
    except FileNotFoundError:
        return (
            "⚠️ Google Calendar integration not configured yet: credentials.json is missing.\n"
            "Please follow the Google Cloud setup guide to add credentials.json."
        )
    except Exception as e:
        return f"❌ Failed to schedule Google Meet: {str(e)}"

# ─── WhatsApp Quick-Send Tools ───

@tool
def create_whatsapp_chat_link(recipient: str, message: str) -> str:
    """Generate a one-click WhatsApp Click-to-Chat link that opens the recipient's direct chat with the pre-filled message.
    
    Args:
        recipient: Name of teammate/client (e.g. 'Pralad', 'Shanzel', 'Shobana') or phone number with country code.
        message: The drafted text message ready to send.
    """
    phone = ""
    # Look up in contacts
    contact = db.get_teammate_by_name(recipient)
    if contact and contact.get("phone"):
        phone = contact["phone"]
    else:
        # Check if recipient contains numbers directly
        clean = re.sub(r"[^\d]", "", recipient)
        if len(clean) >= 10:
            phone = clean
            
    encoded_text = urllib.parse.quote(message)
    
    if phone:
        clean_phone = re.sub(r"[^\d]", "", phone).lstrip("0")
        if len(clean_phone) == 10:
            clean_phone = "91" + clean_phone
        wa_url = f"https://wa.me/{clean_phone}?text={encoded_text}"
        return (
            f"💬 *Drafted WhatsApp Message for {recipient}:*\n"
            f"_{message}_\n\n"
            f"📲 [👉 Click to Open WhatsApp & Send to {recipient}]({wa_url})"
        )
    else:
        wa_url = f"https://api.whatsapp.com/send?text={encoded_text}"
        return (
            f"💬 *Drafted WhatsApp Message for {recipient}:*\n"
            f"_{message}_\n\n"
            f"📲 [👉 Click to Open WhatsApp & Send]({wa_url})\n\n"
            f"💡 *Tip:* Reply with: *'{recipient}\\'s phone is +91...'* so next time it opens their specific chat directly!"
        )

ALL_TOOLS = [
    add_task,
    show_tasks,
    complete_task,
    daily_summary,
    add_teammate,
    list_teammates,
    assign_task_to_teammate,
    get_recent_wispr_meetings,
    import_wispr_action_items,
    get_wispr_notes,
    save_contact,
    list_contacts,
    schedule_meeting,
    create_whatsapp_chat_link,
]
