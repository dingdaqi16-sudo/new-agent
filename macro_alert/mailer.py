from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Iterable, List

from .models import Reminder


def split_recipients(value: str) -> List[str]:
    parts = [item.strip() for item in value.replace(";", ",").split(",")]
    return [item for item in parts if item]


def send_email(reminder: Reminder, *, host: str, port: int, username: str, password: str, sender: str, recipients: Iterable[str]) -> None:
    message = EmailMessage()
    message["Subject"] = reminder.subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(reminder.body)

    with smtplib.SMTP_SSL(host, port) as client:
        client.login(username, password)
        client.send_message(message)


def build_subject(label: str, event_title: str) -> str:
    return f"[宏观提醒][{label}] {event_title}"
