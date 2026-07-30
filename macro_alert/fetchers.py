from __future__ import annotations

import html
import re
import urllib.request
from datetime import datetime, time, timezone
from html.parser import HTMLParser
from typing import List, Optional

from .models import EconomicEvent
from .timeutil import EASTERN, UTC, parse_date_text, to_beijing, to_utc

FOMC_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
BLS_ICS_URL = "https://r.jina.ai/http://www.bls.gov/schedule/news_release/bls.ics"
BEA_URL = "https://www.bea.gov/news/schedule"


class TextExtractor(HTMLParser):
    block_tags = {
        "article",
        "aside",
        "div",
        "footer",
        "header",
        "li",
        "main",
        "p",
        "section",
        "table",
        "tbody",
        "td",
        "th",
        "tr",
        "ul",
        "ol",
        "br",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    }
    ignored_tags = {"script", "style", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: List[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self.ignored_tags:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in {"tr", "li", "p", "div", "section", "article", "header", "footer", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")
        elif tag in {"td", "th"}:
            self.parts.append(" ")
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.ignored_tags and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag in {"tr", "li", "p", "div", "section", "article", "header", "footer", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        self.parts.append(data)

    def text(self) -> str:
        raw = html.unescape("".join(self.parts)).replace("\xa0", " ")
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        lines = []
        for line in raw.split("\n"):
            normalized = re.sub(r"[ \t\f\v]+", " ", line).strip()
            if normalized:
                lines.append(normalized)
        return "\n".join(lines)


def download_text(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; MacroAlert/0.1; +https://example.invalid)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def html_to_text(document: str) -> str:
    parser = TextExtractor()
    parser.feed(document)
    parser.close()
    return parser.text()


def _make_scheduled_event(kind: str, title: str, source_name: str, source_url: str, publish_at_et: datetime, note: str = "") -> EconomicEvent:
    publish_at_beijing = to_beijing(publish_at_et)
    publish_at_utc = to_utc(publish_at_et)
    return EconomicEvent(
        kind=kind,
        title=title,
        source_name=source_name,
        source_url=source_url,
        publish_at_utc=publish_at_utc,
        publish_at_beijing=publish_at_beijing,
        status="scheduled",
        note=note,
    )


def _make_missing_event(kind: str, title: str, source_name: str, source_url: str, note: str) -> EconomicEvent:
    return EconomicEvent(
        kind=kind,
        title=title,
        source_name=source_name,
        source_url=source_url,
        publish_at_utc=None,
        publish_at_beijing=None,
        status="no_release",
        note=note,
    )


def _unfold_ics_lines(text: str) -> List[str]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    unfolded: List[str] = []
    for line in lines:
        if line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    return unfolded


def _parse_ics_datetime(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1]
        tzinfo = timezone.utc
    else:
        tzinfo = EASTERN
    fmt = "%Y%m%dT%H%M%S" if len(raw) == 15 else "%Y%m%dT%H%M"
    dt = datetime.strptime(raw, fmt)
    return dt.replace(tzinfo=tzinfo)


def _iter_ics_events(text: str):
    current = None
    for line in _unfold_ics_lines(text):
        stripped = line.strip()
        if stripped == "BEGIN:VEVENT":
            current = {}
            continue
        if stripped == "END:VEVENT":
            if current is not None:
                yield current
            current = None
            continue
        if current is None or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.split(";", 1)[0].strip().upper()
        current[key] = value.strip()


def _find_bls_event(text: str, summary_phrase: str, now_utc: datetime) -> Optional[datetime]:
    candidates: List[datetime] = []
    for event in _iter_ics_events(text):
        summary = event.get("SUMMARY", "")
        dtstart = event.get("DTSTART", "")
        if summary_phrase.lower() not in summary.lower() or not dtstart:
            continue
        event_dt = _parse_ics_datetime(dtstart).astimezone(UTC)
        if event_dt >= now_utc - datetime.resolution:
            candidates.append(event_dt)
    if not candidates:
        return None
    return min(candidates)


def fetch_cpi_event(now_utc: Optional[datetime] = None) -> EconomicEvent:
    now_utc = now_utc or datetime.now(timezone.utc)
    text = download_text(BLS_ICS_URL)
    publish_at_utc = _find_bls_event(text, "Consumer Price Index", now_utc)
    if publish_at_utc is None:
        return _make_missing_event("cpi", "美国 CPI", "BLS CPI", BLS_ICS_URL, "Official BLS calendar does not list a next CPI release.")
    publish_at_et = publish_at_utc.astimezone(EASTERN)
    return _make_scheduled_event("cpi", "美国 CPI", "BLS CPI", BLS_ICS_URL, publish_at_et)


def fetch_employment_event(now_utc: Optional[datetime] = None) -> EconomicEvent:
    now_utc = now_utc or datetime.now(timezone.utc)
    text = download_text(BLS_ICS_URL)
    publish_at_utc = _find_bls_event(text, "Employment Situation", now_utc)
    if publish_at_utc is None:
        return _make_missing_event("nonfarm", "美国非农就业", "BLS Employment Situation", BLS_ICS_URL, "Official BLS calendar does not list a next employment release.")
    publish_at_et = publish_at_utc.astimezone(EASTERN)
    return _make_scheduled_event("nonfarm", "美国非农就业", "BLS Employment Situation", BLS_ICS_URL, publish_at_et)


def fetch_pce_event(now_utc: Optional[datetime] = None) -> EconomicEvent:
    text = html_to_text(download_text(BEA_URL))
    release_year_match = re.search(r"Year\s+(\d{4})", text)
    fallback_year = int(release_year_match.group(1)) if release_year_match else None
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if "Personal Income and Outlays," not in line:
            continue
        release_date_line = None
        release_time_line = None
        for back in range(1, 6):
            if index - back < 0:
                break
            candidate = lines[index - back].strip()
            if release_time_line is None and re.match(r"^\d{1,2}:\d{2}\s+[AP]M$", candidate):
                release_time_line = candidate
                continue
            if release_date_line is None and re.match(r"^[A-Za-z]+\s+\d{1,2}$", candidate):
                release_date_line = candidate
            if release_date_line and release_time_line:
                break
        if not release_date_line or not release_time_line:
            continue
        release_year = fallback_year or datetime.now(timezone.utc).year
        publish_date = parse_date_text(f"{release_date_line}, {release_year}")
        publish_at_et = datetime.combine(publish_date, time(8, 30), tzinfo=EASTERN)
        return _make_scheduled_event("pce", "美国 PCE", "BEA Release Schedule", BEA_URL, publish_at_et)
    return _make_missing_event("pce", "美国 PCE", "BEA Release Schedule", BEA_URL, "Official BEA schedule does not list Personal Income and Outlays.")


def fetch_fomc_event(now_utc: Optional[datetime] = None) -> EconomicEvent:
    text = html_to_text(download_text(FOMC_URL))
    year_sections = list(re.finditer(r"(?m)^\s*(20\d{2})\s+FOMC Meetings\s*$", text))
    if not year_sections:
        return _make_missing_event("fomc", "联储议息会议", "Federal Reserve FOMC calendars", FOMC_URL, "Official FOMC calendar does not list any future meeting.")

    candidates = []
    for index, heading in enumerate(year_sections):
        year = int(heading.group(1))
        start = heading.end()
        end = year_sections[index + 1].start() if index + 1 < len(year_sections) else len(text)
        block = text[start:end]
        matches = list(
            re.finditer(
                r"(?m)^(?P<month>[A-Za-z/]+)\s*$\n\s*(?P<start_day>\d{1,2})-(?P<end_day>\d{1,2})\*?\s*$",
                block,
            )
        )
        for match in matches:
            month_text = match.group("month")
            month_parts = [part.strip() for part in month_text.split("/") if part.strip()]
            end_day = int(match.group("end_day"))
            # FOMC statement release happens on the second day at 2:00 p.m. ET.
            try:
                publish_date = parse_date_text(f"{month_parts[-1]} {end_day}, {year}")
            except ValueError:
                # If the meeting crosses into the next month, fall back to the second month.
                if len(month_parts) == 2:
                    next_month_text = month_parts[1]
                    next_month = parse_date_text(f"{next_month_text} 1, {year}").month
                    publish_date = datetime(year, next_month, end_day).date()
                else:
                    raise
            publish_at_et = datetime.combine(publish_date, time(14, 0), tzinfo=EASTERN)
            if now_utc is None or to_utc(publish_at_et) >= now_utc - datetime.resolution:
                note = ""
                if "*" in match.group(0):
                    note = "Summary of Economic Projections meeting."
                candidates.append((publish_at_et, note))

    if not candidates:
        return _make_missing_event("fomc", "联储议息会议", "Federal Reserve FOMC calendars", FOMC_URL, "Official FOMC calendar does not list any future meeting.")

    candidates.sort(key=lambda item: item[0])
    publish_at_et, note = candidates[0]
    return _make_scheduled_event("fomc", "联储议息会议", "Federal Reserve FOMC calendars", FOMC_URL, publish_at_et, note=note)


def fetch_all_events(now_utc: Optional[datetime] = None) -> List[EconomicEvent]:
    return [
        fetch_fomc_event(now_utc=now_utc),
        fetch_cpi_event(now_utc=now_utc),
        fetch_pce_event(now_utc=now_utc),
        fetch_employment_event(now_utc=now_utc),
    ]
