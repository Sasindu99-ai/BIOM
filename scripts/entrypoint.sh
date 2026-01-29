#!/usr/bin/env bash

set -e

RUN_MANAGE_PY="uv run python manage.py"

# echo "Collecting static files..."
# $RUN_MANAGE_PY collectstatic --no-input

echo "Running migrations..."
$RUN_MANAGE_PY migrate --no-input

echo "Starting Gunicorn server..."
exec uv run gunicorn manage:wsgi \
    --bind 0.0.0.0:8001 \
    --workers 9 \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile /opt/biom/logs/access.log \
    --error-logfile /opt/biom/logs/error.log \
    --capture-output
