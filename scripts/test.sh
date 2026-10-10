#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose run --rm e2e python -m unittest discover -s tests -v
docker compose run --rm e2e
docker compose down
docker compose up -d --wait mysql backend worker
docker compose run --rm e2e python e2e.py --persistence
