. "$PSScriptRoot\..\scripts\windows-common.ps1"
$own=Get-Process -Id $PID
$tracked=@{pid=$PID;startedUtc=$own.StartTime.ToUniversalTime().ToString('o')}
if((Get-CspTrackedProcess $tracked).Id -ne $PID){throw 'Live process identity failed.'}
$stale=@{pid=$PID;startedUtc='2000-01-01T00:00:00Z'}
if($null -ne (Get-CspTrackedProcess $stale)){throw 'Reused PID must be ignored.'}
Stop-CspComponent $stale
# Reproduce a protected service whose StartTime property is unavailable.
function Get-Process { param($Id,$ErrorAction); return [pscustomobject]@{Id=$Id;StartTime=$null} }
if($null -ne (Get-CspTrackedProcess $tracked)){throw 'Unavailable start time must be ignored.'}
Stop-CspComponent $tracked
Write-Output 'PASS: live PID, reused PID and protected-service null StartTime.'
