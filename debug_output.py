import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.agent import process_message

async def main():
    res = await process_message("123", "show my tasks")
    print("TYPE:", type(res))
    print("REPR:", repr(res))

if __name__ == "__main__":
    asyncio.run(main())
