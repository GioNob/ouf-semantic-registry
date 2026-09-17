# R2c — evidenze di pubblicazione governata e replay storico

Esito: 36 verifiche PASS. Quattro processi owner reali (Semantic, Onboarding, Ingestion, UDP), PostgreSQL/PostGIS e MinIO. Provider esterno, Gateway e identità sono fixture dichiarate.

Discovery → adozione DRAFT → versione esplicita → validazione → approvazione umana di laboratorio → pubblicazione → configurazione Onboarding → acquisizione → serving autorizzato. Un cambio ACTIVE durante consegne pendenti non modifica gli snapshot. Il replay UDP riproduce il vecchio handoff con la vecchia configurazione mentre v2 è attiva, verificando i byte originali, senza duplicare gli oggetti.

## Evidenze CI

| Repository | Run | Esito |
|---|---|---|
| ouf-semantic-registry | [35192761636](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35192761636) | success |
| ouf-semantic-registry | [35192761608](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35192761608) | success |
| ouf-source-onboarding | [35192787801](https://github.com/GioNob/ouf-source-onboarding/actions/runs/35192787801) | success |
| ouf-udp-object-resolution | [35193233762](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35193233762) | success |
| ouf-udp-object-resolution | [35193233691](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35193233691) | success |
| ouf-ingestion-runtime | [35193378609](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35193378609) | success |
| ouf-ingestion-runtime | [35193378596](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35193378596) | success |
| ouf-ingestion-runtime | [35193378584](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35193378584) | success |
| ouf-ingestion-runtime | [35193378765](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35193378765) | success |
| ouf-ingestion-runtime | [35193378601](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35193378601) | success |

## Identità dei commit

Head Ingestion: `22dc923edafccb068cc003c6a1281e2574d49c40`. Il processo della prova PR esegue il merge sintetico `e0e10b537ac4c67462141fa32c259f18c606a3f0`, distinto dal merge effettivo su main.
- publisherCommit: `c176caa5e4d1b8e2ea273bfae05916a390e76569`
- udpCommit: `a19d5447c8db0a2a8ae556ceae7a5225fa975f5b`
- semanticCommit: `cfef6777ff14c218182c06682c6663840437d3d2`

Artifact ID e digest sono nel registro JSON. Le fixture restano escluse dai JAR di produzione.

## Verifica umana e limiti

Persona: operatore/lettore comunale autorizzato. Obiettivo: cambiare configurazione mantenendo spiegabili e riproducibili i risultati precedenti. Superficie verificata: API di consultazione, lineage e governance replay; il browser THS resta da integrare. I campi riservati non compaiono al lettore privo di autorizzazione.

Questa evidenza non chiude REPRODUCE/REPROCESS dei raw in quarantena Ingestion (R3/ING-01), IAM/THS/APISIX reali, tutti gli owner storici o la piena acceptance PET. Nessun gruppo PET viene chiuso automaticamente dalla sola CI. La prova live schema.gov.it resta separata dalla fixture deterministica di questo scenario.

La roadmap incorpora R2d/R2e GIS: CRS comunale configurabile, decisione converti/rigetta versionata anche per fonti dinamiche, grigliati verificati e tracciabili; scenario telecamere/armadi con identità e relazioni visibili all’operatore.
