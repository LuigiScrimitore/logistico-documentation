---
id: LL-006
titolo: La storia di un fact snapshot non è backfillabile — verificarlo prima di rigenerare
sintomi:
  - "una partizione storica non ha più sorgente a monte in nessun livello"
  - "silver ha una sola data mentre il fact gold ne ha diverse"
  - "la landing conserva un solo snapshot per una tabella giornaliera"
tag: [snapshot, partizionamento, gold, backfill, dati]
stadio: lezione
automatizzabile: true
autore: luigi.scrimitore
data: 2026-08-21
origine: [ACT_9015]
---

## Sintomo
`F_GIACENZE_DAILY` ha 5 date di business, ma `silver_curated.giacenze` ne ha **una sola** e la landing conserva
un solo file (`wl1_cndstostock/2026/06/09`). Le partizioni 13/16/19/21 giugno — circa **170k righe** — non
hanno sorgente in nessun livello.

## Strada sbagliata
Trattare le partizioni storiche come rigenerabili perché "basta rilanciare la pipeline su quella data". Per un
fact snapshot **non è vero**, e un full refresh le cancellerebbe **irreversibilmente**.

Errore simmetrico e opposto: assumere che siano stale e quindi da rimuovere. Non sono stale (sono snapshot
legittimi del giorno in cui furono prese), sono **non verificabili**: calcolate con logica pre-fix e senza
sorgente per ricontrollarle.

## Regola
Prima di rigenerare o ripulire un fact, **classificarlo**:

- **fact transazionale** — la sorgente conserva lo storico → le partizioni sono ricostruibili, un rebuild per
  data è sicuro (es. `F_MOVIMENTAZIONE_CARRELLISTI`: 17 date tutte ricostruibili da silver).
- **fact snapshot** — la data deriva dalla data di caricamento (`DATA_FOTO = _silver_load_date`) → **la storia
  esiste solo se qualcuno l'ha catturata quel giorno**. Non backfillabile.

Verifica concreta prima di agire: confrontare la copertura di date del fact con quella della sorgente silver e
della landing. Se la sorgente ha meno date del fact, quelle in eccesso non sono rigenerabili.

**Debito di automazione**: un guardrail che impedisca il full refresh sui fact snapshot, o che almeno lo
segnali. Verificato che oggi il rischio non è attivo — `gold_f_giacenze_daily` e
`gold_f_movimentazione_carrellisti` usano `replaceWhere` limitato a `run_date`, quindi la storia è
strutturalmente protetta — ma nulla lo impedisce a un notebook futuro.

## Perché
Uno snapshot è una fotografia: `DATA_FOTO` non descrive *quando è avvenuto un fatto* ma *quando abbiamo
guardato*. Se nessuno ha guardato il 14 giugno, quel giorno non esiste e non esisterà mai — nessuna sorgente lo
può ricostruire a posteriori.

Implicazione sull'ambiente locale: la landing simulata sovrascrive gli snapshot, quindi il warehouse locale
accumula storia che non è riproducibile. **La storia locale non è un asset certificabile.** In cloud il problema
non si presenta allo stesso modo: l'initial load costruirà la storia dal primo giorno con la logica corrente e
la conserverà.

## Conferme e contraddizioni
- 2026-08-21 · luigi.scrimitore · il caso ha generato una decisione aperta (OP-GIA-1): tenere le 170k righe a
  logica mista, o rimuoverle per avere una baseline coerente accettando la perdita definitiva. Non è una scelta
  tecnica ma di rischio, e va all'utente.
