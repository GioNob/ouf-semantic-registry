# Proposta: normalizzazione canonica governata dei valori

Data: 10 novembre 2026. Stato: **proposta dell'owner, non implementata**. Documento di riferimento per quando il tema verrà affrontato; non modifica contratti, codice o configurazioni esistenti e non chiude gap PET.

## 1. Caso che ha originato la proposta

La fonte `teatri-seaweedfs-c51745c5` (asset `c51745c5-1fc0-4d36-bdcf-1e9a8a049c94`, run `2998141c-1a12-48f4-8f8a-e36625d188db`) ha prodotto 13 `resolution_issue` `UNRESOLVED_IDENTITY`. I candidati sono i 13 teatri già materializzati dalla fonte `teatri-csv-6609b245` (asset `6609b245-86ed-4315-8ce0-73f2a8555bf3`). Il file della nuova fonte era passato da un foglio di calcolo con impostazioni italiane:

| campo | fonte precedente | nuova fonte | natura dell'alterazione |
|---|---|---|---|
| latitudine | `45.65751` | `4.565.751` | informazione persa (posizione decimale) |
| longitudine | `13.78939` | `1.378.939` | informazione persa |
| civico | `5/2` | `05-feb` | convertito in data, ambiguo |
| data_verifica | `2026-09-28` | `28/09/2026` | solo formato, convertibile |

Evidenze rilevanti (lettura in sola lettura dei database `ouf_onboarding` e `ouf_udp`):

- Il profilatore aveva già distinto i due file: nella fonte precedente `latitudine`/`longitudine` erano `DECIMAL` e `data_verifica` `DATE`; nella nuova fonte tutte `STRING`. L'informazione non è stata usata né segnalata.
- Il mapping semantico usa `transform: IDENTITY` e proprietà specifiche del dataset (`semantic/teatri#…`) di tipo `xsd:string`; il `canonicalPayload` riporta le stringhe così come sono.
- La regola sufficiente `identity-v1` richiedeva tutti i 20 campi concordi, `data_verifica` compresa, quindi non poteva funzionare tra fonti diverse né tra acquisizioni in tempi diversi.
- L'ordine di autorità della nuova pubblicazione dava precedenza alla nuova fonte su civico, coordinate e data: un collegamento HUMAN avrebbe sovrascritto valori corretti con valori alterati.

UDP si è comportato correttamente mettendo in quarantena. Il difetto sta a monte: nessun punto della catena dichiara né verifica il formato dei valori.

## 2. Decisioni dell'owner

**D1 — Concetti di un vocabolario controllato condiviso.** Ogni colonna viene abbinata a un concetto di un vocabolario controllato condiviso, non a una proprietà specifica del dataset. Prima di creare un concetto nuovo, il sistema propone se la colonna corrisponde a un concetto esistente, per evitare duplicati.

**D2 — Formato canonico non predefinito.** I concetti non nascono con un formato canonico. Quando compare un concetto nuovo, il sistema propone un formato all'attenzione dell'utente.

**D3 — Proposta del chatbot.** La proposta la formula il chatbot. Ordine delle fonti: riferimenti già presenti nel vocabolario controllato; ricerca in rete su fonti autorevoli (W3C, OGC, ISO, AgID, ISTAT, ANNCSU…); best practice. La proposta cita le fonti con link e data; modello, data e fonti consultate vengono registrati come provenienza. Il contenuto web è input non affidabile e l'approvazione resta HUMAN.

**D4 — Catalogo chiuso di operatori.** Un formato è una specifica dichiarativa versionata che compone operatori di un catalogo chiuso implementato nel codice di OUF. Un interprete deterministico la applica: niente compilazione o espressioni arbitrarie a runtime, nessun modello invocato per singolo record. Un caso non esprimibile richiede un nuovo operatore, cioè un rilascio software ordinario. Il chatbot può comporre solo operatori esistenti e la proposta viene validata contro lo schema del catalogo.

**D5 — Catalogo il più esteso possibile** (sezione 4).

**D6 — Grezzo conservato, canonico normalizzato.** Il grezzo resta nel lake con la sua provenienza; il canonico contiene il valore normalizzato. Se la conversione non è deterministica o il risultato non supera la validazione del concetto, il record non entra nel canonico e va in quarantena di qualità con motivo esplicito. Nessuna correzione silenziosa e nessuna riparazione guidata dal valore di un altro oggetto.

**D7 — Prova automatica prima della revisione.** La proposta viene provata sui valori di profilazione (convertiti, rifiutati, esempi) e l'operatore approva vedendo questi risultati.

**D8 — Evoluzione versionata.** Cambiare un formato approvato richiede una nuova versione del concetto e la ri-normalizzazione dal grezzo.

## 3. Trasporto e applicazione

La specifica viaggia come dato di configurazione attraverso il canale esistente: il bundle pubblicato dall'onboarding, già fissato per hash in ogni handoff (`contractRefs.bundleRef`). Il formato sorgente è specifico della fonte (separatori, pattern data, locale); il formato canonico è specifico del concetto. L'ingestion applica l'interprete nel punto in cui costruisce il `canonicalPayload`. Stesso grezzo e stessa versione di specifica producono sempre lo stesso canonico.

Esempio indicativo, non un contratto:

```json
{
  "concept": "latitudine", "conceptVersion": 1,
  "canonical": { "datatype": "xsd:decimal", "crs": "EPSG:4326" },
  "steps": [
    { "op": "trim" },
    { "op": "parse-decimal", "decimalSeparator": ".", "groupSeparator": null },
    { "op": "range", "min": -90, "max": 90 }
  ],
  "onFailure": "QUALITY_QUARANTINE"
}
```

Con questa specifica `4.565.751` fallisce in `parse-decimal` e il record va in quarantena di qualità prima di arrivare a UDP.

## 4. Catalogo operatori: elenco di partenza

Ogni operatore dovrà dichiarare id e versione, tipi in ingresso e uscita, parametri con schema, semantica, codici d'errore, trattamento di null/vuoto/spazi, dipendenza da locale e fuso, garanzia di determinismo, esempi validi e rifiutati. Gli operatori non hanno effetti esterni; le tabelle di riferimento sono artefatti versionati fissati per hash.

- **Testo:** trim, normalizzazione spazi, maiuscole/minuscole, Unicode NFC/NFKC, rimozione diacritici (solo chiavi di confronto), lunghezza, pattern regex con limiti anti-ReDoS, value-map/enumerazione, split/join multi-valore, rimozione caratteri di controllo.
- **Numeri:** decimale con separatori dichiarati, interi, percentuali, notazione scientifica, precisione e arrotondamento, intervallo, unità di misura con conversione (UCUM), rilevamento di numeri convertiti in date dal foglio di calcolo.
- **Date e tempi:** pattern dichiarato (alternative solo se non ambigue), ISO-8601 data/data-ora/durata/intervallo, fuso esplicito, seriali dei fogli di calcolo, date parziali, intervallo plausibile.
- **Geografia:** latitudine/longitudine decimali con intervallo, gradi-minuti-secondi, coppia → punto, WKT/GeoJSON, CRS dichiarato e trasformazione (es. EPSG:3003/3004/6708 → 4326), bounding box di plausibilità, rilevamento coordinate invertite.
- **Indirizzi e territorio italiani:** civico ed esponente secondo ANNCSU, CAP, sigle di provincia, codici ISTAT, codice catastale, normalizzazione del toponimo (DUG).
- **Identificativi:** codice fiscale e partita IVA con checksum, IBAN, codici IPA, UUID, URI/URL, email, telefono E.164.
- **Booleani e nulli:** vero/falso con valori dichiarati, sentinelle di nullo dichiarate.
- **Composizione:** sequenza, alternativa deterministica con priorità, validazione pura, chiave di confronto derivata separata dal valore canonico.

## 5. Punti aperti

- **A1.** L'approvazione del formato è prerequisito per l'attivazione della fonte, oppure un concetto senza formato entra come testo libero senza poter essere segnale d'identità né avere autorità?
- **A2.** La specifica vive nel concetto (condivisa) e/o nel bundle (fissata per hash); come si combinano formato sorgente e formato canonico.
- **A3.** Punto esatto in cui l'ingestion costruisce oggi il `canonicalPayload` e aggancio dell'interprete (da verificare nel codice).
- **A4.** Collocazione e flusso HUMAN della quarantena di qualità (ricaricare la fonte, scartare il record, richiedere un nuovo operatore).
- **A5.** Impatto su UDP: regole d'identità con soli segnali d'identità confrontati su valori canonici; trattamento dei campi descrittivi come `data_verifica`; eventuale nuova versione di `GOVERNED_IDENTITY` e del decoder della policy.
- **A6.** Capability e attori per proposta, approvazione, quarantena di qualità e pubblicazione del catalogo.

## 6. Prossimo passo previsto

Un progetto completo suddiviso in passi singoli (stato verificato con permalink, architettura, catalogo completo, JSON Schema della specifica, flussi di proposta e approvazione, integrazione in ingestion, quarantena di qualità, impatto UDP, versionamento, sicurezza, piano di lavoro in PR revisionabili, caso di accettazione Teatri). Il caso della sezione 1 è il criterio di accettazione: coordinate e civico alterati in quarantena di qualità con motivo esplicito; `28/09/2026` normalizzata in `2026-09-28`; dopo il ricaricamento del file corretto, collegamento ai 13 oggetti storici senza sovrascritture errate.
