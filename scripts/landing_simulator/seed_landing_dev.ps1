<#
.SYNOPSIS
  Seed manuale della landing DEV (workaround pre-AzCopy): estrai la fotografia del giorno
  in locale -> copiala sul Volume UC DEV -> archivia lo snapshot in zip -> svuota lo stage.
  Runbook: DOCS/main/17_runbook_seed_landing_manuale.md

.DESCRIPTION
  Ciclo giornaliero in un comando. Lo "stage" e' una cartella di lavoro effimera (solo il
  giorno corrente); il Volume DEV accumula la storia; ogni giorno viene archiviato in
  landing_archive\snap_YYYYMMDD.zip (ricaricabile se si ripulisce Azure).

  CDT_DW resta SOLO bridge lookup (OP-02) + quadratura, non una sorgente (cdtdw-non-e-sorgente).

.EXAMPLE
  # fotografia di oggi, fetta minima (un sito + poche tabelle):
  .\seed_landing_dev.ps1 -Sites lgcx -Tables sto_tes_carichi,sto_righe_carico,pesate,tabgen

.EXAMPLE
  # ri-seed su Azure da un archivio (nessuna estrazione):
  .\seed_landing_dev.ps1 -ReseedZip C:\PROGETTI\LOGISTICO_DATA\landing_archive\snap_20260901.zip

.NOTES
  Prerequisiti: py -3 con accesso Oracle (.env degli extractor); Databricks CLI configurata
  (databricks configure --token). Da lanciare sulla macchina dell'utente (auth personale, PAT).
#>
[CmdletBinding()]
param(
  [string]$RunDate    = (Get-Date).ToString('yyyy-MM-dd'),
  [string]$FromDate   = "",                 # default = RunDate (fotografia singolo giorno)
  [string]$Systems    = "logistix,stat",    # operativi. Aggiungi 'cdt_estr' per l'export quadratura (pesante)
  [string]$Sites      = "",                 # es. "lgcx" ; vuoto = tutti i siti da config
  [string]$Tables     = "",                 # es. "sto_tes_carichi,pesate,tabgen" ; vuoto = tutte
  [string]$RepoRoot   = "C:\PROGETTI\LOGISTICO",
  [string]$Stage      = "C:\PROGETTI\LOGISTICO_DATA\landing_stage",
  [string]$Archive    = "C:\PROGETTI\LOGISTICO_DATA\landing_archive",
  [string]$VolumeRoot = "dbfs:/Volumes/landing_dev/logistica/files",
  [switch]$SkipCdtdw,                        # salta l'extractor lookup CDT_DW (cambiano lente)
  [switch]$NoCopy,                           # estrai+archivia ma non copiare sul Volume
  [switch]$KeepStage,                        # non svuotare lo stage a fine run
  [switch]$NoArchive,                        # non creare lo zip di archivio
  [string]$ReseedZip  = "",                  # ri-seed sul Volume da questo zip (salta l'estrazione)
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
function Info($m){ Write-Host "[seed] $m" -ForegroundColor Cyan }
function Warn($m){ Write-Host "[seed] $m" -ForegroundColor Yellow }
if (-not $FromDate) { $FromDate = $RunDate }
$dateCompact = $RunDate -replace '-',''
$oraDir = Join-Path $RepoRoot 'scripts\landing_simulator'
$cdtDir = Join-Path $RepoRoot 'scripts\cdtdw_lookup_extractor'

# --- pre-check CLI (se dovremo copiare)
if (-not $NoCopy -and -not (Get-Command databricks -ErrorAction SilentlyContinue)) {
  throw "Databricks CLI non trovata. Installa (winget install Databricks.DatabricksCLI) e configura (databricks configure --token). Vedi runbook 17."
}

function Copy-SourcesToVolume([string]$root) {
  $sources = Get-ChildItem -Path $root -Directory -Filter '*-landing' -ErrorAction SilentlyContinue
  if (-not $sources) { Warn "nessuna cartella *-landing in $root : niente da copiare."; return }
  foreach ($s in $sources) {
    $dst = "$VolumeRoot/$($s.Name)"
    if ($DryRun) { Write-Host "DRYRUN> databricks fs cp --recursive --overwrite `"$($s.FullName)`" `"$dst`"" -ForegroundColor DarkGray; continue }
    Info "copia $($s.Name) -> $dst"
    & databricks fs cp --recursive --overwrite "$($s.FullName)" "$dst"
    if ($LASTEXITCODE -ne 0) { throw "fs cp fallito per $($s.Name) (exit $LASTEXITCODE)" }
  }
}

# ============ MODALITA' RE-SEED (da zip, nessuna estrazione) ============
if ($ReseedZip) {
  if (-not (Test-Path $ReseedZip)) { throw "archivio non trovato: $ReseedZip" }
  $tmp = Join-Path $Stage "_reseed"
  Info "re-seed da $ReseedZip"
  if (-not $DryRun) {
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    Expand-Archive -Path $ReseedZip -DestinationPath $tmp -Force
  }
  Copy-SourcesToVolume $tmp
  if (-not $DryRun -and -not $KeepStage) { Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue }
  Info "RE-SEED completato."
  return
}

# ============ 1) STAGE PULITO ============
Info "run_date=$RunDate (from=$FromDate) | stage=$Stage"
if (-not $DryRun) {
  New-Item -ItemType Directory -Force -Path $Stage | Out-Null
  Remove-Item -Recurse -Force "$Stage\*" -ErrorAction SilentlyContinue
}

# ============ 2) ESTRAZIONE OPERATIVI (Logistix/STAT[/cdt_estr]) ============
$oraArgs = @('-3','extract_oracle_to_landing.py','--run-date',$RunDate,'--from-date',$FromDate,'--to-date',$RunDate,'--output-dir',$Stage,'--query-timeout','3600')
if ($Systems) { $oraArgs += @('--systems',$Systems) }
if ($Sites)   { $oraArgs += @('--sites',$Sites) }
if ($Tables)  { $oraArgs += @('--tables',$Tables) }
Push-Location $oraDir
try {
  if ($DryRun) { Write-Host "DRYRUN> py $($oraArgs -join ' ')" -ForegroundColor DarkGray }
  else { Info "estrazione operativi ($Systems)..."; & py @oraArgs; if ($LASTEXITCODE -ne 0) { throw "extract_oracle_to_landing fallito (exit $LASTEXITCODE)" } }
} finally { Pop-Location }

# ============ 3) ESTRAZIONE LOOKUP CDT_DW (bridge OP-02) ============
if (-not $SkipCdtdw) {
  $cdtArgs = @('-3','extract_cdtdw_lookups.py','--run-date',$RunDate,'--output-dir',$Stage)
  if ($Tables) { $cdtArgs += @('--tables',$Tables) }
  Push-Location $cdtDir
  try {
    if ($DryRun) { Write-Host "DRYRUN> py $($cdtArgs -join ' ')" -ForegroundColor DarkGray }
    else { Info "estrazione lookup CDT_DW (bridge OP-02)..."; & py @cdtArgs; if ($LASTEXITCODE -ne 0) { throw "extract_cdtdw_lookups fallito (exit $LASTEXITCODE)" } }
  } finally { Pop-Location }
} else { Warn "salto estrazione CDT_DW (-SkipCdtdw)" }

# ============ 4) COPIA SUL VOLUME DEV ============
if (-not $NoCopy) { Copy-SourcesToVolume $Stage } else { Warn "salto copia sul Volume (-NoCopy)" }

# ============ 5) ARCHIVIO ZIP DELLO SNAPSHOT ============
if (-not $NoArchive -and -not $DryRun) {
  New-Item -ItemType Directory -Force -Path $Archive | Out-Null
  $zip = Join-Path $Archive "snap_$dateCompact.zip"
  if (Test-Path $zip) { Remove-Item -Force $zip }
  if (Get-ChildItem -Path $Stage -Force -ErrorAction SilentlyContinue) {
    Compress-Archive -Path "$Stage\*" -DestinationPath $zip -Force
    Info "archivio: $zip ($([math]::Round((Get-Item $zip).Length/1MB,1)) MB)"
  } else { Warn "stage vuoto: nessun archivio creato." }
}

# ============ 6) PULIZIA STAGE ============
if (-not $KeepStage -and -not $DryRun) { Remove-Item -Recurse -Force "$Stage\*" -ErrorAction SilentlyContinue; Info "stage svuotato." }

Info "FATTO (run_date=$RunDate)."
Info "Prossimo: lancia i job DEV (logistica_dim_refresh -> logistica_carichi) con landing_base_path=/Volumes/landing_dev/logistica/files, run_date=$RunDate."
