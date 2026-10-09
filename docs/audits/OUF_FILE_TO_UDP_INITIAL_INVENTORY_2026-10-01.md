# OUF — inventario iniziale file → UDP, 2026-10-01
Checkpoint: 20:54 Europe/Rome. Stato: analisi sorgente e contratti; nessun rollout o nuova esecuzione dati.

## Baseline normativa e continuità

Pacchetto allegato in questa chat: `OUF_Reality_Baseline_Package_v1_7(20261001-185201).zip`.
SHA-256 archivio: `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`.
Verifica SHA256SUMS: 323 file verificati, zero mismatch.
L0 Cross-Module Alignment Matrix v1.7 e README_PACKAGE_STATUS consultati.
L1 consultati per questo inventario: Semantic v1.3 §§9.2,10–11,17–19; Onboarding v1.6 §§92–92.2 e THS-03/04/07; MCP v1.4 capability table e §22; UDP v1.3 §§21–22,109.2,109.6–109.9; Authorization v1.5 §36.10; Gateway v1.5 confini channel-neutral e deployment.

Autorizzazione utente permanente per lettura/scrittura nei repository OUF durante la chat. Decisioni HUMAN autoritative restano THS. PET da consultare nuovamente a ogni sprint; questa matrice non li sostituisce. Nessuna nuova norma derivata dalle fixture.

[Handoff completo e registro dei gate ereditati](../handoffs/OUF_HANDOFF_2026-10-01_FILE_TO_UDP_NEXT_SPRINT.md) restano autorità di continuità. Cinema 8/8 è prova storica delivery/materialization, non nuova verifica live. Teatri rimane asset `6609b245-86ed-4315-8ce0-73f2a8555bf3`, profile `7984c39c-7396-4248-ab0a-f2efc390b49c` v1: nessuna nuova DRAFT, approvazione, run o materializzazione eseguita in questa ripresa.

## Matrice passo / contratto / prova / collegamento

| Passo e owner | Contratto/API da riusare | Pin o prova acquisita | Collegamento e prova mancanti |
| --- | --- | --- | --- |
| Managed upload/profile — Onboarding/Gateway | ManagedFileAsset, FileProfile, source.file.preview | Upload/profile Teatri MCP PASS ereditato; Onboarding live f74c3a9f… secondo manuale | Readback corrente del medesimo profile con account scelto dal connector; acceptance negative/streaming ereditate OPEN |
| Ricerca interna — Semantic | GET /api/semantic/v1/search, ArtifactApi/ArtifactService | Sorgente al be76527ef6d212b40cca2a6a69c0bfa1cd750368 | Ricerca per label/alias/descrizione/tipo/domain/range e risultato sufficiente a proposta; projection MCP bounded e binding Gateway/SDK |
| Lettura semantica — Semantic | GET /artifacts/{id}; GET /references:resolve con semanticId, revisionId, publicationSetId | ValidationService.resolve usa membership exact, senza fallback ACTIVE | Collegare discovery del riferimento completo e lettura della revisione pinned; non equiparare get latest a lettura storica |
| Discovery — Semantic | DiscoveryApi request/candidates/adoption DRAFT/providers; provider port | API e SchemaGovProvider presenti nel tree allo stesso pin | Deployment/provider/egress non verificati; adapter Ontopia non attestato; nessuna query SPARQL arbitraria |
| Proposta mapping — chatbot; persistenza Onboarding | SemanticMapping, source identity, classificazioni, source.onboarding.create | File Teatri già profilato; inferenze non approvate | Mapping motivato con refs ACTIVE/pinned, whitelist transform e CRS/temporal/authority/representation; dubbi da decidere con utente |
| Decisioni — owner/THS | GovernanceApi approval-challenges; source workflow | Endpoint preparazione challenge presente, non prova live | Challenge/link, esito persistito, ripresa idempotente e negative stale/tenant/scope; nessuna conferma MCP |
| Activation/ingestion — Onboarding/Ingestion | PublishedConfigurationBundle → RAW/lineage/handoff | Cinema source/run e 8 ACKED ereditati | Nuova source soltanto dopo review; monitoraggio nuovo percorso senza retry ambiguo |
| Resolution/materialization — UDP | Intake, reference gate, resolution/recovery | Live pin ereditato 83249a897eb4add4289b5181b3299f48ea4c0f99; image 5e048a…; Flyway34, 8/8 | Teatri E2E e serving non provati; preservare motore class-neutral e regola subset concordata |
| Serving/install — UDP/Gateway/MCP | Search autorizzato; manifest/config/routes/policy | Codice Search presente, prova completa ereditata OPEN | R-SMOKE e R-INSTALL restano OPEN; install/reconcile parametrico e prove portabilità/rollback |

Pin abbreviati nella tabella sono riferimenti di continuità: usare i pin completi negli handoff e nei manifest di release prima di ogni modifica/rollout.

## Gap Semantic osservati nel sorgente

Al pin Semantic `be76527ef6d212b40cca2a6a69c0bfa1cd750368`:
- ArtifactApi.search accetta q/status/limit; limite owner 1–100. ArtifactService.search usa similarity di semantic_id: non ricerca label/alias/descrizione e non offre filtri tipo/domain/range previsti dal PET §10.
- Risultato search: semantic_id, artifact_id, revision_id, status, score. Non contiene label/definition né publication_set_id; non è ancora sufficiente a costruire un riferimento pinned completo.
- ArtifactService.get sceglie ultima revision_no e ritorna metadata ridotti. Non usarlo come lettura della revisione storica pinned.
- ValidationService.resolve verifica esattamente semanticId/revisionId/publicationSetId contro semantic_publication_member; ritorna label e metadata. Il risultato non include definition/domain/range: controllare gli altri endpoint e contratti prima di aggiungere DTO/duplicare servizi.
- DiscoveryApi.providers espone schemaGov. Non prova configurazione, salute live o disponibilità Ontopia.
- GovernanceApi prepara una challenge; approvazione/pubblicazione sono operazioni HUMAN separate.

Questi sono gap d'implementazione/collegamento rispetto a requisiti già espressi nel PET, non nuove scelte di dominio. L'inventario non certifica tutte le API o tutta la conformità Semantic.

## Branch MCP/Gateway: evitare regressioni

Inventario GitHub al checkpoint:
- MCP main `5615fdcad8cbcad9ff41ec3d0ad2ccbf9423c042`: manifest senza semantic.search/get e senza managed file tools.
- MCP attachment `1477794494aa02f8b031bf19e08b1cda99dc0ec9`: manifest con source.file.upload/profile/preview/onboarding.create, senza semantic.search/get.
- MCP object-search `d4bcd46f9fcee4d3fca74e65a7505be1561596f5` e object-search-mcp `496d2f0152b6bddcb7965a57ed796388d6aa1d9f`: manifest con urban.object.search, senza managed file tools e senza semantic.search/get.
- La superficie OUF disponibile in questa chat espone contemporaneamente upload/status/profile/preview/onboarding.create e object search, ma nessun tool Semantic. I manifest esaminati non bastano a identificare la revisione live; controllare loader/overlay e receipt di rollout. Non scegliere main o un branch singolo come base equivalente al deploy.
- Gateway main `dbdc24b5481dc9473b21b360ab1142c9aef0194b`: ouf.semantic.read è ACTIVE, mcp.toolEligible=false. È evidenza di configurazione sorgente di quel branch, non prova delle route/policy live.
- Branch Gateway rilevanti da riconciliare: semantic-human-routes 3014f3c3738ffb1a53971cb46676dd71c119cee3; picker-owner-key-repair 2b1c84c9081898aa305c1eb06e90406994393acd; managed-mcp-installer-fix 66de64b2dc99c4e0b970c59fdc31f819a1a448fd; object-search dbdeeaec954ce3b9c0fa5b2fd4d8b57a9ab51e78.

Nessun accesso SSH diretto verificato in questa ripresa. GitHub lettura riuscita e permessi push dichiarati dal connector; la prima scrittura documentale è registrata nel commit.

## Requisiti per il deploy del collegamento

Per questo deliverable conservare separati codice/contratti e binding d'installazione:
- Release manifest con revisioni, immagini digest-pinned e compatibilità API/schema/consumer; integrare managed-file e search senza perdere fix già provati.
- Configurazione esplicita di tenant/Ente, domini, upstream host/porte/reti/TLS trust, issuer/audience, service principal/client, delegation e scopes, secret refs e route IDs. Nessuno di questi valori è una costante di dominio.
- Catalogo capability canonico e proiezione MCP tipizzata; i nomi tool semantic.search/get e le capability owner ouf.semantic.search/read vanno collegati nel binding, senza assumere identità dei nomi.
- Ricerca bounded e riferimenti exact; discovery interna autonoma rispetto ai provider; provider/endpoint/egress/TTL/timeout configurabili.
- Plan/apply/verify idempotenti, drift fail-closed, intent/readback per esiti incerti, rollback delle sole risorse possedute; preservare snapshot privati e oggetti/DB esistenti.
- Test dei nuovi collegamenti e regressioni esistenti: pin storico/ACTIVE switch, tenant/scope denial, DTO bounded, THS separation, timeout/readback e assenza duplicazioni. CI PASS, rollout e acceptance live sono evidenze distinte.

Questi sono requisiti di completamento, non una dichiarazione che installer o deployment siano già pronti.

## Prossima azione concreta

Riconciliare loader/manifest/baseline deploy MCP e contratti Semantic di lettura completa; poi implementare la consultazione interna governata e i suoi binding installabili, riusando owner esistenti. Con riferimenti ufficiali verificati, preparare mapping dello stesso Teatri e presentare soltanto le decisioni di identità/classificazione effettivamente mancanti. Tutti i gate ereditati rimangono nello handoff; nessuna chiusura per omissione.
