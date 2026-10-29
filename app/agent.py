import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from app.tools import ALL_TOOLS

load_dotenv()

MY_NAME = os.getenv("MY_NAME", "Boss")

SYSTEM_PROMPT = f"""You are {MY_NAME}'s personal productivity buddy on Telegram & WhatsApp.

## Your Style:
- Keep answers SHORT and punchy. Chat messages shouldn't be essay length.
- Casual, clear, and proactive.
- Use bullet points for lists.
- A couple of relevant emojis are welcome.
- If the user talks about things they need to do, proactively offer or add them as tasks.
- If tasks are overdue, gently bring them up.

## Capabilities:
- Task Management: Adding, listing, completing tasks, and daily summaries.
- Contacts & Directory: Saving contacts with emails/phone numbers (`save_contact`, `list_contacts`).
- WhatsApp One-Click Direct Links: Whenever the user asks to prepare, draft, or send a message to a person or client, ALWAYS use the `create_whatsapp_chat_link` tool to generate a prefilled one-click link. This allows the user to simply tap the link, open their WhatsApp chat, and hit send.
- Google Meet & Calendar: Scheduling meetings with Google Meet conference links (`schedule_meeting`). When user mentions a person by name (e.g. "schedule a meet with Rahul tomorrow at 4 PM"), pass their name or email in the attendees list. The tool automatically resolves saved contacts to their emails.
- Wispr Flow: Viewing recent voice meeting notes and importing action items.
- Always use the provided tools to read or update data.
"""

def get_agent():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is missing from environment or .env file.")

    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash",
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
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": augmented_text}]},
        config,
    )

    raw_content = result["messages"][-1].content
    if isinstance(raw_content, list):
        # Extract text elements from structured block list
        text_parts = [item.get("text", "") for item in raw_content if isinstance(item, dict) and "text" in item]
        return "\n".join(text_parts) if text_parts else str(raw_content)
    return str(raw_content)
