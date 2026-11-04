---
id: LL-040
titolo: La quadratura delle misure sulle sole chiavi comuni nasconde il sovra-conteggio — controllare anche i totali
sintomi:
  - "quadratura F_CARICO verde (misure delta 0,0%, noMatch 0/392) ma il gold ha più righe e più UF dell'ODI"
  - "N_GOLD > N_ODI nella copertura mentre le misure risultano perfette"
  - "etichette multi-bolla nel gold molto più numerose che in CDT_DW (1004 vs 88)"
tag: [quadratura, gold, carichi, dq, falso-positivo, pesate]
stadio: guardrail-automatico
automatizzabile: true
autore: Francesco Foconi
data: 2026-10-29
origine: [ACT_9037]
---

# LL-040 · Quadratura solo sul comune = falso positivo sul sovra-conteggio

## Sintomo
Dopo una modifica alla grana di F_CARICO la quadratura dà **4 misure a delta 0,0%**, ma il gold ha 1004 etichette
multi-bolla contro 88 dell'ODI e il totale UF è **+0,11%** (164,12M vs 163,94M).

## Strada sbagliata
Leggere "misure 0,0%" come quadratura riuscita. `quadratura_f_carico_misure` confronta le misure **solo sulle chiavi
presenti in entrambi i lati** (join inner): le righe che esistono **solo nel gold** (qui bolle fantasma da snapshot
con bolla placeholder `'2'`, `'ROYAL'`, `'ALMA'`…) non entrano nel delta. Anche filtrare i placeholder con una lista
fissa (`'1'`,`'ONE'`) è fragile: i valori placeholder non sono un insieme chiuso.

## Regola
Una quadratura di misure va sempre accompagnata dal confronto dei **totali su tutte le righe di ciascun lato**
(non solo del comune) e dal conteggio righe `N_GOLD` vs `N_ODI`. Guardrail: `quadratura_f_carico_copertura` espone
`UF_ODI_TOT` / `UF_GOLD_TOT` per giorno × sito ([[ACT_9037]]); scarto atteso ≈ 0.

## Perché
Il confronto sul comune misura la **correttezza delle righe che coincidono**, non la **completezza** né l'assenza di
righe in più. Over-count e under-count si vedono solo sui totali.

## Conferme e contraddizioni
- 2026-10-29: con la guardia sui totali il fix definitivo v2.3.0 risulta UF −0,003% (ottobre), coerente con le ~88
  etichette mancanti ([[ACT_9038]]); il re-merge bronze a 4 chiavi è stato scartato perché la guardia mostrava +0,009%.
