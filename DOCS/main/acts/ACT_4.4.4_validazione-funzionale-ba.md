# ACT_4.4.4 · Validazione funzionale con BA

**Status**: proposed
**Type**: analysis
**Origin**: sprint 4.4
**Sprint**: 4.4 — KPI Picking & Workflow
**Fase / Wave**: FASE 4 — Wave C: Preparazione Spedizioni (Picking)
**Gg (stima)**: 2
**Blocco**: 🏗️ infra — richiede PROD + disponibilità BA
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_4.4.3 (workflow), ACT_4.3.6 (quadratura)   **Blocca**: chiusura funzionale Wave C
**ADR collegate**: —   **OP collegati**: OP-33 (tiebreaker dedup da validare con BA)

## Contesto e motivazione
La Wave C picking va validata funzionalmente con il Business Analyst: KPI, regola 30 min attrezzaggio,
tiebreaker/grana dedup (OP-33). Non avviabile offline — richiede dati in PROD e la presenza del BA.
Sprint [`../sprint_agile/sprint_4.4.md`](../sprint_agile/sprint_4.4.md) (4.4.4, ⏳ PENDENTE). Prerequisiti:
workflow in PROD ([[ACT_4.4.3]]) e quadratura ([[ACT_4.3.6]]).

> **Nota OP-33 — già CONFERMATO tecnicamente (2026-07-05)**: da
> [`../05_open_points.md`](../05_open_points.md) OP-33 🟢, `SEQ_PREL_PREP` **deve** stare nei
> MERGE_KEYS ed è **già incluso** (grain a 9 chiavi in `silver_prep_prep_sped`). Evidenza legacy
> `CDT_DW.sql`: `INS_NEW_PREP_SPED` è `INSERT ... SELECT ... FROM f_prep_sped` **senza GROUP BY** →
> `seq_prel_prep` è attributo di grana, non aggregato; ometterlo collasserebbe ~30k righe sorgente.
> Resta il **sign-off funzionale del BA** sulla scelta (nel registro OP-33 è 🔵 "da validare con BA").

## Obiettivo
Validazione funzionale dei KPI e delle regole prep spedizioni con il BA; sign-off BA su OP-33.
Fatto = sign-off BA sui KPI e sulla regola di grana/dedup.

## Analisi tecnica
- **KPI da rivedere** (view `gold_prod.logistica.kpi_*`, già realizzate):
  `kpi_produttivita_operatore` (RANK sito/mese, 4.4.1 ✅) e `kpi_efficienza_sito_prep`
  (% attrezzaggio, 4.4.2 ✅). Attenzione ai KPI riformulati su dato reale (cartoni/ora, non colli/ora;
  no ORE_PRODUTTIVE carrellisti — cfr. [`../02_pipeline_mapping.md`](../02_pipeline_mapping.md) righe
  577, 552, OP-27).
- **Regola 30 min attrezzaggio** (F_TURNO_PREP_SITO, 4.3.2 ✅, 9 test verdi): Window per
  `(PREPARATORE_COD, DATA_PREPARAZ, SITO_COD)` ordinata per `ORA_INIZIO_PREP`; prima sessione del
  giorno `ORE_PRODUTTIVE = max(0, ORE_LAVORATE - 0.5)` (02 riga 552).
- **Grana/tiebreaker OP-33**: `SEQ_PREL_PREP` nei MERGE_KEYS (grain a 9 chiavi in
  `notebooks/silver/prep_spedizioni/silver_prep_prep_sped.py`; sorgente `silver_storico_liste_uniche`
  a 8 chiavi con `LSPRL_SEQUE_PRELIEVO` + `LSPRL_FLAG_SCARTATO`).
- **Prerequisiti**: workflow in PROD (ACT_4.4.3) e quadratura numerica (ACT_4.3.6).

## Sviluppo (diario)
- 2026-07-03 · pendente: richiede PROD + BA.

## Verifica
Sign-off del BA su: KPI produttività/efficienza, regola 30 min, scelta di grana OP-33
(`SEQ_PREL_PREP`). OP-33 chiuso lato funzionale.

## Esito
— (pendente)

## Follow-up
- Se il BA modifica la grana → aggiornamento di `silver_prep_prep_sped` ([[ACT_4.3.3]]) e re-run
  Silver/Gold (CTAS pulito, cfr. §1.2 nota re-run in `07`).
