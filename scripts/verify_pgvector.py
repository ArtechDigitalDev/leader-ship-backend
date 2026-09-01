"""Verify pgvector setup on the configured DATABASE_URL."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
import psycopg2

conn = psycopg2.connect(settings.DATABASE_URL, connect_timeout=15)
cur = conn.cursor()

cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'")
print("pgvector extension:", cur.fetchone())

cur.execute(
    "SELECT column_name, udt_name FROM information_schema.columns "
    "WHERE table_name = 'lesson_chunks' AND column_name = 'embedding'"
)
print("embedding column:", cur.fetchone())

cur.execute(
    "SELECT indexname FROM pg_indexes "
    "WHERE tablename = 'lesson_chunks' AND indexname LIKE '%hnsw%'"
)
print("HNSW index:", cur.fetchone())

conn.close()
print("OK")
