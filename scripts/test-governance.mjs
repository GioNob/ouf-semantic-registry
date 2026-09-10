import EmbeddedPostgres from '../../semantic_concrete_work/lab/node_modules/embedded-postgres/dist/index.js';
import pgModule from '../../semantic_concrete_work/lab/node_modules/pg/lib/index.js';
import {readFile} from 'node:fs/promises';
import crypto from 'node:crypto';
const {Client}=pgModule, port=55453, dir=`/tmp/ouf-sem-${process.pid}`;
const pg=new EmbeddedPostgres({databaseDir:dir,user:'postgres',password:'postgres',port,persistent:false,initdbFlags:['--encoding=UTF8','--locale=C'],postgresFlags:['-F','-c','unix_socket_directories=','-c','fsync=off'],onLog:()=>{}});
const cfg={host:'127.0.0.1',port,user:'postgres',password:'postgres',database:'postgres'};
const id=()=>crypto.randomUUID(),hash=()=>crypto.randomBytes(32).toString('hex');
function assert(v,m){if(!v)throw Error(m)}
try{
 await pg.initialise();await pg.start();const c=new Client(cfg);await c.connect();
 await c.query(await readFile(new URL('../src/main/resources/db/migration/V1__semantic_registry.sql',import.meta.url),'utf8'));
 await c.query(await readFile(new URL('../src/main/resources/db/migration/V2__governed_publication.sql',import.meta.url),'utf8'));
 const a=id(),r=id(),ch=id(),dec=id(),h=hash();
 await c.query(`insert into ouf_sem.semantic_artifact values($1,'ouf:Place','CLASS','ouf','Place','dept','city','OUF',now(),null)`,[a]);
 await c.query(`insert into ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,lifecycle_status,content_hash,created_by_subject) values($1,$2,1,'UNDER_REVIEW',$3,'human')`,[r,a,h]);
 await c.query(`insert into ouf_sem.approval_challenge(challenge_id,revision_id,target_content_hash,status,expires_at,created_by_subject) values($1,$2,$3,'APPROVED',now()+interval '5 min','human')`,[ch,r,h]);
 await c.query(`insert into ouf_sem.approval_decision(decision_id,challenge_id,decision,target_content_hash,decided_by_subject) values($1,$2,'APPROVED',$3,'human')`,[dec,ch,h]);
 const set=(await c.query(`select ouf_sem.publish_revision($1,$2,'key-1',$3,'human','corr-1') id`,[r,dec,h])).rows[0].id;
 const replay=(await c.query(`select ouf_sem.publish_revision($1,$2,'key-1',$3,'human','corr-1') id`,[r,dec,h])).rows[0].id;
 assert(set===replay,'replay is not idempotent');
 assert((await c.query(`select count(*)::int n from ouf_sem.semantic_publication_member where publication_set_id=$1`,[set])).rows[0].n===1,'manifest incomplete');
 assert((await c.query(`select count(*)::int n from ouf_sem.audit_event where resource_id=$1`,[r])).rows[0].n===1,'audit missing');
 let conflict=false;try{await c.query(`select ouf_sem.publish_revision($1,$2,'key-1',$3,'human','corr-2')`,[r,dec,hash()])}catch(e){conflict=e.code==='23505'}assert(conflict,'payload conflict not rejected');
 let immutable=false;try{await c.query(`update ouf_sem.approval_decision set decision='REJECTED' where decision_id=$1`,[dec])}catch(e){immutable=e.code==='23001'}assert(immutable,'decision mutated');
 console.log(JSON.stringify({status:'PASS',database:(await c.query('select version() v')).rows[0].v,checks:['migrations','approved publication','atomic manifest','idempotent replay','conflict rejection','append-only decision','audit event']},null,2));
 await c.end();
}finally{await pg.stop().catch(()=>{})}
