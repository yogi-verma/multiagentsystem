import logging

from app.config.settings import settings
from app.models.chat_models import AgentResult
from app.services.llm_service import LLMService
from app.state import GraphState

# Import Langfuse observe decorator if enabled
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

class SummaryAgent:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        
    @observe(name="summary_agent")
    async def run(self, state: GraphState) -> AgentResult:
        logger.info(
            "Summary agent started.",
            extra={
                "route": state.route,
                "message_preview": state.user_message[:120],
                "context_messages": len(state.conversation_context),
            },
        )
        summary = await self.llm_service.summarize(state.user_message, state.conversation_context)
        state.summary_output = summary
        logger.info(
            "Summary agent completed.",
            extra={"context_messages": len(state.conversation_context)},
        )
        return AgentResult(
            agent="summary",
            output=summary,
            metadata={"context_messages": len(state.conversation_context)},
        )