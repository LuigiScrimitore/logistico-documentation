# DOCS — Documentazione Logistico 2.0

Mappa della documentazione di progetto. La documentazione **viva** è in [`main/`](main/); il resto è
materiale di supporto/storico organizzato per tema.

| Cartella | Contenuto | Nel repo doc? |
|----------|-----------|:---:|
| [`main/`](main/) | **SSOT viva**: attività ([`acts/`](main/acts/)), decisioni ([`adr/`](main/adr/)), indice unico ([`15_backlog_master.md`](main/15_backlog_master.md)), doc numerati, sprint, milestones | ✅ |
| [`assessment/`](assessment/) | Deliverable dell'assessment iniziale (Analisi Tecnico-Funzionale AS-IS, AT per area, Solution Design, stima, pptx finale) | ✅ |
| [`linee_guida/`](linee_guida/) | Linee guida piattaforma cliente + Punti di approfondimento (v1.0→v2.3) + chiarimenti + richieste infra | ✅ |
| [`analisi/`](analisi/) | Analisi AS-IS / to-be + tabelle sorgenti/target + mappatura Lookup `LU_*` (xlsx) | ✅ |
| [`piani/`](piani/) | Piani operativi: cut-over, rollback, Gantt, Piano di Sviluppo (xlsx) | ✅ |
| [`guide_dev/`](guide_dev/) | Guide operative locali: test locale Bronze/Quickstart, recupero spazio Docker | ✅ |
| [`Archive/`](Archive/) | Documenti **superati** assorbiti in `main/` + mapping speculativi + `pipeline_mapping.md` vecchio | ✅ (storico) |
| `99. SCRIPT/` | Sorgenti SQL ODI/CDT_DW (AS-IS) — **proprietari cliente** | ❌ **solo locale** (`.gitignore`) |
| `altro/` | PDF scambi email (infra, SFTP) — **dati personali** | ❌ **solo locale**, da eliminare a infra conclusa |
| `exec/`, `logs/` | Output/log generati dai run | ❌ **esclusi** (rigenerabili) |

> **Destino repo**: al cutover, il contenuto ✅ confluisce in **`logistico-documentation`** (solo su GitHub —
> vedi [ADR-0016](main/adr/0016_multi_repo_gitlab.md)); il materiale ❌ resta locale.
