---
data: 2026-09-23
titolo: "Decisioni ambienti: modello 4 livelli (ADR-0027) + auth CI = MI unica; naming stage; ACT_9028"
autore: Luigi Scrimitore
push_monorepo: "n/d (doc-pass, da pushare)"
push_documentation: "n/d"
push_gitlab: "—"
act: [ACT_9028]
adr: [ADR-0027]
lesson: [LL-030]
op: [OP-INF-3]
---

## Cosa e' stato fatto
Chiusura decisionale di **OP-INF-3** (modello ambienti) dopo l'incidente duplicati CI ([[LL-030]]).
Due decisioni prese da Luigi, da condividere col team:

1. **Auth CI = Managed Identity UNICA** (non per-utente) — **confermato**. Un solo set `[dev <mi>] logistica_*`;
   è la garanzia strutturale contro i duplicati (una identità → un root_path → uno stato). Chiude la domanda
   aperta di OP-INF-3.
2. **Modello a 4 ambienti per maturità** ([[ADR-0027]], status `proposta`): **sandbox → dev → stage → prod**,
   promozione **solo-avanti a gate**:
   - **sandbox** = sviluppo volatile per-utente da locale (`[dev <utente>]`);
   - **dev** = verifica patch **verde** condivisa via CI/MI (`[dev <mi>]`);
   - **stage** = pre-produzione **osservata N giorni** (monitoraggio + `dq_gate`) quando il flusso e' completo e **quadrato**;
   - **prod** = **certificato** dopo N giorni verdi entro i limiti di certifica.
   - Gate: verde→dev · funzionale+quadrato→stage · stabile N gg + certifica→prod. Esempio guida: `F_CARICO`.

## Novita'
- **Naming job stage deciso**: target DAB `stage` in `mode: production` + `presets.name_prefix: "[stage] "`
  → job **`[stage] logistica_*`**. Distinto da dev (`[dev <identità>]`) e prod (canonico) → nessuna
  collisione anche a workspace condiviso; coerente con [[LL-030]] (canonico riservato a prod).
- **[[ACT_9028]]** aperta (proposed): configurare `stage` end-to-end — catalog `_stage` via Terraform
  ([[ADR-0004]], `_stage` finora solo previsto) + target DAB `stage` + regola CI di promozione dev→stage.

## Doc aggiornati
- `adr/0027_...` (nuovo, proposta) + `README_adr` elenco · `acts/ACT_9028_...` (nuovo) ·
  `15_backlog_master` (righe ADR-0027 + 9028) · `05_open_points` (OP-INF-3 aggiornato) · questo worklog.

## Stato dopo il push / prossimi passi
- **Decisioni pronte da condividere col team** (ADR-0027 `proposta` → ratifica). Restano solo punti
  **implementativi** (in ACT_9028): topologia workspace (unico vs separati), sandbox vs dev sullo stesso
  catalog `_dev`, trigger di promozione dev→stage.
- Prossimo: ratifica team di ADR-0027, poi ACT_9028 (infra `_stage` + target DAB + CI). Auth CI gia' chiarita.
