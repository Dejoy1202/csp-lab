param(
    [Security.SecureString]$RootPassword,
    [string]$MysqlBin = 'C:\Program Files\MySQL\MySQL Server 8.0\bin',
    [string]$Python = 'D:\miniconda3\python.exe',
    [string]$CompilerRoot = 'D:\CspLabData\winlibs\mingw64',
    [string]$JudgeDataRoot = 'D:\CspLabData'
)
. "$PSScriptRoot\windows-common.ps1"
Set-Location -LiteralPath $taskRoot
if (!(Test-Path -LiteralPath '.env')) { & "$PSScriptRoot\init-env.ps1" }
$localPath = Join-Path $taskRoot '.env.windows'
$compilerPath=[IO.Path]::GetFullPath($CompilerRoot)
$dataPath=[IO.Path]::GetFullPath($JudgeDataRoot)
if($dataPath -match '[^\x00-\x7f]'){throw 'Use an ASCII judge-data path because the compiler linker cannot handle Chinese argv.'}
$toolchainPath=Join-Path $dataPath 'toolchain'
if($compilerPath.StartsWith($dataPath+'\',[StringComparison]::OrdinalIgnoreCase)){$toolchainPath=$compilerPath}
if (!(Test-Path -LiteralPath $localPath)) {
    if (!$RootPassword) { $RootPassword = Read-Host 'Local MySQL root password (not saved)' -AsSecureString }
    $dbPassword = New-CspWindowsSecret
    $mysqlExe = Join-Path $MysqlBin 'mysql.exe'
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($RootPassword)
    try {
        $rootText = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
        $sql = "CREATE DATABASE IF NOT EXISTS csp_lab CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci; CREATE USER IF NOT EXISTS 'csp_lab_app'@'localhost' IDENTIFIED BY '$dbPassword'; ALTER USER 'csp_lab_app'@'localhost' IDENTIFIED BY '$dbPassword'; GRANT ALL PRIVILEGES ON csp_lab.* TO 'csp_lab_app'@'localhost';"
        $initialized = Invoke-CspNative $mysqlExe @('--host=127.0.0.1','--port=3306','--user=root','--default-character-set=utf8mb4') $sql @{ MYSQL_PWD=$rootText }
        if ($initialized.ExitCode -ne 0) { throw "Local database initialization failed: $($initialized.Error)" }
    } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $rootText=$null }
    $local = @"
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=csp_lab
DB_URL=jdbc:mysql://127.0.0.1:3306/csp_lab?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai
DB_USER=csp_lab_app
DB_PASSWORD=$dbPassword
MYSQL_BIN=$MysqlBin
PYTHON_EXE=$taskRoot\.runtime\python\Scripts\python.exe
WINDOWS_JUDGE_ROOT=$JudgeDataRoot\judge
WINDOWS_TOOLCHAIN=$toolchainPath
WINDOWS_RUNNER=$taskRoot\.runtime\windows-runner.exe
PYTHONUTF8=1
PYTHONIOENCODING=utf-8
PYTHONPATH=$taskRoot\worker
BASE_URL=http://127.0.0.1:8080
"@
    [IO.File]::WriteAllText($localPath,$local,$utf8)
}
# Selecting an already downloaded project toolchain updates only this path.
$existing=[IO.File]::ReadAllText($localPath,[Text.Encoding]::UTF8)
$replacement=[regex]::Replace($existing,'(?m)^WINDOWS_TOOLCHAIN=.*$',{param($m) "WINDOWS_TOOLCHAIN=$toolchainPath"})
$replacement=[regex]::Replace($replacement,'(?m)^WINDOWS_RUNNER=.*$',{param($m) "WINDOWS_RUNNER=$taskRoot\.runtime\windows-runner.exe"})
[IO.File]::WriteAllText($localPath,$replacement,$utf8)
$config = Get-CspWindowsConfig
$venv = Join-Path $taskRoot '.runtime\python'
if (!(Test-Path -LiteralPath $config.PYTHON_EXE)) {
    & $Python -m venv --system-site-packages $venv
    if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed.' }
}
Invoke-CspWithEnv $config {
    & $config.PYTHON_EXE -m pip install -r (Join-Path $taskRoot 'worker\requirements-windows.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Judge dependencies installation failed.' }
}
# Copy the existing toolchain so sandbox ACL changes do not affect other projects.
if (!(Test-Path -LiteralPath $config.WINDOWS_TOOLCHAIN)) {
    New-Item -ItemType Directory -Path $JudgeDataRoot -Force | Out-Null
    Copy-Item -LiteralPath $CompilerRoot -Destination $config.WINDOWS_TOOLCHAIN -Recurse
}
New-Item -ItemType Directory -Path $config.WINDOWS_JUDGE_ROOT -Force | Out-Null
# GCC's linker still mishandles non-ASCII argv on Windows. Build the trusted
# supervisor in the ASCII data directory, then copy it to the project.
$supervisorBuild=Join-Path $JudgeDataRoot 'supervisor-build'
New-Item -ItemType Directory -Path $supervisorBuild -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $taskRoot 'sandbox\windows\runner.cpp') -Destination (Join-Path $supervisorBuild 'runner.cpp') -Force
Push-Location -LiteralPath $supervisorBuild
try {
    & (Join-Path $CompilerRoot 'bin\g++.exe') -std=c++17 -O2 -static -static-libgcc -static-libstdc++ runner.cpp -o windows-runner.exe -luserenv -ladvapi32 -lole32
    if ($LASTEXITCODE -ne 0) { throw 'Windows supervisor compilation failed.' }
} finally { Pop-Location }
Copy-Item -LiteralPath (Join-Path $supervisorBuild 'windows-runner.exe') -Destination $config.WINDOWS_RUNNER -Force
& $config.WINDOWS_RUNNER prepare $config.WINDOWS_TOOLCHAIN $config.WINDOWS_JUDGE_ROOT
if ($LASTEXITCODE -ne 0) { throw 'AppContainer toolchain preparation failed.' }
Write-Output 'Windows environment prepared. Run scripts/start-windows.ps1.'
