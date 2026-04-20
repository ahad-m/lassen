import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = "5432"  
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

INDEX_NAME = "idx_poetry_verses_embedding_ivfflat_cosine"
TABLE_NAME = "public.poetry_verses"

LISTS = 1000

def main():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
    )
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = 0;")
            cur.execute("SET lock_timeout = 0;")
            cur.execute("SET maintenance_work_mem = '1536MB';")
            cur.execute("SET max_parallel_maintenance_workers = 4;")
            
            cur.execute("SHOW maintenance_work_mem;")
            print(f"✓ maintenance_work_mem: {cur.fetchone()[0]}")
            cur.execute("SHOW max_parallel_maintenance_workers;")
            print(f"✓ max_parallel_maintenance_workers: {cur.fetchone()[0]}")
            
            print(f"\nبناء IVFFlat: lists={LISTS}")
         
            
            # بناء الـ Index
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {INDEX_NAME}
                ON {TABLE_NAME}
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = {LISTS})
                WHERE embedding IS NOT NULL;
            """)
            
            cur.execute(f"ANALYZE {TABLE_NAME};")
            print(" تم بناء الIndex بنجاح")
            
    finally:
        conn.close()

if __name__ == "__main__":
    main()