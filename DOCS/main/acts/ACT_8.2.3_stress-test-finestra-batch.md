# ACT_8.2.3 · Stress test finestra batch (ritardo sorgente)

**Status**: proposed
**Type**: analysis
**Origin**: sprint 8.2
**Sprint**: 8.2 — Shadow Mode Run 10+ gg
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 1
**Blocco**: ☁️ richiede shadow mode attivo (sprint 8.1)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.1.3   **Blocca**: ACT_8.2.4
**ADR collegate**: [[0017_rilascio_a_fasi]], [[0010_incrementale_watermark_pattern2_pruning]], [[0015_tuning_cloud_non_trasferibile]]   **OP collegati**: V-04 (stress test idempotenza su PROD)

## Contesto e motivazione
La finestra batch deve reggere anche quando la sorgente arriva in ritardo rispetto allo **SLA push 04:00**
([[12_checklist_infra_setup]] C4). Uno stress test verifica che la pipeline gestisca correttamente il
ritardo sorgente senza rompere schedule o quadrature, ed è collegato al punto aperto **V-04** (stress test
idempotenza su PROD, milestone `fase_8.md` §7).

## Obiettivo
Stress test della finestra batch con ritardo sorgente eseguito e valutato. Fatto = comportamento della
pipeline in caso di late-arrival documentato e ritenuto accettabile per il go-live.

## Analisi tecnica
- **Scenario**: simulare ritardo dell'arrivo file su landing PROD (push oltre le 04:00) e osservare:
  trigger file-arrival/schedule, ripartenze, watermark ([[0010_incrementale_watermark_pattern2_pruning]]),
  e le quadrature del giorno.
- **Late-arriving dimensions**: verificare che il LAD resolver ([[0011_lad_via_cod_nat]]) gestisca dim in
  ritardo senza generare orphan permanenti (recupero al ciclo successivo).
- **Idempotenza (V-04)**: re-run dello stesso `run_date` dopo l'arrivo tardivo → stesse righe/SUM misura
  chiave (KIT-07 check idempotenza); `replaceWhere` sulla partizione `run_date`, non overwrite totale.
- **Durata/timing**: verificare che il recupero rientri comunque nella finestra batch utile (durata
  workflow < 4h, rif. cutover_plan prereq. 8) sul compute serverless (sizing da ri-tarare,
  [[0015_tuning_cloud_non_trasferibile]] / KIT-08).
- Esito e comportamento vanno recepiti nel **runbook** (ACT_8.1.5, sezione late-arrival/ripartenze).

## Sviluppo (diario)
- 2026-07-03 · in attesa di shadow mode attivo.

## Verifica
- La pipeline gestisce il ritardo **senza perdita dati**; recupero al ciclo successivo verificato.
- Re-run idempotente (nessuna duplicazione); quadratura del giorno rientra in soglia dopo il recupero.
- Comportamento documentato e ritenuto accettabile per il go-live (input al report ACT_8.2.4).

## Esito
— (bloccato)

## Follow-up
Recepire l'esito nel runbook (ACT_8.1.5). Chiudere il punto V-04.
