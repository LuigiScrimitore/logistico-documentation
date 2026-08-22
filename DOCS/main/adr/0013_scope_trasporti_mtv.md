# ADR-0013 · F_TRASPORTO limitato alla grana MTV (TRATTA/BOLLA = estensione futura)

**Status**: accepted (2026-07-05)

**Contesto**:
Certificando F_TRASPORTO vs CDT_DW è emerso che in Oracle i trasporti sono una **gerarchia a più grane**,
non una tabella: `F_TRASP_MTV` (movimento automezzo/viaggio), `F_TRASP_TRATTA` (tratta/leg di una gita,
con nodi origine→dest e **costo per tratta** da `WL1_COSTO_GITA`), `F_TRASP_TRATTA_BOLLA` (bolla per
tratta). Il nostro `gold_f_trasporto` modella **solo la grana MTV**. Domanda architetturale: replicare
tutta la gerarchia o fermarsi a MTV? A differenza di F_MOVIMENTAZIONE (ADR correlata), qui la scelta è
condizionata dalla **disponibilità delle sorgenti**.

**Alternative considerate**:
1. **Modellare tutte le grane** (MTV + TRATTA + TRATTA_BOLLA) — copertura completa, ma: (a) le sorgenti
   TRATTA/BOLLA (`V_TRASP_TRATTA_CONS_PROGR/TRANSITO`, `WL1_COSTO_GITA`, nodi) **non sono nel nostro
   landing** → servirebbero nuove estrazioni; (b) il valore primario di TRATTA è il **costo trasporto**,
   che è **già fuori scope** (listini corrieri assenti — vedi milestone fase_5).
2. **Solo grana MTV** — copre l'analitica movimento-automezzo (fabbisogno logistico core) ed è completa
   rispetto a ciò che estraiamo (`T_TRASP_MTV`).

**Decisione**:
F_TRASPORTO **certificato a grana MTV**. TRATTA/TRATTA_BOLLA rinviate a **estensione futura**, da fare
quando (a) si importeranno le sorgenti tratta e (b) saranno disponibili i listini corrieri per i costi.
Decisione **interna al flusso** (non Reply — vedi ADR-0018). Diversamente da F_CARICO/F_PREP_SPED (dove
la semplificazione era *accidentale* vs sorgenti disponibili), qui è **deliberata e coerente** con lo
scope sorgenti/costi.

**Conseguenze**:
+ Nessun lavoro sprecato su grane non alimentabili; scope chiaro e difendibile.
+ Metodo di certificazione validato: distinguere "sovra-semplificazione accidentale" (→ riscrivere) da
  "scope deliberato" (→ confermare).
− Le analisi di **costo/tratta** (leg, nodi origine-dest) non sono disponibili finché non si aggiungono
  sorgenti + listini (tracciato come estensione futura).

**Riferimenti**:
- Sezione trasporti: `07_certifica_gold_vs_cdtdw.md` §1.3 (F_TRASPORTO, decode A0-A2). Milestone `fase_5.md` (listini corrieri).
- Codice: `notebooks/gold/trasporti/gold_f_trasporto.py`, `silver.logistica_curated.trasporto`.
- Memory `certifica-gold-vs-cdtdw-stato`. Collegate: ADR-0018 (Reply scope).
