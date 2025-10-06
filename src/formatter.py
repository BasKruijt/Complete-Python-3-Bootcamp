from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from .calendar_analyzer import AnalyzedEvent, CalendarReport
from .triage import ScoredThread, TriageResult


def format_event_row(e: AnalyzedEvent) -> str:
    time_range = f"{e.start:%H:%M}–{e.end:%H:%M}"
    location = e.join_link or e.location or ""
    prep = e.prep or ""
    return f"| {time_range} | {e.title} | {location} | {prep} |"


def render_markdown(
    now: datetime,
    triage: TriageResult,
    cal_report: CalendarReport,
    priorities: List[str],
    degraded: bool = False,
    runtime_s: int = 0,
) -> str:
    status = "🟡 Degraded" if degraded else "✅ Healthy"
    lines: List[str] = []
    lines.append(f"# Daily Brief — {now:%Y-%m-%d} (Europe/Amsterdam)")
    lines.append("")
    lines.append(f"Status: {status} (runtime {runtime_s}s)")
    lines.append("")
    lines.append("Top 5 Priorities")
    for p in priorities[:5]:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("Inbox Summary")
    lines.append(f"- Unread: {triage.counts.unread} | Starred: {triage.counts.starred} | Waiting reply: {triage.counts.waiting_reply}")
    lines.append("| Sender | Subject | Age | Action |")
    lines.append("|---|---|---|---|")
    for s in triage.top10:
        age_h = max(0, int((now - s.email.received_at).total_seconds() // 3600))
        sender = s.email.sender.split("<")[-1].strip("<>")
        lines.append(f"| {sender} | {s.email.subject[:80]} | {age_h}h | {s.action_hint} |")
    lines.append("")
    lines.append("Deadlines & Follow-ups")
    for f in triage.followups[:10]:
        lines.append(f"- {f}")
    lines.append("")
    lines.append("Calendar (Today)")
    lines.append("| Start–End | Title | Location/Join | Prep |")
    lines.append("|---|---|---|---|")
    for e in cal_report.today:
        lines.append(format_event_row(e))
    lines.append("")
    if cal_report.lookahead:
        lines.append("Look-ahead")
        for e in cal_report.lookahead:
            lines.append(f"- {e.start:%a %H:%M} {e.title} ({e.location or e.join_link or ''})")
        lines.append("")
    lines.append("Risks/Conflicts")
    for r in cal_report.risks:
        lines.append(f"- {r}")
    return "\n".join(lines)
