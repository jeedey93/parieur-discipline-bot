"""
Analyze yesterday's predictions against actual results for a given sport.
Usage: python scripts/analyze_results.py --sport nhl|nba
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import date, timedelta
from dotenv import load_dotenv
from google import genai

load_dotenv()

PROMPTS = {
    "nhl": """\
You are a disciplined NHL betting analyst. Review the AI's predictions against the actual game results for {date}.

CRITICAL: Understand the difference between PUSH, WIN, and LOSS:
- PUSH: When the result EXACTLY equals the line. The stake is returned. This is NOT a loss, NOT a win. It's neutral.
  Example: Over 6.0 with exactly 6 total goals = PUSH
- WIN: When the bet wins
- LOSS: When the bet loses (but NOT when it's a push!)

For each recommended play:
- List the play header WITH ODDS AND CONFIDENCE (e.g., **Team ML vs Team @ odds - Confidence: High, Units: 1.5u**).
- Show the actual result: Actual Result: <away> <away_score> @ <home> <home_score> (Total goals: <total>)
- State the outcome: WIN, LOSS, or PUSH, with a short reason.
  - If the result EXACTLY equals the line, you MUST mark it as **PUSH** (not LOSS).

IMPORTANT: In the summary section, you MUST always include Total Pushes, even if it's 0.

After all plays, output:
---
Summary of AI Prediction Performance:
- Total Wins: <number>
- Total Losses: <number>
- Total Pushes: <number>

Use this exact format:

As a disciplined NHL betting analyst, I have reviewed the AI's predictions against the actual game results for {date}.

Here's the breakdown:

1.  **<PLAY HEADER WITH @ ODDS AND CONFIDENCE>**
    *   Actual Result: <away> <away_score> @ <home> <home_score> (Total goals: <total>)
    *   Outcome: **WIN**, **LOSS**, or **PUSH** (<short reason>)

---

**Summary of AI Prediction Performance:**

*   **Total Wins: <number>**
*   **Total Losses: <number>**
*   **Total Pushes: <number>**

AI Predictions:
{predictions}

Actual Results:
{actuals}
""",
    "nba": """\
You are a disciplined NBA betting analyst. Review the AI's predictions against the actual game results for {date}.

CRITICAL: Understand the difference between PUSH, WIN, and LOSS:
- PUSH: When the result EXACTLY equals the line. The stake is returned. This is NOT a loss, NOT a win. It's neutral.
  Example: Over 232.0 with exactly 232 total points = PUSH
  Example: Team -3.0 and team wins by exactly 3 points = PUSH
- WIN: When the bet wins
- LOSS: When the bet loses (but NOT when it's a push!)

For each recommended play:
- IMPORTANT: Always include the odds AND confidence/units in the bet header
  Example: **Los Angeles Lakers vs New Orleans Pelicans Under 243.0 @ 1.99 - Confidence: High, Units: 1.5u**
- For totals, compare predicted total to actual total points.
- For spreads, compare predicted spread to actual margin.
- For moneyline, state if the predicted team won or lost.
- If result exactly equals the line, mark as **PUSH** (not LOSS).

IMPORTANT: In the summary section, you MUST always include Total Pushes, even if it's 0.

Format exactly as:

As a disciplined NBA betting analyst, I have reviewed the AI's predictions against the actual game results for {date}.

Here's the breakdown:

1.  **<BET HEADER WITH @ ODDS AND CONFIDENCE>**
    *   Actual Result: <AWAY> <AWAY_SCORE> @ <HOME> <HOME_SCORE>
    *   Outcome: **WIN/LOSS/PUSH** (<short justification>)

---

**Summary of AI Prediction Performance:**

*   **Total Wins: X**
*   **Total Losses: Y**
*   **Total Pushes: Z**

---

AI Predictions:
{predictions}

Actual Results:
{actuals}
""",
}


def call_gemini(prompt):
    api_key = os.environ["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)
    models_to_try = [
        "models/gemini-2.5-flash",
        "models/gemini-3.8-flash",
        "models/gemini-2.5-flash-lite",
        "models/gemini-2.5-pro",
    ]
    retry_waits = [30, 60]

    for model in models_to_try:
        max_retries = len(retry_waits) + 1
        for attempt in range(max_retries):
            try:
                print(f"🤖 Trying {model}...")
                chat = client.chats.create(model=model)
                response = chat.send_message(prompt)
                return response.candidates[0].content.parts[0].text
            except genai.errors.ServerError as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    if attempt < max_retries - 1:
                        wait_time = retry_waits[attempt]
                        print(f"⚠️ {model} 503 error. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        print(f"⚠️ {model} still unavailable, trying next model...")
                        break
                else:
                    raise
            except genai.errors.ClientError as e:
                if "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e):
                    print(f"⚠️ {model} quota exceeded, trying next model...")
                    break
                else:
                    raise

    print("❌ All Gemini models unavailable. Cancelling workflow.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sport", required=True, choices=["nhl", "nba"], help="Sport to analyze")
    args = parser.parse_args()
    sport = args.sport

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    today_str = date.today().isoformat()

    predictions_file = f"data/predictions/{sport}/{sport}_daily_predictions_{yesterday}.txt"
    if not os.path.exists(predictions_file):
        print(f"⚠️  No predictions file for {yesterday} — skipping analysis.")
        sys.exit(0)

    with open(predictions_file, "r") as f:
        predictions_text = f.read()

    # Fetch actual results
    if sport == "nhl":
        from data.nhl_games import get_games_yesterday
        games = get_games_yesterday()
        actuals_text = "\n".join(
            f"{g['away']} {g['away_score']} @ {g['home']} {g['home_score']} (Total goals: {g['away_score'] + g['home_score']})"
            for g in games
        )
    else:
        from data.nba_games import get_nba_games_yesterday
        games = get_nba_games_yesterday()
        actuals_text = "\n".join(
            f"{g['away']} {g['away_score']} @ {g['home']} {g['home_score']}"
            for g in games
        )

    prompt = PROMPTS[sport].format(date=yesterday, predictions=predictions_text, actuals=actuals_text)
    summary = call_gemini(prompt)

    results_folder = os.path.join("data", "bot_results", sport, "2026-27")
    os.makedirs(results_folder, exist_ok=True)
    filename = os.path.join(results_folder, f"{sport}_daily_results_{today_str}.txt")

    with open(filename, "w") as f:
        f.write(summary)

    print(summary)


if __name__ == "__main__":
    main()
