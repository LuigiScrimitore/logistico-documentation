---
data: 2026-10-23
titolo: "Recupero residuo ~2% copertura F_CARICO: riconciliazione (bolla,ordine) pesata→dettaglio, copertura ~100% (ACT_9035)"
autore: Francesco Foconi
push_monorepo: "main @b329553"
push_github: "workflows @6143c71, documentation"
push_gitlab: "workflows v0.1.20 (push solo main, no tag - LL-031); deploy_dev success"
act: [ACT_9035]
adr: []
lesson: []
op: [Q-01]
---

## Fatto
- Chiuso il residuo ~2% di copertura F_CARICO lasciato aperto da [[ACT_9033]]. Causa: ~2.229 pesate con
  `(BOLLA_NRO, COMMESSA_NRO)` non combacianti col dettaglio pur avendo l'MSI nello stesso carico →
  scartate dall'inner join `p⋈r`.
- Fix `silver_prep_carico.py` v2.2.0: **riconciliazione (bolla, ordine) della pesata PRIMA della join**,
  adottando i valori del dettaglio **solo se la chiave rilassata è univoca** (1° `(sito,carico,ordine,msi)`,
  2° `(sito,carico,msi)`). Join e codice a valle invariati. Solo notebook (no wheel).
- Diagnosi + validazione sul dato (warehouse): dei 2.229, **782** recuperabili per ordine-univoco e **1.447**
  per msi-univoco, **0 ambigui/0 orfani** → recupero completo senza fan-out.

## Esito (verificato end-to-end)
- Release monorepo → GitHub → GitLab workflows v0.1.20 → `deploy_dev` success; re-run `logistica_carichi`
  (202610) SUCCESS.
- **Copertura vs CDT_DW: ~98% → ~100%** (13–16/10 tutti 100,0%; 15/10 esatto 28.191/28.191).
- Gold 13–16 = **113.020 righe = 113.020 etichette** → **0 fan-out**. Misure chiave quadrano; unico scarto
  = **4 etichette duplicate nell'ODI legacy** (non un errore gold).

## Indicazioni al team
- Da oggi la copertura F_CARICO è ~100% (il residuo noto del 2% è chiuso). La riconciliazione è sicura
  (adotta i valori del dettaglio solo quando univoci; gli ambigui — oggi 0 — restano esclusi).
- Scoperto: l'**ODI legacy** ha 4 etichette duplicate (13–16/10) — il nostro gold le deduplica. Segnalazione
  minore, non bloccante.
- Follow-up: rigenerare le tabelle pubblicate `quadratura_f_carico_*` al prossimo run quadratura; resta
  aperta la fix testata multi-ordine per le date/`GG_*` per-ordine ([[ACT_9033]], `STCAR_NRO_ORDINE` nella
  chiave landing) e i punti costo/allocazione (OP-CAR-1/OP-CAR-3).
