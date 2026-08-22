# FASE 6 — Wave E: Tracciabilità CE178 & Carrellisti

**Ultimo aggiornamento:** 2026-07-02 | **Wave:** E | **Stato:** 🔵 offline OK; compliance CE178 da validare su cloud

## 1. Obiettivo & scope
Due filoni: (a) **tracciabilità lotti CE178** (compliance food safety — dal ricevimento alla spedizione);
(b) **movimentazione carrellisti** (produttività missioni carrello).

## 2. Sorgenti
Sistema **logistix**: `tracciace178` (~12k/g), `cartellino` (~180/g), `dettaglio_carr` (~10k/g),
`imbfmovim`. `dettaglio_carr` e `imbfmovim` sono **tabelle distinte** (OP-14).

## 3. Bronze (DELTA_MERGE)
`tracciace178`, `cartellino`, `dettaglio_carr`, `imbfmovim`.

## 4. Silver
| Notebook | Target | Note |
|---|---|---|
| `silver_traccia_ce178` | `logistica.tracciabilita_lotto` | clean, dedup |
| `silver_tracciabilita_lotto` | `tracciabilita` | aggregato CE178 per lotto |
| (carrellisti) | `logistica_curated.*` | missioni carrello → produttività |

## 5. Gold
| Notebook | Target | Grain |
|---|---|---|
| `gold_f_tracciabilita_lotti` | `logistica.F_TRACCIABILITA_LOTTI` | per lotto; replaceWhere ANNO_MESE (schedulato con Wave A) |
| (movimentazione carr.) | `F_TURNO_PREP_SITO` (contributo) | produttività operatori carrello |

## 6. Regole di business chiave
- **CE178**: catena lotto ricevimento→spedizione ricostruibile (requisito legale). Il fact lotti è
  schedulato nel workflow `logistica_carichi` (dipende dal Silver CE178 dello stesso run).
- Operatori carrellisti confluiscono in `dim_operatore` (TIPO=CARRELLISTA, OP-15) e alimentano la
  produttività di turno.

## 7. Data Quality & quadratura
- R-04: `lgcx/tracciace178` dedup ratio > 80% = anomalia landing.
- V-06: validazione compliance CE178 su dati reali (richiede PROD).

## 8. Open points di fase
- V-06 compliance CE178 (cloud/BA).
- Carrellisti: consolidamento produttività confluisce in FASE 7 (aggregati).

## 9. Stato & dipendenze
Offline OK. Dipende da FASE 1 (dim_operatore) e condivide il cluster/scheduling con Wave A (carichi).

## 10. Riferimenti
`../02_pipeline_mapping.md` §5 "Carrellisti"/§7, `../05_open_points.md` (OP-14), `../04_piano_sviluppo.md` FASE 6.
