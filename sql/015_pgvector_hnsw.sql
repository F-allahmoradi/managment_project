-- بردار بازیابی از آرایهٔ float به pgvector و ایندکس HNSW کسینوس.
-- مدل قفل‌شده text-embedding-3-small است؛ طول بردار ۱۵۳۶.

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE text_embeddings
    DROP CONSTRAINT IF EXISTS text_embeddings_embedding_not_empty;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'text_embeddings'
          AND column_name = 'embedding'
          AND udt_name = '_float8'
    ) THEN
        ALTER TABLE text_embeddings
            ALTER COLUMN embedding TYPE vector(1536)
            USING embedding::vector(1536);
    END IF;
END $$;

COMMENT ON TABLE text_embeddings IS
    'بردار بازیابی با pgvector. منبع حقیقت نیست؛ raw متن خام است و بقیه فکت استخراج‌شده.';

CREATE INDEX IF NOT EXISTS text_embeddings_embedding_hnsw_idx
    ON text_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

COMMIT;
