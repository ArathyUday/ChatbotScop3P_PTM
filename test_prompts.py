import sys
sys.path.append('.')

from prompts import load_prompt

def test_prompt_loading():
    print("=== Testing Prompt Loading ===")
    
    required_prompts = ['router.txt', 'sql_scop3p.txt', 'sql_scop3ptm.txt', 'summarizer.txt']
    
    for prompt_file in required_prompts:
        try:
            content = load_prompt(prompt_file)
            print(f"{prompt_file}: {len(content)} characters loaded")
        except Exception as e:
            print(f"{prompt_file}: Failed to load - {e}")

if __name__ == "__main__":
    test_prompt_loading()