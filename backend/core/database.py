import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database_v2.sqlite')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
