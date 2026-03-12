"""
Quick token validity check.
Verifies the Meta access token works and shows debug info.

Usage:
    python scripts/check_token.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
import requests

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def check_token():
    """Verify the Meta access token and show info."""
    token = os.getenv("META_ACCESS_TOKEN")
    if not token:
        print("ERROR: META_ACCESS_TOKEN not found in .env")
        return False

    # Check token with /me endpoint
    print("Checking token validity...")
    response = requests.get(
        "https://graph.facebook.com/v25.0/me",
        params={"access_token": token},
    )

    if response.status_code != 200:
        error = response.json().get("error", {})
        code = error.get("code", "unknown")
        message = error.get("message", "Unknown error")
        print(f"TOKEN INVALID - Error {code}: {message}")

        if code == 190:
            print("\nFix: Generate a new token at business.facebook.com")
            print("  1. Go to Business Settings > System Users")
            print("  2. Select your System User")
            print("  3. Generate new token with ads_management permission")
        return False

    data = response.json()
    print(f"Token VALID")
    print(f"  User/App: {data.get('name', 'N/A')}")
    print(f"  ID: {data.get('id', 'N/A')}")

    # Check debug info
    debug_response = requests.get(
        "https://graph.facebook.com/v25.0/debug_token",
        params={
            "input_token": token,
            "access_token": token,
        },
    )

    if debug_response.status_code == 200:
        debug_data = debug_response.json().get("data", {})
        expires = debug_data.get("expires_at", 0)
        if expires == 0:
            print("  Expires: Never (long-lived token)")
        else:
            from datetime import datetime
            exp_date = datetime.fromtimestamp(expires)
            print(f"  Expires: {exp_date.isoformat()}")

        scopes = debug_data.get("scopes", [])
        print(f"  Permissions: {', '.join(scopes)}")

        required = {"ads_management", "ads_read"}
        missing = required - set(scopes)
        if missing:
            print(f"\n  WARNING: Missing required permissions: {', '.join(missing)}")
        else:
            print("  All required permissions present")

    # Check ad account
    account_id = os.getenv("META_AD_ACCOUNT_ID")
    if account_id:
        acc_response = requests.get(
            f"https://graph.facebook.com/v25.0/{account_id}",
            params={
                "access_token": token,
                "fields": "name,account_status,currency,timezone_name",
            },
        )
        if acc_response.status_code == 200:
            acc_data = acc_response.json()
            status_map = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED", 7: "PENDING_RISK_REVIEW"}
            status = status_map.get(acc_data.get("account_status", 0), "UNKNOWN")
            print(f"\n  Ad Account: {account_id}")
            print(f"  Name: {acc_data.get('name', 'N/A')}")
            print(f"  Status: {status}")
            print(f"  Currency: {acc_data.get('currency', 'N/A')}")
            print(f"  Timezone: {acc_data.get('timezone_name', 'N/A')}")
        else:
            print(f"\n  WARNING: Cannot access ad account {account_id}")

    return True


if __name__ == "__main__":
    success = check_token()
    sys.exit(0 if success else 1)
