---
data: 2026-10-14
titolo: "Piano: cutover della landing dev su logisticolanding (percorso diretto) + job orchestratore che parte all'arrivo dei file"
autore: Francesco Foconi
push_monorepo: "PR dedicata"
push_documentation: "da ri-split dopo merge"
push_gitlab: "workflows: da rilasciare (solo main, nessun tag)"
act: [ACT_OP-INF-4]
adr: [ADR-0003]
lesson: [LL-037]
op: [OP-INF-4]
---

## Contesto
Obiettivo: rischedulare i job dev del logistico in modo che partano **quando ci sono i file**, non a orario fisso.
Oggi i 7 job `[dev id_dev_dataplatform_workload_00] logistica_*` sono in pausa ([[LL-037]]).

Perché fallivano ogni notte (verificato sui run del 09/10):
- cercavano i file del giorno nel Volume managed `/Volumes/landing_dev/logistica/files/…/YYYY/MM/DD`, che non viene più
  alimentato: i file nuovi arrivano su `logisticolanding` ([[ACT_OP-INF-4]]). Errori `PATH_NOT_FOUND` in
  `landing_ingestion` (apvpunto_vendita, buoni_eco), `dim_refresh` (`gold_lu_from_cdtdw`), `trasporti` (automezzi, spedizioni);
- i job "verdi" (`carichi`, `giacenze`, `prep_sped`, `datamart`) **non facevano niente**: i loro notebook bronze escono
  con `NO_DATA` se manca la cartella. Stesso caso gestito in due modi diversi;
- la `run_date` di default (`{{job.start_time.iso_date}}`) è in **UTC**: `landing_ingestion` alle 00:30 italiane cercava il
  giorno prima, `trasporti` alle 05:00 lo stesso giorno. Date diverse nella stessa notte.

## Decisioni
1. **Cutover con percorso diretto, senza Volume.** `landing_base_path` (dev) passa da `/Volumes/landing_dev/logistica/files`
   a `abfss://logisticolanding@stdevdataplatformweudata.dfs.core.windows.net`. I notebook costruiscono
   `{landing_base_path}/<area>-landing/...` e accettano `abfss://` (era il default previsto). Nessun permesso nuovo: la
   External Location `logisticolanding_dev` dà `READ_FILES` a `Group-Engineering-dev`, che contiene la Managed Identity
   dei job. Il Volume managed resta com'è con lo storico (nessuna migrazione bloccante). Cambia l'impostazione di
   [[ADR-0003]] (landing = Volume) per dev; il Volume external resta un'opzione futura.
2. **Segnale di landing completa.** A fine invio riuscito `extract_and_send.sh` scrive
   `_control/<env>/<sistema>/<run_date>/_SUCCESS` (run_date, file, esito) nel container. Il trigger guarda solo quel
   percorso: non parte a metà invio, non parte se l'estrazione è KO, e resta sotto il limite di ~10.000 file del trigger
   senza "file events".
3. **Job orchestratore** con trigger **File arrival** sul percorso di controllo, che lancia i 7 job esistenti in ordine:
   `landing_ingestion` → `dim_refresh` → `carichi` · `giacenze` · `trasporti` → `prep_sped` → `datamart`. La `run_date`
   viene dal segnale, uguale per tutta la catena. I 7 job restano lanciabili a mano, senza orari propri.
4. **Trigger attivo solo nel deploy della CI** (Managed Identity), in pausa nei deploy delle sandbox personali, per non avere
   più orchestratori sugli stessi file e cataloghi ([[LL-037]]).
5. **Controllo di sicurezza** (es. 09:00): avviso se il segnale del giorno non è arrivato.

## Passi
1. Giro di prova a mano di `landing_ingestion` sul 2026-10-14 con `landing_base_path` = container (parametro del job,
   nessuna modifica al bundle).
2. `landing_base_path` dev nel `databricks.yml` → container.
3. Segnale `_SUCCESS` in `extract_and_send.sh` + deploy su odi3.
4. Job orchestratore + trigger (attivo solo CI) + controllo di sicurezza; rilascio `workflows` su GitLab.

## Esito
- **Passo 1, giro di prova** (`landing_ingestion`, run_date 2026-10-14, `landing_base_path` = container, run
  533310242585802): **il cutover funziona**. 11 tabelle bronze lette e caricate da `logisticolanding` senza errori di
  permesso (la Managed Identity legge via `Group-Engineering-dev`). 3 task in `PATH_NOT_FOUND` su
  `cdt-estr-raw-landing` (`apvpunto_vendita`, `s_logistix`, `wl1_mag_sito_storico`): quelle cartelle nel container non
  esistono per nessun giorno.
- **Bug trovato**: `extract_and_send.sh` passava di default `SYSTEMS=logistix,stat,cdt_estr,track`, ma nel `config.yaml`
  il sistema si chiama `cdt_estr_raw`, e l'estrattore ignorava in silenzio i nomi sconosciuti. Le anagrafiche CDT_ESTR
  (`apvpunto_vendita`, `automezzi`, `estrai_spedizioni`, `s_logistix`, `wl1_mag_sito_storico`) non sono mai state
  estratte sul relay. Correzione: default `cdt_estr_raw`; l'estrattore termina con errore se `--systems` contiene un
  nome che non è nel `config.yaml` (help e guida di test locale aggiornati, `cnd` era un sistema eliminato).
  Dopo il deploy su odi3: estrazione `cdt_estr_raw` del giorno e ripetizione del giro di prova.
