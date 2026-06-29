#!/bin/bash
# build.sh — 버전 bump + Docker 이미지 빌드/푸시 (빌드 머신 전용)
# Usage: ./deploy/build.sh X.Y.Z
#
# 운영 호스트 배포는 deploy/host/deploy.sh 가 담당 (git pull 후 별도 실행).
set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: $0 X.Y.Z"
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE=honestjung/strati2026
cd "$PROJECT_DIR"

echo "=== [1/3] Bumping version to $VERSION ==="
echo "VERSION = '$VERSION'" > config/version.py
git add config/version.py
if git diff --cached --quiet; then
    echo "(version already at $VERSION, no commit)"
else
    git commit -m "Bump version to $VERSION"
fi

echo ""
echo "=== [2/3] Building $IMAGE:$VERSION ==="
docker build -f deploy/Dockerfile -t "$IMAGE:$VERSION" -t "$IMAGE:latest" .

echo ""
echo "=== [3/3] Pushing image ==="
docker push "$IMAGE:$VERSION"
docker push "$IMAGE:latest"

echo ""
echo "=== Done: $IMAGE:$VERSION ==="
echo "다음 단계 (운영 호스트):"
echo "  cd ~/projects/strati2026 && git pull"
echo "  ./deploy/sync_to_srv.sh           # deploy/host/* → /srv/strati2026/"
echo "  /srv/strati2026/deploy.sh $VERSION"
