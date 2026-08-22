# Decision Matrix — Strategia di Ingestion per Tabella Sorgente

**Progetto:** Logistico 2.0 — Architettura Push Landing Zone → Delta Lake Bronze  
**Autore:** Cloud Solution Architect  
**Data:** 2026-05-30  
**Versione:** 2.0

---

## Indice

1. [Cambio architetturale](#1-cambio-architetturale)
2. [Pattern di ingestion adottato](#2-pattern-di-ingestion-adottato)
3. [Legenda](#3-legenda)
4. [Decision Matrix — Logistix](#4-decision-matrix--logistix)
5. [Decision Matrix — CND/CDT_SOURCE](#5-decision-matrix--cndcdt_source)
6. [Decision Matrix — STAT](#6-decision-matrix--stat)
7. [Merge Keys Bronze per tabella](#7-merge-keys-bronze-per-tabella)
8. [Configurazione landing zone](#8-configurazione-landing-zone)

---

## 1. Cambio architetturale

A partire dalla versione 2.0 il pattern di ingestion è cambiato radicalmente:

| Aspetto | Versione 1.x (deprecata) | Versione 2.0 (attuale) |
|---|---|---|
| Modalità lettura | Pull JDBC da Oracle | Push CSV su landing zone ADLS Gen2 |
| Connettività Oracle | Richiesta (JDBC, firewall, credenziali) | Non richiesta |
| Watermark | Colonna Oracle (es. `DATA_ESTRAZIONE_DWH`) | Path della landing zone (`YYYY/MM/DD`) |
| Partizionamento | `numPartitions` JDBC | Non applicabile (CSV già splittato per giorno) |
| Scrittura Bronze | Append-only con dedup watermark | MERGE INTO (upsert) su chiavi business |
| Formato dati | Record Oracle via driver JDBC | File CSV UTF-8, separatore `;` |
| Frequenza | Giornaliero (pull schedulato) | Giornaliero (push da sistema sorgente) |

---

## 2. Pattern di ingestion adottato

```
Sistema sorgente          Landing Zone ADLS Gen2             Bronze Delta Lake
(Logistix / CND / STAT)       (blob container)              (Unity Catalog)

     Delta giornaliero         landing/
     in formato CSV      ────► {sistema}/                ────► MERGE INTO
     (struttura identica        {[sito]/}                      {catalog}.logistica.{table}
      alla tabella sorgente)    {tabella}/
                                YYYY/MM/DD/
                                *.csv
```

**Colonne aggiunte da Bronze (metadati ingestion):**

| Colonna | Tipo | Descrizione |
|---|---|---|
| `_bronze_load_date` | DATE | Data di riferimento del carico (dal path landing) |
| `_bronze_insert_ts` | TIMESTAMP | Timestamp di prima inserzione nella tabella Bronze |
| `_source_file`      | STRING | Path completo del file CSV sorgente (tracciabilità) |

---

## 3. Legenda

- **Sistema:** Logistix = gestione magazzino operativo multi-sito | CND = distribuzione/logistica CND | STAT = statistiche/buoni economali
- **Formato file:** CSV, encoding UTF-8, separatore `;`, header in prima riga
- **Struttura CSV:** identica alla tabella sorgente (stesse colonne, stesso ordine)
- **Frequenza push:** giornaliero (entro le 04:00 ora locale), lancio Bronze ore 05:00
- **Siti Logistix:** lgax, lgcx, lcax, lccx, lexx, locx, lonx, lscx, lslx
- **Multi-sito:** ogni sito ha la propria cartella; la tabella Bronze è unica e contiene tutti i siti (discriminati da `MAG_SITO_COD`)

---

## 4. Decision Matrix — Logistix

| Tabella | Path landing zone | Siti | Merge keys Bronze | Note |
|---|---|---|---|---|
| `sto_tes_carichi` | `landing/logistix/{sito}/sto_tes_carichi/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, STCAR_NRO_CARICO, STCAR_COD_MAGAZZINO` | Testate carichi ricevimento |
| `sto_righe_carico` | `landing/logistix/{sito}/sto_righe_carico/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, SRCAR_NRO_CARICO, SRCAR_COD_MSI, SRCAR_COD_MAGAZZINO` | Righe dettaglio carico |
| `pesate` | `landing/logistix/{sito}/pesate/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, PSP_NUMETIC, PSP_DATABOLLA` | Pesature prodotti in ricezione |
| `tracciace178` | `landing/logistix/{sito}/tracciace178/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, CE178_NRO_ETICHETTA, CE178_NRO_CARICO` | Reg. CE 178/2002 — retention obbligatoria 5 anni, NO delete |
| `dettaglio_carr` | `landing/logistix/{sito}/dettaglio_carr/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, DTCRL_COD_CARRELLIST, DTCRL_DATA_RICH_ABB, DTCRL_ORA_RICH_ABB, DTCRL_COD_MSI` | Missioni carrellisti |
| `imbfmovim` | `landing/logistix/{sito}/imbfmovim/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, IMFNUMBOL, IMFANNOBOL, IMFPRGRIF, IMFCODIMB` | Movimenti imballi/fustame |
| `cartellino` | `landing/logistix/{sito}/cartellino/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, CARTE_COD_CARRELLIST, CARTE_DATA` | Presenze carrellisti (giornaliero) |
| `carrellisti` | `landing/logistix/{sito}/carrellisti/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, CRLLS_COD_CARRELLIST` | Anagrafica carrellisti |
| `preparatori` | `landing/logistix/{sito}/preparatori/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, PREP_COD_PREPARATOR` | Anagrafica preparatori ordini |
| `ricevitori` | `landing/logistix/{sito}/ricevitori/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, RICV_COD_RICEVITOR` | Anagrafica ricevitori |
| `spedizionieri` | `landing/logistix/{sito}/spedizionieri/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, SPE_CODICE` | Anagrafica spedizionieri |
| `struttura_mag` | `landing/logistix/{sito}/struttura_mag/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, STRM_COD_MAGAZZINO, STRM_CORSIA, STRM_COLONNA, STRM_PIANO` | Struttura fisica magazzino (postazioni pallet) |
| `corsie` | `landing/logistix/{sito}/corsie/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, CORSI_COD_MAGAZZINO, CORSI_CORSIA` | Anagrafica corsie |
| `tabgen` | `landing/logistix/{sito}/tabgen/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, TGEN_NRO_TAB, TGEN_COD_SEDE, TGEN_CHIAVE1_TAB` | Tabelle generali di configurazione |
| `aree_merceologiche` | `landing/logistix/{sito}/aree_merceologiche/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, ARM_COD_AREA_MERCEOLOGICA` | Anagrafica aree merceologiche |
| `classe_posto_pallet` | `landing/logistix/{sito}/classe_posto_pallet/YYYY/MM/DD/*.csv` | Tutti | `MAG_SITO_COD, CLPAL_COD_CLAS_POSPA` | Classi posto pallet |
| `storico_riepiloghi` | `landing/logistix/lgax/storico_riepiloghi/YYYY/MM/DD/*.csv` | **solo lgax** | `RPLPR_SITO, RPLPR_NRO_RIEPILOGO, RPLPR_DATA_PREPARAZ` | Storico riepiloghi preparazione (solo sito lgax) |
| `testate_bolle` | `landing/logistix/lgax/testate_bolle/YYYY/MM/DD/*.csv` | **solo lgax** | `TEBO_SITO, TEBO_NRO_BOLLA, TEBO_DATA_BOLLA` | Testate bolle spedizione (solo sito lgax) |
| `storico_bolle` | `landing/logistix/lgax/storico_bolle/YYYY/MM/DD/*.csv` | **solo lgax** | `BOL_SITO, BOL_NRO_BOLLA, BOL_DATA_BOLLA, BOL_NRO_RIGA` | Righe storico bolle (solo sito lgax) |

---

## 5. Decision Matrix — CND/CDT_SOURCE

| Tabella | Path landing zone | Merge keys Bronze | Note |
|---|---|---|---|
| `t_stock` | `landing/cnd/t_stock/YYYY/MM/DD/*.csv` | `STKNMAG, STKCINT` | Stock magazzino CND per articolo/magazzino |
| `t_prep_sped` | `landing/cnd/t_prep_sped/YYYY/MM/DD/*.csv` | `MAG_SITO_COD, NUM_RIEP, SOCIO_COD, ART_COD` | Preparazione spedizioni CND |
| `t_pdv` | `landing/cnd/t_pdv/YYYY/MM/DD/*.csv` | `PUVCODICE` | Anagrafica punti di vendita |
| `t_vettori` | `landing/cnd/t_vettori/YYYY/MM/DD/*.csv` | `VET_CODICE` | Anagrafica vettori/corrieri CND |
| `t_trasp_mtv` | `landing/cnd/t_trasp_mtv/YYYY/MM/DD/*.csv` | `SP_ID, MAG_SITO_COD, DATABOLLA, NUMBOLLA` | Movimenti trasporto CND |
| `t_nodi_rete` | `landing/cnd/t_nodi_rete/YYYY/MM/DD/*.csv` | `DN_SITO_ORIG, DN_SITO_DEST, DN_TIPO_SITO_ORIG, DN_TIPO_SITO_DEST` | Topologia rete distributiva CND |
| `t_ord_forn_righe` | `landing/cnd/t_ord_forn_righe/YYYY/MM/DD/*.csv` | *(da definire con il team CND)* | Righe ordini fornitori CND — merge keys da verificare con sorgente |

---

## 6. Decision Matrix — STAT

| Tabella | Path landing zone | Merge keys Bronze | Note |
|---|---|---|---|
| `buoni_eco` | `landing/stat/buoni_eco/YYYY/MM/DD/*.csv` | `BUONO_COD` | Buoni economali |
| `tipo_attivita` | `landing/stat/tipo_attivita/YYYY/MM/DD/*.csv` | `TIPO_ATTIVITA_COD` | Anagrafica tipi attività |

---

## 7. Merge Keys Bronze per tabella

Tabella di riferimento rapido: merge keys per ogni tabella Bronze, da passare al widget `merge_keys` del template.

| `table_name` (widget) | `source_system` | `merge_keys` (widget, comma-separated) |
|---|---|---|
| `sto_tes_carichi` | `logistix` | `MAG_SITO_COD,STCAR_NRO_CARICO,STCAR_COD_MAGAZZINO` |
| `sto_righe_carico` | `logistix` | `MAG_SITO_COD,SRCAR_NRO_CARICO,SRCAR_COD_MSI,SRCAR_COD_MAGAZZINO` |
| `pesate` | `logistix` | `MAG_SITO_COD,PSP_NUMETIC,PSP_DATABOLLA` |
| `tracciace178` | `logistix` | `MAG_SITO_COD,CE178_NRO_ETICHETTA,CE178_NRO_CARICO` |
| `dettaglio_carr` | `logistix` | `MAG_SITO_COD,DTCRL_COD_CARRELLIST,DTCRL_DATA_RICH_ABB,DTCRL_ORA_RICH_ABB,DTCRL_COD_MSI` |
| `imbfmovim` | `logistix` | `MAG_SITO_COD,IMFNUMBOL,IMFANNOBOL,IMFPRGRIF,IMFCODIMB` |
| `cartellino` | `logistix` | `MAG_SITO_COD,CARTE_COD_CARRELLIST,CARTE_DATA` |
| `carrellisti` | `logistix` | `MAG_SITO_COD,CRLLS_COD_CARRELLIST` |
| `preparatori` | `logistix` | `MAG_SITO_COD,PREP_COD_PREPARATOR` |
| `ricevitori` | `logistix` | `MAG_SITO_COD,RICV_COD_RICEVITOR` |
| `spedizionieri` | `logistix` | `MAG_SITO_COD,SPE_CODICE` |
| `struttura_mag` | `logistix` | `MAG_SITO_COD,STRM_COD_MAGAZZINO,STRM_CORSIA,STRM_COLONNA,STRM_PIANO` |
| `corsie` | `logistix` | `MAG_SITO_COD,CORSI_COD_MAGAZZINO,CORSI_CORSIA` |
| `tabgen` | `logistix` | `MAG_SITO_COD,TGEN_NRO_TAB,TGEN_COD_SEDE,TGEN_CHIAVE1_TAB` |
| `aree_merceologiche` | `logistix` | `MAG_SITO_COD,ARM_COD_AREA_MERCEOLOGICA` |
| `classe_posto_pallet` | `logistix` | `MAG_SITO_COD,CLPAL_COD_CLAS_POSPA` |
| `storico_riepiloghi` | `logistix` | `RPLPR_SITO,RPLPR_NRO_RIEPILOGO,RPLPR_DATA_PREPARAZ` |
| `testate_bolle` | `logistix` | `TEBO_SITO,TEBO_NRO_BOLLA,TEBO_DATA_BOLLA` |
| `storico_bolle` | `logistix` | `BOL_SITO,BOL_NRO_BOLLA,BOL_DATA_BOLLA,BOL_NRO_RIGA` |
| `t_stock` | `cnd` | `STKNMAG,STKCINT` |
| `t_prep_sped` | `cnd` | `MAG_SITO_COD,NUM_RIEP,SOCIO_COD,ART_COD` |
| `t_pdv` | `cnd` | `PUVCODICE` |
| `t_vettori` | `cnd` | `VET_CODICE` |
| `t_trasp_mtv` | `cnd` | `SP_ID,MAG_SITO_COD,DATABOLLA,NUMBOLLA` |
| `t_nodi_rete` | `cnd` | `DN_SITO_ORIG,DN_SITO_DEST,DN_TIPO_SITO_ORIG,DN_TIPO_SITO_DEST` |
| `t_ord_forn_righe` | `cnd` | *(da definire)* |
| `buoni_eco` | `stat` | `BUONO_COD` |
| `tipo_attivita` | `stat` | `TIPO_ATTIVITA_COD` |

---

## 8. Configurazione landing zone

### Path base

```
abfss://logistica@<storage_account>.dfs.core.windows.net/landing/
```

### Struttura directory completa

```
landing/
  logistix/
    lgax/                        ← Sito Bologna (principale)
      sto_tes_carichi/YYYY/MM/DD/*.csv
      sto_righe_carico/YYYY/MM/DD/*.csv
      pesate/YYYY/MM/DD/*.csv
      tracciace178/YYYY/MM/DD/*.csv
      dettaglio_carr/YYYY/MM/DD/*.csv
      imbfmovim/YYYY/MM/DD/*.csv
      cartellino/YYYY/MM/DD/*.csv
      carrellisti/YYYY/MM/DD/*.csv
      preparatori/YYYY/MM/DD/*.csv
      ricevitori/YYYY/MM/DD/*.csv
      spedizionieri/YYYY/MM/DD/*.csv
      struttura_mag/YYYY/MM/DD/*.csv
      corsie/YYYY/MM/DD/*.csv
      tabgen/YYYY/MM/DD/*.csv
      aree_merceologiche/YYYY/MM/DD/*.csv
      classe_posto_pallet/YYYY/MM/DD/*.csv
      storico_riepiloghi/YYYY/MM/DD/*.csv   ← SOLO lgax
      testate_bolle/YYYY/MM/DD/*.csv        ← SOLO lgax
      storico_bolle/YYYY/MM/DD/*.csv        ← SOLO lgax
    lgcx/ lcax/ lccx/ lexx/ locx/ lonx/ lscx/ lslx/
      <stesse cartelle di lgax, tranne le tre con SOLO lgax>
  cnd/
    t_stock/YYYY/MM/DD/*.csv
    t_prep_sped/YYYY/MM/DD/*.csv
    t_pdv/YYYY/MM/DD/*.csv
    t_vettori/YYYY/MM/DD/*.csv
    t_trasp_mtv/YYYY/MM/DD/*.csv
    t_nodi_rete/YYYY/MM/DD/*.csv
    t_ord_forn_righe/YYYY/MM/DD/*.csv
  stat/
    buoni_eco/YYYY/MM/DD/*.csv
    tipo_attivita/YYYY/MM/DD/*.csv
```

### Accordo SLA con sistemi sorgente

| Sistema | Orario push completato | Orario avvio Bronze | Finestra tolleranza |
|---|---|---|---|
| Logistix (tutti i siti) | 04:00 | 05:00 | 30 min (alert se landing vuota alle 05:30) |
| CND | 03:30 | 05:00 | 30 min |
| STAT | 03:00 | 05:00 | 30 min |

### Gestione file mancanti

Il notebook Bronze esegue un controllo preventivo `dbutils.fs.ls()` su ogni path.  
Se la cartella è assente o non contiene CSV → il notebook termina con `NO_DATA_IN_LANDING` (non è un errore, ma deve essere loggato e monitorato).  
L'orchestratore (Databricks Workflows) deve distinguere `NO_DATA_IN_LANDING` da errori reali e gestire il retry / alerting separatamente.
