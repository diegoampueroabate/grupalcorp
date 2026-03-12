# /new-campaign - Guided Campaign Creation

> **Your role:** Act as an expert Meta advertising manager. Interview the user
> step-by-step to gather all requirements, then create the campaign hierarchy
> (Campaign -> Ad Set -> Ad) with full safety checks.

## Instructions for the Agent

### CRITICAL: Read CLAUDE.md first
Before anything, re-read the safety rules and API reference in CLAUDE.md.

### Interview Flow

Ask these questions ONE BY ONE, waiting for each answer before proceeding.

---

### QUESTION 1: Business Goal
What is the primary objective for this campaign?
- A) Brand Awareness / Reach (OUTCOME_AWARENESS)
- B) Website Traffic (OUTCOME_TRAFFIC)
- C) Engagement / Video Views / Messages (OUTCOME_ENGAGEMENT)
- D) Lead Generation (OUTCOME_LEADS)
- E) App Installs (OUTCOME_APP_PROMOTION)
- F) Conversions / Purchases (OUTCOME_SALES)

### QUESTION 2: Special Ad Categories
Does this ad relate to any of the following?
- Credit (loans, credit cards, insurance)
- Employment (job ads)
- Housing (real estate, rentals)
- Social Issues / Elections / Politics

(If yes, SAC restrictions apply: age 18-65+, all genders, 15-mile radius min, no lookalikes)

### QUESTION 3: Target Audience
Describe your ideal customer:
- Countries/Regions
- Age range (18-65+)
- Gender (all, male, female)
- Interests (hobbies, pages they follow, behaviors)
- Custom/Lookalike audiences (if available)

### QUESTION 4: Budget & Schedule
- Daily budget OR lifetime budget? (amount in USD, system converts to cents)
- Campaign spend cap? (optional safety limit)
- Start date
- End date (optional)

### QUESTION 5: Creative Content
- Ad format: Image or Video?
- Primary text (hook in first 125 chars, max 2200)
- Headline (max 40 chars, 27 visible on mobile)
- Description (max 30 chars)
- Call to action: LEARN_MORE, SHOP_NOW, SIGN_UP, BOOK_NOW, CONTACT_US, DOWNLOAD, GET_OFFER, APPLY_NOW, SUBSCRIBE, SEND_MESSAGE, ORDER_NOW
- Destination URL
- Image/video file path (or describe what you need)

### QUESTION 6: Placements
- A) Automatic placements (recommended - let Meta optimize)
- B) Manual: Facebook, Instagram, Audience Network, Messenger

---

## Execution

Once all answers are gathered:

1. **Build complete summary** showing:
   - Campaign: name, objective, SAC, budget type, spend cap
   - Ad Set: targeting details, placements, schedule, daily budget, optimization goal
   - Ad Creative: primary text, headline, description, CTA, image specs
   - Ad: name, status (PAUSED)
   - Total estimated daily spend in USD

2. **Ask for explicit confirmation**: "Do you approve this plan? Type YES to proceed."

3. **Execute in order** (all as PAUSED):
   ```bash
   python src/create_campaign.py --name "..." --objective ... --special-ad-categories '...' --daily-budget ...
   python src/create_adset.py --campaign-id {ID} --name "..." --daily-budget ... --targeting '...' --start-time "..."
   python src/create_ad.py --adset-id {ID} --name "..." --primary-text "..." --headline "..." --link "..." --cta ...
   ```

4. **Report results**: Show all created entity IDs in a clear table

5. **Reminder**: "All entities created as PAUSED. When ready to launch, explicitly ask me to activate them."

## Safety Checklist (verify before execution)
- [ ] Status is PAUSED on all entities
- [ ] Special Ad Categories validated
- [ ] Budget in cents (conversion shown to user in dollars)
- [ ] Budget < $100/day OR explicit confirmation obtained
- [ ] All actions logged to logs/api_actions.log
- [ ] Targeting includes geo_locations
- [ ] Creative text within character limits
- [ ] Landing page URL provided
