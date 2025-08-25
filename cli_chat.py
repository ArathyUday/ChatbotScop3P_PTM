import sys
import os
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

from pipeline import handle_query, reset_conversation, configure_conversation

def print_separator():
    print("=" * 60)

def print_bot_response(response):
    print(f"🤖 Bot: {response}")
    print()

def print_user_query(query):
    print(f"👤 You: {query}")

def show_help():
    print("""
Available commands:
  /help     - Show this help message
  /reset    - Reset conversation context
  /quit     - Exit the chat
  /test     - Run a quick test conversation
  
Just type your questions normally to chat with the bot!
    """)

def run_test_conversation():
    """Run a predefined test conversation"""
    print("\n Running test conversation...")
    print_separator()
    
    test_queries = [
        "Hi",
        "What is the ProteomeXchange ID?",
        "yes please",
        "Show me p53 phosphorylation sites",
        "What about mutations?",
        "Thank you"
    ]
    
    for query in test_queries:
        print_user_query(query)
        try:
            response = handle_query(query)
            print_bot_response(response)
        except Exception as e:
            print(f" Error: {e}\n")
        
        input("Press Enter to continue...")
    
    print(" Test conversation completed!")
    print_separator()

def main():
    print_separator()
    print(" Protein Modification Chatbot - CLI Interface")
    print("Enhanced with conversational memory!")
    print_separator()
    
    show_help()
    
    print("Start chatting! (Type /help for commands)")
    print_separator()
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.startswith('/'):
                command_parts = user_input.split()
                command = command_parts[0].lower()
                
                if command == '/quit' or command == '/exit':
                    print("👋 Goodbye!")
                    break
                elif command == '/help':
                    show_help()
                    continue
                elif command == '/reset':
                    reset_conversation()
                    print(" Conversation context reset!")
                    continue
                elif command == '/test':
                    run_test_conversation()
                    continue
                else:
                    print(f" Unknown command: {user_input}")
                    print("Type /help for available commands")
                    continue
            
            try:
                response = handle_query(user_input)
                print_bot_response(response)
            except Exception as e:
                print(f" Error processing query: {e}")
                print("Please try rephrasing your question or type /reset to start over.\n")
        
        except KeyboardInterrupt:
            print("\n\n Chat interrupted. Goodbye!")
            break
        except EOFError:
            print("\n\n Chat ended. Goodbye!")
            break

if __name__ == "__main__":
    main()