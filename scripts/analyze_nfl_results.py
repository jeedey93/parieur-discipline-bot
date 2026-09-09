#!/usr/bin/env python3
"""Analyze NFL weekly predictions against actual results and save to data/bot_results/nfl/."""
import os
import sys
import re
import time
import glob
import requests
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from google import genai
from google.genai import types
import pytz

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
EASTERN = pytz.timezone("America/Toronto")


def get_nfl_scores_for_week(week_date_str):
    """Fetch completed NFL games. The Odds API scores endpoint supports max daysFrom=3,
    so this should be run within 3 days of the last game of the week (typically by Wednesday)."""
    url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/scores/?daysFrom=3&apiKey={ODDS_API_KEY}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"⚠️  Could not fetch scores: {e}")
        return []

    week_dt = datetime.strptime(week_date_str, "%Y-%m-%d")
    week_tuesday = week_dt - timedelta(days=(week_dt.weekday() - 1) % 7)
    week_monday = week_tuesday + timedelta(days=6)

    games = []
    for game in data:
        if not game.get("completed"):
            continue
        ct = game.get("commence_time")
        if not ct:
            continue
        try:
            game_date = datetime.fromisoformat(ct.replace("Z", "+00:00")).astimezone(EASTERN).date()
        except Exception:
            continue
        if week_tuesday.date() <= game_date <= week_monday.date():
            scores = game.get("scores") or []
            home_score = next((int(s["score"]) for s in scores if s.get("name") == game.get("home_team")), None)
            away_score = next((int(s["score"]) for s in scores if s.get("name") == game.get("away_team")), None)
            if home_score is None and len(scores) >= 2:
                home_score = int(scores[0]["score"]) if scores[0].get("score") else None
                away_score = int(scores[1]["score"]) if scores[1].get("score") else None
            games.append({
                "home": game.get("home_team"),
                "away": game.get("away_team"),
                "home_score": home_score,
                "away_score": away_score,
                "game_date": str(game_date),
            })
    return games


def get_latest_predictions_file():
    """Return (date_str, content) for the most recent NFL predictions file."""
    pattern = os.path.join("data", "predictions", "nfl", "nfl_weekly_predictions_*.txt")
    files = sorted(glob.glob(pattern))
    if not files:
        return None, None
    latest = files[-1]
    date_str = os.path.basename(latest).replace("nfl_weekly_predictions_", "").replace(".txt", "")
    with open(latest, "r", encoding="utf-8") as f:
        return date_str, f.read()


def parse_featured_picks(predictions_text):
    """Extract only the featured plays (SECTION 3) from predictions."""
    sec3 = re.search(r'SECTION\s*3[^\n]*\n(.*?)$', predictions_text, re.DOTALL | re.IGNORECASE)
    if not sec3:
        return ""
    block = sec3.group(1).strip()
    if 'no qualified' in block.lower():
        return ""
    return block


def analyze_with_gemini(predictions_text, actuals_text, week_date):
    api_key = os.environ["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)

    featured = parse_featured_picks(predictions_text)
    if not featured:
        return f"No featured plays were made for the week of {week_date}. Nothing to evaluate."

    prompt = f"""You are a disciplined NFL betting analyst. Review the AI's featured picks against actual game results for the NFL week of {week_date}.

CRITICAL: Understand WIN / LOSS / PUSH:
- PUSH: Result EXACTLY equals the line. Stake returned. NOT a loss or win.
  Example: Team -3.0 and they win by exactly 3 = PUSH
  Example: Over 44.5 with exactly 44.5 total points = PUSH (rare but possible)
- WIN: Bet wins
- LOSS: Bet loses

For each featured pick (BET OF THE WEEK and Other Recommended Plays):
- Match it to the actual game result
- Include the pick header with odds (e.g., **New York Jets ML vs Tennessee Titans @ 2.02**)
- Show actual result: Actual Result: <away> <away_score> @ <home> <home_score> (Total: <total>)
- State outcome: WIN, LOSS, or PUSH with short reason

After all picks, output:
---
Summary of AI Prediction Performance:
- Total Wins: <number>
- Total Losses: <number>
- Total Pushes: <number>

Format exactly:

As a disciplined NFL betting analyst, I have reviewed the AI's picks for the week of {week_date}.

Here's the breakdown:

1.  **<PICK HEADER WITH @ ODDS>**
    *   Actual Result: <AWAY> <AWAY_SCORE> @ <HOME> <HOME_SCORE> (Total: <TOTAL>)
    *   Outcome: **WIN/LOSS/PUSH** (<short reason>)

---

**Summary of AI Prediction Performance:**

*   **Total Wins: <number>**
*   **Total Losses: <number>**
*   **Total Pushes: <number>**

---

FEATURED PICKS TO EVALUATE:
{featured}

ACTUAL RESULTS:
{actuals_text}
"""

    models_to_try = [
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash",
        "models/gemini-2.0-flash-lite",
        "models/gemini-2.5-flash-lite",
    ]
    retry_waits = [30, 60]

    for model in models_to_try:
        for attempt in range(len(retry_waits) + 1):
            try:
                print(f"🤖 Trying {model}...")
                response = client.models.generate_content(
                    model=model,
                    contents=types.Part.from_text(text=prompt),
                )
                return response.candidates[0].content.parts[0].text
            except genai.errors.ServerError as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    if attempt < len(retry_waits):
                        print(f"⚠️  {model} 503. Retrying in {retry_waits[attempt]}s...")
                        time.sleep(retry_waits[attempt])
                    else:
                        print(f"⚠️  {model} still unavailable, trying next model...")
                        break
                else:
                    raise
            except genai.errors.ClientError as e:
                if "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e):
                    print(f"⚠️  {model} quota exceeded, trying next model...")
                    break
                else:
                    raise

    print("❌ All Gemini models unavailable.")
    sys.exit(1)


def main():
    date_str, predictions_text = get_latest_predictions_file()
    if not date_str:
        print("❌ No NFL predictions file found.")
        sys.exit(1)

    print(f"📋 Analyzing predictions for week of {date_str}...")

    scores = get_nfl_scores_for_week(date_str)
    if not scores:
        print("⚠️  No completed NFL games found for this week yet. Try again after games are played.")
        sys.exit(0)

    actuals_text = "\n".join(
        f"{g['away']} {g['away_score']} @ {g['home']} {g['home_score']} "
        f"(Total: {(g['home_score'] or 0) + (g['away_score'] or 0)}) — {g['game_date']}"
        for g in scores
        if g.get("home_score") is not None and g.get("away_score") is not None
    )

    if not actuals_text:
        print("⚠️  Scores not yet available (games may not be complete).")
        sys.exit(0)

    print(f"✅ Found {len(scores)} completed games")
    summary = analyze_with_gemini(predictions_text, actuals_text, date_str)

    results_dir = os.path.join("data", "bot_results", "nfl")
    os.makedirs(results_dir, exist_ok=True)
    today_str = date.today().isoformat()
    filename = os.path.join(results_dir, f"nfl_weekly_results_{today_str}.txt")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(summary)

    print(summary)
    print(f"\n✅ Saved to {filename}")


if __name__ == "__main__":
    main()
