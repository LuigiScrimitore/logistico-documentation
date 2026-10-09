---
data: 2026-10-06
titolo: "Merge PR pendenti (#14 #16 #18 #19 #20), chiusura #6 superata, pulizia branch monorepo"
autore: Francesco Foconi
push_monorepo: "merge PR #18 #16 #14 #19 #20 + chiusura #6"
push_documentation: "da ri-split dopo merge"
push_gitlab: "—"
act: [ACT_9029, ACT_9025, ACT_9026]
adr: []
lesson: [LL-033, LL-034]
op: [OP-TRA-1]
---

## Contesto
Sul monorepo si erano accumulate **6 PR aperte** (tutte di Foconi, 03/09 → 28/09) mai mergiate, più **4 branch**
già mergiati ma mai cancellati. Inventario completo (monorepo + single repo GitHub + working copy GitLab):
nessun branch solo-locale, nessun commit non pushato, nessuno stash; single repo GitHub = solo `main`.
Il remote GitLab non era raggiungibile (VPN) ma è solo target di release (main + tag).

## Cosa
- **Merge** in quest'ordine, riallineando ogni branch a `main` prima del merge:
  - **#18** — worklog esito verde fix duplicati F_CARICO ([[LL-034]]).
  - **#16** — [[LL-033]] (job DAB girano come la MI → serve grant UC alla MI) + worklog run 11→22.
  - **#14** — [[ACT_9029]] estrattore row-level `CDT_DW.F_CARICO` per quadratura (`extract_f_carico.py`,
    `compare_f_carico.py`) + worklog.
  - **#19** — worklog giro completo giorno 24 via MI (7/7 verde).
  - **#20** — disabilitati i siti spenti `laix`/`lfsx`/`lgsx` dall'estrazione (`config.yaml`, ORA-12514).
- **Conflitti**: solo sugli INDEX generati (lezioni/worklog) → **rigenerati** con `lessons_index.py` /
  `worklog_index.py`, non risolti a mano.
- **Rinumerati i worklog** che collidevano con progressivi già presenti su `main` (stesso giorno):
  `09-23-02→09-23-05` e `09-25-01→09-25-04` (#14), `09-25-01→09-25-03` (#19), `09-29-01→09-29-02` (#20,
  aggiornato anche il riferimento nel commento di `config.yaml`).
- **Chiusa senza merge la #6** ([[ACT_9025]], sito canonico **alfabetico**): superata da [[ACT_9026]] che su `main`
  ha fissato il sito canonico **numerico** (`normalize_sito` + alias map, LL-025/LL-026). Mergiarla avrebbe applicato
  in modo silenzioso la logica alfabetica su `silver_t_stock`/`silver_spedizioni_clean` (orphan sito riaperti) e
  creato un secondo LL-025. Il branch resta su origin per consultazione.
- **Pulizia branch**: cancellati i 4 branch già mergiati (PR #5 #7 #8 #9) e i 5 appena mergiati.
- Scartata la modifica locale non committata su `config.yaml`: identica al contenuto della #20.

## Prossimi passi
1. Ri-split dei single repo (soprattutto `documentation`: LL-033, worklog e ACT_9029 non ancora pubblicati).
2. A VPN accesa, verificare che sul remote GitLab non esistano branch oltre a `main`.
