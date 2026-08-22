# Runbook — Re-esecuzione & verifica certifica (F_CARICO + F_PREP_SPED)

**Data:** 2026-07-02
**Scopo:** eseguire nel tuo ambiente (Docker/WSL, Spark) le modifiche di certifica di questa
sessione e verificarle via quadratura vs CDT_DW. Spark **non gira** nell'ambiente Claude → tutti
gli step Spark vanno lanciati qui.

**Convenzioni comandi**
- Runner locale: `py tests/local_bronze/run_notebook.py --notebook <path> --run-date <RUN_DATE>`.
- `<RUN_DATE>`: usa la stessa cadenza con cui rigeneri normalmente (per rigenerare giugno 2026,
  la finestra di certifica è **15–21 giugno 2026**).
- I DROP sono `spark.sql("DROP TABLE IF EXISTS ...")` da eseguire nel tuo Spark (o via spark-sql).
  Nomi tabella nel runner locale = `<catalog>_<schema>.<table>` (es. `silver_dev_logistica_curated.carico`).

> ⚠️ **Perché i DROP**: lo schema/grain di silver_prep e gold è cambiato. `silver_prep_carico`
> riscrive con `overwriteSchema` (si auto-rigenera), ma `gold_*` usano `mergeSchema` (aggiungono
> colonne, **non le rimuovono**) e `silver_prep_prep_sped` usa MERGE (fallisce su schema diverso).
> Droppare garantisce una ricreazione pulita.

---

## STEP 0 — Prerequisito: anagrafica peso/volume articolo

Pubblica `LU_ART_UNITA_LOGISTICA` (765.356 righe già in landing) in `bronze_dev.condiviso`.

```bash
py tests/local_bronze/run_notebook.py \
  --notebook notebooks/gold/condiviso/gold_lu_from_cdtdw.py \
  --run-date 2026-06-17
```
**Verifica:** log `LU_ART_UNITA_LOGISTICA -> ... 765356 righe (CTAS baseline)`.
**Delta futuri (facoltativo):** `py scripts/cdtdw_lookup_extractor/extract_cdtdw_lookups.py --tables LU_ART_UNITA_LOGISTICA --audit-watermark 17832875` → poi ri-esegui STEP 0 (fa MERGE).

---

## STEP 1 — Carichi (grain etichetta + peso/volume ODI)

**1a. Drop tabelle con schema/grain cambiato**
```sql
DROP TABLE IF EXISTS gold_dev_logistica.f_carico;
DROP TABLE IF EXISTS silver_dev_logistica_curated.carico;
```

**1b. Re-run pipeline carichi** (bronze già contiene le colonne imballo raw)
```bash
# Silver clean dettaglio (ora espone la struttura imballo/pallet)
py tests/local_bronze/run_notebook.py --notebook notebooks/silver/carichi/silver_carichi_dettagli.py --run-date <RUN_DATE>
py tests/local_bronze/run_notebook.py --notebook notebooks/silver/carichi/silver_carichi_testate.py  --run-date <RUN_DATE>
py tests/local_bronze/run_notebook.py --notebook notebooks/silver/carichi/silver_pesate.py           --run-date <RUN_DATE>
# Silver PREP (grain ETICHETTA, guidato da pesata)
py tests/local_bronze/run_notebook.py --notebook notebooks/silver/carichi/silver_prep_carico.py       --run-date <RUN_DATE>
# Gold (aggancio dimensioni + PES/VOL da LU_ART_UNITA_LOGISTICA)
py tests/local_bronze/run_notebook.py --notebook notebooks/gold/carichi/gold_f_carico.py              --run-date <RUN_DATE>
```
**Verifiche attese:**
- `silver_prep_carico`: righe ≈ n. etichette (molte più di prima; grain per NUM_ETICH).
- `gold_f_carico`: log orphan-rate; colonne nuove presenti (`NUM_ETICH`, imballo, `CORRIERE_COD`, `PES_CARICO`).
- `PES_CARICO` non più 0 dove l'articolo è in anagrafica (formula `PESO_LORDO×QTA_UF_CARICO`).

**1c. Quadratura F_CARICO**
```bash
py scripts/quadratura/quadratura_fact.py --fact CARICO --da 2026-06-15 --a 2026-06-21 --soglia 5.0
```
**Atteso:** COUNT ora confrontabili (stesso grain etichetta); QTA allineata; verifica il match-rate
di `PES_CARICO` (dipende dalla copertura di `LU_ART_UNITA_LOGISTICA` sulla variante logistica).

---

## STEP 2 — Prep spedizioni (allineamento articolo/grain/pruning)

**2a. Drop tabelle**
```sql
DROP TABLE IF EXISTS gold_dev_logistica.f_prep_sped;
DROP TABLE IF EXISTS silver_dev_logistica_curated.prep_sped;
```

**2b. Re-run pipeline prep_sped** (silver clean/uniche invariati; rigenerare se serve freschezza)
```bash
# (se necessario) silver clean + uniche di bolle/liste già presenti — rigenera solo se il giorno è cambiato
py tests/local_bronze/run_notebook.py --notebook notebooks/silver/prep_spedizioni/silver_prep_prep_sped.py --run-date <RUN_DATE>
py tests/local_bronze/run_notebook.py --notebook notebooks/gold/prep_spedizioni/gold_f_prep_sped.py         --run-date <RUN_DATE>
```
**Verifiche attese:**
- `silver_prep_prep_sped` v4.0: articolo = `ART_RADICE_COD`+`ART_VAR_LOGIS_COD` (no `ART_COD`);
  niente colonne `ORA_*`; grain con `SEQ_PREL_PREP` → righe **più numerose** (le ~30k prima collassate).
- `gold_f_prep_sped`: aggancio `LU_ART_RADICE` (orphan-rate loggato).

**2c. Quadratura F_PREP_SPED**
```bash
py scripts/quadratura/quadratura_fact.py --fact PREP_SPED --da 2026-06-15 --a 2026-06-21 --soglia 5.0
```
**Atteso:** confronto su `(SITO, data bolla)` con COUNT + SUM(`QTA_PREP`,`VAL_PREP_CES`,`VAL_PREP_VEN`).
NB: la data lato CDT_DW è `GIORNO_BOLLA_SPED_ID`, lato Gold `DATA_BOLLA_SPED` (stessa semantica).

---

## STEP 3 — Recupero disco (dopo i re-run pesanti, se serve)

Pattern noto (vhdx cresce da shuffle spill):
1. `docker run --rm --privileged --pid=host alpine nsenter -t 1 -m -- /sbin/fstrim -v /mnt/docker-desktop-disk`
2. stop Docker + `wsl --shutdown`
3. da **PowerShell Admin**: `diskpart /s C:\PROGETTI\LOGISTICO\scripts\compact_vhdx.txt`

---

## Checklist esito

| Step | Fatto | Note |
|---|---|---|
| 0. `gold_lu_from_cdtdw` (765k) | ✓ | LU_ART_UNITA_LOGISTICA in bronze_dev.condiviso |
| 1a. Drop f_carico + logistica_curated.carico | ✓ | anche silver_logistica.carico_dettaglio (schema cambiato) |
| 1b. Re-run silver+gold carichi | ✓ | 59.621 righe grain etichetta; fix alias ORA_CARICO; fix write mode CTAS vs dyn |
| 1c. Quadratura CARICO | ✓ | 103 ODI / 61 Gold; fix tombstone quadratura (OP-CAR-4/A); gap residuo grain pesata → OP-CAR-5 |
| 2a. Drop f_prep_sped + logistica_curated.prep_sped | ✓ | |
| 2b. Re-run silver+gold prep_sped | ✓ | 6.910.236 righe; SEQ_PREL_PREP nel grain, articolo radice+var |
| 2c. Quadratura PREP_SPED | ✓ | 112 ODI / 94 Gold; OP-PSP-1: scartate TIPO_SCAR 09/10 assenti in CDT_DW, coverage aggiuntiva in Gold |
| 3. Recupero disco (se serve) | ☐ | |

## Open point residui (non bloccanti)
- **OP-CAR-1** `VAL_COSTO_CARICO` = NULL (sorgente cndstostock dismessa/2020).
- **OP-CAR-3** `QTA_ORD_FORN` = 0 (distribuzione WL4 con formula legacy degenere, da validare).
- **OP-CAR-4** ⚠️ PARZIALE (2026-07-02): due cause distinte, una risolta e una nuova (→ OP-CAR-5).
  - **Causa A — bug quadratura (RISOLTO)**: `query_gold_kpi` leggeva TUTTI i parquet fisici via
    `rglob`, inclusi i tombstoned dei full_refresh precedenti → Gold gonfiato ~4× (Jun-17 mostrava
    200-300%). Fix in `quadratura_fact.py`: nuovo helper `live_delta_files()` che legge il
    `_delta_log` (add − remove, + checkpoint) e conta solo i file live. Post-fix: nessun valore
    >100%, Gold live = 59.621 righe (era letto come 238.484). **La quadratura è ora affidabile.**
  - **Causa B — grain INNER JOIN pesata (→ OP-CAR-5)**: verificato che il backfill Oracle
    Jun-10…28 NON cambia il match (silver_carichi_dettagli passato da 28k a 309k righe, ma
    `silver_prep_carico` resta a 59.621). Il grain Gold è guidato dalla **pesata** via INNER JOIN
    su 5 chiavi (SITO, CARICO_LOG_NRO, BOLLA_NRO, COMMESSA_NRO, ART_EAN13). Un carico entra in Gold
    solo quando la sua pesata è già arrivata (batch, giorni dopo) e matcha. CDT_DW popola T_CARICO
    dalla catena WL (registrazione carico), indipendente dalla pesata → ha i carichi prima.
    Effetto: 42 "Solo in ODI" concentrati su Jun-15/18/21 (pesata non ancora arrivata/matchata).
    Dove pesata e carico coesistono il match è perfetto (siti 33/57 Jun-17 = 0.0% delta).
- **OP-PSP-1** ✓ CHIUSO (2026-07-02): 399k righe `DATA_BOLLA_SPED=NULL` sono TIPO_SCAR 09/10
  (articoli scartati prima della spedizione). CDT_DW.F_PREP_SPED ha 0 righe con
  `GIORNO_BOLLA_SPED_ID=0` → CDT_DW esclude le scartate a monte. Il nostro Gold le include via
  LEFT join liste↔bolle. Differenza accettabile: **coverage aggiuntiva in Gold** rispetto a CDT_DW,
  non un bug. Il blocco no-bolla aggiunto in `quadratura_fact.py` lo documenta (sempre 0 vs N siti).
  La quadratura standard (solo righe con bolla) rimane comparabile tra i due sistemi.
- **OP-PSP-2** ✓ RISOLTO (2026-07-02): `DATA_PREL_INIZ` ora valorizzata. Fix in `silver_prep_prep_sped`:
  usare `julian_to_date(LSPRL_DATA_PRELIEVO.cast("long")) + LSPRL_ORA_PRELIEVO` invece di
  `LSPRL_DATA_INIZIO_PRELIEVO` (NULL in sorgente). Partizione Gold `DATA_PREL` ora distribuita
  correttamente su date reali (giu-04…giu-26), `__HIVE_DEFAULT_PARTITION__` = 0 righe.
  Nota: ~0.01% righe still null perché 594/6.9M di storico_liste_uniche mancano `LSPRL_DATA_PRELIEVO`
  (file Bronze precedenti alla colonna). Accettabile.
- **OP-CAR-5** 🆕 (2026-07-02): grain `silver_prep_carico` guidato dalla pesata (INNER JOIN). Un
  carico entra in Gold solo se la pesata è già arrivata e matcha sulle 5 chiavi. CDT_DW popola
  T_CARICO dalla catena WL (indipendente dalla pesata) → gap sistematico sui giorni con pesata in
  ritardo. **Decisione di design da prendere**: (a) LEFT JOIN pesata (carico presente anche senza
  pesata, misure pesata a NULL/0), oppure (b) guidare il grain dalla catena WL/dettaglio come CDT_DW
  e agganciare la pesata come attributo opzionale. Opzione (b) è la più fedele all'ODI ma richiede
  rivedere il calcolo di QTA/PES che oggi vengono dalla pesata. Merita sessione dedicata.
- **F_PREP_SPED aggiuntivo**: colonne business CDT_DW (promo, tipo_prep/prel/riep, mappa completa,
  `PES_PREP`, `VAL_INEVASO_PREP_CES`) da valutare dopo chiusura OP-PSP-1/2.
