# Dalla filiera file → MCP → UDP al ramo Semantic Discovery

## Obiettivo e collegamento verificato sui PET

L'obiettivo concordato resta il percorso file/staging → profiling → chatbot/MCP e mapping Onboarding → decisioni THS → bundle ACTIVE → Ingestion/RAW/handoff → UDP Object Resolution/materializzazione → serving autorizzato. Riusare file, receipt, correzioni e prove esistenti; nessun replay Cinema/Teatri o nuova fonte per comodità.

La ricerca interna in Semantic deve essere autosufficiente. La discovery esterna è un ramo on demand: assenza di un artefatto ACTIVE adeguato **oppure richiesta esplicita di un utente autorizzato**. Non è una dipendenza universale di ogni ingestion. Il gap irrisolto blocca la porzione di mapping che lo richiede; l'eventuale blocco dell'intera fonte dipende dalla policy.

## Responsabilità e riferimenti normativi

| Responsabilità | Owner e confine | PET riletti |
| --- | --- | --- |
| Analisi, confronto candidati, spiegazioni, proposte di mapping e richiesta di discovery | Chatbot/Agent esterno tramite capability MCP tipizzate; niente SPARQL arbitrario o credenziali HUMAN | MCP v1.4, executive boundary e catalogo semantic.discovery.request / source.semantic.mapping.propose; Onboarding v1.6 §§12–13 |
| Search interna, richiesta/worker discovery, provider orchestration, normalizzazione candidati | Semantic/Registry; provider adapter esegue il meccanismo configurato | Semantic v1.3 §§10–11,17–18,26.1–26.4 |
| Trasporto verso provider esterni | Semantic → Gateway southbound → provider autorizzato; Gateway governa autenticazione, allowlist, TLS, limiti e audit | Semantic §25; Gateway v1.5 confini northbound/southbound |
| Mapping specifico della fonte, gap/resume e configurazione | Onboarding; proposta distinta dal valore approvato, riferimento utilizzabile solo dopo pubblicazione/ACTIVE | Onboarding §§9.3,12–13,92–92.2; Semantic §18 |
| Adozione/pubblicazione semantica e approval/activation del mapping | HUMAN_USER autorizzato tramite THS; backend owner rivalida contenuto, stato e policy | Semantic §§9.2,20,74–75; MCP catalogo TRUSTED_HUMAN_ONLY |
| Applicazione del bundle e risultati urbani | Ingestion e UDP; nessun trasferimento di queste responsabilità al Gateway/MCP | Onboarding §92; sprint acquisizione → UDP |

**Configurazione approvata dall'utente il 4 ottobre:** provider predefinito `schema.gov.it`, modificabile nella singola installazione, per esempio `schema.maggioli.it`. È una scelta di default del prodotto, non l'affermazione che i PET impongano un unico provider a tutti gli Enti. Semantic §17 richiede adapter estendibili e §26.2 configura trust level, tipi, meccanismo e rete. §26.3 distingue canonical URI w3id, catalogo/discovery, SPARQL ufficiale **se disponibile e configurato**, content negotiation e fallback tecnico Git revision-pinned. Host predefinito non determina un URL SPARQL completo né le credenziali. L'adapter compila richieste determinate/bounded dal bisogno semantico; il chatbot non invia query libere.

Ogni Ente ha una installazione indipendente; servizi distribuiti o co-localizzati sono supportati. Modificare il provider richiede configurare coerentemente endpoint, TLS, authority applicabile, allowlist/DNS/lease; nessun wildcard o egress indiscriminato.

## Perché il lavoro corrente riguarda il deploy

Il ramo provider risultava disabled/non connesso. La preparazione ha portato alla creazione di candidati fermi; il guard `RUNTIME_EMPTY/EMPTY_ONLY` mantiene provider sets vuoti. Per arrivare a provider admission servono enforcement anche sulle interfacce condivise, coordinazione guard/lease, identità/trasporto e avvio governato. Le automazioni rendono ripetibili questi passaggi per ogni installazione; non chiudono il percorso funzionale MCP → UDP.

I PET impongono i confini di governance e trasporto. Guard/lease, hook OCI, journal a due fasi e firme detached sono **scelte implementative** versionate per rispettare quei confini, non requisiti crittografici letterali dei PET. Il lavoro si è esteso dal collegamento funzionale alla messa in esercizio ripetibile del ramo provider. Questo nesso doveva essere tracciato più chiaramente; non tutte le attività generali di deployment sono necessarie al percorso interno.

## Checkpoint e criterio di uscita

§26 ESEGUITO/PASS: OpenSSL 3.5.7 sul VPS verifica il vettore pubblico valido e respinge le due alterazioni; custody dei 18 sorgenti PASS. Non prova authority, atomicità, runtime o startup.

Prossimo intervento §27: soltanto package v5 dei sorgenti del verificatore, NON ESEGUITO. Poi broker/issuer/attestor reali, mandato/public trust keys espliciti per la singola installazione, acceptance completa di immagine/OCI/rootfs e namespace, guard/lease e startup autorizzato. Provider admission deve verificare OIDC/purpose/TLS/revoca e connettività governata sul target; real reboot/atomic snapshot e gate ereditati restano separati e tracciati. Nessuna firma valida attribuisce autorità applicativa o prova la veridicità delle claim di un attestor.

Il ramo si ricongiunge allo sprint quando il provider necessario può essere invocato governatamente e restituisce candidati compatibili; chatbot/MCP propone, THS governa adozione/pubblicazione, Onboarding riprende su ACTIVE, Ingestion/UDP completano il ciclo. Riusare il file già caricato. Nessun nuovo modulo, ampliamento del deploy generale o rifacimento dei passi provati senza una dipendenza concreta.

## Fonte della verifica

Baseline allegata `OUF_Reality_Baseline_Package_v1_7(20261003-142932).zip`, SHA256 `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`. Riletti testo e originali DOCX: Semantic Model Registry v1.3, Source Onboarding Configuration THS v1.6, MCP Server v1.4; confini Gateway v1.5. Default provider e installazioni indipendenti sono decisioni utente, riportate distintamente dai PET. Nessuna specifica universale nuova è dedotta dalle fixture.
