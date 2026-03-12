"""
Safety rules engine for Meta Ads operations.
Every write operation MUST pass through the appropriate check function before execution.
Implements the 10 Critical Safety Rules from CLAUDE.md.
"""

import os
from .validators import (
    ValidationError,
    validate_objective,
    validate_status,
    validate_budget_cents,
    validate_special_ad_categories,
    validate_targeting,
    validate_date_iso8601,
)

# Budget thresholds (in cents)
DEFAULT_MAX_DAILY_BUDGET = int(os.getenv("MAX_DAILY_BUDGET_CENTS", "10000"))  # $100.00
REQUIRE_CONFIRMATION_ABOVE = 10000  # $100.00


class SafetyViolation(Exception):
    """Raised when a safety rule would be violated."""
    pass


def check_campaign_creation(params: dict) -> dict:
    """
    Validate campaign creation params against safety rules.

    Enforces:
    - Rule 1: status must be PAUSED
    - Rule 6: budgets in cents
    - Rule 8: parameter validation
    - Rule 10: special_ad_categories must be explicitly provided
    """
    # Rule 1: Force PAUSED
    params["status"] = "PAUSED"

    # Validate objective
    if "objective" in params:
        params["objective"] = validate_objective(params["objective"])

    # Validate special_ad_categories (must be present, even if empty list)
    if "special_ad_categories" not in params:
        raise SafetyViolation(
            "special_ad_categories is required. Use [] if no special categories apply. "
            "Ask the user if their ads relate to: credit, employment, housing, or politics."
        )
    params["special_ad_categories"] = validate_special_ad_categories(params["special_ad_categories"])

    # Validate budget if present (CBO mode)
    for budget_field in ("daily_budget", "lifetime_budget", "spend_cap"):
        if budget_field in params and params[budget_field] is not None:
            params[budget_field] = validate_budget_cents(params[budget_field], budget_field)

    return params


def check_adset_creation(params: dict) -> dict:
    """
    Validate ad set creation params.

    Enforces:
    - Rule 1: status PAUSED
    - Rule 3: budget > $100/day requires confirmation
    - Rule 6: budgets in cents
    - Rule 8: targeting validation
    """
    # Rule 1: Force PAUSED
    params["status"] = "PAUSED"

    # Validate budget
    for budget_field in ("daily_budget", "lifetime_budget"):
        if budget_field in params and params[budget_field] is not None:
            params[budget_field] = validate_budget_cents(params[budget_field], budget_field)

    # Rule 3: Budget confirmation gate
    daily_budget = params.get("daily_budget")
    if daily_budget and daily_budget > REQUIRE_CONFIRMATION_ABOVE:
        raise SafetyViolation(
            f"Daily budget ${daily_budget/100:.2f} exceeds $100.00 threshold. "
            f"Requires explicit human confirmation before proceeding."
        )

    # Validate targeting
    if "targeting" in params:
        params["targeting"] = validate_targeting(params["targeting"])

    # Validate dates
    if "start_time" in params:
        validate_date_iso8601(params["start_time"])
    if "end_time" in params and params["end_time"]:
        validate_date_iso8601(params["end_time"])

    return params


def check_ad_creation(params: dict) -> dict:
    """Validate ad creation params. Enforce PAUSED status."""
    params["status"] = "PAUSED"

    if "adset_id" not in params or not params["adset_id"]:
        raise SafetyViolation("adset_id is required to create an ad.")

    if "creative" not in params or not params.get("creative", {}).get("creative_id"):
        raise SafetyViolation("creative with creative_id is required to create an ad.")

    return params


def check_budget_change(new_budget_cents: int, entity_type: str) -> dict:
    """
    Check if budget change requires human confirmation.
    Returns dict with 'requires_confirmation': bool and 'message': str.
    """
    validate_budget_cents(new_budget_cents, "new_budget")

    if new_budget_cents > REQUIRE_CONFIRMATION_ABOVE:
        return {
            "requires_confirmation": True,
            "message": (
                f"Budget change to ${new_budget_cents/100:.2f}/day for {entity_type} "
                f"exceeds $100.00 threshold. Requires explicit confirmation."
            ),
        }

    return {
        "requires_confirmation": False,
        "message": f"Budget ${new_budget_cents/100:.2f}/day for {entity_type} within safe limits.",
    }


def check_status_change(new_status: str, entity_type: str, entity_id: str) -> dict:
    """
    Warn when activating entities. Never auto-activate.
    Returns dict with warning info.
    """
    if new_status.upper() == "ACTIVE":
        return {
            "requires_confirmation": True,
            "message": (
                f"WARNING: You are about to ACTIVATE {entity_type} {entity_id}. "
                f"This will start spending real money. "
                f"Confirm you have reviewed: targeting, budget, creative, and compliance. "
                f"Type YES to confirm activation."
            ),
        }

    return {
        "requires_confirmation": False,
        "message": f"Status change to {new_status} for {entity_type} {entity_id}.",
    }


def get_environment() -> str:
    """Return current environment (development/staging/production)."""
    return os.getenv("ENVIRONMENT", "development")


def is_production() -> bool:
    """Check if running in production environment."""
    return get_environment() == "production"
