# Open Points — Logistico 2.0

**Ultimo aggiornamento:** 2026-06-10 (post primo run completo su dati reali + ridisegno scelta B / standard 2-notebook)
**Owner documento:** Cloud Data Architect — Team Logistico 2.0
**Scopo:** registro dei punti **ancora aperti** che richiedono conferme esterne (Reply o sistemi sorgente) o che sono stati messi in stand-by per fase successiva.

## Legenda stato

| Stato | Significato |
|-------|-------------|
| 🔴 Aperto | Da risolvere prima/insieme alla revisione del codice |
| 🟡 Da confermare (Reply) | In attesa di conferma dal team Reply / Data Platform |
| 🟠 Da confermare (Sorgente) | In attesa di conferma dai sistemi sorgente (Logistix / CND / STAT) |
| 🔵 In stand-by | Rimandato a fase successiva, non bloccante per l'attuale scope |

> Gli OP risolti dalla revisione end-to-end (OP-06 naming `LU_*`/`A_*`, OP-12/13/15 trasformazioni in Silver, OP-14/16 verificati e applicati, OP-27 Gold ricostruito) sono stati rimossi da questo registro e sono tracciati nei documenti di spec dei rispettivi layer.

---

## A. Anagrafiche, Lookup e Schemi condivisi

### OP-01 — Schema `condiviso` non previsto da Reply 🟡
**Descrizione:** Reply non prevede uno schema `gold_prod.condiviso`. Le dimensioni master sono prodotte dal flusso **Master Data Master** con naming `LU_*`.
**Stato implementativo:** rimosso dai notebook attivi; le 4 dim master sono deprecate (exit `DEPRECATED_OP02`). Le fact Gold portano le chiavi naturali; la join master è opzionale (commentata) tramite il parametro `retail_master_schema` (default placeholder `gold_prod.condiviso`).
**Azione:** ottenere da Reply lo schema definitivo (vedi OP-02) e aggiornare il parametro/valore nei workflow.

### OP-02 — Nomi/percorsi esatti delle lookup condivise (Retail Master Data) 🟡
**Descrizione:** servono i nomi esatti delle lookup master Retail da leggere in sola lettura:
- `LU_ART_RADICE` (articolo, ex `L_ART`)
- `LU_FORNITORE` (fornitore, ex `L_FORN`)
- `LU_PDV` (punto vendita)
- `LU_GIORNO`, `LU_MESE` (calendario)
**Azione:** ricevere da Reply schema e nomi esatti (es. `gold_prod.<schema_master>.LU_ART_RADICE`) e permessi di lettura; abilitare le join master attualmente commentate nei notebook Gold.

### OP-03 — Lookup derivate `NCD_*` (categoria merceologica) 🔵 IN STAND-BY
**Descrizione:** `NCD_L_CAT_MERCL`, `NCD_L_CATEG_MERCEOLOGICA`, `NCD_L_CATEGORIA_MERCEOLOGICA`, `NCD_L_MAG_SITO_CAT_MERCL` sono lookup **derivate dal logistico**, oggi non sostituibili né ricostruibili.
**Decisione provvisoria:** mantenere il riferimento alle tabelle `NCD_*` esistenti. Da **ridiscutere in fase successiva**.

### OP-04 — Confine merceologica logistica vs Retail 🟡
**Descrizione:** coesistono lookup merceologiche logistiche `LU_AREA_MERCL_LOGIS` / `LU_MACRO_AGG_MERCL` (da creare in gold logistico) e le `NCD_*` Retail (OP-03). Va definito il confine tra gerarchia master Retail e attributi merceologici logistici.
**Azione:** allineamento con Reply (collegato a OP-03).

### OP-05 — Arricchimenti logistici su anagrafiche master 🟡
**Descrizione:** se servono attributi logistici aggiuntivi su entità master (es. info logistiche di un articolo), come gestirli senza duplicare il master.
**Proposta:** dimensione di dominio logistico separata (es. `gold_prod.logistica.LU_ARTICOLO_LOGISTICA`, chiave `ART_RADICE`) in JOIN con `LU_ART_RADICE`.
**Azione:** confermare con Reply (call già offerta).

---

## B. Landing Zone e modalità di ingestion

### OP-07 — Struttura path landing zone 🟡
**Descrizione:** Reply usa il pattern `<nome_sorgente>-landing` con la struttura concordata con **F. Foconi** per i flussi ODI.
**Stato implementativo:** convenzione `<source>-landing/{tabella}/YYYY/MM/DD/` applicata in tutti i 26 Bronze + Terraform (3 external location con `for_each`).
**Azione:** ricevere la specifica esatta del path (struttura Foconi) e aggiustare se necessario; chiarire lo scope di `landing/logistix/*` e `landing/stat/*` con Reply.

### OP-08 — FULL vs DELTA e naming file 🟠 (regime architetturale risolto, dettagli sorgente da confermare)
**Stato implementativo:** modalità Bronze definite per ciascuna tabella secondo l'analisi AS-IS verificata (DELTA_MERGE/FULL_OVERWRITE/SNAPSHOT). Il separatore CSV è hardcoded `;` (template).
**Da confermare con i sistemi sorgente:**
- file giornaliero = delta (record nuovi+modificati) per le transazionali? full per anagrafiche/giacenze?
- naming/partizionamento: un file/giorno (YYYY/MM/DD) o più file intra-day con timestamp? In tal caso Bronze deve leggere tutti i file del giorno in ordine.
- separatore CSV per sorgente (Logistix/CND/STAT): l'AS-IS CND usava `,`, oggi i Bronze usano `;`. Valutare di rendere il separatore un widget.

### OP-09 — SLA di completamento push e ri-schedulazione workflow 🟠
**Descrizione:** Reply allinea le ingestion ai nostri orari ma servono gli SLA reali per sorgente. Niente deve partire prima delle 02:00–03:00.
**Stato implementativo:** schedule attuale: landing 00:30, dim_refresh 01:00, carichi 02:00, giacenze 03:30, prep_sped 04:30, trasporti 05:00, datamart 06:00.
**Azione:** ricevere gli SLA definitivi per sorgente e ri-fasare lo scheduling (eventuale shift landing → 02:30 e cascata a seguire).

### OP-10 — Filtro statico AREE_MERCEOLOGICHE 🟠
**Descrizione:** l'AS-IS estrae `AREE_MERCEOLOGICHE` con filtro `WHERE ARM_TIPO_AREA = 1`.
**Azione:** concordare con la sorgente se il filtro è applicato a monte o se Bronze deve mantenerlo (oggi Bronze legge tutto).

### OP-11 — Carichi trasferiti via SWAP 🟠
**Descrizione:** alcune query AS-IS considerano `STCAR_TRASFERITO_SWAP` (carichi trasferiti tra siti).
**Azione:** definire con la sorgente come questi record vengono marcati nel delta (rischio doppio conteggio / mancata cattura).

---

## C. Unity Catalog, Infrastruttura, CI/CD

### OP-18 — Granularità Service Principal 🟡
**Descrizione:** Reply indica "un SP per **ciascun job**".
**Azione:** confermare la granularità attesa e recepirla nel provisioning Terraform SP e nei secrets CI/CD.

### OP-19 — Cluster: DBR/VM e shared vs job cluster 🟡 (allineato in YAML, da confermare)
**Stato implementativo:** allineato a DBR `15.4.x-scala2.12` e `Standard_D4s_v3` in tutti i workflow.
**Azione:** confermare con Reply (uso dello shared cluster esistente vs job cluster dedicati).

---

## D. Monitoring, Data Quality, Go-live

### OP-20 — Sistema di alerting Databricks 🟡
**Descrizione:** Reply sta sviluppando un sistema di alerting su Databricks (non ancora disponibile).
**Stato implementativo:** notifiche email su failure come ponte.
**Azione:** integrare quando rilasciato. Richiedere timeline/documentazione.

### OP-21 — Framework Data Quality condiviso 🔴 SENZA RISPOSTA
**Descrizione:** non chiarito se esista un framework DQ standard di piattaforma.
**Stato implementativo:** `dq_helper.py` custom in `logistica_utils`.
**Azione:** **ri-sottoporre a Reply**. Allinearsi se adotta uno standard (Great Expectations, Lakehouse Monitoring, Soda).

### OP-22 — SLA di risposta ai failure 🟡
**Descrizione:** SLA di risposta ai failure operativi da definire.
**Azione:** formalizzare nel `runbook.md` (es. failure Bronze critico → ripristino entro X ore) e i profili abilitati al riavvio job in prod.

### OP-23 — Dati sintetici per test E2E 🟡
**Descrizione:** servono dati sintetici rappresentativi per i test end-to-end. **Ambienti riconosciuti: solo `dev` e `prod`** (separati e speculari); un eventuale terzo ambiente (es. stage/pre-prod) **non è adottato** e sarà deciso in seguito se necessario.
**Azione:** definire con Reply un dataset di test rappresentativo per sorgente (Logistix multi-sito, CND, STAT), utilizzabile in `dev`.

### OP-24 — Criteri di accettazione parallel run 🟡
**Descrizione:** parallel run ODI vs Databricks previsto a piano; restano da definire durata, tolleranza numerica, responsabile validazione.
**Azione:** formalizzare nel `cutover_plan.md` per ciascuna wave.

### OP-25 — Processo formale di go-live 🟡
**Descrizione:** processo di rilascio (approvazione, documenti, evidenze test, checklist, promozione dev→prod) da definire.
**Azione:** produrre una proposta di processo e condividerla con Reply.

---

## E. Emersi dal primo run su dati reali (2026-06-10)

### OP-28 — Allineamento dimensioni: orphan-rate ricorrenti 🟠 (PRIORITÀ 1)
**Descrizione:** sui fact reali gli agganci dimensionali vanno in orphan elevato in modo sistematico, perché i domini-codice delle sorgenti reali non coincidono con le `LU_*`:
- `MAG_SITO_COD` → ~85-86% (F_TRASPORTO da SP_MAGAZZINO@TRACK; F_PREP_SPED da LSPRL_SITO@STAT) vs `LU_SITO`
- `CORRIERE_COD` → 100% su F_ORDINI (STCAR_COD_CORRIERE) vs `LU_CORRIERE`
- `PREPARATORE/OPERATORE_COD` → 10-36% (F_CARICO 13%, F_PREP_SPED 10%, F_TURNO 36%)
- `AREA_MERCEOLOGICA_COD` → 51% su F_TURNO
**Note:** non è un bug di pipeline (i fact scrivono con fallback −1); è disallineamento di **codifica** tra sorgenti (STAT/TRACK/Logistix) e lookup. PDV e VETTORE_PRESU sono invece a 0%.
**Azione:** attività unica di allineamento — ricostruire/mappare le `LU_*` dai domini reali (in particolare la mappa sito multi-sistema, e l'anagrafica corriere/operatore/area). **Prossima attività in corso.**

### OP-29 — Stock: F_GIACENZE_DAILY vuoto (join catena↔struttura_mag) 🔴 (PRIORITÀ 2)
**Descrizione:** `silver_t_stock` produce 0 righe pur con `catena_unificata` a 23.506 righe: il join **INNER** `catena ↔ struttura_mag` su (CORSIA, COLONNA, PIANO, LIVELLO, MAG_SITO_COD) non trova match sui dati reali.
**Note:** essendo INNER (non LEFT lookup), azzera il fatto → unico fact non popolato nel primo run.
**Azione:** investigare formati topografia (corsia/colonna/piano/livello) e sito tra `catena` e `struttura_mag`; valutare LEFT join + fallback o normalizzazione chiavi topografiche.

### OP-30 — Incrementalità Bronze→Silver-clean e clean→prep 🟢 (LARGAMENTE IMPLEMENTATO, 2026-06-11)
**Descrizione:** diversi cleansing/prep ricalcolavano FULL (es. uniche spedizioni su 2M+ righe), insostenibile a regime delta giornaliero. Risolto sul test del nuovo giorno (06-10→06-11) con **tre pilastri**, tutti validati su dati reali:

1. **Bronze pruning (`_row_hash`)** — rollout su **tutti i 14 bronze MERGE** (+ storico_liste). Helper `add_row_hash`/`bronze_merge_upsert` in `logistica_utils/utils.py`. `whenMatchedUpdate(condition="tgt._row_hash <> src._row_hash")`: le righe **identiche** non vengono ri-datate → `_bronze_load_date` = "ultima modifica" → a valle si propaga **solo il delta reale**. Misurato: batch 1.86M → **417k (~22%)** propagate. Chiavi MERGE **null-safe (`<=>`)**.
2. **Clean incrementale** — `silver_storico_liste/bolle_clean` (widget `full_refresh`; incrementale = filtro `_bronze_load_date == run_date` + MERGE upsert null-safe + `dropDuplicates(MERGE_KEYS)`). Carichi/spedizioni/ordini erano già MERGE. No-dup, idempotente (cross-giorno=0).
3. **Pattern #2 prep (chiavi-impattate)** — `storico_liste_uniche`, `storico_bolle_uniche` (GROUP BY) e `prep_sped` (join): ricalcolano solo i gruppi/chiavi toccati dal batch (join null-safe) + MERGE. Validato **incrementale == full**. Dedup `prep_sped` reso deterministico (tiebreaker).

**Causa-radice risolta in corsa:** schema CSV **posizionale** disallineato (87 col vs 146 reali) azzerava `BOL_NRO_RIGA` → chiave nulla → MERGE non-match → duplicazione (8.4M). Fix: lettura **per header**. Vedi memoria `bronze-csv-schema-by-name`.

**Pre-condizione operativa:** attivare il pruning richiede un **rebuild una-tantum** (drop→CTAS) delle bronze esistenti (per creare `_row_hash`).
**Residui:** prep piccoli in full (OP-34); grana prep_sped/seq_prel (OP-33). **Azione finale:** ridurre il lookback giornaliero a 1-2 gg nel run di routine.

### OP-31 — Validazioni delta sorgente da confermare sui dati reali 🟠
**Descrizione:** punti "DA VALIDARE" ora verificabili con dati reali:
- `ESTRAI_SPEDIZIONI` (coda CDC) come **semi-join** filtro sulle spedizioni: oggi leggiamo `spedizioni` a finestra piena su `SP_DATABOLLA` (estrai_spedizioni risultava vuota).
- `merge_keys`/`date_column` di `spedizioni` (SP_ID / SP_DATABOLLA) e `storico_liste` (8 chiavi) confermati sul primo run; restano da validare su più giorni.
**Azione:** decidere se replicare il semi-join ESTRAI_SPEDIZIONI; monitorare i merge_keys su delta multipli.

### OP-32 — Late-arriving dimensions: ri-risoluzione automatica degli orphan 🔴 (PRIORITÀ 2)
**Descrizione:** quando un'anagrafica arriva **dopo** il fatto che la referenzia, la riga di fatto resta agganciata al sentinel **−1** ("SCONOSCIUTO") e **non si auto-corregge** quando la dimensione si completa. Oggi NON esiste un meccanismo LAD: l'unico handler presente (`gold_late_arriving_handler`, solo Carichi) gestisce il late-arriving del *fatto*, non della *dimensione*, e non esegue nemmeno i lookup.

**Due regimi diversi (importante):**
- **Dimensioni lente / strutturali** (sito, magazzino): cambiano di rado; la nascita di un sito è un **evento critico e gestito** (richiede nuova connessione/db-link sul landing). Frequenza bassa → tollerabile anche un reprocess occasionale di partizioni.
- **Dimensioni di dettaglio ad alta frequenza** (ARTICOLI, FORNITORI): **nascono ogni giorno**, spesso **in concomitanza con eventi di supply chain** (es. nuovo ordine a fornitore → l'articolo compare nel fatto carichi/prelievi PRIMA che l'anagrafica master sia propagata). Qui l'orphan è un **fenomeno giornaliero ricorrente e massivo**, non un'eccezione. È questo il caso che impone un meccanismo automatico e schedulato.

**Ostacolo tecnico:** `surrogate_key_fallback` **sovrascrive** la colonna FK con il valore risolto *oppure* −1 → per le righe orphan si **perde il codice naturale originale**, rendendo impossibile la ri-risoluzione chirurgica.

**Meccanismo proposto:**
1. **Preservare il codice naturale** nel fact in colonna dedicata (es. `<dim>_COD_NAT`) accanto alla FK risolta (modifica a `surrogate_key_fallback` + gold).
2. **Job LAD generico, schedulato GIORNALMENTE** dopo il refresh delle dimensioni, parametrico su (fact, fk, dim, nat_key):
   `MERGE INTO fact USING dim ON fact.<nat> = dim.<nat> WHEN MATCHED AND fact.<fk> = '-1' THEN UPDATE SET <fk> = dim.<nat>` — tocca **solo** le righe orphan che ora risolvono (economico, adatto al ritmo giornaliero degli articoli).
3. **Fallback reprocess-partizioni** (pattern `replaceWhere` da `prep`) per backfill massivi o dimensioni lente.
4. **Finestra di retention orphan**: definire per quanti giorni si tenta la ri-risoluzione (oltre, l'orphan diventa permanente / quarantena DQ).

**Dipendenze:** articolo/fornitore arrivano dal **Retail Master** (OP-02): la cadenza di refresh di quelle LU vs l'arrivo dei fatti determina il volume di orphan giornaliero → da coordinare con Reply.
**Azione:** progettare e implementare il job LAD generico + preservazione codice naturale; generalizzare a tutti i fatti; ripuntare/riusare l'handler Carichi.

---

### OP-33 — Grana di `prep_sped`: `SEQ_PREL_PREP` nei MERGE_KEYS? 🔵 DA CHIARIRE
**Descrizione:** i `MERGE_KEYS` di `silver_prep_prep_sped` (7 chiavi: MAG_SITO_COD, GIORNO_ORD_ID, SOCIO_COD, NUM_RIEP, NUM_GABBIA, NUM_ORD, ART_COD) **omettono `SEQ_PREL_PREP`**, mentre il commento di testata dichiara la grana-prelievo come comprensiva di `seq_prel`. Conseguenza misurata (06-11): ~30k righe che differiscono solo per `SEQUE_PRELIEVO`/`FLAG_SCARTATO` **collassano** (2.471.418 → 2.441.456), con scelta del rappresentante prima non deterministica.
**Stato attuale:** scelta **opzione B** (grana a 7 chiavi mantenuta) + fix dedup **deterministico** (tiebreaker `SEQ_PREL_PREP`,`TIPO_SCAR_PREP_COD`,`NUM_BOLLA_SPED` nel `Window.orderBy`) → risultato ora riproducibile. Decisione presa "momentaneamente": l'utente ritiene `SEQ_PREL_PREP` probabilmente **non significativo per il reporting finale**.
**Azione (futura):** confermare col legacy `CDT_DW.INS_NEW_PREP_SPED` se la grana del fact deve includere `seq_prel`. Se sì → aggiungere `SEQ_PREL_PREP` ai MERGE_KEYS (niente collasso; impatta anche il gold F_PREP_SPED). Se no → chiudere confermando i 7 keys.

---

### OP-34 — Pattern #2 sui prep "piccoli" (turno/ordini/trasporto) 🔵 BASSA PRIORITÀ
**Descrizione:** il pattern #2 (incrementale per chiavi-impattate) è stato applicato ai prep **pesanti** dove il guadagno è reale: `storico_liste_uniche`, `storico_bolle_uniche`, `prep_sped`. I prep **piccoli** restano in **FULL recompute**: `prep_turno_prep_sito` (~52k, ~7s), `prep_ordini` (~1k), `prep_trasporto` (~23k, già MERGE). `prep_giacenze`/`prep_carico` sono già incrementali (dynamic partition overwrite per giorno).
**Motivazione (decisione 2026-06-11):** su queste tabelle il full-recompute gira in pochi secondi; il costo/rischio di conversione supera il beneficio. Inoltre `prep_turno` richiederebbe di definire una merge-key/grana di output oggi non esplicita.
**Azione (futura):** rivalutare quando i volumi crescono (storico pluriennale) o se la profondità di ingestion aumenta — allora anche questi prep potrebbero giovarsi del pattern #2. Per `prep_turno` formalizzare prima la grana (SITO, DATA_PREPARAZ, PREPARATORE, NRO_RIEPILOGO).

---

### OP-35 — Strategia watermark / controllo incrementale (granularità per sorgente) 🔵 DA PROGETTARE
**Contesto:** la catena incrementale (clean filtra `_bronze_load_date == run_date`; prep pattern #2 su `_silver_load_date == run_date`) oggi è guidata **dall'esterno** dal `run_date` (widget/job param): **nessuna memoria persistente** dell'ultima data processata. I flag legacy `*_DATA_ESTRAZIONE_DWH` NON sono usabili (READ-ONLY sul sorgente). Serve un meccanismo per il **catch-up** quando si accumulano più giornate di solo-landing.

**Decisione di granularità (2026-06-12):** il watermark va tenuto **a livello di (sistema/sorgente, tabella, sito) — NON globale**. Motivazioni:
- **isolamento fallimenti**: se un singolo caricamento va in errore (es. `spedizioni@TRACK` ORA-01555), si recupera solo quello, non l'intera giornata;
- **upload selettivo**: processare a bronze solo le tabelle/siti pronti, in modo indipendente;
- **coerenza**: 1 bronze notebook = 1 tabella; logistix è multi-sito → grana naturale `(sistema, tabella, sito, data_landing)`.

**Opzioni di store** (da decidere a regime, vedi anche orchestrazione Databricks):
- **A) auto-derivato dal dato** (portare `_bronze_load_date` nel clean → `process_from = MAX(...) + 1` per chiave): zero infra, ma watermark globale-per-tabella (non per sito senza colonna sito nel target STAT).
- **B) tabella di controllo** `*.control.etl_watermark (sistema, tabella, sito, last_landing_date, last_run_ts, righe, esito)`: esplicita, auditabile, granulare, gestisce retry selettivi. **Pattern target consigliato.** Da curare: transazionalità dell'update (update watermark solo se il caricamento ha avuto successo), recovery dai fallimenti parziali.
- **C) stato nell'orchestratore** (task discovery che elenca le partizioni landing non ancora processate per (sorgente,tabella,sito)).

**Stato attuale (interim):** per il recupero manuale dei backlog si usa un **parametro esplicito `process_from`** sul clean (default = `run_date` per il daily). Implementato in OP-30. La scelta A/B/C a regime resta da prendere con il design dell'orchestrazione.

**Decisione (2026-06-14):** scelta **opzione B** (tabella di controllo) su **catalog dedicato `control_<env>`**, schema `etl`, tabella `watermark`, chiave `(stage, sistema, tabella, sito)`. Design dettagliato in **`DOCS/Design - Watermark ETL (OP-35).md`**.

**Stato implementativo (2026-06-14): FONDAMENTA + PILOTA FATTI.**
- Helper in `utils.py`: `get_control_table`, `ensure_watermark_table`, `read_watermark`, `update_watermark` (transazionale: su FAIL non avanza), `pending_landing_dates`. Layer `control` in `get_catalog`.
- Test `tests/local_bronze/test_watermark.py` (ALL_OK): ensure/read/update OK-avanza/FAIL-non-avanza/upsert-idempotente/catch-up/isolamento-sito.
- **Pilota** `silver_storico_liste_clean` (stage `bronze_to_clean`): filtro range `_bronze_load_date > process_from` (watermark o override widget `process_from`), update watermark a fine run. Test `test_watermark_pilot.py` (ALL_OK): da wm 06-11 un solo run fa catch-up 06-12+06-13 e avanza a 06-13; 2° run NO_DATA idempotente.
- Terraform: cataloghi `control_dev`/`control_prod` + schemi `etl`/`parametri` + grants.

**Azione (rollout, da fare):** estendere lo stesso pattern agli altri clean (`storico_bolle_clean`, carichi/spedizioni/ordini), poi stage `landing_to_bronze` nell'orchestratore (uso di `pending_landing_dates`) e — opz. fase 2 — `clean_to_prep`. Deploy Terraform dei control catalog a regime.

### OP-36 — Runner di test locale a sessione Spark singola → SIGKILL per accumulo memoria 🔵 SOLO-LOCALE (non bloccante a regime)
**Descrizione:** `tests/local_bronze/run_big_rerun.py` esegue **tutti i ~95 notebook in UNA sola sessione Spark** (`build_spark` una volta, poi `exec` in sequenza). In un run completo la memoria del driver **si accumula** (cache pattern #2 mai `unpersist`, broadcast, metadati di centinaia di MERGE) e su VM WSL2 da ~19.5 GB la JVM viene **SIGKILL-ata dall'host** senza traceback — osservato 2 volte il 2026-06-13 (a `bolle_uniche` e a fine `SILVER_PREP`).
**Workaround usato (2026-06-13):** spezzare il run in fasi con `--only SILVER_PREP,GOLD_FACT,GOLD_AGG` ecc., così ogni invocazione parte con sessione/memoria fresca. Idempotente (MERGE upsert), quindi sicuro riprendere dal punto morto.
**Perché non bloccante a regime:** su Databricks ogni notebook gira come **task isolato** (sessione/cluster dedicato per step), quindi l'accumulo non si presenta. È un limite **specifico del runner locale di test**.
**Azione (opzionale, qualità del tooling locale):** o (a) `unpersist()` esplicito delle cache pattern #2 a fine notebook, o (b) far girare ogni notebook in un sotto-processo separato (sessione per-notebook), o (c) bumpare driver memory + WSL2 `.wslconfig`. Bassa priorità: il workaround `--only` basta.

---

## Riepilogo per stato

| Stato | Open points |
|-------|-------------|
| 🔴 Aperto | OP-21, **OP-29** (stock vuoto), **OP-32** (LAD ri-risoluzione orphan) |
| 🟠 Da risolvere (run reale) | **OP-28** (dimensioni/orphan — *in corso*), **OP-31** (validazioni delta) |
| 🟢 Implementato (validato 06-11) | **OP-30** (incrementalità: bronze pruning + clean MERGE + pattern #2 prep) |
| 🔵 Da chiarire (basso impatto) | **OP-33** (grana prep_sped / seq_prel), **OP-34** (pattern #2 prep piccoli) |
| 🔵 Da progettare (orchestrazione) | **OP-35** (watermark per-sorgente: auto-derivato vs tabella controllo vs orchestratore) |
| 🔵 Solo-locale (tooling) | **OP-36** (runner test sessione singola → SIGKILL memoria; workaround `--only` per fasi) |
| 🟡 Da confermare (Reply) | OP-01, OP-02, OP-04, OP-05, OP-07, OP-18, OP-19, OP-20, OP-22, OP-23, OP-24, OP-25 |
| 🟠 Da confermare (Sorgente) | OP-08, OP-09, OP-10, OP-11 |
| 🔵 In stand-by | OP-03 |

## OP risolti dalla revisione end-to-end (rimossi dal registro)
- **OP-06** — Naming `dim_*`→`LU_*`, `dm_*`→`A_*` applicato a tutti i notebook Gold, KPI, optimize, workflow.
- **OP-12** — Normalizzazione articolo radice/variante spostata in Silver (`silver_carichi_dettagli`).
- **OP-13** — Driver `WL2_CATENA` rimossa dal Bronze (dato grezzo unitario); il delta arriva via file landing.
- **OP-14** — `DETTAGLIO_CARR` e `IMBFMOVIM` gestite come tabelle distinte (verificato).
- **OP-15** — Unione carrellisti+preparatori avviene in `silver_dim_operatore` (Silver), non in Bronze.
- **OP-16** — Prep-spedizioni da STAT: sorgente corretta nei Bronze + workflow `logistica_landing_ingestion`.
- **OP-27** — Gold ricostruito su colonne reali del Silver corretto (fact, lookup, KPI, optimize).
- **OP-17** — *Superato dal ridisegno scelta B / standard 2-notebook (2026-06-10):* `T_PREP_SPED` non è più letta come tabella sorgente derivata; il consolidamento è ricostruito dalle sorgenti raw nello strato `silver.prep_logistica` (`silver_prep_prep_sped`). La vecchia `silver_prep_sped_integrata` non è più il percorso del fact.
- **OP-26** — *Superato dal ridisegno scelta B (2026-06-10):* i trasporti non leggono più via JDBC. F_TRASPORTO è ricostruito a grana-bolla da `SPEDIZIONI@TRACK` via landing (`bronze_spedizioni` → `silver_prep_trasporto`); `silver_trasp_mtv_build`/`silver_t_trasp_mtv` deprecati; ordini da `sto_tes_carichi` (landing).

## Riferimenti
- `DOCS/Lookup Logistico 2.0 - Mappatura LU.xlsx` — mappatura lookup `LU_*` e owner
- `DOCS/Analisi AS-IS Estrazione - CDT_ESTR.md` — verifica FULL/DELTA
- `DOCS/Tabelle Sorgenti - Logistico 2.0.xlsx` — tipo caricamento verificato
- `DOCS/Tabelle Target CDT_DW - Logistico 2.0.xlsx` — modello Gold v3 (LU_/F_/A_)
- `DOCS/Landing & Bronze - Revision Spec.md` — spec layer Bronze
- `DOCS/Silver - Revision Spec.md` — spec layer Silver
- `DOCS/Gold - Revision Spec.md` — spec layer Gold/DataMart
- `DOCS/Workflow - Revision Spec.md` — spec workflow YAML
- `DOCS/Linee Guida - Punti di approfondimento v2.3.docx` — Q&A aggiornata per Reply
