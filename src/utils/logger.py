"""
Audit logger for Meta Ads API operations.
All write operations are logged with timestamp, action, params, and result.
Logs to logs/api_actions.log in JSON format.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# Ensure logs directory exists
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / "api_actions.log"

# Secrets to redact from logs
_REDACT_KEYS = {"access_token", "app_secret", "META_ACCESS_TOKEN", "META_APP_SECRET"}

_logger: logging.Logger | None = None


def _setup_logger() -> logging.Logger:
    """Configure the audit logger with file and console handlers."""
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger("meta_ads_audit")
    _logger.setLevel(logging.INFO)

    # Avoid duplicate handlers
    if _logger.handlers:
        return _logger

    # File handler (JSON lines)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    # Console handler (human readable)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)

    return _logger


def redact_secrets(data: dict) -> dict:
    """Remove sensitive values from data before logging."""
    if not isinstance(data, dict):
        return data

    redacted = {}
    for key, value in data.items():
        if key.lower() in {k.lower() for k in _REDACT_KEYS}:
            redacted[key] = "***REDACTED***"
        elif isinstance(value, dict):
            redacted[key] = redact_secrets(value)
        elif isinstance(value, list):
            redacted[key] = [redact_secrets(item) if isinstance(item, dict) else item for item in value]
        else:
            redacted[key] = value
    return redacted


def log_action(
    action: str,
    endpoint: str,
    params: dict,
    result: dict | None = None,
    error: str | None = None,
    status: str = "success",
) -> None:
    """
    Log a write API action to the audit trail.

    Args:
        action: Human-readable action name (e.g., "create_campaign")
        endpoint: API endpoint called (e.g., "act_123/campaigns")
        params: Parameters sent (secrets are redacted)
        result: API response (IDs, status)
        error: Error message if failed
        status: "success", "failed", "dry_run"
    """
    logger = _setup_logger()

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "endpoint": endpoint,
        "params": redact_secrets(params),
        "status": status,
    }

    if result is not None:
        entry["result"] = result
    if error is not None:
        entry["error"] = error

    # Write JSON line to file
    logger.info(json.dumps(entry, ensure_ascii=False, default=str))


def log_read(action: str, endpoint: str, params: dict) -> None:
    """Log a read operation (lightweight, for debugging)."""
    logger = _setup_logger()

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "endpoint": endpoint,
        "params": redact_secrets(params),
        "type": "read",
    }

    logger.info(json.dumps(entry, ensure_ascii=False, default=str))
