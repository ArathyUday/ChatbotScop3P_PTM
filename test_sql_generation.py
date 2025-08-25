#!/usr/bin/env python3
import sys
sys.path.append('.')

from pipeline import build_sql_prompt, clean_sql_response  # Import the cleaning function
from llm_client import query_llm
from db_utils import run_sql

def test_sql_generation():
    print("=== Testing SQL Generation with Cleaning ===")
    
    test_queries = [
        ("find phospho sites in Q86US8", "scop3p"),
        ("CS methyl sites", "scop3ptm"),
        ("find EST1A phospho sites in alpha helices", "scop3p")
    ]
    
    for user_query, database in test_queries:
        print(f"\nTesting: '{user_query}' on {database}")
        
        try:
            # Generate SQL
            if database == "scop3p":
                sql_prompt = build_sql_prompt("sql_scop3p.txt", user_query, database)
            else:
                sql_prompt = build_sql_prompt("sql_scop3ptm.txt", user_query, database)
            
            raw_sql = query_llm(sql_prompt, num_predict=200)
            cleaned_sql = clean_sql_response(raw_sql)
            print(f"Cleaned SQL: {cleaned_sql}")
            
            # Test if SQL is valid (try to execute)
            try:
                results = run_sql(database, cleaned_sql)
                print(f"SQL executed successfully, returned {len(results)} rows")
                if results:
                    print(f"Sample result keys: {list(results[0].keys())}")
                    if len(results) > 0:
                        print(f"First result: {results[0]}")
            except Exception as sql_error:
                print(f"SQL xecution failed: {sql_error}")
                
        except Exception as e:
            print(f"SQL generation failed: {e}")

if __name__ == "__main__":
    test_sql_generation()