#!/usr/bin/env bash
# upload_landing.sh — invia la staging di UN (<env>, <sistema>) ad Azure Blob via AzCopy.
# Host: relay Linux odisrvcno3 (Ubuntu 26.04). Eseguito come utente svc_landing,
# invocato via ssh **forced command** dagli agenti ODI (odisrvcno1/odisrvcno2):
# env e sistema arrivano in $SSH_ORIGINAL_COMMAND (es. "dev logistico"); per il test
# manuale si passano come argomenti: upload_landing.sh <env> <sistema>.
#
# Convenzione path (OP-INF-4 / OP-07):
#   /data/landing/staging/<env>/<sistema>/<sorgente>-landing/<tabella>/YYYY/MM/DD/<file>
# I livelli <env>/<sistema>/ instradano verso il container giusto e NON finiscono nel
# container (si copia il CONTENUTO di staging/<env>/<sistema>/).
#
# Mappa (env,sistema) -> destinazione: /opt/landing/conf/<env>/<sistema>.conf (DEST_BASE + SAS_FILE).
# Aggiungere un ambiente/sistema = nuova sub-folder staging + nuovo conf. Nessuna modifica qui.
#
# Decisione: OP-INF-4 / ADR-0023 (trasporto AzCopy). Trasparente per la pipeline.
set -euo pipefail

STAGING_ROOT="/data/landing/staging"
CONF_DIR="/opt/landing/conf"
LOG_ROOT="/var/log/landing"

export AZCOPY_LOG_LOCATION="$LOG_ROOT"
export AZCOPY_JOB_PLAN_LOCATION="$LOG_ROOT/plans"

# 1) env + sistema: da forced command, oppure dagli argomenti per test manuale.
if [ -n "${SSH_ORIGINAL_COMMAND:-}" ]; then
  set -f                                   # niente glob durante lo split dei token
  # shellcheck disable=SC2086
  set -- $SSH_ORIGINAL_COMMAND
  set +f
fi
ENV="${1:-}"
SISTEMA="${2:-}"
# 2) validazione rigida: niente path traversal / injection (solo [a-z0-9-]).
[[ "$ENV"     =~ ^[a-z0-9-]+$ ]] || { echo "ERRORE: env non valido: '$ENV'" >&2; exit 2; }
[[ "$SISTEMA" =~ ^[a-z0-9-]+$ ]] || { echo "ERRORE: sistema non valido: '$SISTEMA'" >&2; exit 2; }

CONF="$CONF_DIR/$ENV/$SISTEMA.conf"
[ -r "$CONF" ] || { echo "ERRORE: conf mancante per '$ENV/$SISTEMA': $CONF" >&2; exit 2; }
DEST_BASE=""; SAS_FILE=""
# shellcheck source=/dev/null
. "$CONF"
: "${DEST_BASE:?DEST_BASE non definito in $CONF}"
: "${SAS_FILE:?SAS_FILE non definito in $CONF}"

SRC="$STAGING_ROOT/$ENV/$SISTEMA/"
[ -d "$SRC" ]       || { echo "ERRORE: staging assente: $SRC" >&2; exit 2; }
[ -r "$SAS_FILE" ]  || { echo "ERRORE: SAS non leggibile: $SAS_FILE" >&2; exit 2; }

# "${SRC}*": AzCopy copia il CONTENUTO della cartella (niente prefisso <env>/<sistema>/ nel
# container). --overwrite=ifSourceNewer = idempotente (richiede permesso Read nel SAS).
azcopy copy "${SRC}*" "${DEST_BASE}$(cat "$SAS_FILE")" \
  --recursive --overwrite=ifSourceNewer --log-level=INFO

echo "$(date -Is) [$ENV/$SISTEMA] upload OK" >> "$LOG_ROOT/upload.log"
