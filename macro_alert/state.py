from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, MutableMapping


def load_state(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {"sent": {}}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {"sent": {}}
    sent = raw.get("sent", {})
    if not isinstance(sent, dict):
        sent = {}
    return {"sent": {str(key): str(value) for key, value in sent.items()}}


def save_state(path: Path, state: MutableMapping[str, Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp_path.write_text(payload, encoding="utf-8")
    tmp_path.replace(path)


def has_sent(state: MutableMapping[str, Dict[str, str]], key: str) -> bool:
    return key in state.get("sent", {})


def mark_sent(state: MutableMapping[str, Dict[str, str]], key: str, sent_at: str) -> None:
    sent = state.setdefault("sent", {})
    sent[key] = sent_at
