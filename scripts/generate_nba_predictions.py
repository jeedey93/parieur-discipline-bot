import os
import sys
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from google import genai
from data.odds import get_nba_odds, match_nba_odds_to_games
from datetime import date, timedelta, datetime
from data.odds import NBA_TEAM_NAME_MAP
from data.nba_games import get_nba_games_today
import glob
import pytz

load_dotenv()

def get_run_time_suffix():
    """Determine if this is 7am or 12pm run based on environment variable or current time in Montreal timezone."""
    run_time = os.getenv("NBA_RUN_TIME")
    if run_time:
        return run_time  # Should be "7am" or "12pm"

    # Use Montreal time (America/Toronto)
    tz = pytz.timezone("America/Toronto")
    now = datetime.now(tz)
    current_hour = now.hour
    # 7am run: 6:00–7:59
    if 6 <= current_hour < 8:
        return "7am"
    # 12pm run: 11:00–12:59
    elif 11 <= current_hour < 13:
        return "12pm"
    else:
        # Default based on which is closer
        if current_hour < 10:
            return "7am"
        else:
            return "12pm"

def analyze_results(results_text, recent_games):
    api_key = os.environ["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)

    # Read and concatenate all historical NBA results files (not predictions)
    hist_dir = os.path.join("data", "bot_results", "nba")
    hist_files = sorted(glob.glob(os.path.join(hist_dir, "nba_daily_results_*.txt")))
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

    # Strictly read external prompt; no fallback
    prompt_path = os.path.join("prompts", "nba_prompt.txt")
    today_str = date.today().isoformat()
    try:
        with open(prompt_path, "r", encoding="utf-8") as pf:
            prompt_text = pf.read()
            prompt_text = prompt_text.replace("{{RESULTS_TEXT}}", results_text)
            prompt_text = prompt_text.replace("{{TODAY_DATE}}", today_str)
            prompt_text = prompt_text.replace("{{HISTORICAL_RESULTS}}", historical_results)
            prompt_text = prompt_text.replace("{{RECENT_RESULTS}}", recent_results)
            prompt_text = prompt_text.replace("{{RECENT_GAMES}}", recent_games)
    except Exception as e:
        # If prompt file is missing or unreadable, skip AI analysis
        return "AI analysis skipped: prompt file not found or unreadable."

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt_text,
        )
        return response.text.strip()
    except genai.errors.ClientError as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e):
            return "AI analysis skipped: Gemini API quota exceeded."
        else:
            raise

today_str = date.today().isoformat()
predictions_folder = os.path.join("data", "predictions", "nba")
daily_runs_folder = os.path.join(predictions_folder, "daily_runs")
os.makedirs(predictions_folder, exist_ok=True)
os.makedirs(daily_runs_folder, exist_ok=True)

# Determine which run this is
run_time = get_run_time_suffix()
# Write directly to daily_runs folder for 7am/12pm runs
if run_time == "7am":
    filename = os.path.join(daily_runs_folder, f"nba_daily_predictions_{today_str}_7am.txt")
elif run_time == "12pm":
    filename = os.path.join(daily_runs_folder, f"nba_daily_predictions_{today_str}_12pm.txt")
else:
    # Fallback goes to main folder
    filename = os.path.join(predictions_folder, f"nba_daily_predictions_{today_str}_{run_time}.txt")

# Check if file already exists - skip if it does
if os.path.exists(filename):
    print(f"⚠️  Predictions file already exists: {filename}")
    print("Skipping prediction generation to avoid overwriting existing file.")
    exit(0)

# Fetch and save games data
games = get_nba_games_today()

# Save raw games data to file
games_data_folder = os.path.join("data", "games", "nba")
os.makedirs(games_data_folder, exist_ok=True)
games_data_file = os.path.join(games_data_folder, f"nba_games_{today_str}.txt")

with open(games_data_file, "w") as gf:
    gf.write(f"Date: {today_str}\n\n")
    if games:
        for game in games:
            gf.write(f"{game['away']} @ {game['home']}\n")
    else:
        gf.write("No games today\n")

print(f"✅ Saved raw games data to: {games_data_file}")

odds = get_nba_odds()

# Optional: allow passing injury notes via environment or external pre-processing
extra_injury_notes = os.getenv("NBA_INJURY_NOTES")

# Read last 7 days of games from saved files
games_dir = os.path.join("data", "games", "nba")
games_files = sorted(glob.glob(os.path.join(games_dir, "nba_games_*.txt")))
last_7_files = games_files[-7:] if len(games_files) >= 7 else games_files
recent_games = ""
for gf in last_7_files:
    try:
        with open(gf, "r", encoding="utf-8") as gfile:
            recent_games += f"\n---\n{os.path.basename(gf)}\n" + gfile.read()
    except Exception:
        continue

if not recent_games:
    recent_games = "No recent games data available"

# Match structured odds to games
matched = match_nba_odds_to_games(games, odds, NBA_TEAM_NAME_MAP)
predictions_text = ""

with open(filename, "w") as f:
    f.write(f"Date: {today_str}\n\n")
    if not matched:
        f.write("No NBA games today or no odds available\n")
        print("No NBA games today or no odds available")
    else:
        print("NBA Matchups and Odds:")
        for g in matched:
            # Headline summary per game (write to file + include in predictions_text)
            line = (
                f"{g['home']} vs {g['away']}\n"
                f"Home odds: {g.get('home_odds')}, Away odds: {g.get('away_odds')}, "
                f"O/U: {g.get('over_under')}\n"
                # Added spreads summary in the headline print
                f"Spreads: Home {g.get('spread_home_points')} ({g.get('spread_home_price')}), "
                f"Away {g.get('spread_away_points')} ({g.get('spread_away_price')})\n"
                "------\n"
            )
            print(line, end="")
            f.write(line)
            predictions_text += line

            # Verbose per-bookmaker markets ONLY for predictions_text (skip writing to file)
            bm_list = g.get('bookmakers_odds', [])
            if bm_list:
                predictions_text += "Bookmakers snapshot:\n"
                for bm in bm_list:
                    title = bm.get('title') or bm.get('key') or 'Unknown Bookmaker'
                    predictions_text += f"  {title}\n"
                    for m in bm.get('markets', []):
                        mkey = m.get('key', 'unknown')
                        outcomes = m.get('outcomes', [])
                        out_strs = []
                        for o in outcomes:
                            if isinstance(o, dict):
                                name = o.get('name', 'N/A')
                                price = o.get('price', 'N/A')
                                point = o.get('point')
                                if point is not None:
                                    out_strs.append(f"{name} @ {price} (point {point})")
                                else:
                                    out_strs.append(f"{name} @ {price}")
                            else:
                                out_strs.append(str(o))
                        predictions_text += f"    {mkey}: " + ", ".join(out_strs) + "\n"
                predictions_text += "------\n"

        # Append any external injury notes to give the model explicit names if provided
        if extra_injury_notes:
            predictions_text += "\nInjury Notes (user-supplied):\n" + extra_injury_notes + "\n"

        if predictions_text:
            summary = analyze_results(predictions_text, recent_games)
            f.write("\nAI Analysis Summary:\n")
            f.write(summary + "\n")
            print("\nAI Analysis Summary:")
            print(summary)

print(f"Saved NBA daily predictions to {filename}")
