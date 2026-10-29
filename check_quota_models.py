import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

candidates = [
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
]

for m in candidates:
    try:
        r = client.models.generate_content(model=m, contents="hello")
        print(f"AVAILABLE (SUCCESS): {m}")
    except Exception as e:
        print(f"UNAVAILABLE: {m} -> {type(e).__name__}: {str(e)[:100]}")
