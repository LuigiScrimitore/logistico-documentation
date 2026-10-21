---
data: 2026-10-21
titolo: "Rinomina CORRIERE_COD -> VETTORE_COD (requisito cliente, scope colonna+tabella): 18 file + dimensione LU_VETTORE"
autore: Francesco Foconi
push_monorepo: "diretto su main (rinomina modello gold/silver)"
push_documentation: "split dopo"
push_gitlab: "lib + workflows: al prossimo giro CI (wheel da ricompilare)"
act: [ACT_9031]
adr: [ADR-0028]
lesson: []
op: [Q-01]
---

## Contesto
Requisito **cliente non derogabile**: il concetto "corriere" nel gold deve chiamarsi **vettore** (le sorgenti
usano già vettore). Scope deciso: **colonna + tabella** (vedi [[ADR-0028]]).

## Fatto (codice)
Rinomina su **18 file** + 2 notebook rinominati:
- Colonna `CORRIERE_COD`→`VETTORE_COD` e `CORRIERE_COD_NAT`→`VETTORE_COD_NAT` in F_CARICO, F_TRASPORTO,
  F_PREP_SPED, A_OUTBOUND_MENSILE, `gold_lad_resolver`, `lib/logistica_utils`.
- Dimensione `LU_CORRIERE`→`LU_VETTORE`, silver `dim_corriere`→`dim_vettore`; file `gold_dim_vettore.py` /
  `silver_dim_vettore.py`; workflow `logistica_dim_refresh` allineato.
- 4 KPI SQL (costo_trasporto, fill_rate, resa_corrieri, optimize).
- Sorgenti intatte (`STCAR_COD_CORRIERE`, `VETTORE_SPED_COD`, `VET_CODICE`).
Verifiche: **0 residui**, sintassi tutti OK, nessun test impattato, workflow punta ai file rinominati.

## Perché NON valido in sandbox
La sandbox `-t dev` isola i **job** ma condivide i **cataloghi** (`gold_dev`/`silver_dev`): un run di rinomina
muterebbe lo schema del dev **condiviso** (CI, altri). Per un rename di schema la validazione è **codice + CI**,
non un run sandbox usa-e-getta.

## Pendente (migrazione, per ambiente)
1. Ricompilare + ricaricare il **wheel** `logistica_utils` sul Volume ([[ADR-0025]]).
2. Deploy via CI su dev → `full_refresh` (overwriteSchema) dei fatti impattati per togliere la vecchia colonna.
3. `dim_refresh` → crea `LU_VETTORE`; poi `DROP` di `LU_CORRIERE` e silver `dim_corriere`.
4. Stessa sequenza su prod al go-live.

## Indicazioni al team
- Chi referenzia `LU_CORRIERE`/`CORRIERE_COD` fuori repo (report MicroStrategy/RAC) va riallineato a
  `LU_VETTORE`/`VETTORE_COD`.
- La migrazione va fatta **una volta** per ambiente, in ordine (full_refresh → dim → drop vecchie).
