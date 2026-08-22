# FASE 1 — Master Data & Dimensioni condivise

**Ultimo aggiornamento:** 2026-07-02 | **Wave:** — | **Stato:** 🔵 offline ✅; first-run cloud pendente

## 1. Obiettivo & scope
Costruire le **dimensioni logistiche** (`dim_*`/`LU_*`) e agganciare le **anagrafiche master** condivise.
Le dimensioni vanno prodotte **prima dei fact** (regola di precedenza). Le anagrafiche master Retail
(articolo/fornitore/PDV/calendario) sono lette in sola lettura, non ricostruite dal logistico.

## 2. Sorgenti
Sistema **logistix** (anagrafiche FULL_OVERWRITE): `struttura_mag`, `tabgen`, `carrellisti`,
`preparatori`, `ricevitori`, `spedizionieri`, `vettori_track`, `aree_merceologiche`, `corsie`,
`classe_posto_pallet`. Anagrafiche master da **cdt_dw** (push): `LU_ART_RADICE`, `LU_FORNITORE`,
`LU_PDV`, `LU_ART_UNITA_LOGISTICA`, `LU_GIORNO`.

## 3. Bronze
Anagrafiche in `FULL_OVERWRITE` (riflettono lo stato corrente): vedi `../02_pipeline_mapping.md` §5
"Anagrafiche". Chiave: lettura per header (mai `.schema()` posizionale su CSV).

## 4. Silver — dimensioni operative
| Notebook | Sorgente | Target | Note |
|---|---|---|---|
| `silver_dim_sito` | `struttura_mag` | `logistica.dim_sito` | 22 siti; `normalize_sito` + alias da `tabgen` nro_tab=7 |
| `silver_dim_operatore` | 4 anagrafiche (UNION, OP-15) | `logistica.dim_operatore` | + self-healing NON_DEFINITO + membro `ND` (OP-28) |
| `silver_dim_corriere` | `vettori_track` | `logistica.dim_corriere` | `VET_DESCRIZIONE` (colonne reali, OP-27) |
| `silver_dim_topografia` | `struttura_mag` | `logistica.dim_topografia` | `CELLA_COD` = concat STRM_* |
| `silver_dim_pdv` | `apvpunto_vendita` | `logistica.dim_pdv` | clean 1:1 |

**Dimensioni master DEPRECATE (OP-02):** `silver_dim_articolo/fornitore/pdv` escluse dai workflow — le
master arrivano da Retail/cdt_dw come `LU_*` in `bronze_dev.condiviso` (brownfield: `bronze_<env>.condiviso`).

## 5. Gold — pubblicazione LU condivise
`gold_lu_from_cdtdw.py` pubblica le `LU_*` da cdt_dw (es. `LU_ART_UNITA_LOGISTICA` 765k righe, CTAS
baseline + MERGE delta). Chiavi naturali validate (no ID interi surrogati per ora — vedi memoria
gold-natural-key-vs-surrogate).

## 6. Data Quality
- Orphan-rate 0.0% su tutti i fact al run 2026-06-17 (OP-28 risolto).
- `RICEVITORE_COD` cablato a `LU_OPERATORE`; NULL sorgente gestiti con `null_val="ND"` (non `-1`).

## 7. Open points di fase
- **OP-02** schema definitivo lookup Retail (in attesa Reply) → sblocca join master + LAD full.
- **OP-32** LAD ri-risoluzione orphan (impl. base `gold_lad_resolver`, full dipende da OP-02).
- **D2** (brownfield): riuso anagrafiche DWW `bronze_dev.prodotto/fornitore/pdv` vs `condiviso` proprio.

## 8. Stato & dipendenze
Offline validato (dim 0.0% orphan). Blocca tutte le wave fact (precedenza dimensioni). Dipende da FASE 0
per il first-run cloud.

## 9. Riferimenti
`../02_pipeline_mapping.md` §5-7, `../05_open_points.md` (OP-01/02/28/32), memoria
`op28-self-healing-operatori`, `gold-natural-key-vs-surrogate`, `sito-mapping-slogistix`.
