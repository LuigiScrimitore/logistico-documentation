---
data: 2026-11-05
titolo: "Prep carichi v3.5.0: cambio mese gestito in automatico (ACT_9040) — workflows v0.1.23"
autore: Francesco Foconi
push_monorepo: "main @14b4307 (PR #48)"
push_github: "workflows 08228f9, documentation ef0d895 (lib e infrastructure invariati)"
push_gitlab: "workflows v0.1.23 d5ac691 — solo main, nessun tag (LL-031)"
act: [ACT_9040]
adr: []
lesson: []
op: []
---

## Fatto
- `silver_prep_carico` v3.5.0: oltre al mese della `run_date` rielabora i mesi con testate timbrate negli ultimi
  `giorni_rielaborazione` giorni (default 5). Chiude il punto aperto "cambio mese" del worklog 2026-11-05-01.
- Dati dev da settembre: timbro quasi sempre il giorno dopo la data carico (max 6 giorni); ~3.000 testate su 124.000
  timbrate nel mese successivo.
- Prova su dev con `run_date=2026-11-05` su tabella di prova (poi eliminata): ottobre + novembre, 0 differenze riga per
  riga con `logistica_curated.carico`.
- Rilascio: PR #48 → GitHub → GitLab workflows v0.1.23. Deploy dev verificato: `metadata.json` riporta d5ac691, notebook
  v3.5.0, schedulazione carichi attiva.

## Stato dopo il push / prossimi passi
- Dal giro del 06/11 il prep rielabora anche ottobre fino a ~09/11 (testate di ottobre timbrate nei 5 giorni), poi solo
  novembre. Al 01/12 controllare nel log del task `mesi elaborati: ['202611', '202612']`.
- Nessuna rielaborazione a mano ai cambi mese.
