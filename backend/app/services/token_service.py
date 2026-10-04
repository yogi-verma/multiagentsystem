from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt

from app.config.settings import settings

class TokenService:
    def create_access_token(self, subject: str) -> str:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.auth_token_expiry_minutes)
        payload: Dict[str, Any] = {
            "sub": subject,
            "exp": expires_at,
        }
        return jwt.encode(payload, settings.auth_secret_key, algorithm=settings.auth_algorithm)

    def decode_access_token(self, token: str) -> Dict[str, Any]:
        return jwt.decode(token, settings.auth_secret_key, algorithms=[settings.auth_algorithm])