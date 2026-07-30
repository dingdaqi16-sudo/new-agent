from __future__ import annotations

import re
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc
BEIJING = ZoneInfo("Asia/Shanghai")
EASTERN = ZoneInfo("America/New_York")

MONTHS = {
    "january": 1,
    "jan": 1,
    "jan.": 1,
    "february": 2,
    "feb": 2,
    "feb.": 2,
    "march": 3,
    "mar": 3,
    "mar.": 3,
    "april": 4,
    "apr": 4,
    "apr.": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "jun.": 6,
    "july": 7,
    "jul": 7,
    "jul.": 7,
    "august": 8,
    "aug": 8,
    "aug.": 8,
    "september": 9,
    "sep": 9,
    "sep.": 9,
    "sept": 9,
    "sept.": 9,
    "october": 10,
    "oct": 10,
    "oct.": 10,
    "november": 11,
    "nov": 11,
    "nov.": 11,
    "december": 12,
    "dec": 12,
    "dec.": 12,
}


def normalize_month_name(month_text: str) -> str:
    month_text = month_text.strip()
    if "/" in month_text:
        month_text = month_text.split("/")[-1].strip()
    return month_text.rstrip(".").lower()


def parse_month(month_text: str) -> int:
    month = MONTHS.get(normalize_month_name(month_text))
    if month is None:
        raise ValueError(f"Unknown month name: {month_text!r}")
    return month


def parse_date_text(date_text: str) -> date:
    raw = date_text.strip().replace(",", "")
    parts = raw.split()
    if len(parts) != 3:
        raise ValueError(f"Unsupported date format: {date_text!r}")
    month = parse_month(parts[0])
    day = int(parts[1])
    year = int(parts[2])
    return date(year, month, day)


def parse_time_text(time_text: str) -> time:
    raw = time_text.strip().replace(".", "")
    match = re.match(r"^(?P<hour>\d{1,2}):(?P<minute>\d{2})\s*(?P<ampm>[AP]M)$", raw, re.I)
    if not match:
        raise ValueError(f"Unsupported time format: {time_text!r}")
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    ampm = match.group("ampm").upper()
    if ampm == "PM" and hour != 12:
        hour += 12
    if ampm == "AM" and hour == 12:
        hour = 0
    return time(hour, minute)


def make_zoned_datetime(date_text: str, time_text: str, tz: ZoneInfo) -> datetime:
    parsed_date = parse_date_text(date_text)
    parsed_time = parse_time_text(time_text)
    return datetime.combine(parsed_date, parsed_time, tzinfo=tz)


def to_beijing(dt: datetime) -> datetime:
    return dt.astimezone(BEIJING)


def to_utc(dt: datetime) -> datetime:
    return dt.astimezone(UTC)


def combine_beijing(local_date: date, local_time: time) -> datetime:
    return datetime.combine(local_date, local_time, tzinfo=BEIJING)
