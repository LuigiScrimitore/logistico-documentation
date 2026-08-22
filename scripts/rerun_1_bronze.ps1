# FASE 1/3 — BRONZE a 22 siti (runner fixato, default = 22 siti, commit 9b4c491).
# Landing gia' completa (22 siti): nessuna ri-estrazione Oracle.
# Lancia da PowerShell normale con Docker Desktop avviato:
#   cd C:\PROGETTI\LOGISTICO ; .\scripts\rerun_1_bronze.ps1

$RUNDATE = "2026-06-16"
$LOG = "C:\PROGETTI\LOGISTICO\DOCS\exec\rerun_bronze_22siti.txt"
New-Item -ItemType Directory -Force -Path (Split-Path $LOG) | Out-Null

$state = docker inspect -f '{{.State.Running}}' logistico-spark 2>$null
if ($state -ne 'true') { Write-Host "Avvio container..."; docker start logistico-spark | Out-Null; Start-Sleep 8 }

Write-Host "FASE BRONZE start $(Get-Date -Format HH:mm:ss)" -ForegroundColor Cyan
docker exec logistico-spark bash -c "cd /workspace/code && python tests/local_bronze/run_all_bronze.py --run-date $RUNDATE" *>&1 | Tee-Object -FilePath $LOG
Write-Host "FASE BRONZE end $(Get-Date -Format HH:mm:ss) -> $LOG" -ForegroundColor Green
Write-Host "Controlla l'header del log: deve dire '22 siti'. Poi lancia rerun_2_silver.ps1" -ForegroundColor Yellow
