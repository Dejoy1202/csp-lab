#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/init-env.sh
docker info --format '{{.ServerVersion}}'
docker compose build backend worker sandbox-image pack-builder e2e
docker compose up -d --wait mysql backend worker
docker compose run --rm pack-builder python build.py --import-existing
echo 'CSP Lab backend is ready: http://127.0.0.1:8080/actuator/health'
