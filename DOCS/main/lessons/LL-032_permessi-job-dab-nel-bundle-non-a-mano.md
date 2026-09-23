---
id: LL-032
titolo: Permessi sui job DAB — si dichiarano nel bundle (permissions:), non a mano
sintomi:
  - "un utente/gruppo non vede i job creati dalla CI/MI (owned dalla MI) nella propria vista Jobs"
  - "i grant CAN_MANAGE/CAN_VIEW dati a mano dalla UI spariscono/si riallineano al deploy DAB successivo"
tag: [databricks, dab, permessi, acl, ci, mi]
stadio: regola-documentata
automatizzabile: false
autore: Francesco Foconi
data: 2026-09-23
origine: [richiesta-grant-group-engineering-dev, ADR-0027]
---

## Sintomo
I job deployati dal bundle via CI/Managed Identity sono di **proprietà della MI**: un utente personale
(o il suo gruppo) **non li vede** nella propria pagina Jobs, e non può eseguirli/gestirli. Dare i grant
**a mano** dalla UI non regge: al **deploy DAB successivo** le permission vengono **riallineate** allo
stato dichiarato nel bundle.

## Perche'
DAB gestisce le risorse in modo **dichiarativo**: ciò che non è nel bundle non è tracciato e viene
riportato allo stato del bundle a ogni deploy. Quindi le permission vanno messe **nel bundle**, non fuori.

## Regola
Dichiarare i permessi nel `databricks.yml` con il blocco **`permissions:`** (a livello di target o di
bundle): valgono per **TUTTE le risorse** create dal bundle, senza doverle specificare job per job.
```yaml
targets:
  dev:
    mode: development
    permissions:
      - level: CAN_MANAGE
        group_name: Group-Engineering-dev
```
- Hanno effetto **solo dopo un `bundle deploy`** (via CI) — non retroattivi.
- Livelli: `CAN_VIEW` / `CAN_MANAGE_RUN` / `CAN_MANAGE`; destinatario `group_name` / `user_name` /
  `service_principal_name`.
- Per-ambiente: il grant al gruppo dev va sul target **dev** (i sandbox personali in home hanno già
  CAN_MANAGE dell'utente); stage/prod avranno i propri gruppi.

## Conferme e contraddizioni
- 2026-09-23 · l'admin conferma che sui job **DAB** non può aggiungere permessi a mano (li sovrascrive il
  deploy) → soluzione: `permissions` nel `databricks.yml`. Aggiunto `CAN_MANAGE` per `Group-Engineering-dev`
  sul target `dev`, così il gruppo vede/gestisce i job `[dev <mi>] logistica_*` (spiega perche' prima
  "non vedevamo niente": ACL, i job erano della MI). Coerente con [[LL-030]] (naming) e [[ADR-0027]] (ambienti).
