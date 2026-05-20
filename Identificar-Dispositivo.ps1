param(
    [Parameter(Mandatory)]
    [string]$IP
)

function Separador($titulo) {
    Write-Host ""
    Write-Host "── $titulo " -ForegroundColor Cyan -NoNewline
    Write-Host ("─" * [Math]::Max(0, 50 - $titulo.Length)) -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  Identificando dispositivo: $IP" -ForegroundColor Yellow
Write-Host ""

# ── 1. PING ──────────────────────────────────────────────────
Separador "PING"
$ping = Test-Connection -ComputerName $IP -Count 2 -Quiet
if ($ping) {
    $latencia = (Test-Connection -ComputerName $IP -Count 2 | Measure-Object -Property Latency -Average).Average
    Write-Host "  Responde al ping  (latencia media: $([Math]::Round($latencia,1)) ms)" -ForegroundColor Green
} else {
    Write-Host "  No responde al ping" -ForegroundColor Red
}

# ── 2. HOSTNAME / DNS ─────────────────────────────────────────
Separador "HOSTNAME / DNS"
try {
    $dns = [System.Net.Dns]::GetHostEntry($IP)
    Write-Host "  Hostname: $($dns.HostName)" -ForegroundColor Green
    if ($dns.Aliases) { Write-Host "  Aliases:  $($dns.Aliases -join ', ')" }
} catch {
    Write-Host "  Sin resolución DNS inversa" -ForegroundColor DarkYellow
}

# ── 3. MAC + FABRICANTE (ARP) ─────────────────────────────────
Separador "MAC / FABRICANTE (ARP)"
# Forzar entrada ARP con un ping previo
Test-Connection -ComputerName $IP -Count 1 -Quiet | Out-Null
$arpLinea = (arp -a $IP 2>$null) -join "`n"
if ($arpLinea -match '([0-9a-f]{2}[:-]){5}[0-9a-f]{2}') {
    $mac = $Matches[0]
    Write-Host "  MAC: $mac" -ForegroundColor Green
    # Lookup OUI (primeros 3 octetos)
    $oui = ($mac -replace '-',':').ToUpper().Substring(0,8)
    try {
        $vendor = Invoke-RestMethod -Uri "https://api.maclookup.app/v2/macs/$oui" -TimeoutSec 5
        if ($vendor.company) {
            Write-Host "  Fabricante: $($vendor.company)" -ForegroundColor Green
        } else {
            Write-Host "  Fabricante: desconocido (OUI: $oui)" -ForegroundColor DarkYellow
        }
    } catch {
        Write-Host "  Fabricante: no se pudo consultar OUI (sin internet o rate limit)" -ForegroundColor DarkYellow
    }
} else {
    Write-Host "  No hay entrada ARP (¿fuera de la misma subred?)" -ForegroundColor DarkYellow
}

# ── 4. PUERTOS COMUNES ────────────────────────────────────────
Separador "PUERTOS ABIERTOS"
$puertos = @{
    21   = "FTP"
    22   = "SSH"
    23   = "Telnet (legacy/IoT)"
    25   = "SMTP"
    53   = "DNS"
    80   = "HTTP"
    443  = "HTTPS"
    554  = "RTSP (cámara IP)"
    1883 = "MQTT (IoT)"
    3000 = "Panel web (Grafana/Node)"
    3389 = "RDP (Windows)"
    5000 = "Panel web genérico"
    5357 = "WS-Discovery (Windows)"
    8080 = "HTTP alternativo"
    8443 = "HTTPS alternativo"
    8883 = "MQTT/TLS"
    9100 = "Impresora (JetDirect)"
    49152 = "UPnP"
}

$abiertos = @()
foreach ($puerto in ($puertos.Keys | Sort-Object)) {
    $tcp = New-Object System.Net.Sockets.TcpClient
    try {
        $resultado = $tcp.BeginConnect($IP, $puerto, $null, $null)
        $ok = $resultado.AsyncWaitHandle.WaitOne(300)
        if ($ok -and $tcp.Connected) {
            $abiertos += $puerto
            Write-Host ("  {0,-6} abierto  — {1}" -f $puerto, $puertos[$puerto]) -ForegroundColor Green
        }
    } catch {}
    finally { $tcp.Close() }
}
if ($abiertos.Count -eq 0) {
    Write-Host "  Ningún puerto conocido responde" -ForegroundColor DarkYellow
}

# ── 5. PANEL WEB ──────────────────────────────────────────────
Separador "PANEL WEB"
$urlsPrueba = @("http://${IP}/", "http://${IP}:8080/", "https://${IP}/")
foreach ($url in $urlsPrueba) {
    try {
        $r = Invoke-WebRequest -Uri $url -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        Write-Host "  $url  →  $($r.StatusCode)" -ForegroundColor Green
        # Extraer título de la página
        if ($r.Content -match '<title[^>]*>([^<]+)</title>') {
            Write-Host "  Título: $($Matches[1].Trim())" -ForegroundColor Green
        }
        # Cabecera Server
        if ($r.Headers["Server"]) {
            Write-Host "  Server: $($r.Headers["Server"])" -ForegroundColor Green
        }
        if ($r.Headers["X-Powered-By"]) {
            Write-Host "  X-Powered-By: $($r.Headers["X-Powered-By"])" -ForegroundColor Green
        }
    } catch {
        Write-Host "  $url  →  sin respuesta" -ForegroundColor DarkGray
    }
}

# ── 6. mDNS / NBNS (NetBIOS) ──────────────────────────────────
Separador "NETBIOS (nombre en red Windows/Samba)"
try {
    $nb = nbtstat -A $IP 2>$null
    $nombre = $nb | Select-String '<00>' | Select-Object -First 1
    if ($nombre) {
        Write-Host "  $($nombre.ToString().Trim())" -ForegroundColor Green
    } else {
        Write-Host "  Sin nombre NetBIOS" -ForegroundColor DarkGray
    }
} catch {
    Write-Host "  nbtstat no disponible" -ForegroundColor DarkGray
}

# ── 7. UPnP ───────────────────────────────────────────────────
Separador "UPnP (descripción del dispositivo)"
$upnpUrls = @(
    "http://${IP}:1900/",
    "http://${IP}:49152/description.xml",
    "http://${IP}:49153/description.xml",
    "http://${IP}:49154/description.xml",
    "http://${IP}:8080/description.xml",
    "http://${IP}:80/description.xml"
)
$upnpEncontrado = $false
foreach ($url in $upnpUrls) {
    try {
        $r = Invoke-WebRequest -Uri $url -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        if ($r.Content -match '<friendlyName>([^<]+)</friendlyName>') {
            Write-Host "  friendlyName: $($Matches[1])" -ForegroundColor Green
            $upnpEncontrado = $true
        }
        if ($r.Content -match '<manufacturer>([^<]+)</manufacturer>') {
            Write-Host "  manufacturer: $($Matches[1])" -ForegroundColor Green
        }
        if ($r.Content -match '<modelName>([^<]+)</modelName>') {
            Write-Host "  modelName:    $($Matches[1])" -ForegroundColor Green
        }
        if ($upnpEncontrado) { break }
    } catch {}
}
if (-not $upnpEncontrado) {
    Write-Host "  Sin respuesta UPnP" -ForegroundColor DarkGray
}

# ── RESUMEN ───────────────────────────────────────────────────
Write-Host ""
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host "  Fin del análisis para $IP" -ForegroundColor Yellow
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host ""
