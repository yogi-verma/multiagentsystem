from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: Optional[str] = None
    history: List[ChatMessage] = Field(default_factory=list)
    
class SearchResult(BaseModel):
    title: str
    snippet: str
    score: float
    source: str
    page_number: Optional[int] = None
    file_name: Optional[str] = None

class AgentResult(BaseModel):
    agent: str
    output: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatResponse(BaseModel):
    conversation_id: str
    route: str
    answer: str
    agents_used: List[str]
    agent_results: List[AgentResult]
    cached: bool = False
    context_messages: int = 0

class ConversationContextResponse(BaseModel):
    conversation_id: str
    message_count: int
    messages: List[Dict[str, str]]