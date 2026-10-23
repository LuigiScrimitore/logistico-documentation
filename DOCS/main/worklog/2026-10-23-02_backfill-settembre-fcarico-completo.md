---
data: 2026-10-23
titolo: "Backfill settembre F_CARICO: da 20 giorni incompleti (94.784) a 30/30 completi (657.114) — tutto il gold su v2.2.0"
autore: Francesco Foconi
push_monorepo: "main"
push_github: "documentation + workflows (config_backfill.yaml)"
push_gitlab: "nessuno (helper locale + doc; nessuna modifica pipeline)"
act: [ACT_9035]
adr: []
lesson: []
op: [Q-01]
---

## Contesto
Dopo la fix del 2% (ACT_9035) la domanda: "tutto il gold F_CARICO è a posto?" No — il re-run aveva toccato
solo 202610. Settembre (202609) era non solo mal-processato ma **incompleto**: **20/30 giorni**, 94.784 righe
(buchi 03–08, 23, 25–27) → ingestion parziale in ramp-up.

## Fatto
- **Ricarico dalla sorgente** con `extract_oracle_to_landing.py`. Scoperto che `--from-date/--to-date` +
  `--ignore-odi-flag` **non bastano**: le tabelle carichi hanno `selection: legacy_flag` (ACT_9030) che
  **sostituisce** finestra-data e flag (verificato in dry-run). Soluzione: **config dedicata**
  `scripts/landing_simulator/config_backfill.yaml` (copia con `selection` disattivata) → `--config` →
  la SQL diventa `WHERE <data> BETWEEN from AND to` con flag ignorato. Verificato su dato reale.
- Estrazione 3 blocchi da 10 gg (`sto_tes_carichi,sto_righe_carico,pesate`, 19 siti con dati) ≈ **1,23M righe**.
- Copia su **Volume** `landing_dev` (l'abfss landing non è scrivibile dall'utente — [[ACT_9034]]).
- Pipeline mirata **ramo F_CARICO** (run 552522402835429): bronze con `landing_base_path`=Volume (09/10-20-30,
  catene per-tabella sequenziali), silver `full_refresh`, `silver_prep_carico`(202609), `gold_f_carico`.

## Esito
- gold F_CARICO **202609: 94.784 → 657.114 righe** (= etichette distinte, **0 fan-out**), **30/30 giorni**,
  distribuzione feriale/weekend regolare e coerente con ottobre. **202610 invariato** (439.229).
- **Tutto il gold F_CARICO disponibile (set+ott) è ora completo e su logica v2.2.0.**

## Indicazioni al team
- Per un **backfill storico** dei carichi: usare `--config config_backfill.yaml` (selection off) +
  `--from-date/--to-date --ignore-odi-flag`; copiare sul **Volume** e lanciare il bronze con
  `landing_base_path`=Volume (l'abfss landing è read-only per gli utenti).
- **Aperto**: settembre non quadrato vs ODI (manca estratto ODI settembre); downstream F_CARICO
  (aggregati/LAD) da rinfrescare; valutare un flag CLI `--no-selection` per evitare la config duplicata.
