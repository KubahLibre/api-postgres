const button = document.querySelector('#lade-btn');
const liste  = document.querySelector('#themen-liste');

button.addEventListener('click', laden);

async function laden() {
  try {
    const antwort = await fetch('/themen');

    if (!antwort.ok) {
      liste.textContent = 'Fehler: HTTP ' + antwort.status;
      return;
    }

    const themen = await antwort.json();
    liste.innerHTML = themen.map(t =>
      `<li><strong>${t.titel}</strong> — `
      + `<span class="status">${t.status}</span> — `
      + `Kategorie ${t.kategorie_id}, Notiz: ${t.notiz ?? '—'}</li>`
    ).join('');
  } catch (fehler) {
    liste.textContent = 'Verbindung fehlgeschlagen: ' + fehler;
  }
}
const formular        = document.querySelector('#neu-form');
const kategorieSelect = document.querySelector('#kategorie-select');
const titelInput      = document.querySelector('#titel-input');
const notizInput      = document.querySelector('#notiz-input');

kategorienLaden();

async function kategorienLaden() {
  const antwort = await fetch('/kategorien');
  if (!antwort.ok) return;
  const kategorien = await antwort.json();
  kategorieSelect.innerHTML = kategorien
    .map(k => `<option value="${k.id}">${k.name}</option>`)
    .join('');
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