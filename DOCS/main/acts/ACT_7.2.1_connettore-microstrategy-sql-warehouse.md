# ACT_7.2.1 · Connettore MicroStrategy → Databricks SQL Warehouse

**Status**: in-progress
**Type**: infra
**Origin**: sprint 7.2
**Sprint**: 7.2 — MicroStrategy & Ottimizzazione Query
**Fase / Wave**: FASE 7 — KPI Aggregati & Reporting
**Gg (stima)**: 2
**Blocco**: ☁️ cloud/PROD (richiede SQL Warehouse cloud attivo)
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_7.2.3 (viste KPI)   **Blocca**: ACT_7.2.5 (dashboard)
**ADR collegate**: —   **Doc collegati**: `13_registro_rename_gold_microstrategy.md` (rename Gold per MSTR)   **OP collegati**: —

## Contesto e motivazione
MicroStrategy è il tool di reporting business: deve interrogare le **viste KPI Gold** (`gold_prod.logistica.kpi_*`)
via Databricks SQL Warehouse (endpoint SQL con Unity Catalog). Il connettore va configurato lato MicroStrategy
(driver Databricks/Simba ODBC-JDBC, host, HTTP path del warehouse, token/OAuth) e richiede il warehouse cloud attivo.
Oggi MSTR è mappato **sulle viste `kpi_*`, non direttamente sulle tabelle `F_*`/`A_*`**: le viste sono lo strato di
disaccoppiamento (cfr. [[13_registro_rename_gold_microstrategy]] nota reporting 2026-07-04). I rename Gold che
impattano MSTR sono tracciati in quel **registro** (`13_registro_rename_gold_microstrategy.md`) — **non** è un ADR
(l'ADR-0013 è `scope_trasporti_mtv`, altro tema).

## Obiettivo
Connettore MicroStrategy → Databricks SQL Warehouse funzionante sulle viste KPI.
Fatto = MicroStrategy legge le 10 KPI views (`gold_prod.logistica.kpi_*`) dal SQL Warehouse con dati coerenti con Gold.

## Analisi tecnica
- **Richiede SQL Warehouse cloud attivo** (dipende dall'accesso infra Azure/Databricks) → attività bloccata offline.
- **Consumatore delle 10 viste KPI** definite in `sql/kpi/gold_kpi_*.sql`, tutte `CREATE OR REPLACE VIEW gold_prod.logistica.kpi_*`:
  `kpi_saturazione_magazzino`, `kpi_aging_articoli`, `kpi_produttivita_operatore`, `kpi_efficienza_sito_prep`,
  `kpi_fill_rate`, `kpi_costo_trasporto`, `kpi_resa_corrieri`, `kpi_bolle_annullate`, `kpi_lead_time_fornitore`
  (→ riscritta `kpi_volumi_inbound_fornitore`), `kpi_qualita_ricevimento`. Chiavi naturali v2.0 ([[adr/0008_chiavi_naturali_gold]]).
- **Impatti rename da recepire lato modello MSTR** prima del rilascio (🔴 in `13_registro_rename_gold_microstrategy` §B/C):
  metriche su `A_INBOUND_MENSILE` (v3→v4, scarto→ammanco), vista `kpi_lead_time_fornitore`→`kpi_volumi_inbound_fornitore`,
  `kpi_qualita_ricevimento` riabilitata con misure ammanco. Azione futura: analisi del modello MSTR per mappare esattamente
  quali viste/attributi/metriche legge.
- Precondizione warehouse: eseguito lo script di ottimizzazione `sql/optimize/gold_optimize_tables.sql` (OPTIMIZE/ZORDER/ANALYZE)
  sulle tabelle sottostanti le viste, per prestazioni query accettabili.

## Sviluppo (diario)
- 2026-07-03 · avanzamento 20%: impostazione preliminare; configurazione bloccata su SQL Warehouse cloud.

## Verifica
- Query di prova da MicroStrategy contro almeno una vista per area (es. `kpi_produttivita_operatore`, `kpi_saturazione_magazzino`)
  restituisce dati coerenti con Gold (stessi valori di un `SELECT` diretto sul warehouse).
- Il connettore autentica e mostra il catalogo `gold_prod` / schema `logistica` con le 10 viste `kpi_*`.

## Esito
— (richiede cloud)

## Follow-up
Da recepire: aggiornamento modello MSTR sui rename 🔴 — traccia nel doc `13_registro_rename_gold_microstrategy.md`.
