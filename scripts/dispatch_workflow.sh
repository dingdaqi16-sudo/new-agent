#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  GITHUB_TOKEN=... ./scripts/dispatch_workflow.sh [ref]

Required env:
  GITHUB_TOKEN

Optional env:
  GITHUB_OWNER   defaults to dingdaqi16-sudo
  GITHUB_REPO    defaults to new-agent
  GITHUB_WORKFLOW defaults to remind.yml

Args:
  ref            defaults to main
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

token="${GITHUB_TOKEN:-}"
if [[ -z "$token" ]]; then
  echo "Missing required environment variable: GITHUB_TOKEN" >&2
  usage
  exit 1
fi

owner="${GITHUB_OWNER:-dingdaqi16-sudo}"
repo="${GITHUB_REPO:-new-agent}"
workflow="${GITHUB_WORKFLOW:-remind.yml}"
ref="${1:-main}"

response_file="$(mktemp)"
trap 'rm -f "$response_file"' EXIT

http_code="$(curl -sS -L \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${token}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -H "Content-Type: application/json" \
  -o "$response_file" \
  -w "%{http_code}" \
  "https://api.github.com/repos/${owner}/${repo}/actions/workflows/${workflow}/dispatches" \
  -d "{\"ref\":\"${ref}\"}")"

if [[ "$http_code" != 2* ]]; then
  echo "dispatch failed with HTTP $http_code" >&2
  cat "$response_file" >&2
  exit 1
fi

echo "dispatched ${owner}/${repo}/${workflow} @ ${ref}"
