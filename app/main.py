import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, BackgroundTasks
from dotenv import load_dotenv

from app.agent import process_message
from app.whatsapp import send_message
from app.database import init_db, get_due_followups, mark_followup_sent

load_dotenv()
init_db()

VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "default_verify_token")

async def followup_loop():
    """Background worker that continuously scans and dispatches due follow-ups."""
    while True:
        try:
            await process_followups()
        except Exception as e:
            print(f"[Followup Loop] Error: {e}")
        await asyncio.sleep(60)

async def process_followups():
    """Check for scheduled follow-ups and send them over WhatsApp."""
    due = get_due_followups()
    for f in due:
        try:
            await send_message(f["teammate_phone"], f["message"])
            mark_followup_sent(f["id"])
            print(f"[Follow-up] Dispatched message to {f['teammate_name']} ({f['teammate_phone']})")
        except Exception as e:
            print(f"[Follow-up] Failed to dispatch to {f['teammate_name']}: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    followup_task = asyncio.create_task(followup_loop())
    print("[Server] Background follow-up scheduler started.")
    
    telegram_bot = None
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        try:
            from bot_telegram import create_telegram_application
            telegram_bot = create_telegram_application()
            await telegram_bot.initialize()
            await telegram_bot.start()
            await telegram_bot.updater.start_polling()
            print("[Server] Telegram bot polling & scheduler started inside FastAPI.")
        except Exception as e:
            print(f"[Server] Failed to start Telegram bot: {e}")
            
    yield
    
    followup_task.cancel()
    if telegram_bot:
        try:
            await telegram_bot.updater.stop()
            await telegram_bot.stop()
            await telegram_bot.shutdown()
        except Exception as e:
            print(f"[Server] Error stopping Telegram bot: {e}")

app = FastAPI(title="WhatsApp Personal AI Agent", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "whatsapp-personal-agent"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Handshake endpoint for Meta WhatsApp Cloud API verification."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("[Webhook] Meta Webhook successfully verified!")
        return Response(content=challenge, media_type="text/plain")

    print("[Webhook] Verification failed. Tokens did not match.")
    return Response(status_code=403)

@app.post("/webhook")
async def handle_incoming_webhook(request: Request, bg_tasks: BackgroundTasks):
    """Receive messages, statuses, and delivery confirmations from WhatsApp."""
    body = await request.json()

    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        for msg in messages:
            if msg.get("type") != "text":
                continue

            sender = msg["from"]
            text = msg["text"]["body"]
            print(f"[Message] WhatsApp message received from {sender}: {text}")

            bg_tasks.add_task(dispatch_agent_reply, sender, text)

    except Exception as e:
        print(f"[Webhook] Error while parsing webhook payload: {e}")

    # Meta strictly expects an immediate HTTP 200 OK
    return Response(status_code=200)

async def dispatch_agent_reply(sender_phone: str, message_text: str):
    """Runs LangGraph agent thinking and returns answer to user."""
    try:
        reply = await process_message(sender_phone, message_text)

        # Meta limits single text payload to 4096 characters
        if len(reply) > 4000:
            for chunk in [reply[i:i+4000] for i in range(0, len(reply), 4000)]:
                await send_message(sender_phone, chunk)
        else:
            await send_message(sender_phone, reply)

        print(f"[Reply] Sent reply to {sender_phone}: {reply[:80]}...")
    except Exception as e:
        print(f"[Error] Error during message processing: {e}")
        try:
            await send_message(sender_phone, "Sorry, I hit a snag processing that. Please try again.")
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
