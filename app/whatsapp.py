import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("META_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID", "")
API_URL = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"

async def send_message(to: str, text: str) -> dict:
    """Send an interactive or freeform text message via WhatsApp Cloud API."""
    if not TOKEN or not PHONE_NUMBER_ID:
        raise ValueError("META_ACCESS_TOKEN and META_PHONE_NUMBER_ID must be set in .env")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": text},
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()

async def send_template(to: str, template_name: str, params: list[str]) -> dict:
    """Send a pre-approved template message for proactive outbound notifications."""
    if not TOKEN or not PHONE_NUMBER_ID:
        raise ValueError("META_ACCESS_TOKEN and META_PHONE_NUMBER_ID must be set in .env")

    components = []
    if params:
        components.append({
            "type": "body",
            "parameters": [{"type": "text", "text": p} for p in params],
        })

    async with httpx.AsyncClient() as client:
        response = await client.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "en"},
                    "components": components,
                },
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()
