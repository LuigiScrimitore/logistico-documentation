# Milestone — FASE 4: Wave C — Preparazione Spedizioni (Picking)

> **Documento di chiusura di fase — deliverable di progetto per il cliente.** Sostituisce `fasi/F4_prep_spedizioni.md` (archiviato). Stato di dettaglio sprint: [`../sprint_agile/`](../sprint_agile/) (4.1–4.5).

**Ultimo aggiornamento:** 2026-07-03 · **Stato fase:** 🔵 PARZIALE (28/33 gg) — F_PREP_SPED v4.0 certificato; backfill/quadratura/edge-cases/BA pendenti

## 1. Executive summary (funzionale)
Picking e preparazione spedizioni: dalle liste di prelievo e bolle al fact **F_PREP_SPED** (grain riga di prelievo con `SEQ_PREL_PREP`) e all'aggregato di turno **F_TURNO_PREP_SITO**. F_PREP_SPED v4.0 certificato, 0.0% orphan PREPARATORE/OPERATORE.

## 2. Perimetro e sorgenti
Sistema **stat**: `storico_liste` (~198-270k/g), `storico_bolle` (~430-880k/g), `testate_bolle`, `storico_riepiloghi`. Sistema **cnd**: `t_prep_sped` (timbrature).

## 3. Deliverable tecnici
**Silver:** `storico_liste_clean` (watermark OP-35 pilota), `storico_liste_uniche` (GROUP BY 8 chiavi, pattern #2), `storico_bolle_clean`, `storico_bolle_uniche`, `prep_riepilogo`, `logistica_curated.prep_sped` (JOIN liste_uniche⋈bolle_uniche, MERGE incrementale pattern #2), `logistica_curated.turno_prep_sito`.
**Gold:** `F_PREP_SPED` (grain riga prelievo con SEQ_PREL_PREP, articolo radice+variante), `F_TURNO_PREP_SITO` (regola 30 min attrezzaggio).

## 4. Sprint della fase
| Sprint | Titolo | Stato | Doc |
|--------|--------|-------|-----|
| 4.1 | Bronze Prep Spedizioni | 🔵 PARZ. | [4.1](../sprint_agile/sprint_4.1.md) |
| 4.2 | Silver Prep Spedizioni | ✅ | [4.2](../sprint_agile/sprint_4.2.md) |
| 4.3 | Gold F_PREP_SPED | 🔵 PARZ. | [4.3](../sprint_agile/sprint_4.3.md) |
| 4.4 | KPI Picking & Workflow | 🔵 PARZ. | [4.4](../sprint_agile/sprint_4.4.md) |
| 4.5 | Edge Cases Prep Spedizioni | 🔵 PARZ. | [4.5](../sprint_agile/sprint_4.5.md) |

## 5. Regole di business chiave
- **DATA_PREL_INIZ** (OP-PSP-2): `julian_to_date(LSPRL_DATA_PRELIEVO)` + `LSPRL_ORA_PRELIEVO` (CDT_ESTR_VISTE.sql); `LSPRL_DATA_INIZIO_PRELIEVO` è NULL in sorgente.
- **Regola 30 min attrezzaggio** (F_TURNO), 9 test verdi.
- Chiave bolle 8 colonne (replica WL1 legacy): `BOL_NRO_BOLLA` NON è chiave.

## 6. Punti risolti
- **OP-PSP-1** — righe scartate senza bolla = coverage aggiuntiva; NULL corretto, non gap (chiuso).
- **OP-PSP-2** — DATA_PREL_INIZ valorizzata (chiuso).
- OP-30 (clean incrementale + pattern #2) validato; OP-35 watermark pilota ALL_OK.

## 7. Punti aperti
- **OP-33** 🔵 — `SEQ_PREL_PREP` nei MERGE_KEYS da confermare col legacy `INS_NEW_PREP_SPED`.
- **OP-34** 🔵 — prep "piccoli" in FULL recompute (bassa priorità).
- Quadratura, validazione BA, stress test idempotenza — richiedono cloud/PROD.

- **OP-NAMING** 🔵 — Validare la naming degli oggetti di fase (tabelle e colonne): coerenza, leggibilità, allineamento standard e unità di misura. La naming legacy (ereditata da CDT_DW/ODI) è probabilmente da rivedere in una fase successiva.

## 8. Decisioni out-of-scope
- FULL recompute dei prep piccoli: accettato come comportamento (bassa priorità), non ottimizzato ora.

## 9. Sviluppi futuri
- Conferma OP-33 con BA/legacy e ricertificazione.
- Stress test idempotenza su PROD con storico reale.

## 10. Riferimenti
`../07_certifica_gold_vs_cdtdw.md`, `../09_runbook_recert_carichi_prepsped.md`, memoria `bronze-csv-schema-by-name`, `../sprint_agile/` (4.1-4.5).
