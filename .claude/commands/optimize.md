# /optimize - Get Optimization Recommendations

> **Your role:** Analyze active/recent campaigns and provide data-driven
> optimization recommendations following Meta best practices.

## Process

### Step 1: Pull Data
Get last 7d and last 14d insights for comparison:
```bash
python src/get_insights.py --level campaign --date-preset last_7d --format json
python src/get_insights.py --level adset --date-preset last_7d --format json
python src/get_insights.py --level campaign --date-preset last_14d --format json
```

### Step 2: Analyze Each Campaign/Ad Set

Check for these signals:

**Learning Phase:**
- Ad sets need 50 conversions/week to exit learning
- If conversions < 50/week, consider consolidating ad sets or increasing budget

**Budget Utilization:**
- Underspend: budget too high for audience size, or bid too restrictive
- Overspend: check pacing settings

**Audience Saturation:**
- Frequency > 3.5 = audience fatigue, need to expand or refresh
- Trending up week-over-week = problem growing

**Creative Fatigue:**
- CTR declining over 7d vs 14d = creative needs refresh
- Suggest new variations every 7-14 days

**Bid Strategy:**
- Lowest Cost with stable CPA = good
- CPA increasing = consider Cost Cap
- CPA volatile = need more data or broader audience

**Placement Performance:**
- Compare CPAs across placements
- Disable placements with >2x average CPA (if using manual)

### Step 3: Generate Ranked Recommendations

Present recommendations in priority order:

```
OPTIMIZATION RECOMMENDATIONS
============================

1. [HIGH IMPACT] Budget Reallocation
   Campaign "X" has 3x better ROAS than "Y".
   Action: Shift 20% of Y's budget to X.
   Expected impact: ~15% improvement in overall ROAS.

2. [MEDIUM IMPACT] Creative Refresh
   Ad Set "Z" CTR dropped from 2.1% to 1.3% over 14 days.
   Action: Create 2-3 new ad variations with different hooks.
   Expected impact: CTR recovery to 1.8%+.

3. [LOW RISK] Audience Expansion
   Frequency at 4.2 on Ad Set "W".
   Action: Broaden age range or add related interests.
   Expected impact: Lower frequency, fresh reach.
```

### Safety Rules for Optimization
- Never recommend budget increase >20% at a time (resets learning phase)
- Always suggest testing changes on one ad set first
- All changes must go through human confirmation
- Present expected impact range for each recommendation
- If data is insufficient (< 1000 impressions), say so instead of guessing
