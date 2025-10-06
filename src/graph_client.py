from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

import msal
import requests

from .config import AppSettings

GRAPH_SCOPE = ["Calendars.Read", "offline_access"]
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"


@dataclass
class CalendarEvent:
    start: datetime
    end: datetime
    subject: str
    organizer: str
    attendees: List[str]
    location: str
    join_link: Optional[str]


class GraphClient:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self._app = msal.ConfidentialClientApplication(
            authority=f"https://login.microsoftonline.com/{settings.MS_TENANT_ID}",
            client_id=settings.MS_CLIENT_ID,
            client_credential=settings.MS_CLIENT_SECRET,
            token_cache=msal.SerializableTokenCache()
        )

    def _acquire_token(self) -> str:
        result = self._app.acquire_token_silent(GRAPH_SCOPE, account=None)
        if not result:
            result = self._app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in result:
            raise RuntimeError(f"MS Graph auth failed: {result.get('error_description')}")
        return result["access_token"]

    def fetch_events(self, start: datetime, end: datetime) -> List[CalendarEvent]:
        token = self._acquire_token()
        url = f"{GRAPH_ENDPOINT}/me/calendarView?startDateTime={start.isoformat()}&endDateTime={end.isoformat()}"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"$orderby": "start/dateTime", "$top": 100}
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        events: List[CalendarEvent] = []
        for item in data.get("value", []):
            attendees = [a.get("emailAddress", {}).get("address", "") for a in item.get("attendees", [])]
            organizer = item.get("organizer", {}).get("emailAddress", {}).get("address", "")
            location = item.get("location", {}).get("displayName", "")
            join_link = None
            body = item.get("bodyPreview", "")
            if "https://teams.microsoft.com" in body:
                join_link = "Teams"
            start_dt = item.get("start", {}).get("dateTime")
            end_dt = item.get("end", {}).get("dateTime")
            if not start_dt or not end_dt:
                continue
            events.append(
                CalendarEvent(
                    start=datetime.fromisoformat(start_dt),
                    end=datetime.fromisoformat(end_dt),
                    subject=item.get("subject", ""),
                    organizer=organizer,
                    attendees=attendees,
                    location=location,
                    join_link=join_link,
                )
            )
        return events
