from datetime import datetime, timedelta

from src.triage import ScoredThread, TriageResult, TriagedCounts, score_threads
from src.gmail_client import EmailSnippet


def make_email(subject: str, unread: bool = True, to_me: bool = True, labels=None):
    return EmailSnippet(
        id="1",
        threadId="t1",
        sender="vip@example.com",
        subject=subject,
        received_at=datetime.utcnow() - timedelta(hours=1),
        labels=labels or [],
        snippet="please review",
        is_unread=unread,
        to_me=to_me,
    )


def test_score_threads_orders_top10():
    emails = [make_email(f"urgent {i}") for i in range(12)]
    triage = score_threads(emails, vip_list=["vip@example.com"])
    assert len(triage.top10) == 10
    assert triage.counts.unread == 12

