from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import AppSettings

GCAL_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"


@dataclass
class GCalEvent:
    start: datetime
    end: datetime
    summary: str
    organizer: str
    attendees: List[str]
    location: str
    join_link: Optional[str]


class GoogleCalendarClient:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self._service = None

    def _credentials(self) -> Credentials:
        token_path = str(self.settings.GCAL_TOKEN_PATH)
        if not self.settings.GMAIL_CLIENT_ID or not self.settings.GMAIL_CLIENT_SECRET:
            raise RuntimeError("Google OAuth client not configured")
        creds = None
        try:
            creds = Credentials.from_authorized_user_file(token_path, [GCAL_SCOPE])
        except Exception:
            creds = None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                from google.auth.transport.requests import Request

                creds.refresh(Request())
            else:
                # Requires client secrets via env like Gmail
                flow = InstalledAppFlow.from_client_config(
                    {
                        "installed": {
                            "client_id": self.settings.GMAIL_CLIENT_ID,
                            "client_secret": self.settings.GMAIL_CLIENT_SECRET,
                            "redirect_uris": [self.settings.GMAIL_REDIRECT_URI],
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                        }
                    },
                    [GCAL_SCOPE],
                )
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as token:
                token.write(creds.to_json())
        return creds

    def _service_client(self):
        if self._service is None:
            creds = self._credentials()
            self._service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return self._service

    def fetch_events(self, start: datetime, end: datetime) -> List[GCalEvent]:
        service = self._service_client()
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start.isoformat() + "Z",
                timeMax=end.isoformat() + "Z",
                maxResults=100,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events: List[GCalEvent] = []
        for e in events_result.get("items", []):
            start_dt = e.get("start", {}).get("dateTime") or e.get("start", {}).get("date")
            end_dt = e.get("end", {}).get("dateTime") or e.get("end", {}).get("date")
            if not start_dt or not end_dt:
                continue
            attendees = [a.get("email", "") for a in e.get("attendees", []) if isinstance(a, dict)]
            organizer = e.get("organizer", {}).get("email", "")
            location = e.get("location", "") or ""
            join_link = None
            hangout = e.get("hangoutLink") or e.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")
            if hangout:
                join_link = "Google Meet"
            events.append(
                GCalEvent(
                    start=datetime.fromisoformat(start_dt.replace("Z", "+00:00")),
                    end=datetime.fromisoformat(end_dt.replace("Z", "+00:00")),
                    summary=e.get("summary", ""),
                    organizer=organizer,
                    attendees=attendees,
                    location=location,
                    join_link=join_link,
                )
            )
        return events
