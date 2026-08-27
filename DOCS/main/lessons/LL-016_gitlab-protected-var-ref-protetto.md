---
id: LL-016
titolo: Una variabile CI "Protected" è assente sui ref non protetti — il job non la vede
sintomi:
  - "terraform chiede interattivamente una var che hai impostato come variabile CI"
  - "Error: No value for required variable (ma la variabile CI esiste)"
  - "una variabile CI/CD sembra ignorata solo in alcune pipeline"
tag: [gitlab, ci-cd, variabili, terraform]
stadio: regola-documentata
automatizzabile: false
autore: luigi.scrimitore
data: 2026-08-27
origine: [ACT_0.1.6]
---

## Sintomo
Hai impostato una variabile CI (es. `TF_VAR_databricks_host`) ma il job non la riceve: terraform la chiede
interattivamente e fallisce con `No value for required variable`. La variabile però **esiste** in
Settings → CI/CD → Variables.

## Strada sbagliata
Cercare l'errore nel nome della variabile o nel codice. Il nome è giusto: semplicemente **non viene iniettata**
in quel job.

## Regola
Il flag **Protected** su una variabile CI la espone **solo alle pipeline su branch/tag _protetti_**. Se la
pipeline gira su un ref non protetto, la variabile è assente (silenziosamente). Due vie:
- **proteggere il ref** (Settings → Repository → Protected branches/tags) — posture consigliata per i deploy;
- oppure **togliere Protected** se il valore non è un segreto (es. identificatori con Managed Identity).
Diagnosi rapida: se *alcune* variabili arrivano e altre no, o se lo stesso job cambia comportamento tra branch,
è quasi sempre Protected + ref non protetto.

## Perché
"Protected" è una feature di sicurezza (i segreti non finiscono in pipeline su branch arbitrari/MR da fork). È
utile per i segreti, ma con auth **Managed Identity** i valori sono identificatori non sensibili: lì Protected
aggiunge solo attrito. Nel caso reale l'`init` passava (backend via MI di sistema, non dipende dalle var) mentre
il `plan` falliva sulla var mancante → sintomo asimmetrico che confonde. Vedi anche [[LL-011]]/[[LL-014]]:
l'ambiente CI va reso esplicito, non dato per scontato.

## Conferme e contraddizioni
- 2026-08-27 · luigi.scrimitore · `logistico-infrastructure`: `plan` chiedeva `databricks_host` benché
  `TF_VAR_databricks_host` fosse impostata (Protected). Con `main` protetto le 4 variabili sono state esposte
  e il `plan` DEV è passato (sola lettura).
