#!/usr/bin/env bash
set -euo pipefail

API_BASE=${API_BASE:-http://localhost:8000/api}
PLAYBACK_SPEED=${PLAYBACK_SPEED:-5}
LOG_PREFIX="[demo]"
ALLOW_DEGRADED=${ALLOW_DEGRADED:-0}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "${LOG_PREFIX} missing dependency: $1" >&2
    exit 10
  }
}

require_cmd curl
require_cmd jq

step() {
  echo "${LOG_PREFIX} $*"
}

fail() {
  echo "${LOG_PREFIX} ERROR: $*" >&2
  exit 1
}

health_json=$(curl -sS "${API_BASE}/health") || fail "health request failed. Is the backend running? Try: cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"
step "Health response: $(echo "${health_json}" | jq -c '{status,track2_error}')"
status=$(echo "${health_json}" | jq -r '.status')
if [[ "${status}" != "ok" ]]; then
  if [[ "${ALLOW_DEGRADED}" == "1" ]]; then
    step "Health is degraded; continuing because ALLOW_DEGRADED=1"
  else
    fail "Health status is not ok (status=${status}). Check track2_error in /api/health. To continue anyway, set ALLOW_DEGRADED=1."
  fi
fi

games_json=$(curl -sS "${API_BASE}/track2/games?recommend=true") || fail "failed to load games"
game_id=$(echo "${games_json}" | jq -r '.games[0].game_id // empty')
if [[ -z "${game_id}" ]]; then
  echo "${LOG_PREFIX} Track2 games list is empty. Populate Track2 data or check /api/health track2_error."
  exit 2
fi
step "Using game_id=${game_id}"

session_payload=$(jq -n --arg gid "${game_id}" --argjson speed "${PLAYBACK_SPEED}" '{
  source_type:"event_log",
  mode:"offline_realtime",
  game_id:$gid,
  playback_speed:$speed
}')
session_json=$(curl -sS -X POST "${API_BASE}/sessions" -H "Content-Type: application/json" -d "${session_payload}") \
  || fail "session creation failed"
session_id=$(echo "${session_json}" | jq -r '.id // empty')
if [[ -z "${session_id}" ]]; then
  fail "session id missing in response: ${session_json}"
fi
step "Session created: ${session_id}"

start_json=$(curl -sS -X POST "${API_BASE}/sessions/${session_id}/start") || fail "failed to start session"
step "Session start response: $(echo "${start_json}" | jq -c '{status}')"

step "Waiting for alerts (up to 60s)..."
alert_resp=""
for _ in {1..60}; do
  sleep 1
  alert_resp=$(curl -sS "${API_BASE}/sessions/${session_id}/alerts") || true
  count=$(echo "${alert_resp}" | jq '.alerts | length')
  if [[ "${count}" -ge 1 ]]; then
    break
  fi
done

if [[ -z "${alert_resp}" ]] || [[ $(echo "${alert_resp}" | jq '.alerts | length') -lt 1 ]]; then
  fail "No alerts observed within 60 seconds"
fi
step "Alerts received: $(echo "${alert_resp}" | jq '.alerts | length')"

clip_url=$(echo "${alert_resp}" | jq -r '.alerts[0].evidence.clips[0] // empty')
overlay_url=$(echo "${alert_resp}" | jq -r '.alerts[0].evidence.overlays[0] // empty')
if [[ -z "${clip_url}" || -z "${overlay_url}" ]]; then
  fail "Evidence URLs missing in first alert"
fi

step "Checking evidence URLs..."
curl -sSI "${clip_url}" | head -n 5 || fail "clip URL not reachable: ${clip_url}"
curl -sSI "${overlay_url}" | head -n 5 || fail "overlay URL not reachable: ${overlay_url}"

step "Demo succeeded"
echo "${LOG_PREFIX} session_id=${session_id}"
echo "${LOG_PREFIX} clip=${clip_url}"
echo "${LOG_PREFIX} overlay=${overlay_url}"
echo "${LOG_PREFIX} Open http://localhost:8000/demo in your browser to explore the backend-only UI (no npm required)."

if [[ "${status}" == "ok" ]]; then
  echo "${LOG_PREFIX} /demo HEAD check:"
  curl -sSI "${API_BASE%/api}/demo" | head -n 5 || true
  curl -sSI "${API_BASE%/api}/demo/" | head -n 5 || true
fi
