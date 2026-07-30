from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class EconomicEvent:
    kind: str
    title: str
    source_name: str
    source_url: str
    publish_at_utc: Optional[datetime]
    publish_at_beijing: Optional[datetime]
    status: str = "scheduled"
    note: str = ""

    @property
    def event_key(self) -> str:
        if self.publish_at_utc is None:
            return f"{self.kind}:{self.status}"
        return f"{self.kind}:{self.publish_at_utc.isoformat()}"


@dataclass(frozen=True)
class Reminder:
    kind: str
    event_key: str
    subject: str
    body: str
    remind_at_utc: datetime

    @property
    def reminder_key(self) -> str:
        return f"{self.event_key}:{self.kind}"
