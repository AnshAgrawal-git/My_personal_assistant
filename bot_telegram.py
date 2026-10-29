import os
import logging
import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telegram import Update, LinkPreviewOptions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from app.agent import process_message
from app import database as db
from app import google_meet

load_dotenv()
db.init_db()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID", "940247023")
MY_NAME = os.getenv("MY_NAME", "Boss")
TZ = ZoneInfo("Asia/Kolkata")

def build_morning_briefing_text() -> str:
    today_str = datetime.datetime.now(TZ).strftime("%A, %d %B %Y")
    lines = [f"🌅 *Good morning, {MY_NAME}!* Here is your briefing for {today_str}:\n"]
    
    # 1. Calendar & Google Meet Events
    events = google_meet.get_today_events()
    lines.append("📅 *Today's Schedule:*")
    if events:
        for ev in events:
            time_part = ev.get('start', '')[11:16] if 'T' in ev.get('start', '') else 'All Day'
            meet_str = f" ([Meet Link]({ev['meet_link']}))" if ev.get('meet_link') else ""
            lines.append(f"• {time_part} — {ev['summary']}{meet_str}")
    else:
        lines.append("• No calendar events scheduled for today. Clear runway! 🚀")
        
    lines.append("")
    
    # 2. Priority Pending Tasks
    tasks = db.list_tasks(status="pending")
    lines.append(f"📋 *Pending Tasks ({len(tasks)}):*")
    if tasks:
        for t in tasks[:5]:
            p_emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(t["priority"], "⚪")
            assign_str = f" → {t['assigned_to']}" if t.get('assigned_to') else ""
            lines.append(f"{p_emoji} #{t['id']} {t['title']}{assign_str}")
        if len(tasks) > 5:
            lines.append(f"_...and {len(tasks) - 5} more._")
    else:
        lines.append("• All caught up! No pending tasks.")
        
    # 3. Overdue Check
    summary = db.get_all_tasks_summary()
    if summary["overdue"]:
        lines.append(f"\n⚠️ *Overdue Items ({len(summary['overdue'])}):*")
        for o in summary["overdue"][:3]:
            lines.append(f"• #{o['id']} {o['title']} (due: {o['due_date']})")
            
    lines.append("\n💪 Ready to roll! Reply anytime to log tasks, schedule calls, or delegate.")
    return "\n".join(lines)

def build_evening_wrapup_text() -> str:
    summary = db.get_all_tasks_summary()
    lines = [
        f"🌙 *Good evening, {MY_NAME}!* Here is your end-of-day wrap-up:\n",
        f"✅ *Completed today:* {summary['done_today']} tasks",
        f"📋 *Still pending:* {summary['pending']} tasks",
    ]
    if summary["overdue"]:
        lines.append(f"⚠️ *Overdue:* {len(summary['overdue'])} tasks")
        
    lines.append("\nGreat job today! Anything you'd like to check off or queue up for tomorrow?")
    return "\n".join(lines)

async def morning_briefing_job(context: ContextTypes.DEFAULT_TYPE):
    """Fires every morning at 08:30 AM IST."""
    if not TELEGRAM_USER_ID:
        return
    text = build_morning_briefing_text()
    try:
        await context.bot.send_message(chat_id=TELEGRAM_USER_ID, text=text, parse_mode="Markdown")
        logging.info("Morning briefing sent proactively to user.")
    except Exception as e:
        logging.error(f"Failed to send morning briefing: {e}")

async def evening_wrapup_job(context: ContextTypes.DEFAULT_TYPE):
    """Fires every evening at 08:00 PM IST."""
    if not TELEGRAM_USER_ID:
        return
    text = build_evening_wrapup_text()
    try:
        await context.bot.send_message(chat_id=TELEGRAM_USER_ID, text=text, parse_mode="Markdown")
        logging.info("Evening wrapup sent proactively to user.")
    except Exception as e:
        logging.error(f"Failed to send evening wrapup: {e}")

async def followup_checker_job(context: ContextTypes.DEFAULT_TYPE):
    """Checks for due teammate follow-ups every 10 minutes."""
    if not TELEGRAM_USER_ID:
        return
    due = db.get_due_followups()
    for f in due:
        msg = (
            f"🔔 *Follow-up Alert!*\n"
            f"Time to ping *{f['teammate_name']}* ({f['teammate_phone']}):\n"
            f"💬 Proposed message:\n_{f['message']}_"
        )
        try:
            await context.bot.send_message(chat_id=TELEGRAM_USER_ID, text=msg, parse_mode="Markdown")
            db.mark_followup_sent(f["id"])
            logging.info(f"Sent follow-up alert for task {f.get('task_id')}")
        except Exception as e:
            logging.error(f"Failed to send follow-up alert: {e}")

# ─── Commands ───

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"Hey {user.first_name}! 🤖\n\n"
        "I am your personal AI productivity buddy.\n\n"
        "• Schedule calls: *Schedule a Google Meet with Rahul tomorrow at 3 PM*\n"
        "• Save contacts: *Save Rahul's email as rahul@example.com*\n"
        "• Track tasks: *Remind me to review contracts by Friday*\n"
        "• Briefings: Try */morning* or */evening* anytime!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def morning_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = build_morning_briefing_text()
    await update.message.reply_text(text, parse_mode="Markdown")

async def evening_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = build_evening_wrapup_text()
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text
    logging.info(f"Received message from {user_id}: {text}")
    
    await update.message.chat.send_action(action="typing")
    
    try:
        reply = await process_message(user_id, text)
        logging.info(f"Agent generated reply (len {len(reply)}): {reply[:100]}...")
        
        preview_opts = LinkPreviewOptions(is_disabled=True)
        if len(reply) > 4000:
            for chunk in [reply[i:i+4000] for i in range(0, len(reply), 4000)]:
                try:
                    await update.message.reply_text(chunk, parse_mode="Markdown", link_preview_options=preview_opts)
                except Exception:
                    await update.message.reply_text(chunk, link_preview_options=preview_opts)
        else:
            try:
                await update.message.reply_text(reply, parse_mode="Markdown", link_preview_options=preview_opts)
            except Exception:
                await update.message.reply_text(reply, link_preview_options=preview_opts)
            
        logging.info("Successfully sent reply to Telegram!")
    except Exception as e:
        logging.error(f"Error processing message: {e}", exc_info=True)
        err_msg = str(e)
        if len(err_msg) > 150:
            err_msg = err_msg[:150] + "..."
        await update.message.reply_text(f"⚠️ Hit an issue: {err_msg}")

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves shared Telegram contact cards directly to database."""
    contact = update.message.contact
    if not contact:
        return
        
    name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
    phone = contact.phone_number.lstrip("+")
    
    success = db.add_teammate(name=name, phone=phone)
    if success:
        await update.message.reply_text(
            f"👤 *Contact Saved!*\n• Name: {name}\n• Phone: +{phone}\n\n"
            f"Next time you say _'Draft a message to {name.split()[0]}'_, I will generate their direct one-click WhatsApp link!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(f"⚠️ Could not save contact for {name}.")

def create_telegram_application():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN missing in .env")
        
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("morning", morning_command))
    app.add_handler(CommandHandler("evening", evening_command))
    app.add_handler(CommandHandler("briefing", morning_command))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    
    # Scheduled Jobs
    job_queue = app.job_queue
    if job_queue:
        # 8:30 AM IST Daily Morning Briefing
        job_queue.run_daily(morning_briefing_job, time=datetime.time(8, 30, tzinfo=TZ))
        # 8:00 PM IST Daily Evening Wrap-up
        job_queue.run_daily(evening_wrapup_job, time=datetime.time(20, 0, tzinfo=TZ))
        # Every 10 minutes: check teammate followups
        job_queue.run_repeating(followup_checker_job, interval=600, first=15)
        
    return app

def main():
    print("[Telegram Bot] Starting bot via polling with JobQueue...")
    app = create_telegram_application()
    print("[Telegram Bot] Bot is online and listening!")
    app.run_polling()

if __name__ == "__main__":
    main()
