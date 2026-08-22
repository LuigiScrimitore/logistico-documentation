# ADR-0018 · Perimetro decisionale di Reply: solo anagrafiche/setup/standard, NON i flussi

**Status**: accepted (2026-07-05)

**Contesto**:
Nel progetto interviene **Reply** (team Data Platform) come partner di piattaforma. Durante gli sviluppi
è ricorsa l'ambiguità su *quali decisioni* richiedano il coinvolgimento di Reply e quali siano interne
al team Logistico. Trattare ogni scelta come "da confermare con Reply" rallenta e sposta responsabilità;
al contrario, decidere internamente su temi di piattaforma condivisa creerebbe disallineamenti di
governance. Serve una regola chiara per classificare le decisioni.

**Alternative considerate**:
1. **Tutto passa da Reply** — massima cautela, ma colli di bottiglia e diluizione della ownership sui
   flussi (che sono dominio del team Logistico).
2. **Confine esplicito**: Reply su ciò che è **condiviso/piattaforma**; il team decide sui **flussi**.

**Decisione**:
Reply è coinvolta **solo** su: **anagrafiche/master data** (es. lookup Retail, OP-02), **setup di
piattaforma** (workspace, catalog condivisi, runner/CI) e **standard condivisi** (naming standard,
governance UC/tag). Le decisioni su **flussi e modellazione** (grana dei fact, scope tabelle, quali
sorgenti importare, pipeline) sono **interne al team**: proponiamo, l'owner di progetto conferma. Non
usare "confermare con Reply" come default per scelte di scope/modellazione (es. scope MTV trasporti
ADR-0013 = decisione interna).

**Conseguenze**:
+ Ownership chiara: il team decide e avanza sui flussi; Reply interviene dove serve davvero.
+ Meno attriti/attese; classificazione rapida di ogni nuova decisione (flusso → team; piattaforma → Reply).
− Richiede disciplina nel classificare correttamente (una decisione "di flusso" che tocca uno standard
  condiviso va comunque allineata con Reply).

**Riferimenti**:
- Memory `reply-scope-governance`. Contesto governance: `12_checklist_infra_setup.md` (interlocuzioni Reply/Ippazio), `05_open_points.md` (OP-02).
- Collegate: ADR-0002 (master/OP-02), ADR-0013 (scope trasporti come decisione interna).
