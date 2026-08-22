# ACT_8.3.3 · Comunicazione utenti finali (finestra < 2h)

**Status**: in-progress
**Type**: doc
**Origin**: sprint 8.3
**Sprint**: 8.3 — Preparazione Cut-Over
**Fase / Wave**: FASE 8 — Shadow Mode, Validazione & Cut-Over
**Gg (stima)**: 1
**Blocco**: ☁️ invio dipende dalla data cut-over confermata
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_8.3.2   **Blocca**: ACT_8.4.1
**ADR collegate**: [[0017_rilascio_a_fasi]]   **OP collegati**: —

## Contesto e motivazione
Il cut-over comporta una finestra di indisponibilità (**< 2h** lato utente; finestra tecnica 22:00–02:00)
per la reportistica MicroStrategy. Va comunicata per tempo con contenuti chiari su finestra, impatti e
contatti. È il pre-requisito #5 del `piani/cutover_plan.md` ("Finestra comunicata agli utenti > 7 giorni di
anticipo") e #6 (comunicazione ai sistemi dipendenti AtTraspo/Logistix).

## Obiettivo
Comunicazione utenti finali pronta e pianificata. Fatto = messaggio approvato con finestra, impatti e
riferimenti, pronto per l'invio in prossimità del cut-over secondo lo scadenzario del piano.

## Analisi tecnica
- **Template già pronto** (PARZ. 50%) — allineare la finestra al Cut-Over Plan (ACT_8.3.2).
- **Messaggi previsti** (testi base nel `piani/cutover_plan.md`):
  - **T-7gg — utenti MicroStrategy** (§3, PM Progetto): oggetto "AGGIORNAMENTO SISTEMA — Sabato [DATA]
    notte: breve interruzione report"; corpo con finestra 22:00→02:00, ripristino con prestazioni
    migliorate, contatto PM.
  - **T-7gg — sistemi dipendenti**: comunicazione a **team AtTraspo** (nessuna estrazione trasporti sabato
    notte) e **team Logistix** (nessuna manutenzione programmata).
  - **T=01:00 — go-live** (§3, PM): oggetto "SISTEMA OPERATIVO — Report disponibili".
  - **In caso di rollback** (rollback_plan §6, PM+BA): "RIPRISTINO SISTEMA — Accesso report ora
    disponibile" + messaggio ai referenti business per area (Carichi, Giacenze, Prep Spedizioni, Trasporti).
- **Canali**: email lista utenti MicroStrategy; per l'emergenza gruppo WhatsApp "LOGISTICO 2.0 —
  EMERGENZA" e Teams "CutOver Night".
- **Da definire**: data specifica, lista destinatari, nome/contatto PM (placeholder nel template).

## Sviluppo (diario)
- 2026-07-03 · template comunicazione pronto (PARZ. 50%).

## Verifica
- Testo approvato (PM + BA); canali e tempistiche di invio definiti in coerenza con la data cut-over
  (T-7gg per il preavviso, T=01:00 per il go-live).

## Esito
— (parziale: template pronto)

## Follow-up
Confermata la data finestra: compilare destinatari/contatti e programmare l'invio T-7gg.
