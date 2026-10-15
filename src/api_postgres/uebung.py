import os
import psycopg
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row


app = FastAPI()


DATABASE_URL = os.environ["DATABASE_URL"]


def verbinde():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


@app.get("/kategorien")
def get_kategorien():
    conn = verbinde()
    cur = conn.cursor()
    cur.execute("SELECT * FROM kategorien")
    kategorien = cur.fetchall()
    return kategorien


@app.get("/themen")
def get_themen():
    conn = verbinde()
    cur = conn.cursor()
    cur.execute("SELECT * FROM themen")
    themen = cur.fetchall()
    return themen


@app.get("/themen/{thema_id}")
def get_thema(thema_id: int) -> dict:
    conn = verbinde()
    cur = conn.cursor()
    cur.execute("SELECT * FROM themen WHERE id = %s", (thema_id,))
    thema = cur.fetchone()
    if thema is None:
        raise HTTPException(status_code=404, detail="Thema nicht gefunden.")
    return thema