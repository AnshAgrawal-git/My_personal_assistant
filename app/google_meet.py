import os
import datetime
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

DATA_DIR = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parent.parent))
CREDENTIALS_PATH = DATA_DIR / "credentials.json"
TOKEN_PATH = DATA_DIR / "token.json"

def get_calendar_service():
    """Authenticates and returns the Google Calendar API service."""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    elif os.getenv("GOOGLE_TOKEN_JSON"):
        import json
        info = json.loads(os.getenv("GOOGLE_TOKEN_JSON"))
        creds = Credentials.from_authorized_user_info(info, SCOPES)
        try:
            with open(TOKEN_PATH, 'w') as f:
                f.write(creds.to_json())
        except Exception:
            pass
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            try:
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
            except Exception:
                pass
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    "credentials.json not found in project folder and GOOGLE_TOKEN_JSON not set."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
            try:
                with open(TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
            except Exception:
                pass

    return build('calendar', 'v3', credentials=creds)

def create_google_meet_event(
    summary: str,
    start_iso: str,
    duration_minutes: int = 30,
    attendee_emails: list[str] = None,
    description: str = ""
) -> dict:
    """
    Creates a Google Calendar event with a Google Meet conference link and sends invites.
    
    start_iso: ISO 8601 string, e.g. '2026-10-30T15:00:00'
    """
    service = get_calendar_service()
    
    start_dt = datetime.datetime.fromisoformat(start_iso)
    end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
    
    # Assume local timezone if not explicitly provided
    timezone = "Asia/Kolkata"
    
    event_body = {
        'summary': summary,
        'description': description or "Scheduled via AI Personal Assistant",
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': timezone,
        },
        'conferenceData': {
            'createRequest': {
                'requestId': f"meet-{int(datetime.datetime.now().timestamp())}",
                'conferenceSolutionKey': {'type': 'hangoutsMeet'}
            }
        },
        'attendees': [{'email': email.strip()} for email in (attendee_emails or []) if email.strip()],
        'reminders': {
            'useDefault': True
        }
    }
    
    event = service.events().insert(
        calendarId='primary',
        body=event_body,
        conferenceDataVersion=1,
        sendUpdates='all'  # Sends Google Calendar email invites to attendees
    ).execute()
    
    meet_link = event.get('hangoutLink') or event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri', '')
    
    return {
        'id': event.get('id'),
        'summary': event.get('summary'),
        'start': event.get('start', {}).get('dateTime'),
        'meet_link': meet_link,
        'html_link': event.get('htmlLink'),
        'attendees': [a.get('email') for a in event.get('attendees', [])]
    }

def get_today_events() -> list[dict]:
    """Retrieves upcoming calendar events for today."""
    try:
        service = get_calendar_service()
        now = datetime.datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + "Z"
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        formatted = []
        for e in events:
            start = e.get('start', {}).get('dateTime') or e.get('start', {}).get('date')
            meet = e.get('hangoutLink') or e.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri', '')
            formatted.append({
                'summary': e.get('summary', 'Untitled Event'),
                'start': start,
                'meet_link': meet
            })
        return formatted
    except Exception as e:
        print(f"Error fetching today events: {e}")
        return []
