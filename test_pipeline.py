import sys
import logging

logging.getLogger().setLevel(logging.CRITICAL)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log', mode='a')
    ]
)
sys.path.append('.')

from pipeline import handle_query, reset_conversation

def test_full_pipeline():
    print("=== Testing Full Pipeline ===")

    sql_based_queries = [
    "What is the ProteomeXchange ID?",
    "How can I interpret the circles and their colors which show PTM sites?",
    "Explain CSS",
    "Why the AlphaFold prediction doesn't show the P-site?",
    "At what resolutions are the X-ray structures most confident?",
    "What is the difference between blue and red PTM sites?",
    "Is it possible to download the PDB structure with colored P-sites?",
    "What is \"E\" secondary structure?",
    "How is the \"Conserved scale\" calculated?",
    "One of the mutations in my favorite protein is associated with a disease — can I access the paper that has produced this result?",
    "In the phospho-sites table I see \"UP\" as a source. Is it as reliable as PRIDE?",
    "What does \"Combined\" evidence mean in the phospho-sites table?",
    "I am looking for a list of proteins with variants related to breast cancer.",
    "By P-site do you mean phosphorylation site or PTM site?",
    "Is it possible to search by modification? I need a list of proteins that go through ubiquitination.",
    "Why is my phosphorylation site not shown in the structure?",
    "How can I assess the functional relevance of a phosphorylation site using Scop3P data?",
    "Why are some phosphorylation sites observed in many experiments while others appear only once?",
    "What does it mean if a site is marked as \"singly phosphorylated\" in Scop3P?",
    "Can I use Scop3P data to infer kinase–substrate relationships?",
    "What if AlphaFold predicts a rigid helix where experimental P-sites cluster in loops? Who should I trust?",
    "Why do some structures have many mapped PTMs, while others with higher resolution show none?",
    "Can I integrate Scop3P with my mass spectrometry dataset for cross-validation?",
    "What is a USI and how does Scop3P use it?",
    "How does Scop3P link phosphorylation sites to the original experiments and authors?"
    ]
    
    for i, query in enumerate(sql_based_queries, 1):
        print(f"\n{'='*50}")
        print(f"Test {i}/{len(sql_based_queries)}: '{query}'")
        print('-' * 50)
        
        # Reset conversation before each query to treat as standalone
        reset_conversation()
        
        try:
            result = handle_query(query)
            print(f"Response: {result}")
        except Exception as e:
            print(f"Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Optional: Wait for user input to continue
        # input("Press Enter to continue to next test...")
        print(f"{'='*50}")

if __name__ == "__main__":
    test_full_pipeline()