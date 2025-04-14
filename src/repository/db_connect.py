import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from contextlib import contextmanager
from dotenv import load_dotenv
import os

load_dotenv()  # Подгружает переменные из .env

@contextmanager
def get_cursor():
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "pvz"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432")
        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        yield cursor
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL:", error)
        print("DB_HOST =", os.getenv("DB_HOST"))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
