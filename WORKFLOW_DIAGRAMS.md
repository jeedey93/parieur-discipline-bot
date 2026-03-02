# NBA Dual Predictions System - Visual Workflow

## Daily Timeline

```
MIDNIGHT
   |
   |
7:00 AM UTC ════════════════════════════════════════════════════════════════
   |
   ├─ GitHub Actions Triggers: nba_dual_predictions.yml
   │
   ├─ Set NBA_RUN_TIME=7am
   │
   ├─ Run: nba_predictions_daily_run.py
   │  ├─ Fetch NBA games (API)
   │  ├─ Fetch current odds (API)
   │  ├─ Generate predictions (Gemini AI)
   │  └─ Save to: nba_daily_predictions_7am_YYYY-MM-DD.txt ✅
   │
   └─ Commit to git ✅
      └─ Message: "Add NBA predictions for YYYY-MM-DD"

(5 HOURS PASS - Market evolves, lines move)

12:00 PM UTC ════════════════════════════════════════════════════════════════
   |
   ├─ GitHub Actions Triggers: nba_dual_predictions.yml
   │
   ├─ Set NBA_RUN_TIME=12pm
   │
   ├─ Run: nba_predictions_daily_run.py
   │  ├─ Fetch NBA games (API) - Updated!
   │  ├─ Fetch current odds (API) - Updated odds!
   │  ├─ Generate predictions (Gemini AI)
   │  └─ Save to: nba_daily_predictions_12pm_YYYY-MM-DD.txt ✅
   │
   ├─ Run: nba_predictions_compare.py
   │  ├─ Read 7am predictions
   │  ├─ Read 12pm predictions
   │  │
   │  ├─ Send to Gemini AI:
   │  │  "Compare morning vs noon predictions"
   │  │  "Analyze line movement impact"
   │  │  "Identify high-conviction plays"
   │  │  "Generate unified recommendations"
   │  │
   │  ├─ Generate: nba_daily_predictions_YYYY-MM-DD.txt (FINAL) ✅
   │  │
   │  └─ Delete temporary files ✅
   │     ├─ Delete: nba_daily_predictions_7am_YYYY-MM-DD.txt
   │     └─ Delete: nba_daily_predictions_12pm_YYYY-MM-DD.txt
   │
   └─ Commit to git ✅
      └─ Message: "Add NBA predictions for YYYY-MM-DD"
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 7:00 AM - MORNING RUN                                       │
└─────────────────────────────────────────────────────────────┘
         │
         ├─→ Odds API ───→ Current odds (Time: 7:00 AM)
         │
         ├─→ NBA Games API ───→ Today's matchups
         │
         └─→ Gemini AI (Morning Prompt)
              │
              ├─ Analyze games
              ├─ Check advanced metrics
              ├─ Generate picks
              │
              └─→ nba_daily_predictions_7am_YYYY-MM-DD.txt
                  ├─ Bet of the Day
                  ├─ Recommended plays
                  ├─ Confidence levels
                  └─ Odds at 7am


5 HOURS PASS
Market moves, sharps place bets, odds shift


┌─────────────────────────────────────────────────────────────┐
│ 12:00 PM - NOON RUN                                         │
└─────────────────────────────────────────────────────────────┘
         │
         ├─→ Odds API ───→ Updated odds (Time: 12:00 PM)
         │
         ├─→ NBA Games API ───→ Updated matchups
         │
         ├─→ Gemini AI (Noon Prompt)
         │   │
         │   ├─ Analyze games (new odds!)
         │   ├─ Check advanced metrics
         │   ├─ Generate picks
         │   │
         │   └─→ nba_daily_predictions_12pm_YYYY-MM-DD.txt
         │       ├─ Bet of the Day (updated!)
         │       ├─ Recommended plays (updated!)
         │       ├─ Confidence levels (updated!)
         │       └─ Odds at 12pm
         │
         └─→ COMPARISON PHASE
              │
              ├─→ Read 7am file
              │   └─ Extract plays and confidence levels
              │
              ├─→ Read 12pm file
              │   └─ Extract plays and confidence levels (updated)
              │
              ├─→ Send BOTH to Gemini AI for analysis:
              │   ├─ Compare plays
              │   ├─ Analyze confidence changes
              │   ├─ Track odds movements
              │   ├─ Identify new plays
              │   ├─ Identify removed plays
              │   └─ Generate unified recommendation list
              │
              ├─→ nba_daily_predictions_YYYY-MM-DD.txt (FINAL)
              │   ├─ 🏆 Bet of the Day (top play)
              │   ├─ Other plays (ranked by confidence)
              │   ├─ Notes on morning→noon changes
              │   └─ Combined analysis
              │
              └─→ Cleanup
                  ├─ Delete nba_daily_predictions_7am_YYYY-MM-DD.txt
                  └─ Delete nba_daily_predictions_12pm_YYYY-MM-DD.txt
```

---

## File Lifecycle

```
Timeline:
┌────────────────────────────────────────────────────────────────────┐
│                    DAILY PREDICTION CYCLE                          │
└────────────────────────────────────────────────────────────────────┘

7:00 AM
   ▼
[nba_daily_predictions_7am_2026-03-01.txt] ────→ EXISTS ✅
   │
   │ (5 hours pass)
   │
12:00 PM
   ▼
[nba_daily_predictions_12pm_2026-03-01.txt] ──→ EXISTS ✅
   │
   │ (COMPARISON)
   ▼
[nba_daily_predictions_2026-03-01.txt] ────────→ CREATED ✅
   │
   │ (CLEANUP)
   ▼
[nba_daily_predictions_7am_2026-03-01.txt] ────→ DELETED 🗑️
[nba_daily_predictions_12pm_2026-03-01.txt] ───→ DELETED 🗑️

FINAL STATE (for git):
   ▼
[nba_daily_predictions_2026-03-01.txt] ────────→ COMMITTED ✅
```

---

## Comparison Analysis Breakdown

```
MORNING PREDICTIONS (7:00 AM)
┌─────────────────────┐
│ BET OF THE DAY:     │
│ Team A -3.5 @ 1.91  │
│ Confidence: 62%     │
├─────────────────────┤
│ PLAY 2:             │
│ Team B ML @ 1.75    │
│ Confidence: 58%     │
├─────────────────────┤
│ PLAY 3:             │
│ Over 225.5 @ 1.94   │
│ Confidence: 55%     │
└─────────────────────┘
        │
        │ ANALYSIS ENGINE
        │ (Gemini AI)
        │
        ▼
  ┌──────────────────────────────────────────┐
  │ • Play A: SAME - Confidence now 65%      │
  │ • Play B: REMOVED - Lost edge            │
  │ • Play C: NEW - Added at noon            │
  │ • Play D: SAME - Confidence 58% → 60%    │
  └──────────────────────────────────────────┘
        │
        ▼
NOON PREDICTIONS (12:00 PM)
┌─────────────────────┐
│ BET OF THE DAY:     │
│ Team A -3.0 @ 1.93  │
│ Confidence: 65%     │
├─────────────────────┤
│ PLAY 2:             │
│ Team D +6.0 @ 1.95  │ ← NEW!
│ Confidence: 60%     │
├─────────────────────┤
│ PLAY 3:             │
│ Over 225.5 @ 1.94   │
│ Confidence: 57%     │
└─────────────────────┘
        │
        │
        ▼
FINAL COMBINED OUTPUT
┌──────────────────────────────────────────┐
│ 🏆 BET OF THE DAY                        │
│ Team A -3.0 @ 1.93                       │
│ Confidence: 65%                          │
│ Note: Appeared in both reports!          │
│       Confidence increased 62%→65%       │
├──────────────────────────────────────────┤
│ PLAY 2:                                  │
│ Team D +6.0 @ 1.95                       │
│ Confidence: 60%                          │
│ Note: New play added at noon             │
│       Line moved from +6.5 to +6.0       │
├──────────────────────────────────────────┤
│ PLAY 3:                                  │
│ Over 225.5 @ 1.94                        │
│ Confidence: 57%                          │
│ Note: Appeared in both reports           │
└──────────────────────────────────────────┘
```

---

## Environment Variables Flow

```
GitHub Actions Workflow
    │
    ├─ Set: NBA_RUN_TIME=7am
    │        ODDS_API_KEY=***
    │        GOOGLE_API_KEY=***
    │
    └─→ nba_predictions_daily_run.py
        │
        ├─ Reads NBA_RUN_TIME
        │  └─ Uses to set temp filename (7am)
        │
        ├─ Reads ODDS_API_KEY
        │  └─ Fetches odds data
        │
        └─ Reads GOOGLE_API_KEY
           └─ Calls Gemini AI for analysis


(5 hours later)

GitHub Actions Workflow
    │
    ├─ Set: NBA_RUN_TIME=12pm
    │        ODDS_API_KEY=***
    │        GOOGLE_API_KEY=***
    │
    ├─→ nba_predictions_daily_run.py
    │   (generates 12pm predictions)
    │
    └─→ nba_predictions_compare.py
        │
        ├─ Uses GOOGLE_API_KEY
        │  └─ Calls Gemini AI for comparison analysis
        │
        ├─ Reads 7am file (from disk)
        ├─ Reads 12pm file (from disk)
        └─ Generates final combined predictions
```

---

## Success Indicators ✅

**After 7:00 AM run:**
- ✅ File created: `nba_daily_predictions_7am_YYYY-MM-DD.txt`
- ✅ Commit made to git
- ✅ GitHub Actions shows green checkmark

**After 12:00 PM run:**
- ✅ File created: `nba_daily_predictions_12pm_YYYY-MM-DD.txt`
- ✅ File created: `nba_daily_predictions_YYYY-MM-DD.txt`
- ✅ Temp files deleted
- ✅ Commit made to git
- ✅ GitHub Actions shows green checkmark

**In git history:**
- ✅ Two commits for the day
- ✅ Only final predictions file in repository
- ✅ Clean git history (temp files not committed)

