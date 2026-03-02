import os
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types
from data.nhl_games import get_games_today
from data.odds import get_nhl_odds, match_odds_to_games
from datetime import date, timedelta
from data.odds import NHL_TEAM_NAME_MAP
import glob
from nhl_injuries_daily_run import scrape_nhl_injuries_by_team

load_dotenv()


def analyze_results(results_text, injuries_text):
    api_key = os.environ["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)

    # Read and concatenate all historical NHL results files
    hist_dir = os.path.join("bot_results", "nhl")
    hist_files = sorted(glob.glob(os.path.join(hist_dir, "nhl_daily_results_*.txt")))
    historical_results = ""
    for hf in hist_files:
        try:
            with open(hf, "r", encoding="utf-8") as hfile:
                historical_results += f"\n---\n{os.path.basename(hf)}\n" + hfile.read()
        except Exception:
            continue

    # Read last 10 days' result files
    last_10_files = hist_files[-10:] if len(hist_files) >= 10 else hist_files
    recent_results = ""
    for rf in last_10_files:
        try:
            with open(rf, "r", encoding="utf-8") as rfile:
                recent_results += f"\n---\n{os.path.basename(rf)}\n" + rfile.read()
        except Exception:
            continue

    # Strictly read external prompt file; no fallback
    prompt_path = os.path.join("prompts", "nhl_prompt.txt")
    today_str = date.today().isoformat()
    try:
        with open(prompt_path, "r", encoding="utf-8") as pf:
            prompt_text = pf.read()
            prompt_text = prompt_text.replace("{{RESULTS_TEXT}}", results_text)
            prompt_text = prompt_text.replace("{{TODAY_DATE}}", today_str)
            prompt_text = prompt_text.replace("{{HISTORICAL_RESULTS}}", historical_results)
            prompt_text = prompt_text.replace("{{RECENT_RESULTS}}", recent_results)
            prompt_text = prompt_text.replace("{{INJURIES}}", injuries_text)
    except Exception:
        return "AI analysis skipped: prompt file not found or unreadable."

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=types.Part.from_text(text=prompt_text),
        )
        return response.candidates[0].content.parts[0].text
    except genai.errors.ClientError as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e):
            return "AI analysis skipped: Gemini API quota exceeded."
        else:
            raise


games = get_games_today()
today_str = date.today().isoformat()
predictions_folder = os.path.join("predictions", "nhl")
os.makedirs(predictions_folder, exist_ok=True)
filename = os.path.join(predictions_folder, f"nhl_daily_predictions_{today_str}.txt")

# Get injuries as a formatted string
injuries_list = scrape_nhl_injuries_by_team()
if injuries_list:
    # Format injuries by team, one team per line, indented players
    injuries_text = "NHL Injured Players by Team:\n"
    for team, players in injuries_list.items():
        if players:
            injuries_text += f"{team}:\n"
            for player in players:
                injuries_text += f"  - {player}\n"
else:
    injuries_text = "NHL Injured Players by Team: None"

with open(filename, "w") as f:
    f.write(f"Date: {today_str}\n\n")

    if not games:
        f.write("No NHL games today\n")
        print("No NHL games today")
    else:
        odds_data = get_nhl_odds()
        matched = match_odds_to_games(games, odds_data, NHL_TEAM_NAME_MAP)

        results_text = ""
        for g in matched:
            line = (
                f"{g['away']} @ {g['home']}\n"
                f"Home odds: {g['home_odds']}, Away odds: {g['away_odds']}, O/U: {g['over_under']}\n"
                "------\n"
            )
            f.write(line)
            results_text += line

        print("NHL Matchups and Odds:")
        print(results_text)
        print(injuries_text)

        if results_text:
            summary = analyze_results(results_text, injuries_text)
            f.write("\nAI Analysis Summary:\n")
            f.write(summary + "\n")
            print("\nAI Analysis Summary:")
            print(summary)

print(f"Saved daily results to {filename}")
