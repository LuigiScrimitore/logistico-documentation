# FASE 4 — Wave C: Preparazione Spedizioni (Picking)

**Ultimo aggiornamento:** 2026-07-02 | **Wave:** C | **Stato:** 🔵 F_PREP_SPED v4.0 certificato; OP-PSP-1/2 chiusi

## 1. Obiettivo & scope
Picking e preparazione spedizioni: dalle liste di prelievo e bolle al fact `F_PREP_SPED` (grain riga di
prelievo con `SEQ_PREL_PREP`) e all'aggregato di turno `F_TURNO_PREP_SITO`.

## 2. Sorgenti
Sistema **stat**: `storico_liste` (~198-270k/g), `storico_bolle` (~430-880k/g), `testate_bolle`,
`storico_riepiloghi`. Sistema **cnd**: `t_prep_sped` (timbrature).

## 3. Bronze (DELTA_MERGE)
`storico_bolle`, `testate_bolle`, `storico_riepiloghi`, `storico_liste`, `t_prep_sped`.
Nota: 4 bronze avevano BOM UTF-8 (fix 2026-06-23, lettura byte-level).

## 4. Silver
| Notebook | Target | Note |
|---|---|---|
| `silver_storico_liste_clean` | `logistica.storico_liste_clean` | clean, MERGE, watermark (OP-35 pilota) |
| `silver_storico_liste_uniche` | `logistica.storico_liste_uniche` | DISTINCT per lista — DQ S7 |
| `silver_storico_bolle_clean` | `logistica.storico_bolle_clean` | clean, MERGE upsert |
| `silver_storico_bolle_uniche` | `logistica.storico_bolle_uniche` | DISTINCT per bolla; flag `_bolla_multipla` (DQ-03) |
| `silver_prep_riepiloghi` | `logistica.prep_riepilogo` | clean, MERGE |
| `silver_prep_prep_sped` | `logistica_curated.prep_sped` | **JOIN liste_uniche⋈bolle_uniche**, MERGE incrementale pattern #2 |
| `silver_prep_turno_prep_sito` | `logistica_curated.turno_prep_sito` | GROUP BY turno/sito |

## 5. Gold
| Notebook | Target | Grain / regole |
|---|---|---|
| `gold_f_prep_sped` | `logistica.F_PREP_SPED` | grain riga prelievo (con `SEQ_PREL_PREP`), articolo radice+variante; aggancio `LU_ART_RADICE` |
| `gold_f_turno_prep_sito` | `logistica.F_TURNO_PREP_SITO` | aggregato turno×sito (regola 30 min attrezzaggio) |

## 6. Regole di business chiave
- **DATA_PREL_INIZ** (OP-PSP-2, risolto): `julian_to_date(LSPRL_DATA_PRELIEVO)` + `LSPRL_ORA_PRELIEVO`
  (formula CDT_ESTR_VISTE.sql); `LSPRL_DATA_INIZIO_PRELIEVO` è NULL in sorgente.
- **Regola 30 minuti attrezzaggio** (F_TURNO): vedi `../01_architettura.md` §7.1.
- Chiave bolle 8 colonne (replica WL1 legacy): `BOL_NRO_BOLLA` NON è chiave (una gabbia/ordine può
  coprire più bolle) — DQ-01/02 chiusi.

## 7. Data Quality & quadratura
`quadratura_fact.py --fact PREP_SPED`. Include **blocco SCARTATE** (OP-PSP-1): confronta
`GIORNO_BOLLA_SPED_ID=0` (CDT_DW) vs `DATA_BOLLA_SPED IS NULL` (Gold).

## 8. Open points di fase
- **OP-PSP-1** 🟢 chiuso: righe scartate (TIPO_SCAR 09/10) senza bolla = coverage aggiuntiva; CDT_DW le
  esclude a monte (0 righe con GIORNO_BOLLA=0). NULL corretto, non gap.
- **OP-PSP-2** 🟢 risolto (DATA_PREL_INIZ).
- **OP-33** 🔵 `SEQ_PREL_PREP` nei MERGE_KEYS da confermare col legacy `INS_NEW_PREP_SPED`.
- **OP-34** 🔵 prep "piccoli" in FULL recompute (bassa priorità).

## 9. Stato & dipendenze
F_PREP_SPED v4.0 certificato; DATA_PREL distribuita su date reali. Dipende da FASE 1 (LU_ART_RADICE).

## 10. Riferimenti
`../07_certifica_gold_vs_cdtdw.md`, `../09_runbook_recert_carichi_prepsped.md`,
memoria `bronze-csv-schema-by-name`.
