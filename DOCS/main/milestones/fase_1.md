# Milestone — FASE 1: Master Data & Dimensioni Condivise

> **Documento di chiusura di fase — deliverable di progetto per il cliente.** Sostituisce `fasi/F1_master_data.md` (archiviato). Stato di dettaglio sprint: [`../sprint_agile/`](../sprint_agile/) (1.1, 1.2, 1.3).

**Ultimo aggiornamento:** 2026-07-03 · **Stato fase:** 🔵 PARZIALE (17/19 gg) — DIM offline ✅; first-run cloud pendente

## 1. Executive summary (funzionale)
Costruzione delle **dimensioni logistiche** (`dim_*`/`LU_*`) e aggancio delle **anagrafiche master condivise**. Le dimensioni sono prodotte **prima dei fact** (regola di precedenza) e sono la base di orphan-rate 0.0% su tutte le wave. Le anagrafiche master (articolo/fornitore/PDV/calendario) sono lette in sola lettura, non ricostruite dal logistico.

## 2. Perimetro e sorgenti
Sistema **logistix** (anagrafiche FULL): `struttura_mag`, `tabgen`, carrellisti/preparatori/ricevitori/spedizionieri, `vettori_track`, `aree_merceologiche`. Anagrafiche master da **cdt_dw** (push): `LU_ART_RADICE`, `LU_FORNITORE`, `LU_PDV`, `LU_ART_UNITA_LOGISTICA`, `LU_GIORNO`.

## 3. Deliverable tecnici
**Silver dimensioni:** `dim_sito` (22 siti, `normalize_sito` + alias da tabgen nro_tab=7), `dim_operatore` (UNION 4 anagrafiche + self-healing + membro ND — OP-28), `dim_corriere`, `dim_topografia`, `dim_pdv`.
**Gold LU condivise:** `gold_lu_from_cdtdw.py` pubblica le `LU_*` in `bronze_dev.condiviso` (D2; `LU_ART_UNITA_LOGISTICA` 765k, CTAS baseline + MERGE delta). Chiavi naturali validate (no ID surrogati per ora).
**Dimensioni master DEPRECATE (OP-02):** `silver_dim_articolo/fornitore/pdv` escluse dai workflow.

## 4. Sprint della fase
| Sprint | Titolo | Stato | Doc |
|--------|--------|-------|-----|
| 1.1 | DIM Calendario & Merceologie | ✅ | [1.1](../sprint_agile/sprint_1.1.md) |
| 1.2 | DIM Articoli, Fornitori, PDV | 🔵 PARZ. | [1.2](../sprint_agile/sprint_1.2.md) |
| 1.3 | DIM Logistiche (Siti, Operatori, Corrieri) | 🔵 PARZ. | [1.3](../sprint_agile/sprint_1.3.md) |

## 5. Regole & decisioni
- Precedenza dimensioni sui fact (golden rule).
- `RICEVITORE_COD` cablato a `LU_OPERATORE`; NULL sorgente → `null_val="ND"` (non `-1`).
- D2: anagrafiche condivise in `bronze_dev.condiviso`.

## 6. Punti risolti
- **OP-28** — orphan operatori azzerato (recovery `dim_operatore` da storico_liste, pattern legacy 3A/4A).
- **OP-15** — unione carrellisti in `dim_operatore`.

## 7. Punti aperti
- **OP-02** — schema definitivo lookup Retail (in attesa Reply) → sblocca join master + LAD full.
- **OP-32** — LAD ri-risoluzione orphan (impl. base `gold_lad_resolver`; full dipende da OP-02).
- First-run cloud delle DIM (dipende da FASE 0).

- **OP-NAMING** 🔵 — Validare la naming degli oggetti di fase (tabelle e colonne): coerenza, leggibilità, allineamento standard e unità di misura. La naming legacy (ereditata da CDT_DW/ODI) è probabilmente da rivedere in una fase successiva.

## 8. Decisioni out-of-scope
- Ricostruzione anagrafiche master dal logistico: **esclusa** (si leggono da Retail/cdt_dw).
- ID surrogati interi: rimandati (oggi chiavi naturali validate).

## 9. Sviluppi futuri
- Aggancio diretto a Gold Retail per le master (OP-02) → deprecare la ripubblicazione in `condiviso`.
- Introduzione surrogate key quando concordato con Reply.

## 10. Riferimenti
`../02_pipeline_mapping.md` §5-7, `../05_open_points.md` (OP-01/02/28/32), `../sprint_agile/` (1.1-1.3).
