# Cut-Over Plan — Migrazione Oracle → Databricks

**Progetto:** Logistico 2.0  
**Autore:** Cloud Solution Architect  
**Data:** 2026-05-29  
**Versione:** 1.0  
**Classificazione:** OPERATIVO — distribuire al team 7 giorni prima del go-live

---

## Indice

1. [Pre-requisiti di ingresso al cutover](#1-pre-requisiti-di-ingresso-al-cutover)
2. [Finestra di cutover e team di presidio](#2-finestra-di-cutover-e-team-di-presidio)
3. [Sequenza step-by-step con orari](#3-sequenza-step-by-step-con-orari)
4. [Smoke test checklist: 15 check funzionali](#4-smoke-test-checklist-15-check-funzionali)
5. [Criteri go/no-go per ogni fase](#5-criteri-gono-go-per-ogni-fase)
6. [Escalation: chi chiamare se un passo fallisce](#6-escalation-chi-chiamare-se-un-passo-fallisce)
7. [Appendice: contatti e accessi](#7-appendice-contatti-e-accessi)

---

## 1. Pre-requisiti di ingresso al cutover

Tutti i seguenti pre-requisiti devono essere soddisfatti e firmati dal PM **almeno 48 ore prima** dell'inizio della finestra di cutover. Se anche uno solo non è soddisfatto, il cutover viene posticipato.

| # | Pre-requisito | Responsabile verifica | Criteri di accettazione |
|---|---|---|---|
| 1 | Shadow mode completato con successo per almeno 10 giorni lavorativi consecutivi | Cloud Architect + BA | Report shadow mode: delta < 0.5% su tutti i KPI principali per 10 gg |
| 2 | Data Quality score > 95% su tutte le gold tables principali | Cloud Architect | Dashboard DQ Databricks: tutte le aree in verde |
| 3 | Approvazione formale PM Progetto | PM Progetto | Email firmata con lista pre-requisiti verificati |
| 4 | Approvazione formale BA Funzionale principale | BA Funzionale | Email con conferma dati corretti per area di competenza |
| 5 | Finestra di cutover comunicata agli utenti finali | PM Progetto | Email inviata con > 7 giorni di anticipo |
| 6 | Finestra comunicata ai sistemi dipendenti (AtTraspo, Logistix) | PM Progetto | Conferma ricevuta da team AtTraspo e Logistix |
| 7 | Oracle DWH e ODI congelati: nessuna modifica pianificata nelle 72h precedenti | DBA Oracle | Conferma scritta da DBA |
| 8 | Ambiente Databricks production validato (cluster size, autoscaling) | Cloud Architect | Test di carico eseguito; durata workflow < 4h |
| 9 | MicroStrategy connection string Databricks configurata e testata | Team BI | Almeno 3 report aperti correttamente in MicroStrategy puntando a Databricks |
| 10 | Rollback plan distribuito e letto dal team | PM Progetto | Conferma lettura da tutti i partecipanti al cutover |
| 11 | Backup Oracle DWH eseguito e verificato (dump completo) | DBA Oracle | Backup datato < 24h prima del cutover |
| 12 | Numero di supporto Azure Premium aperto e attivo | Cloud Architect | Ticket P2 aperto su Azure Portal |

**Check-go finale:** Riunione di 30 minuti il venerdì mattina prima del cutover per revisione lista.

---

## 2. Finestra di cutover e team di presidio

**Data target:** Sabato notte (da concordare — nominare data specifica in fase di pianificazione)  
**Finestra principale:** 22:00 → 02:00 (4 ore)  
**Presidio notturno post-go-live:** 02:00 → 08:00 (6 ore di monitoraggio)

### Team di presidio

| Ruolo | Presenza richiesta | Modalità |
|---|---|---|
| Cloud Architect / Tech Lead | 22:00 - 08:00 | In sede (o remoto su VPN con laptop aziendale) |
| DBA Oracle | 22:00 - 02:00 | In sede (reperibile fino alle 08:00) |
| Team BI / MicroStrategy | 22:00 - 02:00 | In sede |
| BA Funzionale | 22:00 - 01:30 | Remoto (test smoke test) |
| PM Progetto | 22:00 - 01:30 | Remoto (coordinamento) |
| Responsabile Operativo | Reperibile | Telefono acceso; chiamare se go/no-go non è ovvio |

### Strumenti di comunicazione notturna

- **Canale principale:** Gruppo Teams "Logistico 2.0 — CutOver Night" (creare 3 gg prima)
- **Canale backup:** Gruppo WhatsApp "LOGISTICO CUTOVER"
- **Escalation critica:** Chiamata diretta su mobile

---

## 3. Sequenza step-by-step con orari

> Gli orari sono relativi alla finestra di cutover. "T=22:00" = ora di inizio.  
> "T-7gg" = 7 giorni prima del cutover.

---

### T-7gg — Comunicazione utenti (responsabile: PM Progetto)

```
[ ] Inviare email a tutti gli utenti MicroStrategy:
    Oggetto: "AGGIORNAMENTO SISTEMA - Sabato [DATA] notte: breve interruzione report"
    Corpo:
      "Sabato [DATA] dalle ore 22:00 alle ore 02:00 circa, i report MicroStrategy
       dell'area Logistica saranno temporaneamente non disponibili per manutenzione.
       A partire dalle ore 02:00 del [DATA+1], i report saranno nuovamente accessibili
       con prestazioni migliorate.
       Per informazioni: [contatto PM]"

[ ] Comunicare al team AtTraspo: nessuna estrazione trasporti da fare sabato notte
[ ] Comunicare al team Logistix: nessuna manutenzione programmata sabato notte
```

---

### T-1gg (Venerdì sera) — Verifica finale sistemi (responsabile: Cloud Architect)

```
[ ] 20:00 - Eseguire ultimo run shadow mode e verificare delta < 0.5%
[ ] 20:30 - Verificare spazio disco ADLS2: deve avere > 50% libero
[ ] 20:45 - Verificare cluster Databricks production attivo e responsive
[ ] 21:00 - DBA Oracle conferma: dump backup completato, ODI in stato normale
[ ] 21:15 - Team BI conferma: connection string Databricks configurata e pronta
[ ] 21:30 - PM Progetto: send "GREEN LIGHT" email al team di presidio
[ ] 22:00 - Team presidio connesso su Teams
```

---

### T=22:00 — Blocco aggiornamenti Oracle (responsabile: DBA Oracle)

```
[ ] 22:00 - DBA esegue su Oracle DWH:
            -- Congela le tabelle staging per evitare write concorrenti
            -- Su ogni sistema sorgente (Logistix, AtTraspo):
            UPDATE DB_PARMS SET PARM_VAL = 'FREEZE'
            WHERE PARM_COD = 'STATO_ESTR';
            COMMIT;

[ ] 22:05 - DBA verifica: nessun job ODI in esecuzione
            SELECT JOB_NAME, STATUS FROM ODI_JOBS WHERE STATUS = 'RUNNING';
            -- Deve restituire 0 righe

[ ] 22:10 - DBA notifica su Teams: "Oracle congelato alle 22:10 — OK"

[ ] 22:10 - Cloud Architect informa team: "GO — procedere con STEP successivo"
```

**Criteri go/no-go:** 0 job ODI in esecuzione; DB_PARMS impostato a FREEZE.

---

### T=22:15 — Ultimo ciclo Oracle completato

```
[ ] 22:15 - DBA lancia l'ultimo ciclo completo ODI in modo sincrono:
            -- Questo garantisce che Oracle DWH sia aggiornato all'ultimo dato disponibile
            BEGIN CDT_SA.SP_CARICA_CDT_SYNC(RetCod); END;
            -- Attende il completamento

[ ] 22:15-22:45 - Monitorare completamento ODI (stimato 30 min)
[ ] 22:45 - DBA verifica:
            SELECT MAX(LOAD_DATE), COUNT(*) FROM CDT_DW.F_CARICO
            WHERE LOAD_DATE = TRUNC(SYSDATE);
            -- Conteggio deve essere coerente con baseline

[ ] 22:50 - DBA notifica su Teams: "Ultimo ciclo ODI completato — [N] righe caricate"
```

**Criteri go/no-go:** Ciclo ODI completato con RetCod = 0; conteggio F_CARICO coerente.

---

### T=22:30 — Esecuzione backfill finale Databricks (responsabile: Cloud Architect)

```
[ ] 22:30 - Cloud Architect lancia il backfill finale su Databricks:
            -- Notebook: ops/backfill_completo.py
            -- Parametri: run_date = oggi, include_yesterday = TRUE

            dbutils.notebook.run("ops/backfill_completo", timeout_seconds=3600, {
                "run_date": "$(date +%Y-%m-%d)",
                "force_reload": "true",
                "notify_on_completion": "true"
            })

[ ] 22:30-23:30 - Monitorare avanzamento su Databricks Workflows UI
                  - Bronze: 22:30-23:00 (stimato 30 min)
                  - Silver: 23:00-23:20 (stimato 20 min)
                  - Gold:   23:20-23:30 (stimato 10 min)

[ ] 23:30 - Cloud Architect verifica completamento:
            SELECT COUNT(*) FROM logistico.gold_f_carico WHERE run_date = today;
            -- Deve corrispondere a COUNT(*) FROM CDT_DW.F_CARICO (Oracle)
```

**Criteri go/no-go:** Tutti i workflow terminati senza errori; nessun job in stato FAILED.

---

### T=23:30 — Verifica quadratura finale (responsabile: Cloud Architect + BA)

```
[ ] 23:30 - Cloud Architect esegue notebook di quadratura:
            ops/quadratura_cutover.py
            
            -- Confronta per ogni area:
            -- Oracle CDT_DW vs Databricks gold tables
            
            QUERY ORACLE:
            SELECT 'F_CARICO' tab, COUNT(*) cnt, SUM(QTA_RICEVUTA) tot
            FROM CDT_DW.F_CARICO WHERE TRUNC(DATA_CARICO) = TRUNC(SYSDATE-1)
            UNION ALL
            SELECT 'F_STOCK', COUNT(*), SUM(QTA_DISPONIBILE)
            FROM CDT_DW.F_STOCK WHERE SNAPSHOT_DATA = TRUNC(SYSDATE-1)
            UNION ALL
            SELECT 'F_PREP_SPED', COUNT(*), SUM(NUM_IMB_NUCO_PREP)
            FROM CDT_DW.F_PREP_SPED WHERE GIORNO_BOLLA_SPED_ID = TO_NUMBER(TO_CHAR(SYSDATE-1,'YYYYMMDD'));

            QUERY DATABRICKS:
            SELECT 'gold_f_carico' tab, COUNT(*) cnt, SUM(qta_ricevuta) tot
            FROM logistico.gold_f_carico WHERE data_arrivo = DATE_SUB(CURRENT_DATE(),1)
            UNION ALL
            SELECT 'gold_f_giacenze_daily', COUNT(*), SUM(qta_disponibile)
            FROM logistico.gold_f_giacenze_daily WHERE data_snapshot = DATE_SUB(CURRENT_DATE(),1)
            UNION ALL
            SELECT 'gold_f_prep_sped', COUNT(*), SUM(num_imb_nuco_prep)
            FROM logistico.gold_f_prep_sped WHERE giorno_bolla_sped_id = CAST(...)

[ ] 23:30-23:50 - BA Funzionale revisa il report di quadratura generato
[ ] 23:50 - BA notifica su Teams: "Quadratura OK / KO — [dettagli delta]"
```

**Criteri go/no-go:** Delta < 0.5% su conteggi righe E su misure principali per TUTTE le aree. Se anche una area ha delta > 0.5%: STOP e valutare rollback.

---

### T=00:00 — Redirect MicroStrategy a Databricks (responsabile: Team BI)

```
[ ] 00:00 - Team BI accede a MicroStrategy Admin
[ ] 00:02 - Cambia Database Instance per progetto LOGISTICO:
            Da: "LOGISTICO_DWH_ORACLE"
            A:  "LOGISTICO_DWH_DATABRICKS"
[ ] 00:05 - Svuota cache MicroStrategy (Administration → Cache → Invalidate All)
[ ] 00:08 - Apre primo report di test (vedi Smoke Test checklist)
[ ] 00:10 - Notifica su Teams: "MicroStrategy ora punta a Databricks"
```

**Criteri go/no-go:** MicroStrategy risponde con dati; primo report caricato < 60 secondi.

---

### T=00:30 — Smoke test report principali (responsabile: BA + Team BI)

Eseguire checklist smoke test completa (vedi Sezione 4).  
Durata stimata: 30 minuti.

**Criteri go/no-go:** Almeno 12/15 check OK. Nessun check critico (marcato ★) fallito.

---

### T=01:00 — Comunicazione go-live (responsabile: PM Progetto)

```
[ ] 01:00 - PM invia email agli utenti:
            Oggetto: "SISTEMA OPERATIVO - Report disponibili"
            Corpo:
              "Il sistema di reporting logistico è stato aggiornato con successo.
               Tutti i report MicroStrategy sono ora accessibili e mostrano dati
               con prestazioni migliorate.
               In caso di anomalie, contattare: [supporto]"

[ ] 01:05 - PM notifica management: "Go-live completato alle [ora] — tutto OK"
[ ] 01:10 - Cloud Architect aggiorna ticket di progetto: stato = PRODUZIONE
```

---

### T=01:00-08:00 — Presidio notturno (responsabile: Cloud Architect)

```
[ ] Ogni 30 minuti: verificare Dashboard Databricks (workflow, alert)
[ ] 02:00 - BA e PM possono disconnettersi (reperibili su telefono)
[ ] 02:00 - Cloud Architect rimane connesso fino alle 08:00
[ ] 06:00 - Cloud Architect esegue verifica manuale 5 KPI principali in MicroStrategy
[ ] 07:30 - Cloud Architect prepara report go-live per riunione del mattino
[ ] 08:00 - Riunione di stato con PM, BA, management (30 min)
```

---

## 4. Smoke Test checklist: 15 check funzionali su report MicroStrategy

Eseguire al T=00:30. I check marcati ★ sono CRITICI: fallimento = no-go immediato.

| # | Report MicroStrategy | Area | Verifica | Criterio accettazione |
|---|---|---|---|---|
| 1 ★ | Dashboard Carichi Giornalieri | Carichi | Aprire il report per ieri | Carica < 60 sec; dati presenti; nessun "#Error" |
| 2 ★ | Report Stock Attuale per Sito | Giacenze | Aprire il report | Quantità disponibili > 0; snapshot = ieri |
| 3 ★ | Report Preparazioni Spedizioni | Prep Sped | Aprire il report per ieri | Colli e valore cessione presenti |
| 4 ★ | KPI Fill Rate Trasporti | Trasporti | Aprire il report | Fill rate nel range [85%-100%] |
| 5 ★ | Report Movimentazione Carrellisti | Carrellisti | Aprire il report per ieri | Missioni > 0; ore produttive presenti |
| 6 | Report Tracciabilità Lotti (CE178) | Tracciabilità | Aprire il report | Lotti con giacenza presenti |
| 7 | Dashboard Saturation Magazzino | Giacenze | Aprire la dashboard | Percentuale saturazione per sito visualizzata |
| 8 | Report Aging Articoli | Giacenze | Aprire il report | Articoli classificati per giorni in giacenza |
| 9 | Report Ordini Fornitori | Trasporti | Aprire il report | Ordini con data > 30 gg fa presenti |
| 10 | Report Costi Trasporto | Trasporti | Aprire il report | Costi per corriere e tratta presenti |
| 11 | Report Performance Operatori | Carrellisti | Aprire il report | Missioni/ora per operatore presenti |
| 12 | Drill-down da F_CARICO a dettaglio bolla | Carichi | Eseguire drill | Dettaglio riga carico visibile |
| 13 ★ | Filtro per data su report carichi | Carichi | Filtrare per oggi-7 | Risultati restituiti in < 30 sec |
| 14 | Export Excel di un report | QQ | Esportare 1 report | File Excel scaricato correttamente |
| 15 ★ | Conteggio righe report vs Oracle (manuale) | QQ | Confronto manuale | Delta < 1% su almeno 2 report |

**Criteri di passaggio:**
- Checks critici (★): tutti devono essere OK → altrimenti no-go
- Checks non critici: almeno 8/10 devono essere OK
- Check 15: delta < 1% obbligatorio

---

## 5. Criteri go/no-go per ogni fase

| Fase | Orario | Criterio GO | Criterio NO-GO | Azione se NO-GO |
|---|---|---|---|---|
| Congelamento Oracle | 22:00 | 0 job ODI running | Job ODI in running non terminano | Attendere max 30 min; poi kill job e procedere |
| Ultimo ciclo ODI | 22:45 | Ciclo completato, RetCod=0 | Ciclo fallisce o conta < 90% baseline | STOP: investigare; posticipare cutover |
| Backfill Databricks | 23:30 | Tutti workflow OK | Qualsiasi workflow FAILED | Tentare re-run una volta; se fallisce: rollback |
| Quadratura finale | 23:50 | Delta < 0.5% su tutte le aree | Delta > 0.5% su qualsiasi area | STOP: analisi causa; se non risolvibile in 30 min: rollback |
| Redirect MicroStrategy | 00:10 | Primo report aperto < 60s | Report non carica o errore | Rollback MicroStrategy a Oracle; investigare |
| Smoke test | 00:30 | 12/15 check OK, 0 critici KO | Check critico ★ fallito | Rollback MicroStrategy + escalation |
| Comunicazione go-live | 01:00 | Smoke test OK | Smoke test parzialmente KO | Ritardare comunicazione; presidio intensificato |

---

## 6. Escalation: chi chiamare se un passo fallisce

### Matrice di escalation per problema

| Problema | Primo contatto | Se non risolto in 15 min | Se non risolto in 30 min |
|---|---|---|---|
| Workflow Databricks FAILED | Cloud Architect | Tech Lead Databricks Senior | Attivare Rollback Plan |
| ODI non si riattiva | DBA Oracle | DBA Senior / Oracle Support | Rollback: saltare step 3 se Oracle già ok |
| MicroStrategy non vede Databricks | Team BI | Architect MicroStrategy | Rollback MicroStrategy a Oracle |
| Delta quadratura > soglia | Cloud Architect + BA | Investigazione dati 30 min | Rollback se non identificata causa |
| Azure ADLS2 irraggiungibile | Cloud Architect | Azure Support P1 | Attendere; Rollback se > 45 min |
| Cluster Databricks non parte | Cloud Architect | Azure Support P1 | Rollback |

### Script di decisione per go/no-go

```
SE (problema identificato) ALLORA:
  SE (stimato fix < 30 minuti E siamo prima delle 00:30) ALLORA:
    → Tentare fix; riallineare timeline
  ALTRIMENTI SE (siamo dopo le 00:30 E smoke test già OK) ALLORA:
    → Monitorare; rollback solo se impatto utente confermato
  ALTRIMENTI:
    → ROLLBACK: seguire rollback_plan.md
```

---

## 7. Appendice: contatti e accessi

### URL e accessi sistemi

| Sistema | URL | Credenziali |
|---|---|---|
| Databricks Production | https://[workspace].azuredatabricks.net | PAT in Azure Key Vault |
| Oracle DWH | [inserire host:port/service] | CDT_SA user (vedere DBA) |
| MicroStrategy Web Admin | http://[microstrategy-host]/MicroStrategy/admin | Admin credentials |
| Azure Portal | https://portal.azure.com | Account aziendale |
| Azure Monitor / Alerts | https://portal.azure.com/#view/alerts | — |

### Procedure di emergenza pre-configurate

Prima del cutover, assicurarsi che siano pronti:

1. **Notebook Databricks** `ops/backfill_completo.py` — testato e funzionante
2. **Notebook Databricks** `ops/quadratura_cutover.py` — output pre-validato
3. **Script MicroStrategy Command Manager** per switchover DB instance — testato in staging
4. **Script SQL Oracle** per congelamento/scongelamento DB_PARMS — disponibile su repo
5. **Contatto ODI** pre-aperto su Oracle Support (in caso di crash ODI)
