"""
Parameter validators for Meta Marketing API operations.
All validation happens BEFORE API calls to catch errors early.
"""

import re
from datetime import datetime


class ValidationError(Exception):
    """Raised when a parameter fails validation."""
    pass


VALID_OBJECTIVES = [
    "OUTCOME_AWARENESS",
    "OUTCOME_TRAFFIC",
    "OUTCOME_ENGAGEMENT",
    "OUTCOME_LEADS",
    "OUTCOME_APP_PROMOTION",
    "OUTCOME_SALES",
]

VALID_CTA_TYPES = [
    "LEARN_MORE", "SHOP_NOW", "SIGN_UP", "BOOK_NOW",
    "CONTACT_US", "DOWNLOAD", "GET_OFFER", "APPLY_NOW",
    "SUBSCRIBE", "SEND_MESSAGE", "ORDER_NOW",
]

VALID_SPECIAL_AD_CATEGORIES = [
    "CREDIT",
    "EMPLOYMENT",
    "HOUSING",
    "ISSUES_ELECTIONS_POLITICS",
]

VALID_OPTIMIZATION_GOALS = [
    "LINK_CLICKS", "LANDING_PAGE_VIEWS", "IMPRESSIONS", "REACH",
    "OFFSITE_CONVERSIONS", "LEAD_GENERATION", "POST_ENGAGEMENT",
    "VIDEO_VIEWS", "APP_INSTALLS", "QUALITY_LEAD",
    "ENGAGED_USERS", "CONVERSATIONS",
]

TEXT_LIMITS = {
    "primary_text": 2200,
    "headline": 40,
    "description": 30,
}


def validate_ad_account_id(account_id: str) -> str:
    """Ensure account ID starts with 'act_' followed by digits."""
    if not re.match(r"^act_\d+$", account_id):
        raise ValidationError(
            f"Invalid ad account ID: '{account_id}'. Must match format 'act_XXXXXXXXX' (act_ followed by digits)."
        )
    return account_id


def validate_budget_cents(amount: int, label: str = "budget") -> int:
    """Ensure budget is a positive integer (in cents)."""
    if not isinstance(amount, int):
        raise ValidationError(
            f"Invalid {label}: must be an integer (in cents), got {type(amount).__name__}. "
            f"Example: $50.00 = 5000 cents."
        )
    if amount <= 0:
        raise ValidationError(
            f"Invalid {label}: must be positive, got {amount}."
        )
    if amount < 100:
        print(f"WARNING: {label} is {amount} cents (${amount/100:.2f}). This is very low.")
    return amount


def validate_date_iso8601(date_str: str) -> str:
    """Validate ISO 8601 date format."""
    try:
        datetime.fromisoformat(date_str)
        return date_str
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid date format: '{date_str}'. Must be ISO 8601 (e.g., '2026-03-15T00:00:00-0500')."
        )


def validate_objective(objective: str) -> str:
    """Validate campaign objective is one of the allowed values."""
    objective = objective.upper()
    if objective not in VALID_OBJECTIVES:
        raise ValidationError(
            f"Invalid objective: '{objective}'. Must be one of: {', '.join(VALID_OBJECTIVES)}"
        )
    return objective


def validate_optimization_goal(goal: str) -> str:
    """Validate ad set optimization goal."""
    goal = goal.upper()
    if goal not in VALID_OPTIMIZATION_GOALS:
        raise ValidationError(
            f"Invalid optimization_goal: '{goal}'. Must be one of: {', '.join(VALID_OPTIMIZATION_GOALS)}"
        )
    return goal


def validate_status(status: str) -> str:
    """Ensure status is PAUSED (enforce safety rule #1)."""
    if status.upper() != "PAUSED":
        raise ValidationError(
            "Safety Rule #1: All new entities MUST be created with status PAUSED. "
            "Cannot create with status '{status}'. Change to ACTIVE must be done explicitly after review."
        )
    return "PAUSED"


def validate_special_ad_categories(categories: list) -> list:
    """Validate special ad category values."""
    if not isinstance(categories, list):
        raise ValidationError(
            f"special_ad_categories must be a list (use [] for none), got {type(categories).__name__}."
        )
    for cat in categories:
        if cat not in VALID_SPECIAL_AD_CATEGORIES:
            raise ValidationError(
                f"Invalid special ad category: '{cat}'. Must be one of: {', '.join(VALID_SPECIAL_AD_CATEGORIES)}"
            )
    return categories


def validate_targeting(targeting: dict) -> dict:
    """Validate targeting structure has required geo_locations."""
    if not isinstance(targeting, dict):
        raise ValidationError("Targeting must be a dictionary.")

    if "geo_locations" not in targeting:
        raise ValidationError(
            "Targeting must include 'geo_locations' with at least 'countries', 'regions', or 'cities'."
        )

    geo = targeting["geo_locations"]
    if not any(key in geo for key in ("countries", "regions", "cities", "zips", "geo_markets")):
        raise ValidationError(
            "geo_locations must contain at least one of: countries, regions, cities, zips, geo_markets."
        )

    age_min = targeting.get("age_min")
    if age_min is not None and age_min < 18:
        raise ValidationError(f"age_min must be at least 18, got {age_min}.")

    age_max = targeting.get("age_max")
    if age_max is not None and age_max > 65:
        raise ValidationError(f"age_max must be at most 65, got {age_max}.")

    if age_min and age_max and age_min > age_max:
        raise ValidationError(f"age_min ({age_min}) cannot be greater than age_max ({age_max}).")

    return targeting


def validate_creative_text(text: str, field: str) -> str:
    """Validate ad copy lengths against Meta specs."""
    max_length = TEXT_LIMITS.get(field)
    if max_length is None:
        raise ValidationError(f"Unknown text field: '{field}'. Valid fields: {', '.join(TEXT_LIMITS.keys())}")

    if len(text) > max_length:
        raise ValidationError(
            f"{field} exceeds max length: {len(text)}/{max_length} chars. Trim to fit."
        )
    return text


def validate_cta_type(cta: str) -> str:
    """Validate CTA is one of the allowed types."""
    cta = cta.upper()
    if cta not in VALID_CTA_TYPES:
        raise ValidationError(
            f"Invalid CTA type: '{cta}'. Must be one of: {', '.join(VALID_CTA_TYPES)}"
        )
    return cta
