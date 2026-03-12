"""
Create a Meta Ads ad set with targeting and budget validation.

Usage:
    python src/create_adset.py --campaign-id 123 --name "Ad Set 1" \
        --daily-budget 5000 --optimization-goal LINK_CLICKS \
        --targeting '{"geo_locations":{"countries":["US"]},"age_min":25,"age_max":55}' \
        --start-time "2026-03-15T00:00:00-0500" [--dry-run]

All ad sets are created as PAUSED (Safety Rule #1).
Budget > $100/day requires explicit confirmation (Safety Rule #3).
"""

import argparse
import json
import sys

from facebook_business.adobjects.adset import AdSet
from facebook_business.exceptions import FacebookRequestError

from utils.api_client import init_api, get_account
from utils.validators import ValidationError, validate_optimization_goal
from utils.safety import check_adset_creation, SafetyViolation
from utils.logger import log_action


def create_adset(
    campaign_id: str,
    name: str,
    daily_budget: int | None = None,
    lifetime_budget: int | None = None,
    billing_event: str = "IMPRESSIONS",
    optimization_goal: str = "LINK_CLICKS",
    targeting: dict | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    publisher_platforms: list | None = None,
    dry_run: bool = False,
) -> dict:
    """
    Create an ad set with full validation.

    Raises SafetyViolation if daily_budget > $100 (needs human confirmation).
    """
    optimization_goal = validate_optimization_goal(optimization_goal)

    params = {
        "campaign_id": campaign_id,
        "name": name,
        "billing_event": billing_event,
        "optimization_goal": optimization_goal,
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "status": "PAUSED",
    }

    if daily_budget is not None:
        params["daily_budget"] = daily_budget
    if lifetime_budget is not None:
        params["lifetime_budget"] = lifetime_budget
    if targeting is not None:
        params["targeting"] = targeting
    if start_time is not None:
        params["start_time"] = start_time
    if end_time is not None:
        params["end_time"] = end_time
    if publisher_platforms is not None:
        params["publisher_platforms"] = publisher_platforms

    # Safety checks (Rule 1, 3, 6, 8)
    params = check_adset_creation(params)

    account = get_account()
    endpoint = f"{account['id']}/adsets"

    if dry_run:
        log_action("create_adset", endpoint, params, status="dry_run")
        return {
            "dry_run": True,
            "params": params,
            "message": "DRY RUN: Ad set would be created with these params. No API call made.",
        }

    try:
        adset = account.create_ad_set(params=params)
        result = {
            "id": adset["id"],
            "name": name,
            "campaign_id": campaign_id,
            "status": "PAUSED",
            "daily_budget_usd": f"${(daily_budget or 0)/100:.2f}",
        }
        log_action("create_adset", endpoint, params, result=result)
        return result

    except FacebookRequestError as e:
        error_msg = f"Meta API Error {e.api_error_code()}: {e.api_error_message()}"
        log_action("create_adset", endpoint, params, error=error_msg, status="failed")
        raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Create a Meta Ads ad set (always PAUSED)")
    parser.add_argument("--campaign-id", required=True, help="Parent campaign ID")
    parser.add_argument("--name", required=True, help="Ad set name")
    parser.add_argument("--daily-budget", type=int, help="Daily budget in cents")
    parser.add_argument("--lifetime-budget", type=int, help="Lifetime budget in cents")
    parser.add_argument("--billing-event", default="IMPRESSIONS", help="Billing event (default: IMPRESSIONS)")
    parser.add_argument("--optimization-goal", default="LINK_CLICKS", help="Optimization goal")
    parser.add_argument("--targeting", required=True, help="Targeting JSON string")
    parser.add_argument("--start-time", help="Start time (ISO 8601)")
    parser.add_argument("--end-time", help="End time (ISO 8601, optional)")
    parser.add_argument("--publisher-platforms", help="Comma-separated platforms (omit for automatic)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating")

    args = parser.parse_args()

    try:
        targeting = json.loads(args.targeting)
    except json.JSONDecodeError:
        print(f"ERROR: --targeting must be valid JSON. Got: {args.targeting}")
        sys.exit(1)

    platforms = None
    if args.publisher_platforms:
        platforms = [p.strip() for p in args.publisher_platforms.split(",")]

    try:
        init_api()
        result = create_adset(
            campaign_id=args.campaign_id,
            name=args.name,
            daily_budget=args.daily_budget,
            lifetime_budget=args.lifetime_budget,
            billing_event=args.billing_event,
            optimization_goal=args.optimization_goal,
            targeting=targeting,
            start_time=args.start_time,
            end_time=args.end_time,
            publisher_platforms=platforms,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2))

    except (ValidationError, SafetyViolation) as e:
        print(f"VALIDATION ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except FacebookRequestError as e:
        print(f"META API ERROR [{e.api_error_code()}]: {e.api_error_message()}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
