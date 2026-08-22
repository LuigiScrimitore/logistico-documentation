# ADR-0011 · Late-Arriving Dimensions: ri-risoluzione generica via `<dim>_COD_NAT`

**Status**: accepted (2026-06-20, esteso 2026-07-05)

**Contesto**:
Con le chiavi naturali + fallback `-1` (ADR-0008), quando un'anagrafica arriva **dopo** il fatto che la
referenzia, la riga di fatto resta agganciata al sentinel `-1` e **non si auto-corregge**. Le dimensioni
ad alta frequenza (ARTICOLI, FORNITORI) nascono ogni giorno insieme agli eventi supply chain → orphan
giornaliero ricorrente. Ostacolo tecnico: `surrogate_key_fallback` sovrascrive la FK con il valore
risolto o `-1`, **perdendo il codice naturale originale** → impossibile ri-risolvere chirurgicamente in
un secondo momento.

**Alternative considerate**:
1. **Reprocess completo** del fact quando arriva la dimensione — semplice ma costoso e non mirato.
2. **Preservare il codice naturale** in colonna dedicata `<dim>_COD_NAT` accanto alla FK, e un **job LAD
   generico** che ri-risolve solo le righe `FK=-1 AND NAT NOT NULL` via join sulla dim aggiornata.

**Decisione**:
1. Ogni fact espone `<dim>_COD_NAT` (prerequisito **L-01**) — codice naturale scritto **prima** del
   `surrogate_key_fallback`. Verificato su 5 fact core (F_CARICO, F_PREP_SPED, F_TURNO_PREP_SITO,
   F_TRASPORTO, F_ORDINI).
2. Job **`gold_lad_resolver`** generico, config-driven (parametrico su fact/fk/dim/nat_key), idempotente,
   schedulato **dopo** il refresh dimensioni. Estensione 2026-07-05: **retention/quarantena** (widget
   `retention_days`) — i residui con NAT valorizzato ma assenti dal master sono candidati quarantena;
   skip corretto degli `-1` con NAT null (assenza by-design, es. CORRIERE su F_CARICO).

**Conseguenze**:
+ Correzione **chirurgica** (solo le righe orfane) senza reprocess completo; idempotente.
+ Framework generico riutilizzabile per ogni fact con `_COD_NAT`.
− La risoluzione ART/FORNITORE dipende dalla completezza del **Retail Master** → residuo **gated su
  OP-02**; finché il master è parziale, quei residui restano candidati quarantena (fisiologico).
− Le fact senza `_COD_NAT` (giacenze/tracciabilità/movimentazione: solo dim strutturali) sono fuori
  scope LAD → reprocess occasionale.

**Riferimenti**:
- Sezione LAD: `05_open_points.md` (OP-32). Memory `op32-late-arriving-dimensions`.
- Codice: `notebooks/gold/maintenance/gold_lad_resolver.py`. Backlog L-01/L-02.
- Collegate: ADR-0002 (master), ADR-0008 (chiavi naturali).
