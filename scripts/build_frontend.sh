#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${DIR}/frontend"

echo "[build_frontend] npm ci (no-proxy wrapper)"
"${DIR}/scripts/npm_noproxy.sh" ci

echo "[build_frontend] npm run build (no-proxy wrapper)"
"${DIR}/scripts/npm_noproxy.sh" run build
