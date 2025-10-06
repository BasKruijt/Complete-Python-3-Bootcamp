from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Tuple

from .gmail_client import EmailSnippet

DEFAULT_KEYWORDS = [
    "urgent",
    "incident",
    "p1",
    "deadline",
    "invoice",
    "ns",
    "kpn",
    "meeting",
    "reschedule",
]


@dataclass
class TriagedCounts:
    unread: int
    starred: int
    waiting_reply: int


@dataclass
class ScoredThread:
    email: EmailSnippet
    score: float
    action_hint: str


@dataclass
class TriageResult:
    top10: List[ScoredThread]
    counts: TriagedCounts
    followups: List[str]


def load_vip_list(path: str) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def score_threads(emails: Iterable[EmailSnippet], vip_list: List[str]) -> TriageResult:
    scored: List[ScoredThread] = []
    now = datetime.utcnow()

    unread = 0
    starred = 0  # Placeholder: would need label mapping
    waiting_reply = 0

    for e in emails:
        score = 0.0
        age_hours = max(0.0, (now - e.received_at.replace(tzinfo=None)).total_seconds() / 3600.0)
        sender_lower = e.sender.lower()
        subject_lower = e.subject.lower()
        snippet_lower = e.snippet.lower()

        if e.is_unread:
            score += 2.0
            unread += 1
        if e.to_me:
            score += 1.5
        if any(vip in sender_lower for vip in vip_list):
            score += 2.5
        if any(kw in subject_lower or kw in snippet_lower for kw in DEFAULT_KEYWORDS):
            score += 1.0
        if "invoice" in subject_lower:
            score += 0.5
        if age_hours > 48:
            waiting_reply += 1
            score += 1.0
        # Penalize known noise labels if available
        if any(lbl in {"CATEGORY_UPDATES", "CATEGORY_FORUMS", "CATEGORY_PROMOTIONS"} for lbl in e.labels):
            score -= 3.0

        action_hint = "Review"
        if "?" in e.subject or "?" in e.snippet:
            action_hint = "Reply"
        elif "invoice" in subject_lower:
            action_hint = "Pay/Forward to finance"
        elif "meeting" in subject_lower or "reschedule" in subject_lower:
            action_hint = "Schedule/Reschedule"
        elif e.is_unread:
            action_hint = "Read"

        scored.append(ScoredThread(email=e, score=score, action_hint=action_hint))

    scored.sort(key=lambda s: s.score, reverse=True)
    top10 = scored[:10]

    counts = TriagedCounts(unread=unread, starred=starred, waiting_reply=waiting_reply)
    followups = [s.email.subject for s in scored if (now - s.email.received_at.replace(tzinfo=None)).days >= 1][:10]
    return TriageResult(top10=top10, counts=counts, followups=followups)
