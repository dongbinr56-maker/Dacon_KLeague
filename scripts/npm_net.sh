#!/usr/bin/env bash
set -euo pipefail

REGISTRY="${NPM_REGISTRY:-${npm_config_registry:-}}"
if [[ -z "${REGISTRY}" && -f .npmrc ]]; then
  REGISTRY_FROM_FILE="$(grep -E '^registry=' .npmrc | tail -n1 | cut -d= -f2- || true)"
  REGISTRY="${REGISTRY_FROM_FILE:-}"
fi

# Normalize proxy environment (avoid npm env-config warnings)
unset npm_config_http_proxy npm_config_https_proxy

if [[ "${NPM_DISABLE_PROXY:-0}" == "1" ]]; then
  unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy NO_PROXY no_proxy
  unset npm_config_proxy npm_config_https_proxy npm_config_http_proxy
  PROXY_STATE="disabled"
  PROXY_HTTP_VALUE="<unset>"
  PROXY_HTTPS_VALUE="<unset>"
else
  if [[ -z "${npm_config_proxy:-}" && -n "${HTTP_PROXY:-${http_proxy:-}}" ]]; then
    export npm_config_proxy="${HTTP_PROXY:-${http_proxy:-}}"
  fi
  if [[ -z "${npm_config_https_proxy:-}" && -n "${HTTPS_PROXY:-${https_proxy:-}}" ]]; then
    export npm_config_https_proxy="${HTTPS_PROXY:-${https_proxy:-}}"
  fi
  PROXY_STATE="enabled"
  PROXY_HTTP_VALUE="${npm_config_proxy:-${HTTP_PROXY:-${http_proxy:-<none>}}}"
  PROXY_HTTPS_VALUE="${npm_config_https_proxy:-${HTTPS_PROXY:-${https_proxy:-<none>}}}"
fi

if [[ -n "${REGISTRY}" ]]; then
  export npm_config_registry="${REGISTRY}"
fi

REGISTRY_EFFECTIVE="${npm_config_registry:-<npm default>}"
echo "[npm_net] registry=${REGISTRY_EFFECTIVE} proxy=${PROXY_STATE} http_proxy=${PROXY_HTTP_VALUE} https_proxy=${PROXY_HTTPS_VALUE}"

exec npm "$@"
