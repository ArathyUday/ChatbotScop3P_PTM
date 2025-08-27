# Scientific Data Exploration Chatbot

A conversational interface for exploring Post-Translational Modifications (PTMs) in the Scop3P and Scop3PTM databases using Large Language Models.

## Overview

This chatbot enables researchers to query complex proteomics databases using natural language, eliminating the need for SQL expertise. Built with a hybrid architecture combining Llama3-8b-instruct with PostgreSQL databases, it provides accurate, scientifically grounded responses while maintaining conversational context.

### Key Features

- **Natural Language Querying**: Ask questions in plain English about proteins, modifications, and experimental data
- **Multi-Database Support**: Seamless access to both Scop3P (phosphorylation-focused) and Scop3PTM (120+ PTM types)
- **Conversational Memory**: Maintains context across multi-turn interactions
- **Scientific Accuracy**: Prevents hallucination through database-grounded responses
- **Domain Expertise**: Built-in knowledge of proteomics terminology and concepts

### Project Structure
```
scop3p-chatbot/
├── README.md                           # Comprehensive documentation
├── setup.sh                            # Environment setup
├── config.py                           # System configuration
├── app.py                              # Flask web application
├── cli_chat.py                         # Command-line interface
├── pipeline.py                         # Main processing pipeline
├── conversation_manager.py             # Multi-turn dialogue handling
├── db_utils.py                         # Database interface
├── llm_client.py                       # LLM communication
├── lexicon.py                          # Query classification
├── prompts.py                          # Prompt template loader
├── fetch_sql.py                        # SQL execution utility
├── prompts/                            # LLM prompt templates
├── tests/                              # Test suite
├── ChatbotTrainingData.xlsx            # Second Approach - Phi-3.5-mini training dataset
├── comprehensive_codet5_training.json  # Initial Approach - CodeT5-base training dataset
└── chatbot_results.txt                 # Evaluation results
```

### Core Components

- **Conversation Manager** (`conversation_manager.py`): Handles multi-turn dialogue and context
- **Pipeline** (`pipeline.py`): Main processing orchestrator
- **Query Router** (`lexicon.py`): Determines appropriate databases and query types
- **Database Layer** (`db_utils.py`): Unified interface to Scop3P and Scop3PTM
- **LLM Client** (`llm_client.py`): Manages Llama3-8b interactions
- **Prompt Templates** (`prompts/`): Specialized prompts for different tasks

## Quick Start

### Prerequisites

- Python 3.12.3
- PostgreSQL 14.19+
- Ollama (for local LLM deployment)
- 8GB+ RAM recommended
- CUDA-compatible GPU (optional, for faster inference)

### Installation

1. **Clone the repository**
    ```bash
    git clone https://github.com/ArathyUday/ChatbotScop3P_PTM.git
    cd ChatbotScop3P_PTM
    ```

2. **Set up conda environment**
    ```bash
    conda create -n ptmchat python=3.12.3 -y
    conda activate ptmchat

    # Install dependencies
    conda install pip -y
    pip install Flask==3.1.1
    pip install requests==2.32.3
    pip install psycopg2-binary==2.9.10
    pip install sqlalchemy==2.0.43
    conda install pandas -y
    ```

    Alternative: Use the setup script

    ```bash
    bash setup.sh
    ```


3. **Install Ollama and download Llama3**
   ```bash
   # Install Ollama (https://ollama.ai)
   ollama pull llama3:8b-instruct-q4_0
   ```

4. **Configure databases**
   - Update `config.py` with your PostgreSQL credentials
   - Ensure Scop3P and Scop3PTM databases are accessible

5. **Test the installation**
   ```bash
   python tests/test_db.py        # Test database connections
   python tests/test_llm.py       # Test LLM connection
   ```

## Usage

### Command Line Interface

```bash
python cli_chat.py
```

**Example conversation:**
```
You: What is the ProteomeXchange ID?
Bot: The ProteomeXchange ID (PXD) is a unique identifier linking phosphopeptides/PTMs to original PRIDE datasets...
```

### Web API

```bash
python app.py
```

**API Endpoints:**
- `POST /chat` - Send queries to the chatbot
- `POST /reset` - Reset conversation context
- `GET /health` - Health check

## Testing

Run the test suite:

```bash
# Run individual tests
python tests/test_basic.py
python tests/test_pipeline.py
python tests/test_sql_generation.py

```

## Configuration

Key settings in `config.py`:

```python
# Model Configuration
MODEL_NAME = "llama3:8b-instruct-q4_0"
NUM_CTX = 4096          # Context window
NUM_PREDICT = 512       # Max response tokens

# Database Settings
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME_SCOP3P = "scop3p"
DB_NAME_SCOP3PTM = "scop3ptm"
```