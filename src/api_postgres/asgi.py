"""FastAPI-Anwendung. Liest aus PostgreSQL, schreibt noch nichts."""

import os
from contextlib import contextmanager

import psycopg
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

# Kein Default: wenn die Variable fehlt, soll der Start sofort scheitern
# statt zur Laufzeit bei der ersten Anfrage.
DATABASE_URL = os.environ["DATABASE_URL"]

app = FastAPI(title="Lernstand-API")


@contextmanager
def db():
    """Verbindung fuer genau eine Anfrage. Wird danach automatisch geschlossen.

    row_factory=dict_row: psycopg liefert jede Zeile direkt als dict. So
    kann FastAPI sie als JSON ausgeben, ohne dass wir Spaltennamen
    aufzaehlen muessen.
    """
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        yield conn


@app.get("/health")
def health() -> dict:
    """Prueft, ob die Datenbank erreichbar ist - und zaehlt gleich mit."""
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) AS anzahl FROM themen")
        return {"status": "ok", "themen": cur.fetchone()["anzahl"]}


@app.get("/themen")
def liste_themen(status: str | None = None):
    """Alle Themen. Mit ?status=offen wird nur dieses eine Status gezeigt.

    status=None ist der Fall, wenn der Aufrufer den Parameter weggelaesst
    hat. Das Fragezeichen in der Doku ist optional - ohne Angabe kommt der
    Wert als None hier an.
    """
    with db() as conn, conn.cursor() as cur:
        if status is None:
            cur.execute("SELECT * FROM themen ORDER BY id")
        else:
            # %s ist ein Platzhalter, nicht Teil des SQL-Texts. Der Wert
            # wandert als zweites Argument nach psycopg und wird dort
            # geprueft und quotiert. Das ist der Unterschied zu einem
            # f-string, bei dem der Wert im Text landet.
            cur.execute(
                "SELECT * FROM themen WHERE status = %s ORDER BY id",
                (status,),
            )
        return cur.fetchall()


@app.get("/themen/{thema_id}")
def thema_holen(thema_id: int) -> dict:
    """Ein einzelnes Thema. 404, wenn es die Nummer nicht gibt."""
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM themen WHERE id = %s",
            (thema_id,),
        )
        zeile = cur.fetchone()

    if zeile is None:
        raise HTTPException(status_code=404, detail="Thema nicht gefunden.")

    return zeile


class ThemaIn(BaseModel):
    """Was der Aufrufer schicken muss - und was er nicht schicken darf.

    Diese Klasse macht aus einem kaputten JSON-Aufruf eine verstaendliche
    Antwort (422) statt eines Absturzes mitten im Code.
    """

    titel: str = Field(min_length=1, max_length=200)
    kategorie_id: int
    notiz: str | None = None


class ThemaAenderung(BaseModel):
    """Beim Aendern nur der Status - titel und notiz bleiben wie sie sind."""

    status: str


@app.post("/themen", status_code=201)
def thema_anlegen(neu: ThemaIn) -> dict:
    """Legt ein Thema an. Gibt die vollstaendige neue Zeile zurueck.

    Bei falscher kategorie_id gibt es 400 statt 500 - mit Grund im Body,
    statt einer unbrauchbaren Fehlerseite.
    """
    with db() as conn, conn.cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO themen (titel, status, kategorie_id, notiz)
                VALUES (%s, 'offen', %s, %s)
                RETURNING *
                """,
                (neu.titel, neu.kategorie_id, neu.notiz),
            )
            # fetchone holt die eine Zeile, die RETURNING geliefert hat.
            return cur.fetchone()
        except psycopg.errors.ForeignKeyViolation:
            # Bewusst ohne "from": der Aufrufer soll nicht sehen, wie
            # PostgreSQL intern heisst, sondern was er falsch gemacht hat.
            raise HTTPException(
                status_code=400,
                detail=f"Kategorie {neu.kategorie_id} gibt es nicht.",
            ) from None


@app.put("/themen/{thema_id}")
def thema_aendern(thema_id: int, neu: ThemaAenderung) -> dict:
    """Setzt den Status. 404, wenn es die Nummer nicht gibt.

    RETURNING * loest die 404 ohne zweites SELECT: passiert keine Zeile,
    liefert die Datenbank nichts zurueck und fetchone() liefert None.
    """
    with db() as conn, conn.cursor() as cur:
        try:
            cur.execute(
                "UPDATE themen SET status = %s WHERE id = %s RETURNING *",
                (neu.status, thema_id),
            )
            zeile = cur.fetchone()
        except psycopg.errors.ForeignKeyViolation:
            raise HTTPException(
                status_code=400,
                detail=f"Status '{neu.status}' gibt es nicht.",
            ) from None

    if zeile is None:
        raise HTTPException(status_code=404, detail="Thema nicht gefunden.")

    return zeile