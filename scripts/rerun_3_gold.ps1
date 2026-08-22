# FASE 3/3 — GOLD (legge i silver gia' costruiti dalla fase 2).
# I log gold contengono gli orphan_rate dei fatti (SITO/AREA/OPERATORE/PREPARATORE).
# Lancia DOPO rerun_2_silver.ps1:
#   cd C:\PROGETTI\LOGISTICO ; .\scripts\rerun_3_gold.ps1

$RUNDATE = "2026-06-16"
$LOG = "C:\PROGETTI\LOGISTICO\DOCS\exec\rerun_gold_22siti.txt"
New-Item -ItemType Directory -Force -Path (Split-Path $LOG) | Out-Null

$state = docker inspect -f '{{.State.Running}}' logistico-spark 2>$null
if ($state -ne 'true') { Write-Host "Avvio container..."; docker start logistico-spark | Out-Null; Start-Sleep 8 }

Write-Host "FASE GOLD start $(Get-Date -Format HH:mm:ss)" -ForegroundColor Cyan
docker exec logistico-spark bash -c "cd /workspace/code && python tests/local_bronze/run_all_gold.py --run-date $RUNDATE" *>&1 | Tee-Object -FilePath $LOG
Write-Host "FASE GOLD end $(Get-Date -Format HH:mm:ss) -> $LOG" -ForegroundColor Green
Write-Host "Mandami rerun_bronze/silver/gold_22siti.txt per la verifica orphan." -ForegroundColor Yellow
