---
data: 2026-10-15
titolo: "Recupero dei fatti Gold di ottobre (03–14/10) rilanciando i job sui giorni passati, con prova e confronto prima/dopo"
autore: Francesco Foconi
push_monorepo: "PR solo doc"
push_documentation: "split dopo merge"
push_gitlab: "nessuno (nessuna modifica al codice)"
act: [ACT_OP-INF-4]
adr: []
lesson: [LL-006, LL-038]
op: [OP-INF-4]
---

## Contesto
In `gold_dev.logistica` mancano i giorni 03–11/10 di quasi tutti i fatti, e 03–14/10 di giacenze e carrellisti: in quei
giorni i job dev cercavano la landing nel Volume (non più alimentato) e dal 09/10 erano in pausa. Nel container
`logisticolanding` ci sono le cartelle 01–03, 07, 08, 10–15 (mancano 04, 05, 06, 09); ogni estrazione copre anche i 3 giorni
precedenti, quindi i fatti transazionali di 03–14 sono tutti recuperabili.

## Piano
Per ogni `run_date`, **in ordine crescente** (così per ogni riga l'ultima versione scritta è la più recente):

| giorni | job |
|---|---|
| 03, 07, 08, 10, 11 | `carichi` · `trasporti` (senza `bronze_automezzi`) · `prep_sped` · `datamart` |
| 12, 13, 14 | come sopra + `giacenze` |
| 04, 05, 06, 09 (senza cartella) | solo i Gold per giorno: `gold_f_movimentazione_carrellisti`, `gold_dm_turno_prep_sito` |
| alla fine: 15 | `carichi` · `trasporti` · `prep_sped` · `datamart` — riporta all'ultima versione le righe riscritte dai giorni precedenti |
| alla fine: 30/09 | `datamart` (aggregati di settembre, cambiati con il recupero di `F_PREP_SPED`) |

Esclusi:
- `landing_ingestion` e `dim_refresh`: solo anagrafiche, quelle di oggi sono le più aggiornate;
- `bronze_automezzi`: anagrafica da `cdt-estr-raw`, presente solo dal 14/10 (darebbe `PATH_NOT_FOUND` e mail di errore);
- `giacenze` su 03–11: le cartelle `catena` di 01, 03, 07, 08, 10 sono la fotografia del giorno dopo, la 02 è da
  escludere e 04–06/09 non esistono. Le fotografie non si ricostruiscono dopo ([[LL-006]]): giacenze 03–11 restano
  mancanti.

## Sicurezza e prova
1. **Fotografia prima**: righe per giorno di ogni fatto/aggregato e versione Delta di ogni tabella toccata (rete di
   sicurezza: `RESTORE TABLE ... TO VERSION AS OF`).
2. **Prova su un giorno (03/10)**, poi confronto: i giorni fuori dalla finestra recuperata devono restare identici, quelli
   dentro solo crescere, nessuna chiave duplicata (`dq_gate` + controllo diretto).
3. Solo con la prova pulita si procede con gli altri giorni; confronto finale prima/dopo.

## Prova sul 03/10 (esito)
Run `carichi` 480919269590604, `trasporti` 225103614767217 (senza `bronze_automezzi`), `prep_sped` 136180457397643,
`datamart` 1003247194580956: tutti SUCCESS. Confronto prima/dopo **pulito**: nessun giorno fuori finestra cambiato,
nessun calo, 0 chiavi duplicate. Crescono `F_CARICO` 01–02, `F_TRACCIABILITA_LOTTI` 03, `F_TURNO_PREP_SITO` 30/09–03/10,
`F_MOVIMENTAZIONE_CARRELLISTI` 03, aggregati di ottobre.

La prova ha però mostrato due cose da cambiare nel piano:
1. **Silver a watermark** (OP-35): `silver_carichi_testate`, `silver_carichi_dettagli`, `silver_storico_liste_clean`,
   `silver_storico_bolle_clean`, `silver_ordini`, `silver_spedizioni_clean` elaborano solo `_bronze_load_date >
   watermark` (= 15/10): i giorni vecchi rilanciati vengono **ignorati** (bronze `storico_liste` del 03 = 1.005.164 righe,
   `storico_liste_clean` del 03 = 0). L'override `process_from` esiste nei notebook ma **non è collegato** ai job.
2. **Ordine delle versioni**: il bronze transazionale è `DELTA_MERGE` sulla chiave naturale, quindi per ogni chiave resta
   l'ultima versione *scritta*. Rilanciando 14 dopo il 15, le righe della finestra 12–14 tornerebbero alla versione del
   14. La prova sul 03 è sicura (finestra 30/09–03/10, nessuna sovrapposizione col 15, più recente dei carichi di 01–02).
   Le fotografie (`catena`, `catena_esterni`) sono `SNAPSHOT` per partizione del giorno: nessun rischio.

## Piano rivisto
1. Collegare `process_from` (parametro di job, default vuoto = watermark) ai 6 notebook a watermark nei job `carichi`,
   `trasporti`, `prep_sped`; rilascio `workflows`.
2. Giorni 07, 08, 10, 11, 12, 13, 14 in ordine crescente (come la prova; `giacenze` solo 12–14). I silver a watermark
   saltano (nessuna riga oltre il 15): li recupera il passo 4.
3. Giorni senza cartella 04, 05, 06, 09: solo `gold_f_movimentazione_carrellisti` e `gold_dm_turno_prep_sito`.
4. **Chiusura sul 15/10** con `process_from=2026-10-02`: `carichi`, `trasporti`, `prep_sped`, `giacenze`, `datamart`.
   Il bronze torna alla versione del 15 per le chiavi 12–15, i silver a watermark elaborano in un colpo solo tutto il
   bronze dal 03 (una riga per chiave, già all'ultima versione), il watermark torna al 15.
5. `datamart` sul 30/09 (aggregati di settembre). Confronto finale prima/dopo.

## Esito
_(in corso)_
