import sys
sys.path.append('.')

from llm_client import query_llm

def test_llm_connection():
    print("=== Testing LLM Connection ===")
    
    try:
        # Simple test prompt
        response = query_llm("Hello, respond with just 'OK' if you can understand this.")
        print(f"LLM connected and responding: {response[:50]}...")
        
        # Test JSON generation
        json_prompt = '''Return this exact JSON: {"status": "working", "test": true}'''
        json_response = query_llm(json_prompt)
        print(f"JSON test response: {json_response}")
        
    except Exception as e:
        print(f"LLM connection failed: {e}")

if __name__ == "__main__":
    test_llm_connection()