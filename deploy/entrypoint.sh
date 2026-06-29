#!/bin/bash
set -e
umask 002

python manage.py collectstatic --noinput
python manage.py migrate --noinput
# 매 기동마다 이미지의 JSON 을 upsert (DB엔 사용자 데이터 없음 → 안전, 재배포 시 자동 갱신)
python manage.py import_json --upsert

exec gunicorn --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-2}" \
    --access-logfile - config.wsgi:application
