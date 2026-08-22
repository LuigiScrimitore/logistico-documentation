# ACT_2.4.3 · Validazione funzionale con BA (3 mesi vs Oracle)

**Status**: on-hold
**Type**: analysis
**Origin**: sprint 2.4
**Sprint**: 2.4
**Fase / Wave**: FASE 2 — Wave A: Carichi (Inbound)
**Gg (stima)**: 2
**Blocco**: ☁️ cloud/PROD + presenza BA — non avviabile offline
**Created**: 2026-07-05   **Closed**: —   **Owner**: —
**Dipende da**: ACT_2.3.4 (quadratura Gold vs Oracle), ACT_2.4.1, ACT_2.4.2   **Blocca**: chiusura Wave A
**ADR collegate**: —   **OP collegati**: —

## Contesto e motivazione
La certificazione funzionale dell'area Carichi richiede una validazione con i Business Analyst su un periodo di 3 mesi, confrontando output Gold/KPI vs Oracle. È il gate di chiusura Wave A. Non avviabile offline: servono PROD (storico caricato via [[ACT_2.1.6]]) e la presenza dei BA. Complementa la quadratura tecnica ([[ACT_2.3.4]]) con l'occhio di business sui KPI.

## Obiettivo
Validazione funzionale firmata dai BA su 3 mesi di dati, con esiti Gold/KPI allineati a Oracle. Fatto = sign-off BA registrato.

## Analisi tecnica
- **Oggetto del confronto**:
  - Fact `gold_prod.logistica.F_CARICO` (grain etichetta, [[ADR-0006]]) vs `CDT_DW.F_CARICO`.
  - Viste KPI Carichi (sprint 2.4.1/2.4.2, file in `sql/kpi/`):
    - `gold_kpi_lead_time_fornitore.sql` → vista `kpi_volumi_inbound_fornitore` (AVG/P90 lead time; NB v4.0: sorgente `A_INBOUND_MENSILE`, lead time puntuale non disponibile — OP-27; espone volumi qta/peso/volume/pallet).
    - `gold_kpi_qualita_ricevimento.sql` → vista `kpi_qualita_ricevimento` (% conformi, **ammanco** = qta ordinata − ricevuta, calcolo aggregato riabilitato post OP-CAR-3).
  - Entrambe le viste leggono l'aggregato `gold_prod.logistica_dm.A_INBOUND_MENSILE` (grain `FORNITORE_COD + SITO_COD + ANNO_MESE`), non F_CARICO per-riga (il grain etichetta non consente il per-riga).
- **Finestra**: 3 mesi; confronto per `(SITO, FORNITORE, ANNO_MESE)`. Riusare `quadratura_fact.py --fact CARICO --per-mese` come base numerica ([[ACT_2.3.4]]) e affiancare l'analisi KPI di business.
- **Dipendenze**: quadratura tecnica verde ([[ACT_2.3.4]]) e storico 3 mesi caricato ([[ACT_2.1.6]]); ambiente PROD; sessione congiunta con i BA (governance flussi interna al team — memory `reply-scope-governance`).
- **Note su misure disponibili**: `VAL_COSTO_CARICO` fuori scope (sorgente dismessa, fase_2 §8); alcune misure di scarto/qta-ordinata dipendono da OP-CAR-3.

## Sviluppo (diario)
- 2026-07-03 · attività pendente; non avviabile offline (PROD + BA).

## Verifica
- Sign-off dei BA sulla validazione 3 mesi.
- Scostamenti Gold/KPI vs Oracle entro tolleranza concordata su volumi inbound e qualità ricevimento per `(SITO, FORNITORE, mese)`.
- Esito e firma registrati (chiusura Wave A).

## Esito
— (in attesa di PROD e disponibilità BA)

## Follow-up
Nessuna al momento.
