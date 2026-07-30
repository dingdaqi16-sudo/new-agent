from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .fetchers import fetch_all_events
from .mailer import build_subject, send_email, split_recipients
from .models import EconomicEvent, Reminder
from .state import has_sent, load_state, mark_sent, save_state
from .timeutil import BEIJING, UTC, combine_beijing, to_beijing


def build_reminders(event: EconomicEvent) -> List[Reminder]:
    if event.status != "scheduled" or event.publish_at_utc is None or event.publish_at_beijing is None:
        return []

    publish_at_beijing = event.publish_at_beijing
    publish_at_utc = event.publish_at_utc

    first_remind_beijing = combine_beijing(
        (publish_at_beijing.date() - timedelta(days=1)),
        publish_at_beijing.replace(hour=12, minute=0, second=0, microsecond=0).time(),
    )
    second_remind_utc = publish_at_utc - timedelta(hours=2)
    second_remind_beijing = to_beijing(second_remind_utc)

    first_subject = build_subject("前一天12点", event.title)
    second_subject = build_subject("提前2小时", event.title)

    first_body = render_body(event, "前一天12:00", first_remind_beijing, first_remind_beijing.astimezone(UTC))
    second_body = render_body(event, "提前2小时", second_remind_beijing, second_remind_utc)

    return [
        Reminder(
            kind="day_before_noon",
            event_key=event.event_key,
            subject=first_subject,
            body=first_body,
            remind_at_utc=first_remind_beijing.astimezone(UTC),
        ),
        Reminder(
            kind="two_hours_before",
            event_key=event.event_key,
            subject=second_subject,
            body=second_body,
            remind_at_utc=second_remind_utc,
        ),
    ]


def render_body(event: EconomicEvent, remind_label: str, remind_at_beijing: datetime, remind_at_utc: datetime) -> str:
    publish_at_beijing = event.publish_at_beijing.astimezone(BEIJING) if event.publish_at_beijing else None
    publish_at_utc = event.publish_at_utc.astimezone(UTC) if event.publish_at_utc else None
    lines = [
        f"事件：{event.title}",
        f"状态：{event.status}",
        f"提醒类型：{remind_label}",
        f"提醒时间（北京时间）：{remind_at_beijing.strftime('%Y-%m-%d %H:%M')}",
        f"提醒时间（UTC）：{remind_at_utc.strftime('%Y-%m-%d %H:%M')}",
    ]
    if publish_at_beijing and publish_at_utc:
        lines.extend(
            [
                f"发布时间（北京时间）：{publish_at_beijing.strftime('%Y-%m-%d %H:%M')}",
                f"发布时间（UTC）：{publish_at_utc.strftime('%Y-%m-%d %H:%M')}",
            ]
        )
    lines.append(f"来源：{event.source_name} - {event.source_url}")
    if event.note:
        lines.append(f"备注：{event.note}")
    return "\n".join(lines)


def due_reminders(events: Iterable[EconomicEvent], now_utc: datetime, window_minutes: int) -> List[Reminder]:
    due: List[Reminder] = []
    for event in events:
        for reminder in build_reminders(event):
            if reminder.remind_at_utc <= now_utc < reminder.remind_at_utc + timedelta(minutes=window_minutes):
                due.append(reminder)
    due.sort(key=lambda item: item.remind_at_utc)
    return due


def preview(events: Iterable[EconomicEvent], now_utc: datetime, window_minutes: int) -> str:
    lines = []
    for event in events:
        if event.status != "scheduled" or event.publish_at_beijing is None:
            lines.append(f"- {event.kind}: {event.status} ({event.note})")
            continue
        lines.append(
            f"- {event.kind}: {event.publish_at_beijing.strftime('%Y-%m-%d %H:%M')} 北京时间 / {event.source_name}"
        )
        for reminder in build_reminders(event):
            window_end = reminder.remind_at_utc + timedelta(minutes=window_minutes)
            lines.append(
                f"  - {reminder.kind}: {reminder.remind_at_utc.astimezone(BEIJING).strftime('%Y-%m-%d %H:%M')} 北京时间"
                f" | window <= {window_end.astimezone(BEIJING).strftime('%Y-%m-%d %H:%M')}"
            )
    current_due = due_reminders(events, now_utc, window_minutes)
    lines.append("")
    lines.append("Due reminders:")
    if not current_due:
        lines.append("- none")
    else:
        for reminder in current_due:
            lines.append(f"- {reminder.subject} at {reminder.remind_at_utc.astimezone(BEIJING).strftime('%Y-%m-%d %H:%M')}")
    return "\n".join(lines)


def send_due_reminders(
    *,
    events: Iterable[EconomicEvent],
    now_utc: datetime,
    window_minutes: int,
    state_path: Path,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    mail_from: str,
    mail_to: str,
    dry_run: bool = False,
) -> Tuple[int, int]:
    state = load_state(state_path)
    recipients = split_recipients(mail_to)
    if not recipients:
        raise ValueError("MAIL_TO is empty.")

    sent_count = 0
    skipped_count = 0
    changed = False
    for reminder in due_reminders(events, now_utc, window_minutes):
        if has_sent(state, reminder.reminder_key):
            skipped_count += 1
            continue
        if dry_run:
            print(f"[DRY RUN] {reminder.subject}")
            print(reminder.body)
            print()
        else:
            send_email(
                reminder,
                host=smtp_host,
                port=smtp_port,
                username=smtp_user,
                password=smtp_password,
                sender=mail_from,
                recipients=recipients,
            )
        mark_sent(state, reminder.reminder_key, now_utc.isoformat())
        changed = True
        sent_count += 1

    if changed:
        save_state(state_path, state)

    return sent_count, skipped_count


def sync_events(now_utc: datetime) -> List[EconomicEvent]:
    return fetch_all_events(now_utc=now_utc)
