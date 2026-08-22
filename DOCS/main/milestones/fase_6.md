# Milestone — FASE 6: Wave E — Tracciabilità CE178 & Carrellisti

> **Documento di chiusura di fase — deliverable di progetto per il cliente.** Sostituisce `fasi/F6_tracciabilita_carrellisti.md` (archiviato). Stato di dettaglio sprint: [`../sprint_agile/`](../sprint_agile/) (6.1–6.3).

**Ultimo aggiornamento:** 2026-07-03 · **Stato fase:** 🔵 PARZIALE (17/19 gg) — offline OK; compliance CE178 da validare su cloud

## 1. Executive summary (funzionale)
Due filoni: (a) **tracciabilità lotti CE178** (compliance food safety, dal ricevimento alla spedizione); (b) **movimentazione carrellisti** (produttività missioni carrello). Il primo è requisito legale (ricostruzione catena lotto).

## 2. Perimetro e sorgenti
Sistema **logistix**: `tracciace178` (~12k/g), `cartellino` (~180/g), `dettaglio_carr` (~10k/g), `imbfmovim`. `dettaglio_carr` e `imbfmovim` sono tabelle distinte (OP-14).

## 3. Deliverable tecnici
**Silver:** `tracciabilita_lotto` (clean/dedup), `silver_missione_carrellista` (durata, tipo), `silver_sessione_carrellista` (ORE_PRODUTTIVE = MAX(SUM(dur)-30,0)/60).
**Gold:** `F_TRACCIABILITA_LOTTI` (per lotto, replaceWhere ANNO_MESE, schedulato con Wave A), contributo carrellisti a `F_TURNO`.
**Dimensioni:** operatori carrellisti in `dim_operatore` (TIPO=CARRELLISTA, OP-15).

## 4. Sprint della fase
| Sprint | Titolo | Stato | Doc |
|--------|--------|-------|-----|
| 6.1 | CE178 Silver & Gold | ✅ | [6.1](../sprint_agile/sprint_6.1.md) |
| 6.2 | Carrellisti Bronze-Silver-Gold | ✅ | [6.2](../sprint_agile/sprint_6.2.md) |
| 6.3 | Workflow Wave E & Validazione | 🔵 PARZ. | [6.3](../sprint_agile/sprint_6.3.md) |

## 5. Regole di business chiave
- **CE178**: catena lotto ricevimento→spedizione ricostruibile (requisito legale); fact lotti schedulato nel workflow `logistica_carichi`.
- Carrellisti confluiscono in `dim_operatore` e alimentano la produttività di turno.

## 6. Punti risolti
- **OP-14** — DETTAGLIO_CARR e IMBFMOVIM come tabelle distinte.
- **OP-15** — unione carrellisti in dim_operatore.

## 7. Punti aperti
- **V-06** — validazione compliance CE178 su dati reali (richiede PROD/BA).
- Consolidamento produttività carrellisti confluisce in FASE 7 (aggregati).

- **OP-NAMING** 🔵 — Validare la naming degli oggetti di fase (tabelle e colonne): coerenza, leggibilità, allineamento standard e unità di misura. La naming legacy (ereditata da CDT_DW/ODI) è probabilmente da rivedere in una fase successiva.

## 8. Decisioni out-of-scope
- Nessuna decisione out-of-scope specifica; l'unico vincolo è la validazione compliance su dati reali (PROD).

## 9. Sviluppi futuri
- Validazione compliance CE178 con BA in shadow mode.
- Dashboard produttività carrellisti (FASE 7).

## 10. Riferimenti
`../02_pipeline_mapping.md` §5 "Carrellisti"/§7, `../05_open_points.md` (OP-14), `../sprint_agile/` (6.1-6.3).
