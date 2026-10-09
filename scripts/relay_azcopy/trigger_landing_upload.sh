#!/bin/bash
# trigger_landing_upload.sh — lanciato da ODI (OdiOSCommand) sugli agenti odisrvcno1/odisrvcno2
# (in balance). Fa partire l'invio della landing di (<env>,<sistema>) verso Azure chiamando, via
# ssh, lo script sul relay odisrvcno3. Grazie al forced command lato relay, qualunque stringa
# passiamo come "comando" fa partire SOLO /opt/landing/bin/upload_landing.sh; noi passiamo
# "<env> <sistema>", che il relay legge da $SSH_ORIGINAL_COMMAND.
#
# Deploy: identico su entrambi gli agenti, come utente oracle (chiave ~oracle/.ssh/id_rsa_landing
# e host key del relay già in ~oracle/.ssh/known_hosts). Vedi scripts/relay_azcopy/README.md.
#
# Uso (in ODI, Technology=OS Command):  /home/oracle/bin/trigger_landing_upload.sh dev logistico
# Exit code: propagato dal relay (azcopy != 0 -> questo script != 0 -> ODI vede il fallimento).
set -eu

ENV="${1:-dev}"
SISTEMA="${2:-logistico}"

RELAY_USER="svc_landing"
RELAY_HOST="10.8.1.158"               # odisrvcno3
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa_landing}"
KNOWN_HOSTS="${KNOWN_HOSTS:-$HOME/.ssh/known_hosts}"

# validazione anche lato client (difesa in profondità)
case "$ENV"     in *[!a-z0-9-]*|'') echo "ERRORE: env non valido: '$ENV'" >&2; exit 2 ;; esac
case "$SISTEMA" in *[!a-z0-9-]*|'') echo "ERRORE: sistema non valido: '$SISTEMA'" >&2; exit 2 ;; esac

exec ssh -T \
  -i "$SSH_KEY" \
  -o BatchMode=yes \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" \
  -o ConnectTimeout=15 \
  "${RELAY_USER}@${RELAY_HOST}" "$ENV $SISTEMA"
