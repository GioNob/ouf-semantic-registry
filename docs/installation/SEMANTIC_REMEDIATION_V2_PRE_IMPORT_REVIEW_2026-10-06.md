# Revisione prima dell'importazione v2 — 6 ottobre 2026

Qualificazione byte e verifica crittografica VPS PASS secondo gli output forniti dall'operatore alle 13:43:48 e 13:49:47 Europe/Rome. [Receipt delle firme](/docs/handoffs/receipts/SEMANTIC_REMEDIATION_V2_TARGET_CRYPTO_2026-10-06_OPERATOR.json). Le due immagini e i tre documenti nativi hanno firme di provenienza verificate; due SBOM hanno firme verificate. Repository, workflow, merge produttore e ref sono fissati. I risultati completi sono conservati in /home/oufadmin/ouf-crypto-v2.zjJNdo. La receipt byte originale rimane immutata: il suo targetAttestationCryptoVerified=false descrive quella fase precedente.

## Conclusioni della lettura dei sorgenti

| Controllo | Prova disponibile | Stato |
|---|---|---|
| Byte degli archivi e inventario supplementare | ZIP intero e archivi verificati; supplemento ricalcolato dai medesimi byte | PASS |
| Identità del builder | Cinque provenance e due SBOM verificate sul VPS con gh 2.102.0 | PASS operatore |
| Soglia scanner | Adapter, southbound e supplemento nativo: 0 Critical/High/Unknown, DB fissato | PASS per quel DB |
| Inventario nativo | Tutti i 17 ELF del prefisso /usr/local/openresty identificati | PASS entro quel prefisso |
| Copertura di tutte le dipendenze | Syft originale e supplemento separato; confronto completo runtime/sorgenti ancora da documentare | Aperto |
| Accettazione dei componenti custom | OpenResty e zlib non rilasciati; port delle patch; PCRE ereditato; chiave APK di build fixture | Aperto |
| Funzionalità Wasm | Esclusa dalla compilazione del candidato, scelta esplicita nel lock | Valutazione funzionale aperta |
| Dossier dei nuovi digest | Lo stager gateway corrente riusa obbligatoriamente l'immagine del gateway live | Percorso per i nuovi digest da preparare |

La funzione supplement in tools/supplement_semantic_rebuilt_native_sbom.py registra otto componenti e i sette moduli nel lock. L'uguaglianza covered==actual dimostra copertura degli ELF osservati nel prefisso, non automaticamente la copertura di ogni modulo statico, dipendenza Lua/Python o ELF esterno al prefisso. I 45 archivi sorgente fissati non sono, da soli, una SBOM dei soli componenti effettivamente installati. Occorre confrontare il contenuto delle SBOM, le sorgenti incorporate e le opzioni di compilazione, evitando sia componenti mancanti sia componenti scaricati ma non installati.

Dockerfile.semantic-provider-source-fixed introduce una chiave APK generata nel builder per il package zlib custom. La firma della build prova il builder e i byte; non trasforma quella chiave in un publisher approvato. Dockerfile.semantic-southbound-source-fixed e tests/semantic-native-runtime-sources.json dichiarano i commit upstream non rilasciati e l'omissione Wasm. Questi dati devono restare espliciti nella revisione custom.

Nel gateway fissato c0b1f97bdb1fbcd6a88117dea6520ea9c322f265, scripts/stage_semantic_provider_candidates.py imposta southbound.image=gateway_image['Id'] e verifica l'identità del gateway live. Lo ZIP v2 non deve essere forzato dentro quel percorso né sostituire il gateway live per soddisfarlo. Serve un dossier e un percorso di staging isolato coerente coi nuovi digest, preservando gli stager e candidati storici.

## Prossimo passo concreto

Leggere i riepiloghi delle SBOM e del manifesto sorgente già conservati nello snapshot v2. La lettura non avvia scanner o container. Poi completare la matrice di copertura e progettare il percorso isolato per i nuovi digest. Nessuna importazione/registrazione/start eseguita o autorizzata da questa revisione. Publisher trust, dependencyCoverageAccepted, acceptance e start restano false.

Il DB corrente scade il 7 ottobre 2026 alle 08:45:38 Europe/Rome; un eventuale nuovo bundle deve avere scansione e pin freschi, senza bypass. Gate 48 storico, gate 49 aperto, candidati fermati, Cinema/Teatri e il distinto HTTP503 restano preservati.
