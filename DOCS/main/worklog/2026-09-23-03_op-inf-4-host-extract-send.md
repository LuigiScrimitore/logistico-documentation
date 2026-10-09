---
data: 2026-09-23
titolo: OP-INF-4: host extract&send target su Windows
autore: Luigi Scrimitore
push_monorepo: 667bf00
push_documentation: "n/d"
push_gitlab: "—"
act: []
adr: [ADR-0023]
lesson: []
op: [OP-INF-4]
---

## Cosa è stato fatto
- Creato **OP-INF-4** (doc 05): assessment dei due host on-prem + decisione architetturale sull'host di extract & send verso la landing.
- Esito verifiche: `odisrvcno2` (RHEL 6.8 EOL — glibc 2.12, py2.6, openssl 2013, CA rotto) **non idoneo** ad AzCopy; **macchina Windows** (`10.8.1.50`: AzCopy 10.32.7, egress+TLS+CA ok, Python 3.13, **DB access già presente**) **idonea**.

## Novità
- **Decisione (TARGET, non ponte)**: app **Python schedulata sulla Windows** = extract (`oracledb`) → send **AzCopy** → `logisticolanding`. La RHEL6 ODI esce dal percorso.
- Emerso che l'**extract è già Python** (non ODI): `scripts/landing_simulator/extract_oracle_to_landing.py` + `scripts/cdtdw_lookup_extractor/extract_cdtdw_lookups.py` → la scelta è una **consolidazione**, non una riscrittura da ODI.
- Trasporto resta **AzCopy standard** ([[ADR-0023]]); scartati SDK-su-RHEL6, rclone, Docker-su-RHEL6.

## Doc aggiornati
05 (nuovo OP-INF-4 + riepilogo + header).

## Stato dopo il push / prossimi passi
Direzione target decisa. Restano: **provisioning Azure** (container+SAS+Access Connector, §F.2/[[ACT_9012]]), **industrializzazione** dell'app schedulata, **buy-in** piattaforma. Da formalizzare con **ADR** + **ACT** + runbook.
