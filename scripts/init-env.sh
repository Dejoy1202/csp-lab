#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then echo '.env already exists; preserving it.'; exit 0; fi
python3 - <<'PY'
from pathlib import Path
import secrets
text = Path('.env.example').read_text(encoding='utf-8')
for placeholder in ['replace-with-a-long-root-password', 'replace-with-a-long-db-password', 'replace-with-a-long-local-api-key', 'replace-with-a-long-random-password']:
    text = text.replace(placeholder, secrets.token_hex(32))
Path('.env').write_text(text, encoding='utf-8')
PY
chmod 600 .env
echo 'Created .env with random secrets.'
