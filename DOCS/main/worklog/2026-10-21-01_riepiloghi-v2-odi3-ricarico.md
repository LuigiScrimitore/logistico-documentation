---
data: 2026-10-21
titolo: "Riepiloghi: estrattore v2 (stesso anno) installato su odi3 solo il 21/10 — 685 riepiloghi vecchi rientrati dal 17/10, rigenerazione 01–21/10 e ricarico"
autore: Francesco Foconi
push_monorepo: "PR solo doc"
push_documentation: "split dopo merge"
push_gitlab: "nessuno"
act: [ACT_9030]
adr: []
lesson: []
op: [OP-INF-4]
---

## Contesto
La correzione "stesso anno" dei riepiloghi (worklog 2026-10-16-05, PR #42) doveva essere copiata su odi3 prima del job
ODI del 17/10. Il 21/10 le impronte su odi3 erano quelle della prima versione (`66df4f9`): copia non fatta.
Effetti dal 17/10: **685 riepiloghi pre-2026** di nuovo in bronze, `prep_riepilogo`, `turno_prep_sito`,
`F_TURNO_PREP_SITO`; `prep_sped` del **17/10 FAILED** sul `dq_gate` (`orphan_PREPARATORE_COD`, mail di errore), 18–21/10
SUCCESS.

## Fatto
1. Utente: v2 installata su odi3 (sha256 `4d46b5de…` estrattore, `46f9ad2e…` `config.yaml` = `main`), permessi con
   `--reference`. Da qui le estrazioni giornaliere prendono solo i riepiloghi dello stesso anno.
2. Utente: rigenerati i soli `storico_riepiloghi` 01–21/10 (timbri `[D, D+1)`): 21/21 OK, 0,3–16 mila righe al giorno;
   21/10 = 0 righe (STAT non ancora timbrato oggi: nella cartella resta il file delle 06:00 estratto con la v1).

## Piano su Databricks
- `prep_sped` solo `bronze_prep_riepiloghi` + `silver_prep_riepiloghi` per ogni giorno 01–21 (crescente);
- `DELETE` delle righe pre-2026 da bronze, `prep_riepilogo`, `turno_prep_sito`, `F_TURNO_PREP_SITO`, `A_TURNO_PREP_SITO`
  (toglie anche il file v1 del 21);
- `prep_sped` sul 21/10 con `full_refresh=true` senza `bronze_prep_riepiloghi` (turni ricostruiti, preparazioni
  ricalcolate con le date dei riepiloghi, `dq_gate`);
- `datamart` solo `gold_dm_turno_prep_sito` per 01–21, `datamart` completo sul 21.

## Esito
- Fase 1 (riepiloghi 01–21/10): 21/21 SUCCESS. Pulizia: **898** righe pre-2026 in bronze e `prep_riepilogo` (685 della
  v1 + 213 dello stesso anno delle 27 bolle vecchie riemesse il 12/10 e del file v1 delle 06:00 del 21/10: fuori dal
  perimetro del Gold, che parte dal 31/08/2026), 685 in `turno_prep_sito` e `F_TURNO_PREP_SITO`.
- Fase 3: `prep_sped` 21/10 con `full_refresh=true` (run 411457110813550) SUCCESS, `dq_gate` verde; 22/22 `datamart`.
- Confronto prima/dopo: riepiloghi pre-2026 = 0 ovunque; `F_TURNO_PREP_SITO` 339.141 → 341.897 (−685 righe 2019–2025,
  + i riepiloghi 07–16/10 non caricati il 16/10); `A_TURNO_PREP_SITO` 577 → 650 (15–20/10 completi); altre tabelle
  invariate, 0 chiavi duplicate.
