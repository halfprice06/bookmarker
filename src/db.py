import sqlite3
from pathlib import Path

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Create a table to store extracted metadata
    # One table to hold documents, another for tags
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        date TEXT,
        summary TEXT,
        original_filename TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        tag TEXT,
        FOREIGN KEY(document_id) REFERENCES documents(id)
    );
    """)
    conn.commit()
    conn.close()

def insert_document(db_path: str, title: str, date: str, summary: str, original_filename: str, tags: list[str]):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO documents (title, date, summary, original_filename) VALUES (?,?,?,?)", (title, date, summary, original_filename))
    doc_id = cur.lastrowid
    for tag in tags:
        cur.execute("INSERT INTO tags (document_id, tag) VALUES (?,?)", (doc_id, tag))
    conn.commit()
    conn.close()
    return doc_id
