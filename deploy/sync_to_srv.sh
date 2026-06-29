#!/bin/bash
# deploy/sync_to_srv.sh — 운영 호스트에서 deploy/host/* → /srv/strati2026/ 동기화
#   cd ~/projects/strati2026 && git pull && ./deploy/sync_to_srv.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOST_DEST="${HOST_DEST:-/srv/strati2026}"

if [ ! -d "$HOST_DEST" ]; then
    echo "ERROR: $HOST_DEST not found (운영 호스트에서만 실행)." >&2
    exit 1
fi

cp -p "$PROJECT_DIR/deploy/host/deploy.sh"           "$HOST_DEST/"
cp -p "$PROJECT_DIR/deploy/host/docker-compose.yml"  "$HOST_DEST/"
chmod +x "$HOST_DEST/deploy.sh"
echo "synced deploy.sh + docker-compose.yml → $HOST_DEST/"
echo "다음: /srv/strati2026/deploy.sh X.Y.Z"
