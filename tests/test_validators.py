"""Tests for src/utils/validators.py"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.validators import (
    validate_ad_account_id,
    validate_budget_cents,
    validate_date_iso8601,
    validate_objective,
    validate_status,
    validate_targeting,
    validate_creative_text,
    validate_cta_type,
    validate_special_ad_categories,
    validate_optimization_goal,
    ValidationError,
)


class TestAdAccountId:
    def test_valid_account_id(self):
        assert validate_ad_account_id("act_123456789") == "act_123456789"

    def test_valid_long_id(self):
        assert validate_ad_account_id("act_9999999999999") == "act_9999999999999"

    def test_missing_prefix(self):
        with pytest.raises(ValidationError):
            validate_ad_account_id("123456789")

    def test_wrong_prefix(self):
        with pytest.raises(ValidationError):
            validate_ad_account_id("acct_123")

    def test_empty_string(self):
        with pytest.raises(ValidationError):
            validate_ad_account_id("")

    def test_no_digits(self):
        with pytest.raises(ValidationError):
            validate_ad_account_id("act_abc")


class TestBudgetCents:
    def test_valid_budget(self):
        assert validate_budget_cents(5000) == 5000

    def test_minimum_budget(self):
        assert validate_budget_cents(100) == 100

    def test_zero_budget(self):
        with pytest.raises(ValidationError):
            validate_budget_cents(0)

    def test_negative_budget(self):
        with pytest.raises(ValidationError):
            validate_budget_cents(-100)

    def test_float_budget(self):
        with pytest.raises(ValidationError):
            validate_budget_cents(50.00)  # type: ignore

    def test_string_budget(self):
        with pytest.raises(ValidationError):
            validate_budget_cents("5000")  # type: ignore


class TestDateISO8601:
    def test_valid_date(self):
        assert validate_date_iso8601("2026-03-15T00:00:00") == "2026-03-15T00:00:00"

    def test_valid_date_with_timezone(self):
        assert validate_date_iso8601("2026-03-15T00:00:00-05:00") == "2026-03-15T00:00:00-05:00"

    def test_valid_date_only(self):
        assert validate_date_iso8601("2026-03-15") == "2026-03-15"

    def test_invalid_date(self):
        with pytest.raises(ValidationError):
            validate_date_iso8601("not-a-date")

    def test_empty_date(self):
        with pytest.raises(ValidationError):
            validate_date_iso8601("")


class TestObjective:
    def test_valid_objectives(self):
        for obj in ["OUTCOME_AWARENESS", "OUTCOME_TRAFFIC", "OUTCOME_ENGAGEMENT",
                     "OUTCOME_LEADS", "OUTCOME_APP_PROMOTION", "OUTCOME_SALES"]:
            assert validate_objective(obj) == obj

    def test_lowercase_input(self):
        assert validate_objective("outcome_traffic") == "OUTCOME_TRAFFIC"

    def test_invalid_objective(self):
        with pytest.raises(ValidationError):
            validate_objective("INVALID_OBJECTIVE")


class TestStatus:
    def test_paused_allowed(self):
        assert validate_status("PAUSED") == "PAUSED"

    def test_paused_lowercase(self):
        assert validate_status("paused") == "PAUSED"

    def test_active_rejected(self):
        with pytest.raises(ValidationError):
            validate_status("ACTIVE")


class TestTargeting:
    def test_valid_targeting(self):
        targeting = {"geo_locations": {"countries": ["US"]}, "age_min": 25, "age_max": 55}
        result = validate_targeting(targeting)
        assert result["geo_locations"]["countries"] == ["US"]

    def test_missing_geo(self):
        with pytest.raises(ValidationError):
            validate_targeting({"age_min": 25})

    def test_empty_geo(self):
        with pytest.raises(ValidationError):
            validate_targeting({"geo_locations": {}})

    def test_age_below_18(self):
        with pytest.raises(ValidationError):
            validate_targeting({"geo_locations": {"countries": ["US"]}, "age_min": 16})

    def test_age_above_65(self):
        with pytest.raises(ValidationError):
            validate_targeting({"geo_locations": {"countries": ["US"]}, "age_max": 70})

    def test_age_min_greater_than_max(self):
        with pytest.raises(ValidationError):
            validate_targeting({"geo_locations": {"countries": ["US"]}, "age_min": 55, "age_max": 25})

    def test_not_dict(self):
        with pytest.raises(ValidationError):
            validate_targeting("not a dict")  # type: ignore


class TestCreativeText:
    def test_valid_primary_text(self):
        assert validate_creative_text("Hello world", "primary_text") == "Hello world"

    def test_primary_text_too_long(self):
        with pytest.raises(ValidationError):
            validate_creative_text("x" * 2201, "primary_text")

    def test_headline_at_limit(self):
        assert validate_creative_text("x" * 40, "headline") == "x" * 40

    def test_headline_too_long(self):
        with pytest.raises(ValidationError):
            validate_creative_text("x" * 41, "headline")

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            validate_creative_text("x" * 31, "description")

    def test_unknown_field(self):
        with pytest.raises(ValidationError):
            validate_creative_text("text", "unknown_field")


class TestCTAType:
    def test_valid_ctas(self):
        for cta in ["LEARN_MORE", "SHOP_NOW", "SIGN_UP"]:
            assert validate_cta_type(cta) == cta

    def test_lowercase_input(self):
        assert validate_cta_type("learn_more") == "LEARN_MORE"

    def test_invalid_cta(self):
        with pytest.raises(ValidationError):
            validate_cta_type("INVALID_CTA")


class TestSpecialAdCategories:
    def test_empty_list(self):
        assert validate_special_ad_categories([]) == []

    def test_valid_categories(self):
        assert validate_special_ad_categories(["CREDIT", "HOUSING"]) == ["CREDIT", "HOUSING"]

    def test_invalid_category(self):
        with pytest.raises(ValidationError):
            validate_special_ad_categories(["INVALID"])

    def test_not_list(self):
        with pytest.raises(ValidationError):
            validate_special_ad_categories("CREDIT")  # type: ignore


class TestOptimizationGoal:
    def test_valid_goals(self):
        for goal in ["LINK_CLICKS", "LANDING_PAGE_VIEWS", "IMPRESSIONS"]:
            assert validate_optimization_goal(goal) == goal

    def test_lowercase(self):
        assert validate_optimization_goal("link_clicks") == "LINK_CLICKS"

    def test_invalid(self):
        with pytest.raises(ValidationError):
            validate_optimization_goal("INVALID_GOAL")
