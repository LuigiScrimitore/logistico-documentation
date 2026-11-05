---
data: 2026-11-05
titolo: "Giro M2 di DataRelay + fix fotografia dopo il giro (prep v3.4.0): F_CARICO = CDT_DW dal 01/09 al 03/11 — workflows v0.1.22"
autore: Francesco Foconi
push_monorepo: "main @a394cbb (PR #46)"
push_github: "workflows 86e96c3, documentation ca9d7ad (lib e infrastructure invariati)"
push_gitlab: "workflows v0.1.22 aa0bfcf — solo main, nessun tag (LL-031)"
act: [ACT_9038]
adr: []
lesson: [LL-041]
op: [Q-01]
---

## Fatto
- **DataRelay, giro del 05/11** (report `Extractor_Relay/docs/report/REPORT_giro_2026-11-05_M2.md`):
  - nessuna deduplica su `pesate`, `sto_righe_carico` e `sto_tes_carichi`, con 0 righe scartate su 19 siti;
  - finestra dei timbri a 6 giorni solo per questo giro, tornata a 2 alle 07:44 del 05/11;
  - M2 resta attivo.
- **Giro schedulato del 05/11** con il codice v0.1.21: landing, dimensioni e carichi verdi.
- **Quadratura 29/10–03/11 vs CDT_DW**:
  - 31/10–03/11 al 100%;
  - mancavano 665 righe su carichi timbrati il 31/10. La fotografia "dopo il giro" era D+1, ma dal 31/10 al 04/11 il
    bronze non ha fotografie, quindi le righe definitive viste il 05/11 restavano fuori.
- **Correzione**: `silver_prep_carico` v3.4.0 usa come fotografia dopo il giro il primo giorno di landing caricato dopo
  D. Prima della prima landing resta D+1. ACT_9038 e spec R-2.3 aggiornate prima del codice.
- **Ricalcolo** prep ott/nov + gold e **confronto 01/09–03/11 vs CDT_DW**: righe e misure identiche. Unica differenza:
  54 etichette rinumerate dopo il giro legacy, con stessa data/sito/documento/bolla/UF (42 set, 10 ott, 2 nov).
- Rilascio: PR #46 → GitHub → GitLab workflows v0.1.22. Deploy dev verificato: `metadata.json` riporta aa0bfcf e il
  notebook è la v3.4.0.

## Stato dopo il push / prossimi passi
- Il 04/11 si confronta domani, quando CDT_DW ha completato il carico del giorno.
- **Cambio mese**: il prep giornaliero elabora solo il mese della `run_date`. I carichi dell'ultimo giorno del mese
  timbrati il mese successivo vanno rielaborati: oggi l'ho fatto a mano per ottobre. Correzione da fare prima del 01/12.
- Aperti lato DataRelay: M3 (`L_ART_VAR_LOGIS_ST` giornaliera, poi il bronze lato nostro), M7 (certificazione riga per
  riga). Lato nostro: migrazione delle colonne ADR-0029 in dev (SQL dell'utente).
