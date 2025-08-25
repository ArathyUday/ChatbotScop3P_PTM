# test_query.py
import psycopg2
import pandas as pd
import sys

def run_query(query: str, dbname="scop3p", user="postgres", password="", host="localhost", port=5432):
    """Execute a SQL query and return as pandas DataFrame."""
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_query.py \"SELECT * FROM project LIMIT 5;\"")
        sys.exit(1)

    sql = sys.argv[1]
    df = run_query(sql)
    print(df)
