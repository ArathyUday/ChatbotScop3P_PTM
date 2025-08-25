from pipeline import handle_query

# Test basic functionality
test_queries = [
    "What are the phosphorylation sites in p53?",
    "Show me PTMs in BRCA1",
    "Tell me about acetylation modifications"
]

for query in test_queries:
    try:
        result = handle_query(query)
        print(f"Query: {query}")
        print(f"Result: {result}\n")
    except Exception as e:
        print(f"Error with query '{query}': {e}\n")