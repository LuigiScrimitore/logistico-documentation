# Silver — Revision Spec (standard di implementazione)

**Data:** 2026-06-08 · **Autore:** Cloud Data Architect · **Scope:** layer Silver
**Riferimenti:** `Landing & Bronze - Revision Spec.md`, `Lookup Logistico 2.0 - Mappatura LU.xlsx`, `Open Points - Logistico 2.0.md`

## 0. Problema principale da correggere (CRITICO)

Il Silver attuale è stato costruito in larga parte su **colonne inventate**, non presenti nel Bronze reale. Esempi verificati:
- `silver_dim_operatore` usa `CRLLS_COGNOME`, `CRLLS_NOME`, `CRLLS_DATA_ASSUNZIONE`, `CRLLS_COD_CONTRATTO` → **non esistono**. Il Bronze `carrellisti` ha solo: `CRLLS_COD_CARRELLIST`, `CRLLS_DES_CARRELLIST`, `CRLLS_FLAG_CARR_ATT`, `CRLLS_NOME_TERMINALE`, `CRLLS_FLAG_RICOVERO`, `CRLLS_FLAG_PALLINT`, `CRLLS_AZIENDA_PREP_STA`.
- `silver_dim_corriere` usa `VET_RAGIONE_SOC` → reale `VET_DESCRIZIONE`.
- `silver_dim_pdv` usa `PUVDESC` → reale `PUVNOME`.
- `silver_dim_articolo` usa `ARM_DESC_AREA`/`ARM_FLG_ATTIVA` → reali `ARM_DES_AREA_MERCEOLOGICA`/`ARM_TIPO_PREPARAZIONE`.

**Regola assoluta:** ogni notebook Silver deve usare **esclusivamente** colonne presenti nel Bronze corrispondente. Prima di scrivere, l'agente DEVE leggere il/i notebook Bronze sorgente e prendere le colonne reali da `SOURCE_COLS`/`StructType`. **Non inventare attributi** (cognome/nome/contratto/ragione sociale) se non esistono: usare le colonne reali (spesso una `*_DES_*`/descrizione) e lasciare a `null` solo ciò che è genuinamente assente, documentandolo.

## 1. Principi Silver
1. **Cleansing, non modellazione lookup.** Silver = entità di business pulite, tipizzate, deduplicate, rinominate da prefisso Oracle a nome business. I lookup `LU_*` e gli aggregati `A_*` sono artefatti del **Gold** (la rinomina `LU_*`/`A_*` si applica nel pass Gold, non qui).
2. **Allineamento al Bronze reale** (nomi tabella, sistema sorgente, colonne).
3. **Cast espliciti** da StringType ai tipi business; **deduplica** con Window su chiave naturale ordinando per `_bronze_insert_ts DESC`; colonna `_silver_ts = current_timestamp()`.
4. **MERGE INTO** Silver su chiave naturale (CTAS alla prima esecuzione) per le entità incrementali; **overwrite** per le anagrafiche full; **replaceWhere** per gli snapshot (giacenze).
5. **Le trasformazioni rimosse dal Bronze vanno qui** (OP-12 normalizzazione articolo radice/variante; OP-15 unione operatori; OP-17 consolidamento prep_sped).

## 2. Widget standard
```python
dbutils.widgets.dropdown("env", "dev", ["dev","prod"], "Environment")
dbutils.widgets.text("run_date", str(date.today()), "Run Date (YYYY-MM-DD)")
```
Catalcoghi: `get_catalog("bronze", env)` / `get_catalog("silver", env)`. Schema `logistica`. Import `get_logger`; usare `_bronze_insert_ts` (NON `_ingestion_timestamp`).

## 3. Allineamento sorgenti Bronze (post-revisione Bronze)
- Prep-spedizioni: leggere da `bronze.logistica.storico_riepiloghi`, `testate_bolle`, `storico_bolle` (sistema STAT) — OP-16.
- Carrellisti: `dettaglio_carr` e `imbfmovim` sono **due tabelle distinte** (OP-14).
- Giacenze: `bronze.logistica.t_stock` è uno **snapshot** → filtrare `_bronze_load_date = run_date`.
- Timbrature: `bronze.logistica.t_prep_sped` (derivata, OP-17) — il consolidamento prep_sped si ricostruisce qui in Silver dalle sorgenti unitarie.

## 4. Dimensioni master CONDIVISE → DEPRECARE (OP-01/02)

Le dimensioni master sono prodotte dal flusso Retail Master Data e lette in Gold come `LU_*`. **NON** vanno costruite in Silver. Marcare come **DEPRECATI** (header + escludere dai workflow), senza cancellare i file:
- `silver/dimensioni/silver_dim_articolo.py` → master Retail `LU_ART_RADICE` (OP-02)
- `silver/dimensioni/silver_dim_fornitore.py` → master Retail `LU_FORNITORE` (OP-02)
- `silver/dimensioni/silver_dim_pdv.py` → master Retail `LU_PDV` (OP-02). Nota: `bronze.t_pdv` (CND) resta disponibile per eventuali attributi logistici (OP-05).

Header da inserire in cima a questi 3 notebook:
```python
# DEPRECATO (OP-02): dimensione master fornita dal flusso Retail Master Data (LU_*).
# Non eseguire in produzione: il Gold legge la lookup condivisa in sola lettura.
# Mantenuto per tracciabilita'; rimuovere/ridiscutere a valle della conferma Reply.
```

## 5. Dimensioni LOGISTICHE — ricostruire su colonne reali

> Verdetto verificato sulle colonne Bronze reali. Mappare prefisso→business solo su colonne esistenti.

### silver_dim_sito (da `struttura_mag`)
- `SITO_COD` = distinct `MAG_SITO_COD`. `SITO_DESC`: non esiste un nome sito nel sorgente → lasciare `null` (placeholder) o, se utile, derivare da `tabgen` (TGEN_NRO_TAB=7) in un secondo momento. `FLG_ATTIVO`: non disponibile → null. Tenere minimale: SITO_COD + (eventuale descr null) + _silver_ts.

### silver_dim_operatore (UNION 4 anagrafiche — OP-15)
Colonne reali per sistema:
- carrellisti: `CRLLS_COD_CARRELLIST`→OPERATORE_COD, `CRLLS_DES_CARRELLIST`→DESCRIZIONE, `CRLLS_FLAG_CARR_ATT`→FLG_ATTIVO, TIPO='CARRELLISTA'
- preparatori: `PREP_COD_PREPARATOR`→OPERATORE_COD, `PREP_DES_PREPARATOR`→DESCRIZIONE, `PREP_FLAG_PREP_ATT`→FLG_ATTIVO, TIPO='PREPARATORE'
- ricevitori: `RICV_COD_RICEVITOR`→OPERATORE_COD, `RICV_COGNOME`+`RICV_NOME`→DESCRIZIONE (concat), `RICV_FLAG_RICV_ATT`→FLG_ATTIVO, TIPO='RICEVITORE'
- spedizionieri: `SPE_CODICE`→OPERATORE_COD, `SPE_COGNOME`+`SPE_NOME`→DESCRIZIONE (concat), FLG_ATTIVO=null (assente), TIPO='SPEDIZIONIERE'
- `MAG_SITO_COD`→SITO_COD per tutti. **NON** usare cognome/nome/data_assunzione/contratto per carrellisti/preparatori (non esistono). Schema target unico: OPERATORE_COD, SITO_COD, TIPO_OPERATORE, DESCRIZIONE, FLG_ATTIVO, _silver_ts. Dedup su (OPERATORE_COD, SITO_COD, TIPO_OPERATORE).

### silver_dim_corriere (da `vettori`)
- `VET_CODICE`→CORRIERE_COD, `VET_DESCRIZIONE`→RAGIONE_SOCIALE, `VET_INDIRIZZO`→INDIRIZZO, `VET_CITTA`→CITTA, `VET_PROVINCIA`→PROVINCIA, `VET_CAP`→CAP, `VET_STATO`→FLG_ATTIVO. (NON `VET_RAGIONE_SOC`/`VET_FLG_ATTIVO`: inesistenti.)

### silver_dim_topografia (da `struttura_mag`)
- `CELLA_COD` = concat_ws('_', MAG_SITO_COD, STRM_COD_MAGAZZINO, STRM_CORSIA, STRM_COLONNA, STRM_PIANO).
- `SITO_COD`=MAG_SITO_COD, `MAG_COD`=STRM_COD_MAGAZZINO, `CORSIA`=STRM_CORSIA, `COLONNA`=STRM_COLONNA, `PIANO`=STRM_PIANO, `COD_CLAS_POSPA`=STRM_COD_CLAS_POSPA, `COD_ZONA_MAG`=STRM_COD_ZONA_MAG, `COD_SETTOR_MAG`=STRM_COD_SETTOR_MAG, `STATO_POSPA`=STRM_STATO_POSPA. Usare solo colonne STRM_ realmente presenti (verificare nel Bronze).

## 6. Aree merceologiche (da `aree_merceologiche`)
- `COD_AREA_MERC`=ARM_COD_AREA_MERCEOLOGICA, `DES_AREA_MERC`=ARM_DES_AREA_MERCEOLOGICA, `TIPO_PREPARAZIONE`=ARM_TIPO_PREPARAZIONE. (NON `ARM_DESC_AREA`/`ARM_FLG_ATTIVA`.) Questa alimenta la merceologica logistica (LU_AREA_MERCL_LOGIS in Gold).

## 7. Transazionali e altre Silver
Per carichi, pesate, traccia_ce178, giacenze, prep, trasporti, tracciabilità, carrellisti(missione/sessione): **verificare ogni colonna** contro il Bronze reale (prefissi STCAR_, SRCAR_, PSP_, CE178_, STK*, RPLPR_, TEBO_, BOL_, DTCRL_, CARTE_, IMF*, SP_). Correggere i nomi che non esistono. Mantenere cast/dedup/calcoli business (es. SCARTO_QTA, ORE_PRODUTTIVE, regola attrezzaggio resta in Gold). Le normalizzazioni articolo (radice/variante, OP-12) vanno applicate qui dove servono (es. da SRCAR_COD_MSI), come funzioni Spark/lookup, non in Bronze.

## 8. Pattern di scrittura Silver
- Incrementali (transazionali): MERGE su chiave naturale (CTAS prima volta). Filtrare il Bronze per `_bronze_load_date = run_date` se il Bronze è delta giornaliero.
- Anagrafiche/dimensioni logistiche: overwrite completo (riflettono lo stato corrente del Bronze full).
- Giacenze daily: `replaceWhere` su DATA_FOTO/_bronze_load_date.

## 9. Note finali
- NON introdurre JOIN verso sorgenti esterne non necessari; le dimensioni master non si costruiscono (OP-02).
- Header uniforme: Area / Layer Silver / Versione 3.0.0 / Data 2026-06-08 / Descrizione con sorgenti reali.
- Output naming Silver invariato (la rinomina `LU_*` avviene in Gold).
