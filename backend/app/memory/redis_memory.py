import json
from typing import Dict, List, Optional

class RedisMemoryService:
    def __init__(self,url:str, ttl_seconds:int):
        self.url = url
        self.ttl_seconds = ttl_seconds
        self._client = None
        self._memory_store: Dict[str, List[Dict[str, str]]] = {}
        self._kv_store: Dict[str, str] = {}
        
        try:
            import importlib
            
            redis_module = importlib.import_module("redis")
            self._client = redis_module.from_url(url, decode_responses=True)
            self._client.ping()
        except Exception:
            self._client = None    
            
    def conversation_key(self, conversation_id: str) -> str:
        return f"conversation:{conversation_id}:messages"      
    
    def user_key(self, email: str) -> str:
        return f"user:{email}"
    
    def get_messages(self, conversation_id: str) -> List[Dict[str, str]]:
        if self._client:
            try:
                items = self._client.lrange(self.conversation_key(conversation_id), 0, -1)
                return [json.loads(item) for item in items]
            except Exception:
                return self._memory_store.get(conversation_id, [])
        return self._memory_store.get(conversation_id, [])
    
    
    
    def append_message(self, conversation_id: str, role: str, content: str) -> None:
        payload = {"role": role, "content": content}
        if self._client:
            try:
                key = self.conversation_key(conversation_id)
                self._client.rpush(key, json.dumps(payload))
                self._client.expire(key, self.ttl_seconds)
                return
            except Exception:
                pass
        self._memory_store.setdefault(conversation_id, []).append(payload)
        
    def clear_messages(self, conversation_id: str) -> None:
        if self._client:
            try:
                self._client.delete(self.conversation_key(conversation_id))
                return
            except Exception:
                pass
        self._memory_store.pop(conversation_id, None)

    def get_value(self, key: str) -> Optional[str]:
        if self._client:
            try:
                return self._client.get(key)
            except Exception:
                return self._kv_store.get(key)
        return self._kv_store.get(key)
    
    def set_value(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """
        Set a key-value pair in Redis or in-memory store.
        
        Args:
            key: The key to store
            value: The value to store
            ttl: Time to live in seconds. If None, uses default ttl_seconds.
                 If -1, stores permanently without expiration.
        """
        if self._client:
            try:
                if ttl == -1:
                    self._client.set(key, value)
                else:
                    expiry = ttl if ttl is not None else self.ttl_seconds
                    self._client.setex(key, expiry, value)
                return
            except Exception:
                pass
        self._kv_store[key] = value

    @property
    def using_redis(self) -> bool:
        return self._client is not None