# Allineamento obbligatorio degli sprint ai PET

Il committente ha prescritto la lettura dei PET di **tutti e sette i moduli** del Reality Baseline Package v1.7 e il controllo di allineamento all'avvio di ogni sprint. Questa è una condizione del lavoro, non una verifica facoltativa del solo modulo modificato.

Per R2e sono stati letti integralmente i sette PET e i documenti L0 (Blueprint v0.3, Alignment Matrix v1.7, Supersession Notice v1.1). L'integrità del pacchetto allegato è stata verificata: 323 voci del manifest corrispondono. Il manifest locale delle fonti consultate è `OUF_REALITY_BASELINE_V1_7_REFERENCES.json`; identifica i documenti, non sostituisce la loro lettura.

Prima di ogni sprint:

1. Consultare i documenti normativi del pacchetto indicato dal committente, applicando la precedenza L0 e le integrazioni concordate nella roadmap.
2. Esplicitare responsabilità dei moduli, contratti/versioni, dipendenze, autorizzazioni e limiti coinvolti.
3. Mappare ogni risultato dello sprint a una prova e a una superficie osservabile per la persona interessata.
4. Conservare gli esiti reali, distinguendo fixture, componenti owner, ambiente operativo e accettazione umana completa.
5. Non chiudere un requisito PET generale in base alla sola CI di un incremento. Registrare gli scostamenti e mantenere i gate successivi.

## Applicazione a R2e

| Modulo / PET | Vincolo applicato |
|---|---|
| Source Onboarding & Configuration THS v1.6 | Profilazione deterministica; layer, campi, chiavi, label e decisione CRS approvati; bundle storico immutabile |
| EF Ingestion Runtime v1.3 | Esecuzione del bundle fissato; un record per feature; RAW/provenienza; nessuna scelta di identità canonica o target della relazione |
| Data Lake UDP Urban Object Registry v1.3 | Identità canonica, trasformazione governata, contributi e revisioni; risoluzione relazioni; riconciliazione e serving autorizzato |
| Semantic Model Registry v1.3 | Referenze semantiche pubblicate e versionate; risoluzione della pubblicazione esatta |
| Authorization & Access Control v1.5 | SDK owner, default deny, permessi di fonte/oggetto/proprietà/geometria/relazione/lineage; nessun permesso di lettura implicito nella scrittura |
| Urban API Gateway v1.5 | Confini owner e instradamento governato; la fixture di instradamento della CI non certifica il Gateway operativo |
| MCP Server v1.4 | Nessuna decisione semantica nascosta nel canale; API owner con contratti stabili; nessuna nuova logica di business nel canale MCP |

R2d resta vincolante per CRS e grigliati. R3 mantiene osservabilità e remediation complete; R4a il percorso cartografico umano; R4b gli ulteriori formati/casi GIS. I grigliati IGM reali e il collaudo territoriale non sono attestati da R2e.


## Applicazione a R2f

R2f è un incremento autorizzato dal committente prima di R3. Mantiene come fonti vincolanti i sette PET e L0 identificati sopra; l'analisi mirata dei requisiti multi-fonte e dei formati è in `R2F_MULTISOURCE_AND_MANAGED_FORMATS.md`. Questa nota non attesta una nuova lettura integrale dei sette documenti né un'accettazione operativa.

Le CI dei singoli owner attestano soltanto il codice e gli scenari descritti. Il backend della scelta geometrica è verificato; sono ancora necessari il completamento del workflow umano dei conflitti, confronto cartografico autorizzato e collaudo dei nuovi formati fra owner; non possono essere chiusi dalla presenza di un lettore o da una CI R2e storica. Access usa il percorso INTERNAL_MANAGED: nessuna esecuzione di codice nel file e nessuna TBox pubblicata dal profiler.
