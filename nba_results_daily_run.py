import os
from data.nba_games import get_nba_games_yesterday
from datetime import date, timedelta
from google import genai
from google.genai import types
from datetime import date
from dotenv import load_dotenv

load_dotenv()

def analyze_results_with_actuals(results_text, actuals_text, date_str):
    api_key = os.environ["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)
    prompt = f"""
You are a disciplined NBA betting analyst. Your job is to review the AI's predictions against the actual game results for {{DATE}}.

For each recommended play:
- Match the prediction to the actual game result.
- For totals (over/under), compare the predicted total to the actual total points scored:
  - If the result exactly equals the line (e.g., Over 232.0 with exactly 232 points), it's a PUSH (stake returned, no profit/loss).
  - Otherwise, state if it is a WIN or LOSS (e.g., 'Outcome: WIN (234 is over 232.5)').
- For spreads, compare the predicted spread to the actual margin:
  - If the margin exactly equals the spread (e.g., -3.0 and team wins by exactly 3), it's a PUSH.
  - Otherwise, state if it is a WIN or LOSS (e.g., 'Outcome: WIN (Team covered -3.5)').
- For moneyline, state if the predicted team won or lost (e.g., 'Outcome: WIN (Team won)').
- For each play, output:
    * The bet header (as in the predictions)
    * The actual result (e.g., 'TeamA 110 @ TeamB 105')
    * The outcome (WIN/LOSS/PUSH) with a short justification

After all plays, output a summary section:
- Total Wins
- Total Losses
- Total Pushes

Format exactly as this example:

As a disciplined NBA betting analyst, I have reviewed the AI's predictions against the actual game results for {{DATE}}.

Here's the breakdown:

1.  **<BET HEADER>**
    *   Actual Result: <AWAY> <AWAY_SCORE> @ <HOME> <HOME_SCORE>
    *   Outcome: **WIN/LOSS/PUSH** (<short justification>)

---

**Summary of AI Prediction Performance:**

*   **Total Wins: X**
*   **Total Losses: Y**
*   **Total Pushes: Z**

---

AI Predictions:
{results_text}

Actual Results:
{actuals_text}
"""
{results_text}

Actual Results:
{actuals_text}
""".replace("{{DATE}}", date_str)
    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=types.Part.from_text(text=prompt),
        )
        return response.candidates[0].content.parts[0].text
    except genai.errors.ClientError as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e):
            return "AI analysis skipped: Gemini API quota exceeded."
        else:
            raise

# Read the predictions file
yesterday = (date.today() - timedelta(days=1)).isoformat()
predictions_file = f"predictions/nba/nba_daily_predictions_{yesterday}.txt"
with open(predictions_file, "r") as f:
    results_text = f.read()

# Get and format actual results
games = get_nba_games_yesterday()
actuals_text = "\n".join(
    f"{g['away']} {g['away_score']} @ {g['home']} {g['home_score']}" for g in games
)

today_str = date.today().isoformat()
summary = analyze_results_with_actuals(results_text, actuals_text, yesterday)

results_folder = os.path.join("bot_results", "nba")
os.makedirs(results_folder, exist_ok=True)
filename = os.path.join(results_folder, f"nba_daily_results_{today_str}.txt")

# Write summary to file
with open(filename, "w") as out_f:
    out_f.write(summary)

print(summary)
