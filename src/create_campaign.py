"""
Create a Meta Ads campaign with safety guardrails.

Usage:
    python src/create_campaign.py --name "My Campaign" --objective OUTCOME_TRAFFIC \
        --special-ad-categories "[]" [--daily-budget 5000] [--spend-cap 50000] [--dry-run]

All campaigns are created as PAUSED (Safety Rule #1).
Budget values are in CENTS (Safety Rule #6): $50.00 = 5000
"""

import argparse
import json
import sys

from facebook_business.adobjects.campaign import Campaign
from facebook_business.exceptions import FacebookRequestError

from utils.api_client import init_api, get_account
from utils.validators import ValidationError
from utils.safety import check_campaign_creation, SafetyViolation
from utils.logger import log_action


def create_campaign(
    name: str,
    objective: str,
    special_ad_categories: list,
    daily_budget: int | None = None,
    lifetime_budget: int | None = None,
    spend_cap: int | None = None,
    bid_strategy: str | None = None,
    dry_run: bool = False,
) -> dict:
    """
    Create a campaign via the Meta Marketing API.

    Returns dict with campaign ID and status, or error details.
    """
    params = {
        "name": name,
        "objective": objective,
        "special_ad_categories": special_ad_categories,
        "status": "PAUSED",
    }

    if daily_budget is not None:
        params["daily_budget"] = daily_budget
    if lifetime_budget is not None:
        params["lifetime_budget"] = lifetime_budget
    if spend_cap is not None:
        params["spend_cap"] = spend_cap
    if bid_strategy is not None:
        params["bid_strategy"] = bid_strategy

    # Safety checks (Rule 1, 6, 8, 10)
    params = check_campaign_creation(params)

    account = get_account()
    endpoint = f"{account['id']}/campaigns"

    if dry_run:
        log_action("create_campaign", endpoint, params, status="dry_run")
        return {
            "dry_run": True,
            "params": params,
            "message": "DRY RUN: Campaign would be created with these params. No API call made.",
        }

    try:
        campaign = account.create_campaign(params=params)
        result = {
            "id": campaign["id"],
            "name": name,
            "objective": objective,
            "status": "PAUSED",
        }
        log_action("create_campaign", endpoint, params, result=result)
        return result

    except FacebookRequestError as e:
        error_msg = f"Meta API Error {e.api_error_code()}: {e.api_error_message()}"
        log_action("create_campaign", endpoint, params, error=error_msg, status="failed")
        # Rule 9: Do NOT retry. Report and let user decide.
        raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Create a Meta Ads campaign (always PAUSED)")
    parser.add_argument("--name", required=True, help="Campaign name")
    parser.add_argument("--objective", required=True, help="Campaign objective (e.g., OUTCOME_TRAFFIC)")
    parser.add_argument(
        "--special-ad-categories", required=True,
        help='JSON list of special categories (use "[]" for none)',
    )
    parser.add_argument("--daily-budget", type=int, help="Daily budget in cents (CBO)")
    parser.add_argument("--lifetime-budget", type=int, help="Lifetime budget in cents (CBO)")
    parser.add_argument("--spend-cap", type=int, help="Campaign spend cap in cents")
    parser.add_argument("--bid-strategy", help="Bid strategy (e.g., LOWEST_COST_WITHOUT_CAP)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating")

    args = parser.parse_args()

    try:
        categories = json.loads(args.special_ad_categories)
    except json.JSONDecodeError:
        print(f"ERROR: --special-ad-categories must be valid JSON. Got: {args.special_ad_categories}")
        sys.exit(1)

    try:
        init_api()
        result = create_campaign(
            name=args.name,
            objective=args.objective,
            special_ad_categories=categories,
            daily_budget=args.daily_budget,
            lifetime_budget=args.lifetime_budget,
            spend_cap=args.spend_cap,
            bid_strategy=args.bid_strategy,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2))

    except (ValidationError, SafetyViolation) as e:
        print(f"VALIDATION ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except FacebookRequestError as e:
        print(f"META API ERROR [{e.api_error_code()}]: {e.api_error_message()}", file=sys.stderr)
        print("Do NOT retry automatically. Review the error and adjust parameters.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
