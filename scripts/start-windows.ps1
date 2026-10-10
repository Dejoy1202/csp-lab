param([switch]$Rebuild, [switch]$SkipImport)
. "$PSScriptRoot\windows-common.ps1"
Set-Location -LiteralPath $taskRoot
$config = Get-CspWindowsConfig
$runtime = Join-Path $taskRoot '.runtime'
$statePath = Join-Path $runtime 'windows-processes.json'
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
if (Test-Path -LiteralPath $statePath) {
    $tracked=Get-Content -LiteralPath $statePath -Encoding utf8 | ConvertFrom-Json
    $live=@($tracked | Where-Object { $null -ne (Get-CspTrackedProcess $_) })
    if($live.Count -eq 3 -and @($live.name | Sort-Object -Unique).Count -eq 3 -and !$Rebuild) {
        try {
            $health=Invoke-RestMethod -Uri 'http://127.0.0.1:8080/actuator/health' -TimeoutSec 3
            $front=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5173' -TimeoutSec 3
            if($health.status -eq 'UP' -and $front.StatusCode -eq 200) {
                Write-Output 'CSP Lab is already running: http://127.0.0.1:5173'
                return
            }
        } catch {}
    }
    if($live.Count -gt 0){throw 'CSP Lab is partly running or needs a rebuild. Use the exit shortcut first, then start again.'}
    Move-Item -LiteralPath $statePath -Destination (Join-Path $runtime 'windows-processes.previous.json') -Force
}
$jar = Join-Path $taskRoot 'backend\target\csp-lab-backend-0.1.0.jar'
if ($Rebuild -or !(Test-Path -LiteralPath $jar)) {
    Push-Location -LiteralPath (Join-Path $taskRoot 'backend')
    try { & mvn verify; if ($LASTEXITCODE -ne 0) { throw 'Java build failed.' } }
    finally { Pop-Location }
}
foreach ($port in @(8080,5173)) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $port is already in use. Stop the existing CSP Lab instance first."
    }
}
if (!(Test-Path -LiteralPath $config.WINDOWS_RUNNER)) { throw 'Run setup-windows.ps1 to build the sandbox first.' }
# Windows locks a running JAR. Keep Maven's build output free for later rebuilds.
$runtimeJar=Join-Path $runtime 'backend.jar'
Copy-Item -LiteralPath $jar -Destination $runtimeJar -Force
$processes = @()
function Start-CspComponent([string]$Name,[string]$Executable,[string[]]$Arguments,[string]$Directory) {
    $spec=@{name=$Name;executable=$Executable;arguments=$Arguments;directory=$Directory} | ConvertTo-Json -Depth 4
    $launched=Invoke-CspNative $config.PYTHON_EXE @((Join-Path $taskRoot 'scripts\launch-windows.py')) $spec
    if($launched.ExitCode -ne 0){throw "Could not launch $Name`: $($launched.Error)"}
    return ($launched.Output | ConvertFrom-Json)
}
try {
    Invoke-CspWithEnv $config {
        $javaCommand=(Get-Command java.exe).Source
        $javaInfo=Invoke-CspNative $javaCommand @('-XshowSettings:properties','-version')
        if($javaInfo.ExitCode -ne 0 -or $javaInfo.Error -notmatch '(?m)^\s*java.home\s*=\s*(.+)$'){throw 'Could not resolve the installed Java runtime.'}
        $java=Join-Path $matches[1].Trim() 'bin\java.exe'
        $script:processes += Start-CspComponent 'backend' $java @('-Dfile.encoding=UTF-8','-Dserver.address=127.0.0.1','-jar',$runtimeJar) $taskRoot
        $ready=$false
        for($i=0;$i -lt 60;$i++) {
            try { $health=Invoke-RestMethod -Uri 'http://127.0.0.1:8080/actuator/health' -TimeoutSec 2; if($health.status -eq 'UP'){$ready=$true;break} } catch {}
            Start-Sleep -Seconds 1
        }
        if(!$ready){throw 'Backend failed to become ready. See .runtime/backend-error.log.'}
        if(!$SkipImport) {
            & $config.PYTHON_EXE (Join-Path $taskRoot 'problem-packs\build.py') --import-existing --output (Join-Path $taskRoot 'problem-packs\generated')
            if($LASTEXITCODE -ne 0){throw 'Verified pack import failed.'}
        }
        $script:processes += Start-CspComponent 'worker' $config.PYTHON_EXE @((Join-Path $taskRoot 'worker\worker.py')) $taskRoot
        $node=(Get-Command node.exe).Source
        $script:processes += Start-CspComponent 'frontend' $node @((Join-Path $taskRoot 'frontend\node_modules\vite\bin\vite.js'),'--host','127.0.0.1','--strictPort') (Join-Path $taskRoot 'frontend')
        $frontReady=$false
        for($i=0;$i -lt 30;$i++) {
            try { $front=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5173' -TimeoutSec 2; if($front.StatusCode -eq 200){$frontReady=$true;break} } catch {}
            Start-Sleep -Seconds 1
        }
        if(!$frontReady){throw 'Frontend failed to become ready. See .runtime/frontend-error.log.'}
    }
    [IO.File]::WriteAllText($statePath,($processes | ConvertTo-Json),$utf8)
    Write-Output 'CSP Lab: http://127.0.0.1:5173 (Windows local, no Docker)'
} catch {
    foreach($component in $processes){try{Stop-CspComponent $component}catch{}}
    throw
}
