"""
Meta Ads Telegram Bot - Entry point.

Usage:
    python src/bot/main.py
"""

import sys
import logging
from pathlib import Path

# Add project root and src to path
_root = str(Path(__file__).resolve().parent.parent.parent)
_src = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)
if _src not in sys.path:
    sys.path.insert(0, _src)

from src.bot.config import load_config
from src.bot.telegram_handler import TelegramBot


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    # Suppress noisy httpx logs
    logging.getLogger("httpx").setLevel(logging.WARNING)

    config = load_config()
    print(f"Bot configurado. Owner ID: {config.telegram_owner_id}")
    print(f"Modelo Claude: {config.claude_model}")
    print("Iniciando polling de Telegram...")

    bot = TelegramBot(config)
    bot.run()


if __name__ == "__main__":
    main()
