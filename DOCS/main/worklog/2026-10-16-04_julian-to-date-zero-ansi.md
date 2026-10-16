---
data: 2026-10-16
titolo: "julian_to_date: una data '0' faceva fallire il job su serverless (to_date ANSI) — correzione nella libreria + wheel ricaricato sul Volume"
autore: Francesco Foconi
push_monorepo: "PR dedicata"
push_documentation: "split dopo merge"
push_gitlab: "lib: rilascio solo main, nessun tag (LL-031); wheel sul Volume a mano (ADR-0025)"
act: [ACT_9030, ACT_9027]
adr: [ADR-0025]
lesson: [LL-022]
op: []
---

## Contesto
Recupero di ottobre ([[ACT_9030]]): `logistica_prep_sped` del 07/10 FAILED (run 421169607614170) su
`silver_prep_riepiloghi`: `CAST_INVALID_INPUT: The value '0' of the type "STRING" cannot be cast to "DATE"`, su tutti e
3 i tentativi. La nuova estrazione porta riepiloghi che prima non arrivavano: 4 righe del 07/10 hanno
`RPLPR_DATA_MODIFICA = 0`.

## Diagnosi
`logistica_utils.utils.julian_to_date` scarta correttamente lo `0` come giuliano (`null_if_non_positive`), ma poi
calcola sempre il ripiego "data standard" `F.to_date(s)` sulla stessa stringa: su serverless (ANSI) `to_date('0')` **lancia
l'eccezione** invece di dare NULL (verificato sul SQL warehouse: `to_date('0')` → `CAST_INVALID_INPUT`,
`try_to_timestamp('0')` → NULL). È la stessa classe di [[LL-022]]. La funzione è usata da 16 notebook: lo stesso valore
può fermare altri job.

## Decisione
- Ripiego "data standard" solo per le stringhe **non** fatte di sole cifre e con `try_to_timestamp` (NULL sul
  malformato), per i formati `yyyy-MM-dd`, `yyyy-MM-dd HH:mm:ss`, `dd/MM/yyyy`. Comportamento invariato per i giuliani
  validi e per le date standard valide.
- Wheel `logistica_utils-1.0.0` ricostruito da `lib/` e ricaricato sul Volume `_wheels` (stesso nome: i notebook lo
  installano con `%pip` a runtime, [[ADR-0025]]); copia di riserva del wheel precedente in `_wheels/backup/`.
  Verificato prima che il wheel sul Volume coincidesse file per file con `lib/` di `main`.

## Esito
_(in corso)_
