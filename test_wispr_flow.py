import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.agent import process_message

async def main():
    print("Testing Wispr meeting query...")
    try:
        reply = await process_message("test_user", "What were my recent meetings in Wispr Flow?")
        print("SUCCESS! Length:", len(reply))
        print("Reply preview:")
        print(reply.encode("ascii", "replace").decode("ascii")[:400])
    except Exception as e:
        print("ERROR:", type(e), e)

if __name__ == "__main__":
    asyncio.run(main())
