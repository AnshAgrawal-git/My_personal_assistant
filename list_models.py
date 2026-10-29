import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing available models...")
for m in client.models.list():
    if "generateContent" in (m.supported_actions or []):
        print(m.name)
