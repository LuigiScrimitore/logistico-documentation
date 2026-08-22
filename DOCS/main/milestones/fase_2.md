# Milestone — FASE 2: Wave A — Carichi (Inbound)

> **Documento di chiusura di fase — deliverable di progetto per il cliente.** Sostituisce `fasi/F2_carichi.md` (archiviato). Stato di dettaglio sprint: [`../sprint_agile/`](../sprint_agile/) (2.1–2.4).

**Ultimo aggiornamento:** 2026-07-05 · **Stato fase:** 🔵 PARZIALE (21/26 gg) — F_CARICO certificato (grain etichetta); OP-CAR-3/ammanco validati a runtime; backfill/quadratura/BA pendenti

## 1. Executive summary (funzionale)
Ricevimento merce in ingresso: dal carico fornitore alla riga di dettaglio pesata, fino al fact **F_CARICO** (grain **etichetta**) e alla tracciabilità lotti CE178. F_CARICO è certificato con **orphan-rate 0.0%** in locale.

## 2. Perimetro e sorgenti
Sistema **logistix**: `sto_tes_carichi`, `sto_righe_carico`, `pesate`, `tracciace178`. Anagrafica peso/volume: `LU_ART_UNITA_LOGISTICA` (cdt_dw).

## 3. Deliverable tecnici
**Silver:** `carico_testata` (watermark OP-35), `carico_dettaglio` (+ ART_RADICE/ART_VAR, OP-12), `pesata`, `logistica_curated.carico` (JOIN testata⋈dettaglio⋈pesata, grain etichetta, overwrite dyn per ANNO_MESE).
**Gold:** `F_CARICO` (grain etichetta da CDT_SA.sql; `PES_CARICO` = PESO_LORDO×QTA_UF da `LU_ART_UNITA_LOGISTICA`, non dalla pesata; replaceWhere ANNO_MESE), `gold_late_arriving_handler`, `F_TRACCIABILITA_LOTTI`.
**Dimensioni agganciate:** LU_SITO, LU_OPERATORE (+RICEVITORE_COD), LU_FORNITORE, articolo (radice+variante), calendario. `CORRIERE_COD` rimosso da F_CARICO.

## 4. Sprint della fase
| Sprint | Titolo | Stato | Doc |
|--------|--------|-------|-----|
| 2.1 | Bronze Carichi | 🔵 PARZ. | [2.1](../sprint_agile/sprint_2.1.md) |
| 2.2 | Silver Carichi | ✅ | [2.2](../sprint_agile/sprint_2.2.md) |
| 2.3 | Gold F_CARICO | 🔵 PARZ. | [2.3](../sprint_agile/sprint_2.3.md) |
| 2.4 | KPI & Validazione Carichi | 🔵 PARZ. | [2.4](../sprint_agile/sprint_2.4.md) |

## 5. Data Quality & quadratura
`quadratura_fact.py --fact CARICO` (sito×giorno vs CDT_DW). La quadratura conta **solo i file live** (helper `live_delta_files` via `_delta_log`, no tombstone).

## 6. Punti risolti
- **OP-12** — ART_RADICE/ART_VARIANTE derivata in Silver per troncamento.
- **OP-CAR-4/A** — quadratura corretta post-fix tombstone.
- Grain etichetta certificato (catena WL_CARICO WL2→WL3→WL4→T_CARICO).
- **OP-CAR-3** ✅ (validato runtime 2026-07-05) — `QTA_ORD_FORN`: formula legacy degenere; replica pulita = qta ordinata sulla prima etichetta del gruppo (SUM invariante). Popolato (SUM=1.921.348).
- **OP-CAR-5** ✅ (2026-07-04) — grain: **INNER JOIN pesata confermato** fedele al legacy (`V_CARICO_ORDINARIO` usa inner sulla pesata). I gap "solo in ODI" sono timing, gestiti dal lookback re-run. Nessuna modifica.
- **Ammanco — unità** ✅ (2026-07-05) — `QTA_ORD_FORN` è in **COLLI**, `QTA_CARICO` in **PEZZI** (fattore `NUM_PZ_IMB_ORD_FORN`). `A_INBOUND` calcola l'ammanco in pezzi: `QTA_ORDINATA_TOT = SUM(QTA_ORD_FORN × NUM_PZ_IMB_ORD_FORN)` → ammanco +253.243 pz = **1.51%** (prima −14.6M per unità miste). Rimossa la colonna morta `AMMANCO_QTA` da `carico_dettaglio`.

## 7. Punti aperti
- **OP-CAR-1** 🔵 — `VAL_COSTO_CARICO` NULL (sorgente cndstostock dismessa 2020).
- Quadratura vs Oracle e validazione BA — richiedono cloud/PROD.
- **OP-NAMING** 🔵 — Validare la naming degli oggetti di fase (tabelle e colonne): coerenza, leggibilità, allineamento standard e **unità di misura**. *Esempio carichi:* `QTA_ORD_FORN` (colli) e `QTA_CARICO` (pezzi) mantengono i nomi ODI per fedeltà/quadratura CDT_DW; l'unità è nei commenti colonna e i nomi espliciti (in pezzi) vivono nel layer aggregato (`A_INBOUND`). Un rename fisico su F_CARICO (es. `QTA_ORD_FORN_COLLI`/`QTA_CARICO_PZ`) è rinviato a una fase successiva perché impatta quadratura-per-nome e migrazione MSTR.

## 8. Decisioni out-of-scope
- `VAL_COSTO_CARICO`: non valorizzabile (sorgente dismessa) — fuori scope.
- Peso da pesata fisica: **scartato** — si usa l'anagrafica articolo (allineato ODI).

## 9. Sviluppi futuri
- Quadratura automatica su Databricks (backend Spark, DBR-04).

## 10. Riferimenti
`../07_certifica_gold_vs_cdtdw.md`, `../08_playbook_certifica_wave.md`, `../09_runbook_recert_carichi_prepsped.md`, `../sprint_agile/` (2.1-2.4).
