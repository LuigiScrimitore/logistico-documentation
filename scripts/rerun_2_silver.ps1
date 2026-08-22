# FASE 2/3 — SILVER (legge i bronze a 22 siti gia' caricati dalla fase 1).
# Lancia DOPO rerun_1_bronze.ps1:
#   cd C:\PROGETTI\LOGISTICO ; .\scripts\rerun_2_silver.ps1

$RUNDATE = "2026-06-16"
$LOG = "C:\PROGETTI\LOGISTICO\DOCS\exec\rerun_silver_22siti.txt"
New-Item -ItemType Directory -Force -Path (Split-Path $LOG) | Out-Null

$state = docker inspect -f '{{.State.Running}}' logistico-spark 2>$null
if ($state -ne 'true') { Write-Host "Avvio container..."; docker start logistico-spark | Out-Null; Start-Sleep 8 }

Write-Host "FASE SILVER start $(Get-Date -Format HH:mm:ss)" -ForegroundColor Cyan
docker exec logistico-spark bash -c "cd /workspace/code && python tests/local_bronze/run_all_silver.py --run-date $RUNDATE" *>&1 | Tee-Object -FilePath $LOG
Write-Host "FASE SILVER end $(Get-Date -Format HH:mm:ss) -> $LOG" -ForegroundColor Green
Write-Host "Poi lancia rerun_3_gold.ps1" -ForegroundColor Yellow
