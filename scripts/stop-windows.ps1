. "$PSScriptRoot\windows-common.ps1"
$statePath=Join-Path $taskRoot '.runtime\windows-processes.json'
if(!(Test-Path -LiteralPath $statePath)){Write-Output 'No tracked CSP Lab processes.';exit 0}
$components=Get-Content -LiteralPath $statePath -Encoding utf8 | ConvertFrom-Json
foreach($component in $components) {
    Stop-CspComponent $component
}
Remove-Item -LiteralPath $statePath
Write-Output 'Stopped CSP Lab. Local MySQL and its data are retained.'
