---
data: 2026-10-12
titolo: "Salvaguardia: con una run_date passata l'estrazione esclude le tabelle snapshot (catena, catena_esterni)"
autore: Francesco Foconi
push_monorepo: "PR #27 @b6dc815 (estrattore + extract_and_send.sh + doc) + PR esito"
push_documentation: "133abf0 (+ esito)"
push_gitlab: "—"
act: [ACT_OP-INF-4]
adr: []
lesson: [LL-006]
op: [OP-INF-4]
---

## Contesto
Le tabelle **snapshot** (`catena`, `catena_esterni` → giacenze) non hanno filtro per data: sono la fotografia
della giacenza nel momento dell'estrazione, e la data della cartella è solo l'etichetta presa dal `run_date`.
Il giro manuale con `run_date=2026-10-02`, lanciato l'11/10 sera, ha messo nella cartella `2026/10/02` la giacenza
dell'11/10 (9 giorni di scarto). Anche gli altri giri manuali erano stati lanciati il giorno dopo (scarto ~1 giorno).
Una fotografia sbagliata non si può correggere dopo: quella vera non esiste più ([[LL-006]]).
Il job ODI schedulato (ogni mattina, `run_date` = oggi) non ha il problema; il rischio è il rilancio con una data passata.

## Cosa
- `extract_oracle_to_landing.py`: nuova opzione **`--skip-snapshot`**, salta le tabelle con `mode: snapshot`
  (decise dal `config.yaml`, non da nomi scritti nel codice). Default spento: nessun cambio per gli altri usi.
- `extract_and_send.sh`: nuova variabile **`SKIP_SNAPSHOT`** (default **`auto`**): se `run_date` è diversa dalla data
  di oggi su odi3 passa `--skip-snapshot`; `1` = esclude sempre, `0` = include sempre (solo consapevolmente).
  La scelta compare nel log e nel recap.
- Il confronto usa l'orologio di odi3 (UTC), lo stesso con cui si calcola il `run_date` di default: il giro
  schedulato (default = oggi) include sempre gli snapshot.
- Fuori ambito: le tabelle `full` (anagrafiche) rilanciate con data passata portano lo stato di oggi; per le
  dimensioni il danno è minimo e non sono state escluse.

## Deploy su odi3
Ricopiare `extract_and_send.sh` (`/opt/landing/bin/`) e `extract_oracle_to_landing.py`
(`/opt/landing/app/scripts/landing_simulator/`); `config.yaml` invariato.

## Esito (2026-10-14) — IN FUNZIONE SU ODI3
- **Deploy** il 14/10: copiati `extract_and_send.sh` (9090 byte) e `extract_oracle_to_landing.py` (31223 byte), backup
  `.bak2`; `grep -c skip-snapshot` = 2 su entrambi.
- **Prova `DRYRUN=1` con `run_date=2026-10-05`**: `tabelle snapshot (catena, catena_esterni): ESCLUSE (SKIP_SNAPSHOT=auto,
  run_date 2026-10-05, oggi 2026-10-14)` e `catena/catena_esterni -> SKIP (snapshot, --skip-snapshot)` su ogni sito.
- **Job ODI schedulato**: dal recap di odi3 ha girato ogni mattina il 12, 13 e 14/10 alle 04:07 UTC (06:07 ora italiana).
  Fino al 14/10 con la versione precedente (stesso risultato sui giri del giorno); dal 15/10 il recap riporterà anche
  `snapshot : incluse`.

## Prossimi passi
1. Verificare nel recap del giro del 15/10 la riga `snapshot : incluse`.
2. Decidere se cancellare dal container le `catena*/2026/10/02` (fotografia dell'11/10 con data sbagliata).
