"""
Meta Marketing API client wrapper.
Initializes the facebook-business SDK from environment variables.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

_api_instance: FacebookAdsApi | None = None
_account_instance: AdAccount | None = None


def _require_env(key: str) -> str:
    """Get a required environment variable or exit with error."""
    value = os.getenv(key)
    if not value:
        print(f"ERROR: Missing required environment variable: {key}", file=sys.stderr)
        print(f"Copy .env.example to .env and fill in your credentials.", file=sys.stderr)
        sys.exit(1)
    return value


def init_api() -> FacebookAdsApi:
    """Initialize and return the FacebookAdsApi singleton."""
    global _api_instance
    if _api_instance is not None:
        return _api_instance

    app_id = _require_env("META_APP_ID")
    app_secret = _require_env("META_APP_SECRET")
    access_token = _require_env("META_ACCESS_TOKEN")

    _api_instance = FacebookAdsApi.init(app_id, app_secret, access_token)
    return _api_instance


def get_api() -> FacebookAdsApi:
    """Get or create the API instance."""
    global _api_instance
    if _api_instance is None:
        return init_api()
    return _api_instance


def get_account() -> AdAccount:
    """Get the AdAccount object from META_AD_ACCOUNT_ID env var."""
    global _account_instance
    if _account_instance is not None:
        return _account_instance

    get_api()  # Ensure API is initialized
    account_id = _require_env("META_AD_ACCOUNT_ID")

    if not account_id.startswith("act_"):
        print(f"ERROR: META_AD_ACCOUNT_ID must start with 'act_', got: {account_id[:10]}...", file=sys.stderr)
        sys.exit(1)

    _account_instance = AdAccount(account_id)
    return _account_instance


def get_page_id() -> str:
    """Get META_PAGE_ID from environment."""
    return _require_env("META_PAGE_ID")
