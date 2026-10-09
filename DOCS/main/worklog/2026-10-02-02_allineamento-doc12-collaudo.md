---
data: 2026-10-02
titolo: Checklist infra 12 allineata a provisioning consegnato + collaudo relay OK
autore: Luigi Scrimitore
push_monorepo: aa6231b
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_OP-INF-4]
adr: []
lesson: []
op: [OP-INF-4]
---

## Cosa e' stato fatto
- Allineato il doc **collegato** `12_checklist_infra_setup.md` (era ancora a "provisioning in corso") agli esiti reali:
  - **C5** → collaudo relay OK; **C6** → oggetti UC consegnati (Storage Credential `logisticolanding_dev_ro` +
    External Location `logisticolanding_dev`, Access Connector `ac-dev-logistico-00`), resta solo il flip `landing_mode`
    dopo la migrazione storico.
  - **Stato-mail #3** e **§F.2** → thread AzCopy **CHIUSO** (consegnato 2026-10-01 + collaudo 2026-10-02).
  - Header e tabella "chi fa cosa" aggiornati; rimando a [[ACT_OP-INF-4]].

## Novita'
- Nessuna nuova decisione: è un allineamento documentale degli esiti già prodotti (collaudo, worklog 2026-10-02-01).
- Il SAS resta fuori dal repo (gitignored).

## Doc aggiornati
- `12_checklist_infra_setup.md` (C5/C6, stato-mail, §F.2, header, tabella finale).

## Stato dopo il push / prossimi passi
- Documentazione infra coerente con lo stato reale (trasporto landing validato end-to-end dal relay). Prossimi:
  **trigger E2E da ODI**, **migrazione storico Volume→logisticolanding** + external Volume stesso nome → flip
  `landing_mode=external`, industrializzazione estrazione ODI.
