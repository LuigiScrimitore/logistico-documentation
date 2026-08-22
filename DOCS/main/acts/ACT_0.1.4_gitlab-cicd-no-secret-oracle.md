# ACT_0.1.4 · GitLab CI/CD al posto di Key Vault + Secret Scope

**Status**: done   **Type**: infra   **Origin**: sprint 0.1
**Sprint**: 0.1 — Unity Catalog & Storage Foundation   **Fase / Wave**: FASE 0 — Fondamenta
**Closed**: 2026-07-02
**ADR collegate**: ADR-0005 (no segreti Oracle / export su landing, D5)   **OP collegati**: —

## Contesto
L'attività nasceva come "Key Vault + Secret Scope" per custodire le credenziali Oracle usate in un
ipotetico accesso JDBC diretto dai notebook. La decisione D5 (ADR-0005) ha però escluso qualsiasi
connessione Oracle da Databricks: le sorgenti arrivano come **export su landing**, non via JDBC. Caduto
il bisogno di segreti Oracle, l'impianto Key Vault perdeva ragione d'essere e andava ridisegnato.

## Obiettivo
Nessun segreto Oracle su Azure; gestione dei soli secret di deploy (SP, token Databricks) via GitLab
CI/CD; confermare che **Azure Key Vault non è necessario** per il perimetro logistico.

## Esito
Ridisegnata 2026-07-02. Nessun `dbutils.secrets.get(...)` nei notebook: la landing UC Volume usa la
**managed identity** del workspace; le credenziali di deploy (Service Principal, token Databricks) sono
**variabili masked in GitLab CI/CD**. Nessuna colonna da cifrare (dati operativi, no PII). **AKV escluso**
dal perimetro. Coerente con ADR-0005.
