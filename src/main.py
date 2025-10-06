from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timedelta

from dateutil import tz
from rich.console import Console

from .config import load_config
from .deliver import save_report, send_smtp, send_teams
from .formatter import render_markdown
from .triage import TriageResult, load_vip_list, score_threads

console = Console()


def tz_now(tz_name: str) -> datetime:
    return datetime.now(tz.gettz(tz_name))


def fetch_email_and_calendar(settings, now: datetime):
    degraded = False
    triage: TriageResult | None = None
    cal_report = None
    priorities: list[str] = []

    # Emails
    try:
        from .gmail_client import GmailClient

        gmail = GmailClient(settings, enable_send=settings.DELIVERY_EMAIL_ENABLED)
        since = now - timedelta(hours=24)
        emails = gmail.fetch_threads(since=since, max_threads=settings.EMAIL_MAX_THREADS)
        vip_list = load_vip_list(str(settings.VIP_SENDERS_PATH))
        triage = score_threads(emails, vip_list)
        # derive priorities from top threads
        priorities = [f"{s.email.subject[:80]}" for s in triage.top10[:5]]
    except Exception as e:
        degraded = True
        console.log(f"Email fetch failed: {e}")

    # Calendar
    try:
        from .calendar_analyzer import AnalyzedEvent, analyze_calendar
        if settings.PROVIDER_CALENDAR == "graph":
            from .graph_client import GraphClient

            client = GraphClient(settings)
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=4)
            raw = client.fetch_events(start, end)
            events = [
                AnalyzedEvent(
                    start=e.start,
                    end=e.end,
                    title=e.subject,
                    location=e.location,
                    join_link=e.join_link,
                    organizer=e.organizer,
                    attendees=e.attendees,
                    prep=None,
                )
                for e in raw
            ]
        else:
            from .gcal_client import GoogleCalendarClient

            client = GoogleCalendarClient(settings)
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=4)
            raw = client.fetch_events(start, end)
            events = [
                AnalyzedEvent(
                    start=e.start,
                    end=e.end,
                    title=e.summary,
                    location=e.location,
                    join_link=e.join_link,
                    organizer=e.organizer,
                    attendees=e.attendees,
                    prep=None,
                )
                for e in raw
            ]
        cal_report = analyze_calendar(events, now)
    except Exception as e:
        degraded = True
        console.log(f"Calendar fetch failed: {e}")

    return triage, cal_report, priorities, degraded


def main_once() -> int:
    settings = load_config()
    start_ts = time.time()
    now = tz_now(settings.TZ)

    triage, cal_report, priorities, degraded = fetch_email_and_calendar(settings, now)

    if triage is None or cal_report is None:
        degraded = True
        # create empty structures
        from .triage import TriageResult, TriagedCounts
        from .calendar_analyzer import CalendarReport

        triage = TriageResult(top10=[], counts=TriagedCounts(unread=0, starred=0, waiting_reply=0), followups=[])
        cal_report = CalendarReport(today=[], lookahead=[], risks=["Data unavailable"]) 

    md = render_markdown(now, triage, cal_report, priorities, degraded=degraded, runtime_s=int(time.time() - start_ts))
    saved_path = save_report(md, settings.OUTPUT_DIR, now)

    subject = f"Daily Brief – {now:%Y-%m-%d}"
    try:
        if settings.DELIVERY_EMAIL_ENABLED and settings.RECIPIENTS:
            if settings.DELIVERY_SMTP_ENABLED:
                send_smtp(settings, subject, settings.RECIPIENTS, md, attachment_path=saved_path)
            else:
                from .gmail_client import GmailClient

                g = GmailClient(settings, enable_send=True)
                for r in settings.RECIPIENTS:
                    g.send_email(r, subject, md)
        if settings.DELIVERY_TEAMS_ENABLED and settings.TEAMS_WEBHOOK_URL:
            send_teams(settings.TEAMS_WEBHOOK_URL, subject, md[:15000])
    except Exception as e:
        console.log(f"Delivery failed: {e}")

    console.log(f"Report saved to {saved_path}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()
    raise SystemExit(main_once())
