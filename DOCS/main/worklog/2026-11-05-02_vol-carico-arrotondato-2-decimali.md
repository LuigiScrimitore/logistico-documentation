---
data: 2026-11-05
titolo: "VOL_CARICO arrotondato a 2 decimali come CDT_DW (lib v1.0.10) — nessun ricalcolo, effetto dal giro del 06/11"
autore: Francesco Foconi
push_monorepo: "main @3cd3e32 (PR #47)"
push_github: "lib 55ffe99, documentation 355a955 (workflows e infrastructure invariati)"
push_gitlab: "lib v1.0.10 (ae3996b) pubblicato su main il 2026-11-05, senza tag"
act: [ACT_9038]
adr: []
lesson: []
op: [Q-01]
---

## Fatto
- `attach_carico_peso_volume` arrotonda `VOL_CARICO` a 2 decimali, mezzo per eccesso, passando per un decimale a 6 cifre.
- La regola è ricavata dai dati: su settembre e 1-28/10 (1.317.958 righe) restano 0 righe diverse dal legacy; prima erano
  315.293, con scarto ≤ 0,005. Su Databricks i casi limite sono verificati: 0,215 → 0,22, anche quando il double vale
  0,21499…; 2,675 → 2,68. Spec R-2.4 aggiornata.
- Wheel ricostruito da `lib/` di main e ricaricato sul Volume. La copia precedente è in
  `_wheels/backup/…_20261105_prima_VOL2dec.whl`.

## Stato dopo il push / prossimi passi
- **Nessun ricalcolo** per scelta dell'utente: un ricalcolo mensile costa troppo al cliente. L'effetto parte dal giro
  schedulato del 06/11. `gold_f_carico` rilegge ogni giorno tutta `logistica_curated.carico`, quindi da domani anche
  settembre e ottobre escono arrotondati, senza costi aggiuntivi.
- GitLab `logistico-lib` v1.0.10: pubblicato su main (ae3996b), senza tag.
  Il codice che gira è quello sul Volume; GitLab serve solo ad allineare il repository del cliente.
