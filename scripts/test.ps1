$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
chcp.com 65001 > $null
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')))
docker compose run --rm e2e python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Scoring tests failed.' }
docker compose run --rm e2e
if ($LASTEXITCODE -ne 0) { throw 'Integration tests failed.' }
# Recreate application containers while retaining the MySQL named volume.
docker compose down
if ($LASTEXITCODE -ne 0) { throw 'Compose shutdown failed.' }
docker compose up -d --wait mysql backend worker
if ($LASTEXITCODE -ne 0) { throw 'Compose restart failed.' }
docker compose run --rm e2e python e2e.py --persistence
if ($LASTEXITCODE -ne 0) { throw 'Persistence check failed.' }
