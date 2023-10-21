import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector
from config import DB_HOST, DB_PORT



conn = psycopg2.connect(host = DB_HOST,
                        port = DB_PORT,
                        database = "semanticdb",
                        user = "deeptech",
                        password = "deeptech",
                        cursor_factory = RealDictCursor)


def postgres_table_schema(conn):
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    
    cur.execute(
    """DROP TABLE IF EXISTS doc_status;
    """
    )
    conn.commit()
    
    cur.execute(
    """
        CREATE TABLE IF NOT EXISTS doc_status (
            id bigserial PRIMARY KEY,
            doc_id VARCHAR(500) NOT NULL UNIQUE,
            url TEXT NOT NULL UNIQUE,
            status VARCHAR(50) NOT NULL
        );
    """
    )
    
    conn.commit()
    
    cur.execute(
        """
            CREATE TABLE IF NOT EXISTS document (
                id bigserial PRIMARY KEY,
                doc_id VARCHAR(100) NOT NULL,
                raw_contract TEXT NOT NULL,
                summary TEXT NOT NULL,
                metadata JSONB NOT NULL,
                keyword_vector tsvector GENERATED ALWAYS AS (
                    to_tsvector('english', summary) || ' ' ||
                    to_tsvector('english', metadata)
                ) STORED,
                summary_vector vector(1536) 
            );
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS lexical_search ON document USING GIN(keyword_vector)")
    conn.commit()