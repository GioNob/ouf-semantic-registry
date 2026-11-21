# POI-AP_IT

«Ontologia dei Punti di Interesse – Profilo applicativo italiano», versione 0.3 del 23 aprile 2019. Gli autori sono l'Agenzia per l'Italia Digitale (AgID) e STLab del CNR. AgID è editore e titolare dei diritti. La fixture riproduce il Turtle originale. [OntoPiA, italia/dati-semantic-assets](https://github.com/italia/dati-semantic-assets/blob/master/Ontologie/POI/latest/POI-AP_IT.ttl) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

Il test genera in memoria cinque descrizioni Turtle dalle sole triple con la classe come soggetto. È la proiezione `CONSTRUCT { <risorsa> ?p ?o } WHERE { <risorsa> ?p ?o }` di `SchemaGovProxy.fetch`. I nodi anonimi restano oggetti delle triple. Le descrizioni sono ricostruzioni dalla fixture.

La prova D-079 usa per `PointOfInterest` i byte effettivamente restituiti da schema.gov.it il 21 novembre 2026, conservati in `fetched/PointOfInterest.ttl`. Il gateway di test serve separatamente l’intestazione ottenuta dalle triple di `POI-AP_IT.ttl` che hanno l’IRI dell’ontologia come soggetto. Anche l’estratto della classe è attribuito ad AgID e STLab del CNR con licenza [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
