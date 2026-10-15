---
data: 2026-10-15
titolo: "F_PREP_SPED ferma al 02/09: silver_prep_prep_sped partiva prima dei suoi input (dipendenze DAG mancanti) + depends_on duplicato in datamart"
autore: Francesco Foconi
push_monorepo: "PR dedicata"
push_documentation: "split dopo merge"
push_gitlab: "workflows: rilascio solo main, nessun tag (LL-031)"
act: [ACT_9014]
adr: [ADR-0019]
lesson: [LL-038]
op: []
---

## Contesto
Controllando la copertura di ottobre in Gold (`gold_dev.logistica`), `F_PREP_SPED` contiene solo 179.261 righe con
`GIORNO_ORD_ID` 31/08–02/09, anche se il job `logistica_prep_sped` finisce ogni giorno in SUCCESS e riscrive la tabella.

## Diagnosi
- `silver_dev.logistica_curated.prep_sped` (lo strato PREP che alimenta il Gold) ha **un solo `_silver_load_date`:
  2026-09-02**. Le sorgenti invece sono piene: `storico_liste_uniche` ~3,6 M righe caricate dall'11/09 al 15/10,
  `storico_bolle_uniche` ~8,9 M.
- `silver_prep_prep_sped` è incrementale: prende solo le chiavi di prelievo con `_silver_load_date = run_date` in
  `storico_liste_uniche` / `storico_bolle_uniche`. Ma nel job **non ha `depends_on`**: parte insieme ai bronze, prima
  che i due silver "uniche" del giorno siano scritti. Run del 15/10 (ora italiana):

  | task | inizio | fine |
  |---|---|---|
  | `silver_prep_prep_sped` | 08:15:00 | 08:16:41 |
  | `gold_f_prep_sped` | 08:16:41 | 08:17:20 |
  | `silver_storico_bolle_uniche` | 08:18:19 | 08:21:45 |
  | `silver_storico_liste_uniche` | 08:18:25 | 08:23:32 |

  Trova 0 chiavi del giorno, fa un MERGE vuoto ed esce verde. Il giorno dopo cerca solo il nuovo `run_date`: quanto
  caricato il giorno prima non viene più ripreso. Dal 02/09 (unica esecuzione con la tabella non ancora esistente, CTAS
  completo) nessuna riga nuova è arrivata al Gold.
- La dipendenza manca dal 18/08 (`8638f56`, DAG rigenerato dal codice, [[ACT_9014]] / [[ADR-0019]]): i due input non
  sono stati riconosciuti. Manca anche `bronze_prep_riepiloghi` (input `storico_riepiloghi`).
- Controllo su tutti e 7 i job (tabelle lette/scritte da ciascun notebook vs `depends_on`): un solo altro caso.
  In `logistica_aggregati.yml` il task `gold_a_stock_mensile` ha la chiave **`depends_on` scritta due volte**: in YAML
  vale l'ultima, quindi la dipendenza da `gold_dm_giacenze_monthly` (che scrive `A_GIACENZE_MONTHLY`, letta da
  `A_STOCK_MENSILE`) è persa in silenzio. Né `bundle validate` né i test lo segnalavano.

## Decisioni
1. `silver_prep_prep_sped` dipende da `silver_storico_liste_uniche`, `silver_storico_bolle_uniche`,
   `bronze_prep_riepiloghi`.
2. `gold_a_stock_mensile`: un solo `depends_on` con tutte le dipendenze (`gold_dm_giacenze_monthly` + i 5 `lad_*`).
3. Nuovo parametro di job `full_refresh` (default `"false"`) in `logistica_prep_sped`, passato a
   `silver_prep_prep_sped` (il widget esiste già): serve per il recupero e per i ricalcoli futuri.
4. Guardrail in `tests/test_workflows_alignment.py`: niente chiavi YAML duplicate; ogni task che legge una tabella
   scritta da un altro task dello stesso job deve averlo tra i suoi antenati. Regola in [[LL-038]].
5. Recupero: dopo il deploy, un run di `logistica_prep_sped` con `full_refresh=true` (rielabora tutte le liste
   uniche → `prep_sped` → Gold).

## Esito
- PR [#33](https://github.com/LuigiScrimitore/Logistico2.0/pull/33) mergiata (`7dc3a44`); `workflows` **v0.1.12** su
  GitLab (solo main), deploy CI verificato (dipendenze e parametro `full_refresh` presenti sul job della MI).
- Recupero: run 643777881235239 con `full_refresh=true`. `logistica_curated.prep_sped` e `F_PREP_SPED` passano da 179.261
  a **5.385.181 righe** (31/08→15/10), in linea con `storico_liste_uniche` (5.385.182). Ottobre: presenti 01, 02, 12–15;
  03–11 mancano come negli altri fatti (landing non letta in quei giorni, da recuperare rilanciando i giorni).
- Il run termina **FAILED sul `dq_gate`**: check BLOCKING `not_null_DATA_PREL` = **524 righe**. Sono tutte righe
  **scartate** (TIPO_SCAR 09: 441, 10: 83), sito 09, ordine del 12/10, con `LSPRL_DATA_PRELIEVO`/`ORA_PRELIEVO` NULL in
  Logistix: mai prelevate, la data di prelievo non esiste. L'ipotesi "DATA_PREL sempre valorizzata dopo OP-PSP-2"
  (`acceptance.py`) non regge sui dati reali; prima non emergeva perché i dati non arrivavano.

## Decisione (A) — DATA_PREL per le righe senza data di prelievo
`DATA_PREL` è solo la colonna di partizione del Gold (non esiste in CDT_DW). Per le righe senza data di prelievo si usa la
**data dell'ordine** (`GIORNO_ORD_ID`); `DATA_PREL_INIZ` resta NULL come nel legacy e il check `not_null` resta BLOCKING.
Scartata l'alternativa B (escludere le scartate dal check): lascerebbe una partizione a data NULL in Gold.
Il Gold scrive in `partitionOverwriteMode=dynamic`, che non tocca la partizione NULL scritta il 15/10: prima della
scrittura il notebook elimina le righe con `DATA_PREL IS NULL` (idempotente; recuperabile con il time travel Delta).
Verifica: nuovo run di `logistica_prep_sped` dopo il rilascio, `dq_gate` atteso SUCCESS.
