#!/usr/bin/env bash
# extract_and_send.sh - estrae da Oracle sul relay e invia alla landing Azure via AzCopy.
# Area: OP-INF-4 / ACT_OP-INF-4 (variante: extract+send entrambi sul relay odisrvcno3).
#
# Flusso: Oracle --(oracledb thin)--> staging/<env>/<sistema>/<sorgente>-landing/... --(upload_landing.sh -> AzCopy)--> logisticolanding
#
# ESECUZIONE: va lanciato dall'utente che possiede la staging e puo' leggere il SAS
#   (tipicamente svc_landing). Lo step di send riusa upload_landing.sh (che legge il SAS 600).
#
# USO:
#   extract_and_send.sh [env] [sistema] [run_date]
#   es.  extract_and_send.sh dev logistico 2026-09-22
#   (run_date OMESSO = giorno di esecuzione)
# Variabili opzionali (override):
#   SYSTEMS=logistix,stat,cdt_estr,track   sistemi del main extractor
#   DO_CDTDW=1                              estrai anche anagrafiche CDT_DW (0 per saltare)
#   DRYRUN=1                                estrazione in --dry-run + NON invia (prova sicura)
#   APP_DIR / VENV_PY / ENV_FILE / STAGING / SENDER / LOG_DIR / RECAP_LOG / RUN_DIR
#
# LOG:
#   - log completo del run : $RUN_DIR/extract_send_<ts>.log
#   - recap per esecuzione : $RECAP_LOG  (un blocco appeso ad ogni run, OK o KO)
set -uo pipefail   # NON -e: gli errori li gestiamo noi per scrivere sempre il recap

ENV="${1:-dev}"
SISTEMA="${2:-logistico}"
RUN_DATE="${3:-$(date +%F)}"

SYSTEMS="${SYSTEMS:-logistix,stat,cdt_estr,track}"
DO_CDTDW="${DO_CDTDW:-1}"
DRYRUN="${DRYRUN:-0}"

APP_DIR="${APP_DIR:-/opt/landing/app}"
VENV_PY="${VENV_PY:-/opt/landing/venv/bin/python}"
ENV_FILE="${ENV_FILE:-/opt/landing/conf/${ENV}/${SISTEMA}.oracle.env}"
STAGING="${STAGING:-/data/landing/staging/${ENV}/${SISTEMA}}"
SENDER="${SENDER:-/opt/landing/bin/upload_landing.sh}"
LOG_DIR="${LOG_DIR:-/var/log/landing}"
RUN_DIR="${RUN_DIR:-${LOG_DIR}/runs}"
RECAP_LOG="${RECAP_LOG:-${LOG_DIR}/extract_send_recap.log}"

EXTRACT_MAIN="${APP_DIR}/scripts/landing_simulator/extract_oracle_to_landing.py"
EXTRACT_CDTDW="${APP_DIR}/scripts/cdtdw_lookup_extractor/extract_cdtdw_lookups.py"

RUN_TS="$(date '+%Y-%m-%d %H:%M:%S')"
TS_TAG="$(date '+%Y%m%d_%H%M%S')"
mkdir -p "$RUN_DIR" "$LOG_DIR" 2>/dev/null || true
RUN_LOG="${RUN_DIR}/extract_send_${TS_TAG}.log"

ts(){ date '+%Y-%m-%d %H:%M:%S'; }
log(){ echo "[$(ts)] $*"; }
die(){ echo "[$(ts)] ERRORE: $*" >&2; exit 2; }

# ---- Corpo del run (output catturato su RUN_LOG via tee) ----
run_all(){
  # Validazione token (anti path-traversal)
  echo "$ENV"      | grep -qE '^[a-z0-9-]+$'            || die "env non valido: $ENV"
  echo "$SISTEMA"  | grep -qE '^[a-z0-9-]+$'            || die "sistema non valido: $SISTEMA"
  echo "$RUN_DATE" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' || die "run_date non valido: $RUN_DATE"

  # Pre-flight
  [ -x "$VENV_PY" ]      || die "venv python mancante o non eseguibile: $VENV_PY"
  [ -r "$ENV_FILE" ]     || die "env Oracle non leggibile: $ENV_FILE"
  [ -f "$EXTRACT_MAIN" ] || die "estrattore principale mancante: $EXTRACT_MAIN"
  [ "$DRYRUN" = "1" ] || [ -x "$SENDER" ] || die "sender mancante: $SENDER"
  mkdir -p "$STAGING" 2>/dev/null || true

  # Credenziali Oracle nell'ambiente
  set -a; . "$ENV_FILE"; set +a
  : "${ORACLE_HOST:?manca ORACLE_HOST nel env file}"
  : "${ORACLE_SERVICE:?manca ORACLE_SERVICE}"
  : "${ORACLE_USER:?manca ORACLE_USER}"
  : "${ORACLE_PASSWORD:?manca ORACLE_PASSWORD}"

  local DRY_FLAG=""; [ "$DRYRUN" = "1" ] && DRY_FLAG="--dry-run"
  log "START env=$ENV sistema=$SISTEMA run_date=$RUN_DATE systems=$SYSTEMS cdtdw=$DO_CDTDW dryrun=$DRYRUN"
  log "staging=$STAGING"

  # 1) Estrazione principale
  local t0=$SECONDS
  log "Estrazione principale (systems=$SYSTEMS)..."
  "$VENV_PY" "$EXTRACT_MAIN" \
    --systems "$SYSTEMS" --run-date "$RUN_DATE" --output-dir "$STAGING" $DRY_FLAG || die "estrazione principale fallita"

  # 2) Estrazione anagrafiche CDT_DW (opzionale)
  if [ "$DO_CDTDW" = "1" ]; then
    if [ -f "$EXTRACT_CDTDW" ]; then
      if [ "$DRYRUN" = "1" ]; then
        log "  (dryrun: salto cdtdw, non ha --dry-run)"
      else
        log "Estrazione anagrafiche CDT_DW..."
        "$VENV_PY" "$EXTRACT_CDTDW" \
          --run-date "$RUN_DATE" --output-dir "$STAGING" --env-file "$ENV_FILE" || die "estrazione CDT_DW fallita"
      fi
    else
      log "  cdtdw extractor assente ($EXTRACT_CDTDW): salto."
    fi
  fi
  echo "EXTRACT_SECONDS=$((SECONDS - t0))"

  # 3) Invio AzCopy
  if [ "$DRYRUN" = "1" ]; then
    log "DRYRUN: estrazione simulata, NESSUN invio."
    return 0
  fi
  local t1=$SECONDS
  log "Invio AzCopy ($ENV $SISTEMA) via $SENDER ..."
  "$SENDER" "$ENV" "$SISTEMA" || die "invio AzCopy fallito"
  echo "UPLOAD_SECONDS=$((SECONDS - t1))"
  log "DONE extract&send env=$ENV sistema=$SISTEMA run_date=$RUN_DATE"
}

# ---- Esegui tutto: output a schermo + su RUN_LOG ----
SECONDS=0
run_all 2>&1 | tee "$RUN_LOG"
rc=${PIPESTATUS[0]}
TOTAL_S=$SECONDS
STATUS="OK"; [ "$rc" -eq 0 ] || STATUS="KO(rc=$rc)"

# ---- Parsing per il recap ----
field(){ grep -m1 -F "$1" "$RUN_LOG" 2>/dev/null | sed "s/.*$2//" | tr -d '\r'; }
extract_sum="$(grep -m1 'Riepilogo:' "$RUN_LOG" 2>/dev/null | sed 's/.*Riepilogo: *//' | tr -d '\r')"
az_status="$(grep -m1 'Final Job Status' "$RUN_LOG" 2>/dev/null | awk -F': ' '{print $2}' | tr -d '\r')"
az_files="$(grep -m1 'Number of File Transfers Completed' "$RUN_LOG" 2>/dev/null | awk -F': ' '{print $2}' | tr -d '\r')"
az_failed="$(grep -m1 'Number of File Transfers Failed' "$RUN_LOG" 2>/dev/null | awk -F': ' '{print $2}' | tr -d '\r')"
az_bytes="$(grep -m1 'Total Number of Bytes Transferred' "$RUN_LOG" 2>/dev/null | awk -F': ' '{print $2}' | tr -d '\r')"
ex_s="$(grep -m1 'EXTRACT_SECONDS=' "$RUN_LOG" 2>/dev/null | cut -d= -f2 | tr -d '\r')"
up_s="$(grep -m1 'UPLOAD_SECONDS='  "$RUN_LOG" 2>/dev/null | cut -d= -f2 | tr -d '\r')"
staged_files="$(find "$STAGING" -type f 2>/dev/null | wc -l | tr -d ' ')"
staged_size="$(du -sh "$STAGING" 2>/dev/null | cut -f1)"
# bytes -> GB leggibili
az_gb=""; [ -n "${az_bytes:-}" ] && az_gb="$(awk -v b="$az_bytes" 'BEGIN{if(b>0)printf "%.2f GB", b/1073741824}')"

# ---- Scrivi il recap (append) + a schermo/journald ----
{
  echo "================= EXTRACT+SEND RECAP ================="
  echo "run_ts   : $RUN_TS"
  echo "env/sist : $ENV/$SISTEMA   run_date: $RUN_DATE   dryrun: $DRYRUN"
  echo "systems  : $SYSTEMS   cdtdw: $DO_CDTDW"
  echo "extract  : ${extract_sum:-n/d}   (${ex_s:-?}s)"
  echo "staging  : ${staged_files} file totali, ${staged_size:-?} (cumulativo, in $STAGING)"
  if [ "$DRYRUN" = "1" ]; then
    echo "upload   : (dryrun - nessun invio)"
  else
    echo "upload   : ${az_status:-n/d} | file=${az_files:-?} failed=${az_failed:-?} | ${az_gb:-?}   (${up_s:-?}s)"
  fi
  echo "status   : $STATUS   (durata totale: ${TOTAL_S}s)"
  echo "run_log  : $RUN_LOG"
  echo "====================================================="
} | tee -a "$RECAP_LOG"

exit "$rc"
