"""enable_pgvector_on_lesson_chunks

Revision ID: c8d4e2f1a9b0
Revises: b7e2f8a1c3d5
Create Date: 2026-09-01

Enables the pgvector extension (Neon/Postgres) and converts lesson_chunks.embedding
from JSON float arrays to native VECTOR(1536) with an HNSW cosine index.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c8d4e2f1a9b0'
down_revision: Union[str, None] = 'b7e2f8a1c3d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 1536


def upgrade() -> None:
    # Neon and modern Postgres support this out of the box.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "lesson_chunks" not in inspector.get_table_names():
        return

    columns = {col["name"]: col for col in inspector.get_columns("lesson_chunks")}
    if "embedding" not in columns:
        return

    col_type = str(columns["embedding"]["type"]).upper()
    if "VECTOR" not in col_type:
        # JSON/text arrays from the previous migration -> native pgvector column.
        op.execute(f"""
            ALTER TABLE lesson_chunks
            ALTER COLUMN embedding TYPE vector({EMBEDDING_DIM})
            USING CASE
                WHEN embedding IS NULL THEN NULL
                ELSE embedding::text::vector
            END
        """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_lesson_chunks_embedding_hnsw
        ON lesson_chunks
        USING hnsw (embedding vector_cosine_ops)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_lesson_chunks_embedding_hnsw")

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "lesson_chunks" not in inspector.get_table_names():
        return

    columns = {col["name"]: col for col in inspector.get_columns("lesson_chunks")}
    if "embedding" not in columns:
        return

    col_type = str(columns["embedding"]["type"]).upper()
    if "VECTOR" in col_type:
        op.execute(f"""
            ALTER TABLE lesson_chunks
            ALTER COLUMN embedding TYPE JSON
            USING CASE
                WHEN embedding IS NULL THEN NULL
                ELSE to_json(embedding::float4[])::json
            END
        """)
