#!/bin/bash
set -e
umask 002

python manage.py collectstatic --noinput
python manage.py migrate --noinput
# 최초 기동 시에만 JSON 적재 (이미 데이터가 있으면 건너뜀)
python manage.py import_json --if-empty

exec gunicorn --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-2}" \
    --access-logfile - config.wsgi:application
