from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

from .service import preview, send_due_reminders, sync_events


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="macro-alert")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preview_parser = subparsers.add_parser("preview", help="Print the current event plan.")
    preview_parser.add_argument("--window-minutes", type=int, default=int(os.getenv("REMINDER_WINDOW_MINUTES", "20")))

    send_parser = subparsers.add_parser("send", help="Send due reminders.")
    send_parser.add_argument("--window-minutes", type=int, default=int(os.getenv("REMINDER_WINDOW_MINUTES", "20")))
    send_parser.add_argument("--state-file", default=os.getenv("STATE_FILE", "state/sent_reminders.json"))
    send_parser.add_argument("--dry-run", action="store_true")
    send_parser.add_argument("--smtp-host", default=os.getenv("SMTP_HOST", "smtp.qq.com"))
    send_parser.add_argument("--smtp-port", type=int, default=int(os.getenv("SMTP_PORT", "465")))
    send_parser.add_argument("--smtp-user", default=os.getenv("SMTP_USER", ""))
    send_parser.add_argument("--smtp-password", default=os.getenv("SMTP_PASSWORD", ""))
    send_parser.add_argument("--mail-from", default=os.getenv("MAIL_FROM", os.getenv("SMTP_USER", "")))
    send_parser.add_argument("--mail-to", default=os.getenv("MAIL_TO", os.getenv("SMTP_USER", "")))

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    now_utc = datetime.now(timezone.utc)
    events = sync_events(now_utc)

    if args.command == "preview":
        print(preview(events, now_utc, args.window_minutes))
        return

    if args.command == "send":
        if not args.smtp_user and not args.dry_run:
            raise SystemExit("SMTP_USER is required unless you use --dry-run.")
        if not args.smtp_password and not args.dry_run:
            raise SystemExit("SMTP_PASSWORD is required unless you use --dry-run.")
        sent_count, skipped_count = send_due_reminders(
            events=events,
            now_utc=now_utc,
            window_minutes=args.window_minutes,
            state_path=Path(args.state_file),
            smtp_host=args.smtp_host,
            smtp_port=args.smtp_port,
            smtp_user=args.smtp_user,
            smtp_password=args.smtp_password,
            mail_from=args.mail_from or args.smtp_user,
            mail_to=args.mail_to or args.smtp_user,
            dry_run=args.dry_run,
        )
        print(f"sent={sent_count} skipped={skipped_count}")
        return

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
