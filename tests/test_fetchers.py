from __future__ import annotations

import unittest
from datetime import datetime, timezone

from macro_alert.fetchers import fetch_cpi_event, fetch_employment_event, fetch_pce_event, fetch_fomc_event, html_to_text
from macro_alert.timeutil import BEIJING


class FetcherParsingTests(unittest.TestCase):
    def test_cpi_ics_parse(self) -> None:
        text = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART;TZID=US-Eastern:20260812T083000
SUMMARY:Consumer Price Index
END:VEVENT
END:VCALENDAR"""
        import macro_alert.fetchers as fetchers

        original_download = fetchers.download_text
        fetchers.download_text = lambda url: text
        try:
            event = fetch_cpi_event()
        finally:
            fetchers.download_text = original_download
        self.assertEqual(event.kind, "cpi")
        self.assertEqual(event.publish_at_beijing.strftime("%Y-%m-%d %H:%M"), "2026-08-12 20:30")

    def test_employment_ics_parse(self) -> None:
        text = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART;TZID=US-Eastern:20260807T083000
SUMMARY:Employment Situation
END:VEVENT
END:VCALENDAR"""
        import macro_alert.fetchers as fetchers

        original_download = fetchers.download_text
        fetchers.download_text = lambda url: text
        try:
            event = fetch_employment_event()
        finally:
            fetchers.download_text = original_download
        self.assertEqual(event.kind, "nonfarm")
        self.assertEqual(event.publish_at_beijing.strftime("%Y-%m-%d %H:%M"), "2026-08-07 20:30")

    def test_pce_line_parse(self) -> None:
        text = """Year 2026
Release
July 30
8:30 AM
News
GDP (Advance Estimate), 2nd Quarter 2026
July 30
8:30 AM
News
Personal Income and Outlays, June 2026
August 4
8:30 AM
News
Other"""
        import macro_alert.fetchers as fetchers

        original_download = fetchers.download_text
        fetchers.download_text = lambda url: text
        try:
            event = fetch_pce_event()
        finally:
            fetchers.download_text = original_download
        self.assertEqual(event.kind, "pce")
        self.assertEqual(event.publish_at_beijing.strftime("%Y-%m-%d %H:%M"), "2026-07-30 20:30")

    def test_fomc_parse(self) -> None:
        text = """
2026 FOMC Meetings

January
27-28
Statement:

March
17-18*
Statement:

July
28-29
Statement:

September
15-16*
Statement:
"""
        import macro_alert.fetchers as fetchers

        original_download = fetchers.download_text
        fetchers.download_text = lambda url: text
        try:
            now = datetime(2026, 7, 30, tzinfo=timezone.utc)
            event = fetch_fomc_event(now_utc=now)
        finally:
            fetchers.download_text = original_download
        self.assertEqual(event.kind, "fomc")
        self.assertEqual(event.publish_at_beijing.strftime("%Y-%m-%d %H:%M"), "2026-09-17 02:00")


if __name__ == "__main__":
    unittest.main()
