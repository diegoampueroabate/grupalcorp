"""Dispatch Claude tool_use calls to existing Python functions."""

import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Add src/ to path so existing modules can import their utils
_src_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from utils.api_client import init_api, get_account
from utils.safety import SafetyViolation
from utils.validators import ValidationError, validate_budget_cents, validate_targeting
from utils.logger import log_action

_executor = ThreadPoolExecutor(max_workers=3)


def _run_sync(func, *args, **kwargs):
    """Run a sync function in the thread pool."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(_executor, lambda: func(*args, **kwargs))


def _get_campaigns(status_filter: str = "ALL", limit: int = 25) -> str:
    """List campaigns from the ad account."""
    init_api()
    account = get_account()
    params = {"limit": limit}
    fields = ["name", "objective", "status", "daily_budget", "lifetime_budget", "start_time", "stop_time"]

    if status_filter != "ALL":
        params["filtering"] = [{"field": "effective_status", "operator": "IN", "value": [status_filter]}]

    campaigns = account.get_campaigns(fields=fields, params=params)
    result = []
    for c in campaigns:
        entry = {
            "id": c["id"],
            "name": c.get("name", ""),
            "objective": c.get("objective", ""),
            "status": c.get("status", ""),
        }
        if c.get("daily_budget"):
            entry["daily_budget_usd"] = f"${int(c['daily_budget'])/100:.2f}"
        if c.get("lifetime_budget"):
            entry["lifetime_budget_usd"] = f"${int(c['lifetime_budget'])/100:.2f}"
        result.append(entry)
    return json.dumps(result, ensure_ascii=False, default=str)


def _create_campaign(tool_input: dict) -> str:
    """Create a campaign via the existing create_campaign function."""
    from create_campaign import create_campaign as _create

    init_api()
    result = _create(
        name=tool_input["name"],
        objective=tool_input["objective"],
        special_ad_categories=tool_input.get("special_ad_categories", []),
        daily_budget=tool_input.get("daily_budget"),
        spend_cap=tool_input.get("spend_cap"),
        dry_run=tool_input.get("dry_run", False),
    )
    return json.dumps(result, ensure_ascii=False, default=str)


def _create_adset(tool_input: dict) -> str:
    """Create an ad set, handling budget confirmation bypass."""
    from create_adset import create_adset as _create

    init_api()
    budget_confirmed = tool_input.get("budget_confirmed", False)

    try:
        result = _create(
            campaign_id=tool_input["campaign_id"],
            name=tool_input["name"],
            daily_budget=tool_input.get("daily_budget"),
            optimization_goal=tool_input.get("optimization_goal", "LINK_CLICKS"),
            targeting=tool_input.get("targeting"),
            start_time=tool_input.get("start_time"),
            end_time=tool_input.get("end_time"),
            dry_run=tool_input.get("dry_run", False),
        )
        return json.dumps(result, ensure_ascii=False, default=str)

    except SafetyViolation as e:
        if budget_confirmed and "100" in str(e):
            # User confirmed high budget - bypass budget check, keep all other validations
            from facebook_business.adobjects.adset import AdSet

            params = {
                "campaign_id": tool_input["campaign_id"],
                "name": tool_input["name"],
                "billing_event": "IMPRESSIONS",
                "optimization_goal": tool_input.get("optimization_goal", "LINK_CLICKS"),
                "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
                "status": "PAUSED",
            }
            if tool_input.get("daily_budget"):
                params["daily_budget"] = validate_budget_cents(tool_input["daily_budget"], "daily_budget")
            if tool_input.get("targeting"):
                params["targeting"] = validate_targeting(tool_input["targeting"])
            if tool_input.get("start_time"):
                params["start_time"] = tool_input["start_time"]
            if tool_input.get("end_time"):
                params["end_time"] = tool_input["end_time"]

            account = get_account()
            endpoint = f"{account['id']}/adsets"
            adset = account.create_ad_set(params=params)
            result = {
                "id": adset["id"],
                "name": tool_input["name"],
                "campaign_id": tool_input["campaign_id"],
                "status": "PAUSED",
                "daily_budget_usd": f"${tool_input.get('daily_budget', 0)/100:.2f}",
                "budget_confirmed": True,
            }
            log_action("create_adset", endpoint, params, result=result)
            return json.dumps(result, ensure_ascii=False, default=str)
        raise


def _create_ad_with_creative(tool_input: dict, pending_images: dict, chat_id: int) -> str:
    """Create creative + ad in sequence."""
    from create_ad import upload_image, create_creative, create_ad as _create_ad

    init_api()
    image_hash = tool_input.get("image_hash")

    # Handle pending image from Telegram
    if tool_input.get("has_pending_image") and chat_id in pending_images:
        image_path = pending_images.pop(chat_id)
        image_hash = upload_image(image_path)
        try:
            os.unlink(image_path)
        except OSError:
            pass

    creative_name = f"{tool_input['ad_name']} Creative"
    dry_run = tool_input.get("dry_run", False)

    creative_result = create_creative(
        name=creative_name,
        primary_text=tool_input["primary_text"],
        headline=tool_input["headline"],
        description=tool_input.get("description", ""),
        link=tool_input["link"],
        cta_type=tool_input.get("cta_type", "LEARN_MORE"),
        image_hash=image_hash,
        dry_run=dry_run,
    )

    if dry_run:
        ad_result = _create_ad(
            adset_id=tool_input["adset_id"],
            name=tool_input["ad_name"],
            creative_id="DRY_RUN",
            dry_run=True,
        )
        return json.dumps({"creative": creative_result, "ad": ad_result}, ensure_ascii=False, default=str)

    creative_id = creative_result
    ad_result = _create_ad(
        adset_id=tool_input["adset_id"],
        name=tool_input["ad_name"],
        creative_id=creative_id,
    )
    return json.dumps({"creative_id": creative_id, "ad": ad_result}, ensure_ascii=False, default=str)


def _get_insights(tool_input: dict) -> str:
    """Pull insights and generate recommendations."""
    from get_insights import get_insights, format_insights_table, calculate_recommendations

    init_api()
    insights = get_insights(
        level=tool_input.get("level", "campaign"),
        date_preset=tool_input.get("date_preset", "last_7d"),
        object_id=tool_input.get("object_id"),
        time_increment=tool_input.get("time_increment"),
        breakdowns=tool_input.get("breakdowns"),
    )
    formatted = format_insights_table(insights)
    recs = calculate_recommendations(insights)
    result = {
        "formatted_table": formatted,
        "recommendations": recs,
        "raw_count": len(insights),
    }
    return json.dumps(result, ensure_ascii=False, default=str)


def _get_targeting_preset(preset_name: str) -> str:
    """Load a targeting preset from templates."""
    presets_path = Path(__file__).resolve().parent.parent.parent / "templates" / "targeting-presets.json"
    with open(presets_path, "r", encoding="utf-8") as f:
        presets = json.load(f)
    preset = presets.get(preset_name)
    if not preset:
        return json.dumps({"error": f"Preset '{preset_name}' no encontrado"})
    return json.dumps(preset, ensure_ascii=False)


def _get_ad_copy_template(template_name: str) -> str:
    """Load an ad copy template."""
    templates_path = Path(__file__).resolve().parent.parent.parent / "templates" / "ad-copy-templates.json"
    with open(templates_path, "r", encoding="utf-8") as f:
        templates = json.load(f)
    template = templates.get(template_name)
    if not template:
        return json.dumps({"error": f"Template '{template_name}' no encontrado"})
    return json.dumps(template, ensure_ascii=False)


def _check_token_status() -> str:
    """Check if the Meta token is valid."""
    import requests as req

    token = os.getenv("META_ACCESS_TOKEN")
    if not token:
        return json.dumps({"valid": False, "error": "META_ACCESS_TOKEN not set"})

    resp = req.get(
        "https://graph.facebook.com/v25.0/me",
        params={"access_token": token, "fields": "id,name"},
    )
    if resp.status_code != 200:
        error = resp.json().get("error", {})
        return json.dumps({"valid": False, "error_code": error.get("code"), "message": error.get("message")})

    user_data = resp.json()

    # Check token debug info
    debug_resp = req.get(
        "https://graph.facebook.com/v25.0/debug_token",
        params={"input_token": token, "access_token": token},
    )
    token_info = {}
    if debug_resp.status_code == 200:
        data = debug_resp.json().get("data", {})
        token_info = {
            "expires_at": data.get("expires_at", "never"),
            "is_valid": data.get("is_valid"),
            "scopes": data.get("scopes", []),
        }

    return json.dumps({"valid": True, "user": user_data, "token_info": token_info}, ensure_ascii=False)


async def execute_tool(tool_name: str, tool_input: dict, chat_id: int, pending_images: dict) -> str:
    """
    Execute a tool call and return the result as a JSON string.
    All exceptions are caught and returned as error JSON for Claude to interpret.
    """
    try:
        if tool_name == "get_campaigns":
            return await _run_sync(
                _get_campaigns,
                tool_input.get("status_filter", "ALL"),
                tool_input.get("limit", 25),
            )
        elif tool_name == "create_campaign":
            return await _run_sync(_create_campaign, tool_input)
        elif tool_name == "create_adset":
            return await _run_sync(_create_adset, tool_input)
        elif tool_name == "create_ad_with_creative":
            return await _run_sync(_create_ad_with_creative, tool_input, pending_images, chat_id)
        elif tool_name == "get_insights":
            return await _run_sync(_get_insights, tool_input)
        elif tool_name == "get_targeting_preset":
            return await _run_sync(_get_targeting_preset, tool_input["preset_name"])
        elif tool_name == "get_ad_copy_template":
            return await _run_sync(_get_ad_copy_template, tool_input["template_name"])
        elif tool_name == "check_token_status":
            return await _run_sync(_check_token_status)
        else:
            return json.dumps({"error": f"Herramienta desconocida: {tool_name}"})

    except SafetyViolation as e:
        return json.dumps({"safety_violation": True, "message": str(e)})
    except ValidationError as e:
        return json.dumps({"validation_error": True, "message": str(e)})
    except SystemExit:
        return json.dumps({"error": True, "message": "Error de configuracion. Verifica las variables de entorno en .env"})
    except Exception as e:
        return json.dumps({"error": True, "type": type(e).__name__, "message": str(e)})
