# Sprint 2.4 — KPI Carichi & Validazione

> **Vista SAL dello sprint** — avanzamento, stato di fase e note di sprint. Questo file NON è la SSOT del dettaglio operativo.
>
> Il **dettaglio operativo di ogni attività** (contesto, analisi, verifica, esito) è nel relativo file **ACT** in [`../acts/`](../acts/): l'attività con codice `N.N.N` corrisponde a `../acts/ACT_N.N.N_<slug>.md`. Indice completo delle attività in [`../15_backlog_master.md`](../15_backlog_master.md).
>
> **Modello operativo:** l'attività si svolge sull'**ACT** (SSOT del dettaglio); qui si riflette solo lo **stato**. Una fase è chiusa solo quando la sua `GATE-N` è done (deploy + run + cert in cloud) — vedi [`../acts/README.md`](../acts/README.md).
>
> Portfolio (tutte le fasi/sprint): [`../04_piano_sviluppo.md`](../04_piano_sviluppo.md) · Chiusura fase: [`../milestones/fase_2.md`](../milestones/fase_2.md)

## Recap sprint

| Campo | Valore |
|-------|--------|
| **Fase** | FASE 2 — Wave A: Carichi (Inbound) |
| **Obiettivo** | KPI carichi + validazione funzionale con BA |
| **Gg stimati / completati** | 5 / 3 |
| **% avanzamento** | ~60% |
| **Stato** | 🔵 PARZIALE |
| **Data inizio → fine** | 14 set → 18 set 2026 |
| **Ultimo aggiornamento** | 2026-07-03 |

**Note di sprint:** viste KPI e documentazione pronte; la validazione con BA (2.4.3) è ⏳ non avviabile offline (richiede PROD + presenza BA).

## Attività

| # | Attività | Gg | Stato | Note |
|---|----------|----|-------|------|
| 2.4.1 | Vista `kpi_lead_time_fornitore` (AVG, P90) | 1 | ✅ | |
| 2.4.2 | Vista `kpi_qualita_ricevimento` (% conformi, scarti) | 1 | ✅ | |
| 2.4.3 | Validazione funzionale con BA (3 mesi vs Oracle) | 2 | ⏳ PENDENTE | richiede PROD + BA |
| 2.4.4 | Documentazione area Carichi | 1 | ✅ | `mapping_carichi.md` |
