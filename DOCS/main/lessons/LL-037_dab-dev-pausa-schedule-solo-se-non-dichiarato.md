---
id: LL-037
titolo: "DAB mode:development mette in pausa gli schedule solo se `pause_status` non è dichiarato — un UNPAUSED esplicito li lascia attivi in dev"
sintomi:
  - "i job [dev <identità>] girano ogni notte da soli nonostante il target sia mode: development"
  - "arrivano email di failure notturne da job di sviluppo"
  - "bundle validate -t dev -o json mostra pause_status: UNPAUSED su job con prefisso [dev ...]"
  - "un job DAB messo in pausa a mano torna attivo al deploy successivo"
tag: [databricks, dab, schedule, deploy, dev, costi]
stadio: regola-documentata
automatizzabile: true
autore: Francesco Foconi
data: 2026-10-09
origine: [pausa-schedule-job-dev]
---

## Sintomo
I 7 job `[dev id_dev_dataplatform_workload_00] logistica_*` (target `dev`, `mode: development`) giravano
**ogni notte** come da cron, consumando compute: 3 su 7 fallivano ogni notte (landing assente per il giorno
corrente) e mandavano l'email di failure. Ci si aspettava che la modalità development li tenesse in pausa.

## Strada sbagliata
- **Mettere in pausa a mano** (UI o `jobs update`): funziona fino al deploy successivo. DAB è dichiarativo e il
  prossimo `bundle deploy` riapplica lo YAML, quindi i job tornano attivi (stesso principio di [[LL-032]]).
- **Scrivere `pause_status: PAUSED` nello YAML**: lo YAML è condiviso tra i target, quindi metterebbe in pausa
  anche **prod**, dove lo schedule deve girare.

## Regola
Negli YAML dei job **non dichiarare `pause_status`** nello `schedule` (né nei `trigger`/`continuous`): lascia
decidere alla modalità del target.
- `mode: development` → **PAUSED** in automatico, a qualunque deploy (CI o sandbox personale).
- `mode: production` → nessuna modifica → schedule **attivo** (default dell'API Jobs).

Verifica prima del deploy, senza toccare nulla:
```bash
databricks bundle validate -t dev  -o json   # resources.jobs.*.schedule.pause_status -> PAUSED
databricks bundle validate -t prod -o json   # -> UNPAUSED
```
Se serve un controllo esplicito per target, usare `presets.trigger_pause_status` sul target, non lo YAML del job.

## Perché
In development il bundle mette in pausa uno schedule **solo se il suo `pause_status` non è già UNPAUSED**: un
valore esplicito viene rispettato. Il prefisso `[dev ...]` nel nome dimostra che la trasformazione della
modalità è stata applicata, ma non tocca un `UNPAUSED` scritto a mano.

## Conferme e contraddizioni
- 2026-10-09 · `bundle validate -t dev -o json`: con `pause_status: UNPAUSED` nei 7 YAML → **UNPAUSED** (nome
  `[dev flabffoconi] ...`); tolta la riga → **PAUSED** su tutti e 7, mentre `-t prod` resta **UNPAUSED**.
  Prima del fix i 7 job dev avevano girato tutte le notti (06→09/10). Vedi worklog 2026-10-09-01.
