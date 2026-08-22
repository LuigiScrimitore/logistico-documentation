# Pipeline Mapping — Logistico 2.0

Medallion Architecture (Bronze → Silver → Gold) su Databricks locale (Docker).  
Ultimo aggiornamento: 2026-06-17 | Pipeline validata end-to-end.

---

## Indice

1. [Sistemi sorgente](#1-sistemi-sorgente)
2. [Layer Landing](#2-layer-landing)
3. [Layer Bronze](#3-layer-bronze)
4. [Layer Silver](#4-layer-silver)
5. [Layer Gold](#5-layer-gold)
6. [Flussi end-to-end per area](#6-flussi-end-to-end-per-area)
7. [Tabelle dismesse](#7-tabelle-dismesse)
8. [Regole di layer](#8-regole-di-layer)
9. [Note operative](#9-note-operative)

---

## 1. Sistemi sorgente

| Sistema | Tipo connessione | Landing subdir | Siti / Schema |
|---------|-----------------|----------------|---------------|
| **LOGISTIX** | Oracle db-link multi-sito (`LOG_<SITO>`) | `logistix-landing/{sito}/` | 22 siti: laix, lbvx, lcax, leax, lfax, lfmx, lfqx, lfsx, lfvx, lgax, lgcx, lgnx, lgqx, lgrx, lgsx, lgvx, lgzx, lonx, losx, lslx, lsmx, lsvx |
| **STAT** | Oracle db-link unico (`STAT`) | `stat-landing/` | Schema STAT (prep spedizioni) |
| **CDT_ESTR_RAW** | Oracle diretto, schema `CDT_ESTR` | `cdt-estr-raw-landing/` | Anagrafiche locali CDT |
| **TRACK** | Oracle db-link `@TRACK` | `track-landing/` | Trasporti / vettori |

Tutte le estrazioni sono **READ-ONLY** — nessun update di flag CDC sul sorgente Oracle.

---

## 2. Layer Landing

File CSV generati da `scripts/landing_simulator/` (Python + cx_Oracle).  
Path base: `C:/PROGETTI/LOGISTICO_DATA/data/landing/`

### Modalità di estrazione

| Modalità | Descrizione | Filtro |
|----------|-------------|--------|
| `delta` | Finestra su colonna data (Julian Day o DATE) | `date_column >= run_date - N` |
| `full` | Snapshot completo della tabella | Nessun filtro (anagrafiche stabili) |
| `snapshot` | Full per run_date, partizionato per data | Una partizione per giorno |

### Tabelle per sistema

**LOGISTIX** (multi-sito — ogni tabella estratta per tutti i 22 siti attivi)

| Tabella Oracle | Modalità | Chiave di merge | Area |
|----------------|----------|-----------------|------|
| `sto_tes_carichi` | delta | `STCAR_NRO_CARICO`, `STCAR_COD_MAGAZZINO` | Carichi |
| `sto_righe_carico` | delta | `SRCAR_NRO_CARICO`, `SRCAR_COD_MSI`, `SRCAR_COD_MAGAZZINO` | Carichi |
| `pesate` | delta | `PSP_NUMETIC`, `PSP_DATABOLLA` | Carichi |
| `tracciace178` | delta | `CE178_NRO_ETICHETTA`, `CE178_NRO_CARICO` | Tracciabilità |
| `dettaglio_carr` | delta | `DTCRL_COD_CARRELLIST`, `DTCRL_DATA_RICH_ABB`, `DTCRL_ORA_RICH_ABB`, `DTCRL_COD_MSI` | Carrellisti |
| `cartellino` | delta | `CARTE_COD_CARRELLIST`, `CARTE_DATA` | Carrellisti |
| `imbfmovim` | delta | `IMFNUMBOL`, `IMFANNOBOL`, `IMFPRGRIF`, `IMFCODIMB` | Giacenze |
| `abb_tolti` | delta | `ABT_NRO_ETICHETTA`, `ABT_DATA_ANNULLO` | Tracciabilità |
| `catena` | snapshot | — | Giacenze |
| `catena_esterni` | snapshot | — | Giacenze |
| `carrellisti` | full | — | Anagrafica |
| `preparatori` | full | — | Anagrafica |
| `ricevitori` | full | — | Anagrafica |
| `spedizionieri` | full | — | Anagrafica |
| `struttura_mag` | full | — | Anagrafica |
| `corsie` | full | — | Anagrafica |
| `tabgen` | full | — | Anagrafica |
| `aree_merceologiche` | full | `ARM_TIPO_AREA = 1` (filtro business) | Anagrafica |
| `classe_posto_pallet` | full | — | Anagrafica |

**STAT** (db-link unico)

| Tabella Oracle | Modalità | Chiave di merge | Area |
|----------------|----------|-----------------|------|
| `storico_riepiloghi` | delta | `RPLPR_SITO`, `RPLPR_NRO_RIEPILOGO`, `RPLPR_DATA_PREPARAZ` | Prep spedizioni |
| `testate_bolle` | delta | `TEBO_SITO`, `TEBO_NRO_BOLLA`, `TEBO_DATA_BOLLA` | Prep spedizioni |
| `storico_bolle` | delta | `BOL_SITO`, `BOL_NRO_BOLLA`, `BOL_DATA_BOLLA`, `BOL_NRO_RIGA` | Prep spedizioni |
| `storico_liste` | delta | `LSPRL_SITO`, `LSPRL_NRO_GABBIA`, `LSPRL_NRO_ORDINE_NEG`, `LSPRL_COD_NEGOZIO`, `LSPRL_COD_MSI`, `LSPRL_DATA_ORDIN_NEG`, `LSPRL_SEQUE_PRELIEVO`, `LSPRL_FLAG_SCARTATO` | Prep spedizioni |
| `buoni_eco` | full | `BUONO_COD` | Anagrafica |
| `tipo_attivita_eco` | full | — | Anagrafica |

**CDT_ESTR_RAW**

| Tabella Oracle | Modalità | Area |
|----------------|----------|------|
| `AUTOMEZZI` | full | Trasporti |
| `APVPUNTO_VENDITA` | full | Anagrafica PDV |
| `ESTRAI_SPEDIZIONI` | full | Anagrafica stato sped. |

**TRACK**

| Tabella Oracle | Modalità | Chiave di merge | Area |
|----------------|----------|-----------------|------|
| `vettori` | full | — | Anagrafica |
| `SPEDIZIONI` | delta | `SP_ID` | Trasporti |

---

## 3. Layer Bronze

**Regola**: 1:1 rispetto alla sorgente landing. Nessuna derivazione, nessun join.  
Aggiunge metadati `_bronze_load_date`, `_sito_estrazione`. MERGE null-safe su chiave composita.  
Namespace: `bronze_dev.logistica.*`

### Carichi

| Notebook | Sorgente Landing | Tabella Bronze | Modalità | Volume tipico |
|----------|-----------------|----------------|----------|---------------|
| `bronze_carichi_testate.py` | logistix / sto_tes_carichi | `sto_tes_carichi` | DELTA_MERGE | ~1.400 righe/giorno |
| `bronze_carichi_dettagli.py` | logistix / sto_righe_carico | `sto_righe_carico` | DELTA_MERGE | ~30.000 righe/giorno |
| `bronze_pesate.py` | logistix / pesate | `pesate` | DELTA_MERGE | ~16.000 righe/giorno |
| `bronze_traccia_ce178.py` | logistix / tracciace178 | `tracciace178` | DELTA_MERGE | ~12.000 righe/giorno |

### Giacenze

| Notebook | Sorgente Landing | Tabella Bronze | Modalità | Volume tipico |
|----------|-----------------|----------------|----------|---------------|
| `bronze_catena.py` | logistix / catena | `catena` | SNAPSHOT | ~158.000 righe/giorno |
| `bronze_catena_esterni.py` | logistix / catena_esterni | `catena_esterni` | SNAPSHOT | ~5.300 righe/giorno |
| `bronze_movimenti_magazzino.py` | logistix / imbfmovim | `imbfmovim` | DELTA_MERGE | variabile |
| `bronze_giacenze_snapshot.py` | cnd / t_stock | `t_stock` | SNAPSHOT | ~150.000 righe (CND) |

### Prep spedizioni

| Notebook | Sorgente Landing | Tabella Bronze | Modalità | Volume tipico |
|----------|-----------------|----------------|----------|---------------|
| `bronze_prep_bolle_righe.py` | stat / storico_bolle | `storico_bolle` | DELTA_MERGE | ~430.000–880.000 righe/giorno |
| `bronze_prep_bolle_testate.py` | stat / testate_bolle | `testate_bolle` | DELTA_MERGE | ~2.000–9.000 righe/giorno |
| `bronze_prep_riepiloghi.py` | stat / storico_riepiloghi | `storico_riepiloghi` | DELTA_MERGE | ~9.700 righe/giorno |
| `bronze_storico_liste.py` | stat / storico_liste | `storico_liste` | DELTA_MERGE | ~198.000–270.000 righe/giorno |
| `bronze_timbrature.py` | cnd / t_prep_sped | `t_prep_sped` | DELTA_MERGE | variabile (CND) |

### Trasporti

| Notebook | Sorgente Landing | Tabella Bronze | Modalità | Volume tipico |
|----------|-----------------|----------------|----------|---------------|
| `bronze_spedizioni.py` | track / SPEDIZIONI | `spedizioni` | DELTA_MERGE | variabile |
| `bronze_vettori_track.py` | track / vettori | `vettori_track` | FULL_OVERWRITE | 96 righe |
| `bronze_automezzi.py` | cdt_estr_raw / AUTOMEZZI | `automezzi` | FULL_OVERWRITE | ~1.900 righe |
| `bronze_trasporti.py` | cnd / t_trasp_mtv | `t_trasp_mtv` | DELTA_MERGE | variabile (CND) |

### Carrellisti

| Notebook | Sorgente Landing | Tabella Bronze | Modalità | Volume tipico |
|----------|-----------------|----------------|----------|---------------|
| `bronze_cartellino.py` | logistix / cartellino | `cartellino` | DELTA_MERGE | ~180 righe/giorno |
| `bronze_missioni_carr.py` | logistix / dettaglio_carr | `dettaglio_carr` | DELTA_MERGE | ~10.000 righe/giorno |

### Anagrafiche

| Notebook | Sorgente Landing | Tabella Bronze | Modalità |
|----------|-----------------|----------------|----------|
| `bronze_struttura_mag.py` | logistix / struttura_mag | `struttura_mag` | FULL_OVERWRITE |
| `bronze_tabgen.py` | logistix / tabgen | `tabgen` | FULL_OVERWRITE |
| `bronze_carrellisti.py` | logistix / carrellisti | `carrellisti` | FULL_OVERWRITE |
| `bronze_preparatori.py` | logistix / preparatori | `preparatori` | FULL_OVERWRITE |
| `bronze_ricevitori.py` | logistix / ricevitori | `ricevitori` | FULL_OVERWRITE |
| `bronze_spedizionieri.py` | logistix / spedizionieri | `spedizionieri` | FULL_OVERWRITE |
| `bronze_corsie.py` | logistix / corsie | `corsie` | FULL_OVERWRITE |
| `bronze_aree_merceologiche.py` | logistix / aree_merceologiche | `aree_merceologiche` | FULL_OVERWRITE |
| `bronze_classe_posto_pallet.py` | logistix / classe_posto_pallet | `classe_posto_pallet` | FULL_OVERWRITE |
| `bronze_apvpunto_vendita.py` | cdt_estr_raw / APVPUNTO_VENDITA | `apvpunto_vendita` | FULL_OVERWRITE |
| `bronze_pdv.py` | cnd / t_pdv | `t_pdv` | FULL_OVERWRITE |
| `bronze_tipo_attivita.py` | stat / tipo_attivita_eco | `tipo_attivita_eco` | FULL_OVERWRITE |
| `bronze_buoni_eco.py` | stat / buoni_eco | `buoni_eco` | DELTA_MERGE |

---

## 4. Layer Silver

**Regola**: cleansing, normalizzazione sito, deduplicazione, derivazioni business (no join a dimensioni Gold).  
Namespace: `silver_dev.logistica.*` (tabelle operative) e `silver_dev.prep_logistica.*` (tabelle pronte per Gold).

### Dimensioni operative

| Notebook | Sorgente Bronze/Silver | Tabella Silver | Trasformazione |
|----------|----------------------|----------------|----------------|
| `silver_dim_sito.py` | `struttura_mag` | `silver_dev.logistica.dim_sito` | Dedup per MAG_SITO_COD, 22 righe |
| `silver_dim_topografia.py` | `struttura_mag` | `silver_dev.logistica.dim_topografia` | Dedup per SITO+COD_MAGAZZINO |
| `silver_dim_operatore.py` | `carrellisti`, `preparatori`, `ricevitori`, `spedizionieri` | `silver_dev.logistica.dim_operatore` | UNION 4 anagrafiche + self-healing NON_DEFINITO + membro ND |
| `silver_dim_corriere.py` | `vettori_track` | `silver_dev.logistica.dim_corriere` | Clean, dedup su VET_CODICE |
| `silver_dim_pdv.py` | `apvpunto_vendita` | `silver_dev.logistica.dim_pdv` | Clean 1:1 |

### Carichi

| Notebook | Sorgente Bronze | Tabella Silver | Trasformazione |
|----------|----------------|----------------|----------------|
| `silver_carichi_testate.py` | `sto_tes_carichi` | `silver_dev.logistica.carico_testata` | Clean, dedup, MERGE incrementale per run_date |
| `silver_carichi_dettagli.py` | `sto_righe_carico` | `silver_dev.logistica.carico_dettaglio` | Clean, dedup |
| `silver_pesate.py` | `pesate` | `silver_dev.logistica.pesata` | Clean, dedup |
| `silver_prep_carico.py` | `carico_testata` ⋈ `carico_dettaglio` ⋈ `pesata` | `silver_dev.prep_logistica.carico` | JOIN 3 tabelle, calcolo SCARTO_QTA, OVERWRITE dinamico per ANNO_MESE |
| `silver_traccia_ce178.py` | `tracciace178` | `silver_dev.logistica.tracciabilita_lotto` | Clean, dedup |

### Giacenze

| Notebook | Sorgente | Tabella Silver | Trasformazione |
|----------|----------|----------------|----------------|
| `silver_catena_clean.py` | `bronze.catena` | `silver_dev.logistica.catena_clean` | Sito canonico, cast date, deriva ART_RADICE/ART_VAR, SNAPSHOT append |
| `silver_catena_esterni_clean.py` | `bronze.catena_esterni` | `silver_dev.logistica.catena_esterni_clean` | Come catena_clean, SNAPSHOT append |
| `silver_catena_unificata.py` | `catena_clean` ∪ `catena_esterni_clean` | `silver_dev.logistica.catena_unificata` | UNION + dedup ST15 (ambiguità), SNAPSHOT overwrite |
| `silver_t_stock.py` | `catena_unificata` ⋈ `struttura_mag` | `silver_dev.logistica.t_stock` | JOIN sito canonico, aggregazione picking vs scorte (ST13/14), SNAPSHOT |
| `silver_prep_giacenze.py` | `t_stock` | `silver_dev.prep_logistica.giacenze` | Dedup per chiave, SNAPSHOT overwrite per DATA_FOTO |
| `silver_giacenze_aggregata.py` | `prep_logistica.giacenze` | `silver_dev.logistica.giacenza_aggregata` | GROUP BY MAG_COD + DATA_FOTO, SNAPSHOT overwrite |

### Prep spedizioni

| Notebook | Sorgente | Tabella Silver | Trasformazione |
|----------|----------|----------------|----------------|
| `silver_prep_riepiloghi.py` | `storico_riepiloghi` | `silver_dev.logistica.prep_riepilogo` | Clean, dedup, MERGE |
| `silver_storico_bolle_clean.py` | `storico_bolle` | `silver_dev.logistica.storico_bolle_clean` | Clean, dedup per chiave, MERGE upsert |
| `silver_storico_bolle_uniche.py` | `storico_bolle_clean` | `silver_dev.logistica.storico_bolle_uniche` | DISTINCT per bolla, MERGE upsert — DQ S7 (costanza attributi) |
| `silver_storico_liste_clean.py` | `storico_liste` | `silver_dev.logistica.storico_liste_clean` | Clean, dedup, MERGE upsert, watermark |
| `silver_storico_liste_uniche.py` | `storico_liste_clean` | `silver_dev.logistica.storico_liste_uniche` | DISTINCT per lista, MERGE upsert — DQ S7 |
| `silver_prep_bolle.py` | `storico_bolle_clean` ⋈ `testate_bolle` | `silver_dev.logistica.prep_bolla` | JOIN testata + righe bolle |
| `silver_timbrature_sessioni.py` | `t_prep_sped` | `silver_dev.logistica.timbratura_sessione` | Clean, calcolo DURATA_MIN (sessioni timbratura) |
| `silver_prep_sped_integrata.py` | `timbratura_sessione` ⋈ `prep_riepilogo` | `silver_dev.logistica.prep_sped_integrata` | JOIN + GROUP BY + aggregazioni (OP-17) |
| `silver_prep_turno_prep_sito.py` | `prep_riepilogo` ⋈ `prep_bolla` | `silver_dev.prep_logistica.turno_prep_sito` | GROUP BY turno/sito |
| `silver_prep_prep_sped.py` | `storico_liste_uniche` ⋈ `storico_bolle_uniche` | `silver_dev.prep_logistica.prep_sped` | JOIN, MERGE incrementale pattern #2 |

### Trasporti

| Notebook | Sorgente | Tabella Silver | Trasformazione |
|----------|----------|----------------|----------------|
| `silver_vettori_clean.py` | `vettori_track` | `silver_dev.logistica.vettori_track_clean` | Clean, dedup, FULL OVERWRITE |
| `silver_automezzi_clean.py` | `automezzi` | `silver_dev.logistica.automezzi_clean` | Clean 1:1, FULL OVERWRITE |
| `silver_spedizioni_clean.py` | `spedizioni` | `silver_dev.logistica.spedizioni_clean` | Clean, dedup su SP_ID, MERGE |
| `silver_ordini.py` | `sto_tes_carichi` | `silver_dev.logistica.ordine` | Filtro `FLAG_TRASFERITO != 'S'` (ordini pendenti), dedup |
| `silver_trasp_mtv_build.py` | `automezzi_clean` ⋈ `spedizioni_clean` | `silver_dev.logistica.s_trasp_mtv` | Rebuild catena trasporti (sostituzione WL2) |
| `silver_prep_trasporto.py` | `spedizioni_clean` ⋈ `s_trasp_mtv` | `silver_dev.prep_logistica.trasporto` | JOIN + calcoli, UNION CONS/TRANSITO, MERGE |
| `silver_prep_ordini.py` | `silver_dev.logistica.ordine` | `silver_dev.prep_logistica.ordini` | Normalizzazione per Gold, FULL OVERWRITE |
| `silver_costo_trasporto.py` | `spedizioni_clean` ⋈ `vettori_track_clean` | `silver_dev.logistica.costo_trasporto` | Calcolo costo per movimento |

### Tracciabilità e carrellisti

| Notebook | Sorgente | Tabella Silver | Trasformazione |
|----------|----------|----------------|----------------|
| `silver_tracciabilita_lotto.py` | `tracciace178` | `silver_dev.logistica.tracciabilita_lotto` | Aggregazione per SITO+CARICO+DATA+COD_MSI (numEtichette, numAnnullate, numTrasferite), MERGE |
| `silver_missione_carrellista.py` | `dettaglio_carr` | `silver_dev.logistica.missione_carrellista` | Clean, dedup |
| `silver_sessione_carrellista.py` | `missione_carrellista` | `silver_dev.logistica.sessione_carrellista` | Aggregazione per OPERATORE+SESSIONE |

### Tabelle t_* (interfaccia legacy CDT)

Tabelle con prefisso `t_` sono interfacce di compatibilità verso il layer legacy CDT — alimentate da Silver e lette da consumatori esterni.

| Notebook | Sorgente | Tabella Silver |
|----------|----------|----------------|
| `silver_t_pdv.py` | `apvpunto_vendita` (+ left join `gfdit` dismessa) | `silver_dev.logistica.t_pdv` |
| `silver_t_vettori.py` | `vettori_track_clean` | `silver_dev.logistica.t_vettori` |
| `silver_t_stock.py` | `catena_unificata` ⋈ `struttura_mag` | `silver_dev.logistica.t_stock` |
| `silver_t_prep_sped.py` | `bronze.t_prep_sped` | `silver_dev.logistica.t_prep_sped` |
| `silver_t_trasp_mtv.py` | `s_trasp_mtv` | `silver_dev.logistica.t_trasp_mtv` |

---

## 5. Layer Gold

**Regola**: join a dimensioni lookup (LU_*), calcolo FK surrogate (`surrogate_key_fallback`), scrittura fact/aggregati. Nessuna derivazione business — solo normalizzazione e aggancio dimensionale.  
Namespace: `gold_dev.logistica.*` (fact + lookup) e `gold_dev.logistica_dm.*` (aggregati datamart).

### Lookup condivise (da CDT_DW legacy)

| Notebook | Sorgente | Gold Target | Righe tipiche |
|----------|----------|-------------|---------------|
| `gold_lu_from_cdtdw.py` | `cdtdw.condiviso.*` | `gold_dev.logistica.LU_ART_RADICE` | 693.879 |
| | | `gold_dev.logistica.LU_FORNITORE` | 11.478 |
| | | `gold_dev.logistica.LU_PDV` | 4.185 |
| | | `gold_dev.logistica.LU_GIORNO` | 8.035 |
| | | `gold_dev.logistica.LU_MESE` | 264 |

### Lookup logistica

| Notebook | Sorgente Silver | Gold Target | Righe tipiche |
|----------|----------------|-------------|---------------|
| `gold_dim_sito.py` | `silver_dev.logistica.dim_sito` | `gold_dev.logistica.LU_SITO` | 22 |
| `gold_dim_operatore.py` | `silver_dev.logistica.dim_operatore` | `gold_dev.logistica.LU_OPERATORE` | ~16.082 (incl. membro ND) |
| `gold_dim_corriere.py` | `silver_dev.logistica.dim_corriere` | `gold_dev.logistica.LU_CORRIERE` | 96 |
| `gold_dim_topografia.py` | `silver_dev.logistica.dim_topografia` | `gold_dev.logistica.LU_TOPOGRAFIA` | ~379.711 |
| `gold_dim_struttura_merceologica.py` | `silver_dev.logistica.aree_merceologiche` | `gold_dev.logistica.LU_AREA_MERCL_LOGIS` | 19 |

### Fact tables

| Notebook | Sorgente Silver | Gold Target | Grain | Partizione | Orphan rate |
|----------|----------------|-------------|-------|------------|-------------|
| `gold_f_carico.py` | `prep_logistica.carico` | `gold_dev.logistica.F_CARICO` | 1 riga = dettaglio carico | ANNO_MESE | 0.0% su tutti i FK |
| `gold_f_prep_sped.py` | `prep_logistica.prep_sped` | `gold_dev.logistica.F_PREP_SPED` | SITO + RIEPILOGO_NRO + OPERATORE | — | 0.0% |
| `gold_f_turno_prep_sito.py` | `prep_logistica.turno_prep_sito` | `gold_dev.logistica.F_TURNO_PREP_SITO` | SITO + DATA + TURNO | — | 0.0% |
| `gold_f_trasporto.py` | `prep_logistica.trasporto` | `gold_dev.logistica.F_TRASPORTO` | 1 riga = movimento (CONS/TRANSITO) | GIORNO_BOLLA_SPED_ID | 0.0% |
| `gold_f_ordini.py` | `prep_logistica.ordini` | `gold_dev.logistica.F_ORDINI` | 1 riga = ordine | — | 0.0% |
| `gold_f_giacenze_daily.py` | `prep_logistica.giacenze` | `gold_dev.logistica.F_GIACENZE_DAILY` | DATA_FOTO + ART + MAG | DATA_FOTO | 0.0% |
| `gold_f_giacenze_monthly.py` | `prep_logistica.giacenze` | `gold_dev.logistica.F_GIACENZE_MONTHLY` | ANNO_MESE + ART + MAG | — | — |
| `gold_f_tracciabilita_lotti.py` | `silver_dev.logistica.tracciabilita_lotto` | `gold_dev.logistica.F_TRACCIABILITA_LOTTI` | CARICO + LOTTO + DATA | ANNO_MESE | — |
| `gold_f_movimentazione_carrellisti.py` | `silver_dev.logistica.missione_carrellista` | `gold_dev.logistica.F_MOVIMENTAZIONE_CARRELLISTI` | 1 riga = missione | DATA_PRESENZA | — |
| `gold_late_arriving_handler.py` | `F_CARICO` (finestra 90gg) | — | Handler late-arriving | — | — |

### Aggregati datamart (`gold_dev.logistica_dm`)

| Notebook | Sorgente Gold | DM Target | Grain |
|----------|--------------|-----------|-------|
| `gold_a_inbound_mensile.py` | `F_CARICO` | `A_INBOUND_MENSILE` | FORNITORE + SITO + ANNO_MESE |
| `gold_a_outbound_mensile.py` | `F_TRASPORTO` | `A_OUTBOUND_MENSILE` | CORRIERE + SITO + ANNO_MESE |
| `gold_a_stock_mensile.py` | `F_GIACENZE_MONTHLY` | `A_STOCK_MENSILE` | MAG + ANNO_MESE |
| `gold_a_produttivita_mensile.py` | `F_MOVIMENTAZIONE_CARRELLISTI` | `A_PRODUTTIVITA_MENSILE` | OPERATORE + ANNO_MESE |
| `gold_dm_giacenze_monthly.py` | `F_GIACENZE_DAILY` | `A_GIACENZE_MONTHLY` | MAG + ANNO_MESE |
| `gold_dm_turno_prep_sito.py` | `F_TURNO_PREP_SITO` | `A_TURNO_PREP_SITO` | SITO + DATA + TURNO |

---

## 6. Flussi end-to-end per area

### Carichi (Inbound)

```
Oracle LOGISTIX (22 siti)
  sto_tes_carichi, sto_righe_carico, pesate
      │ delta, Julian Day
      ▼
Landing: logistix-landing/{sito}/
      │ DELTA_MERGE, chiave composita
      ▼
Bronze: bronze_dev.logistica.sto_tes_carichi / sto_righe_carico / pesate
      │ clean 1:1, dedup, MERGE incrementale
      ▼
Silver: silver_dev.logistica.carico_testata / carico_dettaglio / pesata
      │ JOIN 3 tabelle, calc SCARTO_QTA
      ▼
Silver: silver_dev.prep_logistica.carico  (~44.700 righe/mese)
      │ join LU_*, surrogate_key_fallback (default_val="-1")
      ▼
Gold:  gold_dev.logistica.F_CARICO  [grain: dettaglio carico, part. ANNO_MESE]
      │ GROUP BY FORNITORE + SITO + ANNO_MESE
      ▼
DM:    gold_dev.logistica_dm.A_INBOUND_MENSILE  (~1.854 righe)
```

### Giacenze (Stock)

```
Oracle LOGISTIX (22 siti)
  catena + catena_esterni
      │ snapshot giornaliero
      ▼
Landing: logistix-landing/{sito}/
      │ SNAPSHOT, schema-on-read
      ▼
Bronze: bronze_dev.logistica.catena / catena_esterni  (~163.000 righe/giorno)
      │ clean, sito canonico, deriva ART_RADICE/ART_VAR, SNAPSHOT append
      ▼
Silver: silver_dev.logistica.catena_clean / catena_esterni_clean
      │ UNION + dedup ST15
      ▼
Silver: silver_dev.logistica.catena_unificata  (~163.000 righe)
      │ JOIN struttura_mag, aggregazione ST13/14
      ▼
Silver: silver_dev.logistica.t_stock → prep_logistica.giacenze  (~54.700 righe)
      │ join LU_SITO, lookup
      ▼
Gold:  gold_dev.logistica.F_GIACENZE_DAILY  [grain: DATA_FOTO + ART + MAG]
      │ GROUP BY MAG + ANNO_MESE
      ▼
DM:    gold_dev.logistica_dm.A_GIACENZE_MONTHLY / A_STOCK_MENSILE  (~54.961 righe)
```

### Prep spedizioni (Fulfillment)

```
Oracle STAT
  storico_riepiloghi, storico_bolle, storico_liste
      │ delta, Julian Day
      ▼
Landing: stat-landing/
      │ DELTA_MERGE
      ▼
Bronze: bronze_dev.logistica.storico_riepiloghi / storico_bolle / storico_liste
      │ clean, dedup, MERGE upsert + watermark
      ▼
Silver clean: storico_bolle_clean, storico_liste_clean
      │ DISTINCT pattern #2 (incrementale su chiavi impattate)
      ▼
Silver uniche: storico_bolle_uniche (~428.000), storico_liste_uniche (~197.000)
      │ JOIN liste ⋈ bolle
      ▼
Silver: silver_dev.prep_logistica.prep_sped
      │ join LU_*, surrogate_key_fallback null_val="ND" per PREPARATORE
      ▼
Gold:  gold_dev.logistica.F_PREP_SPED  [grain: SITO + RIEPILOGO + OPERATORE]
       gold_dev.logistica.F_TURNO_PREP_SITO  [grain: SITO + DATA + TURNO]
```

### Trasporti (Outbound)

```
Oracle TRACK
  SPEDIZIONI + vettori
      │ delta (SP_DATABOLLA DATE) + full
      ▼
Landing: track-landing/
      │ DELTA_MERGE (SP_ID) + FULL_OVERWRITE
      ▼
Bronze: bronze_dev.logistica.spedizioni / vettori_track
      │ clean, dedup
      ▼
Silver: spedizioni_clean, automezzi_clean (da CDT_ESTR)
      │ JOIN automezzi → rebuild catena trasporti
      ▼
Silver: silver_dev.logistica.s_trasp_mtv
      │ JOIN + UNION CONS/TRANSITO, calc
      ▼
Silver: silver_dev.prep_logistica.trasporto  (~40.900 righe)
      │ join LU_SITO, LU_CORRIERE
      ▼
Gold:  gold_dev.logistica.F_TRASPORTO  [grain: movimento, part. GIORNO_BOLLA]
       gold_dev.logistica.F_ORDINI     [grain: ordine]
      │ GROUP BY CORRIERE + SITO + ANNO_MESE
      ▼
DM:    gold_dev.logistica_dm.A_OUTBOUND_MENSILE  (~129 righe)
```

### Tracciabilità lotti

```
Oracle LOGISTIX (22 siti)
  tracciace178 (CE178_*)
      │ delta
      ▼
Bronze: bronze_dev.logistica.tracciace178  (~12.000 righe/giorno)
      │ aggregazione per SITO+CARICO+DATA+COD_MSI
      ▼
Silver: silver_dev.logistica.tracciabilita_lotto  (~8.800 lotti)
      ▼
Gold:  gold_dev.logistica.F_TRACCIABILITA_LOTTI  [part. ANNO_MESE]
```

### Carrellisti

```
Oracle LOGISTIX (22 siti)
  cartellino (sessioni) + dettaglio_carr (missioni)
      │ delta
      ▼
Bronze: bronze_dev.logistica.cartellino (~180/g) / dettaglio_carr (~10.000/g)
      │ clean, dedup
      ▼
Silver: missione_carrellista → sessione_carrellista
      ▼
Gold:  gold_dev.logistica.F_MOVIMENTAZIONE_CARRELLISTI  (~179 righe/giorno)
      │ GROUP BY OPERATORE + ANNO_MESE
      ▼
DM:    gold_dev.logistica_dm.A_PRODUTTIVITA_MENSILE  (~18 righe)
```

---

## 7. Tabelle dismesse

Tabelle rimosse dalla pipeline — non estrarre, non referenziare nei notebook.

| Tabella | Sistema origine | Motivo dismissione |
|---------|-----------------|--------------------|
| `artdgene` | CDT_ESTR | Sinonimo su db-link remoto morto (@TRASPO). Dead-join in AS-IS (nessuna colonna selezionata). |
| `cndpardgene` | CDT_ESTR | Nessun riferimento in pipeline TO-BE. |
| `ass_merceologiche` | CDT_ESTR | Sinonimo @TRASPO inesistente. Nessun consumer. |
| `macro_aggregazioni` | CDT_ESTR | Idem @TRASPO. Nessun consumer. |
| `cndstostock` | CDT_ESTR | Non raggiungibile. Silver fallback: `VAL_STOCK_* → 0` (fisiologico). |
| `gfdit` | CDT_ESTR | Non raggiungibile. Silver fallback: `PDV_FID_COD → '00000'` (fisiologico). |
| `vettori` (CDT_ESTR.VETTORI) | CDT_ESTR | Doppione di `vettori@TRACK`. Fonte unica = TRACK. |
| `contratti_corrieri` | logistix_wl1 | Tabella ORA-00942 (non esiste in Oracle). Schema dismesso. |
| `ordini_testate` | logistix_wl1 | Idem — schema logistix_wl1 dismesso. |
| `ordini_righe` | logistix_wl1 | Idem. |
| `swap` (logistix_wl1) | logistix_wl1 | Idem. |

---

## 8. Regole di layer

### Bronze
- **1:1 con sorgente**: nessuna derivazione, nessun join tra tabelle
- **Schema-on-read**: colonne lette così come arrivano; cast solo se necessario per MERGE
- **Metadati aggiunti**: `_bronze_load_date` (data run), `_sito_estrazione` (sito di provenienza per multi-sito)
- **MERGE null-safe**: chiave composita con operatore `<=>` per gestire NULL in chiave (es. `BOL_NRO_RIGA`)
- **Deduplicazione pre-MERGE**: `ROW_NUMBER() OVER (PARTITION BY chiave ORDER BY ...)` prima del merge

### Silver
- **Normalizzazione sito**: `normalize_sito()` da `logistica_utils` — converte formato numerico (`"20"`) in codice alfa (`"LGAX"`) tramite tabgen
- **surrogate_key_fallback**: `default_val="-1"` per FK orfane; `null_val="ND"` per FK che sono NULL per natura (es. OPERATORE_COD, PREPARATORE_COD)
- **DQ check_not_null**: applicato su chiavi business obbligatorie (non su FK nullable by design)
- **DQ check_row_count**: soglia `min_rows=1` — emette WARNING se 0 righe (non FAIL)
- **DQ S7 (costanza attributi)**: `storico_bolle_uniche` e `storico_liste_uniche` — 11 attributi non costanti per bolla sono fisiologici (aggiornamenti progressivi in sorgente)
- **Pattern #2 incrementale**: ricalcolo delle sole chiavi impattate nel batch, non full-scan
- **NO_DATA graceful exit**: se sorgente assente o vuota, `dbutils.notebook.exit("NO_DATA")` — contato come OK dal runner

### Gold
- **Surrogate key**: tutti i FK risolti via `surrogate_key_fallback` prima della scrittura
- **Membro ND**: `dim_operatore` contiene la riga con `OPERATORE_COD="ND"`, `TIPO=NON_RILEVATO` — assorbe i NULL FK a Gold senza orphan
- **Orphan rate**: check post-join, soglia 0% — warning se > 0
- **Partizioni**: fact tables partizionate per data o ANNO_MESE per performance query
- **Aggregati DM**: sempre derivati da fact Gold — mai da Silver direttamente

---

## 9. Note operative

### Dipendenze di ordinamento Silver
I notebook Silver sono eseguiti in ordine alfabetico da `run_all_silver.py`. Alcune dipendenze inter-notebook non sono rispettate nell'ordine corrente:

| Notebook dipendente | Dipende da | Effetto con ordine attuale |
|--------------------|------------|---------------------------|
| `silver_t_stock` [8] | `silver_catena_unificata` [20] | Legge catena del run precedente (già in warehouse) — fisiologico |
| `silver_prep_prep_sped` [24] | `silver_storico_liste_uniche` [31] | Legge liste del run precedente — fisiologico |
| `silver_giacenze_aggregata` [21] | `silver_prep_giacenze` [22] | 0 righe se t_stock non aggiornato — fisiologico |

In produzione Databricks Jobs, le dipendenze saranno gestite tramite DAG task; localmente il comportamento è corretto perché ogni run legge i dati scritti dal run precedente.

### Sorgenti CND non estratte giornalmente
Le tabelle con prefisso `t_` provenienti da CND (`t_pdv`, `t_stock`, `t_prep_sped`, `t_trasp_mtv`) non hanno estrazione giornaliera automatica. I notebook Silver corrispondenti emettono `NO_DATA` graceful quando la landing è assente — non bloccano il run.

### Membro ND in dim_operatore
La riga `OPERATORE_COD="ND"` è inserita da `silver_dim_operatore` al termine di ogni run. Garantisce che i NULL FK in `F_CARICO.OPERATORE_COD` e `F_TURNO_PREP_SITO.PREPARATORE_COD` si aggancino al membro ND invece di diventare orfani (-1).

### BOL_NRO_RIGA è nullable
`storico_bolle.BOL_NRO_RIGA` ha ~2.141 NULL fisiologici per run. È usata come chiave MERGE con operatore null-safe (`<=>`), non come campo business obbligatorio — esclusa da `check_not_null`.
