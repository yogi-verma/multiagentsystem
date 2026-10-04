import json
from typing import Optional

from app.memory.redis_memory import RedisMemoryService
from app.models.auth_models import LoginRequest, RegisterRequest, UserResponse
from app.utils.security import hash_password, verify_password

class AuthService:
    def __init__(self,memory_service: RedisMemoryService):
        self.memory_service = memory_service
        
    def register_user(self,request:RegisterRequest)->UserResponse:
        key = self.memory_service.user_key(request.email)
        existing = self.memory_service.get_value(key)
        
        if existing:
            raise ValueError("User Already Exists.")    
        
        payload = {
            "email": request.email,
            "hashed_password": hash_password(request.password)
        }
        
        self.memory_service.set_value(key, json.dumps(payload),ttl=-1)
        return UserResponse(email=request.email)
    
    def authenticate_user(self, request: LoginRequest) -> Optional[UserResponse]:
        key = self.memory_service.user_key(request.email)
        stored_user = self.memory_service.get_value(key)
        if not stored_user:
            return None

        payload = json.loads(stored_user)
        if not verify_password(request.password, payload["hashed_password"]):
            return None
        return UserResponse(email=request.email)
    
    
    def get_user(self, email: str) -> Optional[UserResponse]:
        key = self.memory_service.user_key(email)
        stored_user = self.memory_service.get_value(key)
        if not stored_user:
            return None
        payload = json.loads(stored_user)
        return UserResponse(email=payload["email"])