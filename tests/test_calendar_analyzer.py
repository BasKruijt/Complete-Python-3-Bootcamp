from datetime import datetime, timedelta

from src.calendar_analyzer import AnalyzedEvent, analyze_calendar


def test_analyze_calendar_detects_overlap_and_gaps():
    now = datetime(2025, 1, 1, 9, 0)
    a = AnalyzedEvent(start=now, end=now + timedelta(minutes=30), title="A", location="", join_link=None, organizer="o", attendees=[], prep=None)
    b = AnalyzedEvent(start=now + timedelta(minutes=25), end=now + timedelta(minutes=60), title="B", location="", join_link="Teams", organizer="o", attendees=[], prep=None)
    c = AnalyzedEvent(start=now + timedelta(minutes=75), end=now + timedelta(minutes=105), title="C", location="", join_link=None, organizer="o", attendees=[], prep=None)

    report = analyze_calendar([a, b, c], now)
    assert any("overlaps" in r for r in report.risks)
    assert any("<30m gap" in r for r in report.risks)
