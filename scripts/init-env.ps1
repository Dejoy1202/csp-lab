$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
chcp.com 65001 > $null
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskEnvPath = Join-Path $taskRoot '.env'
if (Test-Path -LiteralPath $taskEnvPath) {
    Write-Output '.env already exists; preserving it.'
    exit 0
}
function New-CspSecret {
    $taskBytes = New-Object byte[] 32
    $taskRandom = [Security.Cryptography.RandomNumberGenerator]::Create()
    $taskRandom.GetBytes($taskBytes)
    $taskRandom.Dispose()
    return ([BitConverter]::ToString($taskBytes)).Replace('-','').ToLowerInvariant()
}
$taskText = [IO.File]::ReadAllText((Join-Path $taskRoot '.env.example'),[Text.Encoding]::UTF8)
$taskText = $taskText.Replace('replace-with-a-long-root-password',(New-CspSecret))
$taskText = $taskText.Replace('replace-with-a-long-db-password',(New-CspSecret))
$taskText = $taskText.Replace('replace-with-a-long-local-api-key',(New-CspSecret))
$taskText = $taskText.Replace('replace-with-a-long-random-password',(New-CspSecret))
[IO.File]::WriteAllText($taskEnvPath,$taskText,$utf8)
Write-Output 'Created .env with random secrets. Open the file locally to get your administrator password.'
