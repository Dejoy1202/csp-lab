. "$PSScriptRoot\windows-common.ps1"
$config=Get-CspWindowsConfig
$backupRoot=Join-Path $taskRoot 'backups'
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$target=Join-Path $backupRoot ("csp-lab-{0}.sql.gz" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
$info=New-Object Diagnostics.ProcessStartInfo
$info.FileName=Join-Path $config.MYSQL_BIN 'mysqldump.exe'
$arguments=@('--host=127.0.0.1',"--port=$($config.DB_PORT)","--user=$($config.DB_USER)",'--single-transaction','--no-tablespaces','--set-gtid-purged=OFF','--hex-blob','--default-character-set=utf8mb4',$config.DB_NAME)
$info.Arguments=($arguments | ForEach-Object { ConvertTo-CspArgument $_ }) -join ' '
$info.UseShellExecute=$false
$info.CreateNoWindow=$true
$info.RedirectStandardOutput=$true
$info.RedirectStandardError=$true
$info.StandardErrorEncoding=$utf8
$info.EnvironmentVariables['MYSQL_PWD']=$config.DB_PASSWORD
$child=New-Object Diagnostics.Process
$child.StartInfo=$info
$file=$null
$compressed=$null
try {
    if(!$child.Start()){throw 'Could not start mysqldump.'}
    $errors=$child.StandardError.ReadToEndAsync()
    $file=[IO.File]::Open($target,[IO.FileMode]::CreateNew)
    $compressed=New-Object IO.Compression.GZipStream($file,[IO.Compression.CompressionMode]::Compress)
    # Raw bytes: PowerShell 5.1 must not decode/re-encode the SQL pipeline.
    $child.StandardOutput.BaseStream.CopyTo($compressed)
    $child.WaitForExit()
    if($child.ExitCode -ne 0){throw "Database backup failed: $($errors.Result)"}
    $compressed.Dispose();$compressed=$null
    $file.Dispose();$file=$null
    Write-Output "Database backup: $target"
} catch {
    if($compressed){$compressed.Dispose();$compressed=$null}
    if($file){$file.Dispose();$file=$null}
    if(Test-Path -LiteralPath $target){Remove-Item -LiteralPath $target}
    throw
} finally {
    if($compressed){$compressed.Dispose()}
    if($file){$file.Dispose()}
    $child.Dispose()
}
