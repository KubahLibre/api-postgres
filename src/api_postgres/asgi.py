import os
import psycopg
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from contextlib import contextmanager


app = FastAPI()


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


@app.get("/themen")
def get_themen():
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM themen")
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


class StatusAenderung(BaseModel):
    status: str


@app.put("/themen/{thema_id}")
def thema_bearbeiten(thema_id: int, neu: StatusAenderung) -> dict:
    with db() as conn, conn.cursor() as cur:
        try:
            cur.execute("UPDATE themen SET status = %s WHERE id = %s RETURNING *", (neu.status, thema_id))
            thema = cur.fetchone()
        except psycopg.errors.ForeignKeyViolation:
            raise HTTPException(
                status_code=400,
                detail=f"Status '{neu.status}' gibt es nicht.",
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