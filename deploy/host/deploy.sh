#!/bin/bash
# /srv/strati2026/deploy.sh — strati2026 버전 스왑 배포
# Usage: /srv/strati2026/deploy.sh X.Y.Z
set -euo pipefail

VERSION=${1:-}
if [ -z "$VERSION" ]; then
    echo "Usage: $0 X.Y.Z"
    exit 1
fi

cd /srv/strati2026
IMAGE="honestjung/strati2026:${VERSION}"

echo "=== [1/4] Pulling ${IMAGE} ==="
docker pull "${IMAGE}"

echo ""
echo "=== [2/4] Updating .env (IMAGE_TAG=${VERSION}) ==="
if grep -q '^IMAGE_TAG=' .env 2>/dev/null; then
    sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=${VERSION}/" .env
else
    echo "IMAGE_TAG=${VERSION}" >> .env
fi

echo ""
echo "=== [3/4] Pre-deploy DB snapshot ==="
SNAP_DIR=/srv/strati2026/backup
mkdir -p "$SNAP_DIR"
if [ -f /srv/strati2026/db.sqlite3 ]; then
    TS=$(date -u +%Y%m%d_%H%M%S)
    cp -p /srv/strati2026/db.sqlite3 "$SNAP_DIR/db_pre_${VERSION}_${TS}.sqlite3"
    # 최근 20개만 보관
    ls -1tr "$SNAP_DIR"/db_pre_*.sqlite3 2>/dev/null | head -n -20 \
        | while read -r f; do rm -f "$f"; done
    echo "  snapshot saved."
fi

echo ""
echo "=== [4/4] Swap container ==="
docker compose down
docker compose up -d strati2026
docker compose ps strati2026
echo ""
echo "=== Done: strati2026 -> ${VERSION} ==="
