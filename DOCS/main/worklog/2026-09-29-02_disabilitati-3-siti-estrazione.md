---
data: 2026-09-29
titolo: "Disabilitati 3 siti (laix, lfsx, lgsx) dalle estrazioni landing (ORA-12514, siti spenti)"
autore: Francesco Foconi
push_monorepo: "config.yaml estrattore + worklog (PR dedicata)"
push_documentation: "da ri-split dopo merge"
push_gitlab: "—"
act: []
adr: []
lesson: []
op: []
---

## Contesto
Tentando il giro completo del **27** (e poi 26), l'estrazione e' fallita con **57 errori
`ORA-12514: TNS listener does not currently know of service`**, tutti concentrati su **3 siti**:
`laix`, `lfsx`, `lgsx` (19 tabelle ciascuno). Gli altri 19 siti rispondevano. Confermato via probe
(ancora giu' a distanza di minuti). L'utente ha confermato: **quei 3 siti sono disabilitati**.

Poiche' il seed e' "tutto-o-niente" (basta un errore -> non copia sul Volume), la presenza dei 3 siti
in lista faceva **fallire l'intera estrazione** di ogni giorno.

## Cosa e' stato fatto
- **`scripts/landing_simulator/config.yaml`** (`logistix.dblinks`): **commentati** i 3 siti disabilitati
  `laix`/`lfsx`/`lgsx` (non rimossi, per traccia e facile ri-abilitazione). Le future estrazioni girano
  automaticamente sui **19 siti attivi**, senza ORA-12514.
- Coerente col commento del file: i dblinks seguono `CDT_ESTR.S_LOGISTIX WHERE FLAG_ATTIVO = 1`; questi
  3 siti sono ora spenti.

## Stato al momento dello stop (per la ripresa)
- **27 e 26 NON eseguiti** (giro interrotto). **Landing cloud ferma a `01→24`**: nessun dato parziale di
  25/26/27 spinto sul Volume (stato pulito, nessun rollback necessario).
- Il **25** era gia' rimasto indietro nei giorni scorsi (VPN).

## Ripresa
- Estrarre **27, 26 (e 25)** — ora sui **19 siti attivi** (i 3 esclusi) -> Volume -> run 7 job MI.
- Se i 3 siti tornano attivi (`FLAG_ATTIVO=1` su S_LOGISTIX), **ri-abilitarli** de-commentandoli nel config.
