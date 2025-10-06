from datetime import datetime, timedelta

from src.calendar_analyzer import AnalyzedEvent, CalendarReport
from src.formatter import render_markdown
from src.triage import ScoredThread, TriageResult, TriagedCounts


def test_render_markdown_has_sections():
    now = datetime(2025, 1, 1, 8, 0)
    triage = TriageResult(top10=[], counts=TriagedCounts(unread=0, starred=0, waiting_reply=0), followups=[])
    cal = CalendarReport(today=[], lookahead=[], risks=["risk"]) 
    md = render_markdown(now, triage, cal, priorities=["p1", "p2"], degraded=False, runtime_s=1)
    assert "Daily Brief" in md
    assert "Top 5 Priorities" in md
    assert "Inbox Summary" in md
    assert "Calendar (Today)" in md
    assert "Risks/Conflicts" in md
