const button = document.querySelector('#lade-btn');
const liste  = document.querySelector('#themen-liste');

button.addEventListener('click', laden);

const formular        = document.querySelector('#neu-form');
const kategorieSelect = document.querySelector('#kategorie-select');
const titelInput      = document.querySelector('#titel-input');
const notizInput      = document.querySelector('#notiz-input');

const statusReihenfolge = ['offen', 'angefangen', 'erledigt'];

kategorienLaden();

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
          <strong>${t.titel}</strong>
          <span class="status status-${t.status}">${t.status}</span>
        </div>
        <div class="kat">Kategorie: ${kategorienListe.find(k => k.id === t.kategorie_id)?.name ?? '(unbekannt)'}</div>
        <div class="notiz">Notiz: ${t.notiz ?? '—'}</div>
        <div class="aktionen">
          <button class="status-btn" data-id="${t.id}" data-status="${t.status}">Status weiter</button>
          <button class="loesch-btn" data-id="${t.id}">Löschen</button>
        </div>
      </li>`
    ).join('');
    liste.querySelectorAll('.status-btn').forEach(b =>
      b.addEventListener('click', () => statusAendern(b.dataset.id, b.dataset.status)));
    liste.querySelectorAll('.loesch-btn').forEach(b =>
      b.addEventListener('click', () => loeschen(b.dataset.id)));
  } catch (fehler) {
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