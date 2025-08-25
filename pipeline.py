import json
import logging
from lexicon import classify_query
from prompts import load_prompt
from llm_client import query_llm
from db_utils import run_sql, run_project_sql, run_mutation_sql
from conversation_manager import ConversationManager
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()  # Also print to console
    ]
)
logger = logging.getLogger(__name__)

# Global conversation manager instance
conversation_manager = ConversationManager(max_history=4)

def handle_query(user_query: str):
    """Main conversational query handler with logging"""
    global conversation_manager
    
    logger.info(f"Processing query: '{user_query}'")
    
    # Step 1: Classify intent using LLM
    logger.info("Step 1: Classifying intent...")
    try:
        processing_result = conversation_manager.process_query(user_query)
        logger.info(f"Intent classification result: {processing_result}")
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        return "I'm having trouble understanding your question. Could you please rephrase it?"
    
    # Step 2: Route based on classification
    if processing_result["skip_pipeline"]:
        logger.info("Using direct response (skipping database pipeline)")
        response = processing_result["response"]
    else:
        logger.info("Proceeding to database pipeline...")
        actual_query = processing_result.get("query")
        
        if not actual_query:
            logger.warning("No resolved query found, using original")
            actual_query = user_query
        
        logger.info(f"Database query: '{actual_query}'")
        response = handle_domain_query(actual_query)
    
    # Step 3: Record the interaction
    conversation_manager.record_interaction(user_query, response)
    logger.info(f"Response generated (length: {len(response)})")
    
    return response

def handle_domain_query(user_query: str):
    """Handle domain-specific queries with logging"""
    logger.info(f"Starting domain query processing for: '{user_query}'")
    
    # Step 1: Lexicon route
    logger.info("Step 1: Lexicon routing...")
    routing = classify_query(user_query)
    logger.info(f"Lexicon routing result: {routing}")

    # Step 2: Router fallback if ambiguous
    if routing["mode"] == "llm":
        logger.info("Step 2: Using LLM router fallback...")
        try:
            router_prompt = load_prompt("router.txt").format(user_query=user_query)
            router_response = query_llm(router_prompt)
            logger.info(f"Router LLM response: {router_response}")
            routing = safe_json_parse(router_response)
            logger.info(f"Parsed router result: {routing}")
        except Exception as e:
            logger.error(f"Router fallback failed: {e}")
            routing = {
                "mode": "sql",
                "db": "both", 
                "needs_projects": False,
                "needs_mutations": False
            }

    results = {}
    
    # Step 3: SQL generation with error handling
    logger.info("Step 3: SQL generation and execution...")
    
    if routing["db"] in ["scop3p", "both"]:
        logger.info("Processing SCOP3P database...")
        try:
            sql_prompt = build_sql_prompt("sql_scop3p.txt", user_query, "scop3p")
            raw_sql = query_llm(sql_prompt)
            cleaned_sql = clean_sql_response(raw_sql)
            logger.info(f"Generated SCOP3P SQL: {cleaned_sql}")
            
            if cleaned_sql and cleaned_sql.strip():
                results["scop3p"] = run_sql("scop3p", cleaned_sql)
                logger.info(f"SCOP3P results: {len(results['scop3p'])} rows")
            else:
                logger.warning("Empty SQL generated for SCOP3P")
                results["scop3p"] = []
                
        except Exception as e:
            logger.error(f"SCOP3P processing failed: {e}")
            results["scop3p"] = []

    if routing["db"] in ["scop3ptm", "both"]:
        logger.info("Processing SCOP3PTM database...")
        try:
            sql_prompt = build_sql_prompt("sql_scop3ptm.txt", user_query, "scop3ptm")
            raw_sql = query_llm(sql_prompt)
            cleaned_sql = clean_sql_response(raw_sql)
            logger.info(f"Generated SCOP3PTM SQL: {cleaned_sql}")
            
            if cleaned_sql and cleaned_sql.strip():
                results["scop3ptm"] = run_sql("scop3ptm", cleaned_sql)
                logger.info(f"SCOP3PTM results: {len(results['scop3ptm'])} rows")
            else:
                logger.warning("Empty SQL generated for SCOP3PTM")
                results["scop3ptm"] = []
                
        except Exception as e:
            logger.error(f"SCOP3PTM processing failed: {e}")
            results["scop3ptm"] = []

    # Log total results
    total_results = sum(len(res) for res in results.values())
    logger.info(f"Total database results: {total_results} rows")

    # Step 4: Enrichment with error handling
    logger.info("Step 4: Enrichment processing...")
    projects, mutations = {}, {}
    
    if routing.get("needs_projects"):
        logger.info("Fetching project information...")
        for db, res in results.items():
            try:
                ids = extract_ids(res)
                logger.info(f"Extracted {len(ids)} protein IDs from {db}")
                if ids:
                    proj_sql = build_project_sql(db, ids)
                    projects[db] = run_project_sql(db, proj_sql)
                    logger.info(f"Found {len(projects[db])} projects for {db}")
                else:
                    projects[db] = []
            except Exception as e:
                logger.error(f"Project enrichment failed for {db}: {e}")
                projects[db] = []

    if routing.get("needs_mutations"):
        logger.info("Fetching mutation information...")
        for db, res in results.items():
            try:
                ids = extract_ids(res)
                if ids:
                    mutations[db] = run_mutation_sql(db, ids)
                    logger.info(f"Found {len(mutations[db])} mutations for {db}")
                else:
                    mutations[db] = []
            except Exception as e:
                logger.error(f"Mutation enrichment failed for {db}: {e}")
                mutations[db] = []

    # Step 5: Summarizer with conversation context
    logger.info("Step 5: Generating summary...")
    try:
        def has_meaningful_data(data_dict):
            if not data_dict:
                return False
            for key, value in data_dict.items():
                if isinstance(value, list) and len(value) > 0:
                    return True
                elif value and value != []:
                    return True
            return False
        
        # Build the dynamic prompt
        prompt_sections = []
        prompt_sections.append(f"USER QUERY: {user_query}")
        
        # Add context status to prevent hallucination
        context = conversation_manager.get_conversation_context()
        if context:
            prompt_sections.append(f"CONVERSATION CONTEXT (reference this if relevant):\n{context}")
        else:
            prompt_sections.append("CONVERSATION CONTEXT: None - treat as standalone query")
        
        # Add database results if available
        if has_meaningful_data(results):
            primary_json = json.dumps(results, indent=2, default=str)[:2000]
            prompt_sections.append(f"DATABASE RESULTS:\n{primary_json}")
            logger.info("Added database results to prompt")
        else:
            prompt_sections.append("DATABASE RESULTS: No results found in the database for this query.")
            logger.warning("No database results found")
        
        # Add project information if available
        if has_meaningful_data(projects):
            project_json = json.dumps(projects, indent=2, default=str)[:2000]
            prompt_sections.append(f"PROJECT INFORMATION:\n{project_json}")
            logger.info("Added project info to prompt")
        
        # Add mutation data if available
        if has_meaningful_data(mutations):
            mutation_json = json.dumps(mutations, indent=2, default=str)[:2000]
            prompt_sections.append(f"MUTATION DATA:\n{mutation_json}")
            logger.info("Added mutation data to prompt")
        
        # Load the base template and combine with data sections
        base_template = load_prompt("summarizer.txt")
        data_content = "\n\n".join(prompt_sections)
        summary_prompt = f"{base_template}\n\n{data_content}"
        
        logger.info(f"Summary prompt length: {len(summary_prompt)} chars")
        logger.info("Sending to LLM for final response...")
        
        answer = query_llm(summary_prompt, num_predict=800)
        logger.info(f"Final answer generated (length: {len(answer)})")
        
        return answer
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        import traceback
        traceback.print_exc()
        return f"I encountered an error processing your query: {user_query}. Please try rephrasing your question."
        
def build_sql_prompt(template_file, user_query, database):
    """Build SQL generation prompt for specific database"""
    try:
        template = load_prompt(template_file)
        return template.format(user_query=user_query, database=database)
    except Exception:
        return f"Generate a simple SQL query for {database} database based on: {user_query}"

def extract_ids(results):
    """Extract protein IDs from query results for enrichment"""
    if not results:
        return []
    
    protein_ids = set()
    for row in results:
        try:
            if 'id' in row and row['id'] is not None:
                protein_ids.add(row['id'])
            if 'l_protein_id' in row and row['l_protein_id'] is not None:
                protein_ids.add(row['l_protein_id'])
            if 'protein_id' in row and row['protein_id'] is not None:
                protein_ids.add(row['protein_id'])
        except Exception:
            continue
    
    return list(protein_ids)

def build_project_sql(database, protein_ids):
    """Build SQL to fetch project information"""
    if not protein_ids:
        return "SELECT 1 WHERE FALSE"
    
    ids_str = ','.join(map(str, protein_ids))
    
    if database == "scop3p":
        return f"""
        SELECT DISTINCT proj.project_id, proj.project_title, proj.species, 
               proj.publication_date, proj.submission_type, proj.tissues,
               p.protein_name, p.accession
        FROM project proj
        JOIN peptide pep ON proj.id = pep.l_project_id
        JOIN protein p ON pep.l_protein_id = p.id
        WHERE p.id IN ({ids_str})
        LIMIT 20
        """
    else:  # scop3ptm
        return f"""
        SELECT DISTINCT proj.project_id, proj.project_title, proj.species,
               proj.publication_date, proj.tissue, proj.disease, proj.instrument,
               p.protein_name, p.accession
        FROM project proj
        JOIN peptide_modification pm ON proj.id = pm.l_project_id
        JOIN protein p ON pm.l_protein_id = p.id
        WHERE p.id IN ({ids_str})
        LIMIT 20
        """

def reset_conversation():
    """Reset the conversation state"""
    global conversation_manager
    conversation_manager = ConversationManager(max_history=4)

def configure_conversation(max_history: int = 10):
    """Configure conversation memory limits"""
    global conversation_manager
    conversation_manager = ConversationManager(max_history=max_history)

def clean_sql_response(sql_response):
    """Clean SQL response from LLM by removing markdown and extra formatting"""
    if not sql_response:
        return ""
    
    sql = re.sub(r'^```\s*sql?\s*\n?', '', sql_response, flags=re.IGNORECASE | re.MULTILINE)
    sql = re.sub(r'\n?```\s*$', '', sql, flags=re.MULTILINE)
    return sql.strip()

def build_sql_prompt(template_file, user_query, database):
    """Build SQL generation prompt for specific database"""
    try:
        template = load_prompt(template_file)
        return template.format(user_query=user_query, database=database)
    except Exception as e:
        logger.error(f"Failed to build SQL prompt: {e}")
        return f"Generate a simple SQL query for {database} database based on: {user_query}"

def extract_ids(results):
    """Extract protein IDs from query results for enrichment"""
    if not results:
        return []
    
    protein_ids = set()
    for row in results:
        try:
            if 'id' in row and row['id'] is not None:
                protein_ids.add(row['id'])
            if 'l_protein_id' in row and row['l_protein_id'] is not None:
                protein_ids.add(row['l_protein_id'])
            if 'protein_id' in row and row['protein_id'] is not None:
                protein_ids.add(row['protein_id'])
        except Exception:
            continue
    
    return list(protein_ids)

def build_project_sql(database, protein_ids):
    """Build SQL to fetch project information"""
    if not protein_ids:
        return "SELECT 1 WHERE FALSE"
    
    ids_str = ','.join(map(str, protein_ids))
    
    if database == "scop3p":
        return f"""
        SELECT DISTINCT proj.project_id, proj.project_title, proj.species, 
               proj.publication_date, proj.submission_type, proj.tissues,
               p.protein_name, p.accession
        FROM project proj
        JOIN peptide pep ON proj.id = pep.l_project_id
        JOIN protein p ON pep.l_protein_id = p.id
        WHERE p.id IN ({ids_str})
        LIMIT 20
        """
    else:  # scop3ptm
        return f"""
        SELECT DISTINCT proj.project_id, proj.project_title, proj.species,
               proj.publication_date, proj.tissue, proj.disease, proj.instrument,
               p.protein_name, p.accession
        FROM project proj
        JOIN peptide_modification pm ON proj.id = pm.l_project_id
        JOIN protein p ON pm.l_protein_id = p.id
        WHERE p.id IN ({ids_str})
        LIMIT 20
        """

def safe_json_parse(json_string):
    """Safely parse JSON with fallback"""
    try:
        cleaned = clean_json_response(json_string)
        if not cleaned or cleaned == "{}":
            return {
                "mode": "sql",
                "db": "both",
                "needs_projects": False,
                "needs_mutations": False
            }
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return {
            "mode": "sql", 
            "db": "both",
            "needs_projects": False,
            "needs_mutations": False
        }

def clean_json_response(json_response):
    """Clean JSON response from LLM by removing markdown and extra text"""
    if not json_response or json_response.strip() == "":
        return "{}"
    
    json_str = re.sub(r'^```\s*json?\s*\n?', '', json_response, flags=re.IGNORECASE | re.MULTILINE)
    json_str = re.sub(r'\n?```\s*$', '', json_str, flags=re.MULTILINE)
    
    json_match = re.search(r'\{[^{}]*\}', json_str, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
    else:
        return "{}"
    
    return json_str.strip()