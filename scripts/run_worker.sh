#!/usr/bin/env bash
set -euo pipefail
celery -A app.workers.celery_app:celery_app worker -Q celery --loglevel=info
