# ACT_9040 · Prep carichi: rielaborare il mese precedente al cambio mese

**Status**: rilasciato 2026-11-05 (workflows v0.1.23); attivo dal giro del 06/11
**Type**: fix (pipeline)
**Origin**: punto aperto del worklog 2026-11-05-01 (ACT_9038): ottobre rielaborato a mano il 05/11
**Fase / Wave**: FASE 2 — Wave 2 Carichi (monitoraggio fino al 20/11)
**Gg (stima)**: ~0,5 gg
**Created**: 2026-11-05   **Closed**: 2026-11-05   **Owner**: team

## Contesto e motivazione
`silver_prep_carico` riscrive solo la partizione `ANNO_MESE` della `run_date`. Il legacy elabora un carico nel giro in
cui ne timbra la testata (giorno D), di solito il giorno dopo la data carico, e la fotografia "dopo il giro" è la prima
landing successiva a D ([[ACT_9038]]). I carichi di fine mese sono timbrati e completati nel mese dopo: con la logica
attuale non entrano mai nella partizione del loro mese (stesso caso delle timbrature in ritardo).
Dati dev da settembre: ritardo timbro − data carico = 1 giorno per il 96%, massimo 6 (lacuna 31/10–04/11);
~3.000 testate su 124.000 timbrate nel mese successivo alla data carico.

## Obiettivo ("fatto" =)
- Il prep rielabora, oltre al mese della `run_date`, ogni mese che ha testate con timbro D negli ultimi N giorni
  (widget `giorni_rielaborazione`, default 5: copre la fotografia D+1 e qualche giorno di landing mancante).
- Nessuna rielaborazione manuale al 01/12; risultato del mese precedente identico a una run dedicata.
- Rilascio prima del 01/12.

## Analisi tecnica
Regola guidata dai dati, non dal calendario: una timbratura in ritardo (carico del 20/11 timbrato il 10/12) fa
rielaborare novembre il 10/12. Costo: un mese in più solo nei giorni in cui serve (in pratica i primi giorni del mese).
`legacy_parity=false` (dopo lo spegnimento del legacy): al posto del timbro si usa `_first_seen_date` della testata.
Scrittura invariata: overwrite dinamico per `ANNO_MESE`, riscrive solo i mesi elaborati.

## Sviluppo (diario)
- 2026-11-05 · ACT aperta, branch `fix/act-9040-prep-cambio-mese`. `silver_prep_carico` v3.5.0: widget
  `giorni_rielaborazione` (default 5), mesi elaborati = mese della `run_date` + mesi delle testate timbrate nella finestra.
- 2026-11-05 · Prova su dev, `run_date=2026-11-05`, scrittura su tabella di prova (poi eliminata): elaborati ottobre e
  novembre; 705.782 + 57.250 righe, **0 differenze riga per riga** con `logistica_curated.carico` (ottobre corretto a mano
  in mattinata). PR #48.

## Verifica
Run ad-hoc su dev scrivendo su una tabella di prova e confronto riga per riga (EXCEPT ALL nei due sensi) con la
partizione ottobre già corretta a mano il 05/11.

## Esito
Fatto. Dal giro del 06/11 il prep rielabora anche ottobre finché ci sono testate di ottobre timbrate negli ultimi 5 giorni
(fino al ~09/11), poi solo novembre; dal 01/12 lo stesso per novembre, senza interventi a mano. Da controllare al primo
cambio mese: nel log del task `mesi elaborati: ['202611', '202612']` nei primi giorni di dicembre.
