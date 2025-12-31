#!/usr/bin/env bash
set -euo pipefail

REGISTRY="${NPM_REGISTRY:-${npm_config_registry:-}}"
if [[ -z "${REGISTRY}" && -f .npmrc ]]; then
  REGISTRY_FROM_FILE="$(grep -E '^registry=' .npmrc | tail -n1 | cut -d= -f2- || true)"
  REGISTRY="${REGISTRY_FROM_FILE:-}"
fi

if [[ "${NPM_DISABLE_PROXY:-0}" == "1" ]]; then
  unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy NO_PROXY no_proxy
  unset npm_config_proxy npm_config_https_proxy npm_config_http_proxy
  PROXY_STATE="disabled"
else
  PROXY_STATE="enabled"
fi

if [[ -n "${REGISTRY}" ]]; then
  export npm_config_registry="${REGISTRY}"
fi

REGISTRY_EFFECTIVE="${npm_config_registry:-<npm default>}"
echo "[npm_net] registry=${REGISTRY_EFFECTIVE} proxy=${PROXY_STATE}"

exec npm "$@"
