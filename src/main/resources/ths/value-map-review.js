'use strict';

function renderValueMapReview(review, parent) {
  const document = parent.ownerDocument;
  const section = node('section', '', parent);
  section.className = 'value-map-review';

  function node(tag, value, container) {
    const element = document.createElement(tag);
    element.textContent = value ?? '';
    container.append(element);
    return element;
  }

  function term(value, container) {
    node('strong', value.etichetta, container);
    node('span', value.identificativo, container).className = 'value-map-identifier';
  }

  function pagedTable(title, headers, rows, render) {
    const table = node('table', '', section);
    node('caption', title, table);
    const header = node('tr', '', node('thead', '', table));
    for (const label of headers) node('th', label, header).scope = 'col';
    const body = node('tbody', '', table);
    const controls = node('div', '', section);
    controls.className = 'value-map-pages';
    const previous = node('button', 'Pagina precedente', controls);
    const next = node('button', 'Pagina successiva', controls);
    previous.type = next.type = 'button';
    const status = node('p', '', controls);
    status.setAttribute('role', 'status');
    const pageSize = 25;
    let start = 0;
    function draw() {
      body.replaceChildren();
      for (const row of rows.slice(start, start + pageSize)) render(row, node('tr', '', body));
      status.textContent = (start + 1) + '–' + Math.min(start + pageSize, rows.length) + ' di ' + rows.length;
      previous.disabled = start === 0;
      next.disabled = start + pageSize >= rows.length;
    }
    previous.addEventListener('click', () => { start -= pageSize; draw(); });
    next.addEventListener('click', () => { start += pageSize; draw(); });
    controls.hidden = rows.length <= pageSize;
    draw();
  }

  node('h3', 'Mappa di valori «' + review.nome + '»', section);
  const facts = node('dl', '', section);
  node('dt', 'Vocabolario di destinazione', facts);
  term(review.vocabolario, node('dd', '', facts));
  node('dt', 'Numero di voci', facts);
  node('dd', String(review.numeroVoci), facts);
  if (review.colonnaSorgente) {
    node('dt', 'Colonna sorgente', facts);
    node('dd', review.colonnaSorgente, facts);
  }
  pagedTable('Corrispondenze codice → concetto', ['Codice', 'Concetto'], review.voci, (row, tr) => {
    node('th', row.codice, tr).scope = 'row';
    term(row.concetto, node('td', '', tr));
  });

  node('h3', 'Differenze rispetto alla versione precedente', section);
  node('p', review.versionePrecedente, section);
  if (review.differenze.length) {
    pagedTable('Modifiche dei codici', ['Codice', 'Modifica'], review.differenze, (row, tr) => {
      node('th', row.codice, tr).scope = 'row';
      const cell = node('td', '', tr);
      node('strong', row.modifica, cell);
      for (const [key, label] of [['prima', 'Prima'], ['dopo', 'Dopo']]) {
        if (row[key]) term(row[key], node('p', label + ' · ', cell));
      }
    });
  } else if (review.versionePrecedente !== 'Prima pubblicazione') {
    node('p', 'Nessuna modifica dei codici.', section);
  }
  return section;
}
