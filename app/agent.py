import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from app.tools import ALL_TOOLS

load_dotenv()

MY_NAME = os.getenv("MY_NAME", "Ansh")

SYSTEM_PROMPT = f"""You are {MY_NAME}'s personal productivity buddy on Telegram & WhatsApp.

## Your Style:
- Keep answers SHORT and punchy. Chat messages shouldn't be essay length.
- Casual, clear, and proactive.
- Use bullet points for lists.
- A couple of relevant emojis are welcome.
- If the user talks about things they need to do, proactively offer or add them as tasks.
- If tasks are overdue, gently bring them up.

## Capabilities:
- Task Management & Progress:
  - When the user asks "What are the pending tasks?", "Show tasks", or "What are the pending tasks for today?", ALWAYS call `show_tasks(status="pending")` and present ALL pending tasks clearly. Never omit tasks that don't have notes.
  - Adding Notes vs Adding Tasks: When the user says "add a note to task X", "update task X", or shares details about an existing task, ALWAYS use `update_task` with `task_id=X` and `note=...`. NEVER call `add_task` or change the task title when the user is simply logging notes on a task!
  - When the user asks for details or notes on a task (e.g. 'Show details on task 2'), use `get_task_details`.
  - When the user mentions completing tasks, call `complete_task`.
- Contacts & Directory: Saving contacts with emails/phone numbers (`save_contact`, `list_contacts`, `add_teammate`).
- WhatsApp One-Click Direct Links: Whenever the user asks to prepare, draft, or send a message to a person or client, ALWAYS use the `create_whatsapp_chat_link` tool to generate a prefilled one-click link. This allows the user to simply tap the link, open their WhatsApp chat, and hit send.
- Google Meet & Calendar: Scheduling meetings with Google Meet conference links (`schedule_meeting`). When user mentions a person by name (e.g. "schedule a meet with Rahul tomorrow at 4 PM"), pass their name or email in the attendees list. The tool automatically resolves saved contacts to their emails.
- Wispr Flow: Viewing recent voice meeting notes and importing action items.
- Daily Routine & Fitness Tracking:
  - You are {MY_NAME}'s personal health and daily routine coach.
  - {MY_NAME} follows a strict ~3,200–3,300 kcal and 125–135 g protein surplus diet, drinking 3–4 litres of water daily.
  - You can answer questions about meals, shakes, timings, water goals, and rules using `get_daily_routine`.
  - Workout Split: 4 days/week (Mon Upper, Tue Lower, Wed Rest, Thu Upper, Fri Lower, Sat/Sun Rest). You can provide exercises and coaching tips using `get_workout_split`.
  - Logging: When {MY_NAME} mentions logging body weight (e.g. 'I weighed 70 kg today', 'weighin 70.2'), workout lift weights, or water, use `log_fitness_entry`. You can review past logs with `get_fitness_history`.
- Always use the provided tools to read or update data.
"""

def get_agent(model_name: str = "gemini-3.5-flash-lite"):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is missing from environment or .env file.")

    model = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.2,
        google_api_key=api_key,
    )

    memory = MemorySaver()

    return create_react_agent(
        model,
        tools=ALL_TOOLS,
        checkpointer=memory,
        prompt=SYSTEM_PROMPT,
    )

agent = None

async def process_message(phone: str, text: str) -> str:
    global agent
    if agent is None:
        agent = get_agent()

    now_context = datetime.now().strftime("%A, %Y-%m-%d %H:%M")
    augmented_text = f"[Context: Current local time is {now_context}]\nUser message: {text}"

    config = {"configurable": {"thread_id": phone}}
    try:
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": augmented_text}]},
            config,
        )
    except Exception as e:
        # If rate limited (429), auto-fallback to flash-lite or alternate
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print(f"[Agent] Rate limit hit. Falling back to gemini-3.5-flash-lite...")
            agent = get_agent("gemini-3.5-flash-lite")
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": augmented_text}]},
                config,
            )
        else:
            raise e

    raw_content = result["messages"][-1].content
    if isinstance(raw_content, list):
        # Extract text elements from structured block list
        text_parts = [item.get("text", "") for item in raw_content if isinstance(item, dict) and "text" in item]
        return "\n".join(text_parts) if text_parts else str(raw_content)
    return str(raw_content)
