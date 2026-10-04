from fastapi import Header, HTTPException

from app.config.settings import settings
from app.memory.redis_memory import RedisMemoryService
from app.models.auth_models import UserResponse
from app.services.auth_service import AuthService
from app.services.token_service import TokenService

memory_service = RedisMemoryService(settings.redis_url, settings.redis_ttl_seconds)
auth_service = AuthService(memory_service)
token_service = TokenService()


def get_current_user(authorization: str = Header(default="")) -> UserResponse:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token.")

    token = authorization.replace("Bearer ", "", 1).strip()
    try:
        payload = token_service.decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token subject is missing.")
        user = auth_service.get_user(email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found.")
        return user
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc

