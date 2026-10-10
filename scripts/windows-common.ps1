$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
chcp.com 65001 > $null
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))

function Read-CspEnvFile([string]$Path) {
    $values = @{}
    foreach ($line in [IO.File]::ReadAllLines($Path, [Text.Encoding]::UTF8)) {
        if ($line -match '^\s*([A-Z][A-Z0-9_]*)=(.*)$') {
            $values[$matches[1]] = $matches[2].Trim()
        }
    }
    return $values
}
function Get-CspWindowsConfig {
    $values = Read-CspEnvFile (Join-Path $taskRoot '.env')
    $local = Join-Path $taskRoot '.env.windows'
    if (!(Test-Path -LiteralPath $local)) { throw 'Run scripts/setup-windows.ps1 first.' }
    foreach ($entry in (Read-CspEnvFile $local).GetEnumerator()) { $values[$entry.Key] = $entry.Value }
    return $values
}
function New-CspWindowsSecret {
    $bytes = New-Object byte[] 32
    $random = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $random.GetBytes($bytes) } finally { $random.Dispose() }
    return [BitConverter]::ToString($bytes).Replace('-','').ToLowerInvariant()
}
function Invoke-CspWithEnv($Values, [scriptblock]$Action) {
    $old = @{}
    try {
        foreach ($key in $Values.Keys) {
            $old[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
            [Environment]::SetEnvironmentVariable($key, $Values[$key], 'Process')
        }
        & $Action
    } finally {
        foreach ($key in $old.Keys) { [Environment]::SetEnvironmentVariable($key, $old[$key], 'Process') }
    }
}
function ConvertTo-CspArgument([string]$Value) {
    return '"' + [regex]::Replace([regex]::Replace($Value, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1') + '"'
}
function Get-CspTrackedProcess($Component) {
    $child=Get-Process -Id $Component.pid -ErrorAction SilentlyContinue
    if(!$child){return $null}
    # A stale PID may now belong to a protected Windows service. Its start
    # time is inaccessible; never treat that unrelated process as ours.
    try {
        $started=$child.StartTime
        if($null -eq $started -or $started.ToUniversalTime().Ticks -ne ([datetime]$Component.startedUtc).ToUniversalTime().Ticks){return $null}
    } catch { return $null }
    return $child
}
function Stop-CspComponent($Component) {
    $child=Get-CspTrackedProcess $Component
    if(!$child){return}
    # ParentProcessId can refer to a reused PID after a launcher exits. Include
    # only children created after their verified parent; taskkill /T alone
    # cannot distinguish these stale parent links.
    $owned=@{};$owned[[int]$child.Id]=$child.StartTime.ToUniversalTime().Ticks
    $all=Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,CreationDate
    do {
        $added=$false
        foreach($item in $all) {
            $processId=[int]$item.ProcessId;$parentId=[int]$item.ParentProcessId
            if($owned.ContainsKey($processId) -or !$owned.ContainsKey($parentId) -or !$item.CreationDate){continue}
            $created=([datetime]$item.CreationDate).ToUniversalTime().Ticks
            if($created+10 -lt $owned[$parentId]){continue}
            $owned[$processId]=$created;$added=$true
        }
    } while($added)
    foreach($entry in ($owned.GetEnumerator() | Sort-Object Value -Descending)) {
        $current=Get-Process -Id $entry.Key -ErrorAction SilentlyContinue
        if($current -and $null -ne $current.StartTime -and [Math]::Abs($current.StartTime.ToUniversalTime().Ticks-$entry.Value) -lt 10){Stop-Process -Id $entry.Key}
    }
}
function Invoke-CspNative([string]$Executable, [string[]]$Arguments, [string]$InputText='', $Values=@{}) {
    $info = New-Object Diagnostics.ProcessStartInfo
    $info.FileName=$Executable
    $info.Arguments=($Arguments | ForEach-Object { ConvertTo-CspArgument $_ }) -join ' '
    $info.UseShellExecute=$false
    $info.CreateNoWindow=$true
    $info.RedirectStandardInput=$true
    $info.RedirectStandardOutput=$true
    $info.RedirectStandardError=$true
    $info.StandardOutputEncoding=$utf8
    $info.StandardErrorEncoding=$utf8
    foreach ($key in $Values.Keys) { $info.EnvironmentVariables[$key]=[string]$Values[$key] }
    $child = New-Object Diagnostics.Process
    $child.StartInfo=$info
    try {
        if (!$child.Start()) { throw 'Process could not start.' }
        $outTask=$child.StandardOutput.ReadToEndAsync()
        $errTask=$child.StandardError.ReadToEndAsync()
        $child.StandardInput.Write($InputText)
        $child.StandardInput.Close()
        $child.WaitForExit()
        return @{ ExitCode=$child.ExitCode; Output=$outTask.Result; Error=$errTask.Result }
    } finally { $child.Dispose() }
}
