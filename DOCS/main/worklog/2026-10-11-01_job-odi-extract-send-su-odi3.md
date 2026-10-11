---
data: 2026-10-11
titolo: "Job ODI schedulato che lancia extract_and_send.sh su odi3 (forced command ssh)"
autore: Francesco Foconi
push_monorepo: "PR #24 (README relay + extract_and_send.sh + ACT + worklog)"
push_documentation: "da ri-split dopo merge"
push_gitlab: "—"
act: [ACT_OP-INF-4]
adr: []
lesson: []
op: [OP-INF-4]
---

## Contesto
Obiettivo: lanciare il giro completo estrai+invia (`/opt/landing/bin/extract_and_send.sh`, già presente su odi3 =
`odisrvcno3`, 10.8.1.158) da un **job ODI schedulato**, eseguito dall'agent `odisrvcno1` o `odisrvcno2`.
Il canale ssh agenti → odi3 esiste già (Opzione A, validata il 2026-10-01), ma il forced command della chiave degli
agenti lancia solo `upload_landing.sh` (invio senza estrazione).

## Cosa (procedura, dettagli nel README del relay § "Job ODI schedulato")
1. **odi3**: in `/home/svc_landing/.ssh/authorized_keys` il forced command passa da `upload_landing.sh` a
   `extract_and_send.sh dev logistico` (stessa chiave, `restrict`, `from=` solo .211/.212). Da qui la chiave lancia
   solo estrai+invia, con `run_date` = giorno di esecuzione.
2. **odi3**: spenti `landing-extract-send.timer` e `landing-upload.timer`, così il giro parte solo da ODI.
3. **ODI**: step `OdiOSCommand` sincrono con `ssh … svc_landing@10.8.1.158` (keepalive); l'exit code di odi3 torna a
   ODI, quindi un KO di estrazione o invio fa fallire lo step.
4. **ODI**: scenario schedulato sull'agent (giornaliero).
5. **Verifica** primo run: step ODI verde + `extract_send_recap.log` su odi3 (`status: OK`) + file in `logisticolanding`.

## Note
- Sugli agenti non serve nessuno script nuovo: ODI esegue direttamente `ssh`. L'agent deve girare come `oracle`
  (proprietario di `~/.ssh/id_rsa_landing`).
- Il trigger di solo invio (`trigger_landing_upload.sh`) non serve più: la stessa chiave ora lancia estrai+invia.
- Consigliato aggiornare `/opt/landing/app` su odi3 dal repo (PR #20: siti spenti laix/lfsx/lgsx esclusi).

## Esito — OPERATIVO
- **odi3**: forced command aggiornato su entrambe le chiavi (`grep` = 2, backup `authorized_keys.bak`).
  `landing-extract-send.timer` **non era installato** (nessun doppio giro, ma nemmeno estrazioni automatiche finora).
- **Primo test da agent** (ssh con stringa finale `extract-send`): estrazione **OK** (270 file, ~2,47 M righe,
  0 errori, 413 s), invio **KO** con `sistema non valido: ''` → `exit=2`. Causa: la stringa del client arriva in
  `SSH_ORIGINAL_COMMAND`, che `extract_and_send.sh` passa senza volerlo a `upload_landing.sh`, che le dà la
  precedenza sugli argomenti (`env=extract-send`, `sistema` vuoto).
- **Correzione**: nel comando ssh di ODI si passa `'dev logistico'`; nel repo `extract_and_send.sh` chiama il sender
  con `env -u SSH_ORIGINAL_COMMAND` (da copiare su odi3 insieme all'aggiornamento di `/opt/landing/app`).
- **Secondo test da agent** (stringa finale `'dev logistico'`) → **OK, `exit=0`**: estrazione 270 file / ~2,47 M righe /
  0 errori (430 s); invio `CompletedWithSkipped`: **276 file inviati** (270 + 6 anagrafiche CDT_DW), 0 falliti, 1,48 GB
  in 12 s; 1433 file saltati perché già presenti e invariati (staging cumulativa, `--overwrite=ifSourceNewer`).
  Comando ODI validato end-to-end.
- **ODI**: package con step `OdiOSCommand` sincrono (comando ssh con `dev logistico` senza apici) → scenario → **Run**
  manuale **verde**. Agent ODI su odisrvcno2: girano tutti come `oracle` (ODI 12.2.1.4; agent `ODISRV2Agent1`
  in `base_domain`, `ODISRV2TestAgent` e `ODISRV2DWTAgent` in `test_domain`).
- **Verifica sul container** (SQL su External Location `logisticolanding_dev`): giorno `2026/10/11` = **276 file**
  (logistix 262, stat 6, track 2, cdtdw 6), scritti tutti alle 22:04 ora italiana, cioè dal run ODI (che sovrascrive
  quelli del test manuale). Nessun file `cdt-estr-raw` per l'11/10: tabelle senza righe nel giorno (`empty_skipped`).
- **Schedulazione**: scenario schedulato in ODI ogni giorno alle **06:00** (ora italiana), poi spostato alle
  **05:00** (worklog 2026-10-11-02).
- ⚠️ **odi3 è su UTC** (log a 19:58 = 21:58 italiane): `run_date` di default = data UTC di odi3. Con lo schedule alle
  06:00 italiane (04:00 UTC) la data è corretta; **non schedulare tra 00:00 e 02:00** italiane (sarebbe il giorno prima).
- **Storico nel container**: presenti solo 01, 03, 07, 08, 10, 11 ottobre (prima non c'era schedulazione su odi3).
  *Correzione*: i giorni mancanti **non** si gestiscono tutti allo stesso modo. Tabelle delta **senza** flag: già
  coperte dalla finestra di 4 giorni del giro successivo. Tabelle **col flag** ODI: il lookback non basta (vedi
  worklog 2026-10-11-02). Tabelle **snapshot** (`catena`, `catena_esterni` = giacenze): un giorno saltato è perso;
  rilanciarle con una data passata produce la fotografia di oggi con la data sbagliata ([[LL-006]]).
- Aperto: la staging su odi3 è **cumulativa** (1709 file, 12 GB al 2026-10-11) → definire la pulizia post-invio
  (già tra i follow-up dell'ACT).
