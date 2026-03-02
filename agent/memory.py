import json
from typing import Optional
import redis as redis_lib
import config

SESSION_TTL_SECONDS = 3600  # 1 hour

class SessionMemory:
    def __init__(self, redis_client=None):
        if redis_client is not None:
            self._redis = redis_client
        else:
            self._redis = redis_lib.from_url(config.REDIS_URL, decode_responses=True)

    def _key(self, session_id: str) -> str:
        return f"atlas:session:{session_id}"

    def get(self, session_id: str) -> list[dict]:
        raw = self._redis.get(self._key(session_id))
        if raw is None:
            return []
        return json.loads(raw)

    def save(self, session_id: str, messages: list[dict]) -> None:
        self._redis.set(self._key(session_id), json.dumps(messages), ex=SESSION_TTL_SECONDS)

    def append(self, session_id: str, role: str, content: str) -> list[dict]:
        messages = self.get(session_id)
        messages.append({"role": role, "content": content})
        self.save(session_id, messages)
        return messages

    def clear(self, session_id: str) -> None:
        self._redis.delete(self._key(session_id))
