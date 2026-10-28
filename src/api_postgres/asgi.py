import os
import psycopg
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from contextlib import contextmanager
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

@app.get("/")
def startseite():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


DATABASE_URL = os.environ["DATABASE_URL"]


@contextmanager
def db():
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        yield conn


@app.get("/kategorien")
def get_kategorien():
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM kategorien")
        kategorien = cur.fetchall()
    return kategorien


class KategorieIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)


@app.post("/kategorien", status_code=201)
def kategorie_anlegen(kategorie: KategorieIn) -> dict:
    with db() as conn, conn.cursor() as cur:
        try:
            cur.execute("INSERT INTO kategorien (name) VALUES (%s) RETURNING *", (kategorie.name,))
            return cur.fetchone()
        except psycopg.errors.UniqueViolation:
            raise HTTPException(
                status_code=409,
                detail=f"Kategorie '{kategorie.name}' gibt es schon.",
            ) from None


@app.delete("/kategorien/{kategorie_id}", status_code=200)
def kategorie_loeschen(kategorie_id: int) -> dict:
    with db() as conn, conn.cursor() as cur:
        try:
            cur.execute("DELETE FROM kategorien WHERE id = %s RETURNING *", (kategorie_id,))
            geloescht = cur.fetchone()
        except psycopg.errors.ForeignKeyViolation:
            raise HTTPException(
                status_code=409,
                detail="Diese Kategorie wird noch von Themen benutzt.",
            ) from None
    if geloescht is None:
        raise HTTPException(status_code=404, detail="Kategorie nicht gefunden.")
    return geloescht

@app.get("/themen")
def get_themen(status: str | None = None):
    sql = "SELECT * FROM themen"
    parameter = ()
    if status is not None:
        sql += " WHERE status = %s"
        parameter = (status,)
    sql += " ORDER BY id"

    with db() as conn, conn.cursor() as cur:
        if status is not None:
            cur.execute("SELECT status FROM themen_status WHERE status = %s", (status,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=400, detail=f"Status '{status}' gibt es nicht.")
        cur.execute(sql, parameter)
        themen = cur.fetchall()
    return themen

@app.get("/themen/{thema_id}")
def get_thema(thema_id: int) -> dict:
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM themen WHERE id = %s", (thema_id,))
        thema = cur.fetchone()
    if thema is None:
        raise HTTPException(status_code=404, detail="Thema nicht gefunden.")
    return thema



class ThemaIn(BaseModel):
    titel: str = Field(min_length=1, max_length=200)
    kategorie_id: int
    notiz: str | None = None


@app.post("/themen", status_code=201)
def thema_anlegen(neu: ThemaIn) -> dict:
    with db() as conn, conn.cursor() as cur:
        try:
            cur.execute(
                "INSERT INTO themen (titel, status, kategorie_id, notiz) VALUES (%s, 'offen', %s, %s) RETURNING *",
                (neu.titel, neu.kategorie_id, neu.notiz),
            )
            return cur.fetchone()
        except psycopg.errors.ForeignKeyViolation:
            raise HTTPException(
                status_code=400,
                detail=f"Kategorie {neu.kategorie_id} gibt es nicht.",
                ) from None


class ThemaAenderung(BaseModel):
    titel: str | None = Field(default=None, min_length=1, max_length=200)
    kategorie_id: int | None = None
    notiz: str | None = None
    status: str | None = None


@app.put("/themen/{thema_id}")
def thema_bearbeiten(thema_id: int, neu: ThemaAenderung) -> dict:
    felder = {}
    if neu.titel is not None:
        felder["titel"] = neu.titel
    if neu.kategorie_id is not None:
        felder["kategorie_id"] = neu.kategorie_id
    if neu.notiz is not None:
        felder["notiz"] = neu.notiz
    if neu.status is not None:
        felder["status"] = neu.status
    if not felder:
        raise HTTPException(status_code=422, detail="Keine Aenderung mitgeschickt.")

    set_teil = ", ".join(f"{name} = %s" for name in felder)
    werte = list(felder.values()) + [thema_id]

    with db() as conn, conn.cursor() as cur:
        try:
            cur.execute(f"UPDATE themen SET {set_teil} WHERE id = %s RETURNING *", werte)
            thema = cur.fetchone()
        except psycopg.errors.ForeignKeyViolation:
            raise HTTPException(
                status_code=400,
                detail="Kategorie oder Status gibt es nicht.",
            ) from None
    if thema is None:
        raise HTTPException(status_code=404, detail="Thema nicht gefunden.")
    return thema


@app.delete("/themen/{thema_id}", status_code=200)
def thema_loeschen(thema_id: int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM themen WHERE id = %s RETURNING *", (thema_id,))
        geloescht = cur.fetchone()
    if geloescht is None:
        raise HTTPException(status_code=404, detail="Thema nicht gefunden.")
    return geloescht