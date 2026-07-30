from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from macro_alert.cli import build_parser, env_int, env_str


class CliEnvTests(unittest.TestCase):
    def test_empty_env_string_uses_default(self) -> None:
        with patch.dict(os.environ, {"SMTP_USER": "", "SMTP_PORT": "", "REMINDER_WINDOW_MINUTES": ""}, clear=True):
            self.assertEqual(env_str("SMTP_USER", "fallback@qq.com"), "fallback@qq.com")
            self.assertEqual(env_int("SMTP_PORT", 465), 465)
            self.assertEqual(env_int("REMINDER_WINDOW_MINUTES", 20), 20)

    def test_build_parser_with_empty_env(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SMTP_USER": "",
                "SMTP_PASSWORD": "",
                "SMTP_HOST": "",
                "SMTP_PORT": "",
                "MAIL_FROM": "",
                "MAIL_TO": "",
                "STATE_FILE": "",
                "REMINDER_WINDOW_MINUTES": "",
            },
            clear=True,
        ):
            parser = build_parser()
            args = parser.parse_args(["send", "--dry-run"])
            self.assertEqual(args.smtp_host, "smtp.qq.com")
            self.assertEqual(args.smtp_port, 465)
            self.assertEqual(args.state_file, "state/sent_reminders.json")
            self.assertEqual(args.window_minutes, 20)


if __name__ == "__main__":
    unittest.main()
