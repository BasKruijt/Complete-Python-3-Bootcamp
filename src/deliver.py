from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable, List

import requests

from .config import AppSettings


def save_report(markdown: str, output_dir: Path, now: datetime) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{now:%Y-%m-%d}.md"
    path.write_text(markdown, encoding="utf-8")
    return path


def send_smtp(settings: AppSettings, subject: str, to: List[str], md_body: str, attachment_path: Path | None = None) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASS:
        raise RuntimeError("SMTP not configured")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = ", ".join(to)
    msg.set_content(md_body)

    if attachment_path and attachment_path.exists():
        msg.add_attachment(attachment_path.read_text(encoding="utf-8"), subtype="markdown", filename=attachment_path.name)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.send_message(msg)


def send_teams(webhook_url: str, title: str, text: str) -> None:
    payload = {"title": title, "text": text}
    resp = requests.post(webhook_url, json=payload, timeout=15)
    resp.raise_for_status()
