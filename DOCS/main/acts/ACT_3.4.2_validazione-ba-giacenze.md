# ACT_3.4.2 · Validazione funzionale giacenze con BA

**Status**: proposed
**Type**: analysis
**Origin**: sprint 3.4
**Sprint**: 3.4 — Workflow & Validazione Giacenze
**Fase / Wave**: FASE 3 — Wave B: Giacenze (Stock)
**Gg (stima)**: 2
**Blocco**: ☁️ cloud/PROD + BA (richiede PROD e disponibilità Business Analyst)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_3.4.1 (workflow deployato), ACT_3.3.6 (quadratura)   **Blocca**: chiusura Wave B Giacenze
**ADR collegate**: —   **OP collegati**: —

## Contesto e motivazione
Prima del go-live dell'area giacenze serve una validazione funzionale con il Business Analyst su dati
in PROD. È il gate di chiusura della Wave B: dipende dal workflow deployato
[[ACT_3.4.1_workflow-giacenze]] e dalla quadratura tecnica vs legacy
[[ACT_3.3.6_quadratura-giacenze-oracle]]. Non avviabile offline: richiede PROD e la presenza del BA.

## Obiettivo
Sign-off funzionale del BA sui deliverable giacenze. Fatto = validazione documentata e accettata (verbale).

## Analisi tecnica
- **Deliverable da validare** (`03_...`/`fase_3.md` §3, `02_pipeline_mapping.md` §Giacenze):
  - **`F_GIACENZE_DAILY`** (gold, grain `DATA_FOTO`+`ART_COD_INTERNO`+`MAG_COD`; ~54.7k righe nel big
    re-run, cresciuto da 0 a 55.231).
  - **Datamart mensile** `A_GIACENZE_MONTHLY` (`gold_dm_giacenze_monthly`, grain `ART_RADICE`+`MAG_COD`
    +`ANNO_MESE`) e `A_STOCK_MENSILE`.
  - **KPI**: vista `kpi_saturazione_magazzino` (ACT_3.3.4) e vista `kpi_aging_articoli` con bucket
    30/60/90/180+ (ACT_3.3.5).
- **Attività**: sessione su dati PROD — confronto KPI/aging attesi (business) vs prodotti; coerenza con
  Oracle legacy `CDT_DW.F_STOCK` (agganciarsi ai risultati della quadratura [[ACT_3.3.6_quadratura-giacenze-oracle]]).
- **Gap noti da presentare al BA** (per non farli passare come bug):
  - `VAL_STOCK_*` = 0 (OP ST-01/ST-02): sorgente stock valorizzato assente dall'as-is → valorizzazione
    economica fuori scope finché non si identifica la sorgente (`fase_3.md` §7-8).
  - Colonne non esposte da V_STOCK/CDT_ESTR e messe a NULL nel Gold: `EAN`, `QTA_IN_SCADENZA`,
    `QTA_PZ_ORD_CLIENTE`, `QTA_PZ_PREP_CLIENTE`, `DATA_ULT_STOCK` (vedi `gold_f_giacenze_daily.py`).
  - `OP-NAMING` (fase_3 §7): naming legacy ereditata da CDT_DW/ODI possibilmente da rivedere.
  - Ruolo Reply limitato ad anagrafiche/setup/standard (memoria `reply-scope-governance`): le decisioni
    sui flussi restano interne al team.
- **Precondizione dati**: verificare che il Gold PROD sia completo (ordering OP-29 non ha lasciato Gold
  parziale — in cloud il DAG del workflow garantisce l'ordine, ma va confermato prima della sessione).

## Sviluppo (diario)
- 2026-07-03 · pendente; non avviabile offline (richiede PROD + BA).

## Verifica
Verbale/sign-off del BA; eventuali scostamenti tracciati (con distinzione tra gap noti accettati e
anomalie da correggere).

## Esito
— (in attesa di PROD + BA)

## Follow-up
Scostamenti funzionali (non tra i gap noti) → ACT emergente 9000+.
