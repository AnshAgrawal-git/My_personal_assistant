import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
]

for m in models_to_test:
    try:
        res = client.models.generate_content(model=m, contents="hello")
        print(f"SUCCESS: {m}")
        break
    except Exception as e:
        print(f"FAILED {m}: {e}")
