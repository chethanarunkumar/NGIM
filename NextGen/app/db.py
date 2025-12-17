import os
import psycopg2
import psycopg2.extras
from flask import g
from app.config import Config

def get_db():
    if "db" not in g:
        DATABASE_URL = os.environ.get("DATABASE_URL")

        if DATABASE_URL:
            g.db = psycopg2.connect(
                DATABASE_URL,
                cursor_factory=psycopg2.extras.RealDictCursor,
                sslmode="require"
            )
        else:
            g.db = psycopg2.connect(
                dbname=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                cursor_factory=psycopg2.extras.RealDictCursor
            )

    return g.db
