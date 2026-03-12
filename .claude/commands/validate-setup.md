# /validate-setup - Check Meta API Connection and Permissions

> **Your role:** Run diagnostic checks on the Meta Ads setup and report
> status of each component. Help the user fix any issues found.

## Checks to Run (in order)

### 1. Environment Variables
Verify .env exists and contains required variables:
- META_APP_ID
- META_APP_SECRET
- META_ACCESS_TOKEN
- META_AD_ACCOUNT_ID (must start with act_)
- META_PAGE_ID

**IMPORTANT:** Do NOT display the values, just confirm they exist and are non-empty.

### 2. Python Dependencies
```bash
python -c "import facebook_business; print(f'facebook-business {facebook_business.__version__}')"
python -c "import dotenv; print('python-dotenv OK')"
python -c "import requests; print(f'requests {requests.__version__}')"
```

### 3. MCP Server
Check that meta-ads MCP is configured in .mcp.json and responsive.
Use `/mcp` to verify the server is listed.

### 4. API Connection
Try a read-only call to verify the token works:
```bash
python -c "
from src.utils.api_client import init_api, get_account
init_api()
account = get_account()
print(f'Connected to: {account[\"id\"]}')
print(f'Account name: {account.api_get(fields=[\"name\"])[\"name\"]}')
"
```

### 5. Token Permissions
Check the token has the required permissions:
- ads_management
- ads_read
- pages_read_engagement (for creatives)

### 6. Account Status
Verify the ad account is active and not disabled or in review.

### 7. Project Structure
Verify all required directories and files exist:
- src/ (with all Python scripts)
- src/utils/ (with all utility modules)
- logs/ directory
- templates/ directory
- tests/ directory
- .env file
- requirements.txt

---

## Output Format

Present results as a checklist:
```
META ADS AGENT - SETUP VALIDATION
==================================

[x] Environment variables configured (5/5 present)
[x] Python dependencies installed (facebook-business vXX, python-dotenv, requests)
[x] MCP server (meta-ads) configured
[x] API token valid
[x] Ad account act_XXXX active
[x] Required permissions present
[x] Project structure complete

Overall: READY TO OPERATE
```

Or if issues found:
```
[ ] API token INVALID - Error 190: Token expired
    Fix: Generate a new System User token at business.facebook.com

Overall: ISSUES FOUND (1 critical, 0 warnings)
```
