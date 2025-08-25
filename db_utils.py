import psycopg2
import json
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD

def get_db_connection(dbname):
    """Get database connection with proper error handling"""
    try:
        return psycopg2.connect(
            dbname=dbname, 
            user=DB_USER, 
            password=DB_PASSWORD, 
            host=DB_HOST,
            port=DB_PORT
        )
    except psycopg2.Error as e:
        raise Exception(f"Database connection failed for {dbname}: {e}")

def run_sql(dbname, sql):
    """Execute SQL query and return results as list of dictionaries"""
    if not sql or sql.strip() == "":
        return []
    
    conn = None
    try:
        conn = get_db_connection(dbname)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        return [dict(zip(cols, row)) for row in rows]
    except psycopg2.Error as e:
        print(f"SQL execution error in {dbname}: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in run_sql: {e}")
        return []
    finally:
        if conn:
            conn.close()

def run_project_sql(dbname, sql): 
    """Execute project-related SQL query"""
    return run_sql(dbname, sql)

def run_mutation_sql(dbname, protein_ids): 
    """Execute mutation SQL query for given protein IDs"""
    if not protein_ids:
        return []
    
    mutation_sql = build_mutation_sql(dbname, protein_ids)
    return run_sql(dbname, mutation_sql)

def build_mutation_sql(database, protein_ids):
    """Build SQL to fetch mutation information"""
    if not protein_ids:
        return "SELECT 1 WHERE FALSE"
    
    ids_str = ','.join(map(str, protein_ids))
    
    if database == "scop3p":
        return f"""
        SELECT m.uniprot_position, m.reference_amino_acid, m.alternative_amino_acid,
               m.mutation_type, m.disease, p.protein_name, p.accession
        FROM mutation m
        JOIN protein p ON m.l_protein_id = p.id
        WHERE p.id IN ({ids_str})
        LIMIT 50
        """
    else:  # scop3ptm
        return f"""
        SELECT m.mutation_position, m.reference_amino_acid, m.alternative_amino_acid,
               m.mutation_type, m.disease, p.protein_name, p.accession, g.gene_name
        FROM mutation m
        JOIN protein p ON m.l_protein_id = p.id
        LEFT JOIN gene g ON m.l_gene_id = g.id
        WHERE p.id IN ({ids_str})
        LIMIT 50
        """