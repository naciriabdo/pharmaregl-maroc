# lanceur.ps1 — Ouvre PharmaRégl Maroc comme une application (icône du Bureau).
# 1) démarre le serveur en arrière-plan (fenêtre cachée) s'il ne tourne pas déjà ;
# 2) ouvre l'application dans sa propre fenêtre (Edge ou Chrome en mode « application »).
$ErrorActionPreference = "Continue"
$racine = Split-Path -Parent $PSScriptRoot
Set-Location $racine
$url = "http://localhost:8501"
Add-Type -AssemblyName PresentationFramework

function Pret {
    try { return ((Invoke-WebRequest "$url/_stcore/health" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) }
    catch { return $false }
}

if (-not (Pret)) {
    $py = Join-Path $racine ".venv\Scripts\python.exe"
    if (-not (Test-Path $py)) {
        [System.Windows.MessageBox]::Show("L'installation n'est pas faite : double-cliquez d'abord sur INSTALLER.bat.", "PharmaRégl Maroc") | Out-Null
        exit 1
    }
    New-Item -ItemType Directory -Force (Join-Path $racine "data") | Out-Null
    Start-Process -FilePath $py -WorkingDirectory $racine -WindowStyle Hidden `
        -ArgumentList @("-m", "streamlit", "run", "app.py", "--server.headless", "true", "--server.port", "8501") `
        -RedirectStandardOutput (Join-Path $racine "data\journal.txt") -RedirectStandardError (Join-Path $racine "data\erreurs.txt")
    $t = 0
    while (-not (Pret) -and $t -lt 120) { Start-Sleep -Seconds 1; $t++ }
    if (-not (Pret)) {
        [System.Windows.MessageBox]::Show("Le serveur n'a pas démarré. Consultez le fichier data\erreurs.txt du dossier de l'application.", "PharmaRégl Maroc") | Out-Null
        exit 1
    }
}

$navigateurs = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
                 "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
                 "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
                 "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
                 "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe")
$nav = $navigateurs | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($nav) { Start-Process -FilePath $nav -ArgumentList "--app=$url" } else { Start-Process $url }
