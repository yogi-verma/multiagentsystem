from fastapi import APIRouter

from app.config.settings import settings
from app.memory.redis_memory import RedisMemoryService
from app.services.search_service import SearchService

router = APIRouter(tags=["health"])

memory_service =  RedisMemoryService(settings.redis_url, settings.redis_ttl_seconds)
search_service = SearchService()

@router.get("/health")
def health() -> dict[str,object]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
        "llm_provider": settings.llm_provider,
        "redis_connected": memory_service.using_redis,
        "elasticsearch_connected": search_service.available,
    }