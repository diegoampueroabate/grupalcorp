---
name: meta-ads
description: Meta Marketing API management skill for creating, managing, optimizing, and reporting on Facebook/Instagram ad campaigns with safety guardrails.
license: MIT
---

# Meta Ads Management Skill

## Purpose
Manage Meta advertising campaigns through Claude Code with safety guardrails.
Covers the full campaign lifecycle: creation, monitoring, optimization, and reporting.

## When to Use
- User wants to create a new ad campaign
- User asks for performance reports or metrics
- User needs optimization recommendations
- User wants to validate their Meta API setup
- Any operation involving the Meta Marketing API

## Available Commands

| Command | Purpose |
|---------|---------|
| `/new-campaign` | Guided interview to create Campaign + Ad Set + Ad |
| `/performance-report` | Pull and analyze ad performance with recommendations |
| `/validate-setup` | Check API connection, token, permissions, project structure |
| `/optimize` | Data-driven optimization recommendations for active campaigns |

## Safety Rules Summary
1. All new entities created as PAUSED
2. Budget >$100/day requires human confirmation
3. All budgets in CENTS ($50 = 5000)
4. Every write operation logged to logs/api_actions.log
5. No automatic retry on write failures
6. Never display .env contents or tokens

## Python Scripts

| Script | Purpose |
|--------|---------|
| `src/create_campaign.py` | Create campaign with safety checks |
| `src/create_adset.py` | Create ad set with targeting validation |
| `src/create_ad.py` | Create ad creative + ad |
| `src/get_insights.py` | Pull and format performance metrics |
| `scripts/check_token.py` | Quick token validity check |

## Reference Files
- `CLAUDE.md` - Complete safety rules and API reference
- `Guia.md` - Setup instructions and architecture overview
- `templates/` - Targeting presets and ad copy frameworks
- `tests/` - Unit tests for validators and safety module
