# Pipeline Operativa — Logistico 2.0

**Scopo:** documento operativo della pipeline Medallion (Bronze→Silver→Gold→Gold_dm): grafo
delle dipendenze, ordine di esecuzione dei sub-process e inventario tabelle per schema/flusso.
**Aggiornato:** 2026-06-10 (post ridisegno scelta B + standard 2-notebook prep+gold).

---

## 1. Architettura a layer

| Layer | Catalogo.schema | Ruolo |
|-------|-----------------|-------|
| **Bronze** | `bronze_<env>.logistica` | copia 1:1 raw dei file landing + metadati `_bronze_*`, `_sito_estrazione`/`_sito_cod` |
| **Silver clean** | `silver_<env>.logistica` | cleansing 1:1 (julian→date, `normalize_sito`, trim/cast, dedup) + elaborazioni intermedie (uniche, catena, s_trasp_mtv) |
| **Silver prep** | `silver_<env>.prep_logistica` | Fase 1 modellazione (join) + Fase 2 calcolo (logiche, chiavi-giorno). **Il Gold legge SOLO da qui** |
| **Gold fact** | `gold_<env>.logistica` | Fase 3: aggancio dimensioni (`surrogate_key_fallback`+`check_orphan_rate`), scrittura `F_*` e dimensioni `LU_*` |
| **Gold datamart** | `gold_<env>.logistica_dm` | aggregati mensili `A_*` dai fact |
| **Retail master** | `cdtdw.condiviso` (workaround OP-02) | lookup condivise `LU_FORNITORE`, `LU_PDV`, `LU_ART_RADICE` (estratte da CDT_DW, NON ricostruite dal logistico) |

> `<env>` = `dev`/`prod`. In locale gli FQN a 3 livelli sono collassati a 2 (`silver_dev_logistica`) dal rewriter del runner.

---

## 2. Ordine macro di esecuzione (grafo di fase)

```
[0] LANDING (ingestion Oracle→CSV)  extract_oracle_to_landing.py  (22 siti logistix + stat + cdt_estr_raw + track)
        │
        ▼
[1] BRONZE 1:1  (tutte le aree; UPSERT transazionali / FULL anagrafiche / SNAPSHOT giacenze)
        │
        ├─────────────┬───────────────┬──────────────┬───────────────┐
        ▼             ▼               ▼              ▼               ▼
[2] DIMENSIONI   [3] CARICHI     [4] GIACENZE    [5] SPEDIZIONI   [6] TRASPORTI
   (LU_*)         (F_CARICO)     (F_GIACENZE)    (F_PREP_SPED,    (F_TRASPORTO,
        │                                          F_TURNO_*)      F_ORDINI)
        │             │               │              │               │
        └─────────────┴───────────────┴──────────────┴───────────────┘
                                   │  (i fact agganciano le LU_*)
                                   ▼
[7] GOLD_DM aggregati A_*  (inbound, outbound, produttività, turno, stock, giacenze)
```

**Regola di precedenza:** le **dimensioni `LU_*` (fase 2) vanno costruite prima dei fact** (fase 3-5-6),
perché i fact vi agganciano le surrogate key. Gli **aggregati A_\* (fase 7) per ultimi** (leggono i fact).

---

## 3. Grafo delle dipendenze per flusso (sub-process)

Notazione: `bronze_x` → `silver_x` → `prep_x` → `gold_x`. Frecce = dipendenza dato.

### 3.1 Dimensioni (LU_*)
```
bronze: struttura_mag, tabgen, corsie, aree_merceologiche, carrellisti, preparatori,
        vettori(track/locale), apvpunto_vendita
   │
   ▼ silver_dim_sito / _operatore / _corriere / _topografia / _pdv / _articolo / _fornitore
   │      → dim_sito, dim_operatore, dim_corriere, dim_topografia, ...
   ▼ gold_dim_sito / _operatore / _corriere / _topografia / _pdv / _articolo / _fornitore
          → LU_SITO, LU_OPERATORE, LU_CORRIERE, LU_TOPOGRAFIA, LU_AREA_MERCL_LOGIS
(parallelo) Retail master già pubblicato: cdtdw.condiviso.LU_FORNITORE / LU_PDV / LU_ART_RADICE
```

### 3.2 Carichi → F_CARICO
```
bronze_carichi_testate (sto_tes_carichi) ┐
bronze_carichi_dettagli (sto_righe_carico)│
bronze_pesate (pesate)                    │
   ▼ silver_carichi_testate → carico_testata
   ▼ silver_carichi_dettagli → carico_dettaglio   (incrementale: _bronze_load_date)
   ▼ silver_pesate → pesata
        ▼ silver_prep_carico  → prep_logistica.carico   (join testata⋈dettaglio⋈pesata)
             ▼ gold_f_carico  → F_CARICO   (+ late: gold_late_arriving_handler)
```

### 3.3 Giacenze/Stock → F_GIACENZE_DAILY
```
bronze_catena (catena, SNAPSHOT) ┐   bronze_struttura_mag (anagrafica)
bronze_catena_esterni            │
   ▼ silver_catena_clean → catena_clean ; silver_catena_esterni_clean → catena_esterni_clean
        ▼ silver_catena_unificata → catena_unificata     (UNION + dedup chiave logica)
             ▼ silver_t_stock → t_stock                  (join struttura_mag, picking/scorte)
                  ▼ silver_prep_giacenze → prep_logistica.giacenze
                       ▼ gold_f_giacenze_daily → F_GIACENZE_DAILY
                       (silver_giacenze_aggregata → giacenza_aggregata, ramo mensile)
```

### 3.4 Spedizioni → F_PREP_SPED (prelievo) + F_TURNO_PREP_SITO (produttività)
```
bronze_storico_liste (storico_liste) ┐
bronze_prep_bolle_righe (storico_bolle)│
bronze_prep_riepiloghi (storico_riepiloghi)
   ▼ silver_storico_liste_clean / silver_storico_bolle_clean
        ▼ silver_storico_liste_uniche / silver_storico_bolle_uniche   (GROUP BY 8 chiavi)
             ▼ silver_prep_prep_sped → prep_logistica.prep_sped  (OUTER liste⋈bolle + riepiloghi)
                  ▼ gold_f_prep_sped → F_PREP_SPED
   ▼ silver_prep_riepiloghi → prep_riepilogo
        ▼ silver_prep_turno_prep_sito → prep_logistica.turno_prep_sito  (regola 30', produttività)
             ▼ gold_f_turno_prep_sito → F_TURNO_PREP_SITO
```

### 3.5 Trasporti → F_TRASPORTO (bolla) + F_ORDINI
```
bronze_spedizioni (SPEDIZIONI@TRACK) ┐
   ▼ silver_spedizioni_clean → spedizioni_clean  (map SP_*, normalize_sito, date)
        ▼ silver_prep_trasporto → prep_logistica.trasporto  (grana bolla)
             ▼ gold_f_trasporto → F_TRASPORTO
bronze_carichi_testate (sto_tes_carichi)
   ▼ silver_ordini → ordine
        ▼ silver_prep_ordini → prep_logistica.ordini
             ▼ gold_f_ordini → F_ORDINI
(anagrafica) silver_vettori_clean → vettori_track_clean ; silver_t_vettori → t_vettori
```

### 3.6 Fatti minori
```
bronze carrellisti/cartellino/dettaglio_carr → silver sessione/missione_carrellista
        → gold_f_movimentazione_carrellisti → F_MOVIMENTAZIONE_CARRELLISTI
bronze tracciace178 → silver tracciabilita_lotto → gold_f_tracciabilita_lotti → F_TRACCIABILITA_LOTTI
```

### 3.7 Aggregati (Gold_dm)
```
F_CARICO            → gold_a_inbound_mensile      → A_INBOUND_MENSILE
F_PREP_SPED         → gold_a_outbound_mensile     → A_OUTBOUND_MENSILE   (sorgente da confermare)
F_TURNO_PREP_SITO   → gold_dm_turno_prep_sito     → A_TURNO_PREP_SITO
F_TURNO_PREP_SITO   → gold_a_produttivita_mensile → A_PRODUTTIVITA_MENSILE
F_GIACENZE_DAILY    → gold_dm_giacenze_monthly    → A_GIACENZE_MONTHLY
A_GIACENZE_MONTHLY  → gold_a_stock_mensile        → A_STOCK_MENSILE
```

---

## 4. Inventario tabelle per schema

### 4.1 `bronze_<env>.logistica` (raw 1:1)
**Logistix (multi-sito):** sto_tes_carichi, sto_righe_carico, pesate, tracciace178, dettaglio_carr,
cartellino, imbfmovim, abb_tolti, carrellisti, preparatori, ricevitori, spedizionieri, struttura_mag,
corsie, tabgen, aree_merceologiche, classe_posto_pallet, catena, catena_esterni
**STAT:** storico_riepiloghi, testate_bolle, storico_bolle, storico_liste, buoni_eco, tipo_attivita_eco
**CDT_ESTR_RAW:** vettori (locale), automezzi, apvpunto_vendita, estrai_spedizioni
**TRACK:** vettori, spedizioni

### 4.2 `silver_<env>.logistica` (clean + elaborazioni intermedie)
**Cleansing 1:1:** carico_testata, carico_dettaglio, pesata, ordine, spedizioni_clean,
automezzi_clean, vettori_track_clean, vettori_locale_clean, catena_clean, catena_esterni_clean,
storico_liste_clean, storico_bolle_clean, prep_riepilogo, t_pdv, t_vettori,
sessione_carrellista, missione_carrellista, tracciabilita_lotto
**Elaborazioni intermedie:** storico_liste_uniche, storico_bolle_uniche, catena_unificata,
t_stock, s_trasp_mtv (rebuild WL), giacenza_aggregata
**Dimensioni (silver):** dim_sito, dim_operatore, dim_corriere, dim_topografia, dim_pdv,
dim_articolo, dim_fornitore

### 4.3 `silver_<env>.prep_logistica` (strato PREP — sorgente unica dei Gold)
carico, giacenze, prep_sped, turno_prep_sito, trasporto, ordini

### 4.4 `gold_<env>.logistica` (fact + dimensioni)
**Fact:** F_CARICO, F_GIACENZE_DAILY, F_PREP_SPED, F_TURNO_PREP_SITO, F_TRASPORTO, F_ORDINI,
F_MOVIMENTAZIONE_CARRELLISTI, F_TRACCIABILITA_LOTTI
**Dimensioni:** LU_SITO, LU_OPERATORE, LU_CORRIERE, LU_TOPOGRAFIA, LU_AREA_MERCL_LOGIS
(+ LU_PDV/LU_ART_RADICE/LU_FORNITORE da retail master `cdtdw.condiviso`)

### 4.5 `gold_<env>.logistica_dm` (aggregati)
A_INBOUND_MENSILE, A_OUTBOUND_MENSILE, A_PRODUTTIVITA_MENSILE, A_TURNO_PREP_SITO,
A_GIACENZE_MONTHLY, A_STOCK_MENSILE

---

## 5. Tabelle per flusso (vista sintetica)

| Flusso | Bronze | Silver clean / interm. | Silver prep | Gold |
|--------|--------|------------------------|-------------|------|
| **Dimensioni** | struttura_mag, tabgen, corsie, aree_merceologiche, carrellisti, preparatori, vettori, apvpunto_vendita | dim_sito, dim_operatore, dim_corriere, dim_topografia, dim_pdv, dim_articolo, dim_fornitore | — | LU_SITO, LU_OPERATORE, LU_CORRIERE, LU_TOPOGRAFIA, LU_AREA_MERCL_LOGIS |
| **Carichi** | sto_tes_carichi, sto_righe_carico, pesate | carico_testata, carico_dettaglio, pesata | carico | F_CARICO |
| **Giacenze** | catena, catena_esterni, struttura_mag | catena_clean, catena_esterni_clean, catena_unificata, t_stock | giacenze | F_GIACENZE_DAILY |
| **Spedizioni (prelievo)** | storico_liste, storico_bolle, storico_riepiloghi | storico_liste_clean/uniche, storico_bolle_clean/uniche | prep_sped | F_PREP_SPED |
| **Spedizioni (turno)** | storico_riepiloghi | prep_riepilogo | turno_prep_sito | F_TURNO_PREP_SITO |
| **Trasporti** | spedizioni (@TRACK), automezzi, vettori | spedizioni_clean, automezzi_clean, vettori_track_clean | trasporto | F_TRASPORTO |
| **Ordini** | sto_tes_carichi | ordine | ordini | F_ORDINI |
| **Carrellisti** | carrellisti, cartellino, dettaglio_carr | sessione_carrellista, missione_carrellista | — | F_MOVIMENTAZIONE_CARRELLISTI |
| **Tracciabilità** | tracciace178 | tracciabilita_lotto | — | F_TRACCIABILITA_LOTTI |

---

## 6. Note operative
- **Idempotenza:** giacenze/stock usano *dynamic partition overwrite* per giorno → ri-eseguire lo stesso `run_date` non duplica.
- **Incrementalità (OP-30, implementato 2026-06-11):** tre pilastri — (1) **Bronze pruning** `_row_hash` (le righe identiche non ri-datano `_bronze_load_date`; ~22% propagato sul test); (2) **clean** filtro `_bronze_load_date == run_date` + MERGE upsert null-safe + dedup; (3) **prep grandi** (uniche/prep_sped) pattern #2 **chiavi-impattate** + MERGE. Chiavi MERGE sempre null-safe (`<=>`). Attivazione pruning: **rebuild una-tantum** delle bronze (per creare `_row_hash`). Prep piccoli restano full (OP-34). Widget `full_refresh=true` per ricalcolo completo/backfill.
- **Late-arriving dimensions (OP-32):** non ancora implementato; gli orphan (`-1`) non si auto-correggono.
- **Deprecati (non eseguire):** silver_t_prep_sped, silver_t_trasp_mtv, silver_trasp_mtv_build, silver_trasporti, bronze WL* / s_trasp_mtv, prep_sped_integrata.
- **Runner locale:** `tests/local_bronze/run_notebook.py --notebook <path> --run-date YYYY-MM-DD [--siti ...] [--memory-gb N]`.
