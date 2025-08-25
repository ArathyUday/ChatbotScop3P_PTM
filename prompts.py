import os

def load_prompt(filename):
    """Load prompt template from prompts directory"""
    prompts_dir = os.path.join(os.path.dirname(__file__), 'prompts')
    filepath = os.path.join(prompts_dir, filename)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read().strip()