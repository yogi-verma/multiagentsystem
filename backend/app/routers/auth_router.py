import logging

from fastapi import APIRouter, HTTPException, status

from app.config.settings import settings
from app.memory.redis_memory import RedisMemoryService
from app.models.auth_models import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService
from app.services.token_service import TokenService


router = APIRouter(prefix=settings.api_prefix + "/auth", tags=["auth"])
logger = logging.getLogger(__name__)

memory_service = RedisMemoryService(settings.redis_url, settings.redis_ttl_seconds)
auth_service = AuthService(memory_service)
token_service = TokenService()

@router.post("/register",response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest) -> UserResponse:
    logger.info("Register request received.", extra={"user_id":request.email})
    try:
        user = auth_service.register_user(request)
        logger.info("Register request completed.", extra={"user_id": request.email})
        return user
    except ValueError as exc:
        logger.warning("Register request failed.", extra={"user_id": request.email, "reason": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
    
@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest) -> TokenResponse:
    logger.info("Login request received.", extra={"user_id": request.email})
    user = auth_service.authenticate_user(request)
    if not user:
        logger.warning("Login request rejected.", extra={"user_id": request.email})
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = token_service.create_access_token(user.email)
    logger.info("Login request completed.", extra={"user_id": user.email})
    return TokenResponse(access_token=token, email=user.email)