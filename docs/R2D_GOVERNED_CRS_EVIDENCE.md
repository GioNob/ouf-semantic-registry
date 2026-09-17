# R2d — evidenze delle fondazioni geografiche

Autorità normativa: Reality Baseline Package v1.7, PET UDP v1.3 §29.1, Onboarding v1.6 ONB-A11, Ingestion v1.3 §68 e ING-A09. Le decisioni GIS concordate con il committente integrano la roadmap; il codice non sostituisce i PET.

## Risultato e accettazione umana

Persona: operatore comunale che approva una fonte geografica e lettore autorizzato degli oggetti acquisiti. Obiettivo: scegliere consapevolmente se convertire o rigettare coordinate incompatibili e verificare CRS, risultato e provenienza.

Superfici disponibili: risposta della scheda THS owner Onboarding, profilo pubblicato, lettura owner UDP e stato persistito del job/issue. La scheda contiene `spatialDecision` e `spatialDecisionFindings`, con assi, CONVERT/REJECT, operazioni, accuratezza dichiarata o ignota, area, controlli e risorse. Conferma HUMAN_USER obbligatoria; hash della configurazione e pubblicazione congelano anche questa scelta. Un agente non può confermarla o modificarla dopo l'approvazione.

UDP conserva geometria canonica nel CRS comunale configurabile, originale CRS-tagged e trasformazione; espone separatamente la rappresentazione EPSG:4326 per le query esistenti. Canonico, serving e provenance sono soggetti allo stesso permesso geometrico e label. La geometria rigettata o non trasformabile mette il job in quarantena prima di creare l'Urban Object. La scelta della fonte dinamica rimane valida nel profilo: cambi di CRS, motore o risorse non vengono accettati implicitamente.

La UI di anteprima/importazione e navigazione cartografica è R4a. La remediation e le proiezioni operative complete sono R3. Questa evidenza non dichiara già consegnato quel percorso umano integrato.

## Codice e prove

- UDP PR [#28](https://github.com/GioNob/ouf-udp-object-resolution/pull/28): migrazione V20 compatibile con revisioni storiche; CRS, operazioni esplicite, controllo assi/area/punti; originale e provenienza; ciclo automatico; serving autorizzato; wrapper PostGIS e mount read-only del manifest nel chart.
- Onboarding PR [#15](https://github.com/GioNob/ouf-source-onboarding/pull/15): validazione del profilo e riepilogo della scelta nel contesto umano, con prova dell'approvazione e della pubblicazione immutabile.
- Procedura operativa e contratto: [R2D_GOVERNED_CRS.md](https://github.com/GioNob/ouf-udp-object-resolution/blob/main/docs/R2D_GOVERNED_CRS.md).

La CI dedicata esegue **14 test runtime senza skip**, comprendenti 7 test di trasformazione, 6 di materializzazione/serving/loop (4 preesistenti) e 1 su grigliato realmente letto da PROJ. Due verifiche Python controllano l'inventario; Onboarding aggiunge due test di validazione e uno del percorso approvazione→pubblicazione. Le CI complete verificano anche SDK/autorizzazione, packaging, prestazioni, ripristino e deployment.

Il caso EPSG:6708 verifica la proiezione GRS80 e l'ordine N,E dell'input; un secondo caso usa 32631 per provare che il Comune non è codificato nel programma. I punti di controllo della proiezione UTM31 sono confrontati con [l'esempio ufficiale PostGIS](https://postgis.net/docs/ST_TransformPipeline.html). Il test 6708 usa il meridiano centrale e distingue esplicitamente la successiva assunzione di equivalenza RDN2008/WGS84 per il solo serving della fixture, con accuratezza ignota.

Il test della griglia usa un **NTv2 sintetico** con spostamento costante noto: prova esecuzione effettiva, checksum e pinning; non è una trasformazione geodetica utilizzabile sul territorio. L'avvio del database fallisce con file obbligatorio assente. Il runtime rifiuta risorse/versione diverse, controlli non superati, operazioni fuori area e fallback opzionali. Il test del ciclo automatico usa resolver dei profili e gate delle referenze simulati; database, stato job, trasformazioni e materializzatori sono reali. Non è ancora la catena GeoPackage fra tutti gli owner.

Un primo job di disaster recovery sulla PR ha fallito perché la porta host fissa 55432 era occupata. Lo script ora lascia assegnare a Docker le porte PostgreSQL e usa quelle effettive. Il failure rimane distinguibile dalle evidenze verdi finali.

## Limiti che restano aperti

1. Nessun grigliato IGM/locale è stato fornito, licenziato o collaudato su punti reali di Trieste. Per la coppia CRS e il territorio effettivi servono risorse utilizzabili legittimamente, metadata, checksum e controlli territoriali indipendenti.
2. I controlli attestano l'esecuzione dell'operazione scelta; non certificano l'accuratezza geodetica. L'operatore deve vedere e approvare eventuali approssimazioni, separate fra canonico e serving. Nessuna promessa di precisione centimetrica.
3. Supporto a geometrie 2D; quote, epoche/CRS dinamici e geocodifica non sono inclusi. Nessun riparo geometrico automatico.
4. Il CRS è configurabile per il deployment comunale/tenant attuale; un registro multi-tenant dinamico non è incluso. Per cambiare il CRS di un Comune già popolato occorre pianificare una nuova materializzazione: V20 non trasforma retroattivamente le revisioni storiche.
5. GeoPackage e altri parser GIS, identità stabile per feature e relazioni telecamere↔armadi restano R2e; formati ulteriori R4b. L'approvazione non rende da sola un adapter capace di leggere quei formati.
6. Gateway/IAM/THS reali e acceptance completa restano i rispettivi gate. Nessun gruppo generale PET è chiuso per effetto di questa sola evidenza.

Stato dei commit e delle CI finali: tabella seguente e sezione `r2d` del registro JSON. I digest degli artifact sono metadata GitHub, non checksum ricalcolati scaricando gli archivi.

| Owner | Commit finale verificato | Merge su main |
|---|---|---|
| udp | `4996b345a17536bb1205684f7742e0f735301dae` | `ca3039da36313691c93d6333be4760bc4a760430` |
| onboarding | `823ecc90c2186225f4e88452891af1d14e6613e7` | `584692a4fe3c07ff2d5acc6191e931c66799bbc6` |

| CI sul commit finale | Esito |
|---|---|
| [ouf-udp-object-resolution / 35197306772](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35197306772) | PASS |
| [ouf-udp-object-resolution / 35197306808](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35197306808) | PASS |
| [ouf-source-onboarding / 35197042345](https://github.com/GioNob/ouf-source-onboarding/actions/runs/35197042345) | PASS |
| [ouf-udp-object-resolution / 35197306649](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35197306649) | PASS |

