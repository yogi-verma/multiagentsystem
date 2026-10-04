import logging
from app.config.settings import settings
from app.prompts import LLMPrompts
from app.services.llm_service import LLMService, ModelCapability
from typing import Optional


if settings.langfuse_enabled:
    try:
        from langfuse import observe
    except ImportError:
        def observe(*args, **kwargs):
            def decorator(func):
                return func
            return decorator if args and callable(args[0]) else decorator
else:
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if args and callable(args[0]) else decorator

logger = logging.getLogger(__name__)

class SupervisorAgent:
    
    def __init__(self, llm_service: Optional[LLMService] = None, use_llm_routing: bool = True):
      
        self.llm_service = llm_service
        self.use_llm_routing = use_llm_routing and llm_service is not None
        
        if self.use_llm_routing:
            logger.info("Supervisor initialized with LLM-based routing")
        else:
            logger.info("Supervisor initialized with keyword-based routing")
    
    
    
    
    @observe(name="supervisor_decide_route")
    async def decide_route(self, message: str) -> str:
        """
        Decide which route to take based on the user message.
        
        Args:
            message: User's input message
            
        Returns:
            Route name: "greeting", "search", "summary", or "parallel"
        """
        if self.use_llm_routing:
            try:
                route = await self._llm_based_routing(message)
                logger.info(
                    "Supervisor selected route (LLM-based).",
                    extra={"route": route, "message_preview": message[:120]},
                )
                return route
            except Exception as e:
                logger.warning(
                    f"LLM routing failed, falling back to keyword-based: {e}",
                    extra={"message_preview": message[:120]}
                )
                return self._keyword_based_routing(message)
        else:
            route = self._keyword_based_routing(message)
            logger.info(
                "Supervisor selected route (keyword-based).",
                extra={"route": route, "message_preview": message[:120]},
            )
            return route
    
    @observe(name="llm_routing_decision")
    async def _llm_based_routing(self, message: str) -> str:
        
        prompt = LLMPrompts.routing_decision(user_message=message)
        
        logger.info(
            "Calling LLM for routing decision",
            extra={"message_preview": message[:100], "prompt_length": len(prompt)}
        )
        
        response = await self.llm_service.generate(
            prompt=prompt,
            capability=ModelCapability.QUESTION_ANSWERING,
            max_tokens=20,  
            temperature=0.0, 
        )
        
        logger.info(
            "LLM routing response received",
            extra={
                "raw_response": response,
                "response_length": len(response),
                "message_preview": message[:100]
            }
        )
        
        route = response.strip().lower()
        
        valid_routes = ["greeting", "search", "summary", "parallel"]
        for valid_route in valid_routes:
            if valid_route in route:
                logger.info(
                    f"LLM routing extracted '{valid_route}' from response",
                    extra={"raw_response": response}
                )
                return valid_route
            
        logger.warning(
            f"LLM returned invalid route, defaulting to 'parallel'",
            extra={
                "llm_response": response,
                "cleaned_response": route,
                "message_preview": message[:100]
            }
        )
        return "parallel"
    
    def _keyword_based_routing(self, message: str) -> str:
        lowered = message.strip().lower()
        
        search_only_keywords = ["show me documents", "list documents", "display documents"]
        greeting_keywords = [
            "hello",
            "hi",
            "hey",
            "bonjour",
            "good morning",
            "good afternoon",
            "good evening",
        ]
        
        if lowered in greeting_keywords:
            route = "greeting"
        elif any(keyword in lowered for keyword in search_only_keywords):
            route = "search"
        else:
            route = "parallel"
            
        logger.info(
            "Supervisor selected route.",
            extra={"route": route, "message_preview": message[:120]},
        )
        
        return route