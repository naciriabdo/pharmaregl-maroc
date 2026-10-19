# installer.ps1 — Installe PharmaRégl Maroc sur Windows (lancé par INSTALLER.bat).
# Étapes : Python 3.12 -> environnement .venv -> bibliothèques -> clé Groq et mot de passe -> icône sur le Bureau.
$ErrorActionPreference = "Continue"
$racine = Split-Path -Parent $PSScriptRoot
Set-Location $racine
$Host.UI.RawUI.WindowTitle = "PharmaRégl Maroc — Installation"

function Titre($t)  { Write-Host ""; Write-Host "=== $t ===" -ForegroundColor Cyan }
function Ok($t)     { Write-Host "  OK  $t" -ForegroundColor Green }
function Info($t)   { Write-Host "  $t" -ForegroundColor Gray }
function Echec($t)  {
    Write-Host ""; Write-Host "ERREUR : $t" -ForegroundColor Red
    Write-Host "Faites une capture de cette fenêtre et envoyez-la." -ForegroundColor Yellow
    Read-Host "Appuyez sur Entrée pour fermer"; exit 1
}

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════╗" -ForegroundColor DarkCyan
Write-Host "  ║   PharmaRégl Maroc — installation             ║" -ForegroundColor DarkCyan
Write-Host "  ╚══════════════════════════════════════════════╝" -ForegroundColor DarkCyan

# Fichiers téléchargés depuis Internet : on retire le blocage de Windows
Get-ChildItem -Path $racine -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue

# Une ancienne version tourne peut-être encore : on l'arrête
$ecoute = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
foreach ($c in $ecoute) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue }

# ---------------------------------------------------------------- 1. Python 3.12
Titre "1/5  Python 3.12"
function Trouver-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 -c "import sys" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { return @{ Exe = "py"; Args = @("-3.12") } }
    }
    $chemins = @("$env:LOCALAPPDATA\Python\pythoncore-3.12-64\python.exe",
                 "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
                 "$env:ProgramFiles\Python312\python.exe")
    foreach ($c in $chemins) { if (Test-Path $c) { return @{ Exe = $c; Args = @() } } }
    return $null
}
$python = Trouver-Python
if (-not $python) {
    Info "Python 3.12 absent : installation automatique…"
    if (Get-Command py -ErrorAction SilentlyContinue) { & py install 3.12 }
    $python = Trouver-Python
}
if (-not $python -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
    $python = Trouver-Python
}
if (-not $python) { Echec "Python 3.12 n'a pas pu être installé. Installez-le depuis python.org (cochez « Add python.exe to PATH »), puis relancez INSTALLER.bat." }
Ok "Python 3.12 trouvé"

# ---------------------------------------------------------------- 2. Environnement .venv
Titre "2/5  Environnement Python du projet (.venv)"
$venvPy = Join-Path $racine ".venv\Scripts\python.exe"
if (Test-Path $venvPy) {
    & $venvPy -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)"
    if ($LASTEXITCODE -ne 0) { Info "Ancien environnement d'une autre version : recréation…"; Remove-Item -Recurse -Force (Join-Path $racine ".venv") }
}
if (-not (Test-Path $venvPy)) {
    $a = $python.Args
    & $python.Exe @a -m venv .venv
    if (-not (Test-Path $venvPy)) { Echec "création de l'environnement .venv impossible." }
}
Ok "Environnement prêt"

# ---------------------------------------------------------------- 3. Bibliothèques
Titre "3/5  Bibliothèques (quelques minutes la première fois)"
& $venvPy -m pip install --upgrade pip --disable-pip-version-check -q
& $venvPy -m pip install -r requirements.txt --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { Echec "installation des bibliothèques (vérifiez votre connexion Internet)." }
Ok "Bibliothèques installées"

# ---------------------------------------------------------------- 4. Clé Groq + mot de passe
Titre "4/5  Clé API Groq et mot de passe administrateur"
$secrets = Join-Path $racine ".streamlit\secrets.toml"
function Toml($t) { return '"' + ($t -replace '\\', '\\' -replace '"', '\"') + '"' }
function Ecrire-Utf8($chemin, $texte) { [System.IO.File]::WriteAllText($chemin, $texte, (New-Object System.Text.UTF8Encoding $false)) }
function Lire-MotDePasse {
    while ($true) {
        $s1 = Read-Host "  Choisissez le mot de passe administrateur (8 caractères minimum)" -AsSecureString
        $s2 = Read-Host "  Retapez-le pour confirmer" -AsSecureString
        $t1 = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s1))
        $t2 = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s2))
        if ($t1 -ne $t2) { Write-Host "  Les deux saisies sont différentes, recommencez." -ForegroundColor Yellow }
        elseif ($t1.Length -lt 8) { Write-Host "  Trop court (8 caractères minimum)." -ForegroundColor Yellow }
        else { return $t1 }
    }
}

if (Test-Path $secrets) {
    Ok "Fichier de secrets déjà présent : conservé"
    $contenu = [System.IO.File]::ReadAllText($secrets)
    if ($contenu -notmatch 'ADMIN_PASSWORD') {
        $mdp = Lire-MotDePasse
        Ecrire-Utf8 $secrets ($contenu.TrimEnd() + "`r`nADMIN_PASSWORD = " + (Toml $mdp) + "`r`n")
        Ok "Mot de passe administrateur ajouté"
    }
} else {
    $cle = ""
    # Une clé existe peut-être déjà dans l'ancien dossier du chatbot : on propose de la reprendre
    $dossiers = @([Environment]::GetFolderPath("Desktop"), "$env:USERPROFILE\Documents", "$env:USERPROFILE\Downloads") | Where-Object { Test-Path $_ }
    $anciens = Get-ChildItem -Path $dossiers -Filter "secrets.toml" -Recurse -Depth 5 -File -ErrorAction SilentlyContinue |
               Where-Object { $_.FullName -ne $secrets }
    foreach ($f in $anciens) {
        $m = [regex]::Match([System.IO.File]::ReadAllText($f.FullName), 'GROQ_API_KEY\s*=\s*"(gsk_[^"]+)"')
        if ($m.Success) {
            $k = $m.Groups[1].Value
            $rep = Read-Host ("  Clé Groq trouvée dans " + $f.DirectoryName + " (" + $k.Substring(0, 8) + "…). La réutiliser ? (O/n)")
            if ($rep -notmatch '^[nN]') { $cle = $k; break }
        }
    }
    if (-not $cle) {
        Info "Créez une clé gratuite sur https://console.groq.com/keys (elle commence par gsk_)."
        $cle = (Read-Host "  Collez votre clé Groq puis Entrée (laisser vide pour plus tard)").Trim()
    }
    $mdp = Lire-MotDePasse
    $texte = "# Secrets de PharmaRégl Maroc — ne jamais envoyer ce fichier sur GitHub`r`n"
    if ($cle) { $texte += "GROQ_API_KEY = " + (Toml $cle) + "`r`n" } else { $texte += "# GROQ_API_KEY = `"gsk_...`"`r`n" }
    $texte += "ADMIN_PASSWORD = " + (Toml $mdp) + "`r`n"
    Ecrire-Utf8 $secrets $texte
    Ok "Secrets enregistrés dans .streamlit\secrets.toml"
}

# ---------------------------------------------------------------- 5. Icône sur le Bureau
Titre "5/5  Icône « PharmaRégl Maroc » sur le Bureau et dans le menu Démarrer"
New-Item -ItemType Directory -Force (Join-Path $racine "data") | Out-Null
$ws = New-Object -ComObject WScript.Shell
$cibles = @([Environment]::GetFolderPath("Desktop"), (Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs"))
foreach ($d in $cibles) {
    $lnk = $ws.CreateShortcut((Join-Path $d "PharmaRégl Maroc.lnk"))
    $lnk.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    $lnk.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$racine\outils\lanceur.ps1`""
    $lnk.WorkingDirectory = $racine
    $lnk.IconLocation = "$racine\assets\pharmaregl.ico"
    $lnk.Description = "Assistant de réglementation pharmaceutique"
    $lnk.Save()
}
Ok "Icône créée"

Write-Host ""
Write-Host "  Installation terminée !" -ForegroundColor Green
Write-Host "  Double-cliquez sur l'icône PharmaRégl Maroc du Bureau pour ouvrir l'application."
Write-Host "  Espace administrateur : menu de gauche → « Espace administrateur »."
$rep = Read-Host "  Ouvrir l'application maintenant ? (O/n)"
if ($rep -notmatch '^[nN]') { & (Join-Path $PSScriptRoot "lanceur.ps1") }
