# /performance-report - Pull and Analyze Ad Performance

> **Your role:** Act as a Meta Ads analyst. Pull performance data and provide
> actionable insights with specific optimization recommendations.

## Interview

### QUESTION 1: Scope
What do you want to analyze?
- A) Full account overview (all campaigns)
- B) Specific campaign (provide ID or name)
- C) Specific ad set
- D) Specific ad

### QUESTION 2: Time Range
- A) Last 7 days (default)
- B) Last 14 days
- C) Last 30 days
- D) Month to date
- E) Custom range (provide start/end dates)

### QUESTION 3: Granularity
- A) Daily breakdown
- B) Weekly
- C) Total (aggregated)

### QUESTION 4: Breakdowns (optional)
Want to break down by any of these?
- Age, Gender, Country, Placement, Device

---

## Execution

1. Run insights script:
   ```bash
   python src/get_insights.py --level {level} --date-preset {preset} [--campaign-id {id}] [--time-increment {inc}] [--breakdowns {breakdowns}]
   ```

2. Present key metrics table:
   | Metric | Value |
   |--------|-------|
   | Spend | $X.XX |
   | Impressions | X,XXX |
   | Reach | X,XXX |
   | Clicks | XXX |
   | CTR | X.XX% |
   | CPC | $X.XX |
   | CPM | $X.XX |
   | Frequency | X.X |
   | Conversions | XX |
   | Cost/Conversion | $X.XX |
   | ROAS | X.Xx |

3. Highlight top performers and underperformers

4. Flag issues:
   - Frequency > 3.5 = audience fatigue
   - CTR < 1% = creative needs refresh
   - Quality ranking: BELOW_AVERAGE = relevance problem
   - CPC > $5.00 = consider broader targeting
   - Spend pace anomalies

5. Provide 3-5 actionable recommendations ranked by expected impact

6. Suggest next steps:
   - A/B test opportunities
   - Budget shift recommendations
   - Creative refresh schedule
   - Audience expansion ideas
