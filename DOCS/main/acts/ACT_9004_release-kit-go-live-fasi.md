# ACT_9004 · Release kit go-live a fasi (KIT-01..08)

**Status**: done   **Type**: infra   **Origin**: emerged (preparazione rilascio pre-accesso infra)
**Sprint**: fuori-sprint (emergente)   **Fase / Wave**: FASE 8 (deploy/go-live)
**Closed**: 2026-07-05
**Dipende da**: —   **Blocca**: — (integrazione al gate infra)
**ADR collegate**: ADR-0017 (go-live a fasi), ADR-0014 (DQ/alerting interni), ADR-0015 (tuning cloud non trasferibile)   **OP collegati**: OP-07, OP-24, OP-25

## Contesto
Per non arrivare scoperti al momento dell'accesso infra, sono stati preparati **offline** gli artefatti del
rilascio a fasi (ADR-0017). SSOT del dettaglio = [`14_release_kit.md`](../14_release_kit.md) e
[[release-kit]]. Questa ACT è il tracker del kit.

## Obiettivo
Kit di rilascio pronto pre-accesso: invio SFTP, acceptance/smoke, DQ/alerting, tag costo, DAB, rollback,
tuning — tutto integrabile al gate infra.

## Esito
Consegnati KIT-01..08: **KIT-01** `scripts/sftp/send_to_sftp.py` (push landing); **KIT-02**
acceptance-criteria + smoke-test pipeline; **KIT-03/04** DQ & alerting interni (`dq_monitor`, ponte verso
OP-20/21, ADR-0014); **KIT-05** tag costo (cost attribution); **KIT-06** Databricks Asset Bundle; **KIT-07**
rollback; **KIT-08** tuning. Nota (ADR-0015): il **tuning locale non è trasferibile** al serverless cloud →
si ritara al primo rilascio. Cosa integrare al gate infra è elencato in `14_release_kit.md`.
