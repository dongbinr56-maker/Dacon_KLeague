#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${DIR}/frontend"

echo "[build_frontend] npm ci (proxy-respecting wrapper)"
"${DIR}/scripts/npm_net.sh" ci

echo "[build_frontend] npm run build (proxy-respecting wrapper)"
"${DIR}/scripts/npm_net.sh" run build
