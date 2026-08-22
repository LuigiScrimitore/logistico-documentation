# ACT_0.1.5 · Cluster policy — job cluster serverless

**Status**: done
**Type**: infra
**Origin**: sprint 0.1
**Sprint**: 0.1 — Unity Catalog & Storage Foundation
**Fase / Wave**: FASE 0 — Fondamenta Infrastrutturali
**Closed**: 2026-07-03
**ADR collegate**: ADR-0009 (job cluster serverless)   **OP collegati**: OP-19

## Contesto
I job Databricks logistici avevano bisogno di una policy di compute definita prima di poter girare in
cloud. L'alternativa era un cluster classico con VM dimensionate (`node_type_id`/`num_workers`), che però
richiede tuning manuale e resta acceso/schedulato. Serverless nasce col job e viene killato al termine,
riducendo costo e gestione — ma va confermato con Reply perché impatta la piattaforma condivisa.

## Obiettivo
Definire la policy di compute per i job Databricks come **job cluster serverless** (niente
`node_type_id`/VM), confermata con Reply.

## Esito
Confermato con Reply (2026-07-03): job **serverless** ("nasce col job, killato al termine"); rimossi
`node_type_id`/`num_workers`/`autotermination` dalle variabili. Chiude OP-19. Nota: il tuning di
memoria/spill **non** si eredita dal locale (vedi ADR-0015) — si ritara su serverless al primo rilascio.

> ⚠️ **Correzione implementativa 2026-08-04 ([[ACT_9007]])**: la policy allora creata,
> `logistico-serverless-job-policy` (`runtime_engine=SERVERLESS`, `SINGLE_USER`), è stata **rimossa** dal
> Terraform perché tecnicamente errata: `SERVERLESS` non è un valore valido per `runtime_engine` (solo
> `PHOTON`/`STANDARD`) e **le compute policy non si applicano al serverless**. Il serverless si ottiene
> **non dichiarando compute** nei job. La *decisione* di questa ACT resta valida; cambia solo il "come".
> Vedi ADR-0009 §"Aggiornamento 2026-08-04".
