# Rollback Plan — Migrazione Oracle → Databricks

**Progetto:** Logistico 2.0  
**Autore:** Cloud Solution Architect  
**Data:** 2026-05-29  
**Versione:** 1.0  
**Classificazione:** OPERATIVO — distribuire a tutto il team prima del go-live

---

## Indice

1. [Obiettivo e ambito](#1-obiettivo-e-ambito)
2. [Trigger per rollback: criteri di attivazione](#2-trigger-per-rollback-criteri-di-attivazione)
3. [Matrice RACI — responsabilità decisionale](#3-matrice-raci--responsabilità-decisionale)
4. [Procedura rollback step-by-step](#4-procedura-rollback-step-by-step)
5. [Tempo totale stimato](#5-tempo-totale-stimato)
6. [Verifica post-rollback: checklist 10 punti](#6-verifica-post-rollback-checklist-10-punti)
7. [Contatti di emergenza](#7-contatti-di-emergenza)
8. [Condizioni per ritentare il go-live](#8-condizioni-per-ritentare-il-go-live)

---

## 1. Obiettivo e ambito

Questo documento definisce le procedure da seguire in caso di necessità di tornare al sistema Oracle (ODI + MicroStrategy su Oracle DWH) dopo il go-live su Databricks.

**Il rollback ripristina:**
- I workflow Databricks vengono sospesi
- I job Oracle ODI vengono riabilitati
- MicroStrategy viene reindirizzato verso Oracle DWH
- Gli utenti riacquistano accesso ai report originali

**Il rollback NON ripristina:**
- I dati scritti su Databricks durante il periodo di esercizio (rimangono disponibili per analisi future)
- Le configurazioni di connessione Databricks (rimangono invariate per il re-tentativo)

**Condizione necessaria:** Mantenere Oracle ODI e Oracle DWH operativi e aggiornati in parallelo a Databricks per almeno **30 giorni** dopo il go-live (fase shadow post-cutover).

---

## 2. Trigger per rollback: criteri di attivazione

### Trigger automatici (rollback immediato senza discussione)

| ID | Trigger | Soglia | Rilevamento |
|---|---|---|---|
| T1 | Delta KPI critico: % report con scostamento > soglia | > 5% dei KPI principali con delta > 1% rispetto Oracle | Alert Databricks + monitoraggio manuale post-cutover |
| T2 | Report MicroStrategy non accessibili | Qualsiasi report MicroStrategy principale non caricabile per > 30 minuti | Monitoraggio MicroStrategy + segnalazioni utenti |
| T3 | Errore critico nei workflow Databricks | Workflow bronze o silver falliti per > 2 cicli consecutivi senza recupero | Alert workflow Databricks |
| T4 | Delta Lake corruption | Errore DELTA_INVALID o SNAPSHOT_NOT_FOUND su gold tables principali | Log Databricks + job falliti |
| T5 | Impatto operativo grave | Segnalazione documentata da responsabile operativo che le decisioni di business sono bloccate | Comunicazione formale via email |

### Trigger discrezionali (richiedono consenso PM + BA)

| ID | Trigger | Soglia orientativa |
|---|---|---|
| T6 | Performance report MicroStrategy | Tempo di caricamento report principale > 3× baseline Oracle per > 2 ore |
| T7 | Volume dati anomalo | Numero righe gold_f_carico / gold_f_prep_sped devia > 2% da Oracle DWH |
| T8 | Errori utente sistematici | > 10 segnalazioni di errore dati da parte degli stessi utenti su report diversi |

---

## 3. Matrice RACI — responsabilità decisionale

| Attività | PM Progetto | Cloud Architect | DBA Oracle | Team BI/MicroStrategy | BA Funzionale |
|---|---|---|---|---|---|
| **Decidere il rollback** | A | C | I | C | C |
| **Comunicare la decisione al business** | R | I | I | I | R |
| **Sospendere workflow Databricks** | I | R | I | I | I |
| **Riabilitare job Oracle ODI** | I | C | R | I | I |
| **Verificare Oracle funzionante** | I | C | R | C | I |
| **Redirigere MicroStrategy** | I | C | I | R | I |
| **Comunicare go-live rollback agli utenti** | R | I | I | I | A |
| **Post-mortem e analisi** | A | R | C | C | C |

**Legenda:** R = Responsible (esegue), A = Accountable (decide), C = Consulted, I = Informed

---

## 4. Procedura rollback step-by-step

### STEP 1 — Decisione e comunicazione (durata stimata: 30 minuti)

**Responsabile:** PM Progetto + Cloud Architect

```
[ ] 1.1 PM convoca call di emergenza con: Cloud Architect, BA, Team BI
[ ] 1.2 Presentare evidenza del trigger (screenshot alert, dati KPI, log)
[ ] 1.3 Votazione formale: rollback SI / NO con maggioranza semplice
[ ] 1.4 PM invia email a lista distribuzione "LOGISTICO_ROLLBACK":
         - Oggetto: "ROLLBACK ATTIVATO - Logistico 2.0 - [data/ora]"
         - Corpo: trigger identificato, decision, eta completamento
[ ] 1.5 PM notifica management (CdA / Direzione Logistica) via WhatsApp
```

**Criteri go/no-go per proseguire:** Consenso formale (email o verbale in call registrata).

---

### STEP 2 — Sospensione workflow Databricks (durata stimata: 15 minuti)

**Responsabile:** Cloud Architect

```
[ ] 2.1 Accedere a Databricks Workspace: https://<workspace>.azuredatabricks.net
[ ] 2.2 Navigare: Workflows → Jobs
[ ] 2.3 Per ogni job attivo (lista sotto), selezionare e clicken "Pause":
         - wf_bronze_carichi_daily
         - wf_bronze_giacenze_daily
         - wf_bronze_prep_sped_daily
         - wf_bronze_trasporti_daily
         - wf_bronze_carrellisti_daily
         - wf_silver_all_daily
         - wf_gold_all_daily
         - wf_compliance_ce178_daily
[ ] 2.4 Verificare che nessun job sia in stato "Running" (attendere completamento
         o annullare con "Cancel Run" se in corso)
[ ] 2.5 Documentare l'ora di sospensione e l'ultimo run completato con successo
         per ogni workflow

ALTERNATIVA CLI (se UI non disponibile):
  databricks jobs list | grep -v PAUSED | awk '{print $1}' | xargs -I{} databricks jobs update --job-id {} --pause-status PAUSED
```

**Criteri go/no-go:** Tutti i workflow in stato PAUSED; nessun job in stato RUNNING.

---

### STEP 3 — Riabilitazione job Oracle ODI (durata stimata: 30 minuti)

**Responsabile:** DBA Oracle + Cloud Architect (supporto)

```
[ ] 3.1 DBA accede a ODI Studio (Oracle Data Integrator)
[ ] 3.2 Verificare stato dei seguenti scenari/chain ODI (devono essere in stato DISABLED):
         - SCN_CARICO_GIORNALIERO
         - SCN_STOCK_GIORNALIERO
         - SCN_PREP_SPED_GIORNALIERO
         - SCN_TRASPORTI_GIORNALIERO
         - SCN_CARRELLISTI_GIORNALIERO
[ ] 3.3 Per ogni scenario: clic destro → Enable
[ ] 3.4 Verificare che i trigger di scheduling siano attivi (Operating System 
         o Scheduler ODI configurato per lancio ore 03:00)
[ ] 3.5 Eseguire manualmente un run di test per SCN_CARICO_GIORNALIERO con
         data = ieri: verificare completamento entro 20 minuti
[ ] 3.6 Confermare a PM via messaggio: "ODI riabilitato, test OK"

NOTA: Se ODI non era stato disabilitato prima del cutover (solo "sorvegliato"),
      verificare che non ci siano doppi caricamenti nelle ultime 24h di Oracle.
      In tal caso: TRUNCATE delle tabelle staging Oracle e rilanciare ODI completo.
```

**Criteri go/no-go:** Scenario test ODI completato con RetCod = 0; tabelle DW Oracle aggiornate.

---

### STEP 4 — Verifica Oracle funzionante (durata stimata: 1 ora)

**Responsabile:** DBA Oracle + BA Funzionale

```
[ ] 4.1 Eseguire query di quadratura su Oracle DWH:
         SELECT COUNT(*) FROM CDT_DW.F_CARICO WHERE TRUNC(DATA_CARICO) = TRUNC(SYSDATE-1);
         -- Confrontare con conteggio atteso (baseline pre-cutover)
         
[ ] 4.2 Verificare che F_STOCK sia aggiornato alla data odierna:
         SELECT MAX(SNAPSHOT_DATA) FROM CDT_DW.F_STOCK;
         -- Deve essere = ieri
         
[ ] 4.3 Verificare F_PREP_SPED ultimi 2 giorni:
         SELECT GIORNO_BOLLA_SPED_ID, COUNT(*), SUM(NUM_IMB_NUCO_PREP)
           FROM CDT_DW.F_PREP_SPED
          WHERE GIORNO_BOLLA_SPED_ID >= TO_NUMBER(TO_CHAR(SYSDATE-2,'YYYYMMDD'))
          GROUP BY GIORNO_BOLLA_SPED_ID ORDER BY 1;

[ ] 4.4 BA Funzionale apre MicroStrategy (ancora connesso a Oracle) e verifica
         manualmente 3 report chiave:
         - Report Carichi Giornalieri
         - Report Stock Attuale
         - Report Prep Spedizioni

[ ] 4.5 Se tutto OK: BA conferma a PM "Oracle OK, dati verificati"
[ ] 4.6 Se KO: escalation a DBA Senior per investigazione; aggiornare ETA rollback
```

**Criteri go/no-go:** Conteggi Oracle coerenti con baseline; almeno 3 report MicroStrategy aperti correttamente.

---

### STEP 5 — Reindirizzamento MicroStrategy a Oracle (durata stimata: 30 minuti)

**Responsabile:** Team BI / MicroStrategy

```
[ ] 5.1 Accedere a MicroStrategy Developer (o Web Admin)
[ ] 5.2 Navigare: Administration → Database Instances
[ ] 5.3 Trovare istanza "LOGISTICO_DWH_DATABRICKS" (aggiunta al cutover)
[ ] 5.4 Per ogni progetto MicroStrategy in scope (LOGISTICO, TRASPORTI, ecc.):
         - Clic destro sul progetto → Modify
         - Database Instance → cambiare da "LOGISTICO_DWH_DATABRICKS"
                               a    "LOGISTICO_DWH_ORACLE"
[ ] 5.5 Salvare le modifiche
[ ] 5.6 Svuotare la cache MicroStrategy: Administration → Cache → Invalidate All
[ ] 5.7 Testare accesso a 2 report per progetto

ALTERNATIVA (se configurato):
  Usare MicroStrategy Command Manager per scripted switchover:
  ALTER DATABASE INSTANCE "LOGISTICO_DWH_DATABRICKS"
    ODBC CONNECTION = "LOGISTICO_DWH_ORACLE";
```

**Criteri go/no-go:** Almeno 5 report principali accessibili e con dati aggiornati a ieri.

---

### STEP 6 — Comunicazione agli utenti (durata stimata: 15 minuti)

**Responsabile:** PM Progetto + BA Funzionale

```
[ ] 6.1 PM invia email a tutti gli utenti MicroStrategy:
         Oggetto: "RIPRISTINO SISTEMA - Accesso report ora disponibile"
         Corpo:
           "A seguito di un'anomalia tecnica rilevata dopo l'aggiornamento del sistema,
            abbiamo effettuato un ripristino alla versione precedente.
            I vostri report MicroStrategy sono nuovamente accessibili e 
            visualizzano dati aggiornati alla data di ieri.
            Ci scusiamo per il disagio. Sarete informati sulle prossime attività."

[ ] 6.2 BA Funzionale invia messaggio ai referenti business di ogni area:
         - Area Carichi: [nome referente]
         - Area Giacenze: [nome referente]
         - Area Prep Spedizioni: [nome referente]
         - Area Trasporti: [nome referente]

[ ] 6.3 PM aggiorna ticket di progetto con: trigger, tempi, azioni intraprese
```

---

## 5. Tempo totale stimato

| Step | Attività | Durata | Cumulativo |
|---|---|---|---|
| 1 | Decisione e comunicazione | 30 min | 0:30 |
| 2 | Sospensione workflow Databricks | 15 min | 0:45 |
| 3 | Riabilitazione job Oracle ODI | 30 min | 1:15 |
| 4 | Verifica Oracle funzionante | 60 min | 2:15 |
| 5 | Redirect MicroStrategy | 30 min | 2:45 |
| 6 | Comunicazione utenti | 15 min | 3:00 |

**Tempo totale: ~ 3 ore** (obiettivo < 3 ore; worst case 4 ore se ODI richiede intervento manuale)

**Window critica:** Il rollback deve essere completato entro le 08:00 se attivato di notte, per garantire che gli utenti trovino i report operativi all'apertura uffici.

---

## 6. Verifica post-rollback: checklist 10 punti

Eseguire entro 2 ore dal completamento del rollback (idealmente alle 08:00).

| # | Verifica | Responsabile | Atteso | Esito |
|---|---|---|---|---|
| 1 | Report "Carichi Giornalieri" apre in MicroStrategy | BA Funzionale | Caricamento < 30 sec, dati di ieri presenti | [ ] OK [ ] KO |
| 2 | Report "Stock Attuale per Sito" apre correttamente | BA Funzionale | Dati snapshot di ieri | [ ] OK [ ] KO |
| 3 | Report "Preparazioni Spedizioni" mostra dati di ieri | BA Funzionale | Colli e valore cessione coerenti | [ ] OK [ ] KO |
| 4 | Report "Trasporti e Fill Rate" apre correttamente | BA Funzionale | Fill rate nel range storico normale | [ ] OK [ ] KO |
| 5 | Report "Movimentazione Carrellisti" funzionante | BA Funzionale | Missioni e ore produttive di ieri | [ ] OK [ ] KO |
| 6 | Nessun workflow Databricks in stato RUNNING | Cloud Architect | Tutti PAUSED | [ ] OK [ ] KO |
| 7 | Job ODI di ieri notte completato con stato OK | DBA Oracle | RetCod = 0 in DWH_LOG | [ ] OK [ ] KO |
| 8 | Conteggio F_CARICO Oracle = baseline ± 0.1% | DBA Oracle | Verifica query confronto | [ ] OK [ ] KO |
| 9 | Nessuna segnalazione di errore utente nelle 2h post-rollback | PM Progetto | Inbox email vuota da segnalazioni | [ ] OK [ ] KO |
| 10 | Log rollback documentato su ticket di progetto | PM Progetto | Ticket aggiornato con timeline e causa | [ ] OK [ ] KO |

**Condizione di successo:** Tutti i 10 punti OK. In caso di KO su punti 1-5: escalation immediata.

---

## 7. Contatti di emergenza

| Ruolo | Nome | Contatto principale | Contatto backup |
|---|---|---|---|
| PM Progetto | [INSERIRE NOME] | [mobile] | [email] |
| Cloud Architect / Tech Lead | [INSERIRE NOME] | [mobile] | [email] |
| DBA Oracle Senior | [INSERIRE NOME] | [mobile] | [email] |
| Responsabile Team BI / MicroStrategy | [INSERIRE NOME] | [mobile] | [email] |
| BA Funzionale Logistica | [INSERIRE NOME] | [mobile] | [email] |
| Responsabile IT Infrastrutture | [INSERIRE NOME] | [mobile] | [email] |
| Referente Business (Direz. Logistica) | [INSERIRE NOME] | [mobile] | [email] |
| Support Azure (P1 ticket) | Microsoft | [portal link] | 02-xxx-xxx |

**Canale di comunicazione emergenza:** Gruppo WhatsApp "LOGISTICO 2.0 - EMERGENZA" (creare prima del go-live con tutti i ruoli sopra).

---

## 8. Condizioni per ritentare il go-live

Dopo un rollback, il re-tentativo del go-live richiede:

### Condizioni tecniche obbligatorie

| # | Condizione | Verifica |
|---|---|---|
| 1 | Causa root del problema identificata e documentata | Post-mortem completato e approvato da Cloud Architect |
| 2 | Fix applicato e testato in ambiente di staging | Test regression completo su staging con dati reali del giorno del fallimento |
| 3 | Shadow mode ri-eseguito per almeno 5 giorni lavorativi dopo il fix | Report di shadow mode approvato da BA con delta < 0.5% su tutti i KPI |
| 4 | Rollback plan aggiornato per coprire il nuovo scenario | Questo documento aggiornato con learnings dal primo tentativo |
| 5 | Oracle DWH e ODI ancora operativi (non dismessi) | DBA conferma sistema Oracle ancora accessibile e aggiornato |

### Condizioni temporali

- **Minimo:** 10 giorni lavorativi dopo il rollback prima del re-tentativo
- **Massimo:** 60 giorni dopo il primo go-live (dopo: rivalutare approccio progettuale)
- **Finestra:** Stessa finestra del sabato notte; mai durante periodo di picco operativo (es. festività, inizio mese)

### Approvazione formale

Prima del re-tentativo, è necessaria la firma di approvazione da:
- [ ] PM Progetto
- [ ] Responsabile Business (Direzione Logistica)
- [ ] Cloud Architect
- [ ] BA Funzionale principale
