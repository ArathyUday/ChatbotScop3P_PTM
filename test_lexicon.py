import sys
sys.path.append('.')

from lexicon import classify_query

def test_lexicon_routing():
    print("=== Testing Lexicon Routing ===")
    
    test_cases = [
        ("What are phosphorylation sites in p53?", "both"),
        ("Show me PTMs in BRCA1", "scop3ptm"), 
        ("Tell me about acetylation", "scop3ptm"),
        ("Find ubiquitin modifications", "scop3ptm"),
        ("What experiments studied this protein?", "llm"),
        ("Show mutations in TP53", "llm")
    ]
    
    for query, expected_db in test_cases:
        result = classify_query(query)
        print(f"Query: '{query}'")
        print(f"  Result: {result}")
        print(f"  Expected DB: {expected_db}, Got: {result.get('db', 'llm')}")
        print()

if __name__ == "__main__":
    test_lexicon_routing()