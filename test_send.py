import asyncio
from dotenv import load_dotenv
load_dotenv()

from app.whatsapp import send_message

async def main():
    res = await send_message('919399094867', '🤖 Hello Boss! Your AI productivity buddy is officially online!')
    print("META API RESPONSE:", res)

if __name__ == "__main__":
    asyncio.run(main())
