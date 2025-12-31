#!/usr/bin/env bash
set -euo pipefail

unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy NO_PROXY no_proxy
unset npm_config_proxy npm_config_https_proxy npm_config_http_proxy

REGISTRY=${NPM_REGISTRY:-https://registry.npmjs.org/}

exec npm --registry "${REGISTRY}" "$@"
