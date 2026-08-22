---
id: LL-012
titolo: CERTIFICATE_VERIFY_FAILED in un job container verso un host aziendale → manca la CA interna nel container
sintomi:
  - "CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate"
  - "l'upload/chiamata verso l'host aziendale (GitLab/Nexus/Databricks) fallisce in TLS"
  - "lo stesso job scarica bene da PyPI/Docker Hub ma fallisce sul solo host interno"
tag: [ci-cd, tls, certificati, container, ambiente-cliente]
stadio: regola-documentata
automatizzabile: true
autore: luigi.scrimitore
data: 2026-08-22
origine: [ACT_9017]
---

## Sintomo
Un job CI in un container (es. `image: python:3.11`) fallisce con
`SSL: CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate` **solo** quando parla con un host
aziendale interno (GitLab Package Registry, Nexus, Databricks…), mentre le chiamate verso host pubblici
(PyPI, Docker Hub) nello stesso job **funzionano**.

## Strada sbagliata
Due tentazioni sbagliate:
1. **Disabilitare la verifica TLS** (`-k`, `verify=False`): sblocca ma è un downgrade di sicurezza permanente su
   un sistema aziendale — no.
2. **Sostituire** il CA bundle con la sola CA interna (`REQUESTS_CA_BUNDLE=ca_interna`): così si rompe la
   verifica verso gli host pubblici (PyPI non valida più). Va **aggiunta**, non sostituita.

## Regola
La CA pubblica del container è a posto (gli host pubblici funzionano); manca la **CA aziendale interna**.
Aggiungila al **trust store di sistema** (che già contiene le pubbliche), non sostituirlo:
```yaml
before_script:
  - |
    CA="${CI_SERVER_TLS_CA_FILE:-${COMPANY_CA_BUNDLE:-}}"   # GitLab espone spesso CI_SERVER_TLS_CA_FILE
    if [ -n "$CA" ] && [ -f "$CA" ]; then
      cp "$CA" /usr/local/share/ca-certificates/internal-ca.crt
      update-ca-certificates >/dev/null 2>&1 || true
      export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt   # pubbliche + interna
      export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    fi
```
Se `CI_SERVER_TLS_CA_FILE` non è esposto, farsi dare la CA come **variabile CI di tipo File** (es.
`COMPANY_CA_BUNDLE`) dal team piattaforma: nessuna modifica al codice, solo la variabile.

## Perché
Il container porta solo le **CA pubbliche** (certifi/ca-certificates di base): non conosce la PKI interna
dell'azienda. Il runner *host* può fidarsi della CA interna (comunica con GitLab), ma quella fiducia **non
entra** nel container del job. `update-ca-certificates` fonde la CA interna con le pubbliche in un unico bundle
→ la verifica passa verso entrambi i mondi. È lo stesso principio di [[LL-010]]: non reinventare/azzerare ciò
che è già curato (il bundle pubblico), ma **estenderlo**.

## Conferme e contraddizioni
- 2026-08-22 · luigi.scrimitore · pilot `logistico-lib`: `publish` del wheel falliva in TLS verso
  `cp1lgitlab...` mentre `pip install` da PyPI andava. Aggiunta la CA via `CI_SERVER_TLS_CA_FILE` al trust
  store → `publish` verde, wheel nel Package Registry.
