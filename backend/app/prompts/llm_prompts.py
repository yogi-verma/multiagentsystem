"""
Centralized prompt templates for LLM operations
"""
from typing import Dict


class LLMPrompts:
    """
    Collection of prompt templates for different LLM capabilities.
    """
    
    @staticmethod
    
    
    def summarization(text: str, context: str = "") -> str:
        return f"""You are answering a user's question using retrieved business documents.

Question:
{text}

Conversation context:
{context}

Instructions:
- Give the direct answer first, not a meta-summary of the question.
- If the answer contains a numeric value, include the exact value.
- Keep the answer concise and factual.
- Do not say phrases like "The user is asking..." or "This question is about...".
- If the answer is not fully certain, say what is supported by the available data only.

Answer:"""
                
    @staticmethod
    def code_generation(description: str, language: str = "python") -> str:
        """
        Prompt template for code generation
        """
        return f"""Generate {language} code for the following task:

                     {description}

                      Code:"""
                      
    @staticmethod
    def question_answering(question: str, context: str = "") -> str:
        """
        Prompt template for question answering
        """
        return f"""Answer the following question based on the context provided:

                  Context: {context}
                  Question: {question}

                  Answer:"""
                  
    @staticmethod
    def reasoning(problem: str) -> str:
        """
        Prompt template for complex reasoning tasks
        """
        return f"""Solve the following problem step by step:

                      {problem}

                  Solution:"""
                  
    @staticmethod
    def chat_summary(user_message: str, conversation_history: str = "") -> str:
        """
        Prompt template for chat-based summarization with conversation context
        """
        history_section = f"\nConversation History:\n{conversation_history}\n" if conversation_history else ""

        return f"""You are a helpful AI assistant. Provide a clear and informative response to the user's question.
                {history_section}
            User Question: {user_message}

            Your Response:"""

    @staticmethod
    def grounded_answer(
        user_message: str,
        retrieved_documents: str,
        conversation_history: str = "",
    ) -> str:
        history_section = (
            f"\nConversation History:\n{conversation_history}\n"
            if conversation_history
            else ""
        )

        return f"""You are a helpful AI assistant answering strictly from retrieved documents and prior conversation context.

User Question:
{user_message}

Retrieved Documents:
{retrieved_documents}
{history_section}
Instructions:
- First understand the retrieved documents.
- Then use the conversation history only as supporting context.
- Answer the user's question directly and clearly.
- Do not say meta phrases like "the user is asking" or "based on the query".
- If the documents contain the exact value, return it explicitly.
- Keep the final answer concise but complete.
- If the documents do not contain enough information, say that clearly.

Final Answer:"""
            
    @staticmethod
    def get_all_templates() -> Dict[str, str]:
      
        return {
            "summarization": "Summarize text concisely with optional context",
            "code_generation": "Generate code in specified programming language",
            "question_answering": "Answer questions based on provided context",
            "reasoning": "Solve complex problems with step-by-step reasoning",
            "chat_summary": "Generate conversational responses with history awareness",
            "routing_decision": "Determine which agent(s) should handle a user request",
        }
        
    @staticmethod
    def custom_prompt(template: str, **kwargs) -> str:
        """
        Create a custom prompt from a template string with variable substitution
        
        Args:
            template: Template string with {variable} placeholders
            **kwargs: Variables to substitute in the template
            
        Returns:
            Formatted prompt string
            
        Example:
            >>> template = "Translate {text} to {language}"
            >>> LLMPrompts.custom_prompt(template, text="Hello", language="French")
            'Translate Hello to French'
        """
        return template.format(**kwargs)
    
        
    @staticmethod
    def routing_decision(user_message: str) -> str:
        """
        Prompt template for LLM-based routing decisions
        
        Args:
            user_message: The user's message to analyze for routing
            
        Returns:
            Formatted prompt string for routing decision
        """
        return f"""Analyze this user message and determine the best routing:

Message: "{user_message}"

Routing Options:
- greeting: Simple greetings like "hello", "hi", "hey"
- search: ONLY when user explicitly wants to see raw documents (e.g., "show me documents", "list documents")
- parallel: ALL questions that need answers from documents (e.g., "What is X?", "How much?", "Tell me about Y")

IMPORTANT: Questions asking for information should use "parallel" to search documents AND generate an answer.

Answer with ONE word only (greeting/search/parallel):"""