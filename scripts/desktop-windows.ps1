param([ValidateSet('Start','Stop')][string]$Action='Start')
. "$PSScriptRoot\windows-common.ps1"
try {
    if($Action -eq 'Start') {
        Write-Output 'Starting CSP Lab. Please keep this window open until startup finishes.'
        & "$PSScriptRoot\start-windows.ps1"
        Start-Process 'http://127.0.0.1:5173/'
    } else {
        & "$PSScriptRoot\stop-windows.ps1"
        Write-Output 'Website services stopped. Your database records are retained.'
        Start-Sleep -Seconds 2
    }
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host 'Operation failed. Logs are in the project .runtime folder.'
    Read-Host 'Press Enter to close'
    exit 1
}
