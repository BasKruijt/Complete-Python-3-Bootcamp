from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import AppSettings

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"


@dataclass
class EmailSnippet:
    id: str
    threadId: str
    sender: str
    subject: str
    received_at: datetime
    labels: List[str]
    snippet: str
    is_unread: bool
    to_me: bool


class GmailClient:
    def __init__(self, settings: AppSettings, enable_send: bool = False) -> None:
        self.settings = settings
        self.scopes = [GMAIL_READONLY_SCOPE]
        if enable_send:
            self.scopes.append(GMAIL_SEND_SCOPE)
        self._service = None

    def _credentials(self) -> Credentials:
        token_path = str(self.settings.GMAIL_TOKEN_PATH)
        client_config = {
            "installed": {
                "client_id": self.settings.GMAIL_CLIENT_ID,
                "client_secret": self.settings.GMAIL_CLIENT_SECRET,
                "redirect_uris": [self.settings.GMAIL_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        # Non-interactive guard: do not attempt local server login if not configured
        if not self.settings.GMAIL_CLIENT_ID or not self.settings.GMAIL_CLIENT_SECRET:
            raise RuntimeError("Gmail OAuth client not configured")
        creds: Optional[Credentials] = None
        try:
            creds = Credentials.from_authorized_user_file(token_path, self.scopes)
        except Exception:
            creds = None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                from google.auth.transport.requests import Request

                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(client_config, self.scopes)
                creds = flow.run_local_server(port=0)
            with open(token_path, "w") as token:
                token.write(creds.to_json())
        return creds

    def _service_client(self):
        if self._service is None:
            creds = self._credentials()
            self._service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        return self._service

    def fetch_threads(self, since: datetime, max_threads: int = 200) -> List[EmailSnippet]:
        service = self._service_client()
        after_epoch = int(since.timestamp())
        q = f"after:{after_epoch}"
        results = service.users().threads().list(userId="me", q=q, maxResults=max_threads).execute()
        threads = results.get("threads", [])
        snippets: List[EmailSnippet] = []
        for th in threads:
            thread = (
                service.users()
                .threads()
                .get(userId="me", id=th["id"], format="metadata", metadataHeaders=["From", "To", "Subject", "Date"])
                .execute()
            )
            messages = thread.get("messages", [])
            if not messages:
                continue
            msg = messages[-1]  # last message in thread
            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
            labels = msg.get("labelIds", [])
            snippet = msg.get("snippet", "")
            date_hdr = headers.get("date")
            received_at = datetime.now(timezone.utc)
            if date_hdr:
                try:
                    from email.utils import parsedate_to_datetime

                    received_at = parsedate_to_datetime(date_hdr)
                except Exception:
                    pass
            sender = headers.get("from", "")
            subject = headers.get("subject", "")
            to_me = self.settings.GMAIL_USER and self.settings.GMAIL_USER.lower() in headers.get("to", "").lower()
            is_unread = "UNREAD" in labels
            snippets.append(
                EmailSnippet(
                    id=msg.get("id"),
                    threadId=msg.get("threadId"),
                    sender=sender,
                    subject=subject,
                    received_at=received_at,
                    labels=list(labels),
                    snippet=snippet,
                    is_unread=is_unread,
                    to_me=bool(to_me),
                )
            )
        return snippets

    def send_email(self, to: str, subject: str, body_md: str) -> None:
        service = self._service_client()
        from email.mime.text import MIMEText
        import base64

        message = MIMEText(body_md, _subtype="markdown")
        message["to"] = to
        message["from"] = self.settings.SMTP_FROM or self.settings.GMAIL_USER or ""
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        try:
            service.users().messages().send(userId="me", body={"raw": raw}).execute()
        except HttpError:
            raise
