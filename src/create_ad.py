"""
Create a Meta Ad with creative content.

Usage:
    python src/create_ad.py --adset-id 456 --name "Ad 1" \
        --creative-name "Creative 1" \
        --primary-text "Your hook text here" \
        --headline "Short headline" \
        --description "Brief description" \
        --link "https://example.com" \
        --cta LEARN_MORE \
        [--image-path "./assets/ad-image.jpg"] \
        [--image-hash "abc123"] \
        [--dry-run]

Creates both the AdCreative and the Ad (both as PAUSED).
"""

import argparse
import json
import sys

from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adimage import AdImage
from facebook_business.exceptions import FacebookRequestError

from utils.api_client import init_api, get_account, get_page_id
from utils.validators import ValidationError, validate_creative_text, validate_cta_type
from utils.safety import check_ad_creation, SafetyViolation
from utils.logger import log_action


def upload_image(image_path: str) -> str:
    """Upload an image and return its hash."""
    account = get_account()
    image = AdImage(parent_id=account["id"])
    image[AdImage.Field.filename] = image_path
    image.remote_create()

    image_hash = image[AdImage.Field.hash]
    log_action(
        "upload_image",
        f"{account['id']}/adimages",
        {"filename": image_path},
        result={"image_hash": image_hash},
    )
    return image_hash


def create_creative(
    name: str,
    primary_text: str,
    headline: str,
    description: str,
    link: str,
    cta_type: str,
    image_hash: str | None = None,
    dry_run: bool = False,
) -> str | dict:
    """Create an ad creative and return its ID."""
    # Validate text lengths
    validate_creative_text(primary_text, "primary_text")
    validate_creative_text(headline, "headline")
    validate_creative_text(description, "description")
    cta_type = validate_cta_type(cta_type)

    page_id = get_page_id()

    link_data = {
        "link": link,
        "message": primary_text,
        "name": headline,
        "description": description,
        "call_to_action": {"type": cta_type},
    }

    if image_hash:
        link_data["image_hash"] = image_hash

    params = {
        "name": name,
        "object_story_spec": {
            "page_id": page_id,
            "link_data": link_data,
        },
    }

    account = get_account()
    endpoint = f"{account['id']}/adcreatives"

    if dry_run:
        log_action("create_creative", endpoint, params, status="dry_run")
        return {"dry_run": True, "params": params}

    try:
        creative = account.create_ad_creative(params=params)
        result = {"id": creative["id"], "name": name}
        log_action("create_creative", endpoint, params, result=result)
        return creative["id"]

    except FacebookRequestError as e:
        error_msg = f"Meta API Error {e.api_error_code()}: {e.api_error_message()}"
        log_action("create_creative", endpoint, params, error=error_msg, status="failed")
        raise


def create_ad(
    adset_id: str,
    name: str,
    creative_id: str,
    dry_run: bool = False,
) -> dict:
    """Create an ad referencing the creative. Always PAUSED."""
    params = {
        "name": name,
        "adset_id": adset_id,
        "creative": {"creative_id": creative_id},
        "status": "PAUSED",
    }

    # Safety check (Rule 1)
    params = check_ad_creation(params)

    account = get_account()
    endpoint = f"{account['id']}/ads"

    if dry_run:
        log_action("create_ad", endpoint, params, status="dry_run")
        return {"dry_run": True, "params": params}

    try:
        ad = account.create_ad(params=params)
        result = {
            "id": ad["id"],
            "name": name,
            "adset_id": adset_id,
            "creative_id": creative_id,
            "status": "PAUSED",
        }
        log_action("create_ad", endpoint, params, result=result)
        return result

    except FacebookRequestError as e:
        error_msg = f"Meta API Error {e.api_error_code()}: {e.api_error_message()}"
        log_action("create_ad", endpoint, params, error=error_msg, status="failed")
        raise


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Create a Meta Ad with creative (always PAUSED)")
    parser.add_argument("--adset-id", required=True, help="Parent ad set ID")
    parser.add_argument("--name", required=True, help="Ad name")
    parser.add_argument("--creative-name", help="Creative name (defaults to ad name + ' Creative')")
    parser.add_argument("--primary-text", required=True, help="Primary text (hook in first 125 chars)")
    parser.add_argument("--headline", required=True, help="Headline (max 40 chars, 27 visible on mobile)")
    parser.add_argument("--description", default="", help="Description (max 30 chars)")
    parser.add_argument("--link", required=True, help="Destination URL")
    parser.add_argument("--cta", default="LEARN_MORE", help="Call to action type")
    parser.add_argument("--image-path", help="Path to image file to upload")
    parser.add_argument("--image-hash", help="Pre-uploaded image hash (skip upload)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating")

    args = parser.parse_args()
    creative_name = args.creative_name or f"{args.name} Creative"

    try:
        init_api()

        # Upload image if path provided
        image_hash = args.image_hash
        if args.image_path and not image_hash:
            print(f"Uploading image: {args.image_path}")
            image_hash = upload_image(args.image_path)
            print(f"Image uploaded. Hash: {image_hash}")

        # Create creative
        print("Creating ad creative...")
        creative_result = create_creative(
            name=creative_name,
            primary_text=args.primary_text,
            headline=args.headline,
            description=args.description,
            link=args.link,
            cta_type=args.cta,
            image_hash=image_hash,
            dry_run=args.dry_run,
        )

        if args.dry_run:
            print("\n--- DRY RUN: Creative ---")
            print(json.dumps(creative_result, indent=2))
            # For dry run ad, use placeholder creative ID
            ad_result = create_ad(
                adset_id=args.adset_id,
                name=args.name,
                creative_id="DRY_RUN_CREATIVE_ID",
                dry_run=True,
            )
            print("\n--- DRY RUN: Ad ---")
            print(json.dumps(ad_result, indent=2))
            return

        creative_id = creative_result
        print(f"Creative created. ID: {creative_id}")

        # Create ad
        print("Creating ad...")
        ad_result = create_ad(
            adset_id=args.adset_id,
            name=args.name,
            creative_id=creative_id,
        )
        print(json.dumps(ad_result, indent=2))

    except (ValidationError, SafetyViolation) as e:
        print(f"VALIDATION ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except FacebookRequestError as e:
        print(f"META API ERROR [{e.api_error_code()}]: {e.api_error_message()}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
