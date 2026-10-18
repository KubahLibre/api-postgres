# Lernstand-API

Eine FastAPI-Anwendung mit PostgreSQL dahinter. Themen lassen sich anlegen,
auflisten, einzeln abrufen, im Status ändern und löschen. Keine Benutzeroberfläche —
alles läuft über HTTP.

## Schnellstart

```bash
docker compose up -d --build
docker exec -i db-postgres psql -U appuser -d appdb < db/init.sql
```

Der zweite Befehl ist einmalig nötig: er legt die Tabellen an. Ohne ihn startet
der Container, aber alle Abfragen scheitern, weil es keine Tabellen gibt.

Die API ist danach unter `http://localhost:8001` erreichbar. Die interaktive
Dokumentation liegt unter `http://localhost:8001/docs`.

Stoppen:

```bash
docker compose down
```

Achtung: `docker compose down -v` löscht auch die Daten. Die Daten liegen in
einem benannten Datenträger, nicht in der Datei `db/init.sql`.

## Die Endpunkte

| Methode | Adresse | Zweck | Fehlerfälle |
|---|---|---|---|
| GET | `/kategorien` | alle Kategorien | — |
| GET | `/themen` | alle Themen | — |
| GET | `/themen/{id}` | ein einzelnes Thema | 404, 422 |
| POST | `/themen` | legt ein Thema an | 400, 422 |
| PUT | `/themen/{id}` | ändert den Status | 400, 404, 422 |
| DELETE | `/themen/{id}` | löscht ein Thema | 404, 422 |

### Beispiele

```bash
# alle Themen
curl -s http://localhost:8001/themen

# ein einzelnes
curl -s http://localhost:8001/themen/5

# anlegen
curl -s -X POST http://localhost:8001/themen \
  -H "Content-Type: application/json" \
  -d '{"titel":"Subnetze lernen","kategorie_id":1,"notiz":"Kapitel 3"}'

# Status ändern
curl -s -X PUT http://localhost:8001/themen/5 \
  -H "Content-Type: application/json" \
  -d '{"status":"erledigt"}'

# löschen
curl -s -X DELETE http://localhost:8001/themen/5
```

### Die vier Fehlercodes, und wann sie kommen

| Code | Bedeutung | Auslöser |
|---|---|---|
| 400 | Die Anfrage war gültig, aber der Inhalt passt nicht | `kategorie_id` oder `status` existiert in der Datenbank nicht |
| 404 | Die Adresse zeigt auf etwas, das es nicht gibt | keine Zeile mit dieser Nummer |
| 422 | Die Anfrage war schon falsch, bevor jemand gefragt wurde | `/themen/abc` statt einer Zahl, oder ein fehlendes Pflichtfeld |

Der Unterschied zwischen 404 und 422 ist wichtig: bei 404 **wurde** die
Datenbank gefragt und sie hatte nichts. Bei 422 wird **gar nicht erst** gefragt,
weil schon die Form der Anfrage falsch ist.

## Die Datenbank

Drei Tabellen, in `db/init.sql` festgeschrieben und per `psql` einzuspielen.

**`kategorien`** — die Kategorien

| Spalte | Typ | Besonderheit |
|---|---|---|
| `id` | integer | automatisch vergeben, eindeutig |
| `name` | text | Pflicht, eindeutig |

**`themen`** — die Themen selbst

| Spalte | Typ | Besonderheit |
|---|---|---|
| `id` | integer | automatisch vergeben, eindeutig |
| `titel` | text | Pflicht |
| `status` | text | Pflicht, Vorgabe `offen` |
| `kategorie_id` | integer | Pflicht, zeigt auf `kategorien` |
| `notiz` | text | darf leer sein |

**`themen_status`** — die erlaubten Statuswerte

| Spalte | Typ | Besonderheit |
|---|---|---|
| `status` | text | eindeutig |

Zwei Fremdschlüssel halten die Daten zusammen:

- **`themen.kategorie_id` → `kategorien.id`** — ein Thema braucht eine
  existierende Kategorie.
- **`themen.status` → `themen_status.status`** — nur `offen`, `angefangen` und
  `erledigt` sind erlaubt.

Wer einen anderen Wert schickt, bekommt einen 400. Die Datenbank lehnt die Zeile
ab, nicht der Python-Code.

`status` hat den Vorgabewert `offen`. Deshalb steht bei einem neu angelegten
Thema immer `offen`, auch wenn keiner mitgeschickt wurde.

### Nummern werden nicht wiederverwendet

Die `id` ist eine fortlaufende **Nummerierung**, keine Zählung. Ein Fehlversuch
verbraucht eine Nummer, genauso wie ein gelöschtes Thema. Nach dem Löschen von
`id 5` und erneutem Anlegen bekommt man nicht wieder `5`.

## Konfiguration

Die Zugangsdaten stehen in `docker-compose.yml` und haben Vorgabewerte. Wer sie
ändern will, legt eine `.env` im Projektordner an — die wird von Compose gelesen
und überschreibt die Vorgabewerte:

```bash
DB_USER=appuser
DB_PASSWORD=irgendwas
DB_NAME=appdb
```

Die Vorgabe `test-only-not-a-secret` ist **ausdrücklich kein Geheimnis**, sondern
ein Platzhalter, damit das Repository nichts Echtes enthält. Für alles
Echte gehört das Passwort in eine `.env`, und die gehört in `.gitignore` —
dort steht sie bereits.

## Aufbau des Projekts

```
docker-compose.yml      zwei Dienste: die API und die Datenbank
Dockerfile              baut das Image der API
db/init.sql             legt Tabellen und Fremdschlüssel an
src/api_postgres/
  asgi.py               die Anwendung — alle sechs Endpunkte
  __init__.py           leer, wird vom Build gebraucht
```

Der Container startet `asgi.py` — im `Dockerfile` steht, welches Modul läuft:

```
CMD ["uv", "run", "--no-sync", "uvicorn", "api_postgres.asgi:app", ...]
```

## Warum die Datenbank keinen Port nach außen hat

Der Dienst `postgres` veröffentlicht nichts. Er ist nur im Docker-Netz
erreichbar. Von außen kommt man ausschließlich über die API an die Daten.

Deshalb steht in der `DATABASE_URL` der Hostname `postgres` und nicht
`localhost`: `localhost` wäre der Rechner selbst, `postgres` ist der Name des
Dienstes im Docker-Netz.

## Stand und offene Punkte

- Die Datenbank enthält noch Testdaten aus der Entwicklung.
- Es gibt keinen Endpunkt für Kategorien, mit denen man eine anlegt oder löscht.
- Eine `GET /themen`-Variante mit Statusfilter (`?status=offen`) fehlt noch.