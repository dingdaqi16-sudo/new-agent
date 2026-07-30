from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from contextlib import redirect_stdout
import io

from macro_alert.models import EconomicEvent
from macro_alert.service import build_reminders, due_reminders, send_due_reminders
from macro_alert.timeutil import BEIJING, EASTERN


class ServiceTests(unittest.TestCase):
    def test_build_two_reminders(self) -> None:
        publish_at_et = datetime(2026, 8, 12, 8, 30, tzinfo=EASTERN)
        event = EconomicEvent(
            kind="cpi",
            title="美国 CPI",
            source_name="BLS CPI",
            source_url="https://www.bls.gov/cpi/",
            publish_at_utc=publish_at_et.astimezone(timezone.utc),
            publish_at_beijing=publish_at_et.astimezone(BEIJING),
        )
        reminders = build_reminders(event)
        self.assertEqual(len(reminders), 2)
        self.assertEqual(reminders[0].remind_at_utc.astimezone(BEIJING).strftime("%Y-%m-%d %H:%M"), "2026-08-11 12:00")
        self.assertEqual(reminders[1].remind_at_utc.astimezone(BEIJING).strftime("%Y-%m-%d %H:%M"), "2026-08-12 18:30")

    def test_due_reminders_window(self) -> None:
        publish_at_et = datetime(2026, 8, 12, 8, 30, tzinfo=EASTERN)
        event = EconomicEvent(
            kind="cpi",
            title="美国 CPI",
            source_name="BLS CPI",
            source_url="https://www.bls.gov/cpi/",
            publish_at_utc=publish_at_et.astimezone(timezone.utc),
            publish_at_beijing=publish_at_et.astimezone(BEIJING),
        )
        now = datetime(2026, 8, 11, 4, 5, tzinfo=timezone.utc)
        reminders = due_reminders([event], now, 20)
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0].kind, "day_before_noon")

    def test_send_due_reminders_dry_run_state(self) -> None:
        publish_at_et = datetime(2026, 8, 12, 8, 30, tzinfo=EASTERN)
        event = EconomicEvent(
            kind="cpi",
            title="美国 CPI",
            source_name="BLS CPI",
            source_url="https://www.bls.gov/cpi/",
            publish_at_utc=publish_at_et.astimezone(timezone.utc),
            publish_at_beijing=publish_at_et.astimezone(BEIJING),
        )
        now = datetime(2026, 8, 11, 4, 5, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "state.json"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                sent, skipped = send_due_reminders(
                    events=[event],
                    now_utc=now,
                    window_minutes=20,
                    state_path=state_path,
                    smtp_host="smtp.qq.com",
                    smtp_port=465,
                    smtp_user="user@qq.com",
                    smtp_password="password",
                    mail_from="user@qq.com",
                    mail_to="user@qq.com",
                    dry_run=True,
                )
            self.assertEqual(sent, 1)
            self.assertEqual(skipped, 0)
            self.assertTrue(state_path.exists())


if __name__ == "__main__":
    unittest.main()
