# Specifica legacy di F_CARICO (CDT_DW) — regole verificate sulle fonti

> Casa unica delle regole legacy che decidono **quali righe** finiscono in `CDT_DW.F_CARICO` e **come** si calcolano
> le misure. Scritta il 2026-10-30 per [[ACT_9038]] dopo rilettura integrale delle fonti; ogni regola ha la sua fonte.
> Verificata sui dati: la simulazione locale di queste regole sul dato Oracle completo riproduce set + 1-28/10/2026
> (1.318.009 righe, UF e QTA identiche; unico scarto = 80 etichette rinumerate dopo il consumo, vedi R-2.3).
> Mappa colonna per colonna: [quadratura_f_carico_mappa_colonne.md](quadratura_f_carico_mappa_colonne.md).

**Fonti** (D = `Desktop\01. PROGETTI\01. CONAD NORDOVEST\1. LOGISTICO\`):
`R` = D`F_CARICO F_PESATE\replica_carichi3 vecchia versione 20240227.sql` · `V` = testo `CDT_ESTR.V_CARICO_ORDINARIO` letto
da Oracle (`LOGISTICO_DATA\datarelay_compare\viste_legacy_carico.sql`) · `E` = D`F_CARICO F_PESATE\02. ESTRAI CARICHI` ·
`ERR` = D`errore f carico.txt` · `DW` = D`5. SP_CDT_SA\CDT_DW_SP_LOAD_F_CARICO_ODI.sql` · `PKG` = spec di
`CDT_SA.LOAD_F_CARICO_STEP1` (Oracle `all_source`; il body non è leggibile con la nostra utenza).

## 1. Replica Logistix → WL1 (il "giro" legacy, ~06:45 ogni giorno)
- **R-1.1** WL1 troncate a ogni giro: il legacy elabora solo i record **pendenti** di quel giro (R 55-57).
- **R-1.2** Testate selezionate se `NVL(STCAR_DATA_ESTRAZIONE_DWH,0) = 0` (R 460); righe = inner join con la testata
  pendente su (carico, data, ordine) (R 577-581); radice/variante = `fn_get_radice/fn_get_variante_logistica('LOGISTIX',
  MSI)` = MSI senza ultime 3 cifre / ultime 3 (R 531-532; verificato sui dati).
- **R-1.3** Pesate rimesse in coda (`PSP_DATA_ESTRAZIONE_DWH = 0`) se il loro carico è pendente (R 241-243).
- **R-1.4** `WL1_PESATE` = pesate in coda **agganciate** alle righe del giro su (carico, bolla=`PSP_NUMBOL`,
  ordine=`PSP_NCOM`, radice, variante); data bolla esclusa dal match dal 20081020 (R 919-940).
- **R-1.5** Timbro a fine giro `YYYYMMDDHHMI`: testate **solo se hanno pesate in coda** (modifica 20220228, R 611-613);
  **tutte** le pesate in coda, anche quelle non agganciate, che così si perdono (R 966-967).
- **R-1.6** Esclusione per incongruenza: se Σ pezzi righe ≠ Σ colli×pz pesate per (giorno, carico, articolo), testata e
  pesate marcate `= 1` ed escluse per sempre, con mail (R 266-361). Nei dati set-ott 2026: **mai scattata** (0 marcatori).

## 2. CDT_ESTR.V_CARICO_ORDINARIO → grana del fatto
- **R-2.1** Join tutte INNER (V 88-98): t⋈r su (sito, carico, data, **ordine**); p⋈r su (sito, carico, **bolla**, ordine,
  radice+variante). Nessun carico senza pesata; nessuna riconciliazione bolla/ordine. Filtro `data_carico >= 20061201` (V 103).
- **R-2.2** r = righe aggregate per (sito, carico, data, ordine, MSI, radice, variante, bolla), MAX su ora/date/imballi,
  MIN ricevitore (V 55-84). **Grana = una riga per accoppiamento pesata × gruppo-righe**, di fatto etichetta × bolla.
- **R-2.3** Stato della pesata = quello letto **nel giro** in cui è stata consumata. Se poi cambia in Logistix (es.
  etichetta rinumerata) il legacy tiene il valore vecchio. Criterio per noi: pesata valida se vista per la prima volta
  **entro il giorno di consumo (timbro) della sua testata** (verificato sul nostro bronze: 96840676 vista 19/10 05:31 prima
  del giro delle 07:13; la rinumerata 96841694 vista dal 20/10).
  Implementazione gold: la fotografia "dopo il giro" è il primo giorno di landing **effettivamente caricato** dopo il
  giorno del timbro, non D+1 per definizione (lacuna 31/10–04/11/2026: la fotografia dopo il giro del 31/10 è il 05/11).
- **R-2.4** Formule (V 3-52): `QTA_UF_CARICO = psp_qta_uf_ril`; `QTA_CARICO = nrcolli*pzxcart`; `NUM_IMB_CARICO =
  nrcolli`; `NUM_IMB_FORN_CARICO = qta/DECODE(pz_cart_for,0,1,pz_cart_for)`; `NUM_PLT_CARICO = 1`; `STESSO_IMB_CARICO_FLAG
  = DECODE(pz_cart_for - pz_cartone,0,1,0)`; `NUM_BOLLA_FORN = NVL(r.bolla,'0')` (= `PSP_NUMBOL` per la join);
  `ORA = LPAD(NVL(ora,0),4,'0')`; `FASCIA = SUBSTR(ora,1,2)`; `DATA_SCAD_CARICO = p.psp_data_scadenza`;
  `VAL_COSTO = qta * NVL(stkultstock,0)` (cndstostock outer); PES/VOL = NULL (ricalcolati a valle, "migrato al RAC").
  **Arrotondamento di `VOL_CARICO` in CDT_DW: 2 decimali, mezzo per eccesso** (0,005 → 0,01). Il mapping DW non è
  disponibile; la regola è ricavata dai dati: su set + 1-28/10 (1.317.958 righe) arrotondando così il volume coincide su
  tutte le righe, mentre l'arrotondamento al pari lascia 6.407 righe diverse e il troncamento 161.458.
  `PES_CARICO` coincide già senza arrotondare.

## 3. WL2 → WL4 → T_CARICO (CDT_ESTR)
- **R-3.1** Nessuna dedup: i `MIN(ROWID)` di WL3/WL4 distinguono solo la prima riga del gruppo (sito, ordine, radice,
  variante) per la ripartizione di `QTA_ORD_FORN` (CEIL sulla prima, FLOOR sulle altre, resto sulla prima → Σ gruppo =
  qta ordinata) (E 328-370, 443-474, 668-735). Date JDN → YYYYMMDD; `NVL(ora/oper/bolla,0)` (E 106-152).
- **R-3.2** `GIORNO_SCAD_STOCK_ID` = scadenza stock (WL2_STOCK_DATA_SCAD, outer) altrimenti scadenza carico (E 581, 689).

## 4. CDT_SA.LOAD_F_CARICO_STEP1 (OWB) → scarti in `CDT_SA.E_CARICO`
- **R-4.1** Codici (PKG riga 149-156): 210101 doppi, 210102 sito, **210103 ERRART**, 210104 fornitore, 210106 modello
  peso, 210107 affidabilità tempi, 210108 fascia oraria, 210109 vettore.
- **R-4.2** **ERRART**: articolo cercato nell'anagrafica varianti **storicizzata** `CDT_DW.L_ART_VAR_LOGIS_ST` (staging
  `C$_*`) con `GIORNO_CARICO_ID BETWEEN ART_ST_DATA_INIZ AND ART_ST_DATA_FINE` (ERR 74-76). Riga scartata se nessuna
  versione è valida alla data del carico. Set-ott: 29 righe, 4 carichi, varianti nate il giorno dopo il carico.
  Implementazione gold: finché la tabella è una copia statica, lo scarto si applica solo ai carichi con data ≤ suo ultimo
  aggiornamento (le varianti nate dopo non ci sono e verrebbero scartate a torto).
- **R-4.3** Doppi 210101: riga presente in `V_DOPPI_T_CARICO` su (doc, etichetta, sito, giorno, bolla, radice, variante)
  (ERR 67-82; DDL della vista non disponibile). Lookup INNER su sito, fornitore, fascia, modello peso, affidabilità,
  vettore; OUTER su operatori (ERR 46-66). Affidabilità = banda su giorno carico − consegna prevista (ERR 54-63).
- **R-4.4** Non leggibili (body del package non accessibile): condizioni esatte dei rami 210102/104/106-109.

## 5. CDT_DW
- **R-5.1** `CARICO_INCOMPLETO_FLAG = 1` sulle righe la cui chiave (sito, giorno, doc, ordine) è in `E_CARICO`, 0 se
  non più presente (DW 144-178). Le righe scartate non entrano nel fatto.
- **R-5.2** Corpi non disponibili: `sp_ins_giorno_scad_carico_prec`, `sp_upd_carichi_ord_forn`, `SP_UPD_MAG_SITO_COD`.

## 6. Divergenze decise dal progetto (restano valide)
Colonne esposte, non righe: niente `ART_COD`/`ART_ST_*` (07, 08); chiavi naturali con fallback -1/ND (ADR-0008);
`VAL_COSTO_CARICO` e `QTA_ORD_FORN` **rimosse** dal fatto (decisione SAL, [[ADR-0029]]; supera OP-CAR-1/OP-CAR-3) — le regole
R-2.4 (VAL_COSTO) e R-3.1 (ripartizione QTA_ORD_FORN) restano documentate ma fuori perimetro; GG_* diagnostici aggiunti,
altri esclusi (ACT_9031); rinomina vettore (ADR-0028). Da superare con ACT_9038 (righe): testata per carico invece che
per ordine (ACT_9033), riconciliazione ACT_9035, filtro anti over-split ACT_9037, dedup per chiave in estrazione.

## 7. Incoerenze di documentazione da sanare (rilevate 2026-10-30)
Intestazione `silver_prep_carico` non allineata al codice; mappa colonne (`NUM_BOLLA_FORN`, `CORRIERE_*`, NULLIF);
grana descritta come "riga dettaglio" (07:32, 07:132, gold_f_carico:6); chiave 3 vs 4 colonne (ACT_9029:63, mappa:18,
ACT_9032:78 vs ADR-0006:18); `MIN(ROWID)` descritto come dedup (Revisione:60/75/258, 07:138); VAL_COSTO in 4 versioni
(07:57/121, ACT_9029:109, ACT_9032:105, codice); 09_runbook (CDT_DW indipendente dalla pesata, OP-CAR-3 = 0); LL-034 non
aggiornata per la chiave pesata con bolla; possibile perdita di giorni / GG_* NULL in `gold_late_arriving_handler`
(:42, :60-62, :86-90 — da verificare).
