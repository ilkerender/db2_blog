import sys
import json
import os
import ibm_db
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

def get_env(key):
    val = os.getenv(key)
    if not val:
        sys.exit(f"Error: Environment variable {key} is missing in .env file")
    return val

def main(jsonl_file_path):
    # 1. Build Connection String
    conn_str = (
        f"DATABASE={get_env('DB2_DATABASE')};"
        f"HOSTNAME={get_env('DB2_HOSTNAME')};"
        f"PORT={get_env('DB2_PORT')};"
        f"PROTOCOL=TCPIP;"
        f"UID={get_env('DB2_UID')};"
        f"PWD={get_env('DB2_PWD')};"
    )

    try:
        conn = ibm_db.connect(conn_str, "", "")
    except Exception as e:
        sys.exit(f"Db2 Connection failed: {e}")

    print(f"Connected to {get_env('DB2_DATABASE')}. Ingesting {jsonl_file_path}...")

    # 2. Insert SQL
    sql = "INSERT INTO TEST.DEFNE_POLICY (CONTENT, SECTION_NAME, SUBSECTION_NAME, EMBEDDING) VALUES (?, ?, ?, NULL)"
    stmt = ibm_db.prepare(conn, sql)

    count = 0
    try:
        with open(jsonl_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                content = data.get('page_content', '')
                meta = data.get('metadata', {})
                
                ibm_db.execute(stmt, (content, meta.get('Section'), meta.get('Subsection')))
                count += 1
    except FileNotFoundError:
        sys.exit("File not found.")

    print(f"Inserted {count} rows. Embeddings are currently NULL.")
    ibm_db.close(conn)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python 2_ingest_chunks.py <file.jsonl>")
    main(sys.argv[1])
