<#
  Ejecuta backend/db/schema.sql contra localhost\SQLEXPRESS usando autenticacion de Windows.
  No requiere sqlcmd instalado -- usa System.Data.SqlClient directamente.
#>

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "schema.sql"
$server = "localhost\SQLEXPRESS"
$connString = "Server=$server;Database=master;Trusted_Connection=True;TrustServerCertificate=True;"

$sqlText = Get-Content -Path $scriptPath -Raw

# Divide el script en lotes por las lineas "GO" (igual que hace sqlcmd/SSMS)
$batches = [System.Text.RegularExpressions.Regex]::Split($sqlText, '(?im)^\s*GO\s*$')

Add-Type -AssemblyName "System.Data"

$connection = New-Object System.Data.SqlClient.SqlConnection($connString)
$connection.Open()
Write-Host "Conectado a $server" -ForegroundColor Green

foreach ($batch in $batches) {
    $trimmed = $batch.Trim()
    if ([string]::IsNullOrWhiteSpace($trimmed)) { continue }

    $command = $connection.CreateCommand()
    $command.CommandText = $trimmed
    $command.CommandTimeout = 120
    try {
        $command.ExecuteNonQuery() | Out-Null
    } catch {
        Write-Host "Error ejecutando lote:" -ForegroundColor Red
        Write-Host $trimmed.Substring(0, [Math]::Min(200, $trimmed.Length)) -ForegroundColor DarkGray
        throw
    }
}

$connection.Close()
Write-Host "Base de datos DS_Votaciones creada correctamente." -ForegroundColor Green
