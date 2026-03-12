"""
Retrieve and format Meta Ads performance insights.

Usage:
    python src/get_insights.py --level campaign --date-preset last_7d \
        [--campaign-id 123] [--time-increment 1] \
        [--breakdowns age,gender] [--fields spend,impressions,clicks,ctr,cpc,cpm] \
        [--format table|json]
"""

import argparse
import json
import sys

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.exceptions import FacebookRequestError

from utils.api_client import init_api, get_account
from utils.logger import log_read


DEFAULT_FIELDS = [
    "campaign_name",
    "impressions",
    "reach",
    "clicks",
    "spend",
    "cpc",
    "cpm",
    "ctr",
    "actions",
    "cost_per_action_type",
    "frequency",
    "quality_ranking",
    "engagement_rate_ranking",
    "conversion_rate_ranking",
]

VALID_DATE_PRESETS = [
    "today", "yesterday", "this_month", "last_month",
    "this_quarter", "last_3d", "last_7d", "last_14d",
    "last_28d", "last_30d", "last_90d", "last_week_mon_sun",
    "last_week_sun_sat", "last_quarter", "last_year", "this_year",
]

VALID_LEVELS = ["account", "campaign", "adset", "ad"]
VALID_BREAKDOWNS = ["age", "gender", "country", "publisher_platform", "placement", "device_platform"]


def get_insights(
    level: str = "campaign",
    date_preset: str = "last_7d",
    object_id: str | None = None,
    fields: list | None = None,
    time_increment: int | None = None,
    breakdowns: list | None = None,
) -> list[dict]:
    """
    Pull insights from the Meta API.

    Returns list of insight dicts with requested metrics.
    """
    if date_preset not in VALID_DATE_PRESETS:
        print(f"WARNING: Unknown date_preset '{date_preset}'. Valid: {', '.join(VALID_DATE_PRESETS)}")

    fields = fields or DEFAULT_FIELDS
    params = {"date_preset": date_preset}

    if time_increment is not None:
        params["time_increment"] = time_increment
    if breakdowns:
        params["breakdowns"] = breakdowns

    # Determine API object
    if object_id:
        obj_classes = {
            "campaign": Campaign,
            "adset": AdSet,
            "ad": Ad,
        }
        obj_class = obj_classes.get(level)
        if obj_class:
            api_object = obj_class(object_id)
        else:
            api_object = get_account()
            params["level"] = level
    else:
        api_object = get_account()
        params["level"] = level

    log_read("get_insights", f"{api_object.get('id', 'account')}/insights", params)

    try:
        insights = api_object.get_insights(fields=fields, params=params)
        return [dict(insight) for insight in insights]

    except FacebookRequestError as e:
        print(f"META API ERROR [{e.api_error_code()}]: {e.api_error_message()}", file=sys.stderr)
        raise


def format_insights_table(insights: list[dict]) -> str:
    """Format insights as a readable text table."""
    if not insights:
        return "No data available for the selected time range."

    lines = []
    lines.append("=" * 80)
    lines.append("META ADS PERFORMANCE REPORT")
    lines.append("=" * 80)

    for i, row in enumerate(insights):
        if i > 0:
            lines.append("-" * 80)

        name = row.get("campaign_name") or row.get("adset_name") or row.get("ad_name") or f"Row {i+1}"
        lines.append(f"\n  {name}")

        # Key metrics
        spend = row.get("spend", "0")
        impressions = row.get("impressions", "0")
        reach = row.get("reach", "0")
        clicks = row.get("clicks", "0")
        ctr = row.get("ctr", "0")
        cpc = row.get("cpc", "0")
        cpm = row.get("cpm", "0")
        frequency = row.get("frequency", "N/A")

        lines.append(f"  Spend: ${float(spend):.2f}  |  Impressions: {impressions}  |  Reach: {reach}")
        lines.append(f"  Clicks: {clicks}  |  CTR: {float(ctr):.2f}%  |  CPC: ${float(cpc):.2f}  |  CPM: ${float(cpm):.2f}")
        lines.append(f"  Frequency: {frequency}")

        # Quality rankings
        quality = row.get("quality_ranking", "N/A")
        engagement = row.get("engagement_rate_ranking", "N/A")
        conversion = row.get("conversion_rate_ranking", "N/A")
        if quality != "N/A" or engagement != "N/A":
            lines.append(f"  Quality: {quality}  |  Engagement: {engagement}  |  Conversion: {conversion}")

        # Actions (conversions)
        actions = row.get("actions")
        if actions:
            lines.append("  Actions:")
            for action in actions:
                lines.append(f"    - {action.get('action_type', 'unknown')}: {action.get('value', 0)}")

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


def calculate_recommendations(insights: list[dict]) -> list[str]:
    """
    Generate optimization recommendations based on data.

    Checks for common issues and suggests improvements.
    """
    recommendations = []

    for row in insights:
        name = row.get("campaign_name") or row.get("adset_name") or "Entity"

        # CTR check
        ctr = float(row.get("ctr", 0))
        if ctr > 0 and ctr < 1.0:
            recommendations.append(
                f"LOW CTR ({ctr:.2f}%) on '{name}': Consider refreshing creative content. "
                f"Test new headlines, images, or ad formats."
            )

        # Frequency check
        freq_str = row.get("frequency")
        if freq_str and freq_str != "N/A":
            freq = float(freq_str)
            if freq > 3.5:
                recommendations.append(
                    f"HIGH FREQUENCY ({freq:.1f}) on '{name}': Audience fatigue detected. "
                    f"Expand targeting or refresh creative."
                )

        # Quality ranking check
        quality = row.get("quality_ranking", "")
        if quality == "BELOW_AVERAGE_10" or quality == "BELOW_AVERAGE_20":
            recommendations.append(
                f"LOW QUALITY RANKING on '{name}': Improve ad relevance. "
                f"Refine targeting or improve creative quality."
            )

        # CPC check (high CPC relative to spend)
        cpc = float(row.get("cpc", 0))
        if cpc > 5.0:
            recommendations.append(
                f"HIGH CPC (${cpc:.2f}) on '{name}': Consider broader targeting (Advantage+) "
                f"or testing different bid strategies."
            )

    if not recommendations:
        recommendations.append("Performance metrics look healthy. Continue monitoring.")

    return recommendations


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Get Meta Ads performance insights")
    parser.add_argument("--level", default="campaign", choices=VALID_LEVELS, help="Insight level")
    parser.add_argument("--date-preset", default="last_7d", help="Date range preset")
    parser.add_argument("--campaign-id", help="Specific campaign ID")
    parser.add_argument("--adset-id", help="Specific ad set ID")
    parser.add_argument("--ad-id", help="Specific ad ID")
    parser.add_argument("--time-increment", type=int, help="Time increment (1 for daily)")
    parser.add_argument("--breakdowns", help="Comma-separated breakdowns (age, gender, country, etc.)")
    parser.add_argument("--fields", help="Comma-separated fields to retrieve")
    parser.add_argument("--format", default="table", choices=["table", "json"], help="Output format")

    args = parser.parse_args()

    object_id = args.campaign_id or args.adset_id or args.ad_id
    if args.adset_id:
        level = "adset"
    elif args.ad_id:
        level = "ad"
    else:
        level = args.level

    fields = None
    if args.fields:
        fields = [f.strip() for f in args.fields.split(",")]

    breakdowns = None
    if args.breakdowns:
        breakdowns = [b.strip() for b in args.breakdowns.split(",")]

    try:
        init_api()
        insights = get_insights(
            level=level,
            date_preset=args.date_preset,
            object_id=object_id,
            fields=fields,
            time_increment=args.time_increment,
            breakdowns=breakdowns,
        )

        if args.format == "json":
            print(json.dumps(insights, indent=2, default=str))
        else:
            print(format_insights_table(insights))
            recs = calculate_recommendations(insights)
            print("\nRECOMMENDATIONS:")
            for i, rec in enumerate(recs, 1):
                print(f"  {i}. {rec}")

    except FacebookRequestError as e:
        print(f"META API ERROR [{e.api_error_code()}]: {e.api_error_message()}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
