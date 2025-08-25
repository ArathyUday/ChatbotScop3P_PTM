import sys
sys.path.append('.')

from db_utils import run_sql

def test_database_connections():
    print("=== Testing Database Connections ===")
    
    # Test SCOP3P connection
    try:
        result = run_sql("scop3p", "SELECT COUNT(*) as count FROM protein LIMIT 1")
        print(f"SCOP3P connected: {result[0]['count']} proteins found")
    except Exception as e:
        print(f"SCOP3P connection failed: {e}")
    
    # Test SCOP3PTM connection  
    try:
        result = run_sql("scop3ptm", "SELECT COUNT(*) as count FROM protein LIMIT 1")
        print(f"SCOP3PTM connected: {result[0]['count']} proteins found")
    except Exception as e:
        print(f"SCOP3PTM connection failed: {e}")

if __name__ == "__main__":
    test_database_connections()