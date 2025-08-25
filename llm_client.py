import requests
import json
import logging
from config import OLLAMA_GENERATE_URL, MODEL_NAME, NUM_CTX, NUM_PREDICT

logger = logging.getLogger(__name__)

def query_llm(prompt: str, num_ctx=NUM_CTX, num_predict=NUM_PREDICT) -> str:
    logger.info(f"Querying LLM with prompt length: {len(prompt)}")
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "options": {"num_ctx": num_ctx, "num_predict": num_predict}
    }
    
    try:
        r = requests.post(OLLAMA_GENERATE_URL, json=payload, stream=True)
        logger.info(f"LLM request sent, status: {r.status_code}")
        
        output = ""
        for line in r.iter_lines():
            if line:
                data = json.loads(line)
                if "response" in data:
                    output += data["response"]
        
        logger.info(f"LLM response received (length: {len(output)})")
        return output.strip()
        
    except Exception as e:
        logger.error(f"LLM query failed: {e}")
        raise