#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  SMTP_HOST=... SMTP_PORT=... SMTP_USER=... SMTP_PASSWORD=... MAIL_FROM=... MAIL_TO=... ./scripts/install_launchd.sh [repo_root]

Required env:
  SMTP_HOST
  SMTP_PORT
  SMTP_USER
  SMTP_PASSWORD

Optional env:
  MAIL_FROM   defaults to SMTP_USER
  MAIL_TO     defaults to SMTP_USER
  STATE_FILE  defaults to ~/Library/Application Support/macro-alert-mail/state/sent_reminders.json
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

repo_root="${1:-$(git rev-parse --show-toplevel)}"
label="com.dingdaqi16-sudo.macro-alert-mail"
launch_agents_dir="$HOME/Library/LaunchAgents"
logs_dir="$HOME/Library/Logs/macro-alert-mail"
state_file="${STATE_FILE:-$HOME/Library/Application Support/macro-alert-mail/state/sent_reminders.json}"
plist_path="$launch_agents_dir/$label.plist"

for name in SMTP_HOST SMTP_PORT SMTP_USER SMTP_PASSWORD; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: $name" >&2
    usage
    exit 1
  fi
done

mail_from="${MAIL_FROM:-$SMTP_USER}"
mail_to="${MAIL_TO:-$SMTP_USER}"
export MAIL_FROM="$mail_from"
export MAIL_TO="$mail_to"

mkdir -p "$launch_agents_dir" "$logs_dir" "$(dirname "$state_file")"

python3 - "$plist_path" "$repo_root" "$state_file" "$logs_dir" "$label" <<'PY'
import os
import plistlib
import sys
from pathlib import Path

plist_path = Path(sys.argv[1])
repo_root = sys.argv[2]
state_file = sys.argv[3]
logs_dir = Path(sys.argv[4])
label = sys.argv[5]

payload = {
    "Label": label,
    "ProgramArguments": [
        "/usr/bin/python3",
        "-m",
        "macro_alert.cli",
        "send",
        "--window-minutes",
        "90",
        "--state-file",
        state_file,
    ],
    "WorkingDirectory": repo_root,
    "EnvironmentVariables": {
        "SMTP_HOST": os.environ["SMTP_HOST"],
        "SMTP_PORT": os.environ["SMTP_PORT"],
        "SMTP_USER": os.environ["SMTP_USER"],
        "SMTP_PASSWORD": os.environ["SMTP_PASSWORD"],
        "MAIL_FROM": os.environ["MAIL_FROM"],
        "MAIL_TO": os.environ["MAIL_TO"],
        "REMINDER_WINDOW_MINUTES": "90",
        "STATE_FILE": state_file,
        "PYTHONUNBUFFERED": "1",
    },
    "RunAtLoad": True,
    "StartInterval": 300,
    "StandardOutPath": str(logs_dir / "stdout.log"),
    "StandardErrorPath": str(logs_dir / "stderr.log"),
}

with plist_path.open("wb") as fh:
    plistlib.dump(payload, fh, fmt=plistlib.FMT_XML)
PY

chmod 600 "$plist_path"

launchctl bootout "gui/$(id -u)" "$plist_path" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$plist_path"
launchctl kickstart -k "gui/$(id -u)/$label"

echo "Installed: $plist_path"
echo "Logs: $logs_dir/stdout.log and $logs_dir/stderr.log"
echo "State: $state_file"
