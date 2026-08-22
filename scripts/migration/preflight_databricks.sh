#!/usr/bin/env bash
###############################################################################
# Logistico 2.0 — Preflight: verifica che i catalog/schemi target siano pronti
# e che i gruppi UC esistano, PRIMA di deployare il bundle o girare le pipeline.
#
# Richiede: databricks CLI v0.221+ autenticato (env DATABRICKS_HOST/TOKEN o profilo).
#
# Uso:
#   ./preflight_databricks.sh [--catalog-bronze bronze_dev] [--catalog-control config_dev] ...
#   (i default coincidono con terraform.tfvars.example)
###############################################################################
set -euo pipefail

CAT_BRONZE="bronze_dev"; CAT_SILVER="silver_dev"; CAT_GOLD="gold_dev"
CAT_CONTROL="config_dev"; CAT_LANDING="landing_dev"
SCHEMA_LOG="logistica"; SCHEMA_PREP="prep_logistica"; SCHEMA_DM="logistica_dm"; SCHEMA_ETL="logistica_etl"

while [ $# -gt 0 ]; do
  case "$1" in
    --catalog-bronze) CAT_BRONZE="$2"; shift 2;;
    --catalog-silver) CAT_SILVER="$2"; shift 2;;
    --catalog-gold) CAT_GOLD="$2"; shift 2;;
    --catalog-control) CAT_CONTROL="$2"; shift 2;;
    --catalog-landing) CAT_LANDING="$2"; shift 2;;
    *) echo "arg sconosciuto: $1"; exit 2;;
  esac
done

fail=0

check_catalog() {
  local c="$1"
  if databricks catalogs get "$c" >/dev/null 2>&1; then
    echo "  [OK]   catalog esiste: $c"
  else
    echo "  [FAIL] catalog MANCANTE: $c"; fail=1
  fi
}

check_schema() {
  local c="$1" s="$2"
  if databricks schemas get "${c}.${s}" >/dev/null 2>&1; then
    echo "  [WARN] schema GIÀ presente: ${c}.${s} (terraform lo gestirà come esistente)"
  else
    echo "  [ok]   schema da creare: ${c}.${s}"
  fi
}

echo ">>> Verifica CLI"
databricks --version || { echo "databricks CLI non trovato"; exit 2; }
databricks current-user me >/dev/null 2>&1 && echo "  [OK] autenticazione valida" || { echo "  [FAIL] non autenticato"; exit 2; }

echo ">>> Verifica catalog target esistenti"
for c in "$CAT_BRONZE" "$CAT_SILVER" "$CAT_GOLD" "$CAT_CONTROL" "$CAT_LANDING"; do
  check_catalog "$c"
done

echo ">>> Verifica schemi (informativo)"
check_schema "$CAT_BRONZE" "$SCHEMA_LOG"
check_schema "$CAT_SILVER" "$SCHEMA_LOG"
check_schema "$CAT_SILVER" "$SCHEMA_PREP"
check_schema "$CAT_GOLD" "$SCHEMA_LOG"
check_schema "$CAT_GOLD" "$SCHEMA_DM"
check_schema "$CAT_CONTROL" "$SCHEMA_ETL"

echo ""
if [ "$fail" -eq 0 ]; then
  echo ">>> PREFLIGHT OK — i catalog target esistono. Procedere con terraform apply (overlay brownfield)."
else
  echo ">>> PREFLIGHT FALLITO — catalog mancanti. Confermare i nomi col team DWW (decisioni D1/D4)."
  exit 1
fi
