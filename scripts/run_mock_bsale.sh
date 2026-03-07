#!/usr/bin/env bash
set -euo pipefail
uvicorn mock_servers.bsale.main:app --host 0.0.0.0 --port 8010
