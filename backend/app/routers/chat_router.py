import logging

from fastapi import APIRouter, Depends

from app.config.settings import settings
from app.dependencies.auth_dependencies import get_current_user
from app.memory.redis_memory import RedisMemoryService
from app.models.auth_models import UserResponse
from app.models.chat_models import ChatRequest, ChatResponse, ConversationContextResponse
from app.workflows.chat_workflow import ChatWorkflow

router = APIRouter(prefix=settings.api_prefix, tags=["chat"])
logger = logging.getLogger(__name__)

workflow = ChatWorkflow()
memory_service = RedisMemoryService(settings.redis_url, settings.redis_ttl_seconds)

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: UserResponse = Depends(get_current_user)) -> ChatResponse:
    logger.info(
        "Chat API request received.",
        extra={
            "user_id": current_user.email,
            "conversation_id": request.conversation_id or "new",
            "message_preview": request.message[:120],
        },
    )
    return await workflow.run(request)


@router.get("/conversations/{conversation_id}/context", response_model=ConversationContextResponse)
def get_conversation_context(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ConversationContextResponse:
    logger.info(
        "Conversation context requested.",
        extra={"user_id": current_user.email, "conversation_id": conversation_id},
    )
    messages = memory_service.get_messages(conversation_id)
    return ConversationContextResponse(
        conversation_id=conversation_id,
        message_count=len(messages),
        messages=messages,
    )
    
@router.delete("/conversations/{conversation_id}/context", response_model=ConversationContextResponse)
def clear_conversation_context(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ConversationContextResponse:
    logger.info(
        "Conversation context cleared.",
        extra={"user_id": current_user.email, "conversation_id": conversation_id},
    )
    memory_service.clear_messages(conversation_id)
    return ConversationContextResponse(
        conversation_id=conversation_id,
        message_count=0,
        messages=[],
    )

