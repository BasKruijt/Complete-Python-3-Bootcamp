from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class AnalyzedEvent:
    start: datetime
    end: datetime
    title: str
    location: str
    join_link: Optional[str]
    organizer: str
    attendees: List[str]
    prep: Optional[str]


@dataclass
class CalendarReport:
    today: List[AnalyzedEvent]
    lookahead: List[AnalyzedEvent]
    risks: List[str]


def analyze_calendar(events: List[AnalyzedEvent], now: datetime) -> CalendarReport:
    today_date = now.date()
    today_list: List[AnalyzedEvent] = []
    lookahead_list: List[AnalyzedEvent] = []
    risks: List[str] = []

    events_sorted = sorted(events, key=lambda e: (e.start, e.end))

    # Partition today vs lookahead
    for e in events_sorted:
        if e.start.date() == today_date:
            today_list.append(e)
        elif 0 <= (e.start.date() - today_date).days <= 3:
            lookahead_list.append(e)

    # Risks: overlaps and short gaps
    def detect_conflicts(evts: List[AnalyzedEvent]) -> None:
        for i in range(len(evts) - 1):
            a = evts[i]
            b = evts[i + 1]
            if a.end > b.start:
                risks.append(
                    f"{a.title} overlaps {b.title} ({a.start:%H:%M}-{a.end:%H:%M} vs {b.start:%H:%M}-{b.end:%H:%M})"
                )
            gap = (b.start - a.end).total_seconds() / 60.0
            if 0 <= gap < 30:
                risks.append(f"<30m gap between {a.title} and {b.title} at {a.end:%H:%M}")
            if not a.join_link:
                risks.append(f"No join link: {a.title} at {a.start:%H:%M}")
        if evts:
            last = evts[-1]
            if not last.join_link:
                risks.append(f"No join link: {last.title} at {last.start:%H:%M}")

    detect_conflicts(today_list)
    return CalendarReport(today=today_list, lookahead=lookahead_list, risks=risks)
