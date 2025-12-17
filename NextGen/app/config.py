import os
from urllib.parse import urlparse

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key")

    # If running on Render, DATABASE_URL will exist
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL:
        url = urlparse(DATABASE_URL)

        DB_NAME = url.path[1:]
        DB_USER = url.username
        DB_PASSWORD = url.password
        DB_HOST = url.hostname
        DB_PORT = url.port
    else:
        # Local development (pgAdmin / localhost)
        DB_NAME = "NGIM"
        DB_USER = "postgres"
        DB_PASSWORD = "1234"
        DB_HOST = "localhost"
        DB_PORT = "5432"
