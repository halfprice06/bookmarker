import sqlite3
from pathlib import Path

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check if the documents table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
    table_exists = cur.fetchone() is not None
    
    if not table_exists:
        # Create new tables with all columns
        cur.execute("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            date TEXT,
            summary TEXT,
            original_filename TEXT,
            full_text TEXT,
            markdown_transcription TEXT
        );
        """)
    else:
        # Check if markdown_transcription column exists
        cur.execute("PRAGMA table_info(documents)")
        columns = [column[1] for column in cur.fetchall()]
        if 'markdown_transcription' not in columns:
            # Add the new column
            cur.execute("ALTER TABLE documents ADD COLUMN markdown_transcription TEXT;")
    
    # Create or ensure other tables exist
    cur.execute("""
    CREATE TABLE IF NOT EXISTS document_pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        page_number INTEGER,
        markdown_text TEXT,
        FOREIGN KEY(document_id) REFERENCES documents(id)
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

def insert_document(db_path: str, title: str, date: str, summary: str, original_filename: str, 
                   tags: list[str], full_text: str, markdown_transcription: str, page_transcriptions: list[str]):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Insert main document
    cur.execute(
        """INSERT INTO documents 
           (title, date, summary, original_filename, full_text, markdown_transcription) 
           VALUES (?,?,?,?,?,?)""", 
        (title, date, summary, original_filename, full_text, markdown_transcription)
    )
    doc_id = cur.lastrowid
    
    # Insert individual page transcriptions
    for page_num, page_markdown in enumerate(page_transcriptions, 1):
        cur.execute(
            "INSERT INTO document_pages (document_id, page_number, markdown_text) VALUES (?,?,?)",
            (doc_id, page_num, page_markdown)
        )
    
    # Insert tags
    for tag in tags:
        cur.execute("INSERT INTO tags (document_id, tag) VALUES (?,?)", (doc_id, tag))
    
    conn.commit()
    conn.close()
    return doc_id
