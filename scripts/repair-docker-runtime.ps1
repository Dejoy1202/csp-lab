param(
    [string]$LocalDataRoot = 'C:\Users\Hp\AppData\Local',
    [switch]$NoRestart
)

$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
chcp.com 65001 > $null
$ErrorActionPreference = 'Stop'

# Only use this for the documented Docker AF_UNIX startup failure.
# Keep runtime directories as backups; never touch WSL disks, volumes or settings.
$taskLocalRoot = [IO.Path]::GetFullPath($LocalDataRoot).TrimEnd('\')
if (-not (Test-Path -LiteralPath $taskLocalRoot -PathType Container)) {
    throw 'The explicitly selected local data directory does not exist.'
}
$taskAllowedPrefix = $taskLocalRoot + '\'
# A failed Desktop can leave a proxy pipe behind. Check an actual Engine request,
# with a bounded timeout, instead of treating the pipe's existence as readiness.
$taskCli = Get-Command docker -ErrorAction SilentlyContinue
if ($taskCli) {
    $taskStart = New-Object System.Diagnostics.ProcessStartInfo
    $taskStart.FileName = $taskCli.Source
    $taskStart.Arguments = 'info --format "{{.ServerVersion}}"'
    $taskStart.UseShellExecute = $false
    $taskStart.CreateNoWindow = $true
    $taskStart.RedirectStandardOutput = $true
    $taskStart.RedirectStandardError = $true
    $taskProbe = New-Object System.Diagnostics.Process
    $taskProbe.StartInfo = $taskStart
    [void]$taskProbe.Start()
    $taskOutput = $taskProbe.StandardOutput.ReadToEndAsync()
    $taskError = $taskProbe.StandardError.ReadToEndAsync()
    if ($taskProbe.WaitForExit(8000)) {
        if ($taskProbe.ExitCode -eq 0 -and $taskOutput.Result.Trim()) {
            $taskProbe.Dispose()
            throw 'Docker Engine is already running. This startup repair must not run against an active engine.'
        }
    } else {
        $taskProbe.Kill()
        $taskProbe.WaitForExit()
    }
    $taskProbe.Dispose()
}

$taskInstallRoots = @(
    (Join-Path $taskLocalRoot 'Programs\DockerDesktop'),
    'C:\Program Files\Docker\Docker'
)
Get-Process -Name 'Docker Desktop','com.docker.backend' -ErrorAction SilentlyContinue |
    Where-Object {
        $taskProcessPath = $_.Path
        $taskProcessPath -and @($taskInstallRoots | Where-Object {
            $taskProcessPath.StartsWith($_ + '\', [StringComparison]::OrdinalIgnoreCase)
        }).Count -gt 0
    } | Stop-Process -Force

$taskStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
foreach ($taskRelative in @('Docker\run', 'docker-secrets-engine')) {
    $taskSource = [IO.Path]::GetFullPath((Join-Path $taskLocalRoot $taskRelative))
    $taskBackupName = (Split-Path $taskSource -Leaf) + '.csp-lab-backup-' + $taskStamp
    $taskBackup = [IO.Path]::GetFullPath((Join-Path (Split-Path $taskSource -Parent) $taskBackupName))
    if (-not $taskSource.StartsWith($taskAllowedPrefix, [StringComparison]::OrdinalIgnoreCase) -or
        -not $taskBackup.StartsWith($taskAllowedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Refusing to rename a path outside the explicitly selected local data directory.'
    }
    if (Test-Path -LiteralPath $taskBackup) { throw 'Backup path already exists; nothing will be overwritten.' }
    if (Test-Path -LiteralPath $taskSource -PathType Container) {
        Rename-Item -LiteralPath $taskSource -NewName $taskBackupName
        Write-Output ('Runtime backup: ' + $taskBackup)
    }
    New-Item -ItemType Directory -Path $taskSource > $null
}

if (-not $NoRestart) {
    $taskDesktop = $taskInstallRoots | ForEach-Object { Join-Path $_ 'Docker Desktop.exe' } |
        Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    if (-not $taskDesktop) { throw 'Docker Desktop executable was not found.' }
    Start-Process -FilePath $taskDesktop -WindowStyle Hidden
    Write-Output 'Docker Desktop launched. Verify docker version after startup completes.'
}
