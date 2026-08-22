# FASE 2 — Wave A: Carichi (Inbound)

**Ultimo aggiornamento:** 2026-07-02 | **Wave:** A | **Stato:** 🔵 F_CARICO certificato (grain etichetta); OP-CAR-5 aperto

## 1. Obiettivo & scope
Ricevimento merce in ingresso: dal carico fornitore alla riga di dettaglio pesata, fino al fact
`F_CARICO` (grain **etichetta**) e alla tracciabilità lotti CE178.

## 2. Sorgenti
Sistema **logistix**: `sto_tes_carichi` (testate), `sto_righe_carico` (dettagli), `pesate`,
`tracciace178`. Anagrafica peso/volume: `LU_ART_UNITA_LOGISTICA` (cdt_dw).

## 3. Bronze (DELTA_MERGE)
`sto_tes_carichi` (~1.4k/g), `sto_righe_carico` (~30k/g), `pesate` (~16k/g), `tracciace178` (~12k/g).

## 4. Silver
| Notebook | Target | Note |
|---|---|---|
| `silver_carichi_testate` | `logistica.carico_testata` | clean, MERGE incrementale per run_date (watermark OP-35) |
| `silver_carichi_dettagli` | `logistica.carico_dettaglio` | + derivazione ART_RADICE/ART_VAR (OP-12) |
| `silver_pesate` | `logistica.pesata` | clean, dedup |
| `silver_prep_carico` | `logistica_curated.carico` | **JOIN testata⋈dettaglio⋈pesata**, grain etichetta, OVERWRITE dyn per ANNO_MESE |

## 5. Gold
| Notebook | Target | Grain / regole |
|---|---|---|
| `gold_f_carico` | `logistica.F_CARICO` | grain **etichetta** (CDT_SA.sql); `PES_CARICO` = PESO_LORDO×QTA_UF da `LU_ART_UNITA_LOGISTICA` (NON dalla pesata); replaceWhere ANNO_MESE |
| `gold_late_arriving_handler` | `logistica.F_CARICO` | riprocessa ANNO_MESE nella finestra (lookback 90g) |
| `gold_f_tracciabilita_lotti` | `logistica.F_TRACCIABILITA_LOTTI` | aggregato CE178 per lotto (vedi anche FASE 6) |

## 6. Dimensioni agganciate
`LU_SITO`, `LU_OPERATORE` (validante + `RICEVITORE_COD`), `LU_FORNITORE`, articolo (radice+variante),
calendario. `CORRIERE_COD` **rimosso** da F_CARICO (non rilevante, OP-30-lite). Orphan-rate 0.0%.

## 7. Data Quality & quadratura
`py scripts/quadratura/quadratura_fact.py --fact CARICO --da ... --a ... --soglia 5.0`.
Confronto sito×giorno vs CDT_DW. **La quadratura conta solo i file live** (helper `live_delta_files`
via `_delta_log`) — vedi memoria [[delta-tombstone-pyarrow-read]].

## 8. Open points di fase
- **OP-CAR-5** 🟠 grain `silver_prep_carico` guidato da pesata (INNER JOIN): carico in Gold solo se la
  pesata è arrivata e matcha (5 chiavi); CDT_DW popola T_CARICO dalla catena WL prima. 42 "Solo in ODI"
  su giorni con pesata in ritardo; dove pesata+carico coesistono match perfetto. **Decisione design**:
  LEFT join pesata vs grain da catena WL.
- **OP-CAR-1** 🔵 `VAL_COSTO_CARICO` NULL (sorgente cndstostock dismessa 2020).
- **OP-CAR-3** 🟠 `QTA_ORD_FORN`=0 (formula WL4 degenere, da validare).

## 9. Stato & dipendenze
F_CARICO 0.0% orphan; grain etichetta certificato; quadratura affidabile post-fix tombstone. Dipende da
FASE 1 (dimensioni) e `LU_ART_UNITA_LOGISTICA`.

## 10. Riferimenti
`../07_certifica_gold_vs_cdtdw.md`, `../08_playbook_certifica_wave.md`,
`../09_runbook_recert_carichi_prepsped.md`, memoria `odi-f-carico-grain-peso`.
