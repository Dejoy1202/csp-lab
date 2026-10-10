$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
chcp.com 65001 > $null
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')))
& "$PSScriptRoot\init-env.ps1"
docker info --format '{{.ServerVersion}}'
if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop in Linux container mode first.' }
docker compose build backend worker sandbox-image pack-builder e2e
if ($LASTEXITCODE -ne 0) { throw 'Image build failed.' }
docker compose up -d --wait mysql backend worker
if ($LASTEXITCODE -ne 0) { throw 'Services did not become ready.' }
docker compose run --rm pack-builder python build.py --import-existing
if ($LASTEXITCODE -ne 0) { throw 'Problem import failed. See README for rebuilding packs.' }
Write-Output 'CSP Lab backend is ready: http://127.0.0.1:8080/actuator/health'
