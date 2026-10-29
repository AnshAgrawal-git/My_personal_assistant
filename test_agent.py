import asyncio
from dotenv import load_dotenv
load_dotenv()

from app.agent import process_message

async def main():
    print("Testing LangGraph agent...")
    res = await process_message("919399094867", "Hey, add a task: Review Q3 budget by tomorrow")
    print("\n--- AGENT RESPONSE ---")
    print(res)
    print("----------------------\n")

if __name__ == "__main__":
    asyncio.run(main())
