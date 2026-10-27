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