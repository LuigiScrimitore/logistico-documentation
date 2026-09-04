---
id: LL-024
titolo: Il filtro CDC dell'ODI non è adatto al seed storico — rendilo opt-in, non cablato nel config
sintomi:
  - "seed landing DEV vuoto/parziale sulle transazionali nonostante la finestra data contenga record"
  - "0 righe estratte per una tabella delta ma in Oracle i dati ci sono"
  - "pesate/carichi storici assenti in landing per date già consumate dall'ODI di produzione"
tag: [landing, extractor, cdc, odi, oracle, seed]
stadio: regola-documentata
automatizzabile: false
autore: Francesco Foconi
data: 2026-09-02
origine: [ACT_9020]
---

## Sintomo
L'extractor Oracle→CSV restituisce 0 (o poche) righe per le transazionali su una finestra storica, anche se
in Oracle i record esistono. Il seed della landing DEV risulta svuotato proprio dove serve la storia.

## Strada sbagliata
Applicare **sempre** il filtro CDC dell'ODI legacy (`NVL(<tab>_DATA_ESTRAZIONE_DWH, 0) = 0`) alle tabelle
delta, cablandolo nel `config.yaml`. In produzione quel flag marca i record **già estratti dall'ODI**: su una
finestra storica lascia passare quasi nulla. Aggirarlo commentando a mano `flag_column` nel config è fragile
(va ricordato di ripristinarlo, e cambia un file tracciato).

## Regola
Rendere il filtro CDC **opt-out esplicito** via flag CLI, senza toccare il config:
```bash
py -3.12 extract_oracle_to_landing.py --ignore-odi-flag --from-date 2026-08-31 --to-date 2026-09-02
```
Default OFF (nessuna regressione per la CI a regime); con `--ignore-odi-flag` resta solo la **finestra data**
come filtro. Attenzione alle tabelle senza `date_column` (es. `imbfmovim`): ignorando il flag restano senza
filtro → lettura totale (il cap `--max-rows` fa da rete). Vedi [[LL-022]] (il seed storico attiva anche il bug JDN).

## Perché
Il flag `*_DATA_ESTRAZIONE_DWH` è un meccanismo di **CDC per consumo** (l'ODI lo valorizza quando estrae), non
un marcatore di validità del dato. Per una fotografia storica serve leggere per **competenza temporale**
(finestra data), non per stato di consumo. Cablare il CDC nel config confonde i due scopi.

## Conferme e contraddizioni
- 2026-09-02 · Francesco Foconi · `lgcx/pesate` 01-07 ago: con flag 0 righe, `--ignore-odi-flag` 1065 righe.
  Seed logistix+stat dal 31/08: 3,65M righe (vs 1,19M col flag).
