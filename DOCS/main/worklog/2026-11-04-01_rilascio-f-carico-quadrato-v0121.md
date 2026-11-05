---
data: 2026-11-04
titolo: "Rilascio F_CARICO quadrato col legacy (ACT_9037/9038/9039): workflows v0.1.21, lib v1.0.9 — recupero 31/10–04/11 rinviato al fix DataRelay"
autore: Francesco Foconi
push_monorepo: "main @b39a07f (PR #45)"
push_github: "lib 141cd75, workflows d4006ba, documentation 340658c (infrastructure invariato)"
push_gitlab: "workflows v0.1.21 63bcff1, lib v1.0.9 b00a8e5 — solo main, nessun tag (LL-031)"
act: [ACT_9037, ACT_9038, ACT_9039]
adr: [ADR-0029]
lesson: [LL-041]
op: [Q-01]
---

## Fatto
- PR #45 unita senza attendere revisioni esterne (indicazione dell'utente: il ramo del team è il riferimento).
  Contenuto:
  - bronze carichi con chiave completa e prima/ultima vista;
  - `silver_prep_carico` v3.3.0, cioè stato al giro legacy, ERRART limitato alla data della copia della tabella varianti
    e doppi;
  - via `QTA_ORD_FORN` / `VAL_COSTO_CARICO` (ADR-0029);
  - notebook di recupero ACT_9038.
- Split → GitHub → GitLab (solo `main`).
- `deploy_dev` verificato: il `metadata.json` del bundle riporta 63bcff1; il notebook rilasciato è la v3.3.0.
- Wheel `logistica_utils` ricostruito da `lib/` di main e ricaricato sul Volume. La copia precedente è in
  `_wheels/backup/`.

## Stato trovato prima del rilascio
Dal 31/10 al 04/11 il job `logistica_carichi` è fallito ogni mattina sui 3 task bronze dei carichi, con
`DELTA_MERGE_UNRESOLVED_EXPRESSION … _first_seen_date`: il codice vecchio girava sul bronze ricaricato. Nessuna scrittura,
quindi bronze, silver e gold sono rimasti allo stato quadrato del 30/10. Gli altri 6 job sono verdi.

## Stato dopo il push / prossimi passi
- Da domani il giro schedulato usa il codice nuovo.
- **I giorni 31/10–04/11 dei carichi non sono ricaricati**, per scelta dell'utente: la landing di quei giorni ha ancora
  la deduplica di DataRelay. Si ricaricano dopo la correzione DataRelay (M2 in
  `LOGISTICO_DATA/datarelay_compare/ISTRUZIONI_DataRelay_2026-11-04.md`). Un recupero lanciato per errore è stato
  annullato prima di scrivere.
- Migrazione delle colonne ADR-0029 in dev: è SQL da eseguire a cura dell'utente (ACT_9039).
- Finestra di ripristino: il VACUUM automatico della piattaforma riduce la possibilità di tornare alle versioni pre-30/10
  (`ripristina_act9038.py`) a circa 7 giorni.
