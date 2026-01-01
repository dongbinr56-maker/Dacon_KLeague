#!/usr/bin/env bash
set -euo pipefail

API_BASE=${API_BASE:-http://localhost:8000/api}
FRONTEND_BASE=${FRONTEND_BASE:-http://localhost:3000}
LOG_PREFIX="[smoke_demo]"
ALLOW_DEGRADED=${ALLOW_DEGRADED:-0}
SKIP_IF_NO_GAMES=${SKIP_IF_NO_GAMES:-0}

echo "${LOG_PREFIX} ensure backend is running (frontend optional) ..."

health() {
  curl -sS "${API_BASE}/health" | tee /tmp/smoke_health.json
}

games() {
  curl -sS "${API_BASE}/track2/games" | tee /tmp/smoke_games.json
}

create_session() {
  local game_id=$1
  curl -sS -X POST "${API_BASE}/sessions" \
    -H "Content-Type: application/json" \
    -d "{\"source_type\":\"event_log\",\"mode\":\"offline_realtime\",\"game_id\":\"${game_id}\",\"playback_speed\":5}" \
    | tee /tmp/smoke_session.json
}

start_session() {
  local session_id=$1
  curl -sS -X POST "${API_BASE}/sessions/${session_id}/start" | tee /tmp/smoke_start.json
}

alerts() {
  local session_id=$1
  curl -sS "${API_BASE}/sessions/${session_id}/alerts" | tee /tmp/smoke_alerts.json
}

echo "${LOG_PREFIX} health check..."
health_status=$(health)
echo "${health_status}" | jq .
if echo "${health_status}" | jq -e '.status=="ok"' >/dev/null; then
  echo "${LOG_PREFIX} health ok"
else
  if [[ "${ALLOW_DEGRADED}" == "1" ]]; then
    echo "${LOG_PREFIX} health degraded (continuing because ALLOW_DEGRADED=1)" >&2
  else
    echo "${LOG_PREFIX} health degraded; to continue set ALLOW_DEGRADED=1" >&2
    exit 1
  fi
fi

echo "${LOG_PREFIX} fetch game list..."
game_resp=$(games)
game_id=$(echo "${game_resp}" | jq -r '.games[0].game_id')
if [[ -z "${game_id}" || "${game_id}" == "null" ]]; then
  msg="${LOG_PREFIX} no game_id found (Track2 data missing?). Populate data or check /api/health track2_error."
  if [[ "${SKIP_IF_NO_GAMES}" == "1" ]]; then
    echo "${msg} (SKIP_IF_NO_GAMES=1 → exiting 0)"
    exit 0
  fi
  echo "${msg}" >&2
  exit 2
fi
echo "${LOG_PREFIX} using game_id=${game_id}"

echo "${LOG_PREFIX} create session..."
session_resp=$(create_session "${game_id}")
session_id=$(echo "${session_resp}" | jq -r '.id')
if [[ -z "${session_id}" || "${session_id}" == "null" ]]; then
  echo "${LOG_PREFIX} session creation failed" >&2
  exit 1
fi
echo "${LOG_PREFIX} session=${session_id}"

echo "${LOG_PREFIX} start session..."
start_session "${session_id}" >/dev/null

echo "${LOG_PREFIX} waiting for alerts (max 60s)..."
for _ in {1..60}; do
  sleep 1
  alert_resp=$(alerts "${session_id}")
  count=$(echo "${alert_resp}" | jq '.alerts | length')
  if [[ "${count}" -ge 1 ]]; then
    echo "${LOG_PREFIX} alerts detected=${count}"
    break
  fi
done

if [[ "${count}" -lt 1 ]]; then
  echo "${LOG_PREFIX} no alerts within 60s" >&2
  exit 2
fi

first_clip=$(echo "${alert_resp}" | jq -r '.alerts[0].evidence.clips[0]')
first_overlay=$(echo "${alert_resp}" | jq -r '.alerts[0].evidence.overlays[0]')

echo "${LOG_PREFIX} downloading evidence..."
curl -sS -D /tmp/smoke_clip_headers.txt -o /tmp/smoke_clip.mp4 "${first_clip}"
curl -sS -D /tmp/smoke_overlay_headers.txt -o /tmp/smoke_overlay.png "${first_overlay}"

if [[ ! -s /tmp/smoke_clip.mp4 || ! -s /tmp/smoke_overlay.png ]]; then
  echo "${LOG_PREFIX} evidence download failed or empty" >&2
  exit 3
fi

echo "${LOG_PREFIX} smoke demo SUCCESS (backend-only path verified; frontend optional)"
echo "${LOG_PREFIX} session_id=${session_id}"
echo "${LOG_PREFIX} clip=${first_clip}"
echo "${LOG_PREFIX} overlay=${first_overlay}"
