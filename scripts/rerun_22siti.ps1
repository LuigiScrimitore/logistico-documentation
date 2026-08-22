# ─────────────────────────────────────────────────────────────────────────────
# Re-run completo pipeline a 22 siti (bronze -> silver -> gold) sul giorno 16/06.
# Usa il runner fixato (run_all_bronze default = 22 siti, commit 9b4c491).
#
# Landing gia' completa (22 siti estratti il 16/06): NON serve ri-estrarre da Oracle.
#
# Fasi in sessioni docker exec SEPARATE per evitare il SIGKILL da accumulo memoria (OP-36).
# Log catturati in DOCS\exec\ con suffisso _22siti.
#
# Lancia da PowerShell normale (NON admin), con Docker Desktop avviato:
#   cd C:\PROGETTI\LOGISTICO ; .\scripts\rerun_22siti.ps1
# ─────────────────────────────────────────────────────────────────────────────

$RUNDATE = "2026-06-16"
$EXEC    = "C:\PROGETTI\LOGISTICO\DOCS\exec"
New-Item -ItemType Directory -Force -Path $EXEC | Out-Null

function Run-Phase($name, $cmd) {
    Write-Host "`n==================== FASE $name (start $(Get-Date -Format HH:mm:ss)) ====================" -ForegroundColor Cyan
    $log = Join-Path $EXEC "rerun_${name}_22siti.txt"
    docker exec logistico-spark bash -c $cmd *>&1 | Tee-Object -FilePath $log
    Write-Host "==================== FASE $name (end $(Get-Date -Format HH:mm:ss)) -> $log ====================" -ForegroundColor Green
}

# 0. Verifica container attivo
$state = docker inspect -f '{{.State.Running}}' logistico-spark 2>$null
if ($state -ne 'true') { Write-Host "Avvio container..."; docker start logistico-spark | Out-Null; Start-Sleep 8 }

# 1. BRONZE — 22 siti (default del runner fixato). Sessione dedicata.
Run-Phase "bronze" "cd /workspace/code && python tests/local_bronze/run_all_bronze.py --run-date $RUNDATE"

# 2. SILVER — sessione dedicata (legge i bronze a 22 siti).
Run-Phase "silver" "cd /workspace/code && python tests/local_bronze/run_all_silver.py --run-date $RUNDATE"

# 3. GOLD — sessione dedicata (i log gold contengono gli orphan_rate dei fatti).
Run-Phase "gold" "cd /workspace/code && python tests/local_bronze/run_all_gold.py --run-date $RUNDATE"

# 4. Diagnostiche orphan (riepilogo sintetico SITO + operatori).
Run-Phase "diag_sito"  "cd /workspace/code && python tests/local_bronze/diag_lusito_vals.py"
Run-Phase "diag_op28"  "cd /workspace/code && python tests/local_bronze/diag_op28.py"

Write-Host "`nFATTO. Log in $EXEC (rerun_bronze/silver/gold/diag_*_22siti.txt)." -ForegroundColor Yellow
Write-Host "Mandami i 3 report e i 2 diag per la verifica orphan." -ForegroundColor Yellow
