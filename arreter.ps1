# arreter.ps1 — Arrête le serveur de PharmaRégl Maroc (libère la mémoire de l'ordinateur).
Add-Type -AssemblyName PresentationFramework
$ecoute = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
foreach ($c in $ecoute) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue }
[System.Windows.MessageBox]::Show("PharmaRégl Maroc est arrêté.", "PharmaRégl Maroc") | Out-Null
