import os
from data.nhl_games import get_games_yesterday
from google import genai
from google.genai import types
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

def analyze_results_with_actuals(results_text, actuals_text, summary_date):
    api_key = os.environ["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)
    prompt = f"""
You are a disciplined NHL betting analyst. Review the AI's predictions against the actual game results for {summary_date}.

For each recommended play:
- List the play header (as in the predictions file).
- Show the actual result in the format: Actual Result: <away> <away_score> @ <home> <home_score> (Total goals: <total>)
- State the outcome: WIN or LOSS, with a short reason (e.g., '5 is under 6.5').

After all plays, output a summary section:
---
Summary of AI Prediction Performance:
- Total Wins: <number>
- Total Losses: <number>

Use this exact format:

As a disciplined NHL betting analyst, I have reviewed the AI's predictions against the actual game results for {summary_date}.

Here's the breakdown:

1.  <PLAY HEADER>
    *   Actual Result: <away> <away_score> @ <home> <home_score> (Total goals: <total>)
    *   Outcome: **WIN** or **LOSS** (<short reason>)

---

**Summary of AI Prediction Performance:**

*   **Total Wins: <number>**
*   **Total Losses: <number>**

AI Predictions:
{results_text}

Actual Results:
{actuals_text}
"""
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
predictions_file = f"predictions/nhl/nhl_daily_predictions_{yesterday}.txt"
with open(predictions_file, "r") as f:
    predictions_text = f.read()

# Get and format actual results
games = get_games_yesterday()
actuals_text = "\n".join(
    f"{g['away']} {g['away_score']} @ {g['home']} {g['home_score']}" for g in games
)

# Analyze
summary_date = yesterday
summary = analyze_results_with_actuals(predictions_text, actuals_text, summary_date)

today_str = date.today().isoformat()
results_folder = os.path.join("bot_results", "nhl")
os.makedirs(results_folder, exist_ok=True)
filename = os.path.join(results_folder, f"nhl_daily_results_{today_str}.txt")

# Write summary to file
with open(filename, "w") as out_f:
    out_f.write(summary)

print(summary)
