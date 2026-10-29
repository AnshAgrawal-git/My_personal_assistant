import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.google_meet import CREDENTIALS_PATH, TOKEN_PATH, SCOPES

def main():
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
    print("Opening Google sign-in window in your browser...", flush=True)
    creds = flow.run_local_server(
        port=8080,
        prompt="consent",
        access_type="offline",
        open_browser=True
    )
    with open(TOKEN_PATH, "w") as token:
        token.write(creds.to_json())
    print("\nSUCCESS! token.json saved successfully!", flush=True)

if __name__ == "__main__":
    main()
