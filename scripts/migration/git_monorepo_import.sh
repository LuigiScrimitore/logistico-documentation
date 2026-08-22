#!/usr/bin/env bash
###############################################################################
# Logistico 2.0 — Import del repo logistico nel mono-repo del DWW (area logistico/)
#
# Strategia: git subtree, che PRESERVA la storia dei commit sotto il prefisso
# logistico/. In alternativa, per un import "pulito" senza storia, usare --squash.
#
# Prerequisiti:
#   - accesso in push al mono-repo del DWW
#   - il repo logistico raggiungibile come remote (path locale o URL)
#
# Uso:
#   ./git_monorepo_import.sh <URL_MONOREPO_DWW> <URL_O_PATH_REPO_LOGISTICO> [--squash]
#
# Esempio:
#   ./git_monorepo_import.sh git@gitlab:data-platform/dwh.git /c/PROGETTI/LOGISTICO --squash
#
# NB: script idempotente sul clone (usa una dir temp); NON esegue push automatico:
#     lascia un branch pronto per la Merge Request. Rivedere prima di pushare.
###############################################################################
set -euo pipefail

MONOREPO_URL="${1:?URL del mono-repo DWW richiesto}"
LOGISTICO_SRC="${2:?URL o path del repo logistico richiesto}"
SQUASH_FLAG="${3:-}"

PREFIX="logistico"
BRANCH="feat/import-logistico"
WORKDIR="$(mktemp -d)"
SUBTREE_REMOTE="logistico-src"

echo ">>> Clono il mono-repo DWW in $WORKDIR"
git clone "$MONOREPO_URL" "$WORKDIR/dwh"
cd "$WORKDIR/dwh"

DEFAULT_BRANCH="$(git symbolic-ref --short HEAD)"
echo ">>> Branch di default mono-repo: $DEFAULT_BRANCH"

git checkout -b "$BRANCH"

echo ">>> Aggiungo il repo logistico come remote temporaneo"
git remote add "$SUBTREE_REMOTE" "$LOGISTICO_SRC"
git fetch "$SUBTREE_REMOTE"

# Determina il branch sorgente (main o master)
SRC_BRANCH="main"
git ls-remote --exit-code --heads "$SUBTREE_REMOTE" main >/dev/null 2>&1 || SRC_BRANCH="master"
echo ">>> Branch sorgente logistico: $SRC_BRANCH"

if [ "$SQUASH_FLAG" = "--squash" ]; then
  echo ">>> Import SQUASH (senza storia) sotto $PREFIX/"
  git subtree add --prefix="$PREFIX" "$SUBTREE_REMOTE" "$SRC_BRANCH" --squash
else
  echo ">>> Import con STORIA COMPLETA sotto $PREFIX/"
  git subtree add --prefix="$PREFIX" "$SUBTREE_REMOTE" "$SRC_BRANCH"
fi

git remote remove "$SUBTREE_REMOTE"

cat <<EOF

============================================================================
Import completato nel branch '$BRANCH' del clone in:
  $WORKDIR/dwh

PROSSIMI PASSI (manuali, da rivedere prima):
  cd $WORKDIR/dwh
  # verifica struttura
  ls $PREFIX/
  # eventuale spostamento file specifici / cleanup .gitlab-ci se in conflitto
  git push origin $BRANCH
  # poi aprire la Merge Request verso $DEFAULT_BRANCH

Per aggiornamenti successivi (sync da repo logistico standalone):
  git subtree pull --prefix=$PREFIX <URL_REPO_LOGISTICO> $SRC_BRANCH ${SQUASH_FLAG:+--squash}
============================================================================
EOF
