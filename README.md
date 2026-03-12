# Meta Ads Management Agent

CLI agent for managing Meta (Facebook/Instagram) ad campaigns through Claude Code with safety guardrails.

## How It Works

```
You (natural language) -> Claude Code -> MCP / Python Scripts -> Meta Marketing API v25.0
```

Claude Code acts as your Meta Ads manager. It uses the system prompt in `CLAUDE.md`, slash commands in `.claude/commands/`, and Python scripts in `src/` to create, manage, optimize, and report on campaigns.

## Safety Guarantees

- All new campaigns, ad sets, and ads are created as **PAUSED**
- Budgets > $100/day require explicit human confirmation
- Every write operation is logged to `logs/api_actions.log`
- Parameters are validated before any API call
- Failed writes are never retried automatically

## Prerequisites

- Python 3.10+
- Node.js 18+ (for MCP server)
- Claude Code installed
- Meta Business account with Marketing API access

## Setup

### 1. Clone and install

```bash
cd meta-ads-agent
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env with your Meta API credentials
```

### 3. Verify setup

```bash
python scripts/check_token.py
```

### 4. Start Claude Code

```bash
claude .
# Run /validate-setup to check everything
```

## Commands

| Command | Purpose |
|---------|---------|
| `/new-campaign` | Guided campaign creation (Campaign + Ad Set + Ad) |
| `/performance-report` | Pull metrics and get optimization recommendations |
| `/validate-setup` | Check API connection, token, permissions |
| `/optimize` | Data-driven optimization for active campaigns |

## Project Structure

```
├── CLAUDE.md              # Agent brain (safety rules, API reference)
├── .mcp.json              # MCP server config (meta-ads)
├── .env.example           # Credentials template
├── requirements.txt       # Python dependencies
├── Guia.md                # Setup guide and reference
├── src/
│   ├── create_campaign.py # Campaign creation
│   ├── create_adset.py    # Ad Set creation
│   ├── create_ad.py       # Ad + Creative creation
│   ├── get_insights.py    # Performance reporting
│   └── utils/
│       ├── api_client.py  # API client wrapper
│       ├── validators.py  # Parameter validation
│       ├── safety.py      # Safety rules engine
│       └── logger.py      # Audit logging
├── templates/             # Targeting presets, ad copy frameworks
├── tests/                 # Unit tests
├── logs/                  # Audit trail
├── scripts/               # Utility scripts
└── .claude/
    ├── commands/          # Slash commands
    ├── skills/meta-ads/   # Meta Ads skill
    └── prompts/           # Agentic loop patterns
```

## Running Scripts Directly

```bash
# Create campaign (dry run)
python src/create_campaign.py --name "Test" --objective OUTCOME_TRAFFIC --special-ad-categories "[]" --daily-budget 5000 --dry-run

# Get insights
python src/get_insights.py --level campaign --date-preset last_7d

# Check token
python scripts/check_token.py
```

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```
