param([switch]$StopOnly)
. "$PSScriptRoot\windows-common.ps1"
$statePath=Join-Path $taskRoot '.runtime\windows-processes.json'
$components=Get-Content -LiteralPath $statePath -Encoding utf8 | ConvertFrom-Json
$worker=@($components | Where-Object { $_.name -eq 'worker' })
if($worker.Count -ne 1){throw 'Expected one tracked CSP Lab worker.'}
Stop-CspComponent $worker[0]
if($StopOnly){Write-Output 'Stopped the tracked judge worker.';return}
$config=Get-CspWindowsConfig
Invoke-CspWithEnv $config {
    $spec=@{name='worker';executable=$config.PYTHON_EXE;arguments=@((Join-Path $taskRoot 'worker\worker.py'));directory=$taskRoot} | ConvertTo-Json -Depth 4
    $launched=Invoke-CspNative $config.PYTHON_EXE @((Join-Path $taskRoot 'scripts\launch-windows.py')) $spec
    if($launched.ExitCode -ne 0){throw "Could not launch worker: $($launched.Error)"}
    $metadata=$launched.Output | ConvertFrom-Json
    $worker[0].pid=$metadata.pid
    $worker[0].startedUtc=$metadata.startedUtc
}
[IO.File]::WriteAllText($statePath,($components | ConvertTo-Json),$utf8)
Write-Output 'Restarted the isolated judge worker.'
