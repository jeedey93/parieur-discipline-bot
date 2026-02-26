import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from data.odds import get_nba_odds, match_nba_odds_to_games
from datetime import date
from data.odds import NBA_TEAM_NAME_MAP
from data.nba_games import get_nba_games_today
import glob

load_dotenv()

def analyze_results(results_text):
    api_key = os.environ["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)

    # Read and concatenate all historical NBA results files (not predictions)
    hist_dir = os.path.join("bot_results", "nba")
    hist_files = sorted(glob.glob(os.path.join(hist_dir, "nba_daily_results_*.txt")))
    historical_results = ""
    for hf in hist_files:
        try:
            with open(hf, "r", encoding="utf-8") as hfile:
                historical_results += f"\n---\n{os.path.basename(hf)}\n" + hfile.read()
        except Exception:
            continue

    # Strictly read external prompt; no fallback
    prompt_path = os.path.join("prompts", "nba_prompt_v2.txt")
    today_str = date.today().isoformat()
    try:
        with open(prompt_path, "r", encoding="utf-8") as pf:
            prompt_text = pf.read()
            prompt_text = prompt_text.replace("{{RESULTS_TEXT}}", results_text)
            prompt_text = prompt_text.replace("{{TODAY_DATE}}", today_str)
            prompt_text = prompt_text.replace("{{HISTORICAL_RESULTS}}", historical_results)
    except Exception as e:
        # If prompt file is missing or unreadable, skip AI analysis
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

today_str = date.today().isoformat()
predictions_folder = os.path.join("predictions", "nba")
os.makedirs(predictions_folder, exist_ok=True)
filename = os.path.join(predictions_folder, f"nba_daily_predictions_{today_str}.txt")

games = get_nba_games_today()
odds = get_nba_odds()

# Optional: allow passing injury notes via environment or external pre-processing
extra_injury_notes = os.getenv("NBA_INJURY_NOTES")

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
            summary = analyze_results(predictions_text)
            f.write("\nAI Analysis Summary:\n")
            f.write(summary + "\n")
            print("\nAI Analysis Summary:")
            print(summary)

print(f"Saved NBA daily predictions to {filename}")
