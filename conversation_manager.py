import re
import logging
from typing import Dict, List, Any, Optional
from llm_client import query_llm
from prompts import load_prompt
import json

logger = logging.getLogger(__name__)

class ConversationState:
    def __init__(self, max_history: int = 5):
        self.last_query: Optional[str] = None
        self.last_response: Optional[str] = None
        self.conversation_history: List[Dict] = []
        self.max_history: int = max_history
        self.current_context: Dict[str, Any] = {}
    
    def add_exchange(self, user_query: str, bot_response: str):
        """Add a conversation exchange"""
        self.last_query = user_query
        self.last_response = bot_response
        
        exchange = {
            'user_query': user_query,
            'bot_response': bot_response,
            'timestamp': self._get_timestamp()
        }
        
        self.conversation_history.append(exchange)
        self.conversation_history = self.conversation_history[-self.max_history:]
    
    def get_context_string(self) -> str:
        """Get recent conversation as string for LLM"""
        if not self.conversation_history:
            return "No previous conversation"
        
        recent = self.conversation_history[-2:]  # Last 2 exchanges
        context_parts = []
        
        for exchange in recent:
            context_parts.append(f"User: {exchange['user_query']}")
            context_parts.append(f"Bot: {exchange['bot_response'][:300]}...")
        
        return "\n".join(context_parts)
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()

class ConversationManager:
    def __init__(self, max_history: int = 5):
        self.state = ConversationState(max_history)
    
    def classify_intent_with_llm(self, query: str) -> Dict[str, Any]:
        """Use LLM to classify intent using prompt template"""
        logger.info(f"Classifying intent for: '{query}'")
        
        try:
            # Load prompt template
            prompt_template = load_prompt("intent_classifier.txt")
            logger.info("Intent classifier prompt loaded successfully")
            
            # Prepare context
            context = self.state.get_context_string()
            current_context = json.dumps(self.state.current_context, indent=2) if self.state.current_context else "None"
            
            logger.info(f"Context: {context[:100]}...")
            logger.info(f"Current context: {current_context}")
            
            # Fill template
            prompt = prompt_template.format(
                context=context,
                current_context=current_context,
                user_query=query
            )
            
            logger.info(f"Sending prompt to LLM (length: {len(prompt)})")
            
            # Get LLM response
            response = query_llm(prompt, num_predict=300)
            logger.info(f"LLM raw response: {response}")
            
            parsed_result = self._parse_intent_response(response)
            logger.info(f"Parsed intent result: {parsed_result}")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            logger.info("Using fallback classification")
            return self._fallback_classification(query)
    
    def _parse_intent_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured data with better error handling"""
        try:
            logger.info(f"Attempting to parse response: {response[:200]}...")
            
            # Clean response - remove markdown formatting
            cleaned = re.sub(r'^```\s*json?\s*\n?', '', response, flags=re.IGNORECASE | re.MULTILINE)
            cleaned = re.sub(r'\n?```\s*$', '', cleaned, flags=re.MULTILINE)
            cleaned = cleaned.strip()
            
            logger.info(f"Cleaned response: {cleaned[:200]}...")
            
            # Try to find JSON object in the response
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            json_matches = re.findall(json_pattern, cleaned, re.DOTALL)
            
            if json_matches:
                # Try parsing each potential JSON match
                for json_candidate in json_matches:
                    try:
                        intent_data = json.loads(json_candidate)
                        logger.info(f"Successfully parsed JSON: {intent_data}")
                        
                        # Validate required fields
                        if 'intent' in intent_data and 'action' in intent_data:
                            logger.info("JSON validation passed")
                            return intent_data
                        else:
                            logger.warning(f"JSON missing required fields: {list(intent_data.keys())}")
                    except json.JSONDecodeError as je:
                        logger.warning(f"JSON parse attempt failed: {je}")
                        continue
            
            # If no valid JSON found, try to extract values manually
            logger.warning("No valid JSON found, attempting manual extraction")
            
            # Look for intent and action patterns
            intent_match = re.search(r'"intent":\s*"([^"]+)"', cleaned)
            action_match = re.search(r'"action":\s*"([^"]+)"', cleaned)
            
            if intent_match and action_match:
                manual_result = {
                    "intent": intent_match.group(1),
                    "action": action_match.group(1),
                    "confidence": 0.6,
                    "reasoning": "Manually extracted from malformed JSON"
                }
                logger.info(f"Manual extraction successful: {manual_result}")
                return manual_result
            
            raise ValueError("Could not extract valid intent data")
            
        except Exception as e:
            logger.error(f"Intent parsing completely failed: {e}")
            logger.info("Using fallback classification")
            return self._fallback_classification("")
    
    def _fallback_classification(self, query: str) -> Dict[str, Any]:
        """Simple fallback classification"""
        q = query.lower().strip()
        
        logger.info(f"Using fallback classification for: '{q}'")
        
        # Basic social detection
        if any(word in q for word in ["hi", "hello", "thank", "thanks", "great", "awesome"]):
            result = {
                "intent": "SOCIAL",
                "action": "DIRECT_RESPONSE",
                "direct_response": "Hello! I am here to help you with protein modification research. What would you like to know?",
                "confidence": 0.7
            }
            logger.info("Classified as SOCIAL")
            return result
        
        # Scientific definition questions
        if q.startswith("what is") or q.startswith("what are") or "explain" in q:
            result = {
                "intent": "INFORMATIONAL",
                "action": "DIRECT_RESPONSE", 
                "direct_response": "Let me explain that for you.",
                "confidence": 0.8
            }
            logger.info("Classified as INFORMATIONAL")
            return result
        
        # Basic contextual detection
        if q in ["yes", "no", "continue", "tell me more", "yes please"]:
            result = {
                "intent": "CONTEXTUAL", 
                "action": "EXPAND_PREVIOUS",
                "expansion_topic": "previous_topic",
                "confidence": 0.8
            }
            logger.info("Classified as CONTEXTUAL")
            return result
        
        # Default to database search
        result = {
            "intent": "RESEARCH",
            "action": "DATABASE_SEARCH",
            "resolved_query": query,
            "confidence": 0.5
        }
        logger.info("Classified as RESEARCH (default)")
        return result
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process query and return action plan"""
        intent_data = self.classify_intent_with_llm(query)
        action = intent_data.get("action", "DATABASE_SEARCH")
        
        # Update context with any new entities/topics
        if "entities_mentioned" in intent_data:
            self.state.current_context["recent_entities"] = intent_data["entities_mentioned"]
        if "topics_mentioned" in intent_data:
            self.state.current_context["recent_topics"] = intent_data["topics_mentioned"]
        
        result = {
            "action": action,
            "intent_data": intent_data,
            "skip_pipeline": action in ["DIRECT_RESPONSE", "EXPAND_PREVIOUS", "CLARIFY"]
        }
        
        if action == "DIRECT_RESPONSE":
            # For direct responses, use specialized knowledge from summarizer
            result["response"] = self._generate_informed_direct_response(query, intent_data)
        elif action == "EXPAND_PREVIOUS":
            result["response"] = self._expand_on_previous_topic(intent_data.get("expansion_topic"))
        elif action == "CLARIFY":
            result["response"] = "Could you please be more specific about what you'd like to know?"
        else:  # DATABASE_SEARCH
            result["query"] = intent_data.get("resolved_query") or query
        
        return result
    
    def _expand_on_previous_topic(self, topic: str) -> str:
        """Expand on the previous topic discussed"""
        if not self.state.last_response:
            return "I'd be happy to provide more information, but I'm not sure what specific topic you'd like me to expand on."
        
        # Check if the last response was substantive (not just a greeting)
        last_response = self.state.last_response.lower()
        greeting_patterns = ["hello!", "hi there!", "how can i help", "what would you like", "i'm happy to chat"]
        if any(pattern in last_response for pattern in greeting_patterns) and len(self.state.last_response) < 200:
            return "Of course! I'm here to help with any questions you have. What specific topic would you like to know more about?"
        
        # Check if we have substantive content to expand on
        if len(self.state.last_response) < 100:
            return "I'd be happy to provide more details. What specific aspect would you like me to elaborate on?"
        
        # Use LLM to expand on the previous response
        try:
            expand_prompt = f"""The user asked for more information about a topic we were discussing. Here's what I told them previously:

PREVIOUS RESPONSE: {self.state.last_response}

USER REQUEST: More information / elaboration

Provide additional helpful details about the same topic, building naturally on what was already discussed. Be conversational and informative. Focus on expanding the specific points that were mentioned.

IMPORTANT: Only reference what is shown in the previous response above. Do not invent or assume other discussions.

Response:"""
            
            response = query_llm(expand_prompt, num_predict=500)
            return response
        except Exception:
            return "I'd be happy to provide more details, but I'm having trouble accessing additional information right now. Could you ask a more specific question?"
    
    def _generate_informed_direct_response(self, query: str, intent_data: Dict) -> str:
        """Generate direct response using specialized knowledge from summarizer template"""
        try:
            # Load the summarizer template to get the specialized knowledge
            from prompts import load_prompt
            
            summarizer_template = load_prompt("summarizer.txt")
            
            # Extract just the knowledge base section (everything after "KEY KNOWLEDGE BASE:")
            knowledge_start = summarizer_template.find("KEY KNOWLEDGE BASE:")
            if knowledge_start != -1:
                knowledge_section = summarizer_template[knowledge_start:]
            else:
                knowledge_section = summarizer_template
            
            # Create informed response prompt
            informed_prompt = f"""You are an AI assistant who can understand the proteomics field well enough to answer user questions enthusiastically.

{knowledge_section}

USER QUERY: {query}

INSTRUCTIONS:
- Provide a direct, factual answer to the user's question
- Use the specialized knowledge base above when relevant
- Be conversational and helpful
- If the question relates to protein modifications, databases, or proteomics concepts covered in the knowledge base, reference that information
- Keep the response focused and informative

Response:"""
            
            response = query_llm(informed_prompt, num_predict=400)
            return response
            
        except Exception as e:
            logger.error(f"Informed response generation failed: {e}")
            # Fallback to simple direct response
            return intent_data.get("direct_response", "Hello! I'm here to help with your protein modification research. What would you like to know?")
    
    def record_interaction(self, user_query: str, bot_response: str):
        """Record completed interaction"""
        self.state.add_exchange(user_query, bot_response)
    
    def get_conversation_context(self) -> str:
        """Get conversation context for other prompts"""
        return self.state.get_context_string()
    
    def reset(self):
        """Reset conversation state"""
        self.state = ConversationState(self.state.max_history)