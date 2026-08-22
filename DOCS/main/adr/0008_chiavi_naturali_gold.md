# ADR-0008 · Gold usa chiavi naturali validate (surrogati rimandati)

**Status**: accepted (2026-06)

**Contesto**:
Nel modello a stella le fact referenziano le dimensioni. Scelta classica: **surrogate key** (ID interi
generati) come FK. Ma nel nostro contesto le master (`LU_*`) arrivano dal Retail e non sono ancora
stabilizzate (OP-02, vedi ADR-0002); generare surrogati ora significherebbe gestire mapping e
rigenerazioni fragili mentre le master cambiano. Inoltre il legacy CDT_DW ragiona su **codici naturali**
(`FORNITORE_COD`, `ART_RADICE_COD`, `SITO_COD`…), utili per la quadratura diretta per nome.

**Alternative considerate**:
1. **Surrogate key intere** subito — standard dimensionale, join veloci, ma richiede generazione/mapping
   stabile delle dimensioni (non c'è finché OP-02 è aperto) e complica la quadratura vs CDT_DW.
2. **Chiavi naturali validate** — le fact portano i **codici naturali** già normalizzati; l'aggancio
   dimensione è un `left join` con **fallback a sentinel `-1`** (riga SCONOSCIUTO) + `check_orphan_rate`.
   I surrogati si introdurranno in futuro quando le master saranno stabili.

**Decisione**:
Gold usa **chiavi naturali validate** ora; surrogati rinviati. L'aggancio è `surrogate_key_fallback`
(risolve o `-1`) + DQ orphan-rate. Le fact espongono **anche** `<dim>_COD_NAT` (codice naturale
preservato) per abilitare la ri-risoluzione late-arriving (ADR-0011). Caso cablato: `RICEVITORE_COD`
agganciato a `LU_OPERATORE`.

**Conseguenze**:
+ Quadratura diretta per nome vs CDT_DW; nessuna dipendenza da un generatore di surrogati stabile.
+ Robustezza: una master mancante non rompe la fact (va a `-1`), il LAD la recupera dopo.
− Join su stringhe (meno efficienti dei join interi) — accettabile ai volumi attuali; da rivalutare a scala.
− Introduzione futura dei surrogati sarà un cambiamento (nuova ADR che supersede questa).

**Riferimenti**:
- Sezione modello a stella/chiavi: `01_architettura.md`. Memory `gold-natural-key-vs-surrogate`.
- Codice: `lib/logistica_utils/utils.py` (`surrogate_key_fallback`), `dq_helper.check_orphan_rate`.
- Collegate: ADR-0002 (master condivise), ADR-0011 (LAD via `_COD_NAT`).
