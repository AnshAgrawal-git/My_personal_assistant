# WhatsApp Personal AI Agent — Project Tracker & Master Development Guide

> **Project Location:** `D:\projects\whatsapp-agent`  
> **Status:** Phase 1 in progress (Scaffolded & Ready for Keys)  
> **Target Stack:** Python 3.11+ | FastAPI | LangGraph | Gemini 2.0 Flash | SQLite/PostgreSQL | WhatsApp Business Cloud API | Railway | Wispr Flow MCP

---

## 🧭 How to Continue Across Chats
If you ever switch conversations or reopen Antigravity IDE:
1. Open folder in Antigravity IDE: `File` -> `Open Folder` -> `D:\projects\whatsapp-agent`.
2. Check `PROJECT_TRACKER.md` (this file) to see which step is checked `[x]` vs pending `[ ]`.
3. Tell Antigravity: *"I am working on my whatsapp-agent project in `D:\projects\whatsapp-agent`. Please check PROJECT_TRACKER.md and continue from the next pending step."*

---

## 🗺️ Master Phase & Checklist

### Phase 1: Local Setup & Credentials (In Progress)
- [x] **Step 1.1**: Scaffold project directories and code structure in `D:\projects\whatsapp-agent`.
- [x] **Step 1.2**: Get Gemini API key & verify with `gemini-3.1-flash-lite`.
- [x] **Step 1.3**: Set up Meta Developer App & WhatsApp Cloud sandbox test number.
- [x] **Step 1.4**: Configure `.env` file with credentials.
- [x] **Step 1.5**: Create Python virtual environment and install `requirements.txt`.
- [x] **Step 1.6**: Set up Cloudflare public tunnel (`trycloudflare.com`) and verify Meta webhook handshake.
- [ ] **Step 1.7**: Resolve Meta new business account restriction (`131031 Business Account locked`) via Account Quality review to enable outbound messaging.

### Phase 2: Agent Brain & Core Functionality
- [ ] **Step 2.1**: Test SQLite task creation (`add_task`, `show_tasks`, `complete_task`).
- [ ] **Step 2.2**: Test teammate registration & assignment via LangGraph tool calls.
- [ ] **Step 2.3**: Verify conversation memory per phone number.
- [ ] **Step 2.4**: Test end-to-end messaging flow from personal WhatsApp to bot and back.

### Phase 3: Wispr Flow Integration (Completed ✅)
- [x] **Step 3.1**: Discovered and connected Wispr Flow's native storage (`%APPDATA%\Wispr Flow\flow.sqlite`).
- [x] **Step 3.2**: Created `app/wispr.py` direct bridge for meetings, notes, and action items.
- [x] **Step 3.3**: Created LangGraph agent tools:
  - `get_recent_wispr_meetings` (summaries, dates, action items)
  - `import_wispr_action_items` (convert meeting action items to tracked tasks)
  - `get_wispr_notes` (scratchpad jottings and thoughts)
- [x] **Step 3.4**: Reloaded live Telegram bot with Wispr Flow tools active.

### Phase 3.5: Google Calendar, Google Meet & Contact Book (Completed ✅)
- [x] **Step 3.5.1**: Set up Google Cloud Console OAuth Desktop Client & configured credentials (`credentials.json`).
- [x] **Step 3.5.2**: Generated and persisted permanent OAuth refresh token (`token.json`).
- [x] **Step 3.5.3**: Created `app/google_meet.py` to create Calendar events with automatic Google Meet conference links & email invitations.
- [x] **Step 3.5.4**: Added Contact Book tools in `app/tools.py` (`save_contact`, `list_contacts`) allowing user to save emails and schedule meetings simply by calling out teammate/contact names.
- [x] **Step 3.5.5**: Live end-to-end test passed: generated real Google Meet event and verified link creation.
- [x] **Step 3.5.6**: Telegram bot restarted and live with Google Meet and Contact memory capabilities.

### Phase 3.6: Proactive Schedulers & Daily Briefings (Completed ✅)
- [x] **Step 3.6.1**: Integrated `APScheduler` via `python-telegram-bot[job-queue]`.
- [x] **Step 3.6.2**: Configured Daily Morning Briefing at **08:30 AM IST** (aggregates today's meetings with Meet links, pending tasks, overdue items).
- [x] **Step 3.6.3**: Configured Daily Evening Wrap-up at **08:00 PM IST** (summarizes completed vs pending tasks and plans tomorrow).
- [x] **Step 3.6.4**: Configured 10-minute automated background runner for teammate follow-up notifications.
- [x] **Step 3.6.5**: Added on-demand instant trigger commands: `/morning`, `/evening`, `/briefing`.

### Phase 4: 24/7 Cloud Deployment (Completed ✅)
- [x] **Step 4.1**: Created GitHub repository (`AnshAgrawal-git/My_personal_assistant`) and pushed production codebase.
- [x] **Step 4.2**: Deployed Dockerized application to Render Cloud (`https://my-personal-assistant-atkn.onrender.com`).
- [x] **Step 4.3**: Configured production environment variables with Gemini API, Telegram Token, and OAuth credentials.
- [x] **Step 4.4**: Configured UptimeRobot 5-minute automated HTTP monitor to keep the free cloud container awake 24/7.
- [x] **Step 4.5**: Verified live health endpoints and real-time Telegram polling without conflicts.

### Phase 5: Future Backlog / Planned Enhancements (Pending ⏸️)
- [ ] **Step 5.1**: Google Docs & Sheets Integration (`create_google_doc`, `create_google_sheet`) with automated sharing.
- [ ] **Step 5.2**: Meta WhatsApp Cloud API reconnection (once business entity verification is complete).
- [ ] **Step 5.3**: Cloud PostgreSQL migration for multi-instance high-availability.

---

## 📂 Project Structure Map
```
whatsapp-agent/
├── app/
│   ├── __init__.py          # Package marker
│   ├── main.py              # FastAPI server, webhook route & background workers
│   ├── agent.py             # LangGraph ReAct agent & memory checkpointer
│   ├── tools.py             # Tools: Task CRUD, teammates, follow-ups
│   ├── whatsapp.py          # WhatsApp Cloud API client (send messages & templates)
│   ├── database.py          # SQLite database connection, tables, queries
│   └── wispr.py             # Wispr Flow bridge & meeting action-item extractor
├── .env.example             # Template for required environment variables
├── .gitignore               # Ignores venv, .env, and local database
├── requirements.txt         # Pinned Python package dependencies
├── Dockerfile               # Production container definition for Railway
├── railway.toml             # Railway deployment config
└── PROJECT_TRACKER.md       # This file (source of truth)
```

---

## ⚡ Quick Commands Cheatsheet

```powershell
# Navigate to project
cd C:\Users\lenovo\.gemini\antigravity\scratch\whatsapp-agent

# Activate virtual environment
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

# Run server locally (port 8000)
python -m app.main

# In another terminal: Start ngrok tunnel
ngrok http 8000
```
