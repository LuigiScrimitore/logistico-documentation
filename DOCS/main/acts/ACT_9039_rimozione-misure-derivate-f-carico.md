# ACT_9039 · Rimuovere `QTA_ORD_FORN` e `VAL_COSTO_CARICO` da F_CARICO e dai derivati

**Status**: rilasciato (2026-11-04 con ACT_9038: workflows v0.1.21, lib v1.0.9); resta la migrazione delle colonne in dev (SQL ADR-0029, la esegue l'utente)
**Type**: change (modello)
**Origin**: decisione SAL 2026-10-29/30 → [[ADR-0029]]
**Fase / Wave**: FASE 2 — Wave A Carichi + aggregati
**Gg (stima)**: ~0,5 gg (codice + migrazione dev)
**Created**: 2026-10-30   **Closed**: —   **Owner**: team (aggregati/KPI: review di Luigi)
**OP collegati**: OP-CAR-1, OP-CAR-3 (superati), OP-CAR-8 (nuovo)

## Contesto e motivazione
Il cliente al SAL: `QTA_ORD_FORN` e `VAL_COSTO_CARICO` non sono misure del carico, verranno derivate da altri fatti.
Vanno tolte dal fatto e da ciò che ne dipende. Restringe anche il perimetro della quadratura con il legacy
([[ACT_9038]]) alle misure del carico.

## Obiettivo ("fatto" =)
- `silver_prep_carico` e gold `F_CARICO` senza le due colonne; `NUM_PZ_IMB_ORD_FORN` resta.
- `A_INBOUND_MENSILE` senza `QTA_ORDINATA_TOT`, `AMMANCO_QTA_TOT`, `TASSO_AMMANCO`.
- `sql/kpi/gold_kpi_qualita_ricevimento.sql` sospeso (non più creabile senza ordinato).
- Gate DQ (`acceptance.py`) e quadratura (notebook + `scripts/quadratura/compare_f_carico.py`) senza le due misure.
- Migrazione dev: riscrittura con `overwriteSchema` di `logistica_curated.carico`, gold `F_CARICO`, `A_INBOUND_MENSILE`;
  wheel `logistica_utils` ricaricato sul Volume.
- Job `carichi` e `aggregati` verdi dopo il deploy.

## Analisi tecnica
Consumatori trovati (grep `QTA_ORD_FORN|VAL_COSTO_CARICO|QTA_ORDINATA_TOT|AMMANCO`): `silver_prep_carico.py`,
`gold_a_inbound_mensile.py`, `lib/logistica_utils/acceptance.py` (F_CARICO e A_INBOUND), `quadratura_f_carico_misure.py`,
`scripts/quadratura/compare_f_carico.py`, `sql/kpi/gold_kpi_qualita_ricevimento.sql`. Il KPI SQL non è collegato a job.
Scritture gold con `mergeSchema`/`replaceWhere`: senza migrazione le colonne resterebbero in tabella, vuote.

## Sviluppo (diario)
- 2026-10-30 · ADR-0029 scritta, OP-CAR-1/3 superati, OP-CAR-8 aperto, ADR-0012 superseded. Codice su branch dedicato
  (sopra `fix/act-9037-bolla-pesata`, perché tocca lo stesso `silver_prep_carico`); PR #45 in bozza, review di Luigi per
  aggregati/KPI, da unire con ACT_9038. Nessun consumatore di gold da avvisare (progetto in sviluppo).

## Verifica
Compilazione notebook; run ad-hoc dev di prep → gold → aggregato → quadratura; nessun riferimento residuo alle colonne
(grep); gate DQ verde.

## Esito
— (da compilare)
