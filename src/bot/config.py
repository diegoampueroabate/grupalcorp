"""Bot configuration loaded from environment variables."""

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

# Set fallback values for optional Meta credentials so api_client doesn't exit
if not os.getenv("META_APP_ID"):
    os.environ["META_APP_ID"] = "0"
if not os.getenv("META_APP_SECRET"):
    os.environ["META_APP_SECRET"] = "none"


@dataclass(frozen=True)
class BotConfig:
    telegram_bot_token: str
    telegram_owner_id: int
    anthropic_api_key: str
    claude_model: str


def load_config() -> BotConfig:
    """Load and validate all required config from environment."""
    missing = []

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not telegram_bot_token:
        missing.append("TELEGRAM_BOT_TOKEN")

    telegram_owner_id = os.getenv("TELEGRAM_OWNER_ID", "")
    if not telegram_owner_id:
        missing.append("TELEGRAM_OWNER_ID")

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not anthropic_api_key:
        missing.append("ANTHROPIC_API_KEY")

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        print("Add them to your .env file.", file=sys.stderr)
        sys.exit(1)

    return BotConfig(
        telegram_bot_token=telegram_bot_token,
        telegram_owner_id=int(telegram_owner_id),
        anthropic_api_key=anthropic_api_key,
        claude_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
    )
