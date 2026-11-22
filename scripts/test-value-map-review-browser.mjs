import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { URL, fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const chrome = process.env.CHROME_BIN ?? (process.platform === 'win32'
  ? 'C:/Program Files/Google/Chrome/Application/chrome.exe' : 'google-chrome');
const target = join(root, 'target');
if (!existsSync(target)) mkdirSync(target);
const scratch = mkdtempSync(join(target, 'value-map-browser-'));
assert.equal(dirname(scratch), target);
const source = name => readFileSync(join(root, 'src/main/resources/ths', name), 'utf8');
try {
  const page = join(scratch, 'review.html');
  writeFileSync(page, `<!doctype html><html lang="it"><meta charset="utf-8">
    <style>iframe { width:375px; height:580px; border:0; }</style>
    <iframe title="Scheda a 375 px"></iframe><p id="evidence">PENDING</p>
    <script>
      const frame = document.querySelector('iframe');
      const doc = frame.contentDocument;
      const style = doc.createElement('style');
      style.textContent = ${JSON.stringify(source('value-map-review.css'))};
      doc.head.append(style);
      ${source('value-map-review.js')}
      const concept = {etichetta:'Biblioteca', identificativo:'https://example.org/' + 'term'.repeat(120)};
      const vocabulary = {etichetta:'Servizi', identificativo:'https://example.org/vocabolari/servizi'};
      const literal = '<img src=x onerror=alert(1)>';
      const rows = Array.from({length:2000}, (_,i) => ({codice:i === 0 ? literal : 'codice-' + i, concetto:concept}));
      const diff = [{codice:'A', modifica:'Aggiunto', dopo:concept},
        {codice:'R', modifica:'Rimosso', prima:concept},
        {codice:'M', modifica:'Modificato', prima:concept, dopo:{...concept, etichetta:'Archivio'}}];
      function check(condition, message) { if (!condition) throw new Error(message); }
      const evidence = document.querySelector('#evidence');
      try {
        const card = renderValueMapReview({nome:'Mappa servizi', vocabolario:vocabulary, numeroVoci:rows.length,
          colonnaSorgente:'servizio_codice', voci:rows, versionePrecedente:'1.0.0', differenze:diff}, doc.body);
        const [table, delta] = card.querySelectorAll('table');
        const [previous, next] = card.querySelectorAll('button');
        check(doc.defaultView.innerWidth === 375, 'viewport');
        check(doc.documentElement.scrollWidth <= 375, 'overflow');
        check(card.textContent.includes('Mappa servizi') && card.textContent.includes('2000'), 'name and count');
        check(card.textContent.includes(vocabulary.identificativo) && card.textContent.includes('Servizi'), 'vocabulary');
        check(card.textContent.includes('Colonna sorgente') && card.textContent.includes('servizio_codice'), 'source column');
        check(card.textContent.includes(concept.identificativo) && card.textContent.includes('Biblioteca'), 'concept');
        check(table.tBodies[0].rows[0].textContent.includes(literal) && !card.querySelector('img'), 'literal text');
        check(table.tBodies[0].rows.length === 25 && previous.disabled, 'first page');
        check(delta.textContent.includes('Aggiunto') && delta.textContent.includes('Rimosso')
          && delta.textContent.includes('Modificato') && delta.textContent.includes('Archivio'), 'diff');
        for (let i = 1; i < 80; i++) next.click();
        check(next.disabled && table.tBodies[0].rows[24].textContent.includes('codice-1999'), 'last page');
        previous.click();
        check(!next.disabled && table.tBodies[0].rows[0].textContent.includes('codice-1950'), 'previous page');
        evidence.textContent = 'PET-semantic-104 VALUE_MAP 375px PASS';
      } catch (error) { evidence.textContent = error.message; }
    </script>`);
  const result = spawnSync(chrome, [
    '--headless', '--disable-gpu', '--disable-background-networking', '--disable-component-update',
    '--disable-sync', '--no-first-run', '--no-default-browser-check', '--no-proxy-server',
    '--host-resolver-rules=MAP * ~NOTFOUND', '--disable-crash-reporter',
    // The local Windows runner denies Chrome child-process sandbox setup.
    ...(process.platform === 'win32' ? ['--no-sandbox'] : []),
    '--dump-dom', '--user-data-dir=' + join(scratch, 'profile'), pathToFileURL(page).href,
  ], { encoding:'utf8', timeout:35000, maxBuffer:1048576 });
  if (result.error) throw result.error;
  assert.equal(result.status, 0, result.stderr);
  const evidence = result.stdout.match(/<p id="evidence">([^<]*)<\/p>/)?.[1];
  assert.equal(evidence, 'PET-semantic-104 VALUE_MAP 375px PASS');
  console.log(evidence);
} finally {
  rmSync(scratch, { recursive:true, force:true, maxRetries:3, retryDelay:100 });
}
