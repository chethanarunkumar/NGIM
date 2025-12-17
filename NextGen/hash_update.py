from werkzeug.security import generate_password_hash
import psycopg2
from app.config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST


conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

cur = conn.cursor()

cur.execute(
    "UPDATE users SET password=%s WHERE email='admin@ngim.com';",
    (generate_password_hash("admin123"),)
)

cur.execute(
    "UPDATE users SET password=%s WHERE email='staff@ngim.com';",
    (generate_password_hash("staff123"),)
)

conn.commit()
cur.close()
conn.close()

print("Updated hashed passwords.")
