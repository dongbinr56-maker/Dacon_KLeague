#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${DIR}/frontend"

echo "[build_frontend] probing npm registry connectivity..."
if ! "${DIR}/scripts/npm_net.sh" view @types/node version >/dev/null 2>&1; then
  echo "[build_frontend] public npm registry unreachable via current proxy."
  echo "[build_frontend] set NPM_REGISTRY to an internal mirror or run in CI (GitHub Actions builds frontend)."
  exit 2
fi

echo "[build_frontend] npm ci (proxy-respecting wrapper)"
"${DIR}/scripts/npm_net.sh" ci

echo "[build_frontend] npm run build (proxy-respecting wrapper)"
"${DIR}/scripts/npm_net.sh" run build
