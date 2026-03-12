"""Tests for src/utils/safety.py"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.safety import (
    check_campaign_creation,
    check_adset_creation,
    check_ad_creation,
    check_budget_change,
    check_status_change,
    SafetyViolation,
)
from src.utils.validators import ValidationError


class TestCampaignCreation:
    def test_forces_paused(self):
        params = {
            "name": "Test",
            "objective": "OUTCOME_TRAFFIC",
            "special_ad_categories": [],
            "status": "ACTIVE",
        }
        result = check_campaign_creation(params)
        assert result["status"] == "PAUSED"

    def test_requires_special_ad_categories(self):
        params = {
            "name": "Test",
            "objective": "OUTCOME_TRAFFIC",
        }
        with pytest.raises(SafetyViolation, match="special_ad_categories"):
            check_campaign_creation(params)

    def test_valid_campaign(self):
        params = {
            "name": "Test Campaign",
            "objective": "OUTCOME_TRAFFIC",
            "special_ad_categories": [],
            "daily_budget": 5000,
        }
        result = check_campaign_creation(params)
        assert result["status"] == "PAUSED"
        assert result["daily_budget"] == 5000

    def test_validates_objective(self):
        params = {
            "name": "Test",
            "objective": "INVALID",
            "special_ad_categories": [],
        }
        with pytest.raises(ValidationError):
            check_campaign_creation(params)


class TestAdsetCreation:
    def test_forces_paused(self):
        params = {
            "campaign_id": "123",
            "name": "Test",
            "daily_budget": 5000,
            "status": "ACTIVE",
        }
        result = check_adset_creation(params)
        assert result["status"] == "PAUSED"

    def test_budget_under_100_ok(self):
        params = {
            "campaign_id": "123",
            "name": "Test",
            "daily_budget": 5000,  # $50
        }
        result = check_adset_creation(params)
        assert result["daily_budget"] == 5000

    def test_budget_over_100_requires_confirmation(self):
        params = {
            "campaign_id": "123",
            "name": "Test",
            "daily_budget": 15000,  # $150
        }
        with pytest.raises(SafetyViolation, match="exceeds.*\\$100"):
            check_adset_creation(params)

    def test_validates_targeting(self):
        params = {
            "campaign_id": "123",
            "name": "Test",
            "daily_budget": 5000,
            "targeting": {"age_min": 16},  # Missing geo, age too low
        }
        with pytest.raises(ValidationError):
            check_adset_creation(params)


class TestAdCreation:
    def test_forces_paused(self):
        params = {
            "name": "Test Ad",
            "adset_id": "456",
            "creative": {"creative_id": "789"},
            "status": "ACTIVE",
        }
        result = check_ad_creation(params)
        assert result["status"] == "PAUSED"

    def test_requires_adset_id(self):
        params = {
            "name": "Test Ad",
            "creative": {"creative_id": "789"},
        }
        with pytest.raises(SafetyViolation, match="adset_id"):
            check_ad_creation(params)

    def test_requires_creative(self):
        params = {
            "name": "Test Ad",
            "adset_id": "456",
        }
        with pytest.raises(SafetyViolation, match="creative"):
            check_ad_creation(params)


class TestBudgetChange:
    def test_under_threshold(self):
        result = check_budget_change(5000, "adset")
        assert result["requires_confirmation"] is False

    def test_over_threshold(self):
        result = check_budget_change(15000, "adset")
        assert result["requires_confirmation"] is True

    def test_at_threshold(self):
        result = check_budget_change(10000, "adset")
        assert result["requires_confirmation"] is False


class TestStatusChange:
    def test_activate_requires_confirmation(self):
        result = check_status_change("ACTIVE", "campaign", "123")
        assert result["requires_confirmation"] is True

    def test_pause_no_confirmation(self):
        result = check_status_change("PAUSED", "campaign", "123")
        assert result["requires_confirmation"] is False
