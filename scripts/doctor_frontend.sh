#!/usr/bin/env bash
set -euo pipefail

LOG_PREFIX="[doctor_frontend]"

step() {
  echo "${LOG_PREFIX} $*"
}

run_cmd() {
  local desc=$1
  shift
  step "${desc}"
  set +e
  "$@"
  local rc=$?
  set -e
  step "exit_code=${rc}"
}

step "Node / npm versions"
run_cmd "node -v" node -v
run_cmd "npm -v" npm -v

step "npm registry settings"
run_cmd "npm config get registry" npm config get registry
run_cmd "npm config list (filtered)" bash -lc "npm config list -l | grep -E 'registry|proxy|https-proxy|strict-ssl|auth' || true"

if [[ -f "$HOME/.npmrc" ]]; then
  step "~/.npmrc exists (showing non-sensitive lines)"
  run_cmd "cat ~/.npmrc" bash -lc "sed 's/token=.*/token=***MASKED***/' \"$HOME/.npmrc\""
else
  step "~/.npmrc not found"
fi

if [[ -f ".npmrc" ]]; then
  step "./.npmrc exists (showing non-sensitive lines)"
  run_cmd "cat ./.npmrc" bash -lc "sed 's/token=.*/token=***MASKED***/' .npmrc"
fi

step "Probe @types/node from public registry"
run_cmd "npm view @types/node version --registry=https://registry.npmjs.org/" npm view @types/node version --registry=https://registry.npmjs.org/

step "Doctor finished"
