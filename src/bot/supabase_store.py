"""Persistent conversation store backed by Supabase."""

import logging

from supabase import create_client, Client

logger = logging.getLogger(__name__)

TABLE = "conversation_messages"
MAX_MESSAGES = 30  # ~15 user + ~15 assistant


class SupabaseConversationStore:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.client: Client = create_client(supabase_url, supabase_key)

    def add_message(self, chat_id: int, message: dict) -> None:
        """Insert a message into Supabase."""
        try:
            self.client.table(TABLE).insert({
                "chat_id": chat_id,
                "role": message["role"],
                "content": message["content"],
            }).execute()
        except Exception as e:
            logger.error(f"Failed to save message to Supabase: {e}")

    def get_messages(self, chat_id: int) -> list[dict]:
        """Retrieve the last MAX_MESSAGES for a chat, in chronological order."""
        try:
            result = (
                self.client.table(TABLE)
                .select("role, content")
                .eq("chat_id", chat_id)
                .order("created_at", desc=True)
                .limit(MAX_MESSAGES)
                .execute()
            )
            # Reverse to chronological order (oldest first)
            return [
                {"role": row["role"], "content": row["content"]}
                for row in reversed(result.data)
            ]
        except Exception as e:
            logger.error(f"Failed to load messages from Supabase: {e}")
            return []

    def clear(self, chat_id: int) -> None:
        """Delete all messages for a chat."""
        try:
            self.client.table(TABLE).delete().eq("chat_id", chat_id).execute()
        except Exception as e:
            logger.error(f"Failed to clear messages from Supabase: {e}")
