param([switch]$FullReferences)
. "$PSScriptRoot\windows-common.ps1"
Set-Location -LiteralPath $taskRoot
$config=Get-CspWindowsConfig
$health=Invoke-RestMethod -Uri 'http://127.0.0.1:8080/actuator/health' -TimeoutSec 3
if($health.status -ne 'UP'){throw 'Start CSP Lab before running its live tests.'}
& (Join-Path $taskRoot 'tests\windows_process_tracking.ps1')
Invoke-CspWithEnv $config {
    & $config.PYTHON_EXE tests\test_mutation_gate.py
    if($LASTEXITCODE -ne 0){throw 'Problem construction gate tests failed.'}
    & $config.PYTHON_EXE tests\test_windows_sandbox.py
    if($LASTEXITCODE -ne 0){throw 'Sandbox tests failed.'}
    & $config.PYTHON_EXE tests\e2e.py
    if($LASTEXITCODE -ne 0){throw 'Live API tests failed.'}
    & $config.PYTHON_EXE tests\windows_exit_code_regression.py
    if($LASTEXITCODE -ne 0){throw 'Windows exit-code regression failed.'}
    # Keep timing tests sequential; no concurrent compiler/reference workloads.
    if($FullReferences){
        & $config.PYTHON_EXE tests\windows_reference_compatibility.py --formal
        if($LASTEXITCODE -ne 0){throw 'Reference tests failed.'}
    }
    & $config.PYTHON_EXE problem-packs\verify_exam.py --batches 202509 --output test-results\windows
    if($LASTEXITCODE -ne 0){throw 'Five-question mock test failed.'}
}
Write-Output 'Windows judge/API/mock tests passed. Reports: test-results/windows.'
