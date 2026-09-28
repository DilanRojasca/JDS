<#
  Ejecutar en PowerShell como Administrador (clic derecho -> "Ejecutar como administrador").
  Instala SQL Server Express (autenticacion de Windows), habilita TCP/IP en el puerto 1433
  y el driver ODBC 18. Tarda varios minutos por la descarga (~500-700 MB).
#>

$ErrorActionPreference = "Stop"

Write-Host "1/4 Descargando instalador de SQL Server Express..." -ForegroundColor Cyan
$bootstrap = "$env:TEMP\SQLEXPR-bootstrap.exe"
Invoke-WebRequest -Uri "https://go.microsoft.com/fwlink/?linkid=2216019" -OutFile $bootstrap

Write-Host "2/4 Instalando SQL Server Express (instancia SQLEXPRESS, autenticacion Windows)..." -ForegroundColor Cyan

$originalCulture = Get-Culture
Write-Host "   Formato regional actual: $($originalCulture.Name). Cambiando temporalmente a en-US para evitar el chequeo de idioma del instalador..." -ForegroundColor DarkGray
Set-Culture en-US

try {
    Start-Process -FilePath $bootstrap -ArgumentList "/ACTION=Install","/ENU","/IACCEPTSQLSERVERLICENSETERMS","/QUIET" -Wait
} finally {
    Write-Host "   Restaurando formato regional a $($originalCulture.Name)..." -ForegroundColor DarkGray
    Set-Culture $originalCulture.Name
}

$service = Get-Service -Name "MSSQL`$SQLEXPRESS" -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Host "No se encontro el servicio MSSQL`$SQLEXPRESS. Revisa el log en C:\Program Files\Microsoft SQL Server\170\Setup Bootstrap\Log" -ForegroundColor Red
    exit 1
}
Write-Host "Servicio instalado: $($service.Status)" -ForegroundColor Green

Write-Host "3/4 Habilitando TCP/IP en el puerto 1433..." -ForegroundColor Cyan
$instanceKey = Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server" |
    Where-Object { $_.PSChildName -match "^MSSQL\d+\.SQLEXPRESS$" } |
    Select-Object -First 1 -ExpandProperty PSChildName

$tcpPath = "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\$instanceKey\MSSQLServer\SuperSocketNetLib\Tcp"
Set-ItemProperty -Path $tcpPath -Name "Enabled" -Value 1
Set-ItemProperty -Path "$tcpPath\IPAll" -Name "TcpDynamicPorts" -Value ""
Set-ItemProperty -Path "$tcpPath\IPAll" -Name "TcpPort" -Value "1433"

Restart-Service -Name "MSSQL`$SQLEXPRESS" -Force
Write-Host "TCP/IP habilitado y servicio reiniciado." -ForegroundColor Green

Write-Host "4/4 Instalando ODBC Driver 18 for SQL Server..." -ForegroundColor Cyan
winget install --id Microsoft.msodbcsql.18 --silent --accept-package-agreements --accept-source-agreements

Write-Host ""
Write-Host "Listo. Servidor: localhost\SQLEXPRESS (o localhost,1433), autenticacion de Windows." -ForegroundColor Yellow
Write-Host "Presiona Enter para cerrar." -ForegroundColor Yellow
Read-Host | Out-Null
