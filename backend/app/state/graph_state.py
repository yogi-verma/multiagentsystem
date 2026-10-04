from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.models.chat_models import ChatMessage, SearchResult

@dataclass
class GraphState:
    conversation_id: str
    user_message: str
    history: List[ChatMessage]
    conversation_context: List[Dict[str, str]] = field(default_factory=list)
    route: str = "summary"
    summary_output: str = ""
    search_output: str = ""
    search_results: Optional[List[SearchResult]] = None
    final_answer: str = ""