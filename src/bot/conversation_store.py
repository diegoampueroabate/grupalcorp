"""In-memory conversation history with TTL and size limits."""

import time
from collections import defaultdict
from threading import Lock


class ConversationStore:
    def __init__(self, max_messages: int = 50, ttl_hours: int = 24):
        self.max_messages = max_messages
        self.ttl_seconds = ttl_hours * 3600
        self._conversations: dict[int, list[dict]] = defaultdict(list)
        self._last_activity: dict[int, float] = {}
        self._lock = Lock()

    def add_message(self, chat_id: int, message: dict) -> None:
        with self._lock:
            self._cleanup_expired()
            self._conversations[chat_id].append(message)
            self._last_activity[chat_id] = time.time()
            if len(self._conversations[chat_id]) > self.max_messages:
                self._conversations[chat_id] = self._conversations[chat_id][-self.max_messages:]

    def get_messages(self, chat_id: int) -> list[dict]:
        with self._lock:
            self._cleanup_expired()
            return list(self._conversations[chat_id])

    def clear(self, chat_id: int) -> None:
        with self._lock:
            self._conversations.pop(chat_id, None)
            self._last_activity.pop(chat_id, None)

    def _cleanup_expired(self) -> None:
        now = time.time()
        expired = [cid for cid, ts in self._last_activity.items()
                   if now - ts > self.ttl_seconds]
        for cid in expired:
            del self._conversations[cid]
            del self._last_activity[cid]
