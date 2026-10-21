---
data: 2026-10-21
titolo: "F_CARICO: aggiunti i diagnostici GG_* al gold (ACT_9031); rinomina vettore + flag scarti + scad stock tracciati come da decidere"
autore: Francesco Foconi
push_monorepo: "diretto su main (doc + notebook gold additivo)"
push_documentation: "split dopo"
push_gitlab: "no (nessuna modifica lib/workflows)"
act: [ACT_9031, ACT_9029]
adr: []
lesson: []
op: [Q-01]
---

## Contesto
Revisione della mappa colonne F_CARICO (foglio `Quadratura_F_CARICO` 05/10) vs codice live: emergono 4 azioni.
Le altre voci del foglio sono già live (chiavi, misure, STESSO_IMB, DATA_SCAD da pesata, radice/variante) o
già correttamente escluse (surrogate `*_ID`, storicizzate, `GG_DIFF_*`, `AFFID_*`, `DATI_STO`=costante 0).

## Fatto
- **GG_\* (4)** aggiunti al gold: `notebooks/gold/carichi/gold_f_carico.py` v4.1.0, FASE 3c (`datediff`).
  Additivo (mergeSchema), nessun impatto sui gate. Formule da [[ACT_9029]] (confermate 100% sui dati gg22):
  VITA_RESID=SCAD−CARICO, PREV_CONS=PREV_CONS−EMIS, EFF_CONS=CARICO−EMIS, RITARDO=CARICO−PREV_CONS.
- ACT_9031 creata (SSOT) + riga backlog.

## Da decidere / da fare (tracciato in [[ACT_9031]])
- **Rinomina `CORRIERE_COD`→`VETTORE_COD`**: impatto cross-cutting **17 file** (silver+gold, `gold_lad_resolver`
  via `CORRIERE_COD_NAT`, lib, 4 KPI, `LU_CORRIERE`) → **go/no-go di team**, non fatto alla cieca.
- **CARICO_INCOMPLETO_FLAG**: dagli scarti (`E_CARICO`) → dal nostro DQ, non da F_CARICO. Da disegnare.
- **GIORNO_SCAD_STOCK_ID**: serve la sorgente stock (CND) nel flusso carichi. Da disegnare.

## Esito validazione (2026-10-21)
Smoke test in **sandbox personale** (deploy `-t dev` in home, poi `bundle destroy`): run `gold_f_carico` su
serverless = **SUCCESS**; i 4 GG_ popolati 100% in `gold_dev.logistica.f_carico`; **confronto per chiave vs
CDT_DW (22/09) = 100% match** su tutte e 4 (3.669 chiavi comuni). Sandbox distrutta (0 residui). I GG_ sono
pronti per il dev condiviso al prossimo giro CI.

## Indicazioni al team
- `gold_f_carico` ora espone 4 colonne GG_* in più (additive): al prossimo run verranno popolate; nessuna
  colonna esistente cambia.
- Le 3 azioni restanti sono **ferme in attesa di decisione/sorgenti** (vedi ACT_9031) — in particolare la
  rinomina vettore **non va fatta** finché non è decisa (tocca LAD + 17 file).
