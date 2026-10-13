import os

import psycopg


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://appuser:test-only-not-a-secret@localhost:5432/appdb",
)



def main():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM themen")
            print(cur.fetchone())



if __name__ == "__main__":
    main()