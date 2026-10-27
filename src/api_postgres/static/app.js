const liste  = document.querySelector('#themen-liste');

const formular        = document.querySelector('#neu-form');
const kategorieSelect = document.querySelector('#kategorie-select');
const titelInput      = document.querySelector('#titel-input');
const notizInput      = document.querySelector('#notiz-input');

const statusReihenfolge = ['offen', 'angefangen', 'erledigt'];

kategorienLaden();
laden();

let kategorienListe = [];

async function kategorienLaden() {
  const antwort = await fetch('/kategorien');
  if (!antwort.ok) return;
  kategorienListe = await antwort.json();
  kategorieSelect.innerHTML = kategorienListe
    .map(k => `<option value="${k.id}">${k.name}</option>`)
    .join('');
}
async function laden() {
  try {
    const antwort = await fetch('/themen');

    if (!antwort.ok) {
      liste.textContent = 'Fehler: HTTP ' + antwort.status;
      return;
    }

    const themen = await antwort.json();
    
    liste.innerHTML = themen.map(t =>
      `<li class="karte">
        <div class="kopf">
          <div class="kopf-links">
            <strong>${t.titel}</strong>
            <button class="titel-btn" data-id="${t.id}" title="Titel bearbeiten">&#9998;</button>
          </div>
          <span class="status status-${t.status}">${t.status}</span>
        </div>        <div class="kat">Kategorie: ${kategorienListe.find(k => k.id === t.kategorie_id)?.name ?? '(unbekannt)'}</div>
        <div class="notiz">Notiz: ${t.notiz ?? '—'}</div>
                <div class="aktionen">
          <button class="status-btn" data-id="${t.id}" data-status="${t.status}">Status weiter</button>
          <button class="bearb-btn" data-id="${t.id}">Notiz bearbeiten</button>
          <button class="loesch-btn" data-id="${t.id}">Löschen</button>
        </div>
      </li>`
          ).join('');
    liste.querySelectorAll('.status-btn').forEach(b =>
      b.addEventListener('click', () => statusAendern(b.dataset.id, b.dataset.status)));
    liste.querySelectorAll('.titel-btn').forEach(b =>
      b.addEventListener('click', () => titelBearbeiten(b.dataset.id)));
    liste.querySelectorAll('.bearb-btn').forEach(b =>
      b.addEventListener('click', () => notizBearbeiten(b.dataset.id)));
    liste.querySelectorAll('.loesch-btn').forEach(b =>
      b.addEventListener('click', () => loeschen(b.dataset.id)));  } catch (fehler) {
    liste.textContent = 'Verbindung fehlgeschlagen: ' + fehler;
  }
}
async function statusAendern(id, status) {
  const naechster = statusReihenfolge[(statusReihenfolge.indexOf(status) + 1) % statusReihenfolge.length];
  try {
    const antwort = await fetch('/themen/' + id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: naechster }),
    });

    if (!antwort.ok) {
      liste.textContent = 'Fehler: HTTP ' + antwort.status;
      return;
    }
    await laden();
  } catch (fehler) {
    liste.textContent = 'Verbindung fehlgeschlagen: ' + fehler;
  }
}

async function loeschen(id) {
  if (!confirm('Thema ' + id + ' wirklich loeschen?')) return;
  try {
    const antwort = await fetch('/themen/' + id, { method: 'DELETE' });

    if (!antwort.ok) {
      liste.textContent = 'Fehler: HTTP ' + antwort.status;
      return;
    }
    await laden();
  } catch (fehler) {
    liste.textContent = 'Verbindung fehlgeschlagen: ' + fehler;
  }
}

async function titelBearbeiten(id) {
  try {
    const antwortAlt = await fetch('/themen/' + id);

    if (!antwortAlt.ok) {
      liste.textContent = 'Fehler: HTTP ' + antwortAlt.status;
      return;
    }

    const thema = await antwortAlt.json();

    const titelNeu = prompt('Neuer Titel:', thema.titel);
    if (titelNeu === null) return;
    if (titelNeu.trim() === '') {
      alert('Der Titel darf nicht leer sein.');
      return;
    }

    const antwort = await fetch('/themen/' + id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ titel: titelNeu }),
    });

    if (!antwort.ok) {
      liste.textContent = 'Fehler: HTTP ' + antwort.status;
      return;
    }

    await laden();
  } catch (fehler) {
    liste.textContent = 'Verbindung fehlgeschlagen: ' + fehler;
  }
}

async function notizBearbeiten(id) {
  try {
    const antwortAlt = await fetch('/themen/' + id);

    if (!antwortAlt.ok) {
      liste.textContent = 'Fehler: HTTP ' + antwortAlt.status;
      return;
    }

    const thema = await antwortAlt.json();

    const notizNeu = prompt('Notiz (leer lassen = keine):', thema.notiz ?? '');
    if (notizNeu === null) return;

    const antwort = await fetch('/themen/' + id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notiz: notizNeu === '' ? null : notizNeu }),
    });

    if (!antwort.ok) {
      liste.textContent = 'Fehler: HTTP ' + antwort.status;
      return;
    }

    await laden();
  } catch (fehler) {
    liste.textContent = 'Verbindung fehlgeschlagen: ' + fehler;
  }
}

formular.addEventListener('submit', async (ereignis) => {
  ereignis.preventDefault();
  try {
    const antwort = await fetch('/themen', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        titel: titelInput.value,
        kategorie_id: parseInt(kategorieSelect.value, 10),
        notiz: notizInput.value || null,
      }),
    });

    if (!antwort.ok) {
      liste.textContent = 'Fehler: HTTP ' + antwort.status;
      return;
    }

    titelInput.value = '';
    notizInput.value = '';
    await laden();
  } catch (fehler) {
    liste.textContent = 'Verbindung fehlgeschlagen: ' + fehler;
  }
});