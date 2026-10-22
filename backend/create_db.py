"""Utility script to create MySQL databases using credentials from .env."""

import pymysql
from app.core.config import settings

def init_databases():
    print(f"Connecting to MySQL Server at {settings.DB_HOST}:{settings.DB_PORT} as '{settings.DB_USER}'...")
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            charset="utf8mb4"
        )
        with conn.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS novelia_books CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.execute("CREATE DATABASE IF NOT EXISTS novelia_books_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
        conn.close()
        print("SUCCESS: Databases 'novelia_books' and 'novelia_books_test' are ready!")
    except Exception as exc:
        print(f"ERROR: Could not connect or create databases: {exc}")
        print("Please verify MySQL Server is running and check DB_USER / DB_PASSWORD in backend/.env")

if __name__ == "__main__":
    init_databases()
