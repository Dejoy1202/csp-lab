[CmdletBinding(SupportsShouldProcess=$true,ConfirmImpact='High')]
param([Parameter(Mandatory=$true)][string]$Backup)
. "$PSScriptRoot\windows-common.ps1"
$config=Get-CspWindowsConfig
if($config.DB_NAME -ne 'csp_lab'){throw 'Restore is restricted to the CSP Lab database.'}
if(Test-Path -LiteralPath (Join-Path $taskRoot '.runtime\windows-processes.json')){throw 'Stop CSP Lab before restoring its database.'}
$source=[IO.Path]::GetFullPath($Backup)
if(!(Test-Path -LiteralPath $source -PathType Leaf)){throw 'Backup does not exist.'}
if(!$PSCmdlet.ShouldProcess('local MySQL csp_lab',"Replace existing tables using $source")){return}
$info=New-Object Diagnostics.ProcessStartInfo
$info.FileName=Join-Path $config.MYSQL_BIN 'mysql.exe'
$arguments=@('--host=127.0.0.1',"--port=$($config.DB_PORT)","--user=$($config.DB_USER)",'--default-character-set=utf8mb4',$config.DB_NAME)
$info.Arguments=($arguments | ForEach-Object { ConvertTo-CspArgument $_ }) -join ' '
$info.UseShellExecute=$false;$info.CreateNoWindow=$true
$info.RedirectStandardInput=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
$info.EnvironmentVariables['MYSQL_PWD']=$config.DB_PASSWORD
$child=New-Object Diagnostics.Process;$child.StartInfo=$info
$file=$null;$decompressed=$null
try {
    if(!$child.Start()){throw 'Could not start mysql.'}
    $errors=$child.StandardError.ReadToEndAsync();$output=$child.StandardOutput.ReadToEndAsync()
    $file=[IO.File]::OpenRead($source)
    $decompressed=New-Object IO.Compression.GZipStream($file,[IO.Compression.CompressionMode]::Decompress)
    $decompressed.CopyTo($child.StandardInput.BaseStream)
    $child.StandardInput.Close();$child.WaitForExit()
    if($child.ExitCode -ne 0){throw "Database restore failed: $($errors.Result)"}
    Write-Output 'Restored csp_lab. Run scripts/start-windows.ps1 -SkipImport.'
} finally {
    if($decompressed){$decompressed.Dispose()};if($file){$file.Dispose()};$child.Dispose()
}
